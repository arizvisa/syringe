import ptypes
from ptypes import ptype, pint, pstruct

from . import base, segment, section, dynamic

### header types
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

class EI_CLASS(pint.enum, base.uchar):
    _values_ = [
        ('ELFCLASSNONE', 0),
        ('ELFCLASS32', 1),
        ('ELFCLASS64', 2),
    ]

class EI_DATA(pint.enum, base.uchar):
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

class EI_VERSION(EV_, base.uchar):
    pass

class EI_OSABI(pint.enum, base.uchar):
    _values_ = [
        ('ELFOSABI_SYSV', 0),
        ('ELFOSABI_HPUX', 1),
        ('ELFOSABI_ARM_EABI', 64),
        ('ELFOSABI_STANDALONE', 255),
    ]

class EI_ABIVERSION(base.uchar):
    pass

class EI_PAD(ptype.block):
    length = EI_NIDENT - 9

class E_IDENT(pstruct.type):
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
        res = super(E_IDENT, self).properties()
        if self.initializedQ():
            res['valid'] = self.valid()
        return res

### file type
class File(pstruct.type, base.ElfXX_File):
    def __e_data(self):
        e_ident = self['e_ident'].li

        # Figure out the EI_CLASS to determine the Ehdr size
        ei_class = e_ident['EI_CLASS']
        if ei_class['ELFCLASS32']:
            t = header.Elf32_Ehdr
        elif ei_class['ELFCLASS64']:
            t = header.Elf64_Ehdr
        else:
            raise NotImplementedError(ei_class)

        # Now we can clone it using the byteorder from EI_DATA
        ei_data = e_ident['EI_DATA']
        return ptype.clone(t, recurse=dict(byteorder=ei_data.order()))

    _fields_ = [
        (E_IDENT, 'e_ident'),
        (__e_data, 'e_data'),
    ]

### recursion for python2
from . import header
