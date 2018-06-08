import ptypes
from ptypes import pint,pfloat,dyn,pstruct

class Header(object): pass

class Machine(pint.enum, pint.uint16_t):
    _values_ = [
        ('UNKNOWN', 0x0000), ('AM33', 0x01d3), ('AMD64', 0x8664), ('ARM', 0x01c0),
        ('EBC', 0x0ebc), ('I386', 0x014c), ('IA64', 0x0200), ('M32R', 0x9041),
        ('MIPS16', 0x0266), ('MIPSFPU', 0x0366), ('MIPSFPU16', 0x0466), ('POWERPC', 0x01f0),
        ('POWERPCFP', 0x01f1), ('R4000', 0x0166), ('SH3', 0x01a2), ('SH3DSP', 0x01a3),
        ('SH4', 0x01a6), ('SH5', 0x01a8), ('THUMB', 0x01c2), ('WCEMIPSV2', 0x0169),
    ]

## primitives
byte = dyn.clone(pint.uint8_t)
word = dyn.clone(pint.uint16_t)
dword = dyn.clone(pint.uint32_t)
float = dyn.clone(pfloat.single)
double = dyn.clone(pfloat.double)

uint8 = dyn.clone(pint.uint8_t)
int8 = dyn.clone(pint.int8_t)
int16 = dyn.clone(pint.int16_t)
uint16 = dyn.clone(pint.uint16_t)
int32 = dyn.clone(pint.int32_t)
uint32 = dyn.clone(pint.uint32_t)
uint64 = dyn.clone(pint.uint64_t)

class off_t(pint.uint32_t): pass
class addr_t(pint.uint32_t): pass

import datetime
class TimeDateStamp(uint32):
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0)
    def details(self):
        x = self.epoch + datetime.timedelta( seconds=int(self) )
        return x.strftime('%Y-%m-%d %H:%M:%S')
    def summary(self):
        return '{:#x} {!r}'.format(self.int(), self.details())

class IMAGE_COMDAT_SELECT(ptypes.pint.enum, byte):
    _values_ = [
        ('NODUPIC', 1),
        ('ANY', 2),
        ('SAME_SIZE', 3),
        ('EXACT_MATCH', 4),
        ('ASSOCIATIVE', 5),
        ('LARGEST', 6)
    ]

class rfc4122(pstruct.type):
    class _Data1(pint.bigendian(pint.uint32_t)):
        def summary(self):
            return '{:08x}'.format(self.int())

    class _Data2and3(pint.bigendian(pint.uint16_t)):
        def summary(self):
            return '{:04x}'.format(self.int())

    class _Data4(pint.bigendian(pint.uint64_t)):
        def summary(self):
            res = list(self.serialize())
            d1 = ''.join(map('{:02x}'.format,map(ord,res[:2])) )
            d2 = ''.join(map('{:02x}'.format,map(ord,res[2:])) )
            return '-'.join((d1,d2))

    _fields_ = [
        (_Data1, 'Data1'),
        (_Data2and3, 'Data2'),
        (_Data2and3, 'Data3'),
        (_Data4, 'Data4'),
    ]

    def summary(self, **options):
        if self.initializedQ():
            return '{{Data1-Data2-Data3-Data4}} {:s}'.format(self.str())
        return '{{Data1-Data2-Data3-Data4}} {{????????-????-????-????-????????????}}'

    def str(self):
        d1 = '{:08x}'.format(self['Data1'].int())
        d2 = '{:04x}'.format(self['Data2'].int())
        d3 = '{:04x}'.format(self['Data3'].int())
        _ = list(self['Data4'].serialize())
        d4 = ''.join( map('{:02x}'.format,map(ord,_[:2])) )
        d5 = ''.join( map('{:02x}'.format,map(ord,_[2:])) )
        return '{{{:s}}}'.format('-'.join((d1,d2,d3,d4,d5)))

class GUID(rfc4122):
    _fields_ = [
        (bo(t), n) for bo, (t, n) in zip((pint.littleendian, pint.littleendian, pint.littleendian, pint.bigendian), rfc4122._fields_)
    ]
