import pytest
import pathlib

from matsim import Vehicle

HERE = pathlib.Path(__file__).parent

# files = ['plans_full.xml.gz', 'plans_empty.xml.gz']


# @pytest.mark.parametrize('filepath', files)
def test_vehicle_reader():
    vehicleDataframes = Vehicle.vehicle_reader('C:/Users/raapoto/Documents/Furbain/data/simulation_output/output_allVehicles.xml.gz')
    
    print('\n')
    print(vehicleDataframes.vehicleTypes.head())
    print(vehicleDataframes.vehicles.head(10))