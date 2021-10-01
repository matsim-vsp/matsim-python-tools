# -*- coding: utf-8 -*-

from pathlib import Path
from collections.abc import Iterable
import xml.etree.ElementTree as ET
import json

from xopen import xopen

from .pb.Ids_pb2 import ProtoId
from .pb.Model_pb2 import Coordinate

from matsim.utils import read_pb


def event_reader(filepath, types=None):
    """ Reads an events file in any of the supported formats (xml, json, pb) and yields each contained event.
        Each event will be generated as a dictionary of attribute key/value pairs.

    :param filepath path to the file
    :param types event types to return. Can be an iterable, or comma-separated string. Default None returns all events.
    :returns generator of events from the specified file
    :rtype Iterable[dict]
    """
    # set up event filter - so that we only yield useful events
    if types is None:
        keep = None
    elif isinstance(types, str):
        keep = set(types.split(','))
    elif isinstance(types, Iterable):
        keep = set(types)
    else:
        raise ValueError("Invalid argument for types: %s" % type(types))

    if isinstance(filepath, Path):
        filepath = str(filepath)

    if '.xml' in filepath:
        reader = _event_reader_xml
    elif '.pb' in filepath:
        reader = _event_reader_pb
    elif '.ndjson' in filepath:
        reader = _event_reader_json
    else:
        raise ValueError('Format of %s unknown or not supported' % filepath)

    for event in reader(filepath):
        # skip events we don't care about
        if keep and not event['type'] in keep:
            continue

        yield event


def _event_reader_xml(filepath):
    """ Any content text of the XML element itself is dropped, as MATSim events are attribute-only. """
    with xopen(filepath) as f:
        tree = ET.iterparse(f)
        try:
            for xml_event, elem in tree:
                attributes = elem.attrib

                if elem.tag == 'event':
                    # got one! yield the event to the caller
                    attributes['time'] = float(attributes['time'])
                    yield attributes

                # free memory. Otherwise the data is kept in memory and we loose the advantage of streaming
                elem.clear()

        except Exception as e:
            # Why am I catching this exception instead of allowing it to propagate up?
            # Because some event files (**coughswitzerland**) are badly formed and do not contain
            # the closing </events> tag at the end of the file. If we don't trap that error, the
            # entire analysis fails.
            print('*** XML ERROR:', e)


def _event_reader_pb(filepath, convert=True):
    for event in read_pb(filepath):
        # the conversion nullifies protobufs performance advantage
        if convert:
            yield _convert_pb_event(event)
        else:
            yield event

# Mapping of protobuf types to names
MAPPING = {'activityEnd': 'actend', 'personDeparture': 'departure', 'personEntersVehicle': 'PersonEntersVehicle',
           'vehicleEntersTraffic': 'vehicle enters traffic', 'linkLeave': 'left link', 'linkEnter': 'entered link',
           'vehicleLeavesTraffic': 'vehicle leaves traffic', 'personLeavesVehicle': 'PersonLeavesVehicle',
           'personalArrival': 'arrival', 'activityStart': 'actstart'}


def _convert_pb_event(event):
    entry = {}
    ev_type = event.WhichOneof("type")
    entry["type"] = MAPPING.get(ev_type, ev_type)
    for (desc, v) in event.ListFields():
        if ev_type == desc.name:
            for (attr, evValue) in v.ListFields():
                if type(evValue) == ProtoId:
                    entry[attr.name] = evValue.id

        elif type(v) == Coordinate:
            entry["x"] = v.x
            entry["y"] = v.y
        else:
            entry[desc.name] = v

    return entry


def _event_reader_json(filepath):
    with xopen(filepath) as f:
        for line in f:
            yield json.loads(line)
