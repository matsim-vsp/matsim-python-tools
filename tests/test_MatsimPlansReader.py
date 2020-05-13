import pytest
import pathlib

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
    
    plans = Plans.plan_reader(HERE / filepath, selectedPlansOnly = True)

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

