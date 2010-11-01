import ptypes
from ptypes import *

ptypes.setbyteorder( ptypes.littleendian )
pbinary.setbyteorder( pbinary.littleendian )

class Elf32_Addr(pint.uint32_t): pass
class Elf32_Half(pint.uint16_t): pass
class Elf32_Off(pint.uint32_t): pass
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass

class Record(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

    class Unknown(dyn.block(0)):
        length=property(fget=lambda s:s.blocksize())
        shortname=lambda s: 'Unknown{%x}<%x>'% (s.length, s.type)
