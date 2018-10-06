import ptypes,ndk.dtyp
from ndk.dtyp import CLSID,FILETIME
from ptypes import *

## string primitives
class LengthPrefixedAnsiString(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.clone(pstr.string, length=s['Length'].li.int()), 'String'),
    ]
    def str(self):
        return self['String'].li.str()

class LengthPrefixedUnicodeString(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Length'),
        (lambda s: dyn.clone(pstr.wstring, length=s['Length'].li.int()), 'String'),
    ]
    def str(self):
        return self['String'].li.str()

## PresentationObject Format
class PresentationObjectHeader(pstruct.type):
    def __ClassName(self):
        fmt = self['FormatID'].li.int()
        if fmt == 5:
            return LengthPrefixedAnsiString
        return pstr.string

    _fields_ = [
        (pint.uint32_t, 'OLEVersion'),
        (pint.uint32_t, 'FormatID'),
        (__ClassName, 'ClassName'),
    ]

class PresentationObjectType(ptype.definition):
    cache = {}

@PresentationObjectType.define(type='METAFILEPICT')
@PresentationObjectType.define(type='BITMAP')
@PresentationObjectType.define(type='DIB')
class StandardPresentationObject(pstruct.type):
    class BitmapPresentationSize(pint.uint32_t): pass
    class MetaFilePresentationSize(pint.uint32_t): pass

    def __SizeType(self):
        if self.type in ('BITMAP','DIB'):
            return self.BitmapPresentationSize
        if self.type in ('METAFILEPICT',):
            return self.MetaFilePresentationSize
        return pint.uint32_t

    _fields_ = [
        (__SizeType, 'Width'),
        (__SizeType, 'Height'),
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]

class ClipboardFormatHeader(pstruct.type): pass

@PresentationObjectType.define
class GenericPresentationObject(pstruct.type):
    type = None
    def __ClipboardObject(self):
        fmt = self['Header'].li['ClipboardFormat'].int()
        return ClipboardFormatType.withdefault(fmt, type=fmt)

    _fields_ = [
        (ClipboardFormatHeader, 'Header'),
        (__ClipboardObject, 'Object'),
    ]
PresentationObjectType.default = GenericPresentationObject

## Clipboard Format (not be set to 0)
ClipboardFormatHeader._fields_ = [
    (pint.uint32_t, 'ClipboardFormat')
]

class ClipboardFormatType(ptype.definition):
    cache = {}

@ClipboardFormatType.define
class StandardClipboardFormatPresentationObject(pstruct.type):
    type = None
    _fields_ = [
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]
ClipboardFormatType.default = StandardClipboardFormatPresentationObject

@ClipboardFormatType.define
class RegisteredClipboardFormatPresentationObject(pstruct.type):
    type = 0x00000000
    _fields_ = [
        (pint.uint32_t, 'StringFormatDataSize'),
        (lambda s: dyn.block(s['StringFormatDataSize'].li.int()), 'StringFormatData'),
        (pint.uint32_t, 'PresentationDataSize'),
        (lambda s: dyn.block(s['PresentationDataSize'].li.int()), 'PresentationData'),
    ]

## Object
class ObjectHeader(pstruct.type):
    def __ClassName(self):
        fmt = self['FormatID'].li.int()
        if fmt == 5:
            return LengthPrefixedAnsiString
        return ptype.type
    _fields_ = [
        (pint.uint32_t, 'OLEVersion'),
        (pint.uint32_t, 'FormatID'),
        (__ClassName, 'ClassName'),
        (LengthPrefixedAnsiString, 'TopicName'),
        (LengthPrefixedAnsiString, 'ItemName'),
    ]

class ObjectType(ptype.definition):
    cache = {}

@ObjectType.define
class EmbeddedObject(pstruct.type):
    type = 0x00000002
    _fields_ = [
        (pint.uint32_t, 'NativeDataSize'),
        (lambda s: dyn.block(s['NativeDataSize'].li.int()), 'NativeData'),
    ]

@ObjectType.define
class LinkedObject(pstruct.type):
    type = 0x00000001
    _fields_ = [
        (LengthPrefixedAnsiString, 'NetworkName'),
        (pint.uint32_t, 'Reserved'),
        (pint.uint32_t, 'LinkUpdateOption'),
    ]

### OLE 1.0 Format Structures
class PresentationObject(pstruct.type):
    def __PresentationObject(self):
        fmt = self['Header'].li['FormatID'].int()
        if fmt != 0:
            clsname = self['Header']['ClassName'].str()
            return PresentationObjectType.withdefault(clsname, type=clsname)
        return ptype.type

    _fields_ = [
        (PresentationObjectHeader, 'Header'),
        (__PresentationObject, 'Object'),
    ]

# Ole v1.0
class Object(pstruct.type):
    def __Object(self):
        fmtid = self['Header'].li['FormatID'].int()
        return ObjectType.withdefault(fmtid, type=fmtid)

    _fields_ = [
        (ObjectHeader, 'Header'),
        (__Object, 'Object'),
        (PresentationObject, 'Presentation'),
    ]

if __name__ == '__main__':
    pass
