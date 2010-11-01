#import ...         # at bottom of file
from base import *

class Elf32_Phdr(pstruct.type):
    class __p_type(pint.enum, Elf32_Word):
        _values_ = [
            ('PT_NULL', 0),
            ('PT_LOAD', 1),
            ('PT_DYNAMIC', 2),
            ('PT_INTERP', 3),
            ('PT_NOTE', 4),
            ('PT_SHLIB', 5),
            ('PT_PHDR', 6),
            ('PT_LOPROC', 0x70000000),
            ('PT_HIPROC', 0x7fffffff),
        ]

    def __p_offset(self):
        t = int(self['p_type'].l)
        try:
            type = segment.Type.Lookup(t)
        except KeyError:
            type = dyn.clone(segment.Type.Unknown, type=t)

        # XXX: there's that difference here between the filesz and memsz
        return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda x:int(s.getparent(Elf32_Phdr)['p_filesz'].l)), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off)

    class __p_flags(pbinary.struct):
        # Elf32_Word
        _fields_ = [
            (4, 'PF_MASKPROC'),
            (1+8+16, 'SHF_RESERVED'),
            (1, 'PF_R'),
            (1, 'PF_W'),
            (1, 'PF_X'),
        ]

    _fields_ = [
        (__p_type, 'p_type'),
        (__p_offset, 'p_offset'),
        (Elf32_Addr, 'p_vaddr'),
        (Elf32_Addr, 'p_paddr'),
        (Elf32_Word, 'p_filesz'),
        (Elf32_Word, 'p_memsz'),
        (__p_flags, 'p_flags'),
        (Elf32_Word, 'p_align'),
    ]

class Elf32_Shdr(pstruct.type):
    class __sh_type(pint.enum, Elf32_Word):
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
            ('SHT_LOPROC', 0x70000000),
            ('SHT_HIPROC', 0x7fffffff),
            ('SHT_LOUSER', 0x80000000),
            ('SHT_HIUSER', 0xffffffff),
        ]

    class __sh_flags(pbinary.struct):
        # Elf32_Word
        _fields_ = [
            (4, 'SHF_MASKPROC'),
            (1+8+16, 'SHF_RESERVED'),
            (1, 'SHF_EXECINSTR'),
            (1, 'SHF_ALLOC'),
            (1, 'SHF_WRITE'),
        ]

    def __sh_offset(self):
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off), 'sh_offset'),
        t = int(self['sh_type'].l)
        try:
            type = section.Type.Lookup(t)
        except KeyError:
            type = dyn.clone(section.Type.Unknown)
        return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda _:int(s.getparent(Elf32_Shdr)['sh_size'].l)), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off)

    class __sh_name(Elf32_Word):
        def __repr__(self):
            return ' '.join([self.name(), self.get()])

        def get(self):
            stringtable = self.getparent(Elf32_Ehdr).stringtable()
            return str(stringtable.get(int(self)))

    _fields_ = [
        (__sh_name, 'sh_name'),
        (__sh_type, 'sh_type'),
        (__sh_flags, 'sh_flags'),
        (Elf32_Addr, 'sh_addr'),
        (__sh_offset, 'sh_offset'),
        (Elf32_Word, 'sh_size'),
        (Elf32_Word, 'sh_link'),
        (Elf32_Word, 'sh_info'),
        (Elf32_Word, 'sh_addralign'),
        (Elf32_Word, 'sh_entsize'),
    ]

EI_NIDENT=16
class Elf32_Ehdr(pstruct.type):
    class __e_ident(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'EI_MAG'),
            (pint.uint8_t, 'EI_CLASS'),
            (pint.uint8_t, 'EI_DATA'),
            (pint.uint8_t, 'EI_VERSION'),
            (dyn.block(EI_NIDENT-7), 'EI_PAD'),
        ]
        def blocksize(self):
            return EI_NIDENT

    class __e_type(pint.enum, Elf32_Half):
        _values_ = [
            ('ET_NONE', 0),
            ('ET_REL', 1),
            ('ET_EXEC', 2),
            ('ET_DYN', 3),
            ('ET_CORE', 4),
            ('ET_LOPROC', 0xff00),
            ('ET_HIPROC', 0xffff),
        ]

    class __e_machine(pint.enum, Elf32_Half):
        _values_ = [
            ('ET_NONE', 0),
            ('EM_M32', 1),
            ('EM_SPARC', 2),
            ('EM_386', 3),
            ('EM_68K', 4),
            ('EM_88K', 5),
            ('EM_860', 7),
            ('EM_MIPS', 8),
            ('EM_MIPS_RS4_BE', 10),
#            ('RESERVED', 11-16),
        ]

    def _ent_array(self, type, size, length):
        def array(s):
            root = self.getparent(Elf32_Ehdr)
            t = dyn.clone(type, blocksize=lambda s:int(root[size]))
            return dyn.array(t, int(root[length]))
        return array

    _fields_ = [
        (__e_ident, 'e_ident'),
        (__e_type, 'e_type'),
        (__e_machine, 'e_machine'),
        (Elf32_Word, 'e_version'),
        (Elf32_Addr, 'e_entry'),
        (dyn.rpointer(lambda s: s.parent._ent_array(Elf32_Phdr, 'e_phentsize', 'e_phnum'), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off), 'e_phoff'),
        (dyn.rpointer(lambda s: s.parent._ent_array(Elf32_Shdr, 'e_shentsize', 'e_shnum'), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off), 'e_shoff'),
        (Elf32_Word, 'e_flags'),
        (Elf32_Half, 'e_ehsize'),
        (Elf32_Half, 'e_phentsize'),
        (Elf32_Half, 'e_phnum'),
        (Elf32_Half, 'e_shentsize'),
        (Elf32_Half, 'e_shnum'),
        (Elf32_Half, 'e_shstrndx'),
    ]

    def blocksize(self):
        return int(self['e_ehsize'].l)

    def stringtable(self):
        index = int(self['e_shstrndx'])
        return self['e_shoff'].d.l[index]['sh_offset'].d.l

import section,segment,dynamic  # XXX: down here so we can umm.. tail-recurse ;)
