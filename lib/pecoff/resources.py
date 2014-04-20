import ptypes,headers,datadirectory
from ptypes import pstruct,parray,pbinary,dyn,pstr
from __base__ import *
from headers import virtualaddress

class IMAGE_RESOURCE_DIRECTORY(pstruct.type):
    _fields_ = [
        (dword, 'Characteristics'),
        (dword, 'TimeDateStamp'),
        (word, 'MajorVersion'),
        (word, 'MinorVersion'),
        (word, 'NumberOfNames'),
        (word, 'NumberOfIds'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_TABLE_NAME, length=int(s['NumberOfNames'].l)), 'Names'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_TABLE_ID, length=int(s['NumberOfIds'].l)), 'Ids'),
    ]

class IMAGE_RESOURCE_DIRECTORY_STRING(pstruct.type):
    _fields_ = [
        (word, 'Length'),
        (lambda s: dyn.clone(pstr.wstring,length=int(s['Length'].l)), 'String')
    ]

class IMAGE_RESOURCE_DATA_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda s: dyn.block(s.parent['Size'].l.int())), 'Data RVA'),
        (dword, 'Size'),
        (dword, 'Codepage'),
        (dword, 'Reserved'),       
    ]

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA(pbinary.struct):
    _fields_ = [(1,'type'),(31,'address')]
    def deref(self):
        n = self['address']
        base = self.getparent(datadirectory.Resource)['VirtualAddress'].d
        makepointer = lambda x: dyn.rpointer(x, object=lambda s: base)
        p = makepointer(IMAGE_RESOURCE_DIRECTORY_TABLE) if self['type'] == 1 else makepointer(IMAGE_RESOURCE_DATA_ENTRY)
        return self.parent.new(p, __name__='RVA', offset=self.getoffset()).set(n).d

    d = property(fget=deref)
IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA = pbinary.littleendian(IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA)

class IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME(pstruct.type):
    _fields_ = [
        (virtualaddress(IMAGE_RESOURCE_DIRECTORY_STRING), 'Name RVA'),      # FIXME: this is a (1,31) binary structure and not a 32-bit address. dereferencing this is as a pointer without grabbing lower 31-bits is incorrect
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA, 'RVA'),
    ]
class IMAGE_RESOURCE_DIRECTORY_ENTRY_ID(pstruct.type):
    _fields_ = [
        (dword, 'IntegerID'),
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA, 'RVA'),
    ]

class IMAGE_RESOURCE_DIRECTORY_TABLE(IMAGE_RESOURCE_DIRECTORY):
    pass
class IMAGE_RESOURCE_DIRECTORY_TABLE_NAME(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME
class IMAGE_RESOURCE_DIRECTORY_TABLE_ID(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME

## specific resources
if True:
    import ptypes.ptype as ptype
    class VersionEntry(ptype.definition):
        cache = {}

    class Entry(pstruct.type):
        def __Value(self):
            bs = self['wValueLength'].l.int()
            if bs == 0:
                return pstr.szstring

            try:
                t = getattr(self,'thetype') if hasattr(self, 'thetype') else VersionEntry.lookup(self['szKey'].l.str())
                return dyn.clone(Entries, blocksize=lambda s:bs)
            except KeyError:
                pass
            return dyn.block(bs)

        _fields_ = [
            (word, 'wLength'),
            (word, 'wValueLength'),
            (word, 'wType'),
            (pstr.szwstring, 'szKey'),
            (dyn.align(4), 'Padding'),
            (__Value, 'Value'),
        ]

    class Entries(parray.block):
        _object_ = Entry

    class StringTable(Entries):
        _object_ = dyn.clone(Entry, thetype=pstr.szstring)

    @VersionEntry.define
    class StringFileInfo(Entries):
        type = "StringFileInfo"
        _object_ = dyn.clone(Entry, thetype=StringTable)

    @VersionEntry.define
    class Var(Entries):
        type = "Translation"
        _object_ = dyn.clone(Entry, thetype=dword)

    @VersionEntry.define
    class VarFileInfo(Entries):
        type = "VarFileInfo"

if True:
    class VS_FIXEDFILEINFO(pstruct.type):
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

    class VS_VERSIONINFO(pstruct.type):
        resourcedirectoryentry = 0x10
        def __Children(self):
            bs = self['wLength'].l.int() - self.size()
            return dyn.clone(Entries, blocksize=lambda s:bs)

        _fields_ = [
            (word, 'wLength'),
            (word, 'wValueLength'),
            (word, 'wType'),
            (pstr.szwstring, 'szKey'),
            (dyn.align(4), 'Padding1'),
            (lambda s: VS_FIXEDFILEINFO if s['wValueLength'].l.int() == 0x34 else ptype.type, 'Value'),    # XXX
            (dyn.align(4), 'Padding2'),
            (__Children, 'Children'),
        ]

if __name__ == '__main__':
    import pecoff
#    z = pecoff.Executable.open('c:/Program Files (x86)/Debugging Tools for Windows (x86)/windbg.exe', mode='r')
    z = pecoff.Executable.open('obj/windbg.exe')

    a = z['Pe']['OptionalHeader']['DataDirectory'][2]['VirtualAddress'].d.l
    b = a['Ids'][0]
    print b['Name RVA']
    print b['RVA']

#    from pecoff.resources import DataDirectory

#    print DataDirectory(b['RVA']['address'])
