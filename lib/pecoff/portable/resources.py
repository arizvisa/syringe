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
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_NAME, length=s['NumberOfNames'].li.num()), 'Names'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_ID, length=s['NumberOfIds'].li.num()), 'Ids'),
    ]

    def iterate(self):
        return itertools.chain((x['Name'].getEntryName() for x in self['Names']), (x['Name'].getEntryName() for x in self['Ids']))
    def list(self):
        return list(self.iterate())

    def entry(self, name):
        for x in itertools.chain(iter(self['Names']),iter(self['Ids'])):
            if name == x['Name'].getEntryName():
                return x['Entry'].d
            continue
        return
    getEntry = entry

class IMAGE_RESOURCE_DIRECTORY_STRING(pstruct.type):
    _fields_ = [
        (word, 'Length'),
        (lambda s: dyn.clone(pstr.wstring,length=s['Length'].li.num()), 'String')
    ]
    def str(self):
        return self['String'].str()

class IMAGE_RESOURCE_DATA_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda s: dyn.block(s.parent['Size'].li.num()), type=dword), 'Data'),
        (dword, 'Size'),
        (dword, 'Codepage'),
        (dword, 'Reserved'),       
    ]

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA(ptype.pointer_t):
    class rva(pbinary.struct):
        _fields_ = [(1,'type'),(31,'offset')]
    _value_ = dyn.clone(pbinary.partial, _object_=rva, byteorder=config.byteorder.littleendian)
    def num(self):
        base = self.getparent(headers.DataDirectoryEntry)['Address']
        rva = base.num() + self.object['offset']
        return headers.calculateRelativeAddress(base, rva)
    def summary(self, **attrs):
        return self.object.summary(**attrs)

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_NAME(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY_STRING if self.object['type'] else ptype.undefined
    def getEntryName(self):
        if self.object['type']:
            return self.d.li.str()
        return int(self.object['offset'])
class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_DATA(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA):
    def _object_(self):
        return IMAGE_RESOURCE_DIRECTORY if self.object['type'] else IMAGE_RESOURCE_DATA_ENTRY
class IMAGE_RESOURCE_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_NAME, 'Name'),
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA_DATA, 'Entry'),
    ]

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
            sz = self['wValueLength'].li.num()
            return VersionValue.get(szkey, length=sz)

        def Child(self):
            szkey = self['szKey'].li.str()
            return VersionEntry.lookup(szkey)
            #bs = self['wLength'].li.num() - self.blocksize()
            #return VersionEntry.get(szkey, length=bs)

        def __Children(self):
            bs = self['wLength'].li.num() - self.blocksize()
            assert bs >= 0,bs
            class Member(pstruct.type):
                _fields_ = [
                    (dyn.align(4), 'Padding'),
                    (self.Child(), 'Child'),
                ]
            return dyn.clone(parray.block, _object_=Member, blocksize=lambda s:bs)

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
            l = self['wValueLength'].li.num()
            return dyn.clone(pstr.wstring, length=l)
    
    @VersionEntry.define
    class Var(Entry):
        type = "VarFileInfo"
        def Value(self):
            l = self['wValueLength'].li.num()
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
