import logging,itertools,ptypes
from ptypes import pstruct,parray,pbinary,ptype,dyn,pstr,config
from ..headers import *

from . import headers

class IMAGE_RESOURCE_DIRECTORY(pstruct.type):
    _fields_ = [
        (dword, 'Characteristics'),
        (TimeDateStamp, 'TimeDateStamp'),
        (word, 'MajorVersion'),
        (word, 'MinorVersion'),
        (word, 'NumberOfNamedEntries'),
        (word, 'NumberOfIdEntries'),
        (lambda self: dyn.clone(IMAGE_RESOURCE_DIRECTORY_NAME, length=self['NumberOfNamedEntries'].li.int()), 'Names'),
        (lambda self: dyn.clone(IMAGE_RESOURCE_DIRECTORY_ID, length=self['NumberOfIdEntries'].li.int()), 'Ids'),
    ]

    def iterate(self):
        names = (item.Name() for item in self['Names'])
        identifiers = (item.Name() for item in self['Ids'])
        return itertools.chain(names, identifiers)
    def list(self):
        return [item for item in self.iterate()]
    def entry(self, name):
        iterable = (item['Entry'].d for item in itertools.chain(iter(self['Names']), iter(self['Ids'])) if name == item.Name())
        return next(iterable, None)

    # aliases
    Iterate = iterate
    List = list
    Entry = entry

class IMAGE_RESOURCE_DIRECTORY_STRING(pstruct.type):
    _fields_ = [
        (word, 'Length'),
        (lambda self: dyn.clone(pstr.string, length=self['Length'].li.int()), 'String')
    ]
    def str(self):
        return self['String'].str()

class IMAGE_RESOURCE_DIRECTORY_STRING_U(pstruct.type):
    _fields_ = [
        (word, 'Length'),
        (lambda self: dyn.clone(pstr.wstring, length=self['Length'].li.int()), 'String'),
    ]
    def str(self):
        return self['String'].str()

class IMAGE_RESOURCE_DATA_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda self: dyn.block(self.parent['Size'].li.int()), type=dword), 'OffsetToData'),
        (dword, 'Size'),
        (dword, 'CodePage'),
        (dword, 'Reserved'),
    ]

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA(ptype.rpointer_t):
    def _baseobject_(self):
        base = self.getparent(headers.IMAGE_DATA_DIRECTORY)['Address']
        if base.int() == 0:
            raise ValueError('No Resource Data Directory Entry')
        return base.d
    def encode(self, object, **attrs):
        raise NotImplementedError
    def summary(self, **attrs):
        return self.object.summary(**attrs)

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_NAME(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    class RVAType(pbinary.struct):
        _fields_ = [(1, 'NameIsString'), (31, 'NameOffset')]
        def get(self):
            return self['NameOffset']
        def set(self, value):
            self['NameIsString'] = 0
            self['NameOffset'] = value
            return self
    _value_ = pbinary.littleendian(RVAType)

    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY_STRING_U if self.object['NameIsString'] else ptype.undefined

    def get(self):
        if self.object['NameIsString'] == 0:
            return self.object['NameOffset']
        return self.d.li.str()

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_DATA(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    class RVAType(pbinary.struct):
        _fields_ = [(1, 'DataIsDirectory'), (31, 'OffsetToDirectory')]
        def get(self):
            return self['OffsetToDirectory']
        def set(self, value):
            self['DataIsDirectory'] = 0
            self['OffsetToDirecotry'] = value
            return self
    _value_ = pbinary.littleendian(RVAType)

    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY if self.object['DataIsDirectory'] else IMAGE_RESOURCE_DATA_ENTRY

class IMAGE_RESOURCE_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_NAME, 'Name'),
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_DATA, 'Entry'),
    ]

    def Name(self):
        return self['Name'].get()
    def Entry(self):
        return self['Entry'].d.li

class IMAGE_RESOURCE_DIRECTORY_NAME(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY
class IMAGE_RESOURCE_DIRECTORY_ID(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY

## Resource types
class RT_(pint.enum):
    _values_ = [
        ('CURSOR', 1),
        ('BITMAP', 2),
        ('ICON', 3),
        ('MENU', 4),
        ('DIALOG', 5),
        ('STRING', 6),
        ('FONTDIR', 7),
        ('FONT', 8),
        ('ACCELERATOR', 9),
        ('RCDATA', 10),
        ('MESSAGETABLE', 11),
        ('GROUP_CURSOR', 12),
        ('GROUP_ICON', 14),
        ('VERSION', 16),
        ('DLGINCLUDE', 17),
        ('PLUGPLAY', 19),
        ('VXD', 20),
        ('ANICURSOR', 21),
        ('ANIICON', 22),
        ('HTML', 23),
        ('MANIFEST', 24),
    ]

## resource navigation
class RT_VERSION_ValueType(ptype.definition): cache = {}
class RT_VERSION_EntryType(ptype.definition): cache = {}

class RT_VERSION(pstruct.type):
    class _wType(pint.enum, word):
        _values_ = [
            ('Binary', 0),
            ('Text', 1),
        ]
    def __Value(self):
        length, fields = self['wValueLength'].li.int(), ['wLength', 'wValueLength', 'wType', 'szKey', 'Padding1']
        attribute = getattr(self, 'ValueType') if hasattr(self, 'ValueType') else None
        if callable(attribute):
            return self.ValueType(length, self['wLength'].li.int() - sum(self[fld].li.size() for fld in fields))

        cls, key = self.__class__, self['szKey'].li.str()
        if cls is not RT_VERSION:
            logging.debug("{:s} : No type callback implemented for Value in {!r}. Searching for one instead.".format('.'.join([cls.__module__, cls.__name__]), key))
        return RT_VERSION_ValueType.withdefault(key, type=key, length=length)

    def __Children(self):
        fields = ['Padding2', 'wLength', 'wValueLength', 'wType', 'szKey', 'Padding1', 'Value']
        length, cb = self['Padding2'].li.size() + self['wLength'].li.int(), sum(self[fld].li.size() for fld in fields)
        size = max(0, length - cb)

        # If our class implements a .Children() method, then use that to determine the type.
        attribute = getattr(self, 'Children') if hasattr(self, 'Children') else None
        if callable(attribute):
            return self.Children(size)

        # Otherwise, use the key to lookup the type in our definition.
        cls, key = self.__class__, self['szKey'].li.str()
        if cls is not RT_VERSION:
            logging.debug("{:s} : No type callback implemented for Children in {!r}. Searching for one instead.".format('.'.join([cls.__module__, cls.__name__]), key))

        # And then use that type to build the array of children, but rounded to a multiple of 4.
        res = RT_VERSION_EntryType.lookup(key)
        return dyn.blockarray(res, size)

    def __Unknown(self):
        res, fields = self['wLength'].li.int(), ['Padding2', 'wLength', 'wValueLength', 'wType', 'szKey', 'Padding1', 'Value', 'Children']
        cb = sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, res - cb))

    _fields_ = [
        (dyn.align(4), 'Padding2'),     # XXX: this field should be before Children, but can consolidate all of the definitions if you put it here.
        (word, 'wLength'),
        (word, 'wValueLength'),
        (_wType, 'wType'),
        (pstr.szwstring, 'szKey'),
        (dyn.align(4), 'Padding1'),
        (__Value, 'Value'),
        (__Children, 'Children'),
        (__Unknown, 'Unknown'),
    ]

@RT_VERSION_EntryType.define
class RT_VERSION_StringFileInfo(RT_VERSION):
    type = 'StringFileInfo'
    class StringFileInfo(parray.terminated):
        expected = 0
        def _object_(self):
            return RT_VERSION_String
        def isTerminator(self, item):
            aligned = (self.size() + 3) & ~3
            return False if aligned < self.expected else True

    def Children(self, size):
        return dyn.clone(self.StringFileInfo, expected=size)

class RT_VERSION_String(RT_VERSION):
    def Children(self, length):
        return dyn.clone(pstr.wstring, length=length // 2)

    def ValueType(self, length, maximum):
        # wValueLength = number of 16-bit words of wValue (sometimes)
        if 2 * length <= maximum:
            return dyn.clone(pstr.wstring, length=length)

        # some VS_VERSIONINFO actually fuck this up and don't follow the documentation
        elif length == maximum:
            return dyn.clone(pstr.wstring, length=length // 2)

        # if we hit this case, then we do not understand what's going on and just clamp
        # our size to whatever the maximum is.
        cls = self.__class__
        logging.warning("{:s} : StringFileInfo child for {:s} had a wValueLength ({:d}) that wasn't even close to what was expected ({:d}).".format('.'.join([cls.__module__, cls.__name__]), self.instance(), length, maximum))
        return dyn.clone(pstr.wstring, length=maximum // 2)

@RT_VERSION_EntryType.define
class RT_VERSION_VarFileInfo(RT_VERSION):
    type = 'VarFileInfo'
    def ValueType(self, length, maximum):
        return dyn.blockarray(dword, length)

@RT_VERSION_EntryType.define
class RT_VERSION_Translation(ptype.block):
    type = 'Translation'

@pbinary.littleendian
class VS_FF_(pbinary.flags):
    _fields_ = [
        (26, 'Unused'),
        (1, 'SPECIALBUILD'),
        (1, 'INFOINFERRED'),
        (1, 'PRIVATEBUILD'),
        (1, 'PATCHED'),
        (1, 'PRERELEASE'),
        (1, 'DEBUG'),
    ]

class VOS_(pbinary.enum):
    length, _values_ = 16, [
        ('UNKNOWN', 0),
        ('DOS', 1),
        ('OS216', 2),
        ('OS232', 3),
        ('NT', 4),
        ('WINCE', 5),
    ]

class VOS__(pbinary.enum):
    length, _values_ = 16, [
        ('BASE', 0),
        ('WINDOWS16', 1),
        ('PM16', 2),
        ('PM32', 3),
        ('WINDOWS32', 4),
    ]

class VFT_(pint.enum, dword):
    _values_ = [
        ('UNKNOWN', 0),
        ('APP', 1),
        ('DLL', 2),
        ('DRV', 3),
        ('FONT', 4),
        ('VXD', 5),
        ('STATIC_LIB', 7),
    ]

class VFT2_DRV_(pint.enum, dword):
    _values_= [
        ('UNKNOWN', 0),
        ('PRINTER', 1),
        ('KEYBOARD', 2),
        ('LANGUAGE', 3),
        ('DISPLAY', 4),
        ('MOUSE', 5),
        ('NETWORK', 6),
        ('SYSTEM', 7),
        ('INSTALLABLE', 8),
        ('SOUND', 9),
        ('COMM', 10),
        ('INPUTMETHOD', 11),
        ('VERSIONED_PRINTER', 12),
    ]

class VFT2_FONT_(pint.enum, dword):
    _values_ = [
        ('RASTER', 1),
        ('VECTOR', 2),
        ('TRUETYPE', 3),
    ]

class VFT2(pstruct.type):
    _fields_ = [
        (word, 'langID'),
        (word, 'charsetID')
    ]
    def int(self):
        lg, cp = (self[fld].int() for fld in ['langID', 'charsetID'])
        return lg * 0x10000 + cp
    def str(self):
        return "{:04x}{:04x}".format(*(self[fld].int() for fld in ['langID', 'charsetID']))
    def summary(self):
        return "langID={:#x} charsetID={:d}".format(self['langID'].int(), self['charsetID'].int())

@RT_VERSION_ValueType.define
class VS_FIXEDFILEINFO(pstruct.type):
    type = 'VS_VERSION_INFO'

    class _dwSignature(pint.enum, dword):
        _values_ = [
            ('VS_FFI_SIGNATURE', 0xfeef04bd),
        ]

    class _dwStrucVersion(pint.enum, dword):
        _values_ = [
            ('VS_FFI_STRUCVERSION', 0x10000),
        ]

    class _dwFileVersion(pstruct.type):
        _fields_ = [
            (dword, 'dwFileVersionMS'),
            (dword, 'dwFileVersionLS'),
        ]
        def Version(self):
            ms, ls = (self[fld].int() for fld in self.keys())
            msh = (ms & 0xffff0000) // pow(2,16)
            msl = (ms & 0x0000ffff) // pow(2,0)
            lsh = (ls & 0xffff0000) // pow(2,16)
            lsl = (ls & 0x0000ffff) // pow(2,0)
            return [msh, msl, lsh, lsl]
        def str(self):
            res = self.Version()
            return '.'.join(map("{:d}".format, res))
        def summary(self):
            description = ["{:s}={:#0{:d}x}".format(fld, self[fld].int(), 2 + 8) for fld in self.keys()]
            return "{:s} ({:s})".format(self.str(), ', '.join(description))

    class _dwProductVersion(_dwFileVersion):
        _fields_ = [
            (dword, 'dwProductVersionMS'),
            (dword, 'dwProductVersionLS'),
        ]

    @pbinary.littleendian
    class _dwFileOS(pbinary.struct):
        _fields_ = [
            (VOS__, 'Platform'),
            (VOS_, 'OS'),
        ]

    def __dwFileSubtype(self):
        res = self['dwFileType'].li
        if res['DRV']:
            return VFT2_DRV_
        elif res['FONT']:
            return VFT2_FONT_

        # The following type is used for VFT_VXD, but we fall back
        # to using it as the subtype for all of the unknown filetypes.
        return VFT2

    _fields_ = [
        (_dwSignature, 'dwSignature'),
        (_dwStrucVersion, 'dwStrucVersion'),
        (_dwFileVersion, 'dwFileVersion'),
        (_dwProductVersion, 'dwProductVersion'),
        (dword, 'dwFileFlagsMask'),
        (VS_FF_, 'dwFileFlags'),
        (_dwFileOS, 'dwFileOS'),
        (VFT_, 'dwFileType'),
        (__dwFileSubtype, 'dwFileSubtype'),
        (dword, 'dwFileDateMS'),
        (dword, 'dwFileDateLS'),
    ]

class VS_VERSIONINFO(RT_VERSION):
    def Children(self, length):
        return dyn.blockarray(RT_VERSION, length)

if __name__ == '__main__':
    import ptypes, pecoff
    #source = ptypes.provider.file('c:/Program Files (x86)/Debugging Tools for Windows (x86)/windbg.exe', mode='r')
    source = ptypes.provider.file('obj/windbg.exe')
    z = pecoff.Executable.File(source=source).l

    a = z['DataDirectory'][2]['Address'].d.l
    b = a['Ids'][0]
    print(b['Name'])
    print(b['Entry'])
