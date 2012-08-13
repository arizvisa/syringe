import header,dynamic
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
            ('PT_GNU_EH_FRAME', 0x6474e550),
            ('PT_GNU_STACK', 0x6474e551),
            ('PT_LOPROC', 0x70000000),
            ('PT_HIPROC', 0x7fffffff),
        ]

    def __p_offset(self):
        t = int(self['p_type'].l)
        type = Type.get(t)
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

### segment type definitions
class Type(ptype.definition):
    cache = {}

@Type.define
class PT_LOAD(ptype.block):
    type=1

@Type.define
class PT_DYNAMIC(parray.block):
    type=2
    _object_=dynamic.Elf32_Dyn
    def isTerminator(self, value):
        return value['d_tag'].int() == 0

@Type.define
class PT_INTERP(pstr.szstring):
    type=3

@Type.define
class PT_NOTE(parray.block):
    type=4
    class __note(pstruct.type):
        def __name(self):
            padding = (4-(self.length%4))
            length = int(self['namesz'].l)
            class __name(pstr.szstring):
                def blocksize(self):
                    return padding + length
                pass
            __name.length = length
            return __name

        _fields_ = [
            (Elf32_Word, 'namesz'),
            (Elf32_Word, 'descsz'),
            (Elf32_Word, 'type'),
            (__name, 'name'),
            (lambda s: dyn.block(int(s['descsz'].l)), 'desc'),
        ]

    _object_ = __note
    
@Type.define
class PT_SHLIB(ptype.block):
    type=5
    # FIXME

@Type.define
class PT_PHDR(Elf32_Phdr):
    type=6

@Type.define
class PT_GNU_EH_FRAME(ptype.block):
    type = 0x6474e550
    # FIXME
