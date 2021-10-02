import logging, itertools, datetime

import ptypes
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
    def datetime(self):
        seconds = self.get()
        epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc if hasattr(datetime, 'timezone') else None)
        delta = datetime.timedelta(seconds=seconds)
        raise epoch + delta

class Index(pint.uint16_t):
    def GetIndex(self):
        return self.int() - 1      # 1 off

class IMPORT_TYPE(pbinary.enum):
    length, _values_ = 2, [
        ('CODE', 0),
        ('DATA', 1),
        ('CONST', 2),
    ]

class IMPORT_NAME_TYPE(pbinary.enum):
    length, _values_ = 3, [
        ('ORDINAL', 0),
        ('NAME', 1),
        ('NAME_NOPREFIX', 2),
        ('NAME_UNDECORATE', 3),
    ]

class Import(pstruct.type):
    class Header(pstruct.type):
        class Type(pbinary.struct):
            _fields_ = [
                (IMPORT_TYPE, 'Type'),
                (IMPORT_NAME_TYPE, 'Name Type'),
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

        def valid(self):
            sig1,sig2 = self['Sig1'].int(), self['Sig2'].int()
            return sig1 == 0 and sig2 == 0xffff

    class Member(pstruct.type):
        _fields_ = [
            (pstr.szstring, 'Name'),
            (pstr.szstring, 'Module')
        ]

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

class Linker1(pstruct.type):
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

class Linker2(pstruct.type):
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

class Longnames(ptype.block):
    def extract(self, index):
        data = self.serialize()[index:]
        bytes = ptypes.utils.strdup(data, terminator=b'\0')
        return bytes.decode('latin1')

class Data(ptype.encoded_t):
    def _object_(self):
        header_t = Import.Header
        header = self.new(header_t, source=ptypes.provider.proxy(self)).l
        return Import if header.valid() else Object.File

class Member(pstruct.type):
    class Header(pstruct.type):
        class Name(pstr.string):
            length = 16
            def get(self):
                string = super(Member.Header.Name, self).get()
                return string.rstrip()
            str = get

            # FIXME: this string has the format "/%d" where the integer
            #        that it contains represents the offset into the
            #        Longnames member.

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

    def _Member_(self, name, size):
        '''This is the default callable that returns the type based on the name.'''
        if name == '/':
            result = Linker2
        elif name == '//':
            result = Longnames
        else:
            result = dyn.clone(Data, _value_=dyn.block(size))
        return result

    def __Member(self):
        header = self['Header'].li
        name, size = (header[fld] for fld in ['Name', 'Size'])

        # Use the header attributes that we fetched in order to pass
        # to the closure and determine the member type.
        callable = self._Member_
        return callable if ptype.istype(callable) else callable(name.str(), size.int())

    def __newline(self):
        ofs = self.getoffset('Member') + self['Header'].li['Size'].int()
        res = self.new(pstr.char_t, __name__='newline', offset=ofs)
        if res.l.serialize() == b'\n':
            return pstr.char_t
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (__Member, 'Member'),
        (__newline, 'newline'),
    ]

class Members(parray.terminated):
    # FIXME: it'd be supremely useful to cache all the import and object records
    #        somewhere instead of assigning them directly to Linker and Names

    def __init__(self, **attrs):
        self.Linker = self.Names = None
        return super(Members, self).__init__(**attrs)

    def _object_(self):
        def closure(name, size, index=len(self.value)):

            # Hardcode the first member of our archive
            if index == 0:
                if name != '/':
                    raise NameError(index, name)
                result = Linker1

            # Otherwise we can determine the type by using the name
            elif name == '/':
                result = Linker2
            elif name == '//':
                result = Longnames
            else:
                result = dyn.clone(Data, _value_=dyn.block(size))
            return result
        return dyn.clone(Member, _Member_=staticmethod(closure))

    def isTerminator(self, value):
        count, name = len(self.value), value['Header']['Name']

        # Always read at least one member.
        if not count:
            return False

        # Otherwise if our member name is '/', then we need to cache it.
        elif name.str() == '/' and isinstance(value['Member'], Linker2):
            self.Linker = value['Member']

        # If the name is '//', then we need to cache that too so that we
        # can figure out the member's actual (long) name.
        elif name.str() == '//' and isinstance(value['Member'], Longnames):
            self.Names = value['Member']

        # If our source is bounded, then we calculate the bounds so that
        # we can continue to read all of the available members even if
        # the file is malformed.
        if isinstance(self.source, ptypes.provider.bounded):

            # If our Linker2 member was assigned, then check whether we've
            # read a number of members matching the 'Number of Members' field.
            if self.Linker:
                return count >= 2 + self.Linker['Number of Members'].int()

            # Otherwise, continue to read members while there's still data
            # that we can read from the source. This should guarantee reading
            # the Linker2 member since it should be near the beginning.
            bounds = value.getoffset() + value.size()
            return bounds >= self.source.size()

        # If our source is unbounded, then we need to figure out whether
        # we've read the Linker2 member yet so that we can check the number
        # of members that we've read against it 'Number of Members' field.
        if self.Linker:
            return count >= 2 + self.Linker['Number of Members'].int()

        # Otherwise we always read at least 2 members because the first two
        # should always be Linker1 followed by Linker2.
        return count >= 2

    def iterate(self):
        iterable = (item['Member'] for item in self if isinstance(item['Member'], Data))
        for item in iterable:
            member = item.d.li
            if isinstance(member, Import):
                continue
            yield member
        return

    def iterate_imports(self):
        iterable = (item['Member'] for item in self if isinstance(item['Member'], Data))
        for item in iterable:
            member = item.d.li
            if isinstance(member, Import):
                yield member
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
        members = self['members']
        if not members.Linker:
            raise ptypes.error.InitializationError(self, 'getmember')
        offsets = members.Linker['Offsets']
        if index == 0:
            return self.new(Member, __name__="member[{:d}]".format(index), offset=offsets[index].int(), _Member_=Linker1)
        return self.new(Member, __name__="member[{:d}]".format(index), offset=offsets[index].int())

    def getmemberdata(self, index):
        return self.getmember(index).li.data().l.serialize()

    def getmembercount(self):
        members = self['members']
        if members.Linker:
            return members.Linker['Number of Members'].int()
        raise ptypes.error.InitializationError(members, 'getmembercount')

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
    import sys
    import ptypes, pecoff.Archive as Archive
    from ptypes import *
    source = ptypes.setsource(ptypes.prov.file(sys.argv[1]))

    print("Reading contents of {:s}...".format(source.file.name))
    self = Archive.File()
    self.load()
    print("Successfuly read {:d} members.".format(len(self['members'])))

    # TODO: enumerate all objects that are dll imports
    # TODO: enumerate all objects that are actual object files

    #print('Enumerating all members using view interface...')
    #for index in range(self.getmembercount()):
    #    print(self.getmember(index).load())
    #    print(ptypes.utils.hexdump(self.getmemberdata(index)))
    sys.exit(0)
