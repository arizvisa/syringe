'''Provides a dynamic kind of feel'''
import ptype,parray,pstruct
import utils

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

class union(pstruct.type):
    '''
    Provides a Union-like data structure
    XXX: this hasn't really been tested out, but is in use in a few places.
    '''
    def load(self):
        # all point to the same source
        self.alloc()
        [ n.setoffset( self.getoffset() ) for n in self.value ]     # we use .alloc() because unions aren't digitally tangible
        [ n.load() for n in self.value ]
        return self

    def deserialize(self, source):
        source = iter(source)
        ofs = self.getoffset()

        for n in self.alloc().value:
            n.setoffset(ofs)
            n.deserialize(source)

            # use the previously defined element as input for the next one
            source = iter(n.serialize())
        return self

    def __repr__(self):
        res = '(' + ', '.join([t.__name__ for t,n in self._fields_]) + ')'
        return ' '.join([repr(self.__class__), 'union', res])

    def size(self):
        return self.value[0].size()

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

__all__+= 'block,array,clone,union,cast,pointer,rpointer,opointer'.split(',')

if __name__ == '__main__':
    import ptypes,zlib
    from ptypes import *

    s = 'the quick brown fox jumped over the lazy dog'
    
    class zlibstring(pstr.string):
        length = 44

    t = dyn.transform(zlibstring, lambda s,v: zlib.decompress(v), lambda s,v: zlib.compress(v))

    data = zlib.compress(s)

    z = t()
    z.source = ptypes.provider.string(data)
    print z.deserialize(data)
    print z.l
