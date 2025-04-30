import builtins, functools, itertools, operator, ptypes
from ptypes import *

class PROTOBUF_C_FIELD_FLAG_(pbinary.flags):
    _fields_ = [
        (5, 'RESERVED'),
        (1, 'ONEOF'),
        (1, 'DEPRECATED'),
        (1, 'PACKED'),
    ]

class PROTOBUF_C_LABEL_(pint.enum):
    _values_ = [
        ('REQUIRED', 0),
        ('OPTIONAL', 1),
        ('REPEATED', 2),
        ('NONE', 3),
    ]

class PROTOBUF_C_TYPE_(pint.enum):
    _fields_ = [
        ('INT32', 0),       # int32
        ('SINT32', 1),      # signed int32
        ('SFIXED32', 2),    # signed int32 (4 bytes)
        ('INT64', 3),       # int64
        ('SINT64', 4),      # signed int64
        ('SFIXED64', 5),    # signed int64 (8 bytes)
        ('UINT32', 6),      # unsigned int32
        ('FIXED32', 7),     # unsigned int32 (4 bytes)
        ('UINT64', 8),      # unsigned int64
        ('FIXED64', 9),     # unsigned int64 (8 bytes)
        ('FLOAT', 10),      # float
        ('DOUBLE', 11),     # double
        ('BOOL', 12),       # boolean
        ('ENUM', 13),       # enumerated type
        ('STRING', 14),     # UTF-8 or ASCII string
        ('BYTES', 15),      # arbitrary byte sequence
        ('MESSAGE', 16),    # nested message
    ]

class PROTOBUF_WIRETYPE(ptype.definition):
    cache = {}
    class PROTOBUF_C_WIRE_TYPE_(pint.enum):
        _values_ = [
            ('VARINT', 0),
            ('64BIT', 1),
            ('LENGTH_PREFIXED', 2),
            ('32BIT', 5),
        ]
    _enum_ = PROTOBUF_C_WIRE_TYPE_

@PROTOBUF_WIRETYPE.define
class VARINT(pbinary.terminatedarray):
    type = 0
    class _object_(pbinary.flags):
        _fields_ = [
            (1, 'continue'),
            (7, 'bits'),
        ]
    def isTerminator(self, octet):
        bit = octet['continue']
        return False if bit else True
    def int(self):
        septets = [item['bits'] for item in self]
        shift = lambda res, integer: res * pow(2, 7) + integer
        return functools.reduce(shift, septets[::-1], 0)
    def alloc(self, *args, **attrs):
        if not(args and isinstance(args[0], builtins.int)):
            return super().alloc(*args, **attrs)
        [integer] = args
        bits = integer.bit_length()
        septets, extra = divmod(bits, 7)
        count = septets + 1 if extra else septets

        digits, divisor = [], pow(2, 7)
        while len(digits) < count:
            integer, digit = divmod(integer, divisor)
            digits.insert(0, digit)

        iterable = ({'bits': digit, 'continue': not(not(index))} for index, digit in enumerate(digits))
        items = [self.new(self._object_).alloc(**fields) for fields in iterable]
        return super().alloc(items[::-1], **attrs)
    def summary(self):
        bits, integer = 7 * len(self), self.int()
        count, extra = divmod(bits, 8)
        octets = count + 1 if extra else count
        return "[{:0x}] -> {:d} ({:#0{:d}x})".format(self, integer, integer, 2 + 2 * count)

@PROTOBUF_WIRETYPE.define
class U64(pint.uint64_t):
    type = 1

@PROTOBUF_WIRETYPE.define
class LENGTH_PREFIXED(pstruct.type):
    type = 2
    def __payload(self):
        res = self['length'].li
        #return dyn.clone(MESSAGE, blocksize=lambda _, bs=res.int(): bs)
        return dyn.block(res.int())
    _fields_ = [
        (VARINT, 'length'),
        (__payload, 'payload'),
    ]
    def summary(self):
        length = self['length'].int()
        return self['payload'].summary()

@PROTOBUF_WIRETYPE.define
class SGROUP(ptype.undefined):
    type = 3

@PROTOBUF_WIRETYPE.define
class EGROUP(ptype.undefined):
    type = 4

@PROTOBUF_WIRETYPE.define
class U32(pint.uint32_t):
    type = 5

class TAG(VARINT):
    def wiretype(self):
        return self.int() & 7
    def fieldnumber(self):
        return self.int() // pow(2, 3)
    def alloc(self, *tuple, **attrs):

        # if we were given only attributes, then use them to encode the integer
        # containing the "fieldnum" and the "wiretype".
        if not(tuple):
            fieldnumber = next((attrs.pop(k) for k in ['field', 'fieldnum', 'fieldnumber'] if k in attrs), 0)
            wiretype = attrs.pop('wiretype', 0)
            integer = fieldnumber * pow(2, 3)
            bits = 3 + integer.bit_length()
            septets, extra = divmod(bits, 7)
            length = septets + 1 if extra else septets
            attrs.setdefault('length', length)
            return super().alloc(integer | wiretype & 7, **attrs)

        # if we're given some parameters and they're all integers, then use
        # extract the field number and wiretype for encoding the integer.
        elif len(tuple) in {1, 2} and all(isinstance(item, ptypes.integer_types) for item in tuple):
            [fieldnumber, wiretype] = tuple if len(tuple) == 2 else itertools.chain(tuple, [0])
            attrs.setdefault('fieldnumber', fieldnumber)
            attrs.setdefault('wiretype', wiretype)
            return self.alloc(**attrs)
        return super().alloc(*tuple, **attrs)
    def summary(self):
        integer = self.int()
        wiretype = PROTOBUF_WIRETYPE.enum(length=1).set(integer & 7)
        return "{:s} : fieldnum={:d}".format(wiretype, integer // pow(2, 3))

class TAGVALUE(pstruct.type):
    def __value(self):
        res = self['tag'].li
        wiretype = res.wiretype()
        return PROTOBUF_WIRETYPE.lookup(wiretype)
    _fields_ = [
        (TAG, 'tag'),
        (__value, 'value'),
    ]
    def summary(self):
        if not(self.initializedQ()):
            return super().summary()
        res = self['tag'].li
        wiretype = PROTOBUF_WIRETYPE.enum(length=1).set(res.wiretype())
        fieldnum = res.fieldnumber()
        return "tag.fieldnum={:d} tag.wiretype={:s} value={:s}".format(fieldnum, wiretype, self['value'].summary())
    def alloc(self, *values, **fields):
        newfields = {fld : value for fld, value in fields.items()}
        if values:
            [wired] = values
            tag = TAG().alloc(fieldnum=fields.pop('fieldnum', 0), wiretype=wired.type)
            newfields.setdefault('tag', tag), newfields.setdefault('value', wired)

        res = super().alloc(**newfields)
        if not(isinstance(fields.get('tag'), ptype.generic)) and hasattr(res['value'], 'type'):
            res['tag'].alloc(fieldnum=res['tag'].fieldnumber(), wiretype=res['value'].type)
        return res

class MESSAGE(parray.block):
    '''only used when deserializing.'''
    _object_ = TAGVALUE

if __name__ == '__main__':

    data = bytes.fromhex('12 05 41 70 70 6c 65')
    source = ptypes.setsource(ptypes.prov.bytes(data))
    x = TAGVALUE(source=source).l
 
    data = bytes.fromhex('08 96 01 12 05 41 70 70 6c 65')
    source = ptypes.setsource(ptypes.prov.bytes(data))
    x = Message(source=source, blocksize=lambda: len(data))
    x.l
    print(x[0].summary())

    print("{:#x}".format(x[0]['value']))

    s = b"\0\0\0\1\0\0\0\0\0\0\0\0\0\0\0\211\n\206\1\n\6testdb\22\30select * from testdb.wtf \0012\20America/New_YorkJ\0R4ffffffffa8c0670a-11679-7e4d177e0200-00401a91cdd43863p\5p\6p\3p\2p\v\212\1\v\10\243\243\344\346\324\361\214\3\20\0"
    x = newsql(source=ptypes.prov.bytes(s))
    x.l
    assert(len(s) == x.size())
    print(x['header'])
    print(x['payload'][0])
    print(x['payload'][0]['value'])
    print(x['payload'][0]['value']['payload'])
    print(x['payload'][0]['value']['payload'].hexdump())

    s = bytes.fromhex('0a06746573746462121873656c656374202a2066726f6d207465737464622e77746620013210416d65726963612f4e65775f596f726b4a005234666666666666666661386330363730612d31313637392d3765346431373765303230302d303034303161393163646434333836337005700670037002700b8a010b08a3a3e4e6d4f18c031000')
    x = parray.type(_object_=protocolbuffer.TAGVALUE, source=ptypes.prov.bytes(s))
    print(x.load(length=12))
    print(x[0]['value']['payload'])
    print(x[1]['value']['payload'])
    print(x[2]['value'])
    print(x[3]['value']['payload'])
    print(x[4]['value'])
    print(x[5]['value']['payload'])
    print(x[6]['value'])
    print(x[7]['value'])
    print(x[8]['value'])
    print(x[9]['value'])
    print(x[10]['value'])
    print(x[11]['value']['payload'])

    print(x['payload'][0]['value']['payload'].hexdump())
    s = bytes.fromhex('0a 06 74 65 73 74 64 62  12 18 73')
    protocolbuffer.MESSAGE(length=len(s), source=ptypes.prov.bytes(s)).l
    protocolbuffer.TAGVALUE(source=ptypes.prov.bytes(s)).l

    x = protocolbuffer.MESSAGE(source=ptypes.prov.bytes(s), blocksize=lambda: len(s)).l
    for item in x: p(item)
