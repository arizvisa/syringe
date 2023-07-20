import ptypes
from . import dynamic, segment
from . import EI_CLASS
from .base import *
from .header import EM_

class AT_(pint.enum):
    _values_ = [
        ('AT_NULL', 0),                 # end of vector
        ('AT_IGNORE', 1),               # entry should be ignored
        ('AT_EXECFD', 2),               # file descriptor of program
        ('AT_PHDR', 3),                 # program headers for program
        ('AT_PHENT', 4),                # size of program header entry
        ('AT_PHNUM', 5),                # number of program headers
        ('AT_PAGESZ', 6),               # system page size
        ('AT_BASE', 7),                 # base address of interpreter
        ('AT_FLAGS', 8),                # flags
        ('AT_ENTRY', 9),                # entry point of program
        ('AT_NOTELF', 10),              # program is not ELF
        ('AT_UID', 11),                 # real uid
        ('AT_EUID', 12),                # effective uid
        ('AT_GID', 13),                 # real gid
        ('AT_EGID', 14),                # effective gid
        ('AT_PLATFORM', 15),            # string identifying CPU for optimizations
        ('AT_HWCAP', 16),               # arch dependent hints at CPU capabilities
        ('AT_CLKTCK', 17),              # frequency at which times() increments

        ('AT_FPUCW', 18),               # Used FPU control word

        ('AT_DCACHEBSIZE', 19),
        ('AT_ICACHEBSIZE', 20),
        ('AT_UCACHEBSIZE', 21),
        ('AT_IGNOREPPC', 22),           # A special ignored type value for PPC, for glibc compatibility.

        ('AT_SECURE', 23),              # secure mode boolean
        ('AT_BASE_PLATFORM', 24),       # string identifying real platform, may differ from AT_PLATFORM.
        ('AT_RANDOM', 25),              # address of 16 random bytes
        ('AT_HWCAP2', 26),              # extension of AT_HWCAP
        ('AT_RSEQ_FEATURE_SIZE', 27),   # rseq supported feature size
        ('AT_RSEQ_ALIGN', 28),          # rseq allocation alignment

        ('AT_EXECFN', 31),              # filename of program

        ('AT_SYSINFO', 32),
        ('AT_SYSINFO_EHDR', 33),

        ('AT_L1I_CACHESHAPE', 34),
        ('AT_L1D_CACHESHAPE', 35),
        ('AT_L2_CACHESHAPE', 36),
        ('AT_L3_CACHESHAPE', 37),

        ('AT_L1I_CACHESIZE', 40),
        ('AT_L1I_CACHEGEOMETRY', 41),
        ('AT_L1D_CACHESIZE', 42),
        ('AT_L1D_CACHEGEOMETRY', 43),
        ('AT_L2_CACHESIZE', 44),
        ('AT_L2_CACHEGEOMETRY', 45),
        ('AT_L3_CACHESIZE', 46),
        ('AT_L3_CACHEGEOMETRY', 47),

        ('AT_ADI_BLKSZ', 48),
        ('AT_ADI_NBITS', 49),
        ('AT_ADI_UEONADI', 50),

        ('AT_MINSIGSTKSZ', 51),         # minimal stack size for signal delivery
    ]

### AT_*
class AT_PHDR(segment.ElfXX_Phdr):
    # FIXME
    pass

class AT_ENTRY(void_star):
    type = 9

class AT_PLATFORM(void_star):
    type, _object_ = 15, pstr.szstring

class AT_BASE_PLATFORM(void_star):
    type, _object_ = 24, pstr.szstring

class AT_RANDOM(void_star):
    type, _object_ = 25, dyn.block(0x10)

class AT_EXECFN(void_star):
    type, _object_ = 31, pstr.szstring

class AT_SYSINFO(void):
    type = 32

class AT_SYSINFO_EHDR(void):
    type = 33   # FIXME: we can totally define this page per-architecture

### AT_FLAGS
class AT_FLAGS(ptype.definition):
    cache = {}  # unused

### AT_HWCAP
class AT_HWCAP(ptype.definition):
    cache = {}

@AT_FLAGS.define(type=EM_.byname('EM_386'))
class AT_HWCAP_386(pbinary.flags):
    _fields_ = []

@AT_FLAGS.define(type=EM_.byname('EM_LOONGARCH'))
class HWCAP_LOONGARCH(pbinary.flags):
    _fields_ = [
        (1, 'PTW'),
        (1, 'LBT_MIPS'),
        (1, 'LBT_ARM'),
        (1, 'LBT_X86'),
        (1, 'LVZ'),
        (1, 'CRYPTO'),
        (1, 'COMPLEX'),
        (1, 'CRC32'),
        (1, 'LASX'),
        (1, 'LSX'),
        (1, 'FPU'),
        (1, 'UAL'),
        (1, 'LAM'),
        (1, 'CPUCFG'),
    ]

@AT_FLAGS.define(type=EM_.byname('EM_ARM'))
class COMPAT_HWCAP_ARM64(pbinary.flags):
    _fields_ = [
        (1, 'I8MM'),
        (1, 'ASIMDBF16'),
        (1, 'ASIMDFHM'),
        (1, 'ASIMDDP'),
        (1, 'ASIMDHP'),
        (1, 'FPHP'),
        (1, 'EVTSTRM'),
        (1, 'LPAE'),
        (1, 'VFPD32'),
        (1, 'IDIV'),
        (1, 'IDIVT'),
        (1, 'IDIVA'),
        (1, 'VFPv4'),
        (1, 'TLS'),
        (1, 'VFPV3D16'),
        (1, 'VFPv3'),
        (1, 'NEON'),
        (1, 'THUMBEE'),
        (1, 'CRUNCH'),
        (1, 'IWMMXT'),
        (1, 'JAVA'),
        (1, 'EDSP'),
        (1, 'VFP'),
        (1, 'FPA'),
        (1, 'FAST_MULT'),
        (1, '26BIT'),
        (1, 'THUMB'),
        (1, 'HALF'),
        (1, 'SWP'),
    ]

@AT_FLAGS.define(type=EM_.byname('EM_ARM'))
class HWCAP_ARM(pbinary.flags):
    _fields_ = [
        (1, 'I8MM'),
        (1, 'ASIMDBF16'),
        (1, 'ASIMDFHM'),
        (1, 'ASIMDDP'),
        (1, 'ASIMDHP'),
        (1, 'FPHP'),
        (1, 'EVTSTRM'),
        (1, 'LPAE'),
        (1, 'IDIV'),
        (1, 'VFPD32'),
        (1, 'IDIVT'),
        (1, 'IDIVA'),
        (1, 'VFPv4'),
        (1, 'TLS'),
        (1, 'VFPv3D16'),
        (1, 'VFPv3'),
        (1, 'NEON'),
        (1, 'THUMBEE'),
        (1, 'CRUNCH'),
        (1, 'IWMMXT'),
        (1, 'JAVA'),
        (1, 'EDSP'),
        (1, 'VFP'),
        (1, 'FPA'),
        (1, 'FAST_MULT'),
        (1, '26BIT'),
        (1, 'THUMB'),
        (1, 'HALF'),
        (1, 'SWP'),
    ]

@AT_FLAGS.define(type=EM_.byname('EM_MIPS'))
class HWCAP_MIPS(pbinary.flags):
    _fields_ = [
        (1, 'MIPS_SMARTMIPS'),
        (1, 'MIPS_R6'),
        (1, 'MIPS_MSA'),
        (1, 'MIPS_MIPS3D'),
        (1, 'MIPS_MIPS16E2'),
        (1, 'MIPS_MIPS16'),
        (1, 'MIPS_MDMX'),
        (1, 'MIPS_DSP3'),
        (1, 'MIPS_DSP2'),
        (1, 'MIPS_DSP'),
        (1, 'MIPS_CRC32'),
        (1, 'LOONGSON_CPUCFG'),
        (1, 'LOONGSON_EXT2'),
        (1, 'LOONGSON_EXT'),
        (1, 'LOONGSON_MMI'),
    ]

### AT_FPUCW
class AT_FPUCW(ptype.definition):
    cache = {}

@AT_FLAGS.define(type=EM_.byname('EM_386'))
class AT_FPUCW_386(pbinary.flags):
    type, _fields_ = 19, []

### AT_HWCAP2
class AT_HWCAP2(ptype.definition):
    cache = {}

@AT_FLAGS.define(type=EM_.byname('EM_386'))
class HWCAP2_386(pbinary.flags):
    type, _fields_ = 26, [
        (1, 'RING3MWAIT'),
        (1, 'FSGSBASE'),
    ]

@AT_FLAGS.define(type=EM_.byname('EM_ARM'))
class HWCAP2_ARM(pbinary.flags):
    _fields_ = [
        (1, 'HWCAP2_SSBS'),
        (1, 'HWCAP2_SB'),
        (1, 'HWCAP2_CRC32'),
        (1, 'HWCAP2_SHA2'),
        (1, 'HWCAP2_SHA1'),
        (1, 'HWCAP2_PMULL'),
        (1, 'HWCAP2_AES'),
    ]
    
### Auxiliary values
class ElfXX_auxv_t(pstruct.type):
    pass

class Elf32_auxv_t(ElfXX_auxv_t):
    class _a_type(AT_, Elf32_Word): pass
    _fields_ = [
        (_a_type, 'a_type'),
        (Elf32_Word, 'a_val'),
        #(Elf32_Addr, 'a_un'),
    ]

class Elf64_auxv_t(ElfXX_auxv_t):
    class _a_type(AT_, Elf64_Xword): pass
    _fields_ = [
        (_a_type, 'a_type'),
        (Elf64_Xword, 'a_val'),
        #(Elf64_Addr, 'a_un'),
    ]

class Arguments(pstruct.type):
    class _argv(parray.terminated):
        _object_ = dyn.clone(void_star, _object_=pstr.szstring)
        def isTerminator(self, pointer):
            return not pointer.int()
    _fields_ = [
        (int, 'argc'),
        (_argv, 'argv'),
    ]

class Environment(parray.terminated):
    _object_ = dyn.clone(void_star, _object_=pstr.szstring)
    def isTerminator(self, pointer):
        return not pointer.int()

class Auxiliary(parray.terminated):
    _object_ = Elf32_auxv_t
    def isTerminator(self, aux):
        return aux['a_type']['AT_NULL']

class Stack(pstruct.type):
    _fields_ = [
        (Arguments, 'Arguments'),
        (Environment, 'Environment'),
        (Auxiliary, 'Auxiliary'),
        (dyn.padding(0x10), 'padding'),
        (pstr.szstring, 'argument ASCIIZ'),
        (pstr.szstring, 'environment ASCIIZ'),
        (unsigned_long, 'end marker'),
    ]
