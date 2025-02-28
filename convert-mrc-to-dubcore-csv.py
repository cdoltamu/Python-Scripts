# MARC reading
import sys
from pymarc import MARCReader
# CSV write
import csv
import os
# parse string patterns
import re

# Program 
def write_db_from_marc(marc_input, output_file):
    #Check input string ends in correct file type 
        #if .mrc, proceed
        #if not, print("File must be in .mrc format and the filename must end in .mrc like /FOLDER/FILENAME.mrc")
    #Clean string
    if (marc_input[0]=='"' and marc_input[-1]=='"') or (marc_input[0]=="'" and marc_input[-1]=="'"):
            marc_input= marc_input[1:-1]


    # Open File
    with open(marc_input, 'rb') as fh:
        reader = MARCReader(fh)
        print("Input Opens!")
        #Loop through MARC file
        for record in reader:
             dictionary_for_csv_fields = {}

             dictionary_for_csv_fields = dissertation_dictionary(record)
             dictionary_to_csv(dict_data=dictionary_for_csv_fields,output_name=output_file)
            #run the write to csv function

#Write to csv function
def dictionary_to_csv(dict_data, output_name):
    #Make sure file exists, string trimmed, and ends in .csv
    csv_filename = output_name
    if not csv_filename:
        csv_filename = 'output.csv'
    if (csv_filename[0]=='"' and csv_filename[-1]=='"') or (csv_filename[0]=="'" and csv_filename[-1]=="'"):
        csv_filename =csv_filename[1:-1]
        if not csv_filename[-4:] == '.csv':
            csv_filename = csv_filename + '.csv'

    #if file is blank, create headers
    if not os.path.isfile(csv_filename):
        with open(csv_filename, mode='w', encoding='utf-8', newline='') as csv_file:
            field_names = dict_data.keys()
            writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

            # Write the headers to csv file
            writer.writeheader()
   
    #add each new row of data
    with open(csv_filename, mode='a', encoding='utf-8', newline='') as csv_file:
        field_names = dict_data.keys()
        writer = csv.DictWriter(csv_file, fieldnames=field_names, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writerow(dict_data)

#Store MARC values into dictionary
def dissertation_dictionary(record):
    dissertation_fields = {}

    dissertation_fields['filename'] = get_filename(record)
    dissertation_fields['dc.subject.classification'] = get_dc_subject_classification(record)
    dissertation_fields['dc.creator'] = get_dc_creator(record)
    dissertation_fields['dc.title[en]'] = get_dc_title(record)
    dissertation_fields['dc.title.alternative[en]'] = get_dc_title_alternative(record)
    dissertation_fields['dc.date.issued'] = get_dc_date_issued(record)
    dissertation_fields['dc.format.extent[en]'] = get_dc_format_extent(record)
    dissertation_fields['dc.description[en]'] = get_dc_description(record)
    dissertation_fields['dc.description.abstract[en]'] = get_dc_description_abstract(record)
    dissertation_fields['thesis.degree.name[en]'] = get_thesis_degree_name(record)
    dissertation_fields['thesis.degree.level[en]'] = get_thesis_degree_level(record)
    dissertation_fields['thesis.degree.discipline[en]'] = get_thesis_degree_discipline(record)
    dissertation_fields['dc.subject[en]'] = get_dc_subject(record)
    dissertation_fields['dc.subject.mesh[en]'] = get_dc_subject_mesh(record)
    dissertation_fields['dc.subject.nalt[en]'] = get_dc_subject_nalt(record)
    dissertation_fields['dc.subject.lcsh[en]'] = get_dc_subject_lcsh(record)
    dissertation_fields['dc.contributor.committeeMember'] = get_contributor_committeemember(record)
    dissertation_fields['dc.contributor.advisor'] = get_contributor_advisor(record)
    dissertation_fields['handle'] = get_handle(record)
    dissertation_fields['dc.identifier.oclc'] = get_identifier_oclc(record)
    dissertation_fields['dc.identifier.isbn'] = get_isbn_identifier(record)

    return dissertation_fields

# MARC: 001
def get_filename(record):
    filename = ''
    
    if '001' in record:
        filename = '{id}.pdf'.format(id=str(record['001'].data).strip())
    
    return filename

# MARC: 099$aaa
def get_dc_subject_classification(record):
    dc_subject_classification = ''
    ls_subfields = ''

    # Get SUBJECT CLASSIFICATION
    if '099' in record:

        # populate list of subfields
        ls_subfields = record['099'].get_subfields('a')

        if len(ls_subfields) > 0:
            for subfield in ls_subfields:
                subfield = subfield.strip()
        
        # Join together SUBFIELDS with spaces
        dc_subject_classification = ' '.join(ls_subfields)

        # Some records have 'Disseration' split weirdly; cleanup
        if "Disser- tation" in dc_subject_classification:
            dc_subject_classification = dc_subject_classification.replace('Disser- tation', 'Dissertation')
    
    return dc_subject_classification

# MARC: 020 ISBN
def get_isbn_identifier(record):
    dc_identifier_isbn = ''
    ls_020 = []
    if '020' in record:
        field_020 = record['020']
        if 'a' in field_020:
            isbn = field_020['a'].strip()
            ls_020.append(isbn)
    
        if len(ls_020) > 0:
            dc_identifier_isbn = '||'.join(ls_020)
        
    return dc_identifier_isbn


# MARC: 100$a
# REPEAT REPEAT
def get_dc_creator(record):
    # Default variables
    dc_creator = ''
    ls_100 = []
    ls_creator = []

    # Check if there is 100 field in record, if so get all and put into list
    if '100' in record:
        ls_100 = record.get_fields('100')
    
        # Loop through the 100 fields
        for person in ls_100:
            if 'a' in person:
                initial_name = person['a'].strip()

                # If last character is ',' remove it
                if initial_name[-1] == ',' or '.':
                    formatted_name = initial_name[0:-1].strip()

                    ls_creator.append(formatted_name)
    
    # Check for 110 field
    if '110' in record:
        ls_110 = record.get_fields('110')

        for corp in ls_110:
            if 'a' in corp:
                corp_name = corp['a'].strip()

                if corp_name[-1] == '.':
                    corp_name = corp_name[0:-1]
                
                ls_creator.append(corp_name)

    # Join together CREATOR(S) with double pipe (||) if there are multiple
    if len(ls_creator) > 0:
        dc_creator = '||'.join(ls_creator)

    return dc_creator



# MARC: 245$a$b
# Remove punctuation at end, including /
def get_dc_title(record):
    # Default variables
    title_a = ''
    title_b = ''
    dc_title = ''

    # Get TITLE$a
    if '245' in record:
        field_245 = record['245']

        if field_245['a'] is not None:
            title_a = field_245['a']
            title_a = title_a.strip()

            # Remove trailing [spaces, '.', '/']
            while title_a[-1] in ['.','/']:
                title_a = title_a[0:-1].strip()
        
        # Get TITLE$b
        if 'b' in field_245:
            title_b = str(field_245['b']).strip()

            # Remove trailing [spaces, '.', '/']
            while title_b[-1] in ['.','/']:
                title_b = title_b[0:-1].strip()
    
    # Combine together the two
    dc_title = title_a + ' ' + title_b
    
    return dc_title



# MARC: 246$a
# Remove punctuation at end, including /
def get_dc_title_alternative(record):
    # Default variables
    dc_title_alternative = ''

    # Get TITLE ALTERNATIVE
    if '246' in record:
        field_246 = record['246']

        if 'a' in field_246:
            dc_title_alternative = field_246['a']
            dc_title_alternative = dc_title_alternative.strip()

            # Remove trailing [spaces, '.', '/']
            while dc_title_alternative[-1] in ['.','/']:
                dc_title_alternative = dc_title_alternative[0:-1].strip()
    
    return dc_title_alternative



# MARC: 260$c
# Remove punctuation
def get_dc_date_issued(record):
    # Default variables
    dc_date_issued = ''

    # Get DATE ISSUED - Check 260 first
    if '260' in record:
        field_260 = record['260']

        if 'c' in field_260:
            dc_date_issued = field_260['c']
            dc_date_issued = dc_date_issued.strip()

            # Remove trailing [spaces, '.', '/']
            while dc_date_issued[-1] in ['.','/']:
                dc_date_issued = dc_date_issued[0:-1].strip()
    
    # Get DATE ISSUED - if 260 not there
    if '264' in record:
        field_264 = record['264']

        if 'c' in field_264:
            dc_date_issued = field_264['c']

            # Remove trailing [spaces, '.', '/']
            while dc_date_issued[-1] in ['.','/']:
                dc_date_issued = dc_date_issued[0:-1].strip()
    
    return dc_date_issued



# MARC: 300$a
def get_dc_format_extent(record):
    # Default variables
    dc_format_extent = ''

    # Get FORMAT EXTENT
    if '300' in record:
        field_300 = record['300']

        if 'a' in field_300:
            dc_format_extent = field_300['a']
            dc_format_extent = dc_format_extent.strip()

            # Remove trailing [spaces, '.', '/', ';']
            while dc_format_extent[-1] in ['.','/', ';']:
                dc_format_extent = dc_format_extent[0:-1].strip()
            
            # Remove ' :'
            if ' :' in dc_format_extent:
                dc_format_extent = dc_format_extent.replace(' :', '')
    
    return dc_format_extent



# MARC: 500$a
def get_dc_description(record):
    # Default variables
    dc_description = ''
    ls_description = []

    # Get DESCRIPTION
    if '500' in record:
        fields_500 = record.get_fields('500')

        for each_field in fields_500:
            if 'a' in each_field:
                description_line = each_field['a']
                description_line = description_line.strip()

                #clean string of quotes and/or period
                if description_line[-1] == '"' and description_line[0] == '"':
                    description_line = description_line[1:-1].strip()
                
                if description_line[-1] == '.':
                    description_line = description_line[0:-1]

                ls_description.append(description_line)

            if len(ls_description) > 0:
                dc_description = '||'.join(ls_description)
    
    return dc_description



# MARC: 520$a
def get_dc_description_abstract(record):
    # Default variables
    dc_description_abstract = ''

    # Get DESCRIPTION ABSTRACT
    if '520' in record:
        field_520 = record['520']

        if 'a' in field_520:
            dc_description_abstract = field_520['a']
    
    return dc_description_abstract



# MARC: 502$b
# Will be either Doctoral|Masters|Bachelors in/of [field name]
def get_thesis_degree_name(record):
    # Default variables
    thesis_degree_name = ''

    # Get DEGREE TYPE
    if '502' in record:
        field_502 = record['502']

        if 'b' in field_502:
            field_502b = field_502['b']
            field_502b = field_502b.strip()

            # "{type part} in {department}" -- grabs the {type part}
            if " in " in field_502b:
                field_502b = field_502b[0:field_502b.find(" in ")]

            if field_502b[-1] == '.':
                field_502b = field_502b[0:-1]
            
            thesis_degree_name = field_502b
    
    return thesis_degree_name



# MARC: 502$b
# Will be Doctoral, Masters, or Bachelor
def get_thesis_degree_level(record):
    # Default variables
    thesis_degree_level = ''

    # Get DEGREE LEVEL
    if '502' in record:
        field_502 = record['502']

        if 'b' in field_502:
            field_502b = field_502['b']

            if " in " in field_502b:
                # "{type part} in {department}" -- grabs the {type part}
                type_part_extract = field_502b[0:field_502b.find(" in ")]
                thesis_degree_level = type_part_extract.lower()

            else:
                type_part_extract = field_502b
                thesis_degree_level = type_part_extract.lower()

            # Doctorial/Ph.D
            if thesis_degree_level in ["ph. d", "ph. d.", "ph.d.", "ph d"]:
                thesis_degree_level = 'Doctorial'
            # Master
            elif thesis_degree_level in ['master']:
                thesis_degree_level = 'Master'
            # Bachelor
            elif thesis_degree_level in ['bachelor']:
                thesis_degree_level = 'Bachelor'
    
    return thesis_degree_level



# MARC: 502$b
# Name of department
def get_thesis_degree_discipline(record):
    # Default variables
    thesis_degree_discipline = ''
    ls_degree_disc = []

    #Get DEGREE DISCIPLINE
    if '502' in record:
        field_502 = record['502']
        if 'b' in field_502:
            field_502b = field_502['b']

            if " in " in field_502b:
                cleaned_discipline = field_502b[field_502b.find(" in ")+4:]
                ls_degree_disc.append(cleaned_discipline)

    
    #If not in 502, pull from 500
    if '500' in record:
        fields_500 = record.get_fields('500')
        for field_line in fields_500:
            if 'a' in field_line:
                field_500_descipt = field_line['a']
                if "Major" in field_500_descipt:
                    thesis_degree_discipline_string = field_500_descipt[field_500_descipt.find("subject: ")+9:]

                    #If last character is '."' remove it
                    if thesis_degree_discipline_string[-2] == '.':
                        cleaned_discipline = thesis_degree_discipline_string[0:-2].strip()
                        ls_degree_disc.append(cleaned_discipline)

                    #Worst case, pull from 650
                    elif '650' in record:
                        ls_subjects = record.get_fields('650')
                        for field_line in ls_subjects:
                            if 'a' in field_line:
                                field_650_descript = field_line['a']
                                
                                if "Major" in field_650_descript:
                                    thesis_degree_discipline_string = field_650_descript[field_650_descript.find("Major ")+6:]

                                    #if last character is '.' remove it
                                    if thesis_degree_discipline_string[-1] == '.':
                                        cleaned_discipline = thesis_degree_discipline_string[0:-1].strip()
                                        cleaned_discipline = cleaned_discipline.title()
                                        ls_degree_disc.append(cleaned_discipline)

                                    else:
                                        cleaned_discipline = thesis_degree_discipline_string.title()
                                        ls_degree_disc.append(cleaned_discipline)
        
        
    if len(ls_degree_disc) > 0:
            thesis_degree_discipline = '||'.join(ls_degree_disc)


    return thesis_degree_discipline



# MARC: 600|610|650; ind2: 4-7
# REPEAT REPEAT
def get_dc_subject(record):
    # Default variables
    dc_subject = ''
    ls_subject = []

    for field in ['600','610','650']:
        ls_fields = record.get_fields(field)

        # Process subfields based on INDICATOR
        for subject in ls_fields:
            # Test ind2
            if subject.indicator2 in ['4', '5', '6', '7']:
                
                # Get subfields:
                for sub in ['a','b','v','x','y','z']:
                    results = []
                    if subject.get(sub):
                        results = subject.get_subfields(sub)
                    
                    # Cleanup subfield
                    for val in results:
                        cleaned = val.strip()
                        if cleaned[-1] == '.':
                            cleaned = cleaned[0:-1].strip()

                        # Add CLEANED subject to list of subjects
                        ls_subject.append(cleaned)


    # Join together SUBJECT with double pipe (||)
    if len(ls_subject) > 0:
        dc_subject = '||'.join(ls_subject)

    return dc_subject



# MARC: 600|610|650; ind2: 2
# REPEAT REPEAT
def get_dc_subject_mesh(record):
    # Default variables
    dc_subject_mesh = ''
    ls_subject_mesh = []

    # Process applicable fields
    for field in ['600','610','650']:
        ls_fields = record.get_fields(field)

        # Process subfields based on INDICATOR
        for subject in ls_fields:
            # Test ind2
            if subject.indicator2 in ['2']:
                
                # Get subfields:
                for sub in ['a','b','v','x','y','z']:
                    results = []
                    if subject.get(sub):
                        results = subject.get_subfields(sub)
                    
                    # Cleanup subfield
                    for val in results:
                        cleaned = val.strip()
                        if cleaned[-1] == '.':
                            cleaned = cleaned[0:-1].strip()

                        # Add CLEANED subject to list of subjects
                        ls_subject_mesh.append(cleaned)

    # Join together SUBJECT with double pipe (||)
    if len(ls_subject_mesh) > 0:
        dc_subject_mesh = '||'.join(ls_subject_mesh)
    
    return dc_subject_mesh



# MARC: 600|610|650; ind2: 3
# REPEAT REPEAT
def get_dc_subject_nalt(record):
    # Default variables
    dc_subject_nalt = ''
    ls_subject_nalt = []

    # Process applicable fields
    for field in ['600','610','650']:
        ls_fields = record.get_fields(field)

        # Process subfields based on INDICATOR
        for subject in ls_fields:
            # Test ind2
            if subject.indicator2 in ['3']:
                
                # Get subfields:
                for sub in ['a','b','v','x','y','z']:
                    results = []
                    if subject.get(sub):
                        results = subject.get_subfields(sub)
                    
                    # Cleanup subfield
                    for val in results:
                        cleaned = val.strip()
                        if cleaned[-1] == '.':
                            cleaned = cleaned[0:-1].strip()

                        # Add CLEANED subject to list of subjects
                        ls_subject_nalt.append(cleaned)

    # Join together SUBJECT with double pipe (||)
    if len(ls_subject_nalt) > 0:
        dc_subject_nalt = '||'.join(ls_subject_nalt)
    
    return dc_subject_nalt



# MARC: 600|610|650; ind2: 0-1
# REPEAT REPEAT
def get_dc_subject_lcsh(record):
    # Default variables
    dc_subject_lcsh = ''
    ls_subject_lcsh = []

    # Process applicable fields
    for field in ['600','610','650']:
        ls_fields = record.get_fields(field)

        # Process subfields based on INDICATOR
        for subject in ls_fields:
            # Test ind2
            if subject.indicator2 in ['0','1']:
                
                # Get subfields:
                for sub in ['a','b','v','x','y','z']:
                    results = []
                    if subject.get(sub):
                        results = subject.get_subfields(sub)
                    
                    # Cleanup subfield
                    for val in results:
                        cleaned = val.strip()
                        if cleaned[-1] == '.':
                            cleaned = cleaned[0:-1].strip()

                        # Add CLEANED subject to list of subjects
                        ls_subject_lcsh.append(cleaned)

    # Join together SUBJECT with double pipe (||)
    if len(ls_subject_lcsh) > 0:
        dc_subject_lcsh = '||'.join(ls_subject_lcsh)
    
    return dc_subject_lcsh



# MARC: 700$a
# REPEAT REPEAT
def get_contributor_committeemember(record):
    # Default variables
    dc_contributor_committeeMember = ''
    ls_700 = []
    ls_committee_member = []

    # Check if there is 700 field in record, if so get all and put into list
    if '700' in record:
        ls_700 = record.get_fields('700')
    
    # Loop through the 700 fields and grab names if RELATOR TERM ($e) has 'committee member'
    for person in ls_700:
        if person.get('e'):
            lower_case_relator = str(person['e']).lower()
            if 'committee member' in lower_case_relator:
                if person.get('a'):
                    initial_name = person['a'].strip()

                    # If last character is ',' remove it
                    if initial_name[-1] == ',':
                        formatted_name = initial_name[0:-1].strip()
                        ls_committee_member.append(formatted_name)

    # Join together COMMITTEE_MEMBERS with double pipe (||) if there are multiple
    if len(ls_committee_member) > 0:
        dc_contributor_committeeMember = '||'.join(ls_committee_member)

    return dc_contributor_committeeMember



# MARC: 700$a
# REPEAT REPEAT
def get_contributor_advisor(record):
    # Default variables
    dc_contributor_advisor = ''
    ls_700 = []
    ls_advisor = []

    # Check if there is 700 field in record, if so get all and put into list
    if '700' in record:
        ls_700 = record.get_fields('700')
    
    # Loop through the 700 fields and grab names if RELATOR TERM ($e) has 'supervisor'
    for person in ls_700:
        if person.get('e'):
            lower_case_relator = person['e'].lower()
            if 'advisor' in lower_case_relator or 'supervisor' in lower_case_relator:
                if person['a'] is not None:
                    initial_name = person['a'].strip()

                    # If last character is ',' remove it
                    if initial_name[-1] == ',':
                        formatted_name = initial_name[0:-1].strip()
                        ls_advisor.append(formatted_name)

    # Join together SUPERVISOR(S) with double pipe (||) if there are multiple
    if len(ls_advisor) > 0:
        dc_contributor_advisor = '||'.join(ls_advisor)

    return dc_contributor_advisor



# MARC: 856$u
def get_handle(record):
    # Default variables
    handle = ''
    ls_856 = []

    # Check if there is 856 field in record, if so get all and put into list
    if '856' in record:
        ls_856 = record.get_fields('856')
    
    # Loop through the 856 fields and grab url if HANDLE link
    for url in ls_856:
        for sub in ['u', 'x']:
            if url.get(sub):
                if 'hdl.handle.net' in url[sub]:
                    handle = url[sub].strip()
                    
                    # Uppercase 'dissertation'
                    if 'dissertations' or 'Dissertations' in handle:
                        handle = handle.replace('Dissertations', 'DISSERTATIONS')
                    
                    # Remove Handle prefixing
                    if "http://hdl.handle.net/" in handle:
                        handle = handle.replace("http://hdl.handle.net/", "")
                    if "https://hdl.handle.net/" in handle: 
                        handle = handle.replace("https://hdl.handle.net/", "")

    return handle



# MARC: 035
# OCLC number
def get_identifier_oclc(record):
    # Default variables
    # Repeat Reapeat. Take first in record
    # Clean up prefixes from number
    dc_identifier_oclc = ''
    oclc_fields = []

    # Search for '035' fields in record
    for field in ['035']:
        oclc_fields = record.get_fields(field)

        # Check that there is at least one of the fields
        if len(oclc_fields) > 0:
            for oclc_number in oclc_fields:

                # Check that subfield 'a' exists
                if 'a' in oclc_number:
                    raw_oclc = ''
                    oclc_numbers = ''

                    raw_oclc = oclc_number['a'].strip()

                    # Clean up raw oclc to get just the numbers
                    re_pattern = r'\D'
                    # Find all non digit characters, replace with nothing (delete)
                    oclc_numbers = re.sub(re_pattern, '', raw_oclc)

                    # Check that there is a number string, if so take it
                    if oclc_numbers != '':
                        dc_identifier_oclc = oclc_numbers
                        break


    return dc_identifier_oclc

#write to csv
marc_source_file = input("Please input the path and filename of your MARC file, ending in .mrc >>")
csv_export_file = input("Please input the filename, ending in .csv >>")
write_db_from_marc(marc_source_file, csv_export_file)