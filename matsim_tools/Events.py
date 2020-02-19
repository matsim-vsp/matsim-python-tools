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


import gzip
from xml import sax
from xml.sax import ContentHandler


class EventsHandler(ContentHandler):

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate

    def startDocument(self):
        super().startDocument()

    def endDocument(self):
        super().endDocument()

    def startElement(self, name, attrs):
        if name == 'event':
            time = float(attrs['time'])
            type = attrs['type']

            self.delegate(time, type, attrs)

    def characters(self, content):
        pass  # don't pass characters to save memory


def read(filepath, callback):
    handler = EventsHandler(callback)
    with gzip.open(filepath) as file:
        sax.parse(file, handler)
