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

    def Iterate(self):
        return itertools.chain((n.Name() for n in self['Names']), (n.Name() for n in self['Ids']))
    def List(self):
        return [item for item in self.Iterate()]
    def Entry(self, name):
        iterable = (n['Entry'].d for n in itertools.chain(iter(self['Names']), iter(self['Ids'])) if name == n.Name())
        return next(iterable, None)

    # aliases
    iterate = Iterate
    list = List
    entry = Entry

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
        return IMAGE_RESOURCE_DIRECTORY_STRING if self.object['NameIsString'] else ptype.undefined

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
        length, attribute = self['wValueLength'].li.int(), getattr(self, 'ValueType') if hasattr(self, 'ValueType') else None
        if callable(attribute):
            return self.ValueType(length)

        cls, key = self.__class__, self['szKey'].li.str()
        if cls is not RT_VERSION:
            logging.debug("{:s} : No type callback implemented for Value in {!r}. Searching for one instead.".format('.'.join([cls.__module__, cls.__name__]), key))
        return RT_VERSION_ValueType.withdefault(key, type=key, length=length)

    def __Padding2(self):
        fields = ['wLength', 'wValueLength', 'wType', 'szKey', 'Padding1', 'Value']
        length, cb = self['wLength'].li.int(), sum(self[fld].li.size() for fld in fields)
        return dyn.align(4) if cb < length else dyn.align(0)

    def __Children(self):
        fields = ['wLength', 'wValueLength', 'wType', 'szKey', 'Padding1', 'Value', 'Padding2']
        length, cb = self['wLength'].li.int(), sum(self[fld].li.size() for fld in fields)
        if cb > length:
            raise AssertionError("Invalid block size returned by {!s} for child: {:d} > {:d}".format(self.instance(), cb, length))
        size = max(0, length - cb)

        # If our class implements a .Children() method, then use that to determine the type.
        attribute = getattr(self, 'Children') if hasattr(self, 'Children') else None
        if callable(attribute):
            return self.Children(size)

        # Otherwise, use the key to lookup the type in our definition.
        cls, key = self.__class__, self['szKey'].li.str()
        if cls is not RT_VERSION:
            logging.debug("{:s} : No type callback implemented for Children in {!r}. Searching for one instead.".format('.'.join([cls.__module__, cls.__name__]), key))

        # And then use that type to build the array of children.
        res = RT_VERSION_EntryType.lookup(key)
        return dyn.blockarray(res, size)

    def __Unknown(self):
        res, fields = self['wLength'].li.int(), ['wLength', 'wValueLength', 'wType', 'szKey', 'Padding1', 'Value', 'Padding2', 'Children']
        cb = sum(self[fld].li.size() for fld in fields)
        return dyn.block(max(0, res - cb))

    _fields_ = [
        (dyn.align(4), 'alignment'),
        (word, 'wLength'),
        (word, 'wValueLength'),
        (_wType, 'wType'),
        (pstr.szwstring, 'szKey'),
        (dyn.align(4), 'Padding1'),
        (__Value, 'Value'),
        (__Padding2, 'Padding2'),
        (__Children, 'Children'),
        (__Unknown, 'Unknown'),
    ]

@RT_VERSION_EntryType.define
class RT_VERSION_StringFileInfo(RT_VERSION):
    type = 'StringFileInfo'
    def Children(self, size):
        return dyn.blockarray(RT_VERSION_String, size)

class RT_VERSION_String(RT_VERSION):
    def Children(self, length):
        return dyn.clone(pstr.wstring, length=length // 2)
    def ValueType(self, length):
        # wValueLength = number of 16-bit words of wValue
        return dyn.clone(pstr.wstring, length=length)

@RT_VERSION_EntryType.define
class RT_VERSION_VarFileInfo(RT_VERSION):
    type = 'VarFileInfo'
    def ValueType(self, length):
        return dyn.blockarray(dword, length)

@RT_VERSION_EntryType.define
class RT_VERSION_Translation(ptype.block):
    type = 'Translation'

@RT_VERSION_ValueType.define
class VS_FIXEDFILEINFO(pstruct.type):
    type = 'VS_VERSION_INFO'
    _fields_ = [
        (dword, 'dwSignature'),
        (dword, 'dwStrucVersion'),
        (dword, 'dwFileVersionMS'),
        (dword, 'dwFileVersionLS'),
        (dword, 'dwProductVersionMS'),
        (dword, 'dwProductVersionLS'),
        (dword, 'dwFileFlagsMask'),
        (dword, 'dwFileFlags'),
        (dword, 'dwFileOS'),
        (dword, 'dwFileType'),
        (dword, 'dwFileSubtype'),
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

#    from pecoff.resources import DataDirectory

#    print(DataDirectory(b['RVA']['address']))
