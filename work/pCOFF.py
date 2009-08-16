import sys
sys.path.append('/work/code/ptypes.git')

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

class Symbol(pStruct):
    _fields_ = [
        (ShortName, 'Name'),
        (dword, 'Value'),
        (IMAGE_SYM, 'SectionNumber'),
        (IMAGE_SYM_TYPE, 'Type'),
        (IMAGE_SYM_CLASS, 'StorageClass'),
        (uint8, 'NumberOfAuxSymbols')
    ]

class SymbolTable(pArray):
    _object_ = None

    def deserializeAux(self, iterable, cls, count):
        iterable = iter(iterable)
        res = []
        while count > 0:
            x = self.newchild(cls)
            x.deserialize(iterable)
            res.append(x)
            count -= 1  
        return res

    def deserialize(self, iterable):
        iterable = iter(iterable)
        self.value = []
        length = len(self)
        
        while length > 0:
            res = self.newchild(Symbol)
            res.deserialize(iterable)
            self.value.append(res)
            length -= 1

            count = res['NumberOfAuxSymbols']
            auxtype = res['StorageClass'].getAuxType()

            res = self.deserializeAux(iterable, res['StorageClass'].getAuxType(), count)
            self.value.extend(res)
            length -= len(res)
        return

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

    def lookupByOffset(self, offset):
        data = self.serialize()
        res = data[offset:]
        try:
            length = res.index('\x00')
            res = res[:length]
        except ValueError:
            pass
        return res

def getFileContents(filename):
    input = file('../obj/inject-test.obj', 'rb')
    res = input.read()
    input.close()
    return res

if __name__ == '__main__':
    res = getFileContents('../obj/inject-test.obj')
    filedata, stream = res, iter(res)

    header = FileHeader()
    header.deserialize(stream)
    print header

    if False:
        sections = dyn.array( SectionTable, int(header['NumberOfSections']) )()
        sections.deserialize(stream)

        print '\n'.join([repr(x['Name']) for x in sections])
        print '\n'.join([repr(x) for x in sections])

        res = []
        for x in sections:
            start = int(x['PointerToRawData'])
            data = filedata[ start : start + int(x['SizeOfRawData']) ]
            res.append( (x['Name'].serialize(), data) )

        x = sections[-1]
        ofs,length = (int(x['PointerToRelocations']), int(x['NumberOfRelocations']))
        
        data = filedata[ ofs: ]
        relocations = dyn.array(Relocation, length)()
        relocations.deserialize(data)
        print '\n'.join([repr(x) for x in relocations])

    ## symbol table shit
    ofs,length = int(header['PointerToSymbolTable']), int(header['NumberOfSymbols'])
    data = filedata[ ofs: ]

    stream = iter(data)
    symboltable = SymbolTable()
    symboltable.length = length
    symboltable.deserialize(stream)

    stringtable = StringTable()
    stringtable.deserialize(stream)

    ## list all long symbol names
    if False:
        res = [x for x in symboltable if type(x) is Symbol]
        res = [x['Name'] for x in res if x['Name']['IsShort'] == 0]
        res = [int(x['Offset']) for x in res]
        print repr(res)

        res = [stringtable.lookupByOffset(x) for x in res]
        print '\n'.join([repr(x) for x in res])

    print '\n------------ '.join([repr(x) for x in symboltable])
#    print utils.hexdump(stringtable['Data'].serialize())
