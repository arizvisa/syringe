'''Provides a dynamic kind of feel'''
import ptype,parray,pstruct,config
import utils,provider
import logging

__all__ = []

## FIXME: might want to raise an exception or warning if we have too large of an array or a block
def block(size, **kwds):
    '''
    returns a general block type of the specified size
    '''
    assert type(size) in (int,long), 'dyn.block(%s): argument must be integral'% repr(size)
    if size < 0:
        logging.error('dyn.block(%d): argument cannot be < 0. Defaulting to 0.'% size)
        size = 0
    return clone(ptype.block, length=size)

def blockarray(typ, size, **kwds):
    '''
    returns an array of the specified byte size containing elements of the specified type
    '''
    assert type(size) in (int,long), 'dyn.block(%s): argument must be integral'% repr(size)
    #size = int(size)
    if size < 0:
        logging.error('dyn.blockarray(%s, %d): argument cannot be < 0. defaulting to 0.'% (repr(typ),size))
        size = 0
 
    class _blockarray(parray.block):
        _object_ = typ
    _blockarray.blocksize = lambda s: size

    _blockarray.__name__ = kwds.get('name', 'blockarray(%s, %d)'% (type().shortname(), size))
    return _blockarray

def align(s, **kwds):
    '''return a block that will align a structure to a multiple of the specified number of bytes'''
    class _align(block(0)):
        initializedQ = lambda self: self.value is not None and len(self.value) == self.blocksize()
        def blocksize(self):
            p = self.parent
            i = p.value.index(self)
            offset = reduce(lambda x,y:x+int(y.blocksize()), p.value[:i], 0)
            return (-offset) & (s-1)

        def shortname(self):
            sz = self.blocksize()
            return '%s{size=%d}'% (super(_align, self).shortname(), sz)
    
    _align.__name__ = kwds.get('name', 'align<%d>'% s)
    return _align

def array(type, count, **kwds):
    '''
    returns an array of the specified length containing elements of the specified type
    '''
    count = int(count)
    if count < 0:
        logging.error('dyn.array(%s, count=%d): argument cannot be < 0. Defaulting to 0.'% (repr(type),count))
        size = 0

    if type is None:
        name = 'array(None, %d)'%count
    else:
        module,name = type.__module__,type.__name__
        name = 'array(%s.%s, %d)'%(module, name, count )

    result = ptype.clone(parray.type, _object_=type, length=count)
    result.__name__=kwds.get('name', name)
    return result

def clone(cls, **newattrs):
    '''
    Will clone a class, and set its attributes to **newattrs
    Intended to aid with single-line coding.
    '''
    return ptype.clone(cls, **newattrs)

class __union_generic(ptype.container):
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
    value = None

    initializedQ = lambda self: self.value is not None and self.value.initialized
    def __choose_root(self, objects):
        """return a ptype.block of a size that contain /objects/"""
        if self.root:
            return self.root

        size = 0
        for t in objects:
            x = t().a
            try:
                s = x.blocksize()
                if s > size:
                    size = s
            except:
                pass
            continue
        return clone(ptype.block, length=size)

    def __alloc_root(self, **attrs):
        t = self.__choose_root(t for t,n in self._fields_)
        ofs = self.getoffset()
        self.value = t(offset=ofs, source=self.source)
        self.value.alloc(**attrs)
        return self.value

    def __alloc_objects(self, value):
        # XXX: each newelement will write into the offset occupied by value
        source = provider.proxy(value)
        self.object = [ self.newelement(t, n, 0, source=source) for t,n in self._fields_ ]
        return self

    def alloc(self, **attrs):
        value = self.__alloc_root(**attrs) if self.value is None else self.value
        self.__alloc_objects(value)
        return self

    def serialize(self):
        return self.value.serialize()

    def load(self, **attrs):
        value = self.__alloc_root(**attrs) if self.value is None else self.value
        self.__alloc_objects(value)
        r = self.value.load(source=self.source)
        return self.__deserialize_block(r.serialize())

    def __deserialize_block(self, block):
        # try loading everything as quietly as possible 
        [n.load() for n in self.object]
        return self

    def __getitem__(self, key):
        # load items on demand in order to seem fast
        result = super(union,self).__getitem__(key)
        if not result.initialized:
            return result.l
        return result

    def details(self):
        if self.initialized:
            res = '(' + ', '.join(['%s<%s>'%(n,t.__name__) for t,n in self._fields_]) + ')'
            return ' '.join([self.name(), 'union', res, repr(self.serialize())])

        res = '(' + ', '.join(['%s<%s>'%(n,t.__name__) for t,n in self._fields_]) + ')'
        return ' '.join(('union', res))

    def blocksize(self):
        return self.value.blocksize()
    def size(self):
        return self.value.size()

union_t = union # alias

import pint
integral = ptype.clone(pint.uint32_t, byteorder=config.integer.byteorder)
def pointer(target, type=integral, **attrs):
    return ptype.clone(ptype.pointer_t, _object_=target, _type_=type, **attrs)

def rpointer(target, object=lambda s: list(s.walk())[-1], type=integral, **attrs):
    '''a pointer relative to a particular object'''
    return ptype.clone(ptype.rpointer_t, _object_=target, _baseobject_=object, _type_=type, **attrs)

def opointer(target, calculate=lambda s: s.getoffset(), type=integral, **attrs):
    '''a pointer relative to a particular offset'''
    return ptype.clone(ptype.opointer_t, _object_=target, _calculate_=calculate, _type_=type, **attrs)

__all__+= 'block,align,array,clone,union,cast,pointer,rpointer,opointer'.split(',')

if __name__ == '__main__':
    import ptype,parray
    import pstruct,parray,pint,provider

    import logging
    logging.root=logging.RootLogger(logging.DEBUG)

    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)

            except Success:
                print '%s: Success'% name
                return True

            except Failure,e:
                pass

            print '%s: Failure'% name
            return False

        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import logging
    logging.root=logging.RootLogger(logging.DEBUG)

    import ptypes,zlib
    from ptypes import *

    ptypes.setsource(ptypes.provider.string('A'*50000))

    string1='ABCD'  # bigendian
    string2='DCBA'  # littleendian

    s1 = 'the quick brown fox jumped over the lazy dog'
    s2 = s1.encode('zlib')

    @TestCase
    def Test1():
        import dyn,pint,parray
        class test(dyn.union): 
            root = dyn.array(pint.uint8_t,4)
            _fields_ = [
                (dyn.block(4), 'block'),
                (pint.uint32_t, 'int'),
            ] 

        a = test(source=ptypes.provider.string('A'*4))
        a=a.l
        if a.value[0].int() != 0x41:
            raise Failure

        if a['block'].size() == 4 and a['int'].int() == 0x41414141:
            raise Success

    @TestCase
    def Test2():
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
        if a.size() == 12:
            raise Success

    @TestCase
    def Test3():
        ptype.setbyteorder(config.byteorder.bigendian)

        global x
        s = ptype.provider.string(string1)
        p = dyn.pointer(dyn.block(0))
        x = p(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string1:
            raise Success

    @TestCase
    def Test4():
        ptype.setbyteorder(config.byteorder.littleendian)
        s = ptype.provider.string(string2)

        t = dyn.pointer(dyn.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string2:
            raise Success

    @TestCase
    def Test5():
        ptype.setbyteorder(config.byteorder.littleendian)
        string = '\x26\xf8\x1a\x77'
        s = ptype.provider.string(string)
        
        t = dyn.pointer(dyn.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x771af826 and x.serialize() ==  string:
            raise Success

    @TestCase
    def Test6():
        ptype.setbyteorder(config.byteorder.bigendian)

        s = ptype.provider.string('\x00\x00\x00\x04\x44\x43\x42\x41')
        t = dyn.pointer(dyn.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def Test7():
        ptype.setbyteorder(config.byteorder.littleendian)

        s = ptype.provider.string('\x04\x00\x00\x00\x44\x43\x42\x41')
        t = dyn.pointer(dyn.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def Test8():
        ptype.setbyteorder(config.byteorder.littleendian)
        t = dyn.pointer(dyn.block(4), type=pint.uint64_t)
        x = t(source=ptype.provider.string('\x08\x00\x00\x00\x00\x00\x00\x00\x41\x41\x41\x41')).l

        if x.l.d.getoffset() == 8:
            raise Success

    @TestCase
    def Test9():
        v = dyn.array(pint.int32_t, 4)
        if len(v().a) == 4:
            raise Success

    @TestCase
    def Test10():
        v = dyn.array(pint.int32_t, 8)
        i = range(0x40,0x40+v.length)
        x = ptype.provider.string(''.join(chr(x)+'\x00\x00\x00' for x in i))
        z = v(source=x).l
        if z[4].number() == 0x44:
            raise Success

    @TestCase
    def Test11():
        class test(dyn.union):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint16_t, 'b'),
                (pint.uint8_t, 'c'),
            ]

        a = test().a
        if a['a'].blocksize() == 4 and a['b'].size() == 2 and a['c'].size() == 1 and a.blocksize() == 4:
            raise Success
        
if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

