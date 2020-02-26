# -*- coding: utf-8 -*-

import pandas as pd

from xopen import xopen

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

from .pb.Wireformat_pb2 import ContentType, PBFileHeader
from .pb.Ids_pb2 import ProtoId
from .pb.Events_pb2 import Event
from .pb.Model_pb2 import Coordinate

PB_VERSION = {
    ContentType.EVENTS: (1, Event)
}


def read_delimited(msg, data, pos=0):
    """ Helper function to read delimited protobuf messages from a buffer """
    result = []
    decoder = _DecodeVarint32

    while pos < len(data):
        m = msg()
        next_pos, pos = decoder(data, pos)
        m.ParseFromString(data[pos:pos + next_pos])
        result.append(m)
        pos += next_pos

    return result


def write_delimited(msgs, write):
    """ Helper function to write delimited protobuf messages """
    encoder = _EncodeVarint
    for msg in msgs:
        buf = msg.SerializeToString()
        encoder(write, len(buf))
        write(buf)


def read_pb(filename):
    """ Read MATSim protobuf file and return content as list """
    decoder = _DecodeVarint32

    with xopen(filename, "rb") as f:
        data = f.read()
        header = PBFileHeader()
        offset, pos = decoder(data, 0)
        header.ParseFromString(data[pos: pos + offset])

        supported, msg = PB_VERSION[header.contentType]

        if supported < header.version:
            raise Exception("Unsupported protobuf version: %d" % header.version)

        return read_delimited(msg, data, pos + offset)


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
            elif type(v) == Coordinate:
                entry["x"] = v.x
                entry["y"] = v.y
            else:
                entry[desc.name] = v

        data.append(entry)

    return pd.DataFrame(data)
