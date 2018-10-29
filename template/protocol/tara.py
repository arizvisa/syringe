import ptypes, mp
from ptypes import *

class greeting(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string, length=64), 'tarantool'),
        (dyn.clone(pstr.string, length=44), 'salt'),
        (dyn.clone(pstr.string, length=20), 'null'),
    ]

### enumerations
class key_type(pint.enum):
    _values_ = [
        ('REQUEST_TYPE', 0x00),
        ('SYNC', 0x01),
        ('SERVER_ID', 0x02),
        ('LSN', 0x03),
        ('TIMESTAMP', 0x04),
        ('SCHEMA_ID', 0x05),
        ('SPACE_ID', 0x10),
        ('INDEX_ID', 0x11),
        ('LIMIT', 0x12),
        ('OFFSET', 0x13),
        ('ITERATOR', 0x14),
        ('INDEX_BASE', 0x15),
        ('KEY', 0x20),
        ('TUPLE', 0x21),
        ('FUNCTION_NAME', 0x22),
        ('USER_NAME', 0x23),
        ('SERVER_UUID', 0x24),
        ('CLUSTER_UUID', 0x25),
        ('VCLOCK', 0x26),
        ('EXPR', 0x27), # EVAL
        ('OPS', 0x28), # UPSERT but not UPDATE ops, because of legacy
        ('DATA', 0x30),
        ('ERROR', 0x31),
    ]

class command_type(pint.enum):
    _values_ = [
        ('OK', 0),
        ('SELECT', 1),
        ('INSERT', 2),
        ('REPLACE', 3),
        ('UPDATE', 4),
        ('DELETE', 5),
        ('CALL_16', 6),
        ('AUTH', 7),
        ('EVAL', 8),
        ('UPSERT', 9),
        ('CALL', 10),
        ('PING', 64),
        ('JOIN', 65),
        ('SUBSCRIBE', 66),
        ('TYPE_ERROR', 1 << 15),
    ]

class iterator_type(pint.enum):
    _values_ = [
        ('ITER_EQ', 0),                 # key == x ASC order
        ('ITER_REQ', 1),                # key == x DESC order
        ('ITER_ALL', 2),                # all tuples
        ('ITER_LT', 3),                 # key <  x
        ('ITER_LE', 4),                 # key <= x
        ('ITER_GE', 5),                 # key >= x
        ('ITER_GT', 6),                 # key >  x
        ('ITER_BITS_ALL_SET', 7),       # all bits from x are set in key
        ('ITER_BITS_ANY_SET', 8),       # at least one x's bit is set
        ('ITER_BITS_ALL_NOT_SET', 9),   # all bits are not set
        ('ITER_OVERLAPS', 10),          # key overlaps x
        ('ITER_NEIGHBOR', 11),          # typles in distance ascending order from specified point
    ]

### packet types
class request(pstruct.type):
    _fields_ = [
        (mp.packet, 'size'),
        (mp.packet, 'header'),
        (mp.packet, 'body'),
    ]

class erequest(pstruct.type):
    class headerbody(ptype.encoded_t):
        class _object_(pstruct.type):
            _fields_ = [
                (mp.packet, 'header'),
                (mp.packet, 'body'),
            ]
    _fields_ = [
        (mp.packet, 'size'),
        (lambda s: dyn.clone(s.headerbody, _value_=dyn.block(s['size'].li['data']['value'].int())), 'header/body'),
    ]

class response(pstruct.type):
    _fields_ = [
        (mp.packet, 'size'),
        (mp.packet, 'header'),
        (mp.packet, 'body'),
    ]

class qresponse(pstruct.type):
    _fields_ = [
        (mp.packet, 'size'),
        (lambda s: dyn.block(s['size'].li['data']['value'].int()), 'header/body'),
    ]

