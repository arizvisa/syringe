import sys, logging, functools, ptypes
from ptypes import pstruct, parray, ptype, dyn, pstr, pbinary, utils
from ..headers import *

from . import headers

### DataDirectory entry
class IMAGE_DATA_DIRECTORY(headers.IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(virtualaddress)

@pbinary.littleendian
class CORIMAGE_FLAGS_(pbinary.flags):
    _fields_ = [
        (15, 'reserved_0'),
        (1, 'TRACKDEBUGDATA'),
        (11, 'reserved_17'),
        (1, 'NATIVE_ENTRYPOINT'),
        (1, 'STRONGNAMESIGNED'),
        (1, 'IL_LIBRARY'),
        (1, '32BITREQUIRED'),
        (1, 'ILONLY'),
    ]

class StreamHdr(pstruct.type):
    class _Offset(ptype.rpointer_t):
        _value_ = pint.uint32_t
        def _baseobject_(self):
            return self.getparent(MetaDataRoot)
        def _object_(self):
            res = self.getparent(StreamHdr)
            cb = res['Size'].int()
            t = Stream.withdefault(res['Name'].str(), blocksize=lambda s, cb=cb: cb)
            if issubclass(t, parray.block):
                return dyn.clone(t, blocksize=lambda s, cb=cb: cb)
            return t

    _fields_ = [
        (_Offset, 'Offset'),
        (pint.uint32_t, 'Size'),
        (pstr.szstring, 'Name'),
        (dyn.align(4), 'aligned(Name)'),
    ]

    def Name(self):
        return self['Name'].str()

    def Size(self):
        return self['Size'].int()

class MetaDataRoot(pstruct.type):
    class _Signature(pint.uint32_t):
        def properties(self):
            res = super(MetaDataRoot._Signature, self).properties()
            if self.initializedQ():
                res['valid'] = self.valid()
            return res

        def valid(self):
            return self.int() == self.default().int()

        @classmethod
        def default(cls):
            return cls().set(0x424a5342)

        def summary(self):
            return "{:#0{:d}x} ({:d}) : {!s}".format(self.int(), 2 + 2 * self.size(), self.int(), self.serialize())

    class _StreamHeaders(parray.type):
        _object_ = StreamHdr

        def enumerate(self):
            for index, item in enumerate(self):
                yield index, item
            return

        def iterate(self):
            for _, item in self.enumerate():
                yield item
            return

        def Get(self, name):
            iterable = (stream for stream in self if stream.Name() == name)
            try:
                result = next(iterable)
            except StopIteration:
                raise NameError(name)
            return result

    def __StreamHeaders(self):
        res = self['Streams'].li.int()
        return dyn.clone(self._StreamHeaders, length=res)

    def __StreamData(self):
        cb = self.getparent(IMAGE_DATA_DIRECTORY)['Size'].int()
        total = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        res = max(0, cb - total)
        return dyn.block(res)

    @pbinary.littleendian
    class StorageFlags(pbinary.flags):
        _fields_ = [
            (15, 'Reserved'),
            (1, 'ExtraData'),
        ]

    _fields_ = [
        (_Signature, 'Signature'),
        (pint.uint16_t, 'MajorVersion'),
        (pint.uint16_t, 'MinorVersion'),
        (pint.uint32_t, 'Reserved'),
        (pint.uint32_t, 'Length'),
        (lambda self: dyn.clone(pstr.string, length=self['Length'].li.int()), 'Version'),
        (dyn.align(4), 'aligned(Version)'),
        (StorageFlags, 'Flags'),
        (pint.uint16_t, 'Streams'),
        (__StreamHeaders, 'StreamHeaders'),
        (__StreamData, 'StreamData'),
    ]

    def byname(self, name):
        iterable = (item for item in self['StreamHeaders'].iterate() if item['Name'].str() == name)
        try:
            result = next(iterable)
        except StopIteration:
            raise NameError(name)
        return result

## Resource directory structures
class EncodedInteger(parray.terminated):
    _object_ = pint.uint8_t
    def isTerminator(self, value):
        return value.int() & 0x80 == 0
    def int(self):
        res = 0
        for item in self:
            res *= 0x80
            res += item.int() & 0x7f
        return res
    def summary(self):
        res = self.int()
        return "{:s} -> {:#0{:d}x} ({:d})".format(super(EncodedInteger, self).summary(), res, 2+self.blocksize()*2, res)

class ResourceString(pstruct.type):
    _fields_ = [
        (EncodedInteger, 'Length'),
        (lambda self: dyn.clone(pstr.string, length=self['Length'].li.int()), 'Name'),
    ]
    def str(self):
        return self['Name'].str()
    def summary(self):
        return "{:d} {!r}".format(self['Length'].int(), self['Name'].str())

class ResourceWString(pstruct.type):
    _fields_ = [
        (EncodedInteger, 'Length'),
        (lambda self: dyn.clone(pstr.wstring, length=self['Length'].li.int() // 2), 'Name'),
        (lambda self: dyn.block(self['Length'].li.int() % 2), 'Padding'),
    ]
    def str(self):
        return self['Name'].str()
    def summary(self):
        return "{:d} {!r}".format(self['Length'].int(), self['Name'].str())

## Resource directory headers
class ResourceFileType(ptype.definition): cache = {}

class ResourceManagerHeader(pstruct.type):
    _fields_ = [
        #(pint.uint32_t, 'Magic'),
        (pint.uint32_t, 'Version'),
        (pint.uint32_t, 'Size'),
        (lambda self: dyn.blockarray(ResourceString, self['Size'].li.int()), 'Parsers'),
    ]

class ResourceReaderHeader(pstruct.type):
    class _Types(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'Count'),
            (lambda self: dyn.array(ResourceString, self['Count'].li.int()), 'Name'),
        ]
    def __Padding(self):
        cb = 0

        ri = self.getparent(ResourceInfo)
        cb += ri['Magic'].li.size()

        rfi = self.getparent(ResourceFileInfo)
        cb += rfi['Manager'].li.size()

        cb += sum(self[fld].li.size() for fld in ['Version', 'Count', 'Types'])

        top = ri.getoffset() + ri['Size'].li.size()
        bottom = top + cb
        res = (bottom - top) & 7
        return dyn.block((8 - res) if res > 0 else 0)

    _fields_ = [
        (pint.uint32_t, 'Version'),
        (pint.uint32_t, 'Count'),
        (_Types, 'Types'),
        (__Padding, 'Padding'),

        (lambda self: dyn.array(pint.uint32_t, self['Count'].li.int()), 'Hash'),
        (lambda self: dyn.array(pint.uint32_t, self['Count'].li.int()), 'NameOffset'),
        (pint.uint32_t, 'DataOffset'),
    ]

class ResourceReaderName(pstruct.type):
    _fields_ = [
        (ResourceWString, 'Name'),
        (pint.uint32_t, 'Offset'),
    ]

class ResourceReaderData(pstruct.type):
    _fields_ = [
        (EncodedInteger, 'Type'),
        (EncodedInteger, 'Length'),
        (lambda self: dyn.block(self['Length'].li.int()), 'Blob'),
    ]

@ResourceFileType.define
class ResourceFileInfo(pstruct.type):
    type = 0xbeefcace

    class ResourceData(ptype.encoded_t): pass
    class _ResourceData(pstruct.type):
        def ResourceCount(type):
            def result(self, type=type):
                res = self.getparent(ResourceFileInfo)
                header = res['Reader'].li
                return dyn.array(type, header['Count'].int())
            return result

        _fields_ = [
            (ResourceCount(ResourceReaderName), 'Names'),
            (ResourceCount(ResourceReaderData), 'Values'),
        ]

    def __Data(self):
        res = self.blocksize() - sum(self[fld].li.size() for fld in ['Manager', 'Reader'])
        return dyn.clone(self.ResourceData, _value_=dyn.block(res), _object_=self._ResourceData)

    _fields_ = [
        (ResourceManagerHeader, 'Manager'),
        (ResourceReaderHeader, 'Reader'),
        (__Data, 'Data'),
    ]

class ResourceInfo(pstruct.type):
    def __Padding(self):
        cb = self['Size'].li.size() + self['Size'].li.int()
        res = cb & 7
        return dyn.block((8 - res) if res > 0 else 0)

    class _Magic(pint.uint32_t):
        def Valid(self):
            return self.int() == 0xbeefcace

        def properties(self):
            res = super(ResourceInfo._Magic, self).properties()
            if self.initializedQ():
                res['Valid'] = self.Valid()
            return res

    def __Magic(self):
        res = self['Size'].li.int()
        return dyn.block(0) if res < 4 else self._Magic

    def __Info(self):
        res = self['Size'].li.int()
        if res < 4:
            return dyn.block(res - self['Magic'].li.size())
        return ResourceFileType.get(self['Magic'].int(), blocksize=lambda s, cb=res - self['Magic'].li.size(): cb)

    _fields_ = [
        (pint.uint32_t, 'Size'),
        (__Magic, 'Magic'),
        (__Info, 'Info'),
        (__Padding, 'Padding'),
    ]

    def Data(self):
        res = self['Size'].li.int()
        if self['Magic'].Valid():
            return self['Info']
        t = dyn.block(res)
        return self.new(t, offset=4, source=ptypes.prov.proxy(self)).li

class VtableFixup(pstruct.type):
    @pbinary.littleendian
    class COR_VTABLE_(pbinary.flags):
        _fields_ = [
            (11, 'UNUSED'),
            (1, 'CALL_MOST_DERIVED'),
            (1, 'FROM_UNMANAGED_RETAIN_APPDOMAIN'),
            (1, 'FROM_UNMANAGED'),
            (1, '64BIT'),
            (1, '32BIT'),
        ]

    def __Entry(self):
        self = self.getparent(VtableFixup)
        cls = self.__class__

        res = self['Type'].li
        if res['32BIT'] and res['64BIT']:
            logging.warning("{:s} : {:s} : Both 32-bit and 64-bit flag is set. Assuming 0-bit. : {!r}".format('.'.join((__name__,cls.__name__)), self.instance(), res.summary()))
            t = pint.uint_t
        elif not res['32BIT'] and not res['64BIT']:
            logging.warning("{:s} : {:s} : Neither 32-bit and 64-bit flag is set. Assuming 0-bit. : {!r}".format('.'.join((__name__,cls.__name__)), self.instance(), res.summary()))
            t = pint.uint_t
        else:
            t = pint.uint32_t if res['32BIT'] else pint.uint64_t if res['64BIT'] else pint.uint_t
        count = self['Size'].li.int()
        return dyn.array(t, count)

    _fields_ = [
        (virtualaddress(__Entry, type=uint32), 'VirtualAddress'),
        (pint.uint16_t, 'Size'),
        (COR_VTABLE_, 'Type'),
    ]

class IMAGE_COR20_HEADER(pstruct.type):
    def blocksize(self):
        return self['cb'].li.int()

    _fields_ = [
        (pint.uint32_t, 'cb'),
        (pint.uint16_t, 'MajorRuntimeVersion'),
        (pint.uint16_t, 'MinorRuntimeVersion'),

        (dyn.clone(IMAGE_DATA_DIRECTORY, _object_=MetaDataRoot), 'MetaData'),
        (CORIMAGE_FLAGS_, 'Flags'),
        (pint.uint32_t, 'EntryPoint'),

        (dyn.clone(IMAGE_DATA_DIRECTORY, _object_=lambda self: dyn.blockarray(ResourceInfo, self.getparent(IMAGE_DATA_DIRECTORY)['Size'].li.int())), 'Resources'),
        (IMAGE_DATA_DIRECTORY, 'StrongNameSignature'),

        (IMAGE_DATA_DIRECTORY, 'CodeManagerTable'),
        (dyn.clone(IMAGE_DATA_DIRECTORY, _object_=lambda self: dyn.blockarray(VtableFixup, self.getparent(IMAGE_DATA_DIRECTORY)['Size'].li.int())), 'VTableFixups'),
        (IMAGE_DATA_DIRECTORY, 'ExportAddressTableJumps'),

        (IMAGE_DATA_DIRECTORY, 'ManagedNativeHeader'),
    ]

### Enumerations
class TableType(pint.enum):
    '''A helper for mapping table-name to index.'''
    _values_ = [
        ('Module', 0),
        ('TypeRef', 1),
        ('TypeDef', 2),
        ('Field', 4),
        ('MethodDef', 6),
        ('Param', 8),
        ('InterfaceImpl', 9),
        ('MemberRef', 10),
        ('Constant', 11),
        ('CustomAttribute', 12),
        ('FieldMarshal', 13),
        ('DeclSecurity', 14),
        ('ClassLayout', 15),
        ('FieldLayout', 16),
        ('StandAloneSig', 17),
        ('EventMap', 18),
        ('Event', 20),
        ('PropertyMap', 21),
        ('Property', 23),
        ('MethodSemantics', 24),
        ('MethodImpl', 25),
        ('ModuleRef', 26),
        ('TypeSpec', 27),
        ('ImplMap', 28),
        ('FieldRVA', 29),
        ('Assembly', 32),
        ('AssemblyProcessor', 33),
        ('AssemblyOS', 34),
        ('AssemblyRef', 35),
        ('AssemblyRefProcessor', 36),
        ('AssemblyRefOS', 37),
        ('File', 38),
        ('ExportedType', 39),
        ('ManifestResource', 40),
        ('NestedClass', 41),
        ('GenericParam', 42),
        ('MethodSpec', 43),
        ('GenericParamConstraint', 44),
    ]

class SecurityAction(pint.enum, pint.uint16_t):
    _values_ = [
        ('Nil', 0),
        ('Request', 1),             # request
        ('Demand', 2),              # demand
        ('Assert', 3),              # assert
        ('Deny', 4),                # deny
        ('PermitOnly', 5),          # permitonly
        ('LinkDemand', 6),          # linkcheck
        ('InheritanceDemand', 7),   # inheritcheck
        ('RequestMinimum', 8),      # reqmin
        ('RequestOptional', 9),     # reqopt
        ('RequestRefuse', 10),      # reqrefuse
        ('PrejitGrant', 11),        # prejitgrant
        ('PrejitDenied', 12),
        ('NonCasDemand', 13),
        ('NonCasLinkDemand', 14),
        ('NonCasInheritance', 15),
    ]

class ELEMENT_TYPE(pint.enum, pint.uint8_t):
    _values_ = [
        ('ELEMENT_TYPE_END', 0x00),
        ('ELEMENT_TYPE_VOID', 0x01),
        ('ELEMENT_TYPE_BOOLEAN', 0x02),
        ('ELEMENT_TYPE_CHAR', 0x03),
        ('ELEMENT_TYPE_I1', 0x04),
        ('ELEMENT_TYPE_U1', 0x05),
        ('ELEMENT_TYPE_I2', 0x06),
        ('ELEMENT_TYPE_U2', 0x07),
        ('ELEMENT_TYPE_I4', 0x08),
        ('ELEMENT_TYPE_U4', 0x09),
        ('ELEMENT_TYPE_I8', 0x0a),
        ('ELEMENT_TYPE_U8', 0x0b),
        ('ELEMENT_TYPE_R4', 0x0c),
        ('ELEMENT_TYPE_R8', 0x0d),
        ('ELEMENT_TYPE_STRING', 0x0e),
        ('ELEMENT_TYPE_PTR', 0x0f),
        ('ELEMENT_TYPE_BYREF', 0x10),
        ('ELEMENT_TYPE_VALUETYPE', 0x11),
        ('ELEMENT_TYPE_CLASS', 0x12),
        ('ELEMENT_TYPE_VAR', 0x13),
        ('ELEMENT_TYPE_ARRAY', 0x14),
        ('ELEMENT_TYPE_GENERICINST', 0x15),
        ('ELEMENT_TYPE_TYPEDBYREF', 0x16),
        ('ELEMENT_TYPE_I', 0x18),
        ('ELEMENT_TYPE_U', 0x19),
        ('ELEMENT_TYPE_FNPTR', 0x1b),
        ('ELEMENT_TYPE_OBJECT', 0x1c),
        ('ELEMENT_TYPE_SZARRAY', 0x1d),
        ('ELEMENT_TYPE_MVAR', 0x1e),
        ('ELEMENT_TYPE_CMOD_REQD', 0x1f),
        ('ELEMENT_TYPE_CMOD_OPT', 0x20),
        ('ELEMENT_TYPE_INTERNAL', 0x21),
        ('ELEMENT_TYPE_MODIFIER', 0x40),
        ('ELEMENT_TYPE_SENTINEL', 0x41),
        ('ELEMENT_TYPE_PINNED', 0x45),
        ('ELEMENT_TYPE_CUSTOM(System.type)', 0x50),
        ('ELEMENT_TYPE_CUSTOM(boxed)', 0x51),
        ('ELEMENT_TYPE_RESERVED', 0x52),
        ('ELEMENT_TYPE_CUSTOM(FIELD)', 0x53),
        ('ELEMENT_TYPE_CUSTOM(PROPERTY)', 0x54),
        ('ELEMENT_TYPE_CUSTOM(enum)', 0x55),
    ]

class AssemblyHashAlgorithm(pint.enum, pint.uint32_t):
    _values_ = [
        ('None', 0x0000),
        ('MD5', 0x8003),
        ('SHA1', 0x8004),
    ]

### Base types
@pbinary.bigendian
class CInt(pbinary.struct):
    '''Compressed Integer'''
    class _next_x(pbinary.struct):
        class _length_x(pbinary.struct):
            _fields_ = [
                (6, 'upper'),
                (8, 'value'),
            ]

            def Get(self):
                res = self['upper'] << 8
                return res | self['value']

        class _length_xyz(pbinary.struct):
            _fields_ = [
                (1, 'ext'),
                (5, 'upper'),
                (24, 'value'),
            ]

            def Get(self):
                res = self['upper'] << 24
                return res | self['value']

        _fields_ = [
            (1, 'ext'),
            (lambda self: self._length_xyz if self['ext'] else self._length_x, 'length'),
        ]

        def Get(self):
            return self['length'].Get()

    _fields_ = [
        (1, 'ext'),
        (lambda self: self._next_x if self['ext'] else 7, 'length'),
    ]

    def Get(self):
        return self['length'].Get() if self['ext'] else self['length']
    int = Get

    def summary(self):
        res = self.Get()
        return "{:s} -> {:d} ({:#x})".format(ptypes.bitmap.repr(self.bitmap()), res, res)

class rfc4122(pstruct.type):
    class _Data1(pint.bigendian(pint.uint32_t)):
        def summary(self):
            return '{:08x}'.format(self.int())
    class _Data2and3(pint.bigendian(pint.uint16_t)):
        def summary(self):
            return '{:04x}'.format(self.int())
    class _Data4(pint.bigendian(pint.uint64_t)):
        def summary(self):
            res = bytearray(self.serialize())
            d1 = ''.join(map('{:02x}'.format,res[:2]))
            d2 = ''.join(map('{:02x}'.format,res[2:]))
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
        res = bytearray(self['Data4'].serialize())
        d4 = ''.join(map('{:02x}'.format,res[:2]))
        d5 = ''.join(map('{:02x}'.format,res[2:]))
        return '{{{:s}}}'.format('-'.join((d1,d2,d3,d4,d5)))

    def repr(self):
        return self.summary()

### Blob types
class SerString(pstruct.type):
    _fields_ = [
        (CInt, 'length'),
        (lambda self: dyn.clone(pstr.string, length=self['length'].li.Get()), 'string'),
    ]
    def Length(self):
        return self['length'].int()
    def String(self):
        return self['string']
    def str(self):
        res = self.String()
        return res.str()

    def summary(self):
        return '{:d} : {!r}'.format(self['length'].Get(), self['string'].str())

class SerBlock(pstruct.type):
    _fields_ = [
        (CInt, 'length'),
        (lambda self: dyn.block(self['length'].li.Get()), 'data'),
    ]
    def Length(self):
        return self['length'].int()
    def Data(self):
        return self['data']

    def summary(self):
        return '{:d} : {:s}'.format(self['length'].Get(), self['data'].summary())

class PermissionSet(pstruct.type):
    class Attribute(pstruct.type):
        _fields_ = [
            (SerString, 'String'),
            (SerBlock, 'Properties'),
        ]
    _fields_ = [
        (pint.uint8_t, 'period'),
        (CInt, 'count'),
        (lambda self: dyn.array(self.Attribute, self['count'].li.Get()), 'attributes'),
    ]

### Stream types
class Stream(ptype.definition): cache = {}

@Stream.define
class HStrings(parray.block):
    type = '#Strings'
    _object_ = pstr.szstring

    def Get(self, offset):
        return self.at(self.getoffset() + offset, recurse=False)

@Stream.define
class HUserStrings(parray.block):
    type = '#US'
    class _object_(pstruct.type):
        def __data(self):
            cb = self['length'].li.Get()
            return dyn.clone(pstr.wstring, length= cb // 2)

        _fields_ = [
            (CInt, 'length'),
            (__data, 'data'),
            (lambda self: dyn.block(self['length'].li.Get() & 1), r'\0'),
        ]
        def Length(self):
            return self['length'].int()
        def Data(self):
            return self['data']

    def Get(self, offset):
        return self.at(self.getoffset() + offset, recurse=False)

@Stream.define
class HGUID(parray.block):
    type = '#GUID'
    _object_ = rfc4122

    def Get(self, index):
        if index > 0:
            return self[index - 1]
        raise IndexError(index)

@Stream.define
class HBlob(parray.block):
    type = '#Blob'
    class _object_(pstruct.type):
        _fields_ = [
            (CInt, 'length'),
            (lambda self: dyn.block(self['length'].li.Get()), 'data'),
        ]
        def Length(self):
            return self['length'].int()
        def Data(self):
            return self['data']
        def int(self):
            data = self['data'].serialize()
            return functools.reduce(lambda agg, item: item | agg * 0x100, bytearray(data))
        def summary(self):
            return "({:d}) {:s}".format(self['length'].int(), self['data'].summary())

    def Get(self, offset):
        return self.at(self.getoffset() + offset, recurse=False)

### Mapping types
class ElementType(ptype.definition): cache = {}
@ElementType.define
class BOOLEAN(pint.uint8_t): type=2
@ElementType.define
class CHAR(pstr.char_t): type=3
@ElementType.define
class I1(pint.sint8_t): type=4
@ElementType.define
class U1(pint.uint8_t): type=5
@ElementType.define
class I2(pint.sint16_t): type=6
@ElementType.define
class U2(pint.uint16_t): type=7
@ElementType.define
class I4(pint.uint32_t): type=8
@ElementType.define
class U4(pint.uint32_t): type=9
@ElementType.define
class I8(pint.sint64_t): type=10
@ElementType.define
class U8(pint.uint64_t): type=11
@ElementType.define
class R4(pfloat.single): type=12
@ElementType.define
class R8(pfloat.double): type=13
@ElementType.define
class STRING(SerString): type=14
# FIXME: Implement some more ElementType definitions
# FIXME: Add a .summary() method for friendly output

class TableRow(ptype.encoded_t):
    def __getitem__(self, name):
        dereferenced = self.d.li
        return dereferenced.__getitem__(name)
    def repr(self):
        dereferenced = self.d.li
        return dereferenced.copy(offset=self.getoffset()).repr()
    def summary(self):
        dereferenced = self.d.li
        return dereferenced.copy(offset=self.getoffset()).summary()

class TableRows(parray.type):
    def Get(self, index):
        if index > 0:
            return self[index - 1]
        raise IndexError(index)

    def enumerate(self):
        for index, item in enumerate(self):
            yield index, item
        return

    def iterate(self):
        for _, item in enumerate(self):
            yield item
        return

class Tables(parray.type):
    length = 64
    def _object_(self):
        res = self.getparent(HTables)
        index, lengths = len(self.value), res['Rows'].li
        count = lengths[index].int()

        if count:
            cls = self.__class__
            logging.debug("{:s} : {:s} : Loading {:s}({:d}) table with {:d} rows. : {:d} of {:d}".format('.'.join((res.typename(),cls.__name__)), self.instance(), TableType.byvalue(index, 'undefined'), index, count, 1+len(self.value), self.length))

        rowtype = Table.withdefault(index, type=index)
        rowsize = rowtype.PreCalculateSize(res) if Table.has(index) else 0

        tr, tn = TableRow.__name__, TableType.byvalue(index, None)
        t = dyn.clone(TableRow, _object_=rowtype, _value_=dyn.block(rowsize), typename=classmethod(lambda cls: "{:s}({:s})".format(tr, tn) if tn else tr))
        return dyn.clone(TableRows, _object_=t, length=count, blocksize=(lambda s, cb=rowsize*count: cb))

    def __getindex__(self, index):
        string_types = (str, unicode) if sys.version_info.major < 3 else (str,)
        return TableType.byname(index) if isinstance(index, string_types) else index

    def enumerate(self):
        for index, table in enumerate(self):
            if len(table) > 0:
                yield index, table
            continue
        return

    def iterate(self):
        for _, item in self.enumerate():
            yield res
        return

@Stream.define
class HTables(pstruct.type):
    type = '#~'

    @pbinary.littleendian
    class HeapSizes(pbinary.flags):
        _fields_ = [
            (5, 'Unused'),
            (1, 'HBlob'),
            (1, 'HGUID'),
            (1, 'HStrings'),
        ]

    class BitVector(pbinary.array):
        _object_ = 1
        def index(self, index):
            res = len(self) - index
            return self[res - 1]
        def iterate(self, crit):
            return (index for index, value in enumerate(reversed(self)) if crit(value))

    class _Valid(BitVector):
        length = 64
        def iterate(self):
            return super(HTables._Valid, self).iterate(bool)
        def summary(self):
            return ', '.join(map('{:d}'.format, self.iterate()))

    class _Sorted(BitVector):
        length = 64
        def iterate(self):
            return super(HTables._Sorted, self).iterate(bool)

    class _RowLengths(parray.type):
        length = 64
        def _object_(self):
            res, index = self.getparent(HTables), len(self.value)
            present = res['Valid'].li.index
            return pint.uint32_t if present(index) else pint.uint_t

    def __padding_Tables(self):
        hdr = self.getparent(StreamHdr)
        cb = hdr['Size'].li.int()
        total = sum(self[fld].blocksize() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, cb - total))

    _fields_ = [
        (pint.uint32_t, 'Reserved_0'),
        (pint.uint8_t, 'MajorVersion'),
        (pint.uint8_t, 'MinorVersion'),
        (HeapSizes, 'HeapSizes'),
        (pint.uint8_t, 'Reserved_7'),
        (pbinary.littleendian(_Valid), 'Valid'),
        (pbinary.littleendian(_Sorted), 'Sorted'),
        (_RowLengths, 'Rows'),
        (Tables, 'Tables'),
        (__padding_Tables, 'padding(Tables)'),
    ]

    def Valid(self):
        res = self['Tables']
        for i in self['Valid'].iterate():
            yield res[i]
        return

    def Sorted(self):
        res = self['Tables']
        for i in self['Sorted'].iterate():
            yield res[i]
        return

### #~ tables
class Table(ptype.definition): cache = {}

## index types
class Index(ptype.generic): pass
class StreamIndex(Index, pint.uint_t): pass
class TableIndex(Index, pint.uint_t):
    type = None

    @classmethod
    def Tables(cls, index=0):
        raise NotImplementedError

    @classmethod
    def Of(cls, table):
        class IndexOf(cls):
            pass

        index = TableType.byname(table)
        def Tables(cls, index=index):
            return {index}

        IndexOf.type = index
        IndexOf.Tables = classmethod(Tables)
        return IndexOf

    def classname(self):
        try:
            name = TableType.byvalue(self.type)
        except KeyError:
            return self.typename() if self.type is None else "{:s}<{:s}>".format(self.typename(), self.type)
        return "{:s}<{:s}>".format(self.typename(), name)

    def blocksize(self):
        p = self.__HTables = self.__HTables if hasattr(self, '__HTables') else self.getparent(HTables)
        index, rows = self.type, p['Rows'].li
        count = rows[index].int()
        return 2 if count < 0x10000 else 4

    def __table__(self):
        p = self.getparent(Tables)
        return p[self.type]

    def dereference(self):
        table, index = self.__table__(), self.int()
        if 0 <= index < len(table):
            row = table[index]     # XXX: is this supposed to be an index - 1?
            return row.li
        raise IndexError(index)
        
    d = property(fget=dereference)

    def summary(self):
        try:
            description = self.dereference()
        except IndexError:
            description = None
        return "{:#0{:d}x} ({:d}) :{:s}".format(self.int(), 2 + 2 * self.size(), self.int(), "> {:s}".format(description.summary()) if description else "invalid index {:d} for table {:d}".format(self.int(), self.type))

class CodedIndex(Index):
    pass

class NameIndex(StreamIndex):
    type = 'HStrings'

    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HStrings'] else 2

    def __table__(self):
        p = self.getparent(MetaDataRoot)
        stream = p.byname('#Strings')
        return stream['Offset'].d

    def dereference(self):
        strings = self.__table__().li
        return strings.Get(self.int())
    d = property(fget=dereference)

    def str(self):
        result = self.dereference()
        return result.str()

    def summary(self):
        string = self.dereference()
        return "{:#0{:d}x} ({:d}) :> {:s}".format(self.int(), 2 + 2 * self.size(), self.int(), string.summary())

class GuidIndex(StreamIndex):
    type = 'HGUID'

    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HGUID'] else 2

    def __table__(self):
        p = self.getparent(MetaDataRoot)
        stream = p.byname('#GUID')
        return stream['Offset'].d

    def dereference(self):
        guids = self.__table__().li
        return guids.Get(self.int())
    d = property(fget=dereference)

    def str(self):
        try:
            result = self.dereference()
            string = result.str()
        except IndexError:
            raise ptypes.error.ItemNotFoundError(object, 'str', self.int())
        return string.upper()

    def summary(self):
        try:
            guid = self.dereference()
            string = guid.str()
        except IndexError:
            string = '...'
        return "{:#0{:d}x} ({:d}) :> {:s}".format(self.int(), 2 + 2 * self.size(), self.int(), string.upper())

class BlobIndex(StreamIndex):
    type = 'HBlob'

    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HBlob'] else 2

    def __table__(self):
        p = self.getparent(MetaDataRoot)
        stream = p.byname('#Blob')
        return stream['Offset'].d

    def dereference(self):
        blobs = self.__table__().li
        return blobs.Get(self.int())
    d = property(fget=dereference)

    def data(self):
        dereferenced = self.dereference()
        length, data = dereferenced.Length(), dereferenced.Data()
        if hasattr(self, '_object_'):
            return data.cast(self._object_, blocksize=lambda cb=length: cb)
        return data

    def summary(self):
        if hasattr(self, '_object_'):
            result = self.data()
            return "{:#0{:d}x} ({:d}) :> {:s}".format(self.int(), 2 + 2 * self.size(), self.int(), result.summary())
        blob = self.dereference()
        return "{:#0{:d}x} ({:d}) :> {:s}".format(self.int(), 2 + 2 * self.size(), self.int(), blob.summary())

## Encoded tags
class TaggedIndex(CodedIndex, pstruct.type):
    def __Index(self):
        htables = self.getparent(HTables)

        # get indices of all tables that tag can point into
        indices = self.Tables()

        # figure out the maximum number of rows for the tables specified by self.Tag
        res = htables['Rows'].li
        count = max(res[index].int() for index in indices)

        # return a uint16_t if the tagged index is able to store the maximum number of rows otherwise use a uint32_t
        return dyn.clone(pint.uint_t, length=1) if count < pow(2, 16 - self.Tag.length) else dyn.clone(pint.uint_t, length=3)

    @classmethod
    def Tables(cls):
        '''Returns the indices of every table that can be represent by this TaggedInex'''

        # grab all possible table names and table names specified by self.Tag
        all_Tables, tag_Tables = TableType.mapping(), cls.Tag.mapping()

        # grab the intersection of them as some table names specified by self.Tag might not exist or be defined
        res = {item for item in tag_Tables.keys()} & {item for item in all_Tables.keys()}

        # convert each table name specified by self.Tag into it's correct index.
        return {all_Tables[name] for name in res}

    class TagByte(pbinary.struct):
        _fields_ = [
            (lambda self: 8 - self.getparent(TaggedIndex).Tag.length, 'Index'),
            (lambda self: self.getparent(TaggedIndex).Tag, 'Tag'),
        ]

        def Get(self):
            return self.__field__('Tag').str()

        def Index(self):
            return self['Index']

        def summary(self):
            res = self.Index()
            return "Tag({:s}) : Index={:#x} ({:d})".format(self.Get(), res, res)

    _fields_ = [
        (TagByte, 'Tag'),
        (__Index, 'Index'),
    ]

    def __table__(self):
        raise NotImplementedError

        p = self.getparent(Tables)
        return p[self.type]

    def dereference(self):
        table, index = self.__table__(), self.int()
        if 0 <= index < len(table):
            row = table[index]     # XXX: is this supposed to be an index - 1?
            return row.li
        raise IndexError
    d = property(fget=dereference)

    # FIXME: we should dereference this index if TaggedIndex ever gets implemented
    def summary(self):
        res = self.Index()
        return "Tag({:s}) : Index={:#x} ({:d})".format(self['Tag'].Get(), res, res)

    def Index(self):
        res = self['Index'].int()
        res <<= 8 - self.Tag.length
        res |= self['Tag'].Index()
        return res

class TypeDefOrRef(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('TypeDef', 0),
            ('TypeRef', 1),
            ('TypeSpec', 2),
        ]

class HasConstant(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('Field', 0),
            ('Param', 1),
            ('Property', 2),
        ]

class HasCustomAttribute(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 5, [
            ('MethodDef', 0),
            ('Field', 1),
            ('TypeRef', 2),
            ('TypeDef', 3),
            ('Param', 4),
            ('InterfaceImpl', 5),
            ('MemberRef', 6),
            ('Module', 7),
            ('DeclSecurity', 8),      # labeled as "Permission" from the specification
            ('Property', 9),
            ('Event', 10),
            ('StandAloneSig', 11),
            ('ModuleRef', 12),
            ('TypeSpec', 13),
            ('Assembly', 14),
            ('AssemblyRef', 15),
            ('File', 16),
            ('ExportedType', 17),
            ('ManifestResource', 18),
        ]

class HasFieldMarshal(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 1, [
            ('Field', 0),
            ('Param', 1),
        ]

class HasDeclSecurity(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('TypeDef', 0),
            ('MethodDef', 1),
            ('Assembly', 2),
        ]

class MemberRefParent(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 3, [
            ('TypeDef', 0),
            ('TypeRef', 1),
            ('ModuleRef', 2),
            ('MethodDef', 3),
            ('TypeSpec', 4),
        ]

class HasSemantics(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 1, [
            ('Event', 0),
            ('Property', 1),
        ]

class MethodDefOrRef(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 1, [
            ('MethodDef', 0),
            ('MemberRef', 1),
        ]

class MemberForwarded(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 1, [
            ('Field', 0),
            ('MethodDef', 1),
        ]

class Implementation_ExportedType(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('File', 0),
            ('ExportedType', 1),
        ]

class Implementation_AssemblyRef(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('File', 0),
            ('AssemblyRef', 1),
        ]

class CustomAttributeType(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 3, [
            #('Not used', 0),
            #('Not used', 1),
            ('MethodDef', 2),
            ('MemberRef', 3),
            #('Not used', 4),
        ]

class ResolutionScope(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 2, [
            ('Module', 0),
            ('ModuleRef', 1),
            ('AssemblyRef', 2),
            ('TypeRef', 3),
        ]

class TypeOrMethodDef(TaggedIndex):
    class Tag(pbinary.enum):
        length, _values_ = 1, [
            ('TypeDef', 0),
            ('MethodDef', 1),
        ]

## Attributes and Flags
class TypeAttributes(pbinary.flags):
    class VisibilityMask(pbinary.enum):
        length, _values_ = 3, [
            ('NotPublic', 0),
            ('Public', 1),
            ('NestedPublic', 2),
            ('NestedPrivate', 3),
            ('NestedFamily', 4),
            ('NestedAssembly', 5),
            ('NestedFamANDAssem', 6),
            ('NestedFamORAssem', 7),
        ]
    class LayoutMask(pbinary.enum):
        length, _values_ = 2, [
            ('AutoLayout', 0),
            ('SequentialLayout', 1),
            ('ExplicitLayout', 2),
        ]
    class ClassSemanticsMask(pbinary.enum):
        length, _values_ = 1, [
            ('Class', 0),
            ('Interface', 1),
        ]
    class StringFormatMask(pbinary.enum):
        length, _values_ = 2, [
            ('AnsiClass', 0),
            ('UnicodeClass', 1),
            ('AutoClass', 2),
            ('CustomFormatClass', 3),
        ]
    _fields_ = [
        (8, 'Reserved'),
        (2, 'CustomStringFormat'),
        (1, 'Unused'),
        (1, 'BeforeFieldInit'),
        (1, 'Unused'),
        (1, 'HasSecurity'),
        (StringFormatMask, 'StringFormat'),
        (2, 'Unused'),
        (1, 'Serializeable'),
        (1, 'Import'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (1, 'Unused'),
        (1, 'Sealed'),
        (1, 'Abstract'),
        (1, 'Unused'),
        (ClassSemanticsMask, 'ClassSemantics'),
        (LayoutMask, 'ClassLayout'),
        (VisibilityMask, 'ClassVisibility'),
    ]

class FieldAttributes(pbinary.flags):
    class FieldAccessMask(pbinary.enum):
        length, _values_ = 3, [
            ('CompilerControlled', 0),
            ('Private', 1),
            ('FamANDAssem', 2),
            ('Assembly', 3),
            ('Family', 4),
            ('FAMOrAssme', 5),
            ('Public', 6),
        ]

    _fields_ = [
        (1, 'HasDefault'),
        (1, 'Unused'),
        (1, 'PInvokeImpl'),
        (1, 'HasFieldMarshal'),
        (1, 'Unused'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (1, 'HasFieldRVA'),
        (1, 'NotSerialized'),
        (1, 'Literal'),
        (1, 'InitOnly'),
        (1, 'Static'),
        (1, 'Unused'),
        (FieldAccessMask, 'FieldAccess'),
    ]

@pbinary.littleendian
class MethodImplAttributes(pbinary.flags):
    class CodeTypeMask(pbinary.enum):
        length, _values_ = 2, [
            ('IL', 0),
            ('Native', 1),
            ('OPTIL', 2),
            ('Runtime', 3),
        ]
    class ManagedMask(pbinary.enum):
        length, _values_ = 1, [
            ('Unmanaged', 1),
            ('Managed', 0),
        ]
    _fields_ = [
        (3, 'Unused'),
        (1, 'InternalCall'),
        (4, 'Unused'),
        (1, 'PreserveSig'),
        (1, 'Unused'),
        (1, 'Synchronized'),
        (1, 'ForwardRef'),
        (1, 'NoInlining'),
        (ManagedMask, 'Managed'),
        (CodeTypeMask, 'CodeType'),
    ]

@pbinary.littleendian
class MethodAttributes(pbinary.flags):
    class MemberAccessMask(pbinary.enum):
        length, _values_ = 3, [
            ('CompilerControlled', 0),
            ('Private', 1),
            ('FamANDAssem', 2),
            ('Assem', 3),
            ('Family', 4),
            ('FamORAssem', 5),
            ('Public', 6),
        ]
    class VtableLayoutMask(pbinary.enum):
        length, _values_ = 1, [
            ('ReuseSlot', 0),
            ('NewSlot', 1),
        ]
    _fields_ = [
        (1, 'RequiredSecObject'),
        (1, 'HasSecurity'),
        (1, 'PInvokeImpl'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (1, 'Abstract'),
        (1, 'Strict'),
        (VtableLayoutMask, 'VtableLayout'),
        (1, 'HideBySig'),
        (1, 'Virtual'),
        (1, 'Final'),
        (1, 'Static'),
        (1, 'UnmanagedExport'),
        (MemberAccessMask, 'MemberAccess'),
    ]

@pbinary.littleendian
class ParamAttributes(pbinary.flags):
    _fields_ = [
        (2, 'Unused'),
        (1, 'HasFieldMarshal'),
        (1, 'HasDefault'),
        (7, 'Unused'),
        (1, 'Optional'),
        (2, 'Unused'),
        (1, 'Out'),
        (1, 'In'),
    ]

@pbinary.littleendian
class EventAttributes(pbinary.flags):
    _fields_ = [
        (5, 'Unused'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (9, 'Unused'),
    ]

@pbinary.littleendian
class PropertyAttributes(pbinary.flags):
    _fields_ = [
        (3, 'Unused'),
        (1, 'Default'),
        (1, 'Unused'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (9, 'Unused'),
    ]

@pbinary.littleendian
class MethodSemanticsAttributes(pbinary.flags):
    _fields_ = [
        (10, 'Unused'),
        (1, 'Fire'),
        (1, 'RemoveOn'),
        (1, 'AddOn'),
        (1, 'Other'),
        (1, 'Getter'),
        (1, 'Setter'),
    ]

@pbinary.littleendian
class PInvokeAttributes(pbinary.flags):
    class CharSetMask(pbinary.enum):
        length, _values_ = 2, [
            ('CharSetNotSpec', 0),
            ('CharSetAnsi', 1),
            ('CharSetUnicode', 2),
            ('CharSetAuto', 3),
        ]
    class CallConvMask(pbinary.enum):
        length, _values_ = 3, [
            ('CallConvWinapi', 1),
            ('CallConvCdecl', 2),
            ('CallConvStdcall', 3),
            ('CallConvThiscall', 4),
            ('CallConvFastcall', 5),
        ]
    _fields_ = [
        (5, 'Unused'),
        (CallConvMask, 'CallConv'),
        (1, 'Unused'),
        (1, 'SupportsLastError'),
        (3, 'Unused'),
        (CharSetMask, 'CharSet'),
        (1, 'NoMangle'),
    ]

@pbinary.littleendian
class AssemblyFlags(pbinary.flags):
    class Reserved(pbinary.enum):
        length, _values_ = 2, []

    class HasPublicKey(pbinary.enum):
        length, _values_ = 1, [
            ('SideBySideCompatible', 0),
            ('HasPublicKey', 1),
        ]

    _fields_ = [
        (16, 'Unused'),
        (1, 'EnableJITcompileTracking'),
        (1, 'DisableJITcompileOptimizer'),
        (5, 'Unused'),
        (1, 'Retargetable'),
        (2, 'Unused'),
        (Reserved, 'Reserved'),
        (3, 'Unused'),
        (HasPublicKey, 'Compatibility'),
    ]

@pbinary.littleendian
class FileAttributes(pbinary.flags):
    class ContainsNoMetaData(pbinary.enum):
        length, _values_ = 1, [
            ('ContainsMetaData', 0),
            ('ContainsNoMetaData', 1),
        ]
    _fields_ = [
        (31, 'Unused'),
        (ContainsNoMetaData, 'ContainsNoMetaData'),
    ]

@pbinary.littleendian
class ManifestResourceAttributes(pbinary.flags):
    class VisibilityMask(pbinary.enum):
        length, _values_ = 3, [
            ('Public', 1),
            ('Private', 2),
        ]
    _fields_ = [
        (29, 'Unused'),
        (VisibilityMask, 'Visibility'),
    ]

@pbinary.littleendian
class GenericParamAttributes(pbinary.flags):
    class VarianceMask(pbinary.enum):
        length, _values_ = 2, [
            ('None', 0),
            ('Covariant', 1),
            ('Contravariant', 2),
        ]

    class SpecialConstraintMask(pbinary.enum):
        length, _values_ = 3, [
            ('ReferenceTypeConstraint', 1),
            ('NotNullableValueTypeConstraint', 2),
            ('DefaultConstructorConstraint', 4),
        ]

    _fields_ = [
        (11, 'Unused'),
        (SpecialConstraintMask, 'SpecialConstraint'),
        (VarianceMask, 'Variance'),
    ]

## table definitions
class PreCalculatableTable(ptype.generic):
    @classmethod
    def PreCalculateSize(cls, htables):
        rows, heapsizes = htables['Rows'].li, htables['HeapSizes'].li

        res = []
        for t, name in cls._fields_:
            instance = htables.new(t)
            if isinstance(instance, Index):
                if isinstance(instance, StreamIndex):
                    res.append(4 if heapsizes[instance.type] else 2)
                elif isinstance(instance, TableIndex):
                    res.append(2 if rows[instance.type].int() < 0x10000 else 4)
                elif isinstance(instance, CodedIndex):
                    count = max(rows[index].int() for index in instance.Tables())
                    res.append(2 if count < pow(2, 16 - instance.Tag.length) else 4)
                else:
                    raise TypeError((cls, instance, name))
                continue
            res.append(instance.a.blocksize())
        return sum(res)

@Table.define
class TModule(PreCalculatableTable, pstruct.type):
    type = 0
    _fields_ = [
        (pint.uint16_t, 'Generation'),
        (NameIndex, 'Name'),
        (GuidIndex, 'Mvid'),
        (GuidIndex, 'EncId'),
        (GuidIndex, 'EncBaseId'),
    ]

@Table.define
class TTypeRef(PreCalculatableTable, pstruct.type):
    type = 1
    _fields_ = [
        (ResolutionScope, 'ResolutionScope'),
        (NameIndex, 'TypeName'),
        (NameIndex, 'TypeNamespace'),
    ]
    def summary(self):
        return "Namespace={!r} Name={!r} : ResolutionScope={:s}".format(self['TypeNamespace'].str(), self['TypeName'].str(), self['ResolutionScope'].summary())

@Table.define
class TTypeDef(PreCalculatableTable, pstruct.type):
    type = 2
    _fields_ = [
        (TypeAttributes, 'Flags'),
        (NameIndex, 'TypeName'),
        (NameIndex, 'TypeNamespace'),
        (TypeDefOrRef, 'Extends'),
        (TableIndex.Of('Field'), 'FieldList'),
        (TableIndex.Of('MethodDef'), 'MethodList'),
    ]

@Table.define
class TField(PreCalculatableTable, pstruct.type):
    type = 4
    _fields_ = [
        (FieldAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Signature'),
    ]
    def summary(self):
        signature = self['Signature'].d
        if self['Flags'].int():
            return "Name={!r} Signature={:#0{:d}x} Flags={:s}".format(self['Name'].str(), signature.int(), 2 + 2 * signature.Length(), self['Flags'].summary())
        return "Name={!r} Signature={:#0{:d}x}".format(self['Name'].str(), signature.int(), 2 + 2 * signature.Length())

@Table.define
class TMethodDef(PreCalculatableTable, pstruct.type):
    type = 6
    _fields_ = [
        (pint.uint32_t, 'RVA'),
        (MethodImplAttributes, 'ImplFlags'),
        (MethodAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Signature'),
        (TableIndex.Of('Param'), 'ParamList'),
    ]

@Table.define
class TParam(PreCalculatableTable, pstruct.type):
    type = 8
    _fields_ = [
        (ParamAttributes, 'Flags'),
        (pint.uint16_t, 'Sequence'),
        (NameIndex, 'Name'),
    ]
    def summary(self):
        if self['Flags'].int():
            return "Sequence={:d} Name={!r} Flags={:s}".format(self['Sequence'].int(), self['Name'].str(), self['Flags'].summary())
        return "Sequence={:d} Name={!r}".format(self['Sequence'].int(), self['Name'].str())

@Table.define
class TInterfaceImpl(PreCalculatableTable, pstruct.type):
    type = 9
    _fields_ = [
        (TableIndex.Of('TypeDef'), 'Class'),
        (TypeDefOrRef, 'Interface'),
    ]

@Table.define
class TMemberRef(PreCalculatableTable, pstruct.type):
    type = 10
    _fields_ = [
        (MemberRefParent, 'Class'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Signature'),
    ]

@Table.define
class TConstant(PreCalculatableTable, pstruct.type):
    type = 11
    def __Value(self):
        try:
            type = self['Type'].li
            if type['ELEMENT_TYPE_STRING']:
                return dyn.clone(BlobIndex, _object_=pstr.wstring)
        except KeyError:
            pass
        return BlobIndex

    _fields_ = [
        (ELEMENT_TYPE, 'Type'),
        (pint.uint8_t, 'PaddingZero'),
        (HasConstant, 'Parent'),
        (__Value, 'Value'),
    ]

@Table.define
class TCustomAttribute(PreCalculatableTable, pstruct.type):
    type = 12
    def __Value(self):
        return BlobIndex

    _fields_ = [
        (HasCustomAttribute, 'Parent'),
        (CustomAttributeType, 'Type'),
        (__Value, 'Value'),
    ]

@Table.define
class TFieldMarshal(PreCalculatableTable, pstruct.type):
    type = 13
    _fields_ = [
        (HasFieldMarshal, 'Parent'),
        (BlobIndex, 'NativeType'),
    ]

@Table.define
class TDeclSecurity(PreCalculatableTable, pstruct.type):
    type = 14
    _fields_ = [
        (SecurityAction, 'Action'),
        (HasDeclSecurity, 'Parent'),
        (BlobIndex, 'PermissionSet'),
    ]

@Table.define
class TClassLayout(PreCalculatableTable, pstruct.type):
    type = 15
    _fields_ = [
        (pint.uint16_t, 'PackingSize'),
        (pint.uint32_t, 'ClassSize'),
        (TableIndex.Of('TypeDef'), 'Parent'),
    ]

@Table.define
class TFieldLayout(PreCalculatableTable, pstruct.type):
    type = 16
    _fields_ = [
        (pint.uint32_t, 'Offset'),
        (TableIndex.Of('Field'), 'Field'),
    ]

@Table.define
class TStandAloneSig(PreCalculatableTable, pstruct.type):
    type = 17
    _fields_ = [
        (BlobIndex, 'Signature'),
    ]
    def Signature(self):
        dereferenced = self['Signature'].d
        return dereferenced.Data()
    def summary(self):
        dereferenced = self['Signature'].d
        return "Signature={:#0{:d}x}".format(dereferenced.int(), 2 + 2 * dereferenced.Length())

@Table.define
class TEventMap(PreCalculatableTable, pstruct.type):
    type = 18
    _fields_ = [
        (TableIndex.Of('TypeDef'), 'Parent'),
        (TableIndex.Of('Event'), 'EventList'),
    ]

@Table.define
class TEvent(PreCalculatableTable, pstruct.type):
    type = 20
    _fields_ = [
        (EventAttributes, 'EventFlags'),
        (NameIndex, 'Name'),
        (TypeDefOrRef, 'EventType'),
    ]

@Table.define
class TPropertyMap(PreCalculatableTable, pstruct.type):
    type = 21
    _fields_ = [
        (TableIndex.Of('TypeDef'), 'Parent'),
        (TableIndex.Of('Property'), 'PropertyList'),
    ]

@Table.define
class TProperty(PreCalculatableTable, pstruct.type):
    type = 23
    _fields_ = [
        (PropertyAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Type'),
    ]

@Table.define
class TMethodSemantics(PreCalculatableTable, pstruct.type):
    type = 24
    _fields_ = [
        (MethodSemanticsAttributes, 'Flags'),
        (TableIndex.Of('MethodDef'), 'Method'),
        (HasSemantics, 'Association'),
    ]

@Table.define
class TMethodImpl(PreCalculatableTable, pstruct.type):
    type = 25
    _fields_ = [
        (TableIndex.Of('TypeDef'), 'Class'),
        (MethodDefOrRef, 'MethodBody'),
        (MethodDefOrRef, 'MethodDeclaration'),
    ]

@Table.define
class TModuleRef(PreCalculatableTable, pstruct.type):
    type = 26
    _fields_ = [
        (NameIndex, 'Name'),
    ]
    def Name(self):
        return self['Name'].str()
    def summary(self):
        return "Name={!r}".format(self['Name'].str())

@Table.define
class TTypeSpec(PreCalculatableTable, pstruct.type):
    type = 27
    _fields_ = [
        (BlobIndex, 'Signature'),
    ]
    def Signature(self):
        dereferenced = self['Signature'].d
        return dereferenced.Data()
    def summary(self):
        dereferenced = self['Signature'].d
        return "Signature={:#0{:d}x}".format(dereferenced.int(), 2 + 2 * dereferenced.Length())

@Table.define
class TImplMap(PreCalculatableTable, pstruct.type):
    type = 28
    _fields_ = [
        (PInvokeAttributes, 'MappingFlags'),
        (MemberForwarded, 'MemberForwarded'),
        (NameIndex, 'ImportName'),
        (TableIndex.Of('ModuleRef'), 'ImportScope'),
    ]
    def summary(self):
        scope = self['ImportScope'].d.d
        if self['MappingFlags'].int():
            return "ImportScope={!r} ImportName={!r} : MappingFlags={:s} : MemberForwarded={:s}".format(scope.Name(), self['ImportName'].str(), self['MappingFlags'].summary(), self['MemberForwarded'].summary())
        return "ImportScope={!r} ImportName={!r} : MemberForwarded={:s}".format(scope.Name(), self['ImportName'].str(), self['MemberForwarded'].summary())

@Table.define
class TFieldRVA(PreCalculatableTable, pstruct.type):
    type = 29
    _fields_ = [
        (pint.uint32_t, 'RVA'),
        (TableIndex.Of('Field'), 'Field'),
    ]

@Table.define
class TAssembly(PreCalculatableTable, pstruct.type):
    type = 32
    _fields_ = [
        (AssemblyHashAlgorithm, 'HashAlgId'),
        (pint.uint16_t, 'MajorVersion'),
        (pint.uint16_t, 'MinorVersion'),
        (pint.uint16_t, 'BuildNumber'),
        (pint.uint16_t, 'RevisionNumber'),
        (AssemblyFlags, 'Flags'),
        (BlobIndex, 'PublicKey'),
        (NameIndex, 'Name'),
        (NameIndex, 'Culture'),
    ]

@Table.define
class TAssemblyProcessor(PreCalculatableTable, pstruct.type):
    type = 33
    _fields_ = [
        (pint.uint32_t, 'Processor'),
    ]

@Table.define
class TAssemblyOS(PreCalculatableTable, pstruct.type):
    type = 34
    _fields_ = [
        (pint.uint32_t, 'OSPlatformID'),
        (pint.uint32_t, 'OSMajorVersion'),
        (pint.uint32_t, 'OSMinorVersion'),
    ]

@Table.define
class TAssemblyRef(PreCalculatableTable, pstruct.type):
    type = 35
    _fields_ = [
        (pint.uint16_t, 'MajorVersion'),
        (pint.uint16_t, 'MinorVersion'),
        (pint.uint16_t, 'BuildNumber'),
        (pint.uint16_t, 'RevisionNumber'),
        (AssemblyFlags, 'Flags'),
        (BlobIndex, 'PublicKeyOrToken'),
        (NameIndex, 'Name'),
        (NameIndex, 'Culture'),
        (BlobIndex, 'HashValue'),
    ]
    def summary(self):
        version = (self[fld].int() for fld in ['MajorVersion', 'MinorVersion', 'BuildNumber', 'RevisionNumber'])
        name, culture, pk, hash = (self[fld].d for fld in ['Name', 'Culture', 'PublicKeyOrToken', 'HashValue'])
        items = []
        items.append(name.str())
        items.append("Version={:s}".format('.'.join(map("{:d}".format, version))))
        items.append("Culture={:s}".format(culture.str() or 'neutral'))
        items.append("PublicKeyToken={:s}".format(''.join(map("{:02x}".format, bytearray(pk.serialize())))))
        items.append("HashValue={:s}".format(''.join(map("{:02x}".format, bytearray(hash.serialize())))))
        return ', '.join(items)

@Table.define
class TAssemblyRefProcessor(PreCalculatableTable, pstruct.type):
    type = 36
    _fields_ = [
        (pint.uint32_t, 'Processor'),
        (TableIndex.Of('AssemblyRef'), 'AssemblyRef'),
    ]

@Table.define
class TAssemblyRefOS(PreCalculatableTable, pstruct.type):
    type = 37
    _fields_ = [
        (pint.uint32_t, 'OSPlatformID'),
        (pint.uint32_t, 'OSMajorVersion'),
        (pint.uint32_t, 'OSMinorVersion'),
        (TableIndex.Of('AssemblyRef'), 'AssemblyRef'),
    ]

@Table.define
class TFile(PreCalculatableTable, pstruct.type):
    type = 38
    _fields_ = [
        (FileAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'HashValue'),
    ]

@Table.define
class TExportedType(PreCalculatableTable, pstruct.type):
    type = 39
    _fields_ = [
        (TypeAttributes, 'Flags'),
        (pint.uint32_t, 'TypeDefId'),   # XXX: not-quite a Index into a table
        (NameIndex, 'TypeName'),
        (NameIndex, 'TypeNamespace'),
        (Implementation_ExportedType, 'Implementation'),
    ]

@Table.define
class TManifestResource(PreCalculatableTable, pstruct.type):
    type = 40
    _fields_ = [
        (pint.uint32_t, 'Offset'),
        (ManifestResourceAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (Implementation_AssemblyRef, 'Implementation'),
    ]

@Table.define
class TNestedClass(PreCalculatableTable, pstruct.type):
    type = 41
    _fields_ = [
        (TableIndex.Of('TypeDef'), 'NestedClass'),
        (TableIndex.Of('TypeDef'), 'EnclosingClass'),
    ]

@Table.define
class TGenericParam(PreCalculatableTable, pstruct.type):
    type = 42
    _fields_ = [
        (pint.uint16_t, 'Number'),
        (GenericParamAttributes, 'Flags'),
        (TypeOrMethodDef, 'Owner'),
        (NameIndex, 'Name'),
    ]

@Table.define
class TMethodSpec(PreCalculatableTable, pstruct.type):
    type = 43
    _fields_ = [
        (MethodDefOrRef, 'Method'),
        (BlobIndex, 'Instantiation'),
    ]

@Table.define
class TGenericParamConstraint(PreCalculatableTable, pstruct.type):
    type = 44
    _fields_ = [
        (TableIndex.Of('GenericParam'), 'Owner'),
        (TypeDefOrRef, 'Constraint'),
    ]

class ENCLog(PreCalculatableTable, pstruct.type):
    # FIXME: Edit and continue
    _fields_ = []

class ENCMap(PreCalculatableTable, pstruct.type):
    # FIXME: Edit and continue
    _fields_ = []
