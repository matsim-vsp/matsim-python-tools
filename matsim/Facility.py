import this
import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Facility:
    def __init__(self, facilities):
        self.facilities = facilities

def get_attributes_in_elem(elem):
    pass

def facility_reader(filename):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    facilities = []
    current_facility = {}
    
    for xml_event, elem in tree:
        if elem.tag == 'facility':
            if xml_event == 'start':
                utils.parse_attributes(elem, current_facility)
            else:
                facilities.append(current_facility)
                current_facility = {}
                elem.clear()

        else:
            utils.parse_attributes(elem, current_facility)
            
    
    facilities = pd.DataFrame.from_records(facilities)
    return Facility(facilities)