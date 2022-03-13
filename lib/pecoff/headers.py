import ptypes, datetime, time, logging
from ptypes import pstruct, parray, ptype, dyn, pstr, pint, pfloat, pbinary

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
def LocateBaseAddress(self):
    """Return the base object of the executable. This is used to find the base address."""
    try:
        nth = self.getparent(ptype.boundary)
    except ValueError as msg:
        api = getattr(self.source, '__api__', None)

        # ptypes.provider.Ida
        if hasattr(api, 'get_imagebase'):
            return api.get_imagebase()

        nth = self.getparent(None)
        logging.warning("Unable to identify a boundary for calculating the base address from {:s} and using {:s}.".format(self.instance(), nth.instance()), exc_info=True)
    return nth.getoffset()

def LocateHeader(self):
    """Return the executable sub-header. This will return the executable main header."""
    try:
        nth = self.getparent(Header)
    except ValueError as msg:
        api = getattr(self.source, '__api__', None)

        nth = self.getparent(None)
        logging.warning("Unable to locate the header for the provided".format(self.instance(), nth.instance()), exc_info=True)
    return nth

## types of relative pointers in the executable
def CalculateRelativeAddress(self, address):
    """given a va, returns offset relative to the baseaddress"""
    base = LocateBaseAddress(self)

    # file
    if issubclass(self.source.__class__, ptypes.provider.fileobj):
        pe = LocateHeader(self)
        section = pe['Sections'].getsectionbyaddress(address)
        return base + section.getoffsetbyaddress(address)

    # memory
    return base + address

def CalculateRelativeOffset(self, offset):
    """return an offset relative to the baseaddress"""
    base = LocateBaseAddress(self)

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
    offset = address - header['OptionalHeader']['ImageBase'].int()

    base = LocateBaseAddress(header)

    # file
    if issubclass(self.source.__class__, ptypes.provider.fileobj):
        pe = LocateHeader(self)
        section = pe['Sections'].getsectionbyaddress(offset)
        return base + section.getoffsetbyaddress(offset)

    # memory
    return base + offset

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

class IMAGE_FILE_MACHINE_(pint.enum, WORD):
    '''IMAGE_FILE_HEADER.Machine'''
    _values_ = [
        ('UNKNOWN', 0x0000),        # Unknown
        ('TARGET_HOST', 0x0001),    # Interacts with the host and not a WOW64 guest
        ('I386', 0x014c),           # Intel 386
        ('I860', 0x014d),           # Intel i860
        ('R3000BE', 0x0160),        # MIPS R3000 big-endian
        ('R3000', 0x0162),          # MIPS R3000 little-endian,
        ('R4000', 0x0166),          # MIPS R4000 little-endian
        ('R10000', 0x0168),         # MIPS R10000 little-endian
        ('WCEMIPSV2', 0x0169),      # MIPS little-endian WCE v2
        ('ALPHAOLD', 0x0183),       # Alpha AXP (old)
        ('ALPHA', 0x0184),          # Alpha AXP
        ('SH3', 0x01a2),            # (Hitachi) SH3 little-endian
        ('SH3DSP', 0x01a3),         # (Hitachi) SH3DSP
        ('SH3E', 0x01a4),           # (Hitachi) SH3E little-endian
        ('SH4', 0x01a6),            # (Hitachi) SH4 little-endian
        ('SH5', 0x01a8),            # (Hitachi) SH5
        ('ARM', 0x01c0),            # ARM Little-Endian
        ('THUMB', 0x01c2),          # ARM Thumb/Thumb-2 Little-Endian
        ('ARM2', 0x01c4),           # ARM Thumb-2 Little-Endian
        ('AM33', 0x01d3),           # (Matsushita) TAM33BD
        ('POWERPC', 0x01f0),        # IBM PowerPC Little-Endian
        ('POWERPCFP', 0x01f1),      # IBM POWERPC with floating-point
        ('IA64', 0x0200),           # Intel IA64
        ('MIPS16', 0x0266),         # MIPS
        ('ALPHA64', 0x0284),        # ALPHA AXP64 (64-bit)
        ('MIPSFPU', 0x0366),        # MIPS with FPU
        ('MIPSFPU16', 0x0466),      # MIPS16 with FPU
        ('TRICORE', 0x0520),        # Infineon
        ('CEF', 0x0cef),            # CEF
        ('EBC', 0x0ebc),            # EFI Byte Code
        ('AMD64', 0x8664),          # AMD64 (K8)
        ('M32R', 0x9041),           # M32R little-endian
        ('ARM64', 0xaa64),          # ARM64 Little-Endian
        ('CEE', 0xc0ee),            # CEE (Common Instruction Language)
    ]

    def Architecture(self):
        '''Return the word size for the stored machine type.'''
        sixteen = {'MIPS16', 'MIPSFPU', 'MIPSFPU16'}
        thirtytwo = {'I386', 'R3000BE', 'R3000', 'WCEMIPSV2', 'ALPHAOLD', 'ALPHA', 'SH3', 'SH3DSP', 'SH3E', 'SH4', 'SH5', 'ARM', 'THUMB', 'ARM2', 'AM33', 'POWERPC', 'POWERPCFP', 'TRICORE', 'CEF', 'M32R'}
        sixtyfour = {'I860', 'R4000', 'R10000', 'IA64', 'ALPHA64', 'AMD64', 'ARM64'}
        variable = {'EBC', 'CEE'}

        name = self.str()
        if name in sixteen:
            return 16
        elif name in thirtytwo:
            return 32
        elif name in sixtyfour:
            return 64
        return 8 * ptypes.Config.integer.size

    def Order(self):
        '''Return the byteorder (endianness) for the stored machine type.'''
        big_or_mixed = {'R3000BE', 'ALPHAOLD', 'ALPHA', 'SH5', 'MIPS16', 'ALPHA64', 'MIPSFPU', 'MIPSFPU16', 'EBC', 'CEE'}
        little = {'SH3', 'SH3DSP', 'SH3E', 'SH4', 'ARM', 'THUMB', 'ARM2', 'AM33', 'POWERPC', 'POWERPCFP', 'IA64', 'TRICORE', 'CEF', 'AMD64', 'M32R', 'ARM64'}

        name = self.str()
        if name in big_or_mixed:
            return 'big'
        elif name in little:
            return 'little'
        return 'unknown'

class IMAGE_FILE_(pbinary.flags):
    '''IMAGE_FILE_HEADER.Characteristics'''
    _fields_ = [
        (1, 'BYTES_REVERSED_HI'),
        (1, 'UP_SYSTEM_ONLY'),
        (1, 'DLL'),
        (1, 'SYSTEM'),
        (1, 'NET_RUN_FROM_SWAP'),
        (1, 'REMOVABLE_RUN_FROM_SWAP'),
        (1, 'DEBUG_STRIPPED'),
        (1, '32BIT_MACHINE'),
        (1, 'BYTES_REVERSED_LO'),
        (1, 'reserved_9'),
        (1, 'LARGE_ADDRESS_AWARE'),
        (1, 'AGGRESSIVE_WS_TRIM'),
        (1, 'LOCAL_SYMS_STRIPPED'),
        (1, 'LINE_NUMS_STRIPPED'),
        (1, 'EXECUTABLE_IMAGE'),
        (1, 'RELOCS_STRIPPED'),
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

class IMPORT_TYPE(pbinary.enum):
    length, _values_ = 2, [
        ('CODE', 0),
        ('DATA', 1),
        ('CONST', 2),
    ]

class IMPORT_NAME_TYPE(pbinary.enum):
    length, _values_ = 3, [
        ('ORDINAL', 0),
        ('NAME', 1),
        ('NAME_NOPREFIX', 2),
        ('NAME_UNDECORATE', 3),
    ]

@pbinary.littleendian
class IMAGE_IMPORT_TYPE_INFORMATION(pbinary.struct):
    _fields_ = [
        (11, 'Reserved'),
        (IMPORT_NAME_TYPE, 'Name'),
        (IMPORT_TYPE, 'Type'),
    ]
