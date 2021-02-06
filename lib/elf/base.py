import ptypes
from ptypes import ptype,parray,pstruct,pint,pstr,dyn,pbinary
ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### header markers
class ElfXX_File(ptype.boundary): pass
class ElfXX_Header(ptype.boundary): pass
class ElfXX_Ehdr(ElfXX_Header): pass

### base
class uchar(pint.uint8_t): pass
class ElfXX_BaseOff(ptype.rpointer_t):
    '''Always an offset relative to base of file.'''
    _object_ = ptype.undefined
    def _baseobject_(self):
        return self.getparent(ElfXX_File)

class ElfXX_BaseAddr(ptype.opointer_t):
    '''Always a virtual address relative to base of file.'''
    @classmethod
    def typename(cls):
        return cls.__name__

    def classname(self):
        try: object = self._object_() if callable(self._object_) else self._object_
        except Exception: object = self._object_

        try: type = object.classname() if ptypes.isinstance(object) else object.typename()
        except Exception: pass
        else: return "{:s}<{:s}>".format(self.typename(), type)

        type = object.__name__
        return "{:s}<{:s}>".format(self.typename(), type)

    def _calculate_(self, offset):
        base = self.getparent(ElfXX_File)
        return base.getoffset() + offset

class ElfXX_Off(ElfXX_BaseAddr):
    '''Always an offset that will be converted to an address when its in memory.'''
    _object_ = ptype.undefined
    def _calculate_(self, offset):
        base = self.getparent(ElfXX_File)
        try:
            if isinstance(self.source, ptypes.provider.memorybase):
                p = self.getparent(ElfXX_Ehdr)
                phentries = p['e_phoff'].d.li
                ph = phentries.byoffset(offset)
                return base.getoffset() + ph.getaddressbyoffset(offset)

        except ptypes.error.ItemNotFoundError:
            pass

        return base.getoffset() + offset

class ElfXX_VAddr(ElfXX_BaseAddr):
    '''Always a virtual address that will be converted to an offset when its a file.'''
    _object_ = ptype.undefined
    def _calculate_(self, address):
        base = self.getparent(ElfXX_File)
        try:
            if isinstance(self.source, ptypes.provider.fileobj):
                p = self.getparent(ElfXX_Ehdr)
                phentries = p['e_phoff'].d.li
                ph = phentries.byaddress(address)
                return base.getoffset() + ph.getoffsetbyaddress(address)

        except ptypes.error.ItemNotFoundError:
            pass

        return base.getoffset() + address

class ElfXX_Addr(ptype.pointer_t):
    '''Just a regular address.'''
    _object_ = ptype.undefined

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

### elf32
class Elf32_BaseOff(ElfXX_BaseOff):
    _value_ = pint.uint32_t
class Elf32_BaseAddr(ElfXX_BaseAddr):
    _value_ = pint.uint32_t
class Elf32_Off(ElfXX_Off):
    _value_ = pint.uint32_t
class Elf32_Addr(ElfXX_Addr):
    _value_ = pint.uint32_t
class Elf32_VAddr(ElfXX_VAddr):
    _value_ = pint.uint32_t

class Elf32_Half(pint.uint16_t): pass
class Elf32_Sword(pint.int32_t): pass
class Elf32_Word(pint.uint32_t): pass

### elf64
class Elf64_BaseOff(ElfXX_BaseOff):
    _value_ = pint.uint64_t
class Elf64_BaseAddr(ElfXX_BaseAddr):
    _value_ = pint.uint64_t
class Elf64_Off(ElfXX_Off):
    _value_ = pint.uint64_t
class Elf64_Addr(ElfXX_Addr):
    _value_ = pint.uint64_t
class Elf64_VAddr(ElfXX_VAddr):
    _value_ = pint.uint64_t

class Elf64_Half(Elf32_Half): pass
class Elf64_Word(Elf32_Word): pass
class Elf64_Sword(Elf32_Sword): pass
class Elf64_Xword(pint.uint64_t): pass
class Elf64_Sxword(pint.int64_t): pass

class padstring(pstr.string):
    def set(self, string):
        res, bs = "{!s}".format(string), self.blocksize()
        return super(Elf_Arhdr.padstring, self).set("{:{:d}s}".format(padding, bs))

    def str(self):
        res = super(padstring, self).str()
        return res.rstrip()

class stringinteger(padstring):
    def set(self, integer):
        res, bs = "{!s}".format(integer), self.blocksize()
        return super(padstring, self).set("{: {:d}s}".format(res, bs))

    def int(self):
        res = super(padstring, self).str()
        return int(res.rstrip())

class octalinteger(padstring):
    def set(self, integer):
        res, bs = "{!s}".format(integer), self.blocksize()
        return super(padstring, self).set("{: {:d}s}".format(res, bs))

    def int(self):
        res = super(padstring, self).str()
        return int(res.rstrip(), 8)
