import ptypes
from . import section,segment
from .base import *

class e_flags(ptype.definition):
    cache = {}
    unknown = Elf32_Word

@e_flags.define(type=e_machine.byname('EM_SPARC'))
@e_flags.define(type=e_machine.byname('EM_SPARC32PLUS'))
@e_flags.define(type=e_machine.byname('EM_SPARCV9'))
class e_flags_sparc(pbinary.flags):
    VENDOR_MASK = 0x00ffff00
    class EF_SPARCV9_MM(pbinary.enum):
        width = 2
        _values_ = [
            ('EF_SPARCV9_TSO', 0),
            ('EF_SPARCV9_PSO', 1),
            ('EF_SPARCV9_RMO', 2),
        ]
    class EF_SPARC_EXT_MASK(pbinary.flags):
        _fields_ = [
            (12, 'EF_SPARC_EXT'),
            (1, 'EF_SPARC_SUN_US3'),
            (1, 'EF_SPARC_HAL_R1'),
            (1, 'EF_SPARC_SUN_US1'),
            (1, 'EF_SPARC_32PLUS'),
        ]

    _fields_ = [
        (8, 'EF_SPARC_NONE'),
        (EF_SPARC_EXT_MASK, 'EF_SPARC_EXT_MASK'),
        (6, 'EF_SPARC_UNKNOWN'),
        (EF_SPARCV9_MM, 'EF_SPARCV9_MM'),
    ]

@e_flags.define
class e_flags_arm(pbinary.flags):
    type = e_machine.byname('EM_ARM')
    ABI_MASK = 0xff000000
    GCC_MASK = 0x00400FFF
    class EF_ARM_GCC_MASK(pbinary.struct):
        _fields_ = [
            (1, 'EF_ARM_ABI_UNKNOWN'),
            (1, 'EF_ARM_ABI_FLOAT_HARD'),
            (1, 'EF_ARM_ABI_FLOAT_SOFT'),
            (9, 'EF_ARM_GCC_UNKNOWN'),
        ]
    _fields_ = [
        (8, 'EF_ARM_ABI'),
        (1, 'EF_ARM_BE8'),
        (1, 'EF_ARM_GCC_LEGACY'),
        (2, 'EF_ARM_GCC_ALIGN'),
        (8, 'EF_ARM_UNKNOWN'),
        (EF_ARM_GCC_MASK, 'EF_ARM_GCC_MASK'),
    ]

@e_flags.define
class e_flags_mips(pbinary.flags):
    type = e_machine.byname('EM_MIPS')
    class EF_MIPS_ARCH_(pbinary.enum):
        width = 4
        _values_ = [
            ('EF_MIPS_ARCH_1', 0),
            ('EF_MIPS_ARCH_2', 1),
            ('EF_MIPS_ARCH_3', 2),
            ('EF_MIPS_ARCH_4', 3),
            ('EF_MIPS_ARCH_5', 4),
            ('EF_MIPS_ARCH_32', 5),
            ('EF_MIPS_ARCH_64', 6),
            ('EF_MIPS_ARCH_32R2', 7),
            ('EF_MIPS_ARCH_64R2', 8),
        ]
    class EF_MIPS_ARCH_ASE_(pbinary.enum):
        width = 4
        _values_ = [
            ('EF_MIPS_ARCH_ASE_MDMX', 8),
            ('EF_MIPS_ARCH_ASE_M16', 4),
            ('EF_MIPS_ARCH_ASE_MICROMIPS', 2),
        ]
    class E_MIPS_ABI_(pbinary.enum):
        width = 4
        _values_ = [
            ('E_MIPS_ABI_O32', 1),
            ('E_MIPS_ABI_O64', 2),
            ('E_MIPS_ABI_EABI32', 3),
            ('E_MIPS_ABI_EABI64', 4),
        ]
    _fields_ = [
        (EF_MIPS_ARCH_, 'ARCH'),
        (EF_MIPS_ARCH_ASE_, 'ASE'),
        (8, 'EF_MIPS_ARCH_UNUSED'),
        (E_MIPS_ABI_, 'ABI'),
        (1, 'EF_MIPS_ARCH_RESERVED'),
        (1, 'E_MIPS_NAN2008'),
        (1, 'E_MIPS_FP64'),
        (1, 'EF_MIPS_32BITMODE'),
        (1, 'EF_MIPS_OPTIONS_FIRST'),
        (1, 'EF_MIPS_ABI_ON32'),
        (1, 'EF_MIPS_ABI2'),
        (1, 'EF_MIPS_64BIT_WHIRL'),
        (1, 'EF_MIPS_XGOT'),
        (1, 'EF_MIPS_CPIC'),
        (1, 'EF_MIPS_PIC'),
        (1, 'EF_MIPS_NOREORDER'),
    ]

### 32-bit
class Elf32_Ehdr(pstruct.type, ElfXX_Ehdr):
    def _ent_array(self, type, size, length):
        t = dyn.clone(type, blocksize=lambda s:self[size].li.int())
        return dyn.array(t, self[length].li.int())

    def __e_flags(self):
        res = self['e_machine'].li.int()
        return e_flags.get(res, type=res)

    _fields_ = [
        (e_type, 'e_type'),
        (e_machine, 'e_machine'),
        (e_version, 'e_version'),
        (Elf32_Addr, 'e_entry'),
        (lambda self: dyn.clone(Elf32_Off, _object_=lambda s: self._ent_array(segment.Elf32_Phdr, 'e_phentsize', 'e_phnum')), 'e_phoff'),
        (lambda self: dyn.clone(Elf32_Off, _object_=lambda s: self._ent_array(section.Elf32_Shdr, 'e_shentsize', 'e_shnum')), 'e_shoff'),
        (__e_flags, 'e_flags'),
        (Elf32_Half, 'e_ehsize'),
        (Elf32_Half, 'e_phentsize'),
        (Elf32_Half, 'e_phnum'),
        (Elf32_Half, 'e_shentsize'),
        (Elf32_Half, 'e_shnum'),
        (Elf32_Half, 'e_shstrndx'),
    ]

    def blocksize(self):
        return self['e_ehsize'].li.int()-e_ident().a.blocksize()

    def stringtable(self):
        res, index = self['e_shoff'].d.li, self['e_shstrndx'].int()
        if index < len(res):
            return res[index]['sh_offset'].d.li
        raise ptypes.error.NotFoundError(self, 'stringtable')

### 64-bit
class Elf64_Ehdr(pstruct.type, ElfXX_Ehdr):
    def _ent_array(self, type, size, length):
        t = dyn.clone(type, blocksize=lambda s:self[size].li.int())
        return dyn.array(t, self[length].li.int())

    def __e_flags(self):
        res = self['e_machine'].li.int()
        return e_flags.get(res, type=res)

    _fields_ = [
        (e_type, 'e_type'),
        (e_machine, 'e_machine'),
        (e_version, 'e_version'),
        (Elf64_Addr, 'e_entry'),
        (lambda self: dyn.clone(Elf64_Off, _object_=lambda s: self._ent_array(segment.Elf64_Phdr, 'e_phentsize', 'e_phnum')), 'e_phoff'),
        (lambda self: dyn.clone(Elf64_Off, _object_=lambda s: self._ent_array(section.Elf64_Shdr, 'e_shentsize', 'e_shnum')), 'e_shoff'),
        (__e_flags, 'e_flags'),
        (Elf64_Half, 'e_ehsize'),
        (Elf64_Half, 'e_phentsize'),
        (Elf64_Half, 'e_phnum'),
        (Elf64_Half, 'e_shentsize'),
        (Elf64_Half, 'e_shnum'),
        (Elf64_Half, 'e_shstrndx'),
    ]
    def blocksize(self):
        return self['e_ehsize'].li.int() - e_ident().a.blocksize()

    def stringtable(self):
        res, index = self['e_shoff'].d.li, self['e_shstrndx'].int()
        if index < len(res):
            return res[index]['sh_offset'].d.li
        raise ptypes.error.NotFoundError(self, 'stringtable')
