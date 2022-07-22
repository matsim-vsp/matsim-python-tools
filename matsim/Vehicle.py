import xopen
import xml.etree.ElementTree as ET
import pandas as pd
from matsim import utils

class Vehicle:
    def __init__(self, vehicleTypes, vehicles):
        self.vehicleTypes = vehicleTypes
        self.vehicles = vehicles

# TODO definition
def vehicle_reader(filename):
    tree = ET.iterparse(xopen.xopen(filename, 'r'), events=['start','end'])
    
    vehicleTypes = []
    vehicles = []
    
    currentVehicleType = {}
    currentVehicle = {}
    
    for xml_event, elem in tree:
        _, _, elemTag = elem.tag.partition('}')     # Removing xmlns tag from tag name
        
        # VEHICLES
        if elemTag == 'vehicle' and xml_event == 'start':
            utils.parseAttributes(elem, currentVehicle)
        
        elif elemTag == 'vehicle' and xml_event == 'end':
            vehicles.append(currentVehicle)
            currentVehicle = {}
            elem.clear()
            
        # VEHICLETYPES
        elif elemTag == 'vehicleType' and xml_event == 'start':
            utils.parseAttributes(elem, currentVehicleType)
        
        elif elemTag in ['capacity', 'length', 'passengerCarEquivalents', 'networkMode', 'flowEfficiencyFactor']:
            utils.parseAttributes(elem, currentVehicleType)
        
        elif elemTag == 'attribute' and xml_event == 'start':
            currentVehicleType[elem.attrib['name']] = elem.text
        
        elif elemTag == 'vehicleType' and xml_event == 'end':
            vehicleTypes.append(currentVehicleType)
            currentVehicleType = {}
            elem.clear()
        
        
    vehicleTypes = pd.DataFrame.from_records(vehicleTypes)
    vehicles = pd.DataFrame.from_records(vehicles)
    
    return Vehicle(vehicleTypes, vehicles)
        