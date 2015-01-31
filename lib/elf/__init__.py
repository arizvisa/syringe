import ptypes
from . import base

### base file type
class File(ptypes.pstruct.type, base.ElfXX_File):
    def __e_data(self):
        type = self['e_ident'].li['EI_CLASS'].num()
        if type == 1:
            return header.Elf32_Ehdr
        elif type == 2:
            return header.Elf64_Ehdr
        raise ValueError(type)

    _fields_ = [
        (base.e_ident, 'e_ident'),
        (__e_data, 'e_data'),
    ]

from . import header,segment,section,dynamic
