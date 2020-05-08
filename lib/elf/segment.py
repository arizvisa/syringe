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
        ('PT_TLS', 7),

        ('PT_GNU_EH_FRAME', 0x6474e550),
        ('PT_GNU_STACK', 0x6474e551),
        ('PT_GNU_RELRO', 0x6474e552),

        ('PT_SUNWBSS', 0x6ffffffa),     # Sun-specific segment
        ('PT_SUNWSTACK', 0x6ffffffb),   # Stack segment

        # PT_LOPROC(0x70000000) - PT_HIPROC(0x7fffffff)
        ('PT_ARM_ARCHEXT', 0x70000000), # Platform architecture compatibility information
        ('PT_ARM_UNWIND', 0x70000001),  # Exception unwind tables
    ]

class _p_flags(pbinary.flags):
    # Elf32_Word
    _fields_ = [
        (4, 'PF_MASKPROC'),
        (8, 'PF_MASKOS'),
        (1+16, 'SHF_RESERVED'),
        (1, 'PF_R'),
        (1, 'PF_W'),
        (1, 'PF_X'),
    ]

def _p_offset(ptr, CLASS):
    def p_size(self):
        p = self.getparent(ElfXX_Phdr)
        return p['p_filesz'].li.int()

    def p_offset(self):
        res = self['p_type'].li
        target = CLASS.PT_.get(res.int(), type=res.int(), blocksize=p_size)
        return dyn.clone(ptr, _object_=target)
    return p_offset

class ElfXX_Phdr(ElfXX_Header):
    def bounds(self):
        if isinstance(self.source, ptypes.provider.memorybase):
            fields = 'p_vaddr', 'p_memsz', 'p_align'
        else:
            fields = 'p_offset', 'p_filesz', 'p_align'
        iterable = (self[fld].li for fld in fields)
        return tuple(item.int() for item in iterable)

### Program Headers
class Elf32_Phdr(pstruct.type, ElfXX_Phdr):
    class p_type(_p_type, Elf32_Word): pass
    class p_flags(_p_flags): pass   # XXX

    def __p_unknown(self):
        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, self.blocksize() - res))

    _fields_ = [
        (p_type, 'p_type'),
        (lambda self: _p_offset(Elf32_Off, CLASS=ELFCLASS32), 'p_offset'),
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
        (lambda self: _p_offset(Elf64_Off, CLASS=ELFCLASS64), 'p_offset'),
        (Elf64_Addr, 'p_vaddr'),
        (Elf64_Addr, 'p_paddr'),
        (Elf64_Xword, 'p_filesz'),
        (Elf64_Xword, 'p_memsz'),
        (Elf64_Xword, 'p_align'),
        (__p_unknown, 'p_unknown'),
    ]

### generic segment type definitions
class ELFCLASSXX(object):
    class PT_LOAD(ptype.block):
        type = 1

    class PT_DYNAMIC(parray.block):
        type = 2
        _object_ = dynamic.ElfXX_Dyn

        def search(self, entry):
            if ptype.istype(entry):
                entry = entry.type
            return [x['d_val'] for x in self if x['d_tag'].int() == entry]

    class PT_INTERP(pstr.szstring):
        type = 3

    class PT_NOTE(parray.block):
        type = 4

        class _object_(pstruct.type):
            pass

    class PT_SHLIB(ptype.block):
        type = 5
        # FIXME: this is platform-specific and not in the standard

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

    class PT_GNU_EH_FRAME(ptype.block):
        type = 0x6474e550
        # TODO: this structure is part of the dwarf standard

    class PT_GNU_STACK(ptype.block):
        type = 0x6474e551

    class PT_GNU_RELRO(ptype.block):
        type = 0x6474e552

### 32-bit segment type definitions
class ELFCLASS32(object):
    class PT_(ptype.definition):
        cache = {}

    @PT_.define
    class PT_LOAD(ELFCLASSXX.PT_LOAD):
        pass

    @PT_.define
    class PT_DYNAMIC(ELFCLASSXX.PT_DYNAMIC):
        _object_ = dynamic.Elf32_Dyn

    @PT_.define
    class PT_INTERP(ELFCLASSXX.PT_INTERP):
        pass

    @PT_.define
    class PT_NOTE(ELFCLASSXX.PT_NOTE):
        class _object_(ELFCLASSXX.PT_NOTE._object_):
            _fields_ = [
                (Elf32_Word, 'namesz'),
                (Elf32_Word, 'descsz'),
                (Elf32_Word, 'type'),
                (lambda s: dyn.clone(pstr.string, length=s['namesz'].li.int()), 'name'),
                (dyn.align(4), 'name_pad'),
                (lambda s: dyn.array(Elf32_Word, s['descsz'].li.int() // 4), 'desc'),
                (dyn.align(4), 'desc_pad'),
            ]

    @PT_.define
    class PT_SHLIB(ELFCLASSXX.PT_SHLIB):
        pass

    @PT_.define
    class PT_PHDR(ELFCLASSXX.PT_PHDR):
        pass

    @PT_.define
    class PT_GNU_EH_FRAME(ELFCLASSXX.PT_GNU_EH_FRAME):
        pass

    @PT_.define
    class PT_GNU_STACK(ELFCLASSXX.PT_GNU_STACK):
        pass

    @PT_.define
    class PT_GNU_RELRO(ELFCLASSXX.PT_GNU_RELRO):
        pass

### 64-bit segment type definitions
class ELFCLASS64(object):
    class PT_(ptype.definition):
        cache = {}

    @PT_.define
    class PT_LOAD(ELFCLASSXX.PT_LOAD):
        pass

    @PT_.define
    class PT_DYNAMIC(ELFCLASSXX.PT_DYNAMIC):
        _object_ = dynamic.Elf64_Dyn

    @PT_.define
    class PT_INTERP(ELFCLASSXX.PT_INTERP):
        pass

    @PT_.define
    class PT_NOTE(ELFCLASSXX.PT_NOTE):
        class _object_(ELFCLASSXX.PT_NOTE._object_):
            _fields_ = [
                (Elf64_Word, 'namesz'),
                (Elf64_Word, 'descsz'),
                (Elf64_Word, 'type'),
                (lambda s: dyn.clone(pstr.string, length=s['namesz'].li.int()), 'name'),
                (dyn.align(4), 'name_pad'),
                (lambda s: dyn.array(Elf64_Word, s['descsz'].li.int() // 4), 'desc'),
                (dyn.align(4), 'desc_pad'),
            ]

    @PT_.define
    class PT_SHLIB(ELFCLASSXX.PT_SHLIB):
        pass

    @PT_.define
    class PT_PHDR(ELFCLASSXX.PT_PHDR):
        pass

    @PT_.define
    class PT_GNU_EH_FRAME(ELFCLASSXX.PT_GNU_EH_FRAME):
        pass

    @PT_.define
    class PT_GNU_STACK(ELFCLASSXX.PT_GNU_STACK):
        pass

    @PT_.define
    class PT_GNU_RELRO(ELFCLASSXX.PT_GNU_RELRO):
        pass
