import logging, itertools, ptypes
from ptypes import *

from . import Object

class ulong(pint.bigendian(pint.uint32_t)): pass

class stringinteger(pstr.string):
    def set(self, integer):
        res, bs = str(integer), self.blocksize()
        size = bs - len(res)
        return self.__setvalue__(res + ' ' * max(0, size))

    def get(self):
        result, string = 0, self.__getvalue__()
        stripped = string.rstrip()
        try:
            if stripped:
                result = int(stripped, 10)
            else:
                logging.warning("Returning {:d} due to the inability to convert the empty string ({!r}) at {:s} to an integer.".format(0, string, self.instance()))
        except Exception as E:
            logging.warning("Returning {:d} due to the inability to convert the string ({!r}) at {:s} to an integer.".format(0, string, self.instance()))
        return result

    int = get

class stringdate(stringinteger):
    # FIXME: implement some of the methods that conver this instance
    #        into a proper date that we can interact with.
    def datetime(self):
        string = self.get()
        raise NotImplementedError

class Index(pint.uint16_t):
    def GetIndex(self):
        return self.int() - 1      # 1 off

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
    attribute, cache = 'internalname', {}

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
        table = []
        for string, offset in zip(self['Strings'], self['Offsets']):
            item = string.str(), offset.int()
            table.append(item)
        return table

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
        table, offsets = [], self['Offsets']
        for string, index in zip(self['Strings'], self['Indices']):
            realindex = index.GetIndex()
            offset = offsets[realindex]
            item = string.str(), offset.int()
            table.append(item)
        return table

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
        data = self.serialize()[index:]
        bytes = ptypes.utils.strdup(data, terminator=b'\0')
        return bytes
        #return bytes.decode('latin1')      # FIXME: probably a better idea to decode this using the correct encoding

#######
class Member(pstruct.type):
    internalname = None

    class Header(pstruct.type):
        class Name(pstr.string):
            length = 16
            def get(self):
                string = super(Member.Header.Name, self).get()
                return string.rstrip()
            str = get

        _fields_ = [
            (Name, 'Name'),
            (dyn.clone(stringdate, length=12), 'Date'),
            (dyn.clone(stringinteger, length=6), 'User ID'),
            (dyn.clone(stringinteger, length=6), 'Group ID'),
            (dyn.clone(stringinteger, length=8), 'Mode'),
            (dyn.clone(stringinteger, length=10), 'Size'),
            (dyn.clone(pstr.string, length=2), 'End of Header'),
        ]

        def data(self):
            size = self['Size'].int()
            return self.new(dyn.block(self['Size'].int()), __name__=self['Name'].str(), offset=self.getoffset() + self.size())

    __LinkerMember__ = None
    def __Data(self):
        header = self['Header'].li

        # If the __LinkerMember__ property is defined as something, then use it for our type
        if self.__LinkerMember__:
            res, size = self.__LinkerMember__, header['Size'].int()

        # Otherwise, we use the member name in order to determine the type.
        else:
            filename, size = header['Name'].str(), header['Size'].int()
            default = dyn.clone(MemberType.default, internalname=filename, _value_=dyn.block(size))
            res = MemberType.lookup(filename, default)

        # If our type is related to a block, then clone it using the size from the header.
        return dyn.clone(res, length=size) if ptype.isrelated(res, ptype.block) else res

    def __newline(self):
        ofs = self.getoffset('Member') + self['Header'].li['Size'].int()
        res = self.new(pstr.char_t, __name__='newline', offset=ofs)
        if res.l.serialize() == b'\n':
            return pstr.char_t
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (__Data, 'Member'),
        (__newline, 'newline'),
    ]

class Members(parray.terminated):
    # FIXME: it'd be supremely useful to cache all the import and object records
    #        somewhere instead of assigning them directly to Linker and Names

    Linker, Names = None, None

    def _object_(self):

        # Hardcode the first two members of our archive
        if len(self.value) < 2:
            index = len(self.value)
            t = MemberType.lookup(index)
            return dyn.clone(Member, __LinkerMember__=t)

        # Otherwise we can determine the type by using the name
        return Member

    def isTerminator(self, value):
        name = value['Header']['Name'].str()

        # Always read at least 2 members. If one of them has a member named "/"
        # then we cache it in the "Linker" property.
        if len(self.value) <= 2:
            if name == '/':
                self.Linker = value['Member']
            return False

        # If we find a member named "//" then cache it in the "Names" property.
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

class File(pstruct.type):
    '''A .LIB file'''
    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'signature'),
        (Members, 'members'),
    ]

    ## really slow interface
    def getmember(self, index):
        offsets = self['members'].Linker['Offsets']
        return self.new(Member, __name__="member[{:d}]".format(index), offset=offsets[index])

    def getmemberdata(self, index):
        return self.getmember(index).li.data().l.serialize()

    def getmembercount(self):
        return self['members'].Linker['Number of Members'].int()

    ## faster interface using ptypes to slide view
    def fetchimports(self):
        # FIXME: this seems to be broken at the moment
        offsets = self['members'].Linker['Offsets']

        member_view = self.new(Member, __name__='header', offset=0)
        import_view = self.new(Import, __name__='header', offset=0)

        p = self.new(dyn.block(4), __name__='magic', offset=0)
        import_view = self.new(Import, __name__='import', offset=0)
        member_bs = member_view.alloc().size()
        import_bs = import_view.alloc().size()

        for item in offsets:
            offset = item.int() + member_bs
            p.setoffset(offset)
            if p.load().serialize() == b'\x00\x00\xff\xff':
                import_view.setoffset(offset)
                import_view.setoffset(offset + import_bs)
                import_view.load()
                yield (import_view['Module'].str(), import_view['Name'].str(), import_view['Ordinal/Hint'].int(), tuple(import_view['Type'].values()[:2]))
            continue
        return

    def fetchmembers(self):
        # FIXME: this seems to be broken at the moment
        offsets = self['members'].Linker['Offsets']
        member_view = self.new(Member, __name__='header', offset=0)

        p = self.new(dyn.block(4), __name__='magic', offset=0)
        member_bs = member_view.alloc().size()

        for index, item in enumerate(offsets):
            offset = item.int() + member_bs
            p.setoffset(offset)
            if p.load().serialize() == b'\x00\x00\xff\xff':
                continue

#            yield self.new(Object.File, __name__="Member[{:d}]".format(index), offset=offset)
            yield self.new(Object.File, offset=offset)
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
