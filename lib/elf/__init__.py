import ptypes
import base,header,segment,section,dynamic

### base file type
class File(ptypes.pstruct.type, ptypes.ptype.boundary):
    def __e_data(self):
        type = self['e_ident'].l['EI_CLASS'].num()
        if type == 1:
            return header.Elf32_Ehdr
        elif type == 2:
            return header.Elf64_Ehdr
        raise ValueError(type)

    _fields_ = [
        (base.e_ident, 'e_ident'),
        (__e_data, 'e_data'),
    ]
