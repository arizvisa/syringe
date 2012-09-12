'''base ptype element'''
__all__ = 'istype,iscontainer,type,container,rethrow,none,assign'.split(',')
import bitmap,provider,utils
import types,logging
import inspect
from utils import assign

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def istype(t):
    """True if type ``t`` inherits from ptype.type"""
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)

def iscontainer(t):
    """True if type ``t`` inherits from ptype.container """
    return istype(t) and issubclass(t, container)

def isresolveable(t):
    """True if type ``t`` can be descended into"""
    return isinstance(t, (types.FunctionType, types.MethodType)) or isiterator(t)

def isrelated(t, t2):
    """True if type ``t`` is related to ``t2``"""
    def getbases(result, bases):
        for x in bases:
            if not istype(x) or x in (type,container):
                continue
            result.add(x)
            getbases(result, x.__bases__)
        return result
    return getbases(set(), t.__bases__).intersection( getbases(set(), t.__bases__) )

def forceptype(t, self):
    """Resolve type ``t`` into a ptype.type for the provided object ``self``"""

    # of type ptype
    if isinstance(t, type) or istype(t):
        return t

    # functions
    if isinstance(t, types.FunctionType):
        res = t(self)
        return forceptype(res, self)

    # bound methods
    if isinstance(t, types.MethodType):
        return forceptype(t(), self)

    if inspect.isgenerator(t):
        return forceptype(t.next(), self)

    if False:
        # and lastly iterators
        if isiterator(t):
            return forceptype(t.next(), self)

    raise ValueError('forceptype %s could not be resolved as asked by %s'% (repr(t), self.name()))

## ...and yeah... now it's done.

# fn must be a method, so args[0] will fetch self
import sys,traceback
def rethrow(fn):
    """A decorator that logs any exceptions that are thrown by function ``fn``"""
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
    """``rethrow`` all exceptions that occur during initialization of ``ptype``"""
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
    """``rethrow`` all exceptions that occur during initialization of ``ptype`` and any sub-elements"""
    class newptype(debug(ptype)):
        @rethrow
        def newelement(self, ptype, name='', ofs=0, **attrs):
            res = forceptype(ptype, self)
            assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)
            return super(newptype,self).newelement( debug(res), name, ofs, **attrs )

    newptype.__name__ = 'debugrecurse(%s)'% ptype.__name__
    return newptype

class type(object):
    """A very most atomical ptype.
    
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
    """
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
        """Create a new instance of object. Will assign provided named arguments to self.attrs"""
        try:
            self.source = self.source or provider.memory()
        except AttributeError:
            self.source = provider.memory()
        self.parent = None
        self.attrs = {}
        self.update_attributes(attrs)

    def update_attributes(self, attrs):
        """Update the attributes that will be assigned to sub-elements using the ``attrs`` dict"""
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
        """True if initialized"""
        return self.initialized

    def size(self):
        """Returns the number of bytes that have been loaded into the type"""
        if self.initialized:
            return len(self.value)

        logging.debug("ptype.type.size : %s : unable to get size of type, as object is still uninitialized. returning the blocksize instead."%(self.name()))
        return self.blocksize()

    def blocksize(self):
        """Returns the expected size of the type
    
        By default this returns self.length, but can be overloaded to define the
        size of the type. This *must* return an integral type.
        """

        # XXX: overloading will always provide a side effect of modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something.
        return int(self.length)

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def getparent(self, type=None):
        """Returns the creator of the current type.

        If the ``type`` argument is specified, will descend into .parent
        elements until encountering an instance that inherits from it.
        """
        if type is None:
            return self.parent

        if self.__class__ == type:
            return self

        for x in self.traverse():
            if issubclass(x.__class__,type) or x.__class__ == type:
                return x
            continue

#        raise ValueError('%s match %s not found in chain: %s'% (self.name(), self.new(type).shortname(), '\n'.join(self.backtrace())))
        raise ValueError("ptype.type.getparent : %s : match %s not found in chain : %s"%(self.name(),self.new(type).shortname(), ';'.join(x.shortname() for x in self.traverse())))

    def traverse(self, edges=lambda node:(node.parent for x in range(1) if node.getparent() is not None), filter=lambda node:True, *args, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.

        By default this will follow the .parent attribute until it is None,
        effectively returning a backtrace.
        """
        for self in edges(self, *args, **kwds):
            if not isinstance(self, type):
                continue

            if filter(self):
                yield self

            for y in self.traverse(edges=edges, filter=filter, *args, **kwds):
                yield y
            continue
        return

    def backtrace(self):
        """Return a backtrace to the root element"""
        path = self.traverse()
        path = [ 'type:%s name:%s offset:%x'%(x.shortname(), getattr(x, '__name__', repr(None.__class__)), x.getoffset()) for x in path ]
        return list(reversed(path))

    def set(self, string, **kwds):
        """Set entire type equal to ``string``"""
        assert string.__class__ is str
        last = self.value

        res = str(string)
        self.value = res
        self.length = len(res)
        return self

    a = property(fget=lambda s: s.alloc())   # abbr
    def alloc(self, **attrs):
        """Will zero the ptype instance with the provided ``attrs``.

        This can be overloaded in order to allocate space for the new ptype.
        """
        attrs.setdefault('source', provider.empty())
        return self.load(**attrs)

    ## operator overloads
    def __cmp__(self, x):
        """True if ``x`` is being compared to self.

        If one wants to compare the content of a type, see .compare(x)
        """
        return [-1,0][id(self) is id(x)]

    def setoffset(self, ofs, **_):
        """Changes the current offset to ``ofs``"""
        res = self.offset
        self.offset = ofs
        return res

    def getoffset(self, **_):
        """Returns the current offset"""
        return int(self.offset)

    def newelement(self, ptype, name='', ofs=0, **attrs):
        """Create a new element of type ``ptype`` with the provided ``name`` and ``ofs``

        If any ``attrs`` are provided, this will assign them to the new instance.
        The newly created instance will inherit the current object's .source and
        any .attrs designated by the current instance.
        """
        res = forceptype(ptype, self)
        assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)

        updateattrs = dict(self.attrs)
        updateattrs.update(attrs)

        # instantiate an instance if we're given a type
        if istype(res):
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
        """Synchronize the current instance with data from the .source attributes"""

        with utils.assign(self, **attrs):
            bs = self.blocksize()
            self.source.seek(self.getoffset())
            block = self.source.consume(bs)

            self.value = ''
            result = self.deserialize_block(block)
        return result

    def commit(self, **attrs):
        """Commit the current state back to the .source attribute"""
        with utils.assign(self, **attrs):
            self.source.seek( self.getoffset() )
            self.source.store( self.serialize() )
        return self

    ## byte stream input/output
    def serialize(self):
        """Return contents of type as a string"""
        if self.initialized:
            result = str(self.value)
            bs = self.blocksize()
            if len(result) < bs:
#                padding = (bs - len(result)) * self.attrs.get('padding', '\x00')
                padding = utils.padding.fill(bs-len(result), self.padding)
                return result + padding
            assert len(result) == bs, 'value of %s is larger than blocksize (%d>%d)'%(self.shortname(), len(result), bs)
            return result
        logging.warn('%s.type : %s is uninitialized during serialization (%x:+%x)', self.__module__, self.name(), self.getoffset(), self.blocksize())
#        raise ValueError('%s is uninitialized'% self.name())
        return utils.padding.fill(self.blocksize(), self.padding)

    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
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
        """Return a name similar to Python's standard __repr__() output"""
        return "<class '%s'>"% self.shortname()

    def shortname(self):
        """Return a shorter version of the type's name. Intended to be overloaded"""
        return self.__class__.__name__

    def __repr__(self):
        return self.repr()

    def repr(self):
        """Return a __repr__ of the type"""
        if self.__name__ is None:
            return '[%x] %s %s'%( self.getoffset(), self.name(), self.details())
        return '[%x] %s %s %s'%( self.getoffset(), self.name(), self.__name__, self.details())

    def details(self):
        """Return a detailed __repr__ of the type"""
        if self.initialized:
            return repr(''.join(self.serialize()))
        return '???'

    def summary(self):
        """Return a summary __repr__ of the type"""
        if self.initialized:
            return repr(''.join(self.serialize()))
        return '???'

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)"""
        if self.initialized:
            return utils.hexdump( self.serialize(), offset=self.getoffset(), **options )
        raise ValueError('%s is uninitialized'% self.name())

    def new(self, type, **attrs):
        """Instantiate a new instance of ``type`` from the current ptype with the provided ``attrs``"""
        result = self.newelement(type, None, attrs.get('offset', 0))
        result.__name__ = attrs.get('__name__', hex(id(result)) )
        # FIXME: we should probably do something to prevent this from being committed
        return result

    def copy(self, **kwds):
        """Return a duplicate instance of the current one"""
        result = self.newelement( self.__class__, self.name(), self.getoffset(), **kwds )
        result.deserialize_block( self.serialize() )
        return result

    def cast(self, t, **kwds):
        """Cast the contents of the current instance into a differing ptype"""
        source = provider.string(self.serialize())
        size = self.blocksize()
        result = self.newelement( t, self.__name__, self.getoffset() )

        ### XXX: need some better way to catch exceptions
#        return result.load(source=source, offset=0, blocksize=lambda:size, **kwds)

        try:
            result.load(source=source, offset=0, blocksize=lambda:size, **kwds)
        except Exception,e:
            logging.fatal("ptype.type.cast : %s : %s : raised an exception : %s"%(self.name(),repr(t), repr(e)))

        return result

    def compare(self, value):
        """Returns Truth if ``self`` is equivalent to `value``"""
        if not isrelated(self.__class__, value.__class__):
            return False
        return self.serialize() == value.serialize()

class container(type):
    '''
    This class is capable of containing other ptypes

    Readable properties:
        value:str<r>
            list of all elements that are being contained
    '''
    value = None    # list

    def __isInitialized(self):
        """True if the type is fully initialized"""
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initialized for x in self.value])
    initialized = property(fget=__isInitialized)  # bool

    def commit(self, **kwds):
        """Commit the current state of all children back to the .source attribute"""
        for n in self.value:
            n.commit(**kwds)
        return self

    def size(self):
        """Returns a sum of the number of bytes that are in use by all sub-elements"""
        return reduce(lambda x,y: x+y.size(), self.value, 0)

    def blocksize(self):
        """Returns a sum of the bytes that are expected to be read"""
        return reduce(lambda x,y: x+y.blocksize(), self.value, 0)

    def getoffset(self, field=None):
        '''fetch the offset of the specified field'''
        """Returns the current offset.

        If ``field`` is specified as a ``str``, return the offset of the sub-element with the provided name.
        If specified as a ``list``, descend into sub-elements using ``field`` as the path.
        """
        if not field:
            return super(container, self).getoffset()

        if field.__class__ is list:
            name,res = (field[0], field[1:])
            return self.getoffset(name) + self[name].getoffset(res)

        index = self.getindex(field)
        return self.getoffset() + reduce(lambda x,y: x+y, [ x.size() for x in self.value[:index]], 0)

    def getindex(self, name):
        """Searches the .value attribute for an element with the provided ``name``

        This is intended to overloaded by any type that inherits from ptype.container.
        """
        raise NotImplementedError('Developer forgot to overload this method')

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        for x in self.value:
            if x.contains(offset):
                logging.warn("structure %s is unaligned. found element %s to contain offset %x", self.shortname(), x.shortname(), offset)
                return True
        return False
    
    def at(self, offset, recurse=True, **kwds):
        """Returns element that contains the specified offset

        If ``recurse`` is True, then recursively descend into all sub-elements
        until an atomic type is encountered.
        """
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
        """Will return each element along the path to reach the specified ``offset``"""
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
        """Changes the current offset to ``ofs``

        If ``recurse`` is True, the update all offsets in sub-elements.
        """
        res = super(container, self).setoffset(value)
        if recurse:
            assert self.initialized
            for n in self.value:
                n.setoffset(value, recurse=recurse)
                value += n.blocksize()
            pass
        return res

    def serialize(self):
        """Return contents of all sub-elements concatenated as a string"""
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
        """Synchronize the current instance with data from the .source attributes"""
        with utils.assign(self, **attrs):
            assert self.value is not None, 'Parent must initialize self.value'
            bs = self.blocksize()
            self.source.seek(self.getoffset())
            block = self.source.consume(bs)
            result = self.deserialize_block(block)
        return result

    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
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
        """Return a duplicate instance of the current one"""
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

    def compare(self, value):
        """Compare ``self`` to ``value`` returning truth when the types are the same"""
        if (not isrelated(self.__class__, value.__class__)) or (len(self.value) != len(value.value)):
            return False

        for l,r in zip(self.value,value.value):
            if not l.compare(r):
                return False
            continue
        return True

class empty(type):
    """Empty ptype that occupies no space"""
    length = 0

class none(empty): pass

class block(none):
    """A ptype that can be accessed an array"""
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
    """Used to store ptype definitions that are determined by a specific value

    This object should be used to simplify returning a ptype that is
    identified by a 'type' value which is commonly used in file formats
    that use a (type,length,value) tuple as their containers.

    To use this properly, in your definition file create a class that inherits
    from ptype.definition, and assign an empty dictionary to the `.cache`
    variable.

    Another thing to define is the `.unknown` variable. This will be the
    default type that is returned when an identifier is not located in the
    cache that was defined.

    i.e.
    class mytypelookup(ptype.definition):
        cache = {}
        unknown = ptype.block

    In order to add entries to the cache, one can use the `.add` classmethod
    to add a ptype-entry to the cache by a specific type. However, it is
    recommended to use the `.define` method which takes it's lookup-key from
    the `.type` property.

    @mytypelookup.define
    class myptype(ptype.type):
        type = 66
        length = 10

    With this we can query the cache via `.lookup`, or `.get`.
    The `.get` method is guaranteed to always return a type.
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
    """

    cache = None        # children must assign this empty dictionary
    unknown = block     # default type to return an unknown class

    @classmethod
    def add(cls, type, object):
        """Add ``object`` to cache and key it by ``type``"""
        cls.cache[type] = object

    @classmethod
    def lookup(cls, type):
        """Lookup a ptype by a particular ``type``"""
        return cls.cache[type]

    @classmethod
    def get(cls, type, **unknownattrs):
        """Lookup a ptype by a particular value.

        Returns cls.unknown with the provided ``unknownattrs`` if ``type`` is not found.
        """
        try:
            return cls.cache[type]
        except KeyError:
            pass
        return clone(cls.unknown, type=type, **unknownattrs)

    @classmethod
    def update(cls, otherdefinition):
        """Import the definition cache from ``otherdefinition``, effectively merging the contents into the current definition"""
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
        """Merge contents of current ptype.definition with ``otherdefinition`` and update both with the resulting union"""
        if cls.update(otherdefinition):
            otherdefinition.cache = cls.cache
            return True
        return False

    @classmethod
    def define(cls, type):
        """Add a type to the cache keyed by .type attribute of ``type``.type"""
        cls.add(type.type, type)
        return type

class encoded_t(block):
    """A type that is used to abstract over elements that are in some sort of encoded format"""
    def decode(self, **attr):
        """Decodes an object from specified block into a new element"""
        if 'source' in attr:
            logging.warn('%s.encoded_t : user attempted to change the .source attribute of an encoded block', cls.__module__)
            del(attr['source'])
        name = '*%s'% self.name()
        s = self.serialize()
        return self.newelement(empty, name, 0, source=provider.string(s), **attr)

    def encode(self, object):
        """Encodes current initialized object into block"""
        self.value = object.serialize()
        self.length = len(self.value)
        return self

    d = property(fget=lambda s: s.decode())

class pointer_t(encoded_t):
    """A pointer to a particular type"""
    _type_ = None
    _target_ = None
    _byteorder_ = lambda s,x:x  # passthru

    def blocksize(self):
        """Returns the size"""
        return self._type_().blocksize()

    def newtype(self, **attrs):
        """Returns a new instance of ._type_"""
        t = self._byteorder_(self._type_)
        return t(**attrs)

    def int(self):
        """Return pointer offset as an int"""
        s = self.serialize()
        return self.newtype(source=provider.string(s)).l.int()
    def long(self):
        """Return pointer offset as a long"""
        s = self.serialize()
        return self.newtype(source=provider.string(s)).l.long()

    def decode_offset(self):
        """Returns an integer representing the resulting object's real offset"""
        return self.long()

    def set(self, value):
        """Sets the pointer_t value to ``value```"""
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
    """a pointer_t that's at an offset relative to a specific object"""
    _baseobject_ = None

    def shortname(self):
        return 'rpointer_t(%s, %s)'%(self._target_.__name__, self._baseobject_.__name__)

    def decode_offset(self):
        base = self._baseobject_().getoffset()
        return base + self.int()

class opointer_t(pointer_t):
    """a pointer_t that's calculated via a user-provided function that takes an integer value as an argument"""
    _calculate_ = lambda s,x: x

    def shortname(self):
        return 'opointer_t(%s, %s)'%(self._target_.__name__, self._calculate_.__name__)

    def decode_offset(self):
        return self._calculate_(self.int())

if False:
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
try:
    import pyasm
    raise ImportError

except ImportError:
    # XXX: i'm not sure why i'm implementing this in this module, as it actually
    #       makes sense to put this all in a separate module for the different
    #       types and calling conventions

    class code_t(block):
        machine,mode = 'i386',32
        convention = None

        def call(self, *args, **registers):
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

    if True:
        import ptypes
        from ptypes import *
        reload(ptypes)

        class u8(pint.uint8_t): pass
        class u16(pint.uint16_t): pass
        class u24(dyn.clone(pint.uint_t, length=3)): pass
        class u32(pint.uint32_t): pass

        s = ptypes.provider.string
        s1 = s('A'*8 + 'B'*8)
        s2 = s('A'*4 + 'B'*8 + 'C'*4)

        if False:
            a = u8(source=s1).l
            b = u8(source=s2).l
    #        print a,b
            print a.compare(b)

            a = dyn.array(u8, 16)(source=s1).l
            b = dyn.array(u8, 16)(source=s1).l
            print a.compare(b)

            a = dyn.array(u8, 16)(source=s1).l
            b = dyn.array(u8, 16)(source=s2).l
            print a.compare(b)

            a = dyn.array(u16, 8)(source=s1).l
            b = dyn.array(u32, 4)(source=s1).l
            print a.compare(b)

            a = dyn.array(u16, 8)(source=s1).l
            b = dyn.array(u32, 4)(source=s2).l
            print a.compare(b)

        if True:
            def iterate_differences(o1, o2):
                """Compare ``o1`` to ``o2`` yielding each element that differs"""
                leafs = lambda s: s.traverse(edges=lambda x:x.v, filter=lambda x: not iscontainer(x))

                for l,r in zip(leafs(o1),leafs(o2)):
                    yield l.compare(r),(l,r)
                    continue
                return

            a = dyn.array(u32, 4)(source=s1).l
            b = dyn.array(u32, 4)(source=s2).l
            c = [ {'l':x,'r':y} for t,(x,y) in iterate_differences(a,b) if not t ]
            print c[0]['l'].getoffset() == 4 and c[0]['r'].getoffset() == 4
            print c[1]['l'].getoffset() == 0xc and c[1]['r'].getoffset() == 0xc
