import sys,ptypes
from ptypes import ptype,pstruct,pbinary,dyn,parray,bitmap,pint

from ..__base__ import *

import array

class MachineRelocation(ptype.definition):
    cache = {}

## Base Relocation class (Sub-class for each machine type)
class Relocation(pstruct.type):
    _fields_ = [
        (uint32, 'VirtualAddress'), # FIXME: this can be a virtualaddress(...) to the actual relocation
        (uint32, 'SymbolTableIndex'),
        #(uint16, 'Type')
    ]

    def summary(self):
        fields = [('VirtualAddress', lambda v: '%x'% v), ('SymbolTableIndex', int), ('Type', str)]
        res = ', '.join(['%s=%s'% (k,t(self[k])) for k,t in fields])
        return '{' + res + '}'

    def __relocate__(self, data, symbol, section, namespace):
        raise NotImplementedError

    def relocate(self, data, symboltable, namespace=None):
        '''
        data = a string
        symboltable = an array of symbols
        namespace = a dict for looking up symbol and segment values by name
        '''
        # FIXME: stupid fucking python and it's issues recursive module importing
        headers = sys.modules.get('pecoff.portable.headers', __import__('pecoff.portable.headers'))

        # find the symbol used by the relocation
        symbol = symboltable[self['SymbolTableIndex'].int()]

        # figure out the section our symbol and our relocation points into
        currentsection = self.getparent(headers.SectionTable)
        sectionarray = currentsection.getparent(headers.SectionTableArray)

        # if the symbol is undefined or absolute, then assume the current section
        symbolsectionnumber = symbol.getSectionIndex()
        if symbolsectionnumber is None:
            section = currentsection
        # otherwise use the symbol's section index
        else:
            section = sectionarray[symbolsectionnumber]

        # convert the data into an array that can be processed
        data = array.array('B', data)
        return self.__relocate__(data, symbol, section, namespace).tostring()

### Each relocation entry

## I386
class IMAGE_REL_I386(pint.enum, uint16):
    _values_ = [
        ('ABSOLUTE', 0x0000),
        ('DIR16', 0x0001),
        ('REL16', 0x0002),
        ('DIR32', 0x0006),
        ('DIR32NB', 0x0007),
        ('SEG12', 0x0009),
        ('SECTION', 0x000A),
        ('SECREL', 0x000B),
        ('TOKEN', 0x000C),
        ('SECREL7', 0x000D),
        ('REL32', 0x0014)
    ]

@MachineRelocation.define
class Relocation_I386(Relocation):
    type = Machine.byname('I386')

    _fields_ = Relocation._fields_[:] + [(IMAGE_REL_I386, 'Type')]

    def __relocate__(self, data, symbol, section, namespace=None):
        '''Apply relocations for the specified ``symbol`` to the ``data``.'''
        namespace = namespace or {}

        # figure out the relocation information
        relocationva, relocationtype = self['VirtualAddress'].int(), self['Type'].int()

        # figure out the symbol type
        storageclass = symbol['StorageClass'].int()

        # get the symbol name so that it can be looked up against the namespace
        name = symbol['Name'].str()

        # lookup the symbol's value in the namespace first...otherwise, use what was actually assigned in the symbol table
        value = namespace.get(name, symbol['Value'].int())

        # extract the value that's already encoded within the section's data
        result = ptypes.bitmap.zero
        generator = ( bitmap.new(ch, 8) for ch in data[relocationva : relocationva + 4] )
        for x in generator:
            result = bitmap.insert(result, x)
        result = bitmap.int(result)

        currentva = relocationva + 4

        # FIXME: figure out the machine type in order to determine the relocation types and how to apply them

        # XXX: this is only for x86
        # figure out where to get the relocation's value from based on the relocation type
        if section is None:       # externally defined
            result = value
        elif relocationtype == 0:
            pass
        # XXX: will these relocations work?
        elif relocationtype == 6:                                           # 32-bit VA
            result = (value+result)
        #    print '>',name,hex(result),targetsectionname,hex(namespace[targetsectionname])
        elif relocationtype == 0x14:                                        # 32-bit relative displacement
            result = (value+result+4) - (currentva)
            #raise NotImplementedError(relocationtype)
        elif relocationtype == 7:                                           # use real virtual address (???)
            result = value
        elif relocationtype in [0xA, 0xB]:                                  # [section index, offset from section]
            raise NotImplementedError(relocationtype)
        else:
            raise NotImplementedError(relocationtype)

        # calculate relocation and assign it into an array
        result, serialized = bitmap.new(result, 32), array.array('B','')
        while result[1] > 0:
            result, value = bitmap.consume(result, 8)
            serialized.append(value)

        # update segment data with new serialized relocation
        if len(serialized) != 4:
            raise AssertionError("Expected size of relocation was expected to be {:d} bytes : {:d} != {:d}".format(4, len(serialized), 4))
        data[relocationva : relocationva + len(serialized)] = serialized

        # we're done. so return it back to the user
        return data

## AMD64
class IMAGE_REL_AMD64(pint.enum, uint16):
    _values_ = [
        ('ABSOLUTE', 0x0000),
        ('ADDR64', 0x0001),
        ('ADDR32', 0x0002),
        ('ADDR32NB', 0x0003),
        ('REL32', 0x0004),
        ('REL32_1', 0x0005),
        ('REL32_2', 0x0006),
        ('REL32_3', 0x0007),
        ('REL32_4', 0x0008),
        ('REL32_5', 0x0009),
        ('SECTION', 0x000a),
        ('SECREL', 0x000b),
        ('SECREL7', 0x000c),
        ('TOKEN', 0x000d),
        ('SREL32', 0x000e),
        ('PAIR', 0x000f),
        ('SSPAN32', 0x0010),
    ]

@MachineRelocation.define
class Relocation_AMD64(Relocation):
    type = Machine.byname('AMD64')

    _fields_ = Relocation._fields_[:] + [(IMAGE_REL_AMD64, 'Type')]

    def __relocate__(self, data, symbol, section, namespace=None):
        '''Apply relocations for the specified ``symbol`` to the ``data``.'''
        # FIXME: Implement this
        return data

## per data directory relocations
class BaseRelocationEntry(pbinary.struct):
    _fields_ = [
        (4, 'Type'),
        (12, 'Offset'),
    ]

class BaseRelocationArray(parray.block):
    _object_ = pbinary.littleendian(BaseRelocationEntry)

class BaseRelocationBlock(ptype.block):
    def array(self):
        return self.cast(pbinary.new(BaseRelocationArray), blocksize=self.blocksize)
    def iterate(self):
        for res in iter(self.array()):
            yield res
        return

class IMAGE_BASERELOC_DIRECTORY_ENTRY(pstruct.type):
    _fields_ = [
        (uint32, 'Page RVA'),   # FIXME: this can be a virtualaddress(...) to the page
        (uint32, 'Size'),
        (lambda s: dyn.clone(BaseRelocationBlock, length=s['Size'].li.int()-8), 'Relocations'),
#        (lambda s: dyn.clone(pbinary.blockarray,_object_=BaseRelocationEntry, blockbits=lambda _:(s['Size'].li.int()-8)*8), 'Relocations')
#        (lambda s: dyn.clone(BaseRelocationArray, blocksize=lambda _:s['Size'].li.int()-8), 'Relocations')
    ]

    def fetchrelocations(self):
        block = self['Relocations'].serialize()
        relocations = array.array('H').fromstring(block)
        return [((v&0xf000)/0x1000, v&0x0fff) for v in relocations]

    def getrelocations(self, section):
        pageoffset = self['Page RVA'].int() - section['VirtualAddress'].int()
        if not (pageoffset >= 0 and pageoffset < section.getloadedsize()):
            raise AssertionError("Page Offset in RVA outside bounds of section : not(0 <= {:#x} < {:#x}) : Page RVA {:#x}, VA = {:#x}, Section = {:s}".format(pageoffset, section.getloadedsize(), self['Page RVA'].int(), section['VirtualAddress'].int(), section['Name'].str()))

        for type,offset in self.fetchrelocations():
            if type == 0:
                continue
            yield type,pageoffset+offset
        return

# yeah i really made this an object
class relocationtype(object):
    length = 0
    def read(self, string, offset):
        value = reversed( string[offset : offset+self.length] )
        result = reduce(lambda total,x: total*256 + ord(x), value, 0)
        return result

    def write(self, address, sectiondelta):
        raise NotImplementedError

    def _write(self, value):
        res = bitmap.new( value, self.length*8 )
        string = ''
        while res[1] > 0:
            res,value = bitmap.consume(res, 8)
            string += chr(value)
        return string

if False:       # deprecated because we would like to be able to separate segments from one another
    class relocation_1(relocationtype):
        length = 2
        def write(self, address, sectiondelta):
            value = address + (sectiondelta & 0xffff0000) / 0x10000
            return super(relocation_1, self)._write(value)

    class relocation_2(relocationtype):
        length = 2
        def write(self, address, sectiondelta):
            value = address + (sectiondelta & 0x0000ffff)
            return super(relocation_2, self)._write(value)

    class relocation_3(relocationtype):
        length = 4
        def write(self, address, sectiondelta):
            value = (address + sectiondelta) & 0xffffffff
            return super(relocation_3, self)._write(value)

    class relocation_10(relocationtype):
        length = 8
        def write(self, address, sectiondelta):
            value = address + (sectiondelta & 0xffffffffffffffff)
            return super(relocation_10, self)._write(value)

class IMAGE_BASERELOC_DIRECTORY(parray.block):
    _object_ = IMAGE_BASERELOC_DIRECTORY_ENTRY
    def getbysection(self, section):
        return ( entry for entry in self if section.containsaddress(entry['Page RVA'].int()) )

    def relocate(self, data, section, namespace):
        if not isinstance(data, array.array):
            raise AssertionError("Type of argument `data` must of an instance of {!r} : not isinstance({!r}, array.array)".format(array.array, data.__class__))

        sectionname = section['Name'].str()
        imagebase = self.getparent(Header)['OptionalHeader']['ImageBase'].int()

        sectionarray = section.parent
        sectionvaLookup = dict( ((s['Name'].str(),s['VirtualAddress'].int()) for s in sectionarray) )

        # relocation type 3
        t = relocationtype()
        t.length = 4
        t.write = lambda o, b: t._write(o+b)

        for entry in self.getbysection(section):
            for type,offset in entry.getrelocations(section):
                if type != 3:
                    raise NotImplementedError("Relocations other than type 3 aren't implemented because I couldn't find any to test with")
                currentva = sectionvaLookup[sectionname]+offset

                targetrva = t.read(data, offset)
                targetva = targetrva-imagebase

                try:
                    targetsection = sectionarray.getsectionbyaddress(targetrva-imagebase)

                except KeyError:
                    currentrva = imagebase+currentva
                    print "Relocation target at {:#x} to {:#x} lands outside section space".format(currentrva, targetrva)

                    # XXX: is it possible to hack support for relocations to the
                    #      'mz' header into this? that only fixes that case...but why else would you legitimately need something outside a section?
                    continue

                targetsectionname = targetsection['Name'].str()
                targetoffset = targetva - sectionvaLookup[targetsectionname]

#                relo = t.write(targetva, imagebase)
                relo = t.write(targetoffset, namespace[targetsectionname])
                data[offset : offset + len(relo)] = array.array('c',relo)
            continue

        return data

