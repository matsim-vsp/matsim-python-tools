import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Facility:
    def __init__(self):
        pass

def get_attributes_in_elem(elem):
    pass

def facility_reader(filename):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    facilities = []
    