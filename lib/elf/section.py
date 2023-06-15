import sys, itertools
import ptypes
from .base import *

izip_longest = ptypes.utils.izip_longest

### generic
class _sh_name(pint.type):
    def summary(self):
        try:
            res = self.str()
        except (ptypes.error.TypeError, ptypes.error.ItemNotFoundError):
            return super(_sh_name, self).summary()
        return "{:s} : {!r}".format(super(_sh_name, self).summary(), res)

    def str(self):
        try:
            header = self.getparent(ElfXX_Ehdr)

        except ptypes.error.ItemNotFoundError:
            base = self.getparent(ElfXX_File)
            header = base['e_data']

        table = header.stringtable()
        if isinstance(table, ELFCLASSXX.SHT_STRTAB):
            return table.read(self.int()).str()
        raise ptypes.error.TypeError(self, 'str')

class SHT_(pint.enum):
    _values_ = [
        ('NULL', 0),
        ('PROGBITS', 1),
        ('SYMTAB', 2),
        ('STRTAB', 3),
        ('RELA', 4),
        ('HASH', 5),
        ('DYNAMIC', 6),
        ('NOTE', 7),
        ('NOBITS', 8),
        ('REL', 9),
        ('SHLIB', 10),
        ('DYNSYM', 11),
        ('UNKNOWN12', 12),
        ('UNKNOWN13', 13),
        ('INIT_ARRAY', 14),
        ('FINI_ARRAY', 15),
        ('PREINIT_ARRAY', 16),
        ('GROUP', 17),
        ('SYMTAB_SHNDX', 18),

        # SHT_LOOS(0x60000000) - SHT_HIOS(0x6fffffff)
        ('GNU_INCREMENTAL_INPUTS', 0x6fff4700),
        ('GNU_ATTRIBUTES', 0x6ffffff5),
        ('GNU_HASH', 0x6ffffff6),
        ('GNU_LIBLIST', 0x6ffffff7),
        ('CHECKSUM', 0x6ffffff8),

        # SHT_LOSUNW(0x6ffffffa) - SHT_HISUNW(0x6fffffff)
        ('SUNW_move', 0x6ffffffa),
        ('SUNW_COMDAT', 0x6ffffffb),
        ('SUNW_syminfo', 0x6ffffffc),
        ('GNU_verdef', 0x6ffffffd),
        ('GNU_verneed', 0x6ffffffe),
        ('GNU_versym', 0x6fffffff),

        # SHT_LOPROC(0x70000000) - SHT_HIPROC(0x7fffffff)
        ('ARM_EXIDX', 0x70000001),
        ('ARM_PREEMPTMAP', 0x70000002),
        ('ARM_ATTRIBUTES', 0x70000003),
        ('ARM_DEBUGOVERLAY', 0x70000004),
        ('ARM_OVERLAYSECTION', 0x70000005),
        # SHT_LOUSER(0x80000000) - SHT_HIUSER(0xffffffff)
    ]

class SHF_(pbinary.flags):
    # Elf32_Word
    class SHF_MASKPROC(pbinary.flags):
        _fields_ = [
            (1, 'EXCLUDE'),
            (3, 'RESERVED'),
        ]
    class SHF_MASKOS(pbinary.flags):
        _fields_ = [
            (3, 'RESERVED2'),
            (1, 'GNU_MBIND'),
            (3, 'RESERVED1'),
            (1, 'GNU_BUILD_NOTE'),
        ]
    _fields_ = [
        (SHF_MASKPROC, 'MASKPROC'), # FIXME: lookup based on processor
        (SHF_MASKOS, 'MASKOS'),     # FIXME: lookup based on platform
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
        if alignment.int() > 0:
            count = (size.int() + alignment.int() - 1) // alignment.int()
            return count * alignment.int()
        return size.int()

    def sh_vaddress(self):
        res = self['sh_type'].li
        target = CLASS.SHT_.get(res.int(), type=res.int(), blocksize=sh_size)
        return dyn.clone(ptr, _object_=target)
    return sh_vaddress

class _st_name(pint.type):
    def summary(self):
        try:
            res = self.str()
        except (ptypes.error.TypeError, ptypes.error.ItemNotFoundError):
            return super(_st_name, self).summary()
        return "{:s} : {!r}".format(super(_st_name, self).summary(), res)

    def __section_index__(self, section):
        index = section['sh_link'].int()

        # Backtrack to the header, to grab the list of sections.
        header = section.getparent(ElfXX_Ehdr)
        sections = header['e_shoff'].d.li

        # If the section index fits within our list, then we can
        # snag the string table right out of it.
        if index >= len(sections):
            raise ptypes.error.ItemNotFoundError(self, 'str')
        return sections[index]

    def __symbol_index__(self):
        symbol = self.getparent(ElfXX_Sym)
        if not isinstance(symbol.parent, (ELFCLASSXX.SHT_DYNSYM, ELFCLASSXX.SHT_SYMTAB)):
            raise ptypes.error.ItemNotFoundError(self, '__dynamic_index___')

        # Backtrack to the pointer for our symbol so that we can
        # get to its array. The parent of that is likely a section.
        pointer = symbol.getparent(parray.type).parent
        if isinstance(pointer.parent, ElfXX_Shdr):
            section = self.__section_index__(pointer.parent)
            return section['sh_offset']

        # Otherwise, it's a dynamic segment and we need to query
        # the DT_STRTAB straight out of it.
        from . import segment
        dynamic = pointer.getparent(segment.ELFCLASSXX.PT_DYNAMIC)
        return dynamic.by_tag('DT_STRTAB')

    def __header_index__(self):
        header = self.getparent(ElfXX_Ehdr)
        segments = header['e_phoff'].d.li
        dynamic = segments.by_type('DYNAMIC')
        return dynamic.by_tag('DT_STRTAB')

    def str(self):
        if isinstance(self.parent, ElfXX_Shdr):
            section = self.__section_index__(self.parent)
            table = section['sh_offset'].d.li

        # If our parent wasn't a section, then we need to get
        # the name out of a symbol table of some sort.
        else:
            ptr = self.__symbol_index__()
            table = ptr.d.li

        # Verify the type of table we got is a string table.
        if isinstance(table, ELFCLASSXX.SHT_STRTAB):
            return table.read(self.int()).str()

        # Anything else is an unresolveable error.
        raise ptypes.error.TypeError(self, 'str')

class STT_(pbinary.enum):
    length, _values_ = 4, [
        ('NOTYPE', 0),
        ('OBJECT', 1),
        ('FUNC', 2),
        ('SECTION', 3),
        ('FILE', 4),
        ('COMMON', 5),
        ('TLS', 6),

        # STT_LOOS(10) - STT_HIOS(12)
        ('GNU_IFUNC', 10),

        # STT_LOPROC(13) - STT_HIPROC(15)
    ]

class STB_(pbinary.enum):
    length, _values_ = 4, [
        ('LOCAL', 0),
        ('GLOBAL', 1),
        ('WEAK', 2),

        # STB_LOOS(10) - STB_HIOS(12)
        ('GNU_UNIQUE', 10),
        # STB_LOPROC(13) - STB_HIPROC(15)
    ]

class st_info(pbinary.struct):
    _fields_ = [
        (STB_, 'ST_BIND'),
        (STT_, 'ST_TYPE'),
    ]

    def summary(self, **options):
        if self.value is None:
            return '???'
        res = self.bitmap()
        items = ["{:s}={:s}".format(field[1] + ('' if value is None else "[{:d}]".format(value.bits())), '???' if value is None else value.summary()) for field, value in izip_longest(self._fields_, self.value)]
        if items:
            return "({:s},{:d}) : {:s}".format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res), ' '.join(items))
        return "({:s},{:d})".format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res))

class STV_(pint.enum, uchar):
    _values_ = [
        ('DEFAULT', 0),
        ('INTERNAL', 1),
        ('HIDDEN', 2),
        ('PROTECTED', 3),
    ]

class SHN_(pint.enum):
    _values_ = [
        ('UNDEF', 0),
        # SHN_LORESERVE(0xff00) - SHN_HIRESERVE(0xffff)
        ('BEFORE', 0xff00),
        ('AFTER', 0xff01),
        # SHN_LOPROC(0xff00) - SHN_HIPROC(0xff1f)
        ('ABS', 0xfff1),
        ('COMMON', 0xfff2),
        ('XINDEX', 0xffff),
    ]

class ElfXX_Shdr(ElfXX_Header):
    def getreadsize(self):

        # If our type is SHT_NOBITS, then there's actually no read size so we return 0.
        type = self['sh_type']
        if type['NOBITS']:
            return 0

        # Otherwise we can just return the size from the section header.
        res = self['sh_size'].li
        return res.int()

    def getloadsize(self):
        size, alignment = (self[fld].li for fld in ['sh_size', 'sh_addralign'])
        if alignment.int() > 0:
            count = (size.int() + alignment.int() - 1) // alignment.int()
            return count * alignment.int()
        return size.int()

    def containsaddress(self, va):
        res = self['sh_addr']
        return res.int() <= va < res.int() + self.getloadsize()

    def containsoffset(self, ofs):
        res = self['sh_offset']
        return res.int() <= ofs < res.int() + self.getreadsize()

    def summary(self):
        name, type, flags = (self[fld] for fld in ['sh_name', 'sh_type', 'sh_flags'])
        addr, offset, size, addralign = (self[fld].int() for fld in ['sh_addr', 'sh_offset', 'sh_size', 'sh_addralign'])

        # Organize the flags so they're more descriptive.
        items = ["{:s}={:d}".format(name, flags[name]) if flags[name] > 1 else name for name in flags if not isinstance(flags[name], pbinary.struct) and flags[name]]
        items+= ["{:s}={:s}".format(name, flags[name].summary()) for name in flags if isinstance(flags[name], pbinary.struct) and flags[name].int()]
        flags_summary = ','.join(items)

        # Build the string components for each set of fields.
        description = "{:>13s} {:<20s}".format("({:s})".format(type.str()), name.str())
        location = "offset:{:#0{:d}x}<>{:#0{:d}x} ({:+#0{:d}x})".format(offset, 2+6, offset + size, 2+6, size, 1+2+4)
        address_location = "addr:{:#0{:d}x}({:d})".format(addr, 2+4, addralign)
        extra = ["{:s}={:#x}".format(field, self[field].int()) for field in ['sh_link', 'sh_info'] if self[field].int()]

        # Render them while including the unknown header if it has a size.
        if self['sh_unknown'].size():
            return ' '.join([description, location, address_location] + extra + [flags_summary, "unknown:{:s}".format(self['sh_unknown'].summary())])
        return ' '.join([description, location, address_location] + extra + [flags_summary])

class ELFCOMPRESS_(pint.enum):
    _values_ = [
        ('ZLIB', 1),
    ]

class ElfXX_Chdr(ElfXX_Header):
    def getreadsize(self):
        res = self['ch_size'].li
        return res.int()

    def getloadsize(self):
        size, alignment = (self[fld].li for fld in ['ch_size', 'ch_addralign'])
        if alignment.int() > 0:
            count = (size.int() + alignment.int() - 1) // alignment.int()
            return count * alignment.int()
        return size.int()

class ElfXX_Sym(pstruct.type):
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

class Elf64_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf64_Word): pass
    class sh_type(SHT_, Elf64_Word): pass
    class sh_flags(SHF_):
        _fields_ = [(32, 'RESERVED')] + SHF_._fields_
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
class Elf32_Section(SHN_, pint.uint16_t): pass
class Elf32_Sym(ElfXX_Sym):
    class st_name(_st_name, Elf32_Word): pass
    _fields_ = [
        (st_name, 'st_name'),
        (Elf32_VAddr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (st_info, 'st_info'),
        (STV_, 'st_other'),
        (Elf32_Section, 'st_shndx'),
    ]
class Elf64_Section(SHN_, pint.uint16_t): pass
class Elf64_Sym(ElfXX_Sym):
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
        (Elf32_Off, 'r_offset'),
        (ELF32_R_INFO , 'r_info'),
    ]
class Elf32_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Off, 'r_offset'),
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
        (Elf64_Off, 'r_offset'),
        (ELF64_R_INFO, 'r_info'),
    ]
class Elf64_Rela(pstruct.type):
    _fields_ = [
        (Elf64_Off, 'r_offset'),
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

class SYMINFO_BT_(pint.enum):
    _values_ = [
        ('SELF', 0xffff),
        ('PARENT', 0xfffe),
        ('NONE', 0xfffd),
    ]

class Elf32_Syminfo(pstruct.type):
    class si_boundto(SYMINFO_BT_, Elf32_Half): pass
    _fields_ = [
        (si_boundto, 'si_boundto'),
        (SYMINFO_FLG_, 'si_flags'),
    ]

class Elf64_Syminfo(pstruct.type):
    class si_boundto(SYMINFO_BT_, Elf64_Half): pass
    _fields_ = [
        (si_boundto, 'si_boundto'),
        (SYMINFO_FLG_, 'si_flags'),
    ]

### version definitions
class VER_DEF_(pint.enum):
    _values_ = [
        ('NON', 0),
        ('CURRENT', 1),
        ('NUM', 2),
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
        ('LOCAL', 0),
        ('GLOBAL', 1),
        ('ELIMINATE', 0xff01),
    ]

class VER_NEED_(pint.enum):
    _values_ = [
        ('NONE', 0),
        ('CURRENT', 1),
        ('NUM', 2),
    ]

class ElfXX_VerXauxName(ptype.opointer_t):
    _object_ = pstr.szstring
    def _calculate_(self, offset):
        from .segment import ELFCLASSXX
        p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

        dt_strtab = p.by_tag('DT_STRTAB')
        return dt_strtab.int() + offset

    def str(self):
        return self.d.li.str()

    def summary(self):
        res = super(ElfXX_VerXauxName, self).summary()
        return "{:s} {!r}".format(res, self.str())

class Elf32_Verdef(pstruct.type):
    class vd_version(VER_DEF_, Elf32_Half): pass
    class vd_ndx(VER_NDX_, Elf32_Half): pass
    def __padding_vd_aux(self):
        res, fields = self['vd_aux'].li, ['vd_version', 'vd_flags', 'vd_ndx', 'vd_cnt', 'vd_hash', 'vd_aux', 'vd_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    def __vd_verdaux(self):
        res = self['vd_cnt'].li
        return dyn.array(Elf32_Verdaux, res.int())
    def __padding_vd_next(self):
        res, fields = self['vd_next'].li, ['vd_version', 'vd_flags', 'vd_ndx', 'vd_cnt', 'vd_hash', 'vd_aux', 'vd_next', 'padding(vd_aux)', 'vd_verdaux']
        if res.int() > 0:
            return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)
    _fields_ = [
        (vd_version, 'vd_version'),
        (VER_FLG_, 'vd_flags'),
        (vd_ndx, 'vd_ndx'),
        (Elf32_Half, 'vd_cnt'),     # Number of associated aux entries
        (Elf32_Word, 'vd_hash'),
        (Elf32_Word, 'vd_aux'),     # Offset in bytes to verdaux array
        (Elf32_Word, 'vd_next'),    # Offset in bytes to next verdef entry
        (__padding_vd_aux, 'padding(vd_aux)'),
        (__vd_verdaux, 'vd_verdaux'),
        (__padding_vd_next, 'padding(vd_next)'),
    ]

class Elf32_Verdaux(pstruct.type):
    def __padding_vda_next(self):
        res, fields = self['vda_next'].li, ['vda_name', 'vda_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (dyn.clone(ElfXX_VerXauxName, _value_=Elf32_Word), 'vda_name'),
        (Elf32_Word, 'vda_next'),   # Offset to an array
        (__padding_vda_next, 'padding(vda_next)'),
    ]

class Elf32_Verneed(pstruct.type):
    class vn_version(VER_NEED_, Elf32_Half): pass
    def __padding_vn_aux(self):
        res, fields = self['vn_aux'].li, ['vn_version', 'vn_cnt', 'vn_file', 'vn_aux', 'vn_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    def __vn_vernaux(self):
        res = self['vn_cnt'].li
        return dyn.array(Elf32_Vernaux, res.int())
    def __padding_vn_next(self):
        res, fields = self['vn_next'].li, ['vn_version', 'vn_cnt', 'vn_file', 'vn_aux', 'vn_next', 'padding(vn_aux)', 'vn_vernaux']
        if res.int() > 0:
            return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)
    _fields_ = [
        (vn_version, 'vn_version'),
        (Elf32_Half, 'vn_cnt'),     # Number of elements in vernaux array
        (Elf32_Word, 'vn_file'),    # Offset to filename
        (Elf32_Word, 'vn_aux'),     # Offset in bytes to vernaux array
        (Elf32_Word, 'vn_next'),    # Offset in bytes to next verneed structure
        (__padding_vn_aux, 'padding(vn_aux)'),
        (__vn_vernaux, 'vn_vernaux'),
        (__padding_vn_next, 'padding(vn_next)'),
    ]

class Elf32_Vernaux(pstruct.type):
    def __padding_vna_next(self):
        res, fields = self['vna_next'].li, ['vna_hash', 'vna_flags', 'vna_other', 'vna_name', 'vna_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (Elf32_Word, 'vna_hash'),
        (Elf32_Half, 'vna_flags'),
        (Elf32_Half, 'vna_other'),
        (dyn.clone(ElfXX_VerXauxName, _value_=Elf32_Word), 'vna_name'),
        (Elf32_Word, 'vna_next'),   # Offset in bytes to next vernaux
        (__padding_vna_next, 'padding(vna_next)'),
    ]

class Elf64_Verdef(pstruct.type):
    class vd_version(VER_DEF_, Elf64_Half): pass
    class vd_ndx(VER_NDX_, Elf64_Half): pass
    def __padding_vd_aux(self):
        res, fields = self['vd_aux'].li, ['vd_version', 'vd_flags', 'vd_ndx', 'vd_cnt', 'vd_hash', 'vd_aux', 'vd_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    def __vd_verdaux(self):
        res = self['vd_cnt'].li
        return dyn.array(Elf64_Verdaux, res.int())
    def __padding_vd_next(self):
        res, fields = self['vd_next'].li, ['vd_version', 'vd_flags', 'vd_ndx', 'vd_cnt', 'vd_hash', 'vd_aux', 'vd_next', 'padding(vd_aux)', 'vd_verdaux']
        if res.int() > 0:
            return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)
    _fields_ = [
        (vd_version, 'vd_version'),
        (VER_FLG_, 'vd_flags'),
        (vd_ndx, 'vd_ndx'),
        (Elf64_Half, 'vd_cnt'),     # Number of associated aux entries
        (Elf64_Word, 'vd_hash'),
        (Elf64_Word, 'vd_aux'),     # Offset in bytes to verdaux array
        (Elf64_Word, 'vd_next'),    # Offset in bytes to next verdef entry
        (__padding_vd_aux, 'padding(vd_aux)'),
        (__vd_verdaux, 'vd_verdaux'),
        (__padding_vd_next, 'padding(vd_next)'),
    ]

class Elf64_Verdaux(pstruct.type):
    def __padding_vda_next(self):
        res, fields = self['vda_next'].li, ['vda_name', 'vda_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (dyn.clone(ElfXX_VerXauxName, _value_=Elf64_Word), 'vda_name'),
        (Elf64_Word, 'vda_next'),   # Offset to an array
        (__padding_vda_next, 'padding(vda_next)'),
    ]

class Elf64_Verneed(pstruct.type):
    class vn_version(VER_NEED_, Elf64_Half): pass
    def __padding_vn_aux(self):
        res, fields = self['vn_aux'].li, ['vn_version', 'vn_cnt', 'vn_file', 'vn_aux', 'vn_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    def __vn_vernaux(self):
        res = self['vn_cnt'].li
        return dyn.array(Elf64_Vernaux, res.int())
    def __padding_vn_next(self):
        res, fields = self['vn_next'].li, ['vn_version', 'vn_cnt', 'vn_file', 'vn_aux', 'vn_next', 'padding(vn_aux)', 'vn_vernaux']
        if res.int() > 0:
            return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)
    _fields_ = [
        (vn_version, 'vn_version'),
        (Elf64_Half, 'vn_cnt'),     # Number of elements in vernaux array
        (Elf64_Word, 'vn_file'),    # Offset to filename
        (Elf64_Word, 'vn_aux'),     # Offset in bytes to vernaux array
        (Elf64_Word, 'vn_next'),    # Offset in bytes to next verneed structure
        (__padding_vn_aux, 'padding(vn_aux)'),
        (__vn_vernaux, 'vn_vernaux'),
        (__padding_vn_next, 'padding(vn_next)'),
    ]

class Elf64_Vernaux(pstruct.type):
    def __padding_vna_next(self):
        res, fields = self['vna_next'].li, ['vna_hash', 'vna_flags', 'vna_other', 'vna_name', 'vna_next']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (Elf64_Word, 'vna_hash'),
        (Elf64_Half, 'vna_flags'),
        (Elf64_Half, 'vna_other'),
        (dyn.clone(ElfXX_VerXauxName, _value_=Elf64_Word), 'vna_name'),
        (Elf64_Word, 'vna_next'),   # Offset in bytes to next vernaux
        (__padding_vna_next, 'padding(vna_next)'),
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
            source = ptypes.provider.proxy(self)
            return self.new(self._object_, source=source, offset=offset).l
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
        def hash_of_bytes(cls, name):
            '''unsigned long elf_hash(const unsigned char* name)'''
            nameu = bytearray(name)
            h = 0
            for c in nameu:
                h = (h << 4) + c
                g = h & 0xf0000000
                if g != 0:
                    h ^= g >> 24
                    h ^= g
                continue
            return h & 0xffffffff

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

    class SHT_GNU_HASH(pstruct.type):
        type = 0x6ffffff6
        class _gnuBucketChain(parray.terminated):
            _object_ = None
            def isTerminator(self, item):
                return item.int() & 1

            def iterate(self):
                for item in self:
                    yield item.int() & ~1
                return

        class _gnuHashBuckets(parray.type):
            def getBucket(self, index):
                p = self.getparent(ELFCLASSXX.SHT_GNU_HASH)
                symindx = p['symindx'].int()

                for chain in self:
                    if symindx <= index < symindx + len(chain):
                        return chain
                    symindx += len(chain)
                raise ptypes.error.ItemNotFoundError(self, 'getBucket', "Unable to get bucket for symbol index {:#x} ({:d}).".format(index, index))

            def iterate(self):
                for chain in self:
                    for h in chain:
                        yield h
                    continue
                return

        @classmethod
        def hash_of_bytes(cls, name):
            '''uint32_t Dynobj::gnu_hash(const char* name)'''
            nameu = bytearray(name)
            h = 5381
            for c in nameu:
                h = (h << 5) + h + c
            return h & 0xffffffff

    class SHT_GNU_verdef(parray.block):
        type = 0x6ffffffd
        _object_ = None

    class SHT_GNU_verneed(parray.block):
        type = 0x6ffffffe
        _object_ = None

    class SHT_GNU_versym(parray.block):
        type = 0x6fffffff
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

    @SHT_.define
    class SHT_GNU_HASH(ELFCLASSXX.SHT_GNU_HASH):
        class _gnuBucketChain(ELFCLASSXX.SHT_GNU_HASH._gnuBucketChain):
            _object_ = Elf32_Word

        def __hashbuckets(self):
            chain_t, buckets = self._gnuBucketChain, self['buckets'].li
            def _object_(self, chain_t=chain_t, buckets=buckets):
                index = len(self.value)
                if buckets[index].int():
                    return chain_t
                return dyn.clone(chain_t, length=0)
            return dyn.clone(self._gnuHashBuckets, _object_=_object_, length=self['bucketcount'].li.int())

        _fields_ = [
            (Elf32_Word, 'bucketcount'),
            (Elf32_Word, 'symindx'),
            (Elf32_Word, 'maskwords'),
            (Elf32_Word, 'shift2'),
            (lambda self: dyn.array(Elf32_Word, self['maskwords'].li.int()), 'mask'),
            (lambda self: dyn.array(Elf32_Word, self['bucketcount'].li.int()), 'buckets'),
            (__hashbuckets, 'hashbuckets'),
        ]

    @SHT_.define
    class SHT_GNU_verdef(ELFCLASSXX.SHT_GNU_verdef):
        _object_ = Elf32_Verdef

    @SHT_.define
    class SHT_GNU_verneed(ELFCLASSXX.SHT_GNU_verneed):
        _object_ = Elf32_Verneed

    @SHT_.define
    class SHT_GNU_versym(ELFCLASSXX.SHT_GNU_versym):
        _object_ = Elf32_Half

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

    @SHT_.define
    class SHT_GNU_HASH(ELFCLASSXX.SHT_GNU_HASH):
        class _gnuBucketChain(ELFCLASSXX.SHT_GNU_HASH._gnuBucketChain):
            _object_ = Elf64_Word

        def __hashbuckets(self):
            chain_t, buckets = self._gnuBucketChain, self['buckets'].li
            def _object_(self, chain_t=chain_t, buckets=buckets):
                index = len(self.value)
                if buckets[index].int():
                    return chain_t
                return dyn.clone(chain_t, length=0)
            return dyn.clone(self._gnuHashBuckets, _object_=_object_, length=self['bucketcount'].li.int())

        _fields_ = [
            (Elf64_Word, 'bucketcount'),
            (Elf64_Word, 'symindx'),
            (Elf64_Word, 'maskwords'),
            (Elf64_Word, 'shift2'),
            (lambda self: dyn.array(Elf64_Xword, self['maskwords'].li.int()), 'mask'),
            (lambda self: dyn.array(Elf64_Word, self['bucketcount'].li.int()), 'buckets'),
            (__hashbuckets, 'hashbuckets'),
        ]

    @SHT_.define
    class SHT_GNU_verdef(ELFCLASSXX.SHT_GNU_verdef):
        _object_ = Elf64_Verdef

    @SHT_.define
    class SHT_GNU_verneed(ELFCLASSXX.SHT_GNU_verneed):
        _object_ = Elf64_Verneed

    @SHT_.define
    class SHT_GNU_versym(ELFCLASSXX.SHT_GNU_versym):
        _object_ = Elf64_Half

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

class SectionData(pstruct.type):
    def __data(self):
        item = self.__section__
        res = item.getreadsize()
        return dyn.block(res)

    def __alignment(self):
        item = self.__section__
        return dyn.align(item['sh_addralign'].int())

    _fields_ = [
        (__alignment, 'alignment'),
        (__data, 'data'),
    ]

class MixedSectionData(ptype.block):
    pass
class UndefinedSectionData(ptype.undefined):
    pass
