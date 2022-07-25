import pytest
import pathlib
import pandas as pd
import numpy as np
from collections import defaultdict

from matsim import Plans

HERE = pathlib.Path(__file__).parent

files = ['plans_full.xml.gz', 'plans_empty.xml.gz']


@pytest.mark.parametrize('filepath', files)
def test_plan_reader(filepath):
    count_people = defaultdict(int)
    count_plans = defaultdict(int)
    
    plans = Plans.plan_reader(HERE / filepath)

    for person,plan in plans:
        count_people[person.attrib['id']] += 1
        if plan: count_plans[person.attrib['id']] += 1

    if filepath == 'plans_empty.xml.gz':
        assert len(count_people) == 3
        assert len(count_plans) == 0
    else: 
        assert len(count_people) == 3
        assert len(count_plans) == 3
        assert count_plans['100024301'] == 2


@pytest.mark.parametrize('filepath', files)
def test_plan_reader_selected_only(filepath):
    count_people = defaultdict(int)
    count_plans = defaultdict(int)
    
    plans = Plans.plan_reader(HERE / filepath, selected_plans_only = True)

    for person,plan in plans:
        print(person)
        count_people[person.attrib['id']] += 1
        if plan: count_plans[person.attrib['id']] += 1

    if filepath == 'plans_empty.xml.gz':
        assert len(count_people) == 3
        assert len(count_plans) == 0
    else: 
        assert len(count_people) == 3
        assert len(count_plans) == 3
        assert count_plans['100024301'] == 1
        

def test_non_existent():
    with pytest.raises(IOError):
        plans = Plans.plan_reader("not existing.xml")
        for _ in plans:
            pass

@pytest.mark.parametrize('filepath', files)
def test_plan_reader_dataframe(filepath):
    selected_plans_cases = [True, False]
    
    for selected_plans_only in selected_plans_cases:
        plans_dataframes = Plans.plan_reader_dataframe(HERE / filepath, selected_plans_only)
        
        persons = plans_dataframes.persons
        plans = plans_dataframes.plans
        activities = plans_dataframes.activities
        legs = plans_dataframes.legs
        routes = plans_dataframes.routes
        
        persons_expected_columns_full = ['id', 'home-activity-zone', 'subpopulation']
        persons_expected_columns_empty = ['id', 'age', 'district', 'homeId', 'homeX', 'homeY', 'sex']
        plans_expected_columns = ['id', 'person_id', 'score', 'selected']
        activites_expected_columns = ['id', 'plan_id', 'type', 'link', 'x', 'y', 'end_time', 'zoneId', 'max_dur', 'cemdapStopDuration_s']
        legs_expected_columns = ['id', 'plan_id', 'mode', 'dep_time']
        routes_expected_columns = ['id', 'leg_id', 'value', 'type', 'start_link', 'end_link', 'trav_time', 'distance', 'vehicleRefId']
        
        if filepath == 'plans_empty.xml.gz':
            assert len(persons) == 3
            assert len(plans) == 0
            assert len(activities) == 0
            assert len(legs) == 0
            assert len(routes) == 0
            np.testing.assert_array_equal(persons_expected_columns_empty, persons.keys())
            np.testing.assert_array_equal([], plans.keys())
            np.testing.assert_array_equal([], activities.keys())
            np.testing.assert_array_equal([], legs.keys())
            np.testing.assert_array_equal([], routes.keys())

        else:
            assert len(persons) == 3
            
            if selected_plans_only:
                assert len(plans) == 3
            else:
                assert len(plans) == 4
            
            assert len(activities) == 39
            assert len(legs) == 35
            assert len(routes) == 35
            np.testing.assert_array_equal(persons_expected_columns_full, persons.keys())
            np.testing.assert_array_equal(plans_expected_columns, plans.keys())
            np.testing.assert_array_equal(activites_expected_columns, activities.keys())
            np.testing.assert_array_equal(legs_expected_columns, legs.keys())
            np.testing.assert_array_equal(routes_expected_columns, routes.keys())