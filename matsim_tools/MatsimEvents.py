class Event:

    def __init__(self, time):
        self.time = time


class LinkEvent(Event):

    def __init__(self, time, attrs):
        super().__init__(time)
        self.vehicle_id = attrs['vehicle']
        self.link_id = attrs['link']


class LinkEnterEvent(LinkEvent):

    def __init__(self, time, attrs):
        super().__init__(time, attrs)


class LinkLeaveEvent(LinkEvent):

    def __init__(self, time, attrs):
        super().__init__(time, attrs)
