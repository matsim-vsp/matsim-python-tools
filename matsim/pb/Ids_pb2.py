# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: matsim/pb/Ids.proto

from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='matsim/pb/Ids.proto',
  package='matsim.pb',
  syntax='proto3',
  serialized_options=b'\n\030org.matsim.core.utils.pbP\001',
  serialized_pb=b'\n\x13matsim/pb/Ids.proto\x12\tmatsim.pb\"E\n\x07ProtoId\x12\n\n\x02id\x18\x01 \x01(\t\x12\r\n\x05index\x18\x02 \x01(\x05\x12\x1f\n\x04type\x18\x03 \x01(\x0e\x32\x11.matsim.pb.IdType*\x9b\x01\n\x06IdType\x12\x0e\n\nID_UNKNOWN\x10\x00\x12\x10\n\x0cID_DEPARTURE\x10\x01\x12\x14\n\x10ID_TRANSIT_ROUTE\x10\x02\x12\x13\n\x0fID_TRANSIT_LINE\x10\x03\x12\x0e\n\nID_VEHICLE\x10\x04\x12\x0b\n\x07ID_LINK\x10\x05\x12\r\n\tID_PERSON\x10\x06\x12\x18\n\x14ID_ACTIVITY_FACILITY\x10\x07\x42\x1c\n\x18org.matsim.core.utils.pbP\x01\x62\x06proto3'
)

_IDTYPE = _descriptor.EnumDescriptor(
  name='IdType',
  full_name='matsim.pb.IdType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='ID_UNKNOWN', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_DEPARTURE', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_TRANSIT_ROUTE', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_TRANSIT_LINE', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_VEHICLE', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_LINK', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_PERSON', index=6, number=6,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ID_ACTIVITY_FACILITY', index=7, number=7,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=106,
  serialized_end=261,
)
_sym_db.RegisterEnumDescriptor(_IDTYPE)

IdType = enum_type_wrapper.EnumTypeWrapper(_IDTYPE)
ID_UNKNOWN = 0
ID_DEPARTURE = 1
ID_TRANSIT_ROUTE = 2
ID_TRANSIT_LINE = 3
ID_VEHICLE = 4
ID_LINK = 5
ID_PERSON = 6
ID_ACTIVITY_FACILITY = 7



_PROTOID = _descriptor.Descriptor(
  name='ProtoId',
  full_name='matsim.pb.ProtoId',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='matsim.pb.ProtoId.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='index', full_name='matsim.pb.ProtoId.index', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='type', full_name='matsim.pb.ProtoId.type', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=34,
  serialized_end=103,
)

_PROTOID.fields_by_name['type'].enum_type = _IDTYPE
DESCRIPTOR.message_types_by_name['ProtoId'] = _PROTOID
DESCRIPTOR.enum_types_by_name['IdType'] = _IDTYPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ProtoId = _reflection.GeneratedProtocolMessageType('ProtoId', (_message.Message,), {
  'DESCRIPTOR' : _PROTOID,
  '__module__' : 'matsim.pb.Ids_pb2'
  # @@protoc_insertion_point(class_scope:matsim.pb.ProtoId)
  })
_sym_db.RegisterMessage(ProtoId)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)