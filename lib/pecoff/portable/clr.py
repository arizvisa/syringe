import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,pbinary,utils
from ..__base__ import *

from .headers import virtualaddress
from . import headers

import logging

pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

### DataDirectory entry
class IMAGE_DATA_DIRECTORY(headers.IMAGE_DATA_DIRECTORY):
    addressing = staticmethod(virtualaddress)

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
            t = Stream.get(res['Name'].str(), blocksize=lambda s, cb=cb: cb)
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
            res['valid'] = self.valid()
            return res

        def valid(self):
            return self.int() == 0x424a5342

    class _StreamHeaders(parray.type):
        _object_ = StreamHdr
        def Get(self, name):
            res = next((stream for stream in self if stream.Name() == name), None)
            if res is None:
                raise NameError(name)
            return res
    def __StreamHeaders(self):
        res = self['Streams'].li.int()
        return dyn.clone(self._StreamHeaders, length=res)

    def __StreamData(self):
        cb = self.getparent(IMAGE_DATA_DIRECTORY)['Size'].int()
        total = sum(self[n].li.size() for _, n in self._fields_[:-1])
        res = max((0, cb-total))
        return dyn.block(res)

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
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.int()), 'Version'),
        (dyn.align(4), 'aligned(Version)'),
        (pbinary.littleendian(StorageFlags), 'Flags'),
        (pint.uint16_t, 'Streams'),
        (__StreamHeaders, 'StreamHeaders'),
        (__StreamData, 'StreamData'),
    ]

class VtableFixup(pstruct.type):
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
        res = self['Type'].li
        if res['32BIT'] and res['64BIT']:
            logging.warn("{:s} : {:s} : Both 32-bit and 64-bit flag is set. Assuming 0-bit. : {!r}".format('.'.join((__name__,self.__class__.__name__)), self.instance(), res.summary()))
            t = pint.uint_t
        elif not res['32BIT'] and not res['64BIT']:
            logging.warn("{:s} : {:s} : Neither 32-bit and 64-bit flag is set. Assuming 0-bit. : {!r}".format('.'.join((__name__,self.__class__.__name__)), self.instance(), res.summary()))
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

        (IMAGE_DATA_DIRECTORY, 'Resources'),
        (IMAGE_DATA_DIRECTORY, 'StrongNameSignature'),

        (IMAGE_DATA_DIRECTORY, 'CodeManagerTable'),
        (dyn.clone(IMAGE_DATA_DIRECTORY, _object_=lambda s:dyn.blockarray(VtableFixup, s.getparent(IMAGE_DATA_DIRECTORY)['Size'].li.int())), 'VTableFixups'),
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

    def summary(self):
        res = self.Get()
        return "{:s} -> {:d} ({:#x})".format(ptypes.bitmap.repr(self.bitmap()), res, res)
CInt = pbinary.bigendian(CInt)

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

    def repr(self):
        return self.summary()

### Blob types
class SerString(pstruct.type):
    _fields_ = [
        (CInt, 'length'),
        (lambda s: dyn.clone(pstr.string, length=s['length'].li.Get()), 'string'),
    ]
    def str(self):
        return self['string'].str()

    def summary(self):
        return '{:d} : {!r}'.format(self['length'].Get(), self['string'].str())

class SerBlock(pstruct.type):
    _fields_ = [
        (CInt, 'length'),
        (lambda s: dyn.block(s['length'].li.Get()), 'data'),
    ]

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
        (lambda s: dyn.array(s.Attribute, s['count'].li.Get()), 'attributes'),
    ]

### Stream types
class Stream(ptype.definition): cache = {}

@Stream.define
class HStrings(parray.block):
    type = '#Strings'
    _object_ = pstr.szstring

    def Get(self, offset):
        return self.field(offset)

@Stream.define
class HUserStrings(parray.block):
    type = '#US'
    class _object_(pstruct.type):
        def __data(self):
            cb = self['length'].li.Get()
            return dyn.clone(pstr.wstring, length= cb / 2)

        _fields_ = [
            (CInt, 'length'),
            (__data, 'data'),
            (lambda self: dyn.block(self['length'].li.Get() & 1), r'\0'),
        ]

    def Get(self, offset):
        return self.field(offset)

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

    def Get(self, offset):
        return self.field(offset)

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
# FIXME: Implement some more ElementType definitions

class TableRow(ptype.encoded_t):
    def __getitem__(self, name):
        return self.d.li.__getitem__(name)
    def repr(self):
        return self.d.li.repr()

class Tables(parray.type):
    length = 64
    def _object_(self):
        res = self.getparent(HTables)
        index, lengths = len(self.value), res['Rows'].li
        count = lengths[index].int()

        if count:
            logging.debug("{:s} : {:s} : Loading {:s}({:d}) table with {:d} rows. : {:d} of {:d}".format('.'.join((res.typename(),self.__class__.__name__)), self.instance(), TableType.byvalue(index, 'undefined'), index, count, 1+len(self.value), self.length))

        rowtype = Table.get(index)
        rowsize = rowtype.PreCalculateSize(res) if Table.has(index) else 0
        t = dyn.clone(TableRow, _object_=rowtype, _value_=dyn.block(rowsize))

        def Get(self, index):
            if index > 0:
                return self[index - 1]
            raise IndexError(index)
        return dyn.array(t, count, Get=Get, blocksize=lambda s,cb=rowsize*count:cb)

    def __getindex__(self, index):
        return TableType.byname(index) if isinstance(index, basestring) else index

@Stream.define
class HTables(pstruct.type):
    type = "#~"

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
        def indices(self, crit):
            return [index for index, value in enumerate(reversed(self)) if crit(value)]

    class _Valid(BitVector):
        length = 64
        def indices(self):
            return super(HTables._Valid, self).indices(bool)
        def summary(self):
            return ', '.join(map('{:d}'.format, self.indices()))

    class _Sorted(BitVector):
        length = 64
        def indices(self):
            return super(HTables._Sorted, self).indices(bool)

    class _RowLengths(parray.type):
        length = 64
        def _object_(self):
            res, index = self.getparent(HTables), len(self.value)
            present = res['Valid'].li.index
            return pint.uint32_t if present(index) else pint.uint_t

    def __padding_Tables(self):
        hdr = self.getparent(StreamHdr)
        cb = hdr['Size'].li.int()
        total = sum(self[n].blocksize() for _, n in self._fields_[:-1])
        return dyn.block(max((0, cb-total)))

    _fields_ = [
        (pint.uint32_t, 'Reserved'),
        (pint.uint8_t, 'MajorVersion'),
        (pint.uint8_t, 'MinorVersion'),
        (HeapSizes, 'HeapSizes'),
        (pint.uint8_t, 'Reserved'),
        (pbinary.littleendian(_Valid), 'Valid'),
        (pbinary.littleendian(_Sorted), 'Sorted'),
        (_RowLengths, 'Rows'),
        (Tables, 'Tables'),
        (__padding_Tables, 'padding(Tables)'),
    ]

### #~ tables
class Table(ptype.definition): cache = {}

## index types
class Index(ptype.generic): pass
class StreamIndex(Index, pint.uint_t): pass
class TableIndex(Index): pass
class CodedIndex(Index): pass

class NameIndex(StreamIndex):
    type = 'HStrings'

    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HStrings'] else 2

class GuidIndex(StreamIndex):
    type = 'HGUID'

    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HGUID'] else 2

class BlobIndex(StreamIndex):
    type = 'HBlob'
    def blocksize(self):
        res = self.getparent(HTables)
        heapsizes = res['HeapSizes'].li
        return 4 if heapsizes['HBlob'] else 2

def IndexOf(table):
    index = TableType.byname(table)

    class IndexOf(TableIndex, pint.uint_t): pass

    def blocksize(self, table=table, index=index):
        res = self.getparent(HTables)
        count = res['Rows'].li[index].int()
        return 2 if count < 0x10000 else 4
    IndexOf.blocksize = blocksize

    def Tables(cls, index=index):
        return {index}
    IndexOf.Tables = classmethod(Tables)

    IndexOf.type = index

    return IndexOf

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
        return dyn.clone(pint.uint_t, length=1) if count < 2**(16 - self.Tag.width) else dyn.clone(pint.uint_t, length=3)

    @classmethod
    def Tables(cls):
        '''Returns the indices of every table that can be represent by this TaggedInex'''

        # grab all possible table names and table names specified by self.Tag
        all_Tables, tag_Tables = TableType.mapping(), cls.Tag.mapping()

        # grab the intersection of them as some table names specified by self.Tag might not exist or be defined
        res = tag_Tables.viewkeys() & all_Tables.viewkeys()

        # convert each table name specified by self.Tag into it's correct index.
        return {all_Tables[name] for name in res}

    class TagByte(pbinary.struct):
        _fields_ = [
            (lambda s: 8 - s.getparent(TaggedIndex).Tag.width, 'Index'),
            (lambda s: s.getparent(TaggedIndex).Tag, 'Tag'),
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

    def summary(self):
        res = self.Index()
        return "Tag({:s}) : Index={:#x} ({:d})".format(self['Tag'].Get(), res, res)

    def Index(self):
        res = self['Index'].int()
        res <<= 8 - self.Tag.width
        res |= self['Tag'].Index()
        return res

class TypeDefOrRef(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('TypeDef', 0),
            ('TypeRef', 1),
            ('TypeSpec', 2),
        ]

class HasConstant(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('Field', 0),
            ('Param', 1),
            ('Property', 2),
        ]

class HasCustomAttribute(TaggedIndex):
    class Tag(pbinary.enum):
        width = 5
        _values_ = [
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
        width = 1
        _values_ = [
            ('Field', 0),
            ('Param', 1),
        ]

class HasDeclSecurity(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('TypeDef', 0),
            ('MethodDef', 1),
            ('Assembly', 2),
        ]

class MemberRefParent(TaggedIndex):
    class Tag(pbinary.enum):
        width = 3
        _values_ = [
            ('TypeDef', 0),
            ('TypeRef', 1),
            ('ModuleRef', 2),
            ('MethodDef', 3),
            ('TypeSpec', 4),
        ]

class HasSemantics(TaggedIndex):
    class Tag(pbinary.enum):
        width = 1
        _values_ = [
            ('Event', 0),
            ('Property', 1),
        ]

class MethodDefOrRef(TaggedIndex):
    class Tag(pbinary.enum):
        width = 1
        _values_ = [
            ('MethodDef', 0),
            ('MemberRef', 1),
        ]

class MemberForwarded(TaggedIndex):
    class Tag(pbinary.enum):
        width = 1
        _values_ = [
            ('Field', 0),
            ('MethodDef', 1),
        ]

class Implementation_ExportedType(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('File', 0),
            ('ExportedType', 1),
        ]

class Implementation_AssemblyRef(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('File', 0),
            ('AssemblyRef', 1),
        ]

class CustomAttributeType(TaggedIndex):
    class Tag(pbinary.enum):
        width = 3
        _values_ = [
            ('Not used', 0),
            ('Not used', 1),
            ('MethodDef', 2),
            ('MemberRef', 3),
            ('Not used', 4),
        ]

class ResolutionScope(TaggedIndex):
    class Tag(pbinary.enum):
        width = 2
        _values_ = [
            ('Module', 0),
            ('ModuleRef', 1),
            ('AssemblyRef', 2),
            ('TypeRef', 3),
        ]

class TypeOrMethodDef(TaggedIndex):
    class Tag(pbinary.enum):
        width = 1
        _values_ = [
            ('TypeDef', 0),
            ('MethodDef', 1),
        ]

## Attributes and Flags
class TypeAttributes(pbinary.flags):
    class VisibilityMask(pbinary.enum):
        width = 3
        _values_ = [
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
        width = 2
        _values_ = [
            ('AutoLayout', 0),
            ('SequentialLayout', 1),
            ('ExplicitLayout', 2),
        ]
    class ClassSemanticsMask(pbinary.enum):
        width = 1
        _values_ = [
            ('Class', 0),
            ('Interface', 1),
        ]
    class StringFormatMask(pbinary.enum):
        width = 2
        _values_ = [
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
        width = 3
        _values_ = [
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

class MethodImplAttributes(pbinary.flags):
    class CodeTypeMask(pbinary.enum):
        width = 2
        _values_ = [
            ('IL', 0),
            ('Native', 1),
            ('OPTIL', 2),
            ('Runtime', 3),
        ]
    class ManagedMask(pbinary.enum):
        width = 1
        _values_ = [
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

class MethodAttributes(pbinary.flags):
    class MemberAccessMask(pbinary.enum):
        width = 3
        _values_ = [
            ('CompilerControlled', 0),
            ('Private', 1),
            ('FamANDAssem', 2),
            ('Assem', 3),
            ('Family', 4),
            ('FamORAssem', 5),
            ('Public', 6),
        ]
    class VtableLayoutMask(pbinary.enum):
        width = 1
        _values_ = [
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

class EventAttributes(pbinary.flags):
    _fields_ = [
        (5, 'Unused'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (9, 'Unused'),
    ]

class PropertyAttributes(pbinary.flags):
    _fields_ = [
        (3, 'Unused'),
        (1, 'Default'),
        (1, 'Unused'),
        (1, 'RTSpecialName'),
        (1, 'SpecialName'),
        (9, 'Unused'),
    ]

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

class PInvokeAttributes(pbinary.flags):
    class CharSetMask(pbinary.enum):
        width = 2
        _values_ = [
            ('CharSetNotSpec', 0),
            ('CharSetAnsi', 1),
            ('CharSetUnicode', 2),
            ('CharSetAuto', 3),
        ]
    class CallConvMask(pbinary.enum):
        width = 3
        _values_ = [
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

class AssemblyFlags(pbinary.flags):
    class Reserved(pbinary.enum):
        width = 2
        _values_ = []

    class HasPublicKey(pbinary.enum):
        width = 1
        _values_ = [
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

class FileAttributes(pbinary.flags):
    class ContainsNoMetaData(pbinary.enum):
        width = 1
        _values_ = [
            ('ContainsMetaData', 0),
            ('ContainsNoMetaData', 1),
        ]
    _fields_ = [
        (31, 'Unused'),
        (ContainsNoMetaData, 'ContainsNoMetaData'),
    ]

class ManifestResourceAttributes(pbinary.flags):
    class VisibilityMask(pbinary.enum):
        width = 3
        _values_ = [
            ('Public', 1),
            ('Private', 2),
        ]
    _fields_ = [
        (29, 'Unused'),
        (VisibilityMask, 'Visibility'),
    ]

class GenericParamAttributes(pbinary.flags):
    class VarianceMask(pbinary.enum):
        width = 2
        _values_ = [
            ('None', 0),
            ('Covariant', 1),
            ('Contravariant', 2),
        ]

    class SpecialConstraintMask(pbinary.enum):
        width = 3
        _values_ = [
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
            if issubclass(t, Index):
                if issubclass(t, StreamIndex):
                    res.append(4 if heapsizes[t.type] else 2)
                elif issubclass(t, TableIndex):
                    res.append(2 if rows[t.type].int() < 0x10000 else 4)
                elif issubclass(t, CodedIndex):
                    count = max(rows[index].int() for index in t.Tables())
                    res.append(2 if count < 2**(16 - t.Tag.width) else 4)
                else:
                    raise TypeError((cls, t, name))
                continue
            res.append(t().a.blocksize())
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

@Table.define
class TTypeDef(PreCalculatableTable, pstruct.type):
    type = 2
    _fields_ = [
        (TypeAttributes, 'Flags'),
        (NameIndex, 'TypeName'),
        (NameIndex, 'TypeNamespace'),
        (TypeDefOrRef, 'Extends'),
        (IndexOf('Field'), 'FieldList'),
        (IndexOf('MethodDef'), 'MethodList'),
    ]

@Table.define
class TField(PreCalculatableTable, pstruct.type):
    type = 4
    _fields_ = [
        (FieldAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Signature'),
    ]

@Table.define
class TMethodDef(PreCalculatableTable, pstruct.type):
    type = 6
    _fields_ = [
        (pint.uint32_t, 'RVA'),
        (MethodImplAttributes, 'ImplFlags'),
        (MethodAttributes, 'Flags'),
        (NameIndex, 'Name'),
        (BlobIndex, 'Signature'),
        (IndexOf('Param'), 'ParamList'),
    ]

@Table.define
class TParam(PreCalculatableTable, pstruct.type):
    type = 8
    _fields_ = [
        (ParamAttributes, 'Flags'),
        (pint.uint16_t, 'Sequence'),
        (NameIndex, 'Name'),
    ]

@Table.define
class TInterfaceImpl(PreCalculatableTable, pstruct.type):
    type = 9
    _fields_ = [
        (IndexOf('TypeDef'), 'Class'),
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
    _fields_ = [
        (ELEMENT_TYPE, 'Type'),
        (pint.uint8_t, 'PaddingZero'),
        (HasConstant, 'Parent'),
        (BlobIndex, 'Value'),
    ]

@Table.define
class TCustomAttribute(PreCalculatableTable, pstruct.type):
    type = 12
    _fields_ = [
        (HasCustomAttribute, 'Parent'),
        (CustomAttributeType, 'Type'),
        (BlobIndex, 'Value'),
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
        (IndexOf('TypeDef'), 'Parent'),
    ]

@Table.define
class TFieldLayout(PreCalculatableTable, pstruct.type):
    type = 16
    _fields_ = [
        (pint.uint32_t, 'Offset'),
        (IndexOf('Field'), 'Field'),
    ]

@Table.define
class TStandAloneSig(PreCalculatableTable, pstruct.type):
    type = 17
    _fields_ = [
        (BlobIndex, 'Signature'),
    ]

@Table.define
class TEventMap(PreCalculatableTable, pstruct.type):
    type = 18
    _fields_ = [
        (IndexOf('TypeDef'), 'Parent'),
        (IndexOf('Event'), 'EventList'),
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
        (IndexOf('TypeDef'), 'Parent'),
        (IndexOf('Property'), 'PropertyList'),
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
        (IndexOf('MethodDef'), 'Method'),
        (HasSemantics, 'Association'),
    ]

@Table.define
class TMethodImpl(PreCalculatableTable, pstruct.type):
    type = 25
    _fields_ = [
        (IndexOf('TypeDef'), 'Class'),
        (MethodDefOrRef, 'MethodBody'),
        (MethodDefOrRef, 'MethodDeclaration'),
    ]

@Table.define
class TModuleRef(PreCalculatableTable, pstruct.type):
    type = 26
    _fields_ = [
        (NameIndex, 'Name'),
    ]

@Table.define
class TTypeSpec(PreCalculatableTable, pstruct.type):
    type = 27
    _fields_ = [
        (BlobIndex, 'Signature'),
    ]

@Table.define
class TImplMap(PreCalculatableTable, pstruct.type):
    type = 28
    _fields_ = [
        (PInvokeAttributes, 'MappingFlags'),
        (MemberForwarded, 'MemberForwarded'),
        (NameIndex, 'ImportName'),
        (IndexOf('ModuleRef'), 'ImportScope'),
    ]

@Table.define
class TFieldRVA(PreCalculatableTable, pstruct.type):
    type = 29
    _fields_ = [
        (pint.uint32_t, 'RVA'),
        (IndexOf('Field'), 'Field'),
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

@Table.define
class TAssemblyRefProcessor(PreCalculatableTable, pstruct.type):
    type = 36
    _fields_ = [
        (pint.uint32_t, 'Processor'),
        (IndexOf('AssemblyRef'), 'AssemblyRef'),
    ]

@Table.define
class TAssemblyRefOS(PreCalculatableTable, pstruct.type):
    type = 37
    _fields_ = [
        (pint.uint32_t, 'OSPlatformID'),
        (pint.uint32_t, 'OSMajorVersion'),
        (pint.uint32_t, 'OSMinorVersion'),
        (IndexOf('AssemblyRef'), 'AssemblyRef'),
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
        (IndexOf('TypeDef'), 'NestedClass'),
        (IndexOf('TypeDef'), 'EnclosingClass'),
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
        (IndexOf('GenericParam'), 'Owner'),
        (TypeDefOrRef, 'Constraint'),
    ]

class ENCLog(PreCalculatableTable, pstruct.type):
    # FIXME: Edit and continue
    _fields_ = []

class ENCMap(PreCalculatableTable, pstruct.type):
    # FIXME: Edit and continue
    _fields_ = []
