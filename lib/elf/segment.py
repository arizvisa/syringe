from base import *
import header

### some misc types
class Elf32_Dyn(pstruct.type):
    class __d_un(dyn.union):
        _fields_ = [
            (Elf32_Word, 'd_val'),
            (Elf32_Addr, 'd_ptr'),
        ]

    _fields_ = [
        (Elf32_Sword, 'd_tag'),
#        (__d_un, 'd_un'),
        (Elf32_Word, 'd_val'),
    ]

    # FIXME: this union can be dynamic based on the d_tag field

### segment type definitions
class Type(Record):
    cache = {}

class PT_LOAD(object): type=1

@Type.Define
class PT_DYNAMIC(parray.block):
    type=2
    _object_=Elf32_Dyn
    def isTerminator(self, value):
        return int(value['d_tag']) == 0

@Type.Define
class PT_INTERP(pstr.szstring):
    type=3

@Type.Define
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
#            (lambda s: dyn.clone(tr.szstring, length=int(s['namesz'].l) - ), 'name'),
            (__name, 'name'),
            (lambda s: dyn.block(int(s['descsz'].l)), 'desc'),
        ]

    _object_ = __note
    
class PT_SHLIB(object): type=5

@Type.Define
class PT_PHDR(header.Elf32_Phdr):
    type=6

class PT_GNU_EH_FRAME(object):
    type = 0x6474e550
