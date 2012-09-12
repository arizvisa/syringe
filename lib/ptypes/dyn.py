'''Provides a dynamic kind of feel'''
import ptype,parray,pstruct
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
        initialized = property(fget=lambda self: self.value is not None and len(self.value) == self.blocksize())
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

    initialized = property(fget=lambda self: self.__root is not None and self.__root.initialized)    # bool
    __root = None
    def alloc(self, **attrs):
        with utils.assign(*self, **attrs):
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
        source = provider.string('')
        source.value = self.value
        self.object = [ self.newelement(t, n, 0, source=source) for t,n in self._fields_ ]
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

    def load(self, **kwds):
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
        return self.__root.blocksize()
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

integral = pint.uint32_t
def pointer(target, type=integral, **attrs):
    global byteorder
    m = lambda v: (lambda v:v,lambda v:lambda s,*args,**kwds:v(*args,**kwds))[callable(v) and not ptype.istype(v)](v)
    return ptype.clone(ptype.pointer_t, _target_=target, _type_=type, _byteorder_=m(byteorder), **attrs)

def rpointer(target, object=lambda s: list(s.walk())[-1], type=integral, **attrs):
    '''a pointer relative to a particular object'''
    global byteorder
    m = lambda v: (lambda v:v,lambda v:lambda s,*args,**kwds:v(*args,**kwds))[callable(v) and not ptype.istype(v)](v)
    return ptype.clone(ptype.rpointer_t, _target_=target, _baseobject_=object, _type_=type, _byteorder_=m(byteorder), **attrs)

def opointer(target, calculate=lambda s: s.getoffset(), type=integral, **attrs):
    '''a pointer relative to a particular offset'''
    global byteorder
    m = lambda v: (lambda v:v,lambda v:lambda s,*args,**kwds:v(*args,**kwds))[callable(v) and not ptype.istype(v)](v)
    return ptype.clone(ptype.opointer_t, _target_=target, _calculate_=calculate, _type_=type, _byteorder_=m(byteorder), **attrs)

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

    string1='ABCD'  # bigendian
    string2='DCBA'  # littleendian

    s1 = 'the quick brown fox jumped over the lazy dog'
    s2 = s1.encode('zlib')

    @TestCase
    def Test0():
        class zlibstring(ptype.encoded_t):
            def decode(self, **attr):
                s = provider.string(self.serialize().decode('zlib'))
                name = '*%s'% self.name()
                return self.newelement(dyn.block(len(s.value)), name, 0, source=s, **attr)

            def blocksize(self):
                return len(s2)

        z = zlibstring(source=provider.string(s2))
        if z.l.decode().l.serialize() == s1:
            raise Success

    @TestCase
    def Test1():
        class zlibstring(ptype.encoded_t):
            length = 128
            def decode(self, **attr):
                s = provider.string(self.serialize().decode('zlib'))
                name = '*%s'% self.name()
                return self.newelement(pstr.szstring, name, 0, source=s, **attr)

            def encode(self, object, **attr):
                s = object.serialize().encode('zlib')
                self.length = len(s)
                self.value = s
                return self

        thestring = pstr.szstring().set(s1)

        z = zlibstring(source=provider.string('\x00'*128))
        z.encode(thestring)
        if z.decode().l.str() == thestring.str():
            raise Success

    @TestCase
    def Test2():
        import dyn,pint,parray
        class test(dyn.union): 
            root = dyn.array(pint.uint8_t,4)
            _fields_ = [
                (dyn.block(4), 'block'),
                (pint.uint32_t, 'int'),
            ] 

        a = test(source=ptypes.provider.string('A'*4))
        a=a.l
        if a._union__root[0].int() != 0x41:
            raise Failure

        if a['block'].size() == 4 and a['int'].int() == 0x41414141:
            raise Success

    @TestCase
    def Test3():
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
    def Test4():
        dyn.setbyteorder(pint.bigendian)
        s = ptype.provider.string(string1)

        t = dyn.pointer(dyn.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string1:
            raise Success

    @TestCase
    def Test5():
        dyn.setbyteorder(pint.littleendian)
        s = ptype.provider.string(string2)

        t = dyn.pointer(dyn.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string2:
            raise Success

    @TestCase
    def Test6():
        dyn.setbyteorder(pint.littleendian)
        string = '\x26\xf8\x1a\x77'
        s = ptype.provider.string(string)
        
        t = dyn.pointer(dyn.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x771af826 and x.serialize() ==  string:
            raise Success

    @TestCase
    def Test7():
        dyn.setbyteorder(pint.bigendian)
        global x

        s = ptype.provider.string('\x00\x00\x00\x04\x44\x43\x42\x41')
        t = dyn.pointer(dyn.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def Test8():
        dyn.setbyteorder(pint.littleendian)

        s = ptype.provider.string('\x04\x00\x00\x00\x44\x43\x42\x41')
        t = dyn.pointer(dyn.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def Test9():
        dyn.setbyteorder(pint.littleendian)
        t = dyn.pointer(dyn.block(4), type=pint.uint64_t)
        x = t(source=ptype.provider.string('\x08\x00\x00\x00\x00\x00\x00\x00\x41\x41\x41\x41')).l

        if x.l.d.getoffset() == 8:
            raise Success

    @TestCase
    def Test10():
        v = dyn.array(pint.int32_t, 4)
        if len(v().a) == 4:
            raise Success

    @TestCase
    def Test11():
        v = dyn.array(pint.int32_t, 8)
        i = range(0x40,0x40+v.length)
        x = ptype.provider.string(''.join(chr(x)+'\x00\x00\x00' for x in i))
        z = v(source=x).l
        if z[4].number() == 0x44:
            raise Success
        
if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
