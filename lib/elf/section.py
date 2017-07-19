import ptypes
from .base import *

### generic
class _sh_name(pint.type):
    def summary(self):
        try:
            res = self.str()
        except (ptypes.error.TypeError, ptypes.error.NotFoundError):
            return super(_sh_name, self).summary()
        return '{:s} : {!r}'.format(super(_sh_name, self).summary(), res)

    def str(self):
        table = self.getparent(ElfXX_Ehdr).stringtable()
        if isinstance(table, SHT_STRTAB):
            return table.read(self.int()).str()
        raise ptypes.error.TypeError(self, 'str')

class _sh_type(pint.enum):
    SHT_LOSUNW, SHT_HISUNW = 0x6ffffffa, 0x6fffffff
    SHT_LOOS, SHT_HIOS = 0x60000000, 0x6fffffff
    SHT_LOPROC, SHT_HIPROC = 0x70000000, 0x7fffffff
    SHT_LOUSER, SHT_HIUSER = 0x80000000, 0xffffffff

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
        ('SHT_NUM', 19),

        ('SHT_CHECKSUM', 0x6ffffff8),

        ('SHT_SUNW_move', 0x6ffffffa),
        ('SHT_SUNW_COMDAT', 0x6ffffffb),
        ('SHT_SUNW_syminfo', 0x6ffffffc),

        ('SHT_GNU_HASH', 0x6ffffff6),
        ('SHT_GNU_LIBLIST', 0x6ffffff7),
        ('SHT_GNU_verdef', 0x6ffffffd),
        ('SHT_GNU_verneed', 0x6ffffffe),
        ('SHT_GNU_versym', 0x6fffffff),

        ('SHT_ARM_EXIDX', 0x70000001),
        ('SHT_ARM_PREEMPTMAP', 0x70000002),
        ('SHT_ARM_ATTRIBUTES', 0x70000003),
        ('SHT_ARM_DEBUGOVERLAY', 0x70000004),
        ('SHT_ARM_OVERLAYSECTION', 0x70000005),
    ]

class _sh_flags(pbinary.flags):
    # Elf32_Word
    _fields_ = [
        (4, 'SHF_MASKPROC'),        # FIXME: lookup based on processor
        (8, 'SHF_MASKOS'),          # FIXME: lookup based on platform
        (10, 'SHF_UNKNOWN'),
        (1, 'SHF_GROUP'),
        (1, 'SHF_OS_NONCONFORMING'),
        (1, 'SHF_LINK_ORDER'),
        (1, 'SHF_INFO_LINK'),
        (1, 'SHF_STRINGS'),
        (1, 'SHF_MERGE'),
        (1, 'SHF_UNUSED'),
        (1, 'SHF_EXECINSTR'),
        (1, 'SHF_ALLOC'),
        (1, 'SHF_WRITE'),
    ]

def _sh_offset(size):
    def sh_offset(self):
        res = self['sh_type'].li.int()
        type = Type.get(res, type=res)   # XXX: not 64-bit
        #return dyn.rpointer( lambda s: dyn.clone(type, blocksize=lambda _:int(s.getparent(Elf32_Shdr)['sh_size'].li)), lambda s: s.getparent(ElfXX_File), Elf32_Off)

        base = self.getparent(ElfXX_File)
        result = dyn.clone(type, blocksize=lambda s: self['sh_size'].li.int())
        return dyn.rpointer(result, base, size)
    return sh_offset

class _sh_index(pint.enum):
    SHN_LOPROC, SHN_HIPROC = 0xff00, 0xff1f
    SHN_LOOS, SHN_HIOS = 0xff20, 0xff3f
    SHN_LORESERVE, SHN_HIRESERVE = 0xff00, 0xffff
    _values_ = [
        ('SHN_UNDEF', 0),
        ('SHN_BEFORE', 0xff00),
        ('SHN_AFTER', 0xff01),
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
        return '{:s} : {!r}'.format(super(_st_name, self).summary(), res)

    def str(self):
        index = self.getparent(ElfXX_Shdr)['sh_link'].int()
        res = self.getparent(ElfXX_Ehdr)['e_shoff'].d.li
        if index >= len(res):
            raise ptypes.error.NotFoundError(self, 'str')
        table = res[index]['sh_offset'].d.li
        if isinstance(table, SHT_STRTAB):
            return table.read(self.int()).str()
        raise ptypes.error.TypeError(self, 'str')

class st_info(pbinary.struct):
    class st_bind(pbinary.enum):
        width = 4
        STB_LOPROC, STB_HIPROC = 13, 15
        _values_ = [
            ('STB_LOCAL', 0),
            ('STB_GLOBAL', 1),
            ('STB_WEAK', 2),
        ]
    class st_type(pbinary.enum):
        width = 4
        STT_LOPROC, STT_HIPROC = 13, 15
        _values_ = [
            ('STT_NOTYPE', 0),
            ('STT_OBJECT', 1),
            ('STT_FUNC', 2),
            ('STT_SECTION', 3),
            ('STT_FILE', 4),
        ]
    _fields_ = [
        (st_bind, 'ST_BIND'),
        (st_type, 'ST_TYPE'),
    ]

    def summary(self, **options):
        if self.value is None:
            return '???'
        res = self.bitmap()
        items = ['{:s}={:s}'.format(name + ('' if value is None else '[{:d}]'.format(value.bits())), '???' if value is None else value.summary()) for (_, name), value in map(None, self._fields_, self.value)]
        if items:
            return '({:s},{:d}) : {:s}'.format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res), ' '.join(items))
        return '({:s},{:d})'.format(ptypes.bitmap.hex(res), ptypes.bitmap.size(res))

class ElfXX_Section(pint.enum):
    SHN_LOPROC, SHN_HIPROC = 0xff00, 0xff1f
    SHN_LORESERVE, SHN_HIRESERVE = 0xff00, 0xffff
    _values_ = [
        ('SHN_UNDEF', 0),
        ('SHN_ABS', 0xfff1),
        ('SHN_COMMON', 0xfff2),
    ]

### Section Headers
class Elf32_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf32_Word): pass
    class sh_type(_sh_type, Elf32_Word): pass
    class sh_flags(_sh_flags): pass
    def __sh_unknown(self):
        res = sum(self.new(t).a.size() for t,_ in self._fields_[:-1])
        return dyn.block(max((0,self.blocksize()-res)))
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (Elf32_Addr, 'sh_addr'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(ElfXX_Header), Elf32_Off), 'sh_offset'),
#        (dyn.rpointer(lambda s: dyn.block(int(s.parent['sh_size'])), lambda s: s.getparent(ElfXX_Header), Elf32_Off), 'sh_offset'),
        (_sh_offset(Elf32_Off), 'sh_offset'),
        (Elf32_Word, 'sh_size'),
        (Elf32_Word, 'sh_link'),
        (Elf32_Word, 'sh_info'),
        (Elf32_Word, 'sh_addralign'),
        (Elf32_Word, 'sh_entsize'),
        (__sh_unknown, 'sh_unknown'),
    ]

class Elf64_Shdr(pstruct.type, ElfXX_Shdr):
    class sh_name(_sh_name, Elf64_Word): pass
    class sh_type(_sh_type, Elf64_Word): pass
    class sh_flags(_sh_flags):
        _fields_ = [(32,'SHF_RESERVED2')] + _sh_flags._fields_
    def __sh_unknown(self):
        res = sum(self.new(t).a.size() for t,_ in self._fields_[:-1])
        return dyn.block(max((0,self.blocksize()-res)))
    _fields_ = [
        (sh_name, 'sh_name'),
        (sh_type, 'sh_type'),
        (sh_flags, 'sh_flags'),
        (Elf64_Addr, 'sh_addr'),
        (_sh_offset(Elf64_Off), 'sh_offset'),
        (Elf64_Xword, 'sh_size'),
        (Elf64_Word, 'sh_link'),
        (Elf64_Word, 'sh_info'),
        (Elf64_Xword, 'sh_addralign'),
        (Elf64_Xword, 'sh_entsize'),
        (__sh_unknown, 'sh_unknown'),
    ]

## some types
class Elf32_Section(ElfXX_Section, pint.uint16_t): pass
class Elf64_Section(ElfXX_Section, pint.uint16_t): pass
class Elf32_Sym(pstruct.type):
    class st_name(_st_name, Elf32_Word): pass
    _fields_ = [
        (st_name, 'st_name'),
        (Elf32_Addr, 'st_value'),
        (Elf32_Word, 'st_size'),
        (st_info, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf32_Section, 'st_shndx')
    ]
class Elf64_Sym(pstruct.type):
    class st_name(_st_name, Elf64_Word): pass
    _fields_ = [
        (st_name, 'st_name'),
        (Elf64_Addr, 'st_value'),
        (Elf64_Xword, 'st_size'),
        (st_info, 'st_info'),
        (pint.uint8_t, 'st_other'),
        (Elf64_Section, 'st_shndx')
    ]

class Elf32_Rel(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word , 'r_info'),
    ]
class Elf64_Rel(pstruct.type):
    _fields_ = [
        (Elf64_Addr, 'r_offset'),
        (Elf64_Word , 'r_info'),
        (pint.uint8_t, 'r_type'),
        (pint.uint8_t, 'r_type2'),
        (pint.uint8_t, 'r_type3'),
        (pint.uint8_t, 'r_ssym'),
        (Elf64_Word, 'r_sym'),
    ]

class Elf32_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word, 'r_info'),
        (Elf32_Sword, 'r_addend'),
    ]
class Elf64_Rela(pstruct.type):
    _fields_ = [
        (Elf32_Addr, 'r_offset'),
        (Elf32_Word, 'r_info'),
        (Elf32_Sword, 'r_addend'),
        (pint.uint8_t, 'r_type'),
        (pint.uint8_t, 'r_type2'),
        (pint.uint8_t, 'r_type3'),
        (pint.uint8_t, 'r_ssym'),
        (Elf64_Word, 'r_sym'),
        (Elf64_Sxword, 'r_addend'),
    ]

### each section type
class Type(ptype.definition):
    cache = {}

# data defined by the section header table
@Type.define
class SHT_PROGBITS(ptype.block):
    type = 1

@Type.define
class SHT_SYMTAB(parray.block):
    type = 2
    _object_ = Elf32_Sym

@Type.define
class SHT_STRTAB(parray.block):
    type = 3
    _object_ = pstr.szstring

    def read(self, offset):
        return self.field(offset)
    def summary(self):
        res = (res.str() for res in self)
        res = map('{!r}'.format, res)
        return '{:s} : [ {:s} ]'.format(self.__element__(), ', '.join(res))
    def details(self):
        return '\n'.join(repr(s) for s in self)
    repr = details

@Type.define
class SHT_RELA(parray.block):
    type = 4
    _object_ = Elf32_Rela

@Type.define
class SHT_HASH(pstruct.type):
    type = 5
    _fields_ = [
        (Elf32_Word, 'nbucket'),
        (Elf32_Word, 'nchain'),
        (lambda s: dyn.array(Elf32_Word, s['nbucket'].li.int()), 'bucket'),
        (lambda s: dyn.array(Elf32_Word, s['nchain'].li.int()), 'chain'),
    ]

from . import segment
@Type.define
class SHT_DYNAMIC(segment.PT_DYNAMIC):
    type = 6

@Type.define
class SHT_NOTE(segment.PT_NOTE):
    type = 7

@Type.define
class SHT_NOBITS(ptype.block):
    type = 8

@Type.define
class SHT_REL(parray.block):
    type = 9
    _object_ = Elf32_Rel

@Type.define
class SHT_SHLIB(segment.PT_SHLIB):
    type = 10

@Type.define
class SHT_DYNSYM(parray.block):
    type = 11
    _object_ = Elf32_Sym

# FIXME
@Type.define
class SHT_GROUP(parray.block):
    type = 17
    class GRP_COMDAT(Elf32_Word): pass
    def _object_(self):
        return Elf32_Word if self.value is None or len(self.value) > 0 else Elf32_Word

    _object_ = Elf32_Word

@Type.define
class SHT_ARM_ATTRIBUTES(pstruct.type):
    type = 0x70000003

    class vendortag(ptype.definition):
        cache, unknown = {}, ULEB128
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
            return 'tag={:s} length={:d} attribute={:s}'.format(self['tag'].summary(), self['length'].int(), self['attribute'].__element__())
    class Sections(parray.block):
        def summary(self):
            return '{:s} : [ {:s} ]'.format(self.__element__(), ', '.join(res.summary() for res in self))
    Sections._object_ = Section
    class Attribute(pstruct.type):
        def __value(self):
            tag = self['tag'].li.int()
            return SHT_ARM_ATTRIBUTES.vendortag.get(tag, type=tag)
        _fields_ = [
            (lambda s: SHT_ARM_ATTRIBUTES.Tag, 'tag'),
            (__value, 'value'),
        ]
        def summary(self):
            return '{:s}={:s}'.format(self['tag'].summary(), str(self['value'].get()))
    class Attributes(parray.block):
        def details(self):
            res = []
            for i, n in enumerate(self):
                res.append('[{:x}] {:d} : {:s} = {:s}'.format(n.getoffset(), i, n['tag'].summary(), str(n['value'].get())))
            return '\n'.join(res)
        def summary(self):
            return '{:s} : [ {:s} ]'.format(self.__element__(), ', '.join(res['tag'].summary() for res in self))
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
            return 'length={:d} name={!r} section={:s}'.format(self['length'].int(), self['name'].str(), self['section'].__element__())
    class Vendors(parray.block):
        def summary(self):
            return '{:s} : [ {:s} ]'.format(self.__element__(), ', '.join(res.summary() for res in self))
    Vendors._object_ = Vendor

    def __vendor(self):
        bs = self.blocksize() - self['version'].li.size()
        return dyn.clone(SHT_ARM_ATTRIBUTES.Vendors, blocksize=lambda s,bs=bs: bs)

    _fields_ = [
        (pint.uint8_t, 'version'),
        (__vendor, 'vendor'),
    ]
