import ptypes
from ptypes import pstruct,parray,pbinary,pstr,dyn,utils
from ..__base__ import *

from . import headers
from .headers import virtualaddress

import array

class IMAGE_IMPORT_HINT(pstruct.type):
    _fields_ = [
        ( word, 'Hint' ),
        ( pstr.szstring, 'String' ),
        ( dyn.align(2), 'Padding' )
    ]

    def hint(self):
        return self['Hint'].li.num()

    def str(self):
        return self['String'].li.str()

class IMAGE_IMPORT_NAME_TABLE_ORDINAL(pbinary.struct):
    byteorder = ptypes.config.byteorder.bigendian
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (15, 'Zero'),
        (16, 'Ordinal Number'),
    ]

    def getOrdinal(self):
        """Returns (Ordinal Hint, Ordinal String)"""
        hint = self['Ordinal Number']
        return (hint, 'Ordinal%d'% hint)      # microsoft-convention

    def summary(self):
        return repr(self.getOrdinal())

class IMAGE_IMPORT_NAME_TABLE_NAME(pbinary.struct):
    byteorder = ptypes.config.byteorder.bigendian
    _fields_ = [
        (1, 'OrdinalFlag'),
        (31, 'Name'),
    ]

    def deref(self):
        """Dereferences Name into it's IMAGE_IMPORT_HINT structure""" 
        offset = headers.calculateRelativeAddress(self, self['Name'])
        return self.p.p.new(IMAGE_IMPORT_HINT, __name__='ImportName', offset=offset)

    def getName(self):
        """Returns (Import Hint, Import String)"""
        res = self.deref().li
        return (res.hint(), res.str())

    def summary(self):
        return repr(self.getName())

class IMAGE_IMPORT_NAME_TABLE_ENTRY(dyn.union):
    root = dyn.block(4)
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL, 'Ordinal'),
    ]

    def summary(self):
        if self['Name']['OrdinalFlag'] == 1:
            return 'Ordinal -> %r'% (self['Ordinal'].summary(),)
        return 'Name -> %r'% (self['Name'].summary(),)

    def getImport(self):
        '''Will return a tuple of (iat index, name)'''
        if self['Name']['OrdinalFlag'].num() == 1:
            return self['Ordinal'].getOrdinal()
        return self['Name'].getName()

class IMAGE_IMPORT_ADDRESS_TABLE(parray.terminated):
    _object_ = addr_t
    def isTerminator(self, value):
        return value.num() == 0

class IMAGE_IMPORT_NAME_TABLE(parray.terminated):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY

    def isTerminator(self, v):
        return True if int(v['Name']['Name']) == 0 else False

class IMAGE_IMPORT_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        ( virtualaddress(IMAGE_IMPORT_NAME_TABLE), 'INT'),
        ( TimeDateStamp, 'TimeDateStamp' ),
        ( dword, 'ForwarderChain' ),
        ( virtualaddress(pstr.szstring), 'Name'),
        ( virtualaddress(IMAGE_IMPORT_ADDRESS_TABLE), 'IAT')
    ]

    def iterate(self):
        '''[(hint,importname,importtableaddress),...]'''
        address = self['IAT'].num()
        header = self.getparent(Header)
        section = header['Sections'].getsectionbyaddress(address)
        data = array.array('c',section.data().l.serialize())

        sectionva = section['VirtualAddress'].num()
        nametable = self['INT'].num()-sectionva

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
        return False if sum(ord(n) for n in v.serialize()) > 0 else True

    def iterate(self):
        for x in self[:-1]:
            yield x
        return

    def search(self, key):
        '''
        search the import list for an import dll that matches key
        return the rva
        '''
        for n in self.iterate():
            if key == n['Name'].d.li.str():
                return n
            continue
        raise KeyError(key)

class IMAGE_DELAYLOAD_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        ( dword, 'Attributes'),
        ( virtualaddress(pstr.szstring), 'Name'),
        ( virtualaddress(dword), 'ModuleHandle'),
        ( virtualaddress(IMAGE_IMPORT_ADDRESS_TABLE), 'DIAT'),
        ( virtualaddress(IMAGE_IMPORT_NAME_TABLE), 'DINT'),
        ( virtualaddress(IMAGE_IMPORT_ADDRESS_TABLE), 'BDIAT' ),
        ( virtualaddress(IMAGE_IMPORT_ADDRESS_TABLE), 'UDAT'),
        ( TimeDateStamp, 'TimeStamp'),
    ]
