import ptypes
from ptypes import pstruct,parray,dyn,ptype,pstr,pint
from ..__base__ import *

import logging,itertools

class IMAGE_SYM(pint.enum, uint16):
    _values_ = [
        ('UNDEFINED', 0),
        ('ABSOLUTE', 0xffff),   #-1),
        ('DEBUG', 0xfffe)       #-2)
    ]

    def GetSectionIndex(self):
        '''Returns the physical section number index if defined, otherwise None'''
        res = self.int()
        if res in (0, 0xffff, 0xfffe, -1, -2):
            return None
        return res - 1

    def summary(self):
        res = self.GetSectionIndex()
        return super(IMAGE_SYM, self).summary() if res is None else 'SectionIndex({:d})'.format(res)

class IMAGE_SYM_TYPE(pint.enum, uint16):
    _values_ = [
        ('NULL', 0),
        ('VOID', 1),
        ('CHAR', 2),
        ('SHORT', 3),
        ('INT', 4),
        ('LONG', 5),
        ('FLOAT', 6),
        ('DOUBLE', 7),
        ('STRUCT', 8),
        ('UNION', 9),
        ('ENUM', 10),
        ('MOE', 11),
        ('BYTE', 12),
        ('WORD', 13),
        ('UINT', 14),
        ('DWORD', 15),
        ('FUNCTION', 0x20),
    ]

class IMAGE_SYM_DTYPE(pint.enum, uint16):
    _values_ = [
        ('NULL', 0),
        ('POINTER', 1),
        ('FUNCTION', 2),
        ('ARRAY', 3)
    ]

class IMAGE_SYM_CLASS(pint.enum, uint8):
    _values_ = [
        ('END_OF_FUNCTION', 0xff),
        ('NULL', 0),
        ('AUTOMATIC', 1),
        ('EXTERNAL', 2),
        ('STATIC', 3),
        ('REGISTER', 4),
        ('EXTERNAL_DEF', 5),
        ('LABEL', 6),
        ('UNDEFINED_LABEL', 7),
        ('MEMBER_OF_STRUCT', 8),
        ('ARGUMENT', 9),
        ('STRUCT_TAG', 10),
        ('MEMBER_OF_UNION', 11),
        ('UNION_TAG', 12),
        ('TYPE_DEFINITION', 13),
        ('UNDEFINED_STATIC', 14),
        ('ENUM_TAG', 15),
        ('MEMBER_OF_ENUM', 16),
        ('REGISTER_PARAM', 17),
        ('BIT_FIELD', 18),
        ('BLOCK', 100),
        ('FUNCTION', 101),
        ('END_OF_STRUCT', 102),
        ('FILE', 103),
        ('SECTION', 104),
        ('WEAK_EXTERNAL', 105),
        ('CLR_TOKEN', 106),
    ]

class ShortName(pstruct.type):
    _fields_ = [
        (dword, 'IsShort'),
        (off_t, 'Offset')
    ]

    def str(self):
        '''resolve the Name of the object utilizing the provided StringTable if necessary'''
        if self['IsShort'].int() != 0x00000000:
            return ptypes.utils.strdup( self.serialize(), terminator='\x00')
        stringtable = self.getparent(SymbolTableAndStringTable)['Strings']
        return stringtable.extract( self['Offset'].int() )

    def set(self, string):
        if len(string) <= 8:
            self.load(source=ptypes.provider.string(string + '\x00'*(8-len(string))), offset=0)
            return self

        table = self.getparent(SymbolTableAndStringTable)
        res = table.AddString(string)

        self['IsShort'].set(0)
        self['Offset'].set(res)
        return self

class Symbol(pstruct.type):
    _fields_ = [
        (ShortName, 'Name'),
        (uint32, 'Value'),
        (IMAGE_SYM, 'SectionNumber'),   ## TODO: would be neat to go from symbol to the actual physical section number
        (IMAGE_SYM_TYPE, 'Type'),
        (IMAGE_SYM_CLASS, 'StorageClass'),
        (uint8, 'NumberOfAuxSymbols')
    ]

    def GetSectionIndex(self):
        return self['SectionNumber'].GetSectionIndex()

    def summary(self, **options):
        if self.initializedQ():
            name, value = self['Name'].str(), self['Value'].int()
            sym_section, sym_type, sym_class = map(self.__getitem__, ('SectionNumber', 'Type', 'StorageClass'))
            res = sym_class.int()
            aux = AuxiliaryRecord.withdefault(res, type=res)
            return '{:s} = {:#x} : Section={:s} : (Type={:s}, Class={:s}) : Aux={:s}[{:d}]'.format(name, value, sym_section.summary(), sym_type.summary(), sym_class.summary(), aux.typename(), self['NumberOfAuxSymbols'].int())
        return super(Symbol, self).summary()

    def repr(self): return self.summary()

    @property
    def auxiliary(self):
        res = self.parent.value
        index = res.index(self)+1
        return tuple(res[index:index+self['NumberOfAuxSymbols'].int()])
    aux = auxiliary

class SymbolTable(parray.terminated):
    def _object_(self):
        if len(self.value) == 0:
            self.__auxiliary__ = []
        if len(self.__auxiliary__) > 0:
            return self.__auxiliary__.pop(0)
        return Symbol

    def isTerminator(self, value):
        if isinstance(value, Symbol):
            auxCount = value['NumberOfAuxSymbols'].int()
            res = value['StorageClass'].int()
            auxSymbol = AuxiliaryRecord.withdefault(value, type=value)
            self.__auxiliary__.extend((auxSymbol,) * auxCount)
        return False

    def iterate(self):
        result = self.value[:]
        while len(result) > 0:
            sym = result.pop(0)
            if not isinstance(sym, Symbol):
                raise AssertionError("Unexpected element type while attempting to iterate through symbols : {:s} != {:s}".format(sym.classname(), Symbol.typename()))
            count = sym['NumberOfAuxSymbols'].int()
            aux, result = result[:count], result[count:]
            yield sym, aux
        return

    def GetSymbolAndAuxiliary(self, symbol):
        '''Fetch Symbol and all its Auxiliary data'''
        index = self.value.index(symbol)
        return self.value[index : index+1 + symbol['NumberOfAuxSymbols'].int()]

    def details(self, **options):
        result = []
        for sym, aux in self.iterate():
            result.append(repr(s))
            if sym['NumberOfAuxSymbols'].int() > 0:
                result.extend(ptypes.utils.indent('\n'.join(map('{!r}'.format, aux))).split('\n'))
            continue
        return '\n'.join(result)
        #return '\n'.join(repr(s) for s,a in self.iterate())

    def repr(self):
        return self.details()

    def properties(self):
        res = super(SymbolTable,self).properties()
        res['count'] = len(list(self.iterate()))
        return res

class AuxiliaryRecord(ptype.definition):
    cache = {}
    class NotImplementedAuxiliaryRecord(ptype.undefined):
        type = None
        @classmethod
        def typename(cls):
            return '{:s}<{:d}>'.format(cls.__name__, cls.type)
    default = NotImplementedAuxiliaryRecord

@AuxiliaryRecord.define
class NullAuxiliaryRecord(pstruct.type):
    type = 0
    _fields_ = []

@AuxiliaryRecord.define
class FunctionDefinitionAuxiliaryRecord(pstruct.type):
    type = 2
    _fields_ = [
        (dword, 'TagIndex'),
        (uint32, 'TotalSize'),
        (off_t, 'PointerToLinenumber'),
        (off_t, 'PointerToNextFunction'),
        (word, 'Unused')
    ]

@AuxiliaryRecord.define
class SectionAuxiliaryRecord(pstruct.type):
    type = 3
    _fields_ = [
        (uint32, 'Length'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (dword, 'CheckSum'),
        (word, 'Number'),
        (IMAGE_COMDAT_SELECT, 'Selection'),
        (dyn.block(3), 'Unused')
    ]

@AuxiliaryRecord.define
class FunctionBoundaryAuxiliaryRecord(pstruct.type):
    type = 101
    _fields_ = [
        (dword, 'Unused[0]'),
        (word, 'Linenumber'),
        (dyn.block(6), 'Unused[1]'),
        (off_t, 'PointerToNextFunction'),
        (word, 'Unused[2]')
    ]

@AuxiliaryRecord.define
class FileAuxiliaryRecord(pstruct.type):
    type = 103
    _fields_ = [
        #(dyn.block(18), 'File Name')
        (dyn.clone(pstr.string, length=18), 'File Name')
    ]

    def summary(self):
        return ptypes.utils.strdup(self['File Name'].str(), terminator='\x00')

@AuxiliaryRecord.define
class WeakExternalAuxiliaryRecord(pstruct.type):
    type = 105
    _fields_ = [
        (dword, 'TagIndex'),
        (dword, 'Characteristics'),
        (dyn.block(10), 'Unused')
    ]

@AuxiliaryRecord.define
class CLRAuxiliaryRecord(pstruct.type):
    type = 106
    _fields_ = [
        (byte, 'bAuxType'),
        (byte, 'bReserved'),
        (dword, 'SymbolTableIndex'),
        (dyn.block(12), 'Reserved')
    ]

class StringTable(pstruct.type):
    _fields_ = [
        (uint32, 'Size'),
        (lambda s: dyn.block(s['Size'].li.int() - 4), 'Data')
    ]

    def extract(self, offset):
        '''return the string associated with a particular offset'''
        string = self.serialize()[offset:]
        return ptypes.utils.strdup(string, terminator='\x00')

    def add(self, string):
        '''appends a string to string table, returns offset'''
        res = string + '\x00'
        ofs, data = self.size(), self['Data']
        data.length, data.value = data.length + len(res), data.serialize() + res
        self['Size'].set(data.size() + self['Size'].size())
        return ofs

    def find(self, string):
        '''returns the offset of the specified string within the string table'''
        res, data = string + '\x00', self['Data'].serialize()
        index = data.find(res)
        if index == -1:
            raise LookupError("{:s} : Unable to find null-terminated string within string table {:s} : {!r}".format('.'.join((cls.__module__, cls.__name__))), self.instance(), string)
        return index + self['Size'].size()

class SymbolTableAndStringTable(pstruct.type):
    _fields_ = [
        (lambda s: dyn.clone(SymbolTable, length=s.p.p['NumberOfSymbols'].li.int()), 'Symbols'),
        (StringTable, 'Strings'),
    ]

    ## due to how the data stored, this is all done in O(n) time...
    def names(self):
        return [sym['Name'].str() for sym, _ in self['Symbols'].iterate()]

    def iterate(self):
        for sym, _ in self['Symbols'].iterate():
            yield sym
        return

    def GetSymbol(self, name=None):
        if name:
            return self.li.fetch(name)[0]
        self.li
        return [sym for sym, aux in self['Symbols'].iterate()]

    def GetAuxiliary(self, name):
        res = self.fetch(name)
        return tuple(res[1:]) if len(res) > 1 else ()

    def AddSymbol(self):
        '''Add a new unnamed symbol to the 'Symbols' table. Return the Symbol instance.'''
        cls, index, symbols = self.__class__, len(self['Symbols']), self['Symbols']
        logging.info('{:s} : adding a new symbol at index {:d}'.format('.'.join((cls.__module__, cls.__name__)), index))

        res = symbols.new(Symbol, __name__=str(index), offset=self.getoffset() + self.size(), source=None).alloc()
        res['SectionNumber'].set('UNDEFINED')      # set as undefined since we aren't gonna be placing it anywhere
        symbols.append(res)
        return res

    def AddString(self, string):
        '''Add the specified `string` to the 'Strings' table and return the offset into the table'''
        cls, table = self.__class__, self['Strings']
        res = table.add(string)
        logging.info('{:s} : added a new string to string table {:s} at offset {:d} : {!r}'.format('.'.join((cls.__module__, cls.__name__)), table.instance(), res, string))
        return res

    ## symbol discovery and construction
    def fetch(self, name):
        for sym, aux in self['Symbols'].iterate():
            if sym['Name'].str() == name:
                return tuple(itertools.chain( (sym,), aux ))
            continue
        raise KeyError('Symbol {:s} not found'.format(name))

    def assign(self, name, value):
        '''Find the symbol identified by `name` and set its `value`'''
        name = name.serialize() if isinstance(name, ptype.type) else name[:]
        try:
            res = self.fetch(name)
            sym = next(iter(res))
        except KeyError:
            sym = self.AddSymbol()
            sym['Name'].set(name)
        sym['Value'].set(value)
        sym['SectionNumber'].set('ABSOLUTE')    # absolute address
        return sym
