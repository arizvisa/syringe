import header,dynamic
from base import *

### generic
class sh_name(Elf32_Word):
    def summary(self):
        return self.str()

    def str(self):
        ofs = self.num()
        stringtable = self.getparent(header.Elf32_Ehdr).stringtable()
        return str(stringtable.get(ofs))

class sh_type(pint.enum, Elf32_Word):
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

class sh_flags(pbinary.struct):
    # Elf32_Word
    _fields_ = [
        (4, 'SHF_MASKPROC'),
        (1+8+16, 'SHF_RESERVED'),
        (1, 'SHF_EXECINSTR'),
        (1, 'SHF_ALLOC'),
        (1, 'SHF_WRITE'),
    ]

### 32-bit
class Elf32_Shdr(pstruct.type):
    def __sh_offset(self):
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(header.Elf32_Ehdr), type=Elf32_Off), 'sh_offset'),
        t = int(self['sh_type'].l)
        type = Type.get(t)
        return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda _:int(s.getparent(Elf32_Shdr)['sh_size'].l)), lambda s: s.getparent(header.Elf32_Ehdr), type=Elf32_Off)

    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (Elf32_Addr, 'sh_addr'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(header.Elf32_Ehdr), type=Elf32_Off), 'sh_offset'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(header.Elf32_Ehdr), type=Elf32_Off), 'sh_offset'),
#        (__sh_offset, 'sh_offset'),
        (Elf32_Word, 'sh_size'),
        (Elf32_Word, 'sh_link'),
        (Elf32_Word, 'sh_info'),
        (Elf32_Word, 'sh_addralign'),
        (Elf32_Word, 'sh_entsize'),
    ]

## some types
class Elf32_Sym(pstruct.type):
    _fields_ = [
        (Elf32_Word, 'st_name'),
        (Elf32_Addr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (pint.uint8_t, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf32_Half, 'st_shndx')
    ]

class Elf32_Rel(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word , 'r_info'),
    ]

class Elf32_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word, 'r_info'),
        (Elf32_Sword, 'r_addend'),
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

    def get(self, offset):
        return self.at(offset + self.getoffset(), recurse=False).str()

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
        (lambda s: dyn.array(Elf32_Word, s['nbucket'].l.int()), 'bucket'),
        (lambda s: dyn.array(Elf32_Word, s['nchain'].l.int()), 'chain'),
    ]

@Type.define
class SHT_DYNAMIC(dynamic.Elf32_DynArray):
    type = 6

@Type.define
class SHT_NOTE(parray.block):
    type = 7
    class _object_(pstruct.type):
        _fields_ = [
            (Elf32_Word, 'namesz'),
            (Elf32_Word, 'descsz'),
            (Elf32_Word, 'type'),
            (lambda s: dyn.clone(pstr.string, length=s['namesz'].l.int()), 'name'),
            (dyn.align(4), 'name_pad'),
            (lambda s: dyn.array(Elf32_Word, s['descsz'].l.int()/4), 'desc'),
            (dyn.align(4), 'desc_pad'),
        ]

@Type.define
class SHT_NOBITS(ptype.block):
    type = 8

@Type.define
class SHT_REL(parray.block):
    type = 9
    _object_ = Elf32_Rel

@Type.define
class SHT_SHLIB(ptype.block):
    type = 10
    # FIXME: this is platform-specific and not in the standard

@Type.define
class SHT_DYNSYM(parray.block):
    type = 11
    _object_ = Elf32_Sym

### 64-bit
