import ptypes
from ptypes import *

ptypes.setbyteorder( ptypes.littleendian )

class Elf32_Addr(pint.uint32_t):
    def summary(self):
        return self.details()
class Elf32_Half(pint.uint16_t): pass
class Elf32_Off(pint.uint32_t):
    def summary(self):
        return self.details()
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass
