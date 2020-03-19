import logging,itertools,ptypes
from ptypes import *

from . import Object

class ulong(pint.bigendian(pint.uint32_t)): pass

class stringinteger(pstr.string):
    def __getvalue__(self):
        return int(self.str())
    def __setvalue__(self, integer):
        res, bs = str(integer), self.blocksize()
        return super(stringinteger, self).__setvalue__(res + ' '*(bs-len(res)))

class Index(pint.uint16_t):
    def GetIndex(self):
        return self.int()-1      # 1 off

class Import(pstruct.type):
    class Header(pstruct.type):
        class Type(pbinary.struct):
            _fields_ = [
                (2, 'Type'),
                (3, 'Name Type'),
                (11, 'Reserved')
            ]
        _fields_ = [
            (pint.uint16_t, 'Sig1'),
            (pint.uint16_t, 'Sig2'),
            (pint.uint16_t, 'Version'),
            (pint.uint16_t, 'Machine'),
            (pint.uint32_t, 'Time-Date Stamp'),
            (pint.uint32_t, 'Size Of Data'),
            (pint.uint16_t, 'Ordinal/Hint'),
            (Type, 'Type')
        ]

    class Member(pstruct.type):
        _fields_ = [
            (pstr.szstring, 'Name'),
            (pstr.szstring, 'Module')
        ]

        def valid(self):
            sig1,sig2 = self['Sig1'].int(), self['Sig2'].int()
            return sig1 == 0 and sig2 == 0xffff

        def repr(self):
            if self.initializedQ():
                return '!'.join(self[fld].str() for fld in ['Module', 'Name'])
            return super(Import, self).repr()

    _fields_ = [
        (Header, 'Header'),
        (Member, 'Member')
    ]

    def GetImport(self):
        return self['Member']['Module'].str(), self['Member']['Name'].str(), self['Header']['Ordinal/Hint'].int(), self['Header']['Type']

#######
class MemberType(ptype.definition):
    attribute,cache = 'internalname',{}

    class Data(dynamic.union):
        _fields_ = [
            (Import, 'Import'),
            (Object.File, 'Object'),
            (ptype.block, 'Block'),
        ]

        def isImport(self):
            return self['Import']['Header'].valid()

    default = Data

## Linker objects
@MemberType.define
class Linker1(pstruct.type):
    internalname = 0
    _fields_ = [
        (ulong, 'Number of Symbols'),
        (lambda self: dyn.array(ulong, self['Number of Symbols'].li.int()), 'Offsets'),
        (lambda self: dyn.array(pstr.szstring, self['Number of Symbols'].li.int()), 'Strings')
    ]

    def GetTable(self):
        return [(str(k), v.int()) for k,v in zip(self['Strings'], self['Offsets'])]

@MemberType.define
class Linker2(pstruct.type):
    internalname = 1
    _fields_ = [
        (pint.uint32_t, 'Number of Members'),
        (lambda self: dyn.array(pint.uint32_t, self['Number of Members'].li.int()), 'Offsets'),
        (pint.uint32_t, 'Number of Symbols'),
        (lambda self: dyn.array(Index, self['Number of Symbols'].li.int()), 'Indices'),
        (lambda self: dyn.array(pstr.szstring, self['Number of Symbols'].int()), 'Strings')
    ]

    def GetTable(self):
        return [(k.str(), self['Offsets'][i.GetIndex()].int()) for k,i in zip(self['Strings'], self['Indices'])]

#@MemberType.define
class LinkerMember1(Linker1):
    internalname = "/"
@MemberType.define
class LinkerMember2(Linker2):
    internalname = "/"

@MemberType.define
class Longnames(ptype.block):
    internalname = "//"

    def extract(self, index):
        return utils.strdup(self.serialize()[index:])

    def blocksize(self):
        return self.p['Header'].li['Size'].int()

#######
class Member(pstruct.type):
    internalname = None

    @classmethod
    def get(cls, internalname):
        res = list(cls._fields_)
        _,name = cls._fields_[1]
        res[1] = (MemberType.lookup(internalname), name)
        return dyn.clone(cls, _fields_=res)

    class Header(pstruct.type):
        class Name(pstr.string):
            length = 16
            str = lambda s: s.serialize().rstrip()

        _fields_ = [
            (Name, 'Name'),
            (dyn.clone(pstr.string, length=12), 'Date'),
            (dyn.clone(stringinteger, length=6), 'User ID'),
            (dyn.clone(stringinteger, length=6), 'Group ID'),
            (dyn.clone(stringinteger, length=8), 'Mode'),
            (dyn.clone(stringinteger, length=10), 'Size'),
            (dyn.clone(pstr.string, length=2), 'End of Header'),
        ]

        def data(self):
            size = self['Size'].int()
            return self.new(dyn.block(self['Size'].int()), __name__=self['Name'].str(), offset=self.getoffset()+self.size())

    def __Data(self):
        header = self['Header'].li
        filename,size = header['Name'].str(),header['Size'].int()
        default = dyn.clone(MemberType.default, internalname=filename, _value_=dyn.block(size))
        res = MemberType.lookup(filename, default)
        return dyn.clone(res, length=size) if ptype.isrelated(res, ptype.block) else res

    def __newline(self):
        ofs = self.getoffset('Member') + self['Header'].li['Size'].int()
        res = self.new(pstr.char_t, __name__='newline', offset=ofs)
        if res.l.serialize() == '\n':
            return pstr.char_t
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (__Data, 'Member'),
        (__newline, 'newline'),
    ]

class Members(parray.terminated):
    # FIXME: it'd be supremely useful to cache all the import and object records somewhere

    Linker,Names = None,None

    def _object_(self):
        if len(self.value) < 2:
            return Member.get(len(self.value))
        return Member

    def isTerminator(self, value):
        name = value['Header']['Name'].str()
        if len(self.value) <= 2:
            if name == '/':
                self.Linker = value['Member']
            return False
        if name == '//':
            self.Names = value

        res = self.Linker['Number of Members'].int()
        return False if len(self.value) < res else True

    def iterate(self):
        for m in (x['Member'] for x in self if isinstance(x, ArchiveMember)):
            if m.isImport():
                continue
            yield m['Object']
        return

    def iterate_imports(self):
        for m in (x['Member'] for x in self if isinstance(x, ArchiveMember)):
            if m.isImport():
                yield m['Import']
            continue
        return

    def repr(self):
        if self.initializedQ():
            return "{:s} {:d} members".format(self.name(), len(self))
        return super(Members,self).repr()

class File(pstruct.type):
    '''A .LIB file'''
    _fields_ = [
        (dyn.block(8), 'signature'),
        (Members, 'members'),
    ]

    def repr(self):
        if self.initializedQ():
            return "{:s} signature:{:s} members:{:d}".format(self.name(), self['signature'].summary(), self.getmembercount())
        return super(File,self).repr()

    ## really slow interface
    def getmember(self, index):
        offsets = self['members'].Linker['Offsets']
        return self.new(MemberHeader, __name__="member[{:d}]".format(index), offset=offsets[index])

    def getmemberdata(self, index):
        return self.getmember(index).li.data().l.serialize()

    def getmembercount(self):
        return self['members'].Linker['Number of Members'].int()

    ## faster interface using ptypes to slide view
    def fetchimports(self):
        offsets = self['members'].Linker['Offsets']

        memberheader = self.new(MemberHeader, __name__='header', offset=0)
        importheader = self.new(ImportHeader, __name__='header', offset=0)

        p = self.new(dyn.block(4), __name__='magic', offset=0)
        imp = self.new(Import, __name__='import', offset=0)
        memblocksize = memberheader.alloc().size()
        impblocksize = importheader.alloc().size()

        for o in offsets:
            o = int(o)+memblocksize
            p.setoffset(o)
            if p.load().serialize() == b'\x00\x00\xff\xff':
                importheader.setoffset(o)
                imp.setoffset(o+impblocksize)
                imp.load()
                yield (imp['Module'].str(), imp['Name'].str(), importheader['Ordinal/Hint'].int(), tuple(importheader['Type'].values()[:2]))
            continue
        return

    def fetchmembers(self):
        offsets = self['members'].Linker['Offsets']
        memberheader = self.new(MemberHeader, __name__='header', offset=0)

        p = self.new(dyn.block(4), __name__='magic', offset=0)
        memblocksize = memberheader.alloc().size()

        for index,o in enumerate(offsets):
            o = int(o)+memblocksize
            p.setoffset(o)
            if p.load().serialize() == b'\x00\x00\xff\xff':
                continue

#            yield self.new(Object.File, __name__="Member[{:d}]".format(index), offset=o)
            yield self.new(Object.File, offset=o)
        return

if __name__ == '__main__':
    import pecoff.Archive as Archive
    from ptypes import *
    source = ptypes.file('~/python26/libs/python26.lib')

    print('Reading .lib header')
#    Archive.File = ptypes.debugrecurse(Archive.File)
    self = Archive.File()
#    self.source = provider.file('../../obj/test.lib')
    self.source = ptypes.file('~/python26/libs/python26.lib')
    self.load()

#    print(self['SymbolNames']['Header'])
#    print(self['SymbolNames']['Member'])
#    print(self['MemberNames']['Header'])
#    print(self['MemberNames']['Member'])
#    print(self['LongNames']['Header'])
#    print(self['LongNames']['Member'])
#    print('-'*79)

    ## enumerate all objects that are dll imports
    ## enumerate all objects that are actual object files

    print('enumerating all members')
    for index in xrange( self.getmembercount() ):
        print(self.getmember(index).load())
        print(ptypes.utils.hexdump(self.getmemberdata(index)))

#    a = Archive.File(offset=19912)
