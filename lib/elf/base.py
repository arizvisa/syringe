import ptypes
from ptypes import ptype,parray,pstruct,pint,pstr,dyn,pbinary
ptypes.setbyteorder( ptypes.config.byteorder.littleendian )

### base
class uchar(pint.uint8_t): pass
class ElfXX_Off(ptype.rpointer_t):
    _object_ = ptype.undefined
    def _baseobject_(self):
        return self.getparent(ElfXX_File)
    @classmethod
    def typename(cls):
        return cls.__name__
    def classname(self):
        try: type = self.d.classname() if self.initializedQ() else self._object_().classname()
        except: pass
        else: return '%s<%s>'%(self.typename(), type)

        try: type = self._object_.typename() if ptype.istype(self._object_) else self._object_().classname()
        except: pass
        else: return '%s<%s>'%(self.typename(), type)

        type = self._object_.__name__
        return '%s<%s>'%(self.typename(), type)

class ElfXX_File(ptype.boundary): pass
class ElfXX_Header(ptype.boundary): pass
class ElfXX_Ehdr(ElfXX_Header): pass
class ElfXX_Phdr(ElfXX_Header): pass
class ElfXX_Shdr(ElfXX_Header): pass

### elf32
class Elf32_Addr(pint.uint32_t): pass
class Elf32_Half(pint.uint16_t): pass
class Elf32_Off(ElfXX_Off):
    _value_ = pint.uint32_t
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass

### elf64
class Elf64_Addr(pint.uint64_t): pass
class Elf64_Off(ElfXX_Off):
    _value_ = pint.uint64_t
class Elf64_Half(Elf32_Half): pass
class Elf64_Word(Elf32_Word): pass
class Elf64_Sword(Elf32_Sword): pass
class Elf64_Xword(pint.uint64_t): pass
class Elf64_Sxword(pint.int64_t): pass

### elf general
class e_ident(pstruct.type):
    EI_NIDENT=16
    class EI_CLASS(pint.enum, uchar):
        _values_ = [
            ('ELFCLASSNONE', 0),
            ('ELFCLASS32', 1),
            ('ELFCLASS64', 2),
        ]
    class EI_DATA(pint.enum, uchar):
        # FIXME: switch the byteorder of everything based on this value
        _values_ = [
            ('ELFDATANONE', 0),
            ('ELFDATA2LSB', 1),
            ('ELFDATA2MSB', 2),
        ]
    class EI_OSABI(pint.enum, uchar):
        _values_ = [
            ('ELFOSABI_SYSV', 0),
            ('ELFOSABI_HPUX', 1),
            ('ELFOSABI_ARM_EABI', 64),
            ('ELFOSABI_STANDALONE', 255),
        ]
    _fields_ = [
        (dyn.block(4), 'EI_MAG'),
        (EI_CLASS, 'EI_CLASS'),
        (EI_DATA, 'EI_DATA'),
        (uchar, 'EI_VERSION'),
        (EI_OSABI, 'EI_OSABI'),
        (uchar, 'EI_ABIVERSION'),
        (dyn.block(EI_NIDENT-9), 'EI_PAD'),
    ]
    def valid(self):
        return self.initialized and self['EI_MAG'].serialize() == '\x7fELF'

class e_type(pint.enum, Elf32_Half):
    ET_LOOS, ET_HIOS = 0xfe00, 0xfeff
    ET_LOPROC, ET_HIPROC = 0xff00, 0xffff
    _values_ = [
        ('ET_NONE', 0),
        ('ET_REL', 1),
        ('ET_EXEC', 2),
        ('ET_DYN', 3),
        ('ET_CORE', 4),
    ]

class e_machine(pint.enum, Elf32_Half):
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
        ('EM_SPARC32PLUS', 18),
        ('EM_ARM', 40),
        ('EM_SPARCV9', 43),
#       ('RESERVED', 11-16),
    ]

class e_version(pint.enum, Elf32_Word):
    _values_ = [
        ('EV_NONE',0),
        ('EV_CURRENT',1),
    ]

