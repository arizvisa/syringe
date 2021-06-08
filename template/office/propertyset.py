# [MS-OLEPS].pdf
import ptypes, ndk
from ptypes import *
from ndk.datatypes import *

class GUID(ndk.GUID):
    pass

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

class CURRENCY(INT64): pass
class CodePageString(pstruct.type):
    def __Characters(self):
        expected = self['Size'].li
        return dyn.clone(pstr.string, length=expected.int())
    _fields_ = [
        (DWORD, 'Size'),
        (__Characters, 'Characters'),
        (dyn.padding(4), 'padding(Characters)'),
    ]
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
class FILETIME(ndk.FILETIME): pass
class BLOB(pstruct.type):
    _fields_ = [
        (DWORD, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Bytes'),
    ]
class IndirectPropertyName(CodePageString): pass
class ClipboardData(pstruct.type):
    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'Format'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Data'),
        (dyn.padding(4), 'padding(Data)'),
    ]
class VersionedStream(pstruct.type):
    _fields_ = [
        (GUID, 'VersionGuid'),
        (CodePageString, 'StreamName'), # XXX: not sure whether this is right
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
        type = TypedProperty.lookup(property['VariantType'])
        header = property.item('HeaderType')
        if header['VT_ARRAY']:
            return dyn.clone(TypedPropertyArray, _object_=type)
        elif header['VT_VECTOR']:
            return dyn.clone(TypedPropertyVector, _object_=type)
        return type

    _fields_ = [
        (PropertyType, 'Type'),
        (WORD, 'Padding'),
        (__Value, 'Value'),
    ]

############
class _PROPERTY_IDENTIFIER(pint.enum):
    _values_ = [
        ('DICTIONARY', 0x00000000),
        ('CODEPAGE', 0x00000001),
        ('LOCALE', 0x80000000),
        ('BEHAVIOR', 0x80000001),
    ]

class PropertyIdentifier(_PROPERTY_IDENTIFIER, DWORD):
    pass

class DictionaryEntry(pstruct.type):
    def __Name(self):
        length = self['Length'].li
        raise NotImplementedError

        # FIXME: we need to check the propertyset for the codepage in
        #        order to distinguish whether this is unicode or not.
        return dyn.clone(pstr.string, length=length.int())
        return dyn.clone(pstr.wstring, length=length.int())

    _fields_ = [
        (PropertyIdentifier, 'PropertyIdentifier'),
        (DWORD, 'Length'),
        (lambda self: dyn.block(self['Length'].li.int()), 'Name'),
    ]

class Dictionary(pstruct.type):
    _fields_ = [
        (DWORD, 'NumEntries'),
        (lambda self: dyn.array(DictionaryEntry, self['NumEntries'].li.int()), 'Entry'),
        (dyn.padding(4), 'Padding'),
    ]

class PropertyIdentifierAndOffset(pstruct.type):
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
        (PropertyIdentifier, 'PropertyIdentifier'),
        (DWORD, 'Offset'),
    ]

class PropertySet(pstruct.type):
    def __Property(self):
        res, fields = self['Size'].li.int(), ['Size', 'NumProperties', 'PropertyIdentifierAndOffset']
        return dyn.block(max(0, res - sum(self[fld].li.size() for fld in fields)))

    _fields_ = [
        (DWORD, 'Size'),
        (DWORD, 'NumProperties'),
        (lambda self: dyn.array(PropertyIdentifierAndOffset, self['NumProperties'].li.int()), 'PropertyIdentifierAndOffset'),
        #(lambda self: dyn.array(Property, self['NumProperties'].li.int()), 'Property'),
        (__Property, 'Property'),
    ]

class PropertySetStream(pstruct.type):
    class FMTOFFSET(pstruct.type):
        def __Offset(self):
            raise NotImplementedError
            # FIXME: this should be an rpointer(PropertySet, DWORD)

        _fields_ = [
            (GUID, 'FMTID'),
            (DWORD, 'Offset')
        ]

    _fields_ = [
        (WORD, 'ByteOrder'),
        (WORD, 'Version'),
        (DWORD, 'SystemIdentifier'),
        (GUID, 'CLSID'),
        (DWORD, 'NumPropertySets'),
        (lambda self: dyn.array(FMTOFFSET, self['NumPropertySets'].li.int()), 'FormatOffset'),

        # XXX: this might not be correct and are likely dependent on the offset
        #      specified by the FormatOffset array.
        (lambda self: dyn.array(PropertySet, self['NumPropertySets'].li.int()), 'PropertySet'),
        (ptype.block, 'Padding'),
    ]

if __name__ == '__main__':
    import builtins, operator, os, math, functools, itertools, sys, types
    def FhexToData(representation):
        rows = map(operator.methodcaller('strip'), representation.split('\n'))
        items = [item for offset, item in map(operator.methodcaller('split', ' ', 1), filter(None, rows))]
        return bytes().join(map(bytes.fromhex, items))

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
