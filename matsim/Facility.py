import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Facility:
    def __init__(self, facilities):
        self.facilities = facilities

# Returns facilities as a dataframe
def facility_reader(filename, convert_dataframes_types=True):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    facilities = []
    current_facility = {}
    
    for xml_event, elem in tree:
        # FACILITY
        if elem.tag == 'facility':
            if xml_event == 'start':
                utils.parse_attributes(elem, current_facility)
            else:
                facilities.append(current_facility)
                current_facility = {}
                elem.clear()

        # EVERYTHING ELSE
        else:
            utils.parse_attributes(elem, current_facility)
            
    # Convert to dataframe and converts columns types
    facilities = pd.DataFrame.from_records(facilities)
    if convert_dataframes_types:
        try:
            facilities['x'] = facilities['x'].astype(float)
            facilities['y'] = facilities['y'].astype(float)
        except KeyError:
            print('dataframe types convertion failed')
    
    return Facility(facilities)