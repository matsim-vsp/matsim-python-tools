import gzip
import pathlib

import pytest

from matsim import Plans
from matsim import writers

HERE = pathlib.Path(__file__).parent

files = ['initial_plans.xml.gz']


@pytest.mark.parametrize('filepath', files)
def test_plan_writer(filepath):
    plans = Plans.plan_reader(HERE / filepath)

    with gzip.open("out_"+filepath, 'wb+') as f_write:
        writer = writers.PopulationWriter(f_write)
        writer.start_population(attributes={"coordinateReferenceSystem": "GK4"})

        for person, plan in plans:
            id = person.attrib['id']
            writer.start_person(id)
            writer.start_plan(selected=plan.attrib['selected'] == 'yes')
            activities = [e for e in plan if e.tag == 'activity']
            legs = [e for e in plan if e.tag == 'leg']
            for act, leg in zip(activities[:-1], legs):
                writer.add_activity(
                    type=act.attrib['type'], x=act.attrib['x'], y=act.attrib['y'],
                    end_time=time(act.attrib['end_time']))
                writer.add_leg(mode='walk' if leg.attrib['mode'] == 'walk_main' else leg.attrib['mode'])
            writer.add_activity(
                type=activities[-1].attrib['type'], x=activities[-1].attrib['x'], y=activities[-1].attrib['y'],
                end_time=time(activities[-1].attrib['end_time']))
            writer.end_plan()
            writer.end_person()

        writer.end_population()

    with gzip.open("out_" + filepath) as f_orig:
        with gzip.open(HERE / filepath) as f_new:
            assert f_orig.readlines() == f_new.readlines(), "input and output files don't match!"


def time(x):
    return sum(int(t)*f for t, f in zip(x.split(':'), (3600, 60, 1)))
