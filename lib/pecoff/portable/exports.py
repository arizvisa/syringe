import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils
from ..__base__ import *

from . import headers
from .headers import virtualaddress

import struct,logging

# FuncPointer can also point to some code too
class FuncPointer(virtualaddress(pstr.szstring, type=dword)):
    def getModuleName(self):
        module,name = self.d.li.str().split('.', 1)
        if name.startswith('#'):
            name = 'Ordinal%d'% int(name[1:])
        return module.lower() + '.dll',name

class NamePointer(virtualaddress(pstr.szstring, type=dword)): pass
class Ordinal(word):
    def getExportIndex(self):
        '''Returns the Ordinal's index for things'''
        return self.int() - self.parent.parent.parent['Base'].int()

class IMAGE_EXPORT_DIRECTORY(pstruct.type):
    _p_AddressOfFunctions =    lambda self: virtualaddress(dyn.array(FuncPointer, self['NumberOfFunctions'].li.int()), type=dword)
    _p_AddressOfNames =        lambda self: virtualaddress(dyn.array(NamePointer, self['NumberOfNames'].li.int()), type=dword)
    _p_AddressOfNameOrdinals = lambda self: virtualaddress(dyn.array(Ordinal,     self['NumberOfNames'].li.int()), type=dword)

    def __ExportData(self):
        res = sum(self[n].li.size() for _,n in self._fields_[:-1])
        return dyn.block(self.blocksize() - res)

    _fields_ = [
        ( dword, 'Flags' ),
        ( TimeDateStamp, 'TimeDateStamp' ),
        ( word, 'MajorVersion' ),
        ( word, 'MinorVersion' ),
        ( virtualaddress(pstr.szstring, type=dword), 'Name' ),
        ( dword, 'Base' ),
        ( dword, 'NumberOfFunctions' ),
        ( dword, 'NumberOfNames' ),
        ( _p_AddressOfFunctions, 'AddressOfFunctions' ),
        ( _p_AddressOfNames, 'AddressOfNames' ),
        ( _p_AddressOfNameOrdinals, 'AddressOfNameOrdinals' ),
        ( __ExportData, 'ExportData'),
    ]

    def getNames(self):
        """Returns a list of all the export names"""
        Header = headers.locateHeader(self)
        section = Header['Sections'].getsectionbyaddress(self['AddressOfNames'].int())

        sectionva = section['VirtualAddress'].int()
        offsets = [ (x.int()-sectionva) for x in self['AddressOfNames'].d.load() ]
        data = section.data().load().serialize()

        names = []
        for x in offsets:
            names.append(utils.strdup(data[x:]))
        return names

    def getNameOrdinals(self):
        """Returns a list of all the Ordinals for each export"""
        Header = headers.locateHeader(self)
        address = self['AddressOfNameOrdinals'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva

        data = section.data().load().serialize()

        block = data[offset: offset + 2*self['NumberOfNames'].int()]
        return [ struct.unpack_from('H', block, offset)[0] for offset in xrange(0, len(block), 2) ]

    def getExportAddressTable(self):
        """Returns (export address table offset,[virtualaddress of each export]) from the export address table"""
        Header = headers.locateHeader(self)
        exportdirectory = self.parent.parent

        address = self['AddressOfFunctions'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva
        data = section.data().load().serialize()

        block = data[offset: offset + 4*self['NumberOfFunctions'].int()]
        addresses = ( struct.unpack_from('L', block, offset)[0] for offset in xrange(0, len(block), 4) )

        result = []
        for i,va in enumerate(addresses):
            result.append( utils.strdup(data[va-sectionva:]) if exportdirectory.contains(va) else va )
        return address,result

    def iterate(self):
        """For each export, yields (offset of export, ordinal, name, ordinalString, virtualaddress)"""
        if 0 in (self['AddressOfNames'].int(),self['AddressOfNameOrdinals'].int()):
            base = self['Base'].int()
            ofs,eat = self.getExportAddressTable()
            for i,e in enumerate(eat):
                yield ofs,i+base,'','',e
                ofs += 4
            return

        ofs,eat = self.getExportAddressTable()
        for name,ordinal in zip(self.getNames(), self.getNameOrdinals()):
            if 0 <= ordinal <= len(eat):
                value = eat[ordinal]
            else:
                logging.warning("Error resolving exports for %s : %d", name, ordinal)
                value = 0
            ordinalstring = 'Ordinal%d'% (ordinal + self['Base'].int())
            yield (ofs, ordinal, name, ordinalstring, value)
            ofs += 4
        return

    def search(self, key):
        '''Search the export list for an export that matches key.

        Return it's rva.
        '''
        for ofs,ordinal,name,ordinalstring,value in self.iterateExports():
            if key == ordinal or key == name or key == ordinalstring:
                return value
            continue
        raise KeyError(key)
