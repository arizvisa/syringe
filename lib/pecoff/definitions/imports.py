import ptypes,headers
from ptypes import pstruct,parray,pbinary,pstr,dyn,utils
from __base__ import *
import array

class IMAGE_IMPORT_NAME_TABLE_ORDINAL(pbinary.struct):
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (15, 'Zero'),
        (16, 'Ordinal Number'),
    ]
    def load(self):
        self.source.seek( self.getoffset() )
        string = self.source.consume(4)
        return self.deserialize_stream(reversed(string))

    def get(self):
        hint = int(self['Ordinal Number'])
        return (hint, 'Ordinal%d'% hint)      # microsoft-convention

class IMAGE_IMPORT_NAME_TABLE_NAME(pbinary.struct):
    _fields_ = [
        (1, 'OrdinalFlag'),
        (31, 'Name'),
    ]
    def load(self):
        self.source.seek( self.getoffset() )
        string = self.source.consume(4)
        return self.deserialize_stream(reversed(string))

    def get(self):
        offset = headers.RelativeAddress(self, int(self['Name']))
        return self.newelement(IMAGE_IMPORT_HINT, 'ImportName', offset).load().get()

class IMAGE_IMPORT_NAME_TABLE_ENTRY(dyn.union):
    root = dyn.block(4)
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL, 'Ordinal'),
    ]

#    def __repr__(self):
#        if int(self['Name']['OrdinalFlag']) == 1:
#            return 'Ordinal -> %s'% repr(self['Ordinal'])
#        return 'Name -> %s'% repr(self['Name'])

    def get(self):
        '''Will return a tuple of (iat index, name)'''
        if int(self['Name']['OrdinalFlag']) == 1:
            return self['Ordinal'].get()
        return self['Name'].get()

#class IMAGE_IMPORT_ADDRESS_TABLE(dyn.array(addr_t,0)): pass
class IMAGE_IMPORT_ADDRESS_TABLE(parray.terminated):
    _object_ = addr_t
    def isTerminator(self, value):
        return int(value) == 0

class IMAGE_IMPORT_NAME_TABLE(parray.terminated):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY

    def isTerminator(self, v):
        if int(v['Name']['Name']) == 0:
            return True
        return False

class IMAGE_IMPORT_HINT(pstruct.type):
    _fields_ = [
        ( word, 'Hint' ),
        ( pstr.szstring, 'String' ),
        ( dyn.align(2), 'Padding' )
    ]

    if False:
        def size(self):
            # we're padded to be aligned along an even boundary
            l = super(IMAGE_IMPORT_HINT, self).size()
            return [l, l+1][l&1]

    def get(self):
        return ( int(self['Hint']), self['String'].get() )

class IMAGE_IMPORT_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        ( dyn.opointer(IMAGE_IMPORT_NAME_TABLE, headers.RelativeAddress), 'INT'),
        ( TimeDateStamp, 'TimeDateStamp' ),
        ( dword, 'ForwarderChain' ),
        ( dyn.opointer(pstr.szstring, headers.RelativeAddress), 'Name'),
#        ( dyn.opointer(lambda s: dyn.clone(IMAGE_IMPORT_ADDRESS_TABLE, length=len(s.parent['INT'].d.load())), headers.RelativeAddress), 'IAT')
        ( dyn.opointer(IMAGE_IMPORT_ADDRESS_TABLE, headers.RelativeAddress), 'IAT')
    ]

    def links(self):
        return set(['INT', 'Name', 'IAT'])

    def fetchimports(self):
        '''[(hint,importname,importtableaddress),...]'''
        address = int(self['IAT'])
        NtHeader = self.getparent(headers.NtHeader)
        section = NtHeader['Sections'].getsectionbyaddress(address)
        data = array.array('c',section.get().load().serialize())

        sectionva = int(section['VirtualAddress'])
        nametable = int(self['INT'])-sectionva

        while nametable < len(data):
            # get name
            name = reduce(lambda total,x: ord(x) + total*0x100, reversed(data[nametable:nametable+4]), 0)
            nametable += 4

            # if end of names
            if name == 0:
                return

            # ordinal
            if name & 0x80000000:
                hint = name & 0xffff
                yield (hint, 'Ordinal%d'% hint, address)
                address += 4
                continue

            # string
            p = (name & 0x7fffffff) - sectionva
            hint = reduce(lambda total,x: ord(x) + total*0x100, reversed(data[p:p+2]), 0)
            yield (hint, utils.strdup(data[p+2:].tostring()), address)
            address += 4

        raise ValueError("Terminated reading imports due to being out of input at %x"% address)

class IMAGE_IMPORT_DIRECTORY(parray.terminated):
    _object_ = IMAGE_IMPORT_DIRECTORY_ENTRY

    def isTerminator(self, v):
        total = 0
        for n in v.serialize():
            total += ord(n)
        return [True, False][total > 0]

    def walk(self):
        for x in self[:-1]:
            yield x
        return
