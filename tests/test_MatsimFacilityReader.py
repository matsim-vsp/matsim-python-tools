import pytest
import pathlib

import numpy as np

from matsim import Facility

HERE = pathlib.Path(__file__).parent

files = ['output_facilities.xml.gz']


@pytest.mark.parametrize('filepath', files)
def test_vehicle_reader(filepath):
    facilityReader = Facility.facility_reader(HERE / filepath)
    facilities_dataframe = facilityReader.facilities
    
    facilities_count_types_dataframe = facilities_dataframe['type'].value_counts()
    
    EXPECTED_TOTAL_FACILITIES = 1112
    EXPECTED_EDUCATION_FACILITIES_COUNT = 115
    EXPECTED_HOME_FACILITIES_COUNT = 45
    EXPECTED_OUTSIDE_FACILITIES_COUNT = 404
    EXPECTED_OTHER_FACILITIES_COUNT = 483
    EXPECTED_LEISURE_FACILITIES_COUNT = 13
    EXPECTED_SHOP_FACILITIES_COUNT = 24
    EXPECTED_WORK_FACILITIES_COUNT = 28
    
    EXPECTED_DATAFRAME_KEYS = ['id', 'linkId', 'x', 'y', 'type']

    assert len(facilities_dataframe) == EXPECTED_TOTAL_FACILITIES
    assert facilities_count_types_dataframe.education == EXPECTED_EDUCATION_FACILITIES_COUNT
    assert facilities_count_types_dataframe.home == EXPECTED_HOME_FACILITIES_COUNT
    assert facilities_count_types_dataframe.outside == EXPECTED_OUTSIDE_FACILITIES_COUNT
    assert facilities_count_types_dataframe.other == EXPECTED_OTHER_FACILITIES_COUNT
    assert facilities_count_types_dataframe.leisure == EXPECTED_LEISURE_FACILITIES_COUNT
    assert facilities_count_types_dataframe.shop == EXPECTED_SHOP_FACILITIES_COUNT
    assert facilities_count_types_dataframe.work == EXPECTED_WORK_FACILITIES_COUNT
    
    np.testing.assert_array_equal(EXPECTED_DATAFRAME_KEYS, facilities_dataframe.keys())