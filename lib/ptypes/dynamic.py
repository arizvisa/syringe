'''Provides a dynamic kind of feel'''
from . import ptype,parray,pstruct,config,error,utils,provider
Config = config.defaults
__all__ = 'block,blockarray,align,array,clone,pointer,rpointer,opointer,union'.split(',')

## FIXME: might want to raise an exception or warning if we have too large of a block
def block(size, **kwds):
    """Returns a ptype.block type with the specified ``size``"""
    if size.__class__ not in (int,long):
        t = ptype.block(length=size)
        raise error.UserError(t, 'block', message='Argument size must be integral : %s -> %s'% (size.__class__, repr(size)))

    if size < 0:
        t = ptype.block(length=size)
        Config.log.error('block : %s : Invalid argument size=%d cannot be < 0. Defaulting to 0'% (t.typename(), size))
        size = 0

    def classname(self):
        return 'dynamic.block(%d)'% (self.length if self.value is None else len(self.value))
    kwds.setdefault('classname', classname)
    #kwds.setdefault('__module__', 'ptypes.ptype')
    kwds.setdefault('__module__', 'ptypes.dynamic')
    kwds.setdefault('__name__', 'block')
    return clone(ptype.block, length=size, **kwds)

def blockarray(type, size, **kwds):
    """Returns a parray.block with the specified ``size`` and ``type``"""
    if size.__class__ not in (int,long):
        t = parray.block(_object_=type)
        raise error.UserError(t, 'blockarray', message='Argument size must be integral : %s -> %s'% (size.__class__, repr(size)))

    if size < 0:
        t = parray.block(_object_=type)
        Config.log.error('blockarray : %s : Invalid argument size=%d cannot be < 0. Defaulting to 0'% (t.typename(),size))
        size = 0
 
    class blockarray(parray.block):
        _object_ = type
        def blocksize(self):
            return size

        def classname(self):
            t = type.typename() if ptype.istype(type) else type.__name__
            return 'dynamic.blockarray(%s,%d)'%(t, self.blocksize())
            #return 'dynamic.blockarray(%s,%d)'%(t, size)
    blockarray.__module__ = 'ptypes.dynamic'
    blockarray.__name__ = 'blockarray'
    blockarray.__getinitargs__ = lambda s: (type,size)
    return blockarray

def align(size, **kwds):
    '''return a block that will align a structure to a multiple of the specified number of bytes'''
    if size.__class__ not in (int,long):
        t = ptype.block(length=0)
        raise error.UserError(t, 'align', message='Argument size must be integral : %s -> %s'% (size.__class__, repr(size)))

    class align(block(0)):
        initializedQ = lambda self: self.value is not None
        def blocksize(self):
            p = self.parent
            if p is not None:
                i = p.value.index(self)
                offset = p.getoffset()+reduce(lambda x,y:x+y.blocksize(), p.value[:i], 0)
                return (-offset) & (size-1)
            return 0

        def classname(self):
            sz = self.blocksize()
            return 'dynamic.align(size=%d)'% sz

        def repr(self, **options):
            return self.summary(**options)

    align.__module__ = 'ptypes.dynamic'
    align.__name__ = 'align'
    align.__getinitargs__ = lambda s: (type,size)
    return align

## FIXME: might want to raise an exception or warning if we have too large of an array
def array(type, count, **kwds):
    '''
    returns an array of the specified length containing elements of the specified type
    '''
    count = int(count)
    if count.__class__ not in (int,long):
        t = parray.type(_object_=type,length=count)
        raise error.UserError(t, 'array', message='Argument count must be integral : %s -> %s'% (count.__class__, repr(count)))

    if count < 0:
        t = parray.type(_object_=type,length=count)
        Config.log.error('dynamic.array : %s : Invalid argument count=%d cannot be < 0. Defaulting to 0.'%( t.typename(), count))
        size = 0

    def classname(self):
        obj = type
        t = obj.typename() if ptype.istype(obj) else obj.__name__
        return 'dynamic.array(%s,%d)'%(t, len(self.value) if self.value is not None else count)
        #return 'dynamic.array(%s,%d)'%(t, count)

    kwds.setdefault('classname', classname)
    kwds.setdefault('length', count)
    kwds.setdefault('_object_', type)
    kwds.setdefault('__module__', 'ptypes.dynamic')
    kwds.setdefault('__name__', 'array')
    return ptype.clone(parray.type, **kwds)

def clone(cls, **newattrs):
    '''
    Will clone a class, and set its attributes to **newattrs
    Intended to aid with single-line coding.
    '''
    return ptype.clone(cls, **newattrs)

class _union_generic(ptype.container):
    def __init__(self, *args, **kwds):
        super(_union_generic,self).__init__(*args, **kwds)
        self.__fastindex = {}

    def append(self, object):
        """Add an element as part of a union. Return it's index."""
        name = object.name()

        current = len(self.object)
        self.object.append(object)
        
        self.__fastindex[name.lower()] = current
        return current

    def keys(self):
        return [name for type,name in self._fields_]

    def values(self):
        return list(self.object)

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def getindex(self, name):
        return self.__fastindex[name.lower()]

    def __getitem__(self, name):
        index = self.getindex(name)
        return self.object[index]

class union(_union_generic):
    """
    Provides a data structure with Union-like characteristics
    If the root type isn't defined, it is assumed the first type in the union will be the root.
    """
    root = None         # root type. determines block size.
    _fields_ = []       # aliases of root type that will act on the same data
    object = None       # objects associated with each alias
    value = None

    initializedQ = lambda self: self.value is not None and self.value.initialized
    def __choose_root(self, objects):
        """Return a ptype.block of a size that contain /objects/"""
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
        self.value = self.new(t,offset=self.getoffset())
        return self.value.alloc(**attrs)

    def __alloc_objects(self, value):
        source = provider.proxy(value)      # each element will write into the offset occupied by value
        self.object = []
        for t,n in self._fields_:
            self.append(self.new(t, __name__=n, offset=0, source=source))
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
        r = self.value.load()
        return self.__deserialize_block(r.serialize())

    def __deserialize_block(self, block):
        # try loading everything as quietly as possible 
        for n in self.object:
            try:
                n.load()
            except error.UserError, e:
                Config.log.warning("union.__deserialize_block : %s : Ignoring exception %s"% (self.instance(), e))
            continue
        return self

    def properties(self):
        result = super(union,self).properties()
        if self.initializedQ():
            result['object'] = ['%s<%s>'%(v.name(),v.classname()) for v in self.object]
        else:
            result['object'] = ['%s<%s>'%(n,t.typename()) for t,n in self._fields_]
        return result

    def __getitem__(self, key):
        result = super(union,self).__getitem__(key)
        try:
            if not result.initializedQ():
                result.l
        except error.UserError, e:
            Config.log.warning("union.__getitem__ : %s : Ignoring exception %s"% (self.instance(), e))
        return result

    def details(self):
        if self.initializedQ():
            res = repr(self.serialize())
            root = self.value.classname()
        else:
            res = '???'
            root = self.__choose_root(t for t,n in self._fields_).typename()
        return '%s %s'%(root, res)

    def blocksize(self):
        return self.value.blocksize()
    def size(self):
        return self.value.size()

    def setoffset(self, ofs, recurse=False):
        if self.value is not None:
            self.value.setoffset(ofs, recurse=recurse)
        return super(ptype.container,self).setoffset(ofs, recurse=recurse)
    def getoffset(self, **_):
        return super(ptype.container,self).getoffset(**_)

union_t = union # alias

import pint
integral = ptype.clone(pint.uint32_t, byteorder=Config.integer.order)
def pointer(target, type=integral, **attrs):
    def classname(self):
        return 'dynamic.pointer(%s)'% target.typename() if ptype.istype(target) else target.__name__
#    attrs.setdefault('classname', classname)
    return ptype.clone(ptype.pointer_t, _object_=target, _type_=type, **attrs)

def rpointer(target, object=lambda s: list(s.walk())[-1], type=integral, **attrs):
    '''a pointer relative to a particular object'''
    def classname(self):
        return 'dynamic.rpointer(%s, ...)'% target.typename() if ptype.istype(target) else target.__name__
#    attrs.setdefault('classname', classname)
    return ptype.clone(ptype.rpointer_t, _object_=target, _baseobject_=object, _type_=type, **attrs)

def opointer(target, calculate=lambda s: s.getoffset(), type=integral, **attrs):
    '''a pointer relative to a particular offset'''
    def classname(self):
        return 'dynamic.opointer(%s, ...)'% target.typename() if ptype.istype(target) else target.__name__
#    attrs.setdefault('classname', classname)
    return ptype.clone(ptype.opointer_t, _object_=target, _calculate_=calculate, _type_=type, **attrs)

if __name__ == '__main__':
    import ptype,parray,pstruct,parray,pint,provider
    import logging,config
    config.defaults.log.setLevel(logging.DEBUG)

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
    import ptypes,zlib
    from ptypes import *
    from ptypes import config

    ptypes.setsource(ptypes.provider.string('A'*50000))

    string1='ABCD'  # bigendian
    string2='DCBA'  # littleendian

    s1 = 'the quick brown fox jumped over the lazy dog'
    s2 = s1.encode('zlib')

    @TestCase
    def test_dynamic_union_rootstatic():
        import dynamic,pint,parray
        class test(dynamic.union): 
            root = dynamic.array(pint.uint8_t,4)
            _fields_ = [
                (dynamic.block(4), 'block'),
                (pint.uint32_t, 'int'),
            ] 

        a = test(source=ptypes.provider.string('A'*4))
        a=a.l
        if a.value[0].int() != 0x41:
            raise Failure

        if a['block'].size() == 4 and a['int'].int() == 0x41414141:
            raise Success

    @TestCase
    def test_dynamic_alignment():
        import dynamic,pint,pstruct
        class test(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'u32'),
                (pint.uint8_t, 'u8'),
                (dynamic.align(4), 'alignment'),
                (pint.uint32_t, 'end'),
            ]

        a = test(source=ptypes.provider.string('A'*12))
        a=a.l
        if a.size() == 12:
            raise Success

    @TestCase
    def test_dynamic_pointer_bigendian():
        ptype.setbyteorder(config.byteorder.bigendian)

        s = ptype.provider.string(string1)
        p = dynamic.pointer(dynamic.block(0))
        x = p(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string1:
            raise Success

    @TestCase
    def test_dynamic_pointer_littleendian_1():
        ptype.setbyteorder(config.byteorder.littleendian)
        s = ptype.provider.string(string2)

        t = dynamic.pointer(dynamic.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x41424344 and x.serialize() == string2:
            raise Success

    @TestCase
    def test_dynamic_pointer_littleendian_2():
        ptype.setbyteorder(config.byteorder.littleendian)
        string = '\x26\xf8\x1a\x77'
        s = ptype.provider.string(string)
        
        t = dynamic.pointer(dynamic.block(0))
        x = t(source=s).l
        if x.d.getoffset() == 0x771af826 and x.serialize() ==  string:
            raise Success

    @TestCase
    def test_dynamic_pointer_bigendian_deref():
        ptype.setbyteorder(config.byteorder.bigendian)

        s = ptype.provider.string('\x00\x00\x00\x04\x44\x43\x42\x41')
        t = dynamic.pointer(dynamic.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def test_dynamic_pointer_littleendian_deref():
        ptype.setbyteorder(config.byteorder.littleendian)

        s = ptype.provider.string('\x04\x00\x00\x00\x44\x43\x42\x41')
        t = dynamic.pointer(dynamic.block(4))
        x = t(source=s)
        if x.l.d.getoffset() == 4:
            raise Success

    @TestCase
    def test_dynamic_pointer_littleendian_64bit_deref():
        ptype.setbyteorder(config.byteorder.littleendian)
        t = dynamic.pointer(dynamic.block(4), type=pint.uint64_t)
        x = t(source=ptype.provider.string('\x08\x00\x00\x00\x00\x00\x00\x00\x41\x41\x41\x41')).l
        if x.l.d.getoffset() == 8:
            raise Success

    @TestCase
    def test_dynamic_array_1():
        v = dynamic.array(pint.int32_t, 4)
        if len(v().a) == 4:
            raise Success

    @TestCase
    def test_dynamic_array_2():
        v = dynamic.array(pint.int32_t, 8)
        i = range(0x40,0x40+v.length)
        x = ptype.provider.string(''.join(chr(x)+'\x00\x00\x00' for x in i))
        z = v(source=x).l
        if z[4].num() == 0x44:
            raise Success

    @TestCase
    def test_dynamic_union_rootchoose():
        class test(dynamic.union):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint16_t, 'b'),
                (pint.uint8_t, 'c'),
            ]

        a = test()
        a=a.a
        if a['a'].blocksize() == 4 and a['b'].size() == 2 and a['c'].size() == 1 and a.blocksize() == 4:
            raise Success
        
if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

