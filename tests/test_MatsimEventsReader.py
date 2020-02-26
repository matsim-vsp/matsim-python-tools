from unittest import TestCase
from collections import defaultdict

from matsim import Events

actTypes = {'actstart', 'actend', 'departure', 'arrival', 'travelled', 'PersonEntersVehicle', 'PersonLeavesVehicle',
            'vehicle enters traffic', 'vehicle leaves traffic', 'left link', 'entered link'}


class TestEventsHandler(TestCase):

    def test_event_reader(self):
        events = Events.event_reader('tests/test_events.xml.gz')
        count = defaultdict(int)

        for event in events:
            count[event['type']] += 1

        self.assertEqual(11, len(count))
        self.assertEqual(245, count['actend'])
        self.assertEqual(245, count['departure'])
        self.assertEqual(201, count['PersonEntersVehicle'])
        self.assertEqual(201, count['vehicle enters traffic'])
        self.assertEqual(700, count['left link'])
        self.assertEqual(700, count['entered link'])
        self.assertEqual(201, count['vehicle leaves traffic'])
        self.assertEqual(201, count['PersonLeavesVehicle'])
        self.assertEqual(245, count['arrival'])
        self.assertEqual(245, count['actstart'])
        self.assertEqual(44, count['travelled'])

    def test_event_filter_commas(self):
        events = Events.event_reader('tests/test_events.xml.gz', filter='actend,left link')
        count = defaultdict(int)

        for event in events:
            count[event['type']] += 1

        self.assertEqual(2, len(count))
        self.assertEqual(245, count['actend'])
        self.assertEqual(700, count['left link'])

    def test_event_filter_list(self):
        events = Events.event_reader('tests/test_events.xml.gz', filter=['departure'])
        count = defaultdict(int)

        for event in events:
            count[event['type']] += 1

        self.assertEqual(1, len(count))
        self.assertEqual(245, count['departure'])

    def test_event_filter_set(self):
        events = Events.event_reader('tests/test_events.xml.gz', filter= {'actend', 'departure', 'left link'})
        count = defaultdict(int)

        for event in events:
            count[event['type']] += 1

        self.assertEqual(3, len(count))
        self.assertEqual(245, count['actend'])
        self.assertEqual(245, count['departure'])
        self.assertEqual(700, count['left link'])
