import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### definitions
class bit0(ptype.definition): cache = {}
class bit1(ptype.definition): cache = {}
class bit2container(ptype.definition): cache = {}
class bit2msgtype(ptype.definition): cache = {}
class bit3arraymap(ptype.definition): cache = {}
class d_packet(ptype.definition): cache = {}

### packet
class packet(pstruct.type):
    _fields_ = [
        (lambda s: t_packet, 'type'),
        (lambda s: d_packet.lookup(s['type'].li.PackedType()), 'data'),
    ]

    def packedValue(self):
        return self['type'].PackedValue()

class t_packet(pbinary.struct):
    def __value(self):
        return bit0.lookup(self['otherQ'])
    _fields_ = [
        (1, 'otherQ'),
        (__value, 'value'),
    ]
    def PackedType(self):
        '''Return the msgpack type-id for the packet.'''
        return self.__field__('value').PackedType()
    def PackedValue(self):
        '''Return the integer value encoded within the type field of the packet.'''
        return self.__field__('value').PackedValue()
    def summary(self):
        res = d_packet.lookup(self.PackedType())
        return '{:s} {:s}'.format(res.typename(), super(t_packet,self).summary())

## first bit : positive-fixint or other
@bit0.define
class t_positive_fixint(pbinary.integer):
    type = 0
    def blockbits(self): return 7
    def PackedType(self): return 0b00000000
    def PackedValue(self): return self.int()

@bit0.define
class t_fixother(pbinary.struct):
    type = 1
    def __value(self):
        return bit1.lookup(self['groupQ'])
    _fields_ = [
        (1, 'groupQ'),
        (__value, 'value'),
    ]
    def PackedType(self): return self.__field__('value').PackedType()
    def PackedValue(self): return self.__field__('value').PackedValue()

## second bit : container or group
@bit1.define
class t_1fixcontainer(pbinary.struct):
    type = 0
    def __value(self):
        return bit2container.lookup(self['strQ'])
    _fields_ = [
        (1, 'strQ'),
        (__value, 'value'),
    ]
    def PackedType(self): return self.__field__('value').PackedType()
    def PackedValue(self): return self.__field__('value').PackedValue()

@bit1.define
class t_fixgroup(pbinary.struct):
    type = 1
    def __value(self):
        return bit2msgtype.lookup(self['negative-fixintQ'])
    _fields_ = [
        (1, 'negative-fixintQ'),
        (__value, 'value'),
    ]
    def PackedType(self): return self.__field__('value').PackedType()
    def PackedValue(self): return self.__field__('value').PackedValue()

## third bit : str or array/map
@bit2container.define
class t_fixstr(pbinary.integer):
    type = 1
    def blockbits(self): return 5
    def PackedType(self): return 0b10100000
    def PackedValue(self): return self.int()

@bit2container.define
class t_2fixcontainer(pbinary.struct):
    type = 0
    def __container(self):
        return bit3arraymap.lookup(self['arrayQ'])
    _fields_ = [
        (1, 'arrayQ'),
        (__container, 'value'),
    ]
    def PackedType(self): return self.__field__('value').PackedType()
    def PackedValue(self): return self.__field__('value').PackedValue()

## fourth bit: array or map
@bit3arraymap.define
class t_fixmap(pbinary.integer):
    type = 0
    def blockbits(self): return 4
    def PackedType(self): return 0b10000000
    def PackedValue(self): return self.int()
@bit3arraymap.define
class t_fixarray(pbinary.integer):
    type = 1
    def blockbits(self): return 4
    def PackedType(self): return 0b10010000
    def PackedValue(self): return self.int()

## third bit : negative-fixint or messagetype
@bit2msgtype.define
class t_negative_fixint(pbinary.integer):
    type = 1
    def blockbits(self): return 5
    def PackedType(self): return 0b11100000
    def PackedValue(self): return self.int()

@bit2msgtype.define
class t_message(pbinary.enum):
    type, _width_ = 0, 5
    def PackedType(self): return (0b11 << 6) | self.int()
    def PackedValue(self): raise NotImplementedError
    _values_ = [
        ('nil', 0b00000),
        ('(neverused)', 0b00001),
        ('false', 0b00010),
        ('true', 0b00011),
        ('bin8', 0b00100),
        ('bin16', 0b00101),
        ('bin32', 0b00110),
        ('ext8', 0b00111),
        ('ext16', 0b01000),
        ('ext32', 0b01001),
        ('float32', 0b01010),
        ('float64', 0b01011),
        ('uint8', 0b01100),
        ('uint16', 0b01101),
        ('uint32', 0b01110),
        ('uint64', 0b01111),
        ('int8', 0b10000),
        ('int16', 0b10001),
        ('int32', 0b10010),
        ('int64', 0b10011),
        ('fixext1', 0b10100),
        ('fixext2', 0b10101),
        ('fixext4', 0b10110),
        ('fixext8', 0b10111),
        ('fixext16', 0b11000),
        ('str8', 0b11001),
        ('str16', 0b11010),
        ('str32', 0b11011),
        ('array16', 0b11100),
        ('array32', 0b11101),
        ('map16', 0b11110),
        ('map32', 0b11111),
    ]

### Message data types
class summaryStructure(pstruct.type):
    def summary(self):
        if len(self._fields_) > 1:
            return super(summaryStructure, self).summary()
        res = ('{:s}={:s}'.format(k, self[k].summary()) for _, k in self._fields_)
        return '{{{:s}}}'.format(', '.join(res))
class ConstantHolder(ptype.block):
    constant = None
    def get(self):
        return None
    def set(self, value):
        raise NotImplementedError

class PackedIntegerHolder(pint.uint_t):
    def get(self):
        return self.getparent(packet).packedValue()
    def summary(self):
        return '{integer:d} ({integer:+#x})'.format(integer=self.get())
    def set(self, value):
        pkt = self.getparent(packet)
        leafs = pkt['type'].traverse(edges=lambda self: self.value, filter=lambda self: isinstance(self, pbinary.type) and self.bits() > 1)
        res = list(leafs)[-1]
        if res.name() != 'value':
            raise AssertionError
        return res.set(value)

@d_packet.define
class d_nil(summaryStructure):
    type = 0b11000000
    class _ConstantHolderNone(ConstantHolder): constant = None
    _fields_ = [(_ConstantHolderNone, 'Value')]
@d_packet.define
class d_true(summaryStructure):
    type = 0b11000010
    class _ConstantHolderTrue(ConstantHolder): constant = True
    _fields_ = [(_ConstantHolderTrue, 'Value')]
@d_packet.define
class d_false(summaryStructure):
    type = 0b11000011
    class _ConstantHolderFalse(ConstantHolder): constant = False
    _fields_ = [(_ConstantHolderFalse, 'Value')]

@d_packet.define
class d_positive_fixint(summaryStructure):
    type = 0b00000000
    _fields_ = [(PackedIntegerHolder, 'Value')]
@d_packet.define
class d_negative_fixint(summaryStructure):
    type = 0b11100000
    class _PackedSignedIntegerHolder(PackedIntegerHolder):
        def get(self):
            return -0x20 + super(d_negative_fixint._PackedSignedIntegerHolder, self).get()
    _fields_ = [(_PackedSignedIntegerHolder, 'Value')]

@d_packet.define
class d_uint8(summaryStructure):
    type = 0b11001100
    _fields_ = [(pint.uint8_t,'Value')]
@d_packet.define
class d_uint16(summaryStructure):
    type = 0b11001101
    _fields_ = [(pint.uint16_t,'Value')]
@d_packet.define
class d_uint32(summaryStructure):
    type = 0b11001110
    _fields_ = [(pint.uint32_t,'Value')]
@d_packet.define
class d_uint64(summaryStructure):
    type = 0b11001111
    _fields_ = [(pint.uint64_t,'Value')]

@d_packet.define
class d_int8(summaryStructure):
    type = 0b11010000
    _fields_ = [(pint.int8_t,'Value')]
@d_packet.define
class d_int16(pstruct.type):
    type = 0b11010001
    _fields_ = [(pint.int16_t,'Value')]
@d_packet.define
class d_int32(pstruct.type):
    type = 0b11010010
    _fields_ = [(pint.int32_t,'Value')]
@d_packet.define
class d_int64(pstruct.type):
    type = 0b11010011
    _fields_ = [(pint.int64_t,'Value')]

@d_packet.define
class d_float32(pstruct.type):
    type = 0b11001010
    _fields_ = [(pfloat.single,'Value')]
@d_packet.define
class d_float64(pstruct.type):
    type = 0b11001011
    _fields_ = [(pfloat.double,'Value')]

@d_packet.define
class d_fixstr(summaryStructure):
    type = 0b10100000
    _fields_ = [
        (PackedIntegerHolder, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_str8(summaryStructure):
    type = 0b11011001
    _fields_ = [
        (pint.uint8_t, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_str16(summaryStructure):
    type = 0b11011010
    _fields_ = [
        (pint.uint16_t, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_str32(summaryStructure):
    type = 0b11011011
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.get()), 'Value'),
    ]

@d_packet.define
class d_bin8(summaryStructure):
    type = 0b11000100
    _fields_ = [
        (pint.uint8_t, 'Length'),
        (lambda s: dyn.block(s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_bin16(summaryStructure):
    type = 0b11000101
    _fields_ = [
        (pint.uint16_t, 'Length'),
        (lambda s: dyn.block(s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_bin32(summaryStructure):
    type = 0b11000110
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.block(s['Length'].li.get()), 'Value'),
    ]

@d_packet.define
class d_fixarray(summaryStructure):
    type = 0b10010000
    _fields_ = [
        (PackedIntegerHolder, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_array16(summaryStructure):
    type = 0b11011100
    _fields_ = [
        (pint.uint16_t, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()), 'Value'),
    ]
@d_packet.define
class d_array32(summaryStructure):
    type = 0b11011101
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()), 'Value'),
    ]

@d_packet.define
class d_fixmap(summaryStructure):
    type = 0b10000000
    _fields_ = [
        (PackedIntegerHolder, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()*2), 'Value'),
    ]
    def Data(self):
        p = self.getparent(packet)
        return p['type'].PackedValue()
@d_packet.define
class d_map16(summaryStructure):
    type = 0b11011110
    _fields_ = [
        (pint.uint16_t, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()*2), 'Value'),
    ]
@d_packet.define
class d_map32(summaryStructure):
    type = 0b11011111
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.array(packet, s['Length'].li.get()*2), 'Value'),
    ]

@d_packet.define
class d_fixext1(summaryStructure):
    type = 0b11010100
    _fields_ = [
        (pint.sint8_t, 'Type'),
        (dyn.array(pint.uint8_t, 1), 'Value'),
    ]
@d_packet.define
class d_fixext2(summaryStructure):
    type = 0b11010101
    _fields_ = [
        (pint.sint8_t, 'Type'),
        (dyn.array(pint.uint8_t, 2), 'Value'),
    ]
@d_packet.define
class d_fixext4(summaryStructure):
    type = 0b11010110
    _fields_ = [
        (pint.sint8_t, 'Type'),
        (dyn.array(pint.uint8_t, 4), 'Value'),
    ]
@d_packet.define
class d_fixext8(summaryStructure):
    type = 0b11010111
    _fields_ = [
        (pint.sint8_t, 'Type'),
        (dyn.array(pint.uint8_t, 8), 'Value'),
    ]
@d_packet.define
class d_fixext16(summaryStructure):
    type = 0b11011000
    _fields_ = [
        (pint.sint8_t, 'Type'),
        (dyn.array(pint.uint8_t, 16), 'Value'),
    ]

@d_packet.define
class d_ext8(summaryStructure):
    type = 0b11000111
    _fields_ = [(pint.uint8_t, 'Value'), (pint.sint8_t, 'Type')]
@d_packet.define
class d_ext16(summaryStructure):
    type = 0b11001000
    _fields_ = [(pint.uint16_t, 'Value'), (pint.sint8_t, 'Type')]
@d_packet.define
class d_ext32(summaryStructure):
    type = 0b11001001
    _fields_ = [(pint.uint32_t, 'Value'), (pint.sint8_t, 'Type')]

if __name__ == '__main__':
    import types
    import operator,functools,itertools

    res = [130,196,4,116,121,112,101,196,7,119,111,114,107,101,114,115, 196,4,100,97,116,97,145,130,196,8,119,111,114,107,101,114,105,100, 196,5,115,116,100,46,49,196,5,115,108,111,116,115,160]
    res = str().join(map(chr,res))

    # https://github.com/msgpack/msgpack-python/blob/master/test/test_format.py
    #res = b"\x96" b"\xde\x00\x00" b"\xde\x00\x01\xc0\xc2" b"\xde\x00\x02\xc0\xc2\xc3\xc2" b"\xdf\x00\x00\x00\x00" b"\xdf\x00\x00\x00\x01\xc0\xc2" b"\xdf\x00\x00\x00\x02\xc0\xc2\xc3\xc2"
    _fixnum = res = b"\x92\x93\x00\x40\x7f\x93\xe0\xf0\xff"
    _fixarray = res = b"\x92\x90\x91\x91\xc0"
    _fixraw = res = b"\x94\xa0\xa1a\xa2bc\xa3def"
    _fixmap = res = b"\x82\xc2\x81\xc0\xc0\xc3\x81\xc0\x80"
    _unsignedint = res = b"\x99\xcc\x00\xcc\x80\xcc\xff\xcd\x00\x00\xcd\x80\x00" b"\xcd\xff\xff\xce\x00\x00\x00\x00\xce\x80\x00\x00\x00" b"\xce\xff\xff\xff\xff"
    _signedint = res = b"\x99\xd0\x00\xd0\x80\xd0\xff\xd1\x00\x00\xd1\x80\x00" b"\xd1\xff\xff\xd2\x00\x00\x00\x00\xd2\x80\x00\x00\x00" b"\xd2\xff\xff\xff\xff"
    _raw = res = b"\x96\xda\x00\x00\xda\x00\x01a\xda\x00\x02ab\xdb\x00\x00" b"\x00\x00\xdb\x00\x00\x00\x01a\xdb\x00\x00\x00\x02ab"
    _array = res = b"\x96\xdc\x00\x00\xdc\x00\x01\xc0\xdc\x00\x02\xc2\xc3\xdd\x00" b"\x00\x00\x00\xdd\x00\x00\x00\x01\xc0\xdd\x00\x00\x00\x02" b"\xc2\xc3"
    _map = res = b"\x96" b"\xde\x00\x00" b"\xde\x00\x01\xc0\xc2" b"\xde\x00\x02\xc0\xc2\xc3\xc2" b"\xdf\x00\x00\x00\x00" b"\xdf\x00\x00\x00\x01\xc0\xc2" b"\xdf\x00\x00\x00\x02\xc0\xc2\xc3\xc2"

    x = packet(source=ptypes.prov.string(res))
    x=x.l
