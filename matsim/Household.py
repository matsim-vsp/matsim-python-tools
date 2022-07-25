import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Household:
    def __init__(self, households):
        self.households = households

def houshold_reader(filename):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    housholds = []
    current_persons = []
    current_household = {}
    
    for xml_event, elem in tree:
        _, _, elem_tag = elem.tag.partition('}')     # Removing xmlns tag from tag name
        
        if elem_tag == 'household':
            if xml_event == 'start':
                utils.parse_attributes(elem, current_household)
            else:
                current_household['persons'] = current_persons
                housholds.append(current_household)
                current_household = {}
                current_persons = []
                elem.clear()

        elif elem_tag == 'attribute':
            current_household[elem.attrib['name']] = elem.text
        
        elif elem_tag == 'personId' and xml_event == 'start':
            current_persons.append(elem.attrib['refId'])
    
    housholds = pd.DataFrame.from_records(housholds)
    return Household(housholds)
