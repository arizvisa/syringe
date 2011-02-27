'''Provides a dynamic kind of feel'''
import ptype,parray,pstruct
import utils,provider

__all__ = []

## FIXME: might want to raise an exception or warning if we have too large of an array or a block
def block(size, **kwds):
    '''
    returns a single ptype using the specified size
    '''
    count = int(size)
    assert count >= 0, 'dyn.block(%d): argument cannot be < 0'% (count)

    class _block(ptype.type):
        length = count
        def __getslice__(self, i, j):
            return self.serialize()[i:j]
        def __getitem__(self, index):
            return self.serialize()[index]

    _block.__name__ = kwds.get('name', 'block(%d)'% size)
    return _block

def align(s, **kwds):
    '''Return a block that will align definitions in a structure'''
    class _align(block(0)):
        initialized = property(fget=lambda self: self.value is not None and len(self.value) == self.size())
        def size(self):
            p = self.parent
            i = p.value.index(self)
            offset = reduce(lambda x,y:x+int(y.size()), p.value[:i], 0)
            return (-offset) & (s-1)

        def shortname(self):
            sz = self.size()
            return '%s{size=%d}'% (super(_align, self).shortname(), sz)
    
    _align.__name__ = kwds.get('name', 'align<%d>'% s)
    return _align

def array(obj, elements, **kwds):
    '''
    returns an array based on the length specified
    '''
    count = int(elements)
    assert count >= 0, 'dyn.array(elements=%d): argument cannot be < 0'% (count)

    class _dynarray(parray.type):
        _object_ = obj
        length = count

    if obj is not None:
        _dynarray.__name__ = kwds.get('name', 'array(%s.%s, %d)'% (obj.__module__, obj.__name__, count))
    return _dynarray

def clone(cls, **newattrs):
    '''
    Will clone a class, and set its attributes to **newattrs
    Intended to aid with single-line coding.
    '''
    class __clone(cls): pass
    for k,v in newattrs.items():
        setattr(__clone, k, v)
#    __clone.__name__ = 'clone(%s.%s)'% (cls.__module__, cls.__name__)   # perhaps display newattrs all formatted pretty too?
    __clone.__name__ = '%s.%s'% (cls.__module__, cls.__name__)   # perhaps display newattrs all formatted pretty too?
#    __clone.__name__ = cls.__name__
    return __clone

class __union_generic(ptype.pcontainer):
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
        return list(self.object)

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def __getitem__(self, name):
        index = self.getindex(name)
        return self.object[index]

class union(__union_generic):
    '''
    Provides a data structure with Union-like characteristics
    If the root type isn't defined, it is assumed the first type in the union will be the root.
    '''
    root = None         # root type. determines block size.
    _fields_ = []       # aliases of root type that will act on the same data
    object = None       # objects associated with each alias

    initialized = property(fget=lambda self: self.__root is not None and self.__root.initialized)    # bool
    __root = None
    def alloc(self):
        self.__create_root()
        self.__create_objects()
        return self

    def __create_root(self):
        assert self.root, 'Need to define an element or a root element in order to create a union'
        offset = self.getoffset()
        r = self.newelement(self.root, self.shortname(), offset)
        self.__root = r
        self.value = __import__('array').array('c')

    def __create_objects(self):
        self.object = [ self.newelement(t, n, 0) for t,n in self._fields_ ]
        source = provider.string('')
        source.value = self.value
        for n in self.object:
            n.source = source
        return

    def __init__(self, **attrs):
        super(union, self).__init__(**attrs)
        if not self.root and len(self._fields_) > 0:
            t,n = self._fields_[0]
            self.root = t
        self.__create_root()
        return

    def serialize(self):
        return self.value.tostring()

    def load(self):
        self.__create_root()
        r = self.__root.l
        return self.deserialize_block(r.serialize())

    def deserialize_block(self, block):
        self.value[:] = __import__('array').array('c')
        self.value.fromstring( block[:self.size()] )
        self.__create_objects()

        # try loading everything as quietly as possible
        # [n.load() for n in self.object] 

        return self

    def __getitem__(self, key):
        # load items on demand
        result = super(union,self).__getitem__(key)
        if not result.initialized:
            return result.l
        return result

    def __repr__(self):
        if self.initialized:
            res = '(' + ', '.join(['%s<%s>'%(n,t.__name__) for t,n in self._fields_]) + ')'
            return ' '.join([self.name(), 'union', res, repr(self.serialize())])

        res = '(' + ', '.join(['%s<%s>'%(n,t.__name__) for t,n in self._fields_]) + ')'
        return ' '.join([self.name(), 'union', res])

    def size(self):
        return self.__root.size()

import sys,pint
if sys.byteorder == 'big':
    byteorder = pint.bigendian
elif sys.byteorder == 'little':
    byteorder = pint.littleendian

def setbyteorder(endianness):
    '''Set the global byte order for all pointer types'''
    global byteorder
    byteorder = endianness

def addr_t(type):
    '''Will instantiate a pointer'''
    global byteorder
    parent = byteorder(type)        # XXX: this is how we enforce the byte order
    parentname = parent().shortname()

    class pointer(parent):
        _target_ = None
        def shortname(self):
            return 'pointer<%s>'% (parentname)
        def dereference(self):
            name = '*%s'% self.name()
            p = int(self)
            return self.newelement(self._target_, name, p)
        
        deref=lambda s: s.dereference()
        d = property(fget=deref)

        def __cmp__(self, other):
            if issubclass(other.__class__, self.__class__):
                return cmp(int(self),int(other))
            return super(pointer, self).__cmp__(other)

    pointer._target_ = type
    return pointer

def pointer(target, type=pint.uint32_t):
    '''Will return a pointer to the specified target using the provided base type'''
    parent = addr_t(type)
    parent._target_ = target
    parentname = parent().shortname()

    class pointer(parent):
        _target_ = None
        def shortname(self):
            return '%s(%s)'%(parentname, target.__name__)
        pass

    pointer._target_ = target
    return pointer

def rpointer(target, object=lambda s: list(s.walk())[-1], type=pint.uint32_t):
    '''Will return a pointer to target using the object return from the provided function as the base address'''
    parent = addr_t(type)
    parent._target_ = target
    parentname = parent().shortname()

    class rpointer(parent):
        _object_ = None
        def dereference(self):
            name = '*%s'% self.name()
            base = self._object_().getoffset()
            p = base+int(self)
            return self.newelement(self._target_, name, p)

        def shortname(self):
            return 'r%s(%s, %s)'%(parentname, self._target_.__name__, self._object_.__name__)
        pass
    
    rpointer._object_ = object  # promote to a method
    return rpointer

def opointer(target, calculate=lambda s: s.getoffset(), type=pint.uint32_t):
    '''Return a pointer to target using the provided method to calculate its address'''
    parent = addr_t(type)
    parent._target_ = target
    parentname = parent().shortname()

    class opointer(parent):
        _calculate_ = None
        def dereference(self):
            name = '*%s'% self.name()
            p = self._calculate_()
            return self.newelement(self._target_, name, p)

        def shortname(self):
            return 'o%s(%s, %s)'%(parentname, self._target_.__name__, self._calculate_.__name__)
        pass
    
    opointer._calculate_ = calculate    # promote it to a method
    return opointer

__all__+= 'block,align,array,clone,union,cast,pointer,rpointer,opointer'.split(',')

if __name__ == '__main__':
    import ptypes,zlib
    from ptypes import *

    if False:
        s = 'the quick brown fox jumped over the lazy dog'
        
        class zlibstring(pstr.string):
            length = 44

        t = dyn.transform(zlibstring, lambda s,v: zlib.decompress(v), lambda s,v: zlib.compress(v))

        data = zlib.compress(s)

        z = t()
        z.source = ptypes.provider.string(data)
        print z.l

    if False:
        import dyn,pint,parray
        class test(dyn.union): 
            root = dyn.array(pint.uint8_t,4)
            _fields_ = [
                (dyn.block(4), 'block'),
                (pint.uint32_t, 'int'),
            ] 

        a = test(source=ptypes.provider.string('A'*4))
        a=a.l
        print a

    if False:
        import dyn,pint,pstruct
        class test(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'u32'),
                (pint.uint8_t, 'u8'),
                (dyn.align(4), 'alignment'),
                (pint.uint32_t, 'end'),
            ]

        a = test(source=ptypes.provider.string('A'*12))
        a=a.l
        print a
        
