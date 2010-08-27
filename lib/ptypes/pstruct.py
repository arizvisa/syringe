'''base structure element'''
import ptype

class __pstruct_generic(ptype.pcontainer):
    __fastindex = dict  # our on-demand index lookup for .value

    def getindex(self, name):
        try:
            return self.__fastindex[name]
        except TypeError:
            self.__fastindex = {}
        except KeyError:
            pass

        res = self.keys()
        for i in range( len(res) ):
            if name == res[i]:
                self.__fastindex[name] = i
                return i

        raise KeyError(name)

    def keys(self):
        return [name for type,name in self._fields_]

    def values(self):
        return list(self.value)

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def __getitem__(self, name):
        index = self.getindex(name)
        return self.value[index]

    def __setitem__(self, name, value):
        index = self.getindex(name)
        self.value[index] = value

class type(__pstruct_generic):
    '''
    A pcontainer for managing structured/named data

    Settable properties:
        _fields_:array( tuple( ptype, name ), ... )<w>
            This contains which elements the structure is composed of
    '''
    _fields_ = None     # list of (type,name) tuples

    initialized = property(fget=lambda s: super(type, s).initialized and len(s.value) == len(s._fields_))

    def size(self):
        return reduce(lambda x,y: x + y.size(), self.value, 0)

    def load(self):
        self.value = []

        # create each element
        ofs = self.getoffset()
        for t,name in self._fields_:
            n = self.newelement(t, name, ofs)
            self.value.append(n)
            if ptype.ispcontainer(t) or ptype.isresolveable(t):
                n.load()
            ofs += n.size()
        return super(type, self).load()

    def deserialize(self, source):
        source = iter(source)
        self.value = []
        ofs = self.getoffset()
        for t,name in self._fields_:
            n = self.addelement_stream(source, t, name, ofs)
            ofs += n.size()
        return super(type, self).deserialize(None)

    def __repr__uninitialized(self):
        result = []
        startofs = self.getoffset()
        ofs = '[%x]'% startofs
        for t,name in self._fields_:
            result.append(' '.join([ofs, repr(t), name, '???']))
            ofs = '[%x+??]'% startofs

        if len(result) > 0:
            return '\n'.join(result)
        return '[]'

    def __repr__initialized(self):
        row = lambda name,value: ' '.join(['[%x]'% self.getoffset(name), value.name(), name, repr(value.serialize())])
        return '\n'.join([row(name,value) for (t,name),value in zip(self._fields_, self.value)])

    def __repr__(self):
        if not self.initialized:
            return self.name() + '\n' + self.__repr__uninitialized()
        return self.name() + '\n' + self.__repr__initialized()

    def name(self):
        return repr(self.__class__)

    def at(self, offset):
        result = super(type, self).at(offset)
        index = result[-1]

        result[-1] = self.keys()[index]     # convert our index to a name
        return result

if __name__ == '__main__':
    import pstruct

    import ptype,parray,provider
    import pint as p
    import pstr

    class Elf32_Half(p.bigendian(p.uint16_t)): pass
    class Elf32_Word(p.bigendian(p.uint32_t)): pass
    class Elf32_Addr(p.bigendian(p.uint32_t)): pass
    class Elf32_Off(p.bigendian(p.uint32_t)): pass

    EI_IDENT=16
    class ident(parray.type):
        length = EI_IDENT
        _object_ = pstr.char_t

    import dyn
    class ident(pstruct.type):
        _fields_ = [
            (Elf32_Word, 'EI_MAG'),
            (pstr.uchar_t, 'EI_CLASS'),
            (pstr.uchar_t, 'EI_DATA'),
            (pstr.uchar_t, 'EI_VERSION'),
            (dyn.block(EI_IDENT - 7), 'EI_PAD'),
       ]

    class Elf32_Ehdr(pstruct.type):
        _fields_ = [
            (ident, 'e_ident'),
            (Elf32_Half, 'e_type'),
            (Elf32_Half, 'e_machine'),
            (Elf32_Word, 'e_version'),
            (Elf32_Addr, 'e_entry'),
            (Elf32_Off, 'e_phoff'),
            (Elf32_Off, 'e_shoff'),
            (Elf32_Word, 'e_flags'),
            (Elf32_Half, 'e_ehsize'),
            (Elf32_Half, 'e_phentsize'),
            (Elf32_Half, 'e_phnum'),
            (Elf32_Half, 'e_shentsize'),
            (Elf32_Half, 'e_shnum'),
            (Elf32_Half, 'e_shstrndx'),
            (lambda s: dyn.block( int(s['e_shentsize'].load()) ), 'e_shstrndx'),
        ]

    class Elf32_Shdr(pstruct.type):
        _fields_ = [
            (Elf32_Word, 'sh_name'),
            (Elf32_Word, 'sh_type'),
            (Elf32_Word, 'sh_flags'),
            (Elf32_Addr, 'sh_addr'),
            (Elf32_Off, 'sh_offset'),
            (Elf32_Word, 'sh_size'),
            (Elf32_Word, 'sh_link'),
            (Elf32_Word, 'sh_info'),
            (Elf32_Word, 'sh_addralign'),
            (Elf32_Word, 'sh_entsize'),
        ]

#    print 'Ehdr from alloc'
#    self = Elf32_Ehdr()
#    print self
#    self.load()
#    print self

#    print 'Ehdr from mem'
    self = Elf32_Ehdr()
    self.source = provider.memory()
    self.setoffset(id(self))
#    print self
    self.load()
    print self

#    print self['e_ident']
#    print self['e_ident']['EI_PAD']

