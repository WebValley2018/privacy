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

    def get_data_type(self, index):
        data = self.get_data()
        types={}
        for d in data:
            t = str(type(d[index])).split("'")[1]
            if not t in types:
                types[t]=1
            else:
                types[t] = types[t] + 1
        max_t=0
        max_t_val = None
        for t, c in types.items():
            if c>max_t:
                max_t = c
                max_t_val = t
        return max_t_val
