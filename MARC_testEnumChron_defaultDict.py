# MARC reading
import sys
from pymarc import MARCReader
# MARC write
from pymarc import MARCWriter
from pymarc import Record, Field, Subfield
# parse string patterns
import re

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

        #Loop through MARC file
        for bib_record in reader:
            #Run barcode function
            if ('876' or '877' or '878') in bib_record:
                print('We have got an item, lads')
                barcode_stubs = item_update_dictionary(bib_record, marc_output_barcodes)

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
        #Get new leader and 004
        stub_item_record.leader = get_LDR(record)
        new_001 = get_001(record)
        new_004 = get_004(record)
        #Get new 852
        new_holdings_info = get_holdings_ext(record)
        #Get new 876/877/878
        new_item_supplement_index_record = get_new_record(each_item, record)
        # print(new_item_supplement_index_record)
        #Write new fields to record and add to list
        # stub_item_record.add_field(new_001, new_004, new_holdings_info, new_item_supplement_index_record)
        # print(stub_item_record)
        # all_new_item_records.append(stub_item_record)
        

    # Write each record into MARC
    with open(marc_output_file, 'wb') as marc_file:
        for item_marc in all_new_item_records:
            marc_file.write(item_marc.as_marc())


    
    #read new file to check
    with open(marc_output_file, 'rb') as check_data:
        check_reader = MARCReader(check_data)
        for check_record in check_reader:
            print(check_record)

    
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
        # return new_item

    if item_record.tag == '877':
        new_supplement = add_enum_chron_to_item(item_record, source_record, '854', '864')
        # return new_supplement

    elif item_record.tag == '878':
        new_index = add_enum_chron_to_item(item_record, source_record, '855', '865')
        # return new_index

def add_enum_chron_to_item(item_record, source_record, pattern_field, data_field):
    if '8' in item_record:
        linking_code = item_record['8']
        enum_chron_pattern = linking_code.split('.')[0]
        source_enum_chron = source_record.get_fields(pattern_field, data_field)
        subfield_linking_keys = []
        subfield_patterns = ''
        raw_enum_chron = {}
        enum_chron_dict_linking = raw_enum_chron.values()
        combined_enum_chron = {}
        # raw_enum_chron = []
        # combined_enum_chron = {}
        #Get the pattern for the fields
        for line in source_enum_chron:
            marc_field = line.tag
            subfield_data = []
            if pattern_field in marc_field:
                if line['8'] == enum_chron_pattern:
                    for pattern_subfield in line:
                        subfield_key = pattern_subfield.code
                        subfield_pattern = pattern_subfield.value
                        pattern_data = pattern_subfield.code, pattern_subfield.value
                        subfield_patterns.join(pattern_data)

            if data_field in marc_field:
                if line['8'] == linking_code:
                    line_as_dict = line.subfields_as_dict()
                    all_keys = line_as_dict.keys()
                    if line['8'] in enum_chron_dict_linking:
                        for key in all_keys:
                            print(key)
                    else:
                        raw_enum_chron['8'] = line['8']
                    
        print(raw_enum_chron)
                    
                    # for data_subfields in line:
                    #     subfield_data = data_subfields.value
                    #     parentheses = re.compile("\\((.+)\\)")
                    #     parenthetical_format = parentheses.search(str(pattern_data))
                    #     print(parenthetical_format)

            
            
        # print(subfield_patterns)
                                        

            

            # if data_field in marc_field:
            #     if line['8'] == linking_code:
            #         line_as_dict = line.subfields_as_dict()
            #         all_keys = line_as_dict.keys()
            #         for key in all_keys:
            #             if key in raw_enum_chron:
            #                 enum_data = str(line[key])
            #                 for pattern_data in raw_enum_chron[key]:
            #                     print(pattern_data)
            #                     print(enum_data)
            #                     parentheses = re.compile("\\((.+)\\)")
            #                     parenthetical_format = parentheses.search(pattern_data)
            #                     if parenthetical_format:
            #                         # formatted_data = enum_data
            #                         # raw_enum_chron[key] = raw_enum_chron[key].append(enum_data)
            #                         raw_enum_chron[key] = enum_data
            #                         # print(raw_enum_chron[key])
                                
            #                     elif not pattern_data.endswith('.'):
            #                         raw_enum_chron[key] = pattern_data + ' ' + enum_data
            #                         # raw_enum_chron[key] = ' '.join(raw_enum_chron[key])
                                
            #                     else: 
            #                         raw_enum_chron[key] = raw_enum_chron[key] + [enum_data]
            #                         raw_enum_chron[key] = ''.join(raw_enum_chron[key])
            #                         # print(raw_enum_chron[key])

marc_source_file = input("Please input the path and filename of your MARC file. Make sure it ends in '.mrc': ")
output_prefix = input("Please input the prefix for the two .mrc output files: ")
file_for_barcodes =  output_prefix + '_withbarcodes.mrc'
file_for_holdings_state = output_prefix + '_nobarcodes_needhldgsstate.mrc'
update_item_enum_chron(marc_source_file, file_for_barcodes, file_for_holdings_state)