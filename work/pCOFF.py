import ptypes
from ptypes import *
from warnings import warn

## primitives
class byte(pint.uint8_t): pass
class word(pint.uint16_t): pass
class dword(pint.uint32_t): pass
class float(pint.int32_t): pass     # XXX: not implemented yet
class double(pint.int64_t): pass     # XXX: not implemented yet

uint8 = pint.uint8_t
int8 = pint.int8_t
int16 = pint.int16_t
uint16 = pint.uint16_t
int32 = pint.int32_t
uint32 = pint.uint32_t
off_t = pint.uint32_t
addr_t = pint.uint32_t

class IMAGE_REL_I386(ptypes.pint.penum, uint16):
    _fields_ = [
        ('IMAGE_REL_I386_ABSOLUTE', 0x0000),
        ('IMAGE_REL_I386_DIR16', 0x0001),
        ('IMAGE_REL_I386_REL16', 0x0002),
        ('IMAGE_REL_I386_DIR32', 0x0006),
        ('IMAGE_REL_I386_DIR32NB', 0x0007),
        ('IMAGE_REL_I386_SEG12', 0x0009),
        ('IMAGE_REL_I386_SECTION', 0x000A),
        ('IMAGE_REL_I386_SECREL', 0x000B),
        ('IMAGE_REL_I386_TOKEN', 0x000C),
        ('IMAGE_REL_I386_SECREL7', 0x000D),
        ('IMAGE_REL_I386_REL32', 0x0014)
    ]

class IMAGE_COMDAT_SELECT(ptypes.pint.penum, byte):
    _fields_ = [
        ('IMAGE_COMDAT_SELECT_NODUPIC', 1),
        ('IMAGE_COMDAT_SELECT_ANY', 2),
        ('IMAGE_COMDAT_SELECT_SAME_SIZE', 3),
        ('IMAGE_COMDAT_SELECT_EXACT_MATCH', 4),
        ('IMAGE_COMDAT_SELECT_ASSOCIATIVE', 5),
        ('IMAGE_COMDAT_SELECT_LARGEST', 6)
    ]

## structs
class FileHeader(pstruct.type):
    _fields_ = [
        (word, 'Machine'),
        (uint16, 'NumberOfSections'),
        (dword, 'TimeDateStamp'),
        (off_t, 'PointerToSymbolTable'),
        (uint32, 'NumberOfSymbols'),
        (word, 'SizeOfOptionalHeader'),
        (word, 'Characteristics')
    ]

    def getsymbols(self):
        '''fetch the symbol and string table'''
        ofs,length = (int(self['PointerToSymbolTable']), int(self['NumberOfSymbols']))
        res = self.newelement(SymbolTableAndStringTable, 'symbols', ofs)
        res.length = length
        res.load()
        return res

class SectionTable(pstruct.type):
    # XXX: we can store a longer than 8 byte Name if we want to implement code that navigates to the string table
    #      apparently executables don't care though...
    _fields_ = [
        (pstr.new(8), 'Name'),
        (uint32, 'VirtualSize'),
        (addr_t, 'VirtualAddress'),
        (uint32, 'SizeOfRawData'),
        (off_t, 'PointerToRawData'),
        (off_t, 'PointerToRelocations'),
        (off_t, 'PointerToLinenumbers'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (dword, 'Characteristics'),
    ]

    def __repr__(self):
        name = self['Name'].get()
#        kwds = ['VirtualAddress', 'VirtualSize', 'Characteristics']
#        fields = ', '.join(['%s:%x'% (k, int(self[k])) for k in kwds])
#        v = self.getrelocations()
#        relocations = '\n'.join(map(repr, v))
#        self.delchild(v)
        res = '%s %s {%s}'% (self.__class__, name, fields)
#        if relocations:
#            res += '\n' + relocations
        return res

    def __repr__(self):
        name = self['Name'].get()
        return ' '.join([name, super(SectionTable, self).__repr__()])

    def get(self):
        '''fetch a block containing the contents of the section'''
        return self.getdata().serialize()     # this feels stupid..

    def getdata(self):
        '''fetch a block containing the contents of the section'''
        ofs,length = (int(self['PointerToRawData']), int(self['SizeOfRawData']))

        data = self.newelement(dyn.block(length), 'DATA', ofs)
        data.load()
        return data

    def getrelocations(self):
        '''fetch an array containing the Relocations'''
        ofs,length = (int(self['PointerToRelocations']), int(self['NumberOfRelocations']))

        relocations = self.newelement(dyn.array(Relocation, length), 'RELOCATIONS', ofs)
        relocations.load()
        return relocations

    def getlinenumbers(self):
        '''fetch an array containing the Linenumbers'''
        ofs,length = (int(self['PointerToLinenumbers']), int(self['NumberOfLinenumbers']))

        linenumbers = self.newelement(dyn.array(LineNumber, length), 'LINENUMBERS', ofs)
        linenumbers.setoffset(ofs)
        linenumbers.load()
        return linenumbers

class Relocation(pstruct.type):
    _fields_ = [
        (addr_t, 'VirtualAddress'),
        (uint32, 'SymbolTableIndex'),
        (IMAGE_REL_I386, 'Type')
    ]

    def __repr__(self):
        fields = [('VirtualAddress', lambda v: '%x'% v), ('SymbolTableIndex', int), ('Type', str)]
        res = ', '.join(['%s=%s'% (k,t(self[k])) for k,t in fields])
        return '%s {%s}'% (self.__class__, res)

    def relocate(self, data, symboltable):
        section = self.parent.parent
        baseaddress = int(section['VirtualAddress'])
        symbol = symboltable[int(self['SymbolTableIndex'])]

        name = symbol['Name'].get()

        ### (because we know this software is totally written following the blob design pattern where you have to be cautious about being intrusive... :)
        t,va = int(self['Type']), int(self['VirtualAddress'])

        if t == 0x0006:     # 32-bit VA
            res = int(symbol['Value'])

        elif t == 0x0014:   # 32-bit relative displacement
            anchor = baseaddress + va + 4
            res = int(symbol['Value']) - anchor

        elif t in [ 0x0000, 0x0007, 0x000A, 0x000B ]:
            # [ignore relocation, 32-bit VA, 32-bit RVA, section index, offset from section]
            raise NotImplementedError(t)

        else:
            raise NotImplementedError(t)

        x = type(symbol['Value'])()
        x.set(res)
        return data[:va] + x.serialize() + data[va+x.size():]

class LineNumber(pstruct.type):
    _fields_ = [
        (dword, 'Type'),
        (uint16, 'Linenumber'),
        (addr_t, 'Address')
    ]

class IMAGE_SYM(ptypes.pint.penum, int16):
    _fields_ = [
        ('IMAGE_SYM_UNDEFINED', 0),
        ('IMAGE_SYM_ABSOLUTE', 0xffff),   #-1),
        ('IMAGE_SYM_DEBUG', 0xfffe)       #-2)
    ]

    def get(self):
        '''Returns the section number index if defined, otherwise None'''
        n = int(self)
        if n in [0, 0xffff, 0xfffe, -1, -2]:
            return None
        return n - 1

class IMAGE_SYM_TYPE(ptypes.pint.penum, uint16):
    _fields_ = [
        ('IMAGE_SYM_TYPE_NULL', 0),
        ('IMAGE_SYM_TYPE_VOID', 1),
        ('IMAGE_SYM_TYPE_CHAR', 2),
        ('IMAGE_SYM_TYPE_SHORT', 3),
        ('IMAGE_SYM_TYPE_INT', 4),
        ('IMAGE_SYM_TYPE_LONG', 5),
        ('IMAGE_SYM_TYPE_FLOAT', 6),
        ('IMAGE_SYM_TYPE_DOUBLE', 7),
        ('IMAGE_SYM_TYPE_STRUCT', 8),
        ('IMAGE_SYM_TYPE_UNION', 9),
        ('IMAGE_SYM_TYPE_ENUM', 10),
        ('IMAGE_SYM_TYPE_MOE', 11),
        ('IMAGE_SYM_TYPE_BYTE', 12),
        ('IMAGE_SYM_TYPE_WORD', 13),
        ('IMAGE_SYM_TYPE_UINT', 14),
        ('IMAGE_SYM_TYPE_DWORD', 15),
        ('IMAGE_SYM_TYPE_FUNCTION', 0x20),
    ]

class IMAGE_SYM_DTYPE(ptypes.pint.penum, uint16):
    _fields_ = [
        ('IMAGE_SYM_DTYPE_NULL', 0),
        ('IMAGE_SYM_DTYPE_POINTER', 1),
        ('IMAGE_SYM_DTYPE_FUNCTION', 2),
        ('IMAGE_SYM_DTYPE_ARRAY', 3)
    ]

class IMAGE_SYM_CLASS(ptypes.pint.penum, uint8):
    _fields_ = [
        ('IMAGE_SYM_CLASS_END_OF_FUNCTION', 0xff),
        ('IMAGE_SYM_CLASS_NULL', 0),
        ('IMAGE_SYM_CLASS_AUTOMATIC', 1),
        ('IMAGE_SYM_CLASS_EXTERNAL', 2),
        ('IMAGE_SYM_CLASS_STATIC', 3),
        ('IMAGE_SYM_CLASS_REGISTER', 4),
        ('IMAGE_SYM_CLASS_EXTERNAL_DEF', 5),
        ('IMAGE_SYM_CLASS_LABEL', 6),
        ('IMAGE_SYM_CLASS_UNDEFINED_LABEL', 7),
        ('IMAGE_SYM_CLASS_MEMBER_OF_STRUCT', 8),
        ('IMAGE_SYM_CLASS_ARGUMENT', 9),
        ('IMAGE_SYM_CLASS_STRUCT_TAG', 10),
        ('IMAGE_SYM_CLASS_MEMBER_OF_UNION', 11),
        ('IMAGE_SYM_CLASS_UNION_TAG', 12),
        ('IMAGE_SYM_CLASS_TYPE_DEFINITION', 13),
        ('IMAGE_SYM_CLASS_UNDEFINED_STATIC', 14),
        ('IMAGE_SYM_CLASS_ENUM_TAG', 15),
        ('IMAGE_SYM_CLASS_MEMBER_OF_ENUM', 16),
        ('IMAGE_SYM_CLASS_REGISTER_PARAM', 17),
        ('IMAGE_SYM_CLASS_BIT_FIELD', 18),
        ('IMAGE_SYM_CLASS_BLOCK', 100),
        ('IMAGE_SYM_CLASS_FUNCTION', 101),
        ('IMAGE_SYM_CLASS_END_OF_STRUCT', 102),
        ('IMAGE_SYM_CLASS_FILE', 103),
        ('IMAGE_SYM_CLASS_SECTION', 104),
        ('IMAGE_SYM_CLASS_WEAK_EXTERNAL', 105),
        ('IMAGE_SYM_CLASS_CLR_TOKEN', 106),
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
        (IMAGE_SYM, 'SectionNumber'),   ## XXX: TODO -> would be neat to go from symbol to the actual section number
        (IMAGE_SYM_TYPE, 'Type'),
        (IMAGE_SYM_CLASS, 'StorageClass'),
        (uint8, 'NumberOfAuxSymbols')
    ]

    def __repr__(self):
        if self.initialized:
            kwds = ['SectionNumber', 'Type', 'StorageClass']
            res = ', '.join(['%s:%d'% (k, int(self[k])) for k in kwds])
            return '%s %s {%s} Value:%x'% (self.__class__, self['Name'].get(), res, int(self['Value']))
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
    def createSymbolTable(self):
        class symbolTable(SymbolTable):
            length = self.length
        return symbolTable

    _fields_ = [
        (createSymbolTable, 'Symbols'),
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

class File(pstruct.type):
    _fields_ = [
        (FileHeader, 'Header'),
        (lambda x: x.newelement(dyn.array(SectionTable, int(x['Header']['NumberOfSections'])), 'Sections', x.getoffset() + x['Header'].size()), 'Sections')
    ]

def open(filename):
    res = File()
    res.source = provider.file(filename)
    res.load()
    res.filename = filename     # ;)
    return res

if __name__ == '__main__':
    ## parse the file
    from pCOFF import *
    from provider import fileprovider

    print '-'*20 + 'loading file..'
    coff = File()
    coff.source = fileprovider('../obj/inject-helper.obj')
    coff.load()
    print coff['Header']
    print coff['Sections']

    ### check everything from the symbol table's perspective
    sst = coff['Header'].getsymbols()
    sst.load()

    symboltable = sst['Symbols']

    print '-'*20 + 'printing external symbols'
    ## build list of external symbols
    sym_external = {}
    for name in symboltable.keys():
        v = symboltable.lookup(name)
        if int(v[0]['StorageClass']) == 2:
            sym_external[name] = v
        continue

    print '\n'.join(map(repr, sym_external.values()))
    
    print '-'*20 + 'printing statically defined symbols'
    ## build list of static symbols
    sym_static = {}
    for name in symboltable.keys():
        v = symboltable.lookup(name)
        if int(v[0]['StorageClass']) == 3 and int(v[0]['Value']) == 0:
            num = v[0]['SectionNumber'].get()
            sym_static[num] = (v[0], v[1:1+int(v[0]['NumberOfAuxSymbols'])])
        continue

    for x in sym_static.keys():
        sym,aux = sym_static[x]
        print sym
        if aux:
            print '\n'.join(map(repr,aux))

    print '-'*20 + 'check that the number of relocations in the symboltable matches the section\'s'
    ## build list of static symbols
    ## sanity check that the number of relocations are correct
    sections = coff['Sections']
    for index,(sym,aux) in sym_static.items():
        section = sections[index]
        sectioncount = int(section['NumberOfRelocations'])
        if len(aux) > 0:
            symbolcount = int(aux[0]['NumberOfRelocations'])
            if sectioncount != symbolcount:
                warn('number of relocations (%d) for section %s differs from section definition (%d)'% (symbolcount,sym['Name'].get(),sectioncount))
        print 'relocated section %s'% repr(section)
        continue

    print '-'*20 + 'adding some symbols'
    ## reassign some symbols
    symboltable.assign('_TlsAlloc@0', 0xcccccccc)
    symboltable.assign('.text', 0x4010000)

    print '-'*20 + 'printing all symbol information'
    print '\n'.join(map(repr, symboltable))

    def formatrelocation(relo, symboltable):
        symbol = symboltable[ int(relo['SymbolTableIndex']) ]
        return '\n'.join([repr(symbol), repr(relo)]) + '\n'

    ### everything from the section's perpsective
    print '-'*20 + 'printing all relocations'
    for section in coff['Sections']:
        relocations = section.getrelocations()
        data = section.getdata()
        section.data, section.relocations = data.serialize(), relocations   # save for later
        
    ## do relocations for every section
    for section in coff['Sections']:
        data = section.data
        for r in section.relocations:
            section.data = r.relocate(section.data, symboltable)
        continue
        
    ## print out results
    print '-'*20 + 'printing relocated sections'
    for section in coff['Sections']:
        print repr(section)
        print ptypes.utils.indent('\n'.join(map(lambda x: formatrelocation(x, symboltable), section.relocations)))
#        print ptypes.utils.hexdump(section.data)

    print '-'*20 + 'dumping relocated sections'
    for index in range( len(sections) ):
        section = sections[index]

        name = ptypes.utils.strdup( section['Name'].serialize(), terminator='\x00')
        print name,
        if index in sym_static.keys():
            sym,aux = sym_static[index]
            print sym['Name'].get(), sym['SectionNumber'].get(), int(sym['Value'])
            data = section.getrelocateddata(symboltable)
        else:
            print 
            data = section.getdata().serialize()

#        print ptypes.utils.hexdump( section.getdata().serialize() )
        print ptypes.utils.hexdump( data )

        x = file('%s.section'% name[1:], 'wb')
        x.write(data)
        x.close()
