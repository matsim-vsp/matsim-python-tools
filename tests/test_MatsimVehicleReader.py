from isort import file
import pytest
import pathlib

import numpy as np

from matsim import Vehicle

HERE = pathlib.Path(__file__).parent

files = ['output_allVehicles.xml.gz']


@pytest.mark.parametrize('filepath', files)
def test_vehicle_reader(filepath):
    vehicleDataframes = Vehicle.vehicle_reader(HERE / filepath)
    
    vehicleTypes = vehicleDataframes.vehicleTypes
    vehicles = vehicleDataframes.vehicles
    vehiclesCountsDf = vehicles['type'].value_counts()
    
    expectedVehicleTypesColumns = ['id', 'accessTimeInSecondsPerPerson', 'doorOperationMode', 'egressTimeInSecondsPerPerson', 'seats', 'standingRoomInPersons', 'length', 'width', 'pce', 'networkMode', 'factor']
    expectedVehiclesColumns = ['id','type']
        
    # Checking total lengths
    assert len(vehicleTypes) == 4
    assert len(vehicles) == 113
    
    # Checking vehicles types number of occurrences
    assert vehiclesCountsDf.defaultVehicleType == 44
    assert vehiclesCountsDf.Bus == 43
    assert vehiclesCountsDf.Tram == 25
    assert vehiclesCountsDf.Rail == 1
        
    np.testing.assert_array_equal(expectedVehicleTypesColumns, vehicleTypes.keys())
    np.testing.assert_array_equal(expectedVehiclesColumns, vehicles.keys())