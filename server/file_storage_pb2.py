# Generated-compatible protobuf module for DCSM RPL UTS.
from google.protobuf import descriptor_pool, descriptor as _descriptor, symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
from pathlib import Path
_sym_db = _symbol_database.Default()
_DATA = Path(__file__).resolve().parent.parent.joinpath('proto','file_storage.desc').read_bytes()
DESCRIPTOR = descriptor_pool.Default().AddSerializedFile(_DATA)
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_storage_pb2', globals())
