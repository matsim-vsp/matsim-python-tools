import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Vehicle:
    def __init__(self, vehicle_types, vehicles):
        self.vehicle_types = vehicle_types
        self.vehicles = vehicles

# Returns vehicle_types and vehicles dataframes
# <vehicleType> attributes and children attributes are récursively added to the dataframe
def vehicle_reader(filename):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    vehicle_types = []
    vehicles = []
    
    current_vehicle_type = {}
    current_vehicle = {}
    
    is_parsing_vehicle_type = False
    
    for xml_event, elem in tree:
        _, _, elem_tag = elem.tag.partition('}')     # Removing xmlns tag from tag name
        
        # VEHICLES
        if elem_tag == 'vehicle' and xml_event == 'start':
            utils.parse_attributes(elem, current_vehicle)
        
        elif elem_tag == 'vehicle' and xml_event == 'end':
            vehicles.append(current_vehicle)
            current_vehicle = {}
            elem.clear()
            
        # VEHICLETYPES
        elif elem_tag == 'vehicleType' and xml_event == 'start':
            utils.parse_attributes(elem, current_vehicle_type)
            is_parsing_vehicle_type = True
        
        elif elem_tag == 'attribute' and xml_event == 'start':
            current_vehicle_type[elem.attrib['name']] = elem.text
        
        elif elem_tag in ['length', 'width'] and xml_event == 'start':
            current_vehicle_type[elem_tag] = elem.attrib['meter']
        
        elif elem_tag == 'vehicleType' and xml_event == 'end':
            vehicle_types.append(current_vehicle_type)
            current_vehicle_type = {}
            elem.clear()
            is_parsing_vehicle_type = False
         
        elif is_parsing_vehicle_type and elem_tag not in ['attribute', 'length', 'width']:
            utils.parse_attributes(elem, current_vehicle_type)
        
        
    vehicle_types = pd.DataFrame.from_records(vehicle_types)
    vehicles = pd.DataFrame.from_records(vehicles)
    
    return Vehicle(vehicle_types, vehicles)
        