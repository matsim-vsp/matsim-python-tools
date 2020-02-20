from unittest import TestCase

from matsim_tools import Events

actTypes = {'actstart', 'actend', 'departure', 'arrival', 'travelled', 'PersonEntersVehicle', 'PersonLeavesVehicle',
            'vehicle enters traffic', 'vehicle leaves traffic', 'left link', 'entered link'}


class TestEventsHandler(TestCase):

    def test_parsing(self):
        callback = self.callback
        Events.read('test_events.xml.gz', callback)

    def callback(self, time, type, attrs):
        self.assertLessEqual(21510, time)
        self.assertTrue(type in actTypes, 'event_type ' + type + ' was not in act types')
