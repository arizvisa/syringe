import ptypes
from ptypes import pstruct,parray,pbinary,ptype,dyn,pstr,config

from ..__base__ import *
from . import headers
from .headers import virtualaddress

import logging, itertools

class IMAGE_RESOURCE_DIRECTORY(pstruct.type):
    _fields_ = [
        (dword, 'Characteristics'),
        (TimeDateStamp, 'TimeDateStamp'),
        (word, 'MajorVersion'),
        (word, 'MinorVersion'),
        (word, 'NumberOfNames'),
        (word, 'NumberOfIds'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_NAME, length=s['NumberOfNames'].li.int()), 'Names'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_ID, length=s['NumberOfIds'].li.int()), 'Ids'),
    ]

    def Iterate(self):
        return itertools.chain((n.Name() for n in self['Names']), (n.Name() for n in self['Ids']))
    def List(self):
        return list(self.Iterate())
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
        (lambda s: dyn.clone(pstr.wstring, length=s['Length'].li.int()), 'String')
    ]
    def str(self):
        return self['String'].str()

class IMAGE_RESOURCE_DATA_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda s: dyn.block(s.parent['Size'].li.int()), type=dword), 'Data'),
        (dword, 'Size'),
        (dword, 'Codepage'),
        (dword, 'Reserved'),
    ]

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA(ptype.rpointer_t):
    class RVAType(pbinary.struct):
        _fields_ = [(1, 'type'), (31, 'offset')]
        def get(self):
            return self['offset']
        def set(self, value):
            self['type'] = 0
            self['offset'] = value
            return self
    _value_ = pbinary.littleendian(RVAType)
    def _baseobject_(self):
        base = self.getparent(headers.IMAGE_DATA_DIRECTORY)['Address']
        if base.int() == 0:
            raise ValueError("No Resource Data Directory Entry")
        return base.d
    def encode(self, object, **attrs):
        raise NotImplementedError
    def summary(self, **attrs):
        return self.object.summary(**attrs)

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_NAME(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY_STRING if self.object['type'] else ptype.undefined
    def get(self):
        if self.object['type'] == 0:
            return self.object['offset']
        return self.d.li.str()
class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_DATA(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY if self.object['type'] else IMAGE_RESOURCE_DATA_ENTRY
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
class ResourceType(pint.enum):
    _values_ = [
        ('RT_CURSOR', 1),
        ('RT_FONT', 8),
        ('RT_BITMAP', 2),
        ('RT_ICON', 3),
        ('RT_MENU', 4),
        ('RT_DIALOG', 5),
        ('RT_STRING', 6),
        ('RT_FONTDIR', 7),
        ('RT_ACCELERATOR', 9),
        ('RT_RCDATA', 10),
        ('RT_MESSAGETABLE', 11),
        ('RT_GROUP_CURSOR', 12),
        ('RT_GROUP_ICON', 14),
        ('RT_VERSION', 16),
        ('RT_DLGINCLUDE', 17),
        ('RT_PLUGPLAY', 19),
        ('RT_VXD', 20),
        ('RT_ANICURSOR', 21),
        ('RT_ANIICON', 22),
        ('RT_HTML', 23),
        ('RT_MANIFEST', 24),
    ]

## resource navigation
class RT_VERSION_ValueType(ptype.definition): cache = {}
class RT_VERSION_EntryType(ptype.definition): cache = {}

class RT_VERSION(pstruct.type):
    def __Type(self):
        if callable(getattr(self, 'Type', None)):
            return self.Type()

        cls, key = self.__class__, self['szKey'].li.str()
        if cls != RT_VERSION:
            logging.warn("{:s} : Unknown type for entry {!r}. Searching for one instead.".format('.'.join((cls.__module__, cls.__name__)), key))

        sz = self['wValueLength'].li.int()
        return RT_VERSION_ValueType.withdefault(key, type=key, length=sz)

    def __ChildType(self):
        if callable(getattr(self, 'ChildType', None)):
            return self.ChildType()

        cls, key = self.__class__, self['szKey'].li.str()
        if self.__class__ != RT_VERSION:
            logging.warn("{:s} : Unknown child type for entry {!r}. Searching for one instead.".format('.'.join((cls.__module__, cls.__name__)), key))

        return RT_VERSION_EntryType.lookup(key)
        #bs = self['wLength'].li.int() - self.blocksize()
        #return RT_VERSION_EntryType.withdefault(szkey, type=szkey, length=bs)

    def __Children(self):
        fields = self._fields_[:-1]
        length, cb = self['wLength'].li.int(), sum(self[name].li.size() for _, name in fields)

        if cb > length:
            raise AssertionError("Invalid block size returned for child: {:d}".format(bs))

        ct = self.__ChildType()
        class Member(pstruct.type):
            _fields_ = [
                (dyn.align(4), 'Padding'),
                (ct, 'Child'),
            ]
        return dyn.clone(parray.block, _object_=Member, blocksize=lambda s, bs=length-cb:bs)

    _fields_ = [
        (word, 'wLength'),
        (word, 'wValueLength'),
        (word, 'wType'),
        (pstr.szwstring, 'szKey'),
        (dyn.align(4), 'Padding'),
        (__Type, 'Value'),
        (__Children, 'Children'),
    ]

@RT_VERSION_EntryType.define
class RT_VERSION_StringFileInfo(RT_VERSION):
    type = "StringFileInfo"
    def ChildType(self):
        return RT_VERSION_String

class RT_VERSION_String(RT_VERSION):
    def ChildType(self):
        return ptype.undefined
    def Type(self):
        # wValueLength = number of 16-bit words of wValue
        l = self['wValueLength'].li.int()
        return dyn.clone(pstr.wstring, length=l)

@RT_VERSION_EntryType.define
class RT_VERSION_VarFileInfo(RT_VERSION):
    type = "VarFileInfo"
    def Type(self):
        l = self['wValueLength'].li.int()
        return dyn.clone(parray.block, _object_=dword, blocksize=lambda s:l)
@RT_VERSION_EntryType.define
class RT_VERSION_Translation(ptype.undefined):
    type = "Translation"
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
    def ChildType(self):
        return RT_VERSION

if __name__ == '__main__':
    import pecoff
#    z = pecoff.Executable.open('c:/Program Files (x86)/Debugging Tools for Windows (x86)/windbg.exe', mode='r')
    z = pecoff.Executable.open('obj/windbg.exe')

    a = z['DataDirectory'][2]['Address'].d.l
    b = a['Ids'][0]
    print b['Name']
    print b['Entry']

#    from pecoff.resources import DataDirectory

#    print DataDirectory(b['RVA']['address'])
