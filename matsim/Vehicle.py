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
def vehicle_reader(filename, convert_dataframes_types=True):
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
        
        # ATTRIBUTES
        elif elem_tag == 'attribute' and xml_event == 'start':
            current_vehicle_type[elem.attrib['name']] = elem.text
        
        # LENGTH / WIDTH
        elif elem_tag in ['length', 'width'] and xml_event == 'start':
            current_vehicle_type[elem_tag] = elem.attrib['meter']
        
        # VEHICLETYPES
        elif elem_tag == 'vehicleType' and xml_event == 'end':
            vehicle_types.append(current_vehicle_type)
            current_vehicle_type = {}
            elem.clear()
            is_parsing_vehicle_type = False
        
        # EVERYTHING ELSE
        elif is_parsing_vehicle_type and elem_tag not in ['attribute', 'length', 'width']:
            utils.parse_attributes(elem, current_vehicle_type)

    
    vehicle_types = pd.DataFrame.from_records(vehicle_types)
    vehicles = pd.DataFrame.from_records(vehicles)
    
    if convert_dataframes_types:
        try:
            vehicle_types['accessTimeInSecondsPerPerson'] = vehicle_types['accessTimeInSecondsPerPerson'].astype(float)
            vehicle_types['egressTimeInSecondsPerPerson'] = vehicle_types['egressTimeInSecondsPerPerson'].astype(float)
            vehicle_types['seats'] = vehicle_types['seats'].astype(int)
            vehicle_types['standingRoomInPersons'] = vehicle_types['standingRoomInPersons'].astype(int)
            vehicle_types['length'] = vehicle_types['length'].astype(float)
            vehicle_types['width'] = vehicle_types['width'].astype(float)
            vehicle_types['pce'] = vehicle_types['pce'].astype(float)
            vehicle_types['factor'] = vehicle_types['factor'].astype(float)
        except KeyError:
            print('dataframe types conversion failed')
    
    return Vehicle(vehicle_types, vehicles)
        