import section,segment
from base import *

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
            t = dyn.clone(type, blocksize=lambda s:root[size].int())
            return dyn.array(t, int(root[length]))
        return array

    _fields_ = [
        (__e_ident, 'e_ident'),
        (__e_type, 'e_type'),
        (__e_machine, 'e_machine'),
        (Elf32_Word, 'e_version'),
        (Elf32_Addr, 'e_entry'),
        (dyn.rpointer(lambda s: s.parent._ent_array(segment.Elf32_Phdr, 'e_phentsize', 'e_phnum'), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off), 'e_phoff'),
        (dyn.rpointer(lambda s: s.parent._ent_array(section.Elf32_Shdr, 'e_shentsize', 'e_shnum'), lambda s: s.getparent(Elf32_Ehdr), type=Elf32_Off), 'e_shoff'),
        (Elf32_Word, 'e_flags'),
        (Elf32_Half, 'e_ehsize'),
        (Elf32_Half, 'e_phentsize'),
        (Elf32_Half, 'e_phnum'),
        (Elf32_Half, 'e_shentsize'),
        (Elf32_Half, 'e_shnum'),
        (Elf32_Half, 'e_shstrndx'),
    ]

    def blocksize(self):
        return self['e_ehsize'].l.int()

    def stringtable(self):
        index = self['e_shstrndx'].int()
        return self['e_shoff'].d.l[index]['sh_offset'].d.l
