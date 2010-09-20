'''Provides a dynamic kind of feel'''
import ptype,parray,pstruct
import utils

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

        if False:
            def at(self, offset):
                left,right = self.getoffset(),self.getoffset()+self.size()
                assert offset >= left and offset < right, 'Specified offset %x not found'%offset
                return [offset - self.getoffset()]

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

import pint
from warnings import warn
class _addr_t(ptype.type):
    '''Common address class whose value points to a data structure.'''
    _object_ = None
    def get(self):
        '''Returns a new instance and loads it of self._object_'''
        warn("pointer.get() is deprecated. use pointer.dereference(), or the pointer.d property instead")
        raise NotImplementedError
        return self.newelement(self._object_, repr(self._object_), int(self))
    def dereference(self):
        '''Dereferences the instance pointed to by pointer.'''
        return self.newelement(self._object_, repr(self._object_), int(self))
    deref=dereference

    d = property(fget=dereference)

class addr32_t(_addr_t, pint.uint32_t): pass
class addr64_t(_addr_t, pint.uint64_t): pass
class addr_t(addr32_t): pass

def pointer(object):
    '''Create a new pointer type of a specified object'''
    class pclass(addr_t):
        pass
    pclass.__name__ = 'pointer(%s.%s)'% (object.__module__, object.__name__)
    pclass._object_ = object
    return pclass

def rpointer(object, relative=lambda s: int(s)):
    '''
    Create a relative pointer type of a specified object
    XXX: This functionality might change.
    '''
    p = pointer(object)
    p.__name__ = 'rpointer(%s.%s, %s)'% (object.__module__, object.__name__, repr(relative))
    p.dereference = lambda s: s.newelement(s._object_, repr(s._object_), relative(s))
    p.deref = p.dereference
    p.d = property(fget=p.dereference)
    return p

def cast(sourcevalue, destination):
    raise DeprecationWarning("Please use ptype.cast instead")
    result = sourcevalue.newelement( destination, 'cast(%s, %s)'% (sourcevalue.name(), repr(destination.__class__)), sourcevalue.getoffset() )
    result.deserialize( sourcevalue.serialize() )
    return result

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