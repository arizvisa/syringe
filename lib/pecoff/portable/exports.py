import ptypes
from ptypes import pstruct,parray,ptype,dyn,pstr,utils
from ..__base__ import *

from . import headers
from .headers import virtualaddress

import itertools,array,logging

# FuncPointer can also point to some code too
class FuncPointer(virtualaddress(pstr.szstring, type=dword)):
    def GetModuleName(self):
        module,name = self.d.li.str().split('.', 1)
        if name.startswith('#'):
            name = 'Ordinal%d'% int(name[1:])
        return module.lower() + '.dll',name

class NamePointer(virtualaddress(pstr.szstring, type=dword)): pass
class Ordinal(word):
    def GetExportIndex(self):
        '''Returns the Ordinal's index for things'''
        res = self.getparent(IMAGE_EXPORT_DIRECTORY)
        return self.int() - res['Base'].int()

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

    def GetNames(self):
        """Returns a list of all the export names"""
        Header = headers.locateHeader(self)
        cache, sections = {}, Header['Sections']

        res = []
        for va in self['AddressOfNames'].d.l:
            section = sections.getsectionbyaddress(va.int())
            sectionva, data = cache[section.getoffset()] if section.getoffset() in cache else cache.setdefault(section.getoffset(), (section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())))
            nameofs = va.int() - sectionva
            res.append(utils.strdup(data[nameofs:].tostring()))
        return res

    def GetNameOrdinals(self):
        """Returns a list of all the Ordinals for each export"""
        Header = headers.locateHeader(self)
        address = self['AddressOfNameOrdinals'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        base, offset = self['Base'].int(), address - sectionva

        data = section.data().load().serialize()

        block = data[offset: offset + 2*self['NumberOfNames'].int()]
        return [base+ordinal for ordinal in array.array('H', block)]

    def GetExportAddressTable(self):
        """Returns (export address table offset,[virtualaddress of each export]) from the export address table"""
        Header = headers.locateHeader(self)
        ExportDirectory = self.getparent(headers.IMAGE_DATA_DIRECTORY)

        address = self['AddressOfFunctions'].int()
        section = Header['Sections'].getsectionbyaddress(address)

        sectionva = section['VirtualAddress'].int()
        offset = address - sectionva
        data = section.data().l.serialize()

        block = data[offset: offset + 4*self['NumberOfFunctions'].int()]
        return address, array.array('L', block)

    def iterate(self):
        """For each export, yields (rva offset, hint, name, ordinalname, entrypoint, forwardedrva)"""
        cls = self.__class__
        ExportDirectory = self.getparent(headers.IMAGE_DATA_DIRECTORY)
        Header, Base = headers.locateHeader(self), self['Base'].int()

        # our section data cache
        cache, sections = {}, Header['Sections']

        # grab everything that's important
        aof, aon, aono = self['AddressOfFunctions'], self['AddressOfNames'], self['AddressOfNameOrdinals']

        ## export address table
        if aof.int() > 0:
            # cache the section the eat is contained in since we need it anyways
            section = sections.getsectionbyaddress(aof.int())
            cache.setdefault(section.getoffset(), (section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())))

            # convert the aof into an array that's wikiwiki
            data = aof.d.l.cast(dyn.array(dword, len(aof.d)))
            eat = array.array('L', data.l.serialize())

            # check that the aof is within the bounds of the section, warn the user despite supporting it anyways
            if any(not section.containsaddress(ea) for ea in (aof.int(), aof.int() + 4*self['NumberOfFunctions'].int())):
                logging.warn("{:s} : Export Address Table goes outside bounds of designated section. ({:#x} <= {:#x}{:+#x} < {:#x})".format('.'.join((cls.__module__, cls.__name__)), section['VirtualAddress'].int(), aof.int(), aof.int() + 4*self['NumberOfFunctions'].int(), section['VirtualAddress'].int() + section['VirtualSize'].int()))
        else:
            logging.warn("{:s} : No export addresses found in IMAGE_EXPORT_DIRECTORY. ({:s})".format('.'.join((cls.__module__, cls.__name__)), aof.summary()))
            eat = array.array('L', [])

        ## name ordinal table
        if aono.int() > 0:
            # cache the section the aono is contained in since we need it anyways
            section = sections.getsectionbyaddress(aono.int())
            cache.setdefault(section.getoffset(), (section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())))

            # convert the aono into an array that's also quick
            data = aono.d.l.cast(dyn.array(word, len(aono.d)))
            no = array.array('H', data.l.serialize())

            # check that the aono is within the bounds of the section, warn the user despite supporting it anyways
            if any(not section.containsaddress(ea) for ea in (aono.int(), aono.int() + 2*self['NumberOfNames'].int())):
                logging.warn("{:s} : Export Name Ordinal Table goes outside bounds of designated section. ({:#x} <= {:#x}{:+#x} < {:#x})".format('.'.join((cls.__module__, cls.__name__)), section['VirtualAddress'].int(), aono.int(), aono.int() + 2*self['NumberOfNames'].int(), section['VirtualAddress'].int() + section['VirtualSize'].int()))
        else:
            logging.warn("{:s} : No Export Name Ordinal Table in IMAGE_EXPORT_DIRECTORY. ({:s})".format('.'.join((cls.__module__, cls.__name__)), aono.summary()))
            no = array.array('H', [])

        # check the name table
        if aon.int() == 0:
            logging.warn("{:s} : No Export Name Table in IMAGE_EXPORT_DIRECTORY. ({:s})".format('.'.join((cls.__module__, cls.__name__)), aon.summary()))
            nt = []
        else:
            nt = aon.d.l

        # now we can start returning things to the user
        va = headers.calculateRelativeOffset(self, aof.int())
        for nameva, ordinal in map(None, nt, no):

            # grab the name if we can
            if nameva is None:
                name = None
            else:
                section = sections.getsectionbyaddress(nameva.int())
                sectionva, data = cache[section.getoffset()] if section.getoffset() in cache else cache.setdefault(section.getoffset(), (section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())))
                nameofs = nameva.int() - sectionva
                name = utils.strdup(data[nameofs:].tostring())

            # grab the ordinal if we can
            if ordinal is None:
                forwarded, value = None, None

            elif 0 <= ordinal <= len(eat):
                # this is inside the export directory, so it's a forwardedrva
                if ExportDirectory.containsaddress(eat[ordinal]):
                    section = sections.getsectionbyaddress(eat[ordinal])
                    sectionva, data = cache[section.getoffset()] if section.getoffset() in cache else cache.setdefault(section.getoffset(), (section['VirtualAddress'].int(), array.array('B', section.data().l.serialize())))
                    forwarded, value = utils.strdup(data[eat[ordinal] - sectionva:].tostring()), None

                # otherwise, it's a valid address
                else:
                    forwarded, value = None, eat[ordinal]

            # this ordinal is outside the export address table, although
            # we can read from the file to deal with these sort of fuxed
            # things... this is currently unsupported by pecoff
            else:
                logging.warning("{:s} : Error resolving export address for {:s} : !({:d} <= {:d} < {:d})".format('.'.join((cls.__module__, cls.__name__)), name, 0, ordinal, len(eat)))
                forwarded, value = None, None

            ordinalstring = None if ordinal is None else "Ordinal{:d}".format(ordinal + Base)
            yield va, ordinal, name, ordinalstring, value, forwarded
            va += 4
        return

    def search(self, key):
        '''Search the export list for an export that matches key.

        Return it's rva.
        '''
        for offset, ordinal, name, ordinalstring, value, forwardedrva in self.iterate():
            if key == ordinal or key == name or key == ordinalstring or key == forwardedrva:
                return value
            continue
        raise KeyError(key)
