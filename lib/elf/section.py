import sys, itertools
import ptypes
from .base import *

__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

### generic
class _sh_name(pint.type):
    def summary(self):
        try:
            res = self.str()
        except (ptypes.error.TypeError, ptypes.error.NotFoundError):
            return super(_sh_name, self).summary()
        return "{:s} : {!r}".format(super(_sh_name, self).summary(), res)

    def str(self):
        table = self.getparent(ElfXX_Ehdr).stringtable()
        if isinstance(table, ELFCLASSXX.SHT_STRTAB):
            return table.read(self.int()).str()
        raise ptypes.error.TypeError(self, 'str')

class SHT_(pint.enum):
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
        ('SHT_UNKNOWN12', 12),
        ('SHT_UNKNOWN13', 13),
        ('SHT_INIT_ARRAY', 14),
        ('SHT_FINI_ARRAY', 15),
        ('SHT_PREINIT_ARRAY', 16),
        ('SHT_GROUP', 17),
        ('SHT_SYMTAB_SHNDX', 18),

        # SHT_LOOS(0x60000000) - SHT_HIOS(0x6fffffff)
        ('SHT_GNU_ATTRIBUTES', 0x6ffffff5),
        ('SHT_GNU_HASH', 0x6ffffff6),
        ('SHT_GNU_LIBLIST', 0x6ffffff7),
        ('SHT_CHECKSUM', 0x6ffffff8),

        # SHT_LOSUNW(0x6ffffffa) - SHT_HISUNW(0x6fffffff)
        ('SHT_SUNW_move', 0x6ffffffa),
        ('SHT_SUNW_COMDAT', 0x6ffffffb),
        ('SHT_SUNW_syminfo', 0x6ffffffc),
        ('SHT_GNU_verdef', 0x6ffffffd),
        ('SHT_GNU_verneed', 0x6ffffffe),
        ('SHT_GNU_versym', 0x6fffffff),

        # SHT_LOPROC(0x70000000) - SHT_HIPROC(0x7fffffff)
        ('SHT_ARM_EXIDX', 0x70000001),
        ('SHT_ARM_PREEMPTMAP', 0x70000002),
        ('SHT_ARM_ATTRIBUTES', 0x70000003),
        ('SHT_ARM_DEBUGOVERLAY', 0x70000004),
        ('SHT_ARM_OVERLAYSECTION', 0x70000005),
        # SHT_LOUSER(0x80000000) - SHT_HIUSER(0xffffffff)
    ]

class SHF_(pbinary.flags):
    # Elf32_Word
    _fields_ = [
        (4, 'MASKPROC'),        # FIXME: lookup based on processor
        (8, 'MASKOS'),          # FIXME: lookup based on platform
        (8, 'UNKNOWN'),
        (1, 'COMPRESSED'),
        (1, 'TLS'),
        (1, 'GROUP'),
        (1, 'OS_NONCONFORMING'),
        (1, 'LINK_ORDER'),
        (1, 'INFO_LINK'),
        (1, 'STRINGS'),
        (1, 'MERGE'),
        (1, 'UNUSED'),
        (1, 'EXECINSTR'),
        (1, 'ALLOC'),
        (1, 'WRITE'),
    ]

def _sh_offset(ptr, CLASS):
    def sh_size(self):
        p = self.getparent(ElfXX_Shdr)
        return p['sh_size'].li.int()

    def sh_offset(self):
        res = self['sh_type'].li
        target = CLASS.SHT_.get(res.int(), type=res.int(), blocksize=sh_size)
        return dyn.clone(ptr, _object_=target)
    return sh_offset

def _sh_vaddress(ptr, CLASS):
    def sh_size(self):
        p = self.getparent(ElfXX_Shdr)
        size, alignment = (p[fld].li for fld in ['sh_size', 'sh_addralign'])
        count = (size.int() + alignment.int() - 1) // alignment.int()
        return count * alignment.int()

    def sh_vaddress(self):
        res = self['sh_type'].li
        target = CLASS.SHT_.get(res.int(), type=res.int(), blocksize=sh_size)
        return dyn.clone(ptr, _object_=target)
    return sh_vaddress

class _sh_index(pint.enum):
    _values_ = [
        ('SHN_UNDEF', 0),
        # SHN_LOPROC(0xff00) - SHN_HIPROC(0xff1f)
        ('SHN_BEFORE', 0xff00),
        ('SHN_AFTER', 0xff01),
        # SHN_LOOS(0xff20) - SHN_HIOS(0xff3f)
        # SHN_LORESERVE(0xff00) - SHN_HIRESERVE(0xffff)
        ('SHN_ABS', 0xfff1),
        ('SHN_COMMON', 0xfff2),
        ('SHN_XINDEX', 0xffff),
    ]

class _st_name(pint.type):
    def summary(self):
        try:
            res = self.str()
        except (ptypes.error.TypeError, ptypes.error.NotFoundError):
            return super(_st_name, self).summary()
        return "{:s} : {!r}".format(super(_st_name, self).summary(), res)

    def str(self):
        index = self.getparent(ElfXX_Shdr)['sh_link'].int()
        res = self.getparent(ElfXX_Ehdr)['e_shoff'].d.li
        if index >= len(res):
            raise ptypes.error.NotFoundError(self, 'str')
        table = res[index]['sh_offset'].d.li
        if isinstance(table, ELFCLASSXX.SHT_STRTAB):
            return table.read(self.int()).str()
        raise ptypes.error.TypeError(self, 'str')

class STT_(pbinary.enum):
    width = 4
    _values_ = [
        ('STT_NOTYPE', 0),
        ('STT_OBJECT', 1),
        ('STT_FUNC', 2),
        ('STT_SECTION', 3),
        ('STT_FILE', 4),
        ('STT_COMMON', 5),
        ('STT_TLS', 6),

        # STT_LOOS(10) - STT_HIOS(12)
        ('STT_GNU_IFUNC', 10),

        # STT_LOPROC(13) - STT_HIPROC(15)
    ]

class STB_(pbinary.enum):
    width = 4
    _values_ = [
        ('STB_LOCAL', 0),
        ('STB_GLOBAL', 1),
        ('STB_WEAK', 2),

        # STB_LOOS(10) - STB_HIOS(12)
        ('STB_GNU_UNIQUE', 10),
        # STB_LOPROC(13) - STB_HIPROC(15)
    ]

class st_info(pbinary.struct):
    _fields_ = [
        (STT_, 'ST_BIND'),
        (STB_, 'ST_TYPE'),
    ]

    def summary(self, **options):
        if self.value is None:
            return '???'
        res = self.bitmap()
        items = ["{:s}={:s}".format(field[1] + ('' if value is None else "[{:d}]".format(value.bits())), '???' if value is None else value.summary()) for field, value in __izip_longest__(self._fields_, self.value)]
        if items:
            return "({:s},{:d}) : {:s}".format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res), ' '.join(items))
        return "({:s},{:d})".format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res))

class STV_(pint.enum, uchar):
    _values_ = [
        ('STV_DEFAULT', 0),
        ('STV_INTERNAL', 1),
        ('STV_HIDDEN', 2),
        ('STV_PROTECTED', 3),
    ]

class ElfXX_Section(pint.enum):
    _values_ = [
        ('SHN_UNDEF', 0),
        # SHN_LORESERVE(0xff00) - SHN_HIRESERVE(0xffff)
        # SHN_LOPROC(0xff00) - SHN_HIPROC(0xff1f)
        ('SHN_ABS', 0xfff1),
        ('SHN_COMMON', 0xfff2),
    ]

class ElfXX_Shdr(ElfXX_Header):
    def getreadsize(self):
        res = self['sh_size'].li
        return res.int()

    def getloadedsize(self):
        res, alignment = (self[fld].li for fld in ['sh_size', 'sh_addralign'])
        count = (res.int() + alignment.int() - 1) // alignment.int()
        return count * alignment.int()

    def containsvirtualaddress(self, va):
        res = self['sh_addr']
        return res.int() <= va < res.int() + self.getloadedsize()

    def containsoffset(self, ofs):
        res = self['sh_offset']
        return res.int() <= ofs < res.int() + self.getreadsize()

class ELFCOMPRESS_(pint.enum):
    _values_ = [
        ('ELFCOMPRESS_ZLIB', 1),
    ]
class ElfXX_Chdr(ElfXX_Header):
    pass

### Section Headers
class Elf32_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf32_Word): pass
    class sh_type(SHT_, Elf32_Word): pass
    class sh_flags(SHF_): pass
    def __sh_unknown(self):
        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, self.blocksize() - res))
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (lambda self: _sh_vaddress(Elf32_VAddr, CLASS=ELFCLASS32), 'sh_addr'),
        (lambda self: _sh_offset(Elf32_Off, CLASS=ELFCLASS32), 'sh_offset'),
        (Elf32_Word, 'sh_size'),
        (Elf32_Word, 'sh_link'),
        (Elf32_Word, 'sh_info'),
        (Elf32_Word, 'sh_addralign'),
        (Elf32_Word, 'sh_entsize'),
        (__sh_unknown, 'sh_unknown'),
    ]

class Elf32_Chdr(pstruct.type, ElfXX_Chdr):
    class ch_type(ELFCOMPRESS_, Elf32_Word): pass
    _fields_ = [
        (ch_type, 'ch_type'),
        (Elf32_Word, 'ch_size'),
        (Elf32_Word, 'ch_addralign'),
    ]

    def getreadsize(self):
        res = self['ch_size'].li
        return res.int()

    def getloadedsize(self):
        res, alignment = (self[fld].li for fld in ['ch_size', 'ch_addralign'])
        count = (res.int() + alignment.int() - 1) // alignment.int()
        return count * alignment.int()

class Elf64_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf64_Word): pass
    class sh_type(SHT_, Elf64_Word): pass
    class sh_flags(SHF_):
        _fields_ = [(32, 'SHF_RESERVED2')] + SHF_._fields_
    def __sh_unknown(self):
        res = sum(self[fld].li.size() for _, fld in self._fields_[:-1])
        return dyn.block(max(0, self.blocksize() - res))
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (lambda self: _sh_vaddress(Elf64_VAddr, CLASS=ELFCLASS64), 'sh_addr'),
        (lambda self: _sh_offset(Elf64_Off, CLASS=ELFCLASS64), 'sh_offset'),
        (Elf64_Xword, 'sh_size'),
        (Elf64_Word, 'sh_link'),
        (Elf64_Word, 'sh_info'),
        (Elf64_Xword, 'sh_addralign'),
        (Elf64_Xword, 'sh_entsize'),
        (__sh_unknown, 'sh_unknown'),
    ]

class Elf64_Chdr(pstruct.type, ElfXX_Chdr):
    class ch_type(ELFCOMPRESS_, Elf64_Word): pass
    _fields_ = [
        (ch_type, 'ch_type'),
        (Elf64_Word, 'ch_size'),
        (Elf64_Word, 'ch_addralign'),
    ]

### section types
class Elf32_Section(ElfXX_Section, pint.uint16_t): pass
class Elf32_Sym(pstruct.type):
    class st_name(_st_name, Elf32_Word): pass
    _fields_ = [
        (st_name, 'st_name'),
        (Elf32_VAddr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (st_info, 'st_info'),
        (STV_, 'st_other'),
        (Elf32_Section, 'st_shndx'),
    ]
class Elf64_Section(ElfXX_Section, pint.uint16_t): pass
class Elf64_Sym(pstruct.type):
    class st_name(_st_name, Elf64_Word): pass
    _fields_ = [
        (st_name, 'st_name'),
        (st_info, 'st_info'),
        (STV_, 'st_other'),
        (Elf64_Section, 'st_shndx'),
        (Elf64_VAddr, 'st_value'),
        (Elf64_Xword, 'st_size'),
    ]

class ELF32_R_INFO(pbinary.struct):
    # Elf32_Word
    _fields_ = [
        (8, 'SYM'),
        (8, 'TYPE'),
    ]
class Elf32_Rel(pstruct.type):
    _fields_ = [
        (Elf32_VAddr, 'r_offset'),
        (ELF32_R_INFO , 'r_info'),
    ]
class Elf32_Rela(pstruct.type):
    _fields_ = [
        (Elf32_VAddr, 'r_offset'),
        (ELF32_R_INFO, 'r_info'),
        (Elf32_Sword, 'r_addend'),
    ]

class ELF64_R_INFO(pbinary.flags):
    # Elf64_Xword
    _fields_ = [
        (32, 'SYM'),
        (32, 'TYPE'),
    ]
class Elf64_Rel(pstruct.type):
    _fields_ = [
        (Elf64_VAddr, 'r_offset'),
        (ELF64_R_INFO, 'r_info'),
    ]
class Elf64_Rela(pstruct.type):
    _fields_ = [
        (Elf64_VAddr, 'r_offset'),
        (ELF64_R_INFO, 'r_info'),
        (Elf64_Sxword, 'r_addend'),
    ]

class SYMINFO_FLG_(pbinary.flags):
    # Elf32_Half/Elf64_Half
    _fields_ = [
        (10, 'UNUSED'),
        (1, 'NOEXTDIRECT'),
        (1, 'DIRECTBIND'),
        (1, 'LAZYLOAD'),
        (1, 'COPY'),
        (1, 'RESERVED'),
        (1, 'DIRECT'),
    ]

class Elf32_Syminfo(pstruct.type):
    class SYMINFO_BT_(pint.enum, Elf32_Half):
        _values_ = [
            ('SYMINFO_BT_SELF', 0xffff),
            ('SYMINFO_BT_PARENT', 0xfffe),
            ('SYMINFO_BT_NONE', 0xfffd),
        ]
    _fields_ = [
        (SYMINFO_BT_, 'si_boundto'),
        (SYMINFO_FLG_, 'si_flags'),
    ]

class Elf64_Syminfo(pstruct.type):
    class SYMINFO_BT_(pint.enum, Elf64_Half):
        _values_ = [
            ('SYMINFO_BT_SELF', 0xffff),
            ('SYMINFO_BT_PARENT', 0xfffe),
            ('SYMINFO_BT_NONE', 0xfffd),
        ]
    _fields_ = [
        (SYMINFO_BT_, 'si_boundto'),
        (SYMINFO_FLG_, 'si_flags'),
    ]

class VER_DEF_(pint.enum):
    _values_ = [
        ('VER_DEF_NON', 0),
        ('VER_DEF_CURRENT', 1),
        ('VER_DEF_NUM', 2),
    ]

class VER_FLG_(pbinary.flags):
    # Elf32_Half/Elf64_Half
    _fields_ = [
        (14, 'UNUSED'),
        (1, 'WEAK'),
        (1, 'BASE'),
    ]

class VER_NDX_(pint.enum):
    _values_ = [
        ('VER_NDX_LOCAL', 0),
        ('VER_NDX_GLOBAL', 1),
        ('VER_NDX_ELIMINATE', 0xff01),
    ]

class VER_NEED_(pint.enum):
    _values_ = [
        ('VER_NEED_NONE', 0),
        ('VER_NEED_CURRENT', 1),
        ('VER_NEED_NUM', 2),
    ]

class Elf32_Verdef(pstruct.type):
    class vd_version(VER_DEF_, Elf32_Half): pass
    class vd_ndx(VER_NDX_, Elf32_Half): pass
    _fields_ = [
        (vd_version, 'vd_version'),
        (VER_FLG_, 'vd_flags'),
        (vd_ndx, 'vd_ndx'),
        (Elf32_Half, 'vd_cnt'),     # Number of associated aux entries
        (Elf32_Word, 'vd_hash'),
        (Elf32_Word, 'vd_aux'),     # Offset in bytes to verdaux array
        (Elf32_Word, 'vd_next'),    # Offset in bytes to next verdef entry
    ]

class Elf32_Verdaux(pstruct.type):
    _fields_ = [
        (Elf32_Word, 'vda_name'),
        (Elf32_Word, 'vda_next'),   # Offset to an array
    ]

class Elf32_Verneed(pstruct.type):
    class vn_version(VER_NEED_, Elf32_Half): pass
    _fields_ = [
        (vn_version, 'vn_version'),
        (Elf32_Half, 'vn_cnt'),     # Number of elements in vernaux array
        (Elf32_Word, 'vn_file'),    # Offset to filename
        (Elf32_Word, 'vn_aux'),     # Offset in bytes to vernaux array
        (Elf32_Word, 'vn_next'),    # Offset in bytes to next verneed structure
    ]

class Elf32_Vernaux(pstruct.type):
    _fields_ = [
        (Elf32_Word, 'vna_hash'),
        (Elf32_Half, 'vna_flags'),
        (Elf32_Half, 'vna_other'),
        (Elf32_Word, 'vna_name'),   # Dependency name string offset
        (Elf32_Word, 'vna_next'),   # Offset in bytes to next vernaux
    ]

class Elf64_Verdef(pstruct.type):
    class vd_version(VER_DEF_, Elf64_Half): pass
    class vd_ndx(VER_NDX_, Elf64_Half): pass
    _fields_ = [
        (vd_version, 'vd_version'),
        (VER_FLG_, 'vd_flags'),
        (vd_ndx, 'vd_ndx'),
        (Elf64_Half, 'vd_cnt'),     # Number of associated aux entries
        (Elf64_Word, 'vd_hash'),
        (Elf64_Word, 'vd_aux'),     # Offset in bytes to verdaux array
        (Elf64_Word, 'vd_next'),    # Offset in bytes to next verdef entry
    ]

class Elf64_Verdaux(pstruct.type):
    _fields_ = [
        (Elf64_Word, 'vda_name'),
        (Elf64_Word, 'vda_next'),   # Offset to an array
    ]

class Elf64_Verneed(pstruct.type):
    class vn_version(VER_NEED_, Elf64_Half): pass
    _fields_ = [
        (vn_version, 'vn_version'),
        (Elf64_Half, 'vn_cnt'),     # Number of elements in vernaux array
        (Elf64_Word, 'vn_file'),    # Offset to filename
        (Elf64_Word, 'vn_aux'),     # Offset in bytes to vernaux array
        (Elf64_Word, 'vn_next'),    # Offset in bytes to next verneed structure
    ]

class Elf64_Vernaux(pstruct.type):
    _fields_ = [
        (Elf64_Word, 'vna_hash'),
        (Elf64_Half, 'vna_flags'),
        (Elf64_Half, 'vna_other'),
        (Elf64_Word, 'vna_name'),   # Dependency name string offset
        (Elf64_Word, 'vna_next'),   # Offset in bytes to next vernaux
    ]

### generic section type definitions
class ELFCLASSXX(object):
    class SHT_PROGBITS(ptype.block):
        type = 1

    class SHT_SYMTAB(parray.block):
        type = 2
        _object_ = None

    class SHT_STRTAB(parray.block):
        type = 3
        _object_ = pstr.szstring

        def read(self, offset):
            return self.field(offset)
        def summary(self):
            res = (res.str() for res in self)
            res = map("{!r}".format, res)
            return "{:s} : [ {:s} ]".format(self.__element__(), ', '.join(res))
        def details(self):
            return '\n'.join(map("{!r}".format, self))
        repr = details

    class SHT_RELA(parray.block):
        type = 4
        _object_ = None

    class SHT_HASH(pstruct.type):
        type = 5

        @classmethod
        def hash_of_bytes(cls, bytes):
            h = g = 0
            for item in bytearray(bytes):
                h = (h << 4) + item
                g = h & 0xf0000000
                if g:
                    h ^= g >> 24
                h &= 0xffffffff
            return h

    from .segment import ELFCLASSXX
    class SHT_DYNAMIC(ELFCLASSXX.PT_DYNAMIC):
        '''This is a placeholder and needs to be manually defined.'''
        type = 6

    class SHT_NOTE(ELFCLASSXX.PT_NOTE):
        '''This is a placeholder and needs to be manually defined.'''
        type = 7

    class SHT_NOBITS(ptype.block):
        type = 8

    class SHT_REL(parray.block):
        type = 9
        _object_ = None

    class SHT_SHLIB(ELFCLASSXX.PT_SHLIB):
        '''This is a placeholder and needs to be manually defined.'''
        type = 10

    class SHT_DYNSYM(parray.block):
        type = 11
        _object_ = Elf32_Sym

    class SHT_INIT_ARRAY(parray.block):
        type = 14
        _object_ = None

    class SHT_FINI_ARRAY(parray.block):
        type = 15
        _object_ = None

    class SHT_PREINIT_ARRAY(parray.block):
        type = 16
        _object_ = None

    # FIXME
    class SHT_GROUP(parray.block):
        type = 17
        class GRP_COMDAT(Elf32_Word): pass
        _object_ = None

    class SHT_SYMTAB_SHNDX(parray.block):
        type = 18
        _object_ = None

### 32-bit section type definitions
class ELFCLASS32(object):
    class SHT_(ptype.definition):
        cache = {}

    @SHT_.define
    class SHT_PROGBITS(ELFCLASSXX.SHT_PROGBITS):
        pass

    @SHT_.define
    class SHT_SYMTAB(ELFCLASSXX.SHT_SYMTAB):
        _object_ = Elf32_Sym

    @SHT_.define
    class SHT_STRTAB(ELFCLASSXX.SHT_STRTAB):
        pass

    @SHT_.define
    class SHT_RELA(ELFCLASSXX.SHT_RELA):
        _object_ = Elf32_Rela

    @SHT_.define
    class SHT_HASH(ELFCLASSXX.SHT_HASH):
        _fields_ = [
            (Elf32_Word, 'nbucket'),
            (Elf32_Word, 'nchain'),
            (lambda s: dyn.array(Elf32_Word, s['nbucket'].li.int()), 'bucket'),
            (lambda s: dyn.array(Elf32_Word, s['nchain'].li.int()), 'chain'),
        ]

    from .segment import ELFCLASS32
    @SHT_.define
    class SHT_DYNAMIC(ELFCLASS32.PT_DYNAMIC):
        type = ELFCLASSXX.SHT_DYNAMIC.type

    @SHT_.define
    class SHT_NOTE(ELFCLASS32.PT_NOTE):
        type = ELFCLASSXX.SHT_NOTE.type

    @SHT_.define
    class SHT_NOBITS(ELFCLASSXX.SHT_NOBITS):
        pass

    @SHT_.define
    class SHT_REL(ELFCLASSXX.SHT_REL):
        _object_ = Elf32_Rel

    @SHT_.define
    class SHT_SHLIB(ELFCLASS32.PT_SHLIB):
        type = ELFCLASSXX.SHT_SHLIB.type

    @SHT_.define
    class SHT_DYNSYM(ELFCLASSXX.SHT_DYNSYM):
        _object_ = Elf32_Sym

    @SHT_.define
    class SHT_INIT_ARRAY(ELFCLASSXX.SHT_INIT_ARRAY):
        _object_ = Elf32_VAddr

    @SHT_.define
    class SHT_FINI_ARRAY(ELFCLASSXX.SHT_FINI_ARRAY):
        _object_ = Elf32_VAddr

    @SHT_.define
    class SHT_PREINIT_ARRAY(ELFCLASSXX.SHT_PREINIT_ARRAY):
        _object_ = Elf32_VAddr

    @SHT_.define
    class SHT_GROUP(ELFCLASSXX.SHT_GROUP):
        _object_ = Elf32_Word

    @SHT_.define
    class SHT_SYMTAB_SHNDX(ELFCLASSXX.SHT_SYMTAB_SHNDX):
        _object_ = Elf32_Word

### 64-bit section type definitions
class ELFCLASS64(object):
    class SHT_(ptype.definition):
        cache = {}

    @SHT_.define
    class SHT_PROGBITS(ELFCLASSXX.SHT_PROGBITS):
        pass

    @SHT_.define
    class SHT_SYMTAB(ELFCLASSXX.SHT_SYMTAB):
        _object_ = Elf64_Sym

    @SHT_.define
    class SHT_STRTAB(ELFCLASSXX.SHT_STRTAB):
        pass

    @SHT_.define
    class SHT_RELA(ELFCLASSXX.SHT_RELA):
        _object_ = Elf64_Rela

    @SHT_.define
    class SHT_HASH(ELFCLASSXX.SHT_HASH):
        _fields_ = [
            (Elf64_Word, 'nbucket'),
            (Elf64_Word, 'nchain'),
            (lambda s: dyn.array(Elf64_Word, s['nbucket'].li.int()), 'bucket'),
            (lambda s: dyn.array(Elf64_Word, s['nchain'].li.int()), 'chain'),
        ]

    from .segment import ELFCLASS64
    @SHT_.define
    class SHT_DYNAMIC(ELFCLASS64.PT_DYNAMIC):
        type = ELFCLASSXX.SHT_DYNAMIC.type

    @SHT_.define
    class SHT_NOTE(ELFCLASS64.PT_NOTE):
        type = ELFCLASSXX.SHT_NOTE.type

    @SHT_.define
    class SHT_NOBITS(ELFCLASSXX.SHT_NOBITS):
        pass

    @SHT_.define
    class SHT_REL(ELFCLASSXX.SHT_REL):
        _object_ = Elf64_Rel

    @SHT_.define
    class SHT_SHLIB(ELFCLASS64.PT_SHLIB):
        type = ELFCLASSXX.SHT_SHLIB.type

    @SHT_.define
    class SHT_DYNSYM(ELFCLASSXX.SHT_DYNSYM):
        _object_ = Elf64_Sym

    @SHT_.define
    class SHT_INIT_ARRAY(ELFCLASSXX.SHT_INIT_ARRAY):
        _object_ = Elf64_VAddr

    @SHT_.define
    class SHT_FINI_ARRAY(ELFCLASSXX.SHT_FINI_ARRAY):
        _object_ = Elf64_VAddr

    @SHT_.define
    class SHT_PREINIT_ARRAY(ELFCLASSXX.SHT_PREINIT_ARRAY):
        _object_ = Elf64_VAddr

    @SHT_.define
    class SHT_GROUP(ELFCLASSXX.SHT_GROUP):
        _object_ = Elf64_Word

    @SHT_.define
    class SHT_SYMTAB_SHNDX(ELFCLASSXX.SHT_SYMTAB_SHNDX):
        _object_ = Elf64_Word

### ARM attributes (FIXME: integrate/assign this into the correct class type)
class SHT_ARM_ATTRIBUTES(pstruct.type):
    type = 0x70000003

    class vendortag(ptype.definition):
        cache, default = {}, ULEB128

    @vendortag.define
    class Tag_CPU_raw_name(pstr.szstring): type = 4
    @vendortag.define
    class Tag_CPU_name(pstr.szstring): type = 5
    @vendortag.define
    class Tag_CPU_arch(ULEB128): type = 6
    @vendortag.define
    class Tag_CPU_arch_profile(ULEB128): type = 7
    @vendortag.define
    class Tag_ARM_ISA_use(ULEB128): type = 8
    @vendortag.define
    class Tag_THUMB_ISA_use(ULEB128): type = 9
    @vendortag.define
    class Tag_FP_arch(ULEB128): type = 10
    @vendortag.define
    class Tag_WMMX_arch(ULEB128): type = 11
    @vendortag.define
    class Tag_Advanced_SIMD_arch(ULEB128): type = 12
    @vendortag.define
    class Tag_PCS_config(ULEB128): type = 13
    @vendortag.define
    class Tag_ABI_PCS_R9_use(ULEB128): type = 14
    @vendortag.define
    class Tag_ABI_PCS_RW_data(ULEB128): type = 15
    @vendortag.define
    class Tag_ABI_PCS_RO_data(ULEB128): type = 16
    @vendortag.define
    class Tag_ABI_PCS_GOT_use(ULEB128): type = 17
    @vendortag.define
    class Tag_ABI_PCS_wchar_t(ULEB128): type = 18
    @vendortag.define
    class Tag_ABI_FP_rounding(ULEB128): type = 19
    @vendortag.define
    class Tag_ABI_FP_denormal(ULEB128): type = 20
    @vendortag.define
    class Tag_ABI_FP_exceptions(ULEB128): type = 21
    @vendortag.define
    class Tag_ABI_FP_user_exceptions(ULEB128): type = 22
    @vendortag.define
    class Tag_ABI_FP_number_model(ULEB128): type = 23
    @vendortag.define
    class Tag_ABI_align_needed(ULEB128): type = 24
    @vendortag.define
    class Tag_ABI_align_preserved(ULEB128): type = 25
    @vendortag.define
    class Tag_ABI_enum_size(ULEB128): type = 26
    @vendortag.define
    class Tag_ABI_HardFP_use(ULEB128): type = 27
    @vendortag.define
    class Tag_ABI_VFP_args(ULEB128): type = 28
    @vendortag.define
    class Tag_ABI_WMMX_args(ULEB128): type = 29
    @vendortag.define
    class Tag_ABI_optimization_goals(ULEB128): type = 30
    @vendortag.define
    class Tag_ABI_FP_optimization_goals(ULEB128): type = 31
    @vendortag.define
    class Tag_compatibility(ULEB128): type = 32
    @vendortag.define
    class Tag_CPU_unaligned_access(ULEB128): type = 34
    @vendortag.define
    class Tag_FP_HP_extension(ULEB128): type = 36
    @vendortag.define
    class Tag_ABI_FP_16bit_format(ULEB128): type = 38
    @vendortag.define
    class Tag_MPextension_use(ULEB128): type = 42
    @vendortag.define
    class Tag_DIV_use(ULEB128): type = 44
    @vendortag.define
    class Tag_DSP_extension(ULEB128): type = 46
    @vendortag.define
    class Tag_also_compatible_with(ULEB128): type = 65
    @vendortag.define
    class Tag_conformance(ULEB128): type = 67
    @vendortag.define
    class Tag_Virtualization_use(ULEB128): type = 68

    class Tag(pint.enum, uchar): pass

    class Section(pstruct.type):
        def __value(self):
            tag = self['tag'].li.int()
            length = self['length'].li.int() - (self['tag'].li.size() + self['length'].li.size())
            return dyn.clone(SHT_ARM_ATTRIBUTES.Attributes, blocksize=lambda s,length=length:length)
        _fields_ = [
            (lambda s: SHT_ARM_ATTRIBUTES.Tag, 'tag'),
            (Elf32_Word, 'length'),
            (__value, 'attribute'),
        ]
        def summary(self):
            return "tag={:s} length={:d} attribute={:s}".format(self['tag'].summary(), self['length'].int(), self['attribute'].__element__())
    class Sections(parray.block):
        def summary(self):
            return "{:s} : [ {:s} ]".format(self.__element__(), ', '.join(res.summary() for res in self))
    Sections._object_ = Section
    class Attribute(pstruct.type):
        def __value(self):
            vendortag = SHT_ARM_ATTRIBUTES.vendortag
            res = self['tag'].li.int()
            return vendortag.withdefault(res, type=res)
        _fields_ = [
            (lambda s: SHT_ARM_ATTRIBUTES.Tag, 'tag'),
            (__value, 'value'),
        ]
        def summary(self):
            return "{:s}={:s}".format(self['tag'].summary(), str(self['value'].get()))
    class Attributes(parray.block):
        def details(self):
            res = []
            for i, n in enumerate(self):
                res.append("[{:x}] {:d} : {:s} = {:s}".format(n.getoffset(), i, n['tag'].summary(), str(n['value'].get())))
            return '\n'.join(res)
        def summary(self):
            return "{:s} : [ {:s} ]".format(self.__element__(), ', '.join(res['tag'].summary() for res in self))
        repr = details
    Attributes._object_ = Attribute

    @vendortag.define
    class Tag_File(Section): type = 1
    @vendortag.define
    class Tag_Section(Section): type = 2
    @vendortag.define
    class Tag_Symbol(Section): type = 3

    Tag._values_ = [(t.__name__, t.type) for t in vendortag.cache.values()]

    class Vendor(pstruct.type):
        def __section(self):
            bs = self['length'].li.int() - (self['length'].size() + self['name'].li.size())
            return dyn.clone(SHT_ARM_ATTRIBUTES.Sections, blocksize=lambda s,bs=bs: bs)

        _fields_ = [
            (Elf32_Word, 'length'),
            (pstr.szstring, 'name'),
            (__section, 'section'),
        ]
        def summary(self):
            return "length={:d} name={!r} section={:s}".format(self['length'].int(), self['name'].str(), self['section'].__element__())
    class Vendors(parray.block):
        def summary(self):
            return "{:s} : [ {:s} ]".format(self.__element__(), ', '.join(res.summary() for res in self))
    Vendors._object_ = Vendor

    def __vendor(self):
        bs = self.blocksize() - self['version'].li.size()
        return dyn.clone(SHT_ARM_ATTRIBUTES.Vendors, blocksize=lambda s,bs=bs: bs)

    _fields_ = [
        (pint.uint8_t, 'version'),
        (__vendor, 'vendor'),
    ]
