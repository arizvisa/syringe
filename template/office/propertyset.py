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
