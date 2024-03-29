import logging, itertools, datetime

import ptypes
from ptypes import *

from . import headers, Object

@pint.bigendian
class ulong(pint.uint32_t):
    pass

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
        return epoch + delta

    def summary(self):
        res = super(stringdate, self).summary()
        if self.str() and self.int() >= 0:
            return "{:s} -> {!s}".format(res, self.datetime())
        return res

class Index(pint.uint16_t):
    def GetIndex(self):
        return self.int() - 1      # 1 off

class Import(pstruct.type):
    class Header(pstruct.type):
        _fields_ = [
            (headers.IMAGE_FILE_MACHINE_, 'Sig1'),
            (pint.uint16_t, 'Sig2'),
            (pint.uint16_t, 'Version'),
            (headers.IMAGE_FILE_MACHINE_, 'Machine'),
            (headers.TimeDateStamp, 'Time-Date Stamp'),
            (pint.uint32_t, 'Size Of Data'),
            (pint.uint16_t, 'Ordinal/Hint'),
            (headers.IMAGE_IMPORT_TYPE_INFORMATION, 'Type')
        ]

        def summary(self):
            type = self['Type']
            return "Sig1={:#x} Sig2={:#x} : Machine={:#s} Ordinal/Hint={:#x} ... : (Type) {:s} Name={:s}".format(self['Sig1'], self['Sig2'], self['Machine'], self['Ordinal/Hint'], type.field('Type'), type.field('Name'))

        def valid(self):
            sig1, sig2, version = self['Sig1'].int(), self['Sig2'].int(), self['Version'].int()
            return sig1 == 0x0000 and sig2 == 0xffff and version == 0x0000

    class Member(pstruct.type):
        _fields_ = [
            (pstr.szstring, 'Name'),
            (pstr.szstring, 'Module')
        ]

        def str(self):
            fields = ['Module', 'Name']
            return '!'.join(self[fld].str() for fld in fields)

        def summary(self):
            return "Module={!r} Name={!r}".format(self['Module'].str(), self['Name'].str())

        def repr(self):
            if self.initializedQ():
                return self.str()
            return super(Import, self).repr()

    _fields_ = [
        (Header, 'Header'),
        (Member, 'Member')
    ]

    def summary(self):
        type = self['Header']['Type']
        return "(Header) Machine={:#s} Ordinal/Hint={:#x} Type={:#s} Name={:#s} : (Member) Module={!r} Name={!r}".format(self['Header']['Machine'], self['Header']['Ordinal/Hint'], type.field('Type'), type.field('Name'), self['Member']['Module'].str(), self['Member']['Name'].str())

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
            item = offset.int(), string.str()
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
            item = offset.int(), string.str()
            table.append(item)
        return table

class Longnames(ptype.block):
    def extract(self, index):
        data = bytearray(self.serialize()[index:])
        iterable = itertools.takewhile(lambda byte, sentinel=bytearray(b'\0\n'): byte not in sentinel, iter(data))
        return bytes(iterable).decode('latin1')

class Data(ptype.encoded_t):
    def _object_(self):
        header_t = Import.Header
        header = self.new(header_t, source=ptypes.provider.proxy(self)).l
        return Import if header.valid() else Object.File

    def summary(self):
        res = self.d
        return res.li.summary() if self.initializedQ() and self.value[:6] == b'\x00\x00\xff\xff\x00\x00' else super(Data, self).summary()

class Member(pstruct.type):
    class Header(pstruct.type):
        class _Name(pstr.string):
            length = 16
            def get(self):
                string = super(Member.Header._Name, self).get()
                return string.rstrip()
            str = get

            def OffsetQ(self):
                '''check if the string is of the format "/%d".'''
                res = self.str().rstrip()
                return res not in {'/', '//'} and res.startswith('/')

            def Offset(self):
                '''if the string is a valid offset, then the integer represents the offset into the Longnames member.'''
                res = self.str().rstrip()
                return int(res[1:]) if res.startswith('/') else None

            def Extract(self):
                if not self.OffsetQ():
                    return self.str()

                p = self.getparent(File)
                if 'Longnames' in p and p['Longnames'].size():
                    longnames = p['LongNames']['Member']
                elif 'members' in p and getattr(p['members'], 'Names', None):
                    longnames = p['members'].Names
                else:
                    return self.str()

                offset = self.Offset()
                return longnames.extract(offset)

            def summary(self):
                if not self.OffsetQ():
                    return super(Member.Header._Name, self).summary()

                p = self.getparent(File)
                if 'Longnames' in p and p['Longnames'].size():
                    longnames = p['LongNames']['Member']
                elif 'members' in p and getattr(p['members'], 'Names', None):
                    longnames = p['members'].Names
                else:
                    return super(Member.Header._Name, self).summary()

                offset = self.Offset()
                extracted = longnames.extract(offset)
                summary = super(Member.Header._Name, self).summary()
                return "{:s} -> {!r}".format(summary, extracted)

        _fields_ = [
            (_Name, 'Name'),
            (dyn.clone(stringdate, length=12), 'Date'),
            (dyn.clone(stringinteger, length=6), 'User ID'),
            (dyn.clone(stringinteger, length=6), 'Group ID'),
            (dyn.clone(stringinteger, length=8), 'Mode'),
            (dyn.clone(stringinteger, length=10), 'Size'),
            (dyn.clone(pstr.string, length=2), 'End of Header'),
        ]

        def Name(self):
            res = self['Name']
            return res.str().rstrip()

        def summary(self):
            result = []
            result.append("size={:d}".format(self['Size'].int()))
            if self['User ID'].str().rstrip():
                result.append("uid={:d}".format(self['User ID'].int()))
            if self['Group ID'].str().rstrip():
                result.append("gid={:d}".format(self['Group ID'].int()))
            if self['Mode'].str().rstrip():
                result.append("mode={:o}".format(self['Mode'].int()))

            extracted = "({!s}) {!r}".format(self.Name(), self['Name'].Extract()) if self['Name'].OffsetQ() else self.Name()
            if self['Date'].str().rstrip() and self['Date'].int() > 0:
                dt = self['Date'].datetime()
                return "name={:s} date={!s}{:s}".format(extracted, dt.isoformat(), " {:s}".format(' '.join(result)) if result else '')
            if self['Name'].OffsetQ():
                return "name={:s} {:s}".format(extracted, " {:s}".format(' '.join(result)) if result else '')
            return "name={:s}{:s}".format(extracted, " {:s}".format(' '.join(result)) if result else '')

        def data(self):
            size = self['Size'].int()
            return self.new(dyn.block(self['Size'].int()), __name__=self['Name'].str(), offset=self.getoffset() + self.size())

    def _Member_(self, name, size):
        '''This is the default callable that returns the type based on the name.'''
        if name == '/':
            result = Linker2
        elif name == '//':
            result = dyn.clone(Longnames, length=size)
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

    def __padding(self):
        res, fields = self['Header'].li, ['Member']
        return dyn.block(max(0, res['Size'].int() - sum(self[fld].li.size() for fld in fields)))

    def __newline(self):
        ofs = self.getoffset('Member') + self['Header'].li['Size'].int()
        res = self.new(pstr.char_t, __name__='newline', offset=ofs)
        try:
            if res.l.str() == '\n':
                return pstr.char_t
            return ptype.undefined
        except ptypes.error.LoadError:
            pass
        return ptype.undefined

    _fields_ = [
        (Header, 'Header'),
        (__Member, 'Member'),
        (__padding, 'padding'),
        (__newline, 'newline'),
    ]

class Members(parray.terminated):
    # FIXME: it'd be supremely useful to cache all the import and object records
    #        somewhere instead of assigning them directly to Linker and Names

    def load(self, *args, **kwargs):
        self.Linker = self.Names = None
        return super(Members, self).load(*args, **kwargs)

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
                result = dyn.clone(Longnames, length=size)
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
            if self.Linker or self.Names:
                extra = [(1 if found else 0) for found in [True, self.Linker, self.Names]]
                return count >= sum(extra) + self.Linker['Number of Members'].int()

            # Otherwise, continue to read members while there's still data
            # that we can read from the source. This should guarantee reading
            # the Linker2 member since it should be near the beginning.
            bounds = value.getoffset() + value.size()
            return bounds >= self.source.size()

        # If our source is unbounded, then we need to figure out whether
        # we've read the Linker2 member yet so that we can check the number
        # of members that we've read against it 'Number of Members' field.
        if self.Linker or self.Names:
            extra = [(1 if found else 0) for found in [True, self.Linker, self.Names]]
            return count >= sum(extra) + self.Linker['Number of Members'].int()

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

class Indexed(File):
    class Linker1(pstruct.type):
        def __Strings(self):
            bs, fields = self.blocksize(), ['Number of Symbols', 'Offsets']
            return dyn.block(max(0, self.blocksize() - sum(self[fld].li.size() for fld in fields)))
        _fields_ = [
            (ulong, 'Number of Symbols'),
            (lambda self: dyn.clone(parray.type, _object_=ulong, length=self['Number of Symbols'].li.int()), 'Offsets'),
            (__Strings, 'Strings'),
        ]
        def GetTable(self):
            table, data = [], bytearray(self['Strings'].serialize())
            for offset in self['Offsets']:
                end = data.find(0)
                item = offset.int(), bytes(data[: end + 1])
                table.append(item)
                data = data[end + 1:]
            return table

    class Linker2(pstruct.type):
        def __Strings(self):
            bs, fields = self.blocksize(), ['Number of Members', 'Offsets', 'Number of Symbols', 'Indices']
            return dyn.block(self.blocksize() - sum(self[fld].li.size() for fld in fields))
        _fields_ = [
            (pint.uint32_t, 'Number of Members'),
            (lambda self: dyn.clone(parray.type, _object_=pint.uint32_t, length=self['Number of Members'].li.int()), 'Offsets'),
            (pint.uint32_t, 'Number of Symbols'),
            (lambda self: dyn.clone(parray.type, _object_=Index, length=self['Number of Symbols'].li.int()), 'Indices'),
            (__Strings, 'Strings'),
        ]

        def GetTable(self):
            table, offsets, data = [], self['Offsets'], bytearray(self['Strings'].serialize())
            for string, index in zip(self['Strings'], self['Indices']):
                end = data.find(0)
                realindex = index.GetIndex()
                offset = offsets[realindex]
                item = offset.int(), bytes(data[: end + 1])
                table.append(item)
                data = data[end + 1:]
            return table

    def __indexed_member(self, name, size):
        if name == '/' and len(self.value) == 2:
            return dyn.clone(Indexed.Linker1, blocksize=lambda _, cb=size: cb)
        elif name == '/':
            return dyn.clone(Indexed.Linker2, blocksize=lambda _, cb=size: cb)
        elif name == '//':
            return dyn.clone(Longnames, length=size)
        return dyn.clone(ptype.block, length=size)

    def __Longnames(self):
        offset = sum(self[fld].li.size() for fld in ['signature', 'Linker1', 'Linker2'])
        peek = self.new(Member.Header._Name, source=self.source, offset=self.getoffset() + offset)
        if peek.li.str() == '//':
            return dyn.clone(Member, _Member_=self.__indexed_member)
        return ptype.block

    def __members(self):
        linker2, member_t = self['Linker2'].li, dyn.clone(Member, _Member_=staticmethod(lambda name, size: dyn.clone(Data, _value_=dyn.block(size))))

        # If the Linker2 member is not using the expected type, then we can't trust it to contain
        # the number of members. So, we need to guess things based on the file size.
        if not isinstance(self['Linker2']['Member'], Indexed.Linker2):
            offset = sum(self[fld].li.size() for fld in ['signature', 'Linker1', 'Linker2'])
            if not isinstance(self.source, ptypes.provider.bounded):
                return dyn.array(member_t, 0)

            # If we're decoding from a bounded provider, then we can use
            # the file size to determine the number of members to decode.
            blocksize = max(0, self.source.size() - offset)
            return dyn.blockarray(member_t, blocksize)

        # If the number of members is larger than 2, then use it to determine the array length.
        count = linker2['Member']['Number of Members']
        return dyn.array(member_t, count.int())

    _fields_ = [
        (dyn.clone(pstr.string, length=8), 'signature'),
        (lambda self: dyn.clone(Member, _Member_=self.__indexed_member), 'Linker1'),
        (lambda self: dyn.clone(Member, _Member_=self.__indexed_member), 'Linker2'),
        (__Longnames, 'Longnames'),
        (__members, 'members'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, pecoff.Archive as Archive
    from ptypes import *
    source = ptypes.setsource(ptypes.prov.file(sys.argv[1], 'rb'))

    print("Reading contents of {:s}...".format(source.file.name))
    self = Archive.Indexed()
    self.load()
    print("Successfuly read {:d} members.".format(len(self['members'])))

    # TODO: enumerate all objects that are dll imports
    # TODO: enumerate all objects that are actual object files

    #print('Enumerating all members using view interface...')
    #for index in range(self.getmembercount()):
    #    print(self.getmember(index).load())
    #    print(ptypes.utils.hexdump(self.getmemberdata(index)))
    sys.exit(0)
