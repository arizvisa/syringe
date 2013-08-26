'''base ptype element'''
__all__ = 'istype,iscontainer,type,container,rethrow,none,assign'.split(',')
import bitmap,provider,utils,config
import types,logging
import inspect
from utils import assign

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def istype(t):
    """True if type ``t`` inherits from ptype.type"""
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, base)

def iscontainer(t):
    """True if type ``t`` inherits from ptype.container """
    return (istype(t) and issubclass(t, container)) or pbinary.istype(t)

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

def force(t, self, chain=None):
    """Resolve type ``t`` into a ptype.type for the provided object ``self``"""
    if chain is None:
        chain = []
    chain.append(t)

    # of type pbinary.type. we insert a partial node into the tree
    if pbinary.istype(t):
        t = clone(pbinary.partial, _object_=t)
        return t

    # of type ptype
    if isinstance(t, type) or istype(t):
        return t

    # functions
    if isinstance(t, types.FunctionType):
        res = t(self)
        return force(res, self, chain)

    # bound methods
    if isinstance(t, types.MethodType):
        return force(t(), self, chain)

    if inspect.isgenerator(t):
        return force(t.next(), self, chain)

    if False:
        # and lastly iterators
        if isiterator(t):
            return force(t.next(), self, chain)

    raise ValueError('ptype.force : chain=%s : refusing request to resolve to a non-ptype : %s'% (repr(chain), ','.join(self.backtrace())))

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

            if self.initializedQ():
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
            res = force(ptype, self)
            assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)
            return super(newptype,self).newelement( debug(res), name, ofs, **attrs )

    newptype.__name__ = 'debugrecurse(%s)'% ptype.__name__
    return newptype

class base(object):
    # FIXME: this class should implement
    #           attribute inheritance
    #           addition and removal of elements to trie
    #           initial attribute creation
    #           attributes not propagated during creation

    source = None       # ptype.prov

    attributes = None        # {...}
    ignored = set(('source','parent','attrs','value','__name__','offset'))

    parent = None       # ptype.base
    p = property(fget=lambda s: s.parent)   # abbr to get to .parent

    value = None        # _
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    def __init__(self, **attrs):
        """Create a new instance of object. Will assign provided named arguments to self.attributes"""
        try:
            self.source = self.source or provider.memory()
        except AttributeError:
            self.source = provider.memory()
        self.parent = None
        self.attributes = {}
        self.update_attributes(attrs)

    position = None     # ()
    def setposition(self, position, **kwds):
        res = self.position
        self.position = position
        return res
    def getposition(self):
        return self.position

    def update_attributes(self, attrs={}, **moreattrs):
        """Update the attributes that will be assigned to object.

        Any attributes defined under the 'recurse' key will be propogated to any sub-elements.
        """
        attrs = dict(attrs)
        attrs.update(moreattrs)
        recurse = dict(attrs.pop('recurse')) if attrs.has_key('recurse') else {}
        ignored = self.ignored

        # update self with all attributes
        res = {}
        res.update(recurse)
        res.update(attrs)
        for k,v in res.iteritems():
            setattr(self, k, v)

        # filter out ignored attributes from the recurse dictionary
        recurse = dict(((k,v) for k,v in recurse.iteritems() if k not in ignored and not callable(v)))

        # update self (for instantiated elements)
        self.attributes.update(recurse)

        # update sub-elements with recursive attributes
        if recurse and issubclass(self.__class__, container) and self.value is not None:
            for x in self.value:
                x.update_attributes(recurse=recurse)

        return self

    initialized = property(fget=lambda s: s.initializedQ())
    def initializedQ(self):
        raise NotImplementedError

    def __nonzero__(self):
        return self.initializedQ()

    def traverse(self, edges, filter=lambda node:True, *args, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.
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

    def serialize(self):
        raise NotImplementedError
    def load(self, **attrs):
        raise NotImplementedError
    def commit(self, **attrs):
        raise NotImplementedError
    def alloc(self, **attrs):
        raise NotImplementedError

    # abbreviations
    a = property(fget=lambda s: s.alloc())
    c = property(fget=lambda s: s.commit())
    l = property(fget=lambda s: s.load())

    def __repr__(self):
        return self.repr()
    def repr(self):
        raise NotImplementedError

    # naming
    def name(self):
        """Return a name similar to Python's standard __repr__() output"""
        if hasattr(self, '__module__'):
            module = self.__module__
            return "<class '%s.%s'>"% (module, self.shortname())
        return "<class '.%s'>"% (self.shortname())

    def shortname(self):
        """Return a shorter version of the type's name. Intended to be overloaded"""
        return self.__class__.__name__

    def deserialize_block(self, block):
        raise NotImplementedError('Class %s must implement deserialize_block'% self.shortname())

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)

        options can provide formatting specifiers
        max=x -- sets the maximum character length to the one specified
        summary=1 -- return a hexdump clamped to a height specified by /max/
        oneline=1 -- returns a string repr clamped to a width specified by /max/
        """
        if not self.initializedQ():
            raise ValueError('%s is uninitialized'% self.name())

        ofs,buf = self.getoffset(),self.serialize()
        bs = self.blocksize()

        # return a summary of the entire block.
        if 'summary' in options:
            rows = bs / 16
            max = options.get('max', config.summary.multiline)    # XXX: maximum number of rows to display
            if rows > max:
                result = []
                half = max/2
                bottom = len(buf)-(half*16)
                skip = len(buf) - half*16*2
                result.append( utils.hexdump(buf[:half*16], offset=ofs, lines=half) )
                result.append('%04x  ...skipping %d rows (0x%x bytes)...'% (ofs+half*16, skip/16, skip))
                result.append( utils.hexdump(buf[-half*16:], offset=ofs+bottom, lines=half) )
                return utils.indent('\n'.join(result))

            del options['summary']
        elif 'oneline' in options:
            max = options.get('max', config.summary.oneline)    # XXX: maximum width
            if bs > max:
                left = repr(buf[:max/2])
                right = repr(buf[-max/2:])
                x = bs-max                  # FIXME: not only is the width /max/ hardcoded, but
                                            #        this doesn't actually apply the length 
                                            #        constraint to the outputted string.
                                            #        
                return '%s ... skipped %d bytes ... %s'% (left, x, right)
            del options['oneline']

        options.setdefault('offset', ofs)
        return utils.indent( utils.hexdump(buf, **options) )

    def properties(self):
        """Return a tuple of properties/characteristics describing current state of object to the user"""
        result = {}
        if not self.initializedQ():
            result['uninitialized'] = True
        if not hasattr(self, '__name__') or len(self.__name__) == 0:
            result['unnamed'] = True
        else:
            result['name'] = self.__name__
        return result

    def details(self):
        """Return a detailed __repr__ of the type"""
        if self.initializedQ():
            return repr(self.serialize())
        return '???'

    def summary(self):
        """Return a summary __repr__ of the type"""
        if self.initializedQ():
            return repr(self.serialize())
        return '???'

    def getparent(self, type=None):
        """Returns the creator of the current type.

        If the ``type`` argument is specified, will descend into .parent
        elements until encountering an instance that inherits from it.
        """
        if type is None:
            return self.parent

        if self.__class__ == type:
            return self

        for x in self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None)):
            if issubclass(x.__class__,type) or x.__class__ == type:
                return x
            continue

        raise ValueError("ptype.base.getparent : %s : match %s not found in chain : %s"%(self.name(),self.new(type).shortname(), ';'.join(x.shortname() for x in self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None)))))

    def backtrace(self, fn=lambda x:'<type:%s name:%s offset:%x>'%(x.shortname(), getattr(x, '__name__', repr(None.__class__)), x.getoffset())):
        """
        Return a backtrace to the root element applying ``fn`` to each parent

        By default this returns a string describing the type and location of each structure.
        """
        path = self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None))
        path = [ fn(x) for x in path ]
        return list(reversed(path))

    def new(self, ptype, **attrs):
        """Create a new instance of ``type`` from the current ptype with the provided ``attrs``"""
        offset = attrs.get('offset',0)
        res = force(ptype, self)
        assert istype(res) or isinstance(res, type), '%s is not a ptype class'% (res.__class__)

        if 'recurse' in attrs:
            attrs['recurse'].update(self.attributes)
        else:
            attrs['recurse'] = self.attributes

        # instantiate an instance if we're given a type
        if istype(res):
            res = res(**attrs)

        # update the instance's properties
        res.parent = self
        res.__name__ = attrs.get('__name__', hex(id(res)) )
        res.setoffset(offset)

        if 'source' not in attrs:
            res.source = self.source
        return res

class type(base):
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
    length = 0      # int
    initializedQ = lambda self: self.value is not None and len(self.value) == self.blocksize()    # bool
    padding = utils.padding.source.zero()
    attributes = None    # dict of attributes that will get assigned to any child elements
    ignored = base.ignored.union(('source','parent','attrs','value','__name__','length','position'))
    position = 0,
    #__name__ = '[unnamed-type]'

    ## initialization
    def size(self):
        """Returns the number of bytes that have been loaded into the type"""
        if self.initializedQ() or self.value is not None:
            return len(self.value)

        logging.debug("ptype.type.size : %s.%s : unable to get size of type, as object is still uninitialized. returning the blocksize instead."%(self.__module__,self.shortname()))
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

    def traverse(self, edges=lambda node:tuple(node.v) if iscontainer(node.__class__) else (), filter=lambda node:True, *args, **kwds):
        """
        This will traverse a tree in a top-down approach.
    
        By default this will traverse every sub-element from a given object.
        """
        return super(type,self).traverse(edges, filter, *args, **kwds)

    def set(self, string, **kwds):
        """Set entire type equal to ``string``"""
        assert string.__class__ is str
        last = self.value

        res = str(string)
        self.value = res
        self.length = len(res)
        return self

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
        return self.setposition((ofs,))
    def getoffset(self, **_):
        """Returns the current offset"""
        o, = self.getposition()
        return o
    offset = property(fget=getoffset, fset=setoffset)

    def newelement(self, ptype, name='', ofs=0, **attrs):
        """Create a sub-element of ``ptype`` with the provided ``name`` and ``ofs``

        If any ``attrs`` are provided, this will assign them to the new instance.
        The newly created instance will inherit the current object's .source and
        any .attributes designated by the current instance.
        """
        return self.new(ptype, __name__=name, offset=ofs, **attrs)

    ## reading/writing to memory provider
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
        if self.initializedQ():
            result = str(self.value)
            bs = self.blocksize()
            if len(result) < bs:
#                padding = (bs - len(result)) * self.attributes.get('padding', '\x00')
                padding = utils.padding.fill(bs-len(result), self.padding)
                return result + padding
            assert len(result) == bs, 'value of %s is larger than blocksize (%d>%d)'%(self.shortname(), len(result), bs)
            return result
        logging.warn('ptype.type.serialize : %s.%s is uninitialized during serialization (%x:+%x)', self.__module__, self.shortname(), self.getoffset(), self.blocksize())
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
    def repr(self):
        """Return a __repr__ of the type"""
        prop = '{%s}'% ','.join('%s=%s'%(k,repr(v)) for k,v in self.properties().iteritems())
        return '[%x] %s %s %s'%( self.getoffset(), self.name(), prop, self.details())

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

        try:
            result.load(source=source, offset=0, blocksize=lambda:size, **kwds)
        except Exception,e:
            logging.fatal("ptype.type.cast : %s.%s : %s : raised an exception : %s"%(self.__module__,self.shortname(),repr(t), repr(e)))
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
    #__name__ = '[unnamed-container]'
    def initializedQ(self):
        """True if the type is fully initialized"""
        if self.value is None or None in self.value:
            return False
        return not(False in [x.initializedQ() for x in self.value])

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
        for i,x in enumerate(self.value):
            if x.contains(offset):
                logging.warn("ptype.container.contains : structure %s.%s is unaligned. found element %s to contain offset %x", self.__module__, self.shortname(), x.shortname(), offset)
                return True
            continue
        return False
    
    def at(self, offset, recurse=True, **kwds):
        """Returns element that contains the specified offset

        If ``recurse`` is True, then recursively descend into all sub-elements
        until an atomic type is encountered.
        """
        if not self.contains(offset):
            raise ValueError('%s (%x:+%x) - offset 0x%x can not be located within container.'%(self.shortname(), self.getoffset(), self.blocksize(), offset))

        if not recurse:
            for i,n in enumerate(self.value):
                if n.contains(offset):
                    return n
                continue
            raise ValueError('%s (%x:+%x) - offset 0x%x not found in a child element. returning encompassing parent.'%(self.shortname(), self.getoffset(), self.blocksize(), offset))
    
        try:
            res = self.at(offset, False, **kwds)
        except ValueError, msg:
            logging.info('ptype.container.at : non-fatal exception raised',ValueError,msg)
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
#            padding = (bs - len(result)) * self.attributes.get('padding', '\x00')
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
            try:
                result = self.deserialize_block(block)
            except StopIteration:
                s = self.size()
                if bs > s:
                    raise
                logging.debug('ptype.container.load : %s.%s : +%x bytes cropped to (%x:+%x)', self.__module__, self.shortname(), s, self.getoffset(), bs)
            return self
        return result

    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
        assert self.value is not None, 'Parent must initialize self.value'
        ofs = self.getoffset()
        for n in self.value:
            bs = n.blocksize()
            n.setoffset(ofs)
            # if element in container is already initialized, skip
            if not n.initializedQ():
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

    def summary(self):
        return self.details()

class empty(type):
    """Empty ptype that occupies no space"""
    length = 0

class none(empty): pass

class block(none):
    """A ptype that can be accessed as an array"""
    #__name__ = '[unnamed-block]'
    def __getslice__(self, i, j):
        buffer = self.serialize()
        base = self.getoffset()
        return buffer[i-base:j-base]
    def __getitem__(self, index):
        buffer = self.serialize()
        base = self.getoffset()
        return buffer[index-base]
    def shortname(self):
        return 'block(%d)'% self.length
    def summary(self):
        return self.hexdump(oneline=1)
    def details(self):
        if self.initializedQ():
            return '\n'+self.hexdump(summary=1)
        return '???'

    def __setitem__(self, index, value):
        v = self.value
        self.value = v[:index] + value + v[index:]
    def __setslice__(self, i, j, value):
        v = self.value
        if len(value) != j-i:
            raise ValueError
        self.value = v[:i] + value + v[j:]

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

class wrapper_t(type):
    _value_ = None     # type used to back wrapper_t
    __object = None       # instance
    object = property(fget=lambda s:s.__object)
    value = property(fget=lambda s:s.__object.serialize() if s.__object else None, fset=lambda s,x:s.__object.load(source=provider.string(x)))

    def shortname(self):
        name = self.__object.shortname() if self.initializedQ() else self.newelement(self._value_, 'wrapper_t', 0).shortname()
        return 'wrapper_t(%s)'% name

    def contains(self, offset):
        left = self.getoffset()
        right = left + self.blocksize()
        return left <= offset < right

    def size(self):
        return self.__object.size()

    def blocksize(self):
        name = self.shortname()
        return self.__object.blocksize() if self.initializedQ() else self.newelement(self._value_, name, self.getoffset()).blocksize()

    def commit(self, **kwds):
        void = self.__object.commit(**kwds)
        return self

    def deserialize_block(self, block):
        return self.alloc().__object.deserialize_block(block)

    def load(self, **attrs):
        self.__object = None

        obj,ofs = self._value_,self.getoffset()
        source = provider.proxy(self)
        res = self.newelement(self._value_, 'element', ofs, source=source)

        self.__object = res.load(**attrs)
        return self

    def initializedQ(self):
        return self.__object and self.__object.initializedQ()

class encoded_t(wrapper_t):
    _object_ = None

    ## string encoding
    def encode(self, string):
        return string
    def decode(self, string):
        return string

    ## object dereferencing
    def reference(self, object, **attrs):
        assert object.__class__ == self._object_
        self.value = self.encode(object.serialize())
        return self

    def dereference(self, **attrs):
        if 'source' in attrs:
            logging.warn('ptype.encoded_t.decode : %s.%s : user attempted to change the .source attribute of an encoded block', self.__module__, self.shortname())
            del(attrs['source'])

        string = self.decode(self.value)

        object = self.newelement(self._object_, self.shortname(), 0, source=provider.string(string))
        object = object.l

        name = '*%s'% self.shortname()
        return self.newelement(self._object_, name, 0, source=provider.proxy(object), **attrs)

    d = property(fget=lambda s,**a: s.dereference(**a), fset=lambda s,*x,**a:s.reference(*x,**a))
    deref = lambda s,**a: s.dereference(**a)
    ref = lambda s,*x,**a: s.reference(*x,**a)

def setbyteorder(endianness):
    '''Sets the byte order for any pointer_t
    can be either .bigendian or .littleendian
    '''
    global pointer_t
    assert endianness in (config.byteorder.bigendian,config.byteorder.littleendian), repr(endianness)
    pointer_t.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian

class pointer_t(encoded_t):
    _value_ = clone(block, length=config.integer.wordsize)
    _object_ = None
    byteorder = config.integer.byteorder

    def dereference(self, **attrs):
        name = '*%s'% self.name()
        return self.newelement(self._object_, name, self.decode_offset(), **attrs)

    def reference(self, object, **attrs):
        ofs = object.getoffset()
        self._object_ = object.__class__
        self.set(ofs)
        return self

    def set(self, offset):
        bs = self.blocksize()
        x = bitmap.new(offset, bs*8)
        self.a.object.set( bitmap.data(x, reversed=(self.byteorder is config.byteorder.littleendian)) )
        return self

    def number(self):
        assert self.initialized
        bs = self.blocksize()
        res = bitmap.zero
        value = reversed(self.value) if self.byteorder is config.byteorder.littleendian else self.value
        for x in value:
            res = bitmap.push(res, (ord(x),8))
        return bitmap.number(res)

    def int(self):
        return int(self.number())
    def long(self):
        return long(self.number())
    def decode_offset(self):
        """Returns an integer representing the resulting object's real offset"""
        return self.long()

    def shortname(self):
        target = force(self._object_, self)
        return 'pointer_t<%s>'% target().shortname()
    def __cmp__(self, other):
        if issubclass(other.__class__, self.__class__):
            return cmp(self.number(),other.number())
        return super(pointer_t, self).__cmp__(other)
    def details(self):
        if self.initializedQ():
            return '(pointer_t*)0x%x'% self.number()
        return '(pointer_t*) ???'
    summary = details

class rpointer_t(pointer_t):
    """a pointer_t that's at an offset relative to a specific object"""
    _baseobject_ = None
    #__name__ = '[unnamed-rpointer]'

    def shortname(self):
        return 'rpointer_t(%s, %s)'%(self._object_.__name__, self._baseobject_.__name__)

    def decode_offset(self):
        base = self._baseobject_().getoffset()
        return base + self.int()

class opointer_t(pointer_t):
    """a pointer_t that's calculated via a user-provided function that takes an integer value as an argument"""
    _calculate_ = lambda s,x: x
    #__name__ = '[unnamed-opointer]'

    def shortname(self):
        return 'opointer_t(%s, %s)'%(self._object_.__name__, self._calculate_.__name__)

    def decode_offset(self):
        return self._calculate_(self.int())

setbyteorder(config.integer.byteorder)

import pbinary  # XXX: recursive. yay.

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

    if False:
        import pint
        class wr(ptype.wrapper_t):
            _object_ = pint.uint32_t

        x = wr(source=provider.string('\xde\xad\xde\xad\x00\x00\x00\x00'))
        x = x.l

    if False:
        import zlib,dyn,ptype,pint
        class zlib(ptype.encoded_t):
            _value_ = dyn.clone(ptype.block, length=512)
            _object_ = dyn.array(pint.uint32_t, 4)
            def decode(self, string):
                string = string.decode('zlib')
                res = self.newelement(self._object_, 'zlib-encoded', 0, source=provider.string(string))
                return res

            def encode(self, object):
                return object.serialize().encode('zlib')

        s = '\xde\xad\xde\xad'*4
        x = zlib(source=provider.string(s.encode('zlib')+'\x00'*500))
        x = x.l

    if False:
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

if __name__ == '__main__':
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
    import ptypes
    from ptypes import *

    @TestCase
    def test_wrapper_read():
        class wrap(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.block, length=0x10)

        s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        a = wrap(source=ptypes.prov.string(s))
        a = a.l
        if a.serialize() == 'ABCDEFGHIJKLMNOP':
            raise Success
        
    @TestCase
    def test_wrapper_write():
        class wrap(ptype.wrapper_t):
            _value_ = ptype.clone(ptype.block, length=0x10)

        s = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        a = wrap(source=ptypes.prov.string(s))
        a = a.l
        a.object[:0x10] = s[:0x10].lower()
        a.commit()

        if a.l.serialize() == 'abcdefghijklmnop':
            raise Success
    
    @TestCase
    def test_encoded_b64():
        s = 'AAAABBBBCCCCDDDD'.encode('base64').replace('\n','\x00') + 'A'*20
        class b64(ptype.encoded_t):
            _value_ = pstr.szstring
            _object_ = dyn.array(pint.uint32_t, 4)

            def encode(self, string):
                return string.encode('base64')

            def decode(self, string):
                return string.decode('base64')
                
        x = b64(source=ptypes.prov.string(s))
        x = x.l
        y = x.d.l
        if x.size() == 25 and y[0].serialize() == 'AAAA' and y[1].serialize() == 'BBBB' and y[2].serialize() == 'CCCC' and y[3].serialize() == 'DDDD':
            raise Success

    @TestCase
    def test_encoded_xorenc():
        k = 0x80
        s = ''.join(chr(ord(x)^k) for x in 'hello world')
        class xor(ptype.encoded_t):
            _value_ = dyn.block(len(s))
            _object_ = dyn.block(len(s))

            key = k

            def encode(self, string):
                return ''.join(chr(ord(x)^k) for x in string)
            def decode(self, string):
                return ''.join(chr(ord(x)^k) for x in string)
        
        x = xor(source=ptypes.prov.string(s))
        x = x.l
        if x.d.l.serialize() == 'hello world':
            raise Success

    @TestCase
    def test_shared_user_data_pointer():
        ptypes.setsource(ptypes.prov.memory())
        from ptypes import dyn,pint,pstruct
        from ptypes import pstr

        LONG,ULONG = pint.int32_t,pint.uint32_t
        WORD = pint.uint16_t
        WCHAR = pint.uint16_t
        UCHAR = pint.uint8_t
        UINT64 = pint.uint64_t

        class KSYSTEM_TIME(pstruct.type):
            _fields_ = [
                (ULONG, 'LowPart'),
                (LONG, 'High1Time'),
                (LONG, 'High2Time'),
            ]

        class NT_PRODUCT_TYPE(ULONG): pass
        class ALTERNATIVE_ARCHITECTURE_TYPE(pstruct.type):
            _fields_ = [(ULONG, 'something'),(ULONG,'pad')]
        class LARGE_INTEGER(pstruct.type):
            _fields_ = [    
                (ULONG, 'LowPart'),
                (LONG, 'HighPart'),
            ]

        class _XSTATE_FEATURE(pstruct.type):
            _fields_ = [(ULONG,'Offset'),(ULONG,'Size')]

        class _XSTATE_CONFIGURATION(pstruct.type):
            _fields_ = [
                (LONG, 'EnabledFeatures'),
                (ULONG, 'Size'),
                (ULONG, 'OptimizedSave'),
                (dyn.array(_XSTATE_FEATURE,64), 'Features'),
            ]

        class _KUSER_SHARED_DATA(pstruct.type):
            _fields_ = [
                (ULONG, 'TickCountLowDeprecated'),
                (ULONG, 'TickCountMultiplier'),
                (KSYSTEM_TIME, 'InterruptTime'),
                (KSYSTEM_TIME, 'SystemTime'),
                (KSYSTEM_TIME, 'TimeZoneBias'),
                (WORD, 'ImageNumberLow'),
                (WORD, 'ImageNumberHigh'),
                (dyn.clone(pstr.wstring, length=260), 'NtSystemRoot'),
                (ULONG, 'MaxStackTraceDepth'),
                (ULONG, 'CryptoExponent'),
                (ULONG, 'TimeZoneId'),
                (ULONG, 'LargePageMinimum'),
                (dyn.array(ULONG,7), 'Reserved2'),
                (NT_PRODUCT_TYPE, 'NtProductType'),
                (UCHAR, 'ProductTypeIsValid'),
                (ULONG, 'NtMajorVersion'),
                (ULONG, 'NtMinorVersion'),
                (dyn.array(UCHAR,64), 'ProcessorFeatures'),
                (ULONG, 'Reserved1'),
                (ULONG, 'Reserved3'),
                (ULONG, 'TimeSlip'),
                (ALTERNATIVE_ARCHITECTURE_TYPE, 'AlternativeArchitecture'),
                (LARGE_INTEGER, 'SystemExpirationDate'),
                (ULONG, 'SuiteMask'),
                (UCHAR, 'KdDebuggerEnabled'),
                (UCHAR, 'NXSupportPolicy'),
                (ULONG, 'ActiveConsoleId'),
                (ULONG, 'DismountCount'),
                (ULONG, 'ComPlusPackage'),
                (ULONG, 'LastSystemRITEventTickCount'),
                (ULONG, 'NumberOfPhysicalPages'),
                (UCHAR, 'SafeBootMode'),

                (UCHAR, 'TscQpcData'),
                (dyn.array(UCHAR,2), 'TscQpcPad'),
                (ULONG, 'SharedDataFlags'),
                (ULONG, 'DataFlagsPad'),
                (UINT64, 'TestRetInstruction'),
                (ULONG, 'SystemCall'),
                (ULONG, 'SystemCallReturn'),
                (dyn.array(ULONG,3), 'SystemCallPad'),
                (UINT64, 'TickCount')
            ]

        p = dyn.pointer(_KUSER_SHARED_DATA)
        KERNEL_BASE = 0x7fff0000
        z = p()
        z.set(KERNEL_BASE-0x10000)
        a = z.d.l['NtSystemRoot'].str()
        if 'windows' in a.lower():      # probably not the greatest test...
            raise Success

#    @TestCase
    def test_pecoff():
        # this test sucks, but whatever
        import pecoff,ctypes,sys
        v = sys.version_info
        a = ctypes.CDLL('python%d%d.dll'% (v.major,v.minor))._handle

        x = pecoff.Executable.File(offset=a)
        x=x.l
        if x['Pe']['Signature'].serialize() == 'PE\x00\x00':
            raise Success

    @TestCase
    def test_attributes_static_1():
        from ptypes import pint
        argh = pint.uint32_t

        x = argh(a1=5).a
        if 'a1' not in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_1():
        from ptypes import pint

        argh = pint.uint32_t

        x = argh(recurse={'a1':5}).a
        if 'a1' in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_2():
        from ptypes import pint,parray
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(a1=5).a
        if 'a1' not in x.attributes and 'a1' not in x.v[0].attributes and 'a1' not in dir(x.v[0]) and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_2():
        from ptypes import pint,parray
        global argh,x
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(recurse={'a1':5}).a
        if 'a1' in x.attributes and 'a1' in x.v[0].attributes and 'a1' in dir(x.v[0]) and x.v[0].a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_3():
        from ptypes import pint
        argh = pint.uint32_t

        x = argh().a
        x.update_attributes({'a2':5})
        if 'a2' not in x.attributes and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_3():
        from ptypes import pint

        argh = pint.uint32_t

        x = argh().a
        x.update_attributes(recurse={'a2':5})
        if 'a2' in x.attributes and x.a2 == 5:
            raise Success
    
    @TestCase
    def test_attributes_static_4():
        from ptypes import pint,parray
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.update_attributes({'a2':5})
        if 'a2' not in x.attributes and 'a2' not in x.v[0].attributes and 'a2' not in dir(x.v[0]) and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_4():
        from ptypes import pint,parray
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.update_attributes(recurse={'a2':5})
        if 'a2' in x.attributes and 'a2' in x.v[0].attributes and 'a2' in dir(x.v[0]) and x.v[0].a2 == 5:
            raise Success

    @TestCase
    def test_attributes_static_5():
        from ptypes import pint
        argh = pint.uint32_t

        a = argh(a1=5).a
        x = a.new(argh)
        if 'a1' not in a.attributes and 'a1' not in x.attributes and 'a1' not in dir(x):
            raise Success

    @TestCase
    def test_attributes_recurse_5():
        from ptypes import pint

        argh = pint.uint32_t

        a = argh(recurse={'a1':5}).a
        x = a.new(argh)
        if 'a1' in a.attributes and 'a1' in x.attributes and x.a1 == 5:
            raise Success

if __name__ == '__main__':
#    logging.root=logging.RootLogger(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

