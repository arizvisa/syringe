import sys,array,importlib,ptypes,functools
from ptypes import ptype,pstruct,pbinary,dyn,parray,bitmap,pint
from ..headers import *

# TODO: https://github.com/polycone/pe-loader/blob/master/loader/src/loader/relocations.cpp

## Base Relocation class (Sub-class for each machine type)
class MachineRelocation(ptype.definition):
    cache = {}

## Segment relocation entries
class Relocation(pstruct.type):
    def __Type(self):
        header = LocateHeader(self)
        machine = header.Machine()
        return MachineRelocation.lookup(machine.int())

    _fields_ = [
        (uint32, 'VirtualAddress'), # FIXME: this can be a virtualaddress(...) to the actual relocation
        (uint32, 'SymbolTableIndex'),
        (__Type, 'Type')
    ]

    def summary(self):
        fields = [('VirtualAddress', lambda v: '%x'% v), ('SymbolTableIndex', int), ('Type', str)]
        res = ', '.join(['%s=%s'% (k,t(self[k])) for k,t in fields])
        return '{' + res + '}'

    def relocate(self, data, symboltable, namespace=None):
        '''
        data = a string
        symboltable = an array of symbols
        namespace = a dict for looking up symbol and segment values by name
        '''
        raise NotImplementedError('This has been deprecated due to a refactor')

        # FIXME: stupid fucking python and it's issues recursive module importing
        headers = sys.modules.get('pecoff.portable.headers', importlib.import_module('pecoff.portable.headers'))

        # find the symbol used by the relocation
        symbol = symboltable[self['SymbolTableIndex'].int()]

        # figure out the section our symbol and our relocation points into
        currentsection = self.getparent(headers.IMAGE_SECTION_HEADER)
        sectionarray = currentsection.getparent(headers.SectionTableArray)

        # if the symbol is undefined or absolute, then assume the current section
        symbolsectionnumber = symbol.SectionIndex()
        if symbolsectionnumber is None:
            section = currentsection
        # otherwise use the symbol's section index
        else:
            section = sectionarray[symbolsectionnumber]

        # convert the data into an array that can be processed
        data = bytearray(data)
        updated = self['Type'].__relocate__(data, symbol, section, namespace)
        return bytes(updated)

class RelocationTable(parray.type):
    _object_ = Relocation

### Each relocation entry

## I386
@MachineRelocation.define
class IMAGE_REL_I386(pint.enum, uint16):
    type = IMAGE_FILE_MACHINE_.byname('I386')

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

    def __relocate__(self, data, symbol, section, namespace=None):
        '''Apply relocations for the specified ``symbol`` to the ``data``.'''
        raise NotImplementedError('This internal method has been deprecated due to a refactor')

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
            result = bitmap.append(result, x)
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
        #    print('>',name,hex(result),targetsectionname,hex(namespace[targetsectionname]))
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
        result, serialized = bitmap.new(result, 32), bytearray()
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
@MachineRelocation.define
class IMAGE_REL_AMD64(pint.enum, uint16):
    type = IMAGE_FILE_MACHINE_.byname('AMD64')
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

    def __relocate__(self, data, symbol, section, namespace=None):
        '''Apply relocations for the specified ``symbol`` to the ``data``.'''
        raise NotImplementedError('This internal method has been deprecated due to a refactor')
        return data

## per data directory relocations
class RelocationType(ptype.definition):
    cache = {}

class RelocationTypeBase(pbinary.integer):
    def blockbits(self):
        return 12

    def read(self, data, offset, length):
        '''Given the specified data, read length bytes from the provided offset and return as a little-endian integer.'''
        res = bytearray(data[offset : offset + length])
        return functools.reduce(lambda agg, item: agg * 0x100 + item, reversed(res), 0)

    def write(self, integer, length):
        '''Given the specified integer and its length, encode it into its little-endian form and return a string.'''
        res, binteger = bytearray(), bitmap.new(integer, 8 * length)
        octets = bitmap.split(binteger, 8)
        for item in reversed(octets):
            res.append(bitmap.int(item))
        return bytes(res)

@RelocationType.define(type=1)
class RelocationType1(RelocationTypeBase):
    def read(self, data, offset):
        return super(RelocationType1, self).read(data, offset, 2)

    def write(self, address, delta):
        res = address + (delta & 0xffff0000) // 0x10000
        return super(RelocationType1, self).write(res, 2)

@RelocationType.define(type=2)
class RelocationType2(RelocationTypeBase):
    def read(self, data, offset):
        return super(RelocationType2, self).read(data, offset, 2)

    def write(self, address, delta):
        res = address + (delta & 0x0000ffff)
        return super(RelocationType2, self).write(res, 2)

@RelocationType.define(type=3)
class RelocationType3(RelocationTypeBase):
    def read(self, data, offset):
        return super(RelocationType3, self).read(data, offset, 4)

    def write(self, address, delta):
        res = (address + delta) & 0xffffffff
        return super(RelocationType3, self).write(res, 4)

@RelocationType.define(type=10)
class RelocationType10(RelocationTypeBase):
    def read(self, data, offset):
        return super(RelocationType10, self).read(data, offset, 8)

    def write(self, address, delta):
        res = address + (delta & 0xffffffffffffffff)
        return super(RelocationType10, self).write(res, 8)

class BaseRelocationEntry_(pbinary.struct):
    def __Offset(self):
        res = self['Type']
        return RelocationType.lookup(res, 12)

    def blockbits(self):
        # hardcode the number of bits since despite this structure being
        # variably-sized, we know what it's supposed to be. this way we
        # can be formatted as little-endian without having to be tricky.
        return 16

    _fields_ = [
        (4, 'Type'),
        (__Offset, 'Offset'),
    ]

@pbinary.littleendian
class BaseRelocationEntry(pbinary.partial):
    _object_ = BaseRelocationEntry_

    def apply(self, entry, imagebase, sectiontable, segment, **addresses):
        '''
        Apply the current relocation to the provided segment (data) using the
        specified IMAGE_BASE_RELOCATION along with the imagebase to convert
        the relocation target address into an offset, and the provided section
        table to calculate the new relocated address that is written. If any
        section names are provided as extra arguments, then use that as the
        segment base address instead.
        '''
        relocation, page = self.field('Offset'), entry['VirtualAddress'].int()
        section = sectiontable.getsectionbyaddress(page)

        # FIXME: I haven't actually verified this is working correctly since
        #        it's not actually being used yet since the refactor.

        res = relocation.read(segment, page - section['VirtualAddress'].int() + relocation.int())
        target = res - imagebase
        section = sectiontable.getsectionbyaddress(target)

        offset = target - section['VirtualAddress'].int()
        res = relocation.write(offset, addresses.get(section['Name'].str(), section['VirtualAddress'].int()))

        segment[offset : offset + len(res)] = bytearray(res)

        return segment

class BaseRelocationArray(parray.block):
    _object_ = BaseRelocationEntry

class BaseRelocationBlock(ptype.block):
    def array(self):
        '''Return this type casted to a BaseRelocationArray with the correct types.'''
        return self.cast(BaseRelocationArray, blocksize=self.blocksize)

    def iterate(self):
        '''Iterate through each relocation wrapped by this type.'''
        res = self.array()
        for item in iter(res):
            yield item
        return

class IMAGE_BASE_RELOCATION(pstruct.type):
    def __TypeOffset(self):
        res, fields = self['SizeOfBlock'].li, ['VirtualAddress', 'SizeOfBlock']
        size = res.int() - sum(self[fld].li.size() for fld in fields)
        return dyn.clone(BaseRelocationBlock, length=max(0, size))
        #return dyn.blockarray(WORD, max(0, size))
        #return dyn.clone(pbinary.blockarray,_object_=BaseRelocationEntry, blockbits=lambda _, octets=max(0, size): 8 * octets)
        #return dyn.clone(BaseRelocationArray, blocksize=lambda _, cb=max(0, size): cb)

    _fields_ = [
        (virtualaddress(VOID, type=DWORD), 'VirtualAddress'),
        (DWORD, 'SizeOfBlock'),
        (__TypeOffset, 'TypeOffset'),
    ]

    def summary(self):
        res = self['TypeOffset'].array()
        return "VirtualAddress={:#x} SizeOfBlock={:#x} TypeOffset=...{:d} entr{:s}...".format(self['VirtualAddress'], self['SizeOfBlock'], len(res), 'y' if len(res) == 1 else 'ies')

    def extract(self):
        '''Return a list of tuples containing the relocation type and offset contained within this entry.'''
        block = self['TypeOffset'].serialize()
        relocations = array.array('I' if len(array.array('I', 4 * b'\0')) > 1 else 'H', block)
        return [((item & 0xf000) // 0x1000, item & 0x0fff) for item in relocations]

    def getrelocations(self, section):
        pageoffset, loadedsize = self['VirtualAddress'].int() - section['VirtualAddress'].int(), section.getloadedsize()
        if not (pageoffset >= 0 and pageoffset < loadedsize):
            va, sectionva, name = self['VirtualAddress'].int(), section['VirtualAddress'].int(), section['Name'].str()
            raise AssertionError("Page Offset in RVA outside bounds of section ({:#x} not in {:#x}..{:#x}) : IMAGE_BASE_RELOCATION.VirtualAddress({:#x}) IMAGE_SECTION_HEADER.VirtualAddress({:#x}{:+#x}) IMAGE_SECTION_HEADER.Name({!r})".format(va, sectionva, sectionva + loadedsize, va, sectionva, loadedsize, name))

        for type, offset in self.extract():
            if type == 0:
                continue
            yield type, pageoffset + offset
        return

class IMAGE_BASERELOC_DIRECTORY(parray.block):
    _object_ = IMAGE_BASE_RELOCATION
    def filter(self, section):
        '''Return each relocation item that is within the specified IMAGE_SECTION_HEADER.'''
        for item in self:
            res = item['VirtualAddress']
            if section.containsaddress(res.int()):
                yield item
            continue
        return

    def relocate(self, data, section, namespace):
        if not isinstance(data, bytearray):
            raise AssertionError("Type of argument `data` must be an instance of {!s} : not isinstance({!s}, {!s})".format(bytearray, data.__class__, bytearray))

        sectionname = section['Name'].str()
        header = LocateHeader(self)
        imagebase = header['OptionalHeader']['ImageBase'].int()

        sectionarray = section.parent
        sectionvaLookup = {s['Name'].str() : s['VirtualAddress'].int() for s in sectionarray}

        # relocation type 3
        res = RelocationType.lookup(3)
        R = res()

        for entry in self.filter(section):
            for type, offset in entry.getrelocations(section):
                if type != 3:
                    raise NotImplementedError("Relocations other than type 3 aren't implemented because I couldn't find any to test with")
                currentva = sectionvaLookup[sectionname] + offset

                targetrva = R.read(data, offset)
                targetva = targetrva - imagebase

                try:
                    targetsection = sectionarray.getsectionbyaddress(targetrva - imagebase)

                except KeyError:
                    currentrva = imagebase+currentva
                    print("Relocation target at {:#x} to {:#x} lands outside section space".format(currentrva, targetrva))

                    # XXX: is it possible to hack support for relocations to the
                    #      'mz' header into this? that only fixes that case...but why else would you legitimately need something outside a section?
                    continue

                targetsectionname = targetsection['Name'].str()
                targetoffset = targetva - sectionvaLookup[targetsectionname]

#                relocation = R.write(targetva, imagebase)
                # apply the relocation to the data that was passed to us
                relocation = R.write(targetoffset, namespace[targetsectionname])
                data[offset : offset + len(relocation)] = bytearray(relocation)
            continue

        return data
