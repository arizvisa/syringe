import ptypes,headers
from ptypes import pstruct,parray,ptype,dyn,pstr,utils
from __base__ import *
import struct,logging

from headers import virtualaddress

# FuncPointer can also point to some code too
class FuncPointer(virtualaddress(pstr.szstring)):
    def getModuleName(self):
        module,name = self.d.l.str().split('.', 1)
        if name.startswith('#'):
            name = 'Ordinal%d'% int(name[1:])
        return module.lower() + '.dll',name

class NamePointer(virtualaddress(pstr.szstring)): pass
class Ordinal(word):
    def getExportIndex(self):
        '''Returns the Ordinal's index for things'''
        return self.int() - self.parent.parent.parent['Base'].int()

class IMAGE_EXPORT_DIRECTORY(pstruct.type):
    _p_AddressOfFunctions =    lambda self: virtualaddress(dyn.array(FuncPointer, self['NumberOfFunctions'].load().int()))
    _p_AddressOfNames =        lambda self: virtualaddress(dyn.array(NamePointer, self['NumberOfNames'].load().int()))
    _p_AddressOfNameOrdinals = lambda self: virtualaddress(dyn.array(Ordinal,     self['NumberOfNames'].load().int()))

    _fields_ = [
        ( dword, 'Flags' ),
        ( TimeDateStamp, 'TimeDateStamp' ),
        ( word, 'MajorVersion' ),
        ( word, 'MinorVersion' ),
        ( virtualaddress(pstr.szstring), 'Name' ),
        ( dword, 'Base' ),
        ( dword, 'NumberOfFunctions' ),
        ( dword, 'NumberOfNames' ),
        ( _p_AddressOfFunctions, 'AddressOfFunctions' ),
        ( _p_AddressOfNames, 'AddressOfNames' ),
        ( _p_AddressOfNameOrdinals, 'AddressOfNameOrdinals' )
    ]

    def getNames(self):
        Header = headers.locateHeader(self)
        section = Header['Sections'].getsectionbyaddress(self['AddressOfNames'].int())

        sectionva = section['VirtualAddress'].int()
        offsets = [ (x.int()-sectionva) for x in self['AddressOfNames'].d.load() ]

        data = section.data().load().serialize()

        names = []
        for x in offsets:
            res = utils.strdup(data[x:])
            names.append(res)
        return names

    def getNameOrdinals(self):
        Header = headers.locateHeader(self)
        address = self['AddressOfNameOrdinals'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva

        data = section.data().load().serialize()

        block = data[offset: offset + 2*self['NumberOfNames'].int()]
        return [ struct.unpack_from('H', block, offset)[0] for offset in xrange(0, len(block), 2) ]

    def getExportAddressTable(self):
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
            if exportdirectory.contains(va):
                offset = va-sectionva
                result.append( utils.strdup(data[offset:]) )
            else:
                result.append( va )
        return address,result

    def enumerateAllExports(self):
        result = []
        if 0 in (self['AddressOfNames'].num(),self['AddressOfNameOrdinals'].num()):
            base = self['Base'].num()
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
        '''
        search the export list for an export that wildly matches key to everything.
        return the rva
        '''
        for ofs,ordinal,name,ordinalstring,value in self.enumerateAllExports():
            if key == ordinal or key == name or key == ordinalstring:
                return value
            continue
        raise KeyError(key)
