import ptypes
from ptypes import ptype,parray,pstruct,pint,pstr,dyn,pbinary
ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

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
        else: return "{:s}<{:s}>".format(self.typename(), type)

        try: type = self._object_.typename() if ptype.istype(self._object_) else self._object_().classname()
        except: pass
        else: return "{:s}<{:s}>".format(self.typename(), type)

        type = self._object_.__name__
        return "{:s}<{:s}>".format(self.typename(), type)

class ULEB128(pbinary.terminatedarray):
    class septet(pbinary.struct):
        _fields_ = [
            (1, 'more'),
            (7, 'value'),
        ]
    _object_ = septet
    def isTerminator(self, value):
        return not bool(value['more'])

    def int(self): return self.get()
    def get(self):
        res = 0
        for n in reversed(self):
            res = (res << 7) | n['value']
        return res
    def set(self, value):
        result = []
        while value > 0:
            result.append( self.new(self.septet).set((1, value & (2**7-1))) )
            value //= 2**7
        result[-1].set(more=0)
        self.value[:] = result[:]
        return self

    def summary(self):
        res = self.int()
        return "{:s} : {:d} : ({:#x}, {:d})".format(self.__element__(), res, res, 7*len(self))

class ElfXX_File(ptype.boundary): pass
class ElfXX_Header(ptype.boundary): pass
class ElfXX_Ehdr(ElfXX_Header): pass
class ElfXX_Phdr(ElfXX_Header): pass
class ElfXX_Shdr(ElfXX_Header): pass

### elf32
class Elf32_Addr(pint.uint32_t): pass
class Elf32_Half(pint.uint16_t): pass
class Elf32_Off(ElfXX_Off):
    _value_ = Elf32_Addr
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass

### elf64
class Elf64_Addr(pint.uint64_t): pass
class Elf64_Off(ElfXX_Off):
    _value_ = Elf64_Addr
class Elf64_Half(Elf32_Half): pass
class Elf64_Word(Elf32_Word): pass
class Elf64_Sword(Elf32_Sword): pass
class Elf64_Xword(pint.uint64_t): pass
class Elf64_Sxword(pint.int64_t): pass

### elf general
EI_NIDENT = 16

class EV_(pint.enum):
    _values_ = [
        ('EV_NONE', 0),
        ('EV_CURRENT', 1),
    ]

class EI_MAG(ptype.block):
    length = 4

    def default(self):
        return self.set(b'\x7fELF')

    def valid(self):
        res = self.copy().default()
        return res.serialize() == self.serialize()

    def properties(self):
        res = super(EI_MAG, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

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
    def order(self):
        if self['ELFDATA2LSB']:
            return ptypes.config.byteorder.littleendian
        elif self['ELFDATA2MSB']:
            return ptypes.config.byteorder.bigendian
        return ptypes.config.defaults.integer.order

class EI_VERSION(EV_, uchar):
    pass

class EI_OSABI(pint.enum, uchar):
    _values_ = [
        ('ELFOSABI_SYSV', 0),
        ('ELFOSABI_HPUX', 1),
        ('ELFOSABI_ARM_EABI', 64),
        ('ELFOSABI_STANDALONE', 255),
    ]

class EI_ABIVERSION(uchar):
    pass

class EI_PAD(ptype.block):
    length = EI_NIDENT - 9

class e_ident(pstruct.type):
    _fields_ = [
        (EI_MAG, 'EI_MAG'),
        (EI_CLASS, 'EI_CLASS'),
        (EI_DATA, 'EI_DATA'),
        (EI_VERSION, 'EI_VERSION'),
        (EI_OSABI, 'EI_OSABI'),
        (EI_ABIVERSION, 'EI_ABIVERSION'),
        (EI_PAD, 'EI_PAD'),
    ]

    def valid(self):
        return self.initializedQ() and self['EI_MAG'].valid()
    def properties(self):
        res = super(e_ident, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

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

class e_version(EV_, Elf32_Word):
    pass
