#import sys
#sys.path.append('/work/code/ptypes.git')

import ptypes
from ptypes import *
config.WIDTH = None

## primitives
byte = pByte
word = pWord
dword = pDword
uint8 = int8 = bigendian(pByte)
uint16 = int16 = bigendian(pWord)
uint32 = int32 = bigendian(pDword)
off_t = bigendian(pDword)
addr_t = bigendian(pDword)

class IMAGE_REL_I386(pEnum, uint16):
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

## structs
class FileHeader(pStruct):
    _fields_ = [
        (word, 'Machine'),
        (uint16, 'NumberOfSections'),
        (dword, 'TimeDateStamp'),
        (off_t, 'PointerToSymbolTable'),
        (uint32, 'NumberOfSymbols'),
        (word, 'SizeOfOptionalHeader'),
        (word, 'Characteristics')
    ]

    def getSymbolAndStringTable(self, filedata):
        '''fetch a 2 element array containing (SymbolTable, StringTable)'''
        ofs,length = (int(self['PointerToSymbolTable']), int(self['NumberOfSymbols']))
        stream = iter(filedata[ofs:])

        syms = SymbolTable()
        syms.totallength = length
        syms.setOffset(ofs)
        syms.deserialize(stream)
        ofs += syms.size()

        strs = StringTable()
        strs.setOffset(ofs)
        strs.deserialize(stream)

        res = dyn.array(pStruct, 0, 'SYMBOLANDSTRINGTABLE')()
        res.append(syms)
        res.append(strs)
        return res

class SectionTable(pStruct):
    _fields_ = [
        (dyn.block(8), 'Name'),
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

    def getData(self, filedata):
        '''fetch a block containing the contents of the section'''
        ofs,length = (int(self['PointerToRawData']), int(self['SizeOfRawData']))

        data = dyn.block(length, name='DATA')()
        data.setOffset(ofs)
        data.deserialize(filedata[ofs:ofs+length])
        return data

    def getRelocations(self, filedata):
        '''fetch an array containing the Relocations'''
        ofs,length = (int(self['PointerToRelocations']), int(self['NumberOfRelocations']))

        relocations = dyn.array(Relocation, length)()
        relocations.setOffset(ofs)
        relocations.deserialize(filedata[ofs:])
        return relocations

    def getLinenumbers(self, filedata):
        '''fetch an array containing the Linenumbers'''
        ofs,length = (int(self['PointerToLinenumbers']), int(self['NumberOfLinenumbers']))

        linenumbers = dyn.array(LineNumber, length)()
        linenumbers.setOffset(ofs)
        linenumbers.deserialize( filedata[ofs:] )
        return linenumbers

class Relocation(pStruct):
    _fields_ = [
        (addr_t, 'VirtualAddress'),
        (uint32, 'SymbolTableIndex'),
        (IMAGE_REL_I386, 'Type')
    ]

class LineNumber(pStruct):
    _fields_ = [
        (dword, 'Type'),
        (uint16, 'Linenumber'),
        (addr_t, 'Address')
    ]

class IMAGE_SYM(pEnum, int16):
    _fields_ = [
        ('IMAGE_SYM_UNDEFINED', 0),
        ('IMAGE_SYM_ABSOLUTE', 0xffff),   #-1),
        ('IMAGE_SYM_DEBUG', 0xfffe)       #-2)
    ]

class IMAGE_SYM_TYPE(pEnum, uint16):
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

class IMAGE_SYM_DTYPE(pEnum, uint16):
    _fields_ = [
        ('IMAGE_SYM_DTYPE_NULL', 0),
        ('IMAGE_SYM_DTYPE_POINTER', 1),
        ('IMAGE_SYM_DTYPE_FUNCTION', 2),
        ('IMAGE_SYM_DTYPE_ARRAY', 3)
    ]

class IMAGE_SYM_CLASS(pEnum, uint8):
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

    def getAuxType(self):
        '''return the pType constructor for the symbol storage class type'''
        res = int(self)
        try:
            res = AuxiliaryRecord.lookupByStorageClass(res)
        except KeyError:
            res = AuxiliaryRecord
        return res

class ShortName(pStruct):
    _fields_ = [
        (dword, 'IsShort'),
        (off_t, 'Offset')
    ]

    def get(self, stringtable):
        '''resolve the Name of the object utilizing the provided StringTable if necessary'''
        if int(self['IsShort']) != 0x00000000:
            res = self.serialize()
            try:
                length = res.index('\x00')
                res = res[:length]
            except ValueError:
                pass
            return res
        return stringtable.get( int(self['Offset']) )

class Symbol(pStruct):
    _fields_ = [
        (ShortName, 'Name'),
        (dword, 'Value'),
        (IMAGE_SYM, 'SectionNumber'),
        (IMAGE_SYM_TYPE, 'Type'),
        (IMAGE_SYM_CLASS, 'StorageClass'),
        (uint8, 'NumberOfAuxSymbols')
    ]

class SymbolTableEntry(pStruct):
    _fields_ = [
        (Symbol, 'symbol'),
        (lambda x: dyn.array(x['symbol']['StorageClass'].getAuxType(), x['symbol']['NumberOfAuxSymbols'])(), 'aux')
    ]

class SymbolTable(pTerminatedArray):
    _object_ = SymbolTableEntry
    length = 0

    def isTerminator(self, n):
        count = len(n['aux'])
        self.__length += 1+count
        return not(self.__length < self.totallength)

    def deserialize(self, iterable):
        self.__length = 0
        super(SymbolTable, self).deserialize(iterable)
        assert self.__length == self.totallength, '%d != %d | %d'% (self.__length, self.totallength, self.length)

class AuxiliaryRecord(pStruct):
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

class SectionAuxiliaryRecord(AuxiliaryRecord):
    storageClass = 3
    _fields_ = [
        (uint32, 'Length'),
        (uint16, 'NumberOfRelocations'),
        (uint16, 'NumberOfLinenumbers'),
        (dword, 'CheckSum'),
        (word, 'Number'),
        (byte, 'Selection'),
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

class StringTable(pStruct):
    _fields_ = [
        (uint32, 'Size'),
        (lambda self: dyn.block(self['Size'] - 4)(), 'Data')
    ]

    def get(self, offset):
        '''return the string associated with a particular offset'''
        data = self.serialize()
        res = data[offset:]
        try:
            length = res.index('\x00')
            res = res[:length]
        except ValueError:
            pass
        return res

def getFileContents(filename):
    input = file(filename, 'rb')
    res = input.read()
    input.close()
    return res

class File(pStruct):
    _fields_ = [
        (FileHeader, 'Header'),
        (lambda x: dyn.array( SectionTable, int(x['Header']['NumberOfSections']) )(), 'Sections')
    ]

if __name__ == '__main__':
    filedata = getFileContents('../obj/inject-test.obj')

    ## parse the file
    coff = File()
    coff.deserialize(filedata)
    print repr(coff)

    ## prove we can get section data
    print '\n'.join([repr(x) for x in coff['Sections']])

    ## handle relocations(?)
    sections = coff['Sections']
    x = sections[-1]
    relocations = x.getRelocations(filedata)
    print '\n'.join([repr(x) for x in relocations])

    ## prove we can view the symbol table
    symboltable, stringtable = coff['Header'].getSymbolAndStringTable(filedata)
    print '\n'.join([repr(x) for x in symboltable])
    print '\n'.join([repr(x['symbol']) for x in symboltable])
    print '\n'.join([repr(x['aux']) for x in symboltable])

    ## prove we can view the string table
    print repr(stringtable)

    ## prove we can do both
    print '\n'.join([repr(x['symbol']['Name'].get(stringtable)) for x in symboltable])
