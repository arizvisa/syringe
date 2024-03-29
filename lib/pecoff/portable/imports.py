import functools,itertools,ptypes
from ptypes import pstruct,parray,pbinary,pstr,ptype,dyn,utils
from ..headers import *

class IMAGE_IMPORT_HINT(pstruct.type):
    _fields_ = [
        (word, 'Hint'),
        (pstr.szstring, 'String'),
        (dyn.align(2), 'Padding')
    ]
    def str(self): return self.String()
    def Hint(self):
        return self['Hint'].li.int()
    def String(self):
        return self['String'].li.str()

class _IMAGE_IMPORT_NAME_TABLE_ORDINAL(pbinary.struct):

    def GetOrdinal(self):
        """Returns (Ordinal Hint, Ordinal String)"""
        hint = self['Ordinal Number']
        return (hint, 'Ordinal%d'% hint)      # microsoft-convention

    def summary(self):
        return repr(self.GetOrdinal())

@pbinary.littleendian
class IMAGE_IMPORT_NAME_TABLE_ORDINAL(_IMAGE_IMPORT_NAME_TABLE_ORDINAL):
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (15, 'Zero'),
        (16, 'Ordinal Number'),
    ]
@pbinary.littleendian
class IMAGE_IMPORT_NAME_TABLE_ORDINAL64(_IMAGE_IMPORT_NAME_TABLE_ORDINAL):
    _fields_ = [
        (1, 'OrdinalFlag'),   # True if an ordinal
        (47, 'Zero'),
        (16, 'Ordinal Number'),
    ]

class _IMAGE_IMPORT_NAME_TABLE_NAME(pbinary.struct):
    def dereference(self):
        """Dereferences Name into it's IMAGE_IMPORT_HINT structure"""
        parent = self.getparent((IMAGE_IMPORT_DIRECTORY,IMAGE_DELAYLOAD_DIRECTORY))
        offset = CalculateRelativeAddress(parent, self['Name'])
        return self.p.p.new(IMAGE_IMPORT_HINT, __name__='ImportName', offset=offset)

    # set all the required attributes so that this is faking a ptype.pointer_t
    d = property(fget=lambda s,**a: s.dereference(**a))

    def GetName(self):
        """Returns (Import Hint, Import String)"""
        if not self['OrdinalFlag'] and self['Name']:
            res = self.dereference().li
            return (res.Hint(), res.String())
        return (0, None)

    def summary(self):
        hint,string = self.GetName()
        return '({:d}, {:s})'.format(hint, repr(string) if string is None else '"%s"'%string)

@pbinary.littleendian
class IMAGE_IMPORT_NAME_TABLE_NAME(_IMAGE_IMPORT_NAME_TABLE_NAME):
    _fields_ = [
        (1, 'OrdinalFlag'),
        (31, 'Name'),
    ]
@pbinary.littleendian
class IMAGE_IMPORT_NAME_TABLE_NAME64(_IMAGE_IMPORT_NAME_TABLE_NAME):
    _fields_ = [
        (1, 'OrdinalFlag'),
        (32, 'Zero'),
        (31, 'Name'),
    ]

class _IMAGE_IMPORT_NAME_TABLE_ENTRY(dyn.union):
    def OrdinalQ(self):
        bc = 8 * self.object.size()
        mask = pow(2, bc - 1)
        return bool(self.object.int() & mask)
    def NameQ(self):
        return not self.OrdinalQ()
    def summary(self):
        if self.OrdinalQ():
            return 'Ordinal -> '+ self['Ordinal'].summary()
        return 'Name -> '+ self['Name'].summary()

    def GetImport(self):
        '''Will return a tuple of (iat index, name)'''
        if self.OrdinalQ() == 1:
            return self['Ordinal'].GetOrdinal()
        return self['Name'].GetName()

class IMAGE_IMPORT_NAME_TABLE_ENTRY(_IMAGE_IMPORT_NAME_TABLE_ENTRY):
    _value_ = uint32
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL, 'Ordinal'),
    ]

class IMAGE_IMPORT_NAME_TABLE_ENTRY64(_IMAGE_IMPORT_NAME_TABLE_ENTRY):
    _value_ = uint64
    _fields_ = [
        (IMAGE_IMPORT_NAME_TABLE_NAME64, 'Name'),
        (IMAGE_IMPORT_NAME_TABLE_ORDINAL64, 'Ordinal'),
    ]

class _IMAGE_IMPORT_ADDRESS_TABLE(parray.terminated):
    def isTerminator(self, value):
        return value.int() == 0 if self.length is None else self.length < len(self.value)

class IMAGE_IMPORT_ADDRESS_TABLE(_IMAGE_IMPORT_ADDRESS_TABLE):
    _object_ = uint32
class IMAGE_IMPORT_ADDRESS_TABLE64(_IMAGE_IMPORT_ADDRESS_TABLE):
    _object_ = uint64

class _IMAGE_IMPORT_NAME_TABLE(parray.terminated):
    _object_ = uint32
    def isTerminator(self, value):
        return sum(bytearray(value.serialize())) == 0

class IMAGE_IMPORT_NAME_TABLE(_IMAGE_IMPORT_NAME_TABLE):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY
class IMAGE_IMPORT_NAME_TABLE64(_IMAGE_IMPORT_NAME_TABLE):
    _object_ = IMAGE_IMPORT_NAME_TABLE_ENTRY64

class IMAGE_IMPORT_DESCRIPTOR(pstruct.type):
    def __IAT(self):
        res = IMAGE_IMPORT_ADDRESS_TABLE64 if self.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_ADDRESS_TABLE
        if hasattr(ptypes.provider, 'Ida') and self.source is ptypes.provider.Ida:
            entry = self.getparent(IMAGE_IMPORT_DESCRIPTOR)
            count = entry['INT'].li.d.l
            return dyn.clone(res, length=len(count))
        return res

    _fields_ = [
        (virtualaddress(lambda self: IMAGE_IMPORT_NAME_TABLE64 if self.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_NAME_TABLE, type=dword), 'INT'),  # FIXME
        (TimeDateStamp, 'TimeDateStamp'),
        (dword, 'ForwarderChain'),
        (virtualaddress(pstr.szstring, type=dword), 'Name'),
        (virtualaddress(__IAT, type=dword), 'IAT')
    ]

    def Hint(self, index):
        '''Given an index into the import directory entry, return the hint'''
        Header = LocateHeader(self)
        sections = Header['Sections']
        entry = self['INT'].d.li[index]
        if entry.OrdinalQ():
            res = entry['Ordinal']
            return res['Ordinal Number'] & 0xffff
        res = entry['Name']
        name = res.d.li
        return name['Hint'].int()

    def Name(self, index):
        '''Given an index into the import directory entry, return its name'''
        Header = LocateHeader(self)
        sections = Header['Sections']
        entry = self['INT'].d.li[index]
        if entry.OrdinalQ():
            res = entry['Ordinal']
            hint = res['Ordinal Number'] & 0xffff
            return "Ordinal{:d}".format(hint)
        res = entry['Name']
        name = res.d.li
        return name['String'].str()

    def Offset(self, index):
        '''Given an index into the import directory entry, return the va of the address containing the import.'''
        entry = self['IAT'].d.li[index]
        offset = CalculateRelativeOffset(self, self['IAT'].int())
        return offset + index * entry.size()

    def iterate(self):
        '''[(hint, importentry_name, importentry_offset, importentry_value),...]'''
        Header = LocateHeader(self)
        int, iat = self['INT'], self['IAT']

        cache, sections = {}, Header['Sections']
        for entry, address in zip(int.d.li[:-1], iat.d.li[:-1]):
            if entry.OrdinalQ():
                ordinal = entry['Ordinal']
                hint = ordinal['Ordinal Number'] & 0xffff
                yield hint, "Ordinal{:d}".format(hint), address.getoffset(), address.int()
                continue
            entryname = entry['Name']
            entryname_va = entryname['Name']
            section = sections.getsectionbyaddress(entryname_va)
            section_offset = section.getoffset()
            if section_offset in cache:
                sectionva, data = cache[section_offset]
            else:
                sectionva, data = cache.setdefault(section_offset, (section['VirtualAddress'].int(), bytearray(section.data().li.serialize())))
            hint_offset = entryname_va - sectionva
            hint = functools.reduce(lambda agg, by: agg * 0x100 + by, data[hint_offset : 2 + hint_offset][::-1])
            name = bytearray(itertools.takewhile(lambda by: by > 0, data[2 + hint_offset:]))
            yield hint, bytes(name).decode('utf-8', 'replace'), address.getoffset(), address.int()
        return

class IMAGE_IMPORT_DIRECTORY(parray.terminated):
    _object_ = IMAGE_IMPORT_DESCRIPTOR

    def isTerminator(self, value):
        return sum(bytearray(value.serialize())) == 0

    def iterate(self):
        for entry in self[:-1]:
            yield entry
        return

    def search(self, key):
        '''
        search the import list for an import dll that matches key
        return the rva
        '''
        for entry in self.iterate():
            if key == entry['Name'].d.li.str():
                return entry
            continue
        raise KeyError(key)

class IMAGE_DELAYLOAD_DIRECTORY_ENTRY(pstruct.type):
    def __IAT(self):
        res = IMAGE_IMPORT_ADDRESS_TABLE64 if self.getparent(Header)['OptionalHeader'].is64() else IMAGE_IMPORT_ADDRESS_TABLE
        if hasattr(ptypes.provider, 'Ida') and self.source is ptypes.provider.Ida:
            entry = self.getparent(IMAGE_DELAYLOAD_DIRECTORY_ENTRY)
            count = entry['DINT'].li.d.l
            return dyn.clone(res, length=len(count))
        return res
    _fields_ = [
        (dword, 'Attributes'),
        (virtualaddress(pstr.szstring, type=dword), 'Name'),
        (virtualaddress(dword, type=dword), 'ModuleHandle'),
        (virtualaddress(__IAT, type=dword), 'DIAT'),
        (lambda self: virtualaddress(IMAGE_IMPORT_NAME_TABLE64, type=dword) if self.getparent(Header)['OptionalHeader'].is64() else virtualaddress(IMAGE_IMPORT_NAME_TABLE, type=dword), 'DINT'),
        (virtualaddress(__IAT, type=dword), 'BDIAT'),
        (virtualaddress(__IAT, type=dword), 'UDAT'),
        (TimeDateStamp, 'TimeStamp'),
    ]

    def Hint(self, index):
        '''Given an index into the import directory entry, return the hint'''
        Header = LocateHeader(self)
        sections = Header['Sections']
        entry = self['DINT'].d.li[index]
        if entry.OrdinalQ():
            res = entry['Ordinal']
            return res['Ordinal Number'] & 0xffff
        res = entry['Name']
        name = res.d.li
        return name['Hint'].int()

    def Name(self, index):
        '''Given an index into the import directory entry, return its name'''
        Header = LocateHeader(self)
        sections = Header['Sections']
        entry = self['DINT'].d.li[index]
        if entry.OrdinalQ():
            res = entry['Ordinal']
            hint = res['Ordinal Number'] & 0xffff
            return "Ordinal{:d}".format(hint)
        res = entry['Name']
        name = res.d.li
        return name['String'].str()

    def Offset(self, index):
        '''Given an index into the import directory entry, return the va of the address containing the import.'''
        entry = self['DIAT'].d.li[index]
        offset = CalculateRelativeOffset(self, self['DIAT'].int())
        return offset + index * entry.size()

    def iterate(self):
        '''[(hint, importentry_name, importentry_offset, importentry_value),...]'''
        Header = LocateHeader(self)
        int, iat = self['DINT'], self['DIAT']

        cache, sections = {}, Header['Sections']
        for entry, address in zip(int.d.li[:-1], iat.d.li[:-1]):
            if entry.OrdinalQ():
                ordinal = entry['Ordinal']
                hint = ordinal['Ordinal Number'] & 0xffff
                yield hint, "Ordinal{:d}".format(hint), address.getoffset(), address.int()
                continue
            entryname = entry['Name']
            entryname_va = entryname['Name']
            section = sections.getsectionbyaddress(entryname_va)
            section_offset = section.getoffset()
            if section_offset in cache:
                sectionva, data = cache[section_offset]
            else:
                sectionva, data = cache.setdefault(section_offset, (section['VirtualAddress'].int(), bytearray(section.data().li.serialize())))
            hint_offset = entryname_va - sectionva
            hint = functools.reduce(lambda agg, by: agg * 0x100 + by, data[hint_offset : 2 + hint_offset][::-1])
            name = bytearray(itertools.takewhile(lambda by: by > 0, data[2 + hint_offset:]))
            yield hint, bytes(name).decode('utf-8', 'replace'), address.getoffset(), address.int()
        return

class IMAGE_DELAYLOAD_DIRECTORY(parray.block):
    _object_ = IMAGE_DELAYLOAD_DIRECTORY_ENTRY

    def isTerminator(self, value):
        return sum(bytearray(value.serialize())) == 0

    def iterate(self):
        for entry in self[:-1]:
            yield entry
        return

class IMAGE_BOUND_OffsetModuleName(ptype.opointer_t):
    _object_ = pstr.szstring
    _value_ = word
    def _calculate_(self, number):
        res = self.getparent(IMAGE_BOUND_IMPORT_DIRECTORY)
        return res.getoffset() + number

    def summary(self):
        res = super(IMAGE_BOUND_OffsetModuleName, self).summary()
        return "{:s} -> {:s}".format(res, self.d.li.str())

class IMAGE_BOUND_FORWARDER_REF(pstruct.type):
    _fields_ = [
        (TimeDateStamp, 'TimeDateStamp'),
        (IMAGE_BOUND_OffsetModuleName, 'OffsetModuleName'),
        (word, 'Reserved'),
    ]

class IMAGE_BOUND_IMPORT_DESCRIPTOR(pstruct.type):
    def __ModuleForwarderRefs(self):
        res = self['NumberOfModuleForwarderRefs'].li
        return dyn.array(IMAGE_BOUND_FORWARDER_REF, res.int())

    _fields_ = [
        (TimeDateStamp, 'TimeDateStamp'),
        (IMAGE_BOUND_OffsetModuleName, 'OffsetModuleName'),
        (word, 'NumberOfModuleForwarderRefs'),
        (__ModuleForwarderRefs, 'ModuleForwarderRefs'),
    ]

class IMAGE_BOUND_IMPORT_DIRECTORY(parray.terminated):
    _object_ = IMAGE_BOUND_IMPORT_DESCRIPTOR
    def isTerminator(self, value):
        return sum(bytearray(value.serialize())) == 0

