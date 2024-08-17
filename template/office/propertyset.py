# [MS-OLEPS].pdf
import sys, ptypes
from ptypes import *
from . import intsafe, storage
from .intsafe import *

HRESULT = sys.modules['ndk.datatypes'].HRESULT if 'ndk.datatypes' in sys.modules else intsafe.LONG
class HRESULT(HRESULT):
    '''
    This type should come from ndk.datatypes so that we can easily decode the error code, but
    since this template might be distributed without it.. we autodetect the module instead.
    '''

# Variant types
class VT_(object):
    _values_ = [
        ('EMPTY', 0x0000),              # Type is undefined, and the minimum property set version is 0.
        ('NULL', 0x0001),               # Type is null, and the minimum property set version is 0.
        ('I2', 0x0002),                 # Type is 16-bit signed integer, and the minimum property set version is 0.
        ('I4', 0x0003),                 # Type is 32-bit signed integer, and the minimum property set version is 0.
        ('R4', 0x0004),                 # Type is 4-byte (single-precision) IEEE floating-point number, and the minimum property set version is 0.
        ('R8', 0x0005),                 # Type is 8-byte (double-precision) IEEE floating-point number, and the minimum property set version is 0.
        ('CY', 0x0006),                 # Type is CURRENCY, and the minimum property set version is 0.
        ('DATE', 0x0007),               # Type is DATE, and the minimum property set version is 0.
        ('BSTR', 0x0008),               # Type is CodePageString, and the minimum property set version is 0.
        ('ERROR', 0x000A),              # Type is HRESULT, and the minimum property set version is 0.
        ('BOOL', 0x000B),               # Type is VARIANT_BOOL, and the minimum property set version is 0.
        ('VARIANT', 0x000C),            # Type is a variant which depends on the header type.
        ('DECIMAL', 0x000E),            # Type is DECIMAL, and the minimum property set version is 0.
        ('I1', 0x0010),                 # Type is 1-byte signed integer, and the minimum property set version is 1.
        ('UI1', 0x0011),                # Type is 1-byte unsigned integer, and the minimum property set version is 0.
        ('UI2', 0x0012),                # Type is 2-byte unsigned integer, and the minimum property set version is 0.
        ('UI4', 0x0013),                # Type is 4-byte unsigned integer, and the minimum property set version is 0.
        ('I8', 0x0014),                 # Type is 8-byte signed integer, and the minimum property set version is 0.
        ('UI8', 0x0015),                # Type is 8-byte unsigned integer, and the minimum property set version is 0.
        ('INT', 0x0016),                # Type is 4-byte signed integer, and the minimum property set version is 1.
        ('UINT', 0x0017),               # Type is 4-byte unsigned integer, and the minimum property set version is 1.
        ('LPSTR', 0x001E),              # Type is CodePageString, and the minimum property set version is 0.
        ('LPWSTR', 0x001F),             # Type is UnicodeString, and the minimum property set version is 0.
        ('FILETIME', 0x0040),           # Type is FILETIME, and the minimum property set version is 0.
        ('BLOB', 0x0041),               # Type is binary large object (BLOB), and the minimum property set version is 0.
        ('STREAM', 0x0042),             # Type is Stream, and the minimum property set version is 0. VT_STREAM is not allowed in a simple property set.
        ('STORAGE', 0x0043),            # Type is Storage, and the minimum property set version is 0. VT_STORAGE is not allowed in a simple property set.
        ('STREAMED_Object', 0x0044),    # Type is Stream representing an Object in an application-specific manner, and the minimum property set version is 0. VT_STREAMED_Object is not allowed in a simple property set.
        ('STORED_Object', 0x0045),      # Type is Storage representing an Object in an application-specific manner, and the minimum property set version is 0. VT_STORED_Object is not allowed in a simple property set.
        ('BLOB_Object', 0x0046),        # Type is BLOB representing an object in an application-specific manner. The minimum property set version is 0.
        ('CF', 0x0047),                 # Type is PropertyIdentifier, and the minimum property set version is 0.
        ('CLSID', 0x0048),              # Type is CLSID, and the minimum property set version is 0.
        ('VERSIONED_STREAM', 0x0049),   # Type is Stream with application-specific version GUID (VersionedStream). The minimum property set version is 0. VT_VERSIONED_STREAM is not allowed in a simple property set.
    ]

class CURRENCY(INT64):
    ''' [MS-OAUT] '''
    def float(self):
        res = self.get()
        unsigned = pow(2, 8 * self.blocksize())
        signed = res if res < unsigned // 2 else res - unsigned
        return signed / pow(10, 4)

    def set(self, number):
        if not isinstance(number, float):
            return super(CURRENCY, self).set(number)

        unsigned = pow(2, 8 * self.blocksize())
        half = unsigned // 2

        res = math.trunc(number * pow(10, 4))
        signed = min(res + unsigned, unsigned - 1) if res < 0 else min(res, half - 1)
        return super(CURRENCY, self).set(signed)

    def summary(self):
        return "({:#x}) {:f}".format(self, self.float())

class CodePageString(pstruct.type):
    def __Characters(self):
        expected = self['Size'].li
        return dyn.clone(pstr.string, length=expected.int())
    _fields_ = [
        (DWORD, 'Size'),
        (__Characters, 'Characters'),
        (dyn.padding(4), 'padding(Characters)'),
    ]
    def alloc(self, **fields):
        fields.setdefault('Characters', pstr.szstring().set(fields.pop('Characters'))) if isinstance(fields.get('Characters'), (''.__class__, u''.__class__)) else fields.get('Characters')
        res = super(CodePageString, self).alloc(**fields)
        res['padding(Characters)'] if 'padding(Characters)' in fields else res['padding(Characters)'].a
        return res if 'Size' in fields else res.set(Size=res['Characters'].size())

class DATE(pfloat.double): pass
class VARIANT_BOOL(pint.enum, short):
    _values_ = [('VARIANT_TRUE', 0xffff), ('VARIANT_FALSE', 0x0000)]
class DECIMAL(pstruct.type):
    _fields_ = [
        (WORD, 'wReserved'),
        (BYTE, 'scale'),
        (BYTE, 'sign'),
        (ULONG, 'Hi32'),
        (ULONGLONG, 'Lo64'),
    ]
class UnicodeString(pstruct.type):
    def __Characters(self):
        expected = self['Length'].li
        return dyn.clone(pstr.wstring, length=expected.int())
    _fields_ = [
        (DWORD, 'Length'),
        (__Characters, 'Characters'),
        (dyn.padding(4), 'padding(Characters)'),
    ]
    def alloc(self, **fields):
        fields.setdefault('Characters', pstr.szwstring().set(fields.pop('Characters'))) if isinstance(fields.get('Characters'), (''.__class__, u''.__class__)) else fields.get('Characters')
        res = super(UnicodeString, self).alloc(**fields)
        res['padding(Characters)'] if 'padding(Characters)' in fields else res['padding(Characters)'].a
        return res if 'Length' in fields else res.set(Length=res['Characters'].size())

class FILETIME(intsafe.FILETIME): pass
class BLOB(pstruct.type):
    _fields_ = [
        (DWORD, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Bytes'),
        (dyn.padding(4), 'padding(Bytes)'),
    ]
    def alloc(self, **fields):
        res = super(BLOB, self).alloc(**fields)
        res['padding(Bytes)'] if 'padding(Bytes)' in fields else res['padding(Bytes)'].a
        return res if 'Size' in fields else res.set(Size=res['Bytes'].size())

class IndirectPropertyName(CodePageString): pass
class ClipboardData(pstruct.type):
    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'Format'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Data'),
        (dyn.padding(4), 'padding(Data)'),
    ]
    def alloc(self, **fields):
        res = super(ClipboardData, self).alloc(**fields)
        res['padding(Data)'] if 'padding(Data)' in fields else res['padding(Data)'].a
        return res if 'Size' in fields else res.set(Size=res['Data'].size())

class VersionedStream(pstruct.type):
    _fields_ = [
        (GUID, 'VersionGuid'),
        (CodePageString, 'StreamName'), # XXX: not sure whether this is right
    ]

################
class VectorHeader(pstruct.type):
    _fields_ = [
        (DWORD, 'Length'),
    ]
    def Count(self):
        length = self['Length']
        return length.int()

class ArrayDimension(pstruct.type):
    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'IndexOffset'),
    ]
    def Count(self):
        return self['Size'].int()

class ArrayHeader(pstruct.type):
    class _Type(pint.enum, VT_, DWORD):
        pass
    _fields_ = [
        (_Type, 'Type'),
        (DWORD, 'NumDimensions'),
        (lambda self: dyn.array(ArrayDimension, self['NumDimensions'].li.int()), 'Dimension'),
    ]
    def Count(self):
        items = (item.Count() for item in self['Dimension'])
        return functools.reduce(operator.mul, items)

class TypedPropertyVector(pstruct.type):
    def __Scalar(self):
        header = self['Header'].li
        return dyn.array(self._object_, header.Count())
    _fields_ = [
        (VectorHeader, 'Header'),
        (__Scalar, 'Scalar'),
    ]

class TypedPropertyArray(pstruct.type):
    def __Scalar(self):
        header = self['Header'].li
        if self._object_.type != header['Type'].int():
            # XXX: We don't really need to raise an exception here, but as
            #      I'm not sure which field should get priority. We can
            #      update this whenever we encounter this type.
            raise Exception("TypedPropertyArray type ({:#x}) conflicts with TypedPropertyValue type ({:#x})".format(header['Type'].int(), self._object_.type))

            t = TypedProperty.lookup(header['Type'].int())
            return dyn.array(t, header.Count())
        return dyn.array(self._object_, header.Count())
    _fields_ = [
        (ArrayHeader, 'Header'),
        (__Scalar, 'Scalar'),
    ]

@pbinary.littleendian
class PropertyType(pbinary.struct):
    class _HeaderType(pbinary.flags):
        _fields_ = [
            (2, 'Unused'),
            (1, 'VT_ARRAY'),
            (1, 'VT_VECTOR'),
        ]
    class _VariantType(pbinary.enum, VT_):
        length = 12
    _fields_ = [
        (_HeaderType, 'HeaderType'),
        (_VariantType, 'VariantType'),
    ]

class TypedPropertyValue(pstruct.type):
    def __Value(self):
        property = self['Type'].li
        type, variantType = TypedProperty.lookup(property['VariantType']), property.field('VariantType')
        header = property.field('HeaderType')
        if header['VT_ARRAY'] and not variantType['VARIANT']:
            return dyn.clone(TypedPropertyArray, _object_=type)

        elif header['VT_VECTOR'] and not variantType['VARIANT']:
            return dyn.clone(TypedPropertyVector, _object_=type)

        # Special handling for any of the nested variant types.
        elif header['VT_ARRAY'] and variantType['VARIANT']:
            object = dyn.clone(TypedPropertyArray, _object_=TypedPropertyValue)
            return dyn.clone(TypedPropertyArray, _object_=object)

        elif header['VT_VECTOR'] and variantType['VARIANT']:
            object = dyn.clone(TypedPropertyVector, _object_=TypedPropertyValue)
            return dyn.clone(TypedPropertyVector, _object_=object)
        return type

    _fields_ = [
        (PropertyType, 'Type'),
        (WORD, 'Padding'),
        (__Value, 'Value'),
    ]

class TypedProperty(ptype.definition):
    cache = {}
@TypedProperty.define
class VT_EMPTY(ptype.undefined):
    type = 0x0000
@TypedProperty.define
class VT_NULL(ptype.undefined):
    type = 0x0001
@TypedProperty.define
class VT_I2(pstruct.type):
    type, _fields_ = 0x0002, [(INT16, 'I'), (dyn.block(2), 'padding(I)')]
    int = lambda self: self['I'].int()
@TypedProperty.define
class VT_I4(INT32):
    type = 0x0003
@TypedProperty.define
class VT_R4(pfloat.single):
    type = 0x0004
@TypedProperty.define
class VT_R8(pfloat.double):
    type = 0x0005
@TypedProperty.define
class VT_CY(CURRENCY):
    type = 0x0006
@TypedProperty.define
class VT_DATE(DATE):
    type = 0x0007
@TypedProperty.define
class VT_BSTR(CodePageString):
    type = 0x0008
@TypedProperty.define
class VT_ERROR(HRESULT):
    type = 0x000a
@TypedProperty.define
class VT_BOOL(VARIANT_BOOL):
    type = 0x000b
@TypedProperty.define
class VT_VARIANT(ptype.undefined):
    type = 0x000c
@TypedProperty.define
class VT_DECIMAL(DECIMAL):
    type = 0x000e
@TypedProperty.define
class VT_I1(pstruct.type):
    type, _fields_ = 0x0010, [(INT8, 'I'), (dyn.block(3), 'padding(I)')]
    int = lambda self: self['I'].int()
@TypedProperty.define
class VT_UI1(pstruct.type):
    type, _fields_ = 0x0011, [(UINT8, 'UI'), (dyn.block(3), 'padding(UI)')]
    int = lambda self: self['UI'].int()
@TypedProperty.define
class VT_UI2(pstruct.type):
    type, _fields_ = 0x0012, [(UINT16, 'UI'), (dyn.block(2), 'padding(UI)')]
    int = lambda self: self['UI'].int()
@TypedProperty.define
class VT_UI4(UINT32):
    type = 0x0013
@TypedProperty.define
class VT_UI8(UINT64):
    type = 0x0014
@TypedProperty.define
class VT_I8(INT64):
    type = 0x0015
@TypedProperty.define
class VT_INT(INT):
    type = 0x0016
@TypedProperty.define
class VT_UINT(UINT):
    type = 0x0017
@TypedProperty.define
class VT_LPSTR(CodePageString):
    type = 0x001e
@TypedProperty.define
class VT_LPWSTR(UnicodeString):
    type = 0x001f
@TypedProperty.define
class VT_FILETIME(FILETIME):
    type = 0x0040
@TypedProperty.define
class VT_BLOB(BLOB):
    type = 0x0041
@TypedProperty.define
class VT_STREAM(IndirectPropertyName):
    type = 0x0042
@TypedProperty.define
class VT_STORAGE(IndirectPropertyName):
    type = 0x0043
@TypedProperty.define
class VT_STREAMED_OBJECT(IndirectPropertyName):
    type = 0x0044
@TypedProperty.define
class VT_STORED_OBJECT(IndirectPropertyName):
    type = 0x0045
@TypedProperty.define
class VT_BLOB_OBJECT(BLOB):
    type = 0x0046
@TypedProperty.define
class VT_CF(ClipboardData):
    type = 0x0047
@TypedProperty.define
class VT_VERSIONED_STREAM(VersionedStream):
    type = 0x0048

############
class _PROPERTY_IDENTIFIER_RESERVED(pint.enum):
    _values_ = [
        ('DICTIONARY', 0x00000000),     # Dictionary
        ('CODEPAGE', 0x00000001),       # VT_I2
        ('LOCALE', 0x80000000),         # VT_UI4
        ('BEHAVIOR', 0x80000003),       # VT_UI4
    ]

class PIDSI_(pint.enum):
    _values_ = [
        ('TITLE', 0x00000002),          # VT_LPSTR
        ('SUBJECT', 0x00000003),        # VT_LPSTR
        ('AUTHOR', 0x00000004),         # VT_LPSTR
        ('KEYWORDS', 0x00000005),       # VT_LPSTR
        ('COMMENTS', 0x00000006),       # VT_LPSTR
        ('TEMPLATE', 0x00000007),       # VT_LPSTR
        ('LASTAUTHOR', 0x00000008),     # VT_LPSTR
        ('REVNUMBER', 0x00000009),      # VT_LPSTR
        ('EDITTIME', 0x0000000A),       # VT_FILETIME (UTC)
        ('LASTPRINTED', 0x0000000B),    # VT_FILETIME (UTC)
        ('CREATE_DTM', 0x0000000C),     # VT_FILETIME (UTC)
        ('LASTSAVE_DTM', 0x0000000D),   # VT_FILETIME (UTC)
        ('PAGECOUNT', 0x0000000E),      # VT_I4
        ('WORDCOUNT', 0x0000000F),      # VT_I4
        ('CHARCOUNT', 0x00000010),      # VT_I4
        ('THUMBNAIL', 0x00000011),      # VT_CF
        ('APPNAME', 0x00000012),        # VT_LPSTR
        ('DOC_SECURITY', 0x00000013),   # VT_I4
    ] + _PROPERTY_IDENTIFIER_RESERVED._values_

class PIDDSI_(pint.enum):
    _values_ = [
        ('CATEGORY', 0x00000002),       # VT_LPSTR
        ('PRESFORMAT', 0x00000003),     # VT_LPSTR
        ('BYTECOUNT', 0x00000004),      # VT_I4
        ('LINECOUNT', 0x00000005),      # VT_I4
        ('PARCOUNT', 0x00000006),       # VT_I4
        ('SLIDECOUNT', 0x00000007),     # VT_I4
        ('NOTECOUNT', 0x00000008),      # VT_I4
        ('HIDDENCOUNT', 0x00000009),    # VT_I4
        ('MMCLIPCOUNT', 0x0000000A),    # VT_I4
        ('SCALE', 0x0000000B),          # VT_BOOL
        ('HEADINGPAIR', 0x0000000C),    # VT_VARIANT | VT_VECTOR
        ('DOCPARTS', 0x0000000D),       # VT_VECTOR | VT_LPSTR
        ('MANAGER', 0x0000000E),        # VT_LPSTR
        ('COMPANY', 0x0000000F),        # VT_LPSTR
        ('LINKSDIRTY', 0x00000010),     # VT_BOOL
    ] + _PROPERTY_IDENTIFIER_RESERVED._values_

class ReservedProperty(_PROPERTY_IDENTIFIER_RESERVED, DWORD):
    pass

class PropertyIdentifier(ptype.definition):
    cache, default = {}, ReservedProperty

    # FIXME: the correct property identifier should be determined by the
    #        FMTID that is referenced by the FMTOFFSET for an entry.

@PropertyIdentifier.define
class SummaryInformationProperty(PIDSI_, DWORD):
    type = (0xF29F85E0, 0x4FF9, 0x1068, 0xAB9108002B27B3D9)

@PropertyIdentifier.define
class DocumentSummaryInformationProperty(PIDDSI_, DWORD):
    type = (0xD5CDD505, 0x2E9C, 0x101B, 0x939708002B2CF9AE)

@PropertyIdentifier.define
class PropertyBagProperty(_PROPERTY_IDENTIFIER_RESERVED, DWORD):
    type = (0x20001801, 0x5DE6, 0x11D1, 0x8E3800C04FB9386D)

class DictionaryEntry(pstruct.type):
    def __PropertyIdentifier(self):
        if hasattr(self, '__format_identifier__'):
            return PropertyIdentifier.get(self.__format_identifier__)

        try:
            p = self.getparent(FMTOFFSET)

        except ptypes.error.ItemNotFoundError:
            return PropertyIdentifier.default

        fmtid = p['FMTID']
        return PropertyIdentifier.get(fmtid.identifier())

    def __Name(self):
        length = self['Length'].li
        raise NotImplementedError

        # FIXME: we need to check the propertyset for the codepage in
        #        order to distinguish whether this is unicode or not.
        return dyn.clone(pstr.string, length=length.int())
        return dyn.clone(pstr.wstring, length=length.int())

    _fields_ = [
        (__PropertyIdentifier, 'PropertyIdentifier'),
        (DWORD, 'Length'),
        (lambda self: dyn.block(self['Length'].li.int()), 'Name'),
    ]

    def alloc(self, **fields):
        res = super(DictionaryEntry, self).alloc(**fields)
        return res if 'Length' in fields else res.set(Length=res['Name'].size())

class Dictionary(pstruct.type):
    _fields_ = [
        (DWORD, 'NumEntries'),
        (lambda self: dyn.array(DictionaryEntry, self['NumEntries'].li.int()), 'Entry'),
        (dyn.padding(4), 'Padding'),
    ]

    def alloc(self, **fields):
        res = super(Dictionary, self).alloc(**fields)
        return res if 'NumEntries' in fields else res.set(NumEntries=len(res['Entry']))

    def enumerate(self):
        for index, item in enumerate(self['Entry']):
            yield index, item['PropertyIdentifier'], item['Name']
        return

class PropertyIdentifierAndOffset(pstruct.type):
    def __PropertyIdentifier(self):
        if hasattr(self, '__format_identifier__'):
            return PropertyIdentifier.get(self.__format_identifier__)

        try:
            fmtoffset = self.getparent(FMTOFFSET)
        except ptypes.error.ItemNotFoundError:
            return PropertyIdentifier.default

        fmtid = fmtoffset['FMTID']
        return PropertyIdentifier.lookup(fmtid.identifier(), default)

    def __Offset(self):
        try:
            p = self.getparent(PropertySet)
        except ptypes.error.ItemNotFoundError:
            return DWORD

        identifier = self['PropertyIdentifier'].li
        if identifier['DICTIONARY']:
            return dyn.rpointer(Dictionary, p, DWORD)
        return dyn.rpointer(TypedPropertyValue, p, DWORD)

    _fields_ = [
        (__PropertyIdentifier, 'PropertyIdentifier'),
        (__Offset, 'Offset'),
    ]

class PropertySet(pstruct.type):
    def __PropertyIdentifierAndOffset(self):
        offset, count = self.getoffset(), self['NumProperties'].li

        try:
            p = self.getparent(PropertySetStream)
            fmtid = next((item['FMTID'] for item in p['FormatOffset'] if item['Offset'].int() == offset), None)

        except ptypes.error.ItemNotFoundError:
            fmtid = None

        if fmtid is None:
            return dyn.array(PropertyIdentifierAndOffset, count.int())

        propertyidentifierandoffset = dyn.clone(PropertyIdentifierAndOffset, __format_identifier__=fmtid.identifier())
        return dyn.array(propertyidentifierandoffset, count.int())

    def __Property(self):
        res, fields = self['Size'].li.int(), ['Size', 'NumProperties', 'PropertyIdentifierAndOffset']
        return dyn.block(max(0, res - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'NumProperties'),
        (__PropertyIdentifierAndOffset, 'PropertyIdentifierAndOffset'),
        (__Property, 'Property'),
    ]

    def alloc(self, **fields):
        res = super(PropertySet, self).alloc(**fields)
        if 'NumProperties' not in fields:
            res.set(NumProperties=len(res['PropertyIdentifierAndOffset']))
        if 'Size' not in fields:
            res.set(Size=sum(res[fld].size() for fld in ['Size', 'NumProperties', 'PropertyIdentifierAndOffset']))
        return res

    def enumerate(self):
        for index, item in enumerate(self['PropertyIdentifierAndOffset']):
            property = item['Offset'].d.li
            yield index, item['PropertyIdentifier'], property
        return

    def iterate(self):
        for _, identifier, property in self.enumerate():
            value = {entry['PropertyIdentifier'] : entry['Name'] for _, entry in property.enumerate()} if isinstance(property, Dictionary) else property['Value']
            yield identifier, value
        return

class FMTID(GUID):
    '''
    FMTID_SummaryInformation    {F29F85E0-4FF9-1068-AB91-08002B27B3D9}  "\005SummaryInformation"
    FMTID_DocSummaryInformation {D5CDD502-2E9C-101B-9397-08002B2CF9AE}  "\005DocumentSummaryInformation"
    FMTID_UserDefinedProperties {D5CDD505-2E9C-101B-9397-08002B2CF9AE}  "\005DocumentSummaryInformation"
    FMTID_GlobalInfo            {56616F00-C154-11CE-8553-00AA00A1F95B}  "\005GlobalInfo"
    FMTID_ImageContents         {56616400-C154-11CE-8553-00AA00A1F95B}  "\005ImageContents"
    FMTID_ImageInfo             {56616500-C154-11CE-8553-00AA00A1F95B}  "\005ImageInfo"
    '''
    def identifier(self):
        iterable = (self[fld].int() for fld in self)
        return tuple(iterable)

    def to_name(self):
        res = ptypes.bitmap.new(0, 0)
        for item in bytearray(self.serialize()):
            res = ptypes.bitmap.append(res, (item, 8))
        res = ptypes.bitmap.push(res, ptypes.bitmap.new(0, 2))
        table32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ012345'
        items = [table32[index] for index in map(ptypes.bitmap.int, reversed(ptypes.bitmap.split(res, 5)))]
        string = ''.join(item.lower() if (index * 5) % 8 else item.upper() for index, item in enumerate(items))
        return "\5{:s}".format(string)

    def of_name(self, name):
        prefix, string = name[:1], name[1:]
        table32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ012345'
        lookup = {item : index for index, item in enumerate(table32)}
        integers = [lookup[item.upper()] for item in string]
        items = (ptypes.bitmap.new(integer, 5) for integer in integers)
        res = functools.reduce(ptypes.bitmap.append, items, ptypes.bitmap.new(0, 0))
        integer, zero = ptypes.bitmap.consume(res, 2)
        assert(zero == 0)
        data = bytearray(map(ptypes.bitmap.int, reversed(ptypes.bitmap.split(integer, 8))))
        return self.load(offset=0, source=ptypes.prov.bytes(bytes(data)))

class FMTOFFSET(pstruct.type):
    def __Offset(self):
        try:
            p = self.getparent(PropertySetStream)
        except ptypes.error.ItemNotFoundError:
            return DWORD

        formatId = self['FMTID'].li
        return dyn.rpointer(PropertySet, p, DWORD)

    _fields_ = [
        (FMTID, 'FMTID'),
        (__Offset, 'Offset')
    ]

class PropertySetStream(pstruct.type):
    class _ByteOrder(pint.enum, WORD):
        _values_ = [
            ('LittleEndian', 0xfffe),
            ('BigEndian', 0xfeff),
        ]
    _fields_ = [
        (_ByteOrder, 'ByteOrder'),
        (WORD, 'Version'),
        (DWORD, 'SystemIdentifier'),
        (GUID, 'CLSID'),
        (DWORD, 'NumPropertySets'),
        (lambda self: dyn.array(FMTOFFSET, self['NumPropertySets'].li.int()), 'FormatOffset'),

        # XXX: this might not be correct and are likely dependent on the offset
        #      specified by the FormatOffset array. that's how we figure out the
        #      FMTID in order to choose the correct PropertyIdentifier anywayz.
        (lambda self: dyn.array(PropertySet, self['NumPropertySets'].li.int()), 'PropertySet'),
        (ptype.block, 'Padding'),
    ]

    def enumerate(self):
        for index, item in enumerate(self['FormatOffset']):
            yield index, item['FMTID'], item['Offset'].d.li
        return

### Definitions, based on the PropertySetStream... Should allow
### using office.storage to blindly decode these from the directory.

# XXX: i'm pretty sure that the FMTID has to match in order to
#      be sure about the contents for each of these streams.
@storage.DirectoryStream.define
class SummaryInformationStream(PropertySetStream):
    type = '\005SummaryInformation'

@storage.DirectoryStream.define
class DocumentSummaryInformationStream(PropertySetStream):
    type = '\005DocumentSummaryInformation'

@storage.DirectoryStream.define
class GlobalInfoStream(PropertySetStream):
    type = '\005GlobalInfo'

@storage.DirectoryStream.define
class ImageContentsStream(PropertySetStream):
    type = '\005ImageContents'

@storage.DirectoryStream.define
class ImageInfoStream(PropertySetStream):
    type = '\005ImageInfo'

if __name__ == '__main__':
    import builtins, operator, os, math, functools, itertools, sys, types
    def FhexToData(representation):
        rows = map(operator.methodcaller('strip'), representation.split('\n'))
        items = [item.replace(' ', '') for offset, item in map(operator.methodcaller('split', ' ', 1), filter(None, rows))]
        return bytes().join(map(operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex, items))

    ### SummaryInformation (PropertySetStream)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x FE FF 00 00 06 00 02 00 00 00 00 00 00 00 00 00
    01x 00 00 00 00 00 00 00 00 01 00 00 00 E0 85 9F F2
    02x F9 4F 68 10 AB 91 08 00 2B 27 B3 D9 30 00 00 00
    03x 8C 01 00 00 12 00 00 00 01 00 00 00 98 00 00 00
    04x 02 00 00 00 A0 00 00 00 03 00 00 00 B8 00 00 00
    05x 04 00 00 00 C4 00 00 00 05 00 00 00 D0 00 00 00
    06x 06 00 00 00 DC 00 00 00 07 00 00 00 E8 00 00 00
    07x 08 00 00 00 FC 00 00 00 09 00 00 00 10 01 00 00
    08x 12 00 00 00 1C 01 00 00 0A 00 00 00 3C 01 00 00
    09x 0B 00 00 00 48 01 00 00 0C 00 00 00 54 01 00 00
    0Ax 0D 00 00 00 60 01 00 00 0E 00 00 00 6C 01 00 00
    0Bx 0F 00 00 00 74 01 00 00 10 00 00 00 7C 01 00 00
    0Cx 13 00 00 00 84 01 00 00 02 00 00 00 E4 04 00 00
    0Dx 1E 00 00 00 0F 00 00 00 4A 6F 65 27 73 20 64 6F
    0Ex 63 75 6D 65 6E 74 00 00 1E 00 00 00 04 00 00 00
    0Fx 4A 6F 62 00 1E 00 00 00 04 00 00 00 4A 6F 65 00
    10x 1E 00 00 00 04 00 00 00 00 00 00 00 1E 00 00 00
    11x 04 00 00 00 00 00 00 00 1E 00 00 00 0C 00 00 00
    12x 4E 6F 72 6D 61 6C 2E 64 6F 74 6D 00 1E 00 00 00
    13x 0A 00 00 00 43 6F 72 6E 65 6C 69 75 73 00 00 00
    14x 1E 00 00 00 04 00 00 00 36 36 00 00 1E 00 00 00
    15x 18 00 00 00 4D 69 63 72 6F 73 6F 66 74 20 4F 66
    16x 66 69 63 65 20 57 6F 72 64 00 00 00 40 00 00 00
    17x 00 6E D9 A2 42 00 00 00 40 00 00 00 00 16 D0 A1
    18x 4E 8E C6 01 40 00 00 00 00 1C F2 D5 2A CE C6 01
    19x 40 00 00 00 00 3C DC 73 DD 80 C8 01 03 00 00 00
    1Ax 0E 00 00 00 03 00 00 00 E5 0D 00 00 03 00 00 00
    1Bx 38 4F 00 00 03 00 00 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### CodePage Property (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 02 00 00 00 E4 04 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_TITLE (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 0F 00 00 00 4A 6F 65 27 73 20 64 6F
    01x 63 75 6D 65 6E 74 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_SUBJECT (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 04 00 00 00 4A 6F 62 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_AUTHOR (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 04 00 00 00 4A 6F 65 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_KEYWORDS (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 04 00 00 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_COMMENTS (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 04 00 00 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_TEMPLATE (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 0C 00 00 00 4E 6F 72 6D 61 6C 2E 64
    01x 6F 74 6D 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_LASTAUTHOR (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 0A 00 00 00 43 6F 72 6E 65 6C 69 75
    01x 73 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_REVNUMBER (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 04 00 00 00 36 36 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_APPNAME (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 1E 00 00 00 18 00 00 00 4D 69 63 72 6F 73 6F 66
    01x 74 20 4F 66 66 69 63 65 20 57 6F 72 64 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_EDITTIME (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 40 00 00 00 00 6E D9 A2 42 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_LASTPRINTED (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 40 00 00 00 00 16 D0 A1 4E 8E C6 01
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_CREATE_DTM (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 40 00 00 00 00 1C F2 D5 2A CE C6 01
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_LASTSAVE_DTM (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 40 00 00 00 00 3C DC 73 DD 80 C8 01
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_PAGECOUNT (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 03 00 00 00 0E 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_WORDCOUNT (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 03 00 00 00 E5 0D 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_CHARCOUNT (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 03 00 00 00 38 4F 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### PIDSI_DOC_SECURITY (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 03 00 00 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Control Stream (alternate stream binding?)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 00 00 00 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### "CONTENTS" Stream (PropertySetStream)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x FE FF 01 00 06 00 02 00 53 FF 4B 99 F9 DD AD 42
    01x A5 6A FF EA 36 17 AC 16 01 00 00 00 01 18 00 20
    02x E6 5D D1 11 8E 38 00 C0 4F B9 38 6D 30 00 00 00
    03x DC 01 00 00 0A 00 00 00 01 00 00 00 58 00 00 00
    04x 00 00 00 80 60 00 00 00 01 00 00 80 68 00 00 00
    05x 00 00 00 00 70 00 00 00 04 00 00 00 38 01 00 00
    06x 06 00 00 00 4C 01 00 00 07 00 00 00 70 01 00 00
    07x 0C 00 00 00 7C 01 00 00 27 00 00 00 94 01 00 00
    08x 92 00 00 00 C0 01 00 00 02 00 00 00 B0 04 00 00
    09x 13 00 00 00 00 00 09 08 13 00 00 00 01 00 00 00
    0Ax 06 00 00 00 04 00 00 00 0E 00 00 00 44 00 69 00
    0Bx 73 00 70 00 6C 00 61 00 79 00 43 00 6F 00 6C 00
    0Cx 6F 00 75 00 72 00 00 00 06 00 00 00 09 00 00 00
    0Dx 4D 00 79 00 53 00 74 00 72 00 65 00 61 00 6D 00
    0Ex 00 00 00 00 07 00 00 00 0B 00 00 00 50 00 72 00
    0Fx 69 00 63 00 65 00 28 00 47 00 42 00 50 00 29 00
    10x 00 00 00 00 0C 00 00 00 0A 00 00 00 4D 00 79 00
    11x 53 00 74 00 6F 00 72 00 61 00 67 00 65 00 00 00
    12x 27 00 00 00 0E 00 00 00 43 00 61 00 73 00 65 00
    13x 53 00 65 00 6E 00 73 00 69 00 74 00 69 00 76 00
    14x 65 00 00 00 92 00 00 00 0E 00 00 00 43 00 41 00
    15x 53 00 45 00 53 00 45 00 4E 00 53 00 49 00 54 00
    16x 49 00 56 00 45 00 00 00 08 00 00 00 0A 00 00 00
    17x 47 00 72 00 65 00 79 00 00 00 00 00 49 00 00 00
    18x CA 84 95 F9 23 CA 0B 47 83 94 22 01 77 90 7A AD
    19x 0C 00 00 00 70 00 72 00 6F 00 70 00 36 00 00 00
    1Ax 06 00 00 00 00 50 14 00 00 00 00 00 45 00 00 00
    1Bx 0E 00 00 00 70 00 72 00 6F 00 70 00 31 00 32 00
    1Cx 00 00 00 00 10 20 00 00 10 00 00 00 02 00 00 00
    1Dx 03 00 00 00 FF FF FF FF 05 00 00 00 00 00 00 00
    1Ex 03 F8 14 17 12 87 45 29 25 11 33 56 79 A2 9C 00
    1Fx 0C 10 00 00 02 00 00 00 11 00 00 00 A9 00 00 00
    20x 14 00 00 00 A9 00 76 99 3B 22 10 9C
    '''
    data = FhexToData(hexadecimal_representation)

    ### CodePage (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 02 00 00 00 B0 04 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Locale (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 13 00 00 00 00 00 09 08
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary (Dictionary)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 06 00 00 00 04 00 00 00 0E 00 00 00 44 00 69 00
    01x 73 00 70 00 6C 00 61 00 79 00 43 00 6F 00 6C 00
    02x 6F 00 75 00 72 00 00 00 06 00 00 00 09 00 00 00
    03x 4D 00 79 00 53 00 74 00 72 00 65 00 61 00 6D 00
    04x 00 00 00 00 07 00 00 00 0B 00 00 00 50 00 72 00
    05x 69 00 63 00 65 00 28 00 47 00 42 00 50 00 29 00
    06x 00 00 00 00 0C 00 00 00 0A 00 00 00 4D 00 79 00
    07x 53 00 74 00 6F 00 72 00 61 00 67 00 65 00 00 00
    08x 27 00 00 00 0E 00 00 00 43 00 61 00 73 00 65 00
    09x 53 00 65 00 6E 00 73 00 69 00 74 00 69 00 76 00
    0Ax 65 00 00 00 92 00 00 00 0E 00 00 00 43 00 41 00
    0Bx 53 00 45 00 53 00 45 00 4E 00 53 00 49 00 54 00
    0Cx 49 00 56 00 45 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 0 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 04 00 00 00 0E 00 00 00 44 00 69 00 73 00 70 00
    00x 6C 00 61 00 79 00 43 00 6F 00 6C 00 6F 00 75 00
    02x 72 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 1 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 06 00 00 00 09 00 00 00 4D 00 79 00 53 00 74 00
    00x 72 00 65 00 61 00 6D 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 2 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 07 00 00 00 0B 00 00 00 50 00 72 00 69 00 63 00
    00x 65 00 28 00 47 00 42 00 50 00 29 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 3 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 0C 00 00 00 0A 00 00 00 4D 00 79 00 53 00 74 00
    00x 6F 00 72 00 61 00 67 00 65 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 4 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 27 00 00 00 0E 00 00 00 43 00 61 00 73 00 65 00
    00x 53 00 65 00 6E 00 73 00 69 00 74 00 69 00 76 00
    02x 65 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Dictionary Entry 5 (DictionaryEntry)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 92 00 00 00 0E 00 00 00 43 00 41 00 53 00 45 00
    00x 53 00 45 00 4E 00 53 00 49 00 54 00 49 00 56 00
    02x 45 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### DisplayColour (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 08 00 00 00 0A 00 00 00 47 00 72 00 65 00 79 00
    01x 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### MyStream (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 49 00 00 00 CA 84 95 F9 23 CA 0B 47 83 94 22 01
    01x 77 90 7A AD 0C 00 00 00 70 00 72 00 6F 00 70 00
    02x 36 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### Price(GBP) (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 06 00 00 00 00 50 14 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### MyStorage (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    01x 45 00 00 00 0E 00 00 00 70 00 72 00 6F 00 70 00
    02x 31 00 32 00 00 00 00 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### CaseSensitive Mixed Case (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 10 20 00 00 10 00 00 00 02 00 00 00 03 00 00 00
    01x FF FF FF FF 05 00 00 00 00 00 00 00 03 F8 14 17
    02x 12 87 45 29 25 11 33 56 79 A2 9C 00
    '''
    data = FhexToData(hexadecimal_representation)

    ### CASESENSITIVE All Uppercase (TypedPropertyValue)
    #   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9 xA xB xC xD xE xF
    hexadecimal_representation = '''
    00x 0C 10 00 00 02 00 00 00 11 00 00 00 A9 00 00 00
    01x 14 00 00 00 A9 00 76 99 3B 22 10 9C
    '''
    data = FhexToData(hexadecimal_representation)

    {
        "000000010040": "PidLidAttendeeCriticalChange",
        "00000002001F": "PidLidWhere",
        "000000030102": "PidLidGlobalObjectId",
        "00000004000B": "PidLidIsSilent",
        "00000005000B": "PidLidIsRecurring",
        "00000006001F": "PidLidRequiredAttendees",
        "00000007001F": "PidLidOptionalAttendees",
        "00000008001F": "PidLidResourceAttendees",
        "00000009000B": "PidLidDelegateMail",
        "0000000A000B": "PidLidIsException",
        "0000000C0003": "PidLidTimeZone",
        "0000000D0003": "PidLidStartRecurrenceDate",
        "0000000E0003": "PidLidStartRecurrenceTime",
        "0000000F0003": "PidLidEndRecurrenceDate",
        "000000100003": "PidLidEndRecurrenceTime",
        "000000110002": "PidLidDayInterval",
        "000000120002": "PidLidWeekInterval",
        "000000130002": "PidLidMonthInterval",
        "000000140002": "PidLidYearInterval",
        "000000150003": "PidLidClientIntent",
        "000000170003": "PidLidMonthOfYearMask",
        "000000180002": "PidLidOldRecurrenceType",
        "0000001A0040": "PidLidOwnerCriticalChange",
        "0000001C0003": "PidLidCalendarType",
        "000000230102": "PidLidCleanGlobalObjectId",
        "00000024001F": "PidLidAppointmentMessageClass",
        "000000260003": "PidLidMeetingType",
        "00000028001F": "PidLidOldLocation",
        "000000290040": "PidLidOldWhenStartWhole",
        "0000002A0040": "PidLidOldWhenEndWhole",
        "000010000003": "PidLidDayOfMonth",
        "000010010003": "PidLidICalendarDayOfWeekMask",
        "000010050003": "PidLidOccurrences",
        "000010060003": "PidLidMonthOfYear",
        "0000100B000B": "PidLidNoEndDateFlag",
        "0000100D0003": "PidLidRecurrenceDuration",
        "00008005001F": "PidLidFileUnder",
        "000080060003": "PidLidFileUnderId",
        "000080071003": "PidLidContactItemData",
        "00008010001F": "PidLidDepartment",
        "00008015000B": "PidLidHasPicture",
        "0000801A001F": "PidLidHomeAddress",
        "0000801B001F": "PidLidWorkAddress",
        "0000801C001F": "PidLidOtherAddress",
        "000080220003": "PidLidPostalAddressId",
        "000080230003": "PidLidContactCharacterSet",
        "00008025000B": "PidLidAutoLog",
        "000080261003": "PidLidFileUnderList",
        "000080281003": "PidLidAddressBookProviderEmailList",
        "000080290003": "PidLidAddressBookProviderArrayType",
        "0000802B001F": "PidLidHtml",
        "0000802C001F": "PidLidYomiFirstName",
        "0000802D001F": "PidLidYomiLastName",
        "0000802E001F": "PidLidYomiCompanyName",
        "000080400102": "PidLidBusinessCardDisplayDefinition",
        "000080410102": "PidLidBusinessCardCardPicture",
        "00008045000B": "PidLidPromptSendUpdate",
        "00008045001F": "PidLidWorkAddressStreet",
        "00008046001F": "PidLidWorkAddressCity",
        "00008047001F": "PidLidWorkAddressState",
        "00008048001F": "PidLidWorkAddressPostalCode",
        "00008049001F": "PidLidWorkAddressCountry",
        "0000804A001F": "PidLidWorkAddressPostOfficeBox",
        "0000804C0003": "PidLidDistributionListChecksum",
        "0000804D0102": "PidLidBirthdayEventEntryId",
        "0000804E0102": "PidLidAnniversaryEventEntryId",
        "0000804F001F": "PidLidContactUserField1",
        "00008050001F": "PidLidContactUserField2",
        "00008051001F": "PidLidContactUserField3",
        "00008052001F": "PidLidContactUserField4",
        "00008053001F": "PidLidDistributionListName",
        "000080541102": "PidLidDistributionListOneOffMembers",
        "000080551102": "PidLidDistributionListMembers",
        "00008062001F": "PidLidInstantMessagingAddress",
        "000080640102": "PidLidDistributionListStream",
        "00008080001F": "PidLidEmail1DisplayName",
        "00008082001F": "PidLidEmail1AddressType",
        "00008083001F": "PidLidEmail1EmailAddress",
        "00008084001F": "PidLidEmail1OriginalDisplayName",
        "000080850102": "PidLidEmail1OriginalEntryId",
        "00008090001F": "PidLidEmail2DisplayName",
        "00008092001F": "PidLidEmail2AddressType",
        "00008093001F": "PidLidEmail2EmailAddress",
        "00008094001F": "PidLidEmail2OriginalDisplayName",
        "000080950102": "PidLidEmail2OriginalEntryId",
        "000080A0001F": "PidLidEmail3DisplayName",
        "000080A2001F": "PidLidEmail3AddressType",
        "000080A3001F": "PidLidEmail3EmailAddress",
        "000080A4001F": "PidLidEmail3OriginalDisplayName",
        "000080A50102": "PidLidEmail3OriginalEntryId",
        "000080B2001F": "PidLidFax1AddressType",
        "000080B3001F": "PidLidFax1EmailAddress",
        "000080B4001F": "PidLidFax1OriginalDisplayName",
        "000080B50102": "PidLidFax1OriginalEntryId",
        "000080C2001F": "PidLidFax2AddressType",
        "000080C3001F": "PidLidFax2EmailAddress",
        "000080C4001F": "PidLidFax2OriginalDisplayName",
        "000080C50102": "PidLidFax2OriginalEntryId",
        "000080D2001F": "PidLidFax3AddressType",
        "000080D3001F": "PidLidFax3EmailAddress",
        "000080D4001F": "PidLidFax3OriginalDisplayName",
        "000080D50102": "PidLidFax3OriginalEntryId",
        "000080D8001F": "PidLidFreeBusyLocation",
        "000080DA001F": "PidLidHomeAddressCountryCode",
        "000080DB001F": "PidLidWorkAddressCountryCode",
        "000080DC001F": "PidLidOtherAddressCountryCode",
        "000080DD001F": "PidLidAddressCountryCode",
        "000080DE0040": "PidLidBirthdayLocal",
        "000080DF0040": "PidLidWeddingAnniversaryLocal",
        "000080E0000B": "PidLidIsContactLinked",
        "000080E20102": "PidLidContactLinkedGlobalAddressListEntryId",
        "000080E3101F": "PidLidContactLinkSMTPAddressCache",
        "000080E51102": "PidLidContactLinkLinkRejectHistory",
        "000080E60003": "PidLidContactLinkGlobalAddressListLinkState",
        "000080E80048": "PidLidContactLinkGlobalAddressListLinkId",
        "000081010003": "PidLidTaskStatus",
        "000081020005": "PidLidPercentComplete",
        "00008103000B": "PidLidTeamTask",
        "000081040040": "PidLidTaskStartDate",
        "000081050040": "PidLidTaskDueDate",
        "00008107000B": "PidLidTaskResetReminder",
        "00008108000B": "PidLidTaskAccepted",
        "00008109000B": "PidLidTaskDeadOccurrence",
        "0000810F0040": "PidLidTaskDateCompleted",
        "000081100003": "PidLidTaskActualEffort",
        "000081110003": "PidLidTaskEstimatedEffort",
        "000081120003": "PidLidTaskVersion",
        "000081130003": "PidLidTaskState",
        "000081150040": "PidLidTaskLastUpdate",
        "000081160102": "PidLidTaskRecurrence",
        "000081170102": "PidLidTaskAssigners",
        "00008119000B": "PidLidTaskStatusOnComplete",
        "0000811A0003": "PidLidTaskHistory",
        "0000811B000B": "PidLidTaskUpdates",
        "0000811C000B": "PidLidTaskComplete",
        "0000811E000B": "PidLidTaskFCreator",
        "0000811F001F": "PidLidTaskOwner",
        "000081200003": "PidLidTaskMultipleRecipients",
        "00008121001F": "PidLidTaskAssigner",
        "00008122001F": "PidLidTaskLastUser",
        "000081230003": "PidLidTaskOrdinal",
        "00008124000B": "PidLidTaskNoCompute",
        "00008125001F": "PidLidTaskLastDelegate",
        "00008126000B": "PidLidTaskFRecurring",
        "00008127001F": "PidLidTaskRole",
        "000081290003": "PidLidTaskOwnership",
        "0000812A0003": "PidLidTaskAcceptanceState",
        "0000812C000B": "PidLidTaskFFixOffline",
        "000081390003": "PidLidTaskCustomFlags",
        "000082010003": "PidLidAppointmentSequence",
        "000082020040": "PidLidAppointmentSequenceTime",
        "000082030003": "PidLidAppointmentLastSequence",
        "000082040003": "PidLidChangeHighlight",
        "000082050003": "PidLidBusyStatus",
        "00008206000B": "PidLidFExceptionalBody",
        "000082070003": "PidLidAppointmentAuxiliaryFlags",
        "00008208001F": "PidLidLocation",
        "00008209001F": "PidLidMeetingWorkspaceUrl",
        "0000820A000B": "PidLidForwardInstance",
        "0000820C1102": "PidLidLinkedTaskItems",
        "0000820D0040": "PidLidAppointmentStartWhole",
        "0000820E0040": "PidLidAppointmentEndWhole",
        "0000820F0040": "PidLidAppointmentStartTime",
        "000082100040": "PidLidAppointmentEndTime",
        "000082110040": "PidLidAppointmentEndDate",
        "000082120040": "PidLidAppointmentStartDate",
        "000082130003": "PidLidAppointmentDuration",
        "000082140003": "PidLidAppointmentColor",
        "00008215000B": "PidLidAppointmentSubType",
        "000082160102": "PidLidAppointmentRecur",
        "000082170003": "PidLidAppointmentStateFlags",
        "000082180003": "PidLidResponseStatus",
        "000082200040": "PidLidAppointmentReplyTime",
        "00008223000B": "PidLidRecurring",
        "000082240003": "PidLidIntendedBusyStatus",
        "000082260040": "PidLidAppointmentUpdateTime",
        "000082280040": "PidLidExceptionReplaceTime",
        "00008229000B": "PidLidFInvited",
        "0000822B000B": "PidLidFExceptionalAttendees",
        "0000822E001F": "PidLidOwnerName",
        "0000822F000B": "PidLidFOthersAppointment",
        "00008230001F": "PidLidAppointmentReplyName",
        "000082310003": "PidLidRecurrenceType",
        "00008232001F": "PidLidRecurrencePattern",
        "000082330102": "PidLidTimeZoneStruct",
        "00008234001F": "PidLidTimeZoneDescription",
        "000082350040": "PidLidClipStart",
        "000082360040": "PidLidClipEnd",
        "000082370102": "PidLidOriginalStoreEntryId",
        "00008238001F": "PidLidAllAttendeesString",
        "0000823A000B": "PidLidAutoFillLocation",
        "0000823B001F": "PidLidToAttendeesString",
        "0000823C001F": "PidLidCcAttendeesString",
        "00008240000B": "PidLidConferencingCheck",
        "000082410003": "PidLidConferencingType",
        "00008242001F": "PidLidDirectory",
        "00008243001F": "PidLidOrganizerAlias",
        "00008244000B": "PidLidAutoStartCheck",
        "00008246000B": "PidLidAllowExternalCheck",
        "00008247001F": "PidLidCollaborateDoc",
        "00008248001F": "PidLidNetShowUrl",
        "00008249001F": "PidLidOnlinePassword",
        "000082500040": "PidLidAppointmentProposedStartWhole",
        "000082510040": "PidLidAppointmentProposedEndWhole",
        "000082560003": "PidLidAppointmentProposedDuration",
        "00008257000B": "PidLidAppointmentCounterProposal",
        "000082590003": "PidLidAppointmentProposalNumber",
        "0000825A000B": "PidLidAppointmentNotAllowPropose",
        "0000825D0102": "PidLidAppointmentUnsendableRecipients",
        "0000825E0102": "PidLidAppointmentTimeZoneDefinitionStartDisplay",
        "0000825F0102": "PidLidAppointmentTimeZoneDefinitionEndDisplay",
        "000082600102": "PidLidAppointmentTimeZoneDefinitionRecur",
        "000082610102": "PidLidForwardNotificationRecipients",
        "0000827A0102": "PidLidInboundICalStream",
        "0000827B000B": "PidLidSingleBodyICal",
        "000085010003": "PidLidReminderDelta",
        "000085020040": "PidLidReminderTime",
        "00008503000B": "PidLidReminderSet",
        "000085040040": "PidLidReminderTimeTime",
        "000085050040": "PidLidReminderTimeDate",
        "00008506000B": "PidLidPrivate",
        "0000850E000B": "PidLidAgingDontAgeMe",
        "000085100003": "PidLidSideEffects",
        "000085110003": "PidLidRemoteStatus",
        "00008514000B": "PidLidSmartNoAttach",
        "000085160040": "PidLidCommonStart",
        "000085170040": "PidLidCommonEnd",
        "000085180003": "PidLidTaskMode",
        "000085190102": "PidLidTaskGlobalId",
        "0000851A0003": "PidLidAutoProcessState",
        "0000851C000B": "PidLidReminderOverride",
        "0000851D0003": "PidLidReminderType",
        "0000851E000B": "PidLidReminderPlaySound",
        "0000851F001F": "PidLidReminderFileParameter",
        "000085200102": "PidLidVerbStream",
        "00008524001F": "PidLidVerbResponse",
        "00008530001F": "PidLidFlagRequest",
        "00008535001F": "PidLidBilling",
        "00008536001F": "PidLidNonSendableTo",
        "00008537001F": "PidLidNonSendableCc",
        "00008538001F": "PidLidNonSendableBcc",
        "00008539101F": "PidLidCompanies",
        "0000853A101F": "PidLidContacts",
        "000085431003": "PidLidNonSendToTrackStatus",
        "000085441003": "PidLidNonSendCcTrackStatus",
        "000085451003": "PidLidNonSendBccTrackStatus",
        "000085520003": "PidLidCurrentVersion",
        "00008554001F": "PidLidCurrentVersionName",
        "000085600040": "PidLidReminderSignalTime",
        "00008580001F": "PidLidInternetAccountName",
        "00008581001F": "PidLidInternetAccountStamp",
        "00008582000B": "PidLidUseTnef",
        "000085840102": "PidLidContactLinkSearchKey",
        "000085850102": "PidLidContactLinkEntry",
        "00008586001F": "PidLidContactLinkName",
        "0000859C0102": "PidLidSpamOriginalFolder",
        "000085A00040": "PidLidToDoOrdinalDate",
        "000085A1001F": "PidLidToDoSubOrdinal",
        "000085A4001F": "PidLidToDoTitle",
        "000085B1001F": "PidLidInfoPathFormName",
        "000085B5000B": "PidLidClassified",
        "000085B6001F": "PidLidClassification",
        "000085B7001F": "PidLidClassificationDescription",
        "000085B8001F": "PidLidClassificationGuid",
        "000085BA000B": "PidLidClassificationKeep",
        "000085BD0102": "PidLidReferenceEntryId",
        "000085BF0040": "PidLidValidFlagStringProof",
        "000085C00003": "PidLidFlagString",
        "000085C60102": "PidLidConversationActionMoveFolderEid",
        "000085C70102": "PidLidConversationActionMoveStoreEid",
        "000085C80040": "PidLidConversationActionMaxDeliveryTime",
        "000085C90003": "PidLidConversationProcessed",
        "000085CA0040": "PidLidConversationActionLastAppliedTime",
        "000085CB0003": "PidLidConversationActionVersion",
        "000085CC000B": "PidLidServerProcessed",
        "000085CD0003": "PidLidServerProcessingActions",
        "000085E00003": "PidLidPendingStateForSiteMailboxDocument",
        "00008700001F": "PidLidLogType",
        "000087060040": "PidLidLogStart",
        "000087070003": "PidLidLogDuration",
        "000087080040": "PidLidLogEnd",
        "0000870C0003": "PidLidLogFlags",
        "0000870E000B": "PidLidLogDocumentPrinted",
        "0000870F000B": "PidLidLogDocumentSaved",
        "00008710000B": "PidLidLogDocumentRouted",
        "00008711000B": "PidLidLogDocumentPosted",
        "00008712001F": "PidLidLogTypeDesc",
        "00008900001F": "PidLidPostRssChannelLink",
        "00008901001F": "PidLidPostRssItemLink",
        "000089020003": "PidLidPostRssItemHash",
        "00008903001F": "PidLidPostRssItemGuid",
        "00008904001F": "PidLidPostRssChannel",
        "00008905001F": "PidLidPostRssItemXml",
        "00008906001F": "PidLidPostRssSubscription",
        "00008A000003": "PidLidSharingStatus",
        "00008A010102": "PidLidSharingProviderGuid",
        "00008A02001F": "PidLidSharingProviderName",
        "00008A03001F": "PidLidSharingProviderUrl",
        "00008A04001F": "PidLidSharingRemotePath",
        "00008A05001F": "PidLidSharingRemoteName",
        "00008A06001F": "PidLidSharingRemoteUid",
        "00008A07001F": "PidLidSharingInitiatorName",
        "00008A08001F": "PidLidSharingInitiatorSmtp",
        "00008A090102": "PidLidSharingInitiatorEntryId",
        "00008A0A0003": "PidLidSharingFlags",
        "00008A0B001F": "PidLidSharingProviderExtension",
        "00008A0C001F": "PidLidSharingRemoteUser",
        "00008A0D001F": "PidLidSharingRemotePass",
        "00008A0E001F": "PidLidSharingLocalPath",
        "00008A0F001F": "PidLidSharingLocalName",
        "00008A10001F": "PidLidSharingLocalUid",
        "00008A130102": "PidLidSharingFilter",
        "00008A14001F": "PidLidSharingLocalType",
        "00008A150102": "PidLidSharingFolderEntryId",
        "00008A170003": "PidLidSharingCapabilities",
        "00008A180003": "PidLidSharingFlavor",
        "00008A190003": "PidLidSharingAnonymity",
        "00008A1A0003": "PidLidSharingReciprocation",
        "00008A1B0003": "PidLidSharingPermissions",
        "00008A1C0102": "PidLidSharingInstanceGuid",
        "00008A1D001F": "PidLidSharingRemoteType",
        "00008A1E001F": "PidLidSharingParticipants",
        "00008A1F0040": "PidLidSharingLastSyncTime",
        "00008A21001F": "PidLidSharingExtensionXml",
        "00008A220040": "PidLidSharingRemoteLastModificationTime",
        "00008A230040": "PidLidSharingLocalLastModificationTime",
        "00008A24001F": "PidLidSharingConfigurationUrl",
        "00008A250040": "PidLidSharingStart",
        "00008A260040": "PidLidSharingStop",
        "00008A270003": "PidLidSharingResponseType",
        "00008A280040": "PidLidSharingResponseTime",
        "00008A290102": "PidLidSharingOriginalMessageEntryId",
        "00008A2A0003": "PidLidSharingSyncInterval",
        "00008A2B0003": "PidLidSharingDetail",
        "00008A2C0003": "PidLidSharingTimeToLive",
        "00008A2D0102": "PidLidSharingBindingEntryId",
        "00008A2E0102": "PidLidSharingIndexEntryId",
        "00008A2F001F": "PidLidSharingRemoteComment",
        "00008A400040": "PidLidSharingWorkingHoursStart",
        "00008A410040": "PidLidSharingWorkingHoursEnd",
        "00008A420003": "PidLidSharingWorkingHoursDays",
        "00008A430102": "PidLidSharingWorkingHoursTimeZone",
        "00008A440040": "PidLidSharingDataRangeStart",
        "00008A450040": "PidLidSharingDataRangeEnd",
        "00008A460003": "PidLidSharingRangeStart",
        "00008A470003": "PidLidSharingRangeEnd",
        "00008A48001F": "PidLidSharingRemoteStoreUid",
        "00008A49001F": "PidLidSharingLocalStoreUid",
        "00008A4B0003": "PidLidSharingRemoteByteSize",
        "00008A4C0003": "PidLidSharingRemoteCrc",
        "00008A4D001F": "PidLidSharingLocalComment",
        "00008A4E0003": "PidLidSharingRoamLog",
        "00008A4F0003": "PidLidSharingRemoteMessageCount",
        "00008A51001F": "PidLidSharingBrowseUrl",
        "00008A550040": "PidLidSharingLastAutoSyncTime",
        "00008A560003": "PidLidSharingTimeToLiveAuto",
        "00008A5B001F": "PidLidSharingRemoteVersion",
        "00008A5C0102": "PidLidSharingParentBindingEntryId",
        "00008A600003": "PidLidSharingSyncFlags",
        "00008B000003": "PidLidNoteColor",
        "00008B020003": "PidLidNoteWidth",
        "00008B030003": "PidLidNoteHeight",
        "00008B040003": "PidLidNoteX",
        "00008B050003": "PidLidNoteY",
        "00009000101F": "PidLidCategories",
        "00010102": "PidTagTemplateData",
        "0002": "PidNameXVoiceMessageDuration",
        "0002000B": "PidTagAlternateRecipientAllowed",
        "0003": "PidNameWordCount",
        "0004001F": "PidTagAutoForwardComment",
        "00040102": "PidTagScriptData",
        "0005": "PidNameCalendarGeoLongitude",
        "0005000B": "PidTagAutoForwarded",
        "000B": "PidNameXRequireProtectedPlayOnPhone",
        "000F0040": "PidTagDeferredDeliveryTime",
        "00100040": "PidTagDeliverTime",
        "00150040": "PidTagExpiryTime",
        "00170003": "PidTagImportance",
        "001A001F": "PidTagMessageClass",
        "001F": "PidNameXVoiceMessageSenderName",
        "0023000B": "PidTagOriginatorDeliveryReportRequested",
        "00250102": "PidTagParentKey",
        "00260003": "PidTagPriority",
        "0029000B": "PidTagReadReceiptRequested",
        "002A0040": "PidTagReceiptTime",
        "002B000B": "PidTagRecipientReassignmentProhibited",
        "002E0003": "PidTagOriginalSensitivity",
        "00300040": "PidTagReplyTime",
        "00310102": "PidTagReportTag",
        "00320040": "PidTagReportTime",
        "00360003": "PidTagSensitivity",
        "0037001F": "PidTagSubject",
        "00390040": "PidTagClientSubmitTime",
        "003A001F": "PidTagReportName",
        "003B0102": "PidTagSentRepresentingSearchKey",
        "003D001F": "PidTagSubjectPrefix",
        "003F0102": "PidTagReceivedByEntryId",
        "0040": "PidNameOMSScheduleTime",
        "0040001F": "PidTagReceivedByName",
        "00410102": "PidTagSentRepresentingEntryId",
        "0042001F": "PidTagSentRepresentingName",
        "00430102": "PidTagReceivedRepresentingEntryId",
        "0044001F": "PidTagReceivedRepresentingName",
        "00450102": "PidTagReportEntryId",
        "00460102": "PidTagReadReceiptEntryId",
        "00470102": "PidTagMessageSubmissionId",
        "0049001F": "PidTagOriginalSubject",
        "004B001F": "PidTagOriginalMessageClass",
        "004C0102": "PidTagOriginalAuthorEntryId",
        "004D001F": "PidTagOriginalAuthorName",
        "004E0040": "PidTagOriginalSubmitTime",
        "004F0102": "PidTagReplyRecipientEntries",
        "0050001F": "PidTagReplyRecipientNames",
        "00510102": "PidTagReceivedBySearchKey",
        "00520102": "PidTagReceivedRepresentingSearchKey",
        "00530102": "PidTagReadReceiptSearchKey",
        "00540102": "PidTagReportSearchKey",
        "00550040": "PidTagOriginalDeliveryTime",
        "0057000B": "PidTagMessageToMe",
        "0058000B": "PidTagMessageCcMe",
        "0059000B": "PidTagMessageRecipientMe",
        "005A001F": "PidTagOriginalSenderName",
        "005B0102": "PidTagOriginalSenderEntryId",
        "005C0102": "PidTagOriginalSenderSearchKey",
        "005D001F": "PidTagOriginalSentRepresentingName",
        "005E0102": "PidTagOriginalSentRepresentingEntryId",
        "005F0102": "PidTagOriginalSentRepresentingSearchKey",
        "00600040": "PidTagStartDate",
        "00610040": "PidTagEndDate",
        "00620003": "PidTagOwnerAppointmentId",
        "0063000B": "PidTagResponseRequested",
        "0064001F": "PidTagSentRepresentingAddressType",
        "0065001F": "PidTagSentRepresentingEmailAddress",
        "0066001F": "PidTagOriginalSenderAddressType",
        "0067001F": "PidTagOriginalSenderEmailAddress",
        "0068001F": "PidTagOriginalSentRepresentingAddressType",
        "0069001F": "PidTagOriginalSentRepresentingEmailAddress",
        "0070001F": "PidTagConversationTopic",
        "00710102": "PidTagConversationIndex",
        "0072001F": "PidTagOriginalDisplayBcc",
        "0073001F": "PidTagOriginalDisplayCc",
        "0074001F": "PidTagOriginalDisplayTo",
        "0075001F": "PidTagReceivedByAddressType",
        "0076001F": "PidTagReceivedByEmailAddress",
        "0077001F": "PidTagReceivedRepresentingAddressType",
        "0078001F": "PidTagReceivedRepresentingEmailAddress",
        "007D001F": "PidTagTransportMessageHeaders",
        "007F0102": "PidTagTnefCorrelationKey",
        "0080001F": "PidTagReportDisposition",
        "0081001F": "PidTagReportDispositionMode",
        "0102": "PidNameThumbnail",
        "08070003": "PidTagAddressBookRoomCapacity",
        "0809001F": "PidTagAddressBookRoomDescription",
        "0C040003": "PidTagNonDeliveryReportReasonCode",
        "0C050003": "PidTagNonDeliveryReportDiagCode",
        "0C06000B": "PidTagNonDeliveryReportStatusCode",
        "0C08000B": "PidTagOriginatorNonDeliveryReportRequested",
        "0C150003": "PidTagRecipientType",
        "0C17000B": "PidTagReplyRequested",
        "0C190102": "PidTagSenderEntryId",
        "0C1A001F": "PidTagSenderName",
        "0C1B001F": "PidTagSupplementaryInfo",
        "0C1D0102": "PidTagSenderSearchKey",
        "0C1E001F": "PidTagSenderAddressType",
        "0C1F001F": "PidTagSenderEmailAddress",
        "0C200003": "PidTagNonDeliveryReportStatusCode",
        "0C21001F": "PidTagRemoteMessageTransferAgent",
        "0E01000B": "PidTagDeleteAfterSubmit",
        "0E02001F": "PidTagDisplayBcc",
        "0E03001F": "PidTagDisplayCc",
        "0E04001F": "PidTagDisplayTo",
        "0E060040": "PidTagMessageDeliveryTime",
        "0E070003": "PidTagMessageFlags",
        "0E080003": "PidTagMessageSize",
        "0E080014": "PidTagMessageSizeExtended",
        "0E090102": "PidTagParentEntryId",
        "0E0F000B": "PidTagResponsibility",
        "0E12000D": "PidTagMessageRecipients",
        "0E13000D": "PidTagMessageAttachments",
        "0E170003": "PidTagMessageStatus",
        "0E1B000B": "PidTagHasAttachments",
        "0E1D001F": "PidTagNormalizedSubject",
        "0E1F000B": "PidTagRtfInSync",
        "0E200003": "PidTagAttachSize",
        "0E210003": "PidTagAttachNumber",
        "0E28001F": "PidTagPrimarySendAccount",
        "0E29001F": "PidTagNextSendAcct",
        "0E2B0003": "PidTagToDoItemFlags",
        "0E2C0102": "PidTagSwappedToDoStore",
        "0E2D0102": "PidTagSwappedToDoData",
        "0E69000B": "PidTagRead",
        "0E6A001F": "PidTagSecurityDescriptorAsXml",
        "0E790003": "PidTagTrustSender",
        "0E840102": "PidTagExchangeNTSecurityDescriptor",
        "0E990102": "PidTagExtendedRuleMessageActions",
        "0E9A0102": "PidTagExtendedRuleMessageCondition",
        "0E9B0003": "PidTagExtendedRuleSizeLimit",
        "0FF40003": "PidTagAccess",
        "0FF50003": "PidTagRowType",
        "0FF60102": "PidTagInstanceKey",
        "0FF70003": "PidTagAccessLevel",
        "0FF80102": "PidTagMappingSignature",
        "0FF90102": "PidTagRecordKey",
        "0FFB0102": "PidTagStoreEntryId",
        "0FFE0003": "PidTagObjectType",
        "0FFF0102": "PidTagEntryId",
        "1000001F": "PidTagBody",
        "1001001F": "PidTagReportText",
        "10090102": "PidTagRtfCompressed",
        "1013001F": "PidTagBodyHtml",
        "10130102": "PidTagHtml",
        "1014001F": "PidTagBodyContentLocation",
        "1015001F": "PidTagBodyContentId",
        "10160003": "PidTagNativeBody",
        "101F": "PidNameKeywords",
        "1035001F": "PidTagInternetMessageId",
        "1039001F": "PidTagInternetReferences",
        "1040": "PidNameICalendarRecurrenceDate",
        "1042001F": "PidTagInReplyToId",
        "1043001F": "PidTagListHelp",
        "1044001F": "PidTagListSubscribe",
        "1045001F": "PidTagListUnsubscribe",
        "1046001F": "PidTagOriginalMessageId",
        "10800003": "PidTagIconIndex",
        "10810003": "PidTagLastVerbExecuted",
        "10820040": "PidTagLastVerbExecutionTime",
        "10900003": "PidTagFlagStatus",
        "10910040": "PidTagFlagCompleteTime",
        "10950003": "PidTagFollowupIcon",
        "10960003": "PidTagBlockStatus",
        "10C30040": "PidTagICalendarStartTime",
        "10C40040": "PidTagICalendarEndTime",
        "10C50040": "PidTagCdoRecurrenceid",
        "10CA0040": "PidTagICalendarReminderNextTime",
        "10F4000B": "PidTagAttributeHidden",
        "10F6000B": "PidTagAttributeReadOnly",
        "1102": "PidNameRightsManagementLicense",
        "30000003": "PidTagRowid",
        "3001001F": "PidTagDisplayName",
        "3002001F": "PidTagAddressType",
        "3003001F": "PidTagEmailAddress",
        "3004001F": "PidTagComment",
        "30050003": "PidTagDepth",
        "30070040": "PidTagCreationTime",
        "30080040": "PidTagLastModificationTime",
        "300B0102": "PidTagSearchKey",
        "30100102": "PidTagTargetEntryId",
        "30130102": "PidTagConversationId",
        "3016000B": "PidTagConversationIndexTracking",
        "30180102": "PidTagArchiveTag",
        "30190102": "PidTagPolicyTag",
        "301A0003": "PidTagRetentionPeriod",
        "301B0102": "PidTagStartDateEtc",
        "301C0040": "PidTagRetentionDate",
        "301D0003": "PidTagRetentionFlags",
        "301E0003": "PidTagArchivePeriod",
        "301F0040": "PidTagArchiveDate",
        "340D0003": "PidTagStoreSupportMask",
        "340E0003": "PidTagStoreState",
        "36000003": "PidTagContainerFlags",
        "36010003": "PidTagFolderType",
        "36020003": "PidTagContentCount",
        "36030003": "PidTagContentUnreadCount",
        "3609000B": "PidTagSelectable",
        "360A000B": "PidTagSubfolders",
        "360C001F": "PidTagAnr",
        "360E000D": "PidTagContainerHierarchy",
        "360F000D": "PidTagContainerContents",
        "3610000D": "PidTagFolderAssociatedContents",
        "3613001F": "PidTagContainerClass",
        "36D00102": "PidTagIpmAppointmentEntryId",
        "36D10102": "PidTagIpmContactEntryId",
        "36D20102": "PidTagIpmJournalEntryId",
        "36D30102": "PidTagIpmNoteEntryId",
        "36D40102": "PidTagIpmTaskEntryId",
        "36D50102": "PidTagRemindersOnlineEntryId",
        "36D70102": "PidTagIpmDraftsEntryId",
        "36D81102": "PidTagAdditionalRenEntryIds",
        "36D90102": "PidTagAdditionalRenEntryIdsEx",
        "36DA0102": "PidTagExtendedFolderFlags",
        "36E20003": "PidTagOrdinalMost",
        "36E41102": "PidTagFreeBusyEntryIds",
        "36E5001F": "PidTagDefaultPostMessageClass",
        "3701000D": "PidTagAttachDataObject",
        "37010102": "PidTagAttachDataBinary",
        "37020102": "PidTagAttachEncoding",
        "3703001F": "PidTagAttachExtension",
        "3704001F": "PidTagAttachFilename",
        "37050003": "PidTagAttachMethod",
        "3707001F": "PidTagAttachLongFilename",
        "3708001F": "PidTagAttachPathname",
        "37090102": "PidTagAttachRendering",
        "370A0102": "PidTagAttachTag",
        "370B0003": "PidTagRenderingPosition",
        "370C001F": "PidTagAttachTransportName",
        "370D001F": "PidTagAttachLongPathname",
        "370E001F": "PidTagAttachMimeTag",
        "370F0102": "PidTagAttachAdditionalInformation",
        "3711001F": "PidTagAttachContentBase",
        "3712001F": "PidTagAttachContentId",
        "3713001F": "PidTagAttachContentLocation",
        "37140003": "PidTagAttachFlags",
        "3719001F": "PidTagAttachPayloadProviderGuidString",
        "371A001F": "PidTagAttachPayloadClass",
        "371B001F": "PidTagTextAttachmentCharset",
        "39000003": "PidTagDisplayType",
        "39020102": "PidTagTemplateid",
        "39050003": "PidTagDisplayTypeEx",
        "39FE001F": "PidTagSmtpAddress",
        "39FF001F": "PidTagAddressBookDisplayNamePrintable",
        "3A00001F": "PidTagAccount",
        "3A02001F": "PidTagCallbackTelephoneNumber",
        "3A05001F": "PidTagGeneration",
        "3A06001F": "PidTagGivenName",
        "3A07001F": "PidTagGovernmentIdNumber",
        "3A08001F": "PidTagBusinessTelephoneNumber",
        "3A09001F": "PidTagHomeTelephoneNumber",
        "3A0A001F": "PidTagInitials",
        "3A0B001F": "PidTagKeyword",
        "3A0C001F": "PidTagLanguage",
        "3A0D001F": "PidTagLocation",
        "3A0F001F": "PidTagMessageHandlingSystemCommonName",
        "3A10001F": "PidTagOrganizationalIdNumber",
        "3A11001F": "PidTagSurname",
        "3A120102": "PidTagOriginalEntryId",
        "3A15001F": "PidTagPostalAddress",
        "3A16001F": "PidTagCompanyName",
        "3A17001F": "PidTagTitle",
        "3A18001F": "PidTagDepartmentName",
        "3A19001F": "PidTagOfficeLocation",
        "3A1A001F": "PidTagPrimaryTelephoneNumber",
        "3A1B001F": "PidTagBusiness2TelephoneNumber",
        "3A1B101F": "PidTagBusiness2TelephoneNumbers",
        "3A1C001F": "PidTagMobileTelephoneNumber",
        "3A1D001F": "PidTagRadioTelephoneNumber",
        "3A1E001F": "PidTagCarTelephoneNumber",
        "3A1F001F": "PidTagOtherTelephoneNumber",
        "3A20001F": "PidTagTransmittableDisplayName",
        "3A21001F": "PidTagPagerTelephoneNumber",
        "3A220102": "PidTagUserCertificate",
        "3A23001F": "PidTagPrimaryFaxNumber",
        "3A24001F": "PidTagBusinessFaxNumber",
        "3A25001F": "PidTagHomeFaxNumber",
        "3A26001F": "PidTagCountry",
        "3A27001F": "PidTagLocality",
        "3A28001F": "PidTagStateOrProvince",
        "3A29001F": "PidTagStreetAddress",
        "3A2A001F": "PidTagPostalCode",
        "3A2B001F": "PidTagPostOfficeBox",
        "3A2C1102": "PidTagTelexNumber",
        "3A2D001F": "PidTagIsdnNumber",
        "3A2E001F": "PidTagAssistantTelephoneNumber",
        "3A2F001F": "PidTagHome2TelephoneNumber",
        "3A2F101F": "PidTagHome2TelephoneNumbers",
        "3A30001F": "PidTagAssistant",
        "3A40000B": "PidTagSendRichInfo",
        "3A410040": "PidTagWeddingAnniversary",
        "3A420040": "PidTagBirthday",
        "3A43001F": "PidTagHobbies",
        "3A44001F": "PidTagMiddleName",
        "3A45001F": "PidTagDisplayNamePrefix",
        "3A46001F": "PidTagProfession",
        "3A47001F": "PidTagReferredByName",
        "3A48001F": "PidTagSpouseName",
        "3A49001F": "PidTagComputerNetworkName",
        "3A4A001F": "PidTagCustomerId",
        "3A4B001F": "PidTagTelecommunicationsDeviceForDeafTelephoneNumber",
        "3A4C001F": "PidTagFtpSite",
        "3A4D0002": "PidTagGender",
        "3A4E001F": "PidTagManagerName",
        "3A4F001F": "PidTagNickname",
        "3A50001F": "PidTagPersonalHomePage",
        "3A51001F": "PidTagBusinessHomePage",
        "3A57001F": "PidTagCompanyMainTelephoneNumber",
        "3A58101F": "PidTagChildrensNames",
        "3A59001F": "PidTagHomeAddressCity",
        "3A5A001F": "PidTagHomeAddressCountry",
        "3A5B001F": "PidTagHomeAddressPostalCode",
        "3A5C001F": "PidTagHomeAddressStateOrProvince",
        "3A5D001F": "PidTagHomeAddressStreet",
        "3A5E001F": "PidTagHomeAddressPostOfficeBox",
        "3A5F001F": "PidTagOtherAddressCity",
        "3A60001F": "PidTagOtherAddressCountry",
        "3A61001F": "PidTagOtherAddressPostalCode",
        "3A62001F": "PidTagOtherAddressStateOrProvince",
        "3A63001F": "PidTagOtherAddressStreet",
        "3A64001F": "PidTagOtherAddressPostOfficeBox",
        "3A701102": "PidTagUserX509Certificate",
        "3A710003": "PidTagSendInternetEncoding",
        "3F080003": "PidTagInitialDetailsPane",
        "3FDE0003": "PidTagInternetCodepage",
        "3FDF0003": "PidTagAutoResponseSuppress",
        "3FE00102": "PidTagAccessControlListData",
        "3FE3000B": "PidTagDelegatedByRule",
        "3FE70003": "PidTagResolveMethod",
        "3FEA000B": "PidTagHasDeferredActionMessages",
        "3FEB0003": "PidTagDeferredSendNumber",
        "3FEC0003": "PidTagDeferredSendUnits",
        "3FED0003": "PidTagExpiryNumber",
        "3FEE0003": "PidTagExpiryUnits",
        "3FEF0040": "PidTagDeferredSendTime",
        "3FF00102": "PidTagConflictEntryId",
        "3FF10003": "PidTagMessageLocaleId",
        "3FF8001F": "PidTagCreatorName",
        "3FF90102": "PidTagCreatorEntryId",
        "3FFA001F": "PidTagLastModifierName",
        "3FFB0102": "PidTagLastModifierEntryId",
        "3FFD0003": "PidTagMessageCodepage",
        "401A0003": "PidTagSentRepresentingFlags",
        "4029001F": "PidTagReadReceiptAddressType",
        "402A001F": "PidTagReadReceiptEmailAddress",
        "402B001F": "PidTagReadReceiptName",
        "40760003": "PidTagContentFilterSpamConfidenceLevel",
        "40790003": "PidTagSenderIdStatus",
        "40820040": "PidTagHierRev",
        "4083001F": "PidTagPurportedSenderDomain",
        "59020003": "PidTagInternetMailOverrideFormat",
        "59090003": "PidTagMessageEditorFormat",
        "5D01001F": "PidTagSenderSmtpAddress",
        "5D02001F": "PidTagSentRepresentingSmtpAddress",
        "5D05001F": "PidTagReadReceiptSmtpAddress",
        "5D07001F": "PidTagReceivedBySmtpAddress",
        "5D08001F": "PidTagReceivedRepresentingSmtpAddress",
        "5FDF0003": "PidTagRecipientOrder",
        "5FE1000B": "PidTagRecipientProposed",
        "5FE30040": "PidTagRecipientProposedStartTime",
        "5FE40040": "PidTagRecipientProposedEndTime",
        "5FF6001F": "PidTagRecipientDisplayName",
        "5FF70102": "PidTagRecipientEntryId",
        "5FFB0040": "PidTagRecipientTrackStatusTime",
        "5FFD0003": "PidTagRecipientFlags",
        "5FFF0003": "PidTagRecipientTrackStatus",
        "61000003": "PidTagJunkIncludeContacts",
        "61010003": "PidTagJunkThreshold",
        "61020003": "PidTagJunkPermanentlyDelete",
        "61030003": "PidTagJunkAddRecipientsToSafeSendersList",
        "6107000B": "PidTagJunkPhishingEnableLinks",
        "64F00102": "PidTagMimeSkeleton",
        "65C20102": "PidTagReplyTemplateId",
        "65E00102": "PidTagSourceKey",
        "65E10102": "PidTagParentSourceKey",
        "65E20102": "PidTagChangeKey",
        "65E30102": "PidTagPredecessorChangeList",
        "65E90003": "PidTagRuleMessageState",
        "65EA0003": "PidTagRuleMessageUserFlags",
        "65EB001F": "PidTagRuleMessageProvider",
        "65EC001F": "PidTagRuleMessageName",
        "65ED0003": "PidTagRuleMessageLevel",
        "65EE0102": "PidTagRuleMessageProviderData",
        "65F30003": "PidTagRuleMessageSequence",
        "66190102": "PidTagUserEntryId",
        "661B0102": "PidTagMailboxOwnerEntryId",
        "661C001F": "PidTagMailboxOwnerName",
        "661D000B": "PidTagOutOfOfficeState",
        "66220102": "PidTagSchedulePlusFreeBusyEntryId",
        "66390003": "PidTagRights",
        "663A000B": "PidTagHasRules",
        "663B0102": "PidTagAddressBookEntryId",
        "663E0003": "PidTagHierarchyChangeNumber",
        "66450102": "PidTagClientActions",
        "66460102": "PidTagDamOriginalEntryId",
        "6647000B": "PidTagDamBackPatched",
        "66480003": "PidTagRuleError",
        "66490003": "PidTagRuleActionType",
        "664A000B": "PidTagHasNamedProperties",
        "66500003": "PidTagRuleActionNumber",
        "66510102": "PidTagRuleFolderEntryId",
        "666A0003": "PidTagProhibitReceiveQuota",
        "666C000B": "PidTagInConflict",
        "666D0003": "PidTagMaximumSubmitMessageSize",
        "666E0003": "PidTagProhibitSendQuota",
        "66710014": "PidTagMemberId",
        "6672001F": "PidTagMemberName",
        "66730003": "PidTagMemberRights",
        "66740014": "PidTagRuleId",
        "66750102": "PidTagRuleIds",
        "66760003": "PidTagRuleSequence",
        "66770003": "PidTagRuleState",
        "66780003": "PidTagRuleUserFlags",
        "667900FD": "PidTagRuleCondition",
        "668000FE": "PidTagRuleActions",
        "6681001F": "PidTagRuleProvider",
        "6682001F": "PidTagRuleName",
        "66830003": "PidTagRuleLevel",
        "66840102": "PidTagRuleProviderData",
        "668F0040": "PidTagDeletedOn",
        "66A10003": "PidTagLocaleId",
        "66A80003": "PidTagFolderFlags",
        "66C30003": "PidTagCodePageId",
        "6704000D": "PidTagAddressBookManageDistributionList",
        "67050003": "PidTagSortLocaleId",
        "67090040": "PidTagLocalCommitTime",
        "670A0040": "PidTagLocalCommitTimeMax",
        "670B0003": "PidTagDeletedCountTotal",
        "670E001F": "PidTagFlatUrlName",
        "674000FB": "PidTagSentMailSvrEID",
        "674100FB": "PidTagDeferredActionMessageOriginalEntryId",
        "67480014": "PidTagFolderId",
        "67490014": "PidTagParentFolderId",
        "674A0014": "PidTagMid",
        "674D0014": "PidTagInstID",
        "674E0003": "PidTagInstanceNum",
        "674F0014": "PidTagAddressBookMessageId",
        "67A40014": "PidTagChangeNumber",
        "67AA000B": "PidTagAssociated",
        "6800001F": "PidTagOfflineAddressBookName",
        "68010003": "PidTagVoiceMessageDuration",
        "6802001E": "PidTagOfflineAddressBookContainerGuid",
        "6802001F": "PidTagSenderTelephoneNumber",
        "68020102": "PidTagRwRulesStream",
        "68030003": "PidTagOfflineAddressBookMessageClass",
        "6803001F": "PidTagVoiceMessageSenderName",
        "68040003": "PidTagFaxNumberOfPages",
        "6804001E": "PidTagOfflineAddressBookDistinguishedName",
        "6805001F": "PidTagVoiceMessageAttachmentOrder",
        "68051003": "PidTagOfflineAddressBookTruncatedProperties",
        "6806001F": "PidTagCallId",
        "6820001F": "PidTagReportingMessageTransferAgent",
        "68340003": "PidTagSearchFolderLastUsed",
        "683A0003": "PidTagSearchFolderExpiration",
        "68410003": "PidTagSearchFolderTemplateId",
        "6842000B": "PidTagScheduleInfoDelegatorWantsCopy",
        "68420102": "PidTagWlinkGroupHeaderID",
        "6843000B": "PidTagScheduleInfoDontMailDelegates",
        "68440102": "PidTagSearchFolderRecreateInfo",
        "6844101F": "PidTagScheduleInfoDelegateNames",
        "68450102": "PidTagSearchFolderDefinition",
        "68451102": "PidTagScheduleInfoDelegateEntryIds",
        "68460003": "PidTagSearchFolderStorageType",
        "6846000B": "PidTagGatewayNeedsToRefresh",
        "68470003": "PidTagWlinkSaveStamp",
        "68480003": "PidTagSearchFolderEfpFlags",
        "68490003": "PidTagWlinkType",
        "6849001F": "PidTagFreeBusyMessageEmailAddress",
        "684A0003": "PidTagWlinkFlags",
        "684A101F": "PidTagScheduleInfoDelegateNamesW",
        "684B000B": "PidTagScheduleInfoDelegatorWantsInfo",
        "684B0102": "PidTagWlinkOrdinal",
        "684C0102": "PidTagWlinkEntryId",
        "684D0102": "PidTagWlinkRecordKey",
        "684E0102": "PidTagWlinkStoreEntryId",
        "684F0102": "PidTagWlinkFolderType",
        "684F1003": "PidTagScheduleInfoMonthsMerged",
        "68500102": "PidTagWlinkGroupClsid",
        "68501102": "PidTagScheduleInfoFreeBusyMerged",
        "6851001F": "PidTagWlinkGroupName",
        "68511003": "PidTagScheduleInfoMonthsTentative",
        "68520003": "PidTagWlinkSection",
        "68521102": "PidTagScheduleInfoFreeBusyTentative",
        "68530003": "PidTagWlinkCalendarColor",
        "68531003": "PidTagScheduleInfoMonthsBusy",
        "68540102": "PidTagWlinkAddressBookEID",
        "68541102": "PidTagScheduleInfoFreeBusyBusy",
        "68551003": "PidTagScheduleInfoMonthsAway",
        "68561102": "PidTagScheduleInfoFreeBusyAway",
        "68680040": "PidTagFreeBusyRangeTimestamp",
        "68690003": "PidTagFreeBusyCountMonths",
        "686A0102": "PidTagScheduleInfoAppointmentTombstone",
        "686B1003": "PidTagDelegateFlags",
        "686C0102": "PidTagScheduleInfoFreeBusy",
        "686D000B": "PidTagScheduleInfoAutoAcceptAppointments",
        "686E000B": "PidTagScheduleInfoDisallowRecurringAppts",
        "686F000B": "PidTagScheduleInfoDisallowOverlappingAppts",
        "68900102": "PidTagWlinkClientID",
        "68910102": "PidTagWlinkAddressBookStoreEID",
        "68920003": "PidTagWlinkROGroupType",
        "70010102": "PidTagViewDescriptorBinary",
        "7002001F": "PidTagViewDescriptorStrings",
        "7006001F": "PidTagViewDescriptorName",
        "70070003": "PidTagViewDescriptorVersion",
        "7C060003": "PidTagRoamingDatatypes",
        "7C070102": "PidTagRoamingDictionary",
        "7C080102": "PidTagRoamingXmlStream",
        "7C24000B": "PidTagOscSyncEnabled",
        "7D01000B": "PidTagProcessed",
        "7FF90040": "PidTagExceptionReplaceTime",
        "7FFA0003": "PidTagAttachmentLinkId",
        "7FFB0040": "PidTagExceptionStartTime",
        "7FFC0040": "PidTagExceptionEndTime",
        "7FFD0003": "PidTagAttachmentFlags",
        "7FFE000B": "PidTagAttachmentHidden",
        "7FFF000B": "PidTagAttachmentContactPhoto",
        "8004001F": "PidTagAddressBookFolderPathname",
        "8005000D": "PidTagAddressBookManager",
        "8005001F": "PidTagAddressBookManagerDistinguishedName",
        "8006000D": "PidTagAddressBookHomeMessageDatabase",
        "8008000D": "PidTagAddressBookIsMemberOfDistributionList",
        "8009000D": "PidTagAddressBookMember",
        "800C000D": "PidTagAddressBookOwner",
        "800E000D": "PidTagAddressBookReports",
        "800F101F": "PidTagAddressBookProxyAddresses",
        "8011001F": "PidTagAddressBookTargetAddress",
        "8015000D": "PidTagAddressBookPublicDelegates",
        "8024000D": "PidTagAddressBookOwnerBackLink",
        "802D001F": "PidTagAddressBookExtensionAttribute1",
        "802E001F": "PidTagAddressBookExtensionAttribute2",
        "802F001F": "PidTagAddressBookExtensionAttribute3",
        "8030001F": "PidTagAddressBookExtensionAttribute4",
        "8031001F": "PidTagAddressBookExtensionAttribute5",
        "8032001F": "PidTagAddressBookExtensionAttribute6",
        "8033001F": "PidTagAddressBookExtensionAttribute7",
        "8034001F": "PidTagAddressBookExtensionAttribute8",
        "8035001F": "PidTagAddressBookExtensionAttribute9",
        "8036001F": "PidTagAddressBookExtensionAttribute10",
        "803C001F": "PidTagAddressBookObjectDistinguishedName",
        "806A0003": "PidTagAddressBookDeliveryContentLength",
        "8073000D": "PidTagAddressBookDistributionListMemberSubmitAccepted",
        "8170101F": "PidTagAddressBookNetworkAddress",
        "8C57001F": "PidTagAddressBookExtensionAttribute11",
        "8C58001F": "PidTagAddressBookExtensionAttribute12",
        "8C59001F": "PidTagAddressBookExtensionAttribute13",
        "8C60001F": "PidTagAddressBookExtensionAttribute14",
        "8C61001F": "PidTagAddressBookExtensionAttribute15",
        "8C6A1102": "PidTagAddressBookX509Certificate",
        "8C6D0102": "PidTagAddressBookObjectGuid",
        "8C8E001F": "PidTagAddressBookPhoneticGivenName",
        "8C8F001F": "PidTagAddressBookPhoneticSurname",
        "8C90001F": "PidTagAddressBookPhoneticDepartmentName",
        "8C91001F": "PidTagAddressBookPhoneticCompanyName",
        "8C92001F": "PidTagAddressBookPhoneticDisplayName",
        "8C930003": "PidTagAddressBookDisplayTypeExtended",
        "8C94000D": "PidTagAddressBookHierarchicalShowInDepartments",
        "8C96101F": "PidTagAddressBookRoomContainers",
        "8C97000D": "PidTagAddressBookHierarchicalDepartmentMembers",
        "8C98001E": "PidTagAddressBookHierarchicalRootDepartment",
        "8C99000D": "PidTagAddressBookHierarchicalParentDepartment",
        "8C9A000D": "PidTagAddressBookHierarchicalChildDepartments",
        "8C9E0102": "PidTagThumbnailPhoto",
        "8CA00003": "PidTagAddressBookSeniorityIndex",
        "8CA8001F": "PidTagAddressBookOrganizationalUnitRootDistinguishedName",
        "8CAC101F": "PidTagAddressBookSenderHintTranslations",
        "8CB5000B": "PidTagAddressBookModerationEnabled",
        "8CC20102": "PidTagSpokenName",
        "8CD8000D": "PidTagAddressBookAuthorizedSenders",
        "8CD9000D": "PidTagAddressBookUnauthorizedSenders",
        "8CDA000D": "PidTagAddressBookDistributionListMemberSubmitRejected",
        "8CDB000D": "PidTagAddressBookDistributionListRejectMessagesFromDLMembers",
        "8CDD000B": "PidTagAddressBookHierarchicalIsHierarchicalGroup",
        "8CE20003": "PidTagAddressBookDistributionListMemberCount",
        "8CE30003": "PidTagAddressBookDistributionListExternalMemberCount",
        "FFFB000B": "PidTagAddressBookIsMaster",
        "FFFC0102": "PidTagAddressBookParentEntryId",
        "FFFD0003": "PidTagAddressBookContainerId"
    }
