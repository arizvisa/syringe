from base import *

# This should map d_tag to type, and should point to all the definitions
class Type(ptype.definition):
    cache = {}

class Elf32_Dyn(pstruct.type):
    class d_tag(pint.enum, Elf32_Sword):
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

            ('DT_DEPRECATED_SPARC_REGISTER', 0x7000001),
            ('DT_CHECKSUM', 0x6ffffdf8),
            ('DT_PLTPADSZ', 0x6ffffdf9),
            ('DT_MOVEENT', 0x6ffffdfa),
            ('DT_MOVESZ', 0x6ffffdfb),
            ('DT_FEATURE_1', 0x6ffffdfc),
            ('DT_POSFLAG_1', 0x6ffffdfd),
            ('DT_SYMINSZ', 0x6ffffdfe),
            ('DT_SYMINENT', 0x6ffffdff),

            ('DT_CONFIG', 0x6ffffefa),
            ('DT_DEPAUDIT', 0x6ffffefb),
            ('DT_AUDIT', 0x6ffffefc),
            ('DT_PLTPAD', 0x6ffffefd),
            ('DT_MOVETAB', 0x6ffffefe),
            ('DT_SYMINFO', 0x6ffffeff),

            ('DT_VERSYM', 0x6ffffff0),
            ('DT_RELACOUNT', 0x6ffffff9),
            ('DT_RELCOUNT', 0x6ffffffa),
            ('DT_FLAGS_1', 0x6ffffffb),
            ('DT_VERDEF', 0x6ffffffc),
            ('DT_VERDEFNUM', 0x6ffffffd),
            ('DT_VERNEED', 0x6ffffffe),
            ('DT_VERNEEDNUM', 0x6fffffff),

            ('DT_AUXILIARY', 0x7ffffffd),
            ('DT_USED', 0x7ffffffe),
            ('DT_FILTER', 0x7fffffff),

            ('DT_GNU_PRELINKED', 0x6ffffdf5),
            ('DT_GNU_CONFLICTSZ', 0x6ffffdf6),
            ('DT_GNU_LIBLISTSZ', 0x6ffffdf7),

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
        ]

    def __d_val(self):
        res = self['d_tag'].li.int()
        return Type.lookup(res, dyn.clone(Type.unknown, type=res))

    _fields_ = [
        (d_tag, 'd_tag'),
        (__d_val, 'd_val'),
    ]

####
class d_val(Elf32_Word): pass
class d_ptr(Elf32_Addr): pass
class d_ign(dyn.block(4)): pass

####
@Type.define
class DT_NULL(d_ign): type = 0

@Type.define
class DT_NEEDED(d_val): type = 1
# FIXME

@Type.define
class DT_PLTRELSZ(d_val): type = 2

@Type.define
class DT_PLTGOT(d_ptr): type = 3

@Type.define
class DT_HASH(d_ptr): type = 4

@Type.define
class DT_STRTAB(d_ptr): type = 5

@Type.define
class DT_SYMTAB(d_ptr): type = 6

@Type.define
class DT_RELA(d_ptr): type = 7

@Type.define
class DT_RELASZ(d_val): type = 8

@Type.define
class DT_RELAENT(d_val): type = 9

@Type.define
class DT_STRSZ(d_val): type = 10

@Type.define
class DT_SYMENT(d_val): type = 11

@Type.define
class DT_INIT(d_ptr): type = 12

@Type.define
class DT_FINI(d_ptr): type = 13

@Type.define
class DT_SONAME(d_val): type = 14

@Type.define
class DT_RPATH(d_val): type = 15

@Type.define
class DT_SYMBOLIC(d_ign): type = 16

@Type.define
class DT_REL(d_ptr): type = 17

@Type.define
class DT_RELSZ(d_val): type = 18

@Type.define
class DT_RELENT(d_val): type = 19

@Type.define
class DT_PLTREL(d_val): type = 20

@Type.define
class DT_DEBUG(d_ptr): type = 21

@Type.define
class DT_TEXTREL(d_ign): type = 22

@Type.define
class DT_JMPREL(d_ptr): type = 23

@Type.define
class DT_BIND_NOW(d_ign): type = 24

@Type.define
class DT_INIT_ARRAY(d_ptr): type = 25

@Type.define
class DT_FINI_ARRAY(d_ptr): type = 26

@Type.define
class DT_INIT_ARRAYSZ(d_val): type = 27

@Type.define
class DT_FINI_ARRAYSZ(d_val): type = 28

@Type.define
class DT_RUNPATH(d_ptr): type = 29

@Type.define
class DT_FLAGS(d_val): type = 30

@Type.define
class DT_PREINIT_ARRAY(d_ptr): type = 32

@Type.define
class DT_PREINIT_ARRAYSZ(d_val): type = 33

@Type.define
class DT_MAXPOSTAGS(d_val): type = 34

@Type.define
class DT_SUNW_AUXILIARY(d_ptr): type = 0x6000000d

@Type.define
class DT_SUNW_RTLDINF(d_ptr): type = 0x6000000e

@Type.define
class DT_SUNW_FILTER(d_ptr): type = 0x6000000f

@Type.define
class DT_SUNW_CAP(d_val): type = 0x60000010

@Type.define
class DT_SUNW_SYMTAB(d_ptr): type = 0x60000011

@Type.define
class DT_SUNW_SYMSZ(d_val): type = 0x60000012

@Type.define
class DT_SUNW_SORTENT(d_val): type = 0x60000013

@Type.define
class DT_SUNW_SYMSORT(d_ptr): type = 0x60000014

@Type.define
class DT_SUNW_SYMSORTSZ(d_val): type = 0x60000015

@Type.define
class DT_SUNW_TLSSORT(d_ptr): type = 0x60000016

@Type.define
class DT_SUNW_TLSSORTSZ(d_val): type = 0x60000017

@Type.define
class DT_SUNW_STRPAD(d_val): type = 0x60000019

@Type.define
class DT_SUNW_LDMACH(d_val): type = 0x6000001b

@Type.define
class DT_DEPRECATED_SPARC_REGISTER(d_val): type = 0x7000001

@Type.define
class DT_CHECKSUM(d_val): type = 0x6ffffdf8

@Type.define
class DT_PLTPADSZ(d_val): type = 0x6ffffdf9

@Type.define
class DT_MOVEENT(d_val): type = 0x6ffffdfa

@Type.define
class DT_MOVESZ(d_val): type = 0x6ffffdfb

@Type.define
class DT_FEATURE_1(d_val): type = 0x6ffffdfc

@Type.define
class DT_POSFLAG_1(d_val): type = 0x6ffffdfd

@Type.define
class DT_SYMINSZ(d_val): type = 0x6ffffdfe

@Type.define
class DT_SYMINENT(d_val): type = 0x6ffffdff

@Type.define
class DT_CONFIG(d_ptr): type = 0x6ffffefa

@Type.define
class DT_DEPAUDIT(d_ptr): type = 0x6ffffefb

@Type.define
class DT_AUDIT(d_ptr): type = 0x6ffffefc

@Type.define
class DT_PLTPAD(d_ptr): type = 0x6ffffefd

@Type.define
class DT_MOVETAB(d_ptr): type = 0x6ffffefe

@Type.define
class DT_SYMINFO(d_ptr): type = 0x6ffffeff

@Type.define
class DT_VERSYM(d_ptr): type = 0x6ffffff0

@Type.define
class DT_RELACOUNT(d_val): type = 0x6ffffff9

@Type.define
class DT_RELCOUNT(d_val): type = 0x6ffffffa

@Type.define
class DT_FLAGS_1(d_val): type = 0x6ffffffb

@Type.define
class DT_VERDEF(d_ptr): type = 0x6ffffffc

@Type.define
class DT_VERDEFNUM(d_val): type = 0x6ffffffd

@Type.define
class DT_VERNEED(d_ptr): type = 0x6ffffffe

@Type.define
class DT_VERNEEDNUM(d_val): type = 0x6fffffff

@Type.define
class DT_AUXILIARY(d_ptr): type = 0x7ffffffd

@Type.define
class DT_USED(d_ptr): type = 0x7ffffffe

@Type.define
class DT_FILTER(d_ptr): type = 0x7fffffff

@Type.define
class DT_GNU_PRELINKED(d_val): type = 0x6ffffdf5

@Type.define
class DT_GNU_CONFLICTSZ(d_val): type = 0x6ffffdf6

@Type.define
class DT_GNU_LIBLISTSZ(d_val): type = 0x6ffffdf7

@Type.define
class DT_GNU_HASH(d_ptr): type = 0x6ffffef5

@Type.define
class DT_TLSDESC_PLT(d_ptr): type = 0x6ffffef6

@Type.define
class DT_TLSDESC_GOT(d_ptr): type = 0x6ffffef7

@Type.define
class DT_GNU_CONFLICT(d_ptr): type = 0x6ffffef8

@Type.define
class DT_GNU_LIBLIST(d_ptr): type = 0x6ffffef9

@Type.define
class DT_CONFIG(d_ptr): type = 0x6ffffefa

@Type.define
class DT_DEPAUDIT(d_ptr): type = 0x6ffffefb

@Type.define
class DT_AUDIT(d_ptr): type = 0x6ffffefc

@Type.define
class DT_PLTPAD(d_ptr): type = 0x6ffffefd

@Type.define
class DT_MOVETAB(d_ptr): type = 0x6ffffefe

@Type.define
class DT_SYMINFO(d_ptr): type = 0x6ffffeff

