"""
Created on Fri Jun 29 17:31:36 2018

@author: Syamantak
@author: eutampieri
"""

# Import `pyexcel`
import pyexcel
from pyexcel._compact import OrderedDict


class Excel:
    def __init__(self, fn):
        self.filename = fn
    
    def get_columns(self):
        # Get an array from the data
        return pyexcel.get_array(file_name=self.filename)[0]

    def get_data(self):
        # Retrieve the records of the file
        return pyexcel.get_array(file_name=self.filename)[1:]
