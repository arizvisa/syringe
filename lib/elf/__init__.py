import ptypes
from ptypes import dyn

from . import base

### base file type
class File(ptypes.pstruct.type, base.ElfXX_File):
    def __e_data(self):
        e_ident = self['e_ident'].li
        type = e_ident['EI_CLASS'].int()
        order = e_ident['EI_DATA'].order()
        if type == 1:
            return dyn.clone(header.Elf32_Ehdr, recurse=dict(byteorder=order))
        elif type == 2:
            return dyn.clone(header.Elf64_Ehdr, recurse=dict(byteorder=order))
        raise ValueError(type)

    _fields_ = [
        (base.e_ident, 'e_ident'),
        (__e_data, 'e_data'),
    ]

from . import header,segment,section,dynamic
