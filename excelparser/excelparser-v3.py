"""
Created on Fri Jun 29 17:31:36 2018

@author: Syamantak
"""

# Import `pyexcel`
import pyexcel

filename="TestData.xlsx"
#file_name is the input into pyexcel
    
def read():
    
    # Get an array from the data
    my_array = pyexcel.get_array(file_name=filename)
    print("Printing array from spreadsheet" + '\n')
    print(my_array)
    print('\n')
    
    # Import `OrderedDict` module 
    from pyexcel._compact import OrderedDict
    
    # Get your data in an ordered dictionary of lists
    my_dict = pyexcel.get_book(file_name=filename, name_columns_by_row=0)
    print("Printing book of lists:" + '\n')
    print(my_dict)
    print('\n')
    
    # Get your data in an ordered dictionary of lists
    dict_1 = pyexcel.get_book_dict(file_name=filename, name_columns_by_row=0)
    print("Printing dictionary of lists:" + '\n')
    print(dict_1)
    print('\n')
    
    # Retrieve the records of the file
    patientRecords = pyexcel.get_records(file_name=filename)
    print("Printing all the patient records:" + '\n')
    print(patientRecords)


#enter commands here
read()