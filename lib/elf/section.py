from .base import *

### generic
class _sh_name(pint.uint_t):
    def summary(self):
        return self.str()

    def str(self):
        ofs = self.num()
        stringtable = self.getparent(ElfXX_Ehdr).stringtable()
        res = stringtable.extract(ofs)
        return res.str()

class _sh_type(pint.enum):
    _values_ = [
        ('SHT_NULL', 0),
        ('SHT_PROGBITS', 1),
        ('SHT_SYMTAB', 2),
        ('SHT_STRTAB', 3),
        ('SHT_RELA', 4),
        ('SHT_HASH', 5),
        ('SHT_DYNAMIC', 6),
        ('SHT_NOTE', 7),
        ('SHT_NOBITS', 8),
        ('SHT_REL', 9),
        ('SHT_SHLIB', 10),
        ('SHT_DYNSYM', 11),
        ('SHT_UNKNOWN12', 12),
        ('SHT_UNKNOWN13', 13),
        ('SHT_INIT_ARRAY', 14),
        ('SHT_FINI_ARRAY', 15),
        ('SHT_PREINIT_ARRAY', 16),
        ('SHT_GROUP', 17),
        ('SHT_SYMTAB_SHNDX', 18),
        ('SHT_NUM', 19),

        ('SHT_LOOS', 0x60000000),
        ('SHT_GNU_HASH', 0x6ffffff6),
        ('SHT_GNU_LIBLIST', 0x6ffffff7),
        ('SHT_CHECKSUM', 0x6ffffff8),
        ('SHT_LOSUNW', 0x6ffffffa),
        ('SHT_SUNW_move', 0x6ffffffa),
        ('SHT_SUNW_COMDAT', 0x6ffffffb),
        ('SHT_SUNW_syminfo', 0x6ffffffc),
        ('SHT_GNU_verdef', 0x6ffffffd),
        ('SHT_GNU_verneed', 0x6ffffffe),
        ('SHT_GNU_versym', 0x6fffffff),
        ('SHT_HISUNW', 0x6fffffff),
        ('SHT_HIOS', 0x6fffffff),

        ('SHT_LOPROC', 0x70000000),
        ('SHT_HIPROC', 0x7fffffff),
        ('SHT_LOUSER', 0x80000000),
        ('SHT_HIUSER', 0xffffffff),
    ]

class _sh_flags(pbinary.flags):
    # Elf32_Word
    _fields_ = [
        (4, 'SHF_MASKPROC'),
        (1+8+16, 'SHF_RESERVED'),
        (1, 'SHF_EXECINSTR'),
        (1, 'SHF_ALLOC'),
        (1, 'SHF_WRITE'),
    ]

def _sh_offset(size):
    def sh_offset(self):
        type = Type.get(self['sh_type'].li.num())   # XXX: not 64-bit
        #return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda _:int(s.getparent(Elf32_Shdr)['sh_size'].li)), lambda s: s.getparent(ElfXX_File), Elf32_Off)

        base = self.getparent(ElfXX_File)
        result = dyn.clone(type, blocksize=lambda _: self['sh_size'].li.num())
        return dyn.rpointer(result, base, size)
    return sh_offset

### Section Headers
class Elf32_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf32_Word): pass
    class sh_type(_sh_type, Elf32_Word): pass
    class sh_flags(_sh_flags):
        _fields_ = _sh_flags._fields_
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (Elf32_Addr, 'sh_addr'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(ElfXX_Header), Elf32_Off), 'sh_offset'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(ElfXX_Header), Elf32_Off), 'sh_offset'),
        (_sh_offset(Elf32_Off), 'sh_offset'),
        (Elf32_Word, 'sh_size'),
        (Elf32_Word, 'sh_link'),
        (Elf32_Word, 'sh_info'),
        (Elf32_Word, 'sh_addralign'),
        (Elf32_Word, 'sh_entsize'),
    ]

class Elf64_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf64_Word): pass
    class sh_type(_sh_type, Elf64_Word): pass
    class sh_flags(_sh_flags):
        _fields_ = [(32,'SHF_RESERVED2')] + _sh_flags._fields_
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (Elf64_Addr, 'sh_addr'),
        (_sh_offset(Elf64_Off), 'sh_offset'),
        (Elf64_Xword, 'sh_size'),
        (Elf64_Word, 'sh_link'),
        (Elf64_Word, 'sh_info'),
        (Elf64_Xword, 'sh_addralign'),
        (Elf64_Xword, 'sh_entsize'),
    ]

## some types
class Elf32_Section(pint.uint16_t): pass
class Elf64_Section(pint.uint16_t): pass
class Elf32_Sym(pstruct.type):
    _fields_ = [
        (Elf32_Word, 'st_name'),
        (Elf32_Addr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (pint.uint8_t, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf32_Section, 'st_shndx')
    ]
class Elf64_Sym(pstruct.type):
    _fields_ = [
        (Elf64_Word, 'st_name'),
        (Elf64_Addr, 'st_value'),
        (Elf64_Xword, 'st_size'),
        (pint.uint8_t, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf64_Section, 'st_shndx')
    ]

class Elf32_Rel(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word , 'r_info'),
    ]
class Elf64_Rel(pstruct.type):
    _fields_ = [
        (Elf64_Addr, 'r_offset'),
        (Elf64_Word , 'r_info'),
        (pint.uint8_t, 'r_type'),
        (pint.uint8_t, 'r_type2'),
        (pint.uint8_t, 'r_type3'),
        (pint.uint8_t, 'r_ssym'),
        (Elf64_Word, 'r_sym'),
    ]

class Elf32_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word, 'r_info'),
        (Elf32_Sword, 'r_addend'),
    ]
class Elf64_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word, 'r_info'),
        (Elf32_Sword, 'r_addend'),
        (pint.uint8_t, 'r_type'),
        (pint.uint8_t, 'r_type2'),
        (pint.uint8_t, 'r_type3'),
        (pint.uint8_t, 'r_ssym'),
        (Elf64_Word, 'r_sym'),
        (Elf64_Sxword, 'r_addend'),
    ]

### each section type
class Type(ptype.definition):
    cache = {}

# data defined by the section header table
@Type.define
class SHT_PROGBITS(ptype.block):
    type = 1

@Type.define
class SHT_SYMTAB(parray.block):
    type = 2
    _object_ = Elf32_Sym

@Type.define
class SHT_STRTAB(parray.block):
    type = 3
    _object_ = pstr.szstring

    def extract(self, offset):
        return self.at(offset + self.getoffset(), recurse=False)

@Type.define
class SHT_RELA(parray.block):
    type = 4
    _object_ = Elf32_Rela

@Type.define
class SHT_HASH(pstruct.type):
    type = 5
    _fields_ = [
        (Elf32_Word, 'nbucket'),
        (Elf32_Word, 'nchain'),
        (lambda s: dyn.array(Elf32_Word, s['nbucket'].li.num()), 'bucket'),
        (lambda s: dyn.array(Elf32_Word, s['nchain'].li.num()), 'chain'),
    ]

from . import segment
@Type.define
class SHT_DYNAMIC(segment.PT_DYNAMIC):
    type = 6

@Type.define
class SHT_NOTE(segment.PT_NOTE):
    type = 7

@Type.define
class SHT_NOBITS(ptype.block):
    type = 8

@Type.define
class SHT_REL(parray.block):
    type = 9
    _object_ = Elf32_Rel

@Type.define
class SHT_SHLIB(segment.PT_SHLIB):
    type = 10

@Type.define
class SHT_DYNSYM(parray.block):
    type = 11
    _object_ = Elf32_Sym
