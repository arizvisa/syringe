import ptypes
from ptypes import *
from ptypes.pint import *
import Object

class ulong(bigendian(uint32_t)): pass

class stringinteger(pstr.string):
    def __int__(self):
        return int(self.get())

class MemberHeaderName(pstr.string):
    length = 16

    def __str__(self):
        return self.serialize().rstrip()

    def get(self):
        s = str(self)
        if s[0] == '/':
            return self.parent.parent['LongNames']['Member'].get(int(s[1:]))
        return s

class MemberHeader(pstruct.type):
    _fields_ = [
        (MemberHeaderName, 'Name'),
        (dyn.clone(pstr.string, length=12), 'Date'),
        (dyn.clone(pstr.string, length=6), 'User ID'),
        (dyn.clone(pstr.string, length=6), 'Group ID'),
        (dyn.clone(pstr.string, length=8), 'Mode'),
        (dyn.clone(stringinteger, length=10), 'Size'),
        (dyn.clone(pstr.string, length=2), 'End of Header'),
    ]

    def get(self):
        size = int(self['Size'])
        return self.newelement(dyn.block(int(self['Size'])), self['Name'].get(), self.getoffset()+self.size())

class FirstLinker(pstruct.type):
    _fields_ = [
        (ulong, 'Number of Symbols'),
        (lambda self: dyn.array(ulong, int(self['Number of Symbols'].load())), 'Offsets'),
        (lambda self: dyn.array(pstr.szstring, int(self['Number of Symbols'])), 'String Table')
    ]

    def get(self):
        return [(str(k), int(v)) for k,v in zip(self['String Table'], self['Offsets'])]

class Index(uint16_t):
    def get(self):
        return int(self)-1      # 1 off

class SecondLinker(pstruct.type):
    _fields_ = [
        (uint32_t, 'Number of Members'),
        (lambda self: dyn.array(uint32_t, int(self['Number of Members'].load()))(), 'Offsets'),
        (uint32_t, 'Number of Symbols'),
        (lambda self: dyn.array(Index, int(self['Number of Symbols'].load())), 'Indices'),
        (lambda self: dyn.array(pstr.szstring, int(self['Number of Symbols'])), 'String Table')
    ]

    def get(self):
        return [(k.get(), int(self['Offsets'][i.get()])) for k,i in zip(self['String Table'], self['Indices'])]

class Longnames(ptype.type):
    length = 0

    def get(self, index):
        return utils.strdup(self.serialize()[index:])

def newMember(name, membertype):
    class Member(pstruct.type):
        _fields_ = [
            (MemberHeader, 'Header'),
            (lambda s: dyn.block(int(s['Header']['Size'])), 'Member'),
            (pstr.char_t, 'newline')
        ]

        def fetch(self):
            return dyn.cast(self['Member'], membertype)

        def deserialize(self, source):
            super(Member, self).deserialize(source)
            s = str(self['Header']['Name'])
            #assert s == name, 'Found name %s, but expected %s'%(s, name)
            return self

    return Member

class ImportHeaderType(pbinary.struct):
    _fields_ = [
        (2, 'Type'),
        (3, 'Name Type'),
        (11, 'Reserved')
    ]

class ImportHeader(pstruct.type):
    _fields_ = [
        (uint16_t, 'Sig1'),
        (uint16_t, 'Sig2'),
        (uint16_t, 'Version'),
        (uint16_t, 'Machine'),
        (uint32_t, 'Time-Date Stamp'),
        (uint32_t, 'Size Of Data'),
        (uint16_t, 'Ordinal/Hint'),
        (ImportHeaderType, 'Type')
    ]

    def valid(self):
        sig1,sig2 = int(self['Sig1']), int(self['Sig2'])
        return sig1 == 0 and sig2 == 0xffff

class Import(pstruct.type):
    _fields_ = [
        (pstr.szstring, 'Name'),
        (pstr.szstring, 'Module')
    ]

class ImportMember(pstruct.type):
    _fields_ = [
        (ImportHeader, 'Header'),
        (Import, 'Member')
    ]

    def get(self):
        return self['Member']['Module'].get(), self['Member']['Name'].get(), int(self['Header']['Ordinal/Hint']), self['Header']['Type']

class File(pstruct.type):
    '''A .LIB file'''
    _fields_ = [
        (dyn.block(8), 'signature'),
        (newMember('/', FirstLinker), 'SymbolNames'),
        (newMember('/', SecondLinker), 'MemberNames'),
        (newMember('//', lambda s: dyn.clone(Longnames, length=int(s['Header']['Size']))), 'LongNames'),
    ]
    
    ## really slow interface
    def getmember(self, index):
        offsets = self['MemberNames'].fetch()['Offsets']
        return self.newelement(MemberHeader, 'member[%d]'% index, offsets[index])

    def getmemberdata(self, index):
        return self.getmember(index).load().get().load().serialize()

    def getmembercount(self):
        return int(self['MemberNames'].fetch()['Number of Members'])

    ## faster interface using ptypes to slide view
    def fetchimports(self):
        offsets = self['MemberNames'].fetch()['Offsets']
        memberheader = self.newelement(MemberHeader, 'header', 0)
        importheader = self.newelement(ImportHeader, 'header', 0)

        p = self.newelement(dyn.block(4), 'magic', 0)
        imp = self.newelement(Import, 'import', 0)
        memblocksize = memberheader.alloc().size()
        impblocksize = importheader.alloc().size()

        for o in offsets:
            o = int(o)+memblocksize
            p.setoffset(o)
            if p.load().serialize() == '\x00\x00\xff\xff':
                importheader.setoffset(o)
                imp.setoffset(o+impblocksize)
                imp.load()
                yield (imp['Module'].get(), imp['Name'].get(), int(importheader['Ordinal/Hint']), tuple([v for v,s in importheader['Type'].values()]))
            continue
        return

    def fetchmembers(self):
        offsets = self['MemberNames'].fetch()['Offsets']
        memberheader = self.newelement(MemberHeader, 'header', 0)

        p = self.newelement(dyn.block(4), 'magic', 0)
        memblocksize = memberheader.alloc().size()

        for index,o in enumerate(offsets):
            o = int(o)+memblocksize
            p.setoffset(o)
            if p.load().serialize() == '\x00\x00\xff\xff':
                continue

            yield self.newelement(Object.File, 'Member[%d]'% index, o)
        return

def open(filename):
    res = File()
    res.source = provider.file(filename)
    res.load()
    res.filename = filename
    return res

if __name__ == '__main__':
    import Archive
    from ptypes import *

    print 'Reading .lib header'
    self = Archive.File()
#    self.source = provider.file('../../obj/test.lib')
    self.source = provider.file('c:/python25/libs/python25.lib')
    self.load()

    print self['SymbolNames']['Header']
#    print self['SymbolNames']['Member'].get()
    print self['MemberNames']['Header']
#    print self['MemberNames']['Member'].get()
#    print self['LongNames']['Header']
#    print self['LongNames']['Member']
#    print '-'*79

    ## enumerate all objects that are dll imports
    ## enumerate all objects that are actual object files

    print 'enumberating all members'
    for index in xrange( self.getmembercount() ):
        print self.getmember(index).load()
        print ptypes.utils.hexdump(self.getmemberdata(index))
