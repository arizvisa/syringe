import sys
import itertools,functools,operator
import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class proto_version(pint.enum, pint.uint8_t):
    _values_ = [
        ('v0', 0),
        ('v2', 2),
    ]

class proto_type(pint.enum, pint.uint8_t):
    _values_ = [
        ('INFO', 1),
        ('SECURITY', 2),
        ('AS_MSG', 3),
        ('AS_MSG_COMPRESSED', 4),
        ('INTERNAL_XDR', 5),
    ]

class AS_MSG_INFO1(pbinary.flags):
    _fields_ = [
        (1, 'READ'),                   # contains a read operation
        (1, 'GET_ALL'),                # get all bins, period
        (1, 'unused'),
        (1, 'BATCH'),                  # new batch protocol
        (1, 'XDR'),                    # operation is being performed by XDR
        (1, 'GET_NOBINDATA'),          # Do not get information about bins and its data
        (1, 'CONSISTENCY_LEVEL_B0'),   # read consistency level - bit 0
        (1, 'CONSISTENCY_LEVEL_B1'),   # read consistency level - bit 1
    ]

class AS_MSG_INFO2(pbinary.flags):
    _fields_ = [
        (1, 'WRITE'),              # contains a write semantic
        (1, 'DELETE'),             # delete record
        (1, 'GENERATION'),         # pay attention to the generation
        (1, 'GENERATION_GT'),      # apply write if new generation > old, good for restore
        (1, 'DURABLE_DELETE'),     # op resulting in record deletion leaves tombstone (Enterprise only)
        (1, 'CREATE_ONLY'),        # write record only if it doesn't exist
        (1, 'BIN_CREATE_ONLY'),    # write bin only if it doesn't exist
        (1, 'RESPOND_ALL_OPS'),    # all bin ops (read, write, or modify) require a response, in request order
    ]

class AS_MSG_INFO3(pbinary.flags):
    _fields_ = [
        (1, 'LAST'),               # this is the last of a multi-part message
        (1, 'COMMIT_LEVEL_B0'),    # write commit level - bit 0
        (1, 'COMMIT_LEVEL_B1'),    # write commit level - bit 1
        (1, 'UPDATE_ONLY'),        # update existing record only, do not create new record
        (1, 'CREATE_OR_REPLACE'),  # completely replace existing record, or create new record
        (1, 'REPLACE_ONLY'),       # completely replace existing record, do not create new record
        (1, 'BIN_REPLACE_ONL'),    # replace existing bin, do not create new bin
    ]

class AS_MSG_FIELD_TYPE(pint.enum, pint.uint8_t):
    _values_ = [
        ('NAMESPACE', 0),        # UTF8 string
        ('SET', 1),
        ('KEY', 2),              # contains a key value
        ('DIGEST_RIPE', 4),      # Key digest computed with RIPE160
        ('DIGEST_RIPE_ARRAY', 6),
        ('TRID', 7),
        ('SCAN_OPTIONS', 8),
        ('INDEX_NAME', 21),
        ('INDEX_RANGE', 22),
        ('INDEX_TYPE', 26),
        ('UDF_FILENAME', 30),
        ('UDF_FUNCTION', 31),
        ('UDF_ARGLIST', 32),
        ('UDF_OP', 33),
        ('QUERY_BINLIST', 40),
        ('BATCH', 41),
        ('BATCH_WITH_SET', 42),
    ]

### Sub-field types (FIXME)
class msg_field(ptype.definition):
    AS_MSG_FIELD_TYPE
    cache = {}

class as_msg_field_s(pstruct.type):
    def __data(self):
        t = self['type'].li.int()
        return msg_field.lookup(t)

    _fields_ = [
        #/* NB: field_sz is sizeof(type) + sizeof(data) */
        (pint.uint32_t, 'field_sz'),    # get the data size through the accessor function, don't worry, it's a small macro
        (AS_MSG_FIELD_TYPE, 'type'),    # ordering matters :-( see as_transaction_prepare
        (__data, 'data'),
    ]

@msg_field.define
class as_msg_key_s(pstruct.type):
    type = AS_MSG_FIELD_TYPE.byname("KEY")

    _fields_ = [
        (as_msg_field_s, 'f'),
        (ptype.block, 'key'),
    ]

@msg_field.define
class as_msg_number_s(pstruct.type):
    type = AS_MSG_FIELD_TYPE.byname("KEY")

    _fields_ = [
        (as_msg_field_s, 'f'),
        (pint.uint32_t, 'number'),
    ]

class as_msg_op_s(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'op_sz'),
        (pint.uint8_t, 'op'),
        (pint.uint8_t, 'particle_type'),
        (pint.uint8_t, 'version'),        # now unused
        (pint.uint8_t, 'name_sz'),
        (lambda s: dyn.block(s['name_sz'].li.int()), 'name'),         # UTF-8
        (lambda s: dyn.block(s['op_sz'].li.int() - (8+s['name'].li.size())), 'value'),
    ]

### Sub-message types
class msg_proto(ptype.definition):
    proto_type
    cache = {}

@msg_proto.define
class as_msg_s(pstruct.type):
    type = proto_type.byname("AS_MSG")

    _fields_ = [
        (pint.uint8_t, 'header_sz'),
        (AS_MSG_INFO1, 'info1'),
        (AS_MSG_INFO2, 'info2'),
        (AS_MSG_INFO3, 'info3'),
        (pint.uint8_t, 'unused'),
        (pint.uint8_t, 'result_code'),

        (pint.uint32_t, 'generation'),
        (pint.uint32_t, 'record_ttl'),
        (pint.uint32_t, 'transaction_ttl'),
        (pint.uint16_t, 'n_fields'),
        (pint.uint16_t, 'n_ops'),
#        (ptype.block, 'data'),

        (lambda s: dyn.array(as_msg_field_s, s['n_fields'].li.int()), 'fields'),
        (lambda s: dyn.array(as_msg_op_s, s['n_ops'].li.int()), 'ops'),
    ]

@msg_proto.define
class as_comp_proto_s(pstruct.type):
    type = proto_type.byname("AS_MSG_COMPRESSED")

    def __data(self):
        p = self.getparent(as_proto_s)
        sz = p['sz'].li.int()
        return dyn.block(sz - self['org_sz'].blocksize())

    _fields_ = [
        (pint.uint64_t, 'org_sz'),
        (__data, 'data'),
    ]

@msg_proto.define
class as_sec_msg_s(pstruct.type):
    type = proto_type.byname("SECURITY")

    _fields_ = [
        (pint.uint8_t, 'scheme'),
        (pint.uint8_t, 'result'),
        (pint.uint8_t, 'command'),
        (pint.uint8_t, 'n_fields'),
        (dyn.block(12), 'unused'),
        (ptype.block, 'fields'),
    ]

### main packet structure
PROTO_SIZE_MAX = 128*1024*1024  # * 32
class as_proto_s(pstruct.type):
    def __data(self):
        t, sz = self['type'].li, self['sz'].li.int()
        return msg_proto.lookup(t, blocksize=lambda s: sz)

    _fields_ = [
        (proto_version, 'version'),
        (proto_type, 'type'),
        (pint.uint64_t, 'sz'),
        (__data, 'data'),
    ]

class cl_msg_s(pstruct.type):
    _fields_ = [
        (as_proto_s, 'proto'),
        (as_msg_s, 'msg'),
    ]
