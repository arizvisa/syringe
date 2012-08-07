import ptypes,headers
from ptypes import pstruct,parray,ptype,dyn,pstr,utils
from __base__ import *
import struct

from headers import virtualaddress

# FuncPointer can also point to some code too
#class FuncPointer(virtualaddress(ptype.type, headers.RelativeAddress)): pass
class FuncPointer(virtualaddress(pstr.szstring)):
    def getModuleName(self):
        module,name = self.d.l.get().split('.', 1)
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
        ( dword, 'TimeDateStamp' ),
        ( word, 'MajorVersion' ),
        ( word, 'MinorVersion' ),
        ( dword, 'Name' ),
        ( dword, 'Base' ),
        ( dword, 'NumberOfFunctions' ),
        ( dword, 'NumberOfNames' ),
        ( _p_AddressOfFunctions, 'AddressOfFunctions' ),
        ( _p_AddressOfNames, 'AddressOfNames' ),
        ( _p_AddressOfNameOrdinals, 'AddressOfNameOrdinals' )
    ]

    def getNames(self):
        Header = headers.findHeader(self)
        section = Header['Sections'].getsectionbyaddress(self['AddressOfNames'].int())

        sectionva = section['VirtualAddress'].int()
        offsets = [ (x.int()-sectionva) for x in self['AddressOfNames'].d.load() ]

        data = section.get().load().serialize()

        names = []
        for x in offsets:
            res = utils.strdup(data[x:])
            names.append(res)
        return names

    def getNameOrdinals(self):
        Header = headers.findHeader(self)
        address = self['AddressOfNameOrdinals'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva

        data = section.get().load().serialize()

        block = data[offset: offset + 2*self['NumberOfNames'].int()]
        return [ struct.unpack_from('H', block, offset)[0] for offset in xrange(0, len(block), 2) ]

    def getExportAddressTable(self):
        Header = headers.findHeader(self)
        exportdirectory = self.parent.parent

        address = self['AddressOfFunctions'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva
        data = section.get().load().serialize()

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
        ofs,eat = self.getExportAddressTable()
        try:
            for name,ordinal in zip(self.getNames(), self.getNameOrdinals()):
                value = eat[ordinal]
                ordinalstring = 'Ordinal%d'% (ordinal + self['Base'].int())
                yield (ofs, ordinal, name, ordinalstring, value)
                ofs += 4

        except KeyError:
            print 'Error resolving exports...quitting early.'
            # XXX: this one's for you shunimpl.dll
            pass
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
