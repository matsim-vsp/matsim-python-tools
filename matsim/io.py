# -*- coding: utf-8 -*-

import pandas as pd

from xopen import xopen

from .pb.Wireformat_pb2 import ContentType, PBFileHeader
from .pb.Ids_pb2 import ProtoId
from .pb.Events_pb2 import EventBatch
from .pb.Model_pb2 import Coordinate

from .utils import _read_varint, read_delimited

PB_VERSION = {
    ContentType.EVENTS: (1, EventBatch)
}

def read_pb(filename):
    """ Read MATSim protobuf file and return content as list """
    with xopen(filename, "rb") as f:
        header = PBFileHeader()
        offset, pos = _read_varint(f)
        header.ParseFromString(f.read(offset))

        supported, msg = PB_VERSION[header.contentType]
        if supported < header.version:
            raise Exception("Unsupported protobuf version: %d" % header.version)

        for batch in read_delimited(msg, f):
            for ev in batch.events:
                yield ev


def to_pandas(messages):
    """ Convert protobuf messages to pandas dataframe """
    data = []

    for m in messages:
        entry = {}
        ev_type = m.WhichOneof("type")
        entry["type"] = ev_type
        for (desc, v) in m.ListFields():
            if ev_type == desc.name:
                for (attr, evValue) in v.ListFields():
                    if type(evValue) == ProtoId:
                        entry[attr.name] = evValue.id

                # check for generic event?

            elif type(v) == Coordinate:
                entry["x"] = v.x
                entry["y"] = v.y
            else:
                entry[desc.name] = v

        data.append(entry)

    return pd.DataFrame(data)
