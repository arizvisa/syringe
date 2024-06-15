'''
macOS Mojave version 10.14.1
ripped from https://www.fortinet.com/blog/threat-research/a-look-into-xpc-internals--reverse-engineering-the-xpc-objects
'''
import ptypes
from ptypes import *

class uint8_t(pint.uint8_t): pass
class uint16_t(pint.uint16_t): pass
class uint32_t(pint.uint32_t): pass
class uint64_t(pint.uint64_t): pass
class sint8_t(pint.sint8_t): pass
class sint16_t(pint.sint16_t): pass
class sint32_t(pint.sint32_t): pass
class sint64_t(pint.sint64_t): pass
class single(pfloat.single): pass
class double(pfloat.double): pass
class void_star(ptype.pointer_t): pass

class OS_xpc_(pint.enum, uint64_t):
    # FIXME: these should be addrs
    _values_ = [
        ('bool', 1),
        ('bundle', 2),
        ('null', 3),
        ('int64', 4),
        ('uint64', 5),
        ('uuid', 6),
        ('double', 7),
        ('date', 8),
        ('data', 9),
        ('dictionary', 10),
        ('pointer', 11),
        ('pipe', 12),
        ('string', 13),
        ('shmem', 14),
        ('serializer', 15),
        ('service', 16),
        ('service_instance', 17),
        ('fd', 18),
        ('file_transfer', 19),
        ('mach_send', 20),
        ('mach_recv', 21),
        ('array', 22),
        ('activity', 23),
        ('error', 24),
        ('endpoint', 25),
        ('connection', 26),
        ('dispatch_data', 27),
        ('data', 28),
        ('dictionary', 29),
    ]

class isa(ptype.definition):
    cache, attribute = {}, 'address'

class xpc_object_t(pstruct.type):
    _fields_ = [
        (OS_xpc_, 'isa'),
        (uint32_t, 'xref'),
        (uint32_t, 'ref'),
        (uint32_t, 'unknown/unused'),
        (uint32_t, 'size'),
        (lambda self: isa.lookup(self['isa'].int()), 'object'),
    ]

@isa.define
class xpc_uint64_t(pstruct.type):
    address = OS_xpc_.byname('uint64')
    _fields_ = [
        #(uint32_t, '0x8'),
        (uint64_t, 'value'),
    ]

@isa.define
class xpc_int64_t(pstruct.type):
    address = OS_xpc_.byname('int64')
    _fields_ = [
        #(uint32_t, '0x8'),
        (sint64_t, 'value'),
    ]

@isa.define
class xpc_uuid_t(pstruct.type):
    address = OS_xpc_.byname('uuid')
    _fields_ = [
        #(uint32_t, '0x10'),
        (uint64_t, 'first'),
        (uint64_t, 'second'),
    ]

@isa.define
class xpc_double_t(pstruct.type):
    address = OS_xpc_.byname('double')
    _fields_ = [
        #(uint32_t, '0x8'),
        (double, 'value'),
    ]

@isa.define
class xpc_date_t(pstruct.type):
    address = OS_xpc_.byname('date')
    _fields_ = [
        #(uint32_t, '0x8'),
        (dynamic.block(8), 'value'),
    ]

@isa.define
class xpc_string_t(pstruct.type):
    address = OS_xpc_.byname('string')
    _fields_ = [
        #(uint32_t, '(len + 8) & 0xFFFFFFFC'),
        (uint32_t, 'len'),
        (dynamic.pointer(lambda self: dynamic.clone(pstr.string, length=self.p['len'].li.int())), 'value'),
    ]

@isa.define
class xpc_array_t(pstruct.type):
    address = OS_xpc_.byname('array')
    _fields_ = [
        #(uint32_t, '0x4'),
        (uint32_t, 'length'),
        (uint32_t, 'capacity'),
        (dynamic.pointer(xpc_object_t), 'buffer'),
    ]

@isa.define
class OS_dispatch_data(pstruct.type):
    address = OS_xpc_.byname('dispatch_data')
    _fields_ = [
        (uint64_t, 'unknown/unused'),
        (void_star, 'pointer to data buffer'),
        (void_star, '_dispatch_to_data_destructor_none'),
        (uint64_t, 'length'),
        (uint64_t, '0x00'),
        (lambda self: dynamic.block(self['length'].li.int()), 'data buffer'),
    ]

@isa.define
class xpc_data_t(pstruct.type):
    address = OS_xpc_.byname('data')
    _fields_ = [
        #(uint32_t, '((length + 7) & 0xFFFFFFFC) or 0x04'),
        (uint32_t, 'unknow/unused'),
        (dynamic.pointer(OS_dispatch_data), 'pointer to OS_dispatch_data'),
        (uint32_t, 'unknown/unused'),
        (uint64_t, 'data length'),
        (uint32_t, '0x00'),
    ]

class hash_entry(pstruct.type):
    def __self(self):
        return hash_entry
    _fields_ = [
        (dynamic.pointer(__self), 'next'),
        (dynamic.pointer(__self), 'prev'),
        (dynamic.pointer(xpc_object_t), 'object'),
        (uint64_t, 'flags'),
        (pstr.string, 'key'),
    ]

@isa.define
class xpc_dictionary_t(pstruct.type):
    address = OS_xpc_.byname('dictionary')
    _fields_ = [
        (void_star, 'connection'),
        (uint64_t, 'unknown/unused'),
        (uint32_t, 'count'),
        (dynamic.block(32), 'audit token or 0x0202...02'),
        (uint32_t, 'unknown/unused'),
        (dynamic.array(hash_entry, 7), 'hash_buckets'),
        (uint64_t, 'importance voucher'),
        (uint64_t, 'bitfield transaction'),
        (uint64_t, 'unknown/unused'),
    ]
