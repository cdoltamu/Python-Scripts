# MARC reading
import sys
from pymarc import MARCReader
# MARC write
from pymarc import MARCWriter
from pymarc import Record, Field, Subfield
from pymarc import MARCMakerReader
# parse string patterns
import re
# add error logging
import logging

# Program
def update_item_enum_chron(marc_input, marc_output_barcodes, marc_output_hldgs_state):
    #marc_output_barcodes is for records with barcodes
    #marc_output_hldgs_state is for records with no barcodes, so someone will need to manually create a holdings statement based on the item enum/chron
    
    #Clean string
    if (marc_input[0] == '"' and marc_input[-1] == '"') or (marc_input[0] == "'" and marc_input[-1] == "'"):
            marc_input= marc_input[1:-1]
    #Check input string for correct file type
    if (marc_input[-4:] != '.mrc'):
            print('File must be in .mrc format and the filename must end in .mrc like \\FOLDER\\FILENAME.mrc')

    #Open file
    with open(marc_input, 'rb') as fh:
        reader = MARCReader(fh)
        marc_output_hldgs_state = Record()

        #initialize MARCWriter
        writer = MARCWriter(open(marc_output_barcodes, 'wb'))

        #Loop through MARC file
        for bib_record in reader:
            barcode_stubs = []
            #Run barcode function
            if ('876' or '877' or '878') in bib_record:
                barcode_stubs = item_update_dictionary(bib_record, marc_output_barcodes)
                
            #Write records to output file
                for each_record in barcode_stubs:
                    print(each_record.leader)
                    # writer.write(each_record.leader)
                    writer.write(each_record)

                # check_reader = MARCReader(open(marc_output_barcodes,'rb'))
                # for check_record in check_reader:
                #     print(check_record.leader)

            #otherwise, run statement function
            else:
                print(bib_record['001'])

#Store MARC values into a dictionary for barcodes file
def item_update_dictionary(record, marc_output_file):
    all_new_item_records = []
    #Create separate stub records for each item to import into FOLIO
    records_with_items = record.get_fields('876', '877', '878')
    for each_item in records_with_items:
        stub_item_record = Record()
        #Get leader from original record and 004 from holdings
        stub_item_record.leader = get_LDR(record)
        # print(stub_item_record)
        new_001 = get_001(record)
        new_004 = get_004(record)
        #Get title from original record for Data Import debugging
        new_245 = get_245(record)
        #Get new 852
        new_holdings_info = get_holdings_ext(record)
        #Get new 876/877/878
        new_item_supplement_index_record = get_new_record(each_item, record)
        #Write new fields to record and add to list
        stub_item_record.add_field(new_001, new_004, new_245, new_holdings_info, new_item_supplement_index_record)
        # print(type(stub_item_record))
        all_new_item_records.append(stub_item_record)

    return all_new_item_records

    
#Copy the LDR from bib record - FOLIO will not accept default pymarc leader
def get_LDR(source_record):
    bib_leader = source_record.leader
    return bib_leader  

def get_001(source_record):
    if '001' in source_record:
        bib_001 = source_record['001']
        return bib_001

#Copy the 004 from bib record - I may not need this step, but want to include just in case
def get_004(source_record):
    if '004' in source_record:
        bib_004 = source_record['004']
        return bib_004
    
#Copy the title from the bib record - included for FOLIO data import debugging
def get_245(source_record):
    if '245' in source_record:
        bib_245 = source_record['245']
        # print(type(bib_245))
        return bib_245
    else:
        bib_245 = Field(tag= '245', indicators= ['0','0'], subfields=[Subfield(code='a', value='BLAH')])
        return bib_245

#Copy the 852 $c on from the bib record - want to include just in case I end up creating new items because something was skipped in initial import
def get_holdings_ext(source_record):
    if '852' in source_record:
        #Keep indicators
        original_852 = source_record['852']
        cleaned_852 = Field(original_852.tag, original_852.indicators)
        subfields_to_keep = ['c', 'k', 'h', 'm', 'o']

        for subfield in original_852.subfields:
            
            subfield_dict = []
            if subfield.code in subfields_to_keep:
                cleaned_852.add_subfield(subfield.code, subfield.value)     

            if 't' in original_852:
                if original_852['t'] > '1':
                    cleaned_852.add_subfield('t', original_852['t'])

        return cleaned_852

def get_new_record(item_record, source_record):
    if item_record.tag == '876':
        new_item = add_enum_chron_to_item(item_record, source_record, '853', '863')
        return new_item

    if item_record.tag == '877':
        new_supplement = add_enum_chron_to_item(item_record, source_record, '854', '864')
        return new_supplement

    elif item_record.tag == '878':
        new_index = add_enum_chron_to_item(item_record, source_record, '855', '865')
        return new_index

def add_enum_chron_to_item(item_record, source_record, pattern_field, data_field):
    if '8' in item_record:
        linking_code = item_record['8']
        enum_chron_pattern = linking_code.split('.')[0]
        source_enum_chron = source_record.get_fields(pattern_field, data_field)
        raw_enum_chron = {}
        enum_chron_dict_linking = raw_enum_chron.values()
        combined_enum_chron = {}

        for line in source_enum_chron:
            marc_field = line.tag
            #Get the pattern for the fields
            if pattern_field in marc_field:
                if line['8'] == enum_chron_pattern:
                    for pattern_subfield in line:
                        raw_enum_chron.update(line.subfields_as_dict())
                     

            #Get the data for the fields
            if data_field in marc_field:
                if line['8'] == linking_code:
                    line_as_dict = line.subfields_as_dict()
                    all_keys = line_as_dict.keys()

                    #Error catching for multiple enumerations and chronologies per item
                    if line['8'] in enum_chron_dict_linking:
                        logger.warning('%s has multiple enum/chron [%s] add by hand', str(item_record), str(line))
                        raw_enum_chron['8'] = 'error'

                    else:
                        #add the data to the pattern
                        for key in all_keys:    
                            raw_enum_chron['8'] = line['8']  
                            raw_enum_chron_keys = raw_enum_chron.keys()
                            if key in raw_enum_chron:
                                enum_data = str(line[key])
                                for pattern_data in raw_enum_chron[key]:
                                    #cleaning the pattern data
                                    parentheses = re.compile("\\((.+)\\)")
                                    parenthetical_format = parentheses.search(pattern_data)
                                    if parenthetical_format:
                                        raw_enum_chron[key] = enum_data
                                    
                                    elif not pattern_data.endswith('.'):
                                        raw_enum_chron[key] = pattern_data + ' ' + enum_data
                                    
                                    else: 
                                        raw_enum_chron[key] = pattern_data + enum_data

                                    #removing unused pattern keys from raw list
                                    for raw_key in list(raw_enum_chron):
                                        if raw_key not in all_keys:
                                            raw_enum_chron.pop(raw_key)

        #Combine levels of enum and chronology into tuples
        enum_chron_keys = raw_enum_chron.keys()
        enum_tuple = ()
        chron_tuple = ()
        #add flag for items with multiple enum/chron
        if raw_enum_chron['8'] == 'error':
            item_record.add_subfield('7', 'add additional enum/chron by hand')

        if ('a' or 'b' or 'c') in enum_chron_keys:
            for key in enum_chron_keys:
                if key == 'a':
                    if '3' in combined_enum_chron:
                        next_part_first_enum = combined_enum_chron['3'] + '; ' + raw_enum_chron[key]
                        combined_enum_chron['3'] = next_part_first_enum
                    else:
                        first_enum = raw_enum_chron[key]
                        combined_enum_chron['3'] = first_enum
                if key == 'b':
                    second_enum = combined_enum_chron['3'] + ':' + raw_enum_chron[key]
                    combined_enum_chron['3'] = second_enum
                if key == 'c':
                    third_enum = combined_enum_chron['3'] + ':' + raw_enum_chron[key]
                    combined_enum_chron['3'] = third_enum
                    
            item_record.add_subfield('3', combined_enum_chron['3'])
    
        if ('i' or 'j' or 'k') in enum_chron_keys:
            for key in enum_chron_keys:
                if key == 'i':
                    combined_enum_chron['4'] = raw_enum_chron[key]

                if key == 'j':
                    second_chron = combined_enum_chron['4'] + ':' + raw_enum_chron[key]
                    combined_enum_chron['4'] = second_chron
                if key == 'k':
                    third_chron = combined_enum_chron['4'] + ':' + raw_enum_chron[key]
                    combined_enum_chron['4'] = third_chron

            item_record.add_subfield('4', combined_enum_chron['4'])

    return item_record
                

marc_source_file = input("Please input the path and filename of your MARC file. Make sure it ends in '.mrc': ")
output_prefix = input("Please input the prefix for the two .mrc output files: ")

#Create log file for each job
logger = logging.getLogger(__name__)
logging.basicConfig(filename=('logs//' + output_prefix + '- log.txt'), encoding='utf-8', level=logging.DEBUG)

file_for_barcodes =  output_prefix + '_withbarcodes.mrc'
file_for_holdings_state = output_prefix + '_nobarcodes_needhldgsstate.mrc'
update_item_enum_chron(marc_source_file, file_for_barcodes, file_for_holdings_state)

sys.exit()