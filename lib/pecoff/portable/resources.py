import ptypes
from ptypes import pstruct,parray,pbinary,ptype,dyn,pstr,config

from ..__base__ import *
from . import headers
from .headers import virtualaddress

import itertools

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
    iterate = Iterate
    def List(self):
        return list(self.Iterate())
    list = List

    def Entry(self, name):
        iterable = (n['Entry'].d for n in itertools.chain(iter(self['Names']), iter(self['Ids'])) if name == n.Name())
        return next(iterable, None)
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

## specific resources
if True:
    import ptypes.ptype as ptype
    class VersionValue(ptype.definition): cache = {}
    class VersionEntry(ptype.definition): cache = {}

    class Entry(pstruct.type):
        def Value(self):
            szkey = self['szKey'].li.str()
            sz = self['wValueLength'].li.int()
            return VersionValue.get(szkey, type=szkey, length=sz)

        def Child(self):
            szkey = self['szKey'].li.str()
            return VersionEntry.lookup(szkey)
            #bs = self['wLength'].li.int() - self.blocksize()
            #return VersionEntry.get(szkey, type=szkey, length=bs)

        def __Children(self):
            bs = self['wLength'].li.int() - sum(self[n].li.size() for _, n in self._fields_[:-1])
            assert bs >= 0, bs
            class Member(pstruct.type):
                _fields_ = [
                    (dyn.align(4), 'Padding'),
                    (self.Child(), 'Child'),
                ]
            return dyn.clone(parray.block, _object_=Member, blocksize=lambda s, bs=bs:bs)

        _fields_ = [
            (word, 'wLength'),
            (word, 'wValueLength'),
            (word, 'wType'),
            (pstr.szwstring, 'szKey'),
            (dyn.align(4), 'Padding'),
            (lambda s: s.Value(), 'Value'),
            (__Children, 'Children'),
        ]

    @VersionEntry.define
    class StringTable(Entry):
        type = "StringFileInfo"
        def Child(self):
            return String

    class String(Entry):
        def Child(self):
            return Empty
        def Value(self):
            # wValueLength = number of 16-bit words of wValue
            l = self['wValueLength'].li.int()
            return dyn.clone(pstr.wstring, length=l)

    @VersionEntry.define
    class Var(Entry):
        type = "VarFileInfo"
        def Value(self):
            l = self['wValueLength'].li.int()
            return dyn.clone(parray.block, _object_=dword, blocksize=lambda s:l)
    @VersionEntry.define
    class Empty(ptype.undefined):
        type = "Translation"

    @VersionValue.define
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

    class VS_VERSIONINFO(Entry):
        def Child(self):
            return Entry

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
