#import utilities
import sys
# import pandas as pd

def search_for_nonmatches(my_file, source_file, save_file):
    file_for_numbers = open(my_file)
    file_all_numbers = open(source_file)
    file_save = open(save_file, 'x')
    for number in file_for_numbers:
        if number in file_all_numbers:
             print("More Oclcs")
        else:
            make_note = open(save_file, 'a')
            make_note.write(number)


file_to_compare = input("Please input the file with information you want to test")
base_file = input("Please input the file with data you wish to compare against")
output_file = "RESULTS.txt"
search_for_nonmatches(file_to_compare, base_file, output_file)