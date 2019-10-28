import ptypes
from ptypes import dyn

from . import base

### base file type
class File(ptypes.pstruct.type, base.ElfXX_File):
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
        return dyn.clone(t, recurse=dict(byteorder=ei_data.order()))

    _fields_ = [
        (base.e_ident, 'e_ident'),
        (__e_data, 'e_data'),
    ]

from . import header,segment,section,dynamic
