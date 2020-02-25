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

    def on_event(self, time, type, attrs):
        if (type in self.handlers):
            self.handlers[type](time, attrs)

    def on_transit_driver_starts(self, time, attrs):
        self.drivers.add(attrs['id'])

    def on_activity_end(self, time, attrs):
        if self.is_stage_activity(attrs['acttype']) or attrs['id'] in self.drivers or not self.person_filter(
                attrs['id']):
            return

    def on_activity_start(self, time, attrs):
        pass

    def on_person_arrival(self, time, attrs):
        pass

    def on_person_departure(self, time, attrs):
        pass

    def on_person_stuck(self, time, attrs):
        pass

    def is_stage_activity(self, type):
        return type.endswith("interaction")


