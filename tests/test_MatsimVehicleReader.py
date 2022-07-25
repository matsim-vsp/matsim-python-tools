import pytest
import pathlib

import numpy as np

from matsim import Vehicle

HERE = pathlib.Path(__file__).parent

files = ['output_allVehicles.xml.gz']


@pytest.mark.parametrize('filepath', files)
def test_vehicle_reader(filepath):
    vehicle_dataframes = Vehicle.vehicle_reader(HERE / filepath)
    
    vehicle_types = vehicle_dataframes.vehicle_types
    vehicles = vehicle_dataframes.vehicles
    vehicles_counts_dataframes = vehicles['type'].value_counts()
    
    expected_vehicle_types_columns = ['id', 'accessTimeInSecondsPerPerson', 'doorOperationMode', 'egressTimeInSecondsPerPerson', 'seats', 'standingRoomInPersons', 'length', 'width', 'pce', 'networkMode', 'factor']
    expected_vehicles_columns = ['id','type']
    EXPECTED_VEHICLETYPES_ROW_0_RESULT = {
        'id': 'Bus',
        'accessTimeInSecondsPerPerson': 0.5,
        'doorOperationMode': 'serial',
        'egressTimeInSecondsPerPerson': 0.5,
        'seats': 70,
        'standingRoomInPersons': 0,
        'length': 18.0,
        'width': 2.5,
        'pce': 2.8,
        'networkMode': 'car',
        'factor': 1.0
    }
        
    # Checking total lengths
    assert len(vehicle_types) == 4
    assert len(vehicles) == 113
    
    # Checking vehicles types number of occurrences
    assert vehicles_counts_dataframes.defaultVehicleType == 44
    assert vehicles_counts_dataframes.Bus == 43
    assert vehicles_counts_dataframes.Tram == 25
    assert vehicles_counts_dataframes.Rail == 1
    
    assert vehicle_types.iloc[0].to_dict() == EXPECTED_VEHICLETYPES_ROW_0_RESULT
    np.testing.assert_array_equal(expected_vehicle_types_columns, vehicle_types.keys())
    np.testing.assert_array_equal(expected_vehicles_columns, vehicles.keys())