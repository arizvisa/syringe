from .base import *
from . import dynamic

class _p_type(pint.enum):
    _values_ = [
        ('PT_NULL', 0),
        ('PT_LOAD', 1),
        ('PT_DYNAMIC', 2),
        ('PT_INTERP', 3),
        ('PT_NOTE', 4),
        ('PT_SHLIB', 5),
        ('PT_PHDR', 6),
        ('PT_GNU_EH_FRAME', 0x6474e550),
        ('PT_GNU_STACK', 0x6474e551),
        ('PT_GNU_RELRO', 0x6474e552),
        ('PT_LOPROC', 0x70000000),
        ('PT_HIPROC', 0x7fffffff),
    ]

class _p_flags(pbinary.flags):
    # Elf32_Word
    _fields_ = [
        (4, 'PF_MASKPROC'),
        (1+8+16, 'SHF_RESERVED'),
        (1, 'PF_R'),
        (1, 'PF_W'),
        (1, 'PF_X'),
    ]

def _p_offset(size):
    def p_offset(self):
        type = Type.get(self['p_type'].li.int())
        #return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda x:int(s.getparent(ElfXX_Phdr)['p_filesz'].li)), lambda s: s.getparent(ElfXX_File), Elf32_Off)

        base = self.getparent(ElfXX_File)
        result = dyn.clone(type, blocksize=lambda _:self['p_filesz'].li.int())
        return dyn.rpointer(result, base, size)
    return p_offset

### Program Headers
class Elf32_Phdr(pstruct.type, ElfXX_Phdr):
    class p_type(_p_type, Elf32_Word): pass
    class p_flags(_p_flags): pass   # XXX
    _fields_ = [
        (p_type, 'p_type'),
        (_p_offset(Elf32_Off), 'p_offset'),
        (Elf32_Addr, 'p_vaddr'),
        (Elf32_Addr, 'p_paddr'),
        (Elf32_Word, 'p_filesz'),
        (Elf32_Word, 'p_memsz'),
        (p_flags, 'p_flags'),
        (Elf32_Word, 'p_align'),
    ]

class Elf64_Phdr(pstruct.type, ElfXX_Phdr):
    class p_type(_p_type, Elf64_Word): pass
    class p_flags(_p_flags): pass   # XXX
    _fields_ = [
        (p_type, 'p_type'),
        (p_flags, 'p_flags'),
        (_p_offset(Elf64_Off), 'p_offset'),
        (Elf64_Addr, 'p_vaddr'),
        (Elf64_Addr, 'p_paddr'),
        (Elf64_Xword, 'p_filesz'),
        (Elf64_Xword, 'p_memsz'),
        (Elf64_Xword, 'p_align'),
    ]

### segment type definitions
class Type(ptype.definition):
    cache = {}

@Type.define
class PT_LOAD(ptype.block):
    type = 1

@Type.define
class PT_DYNAMIC(parray.block):
    type = 2
    _object_ = dynamic.Elf32_Dyn

    def search(self, entry):
        if ptype.istype(entry):
            entry = entry.type
        return [x['d_val'] for x in self if x['d_tag'].int() == entry]

@Type.define
class PT_INTERP(pstr.szstring):
    type = 3

@Type.define
class PT_NOTE(parray.block):
    type = 4
    class _object_(pstruct.type):
        _fields_ = [
            (Elf32_Word, 'namesz'),
            (Elf32_Word, 'descsz'),
            (Elf32_Word, 'type'),
            (lambda s: dyn.clone(pstr.string, length=s['namesz'].li.int()), 'name'),
            (dyn.align(4), 'name_pad'),
            (lambda s: dyn.array(Elf32_Word, s['descsz'].li.int()/4), 'desc'),
            (dyn.align(4), 'desc_pad'),
        ]

@Type.define
class PT_SHLIB(ptype.block):
    type = 5
    # FIXME: this is platform-specific and not in the standard

@Type.define
class PT_PHDR(parray.block):
    type = 6
    _object_ = Elf32_Phdr

@Type.define
class PT_GNU_EH_FRAME(ptype.block):
    type = 0x6474e550
    # FIXME: this structure is part of the dwarf standard

@Type.define
class PT_GNU_STACK(ptype.block):
    type = 0x6474e551

@Type.define
class PT_GNU_RELRO(ptype.block):
    type = 0x6474e552
