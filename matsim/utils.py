# -*- coding: utf-8 -*-

from google.protobuf.internal.encoder import _EncodeVarint

from xopen import xopen

from .pb.Wireformat_pb2 import ContentType, PBFileHeader
from .pb.Events_pb2 import EventBatch

PB_VERSION = {
    ContentType.EVENTS: (1, EventBatch)
}


def read_pb(filepath):
    """ Read MATSim protobuf file and yield each element """
    with xopen(filepath, "rb") as f:
        header = PBFileHeader()
        offset, pos = _read_varint(f)
        header.ParseFromString(f.read(offset))

        supported, msg = PB_VERSION[header.contentType]
        if supported < header.version:
            raise Exception("Unsupported protobuf version: %d" % header.version)

        for batch in read_delimited(msg, f):
            for ev in batch.events:
                yield ev


def write_delimited(msgs, write):
    """ Helper function to write delimited protobuf messages """
    encoder = _EncodeVarint
    for msg in msgs:
        buf = msg.SerializeToString()
        encoder(write, len(buf))
        write(buf)


def read_delimited(msg_class, stream):
    """ Helper function to read delimited protobuf messages from a buffer """
    while 1:
        m = msg_class()
        length, read = _read_varint(stream)
        if read == 0:
            return
        m.ParseFromString(stream.read(length))
        yield m


def _read_varint(stream):
    """
    read a varint from a stream
    :returns (result, bytes read)
    """
    # Mask for 32bit integer
    mask = (1 << 32) - 1

    result = 0
    shift = 0
    pos = 0
    while 1:
        buf = stream.read(1)
        if not buf:
            return 0, 0

        b = buf[0]
        result |= ((b & 0x7f) << shift)
        pos += 1
        if not (b & 0x80):
            result &= mask
            result = int(result)
            return result, pos
        shift += 7
        if shift >= 64:
            raise RuntimeError('Too many bytes when decoding varint.')
