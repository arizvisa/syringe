'''base ptype element'''
__all__ = 'istype,iscontainer,type,container,rethrow,none,assign'.split(',')
import bitmap,provider,utils
import types,logging
import inspect
from utils import assign

## this is all a horrible and slow way to do this...
def isiterator(t):
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def istype(t):
    ''' returns true if specified type is a class and inherits from ptype.type '''
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

def iscontainer(t):
    ''' returns true if specified type inherits from container '''
    return istype(t) and issubclass(t, container)

def isresolveable(p):
    return isinstance(p, (types.FunctionType, types.MethodType)) or isiterator(p)

def forceptype(p, self):
    ''' as long as value is a function, keep calling it with a context until we get a "ptype" '''

    # of type ptype
    if isinstance(p, type) or istype(p):
        return p

    # functions
    if isinstance(p, types.FunctionType):
        res = p(self)
        return forceptype(res, self)

    # bound methods
    if isinstance(p, types.MethodType):
        return forceptype(p(), self)

    if inspect.isgenerator(p):
        return forceptype(p.next(), self)

    if False:
        # and lastly iterators
        if isiterator(p):
            return forceptype(p.next(), self)

    raise ValueError('forceptype %s could not be resolved as asked by %s'% (repr(p), self.name()))

## ...and yeah... now it's done.

# fn must be a method, so args[0] will fetch self
import sys,traceback
def rethrow(fn):
    def catch(*args, **kwds):
        try:
            return fn(*args, **kwds)

        except:
            # FIXME: this code is stupid.
            #        what we want is when an exception is raised in
            #          .load/.deserialize, to display the elements involved,
            #          and display the fields that have been successfully
            #          loaded. in order to debug those, all we care about is
            #          what particular field caused the structure initialization
            #          to fail.
            tb = traceback.format_stack()
            self = args[0]
            type, exception = sys.exc_info()[:2]

            path = ' ->\n\t'.join( self.backtrace() )

            res = []
            res.append('')
            res.append('Caught exception: %s\n'% exception)
            res.append('%s<%x:+??> %s =>'%(self.shortname(),self.getoffset(), path))
            res.append('\t<method name> %s'% fn.__name__)

            if self.initialized:
                if iscontainer(self.__class__):
                    if self.value:
                        res.append('\t<container length> %x'% len(self.value))
                    else:
                        res.append('\t<container value> %s'% repr(self.value))
                else:
                    res.append('\t<type length> %x'% len(self))

            res.append('')
            res.append('Traceback (most recent call last):')
            res.append( ''.join(tb) )
            res.append('')
            sys.stderr.write('\n'.join(res))
            raise

        pass
    catch.__name__ = 'catching(%s)'% fn.__name__
    return catch

def debug(ptype):
    '''Will clone ptype into one containing more detailed debugging information'''
    assert istype(ptype), '%s is not a ptype'% repr(ptype)
    class newptype(ptype):
        @rethrow
        def deserialize_block(self, block):
            return super(newptype, self).deserialize_block(block)

        @rethrow
        def serialize(self):
            return super(newptype, self).serialize()

        @rethrow
        def load(self, **kwds):
            return super(newptype, self).load(**kwds)

        @rethrow
        def commit(self, **kwds):
            return super(newptype, self).commit(**kwds)

    newptype.__name__ = 'debug(%s)'% ptype.__name__
    return newptype

def debugrecurse(ptype):
    '''Will clone ptype into one containing recursive debugging information'''
    class newptype(debug(ptype)):
        @rethrow
        def newelement(self, ptype, name='', ofs=0, **attrs):
            res = forceptype(ptype, self)
            assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)
            return super(newptype,self).newelement( debug(res), name, ofs, **attrs )

    newptype.__name__ = 'debugrecurse(%s)'% ptype.__name__
    return newptype

class type(object):
    '''
    A very most atomical ptype.
    
    Contains the following settable properties:
        length:int<w>
            size of ptype
        source:ptypes.provider<rw>
            source of input for ptype

    Readable properties:
        value:str<r>
            contents of ptype

        parent:subclass(ptype.type)<r>
            the ptype that created us

        initialized:bool(r)
            if ptype has been initialized yet
    '''
    offset = 0
    length = 0      # int
    value = None    # str
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    initialized = property(fget=lambda self: self.value is not None and len(self.value) == self.blocksize())    # bool
    source = None   # ptype.provider
    p = property(fget=lambda s: s.parent)   # abbr to get to .parent
    parent = type   # ptype.type

    padding = utils.padding.source.zero()

    attrs = None    # dict of attributes that will get assigned to any child elements
    __name__ = None # default to unnamed
    
    ## initialization
    def __init__(self, **attrs):
        '''Create a new instance of object. Will assign provided named arguments to self.attrs'''
        try:
            self.source = self.source or provider.memory()
        except AttributeError:
            self.source = provider.memory()
        self.parent = None
        self.attrs = {}
        self.update_attributes(attrs)

    def update_attributes(self, attrs):
        if 'recurse' not in attrs:
            recurse=attrs   # XXX: copy all attrs into recurse, since we conditionaly propogate
        else:
            recurse=attrs['recurse']
            del(attrs['recurse'])

        # FIXME: the next block is responsible for conditionally propogating
        #        attributes. i think that some code in pecoff propogates data
        #        to children elements. that code should be rewritten to use the
        #        new 'recurse' parameter.

        # disallow which attributes are not allowed to be recursed into any child elements
        a = set( ('source','offset','length','value','_fields_','parent','__name__', 'size', 'blocksize') )
        self.attrs.update(dict(((k,v) for k,v in recurse.iteritems() if k not in a)))

        # update self if user specified
        attrs.update(recurse)
        for k,v in attrs.items():
            setattr(self, k, v)
        return self

    def __nonzero__(self):
        return self.initialized

    def size(self):
        '''returns the number of bytes used by type'''
        if self.initialized:
            return len(self.value)

        logging.debug("%s.size() -- object is uninitialized, returning 0."%self.name())
        return 0

    def blocksize(self):
        '''Can be overloaded to define the block's size. This MUST return an integral type'''

        # XXX: overloading will always provide a side effect of modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something
        return int(self.length)

    def contains(self, offset):
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def getparent(self, type=None):
        if type is None:
            return self.parent

        if self.__class__ == type:
            return self

        for x in self.traverse():
            if issubclass(x.__class__,type) or x.__class__ == type:
                return x
            continue

        raise ValueError('%s match %s not found in chain: %s'% (self.name(), self.new(type).shortname(), '\n'.join(self.backtrace())))

    def traverse(self, branches=lambda node:(node.parent for x in range(1) if node.getparent() is not None), *args, **kwds):
        '''
        Will walk the elements returned by the generator branches(visitee)
        defaults to getting the path to the root node
        '''
        for self in branches(self, *args, **kwds):
            yield self
            for y in self.traverse(branches, *args, **kwds):
                yield y
            continue
        return

    def backtrace(self):
        '''Return a backtrace to the root element'''
        path = self.traverse()
        path = [ 'type:%s name:%s offset:%x'%(x.shortname(), getattr(x, '__name__', repr(None.__class__)), x.getoffset()) for x in path ]
        return list(reversed(path))

    def set(self, string, **kwds):
        '''set entire type equal to string'''
        assert string.__class__ is str
        last = self.value

        res = str(string)
        self.value = res
        self.length = len(res)
        return self

    a = property(fget=lambda s: s.alloc())   # abbr
    def alloc(self, **kwds):
        '''will initialize a ptype with zeroes'''
        kwds.setdefault('source', provider.empty())        
        return self.load(**kwds)

    ## operator overloads
    def __cmp__(self, x):
        '''true only if being compared to self. see .compare for comparing content'''
        return [-1,0][id(self) is id(x)]

    def setoffset(self, value, **kwds):
        '''modifies the current offset (should probably be deprecated)'''
        res = self.offset
        self.offset = value
        return res

    def getoffset(self, **kwds):
        '''returns the current offset (should probably be deprecated)'''
        return int(self.offset)

    def newelement(self, ptype, name='', ofs=0, **attrs):
        '''
        create a new element of type ptype with the specified name and offset.
        this will duplicate the source, and set the new element's .parent
        attribute. this will also pass the self.attrs property to the child constructor.
        '''
        res = forceptype(ptype, self)
        assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)

        updateattrs = dict(self.attrs)
        updateattrs.update(attrs)

        # instantiate an instance if we're given a type
        if istype(res):
#            res.name = lambda s: name
            res = res(**updateattrs)

        # update the instance's properties
        res.parent = self
        res.__name__ = name
        res.setoffset(ofs)

        if 'source' not in updateattrs:
            res.source = self.source

        return res

    ## reading/writing to memory provider
    l = property(fget=lambda s: s.load())   # abbr

    def load(self, **attrs):
        '''sync self with some specified data source'''

        with utils.assign(self, **attrs):
            bs = self.blocksize()
            self.source.seek(self.getoffset())
            block = self.source.consume(bs)

            self.value = ''
            result = self.deserialize_block(block)
        return result

    def commit(self, **attrs):
        '''write self to self.source'''
        with utils.assign(self, **attrs):
            self.source.seek( self.getoffset() )
            self.source.store( self.serialize() )
        return self

    ## byte stream input/output
    def serialize(self):
        '''return self as a byte stream'''
        if self.initialized:
            result = str(self.value)
            bs = self.blocksize()
            if len(result) < bs:
#                padding = (bs - len(result)) * self.attrs.get('padding', '\x00')
                padding = utils.padding.fill(bs-len(result), self.padding)
                return result + padding
            assert len(result) == bs, 'value of %s is larger than blocksize (%d>%d)'%(self.shortname(), len(result), bs)
            return result
        raise ValueError('%s is uninitialized'% self.name())

    def deserialize_block(self, block):
        bs = self.blocksize()
        if len(block) < bs:
            self.value = block[:bs]
            path = ' ->\n\t'.join(self.backtrace())
            raise StopIteration("Failed reading %s at offset %x byte %d of %d\n\t%s"%(self.name(), self.getoffset(), len(block), bs, path))

        # all is good.
        self.value = block[:bs]
        return self

    ## representation
    def name(self):
        return "<class '%s'>"% self.shortname()

    def shortname(self):
        '''intended to be overloaded. should return the short name of the current ptype.'''
        return self.__class__.__name__

    def __repr__(self):
        return self.repr()

    def repr(self):
        if self.__name__ is None:
            return '[%x] %s %s'%( self.getoffset(), self.name(), self.details())
        return '[%x] %s %s %s'%( self.getoffset(), self.name(), self.__name__, self.details())

    def details(self):
        '''return a detailed description of the type's value'''
        if self.initialized:
            return repr(''.join(self.serialize()))
        return '???'

    def summary(self):
        '''return a summary of the type's value'''
        if self.initialized:
            return repr(''.join(self.serialize()))
        return '???'

    def hexdump(self, **kwds):
        '''return a hexdump of the type's value'''
        if self.initialized:
            return utils.hexdump( self.serialize(), offset=self.getoffset(), **kwds )
        raise ValueError('%s is uninitialized'% self.name())

    def new(self, type, **kwds):
        '''instantiate a new type as a child of the current ptype'''
        result = self.newelement(type, None, kwds.get('offset', 0))
        result.__name__ = kwds.get('__name__', hex(id(result)) )
        # FIXME: we should probably do something to prevent this from being committed
        return result

    def copy(self, **kwds):
        '''return a duplicated instance of the current type'''
        result = self.newelement( self.__class__, self.name(), self.getoffset(), **kwds )
        result.deserialize_block( self.serialize() )
        return result

    def cast(self, t, **kwds):
        '''cast the contents of the current ptype to a differing ptype'''
        source = provider.string(self.serialize())
        size = self.blocksize()
        result = self.newelement( t, self.__name__, self.getoffset() )

        ### XXX: need some better way to catch exceptions
#        return result.load(source=source, offset=0, blocksize=lambda:size, **kwds)

        try:
            result.load(source=source, offset=0, blocksize=lambda:size, **kwds)
        except Exception,e:
            logging.fatal('%s.cast(%s) -- %s'%(self.name(),repr(t), repr(e)))
        return result

class container(type):
    '''
    This class is capable of containing other ptypes

    Readable properties:
        value:str<r>
            list of all elements that are being contained
    '''
    value = None    # list

    def isInitialized(self):
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value])
    initialized = property(fget=isInitialized)  # bool

    def commit(self, **kwds):
        '''will commit values of all children back to source'''
        for n in self.value:
            n.commit(**kwds)
        return self

    def size(self):
        '''Calculate the total used size of a container'''
        return reduce(lambda x,y: x+y.size(), self.value, 0)

    def blocksize(self):
        return reduce(lambda x,y: x+y.blocksize(), self.value, 0)

    def getoffset(self, field=None, **attrs):
        '''fetch the offset of the specified field'''
        if not field:
            return super(container, self).getoffset()

        if field.__class__ is list:
            name,res = (field[0], field[1:])
            return self.getoffset(name) + self[name].getoffset(res)

        index = self.getindex(field)
        return self.getoffset() + reduce(lambda x,y: x+y, [ x.size() for x in self.value[:index]], 0)

    def getindex(self, name):
        '''intended to be overloaded. should return the index into self.value of the specified name'''
        raise NotImplementedError('Developer forgot to overload this method')

    def contains(self, offset):
        for x in self.value:
            if x.contains(offset):
                logging.warn("structure %s is unaligned. found element %s to contain offset %x", self.shortname(), x.shortname(), offset)
                return True
        return False
    
    def at(self, offset, recurse=True, **kwds):
        if not recurse:
            for i,n in enumerate(self.value):
                if n.contains(offset):
                    return n
                continue
            raise ValueError('%s (%x:+%x) - Offset 0x%x not found in a child element. returning encompassing parent.'%(self.shortname(), self.getoffset(), self.blocksize(), offset))
    
        try:
            res = self.at(offset, False, **kwds)
        except ValueError, msg:
            logging.info('non-fatal exception raised',ValueError,msg)
            return self

        # drill into containees for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (NotImplementedError, AttributeError):
            pass
        return res
        
    def walkto(self, offset, **kwds):
        '''will walk all the objects needed to reach a particular offset'''
        obj = self

        # drill into containees for more detail
        try:
            while True:
                yield obj
                obj = obj.at(offset, recurse=False, **kwds)
            assert False is True
        except (NotImplementedError, AttributeError):
            pass
        return

    def setoffset(self, value, recurse=False):
        '''modifies the current offset, set recurse=True to update all offsets in all children'''
        res = super(container, self).setoffset(value)
        if recurse:
            assert self.initialized
            for n in self.value:
                n.setoffset(value, recurse=recurse)
                value += n.blocksize()
            pass
        return res

    def serialize(self):
        result = ''.join( (x.serialize() for x in self.value) )
        bs = self.blocksize()
        if len(result) < bs:
#            padding = (bs - len(result)) * self.attrs.get('padding', '\x00')
            padding = utils.padding.fill(bs-len(result), self.padding)
            return result + padding
        if len(result) > bs:
            #XXX: serialized contents is larger than user allowed us to be
            #result = result[:bs]
            pass
        return result

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            assert self.value is not None, 'Parent must initialize self.value'
            bs = self.blocksize()
            self.source.seek(self.getoffset())
            block = self.source.consume(bs)
            result = self.deserialize_block(block)
        return result

    def deserialize_block(self, block):
        assert self.value is not None, 'Parent must initialize self.value'
        ofs = self.getoffset()
        for n in self.value:
            bs = n.blocksize()
            n.setoffset(ofs)
            n.deserialize_block(block[:bs])
            block = block[bs:]
            ofs += bs
        return self

    def copy(self, **kwds):
        '''return a duplicated instance of the current ptype'''
        result = self.newelement( self.__class__, self.name(), self.getoffset() )

        # assign to self
        kwds.setdefault('parent', self.parent)
        kwds.setdefault('source', self.source)
        result.update_attributes(kwds)

        def all(node, **attrs):
            if node.v.__class__ is list:
                for x in node.v:
                    yield x
            return

        # update attributes in all children too
        result = result.alloc(offset=0,source=provider.string(self.serialize()))

        ofs = result.getoffset()
        for x in result.traverse(all):
            x.setoffset( x.getoffset()+ofs )
            x.source = result.source
        return result

class empty(type):
    '''empty ptype that occupies no space'''
    length = 0

class none(empty): pass

class block(none):
    def __getslice__(self, i, j):
        return self.serialize()[i:j]
    def __getitem__(self, index):
        return self.serialize()[index]
    def shortname(self):
        return 'block(%d)'% self.length

def clone(cls, **newattrs):
    '''
    will clone a class, and set its attributes to **newattrs
    intended to aid with single-line coding.
    '''
    class __clone(cls): pass
    for k,v in newattrs.items():
        setattr(__clone, k, v)

    # FIXME: figure out why some object names are inconsistent
#    __clone.__name__ = 'clone(%s.%s)'% (cls.__module__, cls.__name__)   # perhaps display newattrs all formatted pretty too?
#    __clone.__name__ = '%s.%s'% (cls.__module__, cls.__name__)   # perhaps display newattrs all formatted pretty too?
    __clone.__name__ = cls.__name__
    return __clone

class definition(object):
    '''
        this object should be used to simplify returning a ptype
        that is identified by a 'type' value which is commonly
        used in file formats that use a (type,length,value) tuple
        as their containers.

        to use this properly, in your definition file create a
        class that inherits from ptype.definition, and assign
        an empty dictionary to the `.cache` variable.

        another thing to define is the `.unknown` variable. this
        will be the default type that is returned when an
        identifier is not located in the cache that was defined.

        i.e.
        class mytypelookup(ptype.definition):
            cache = {}
            unknown = ptype.block

        in order to add entries to the cache, one can use the
        `.add` classmethod to add a ptype-entry to the cache by a
        specific type. however, it is recommended to use the
        `.define` method which takes it's lookup-key from the
        `.type` property.

        @mytypelookup.define
        class myptype(ptype.type):
            type = 66
            length = 10

        with this we can query the cache via `.lookup`, or `.get`.
        the `.get` method is guaranteed to always return a type.
        optionally one can assign attributes to a clone of the
        fetched type.

        i.e.
        theptype = mytypelookup.lookup(66)
        
        or

        class structure(pstruct.type):
            def __value(self):
                id = self['type'].int()
                thelength = self['length'].int()
                return myptypelookup.get(id, length=thelength)

            _fields_ = [
                (uint32_t, 'type'),
                (uint32_t, 'size')
                (__value, 'unknown')
            ]

    '''

    cache = None        # children must assign this empty dictionary
    unknown = block     # default type to return an unknown class

    @classmethod
    def add(cls, type, object):
        '''add object to cache and key it by type'''
        cls.cache[type] = object

    @classmethod
    def lookup(cls, type):
        '''lookup a ptype by a particular value'''
        return cls.cache[type]

    @classmethod
    def get(cls, _, **unknownattrs):
        '''lookup a ptype by a particular value. return cls.unknown with specified attributes if not found'''
        try:
            return cls.cache[_]
        except KeyError:
            pass
        return clone(cls.unknown, type=_, **unknownattrs)

    @classmethod
    def update(cls, otherdefinition):
        '''import the definition cache from another, effectively merging the contents into the current definition'''
        a = set(cls.cache.keys())
        b = set(otherdefinition.cache.keys())
        if a.intersection(b):
            logging.warn('%s : Unable to import module %s due to multiple definitions of the same record',cls.__module__, repr(otherdefinition))
            logging.warn('%s : duplicate records %s', cls.__module__, repr(a.intersection(b)))
            return False

        # merge record caches into a single one
        cls.cache.update(otherdefinition.cache)
        otherdefinition.cache = cls.cache
        return True

    @classmethod
    def merge(cls, otherdefinition):
        '''merge contents of record cache and assign them to both the present definition and the other definition'''
        if cls.update(otherdefinition):
            otherdefinition.cache = cls.cache
            return True
        return False

    @classmethod
    def define(cls, type):
        '''add a type to the cache keyed by `type`.type (this is intended to be used as a decorator to your class definition)'''
        cls.add(type.type, type)
        return type

class encoded_t(block):
    def decode(self, **attr):
        '''decodes an object from specified block into a new element'''
        if 'source' in attr:
            logging.warn('%s.encoded_t : user attempted to change the .source attribute of an encoded block', cls.__module__)
            del(attr['source'])
        name = '*%s'% self.name()
        s = self.serialize()
        return self.newelement(empty, name, 0, source=provider.string(s), **attr)

    def encode(self, object):
        '''encodes initialized object to block'''
        self.value = object.serialize()
        self.length = len(self.value)
        return self

    d = property(fget=lambda s: s.decode())

class pointer_t(encoded_t):
    _type_ = None
    _target_ = None
    _byteorder_ = lambda s,x:x  # passthru

    def blocksize(self):
        return self._type_().blocksize()

    def newtype(self, **attrs):
        t = self._byteorder_(self._type_)
        return t(**attrs)

    def int(self):
        s = self.serialize()
        return self.newtype(source=provider.string(s)).l.int()
    def long(self):
        s = self.serialize()
        return self.newtype(source=provider.string(s)).l.long()

    def decode_offset(self):
        '''Returns an integer representing the resulting object's real offset'''
        return self.long()

    def set(self, value):
        assert value.__class__ in (int,long)
        n = self._type_().alloc().set(value)
        self.value = n.serialize()
        return self

    def decode(self, **attr):
        name = '*%s'%self.shortname()
        return self.newelement(self._target_, name, self.decode_offset(), **attr)

    def encode(self, object, **attr):
        raise NotImplementedError

    def shortname(self):
        target = forceptype(self._target_, self)
        return 'pointer_t<%s>'% target().shortname()
    
    deref = lambda s,**attrs: s.decode(**attrs)
    dereference = lambda s,**attrs: s.decode(**attrs)

    def __cmp__(self, other):
        if issubclass(other.__class__, self.__class__):
            return cmp(int(self),int(other))
        return super(pointer_t, self).__cmp__(other)

    def details(self):
        return '(void*)0x%x'% self.int()
    summary = details

class rpointer_t(pointer_t):
    '''a pointer_t that's an offset relative to a specific object'''
    _baseobject_ = None

    def shortname(self):
        return 'rpointer_t(%s, %s)'%(self._target_.__name__, self._baseobject_.__name__)

    def decode_offset(self):
        base = self._baseobject_().getoffset()
        return base + self.int()

class opointer_t(pointer_t):
    '''a pointer_t that's calculated via a user-provided function that takes an integer value as an argument'''
    _calculate_ = lambda s,x: x

    def shortname(self):
        return 'opointer_t(%s, %s)'%(self._target_.__name__, self._calculate_.__name__)

    def decode_offset(self):
        return self._calculate_(self.int())

try:
    import pymsasid as udis
    import pymsasid.syn_att as udis_att
    raise ImportError

    class _udis_glue(udis.input.FileHook):
        def __init__(self, source, base_address):
            udis.input.FileHook.__init__(self, source, base_address)
            self.entry_point = base_address
            self.source = source

        def hook(self):
            '''returns a byte as an integer'''
            ch = self.source.consume(1)
            return ord(ch)

        def seek(self, offset):
            self.source.seek(offset)

        @classmethod
        def new(cls, type, mode):
            return udis.Pymsasid(hook=cls, source=type.source, mode=mode)

    class code_t(block):
        '''code_t is always referenced by a pointer'''
        mode = 32

        def __init__(self, **kwds):
            super(code_t, self).__init__(**kwds)
            self.u = _udis_glue.new(self, self.mode)

        def details(self):
            sz = self.blocksize()
            if sz == 0: 
                count = 5
                result = []
                pc = self.getoffset()
                while len(result) < count:
                    n = self.u.disassemble(pc)
                    result.append(n)
                    pc = n.next_add()
                return ';'.join([str(x).strip() for x in result])

            result = []
            st = pc = self.getoffset()
            while pc < st+sz:
                n = self.u.disassemble(pc)
                result.append(n)
                pc = n.next_add()
            return ';'.join([str(x).strip() for x in result])

except ImportError:
    class code_t(block):
        machine,mode = 'i386',32

    def call(address):
        # returns a python function that when provided a dict containing the register state
        # calls the specified address and returns the register state upon return
        pass

if __name__ == '__main__':
    import ptype
    if False:
        class p10bytes(ptype.type):
            length = 10

        import provider

        x = p10bytes()
        print repr(x)
    #    x.load()
    #    print repr(x)

        x.source = provider.memory()
        x.setoffset(id(x))
        x.load()
        print repr(x)

    if False:
        x.value = '\x7fHAI\x01\x01\x01\x00\x00\x00'
        x.commit()

        x.alloc()
        x.deserialize(input.file.read())
        x.set('hello there okay')

        x.set("okay, what the fuck. please work. i'm tired.")
        x.commit()

    if False:
        class u8(ptype.type): length=1
        class u16(ptype.type): length=2
        class u32(ptype.type): length=4
        
        x = ptype.container(value=[])
        x.v.append( u8() )
        x.v.append( u32() )
        x.v.append( u16() )
        x.v.append( u16() )
        x.v.append( u32() )
        x.v.append( u16() )
        x.v.append( u8() )
        x.v.append( u8() )
        x.v.append( u16() )
        x.source=provider.empty()
        print x.l

    if False:
        import ptypes
        from ptypes import *
        a = dyn.block(0x100)
        b = a(source=ptypes.provider.string())
        print b.set('\xcc'*100)
        b.commit()

        self = b
        a = ptype.code_t(source=self.source, offset=self.getoffset())
        b = b.cast(ptype.code_t)
