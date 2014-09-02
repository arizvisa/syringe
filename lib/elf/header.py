from . import section,segment
from .base import *

### 32-bit
class Elf32_Ehdr(pstruct.type, ElfXX_Header):
    def _ent_array(self, type, size, length):
        t = dyn.clone(type, blocksize=lambda s:self[size].number())
        return dyn.array(t, self[length].number())

    _fields_ = [
        (e_type, 'e_type'),
        (e_machine, 'e_machine'),
        (e_version, 'e_version'),
        (Elf32_Addr, 'e_entry'),
        (lambda self: dyn.clone(Elf32_Off, _object_=lambda s: self._ent_array(segment.Elf32_Phdr, 'e_phentsize', 'e_phnum')), 'e_phoff'),
        (lambda self: dyn.clone(Elf32_Off, _object_=lambda s: self._ent_array(section.Elf32_Shdr, 'e_shentsize', 'e_shnum')), 'e_shoff'),
        (Elf32_Word, 'e_flags'),
        (Elf32_Half, 'e_ehsize'),
        (Elf32_Half, 'e_phentsize'),
        (Elf32_Half, 'e_phnum'),
        (Elf32_Half, 'e_shentsize'),
        (Elf32_Half, 'e_shnum'),
        (Elf32_Half, 'e_shstrndx'),
    ]

    def blocksize(self):
        return self['e_ehsize'].l.number()-e_ident().a.blocksize()

    def stringtable(self):
        index = self['e_shstrndx'].number()
        return self['e_shoff'].d.l[index]['sh_offset'].d.l

### 64-bit
class Elf64_Ehdr(pstruct.type, ElfXX_Header):
    def _ent_array(self, type, size, length):
        t = dyn.clone(type, blocksize=lambda s:self[size].number())
        return dyn.array(t, self[length].number())
    _fields_ = [
        (e_type, 'e_type'),
        (e_machine, 'e_machine'),
        (e_version, 'e_version'),
        (Elf64_Addr, 'e_entry'),
        (lambda self: dyn.clone(Elf64_Off, _object_=lambda s: self._ent_array(segment.Elf64_Phdr, 'e_phentsize', 'e_phnum')), 'e_phoff'),
        (lambda self: dyn.clone(Elf64_Off, _object_=lambda s: self._ent_array(section.Elf64_Shdr, 'e_shentsize', 'e_shnum')), 'e_shoff'),
        (Elf64_Word, 'e_flags'),
        (Elf64_Half, 'e_ehsize'),
        (Elf64_Half, 'e_phentsize'),
        (Elf64_Half, 'e_phnum'),
        (Elf64_Half, 'e_shentsize'),
        (Elf64_Half, 'e_shnum'),
        (Elf64_Half, 'e_shstrndx'),
    ]
    def blocksize(self):
        return self['e_ehsize'].l.number() - e_ident().a.blocksize()
    def stringtable(self):
        index = self['e_shstrndx'].number()
        return self['e_shoff'].d.l[index]['sh_offset'].d.l
