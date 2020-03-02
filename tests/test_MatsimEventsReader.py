import pytest
import pathlib

from collections import defaultdict

from matsim import Events

HERE = pathlib.Path(__file__).parent

actTypes = {'actstart', 'actend', 'departure', 'arrival', 'travelled', 'PersonEntersVehicle', 'PersonLeavesVehicle',
            'vehicle enters traffic', 'vehicle leaves traffic', 'left link', 'entered link'}

files = ['output_events.xml.gz', 'output_events.pb.gz', 'output_events.ndjson.gz']


@pytest.mark.parametrize('filepath', files)
def test_event_reader(filepath):
    events = Events.event_reader(HERE / filepath)
    count = defaultdict(int)

    for event in events:
        count[event['type']] += 1

    assert len(count) == 10
    assert count['actend'] == 201
    assert count['departure'] == 201
    assert count['PersonEntersVehicle'] == 201
    assert count['vehicle enters traffic'] == 201
    assert count['left link'] == 700
    assert count['entered link'] == 700
    assert count['vehicle leaves traffic'] == 201
    assert count['PersonLeavesVehicle'] == 201
    assert count['arrival'] == 201
    assert count['actstart'] == 201


@pytest.mark.parametrize('filepath', files)
def test_event_filter_commas(filepath):
    events = Events.event_reader(HERE / filepath, types='actend,left link')
    count = defaultdict(int)

    for event in events:
        count[event['type']] += 1

    assert len(count) == 2
    assert count['actend'] == 201
    assert count['left link'] == 700


@pytest.mark.parametrize('filepath', files)
def test_event_filter(filepath):
    events = Events.event_reader(HERE / filepath, types={'actend', 'departure', 'left link'})
    count = defaultdict(int)

    for event in events:
        count[event['type']] += 1

    assert len(count) == 3
    assert count['actend'] == 201
    assert count['departure'] == 201
    assert count['left link'] == 700


def test_non_existent():
    with pytest.raises(IOError):
        events = Events.event_reader("not existing.xml")
        for _ in events:
            pass
