import ptypes
from .base import *

### definition and enumerations for dynamic entry types

# legal values for d_tag (dynamic entry type)
class DT_(pint.enum):
    _values_ = [
        ('DT_NULL', 0),
        ('DT_NEEDED', 1),
        ('DT_PLTRELSZ', 2),
        ('DT_PLTGOT', 3),
        ('DT_HASH', 4),
        ('DT_STRTAB', 5),
        ('DT_SYMTAB', 6),
        ('DT_RELA', 7),
        ('DT_RELASZ', 8),
        ('DT_RELAENT', 9),
        ('DT_STRSZ', 10),
        ('DT_SYMENT', 11),
        ('DT_INIT', 12),
        ('DT_FINI', 13),
        ('DT_SONAME', 14),      # offset into string table
        ('DT_RPATH', 15),
        ('DT_SYMBOLIC', 16),
        ('DT_REL', 17),
        ('DT_RELSZ', 18),
        ('DT_RELENT', 19),
        ('DT_PLTREL', 20),
        ('DT_DEBUG', 21),
        ('DT_TEXTREL', 22),
        ('DT_JMPREL', 23),

        ('DT_BIND_NOW', 24),
        ('DT_INIT_ARRAY', 25),
        ('DT_FINI_ARRAY', 26),
        ('DT_INIT_ARRAYSZ', 27),
        ('DT_FINI_ARRAYSZ', 28),
        ('DT_RUNPATH', 29),
        ('DT_FLAGS', 30),

        ('DT_PREINIT_ARRAY', 32),
        ('DT_PREINIT_ARRAYSZ', 33),
        ('DT_MAXPOSTAGS', 34),
        ('DT_NUM', 35),

        # DT_VALRNGLO(0x6ffffd00) - DT_VALRNGHI(0x6ffffdff)
        ('DT_GNU_PRELINKED', 0x6ffffdf5),
        ('DT_GNU_CONFLICTSZ', 0x6ffffdf6),
        ('DT_GNU_LIBLISTSZ', 0x6ffffdf7),
        ('DT_CHECKSUM', 0x6ffffdf8),
        ('DT_PLTPADSZ', 0x6ffffdf9),
        ('DT_MOVEENT', 0x6ffffdfa),
        ('DT_MOVESZ', 0x6ffffdfb),
        ('DT_FEATURE_1', 0x6ffffdfc),
        ('DT_POSFLAG_1', 0x6ffffdfd),
        ('DT_SYMINSZ', 0x6ffffdfe),
        ('DT_SYMINENT', 0x6ffffdff),

        # DT_ADDRRNGLO(0x6ffffe00) - DT_ADDRRNGHI(0x6ffffeff)
        ('DT_GNU_HASH', 0x6ffffef5),
        ('DT_TLSDESC_PLT', 0x6ffffef6),
        ('DT_TLSDESC_GOT', 0x6ffffef7),
        ('DT_GNU_CONFLICT', 0x6ffffef8),
        ('DT_GNU_LIBLIST', 0x6ffffef9),
        ('DT_CONFIG', 0x6ffffefa),
        ('DT_DEPAUDIT', 0x6ffffefb),
        ('DT_AUDIT', 0x6ffffefc),
        ('DT_PLTPAD', 0x6ffffefd),
        ('DT_MOVETAB', 0x6ffffefe),
        ('DT_SYMINFO', 0x6ffffeff),

        # GNU extensions (versioning entry types)
        ('DT_VERSYM', 0x6ffffff0),
        ('DT_RELACOUNT', 0x6ffffff9),
        ('DT_RELCOUNT', 0x6ffffffa),
        ('DT_FLAGS_1', 0x6ffffffb),
        ('DT_VERDEF', 0x6ffffffc),
        ('DT_VERDEFNUM', 0x6ffffffd),
        ('DT_VERNEED', 0x6ffffffe),
        ('DT_VERNEEDNUM', 0x6fffffff),

        # Sun machine-independant extensions
        ('DT_AUXILIARY', 0x7ffffffd),
        ('DT_USED', 0x7ffffffe),
        ('DT_FILTER', 0x7fffffff),

        # SUN machine-dependant extensions
        ('DT_DEPRECATED_SPARC_REGISTER', 0x7000001),

        ('DT_SUNW_AUXILIARY', 0x6000000d),
        ('DT_SUNW_RTLDINF', 0x6000000e),
        ('DT_SUNW_FILTER', 0x6000000f),
        ('DT_SUNW_CAP', 0x60000010),
        ('DT_SUNW_SYMTAB', 0x60000011),
        ('DT_SUNW_SYMSZ', 0x60000012),
        ('DT_SUNW_SORTENT', 0x60000013),
        ('DT_SUNW_SYMSORT', 0x60000014),
        ('DT_SUNW_SYMSORTSZ', 0x60000015),
        ('DT_SUNW_TLSSORT', 0x60000016),
        ('DT_SUNW_TLSSORTSZ', 0x60000017),
        ('DT_SUNW_STRPAD', 0x60000019),
        ('DT_SUNW_LDMACH', 0x6000001b),
    ]

### generic definitions
class DF_(pbinary.flags):
    _fields_ = [
        (27, 'RESERVED'),
        (1, 'STATIC_TLS'),
        (1, 'BIND_NOW'),
        (1, 'TEXTREL'),
        (1, 'SYMBOLIc'),
        (1, 'ORIGIN'),
    ]

class DF_1_(pbinary.flags):
    _fields_ = [
        (1, 'RESERVED'),
        (1, 'NOCOMMON'),
        (1, 'WEAKFILTER'),
        (1, 'KMOD'),
        (1, 'PIE'),
        (1, 'STUB'),
        (1, 'SINGLETON'),
        (1, 'GLOBAUDIT'),
        (1, 'SYMINTPOSE'),
        (1, 'NORELOC'),
        (1, 'EDITED'),
        (1, 'NOHDR'),
        (1, 'NOKSYMS'),
        (1, 'IGNMULDEF'),
        (1, 'NODIRECT'),
        (1, 'DISPRELPND'),
        (1, 'DISPRELDNE'),
        (1, 'ENDFILTEE'),
        (1, 'CONFALT'),
        (1, 'NODUMP'),
        (1, 'NODEFLIB'),
        (1, 'INTERPOSE'),
        (1, 'TRANS'),
        (1, 'DIRECT'),
        (1, 'ORIGIN'),
        (1, 'NOOPEN'),
        (1, 'INITFIRST'),
        (1, 'LOADFLTR'),
        (1, 'NODELETE'),
        (1, 'GROUP'),
        (1, 'GLOBAL'),
        (1, 'NOW'),
    ]

class DTF_1_(pbinary.flags):
    _fields_ = [
        (30, 'RESERVED'),
        (1, 'CONFEXP'),
        (1, 'PARINIT'),
    ]

class DF_P1_(pbinary.flags):
    _fields_ = [
        (30, 'RESERVED'),
        (1, 'GROUPPERM'),
        (1, 'LAZYLOAD'),
    ]

### version definitions
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
        res, fields = self['vna_next'].li, ['vna_hash', 'vna_flags', 'vna_other', 'vna_name']
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
        res, fields = self['vna_next'].li, ['vna_hash', 'vna_flags', 'vna_other', 'vna_name']
        return dyn.block(max(0, res.int() - sum(self[fld].li.size() for fld in fields)))
    _fields_ = [
        (Elf64_Word, 'vna_hash'),
        (Elf64_Half, 'vna_flags'),
        (Elf64_Half, 'vna_other'),
        (dyn.clone(ElfXX_VerXauxName, _value_=Elf64_Word), 'vna_name'),
        (Elf64_Word, 'vna_next'),   # Offset in bytes to next vernaux
        (__padding_vna_next, 'padding(vna_next)'),
    ]

### 32-bit definitions
class ELFCLASS32(object):

    ## this should map d_tag to a type
    class DT_(ptype.definition):
        cache = {}

    ## types available for d_un
    class d_val(Elf32_Word): pass
    class d_baseptr(Elf32_BaseAddr): pass
    class d_vaptr(Elf32_VAddr): pass
    class d_ptr(Elf32_Addr): pass
    class d_ign(dyn.block(4)): pass
    class d_rtptr(Elf32_VAddr):
        def _calculate_(self, address):
            return address if isinstance(self.source, ptypes.provider.memorybase) else super(ELFCLASS32.d_rtptr, self)._calculate_(address)

    ## dynamic entry type for d_un
    @DT_.define
    class DT_NULL(d_ign): type = 0
    @DT_.define
    class DT_NEEDED(d_val): type = 1 # FIXME
    @DT_.define
    class DT_PLTRELSZ(d_val): type = 2
    @DT_.define
    class DT_PLTGOT(d_vaptr):
        type = 3
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            # first entry is a Elf32_VAddr to the dynamic segment
            dt_jmprel = p.by_tag('DT_JMPREL')
            return dyn.array(Elf32_Addr, 3 + len(dt_jmprel.d.li))
    @DT_.define
    class DT_HASH(d_ptr): type = 4
    @DT_.define
    class DT_STRTAB(d_ptr):
        type = 5
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_strsz = p.by_tag('DT_STRSZ')

            from .section import ELFCLASS32
            return dyn.clone(ELFCLASS32.SHT_STRTAB, blocksize=dt_strsz.int)
    @DT_.define
    class DT_SYMTAB(d_ptr):
        type = 6
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            # XXX: apparently the glibc folks are determining the symtab size
            #      by assuming the strtab immediately follows it. Heh.
            from .section import ELFCLASS32
            dt_strtab = p.by_tag('DT_STRTAB')
            dt_syment = p.by_tag('DT_SYMENT')
            return dyn.clone(ELFCLASS32.SHT_SYMTAB, blocksize=lambda self, cb=dt_strtab.int() - self.int(): cb)
    @DT_.define
    class DT_RELA(d_ptr):
        type = 7
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            from .section import Elf32_Rela
            dt_relaent = p.by_tag('DT_RELAENT')
            res = p.by_tag(['DT_RELASZ', 'DT_RELACOUNT'])
            if isinstance(res, ELFCLASS32.DT_RELASZ):
                return dyn.blockarray(Elf32_Rela, res.int())
            elif isinstance(res, ELFCLASS32.DT_RELACOUNT):
                return dyn.array(Elf32_Rela, res.int())
            raise NotImplementedError
    @DT_.define
    class DT_RELASZ(d_val): type = 8
    @DT_.define
    class DT_RELAENT(d_val): type = 9
    @DT_.define
    class DT_STRSZ(d_val): type = 10
    @DT_.define
    class DT_SYMENT(d_val): type = 11
    @DT_.define
    class DT_INIT(d_ptr): type = 12
    @DT_.define
    class DT_FINI(d_ptr): type = 13
    @DT_.define
    class DT_SONAME(d_val):
        type = 14
        def dereference(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_strtab = p.by_tag('DT_STRTAB')
            res = dt_strtab.d.li
            return res.field(self.get())
        d = property(fget=dereference)
        def str(self):
            res = self.dereference()
            return res.str()
    @DT_.define
    class DT_RPATH(d_val): type = 15
    @DT_.define
    class DT_SYMBOLIC(d_ign): type = 16
    @DT_.define
    class DT_REL(d_ptr): type = 17
    @DT_.define
    class DT_RELSZ(d_val): type = 18
    @DT_.define
    class DT_RELENT(d_val): type = 19
    @DT_.define
    class DT_PLTREL(pint.enum, d_val):
        type = 20
        _values_ = [
            ('DT_RELA', 7),
            ('DT_REL', 17),
        ]
    @DT_.define
    class DT_DEBUG(d_ptr): type = 21
    @DT_.define
    class DT_TEXTREL(d_ign): type = 22
    @DT_.define
    class DT_JMPREL(d_ptr):
        type = 23
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            from .section import Elf64_Rel, Elf64_Rela
            dt_pltrelsz = p.by_tag('DT_PLTRELSZ')
            dt_pltrel = p.by_tag('DT_PLTREL')
            if dt_pltrel['DT_REL']:
                t = Elf64_Rel
            elif dt_pltrel['DT_RELA']:
                t = Elf64_Rela
            else:
                raise NotImplementedError(dt_pltrel)
            return dyn.blockarray(t, dt_pltrelsz.int())
    @DT_.define
    class DT_BIND_NOW(d_ign): type = 24
    @DT_.define
    class DT_INIT_ARRAY(d_ptr): type = 25
    @DT_.define
    class DT_FINI_ARRAY(d_ptr): type = 26
    @DT_.define
    class DT_INIT_ARRAYSZ(d_val): type = 27
    @DT_.define
    class DT_FINI_ARRAYSZ(d_val): type = 28
    @DT_.define
    class DT_RUNPATH(d_ptr): type = 29
    @DT_.define
    class DT_FLAGS(DF_): type = 30
    @DT_.define
    class DT_PREINIT_ARRAY(d_ptr): type = 32
    @DT_.define
    class DT_PREINIT_ARRAYSZ(d_val): type = 33
    @DT_.define
    class DT_MAXPOSTAGS(d_val): type = 34
    @DT_.define
    class DT_NUM(d_val): type = 35

    # DT_VALRNGLO(0x6ffffd00) - DT_VALRNGHI(0x6ffffdff)
    @DT_.define
    class DT_GNU_PRELINKED(d_val): type = 0x6ffffdf5
    @DT_.define
    class DT_GNU_CONFLICTSZ(d_val): type = 0x6ffffdf6
    @DT_.define
    class DT_GNU_LIBLISTSZ(d_val): type = 0x6ffffdf7
    @DT_.define
    class DT_CHECKSUM(d_val): type = 0x6ffffdf8
    @DT_.define
    class DT_PLTPADSZ(d_val): type = 0x6ffffdf9
    @DT_.define
    class DT_MOVEENT(d_val): type = 0x6ffffdfa
    @DT_.define
    class DT_MOVESZ(d_val): type = 0x6ffffdfb
    @DT_.define
    class DT_FEATURE_1(DTF_1_): type = 0x6ffffdfc
    @DT_.define
    class DT_POSFLAG_1(DF_P1_): type = 0x6ffffdfd
    @DT_.define
    class DT_SYMINSZ(d_val): type = 0x6ffffdfe
    @DT_.define
    class DT_SYMINENT(d_val): type = 0x6ffffdff

    # DT_ADDRRNGLO(0x6ffffe00) - DT_ADDRRNGHI(0x6ffffeff)
    @DT_.define
    class DT_GNU_HASH(d_ptr): type = 0x6ffffef5
    @DT_.define
    class DT_TLSDESC_PLT(d_ptr): type = 0x6ffffef6
    @DT_.define
    class DT_TLSDESC_GOT(d_ptr): type = 0x6ffffef7
    @DT_.define
    class DT_GNU_CONFLICT(d_ptr): type = 0x6ffffef8
    @DT_.define
    class DT_GNU_LIBLIST(d_ptr): type = 0x6ffffef9
    @DT_.define
    class DT_CONFIG(d_ptr): type = 0x6ffffefa
    @DT_.define
    class DT_DEPAUDIT(d_ptr): type = 0x6ffffefb
    @DT_.define
    class DT_AUDIT(d_ptr): type = 0x6ffffefc
    @DT_.define
    class DT_PLTPAD(d_ptr): type = 0x6ffffefd
    @DT_.define
    class DT_MOVETAB(d_ptr): type = 0x6ffffefe
    @DT_.define
    class DT_SYMINFO(d_ptr): type = 0x6ffffeff

    # GNU extensions (versioning entry types)
    @DT_.define
    class DT_VERSYM(d_val): type = 0x6ffffff0
    @DT_.define
    class DT_RELACOUNT(d_val): type = 0x6ffffff9
    @DT_.define
    class DT_RELCOUNT(d_val): type = 0x6ffffffa
    @DT_.define
    class DT_FLAGS_1(DF_1_): type = 0x6ffffffb
    @DT_.define
    class DT_VERDEF(d_baseptr):
        type = 0x6ffffffc
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_verdefnum = p.by_tag('DT_VERDEFNUM')
            return dyn.array(Elf32_Verdef, dt_verdefnum.int())
    @DT_.define
    class DT_VERDEFNUM(d_val): type = 0x6ffffffd
    @DT_.define
    class DT_VERNEED(d_baseptr):
        type = 0x6ffffffe
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_verneednum = p.by_tag('DT_VERNEEDNUM')
            return dyn.array(Elf32_Verneed, dt_verneednum.int())
    @DT_.define
    class DT_VERNEEDNUM(d_val): type = 0x6fffffff

    # Sun machine-independant extensions
    @DT_.define
    class DT_AUXILIARY(d_val): type = 0x7ffffffd
    @DT_.define
    class DT_USED(d_val): type = 0x7ffffffe
    @DT_.define
    class DT_FILTER(d_val): type = 0x7fffffff

    # SUN machine-dependant extensions
    @DT_.define
    class DT_DEPRECATED_SPARC_REGISTER(d_val): type = 0x7000001
    @DT_.define
    class DT_SUNW_AUXILIARY(d_ptr): type = 0x6000000d
    @DT_.define
    class DT_SUNW_RTLDINF(d_ptr): type = 0x6000000e
    @DT_.define
    class DT_SUNW_FILTER(d_ptr): type = 0x6000000f
    @DT_.define
    class DT_SUNW_CAP(d_val): type = 0x60000010
    @DT_.define
    class DT_SUNW_SYMTAB(d_ptr): type = 0x60000011
    @DT_.define
    class DT_SUNW_SYMSZ(d_val): type = 0x60000012
    @DT_.define
    class DT_SUNW_SORTENT(d_val): type = 0x60000013
    @DT_.define
    class DT_SUNW_SYMSORT(d_ptr): type = 0x60000014
    @DT_.define
    class DT_SUNW_SYMSORTSZ(d_val): type = 0x60000015
    @DT_.define
    class DT_SUNW_TLSSORT(d_ptr): type = 0x60000016
    @DT_.define
    class DT_SUNW_TLSSORTSZ(d_val): type = 0x60000017
    @DT_.define
    class DT_SUNW_STRPAD(d_val): type = 0x60000019
    @DT_.define
    class DT_SUNW_LDMACH(d_val): type = 0x6000001b

### 64-bit definitions
class ELFCLASS64(object):

    ## this should map d_tag to a type
    class DT_(ptype.definition):
        cache = {}

    ## types available for d_un
    class d_val(Elf64_Xword): pass
    class d_baseptr(Elf64_BaseAddr): pass
    class d_vaptr(Elf64_VAddr): pass
    class d_ptr(Elf64_Addr): pass
    class d_ign(dyn.block(8)): pass
    class d_rtptr(Elf64_VAddr):
        def _calculate_(self, address):
            return address if isinstance(self.source, ptypes.provider.memorybase) else super(ELFCLASS64.d_rtptr, self)._calculate_(address)

    ## dynamic entry type for d_un
    @DT_.define
    class DT_NULL(d_ign): type = 0
    @DT_.define
    class DT_NEEDED(d_val): type = 1 # FIXME
    @DT_.define
    class DT_PLTRELSZ(d_val): type = 2
    @DT_.define
    class DT_PLTGOT(d_rtptr):
        type = 3
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            # first entry is a Elf64_VAddr to the dynamic segment
            dt_jmprel = p.by_tag('DT_JMPREL')
            return dyn.array(Elf64_Addr, 3 + len(dt_jmprel.d.li))
    @DT_.define
    class DT_HASH(d_ptr): type = 4
    @DT_.define
    class DT_STRTAB(d_ptr):
        type = 5
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_strsz = p.by_tag('DT_STRSZ')

            from .section import ELFCLASS64
            return dyn.clone(ELFCLASS64.SHT_STRTAB, blocksize=dt_strsz.int)
    @DT_.define
    class DT_SYMTAB(d_ptr):
        type = 6
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            # XXX: apparently the glibc folks are determining the symtab size
            #      by assuming the strtab immediately follows it. Heh.
            from .section import ELFCLASS64
            dt_strtab = p.by_tag('DT_STRTAB')
            dt_syment = p.by_tag('DT_SYMENT')
            return dyn.clone(ELFCLASS64.SHT_SYMTAB, blocksize=lambda self, cb=dt_strtab.int() - self.int(): cb)
    @DT_.define
    class DT_RELA(d_ptr):
        type = 7
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            from .section import Elf64_Rela
            dt_relaent = p.by_tag('DT_RELAENT')
            res = p.by_tag(['DT_RELASZ', 'DT_RELACOUNT'])
            if isinstance(res, ELFCLASS64.DT_RELASZ):
                return dyn.blockarray(Elf64_Rela, res.int())
            elif isinstance(res, ELFCLASS64.DT_RELACOUNT):
                return dyn.array(Elf64_Rela, res.int())
            raise NotImplementedError
    @DT_.define
    class DT_RELASZ(d_val): type = 8
    @DT_.define
    class DT_RELAENT(d_val): type = 9
    @DT_.define
    class DT_STRSZ(d_val): type = 10
    @DT_.define
    class DT_SYMENT(d_val): type = 11
    @DT_.define
    class DT_INIT(d_ptr): type = 12
    @DT_.define
    class DT_FINI(d_ptr): type = 13
    @DT_.define
    class DT_SONAME(d_val):
        type = 14
        def dereference(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_strtab = p.by_tag('DT_STRTAB')
            res = dt_strtab.d.li
            return res.field(self.get())
        d = property(fget=dereference)
        def str(self):
            res = self.dereference()
            return res.str()
    @DT_.define
    class DT_RPATH(d_val): type = 15
    @DT_.define
    class DT_SYMBOLIC(d_ign): type = 16
    @DT_.define
    class DT_REL(d_ptr): type = 17
    @DT_.define
    class DT_RELSZ(d_val): type = 18
    @DT_.define
    class DT_RELENT(d_val): type = 19
    @DT_.define
    class DT_PLTREL(pint.enum, d_val):
        type = 20
        _values_ = [
            ('DT_RELA', 7),
            ('DT_REL', 17),
        ]
    @DT_.define
    class DT_DEBUG(d_ptr): type = 21
    @DT_.define
    class DT_TEXTREL(d_ign): type = 22
    @DT_.define
    class DT_JMPREL(d_ptr):
        type = 23
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)

            from .section import Elf64_Rel, Elf64_Rela
            dt_pltrelsz = p.by_tag('DT_PLTRELSZ')
            dt_pltrel = p.by_tag('DT_PLTREL')
            if dt_pltrel['DT_REL']:
                t = Elf64_Rel
            elif dt_pltrel['DT_RELA']:
                t = Elf64_Rela
            else:
                raise NotImplementedError(dt_pltrel)
            return dyn.blockarray(t, dt_pltrelsz.int())
    @DT_.define
    class DT_BIND_NOW(d_ign): type = 24
    @DT_.define
    class DT_INIT_ARRAY(d_ptr): type = 25
    @DT_.define
    class DT_FINI_ARRAY(d_ptr): type = 26
    @DT_.define
    class DT_INIT_ARRAYSZ(d_val): type = 27
    @DT_.define
    class DT_FINI_ARRAYSZ(d_val): type = 28
    @DT_.define
    class DT_RUNPATH(d_ptr): type = 29
    @DT_.define
    class DT_FLAGS(DF_):
        type, _fields_ = 30, [(32, 'alignment')] + DF_._fields_
    @DT_.define
    class DT_PREINIT_ARRAY(d_ptr): type = 32
    @DT_.define
    class DT_PREINIT_ARRAYSZ(d_val): type = 33
    @DT_.define
    class DT_MAXPOSTAGS(d_val): type = 34
    @DT_.define
    class DT_NUM(d_val): type = 35

    # DT_VALRNGLO(0x6ffffd00) - DT_VALRNGHI(0x6ffffdff)
    @DT_.define
    class DT_GNU_PRELINKED(d_val): type = 0x6ffffdf5
    @DT_.define
    class DT_GNU_CONFLICTSZ(d_val): type = 0x6ffffdf6
    @DT_.define
    class DT_GNU_LIBLISTSZ(d_val): type = 0x6ffffdf7
    @DT_.define
    class DT_CHECKSUM(d_val): type = 0x6ffffdf8
    @DT_.define
    class DT_PLTPADSZ(d_val): type = 0x6ffffdf9
    @DT_.define
    class DT_MOVEENT(d_val): type = 0x6ffffdfa
    @DT_.define
    class DT_MOVESZ(d_val): type = 0x6ffffdfb
    @DT_.define
    class DT_FEATURE_1(DTF_1_):
        type, _fields_ = 0x6ffffdfc, [(32, 'alignment')] + DTF_1_._fields_
    @DT_.define
    class DT_POSFLAG_1(DF_P1_):
        type, _fields_ = 0x6ffffdfd, [(32, 'alignment')] + DF_P1_._fields_
    @DT_.define
    class DT_SYMINSZ(d_val): type = 0x6ffffdfe
    @DT_.define
    class DT_SYMINENT(d_val): type = 0x6ffffdff

    # DT_ADDRRNGLO(0x6ffffe00) - DT_ADDRRNGHI(0x6ffffeff)
    @DT_.define
    class DT_GNU_HASH(d_ptr): type = 0x6ffffef5
    @DT_.define
    class DT_TLSDESC_PLT(d_ptr): type = 0x6ffffef6
    @DT_.define
    class DT_TLSDESC_GOT(d_ptr): type = 0x6ffffef7
    @DT_.define
    class DT_GNU_CONFLICT(d_ptr): type = 0x6ffffef8
    @DT_.define
    class DT_GNU_LIBLIST(d_ptr): type = 0x6ffffef9
    @DT_.define
    class DT_CONFIG(d_ptr): type = 0x6ffffefa
    @DT_.define
    class DT_DEPAUDIT(d_ptr): type = 0x6ffffefb
    @DT_.define
    class DT_AUDIT(d_ptr): type = 0x6ffffefc
    @DT_.define
    class DT_PLTPAD(d_ptr): type = 0x6ffffefd
    @DT_.define
    class DT_MOVETAB(d_ptr): type = 0x6ffffefe
    @DT_.define
    class DT_SYMINFO(d_ptr): type = 0x6ffffeff

    # GNU extensions (versioning entry types)
    @DT_.define
    class DT_VERSYM(d_val): type = 0x6ffffff0
    @DT_.define
    class DT_RELACOUNT(d_val): type = 0x6ffffff9
    @DT_.define
    class DT_RELCOUNT(d_val): type = 0x6ffffffa
    @DT_.define
    class DT_FLAGS_1(DF_1_):
        type, _fields_ = 0x6ffffffb, [(32, 'alignment')] + DF_1_._fields_
    @DT_.define
    class DT_VERDEF(d_baseptr):
        type = 0x6ffffffc
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_verdefnum = p.by_tag('DT_VERDEFNUM')
            return dyn.array(Elf64_Verdef, dt_verdefnum.int())
    @DT_.define
    class DT_VERDEFNUM(d_val): type = 0x6ffffffd
    @DT_.define
    class DT_VERNEED(d_baseptr):
        type = 0x6ffffffe
        def _object_(self):
            from .segment import ELFCLASSXX
            p = self.getparent(ELFCLASSXX.PT_DYNAMIC)
            dt_verneednum = p.by_tag('DT_VERNEEDNUM')
            return dyn.array(Elf64_Verneed, dt_verneednum.int())
    @DT_.define
    class DT_VERNEEDNUM(d_val): type = 0x6fffffff

    # Sun machine-independant extensions
    @DT_.define
    class DT_AUXILIARY(d_val): type = 0x7ffffffd
    @DT_.define
    class DT_USED(d_val): type = 0x7ffffffe
    @DT_.define
    class DT_FILTER(d_val): type = 0x7fffffff

    # SUN machine-dependant extensions
    @DT_.define
    class DT_DEPRECATED_SPARC_REGISTER(d_val): type = 0x7000001
    @DT_.define
    class DT_SUNW_AUXILIARY(d_ptr): type = 0x6000000d
    @DT_.define
    class DT_SUNW_RTLDINF(d_ptr): type = 0x6000000e
    @DT_.define
    class DT_SUNW_FILTER(d_ptr): type = 0x6000000f
    @DT_.define
    class DT_SUNW_CAP(d_val): type = 0x60000010
    @DT_.define
    class DT_SUNW_SYMTAB(d_ptr): type = 0x60000011
    @DT_.define
    class DT_SUNW_SYMSZ(d_val): type = 0x60000012
    @DT_.define
    class DT_SUNW_SORTENT(d_val): type = 0x60000013
    @DT_.define
    class DT_SUNW_SYMSORT(d_ptr): type = 0x60000014
    @DT_.define
    class DT_SUNW_SYMSORTSZ(d_val): type = 0x60000015
    @DT_.define
    class DT_SUNW_TLSSORT(d_ptr): type = 0x60000016
    @DT_.define
    class DT_SUNW_TLSSORTSZ(d_val): type = 0x60000017
    @DT_.define
    class DT_SUNW_STRPAD(d_val): type = 0x60000019
    @DT_.define
    class DT_SUNW_LDMACH(d_val): type = 0x6000001b

### dynamic section entry
class ElfXX_Dyn(pstruct.type): pass

class Elf32_Dyn(ElfXX_Dyn):
    class _d_tag(DT_, Elf32_Sword):
        pass

    def __d_un(self):
        res = self['d_tag'].li.int()
        return ELFCLASS32.DT_.withdefault(res, type=res)

    _fields_ = [
        (_d_tag, 'd_tag'),
        (__d_un, 'd_un'),
    ]

class Elf64_Dyn(ElfXX_Dyn):
    class _d_tag(DT_, Elf64_Sxword):
        pass

    def __d_un(self):
        res = self['d_tag'].li.int()
        return ELFCLASS64.DT_.withdefault(res, type=res)

    _fields_ = [
        (_d_tag, 'd_tag'),
        (__d_un, 'd_un'),
    ]

### link_maps
class link_map32(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'l_addr'),
        (dyn.clone(Elf32_Addr, _object_=pstr.szstring), 'l_name'),
        (dyn.clone(Elf32_Addr, _object_=Elf32_Dyn), 'l_ld'),
        (lambda self: dyn.clone(Elf32_Addr, _object_=link_map32), 'l_next'),
        (lambda self: dyn.clone(Elf32_Addr, _object_=link_map32), 'l_prev'),
    ]

class link_map64(pstruct.type):
    _fields_ = [
        (Elf64_Addr, 'l_addr'),
        (dyn.clone(Elf64_Addr, _object_=pstr.szstring), 'l_name'),
        (dyn.pointer(pstr.szstring, Elf64_Addr), 'l_name'),
        (dyn.clone(Elf64_Addr, _object_=Elf64_Dyn), 'l_ld'),
        (lambda self: dyn.clone(Elf64_Addr, _object_=link_map64), 'l_next'),
        (lambda self: dyn.clone(Elf64_Addr, _object_=link_map64), 'l_prev'),
    ]

class RT_(pint.enum):
    _values_ = [
        ('RT_CONSISTENT', 0),
        ('RT_ADD', 1),
        ('RT_DELETE', 2),
    ]

class r_debug32(pstruct.type):
    class r_state(RT_, Elf32_Word): pass
    _fields_ = [
        (pint.int32_t, 'version'),
        (dyn.clone(Elf32_Addr, _object_=link_map32), 'r_map'),
        (Elf32_Addr, 'r_brk'),
        (r_state, 'r_state'),
        (Elf32_Addr, 'r_ldbase'), # elf.File
    ]

class r_debug64(pstruct.type):
    class r_state(RT_, Elf64_Word): pass
    _fields_ = [
        (pint.int32_t, 'version'),
        (dyn.align(8), 'align(version)'),
        (dyn.clone(Elf64_Addr, _object_=link_map64), 'r_map'),
        (Elf64_Addr, 'r_brk'),
        (r_state, 'r_state'),
        (dyn.align(8), 'align(r_state)'),
        (Elf64_Addr, 'r_ldbase'), # elf.File
    ]
