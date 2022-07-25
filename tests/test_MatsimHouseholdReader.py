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
    
    EXPECTED_TOTAL_HOUSEHOLDS = 112
    EXPECTED_HOUSEHOLD_COLUMNS = ['id', 'bikeAvailability', 'carAvailability', 'censusId', 'household_income', 'members']
    ROW_84_EXPECTED_RESULT = {
        'id': 2293,
        'bikeAvailability': 'none',
        'carAvailability': 'some',
        'censusId': 503,
        'household_income': 3916.708525944572,
        'members' : [5427, 5428, 5429, 5430, 5431]
    }
    
    
    assert len(household_dataframe) == EXPECTED_TOTAL_HOUSEHOLDS
    assert household_dataframe.iloc[84].to_dict() == ROW_84_EXPECTED_RESULT
    np.testing.assert_array_equal(EXPECTED_HOUSEHOLD_COLUMNS, household_dataframe.keys())