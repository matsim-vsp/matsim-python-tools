import pytest
import pathlib
import numpy as np
from matsim import Household

HERE = pathlib.Path(__file__).parent

files = ['output_households.xml.gz']

@pytest.mark.parametrize('filepath', files)
def test_vehicle_reader(filepath):
    household_reader = Household.houshold_reader(HERE / filepath)
    
    household_dataframe = household_reader.households
    
    print(household_dataframe)