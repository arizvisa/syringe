from .base import *
from . import dynamic

class _p_type(pint.enum):
    PT_LOPROC, PT_HIPROC = 0x70000000, 0x7fffffff
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

        ('PT_ARM_ARCHEXT', 0x70000000),  # Platform architecture compatibility information
        ('PT_ARM_UNWIND', 0x70000001),  # Exception unwind tables
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

def _p_offset(ptr):
    def p_size(self):
        p = self.getparent(ElfXX_Phdr)
        return p['p_filesz'].li.int()

    def p_offset(self):
        res = self['p_type'].li
        target = Type.get(res.int(), type=res.int(), blocksize=p_size)
        return dyn.clone(ptr, _object_=target)
    return p_offset

### Program Headers
class Elf32_Phdr(pstruct.type, ElfXX_Phdr):
    class p_type(_p_type, Elf32_Word): pass
    class p_flags(_p_flags): pass   # XXX

    def __p_unknown(self):
        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, self.blocksize() - res))

    _fields_ = [
        (p_type, 'p_type'),
        (_p_offset(Elf32_Off), 'p_offset'),
        (Elf32_Addr, 'p_vaddr'),
        (Elf32_Addr, 'p_paddr'),
        (Elf32_Word, 'p_filesz'),
        (Elf32_Word, 'p_memsz'),
        (p_flags, 'p_flags'),
        (Elf32_Word, 'p_align'),
        (__p_unknown, 'p_unknown'),
    ]

class Elf64_Phdr(pstruct.type, ElfXX_Phdr):
    class p_type(_p_type, Elf64_Word): pass
    class p_flags(_p_flags): pass   # XXX

    def __p_unknown(self):
        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, self.blocksize() - res))

    _fields_ = [
        (p_type, 'p_type'),
        (p_flags, 'p_flags'),
        (_p_offset(Elf64_Off), 'p_offset'),
        (Elf64_Addr, 'p_vaddr'),
        (Elf64_Addr, 'p_paddr'),
        (Elf64_Xword, 'p_filesz'),
        (Elf64_Xword, 'p_memsz'),
        (Elf64_Xword, 'p_align'),
        (__p_unknown, 'p_unknown'),
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
            (lambda s: dyn.array(Elf32_Word, s['descsz'].li.int() // 4), 'desc'),
            (dyn.align(4), 'desc_pad'),
        ]

@Type.define
class PT_SHLIB(ptype.block):
    type = 5
    # FIXME: this is platform-specific and not in the standard

@Type.define
class PT_PHDR(parray.block):
    type = 6
    def _object_(self):
        if not hasattr(self, '__boundary__'):
            res = self.getparent(ElfXX_File)
            setattr(self, '__boundary__', res)

        # figure out what elf class we're using
        p = self.__boundary__
        e_ident = p['e_ident']
        ei_class = e_ident['EI_CLASS']

        # so that we can determine which Phdr type to use
        if ei_class['ELFCLASS32']:
            return Elf32_Phdr
        elif ei_class['ELFCLASS64']:
            return Elf64_Phdr
        raise NotImplementedError(ei_class)

@Type.define
class PT_GNU_EH_FRAME(ptype.block):
    type = 0x6474e550
    # TODO: this structure is part of the dwarf standard

@Type.define
class PT_GNU_STACK(ptype.block):
    type = 0x6474e551

@Type.define
class PT_GNU_RELRO(ptype.block):
    type = 0x6474e552
