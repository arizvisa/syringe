from base import *
import header

### some types
class Elf32_Sym(pstruct.type):
    _fields_ = [
        (Elf32_Word, 'st_name'),
        (Elf32_Addr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (pint.uint8_t, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf32_Half, 'st_shndx')
    ]

### each section type
class Type(Record):
    cache = {}

# data defined by the section header table
class SHT_PROGBITS(object):
    type = 1

@Type.Define
class SHT_SYMTAB(parray.block):
    type = 2
    _object_ = Elf32_Sym

@Type.Define
class SHT_STRTAB(parray.block):
    type = 3
    _object_ = pstr.szstring

    def get(self, offset):
        return self.at(offset + self.getoffset(), recurse=False).get()

class SHT_RELA(object): type = 4
class SHT_HASH(object): type = 5
class SHT_DYNAMIC(object): type = 6
class SHT_NOTE(object): type = 7
class SHT_NOBITS(object): type = 8
class SHT_REL(object): type = 9
class SHT_SHLIB(object): type = 10
class SHT_DYNSYM(object): type = 11
