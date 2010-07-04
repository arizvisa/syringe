import ptypes
from ptypes import pstruct,parray,dyn
from __base__ import *

class IMAGE_SYM(ptypes.pint.enum, int16):
    _fields_ = [
        ('UNDEFINED', 0),
        ('ABSOLUTE', 0xffff),   #-1),
        ('DEBUG', 0xfffe)       #-2)
    ]

    def get(self):
        '''Returns the physical section number index if defined, otherwise None'''
        n = int(self)
        if n in [0, 0xffff, 0xfffe, -1, -2]:
            return None
        return n - 1

class IMAGE_SYM_TYPE(ptypes.pint.enum, uint16):
    _fields_ = [
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

class IMAGE_SYM_DTYPE(ptypes.pint.enum, uint16):
    _fields_ = [
        ('NULL', 0),
        ('POINTER', 1),
        ('FUNCTION', 2),
        ('ARRAY', 3)
    ]

class IMAGE_SYM_CLASS(ptypes.pint.enum, uint8):
    _fields_ = [
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

    def getauxtype(self):
        '''return the pType constructor for the symbol storage class type'''
        res = int(self)
        try:
            res = AuxiliaryRecord.lookupByStorageClass(res)
        except KeyError:
            res = AuxiliaryRecord
        return res

class ShortName(pstruct.type):
    _fields_ = [
        (dword, 'IsShort'),
        (off_t, 'Offset')
    ]

    def get(self):
        stringtable = self.parent.parent.parent['Strings']
        '''resolve the Name of the object utilizing the provided StringTable if necessary'''
        if int(self['IsShort']) != 0x00000000:
            return ptypes.utils.strdup( self.serialize(), terminator='\x00')
        return stringtable.get( int(self['Offset']) )

    def set(self, string):
        if len(string) <= 8:
            string = string + '\x00'*(8-len(string))
            self.deserialize(string)
            return

        stringtable = self.parent.parent.parent['Strings']
        self['IsShort'].set(0)
        ofs = stringtable.add(string)
        self['Offset'].set(ofs)

class Symbol(pstruct.type):
    _fields_ = [
        (ShortName, 'Name'),
        (uint32, 'Value'),
        (IMAGE_SYM, 'SectionNumber'),   ## XXX: TODO -> would be neat to go from symbol to the actual physical section number
        (IMAGE_SYM_TYPE, 'Type'),
        (IMAGE_SYM_CLASS, 'StorageClass'),
        (uint8, 'NumberOfAuxSymbols')
    ]

    def __repr__(self):
        if self.initialized:
            kwds = ['SectionNumber', 'Type', 'StorageClass', 'NumberOfAuxSymbols']
            res = ', '.join(['%s:%d'% (k, int(self[k])) for k in kwds])
            #print self['Name'].get(), self['Value']
            return '[%x] %s %s {%s} Value: 0x%x'% (self.getoffset(), self.__class__, self['Name'].get(), res, int(self['Value']))
        return super(Symbol, self).__repr__()

class SymbolTable(parray.type):
    lastsymbol = Symbol()
    auxleft = 0
    def nextSymbol(self):
        index = len(self.value)
        offset = self.getoffset() + self.size()

        # read auxiliary symbols
        if self.auxleft > 0:
            res = self.value[-1]
            if type(res) is Symbol:
                res.load()
                self.auxleft = int(res['NumberOfAuxSymbols']) - 1

            cls = self.lastsymbol['StorageClass'].getauxtype()
            res = self.newelement(cls, str(index), offset)
            res.load()
            return res

        # start with a symbol
        res = self.newelement(Symbol, str(index), offset)
        res.load()
        self.lastsymbol = res
        self.auxleft = int(res['NumberOfAuxSymbols'])
        return res

    _object_ = nextSymbol

    def fetchsymbol(self, symbol):
        '''Fetch Symbol and all its Auxiliary data'''
        index = self.value.index(symbol)
        return self.value[index : index+1 + int(symbol['NumberOfAuxSymbols'])]

class AuxiliaryRecord(pstruct.type):
    @classmethod
    def lookupByStorageClass(cls, storageClass):
        res = globals().values()
        res = [ x for x in res if type(x) is type ]
        res = [ x for x in res if issubclass(x, AuxiliaryRecord) and x is not cls ]
        for x in res:
            if x.storageClass == storageClass:
                return x
        raise KeyError

class NullAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 0
    _fields_ = []

class FunctionDefinitionAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 2
    _fields_ = [
        (dword, 'TagIndex'),
        (uint32, 'TotalSize'),
        (off_t, 'PointerToLinenumber'),
        (off_t, 'PointerToNextFunction'),
        (word, 'Unused')
    ]

class FunctionBoundaryAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 101
    _fields_ = [
        (dword, 'Unused[0]'),
        (word, 'Linenumber'),
        (dyn.block(6), 'Unused[1]'),
        (off_t, 'PointerToNextFunction'),
        (word, 'Unused[2]')
    ]

class WeakExternalAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 105
    _fields_ = [
        (dword, 'TagIndex'),
        (dword, 'Characteristics'),
        (dyn.block(10), 'Unused')
    ]

class FileAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 103
    _fields_ = [
        (dyn.block(18), 'File Name')
    ]

    def __repr__(self):
        return ' '.join([self.name(), ptypes.utils.strdup(self['File Name'], terminator='\x00')])

class SectionAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 3
    _fields_ = [
        (uint32, 'Length'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (dword, 'CheckSum'),
        (word, 'Number'),
        (IMAGE_COMDAT_SELECT, 'Selection'),
        (dyn.block(3), 'Unused')
    ]

class CLRAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 106
    _fields_ = [
        (byte, 'bAuxType'),
        (byte, 'bReserved'),
        (dword, 'SymbolTableIndex'),
        (dyn.block(12), 'Reserved')
    ]

class StringTable(pstruct.type):
    def fetchData(self):
        if not self['Size'].initialized:    # XXX: this doesn't seem right
            self['Size'].load()
        count = int(self['Size'])
        cls = dyn.block(count - 4)
        return cls()

    def initialized(cls, value):
        def fn(self):
            res = self.newelement(cls, cls.__name__, self.getoffset() + self.size())
            res.set(value)
            return res
        return fn

    _fields_ = [
        (initialized(uint32, 4), 'Size'),
        (fetchData, 'Data')
    ]

    def get(self, offset):
        '''return the string associated with a particular offset'''
        string = self.serialize()
        string = string[offset:]
        return ptypes.utils.strdup(string, terminator='\x00')

    def add(self, string):
        '''appends a string to string table, returns offset'''
        ofs, data = self.size(), self['Data']
        data.value = data.serialize() + string + '\x00'
        data.length = len(data.value)
        self['Size'].set( data.size() + self['Size'].size() )
        return ofs

class SymbolTableAndStringTable(pstruct.type):
    length = 0

    _fields_ = [
        (lambda s: dyn.clone(SymbolTable, length=s.length), 'Symbols'),
        (StringTable, 'Strings'),
    ]

    ## this is all done in O(n) time...   FIXME: pull this functionality into an object that manages symbols instead of using ptypes
    def names(self):
        return [x['Name'].get() for x in self['Symbols'] if type(x) is Symbol]

    def get(self, name=None):
        if not self.initialized:
            self.load()

        if name:
            for x in self.get():
                if x['Name'].get() == name:
                    return self['Symbols'].fetchsymbol(x)[0]
                continue
                    
            raise KeyError('symbol %s not found'% name)
        return [x for x in self['Symbols'] if type(x) is Symbol]

    def getaux(self, name):
        for x in self.get():
            if int(x['NumberOfAuxSymbols']) > 0 and x['Name'].get() == name:
                return self['Symbols'].fetchsymbol(x)[1:]
            continue
        return ()

    def assign(self, name, value):
        try:
            sym = self.get(name)
            sym['Value'].set(value)
            sym['SectionNumber'].set(-1)    # absolute address

        except KeyError:
            self.add(name)
            return self.assign(name, value)
        return

    def add(self, name):
        warn('adding new symbol %s'% name)
        if ptype.is_ptype(name):
            name = name.serialize()
        else:
            name = str(name)

        symbols = self['Symbols']

        v = symbols.newelement(Symbol, len(self.value), self.getoffset() + self.size())
        v.source = None
        v.alloc()
        v['Name'].set(name)
        v['SectionNumber'].set(0)      # XXX: set as undefined since we aren't gonna be placing it anywhere
        symbols.append(v)

