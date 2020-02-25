from unittest import TestCase

from matsim.Events import LinkEnterEvent, LinkLeaveEvent


class TestMatsimEvents(TestCase):

    def test_linkEnterEvent(self):
        time = 1
        vehicleId = '1'
        linkId = 'some-link-id'
        attrs = {'vehicle': vehicleId, 'link': linkId, 'should-ignore': 'this-value'}

        event = LinkEnterEvent(time, attrs)

        self.assertEqual(time, event.time)
        self.assertEqual(vehicleId, event.vehicle_id)
        self.assertEqual(linkId, event.link_id)

    def test_linkLeaveEvent(self):
        time = 1
        vehicleId = '1'
        linkId = 'some-link-id'
        attrs = {'vehicle': vehicleId, 'link': linkId, 'should-ignore': 'this-value'}

        event = LinkLeaveEvent(time, attrs)

        self.assertEqual(time, event.time)
        self.assertEqual(vehicleId, event.vehicle_id)
        self.assertEqual(linkId, event.link_id)
