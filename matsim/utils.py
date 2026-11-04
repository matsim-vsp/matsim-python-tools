# -*- coding: utf-8 -*-

import glob
import os

from google.protobuf.internal.encoder import _EncodeVarint

from xopen import xopen

from .pb.Wireformat_pb2 import ContentType, PBFileHeader
from .pb.Events_pb2 import EventBatch

PB_VERSION = {
    ContentType.EVENTS: (1, EventBatch)
}

# Suffixes of compressed files that MATSim may write, in the order they are tried
COMPRESSION_SUFFIXES = ("", ".zst", ".gz", ".lz4", ".bz2", ".xz")


def _strip_compression(path: str) -> str:
    for suffix in COMPRESSION_SUFFIXES[1:]:
        if path.endswith(suffix):
            return path[:-len(suffix)]

    return path


def find_file(path) -> str:
    """ Find a file, which may exist uncompressed or with any compression suffix.
    E.g. for 'output_plans.xml' or 'output_plans.xml.gz' also 'output_plans.xml.zst' is found.

    :raises FileNotFoundError: if no such file exists
    """
    path = str(path)
    if os.path.exists(path):
        return path

    base = _strip_compression(path)
    for suffix in COMPRESSION_SUFFIXES:
        if os.path.exists(base + suffix):
            return base + suffix

    raise FileNotFoundError("Could not find %s with any of the suffixes %s" % (base, COMPRESSION_SUFFIXES))


def glob_file(directory, pattern: str) -> str:
    """ Find a file matching a glob pattern in a directory, which may exist uncompressed or with any compression suffix.
    E.g. pattern '*.output_trips.csv' finds 'run.output_trips.csv.zst'.

    :raises FileNotFoundError: if no such file exists
    """
    base = _strip_compression(pattern)
    for suffix in COMPRESSION_SUFFIXES:
        matches = sorted(glob.glob(os.path.join(str(directory), base + suffix)))
        if matches:
            return matches[0]

    raise FileNotFoundError("No %s file found in %s" % (base, directory))


# Parses attributes of an element and adds them to the given dictionary
def parse_attributes(elem, dict):
    for attrib in elem.attrib:
        dict[attrib] = elem.attrib[attrib]
    return dict


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
