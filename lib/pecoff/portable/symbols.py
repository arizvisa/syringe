import logging,itertools,ptypes
from ptypes import pstruct,parray,dyn,ptype,pstr,pint
from ..headers import *

class IMAGE_SYM(pint.enum, uint16):
    _values_ = [
        ('UNDEFINED', 0),
        ('ABSOLUTE', 0xffff),   #-1),
        ('DEBUG', 0xfffe)       #-2)
    ]

    def Index(self):
        '''Returns the physical section number index if defined, otherwise None'''
        res = self.int()
        if res in (0, 0xffff, 0xfffe, -1, -2):
            return None
        return res - 1

    def summary(self):
        res = self.Index()
        return super(IMAGE_SYM, self).summary() if res is None else "SectionIndex({:d})".format(res)

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
            bytes = self.serialize()
            terminated = ptypes.utils.strdup(bytes, terminator=b'\0')
            return terminated.decode('latin1')

        try:
            res = self.getparent(SymbolTableAndStringTable)

        except ptypes.error.ItemNotFoundError:
            logging.warning("{:s} : unable to return symbol name at offset {:#x} due to missing {:s}".format(self.instance(), self['Offset'].int(), SymbolTableAndStringTable.typename()))
            return '<MissingStringTable>'

        stringtable = res['Strings']
        return stringtable.extract(self['Offset'].int())

    def set(self, string):
        encoded = string if isinstance(string, bytes) else string.encode('latin1')
        if len(encoded) <= 8:
            return self.load(source=ptypes.provider.bytes(encoded + b'\0' * (8 - len(encoded))), offset=0)

        table = self.getparent(SymbolTableAndStringTable)
        res = table.AddString(encoded)

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

    def Name(self):
        return self['Name'].str()

    def SectionIndex(self):
        return self['SectionNumber'].Index()

    def AuxiliarySymbols(self):
        res = self.parent.value
        index = res.index(self)+1
        return tuple(res[index : index + self['NumberOfAuxSymbols'].int()])

    def summary(self, **options):
        if self.initializedQ():
            name, value = self['Name'].str(), self['Value'].int()
            sym_section, sym_type, sym_class = map(self.__getitem__, ('SectionNumber', 'Type', 'StorageClass'))
            aux = AuxiliaryRecord.withdefault(sym_class.int(), type=sym_class.int())
            return "{:s} = {:#x} : SectionNumber={:s} : (Type={:s}, StorageClass={:s}) : AuxiliarySymbols={:s}[{:d}]".format(name, value, sym_section.summary(), sym_type.summary(), sym_class.summary(), aux.typename(), self['NumberOfAuxSymbols'].int())
        return super(Symbol, self).summary()

    def repr(self):
        return self.summary()

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
            auxSymbol = AuxiliaryRecord.withdefault(res, type=res)
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

    def enumerate(self):
        for index, item in enumerate(self):
            if isinstance(item, Symbol):
                yield index, item
            continue
        return

    def SymbolAndAuxiliary(self, symbol):
        '''Fetch Symbol and all its Auxiliary data'''
        index = self.value.index(symbol)
        return self.value[index : index+1 + symbol['NumberOfAuxSymbols'].int()]

    def details(self, **options):
        result = []
        for sym, aux in self.iterate():
            result.append("{!r}".format(sym))
            if sym['NumberOfAuxSymbols'].int() > 0:
                result.extend(ptypes.utils.indent('\n'.join(map("{!r}".format, aux))).split('\n'))
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
            return "{:s}<{:d}>".format(cls.__name__, cls.type)
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
        return ptypes.utils.strdup(self['File Name'].str(), terminator='\0')

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
        bytes = self.serialize()[offset:]
        terminated = ptypes.utils.strdup(bytes, terminator=b'\0')
        return terminated.decode('latin1')

    def add(self, string):
        '''appends a string to string table, returns offset'''
        res, nullbyte = string if isinstance(string, bytes) else string.encode('latin1'), b'\0'
        offset, data = self.size(), self['Data']
        data.length, data.value = data.length + len(res) + len(nullbyte), data.serialize() + res + nullbyte
        self['Size'].set(data.size() + self['Size'].size())
        return offset

    def find(self, string):
        '''returns the offset of the specified string within the string table'''
        res, nullbyte, data = string if isinstance(string, bytes) else string.encode('latin1'), b'\0', self['Data'].serialize()
        index = data.find(res + nullbyte)
        if index == -1:
            raise LookupError("{:s} : Unable to find null-terminated string ({!r}) within string table".format(self.instance(), string))
        return index + self['Size'].size()

class SymbolTableAndStringTable(pstruct.type):
    def __Symbols(self):
        p = self.getparent(Header)
        header = p.FileHeader()
        return dyn.clone(SymbolTable, length=header['NumberOfSymbols'].int())

    _fields_ = [
        (__Symbols, 'Symbols'),
        (StringTable, 'Strings'),
    ]

    ## due to how the data stored, this is all done in O(n) time...
    def names(self):
        return [sym['Name'].str() for sym, _ in self['Symbols'].iterate()]

    def iterate(self):
        for sym, _ in self['Symbols'].iterate():
            yield sym
        return

    def enumerate(self):
        for item in self['Symbols'].enumerate():
            yield item
        return

    def Symbol(self, name=None):
        if name:
            return self.li.fetch(name)[0]
        self.li
        return [sym for sym, aux in self['Symbols'].iterate()]

    def Auxiliary(self, name):
        res = self.fetch(name)
        return tuple(res[1:]) if len(res) > 1 else ()

    def AddSymbol(self):
        '''Add a new unnamed symbol to the 'Symbols' table. Return the Symbol instance.'''
        index, symbols = len(self['Symbols']), self['Symbols']
        logging.info("{:s} : adding a new symbol at index {:d}".format(self.instance(), index))

        res = symbols.new(Symbol, __name__=str(index), offset=self.getoffset() + self.size(), source=None).alloc()
        res['SectionNumber'].set('UNDEFINED')      # set as undefined since we aren't gonna be placing it anywhere
        symbols.append(res)
        return res

    def AddString(self, string):
        '''Add the specified `string` to the 'Strings' table and return the offset into the table'''
        table, item = self['Strings'], string if isinstance(string, bytes) else string.encode('latin1')
        res = table.add(item)
        logging.info("{:s} : added a new string to string table {:s} at offset {:d} : {!r}".format(self.instance(), table.instance(), res, string.decode('latin1') if isinstance(string, bytes) else string))
        return res

    ## symbol discovery and construction
    def fetch(self, name):
        for sym, aux in self['Symbols'].iterate():
            if sym['Name'].str() == name:
                return tuple(itertools.chain( [sym], aux ))
            continue
        raise KeyError("Symbol {:s} not found".format(name))

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
