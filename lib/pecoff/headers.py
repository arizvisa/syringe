import ptypes, datetime, time
from ptypes import pstruct,parray,ptype,dyn,pstr,pint,pfloat,pbinary

## primitives
byte = dyn.clone(pint.uint8_t)
word = dyn.clone(pint.uint16_t)
dword = dyn.clone(pint.uint32_t)
float = dyn.clone(pfloat.single)
double = dyn.clone(pfloat.double)

uint0 = dyn.clone(pint.uint_t)
int0 = dyn.clone(pint.int_t)
uint8 = dyn.clone(pint.uint8_t)
int8 = dyn.clone(pint.int8_t)
int16 = dyn.clone(pint.int16_t)
uint16 = dyn.clone(pint.uint16_t)
int32 = dyn.clone(pint.int32_t)
uint32 = dyn.clone(pint.uint32_t)
uint64 = dyn.clone(pint.uint64_t)

class off_t(pint.uint32_t): pass
class addr_t(pint.uint32_t): pass

class VOID(ptype.undefined): pass
class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class ULONGLONG(pint.uint64_t): pass

### locating particular parts of the executable
def LocateBase(self):
    """Return the base object of the executable. This is used to find the base address."""
    try:
        nth = self.getparent(ptype.boundary)
    except ValueError as msg:
        items = [item for item in self.backtrace(fn=lambda item: item)]
        nth = items[-1]
    return nth

def LocateHeader(self):
    """Return the executable sub-header. This will return the executable main header."""
    try:
        nth = self.getparent(Header)
    except ValueError as msg:
        items = [item for item in self.backtrace(fn=lambda item: item)]
        nth = items[-1]
    return nth

## types of relative pointers in the executable
def CalculateRelativeAddress(self, address):
    """given a va, returns offset relative to the baseaddress"""
    base = LocateBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.fileobj):
        pe = LocateHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def CalculateRelativeOffset(self, offset):
    """return an offset relative to the baseaddress"""
    base = LocateBase(self).getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.fileobj):
        return base + offset

    # memory
    pe = LocateHeader(self)
    section = pe['Sections'].getsectionbyoffset(offset)
    o = offset - section['PointerToRawData'].int()
    return base + section['VirtualAddress'].int() + o

def CalculateRealAddress(self, address):
    """given an rva, return offset relative to the baseaddress"""
    header = LocateHeader(self)
    base = LocateBase(header)
    address -= header['OptionalHeader']['ImageBase'].int()
    base = base.getoffset()

    # file
    if issubclass(self.source.__class__, ptypes.provider.fileobj):
        pe = LocateHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

## ptypes closures
def realaddress(target, **kwds):
    """Returns a pointer to /target/ where value is an rva"""
    kwds.setdefault('__name__', 'realaddress')
    if 'type' in kwds:
        return dyn.opointer(target, CalculateRealAddress, kwds.pop('type'), **kwds)
    return dyn.opointer(target, CalculateRealAddress, **kwds)

def fileoffset(target, **kwds):
    """Returns a pointer to /target/ where value is a fileoffset"""
    kwds.setdefault('__name__', 'fileoffset')
    if 'type' in kwds:
        return dyn.opointer(target, CalculateRelativeOffset, kwds.pop('type'), **kwds)
    return dyn.opointer(target, CalculateRelativeOffset, **kwds)
def virtualaddress(target, **kwds):
    """Returns a pointer to /target/ where value is a va"""
    kwds.setdefault('__name__', 'virtualaddress')
    if 'type' in kwds:
        return dyn.opointer(target, CalculateRelativeAddress, kwds.pop('type'), **kwds)
    return dyn.opointer(target, CalculateRelativeAddress, **kwds)

## core header types
class Header(object): pass

class Machine(pint.enum, WORD):
    _values_ = [
        ('UNKNOWN', 0x0000), ('AM33', 0x01d3), ('AMD64', 0x8664), ('ARM', 0x01c0),
        ('EBC', 0x0ebc), ('I386', 0x014c), ('IA64', 0x0200), ('M32R', 0x9041),
        ('MIPS16', 0x0266), ('MIPSFPU', 0x0366), ('MIPSFPU16', 0x0466), ('POWERPC', 0x01f0),
        ('POWERPCFP', 0x01f1), ('R4000', 0x0166), ('SH3', 0x01a2), ('SH3DSP', 0x01a3),
        ('SH4', 0x01a6), ('SH5', 0x01a8), ('THUMB', 0x01c2), ('WCEMIPSV2', 0x0169),
    ]

class TimeDateStamp(DWORD):
    def datetime(self):
        res = self.int()
        epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        delta = datetime.timedelta(seconds=res)
        return epoch + delta
    def details(self):
        tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone)))
        res = self.datetime().astimezone(tzinfo)
        return res.isoformat()
    def summary(self):
        tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone)))
        res = self.datetime().astimezone(tzinfo)
        return '({:#0{:d}x}) {!s}'.format(self.int(), 2 + 2 * self.size(), res)

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
        def str(self):
            res = 2 * self.size()
            return "{:0{:d}x}".format(self.int(), res)
        def summary(self):
            return self.str()

    class _Data2and3(pint.bigendian(pint.uint16_t)):
        def str(self):
            res = 2 * self.size()
            return "{:0{:d}x}".format(self.int(), res)
        def summary(self):
            return self.str()

    class _Data4(pint.bigendian(pint.uint64_t)):
        def str(self):
            res = bytearray(self.serialize())
            d1 = ''.join(map('{:02x}'.format, res[:2]))
            d2 = ''.join(map('{:02x}'.format, res[2:]))
            return '-'.join([d1, d2])
        def summary(self):
            return self.str()

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
        res = bytearray(self['Data4'].serialize())
        d4 = ''.join(map('{:02x}'.format,res[:2]))
        d5 = ''.join(map('{:02x}'.format,res[2:]))
        return '{{{:s}}}'.format('-'.join((d1,d2,d3,d4,d5)))

class GUID(rfc4122):
    _fields_ = [
        (bo(t), n) for bo, (t, n) in zip((pint.littleendian, pint.littleendian, pint.littleendian, pint.bigendian), rfc4122._fields_)
    ]
