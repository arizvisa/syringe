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

class _IMAGE_IMPORT_NAME_TABLE_ORDINAL(pbinary.struct):
    byteorder = ptypes.config.byteorder.bigendian

    def getOrdinal(self):
        """Returns (Ordinal Hint, Ordinal String)"""
        hint = self['Ordinal Number']
        return (hint, 'Ordinal%d'% hint)      # microsoft-convention

    def summary(self):
        return repr(self.getOrdinal())

class IMAGE_IMPORT_NAME_TABLE_ORDINAL32(_IMAGE_IMPORT_NAME_TABLE_ORDINAL):
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (15, 'Zero'),
        (16, 'Ordinal Number'),
    ]
class IMAGE_IMPORT_NAME_TABLE_ORDINAL64(_IMAGE_IMPORT_NAME_TABLE_ORDINAL):
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (47, 'Zero'),
        (16, 'Ordinal Number'),
    ]
IMAGE_IMPORT_NAME_TABLE_ORDINAL = IMAGE_IMPORT_NAME_TABLE_ORDINAL32 if ptypes.Config.integer.size == 4 else IMAGE_IMPORT_NAME_TABLE_ORDINAL64

class _IMAGE_IMPORT_NAME_TABLE_NAME(pbinary.struct):
    byteorder = ptypes.config.byteorder.bigendian

    def dereference(self):
        """Dereferences Name into it's IMAGE_IMPORT_HINT structure"""
        parent = self.getparent(IMAGE_IMPORT_DIRECTORY)
        offset = headers.calculateRelativeAddress(parent, self['Name'])
        return self.p.p.new(IMAGE_IMPORT_HINT, __name__='ImportName', offset=offset)

    # set all the required attributes so that this is faking a ptype.pointer_t
    d = property(fget=lambda s,**a: s.dereference(**a))
    deref = lambda s,**a: s.dereference(**a)

    def getName(self):
        """Returns (Import Hint, Import String)"""
        if self['Name'] != 0:
            res = self.deref().li
            return (res.hint(), res.str())
        return (0, None)

    def summary(self):
        hint,string = self.getName()
        return '({:d}, {:s})'.format(hint, repr(string) if string is None else '"%s"'%string)

class IMAGE_IMPORT_NAME_TABLE_NAME32(_IMAGE_IMPORT_NAME_TABLE_NAME):
    _fields_ = [
        (1, 'OrdinalFlag'),
        (31, 'Name'),
    ]
class IMAGE_IMPORT_NAME_TABLE_NAME64(_IMAGE_IMPORT_NAME_TABLE_NAME):
    _fields_ = [
        (1, 'OrdinalFlag'),
        (32, 'Zero'),
        (31, 'Name'),
    ]
IMAGE_IMPORT_NAME_TABLE_NAME = IMAGE_IMPORT_NAME_TABLE_NAME32 if ptypes.Config.integer.size == 4 else IMAGE_IMPORT_NAME_TABLE_NAME64

class _IMAGE_IMPORT_NAME_TABLE_ENTRY(dyn.union):
    def ordinalQ(self):
        res = self.object.int() & 1<<(8*self.object.size()-1)
        return bool(res)

    def summary(self):
        if self.ordinalQ():
            return 'Ordinal -> '+ self['Ordinal'].summary()
        return 'Name -> '+ self['Name'].summary()

    def getImport(self):
        '''Will return a tuple of (iat index, name)'''
        if self.ordinalQ() == 1:
            return self['Ordinal'].getOrdinal()
        return self['Name'].getName()

class IMAGE_IMPORT_NAME_TABLE_ENTRY32(_IMAGE_IMPORT_NAME_TABLE_ENTRY):
    root = uint32
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME32, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL32, 'Ordinal'),
    ]
class IMAGE_IMPORT_NAME_TABLE_ENTRY64(_IMAGE_IMPORT_NAME_TABLE_ENTRY):
    root = uint64
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME64, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL64, 'Ordinal'),
    ]
IMAGE_IMPORT_NAME_TABLE_ENTRY = IMAGE_IMPORT_NAME_TABLE_ENTRY32 if ptypes.Config.integer.size == 4 else IMAGE_IMPORT_NAME_TABLE_ENTRY64

class _IMAGE_IMPORT_ADDRESS_TABLE(parray.terminated):
    def isTerminator(self, value):
        return value.num() == 0 if self.length is None else self.length < len(self.value)

class IMAGE_IMPORT_ADDRESS_TABLE32(_IMAGE_IMPORT_ADDRESS_TABLE):
    _object_ = uint32
class IMAGE_IMPORT_ADDRESS_TABLE64(_IMAGE_IMPORT_ADDRESS_TABLE):
    _object_ = uint64
IMAGE_IMPORT_ADDRESS_TABLE = IMAGE_IMPORT_ADDRESS_TABLE32 if ptypes.Config.integer.size == 4 else IMAGE_IMPORT_ADDRESS_TABLE64

class _IMAGE_IMPORT_NAME_TABLE(parray.terminated):
    _object_ = uint32
    def isTerminator(self, value):
        return True if int(value['Name']['Name']) == 0 else False

class IMAGE_IMPORT_NAME_TABLE32(_IMAGE_IMPORT_NAME_TABLE):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY32
class IMAGE_IMPORT_NAME_TABLE64(_IMAGE_IMPORT_NAME_TABLE):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY64
IMAGE_IMPORT_NAME_TABLE = IMAGE_IMPORT_NAME_TABLE32 if ptypes.Config.integer.size == 4 else IMAGE_IMPORT_NAME_TABLE64

class IMAGE_IMPORT_DIRECTORY_ENTRY(pstruct.type):
    def __IAT(self):
        res = IMAGE_IMPORT_ADDRESS_TABLE64 if self.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_ADDRESS_TABLE32
        if self.source in [getattr(ptypes.provider,'Ida',None)]:
            entry = self.getparent(IMAGE_IMPORT_DIRECTORY_ENTRY)
            int = entry['INT'].li.d.l
            return dyn.clone(res, length=len(int))
        return res

    _fields_ = [
        ( virtualaddress(lambda s: IMAGE_IMPORT_NAME_TABLE64 if s.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_NAME_TABLE32), 'INT'),  # FIXME
        ( TimeDateStamp, 'TimeDateStamp' ),
        ( dword, 'ForwarderChain' ),
        ( virtualaddress(pstr.szstring), 'Name'),
        ( virtualaddress(__IAT), 'IAT')
    ]

    def iterate(self):
        '''[(hint,importname,importtableaddress),...]'''
        header = self.getparent(Header)
        nametable, addresstable = self['INT'], self['IAT']

        section = header['Sections'].getsectionbyaddress(addresstable.int())
        sectionva, data = section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())

        for name, address in zip(nametable.d.l[:-1], addresstable.d.l[:-1]):
            if name.ordinalQ():
                hint = name.object.int() & 0xffff
                yield hint, 'Ordinal{:d}'.format(hint), address.getoffset()
                continue
            p = name['name']['name'] - sectionva
            hint =  data[p] | data[p+1]*0x100
            yield hint, utils.strdup(data[p+2:].tostring()), address.getoffset()
        return

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
    def __IAT(self):
        if self.source in [getattr(ptypes.provider,'Ida',None)]:
            entry = self.getparent(IMAGE_DELAYLOAD_DIRECTORY_ENTRY)
            int = entry['DINT'].li.d.l
            return dyn.clone(IMAGE_IMPORT_ADDRESS_TABLE, length=len(int))
        return IMAGE_IMPORT_ADDRESS_TABLE
    _fields_ = [
        ( dword, 'Attributes'),
        ( virtualaddress(pstr.szstring), 'Name'),
        ( virtualaddress(dword), 'ModuleHandle'),
        ( virtualaddress(__IAT), 'DIAT'),
        ( virtualaddress(IMAGE_IMPORT_NAME_TABLE), 'DINT'),
        ( virtualaddress(__IAT), 'BDIAT' ),
        ( virtualaddress(__IAT), 'UDAT'),
        ( TimeDateStamp, 'TimeStamp'),
    ]

class IMAGE_DELAYLOAD_DIRECTORY(parray.block):
    _object_ = IMAGE_DELAYLOAD_DIRECTORY_ENTRY
    def isTerminator(self, v):
        return False if sum(ord(n) for n in v.serialize()) > 0 else True

    def iterate(self):
        for x in self[:-1]:
            yield x
        return

