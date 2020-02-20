class TripEventHandler:

    def __init__(self, main_mode_identifier, person_filter):
        self.drivers = set()
        self.persons = {}
        self.stuck = set()
        self.main_mode_identifier = main_mode_identifier
        self.person_filter = person_filter
        self.handlers = {
            'actstart': self.on_activity_start, 'actend': self.on_activity_end, 'departure': self.on_person_departure,
            'arrival': self.on_person_arrival, 'stuck': self.on_person_stuck
        }

    def on_event(self, time, event_type, attrs):
        if event_type in self.handlers:
            self.handlers[event_type](time, attrs)

    def on_transit_driver_starts(self, time, attrs):
        self.drivers.add(attrs['id'])

    def on_activity_end(self, time, attrs):

        person_id = attrs['person']

        if self.is_stage_activity(attrs['actType']) or person_id in self.drivers or not self.person_filter(person_id):
            return

        trip = Trip()
        trip._departure_time = time
        trip._departure_link = attrs['link']
        if 'facility' in attrs:
            trip._departure_facility = attrs['facility']

        self.persons.setdefault(person_id, []).append(trip)

    def on_activity_start(self, time, attrs):

        person_id = attrs['person']

        if self.is_stage_activity(attrs['actType']) or id not in self.persons:
            return

        trip = self.persons[person_id][-1]  # get the last trip of the list associated with the person id
        trip._arrival_link = attrs['link']
        trip._arrival_time = time
        if 'facility' in attrs:
            trip._arrival_facility = attrs['facility']

    def on_person_arrival(self, time, attrs):
        pass

    def on_person_departure(self, time, attrs):
        pass

    def on_person_stuck(self, time, attrs):
        pass

    def is_stage_activity(self, type):
        return type.endswith("interaction")


class Trip:

    def __init__(self):
        self._departure_time = -1
        self._departure_link = ''
        self._departure_facility = ''
        self._arrival_time = -1
        self._arrival_link = ''
        self._arrival_facility = ''
        self._main_mode = ''
        self._legs = []

    @property
    def departure_time(self):
        return self._departure_time

    @property
    def departure_link(self):
        return self._departure_link

    @property
    def departure_facility(self):
        return self._departure_facility

    @property
    def arrival_time(self):
        return self._departure_time

    @property
    def arrival_link(self):
        return self._arrival_link

    @property
    def arrival_facility(self):
        return self._arrival_facility

    @property
    def main_mode(self):
        return self._main_mode

    @property
    def legs(self):
        return self._legs
