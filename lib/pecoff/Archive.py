import ptypes
from ptypes import *
from ptypes.pint import *
import logging
import Object

class ulong(bigendian(uint32_t)): pass

class stringinteger(pstr.string):
    def __int__(self):
        return int(self.str())

class newline(pstr.szstring):
    def isTerminator(self, value):
        if value.serialize() != '\n':
            self.value=''
            return False
        return True

#
class MemberHeaderName(pstr.string):
    length = 16

    def str(self):
        s = self.serialize().rstrip()
#        if s[0] == '/':
#            return self.parent.parent['LongNames']['Member'].get(int(s[1:]))
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

# FIXME: instead of making each of these a .union explicitly, I can probably transform them into
#            union all in one place in the Members array

class FirstLinker(dyn.union):
    class __FirstLinker(pstruct.type):
        _fields_ = [
            (ulong, 'Number of Symbols'),
            (lambda self: dyn.array(ulong, int(self['Number of Symbols'].load())), 'Offsets'),
            (lambda self: dyn.array(pstr.szstring, int(self['Number of Symbols'])), 'String Table')
        ]

        def get(self):
            return [(str(k), int(v)) for k,v in zip(self['String Table'], self['Offsets'])]
    _fields_ = [(__FirstLinker, 'Data')]

class FirstLinkerMember(pstruct.type):
    _fields_ = [
        (MemberHeader, 'Header'),
        (FirstLinker, 'Member'),
        (pstr.char_t, 'newline')
    ]

class Index(uint16_t):
    def get(self):
        return int(self)-1      # 1 off

class SecondLinker(dyn.union):
    class __SecondLinker(pstruct.type):
        _fields_ = [
            (uint32_t, 'Number of Members'),
            (lambda self: dyn.array(uint32_t, int(self['Number of Members'].load()))(), 'Offsets'),
            (uint32_t, 'Number of Symbols'),
            (lambda self: dyn.array(Index, int(self['Number of Symbols'].load())), 'Indices'),
            (lambda self: dyn.array(pstr.szstring, int(self['Number of Symbols'])), 'String Table')
        ]

        def get(self):
            return [(k.get(), int(self['Offsets'][i.get()])) for k,i in zip(self['String Table'], self['Indices'])]
    _fields_ = [(__SecondLinker, 'Data')]    

class SecondLinkerMember(pstruct.type):
    _fields_ = [
        (MemberHeader, 'Header'),
        (SecondLinker, 'Member'),
        (pstr.char_t, 'newline')
    ]

class Longnames(ptype.type):
    length = 0

    def get(self, index):
        warnings.warn('.get has been deprecated in favor of .extract', DeprecationWarning)

    def extract(self, index):
        return utils.strdup(self.serialize()[index:])

class LongnamesMember(pstruct.type):
    _fields_ = [
        (MemberHeader, 'Header'),
        (lambda s: dyn.clone(Longnames, length=int(s['Header'].l['Size'])), 'Member'),
        (pstr.char_t, 'newline')
    ]

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
    def __repr__(self):
        return '%s!%s'%( self['Module'].str(), self['Name'].str() )

class ImportMember(pstruct.type):
    _fields_ = [
        (ImportHeader, 'Header'),
        (Import, 'Member')
    ]

    def get(self):
        return self['Member']['Module'].get(), self['Member']['Name'].get(), int(self['Header']['Ordinal/Hint']), self['Header']['Type']

class MemberData(dyn.union):
    root=dyn.block(0)
    _fields_ = [
        (ImportMember, 'Import'),
        (Object.File, 'Object'),
    ]

    def isImport(self):
        return self['Import']['Header'].valid()

class ArchiveMember(pstruct.type):
    def __Member(self):
        return dyn.clone(MemberData, root=dyn.block(int(self['Header'].l['Size'])))

    _fields_ = [
        (MemberHeader, 'Header'),
        (__Member, 'Member'),
        (newline, 'newline'),
    ]

    def isImport(self):
        return self['Member']['Import']['Header'].valid()

class Members(parray.terminated):
    # FIXME: it'd be supremely useful to cache all the import and object records somewhere

    FirstLinker = SecondLinker = None
    Longnames = None

    queue = None
    def __ArchiveMember(self):
        if self.queue:
            return self.queue.pop(0)
        return ArchiveMember

    def load(self):
        self.queue = []
        self.queue.append(FirstLinkerMember)
        self.queue.append(SecondLinkerMember)

        logging.info('loading %s.%s from %s'% (type(self).__module__, type(self).__name__, self.source) )
        result = super(Members,self).load()
        logging.info('done')
#        print len(list(self.walk())),len(list(self.walkimports()))

        return result

    _object_ = __ArchiveMember

    __count = 0
    def isTerminator(self, value):
        name = value['Header']['Name'].str()
        if len(self.queue) == 1:
            logging.info('...loaded FirstLinker record')
            self.FirstLinker = value['Member']
            return False

        if name == '//':
            assert self.Longnames is None, 'self.Longnames has already been defined'
            self.Longnames = value['Member']
            logging.info('..loaded Longnames record -> %d bytes'% len(self.Longnames))
            return False

        if len(self.queue) == 0:
            if name == '/':
                logging.info('..loading the SecondLinker data')
                self.SecondLinker = value['Member']['Data']
            
                self.__count = int(self.SecondLinker['Number of Members'].l)-1
                logging.info('.loading %d total members'% (self.__count+1))
                return False

            if self.__count > 0:
                self.__count -= 1
                return False

            if self.__count == 0:
                return True
            pass
        return False

    def walk(self):
        for m in (x['Member'] for x in self if type(x) is ArchiveMember):
            if m.isImport():
                continue
            yield m['Object']
        return

    def walkimports(self):
        for m in (x['Member'] for x in self if type(x) is ArchiveMember):
            if m.isImport():
                yield m['Import']
            continue
        return

    def __repr__(self):
        return '%s %d members'%( self.name(), len(self) )

class File(pstruct.type):
    '''A .LIB file'''
    _fields_ = [
        (dyn.block(8), 'signature'),
        (Members, 'members'),
    ]

    def __repr__(self):
        return '%s signature:%s members:%d'% (self.name(), repr(self['signature'].serialize()), self.getmembercount())
    
    ## really slow interface
    def getmember(self, index):
        offsets = self['members'].SecondLinker['Offsets']
        return self.newelement(MemberHeader, 'member[%d]'% index, offsets[index])

    def getmemberdata(self, index):
        return self.getmember(index).load().get().load().serialize()

    def getmembercount(self):
        return int(self['members'].SecondLinker['Number of Members'])

    ## faster interface using ptypes to slide view
    def fetchimports(self):
        offsets = self['members'].SecondLinker['Offsets']
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
                yield (imp['Module'].str(), imp['Name'].str(), int(importheader['Ordinal/Hint']), tuple(importheader['Type'].values()[:2]))
            continue
        return

    def fetchmembers(self):
        offsets = self['members'].SecondLinker['Offsets']
        memberheader = self.newelement(MemberHeader, 'header', 0)

        p = self.newelement(dyn.block(4), 'magic', 0)
        memblocksize = memberheader.alloc().size()

        for index,o in enumerate(offsets):
            o = int(o)+memblocksize
            p.setoffset(o)
            if p.load().serialize() == '\x00\x00\xff\xff':
                continue

#            yield self.newelement(Object.File, 'Member[%d]'% index, o)
            yield self.newelement(Object.File, None, o)
        return

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
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
