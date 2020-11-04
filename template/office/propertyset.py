# [MS-OLEPS].pdf

class PropertyIdentifier(ptype.enumeration, DWORD):
    _values_ = [
        ('DICTIONARY_PROPERTY_IDENTIFIER', 0x00000000),
        ('CODEPAGE_PROPERTY_IDENTIFIER', 0x00000001),
        ('LOCALE_PROPERTY_IDENTIFIER', 0x80000000),
        ('BEHAVIOR_PROPERTY_IDENTIFIER', 0x80000001),
    ]

class PropertyType(ptype.enumeration, WORD):
    _values_ = [
        ('VT_EMPTY', 0x0000),
        ('VT_NULL', 0x0001),
        ('VT_I2', 0x0002),
        ('VT_I4', 0x0003),
        ('VT_R4', 0x0004),
        ('VT_R8', 0x0005),
        ('VT_CY', 0x0006),
        ('VT_DATE', 0x0007),
        ('VT_BSTR', 0x0008),
        ('VT_ERROR', 0x000a),
        ('VT_BOOL', 0x000b),
        ('VT_DECIMAL', 0x000e),
        ('VT_I1', 0x0010),
        ('VT_UI1', 0x0011),
        ('VT_UI2', 0x0012),
        ('VT_UI4', 0x0013),
        ('VT_I8', 0x0014),

        ('VT_UI8', 0x0015),
        ('VT_INT', 0x0016),
        ('VT_UINT', 0x0017),
        ('VT_LPSTR', 0x001e),
        ('VT_LPWSTR', 0x001f),
        ('VT_FILETIME', 0x0040),
        ('VT_BLOB', 0x0041),
        ('VT_STREAM', 0x0042),
        ('VT_STORAGE', 0x0043),
        ('VT_STREAMED_Object', 0x0044),
        ('VT_STORED_Object', 0x0045),
        ('VT_BLOB_Object', 0x0046),
        ('VT_CF', 0x0047),
        ('VT_CLSID', 0x0018),
        ('VT_VERSIONED_STREAM', 0x0049),
        ('VT_VECTOR|VT_I2', 0x1002),
        ('VT_VECTOR|VT_I4', 0x1003),
        ('VT_VECTOR|VT_R4', 0x1004),

        ('VT_VECTOR|VT_R8', 0x1005),
        ('VT_VECTOR|VT_CY', 0x1006),
        ('VT_VECTOR|VT_DATE', 0x1007),
        ('VT_VECTOR|VT_BSTR', 0x1008),
        ('VT_VECTOR|VT_ERROR', 0x100a),
        ('VT_VECTOR|VT_BOOL', 0x100b),
        ('VT_VECTOR|VT_VARIANT', 0x100c),
        ('VT_VECTOR|VT_I1', 0x1010),
        ('VT_VECTOR|VT_UI1', 0x1011),
        ('VT_VECTOR|VT_UI2', 0x1012),
        ('VT_VECTOR|VT_UI4', 0x1013),
        ('VT_VECTOR|VT_I8', 0x1014),
        ('VT_VECTOR|VT_UI8', 0x1015),
        ('VT_VECTOR|VT_LPSTR', 0x101e),
        ('VT_VECTOR|VT_LPWSTR', 0x101f),
        ('VT_VECTOR|VT_FILETIME', 0x1040),
        ('VT_VECTOR|VT_CF', 0x1047),
        ('VT_VECTOR|VT_CLSID', 0x1048),

        ('VT_ARRAY|VT_I2', 0x2002),
        ('VT_ARRAY|VT_I4', 0x2003),
        ('VT_ARRAY|VT_R4', 0x2004),
        ('VT_ARRAY|VT_R8', 0x2005),
        ('VT_ARRAY|VT_CY', 0x2006),
        ('VT_ARRAY|VT_DATE', 0x2007),
        ('VT_ARRAY|VT_BSTR', 0x2008),
        ('VT_ARRAY|VT_ERROR', 0x200a),
        ('VT_ARRAY|VT_BOOL', 0x200b),
        ('VT_ARRAY|VT_VARIANT', 0x200c),
        ('VT_ARRAY|VT_DECIMAL', 0x200e),
        ('VT_ARRAY|VT_I1', 0x2010),
        ('VT_ARRAY|VT_UI1', 0x2011),
        ('VT_ARRAY|VT_UI2', 0x2012),
        ('VT_ARRAY|VT_UI4', 0x2013),
        ('VT_ARRAY|VT_INT', 0x2016),
        ('VT_ARRAY|VT_UINT', 0x2017),
    ]

class CURRENCY(pint.int64_t): pass
class DATE(dyn.block(8)): pass

class CodePageString(pstruct.type):
    _fields_ = [
        (pint.uint32, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Characters'),
        (dyn.align(4), 'Alignment'),
    ]

class DECIMAL(pstruct.type):
    _fields_ = [
        (WORD, 'wReserved'),
        (BYTE, 'scale'),
        (BYTE, 'sign'),
        (DWORD, 'Hi32'),
        (DWORD, 'Lo64'),
    ]

class UnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint32, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Characters'),
        (dyn.align(4), 'Alignment'),
    ]

class FILETIME(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'dwLowDateTime'),
        (pint.uint32_t, 'dwHighDateTime'),
    ]

class BLOB(pstruct.type):
    _fields_ = [
        (pint.uint32, 'Size'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Bytes'),
        (dyn.align(4), 'Alignment'),
    ]

class IndirectPropertyName(CodePageString): pass

class ClipboardData(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'Format'),
        (lambda self: dyn.block(self['Size'].li.int()), 'Bytes'),
        (dyn.align(4), 'Alignment'),
    ]

class GUID(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Data1'),
        (pint.uint16_t, 'Data2'),
        (pint.uint16_t, 'Data3'),
        (dyn.block(8), 'Data4'),
    ]

class VersionedStream(pstruct.type):
    _fields_ = [
        (GUID, 'VersionGuid'),
        (IndirectPropertyName, 'StreamName'),
    ]

class VectorHeader(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Length'),
    ]

class ArrayDimension(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Size'),
        (pint.int32_t, 'IndexOffset'),
    ]
class ArrayHeader(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Type'),
        (pint.uint32_t, 'NumDimensions'),
        (lambda self: dyn.array(ArrayDimension, self['NumDimensions'].li.int()), 'Dimension'),
    ]

class TypedValue(ptype.definition):
    cache = {}

class TypedPropertyValue(pstruct.type):
    def __Value(self):
        res = self['Type'].li.int()
        return TypedValue.withdefault(res, type=res)
    _fields_ = [
        (PropertyType, 'Type'),
        (dyn.block(2), 'Padding'),
        (__Value, 'Value'),
    ]

class DictionaryEntry(pstruct.type):
    _fields_ = [
        (PropertyIdentifier, 'PropertyIdentifier'),
        (pint.uint32_t, 'Length'),
        (lamdda s: dyn.block(s['Length'].li.int()), 'Name'),
    ]

class Dictionary(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'NumEntries'),
        (lambda self: dyn.array(DictionaryEntry, self['NumEntries'].li.int()), 'Entry'),
    ]

class PropertyIdentifierAndOffset(pstruct.type):
    _fields_ = [
        (PropertyIdentifier, 'PropertyIdentifier'),
        (pint.uint32_t, 'Offset'),  # FIXME: dyn.rpointer(Property, base=PropertySet)
    ]

class PropertySet(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'NumProperties'),
        (lambda self: dyn.array(PropertyIdentifierAndOffset, self['NumProperties'].li.int()), 'PropertyIdentifierAndOffset'),
        (lambda self: dyn.array(Property, self['NumProperties'].li.int()), 'Property'),
    ]

class PropertySetStream(pstruct.type):
    class FMTOFFSET(pstruct.type):
        _fields_ = [(GUID,'FMTID'),(pint.uint32_t,'Offset')]
    _fields_ = [
        (pint.uint16_t, 'ByteOrder'),
        (pint.uint16_t, 'Version'),
        (pint.uint32_t, 'SystemIdentifier'),
        (GUID, 'CLSID'),
        (pint.uint32_t, 'NumPropertySets'),
        (lambda self: dyn.array(FMTOFFSET, self['NumPropertySets'].li.int()), 'FormatOffset'),
        (lambda self: dyn.array(PropertySet, self['NumPropertySets'].li.int()), 'PropertySet'),
    ]
