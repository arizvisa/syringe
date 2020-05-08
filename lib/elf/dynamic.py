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
        ('DT_SONAME', 14),
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

### 32-bit definitions
class ELFCLASS32(object):

    ## this should map d_tag to a type
    class DT_(ptype.definition):
        cache = {}

    ## types available for d_un
    class d_val(Elf32_Word): pass
    class d_ptr(Elf32_Addr): pass
    class d_ign(dyn.block(4)): pass

    ## dynamic entry type for d_un
    @DT_.define
    class DT_NULL(d_ign): type = 0
    @DT_.define
    class DT_NEEDED(d_val): type = 1 # FIXME
    @DT_.define
    class DT_PLTRELSZ(d_val): type = 2
    @DT_.define
    class DT_PLTGOT(d_ptr): type = 3
    @DT_.define
    class DT_HASH(d_ptr): type = 4
    @DT_.define
    class DT_STRTAB(d_ptr): type = 5
    @DT_.define
    class DT_SYMTAB(d_ptr): type = 6
    @DT_.define
    class DT_RELA(d_ptr): type = 7
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
    class DT_SONAME(d_val): type = 14
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
    class DT_PLTREL(d_val): type = 20
    @DT_.define
    class DT_DEBUG(d_ptr): type = 21
    @DT_.define
    class DT_TEXTREL(d_ign): type = 22
    @DT_.define
    class DT_JMPREL(d_ptr): type = 23
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
    class DT_VERDEF(d_val): type = 0x6ffffffc
    @DT_.define
    class DT_VERDEFNUM(d_val): type = 0x6ffffffd
    @DT_.define
    class DT_VERNEED(d_val): type = 0x6ffffffe
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
    class d_ptr(Elf64_Addr): pass
    class d_ign(dyn.block(8)): pass

    ## dynamic entry type for d_un
    @DT_.define
    class DT_NULL(d_ign): type = 0
    @DT_.define
    class DT_NEEDED(d_val): type = 1 # FIXME
    @DT_.define
    class DT_PLTRELSZ(d_val): type = 2
    @DT_.define
    class DT_PLTGOT(d_ptr): type = 3
    @DT_.define
    class DT_HASH(d_ptr): type = 4
    @DT_.define
    class DT_STRTAB(d_ptr): type = 5
    @DT_.define
    class DT_SYMTAB(d_ptr): type = 6
    @DT_.define
    class DT_RELA(d_ptr): type = 7
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
    class DT_SONAME(d_val): type = 14
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
    class DT_PLTREL(d_val): type = 20
    @DT_.define
    class DT_DEBUG(d_ptr): type = 21
    @DT_.define
    class DT_TEXTREL(d_ign): type = 22
    @DT_.define
    class DT_JMPREL(d_ptr): type = 23
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
    class DT_VERDEF(d_val): type = 0x6ffffffc
    @DT_.define
    class DT_VERDEFNUM(d_val): type = 0x6ffffffd
    @DT_.define
    class DT_VERNEED(d_val): type = 0x6ffffffe
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
        (dyn.pointer(pstr.szstring, Elf32_Addr), 'l_name'),
        (dyn.pointer(Elf32_Dyn, Elf32_Addr), 'l_ld'),
        (lambda self: dyn.pointer(link_map32, Elf32_Addr), 'l_next'),
        (lambda self: dyn.pointer(link_map32, Elf32_Addr), 'l_prev'),
    ]

class link_map64(pstruct.type):
    _fields_ = [
        (Elf64_Addr, 'l_addr'),
        (dyn.pointer(pstr.szstring, Elf64_Addr), 'l_name'),
        (dyn.pointer(Elf64_Dyn, Elf64_Addr), 'l_ld'),
        (lambda self: dyn.pointer(link_map64, Elf64_Addr), 'l_next'),
        (lambda self: dyn.pointer(link_map64, Elf64_Addr), 'l_prev'),
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
        (dyn.pointer(link_map32, Elf32_Addr), 'r_map'),
        (dyn.pointer(ptype.undefined, Elf32_Addr), 'r_brk'),
        (r_state, 'r_state'),
        (dyn.pointer(ptype.undefined, Elf32_Addr), 'r_ldbase'), # elf.File
    ]

class r_debug64(pstruct.type):
    class r_state(RT_, Elf64_Word): pass
    _fields_ = [
        (pint.int32_t, 'version'),
        (dyn.align(8), 'align(version)'),
        (dyn.pointer(link_map64, Elf64_Addr), 'r_map'),
        (dyn.pointer(ptype.undefined, Elf64_Addr), 'r_brk'),
        (r_state, 'r_state'),
        (dyn.align(8), 'align(r_state)'),
        (dyn.pointer(ptype.undefined, Elf64_Addr), 'r_ldbase'), # elf.File
    ]
