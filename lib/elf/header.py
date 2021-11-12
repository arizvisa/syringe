import ptypes, time, datetime
from . import EV_, E_IDENT, section, segment
from .base import *

class ET_(pint.enum, Elf32_Half):
    _values_ = [
        ('NONE', 0),
        ('REL', 1),
        ('EXEC', 2),
        ('DYN', 3),
        ('CORE', 4),
        # ET_LOOS(0xfe00) - ET_HIOS(0xfeff)
        # ET_LOPROC(0xff00) - ET_HIPROC(0xffff)
    ]

class EM_(pint.enum, Elf32_Half):
    _values_ = [
        ('EM_NONE', 0),
        ('EM_M32', 1),
        ('EM_SPARC', 2),
        ('EM_386', 3),
        ('EM_68K', 4),
        ('EM_88K', 5),
        ('EM_IAMCU', 6),
        ('EM_860', 7),
        ('EM_MIPS', 8),
        ('EM_S370', 9),
        ('EM_MIPS_RS4_BE', 10),
#       ('RESERVED', 11-14),
        ('EM_PARISC', 15),
#       ('RESERVED', 16),
        ('EM_VPP500', 17),
        ('EM_SPARC32PLUS', 18),
        ('EM_960', 19),
        ('EM_PPC', 20),
        ('EM_PPC64', 21),
        ('EM_S390', 22),
        ('EM_SPU', 23),
#       ('RESERVED', 24-35),
        ('EM_V800', 36),
        ('EM_FR20', 37),
        ('EM_RH32', 38),
        ('EM_RCE', 39),
        ('EM_ARM', 40),
        ('EM_ALPHA', 41),
        ('EM_SH', 42),
        ('EM_SPARCV9', 43),
        ('EM_TRICORE', 44),
        ('EM_ARC', 45),
        ('EM_H8_300', 46),
        ('EM_H8_300H', 47),
        ('EM_H8S', 48),
        ('EM_H8_500', 49),
        ('EM_IA_64', 50),
        ('EM_MIPS_X', 51),
        ('EM_COLDFIRE', 52),
        ('EM_68HC12', 53),
        ('EM_MMA', 54),
        ('EM_PCP', 55),
        ('EM_NCPU', 56),
        ('EM_NDR1', 57),
        ('EM_STARCORE', 58),
        ('EM_ME16', 59),
        ('EM_ST100', 60),
        ('EM_TINYJ', 61),
        ('EM_X86_64', 62),
        ('EM_PDSP', 63),
        ('EM_PDP10', 64),
        ('EM_PDP11', 65),
        ('EM_FX66', 66),
        ('EM_ST9PLUS', 67),
        ('EM_ST7', 68),
        ('EM_68HC16', 69),
        ('EM_68HC11', 70),
        ('EM_68HC08', 71),
        ('EM_68HC05', 72),
        ('EM_SVX', 73),
        ('EM_ST19', 74),
        ('EM_VAX', 75),
        ('EM_CRIS', 76),
        ('EM_JAVELIN', 77),
        ('EM_FIREPATH', 78),
        ('EM_ZSP', 79),
        ('EM_MMIX', 80),
        ('EM_HUANY', 81),
        ('EM_PRISM', 82),
        ('EM_AVR', 83),
        ('EM_FR30', 84),
        ('EM_D10V', 85),
        ('EM_D30V', 86),
        ('EM_V850', 87),
        ('EM_M32R', 88),
        ('EM_MN10300', 89),
        ('EM_MN10200', 90),
        ('EM_PJ', 91),
        ('EM_OPENRISC', 92),
        ('EM_ARC_COMPACT', 93),
        ('EM_XTENSA', 94),
        ('EM_VIDEOCORE', 95),
        ('EM_TMM_GPP', 96),
        ('EM_NS32K', 97),
        ('EM_TPC', 98),
        ('EM_SNP1K', 99),
        ('EM_ST200', 100),
        ('EM_IP2K', 101),
        ('EM_MAX', 102),
        ('EM_CR', 103),
        ('EM_F2MC16', 104),
        ('EM_MSP430', 105),
        ('EM_BLACKFIN', 106),
        ('EM_SE_C33', 107),
        ('EM_SEP', 108),
        ('EM_ARCA', 109),
        ('EM_UNICORE', 110),
        ('EM_EXCESS', 111),
        ('EM_DXP', 112),
        ('EM_ALTERA_NIOS2', 113),
        ('EM_CRX', 114),
        ('EM_XGATE', 115),
        ('EM_C166', 116),
        ('EM_M16C', 117),
        ('EM_DSPIC30F', 118),
        ('EM_CE', 119),
        ('EM_M32C', 120),
#        ('RESERVED', 121-130),
        ('EM_TSK3000', 131),
        ('EM_RS08', 132),
        ('EM_SHARC', 133),
        ('EM_ECOG2', 134),
        ('EM_SCORE7', 135),
        ('EM_DSP24', 136),
        ('EM_VIDEOCORE3', 137),
        ('EM_LATTICEMICO32', 138),
        ('EM_SE_C17', 139),
        ('EM_TI_C6000', 140),
        ('EM_TI_C2000', 141),
        ('EM_TI_C5500', 142),
        ('EM_TI_ARP32', 143),
        ('EM_TI_PRU', 144),
#        ('RESERVED', 145-159),
        ('EM_MMDSP_PLUS', 160),
        ('EM_CYPRESS_M8C', 161),
        ('EM_R32C', 162),
        ('EM_TRIMEDIA', 163),
        ('EM_QDSP6', 164),
        ('EM_8051', 165),
        ('EM_STXP7X', 166),
        ('EM_NDS32', 167),
        ('EM_ECOG1', 168),
        ('EM_ECOG1X', 168),
        ('EM_MAXQ30', 169),
        ('EM_XIMO16', 170),
        ('EM_MANIK', 171),
        ('EM_CRAYNV2', 172),
        ('EM_RX', 173),
        ('EM_METAG', 174),
        ('EM_MCST_ELBRUS', 175),
        ('EM_ECOG16', 176),
        ('EM_CR16', 177),
        ('EM_ETPU', 178),
        ('EM_SLE9X', 179),
        ('EM_L10M', 180),
        ('EM_K10M', 181),
#        ('RESERVED', 182),
        ('EM_AARCH64', 183),
#        ('RESERVED', 184),
        ('EM_AVR32', 185),
        ('EM_STM8', 186),
        ('EM_TILE64', 187),
        ('EM_TILEPRO', 188),
        ('EM_MICROBLAZE', 189),
        ('EM_CUDA', 190),
        ('EM_TILEGX', 191),
        ('EM_CLOUDSHIELD', 192),
        ('EM_COREA_1ST', 193),
        ('EM_COREA_2ND', 194),
        ('EM_ARC_COMPACT2', 195),
        ('EM_OPEN8', 196),
        ('EM_RL78', 197),
        ('EM_VIDEOCORE5', 198),
        ('EM_78KOR', 199),
        ('EM_56800EX', 200),
        ('EM_BA1', 201),
        ('EM_BA2', 202),
        ('EM_XCORE', 203),
        ('EM_MCHP_PIC', 204),
        ('EM_INTEL205', 205),
        ('EM_INTEL206', 206),
        ('EM_INTEL207', 207),
        ('EM_INTEL208', 208),
        ('EM_INTEL209', 209),
        ('EM_KM32', 210),
        ('EM_KMX32', 211),
        ('EM_KMX16', 212),
        ('EM_KMX8', 213),
        ('EM_KVARC', 214),
        ('EM_CDP', 215),
        ('EM_COGE', 216),
        ('EM_COOL', 217),
        ('EM_NORC', 218),
        ('EM_CSR_KALIMBA', 219),
        ('EM_Z80', 220),
        ('EM_VISIUM', 221),
        ('EM_FT32', 222),
        ('EM_MOXIE', 223),
        ('EM_AMDGPU', 224),
#        ('RESERVED', 225-242),
        ('EM_RISCV', 243),
    ]

class E_VERSION(EV_, Elf32_Word):
    pass

class E_FLAGS(ptype.definition):
    cache = {}
    default = Elf32_Word

@E_FLAGS.define(type=EM_.byname('EM_SPARC'))
@E_FLAGS.define(type=EM_.byname('EM_SPARC32PLUS'))
@E_FLAGS.define(type=EM_.byname('EM_SPARCV9'))
class E_FLAGS_SPARC(pbinary.flags):
    VENDOR_MASK = 0x00ffff00
    class EF_SPARCV9_MM(pbinary.enum):
        length, _values_ = 2, [
            ('EF_SPARCV9_TSO', 0),
            ('EF_SPARCV9_PSO', 1),
            ('EF_SPARCV9_RMO', 2),
        ]
    class EF_SPARC_EXT_MASK(pbinary.flags):
        _fields_ = [
            (12, 'EF_SPARC_EXT'),
            (1, 'EF_SPARC_SUN_US3'),
            (1, 'EF_SPARC_HAL_R1'),
            (1, 'EF_SPARC_SUN_US1'),
            (1, 'EF_SPARC_32PLUS'),
        ]

    _fields_ = [
        (8, 'EF_SPARC_NONE'),
        (EF_SPARC_EXT_MASK, 'EF_SPARC_EXT_MASK'),
        (6, 'EF_SPARC_UNKNOWN'),
        (EF_SPARCV9_MM, 'EF_SPARCV9_MM'),
    ]

@E_FLAGS.define
class E_FLAGS_ARM(pbinary.flags):
    type = EM_.byname('EM_ARM')
    ABI_MASK = 0xff000000
    GCC_MASK = 0x00400FFF
    class EF_ARM_GCC_MASK(pbinary.struct):
        _fields_ = [
            (1, 'EF_ARM_ABI_UNKNOWN'),
            (1, 'EF_ARM_ABI_FLOAT_HARD'),
            (1, 'EF_ARM_ABI_FLOAT_SOFT'),
            (9, 'EF_ARM_GCC_UNKNOWN'),
        ]
    _fields_ = [
        (8, 'EF_ARM_ABI'),
        (1, 'EF_ARM_BE8'),
        (1, 'EF_ARM_GCC_LEGACY'),
        (2, 'EF_ARM_GCC_ALIGN'),
        (8, 'EF_ARM_UNKNOWN'),
        (EF_ARM_GCC_MASK, 'EF_ARM_GCC_MASK'),
    ]

@E_FLAGS.define
class E_FLAGS_MIPS(pbinary.flags):
    type = EM_.byname('EM_MIPS')
    class EF_MIPS_ARCH_(pbinary.enum):
        length, _values_ = 4, [
            ('EF_MIPS_ARCH_1', 0),
            ('EF_MIPS_ARCH_2', 1),
            ('EF_MIPS_ARCH_3', 2),
            ('EF_MIPS_ARCH_4', 3),
            ('EF_MIPS_ARCH_5', 4),
            ('EF_MIPS_ARCH_32', 5),
            ('EF_MIPS_ARCH_64', 6),
            ('EF_MIPS_ARCH_32R2', 7),
            ('EF_MIPS_ARCH_64R2', 8),
        ]
    class EF_MIPS_ARCH_ASE_(pbinary.enum):
        length, _values_ = 4, [
            ('EF_MIPS_ARCH_ASE_MDMX', 8),
            ('EF_MIPS_ARCH_ASE_M16', 4),
            ('EF_MIPS_ARCH_ASE_MICROMIPS', 2),
        ]
    class E_MIPS_ABI_(pbinary.enum):
        length, _values_ = 4, [
            ('E_MIPS_ABI_O32', 1),
            ('E_MIPS_ABI_O64', 2),
            ('E_MIPS_ABI_EABI32', 3),
            ('E_MIPS_ABI_EABI64', 4),
        ]
    _fields_ = [
        (EF_MIPS_ARCH_, 'ARCH'),
        (EF_MIPS_ARCH_ASE_, 'ASE'),
        (8, 'EF_MIPS_ARCH_UNUSED'),
        (E_MIPS_ABI_, 'ABI'),
        (1, 'EF_MIPS_ARCH_RESERVED'),
        (1, 'E_MIPS_NAN2008'),
        (1, 'E_MIPS_FP64'),
        (1, 'EF_MIPS_32BITMODE'),
        (1, 'EF_MIPS_OPTIONS_FIRST'),
        (1, 'EF_MIPS_ABI_ON32'),
        (1, 'EF_MIPS_ABI2'),
        (1, 'EF_MIPS_64BIT_WHIRL'),
        (1, 'EF_MIPS_XGOT'),
        (1, 'EF_MIPS_CPIC'),
        (1, 'EF_MIPS_PIC'),
        (1, 'EF_MIPS_NOREORDER'),
    ]

class PN_(pint.enum):
    _values_ = [
        ('XNUM', 0xffff),
    ]

class XhdrEntries(parray.type):
    def iterate(self):
        for index, item in self.enumerate():
            yield item
        return

    def enumerate(self):
        for index, item in enumerate(self):
            yield index, item
        return

    def sorted(self, fld):
        items = {}
        for index, item in enumerate(self):
            offset = item[fld].int()
            items[offset] = (index, item)

        # Now that we've aggregated all of the entries, sort everything
        # and yield them back to the user.
        for offset in sorted(items):
            index, item = items[offset]
            yield index, item
        return

class ShdrEntries(XhdrEntries):
    def byoffset(self, ofs):
        iterable = (item for item in self if item.containsoffset(ofs))
        try:
            result = next(iterable)
        except StopIteration:
            raise ptypes.error.ItemNotFoundError(self, 'ShdrEntries.byoffset', "Unable to locate Shdr with the specified offset ({:#x})".format(ofs))
        return result

    def byaddress(self, va):
        iterable = (item for item in self if item.containsaddress(va))
        try:
            result = next(iterable)
        except StopIteration:
            raise ptypes.error.ItemNotFoundError(self, 'ShdrEntries.byoffset', "Unable to locate Shdr with the specified virtual address ({:#x})".format(va))
        return result

    def sorted(self):
        for index, item in super(ShdrEntries, self).sorted('sh_offset'):
            yield index, item
        return

class PhdrEntries(XhdrEntries):
    def byoffset(self, ofs):
        if isinstance(self.source, ptypes.provider.memorybase):
            iterable = (item for item in self if item.loadableQ() and item.containsoffset(ofs))
        else:
            iterable = (item for item in self if item.containsoffset(ofs))

        # Now that we have an iterable, return the first result we find
        try:
            result = next(iterable)
        except StopIteration:
            raise ptypes.error.ItemNotFoundError(self, 'PhdrEntries.byoffset', "Unable to locate Phdr with the specified offset ({:#x})".format(ofs))
        return result

    def byaddress(self, va):
        iterable = (item for item in self if item.loadableQ() and item.containsaddress(va))

        # Now that we have an iterable, return the first result we find.
        try:
            result = next(iterable)

        # If our iterator has no items, then we weren't able to find a match
        # and we'll need to raise an exception.
        except StopIteration:
            raise ptypes.error.ItemNotFoundError(self, 'PhdrEntries.byoffset', "Unable to locate Phdr with the specified virtual address ({:#x})".format(va))
        return result

    def enumerate(self):
        for index, item in super(PhdrEntries, self).enumerate():

            # If our source is memory-backed, then we'll want to filter our
            # items by whether they're loaded or not. So, we'll just check the
            # phdr flags in order to figure that out.
            if isinstance(self.source, ptypes.provider.memorybase):
                flags = item['p_type']
                if any(flags[fl] for fl in ['LOAD', 'DYNAMIC']):
                    yield index, item
                continue

            # Otherwise we'll just yield everything because it's in the file.
            yield index, item
        return

    def sorted(self):
        fld = 'p_vaddr' if isinstance(self.source, ptypes.provider.memorybase) else 'p_offset'
        for index, item in super(PhdrEntries, self).sorted(fld):

            # If we are actually dealing with a source that's backed by
            # actual memory, then only yield a phdr if it's actually loaded.
            if isinstance(item.source, ptypes.provider.memory):
                if item.loadableQ():
                    yield index, item
                continue

            # Otherwise, we can just yield everything without having to filter.
            yield index, item
        return

### 32-bit
class Elf32_Ehdr(pstruct.type, ElfXX_Ehdr):
    def _ent_array(self, entries, type, size, length):
        t = dyn.clone(type, blocksize=lambda self, cb=size.int(): cb)
        return dyn.clone(entries, _object_=t, length=length.int())
    def _phent_array(self, type, size, length):
        return self._ent_array(PhdrEntries, type, size, length)
    def _shent_array(self, type, size, length):
        return self._ent_array(ShdrEntries, type, size, length)

    def __e_flags(self):
        res = self['e_machine'].li.int()
        return E_FLAGS.withdefault(res, type=res)

    class e_phnum(PN_, Elf32_Half): pass

    def __padding(self):
        res = self['e_ehsize'].li
        cb = sum(self[fld].li.size() for fld in self.keys()[:-1]) + E_IDENT().a.blocksize()
        return dyn.block(res.int() - cb)

    _fields_ = [
        (ET_, 'e_type'),
        (EM_, 'e_machine'),
        (E_VERSION, 'e_version'),
        (Elf32_VAddr, 'e_entry'),
        (lambda self: dyn.clone(Elf32_BaseOff, _object_=lambda s: self._phent_array(segment.Elf32_Phdr, self['e_phentsize'].li, self['e_phnum'].li)), 'e_phoff'),
        (lambda self: dyn.clone(Elf32_Off, _object_=lambda s: self._shent_array(section.Elf32_Shdr, self['e_shentsize'].li, self['e_shnum'].li)), 'e_shoff'),
        (__e_flags, 'e_flags'),
        (Elf32_Half, 'e_ehsize'),
        (Elf32_Half, 'e_phentsize'),
        (e_phnum, 'e_phnum'),
        (Elf32_Half, 'e_shentsize'),
        (Elf32_Half, 'e_shnum'),
        (Elf32_Half, 'e_shstrndx'),
        (__padding, 'padding'),
    ]

    def stringtable(self):
        res, index = self['e_shoff'].d.li, self['e_shstrndx'].int()
        if index < len(res):
            return res[index]['sh_offset'].d.li
        raise ptypes.error.ItemNotFoundError(self, 'stringtable')

### 64-bit
class Elf64_Ehdr(pstruct.type, ElfXX_Ehdr):
    def _ent_array(self, entries, type, size, length):
        t = dyn.clone(type, blocksize=lambda self, cb=size.int(): cb)
        return dyn.clone(entries, _object_=t, length=length.int())
    def _phent_array(self, type, size, length):
        return self._ent_array(PhdrEntries, type, size, length)
    def _shent_array(self, type, size, length):
        return self._ent_array(ShdrEntries, type, size, length)

    def __e_flags(self):
        res = self['e_machine'].li.int()
        return E_FLAGS.withdefault(res, type=res)

    class e_phnum(PN_, Elf64_Half): pass

    def __padding(self):
        res = self['e_ehsize'].li
        cb = sum(self[fld].li.size() for fld in self.keys()[:-1]) + E_IDENT().a.blocksize()
        return dyn.block(res.int() - cb)

    _fields_ = [
        (ET_, 'e_type'),
        (EM_, 'e_machine'),
        (E_VERSION, 'e_version'),
        (Elf64_VAddr, 'e_entry'),
        (lambda self: dyn.clone(Elf64_BaseOff, _object_=lambda s: self._phent_array(segment.Elf64_Phdr, self['e_phentsize'].li, self['e_phnum'].li)), 'e_phoff'),
        (lambda self: dyn.clone(Elf64_Off, _object_=lambda s: self._shent_array(section.Elf64_Shdr, self['e_shentsize'].li, self['e_shnum'].li)), 'e_shoff'),
        (__e_flags, 'e_flags'),
        (Elf64_Half, 'e_ehsize'),
        (Elf64_Half, 'e_phentsize'),
        (e_phnum, 'e_phnum'),
        (Elf64_Half, 'e_shentsize'),
        (Elf64_Half, 'e_shnum'),
        (Elf64_Half, 'e_shstrndx'),
        (__padding, 'padding'),
    ]

    def stringtable(self):
        res, index = self['e_shoff'].d.li, self['e_shstrndx'].int()
        if index < len(res):
            return res[index]['sh_offset'].d.li
        raise ptypes.error.ItemNotFoundError(self, 'stringtable')

### Archives
class Elf_Armag(pstr.string):
    length = 8
    def default(self, **kwargs):
        archiveQ = next((kwargs.get(item) for item in kwargs if item in {'thin', 'archive'}), True)
        if archiveQ:
            return self.set('!<arch>\012')
        return self.set('!<thin>\012')
    def valid(self):
        res = self.str()
        if res == self.copy().default(archive=True).str():
            return True
        elif res == self.copy().default(thin=True).str():
            return True
        return False
    def properties(self):
        res = super(Elf_Armag, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

class Elf_Arhdr(pstruct.type):
    class time_t(stringinteger):
        length = 12
        def datetime(self):
            res = self.int()
            return datetime.datetime.fromtimestamp(res, datetime.timezone.utc)
        def gmtime(self):
            res = self.int()
            return time.gmtime(res)
        def details(self):
            tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone)))
            try:
                res = self.datetime().astimezone(tzinfo)
            except (ValueError, OverflowError):
                return super(Elf_Arhdr.time_t, self).details() + '\n'
            return "({:d}) {!s}".format(self.int(), res.isoformat())
        repr = details
        def summary(self):
            tzinfo = datetime.timezone(datetime.timedelta(seconds=-(time.altzone if time.daylight else time.timezone)))
            try:
                res = self.datetime().astimezone(tzinfo)
            except (ValueError, OverflowError):
                return super(Elf_Arhdr.time_t, self).summary()
            return "({:d}) {!s}".format(self.int(), res.isoformat())

    class uid_t(stringinteger): length = 6
    class gid_t(stringinteger): length = 6
    class mode_t(octalinteger): length = 8
    class size_t(stringinteger): length = 10

    class _fmag(pstr.string):
        length = 2
        def default(self):
            return self.set('`\012')

    _fields_ = [
        (dyn.clone(padstring, length=0x10), 'ar_name'),
        (time_t, 'ar_date'),
        (uid_t, 'ar_uid'),
        (gid_t, 'ar_gid'),
        (mode_t, 'ar_mode'),
        (size_t, 'ar_size'),
        (_fmag, 'ar_fmag'),
    ]

    def summary(self):
        try:
            name, ts = self['ar_name'], self['ar_date'].summary()
            mode, size, uid, gid = (self[fld].int() for fld in ['ar_mode', 'ar_size', 'ar_uid', 'ar_gid'])
            return "ar_name=\"{!s}\" ar_mode={:o} ar_size={:+d} ar_date={:s} ar_uid/ar_gid={:d}/{:d}".format(name.str(), mode, size, ts.isoformat(), uid, gid)
        except ValueError:
            pass
        return super(Elf_Arhdr, self).summary()

class Elf_Arnames(pstruct.type):
    class _an_pointer(parray.type):
        _object_ = pint.bigendian(pint.uint32_t)

        def summary(self):
            iterable = (item.int() for item in self)
            return "[{:s}]".format(', '.join(map("{:#x}".format, iterable)))

    def __an_pointer(self):
        res = self['an_count'].li
        return dyn.clone(self._an_pointer, length=res.int())

    class _an_table(parray.type):
        _object_ = pstr.szstring
        def summary(self):
            iterable = (item.str() for item in self)
            return "[{:s}]".format(', '.join(iterable))

    def __an_table(self):
        res = self['an_count'].li
        return dyn.clone(self._an_table, length=res.int())

    _fields_ = [
        (pint.bigendian(pint.uint32_t), 'an_count'),
        (__an_pointer, 'an_pointer'),
        (__an_table, 'an_table'),
    ]

class Elf_Armember(pstruct.type):
    def __am_data(self):
        res = self['am_hdr'].li
        if res['ar_name'].str() == '//':
            return dyn.clone(pstr.string, length=res['ar_size'].int())
        elif res['ar_name'].str() == '/':
            return Elf_Arnames
        return dyn.block(res['ar_size'].int())

    _fields_ = [
        (Elf_Arhdr, 'am_hdr'),
        (__am_data, 'am_data'),
    ]
