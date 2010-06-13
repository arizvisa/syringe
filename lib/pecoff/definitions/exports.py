import ptypes,headers
from ptypes import pstruct,parray,ptype,dyn,pstr,utils
from __base__ import *
import struct

# FuncPointer can also point to some code too
#class FuncPointer(dyn.rpointer(ptype.type, headers.Header_RelativeAddress)): pass
class FuncPointer(dyn.rpointer(pstr.szstring, headers.Header_RelativeAddress)):
    def getModuleName(self):
        module,name = self.d.l.get().split('.', 1)
        if name.startswith('#'):
            name = 'Ordinal%d'% int(n[1:])
        return module.lower() + '.dll',name

class NamePointer(dyn.rpointer(pstr.szstring, headers.Header_RelativeAddress)): pass
class Ordinal(word):
    def getExportIndex(self):
        '''Returns the Ordinal's index for things'''
        return int(self) - int(self.parent.parent.parent['Base'])

class IMAGE_EXPORT_DIRECTORY(pstruct.type):
    _p_AddressOfFunctions =    lambda self: dyn.rpointer(dyn.array(FuncPointer, int(self['NumberOfFunctions'].load())), headers.Header_RelativeAddress)
    _p_AddressOfNames =        lambda self: dyn.rpointer(dyn.array(NamePointer, int(self['NumberOfNames'].load())), headers.Header_RelativeAddress)
    _p_AddressOfNameOrdinals = lambda self: dyn.rpointer(dyn.array(Ordinal,     int(self['NumberOfNames'].load())), headers.Header_RelativeAddress)

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
        section = Header['Sections'].getsectionbyaddress(int(self['AddressOfNames']))

        sectionva = int(section['VirtualAddress'])
        offsets = [ (int(x)-sectionva) for x in self['AddressOfNames'].d.load() ]

        data = section.get().load().serialize()

        names = []
        for x in offsets:
            res = utils.strdup(data[x:])
            names.append(res)
        return names

    def getNameOrdinals(self):
        Header = headers.findHeader(self)
        address = int(self['AddressOfNameOrdinals'])
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = int(section['VirtualAddress'])
        offset = address - sectionva

        data = section.get().load().serialize()

        block = data[offset: offset + 2*int(self['NumberOfNames'])]
        return [ struct.unpack_from('H', block, offset)[0] for offset in xrange(0, len(block), 2) ]

    def getExportAddressTable(self):
        Header = headers.findHeader(self)
        exportdirectory = self.parent.parent

        address = int(self['AddressOfFunctions'])
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = int(section['VirtualAddress'])
        offset = address - sectionva
        data = section.get().load().serialize()

        block = data[offset: offset + 4*int(self['NumberOfFunctions'])]
        addresses = ( struct.unpack_from('L', block, offset)[0] for offset in xrange(0, len(block), 4) )

        result = []
        for i,va in enumerate(addresses):
            if exportdirectory.contains(va):
                offset = va-sectionva
                result.append( utils.strdup(data[offset:]) )
                continue
            result.append( va )
        return result

    def enumerateAllExports(self):
        result = []
        eat = self.getExportAddressTable()
        try:
            for name,ordinal in zip(self.getNames(), self.getNameOrdinals()):
                value = eat[ordinal]
                ordinalstring = 'Ordinal%d'% (ordinal + int(self['Base']))
                yield (ordinal, name, ordinalstring, value)

        except KeyError:
            print 'Error resolving exports...quitting early.'
            # XXX: this one's for you shunimpl.dll
            pass
        return

    if False:
        def getFunctions(self):
            return list(self.getExportAddressTable())

        def lookupByName(self):
            result, eat = [], self.getFunctions()
            for name,ordinal in zip( self.getNames(), self.getNameOrdinals() ):
                v = eat[ordinal]
                result.append((name, (ordinal, v)))
            return result

    if False:
        def lookupByOrdinal(self):
            result = []
            for index,va in enumerate( self.iterateExportAddressTable ):
                result.append((index+int(self['Base']), va))
            return result


    if False:
        def getNameLookup(self):
            '''returns a list of all symbols and their rva's'''    
            result = []
            eat = self.getFunctions()
            for name,ordinal in zip( self.getNames(), self.getNameOrdinals() ):
    #            print name,hex(int(eat[ordinal])),ordinal
                result.append((name, eat[ordinal]))
            return result

        def getOrdinalLookup(self):
            '''returns a list of all ordinals and their rva's'''    
            result = []
            eat = self.getFunctions()
            for index,va in enumerate(eat):
                result.append((index+int(self['Base']), va))
            return result
