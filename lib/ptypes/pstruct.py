'''base structure element'''
import ptype,utils,logging

class __pstruct_generic(ptype.container):
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
        assert isinstance(value, ptype.type), 'Cannot assign a non-ptype to an element of a container. Use .set instead.'

        index = self.getindex(name)
        offset = self.value[index].getoffset()

        value.setoffset(offset, recurse=True)
        value.source = self.source

        self.value[index] = value

class type(__pstruct_generic):
    '''
    A container for managing structured/named data

    Settable properties:
        _fields_:array( tuple( ptype, name ), ... )<w>
            This contains which elements the structure is composed of
    '''
    _fields_ = None     # list of (type,name) tuples

    initialized = property(fget=lambda s: super(type, s).initialized and len(s.value) == len(s._fields_))

    def contains(self, offset):
        return super(ptype.container, self).contains(offset)

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value = []

            try:
                ofs = self.getoffset()
                for t,name in self._fields_:
                    # create each element
                    n = self.newelement(t, name, ofs, source=self.source)
                    self.value.append(n)
                    if ptype.iscontainer(t) or ptype.isresolveable(t):
                        n.load()
                    ofs += n.blocksize()

            except StopIteration, e:
                raise
            result = super(type, self).load()
        return result

    def details(self):
        row = lambda name,value: ' '.join(['[%x]'% self.getoffset(name), value.name(), name, value.summary()])
        result = [row(name,value) for (t,name),value in zip(self._fields_, self.value)]
        if len(result) > 0:
            return '\n'.join(result)
        return '[%x] empty []'%self.getoffset()

    def repr(self):
        # print out a friendly header for the structure
        if self.__name__ is None:
            return '%s\n%s'%(self.name(),self.details())
        return '%s %s\n%s'%(self.name(),self.__name__,self.details())

    def set(self, *tuples, **allocator):
        # allocate type if we're asked to
        for name,cls in allocator.items():
            try:
                value = self.newelement(cls, 0, name)        
                value = value.a
            except AssertionError:      # XXX: newelement raises one of python's stupid assertions
                value = cls
            self[name] = value

        # set each value in tuple
        for name,value in tuples:
            self[name].set(value)

        self.setoffset( self.getoffset(), recurse=True )
        return self

def make(fields, **attrs):
    """Given a set of initialized ptype objects, return a pstruct object describing it.

    This will automatically create padding in the structure for any holes that were found.
    """
    fields = set(fields)

    # FIXME: instead of this assert, if more than one structure occupies the
    # same location, then we should promote them all into a union.
    assert len(set([x.getoffset() for x in fields])) == len(fields),'more than one field is occupying the same location'

    types = list(fields)
    types.sort(cmp=lambda a,b: cmp(a.getoffset(),b.getoffset()))

    ofs,result = 0,[]
    for object in types:
        o,n,s = object.getoffset(), object.__name__, object.blocksize()
        assert o >= ofs

        delta = o-ofs
        if delta > 0:
            result.append((ptype.clone(ptype.block,length=delta), '__padding_%x'%ofs))
            ofs += delta

        if s > 0:
            n = (n, 'unknown_%x'%ofs)[n is None]
            result.append((object.__class__, n))
            ofs += s
        continue
    return ptype.clone(type, _fields_=result, **attrs)

if __name__ == '__main__':
    import pstruct

    import ptype,parray,provider
    import pint as p
    import pstr,dyn

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

