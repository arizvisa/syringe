'''base ptype element'''
import sys,types,inspect,functools,itertools
from . import bitmap,provider,utils,config,error
Config = config.defaults

__all__ = 'istype,iscontainer,isrelated,type,container,undefined,block,definition,encoded_t,pointer_t,rpointer_t,opointer_t,boundary,debug,debugrecurse,clone,setbyteorder'.split(',')

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def iscallable(t):
    """True if type ``t`` is a code object that can be called"""
    return callable(t) and hasattr(t, '__call__')

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

    path = ','.join(self.backtrace())
    raise error.TypeError(self, 'force<ptype>', message='chain=%s : refusing request to resolve %s to a type that does not inherit from ptype.type : %s'% (repr(chain), repr(t), path))

# fn must be a method, so args[0] will fetch self
import traceback
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
            res.append('%s<%x:+??> %s =>'%(self.classname(),self.getoffset(), path))
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
            # FIXME: these exceptions look ugly as hell

        pass
    functools.update_wrapper(catch, fn)
    catch.__name__ = 'catching(%s)'% catch.__name__
    return catch

def debug(ptype):
    """``rethrow`` all exceptions that occur during initialization of ``ptype``"""
    if not istype(ptype):
        raise error.TypeError(ptype, 'debug', message='%s is not a ptype'% repr(ptype))

    # FIXME: when loading, display the current offset and position
    class decorated(ptype):
        __doc__ = ptype.__doc__
        @rethrow
        def deserialize_block(self, block):
            return super(decorated, self).deserialize_block(block)

        @rethrow
        def serialize(self):
            return super(decorated, self).serialize()

        @rethrow
        def load(self, **kwds):
#            print 'loading', self.classname(), self.name()
            return super(decorated, self).load(**kwds)

        @rethrow
        def commit(self, **kwds):
            return super(decorated, self).commit(**kwds)

    decorated.__name__ = 'debug(%s)'% ptype.__name__
    return decorated

def debugrecurse(ptype):
    """``rethrow`` all exceptions that occur during initialization of ``ptype`` and any sub-elements"""
    class decorated(debug(ptype)):
        __doc__ = ptype.__doc__
        @rethrow
        def new(self, t, **attrs):
            res = force(t, self)
#            print 'creating', self.classname(), self.name(), res

            if istype(res) or isinstance(res,type):
                debugres = debug(res)
                return super(decorated,self).new(debugres, **attrs)

            raise error.TypeError(self, 'debug(new)', message='%s is not a ptype class'% repr(res.__class__))

    decorated.__name__ = 'debugrecurse(%s)'% ptype.__name__
    return decorated

source = provider.memory()
class _base_generic(object):
    # XXX: this class should implement
    #           attribute inheritance
    #           addition and removal of elements to trie
    #           initial attribute creation
    #           attributes not propagated during creation

    __slots__ = ('__source','attributes','ignored','parent','value','position')

    # FIXME: it'd probably be a good idea to have this not depend on globals.source,
    #        and instead have globals.source depend on this. 
    __source = None      # ptype.prov
    @property
    def source(self):
        if self.parent is None:
            global source
            return source if self.__source is None else self.__source 
        if self.__source is None:
            return self.parent.source
        return self.__source
    @source.setter
    def source(self, value):
        self.__source = value

    attributes = None        # {...}
    ignored = set(('source','parent','attrs','value','__name__','offset','position'))

    parent = None       # ptype.base
    p = property(fget=lambda s: s.parent)   # abbr to get to .parent

    value = None        # _
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    def __init__(self, **attrs):
        """Create a new instance of object. Will assign provided named arguments to self.attributes"""
        self.attributes = {} if self.attributes is None else self.attributes
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

        Any attributes defined under the 'recurse' key will be propogated to any
        sub-elements.
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
        #recurse = dict(((k,v) for k,v in recurse.iteritems() if k not in ignored and not callable(v)))
        recurse = dict((k,v) for k,v in recurse.iteritems() if k not in ignored)

        # update self (for instantiated elements)
        self.attributes.update(recurse)

        # update sub-elements with recursive attributes
        if recurse and issubclass(self.__class__, container) and self.value is not None:
            for x in self.value:
                x.update_attributes(recurse=recurse)

        return self

    def properties(self):
        """Return a tuple of properties/characteristics describing the current state of the object to the user"""
        result = {}
        if not self.initializedQ():
            result['uninitialized'] = True
        if not hasattr(self, '__name__') or len(self.__name__) == 0:
            result['unnamed'] = True
        return result

    initialized = property(fget=lambda s: s.initializedQ())
    def initializedQ(self):
        raise error.ImplementationError(self, 'base.initializedQ')

    def __nonzero__(self):
        return self.initializedQ()

    def traverse(self, edges, filter=lambda node:True, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.
        """
        for self in edges(self, **kwds):
            if not isinstance(self, base):
                continue

            if filter(self):
                yield self

            for y in self.traverse(edges=edges, filter=filter, **kwds):
                yield y
            continue
        return

    def deserialize_block(self, block):
        raise error.ImplementationError(self, 'base.deserialize_block', message='Subclass %s must implement deserialize_block'% self.classname())
    def serialize(self):
        raise error.ImplementationError(self, 'base.serialize')

    def load(self, **attrs):
        raise error.ImplementationError(self, 'base.load')
    def commit(self, **attrs):
        raise error.ImplementationError(self, 'base.commit')
    def alloc(self, **attrs):
        raise error.ImplementationError(self, 'base.alloc')

    # abbreviations
    a = property(fget=lambda s: s.alloc())
    c = property(fget=lambda s: s.commit())
    l = property(fget=lambda s: s.load())

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        prop = '%s'% ','.join('%s=%s'%(k,repr(v)) for k,v in self.properties().iteritems())
        result = self.repr()

        # multiline
        if result.count('\n') > 0:
            if prop:
                return "%s '%s' {%s}\n%s"%(utils.repr_class(self.classname()),self.name(),prop,result)
            return "%s '%s'\n%s"%(utils.repr_class(self.classname()),self.name(),result)

        # single-line
        descr = "%s '%s'"%(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(),self.name())
        if prop:
            return "[%s] %s {%s} %s"%(utils.repr_position(self.getposition(), hex=Config.display.partial.hex, precision=3 if Config.display.partial.fractional else 0), descr, prop, result)
        return "[%s] %s %s"%(utils.repr_position(self.getposition(), hex=Config.display.partial.hex, precision=3 if Config.display.partial.fractional else 0), descr, result)

    # naming
    @classmethod
    def typename(cls):
        """Return the name of the ptype"""
        if Config.display.show_module_name and hasattr(cls, '__module__') and cls.__module__ is not None:
            return '%s.%s'%( cls.__module__, cls.__name__ )
        return cls.__name__
    def classname(self):
        """Return the dynamic classname. Can be overwritten."""
        return self.typename()
    def shortname(self):
        return getattr(self, '__name__', 'unnamed_x%x'%id(self))
    def name(self):
        """Return the loaded name of the instance"""
        name = self.shortname()
        if Config.display.show_parent_name and self.parent is not None:
            return '%s.%s'%( self.parent.name(), name )
        return name
    def instance(self):
        name,ofs = self.classname(),self.getoffset()
        try:
            bs = self.blocksize()
            return '%s[%x:+%x]'% (name, ofs, bs)
        except:
            pass
        return '%s[%x:+?]'% (name, ofs)
        #return '(%s)%s'%( self.classname(), self.name() )

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)

        Options can provide formatting specifiers
        terse -- display the hexdump tersely if larger than a specific threshold
        threshold -- maximum number of rows to display
        """
        if not self.initializedQ():
            raise error.InitializationError(self, 'base.hexdump')

        length = options.pop('length', Config.display.hexdump.width)
        ofs,bs,buf = self.getoffset(),self.blocksize(),self.serialize()
        #ofs,bs,buf = self.getoffset(),self.blocksize(),''.join((x.serialize() if x.initialized else '?'*x.blocksize()) for x in self.value)
        return utils.hexdump(buf, offset=ofs, length=length, **options)

    def details(self, **options):
        """Return details of the object. This can be displayed in multiple-lines."""
        if not self.initializedQ():
            return '???'

        length = options.pop('length', Config.display.hexdump.width)
        ofs,bs,buf = self.getoffset(),self.blocksize(),self.serialize()

        # if larger than threshold...
        threshold = options.pop('threshold', Config.display.threshold.details)
        message = options.pop('threshold_message', Config.display.threshold.details_message)
        if threshold > 0 and bs/length > threshold:
            return '\n'.join(utils.emit_hexrows(buf, threshold, message, width=length, **options))
        return utils.hexdump(buf, offset=ofs, length=length, **options)

    def summary(self, **options):
        """Return a summary of the object. This can be displayed on a single-line."""
        if not self.initializedQ():
            return '???'

        ofs,bs,buf = self.getoffset(),self.blocksize(),self.serialize()

        # if larger than threshold...
        threshold = options.get('threshold', Config.display.threshold.summary)
        message = options.pop('threshold_message', Config.display.threshold.summary_message)
        if threshold > 0 and bs > threshold:
            return '"{}"'.format(utils.emit_repr(buf, threshold, message, **options))
        return '"{}"'.format(utils.emit_repr(buf, **options))

    def repr(self, **options):
        """The output that __repr__ displays"""
        raise error.ImplementationError(self, 'base.repr')

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
            if isinstance(x,type) or issubclass(x.__class__,type):
                return x
            continue

        # XXX
        chain = ';'.join(utils.repr_instance(x.classname(),x.name()) for x in self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None)))
        raise error.NotFoundError(self, 'base.getparent', message="match %s not found in chain : %s[%x:+%x] : %s"%(type.typename(), self.classname(), self.getoffset(), self.blocksize(), chain))

    def backtrace(self, fn=lambda x:'<type:%s name:%s offset:%x>'%(x.classname(), x.name(), x.getoffset())):
        """
        Return a backtrace to the root element applying ``fn`` to each parent

        By default this returns a string describing the type and location of
        each structure.
        """
        path = self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None))
        path = [ fn(x) for x in path ]
        return list(reversed(path))

    def new(self, ptype, **attrs):
        """Create a new instance of ``ptype`` with the provided ``attrs``

        If any ``attrs`` are provided, this will assign them to the new instance.
        The newly created instance will inherit the current object's .source and
        any .attributes designated by the current instance.
        """
        offset = attrs.get('offset',0)
        res = force(ptype, self)

        if not(istype(res) or isinstance(res,type)):
            raise error.TypeError(self, 'base.new', message='%s is not a ptype class'% repr(res.__class__))

        if 'recurse' in attrs:
            attrs['recurse'].update(self.attributes)
        else:
            attrs['recurse'] = self.attributes

        attrs.setdefault('parent', self)

        # instantiate an instance if we're given a type
        assert istype(res) or isinstance(res,type), 'Type %s is not a ptype'% repr(res)
        if istype(res):
            res = res(**attrs)

        # update the instance's properties
        res.__name__ = attrs.get('__name__', hex(id(res)) )
        res.setposition((offset,))
        return res

    def get(self):
        """Return a representation of a type.

        This value should be able to be passed to .set
        """
        raise error.ImplementationError(self, 'base.get')

    def set(self, value, **attrs):
        """Set value of type to ``value``.
        
        Should be the same value as returned by .get
        """
        raise error.ImplementationError(self, 'base.set')

    def __eq__(self, other):
        return id(self) == id(other)
    def __ne__(self, other):
        return not(self == other)
    def __getstate__(self):
        return ()
    def __setstate__(self, state):
        return

class base(_base_generic):
    # FIXME: move all generic functions that are shared between type and
    #        container into this class.
    #        like methods that use only things like position,value,initialized
    #        or things unimplemented methods/metaclass-like stuff
    pass
    

class type(base):
    """The most atomical type.. all container types are composed of these.
    
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

    ## position
    def setoffset(self, ofs, **_):
        """Changes the current offset to ``ofs``"""
        return self.setposition((ofs,))
    def getoffset(self, **_):
        """Returns the current offset"""
        o, = self.getposition()
        return o
    offset = property(fget=getoffset, fset=setoffset)

    ## byte stream input/output
    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
        bs = self.blocksize()
        if len(block) < bs:
            self.value = block[:bs]
            raise StopIteration(self, len(block))

        # all is good.
        self.value = block[:bs]
        return self

    def serialize(self):
        """Return contents of type as a string"""
        ofs,bs = self.getoffset(),self.blocksize()
        if not self.initializedQ():
            Config.log.warn('type.serialize : %s : Uninitialized during serialization', self.instance())
            return utils.padding.fill(self.blocksize(), self.padding)

        result = str(self.value)
        if len(result) < bs:
            Config.log.info('type.serialize : %s : Partially initialized during serialization', self.instance())
            padding = utils.padding.fill(bs-len(result), self.padding)
            result += padding

        if len(result) != bs:
            raise StopIteration(self, len(result))
        return result

    ## set/get
    def set(self, value, **attrs):
        """Set entire type equal to ``value``"""
        if value.__class__ is not str:
            raise error.TypeError(self, 'type.set', message='type %s is not serialized data'% repr(value.__class__))
        last = self.value

        res = str(value)
        self.value = res
        self.length = len(res)
        return self

    def get(self):
        return self.serialize()

    ## reading/writing to provider
    def load(self, **attrs):
        """Synchronize the current instance with data from the .source attributes"""
        with utils.assign(self, **attrs):
            ofs,bs = self.getoffset(),self.blocksize()
            try:
                self.source.seek(ofs)
                block = self.source.consume(bs)
                self = self.deserialize_block(block)
            except (StopIteration,error.ProviderError), e:
                raise error.LoadError(self, consumed=bs, exception=e)
        return self
            
    def commit(self, **attrs):
        """Commit the current state back to the .source attribute"""
        try:
            with utils.assign(self, **attrs):
                ofs,data = self.getoffset(),self.serialize()
                self.source.seek(ofs)
                self.source.store(data)
            return self

        except (StopIteration,error.ProviderError), e:
            raise error.CommitError(self, exception=e)

    def alloc(self, **attrs):
        """Will zero the ptype instance with the provided ``attrs``.

        This can be overloaded in order to allocate space for the new ptype.
        """
        attrs.setdefault('source', provider.empty())
        return self.load(**attrs)

    ## size boundaries
    def size(self):
        """Returns the number of bytes that have been loaded into the type.

        If type is uninitialized, issue a warning and return 0.
        """
        if self.initializedQ() or self.value is not None:
            return len(self.value)
        Config.log.warn("type.size : %s : Unable to get size of ptype.type, as object is still uninitialized."% self.instance())
        return 0

    def blocksize(self):
        """Returns the expected size of the type
    
        By default this returns self.length, but can be overloaded to define the
        size of the type. This *must* return an integral type.
        """

        # XXX: overloading will always provide a side effect of modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something.
        return int(self.length)

    ## utils
    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def traverse(self, edges=lambda node:tuple(node.value) if iscontainer(node.__class__) else (), filter=lambda node:True, **kwds):
        """
        This will traverse a tree in a top-down approach.
    
        By default this will traverse every sub-element from a given object.
        """
        return super(type,self).traverse(edges, filter, **kwds)

    if False:
        def collect(self, filter=lambda node:True, **kwds):
            """Return all contiguous nodes in a trie"""
            edges = lambda node:tuple(node.value) if iscontainer(node.__class__) else ()
            encoded = lambda node: (node.d,) if isinstance(node, encoded_t) else ()
            for node in itertools.chain(self.traverse(edges, filter=filter, **kwds), self.traverse(encoded, filter=filter, **kwds)):
                parent = node.getparent(encoded_t)

    def collect(self, *args, **kwds):
        global encoded_t
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or isinstance(other, encoded_t) or issubclass(other.__class__, encoded_t)
        parentTester = parentTester()

        #edges = lambda node:tuple(node.value) if iscontainer(node.__class__) else ()
        #encoded = lambda node: (node.d,) if isinstance(node, encoded_t) else ()
        #itertools.chain(self.traverse(edges, filter=filter, *args, **kwds), self.traverse(encoded, filter=filter, *args, **kwds)):
        duplicates = set()
        if parentTester == self:
            yield self
            duplicates.add(self)
        for n in self.traverse(filter=lambda n: parentTester == n):
            if n.parent is None:
                if n not in duplicates:
                    yield n 
                    duplicates.add(n)
                continue
            try:
                result = n.d.l
            except Exception:
                continue
            if result not in duplicates:
                yield result
                duplicates.add(result)
            duplicates.add(result)
            for o in result.collect():
                result = o.getparent(parentTester)
                if result not in duplicates:
                    yield result
                    duplicates.add(result)
                continue
            continue
        return

    def copy(self, **kwds):
        """Return a duplicate instance of the current one."""
        name = kwds.pop('__name__', self.shortname())
        ofs = kwds.pop('offset', self.getoffset())
        result = self.new(self.__class__, __name__=name, offset=ofs, **kwds)
        return result.deserialize_block(self.serialize()) if self.initializedQ() else result

    def cast(self, t, **kwds):
        """Cast the contents of the current instance into a differing ptype"""
        kwds.setdefault('parent', self.parent)

        source = provider.string(self.serialize())
        result = self.new( t, offset=self.getoffset(), **kwds)

        try:
            result = result.load(source=source, offset=0)

            a,b = self.size(),result.size()
            if a > b:
                Config.log.info("type.cast : %s : Result %s size is smaller than source : %x < %x", self.classname(), result.classname(), result.size(), self.size())
            elif a < b:
                Config.log.warning("type.cast : %s : Result %s is partially initialized : %x > %x", self.classname(), result.classname(), result.size(), self.size())

        except Exception,e:
            Config.log.fatal("type.cast : %s : %s : Error during cast resulted in a partially initialized instance : %s"%(self.classname(), t.typename(), repr(e)))
        return result

    def compare(self, other):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self.serialize(),other.serialize()))
        """
        if False in (self.initializedQ(),other.initializedQ()):
            Config.log.fatal('type.compare : %s : Instance not initialized (%s)'% (self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        s,o = self.serialize(),other.serialize()
        if s == o:
            return

        comparison = [bool(ord(x)^ord(y)) for x,y in zip(s,o)]
        result = [(different,len(list(times))) for different,times in itertools.groupby(comparison)]
        index = 0
        for diff,length in result:
            #if diff: yield index,length
            if diff: yield index,(s[index:index+length],o[index:index+length])
            index += length

        if len(s) != len(o):
            #yield index,max(len(s),len(o))-index
            yield index,(s[index:],'') if len(s) > len(o) else ('',o[index:])
        return

    ## operator overloads
    def __cmp__(self, other):
        """Returns 0 if ``other`` represents the same data as ``self``

        To compare the actual contents, see .compare(other)
        """
        if self.initializedQ() != other.initializedQ():
            return -1
        if self.initializedQ():
            return 0 if (self.getoffset(),self.serialize()) == (other.getoffset(),other.serialize()) else -1
        return 0 if (self.getoffset(),self.blocksize()) == (other.getoffset(),other.blocksize()) else +1

    def repr(self, **options):
        """Display all ptype.type instances as a single-line hexstring"""
        return self.summary(**options)

    def __getstate__(self):
        return (super(type,self).__getstate__(),self.length,self.value,)
    def __setstate__(self, state):
        state,self.length,self.value = state
        super(type,self).__setstate__(state)

# FIXME: the common parts of type and container need to be put in a separate class
#        that way we don't inherit things from ptype.type like .length and such..
class container(type):
    '''
    This class is capable of containing other ptypes

    Readable properties:
        value:str<r>
            list of all elements that are being contained
    '''
    def initializedQ(self):
        """True if the type is fully initialized"""
        if self.value is None:
            return False
        return all(x is not None and x.initializedQ() for x in self.value)

    def size(self):
        """Returns a sum of the number of bytes that are currently in use by all sub-elements"""
        return reduce(lambda x,y: x+y.size(), self.value, 0)

    def blocksize(self):
        """Returns a sum of the bytes that are expected to be read"""
        return reduce(lambda x,y: x+y.blocksize(), self.value, 0)

    def getoffset(self, field=None):
        """Returns the current offset.

        If ``field`` is specified as a ``str``, return the offset of the
        sub-element with the provided name. If specified as a ``list`` or
        ``tuple``, descend into sub-elements using ``field`` as the path.
        """
        if field is None:
            return super(container,self).getoffset()

        if field.__class__ in (tuple,list):
            #name,res = (field[0], field[1:])
            name,res = (lambda hd,*tl:(hd,tl))(*field)
            return self[name].getoffset(res) if len(res) > 0 else self.getoffset(name)

        index = self.getindex(field)
        return self.getoffset() + reduce(lambda x,y: x+y, [ x.size() if x.initializedQ() else x.blocksize() for x in self.value[:index]], 0)

    def getindex(self, name):
        """Searches the .value attribute for an element with the provided ``name``

        This is intended to be overloaded by any type that inherits from
        ptype.container.
        """
        raise error.ImplementationError(self, 'container.getindex', 'Developer forgot to overload this method')

    def __getitem__(self, key):
        index = self.getindex(key)
        return self.value[index]

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        return any(x.contains(offset) for x in self.value)
    
    def at(self, offset, recurse=True, **kwds):
        """Returns element that contains the specified offset

        If ``recurse`` is True, then recursively descend into all sub-elements
        until an atomic type is encountered.
        """
        if not self.contains(offset):
            raise error.NotFoundError(self, 'container.at', 'offset 0x%x can not be located within container.'%offset)

        if not recurse:
            for n in self.value:
                if n.contains(offset):
                    return n
                continue
            raise error.NotFoundError(self, 'container.at', 'offset 0x%x not found in a child element. returning encompassing parent.'%offset)
    
        try:
            res = self.at(offset, False, **kwds)

        except ValueError, msg:
            Config.log.info('container.at : %s : Non-fatal exception raised : %s'% (self.instance(), repr(ValueError,msg)))
            return self

        # drill into containees for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (error.ImplementationError, AttributeError):
            pass

        return res
        
    def walkto(self, offset, **kwds):
        """Will return each element along the path to reach the requested ``offset``"""
        obj = self

        # drill into containees for more detail
        try:
            while True:
                yield obj
                obj = obj.at(offset, recurse=False, **kwds)
            assert False is True
        except (error.ImplementationError, AttributeError):
            pass
        return

    def setoffset(self, ofs, recurse=False):
        """Changes the current offset to ``ofs``

        If ``recurse`` is True, the update all offsets in sub-elements.
        """
        res = super(container, self).setoffset(ofs)
        if recurse:
            if self.value is None:  # if we're not initialized at all...
                raise error.InitializationError(self, 'container.setoffset')

            for n in self.value:
                n.setoffset(ofs, recurse=recurse)
                ofs += n.blocksize()
            pass
        return res

    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
        if self.value is None:
            raise error.SyntaxError(self, 'container.deserialize_block', message='caller is responsible for allocation of elements in self.value')

        total = 0
        ofs = self.getoffset()
        for n in self.value:
            bs = n.blocksize()
            n.setoffset(ofs)

            # if element in container is already initialized, skip
            data = block[:bs]
            if not n.initializedQ():
                n.deserialize_block(data)

            block = block[bs:]
            ofs += bs
            total += bs

        expected = self.blocksize()
        if total < expected:
            path = ' -> '.join(self.backtrace())
            Config.log.warn('container.deserialize_block : %s : Container less than expected blocksize : %x < %x : %s'%(self.instance(), total, expected, path))
        elif total > expected:
            path = ' -> '.join(self.backtrace())
            Config.log.debug('container.deserialize_block : %s : Container larger than expected blocksize : %x > %x : %s'%(self.instance(), total, expected, path))
        return self

    def serialize(self):
        """Return contents of all sub-elements concatenated as a string"""
        result = ''.join( (x.serialize() for x in self.value) )
        bs = self.blocksize()

        if len(result) < bs:
            padding = utils.padding.fill(bs-len(result), self.padding)
            return result + padding

        if len(result) > bs:
            Config.log.debug('container.serialize : %s : Container larger than expected blocksize : %x > %x'%(self.instance(), len(result), bs))
        return result

    def load(self, **attrs):
        """Allocate the current instance with data from the .source attributes"""
        if self.value is None and 'value' not in attrs:
            raise error.UserError(self, 'container.load', message='Parent must initialize self.value')

        try:
            result = super(container,self).load(**attrs)

        except error.LoadError, e:
            ofs,s,bs = self.getoffset(),self.size(),self.blocksize()
            if s < bs:
                Config.log.warning('container.load : %s : Unable to complete read : read {%x:+%x}', self.instance(), ofs, s)
            else:
                Config.log.debug('container.load : %s : Cropped to {%x:+%x}', self.instance(), ofs, s)
            return self
        return result

    def commit(self, **kwds):
        """Commit the current state of all children back to the .source attribute"""
        try:
            for n in self.value:
                n.commit(**kwds)
            return self

        except error.CommitError, e:
            raise error.CommitError(self, exception=e)

    def copy(self, **kwds):
        """Performs a deep-copy of self repopulating the new instance if self is initialized

        If a recurse=False is passed, a shallow-copy will be performed and an
        uninitialized object will be returned.
        """

        # create an instance of self and update with requested attributes
        result = self.new(self.__class__, __name__=self.classname(), offset=self.getoffset())
        kwds.setdefault('value', self.value)
        result.update_attributes(kwds)

        # reinitialize new object using contents of old object
        if self.initializedQ():
            return result.load(offset=0,source=provider.string(self.serialize()))
        return result

    def compare(self, other):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self,other))
        """
        if False in (self.initializedQ(),other.initializedQ()):
            Config.log.fatal('container.compare : %s : Instance not initialized (%s)'% (self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        if self.value == other.value:
            return

        def between(object,(left,right)):
            (left,right) = (left,right) if right > left else (right,left)
            l,r = object.at(left),object.at(right)
            li,ri = object.value.index(l),object.value.index(r)
            for i in xrange(li,ri):
                yield i
            return

        sofs,oofs=self.getoffset(),other.getoffset()
        for ofs,(s,o) in super(container,self).compare(other):
            if len(s) == 0:
                i = other.value.index(other.at(oofs+ofs))
                yield ofs, (None,tuple(other.value[i:]))
            elif len(o) == 0:
                i = self.value.index(self.at(sofs+ofs))
                yield ofs, (tuple(self.value[i:]), None)
            else:
                assert len(s) == len(o)
                length = len(s)
                s = (self.value[i] for i in between(self, (sofs+ofs,sofs+ofs+length)))
                o = (other.value[i] for i in between(other, (oofs+ofs,oofs+ofs+length)))
                yield ofs, (tuple(s), tuple(o))
            continue
        return

    def repr(self, **options):
        """Display all ptype.container types as a hexstring"""
        if self.initializedQ():
            return self.summary()
        if self.value is not None:
            #return ''.join((x.serialize() if x.initializedQ() else '?'*x.blocksize()) for x in self.value)
            return ''.join((x.serialize() if x.initializedQ() else '?'*x.blocksize()) for x in self.value)
        return '???'

    def append(self, object):
        """Add an element to a ptype.container. Return it's index."""
        current = len(self.value)
        self.value.append(object)
        return current

    def __iter__(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.__iter__')

        for res in self.value:
            yield res
        return

    def set(self, *elements):
        """Set ``self`` with instances or copies of the types provided in the iterable ``elements``.

        If uninitialized, this will make a copy of all the instances in ``elements`` and update the
        'parent' and 'source' attributes to match. All the offsets will be
        recursively updated.

        If initialized, this will pass the argument to .set using the current contents.

        This is an internal function and is not intended to be used outside of ptypes.
        """
        if self.initializedQ() and len(self.value) == len(elements):
            [x.set(v) for x,v in zip(self.value,elements)]
            self.setoffset(self.getoffset(), recurse=True)
            return self

        self.value = [x.copy(parent=self.parent) if isinstance(x,type) else self.new(x).a for x in elements]
        self.setoffset(self.getoffset(), recurse=True)
        return self

    def get(self):
        return [v.get() for v in self.value]

    def __getstate__(self):
        return (super(container,self).__getstate__(),self.source, self.attributes, self.ignored, self.parent, self.position)
    def __setstate__(self, state):
        state,self.source,self.attributes,self.ignored,self.parent,self.position = state
        super(container,self).__setstate__(state)

class undefined(type):
    """An empty ptype that is eternally undefined"""

class block(type):
    """A ptype that can be accessed as an array"""
    def classname(self):
        return 'block(%d)'% self.length
    def __getslice__(self, i, j):
        buffer = self.serialize()
        base = self.getoffset()
        return buffer[i-base:j-base]
    def __getitem__(self, index):
        buffer = self.serialize()
        base = self.getoffset()
        return buffer[index-base]
    def repr(self, **options):
        """Display all ptype.block instances as a hexdump"""
        if self.blocksize() > 0:
            return self.details(**options)
        return self.summary(**options)
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
    class __clone(cls):
        __doc__ = cls.__doc__

    #newattrs.setdefault('__name__', cls.__name__)
    #newattrs.setdefault('__name__', 'clone({:s})'.format(cls.__name__))
    newattrs.setdefault('__name__', Config.ptype.clone_name.format(cls.__name__))
    for k,v in newattrs.items():
        setattr(__clone, k, v)
    return __clone

class definition(object):
    """Used to store ptype definitions that are determined by a specific value

    This object should be used to simplify returning a ptype that is
    identified by a 'type' value which is commonly used in file formats
    that use a (type,length,value) tuple as their containers.

    To use this properly, in your definition file create a class that inherits
    from ptype.definition, and assign an empty dictionary to the `.cache`
    variable. The .attribute property defines which attribute to key the
    definition by. This defualts to 'type'

    Another thing to define is the `.unknown` variable. This will be the
    default type that is returned when an identifier is not located in the
    cache that was defined.

    i.e.
    class mytypelookup(ptype.definition):
        cache = {}
        unknown = ptype.block
        attribute = 'type'

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
    attribute = 'type'

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

        Returns cls.unknown with the provided ``unknownattrs`` if ``type`` is
        not found.
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
            Config.log.warn('definition.update : %s : Unable to import module %s due to multiple definitions of the same record',cls.__module__, repr(otherdefinition))
            Config.log.warn('definition.update : %s : Duplicate records : %s', cls.__module__, repr(a.intersection(b)))
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
        cls.add(getattr(type,cls.attribute), type)
        return type

# FIXME: it'd be cool if the .length of _value_ would be automatically figured out either by checking
#        .length or .blocksize() or something. maybe only if ._value_ is a ptype.type
class wrapper_t(type):
    '''This type represents a block that is defined by another ptype.

    Settable properties:
        _value_:ptype
            The type that the wrapper_t will use for it's backing.

    Readable properties:
        object:instance
            The object that the wrapper_t is using.
    '''
    _value_ = None
    @property
    def value(self):
        if not self.object.initializedQ():
            return None
        return self.object.serialize()
    # this setter shouldn't really ever be used...but...it's available.
    @value.setter
    def value(self, data):
        return self.object.load(source=provider.string(data))

    def __create_instance(self, name):
        return self.new(self._value_, __name__=name, offset=0, source=provider.proxy(self))
    def __copy_instance(self, instance):
        result = instance.copy()
        self._value_ = result.__class__
        return result

    __object = None
    @property
    def object(self):
        if self._value_ is None:
            raise error.UserError(self, 'wrapper_t.object', message='wrapper_t._value_ is undefined.')
        if (self.__object is None) or (self.__object.__class__ != self._value_):
            self.__object = self.__create_instance('wrapped_object<%s>'% self._value_.typename())
        return self.__object
    @object.setter
    def object(self, value):
        self.__object = self.__copy_instance(value)

    def initializedQ(self):
        return (self._value_ is not None) and (self.__object is not None) and (self.__object.initializedQ())

    def blocksize(self):
        if self.initializedQ():
            return self.__object.blocksize()
        if self._value_ is None:
            raise error.InitializationError(self, 'wrapper_t.blocksize')
        return self.new(self._value_, offset=self.getoffset(), source=self.source).blocksize()

    def deserialize_block(self, block):
        if self._value_ is None:
            self._value_ = clone(block, length=len(block))
        return self.alloc().object.deserialize_block(block)

    # forwarded methods 
    def load(self, **attrs):
        self.object.load(**attrs)
        return self

    def serialize(self):
        if self.initializedQ():
            return self.object.serialize()
        raise error.InitializationError(self, 'wrapper_t.serialize')
        
    def size(self):
        if self.initializedQ():
            return self.object.size()
        raise error.InitializationError(self, 'wrapper_t.size')

    def classname(self):
        if self.initializedQ():
            return '%s<%s>'% (self.typename(),self.object.classname())
        if self._value_ is None:
            return '%s<?>'% self.typename()
        return '%s<%s>'% (self.typename(),self._value_.typename())

    def contains(self, offset):
        left = self.getoffset()
        right = left + self.blocksize()
        return left <= offset < right

    def get(self):
        raise error.ImplementationError(self, 'wrapper_t.get')

    def set(self, value, **attrs):
        raise error.ImplementationError(self, 'wrapper_t.set')

    def __getstate__(self):
        return super(wrapper_t,self).__getstate__(),self._value_,self.__object

    def __setstate__(self, state):
        state,self._value_,self.__object = state
        super(wrapper_t,self).__setstate__(state)

class encoded_t(wrapper_t):
    ## string encoding (simulates ._object_)
    def encode(self, object):
        """Take object and serialize it to an encoded string"""
        return object.serialize()

    def decode(self, string):
        """Take a string and decode it into a ptype.block object"""
        return clone(block, length=len(string), source=provider.string(string))

    ## object dereferencing, force .object to match the length for the provided data
    def reference(self, object, **attrs):
        data = self.encode(object)
        self._value_ = clone(block, length=len(data))
        self.value = data
        return self

    def dereference(self, **attrs):
        if 'source' in attrs:
            Config.log.warn('encoded_t.decode : %s : User attempted to change the .source attribute of an encoded block', self.classname())
            del(attrs['source'])

        object = self.decode(self.value)
        return self.new(object, __name__='*%s'%self.shortname())

    d = property(fget=lambda s,**a: s.dereference(**a), fset=lambda s,*x,**a:s.reference(*x,**a))
    deref = lambda s,**a: s.dereference(**a)
    ref = lambda s,*x,**a: s.reference(*x,**a)

def setbyteorder(endianness):
    '''Sets the byte order for any pointer_t
    can be either .bigendian or .littleendian
    '''
    global pointer_t
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        pointer_t._value_.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness %s"% repr(endianness))

class pointer_t(encoded_t):
    _object_ = None

    class _value_(block):
        '''Default pointer value that can return an integer in any byteorder'''
        length,byteorder = Config.integer.size, Config.integer.order

        def set(self, offset):
            bs = self.blocksize()
            res = bitmap.new(offset, bs*8)
            return super(pointer_t._value_,self).set(bitmap.data(res, reversed=(self.byteorder is config.byteorder.littleendian)))

        def get(self):
            bs = self.blocksize()
            value = reversed(self.value) if self.byteorder is config.byteorder.littleendian else self.value
            res = reduce(lambda t,c: bitmap.push(t,(ord(c),8)), value, bitmap.zero)
            return bitmap.number(res)

    def dereference(self, **attrs):
        name = '*%s'% self.name()
        return self.new(self._object_, __name__=name, offset=self.decode_offset(), **attrs)

    def reference(self, object, **attrs):
        self._object_ = object.__class__
        self.set(object.getoffset())

        # make a child of current object
        object.parent = self
        return self

    def get(self):
        return self.object.get()

    def set(self, offset):
        """Sets the value of pointer to the specified offset"""
        return self.object.set(offset)

    def num(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'pointer_t.num')
        return self.object.get()

    def number(self):
        """Return the value of pointer as an integral"""
        return self.num()
    def int(self):
        return int(self.num())
    def long(self):
        return long(self.num())
    def decode_offset(self):
        """Returns an integer representing the resulting object's real offset"""
        return self.num()

    def classname(self):
        if self.initializedQ():
            return '%s<%s>'% (self.typename(),self.object.classname())
        targetname = force(self._object_, self).typename() if istype(self._object_) else getattr(self._object_, '__name__', 'None')
        return '%s<%s>'% (self.typename(),targetname)

    def summary(self, **options):
        if self.initializedQ():
            return '*0x%x'% self.num()
        return '*???'
    def repr(self, **options):
        """Display all pointer_t instances as an integer"""
        return self.summary(**options)
    def __getstate__(self):
        return super(pointer_t,self).__getstate__(),self._object_
    def __setstate__(self, state):
        state,self._object_ = state
        super(wrapper_t,self).__setstate__(state)

class rpointer_t(pointer_t):
    """a pointer_t that's at an offset relative to a specific object"""
    _baseobject_ = None

    def classname(self):
        if self.initializedQ():
            baseobject = self._baseobject_
            basename = baseobject.classname() if isinstance(self._baseobject_, base) else baseobject.__name__
            return '%s(%s, %s)'%(self.typename(), self.object.classname(), basename)

        objectname = force(self._object_,self).typename() if istype(self._object_) else self._object_.__name__
        return '%s(%s, ...)'%(self.typename(), objectname)

    def decode_offset(self):
        root = self._baseobject_
        base = root.getoffset() if isinstance(root,type) else root().getoffset()
        return base + self.num()

    def __getstate__(self):
        return super(rpointer_t,self).__getstate__(),self._baseobject_
    def __setstate__(self, state):
        state,self._baseobject_, = state
        super(rpointer_t,self).__setstate__(state)

class opointer_t(pointer_t):
    """a pointer_t that's calculated via a user-provided function that takes an integer value as an argument"""
    _calculate_ = lambda s,x: x

    def classname(self):
        calcname = self._calculate_.__name__
        if self.initializedQ():
            return '%s(%s, %s)'%(self.typename(), self.object.classname(), calcname)
        objectname = force(self._object_,self).typename() if istype(self._object_) else self._object_.__name__
        return '%s(%s, %s)'%(self.typename(), objectname, calcname)

    def decode_offset(self):
        return self._calculate_(self.num())

class boundary(base):
    """Used to mark a boundary in a ptype tree. Can be used to make .getparent() stop."""

class constant(type):
    """A ptype that uses .__doc__ to describe a string constant

    This will log a warning if the loaded data does not match the expected string.
    """
    length = property(fget=lambda s: len(s.__doc__),fset=lambda s,v:None)

    def __init__(self, **attrs):
        if self.__doc__ is None:
            Config.log.warn('constant.__init__ : %s : Constant was not initialized', self.classname())
            self.__doc__ = ''
        return super(constant,self).__init__(**attrs)

    def set(self, string):
        bs,data = self.blocksize(),self.__doc__

        if (data != string) or (bs != len(string)):
            Config.log.warn('constant.set : %s : Data did not match expected value : %s != %s', self.classname(), repr(string), repr(data))

        if len(string) < bs:
            self.value = string + utils.padding.fill(bs-len(string), self.padding)
            return self

        self.value = string[:bs]
        return self

    def deserialize_block(self, block):
        data = self.__doc__
        if data != block:
            Config.log.warn('constant.deserialize_block : %s : Data loaded from source did not match expected value. forced. : %s != %s', self.instance(), repr(block), repr(data))
        return super(constant,self).deserialize_block(data)

    def alloc(self, **attrs):
        """Allocate the ptype instance with requested string"""
        attrs.setdefault('source', provider.string(self.__doc__))
        return self.load(**attrs)

    def __getstate__(self):
        return super(constant,self).__getstate__(),self.__doc__
    def __setstate__(self, state):
        state,self.__doc__ = state
        super(constant,self).__setstate__(state)

from . import pbinary  # XXX: recursive. yay.

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
    def test_encoded_xorenc():
        k = 0x80
        s = ''.join(chr(ord(x)^k) for x in 'hello world')
        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(s))
            _object_ = dynamic.block(len(s))

            key = k

            def encode(self, object):
                return ''.join(chr(ord(x)^k) for x in object.serialize())
            def decode(self, string):
                data = ''.join(chr(ord(x)^k) for x in string)
                return dynamic.clone(self._object_, source=prov.string(data))
        
        x = xor(source=ptypes.prov.string(s))
        x = x.l
        if x.d.l.serialize() == 'hello world':
            raise Success

    @TestCase
    def test_decoded_xorenc():
        from ptypes import pstr

        k = 0x80
        data = 'hello world'
        match = ''.join(chr(ord(x)^k) for x in data)

        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(data))
            _object_ = dynamic.block(len(match))

            key = k

            def encode(self, object):
                return ''.join(chr(ord(x)^k) for x in object.serialize())
            def decode(self, string):
                data = ''.join(chr(ord(x)^k) for x in string)
                return dynamic.clone(self._object_, source=prov.string(data))

        instance = pstr.string().set(match)

        x = xor(source=ptypes.prov.string('\x00'*0x100)).l
        x = x.reference(instance)
        if x.serialize() == data:
            raise Success        

    @TestCase
    def test_encoded_b64():
        s = 'AAAABBBBCCCCDDDD'.encode('base64').strip() + '\x00' + 'A'*20
        class b64(ptype.encoded_t):
            _value_ = pstr.szstring
            _object_ = dynamic.array(pint.uint32_t, 4)

            def encode(self, object):
                return object.serialize().encode('base64')

            def decode(self, string):
                data = string.decode('base64')
                return dynamic.clone(self._object_, source=prov.string(data))
                
        x = b64(source=ptypes.prov.string(s))
        x = x.l
        y = x.d.l
        if x.size() == 25 and y[0].serialize() == 'AAAA' and y[1].serialize() == 'BBBB' and y[2].serialize() == 'CCCC' and y[3].serialize() == 'DDDD':
            raise Success

    @TestCase
    def test_decoded_b64():
        input = 'AAAABBBBCCCCDDDD\x00'
        result = 'AAAABBBBCCCCDDDD\x00'.encode('base64')

        class b64(ptype.encoded_t):
            _value_ = dynamic.block(len(result))
            _object_ = dynamic.array(pint.uint32_t, 4)

            def encode(self, object):
                return object.serialize().encode('base64')

            def decode(self, string):
                data = string.decode('base64')
                return dynamic.clone(self._object_, source=prov.string(data))

        instance = pstr.szstring().set(input)

        x = b64(source=ptypes.prov.string('A'*0x100+'\x00')).l
        x = x.reference(instance)
        if x.serialize() == result:
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

    @TestCase
    def test_constant_load_correct():
        data = "MARK"
        class placeholder(ptype.constant):
            __doc__ = data

        a = placeholder(source=provider.string(data))
        if a.l.serialize() == "MARK":
            raise Success

    @TestCase
    def test_constant_alloc_ignored():
        class placeholder(ptype.constant):
            """MARK"""

        a = placeholder(source=provider.random())
        if a.a.serialize() == "MARK":
            raise Success

    @TestCase
    def test_constant_load_ignored():
        class placeholder(ptype.constant):
            """MARK"""

        a = placeholder(source=provider.random())
        if a.l.serialize() == "MARK":
            raise Success

    @TestCase
    def test_constant_set_length():
        class placeholder(ptype.constant):
            """MARK"""

        a = placeholder(source=provider.random())
        a.set("ADFA")
        if a.serialize() == 'ADFA':
            raise Success

    @TestCase
    def test_constant_set_data():
        class placeholder(ptype.constant):
            """MARK"""

        a = placeholder(source=provider.random())
        a.set("ASDFASDF")
        if a.serialize() == "ASDF":
            raise Success

    @TestCase
    def test_constant_set():
        class placeholder(ptype.constant):
            """MARK"""

        a = placeholder(source=provider.random())
        a.set("MARK")
        if a.serialize() == "MARK":
            raise Success

    @TestCase
    def test_pointer_deref():
        from ptypes import pint
        data = '\x04\x00\x00\x00AAAA'

        a = ptype.pointer_t(source=prov.string(data), offset=0, _object_=pint.uint32_t)
        a = a.l
        b = a.dereference()
        if b.l.num() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref():
        from ptypes import pint,dyn
        src = prov.string('\x04\x00\x00\x00AAAAAAAA')
        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4)).l
        b = a.d.l
        assert b.serialize() == '\x41\x41\x41\x41'

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a = a.reference(c)
        if a.num() == c.getoffset() and a.d.l.num() == 0x42424242:
            raise Success

    @TestCase
    def test_type_cast_same():
        from ptypes import pint,dyn
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = pint.uint32_t

        data = prov.string('AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_container_cast_same():
        from ptypes import pint,dyn
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = dynamic.array(pint.uint8_t, 4)

        data = prov.string('AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_type_cast_diff_large_to_small():
        from ptypes import ptype
        t1 = ptype.clone(ptype.type, length=4)
        t2 = ptype.clone(ptype.type, length=2)
        data = prov.string('ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.serialize() == 'AB':
            raise Success

    @TestCase
    def test_type_cast_diff_small_to_large():
        from ptypes import ptype
        t1 = ptype.clone(ptype.type, length=2)
        t2 = ptype.clone(ptype.type, length=4)
        data = prov.string('ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.size() == b.size() and not b.initialized:
            raise Success

    @TestCase
    def test_container_cast_large_to_small():
        from ptypes import pint,dyn
        t1 = dynamic.array(pint.uint8_t, 8)
        t2 = dynamic.array(pint.uint8_t, 4)
        data = prov.string('ABCDEFGH')

        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and b.serialize() == 'ABCD':
            raise Success

    @TestCase
    def test_container_cast_small_to_large():
        from ptypes import pint,dyn
        t1 = dynamic.array(pint.uint8_t, 4)
        t2 = dynamic.array(pint.uint8_t, 8)
        data = prov.string('ABCDEFGH')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and not b.initialized and b.blocksize() == 8:
            raise Success

    @TestCase
    def test_type_copy():
        from ptypes import pint
        data = prov.string("WIQIWIQIWIQIWIQI")
        a = pint.uint32_t(source=data).a
        b = a.copy()
        if b.l.serialize() == a.l.serialize() and a is not b:
            raise Success

    @TestCase
    def test_container_copy():
        class leaf_sr(ptype.type):
            length = 4
        class leaf_jr(ptype.type):
            length = 2

        class branch(ptype.container): pass
            
        a = branch(source=prov.empty())
        a.set(leaf_sr, leaf_jr, branch().set(leaf_jr,leaf_jr,leaf_jr))
        b = a.copy()
        if b.v[2].v[1].size() == leaf_jr.length:
            raise Success

    # XXX: test casting between block types and stream types (szstring) as this
    #      might've been broken at some point...

    @TestCase
    def test_type_getoffset():
        class bah(ptype.type): length=2
        data = prov.string(map(chr,xrange(ord('a'),ord('z'))))
        a = bah(offset=0,source=data)
        if a.getoffset() == 0 and a.l.serialize()=='ab':
            raise Success

    @TestCase
    def test_type_setoffset():
        class bah(ptype.type): length=2
        data = prov.string(map(chr,xrange(ord('a'),ord('z'))))
        a = bah(offset=0,source=data)
        a.setoffset(20)
        if a.l.initializedQ() and a.getoffset() == 20 and a.serialize() == 'uv':
            raise Success

    @TestCase
    def test_container_setoffset_recurse():
        class bah(ptype.type): length=2
        class cont(ptype.container): getindex = lambda s,i: i
        a = cont()
        a.set(bah(), bah(), bah())
        a.setoffset(a.getoffset(), recurse=True)
        if tuple(x.getoffset() for x in a.value) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_field():
        class bah(ptype.type): length=2
        class cont(ptype.container): getindex = lambda s,i: i

        a = cont()
        a.set(bah(), bah(), bah())
        a.a
        if tuple(a.getoffset(i) for i in range(len(a.v))) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_iterable():
        class bah(ptype.type): length=2
        class cont(ptype.container): getindex = lambda s,i: i

        a = cont()
        a.set(bah(), bah(), bah())
        a.set(bah(), a.copy(), bah())
        a.setoffset(a.getoffset(), recurse=True)
        if a.getoffset((1,2)) == 6:
            raise Success

    @TestCase
    def test_decompression_block():
        from ptypes import dynamic,pint,pstruct,ptype
        class cblock(pstruct.type):
            class _zlibblock(ptype.encoded_t):
                def encode(self, object):
                    return object.serialize().encode('zlib')
                def decode(self, string):
                    return super(cblock._zlibblock,self).decode(string.decode('zlib'))

            def __zlibblock(self):
                return ptype.clone(self._zlibblock, _value_=dynamic.block(self['size'].l.int()))
                
            _fields_ = [
                (pint.uint32_t, 'size'),
                (__zlibblock, 'data'),
            ]
        message = 'hi there.'
        cmessage = message.encode('zlib')
        data = pint.uint32_t().set(len(cmessage)).serialize()+cmessage
        a = cblock(source=prov.string(data))            
        if a.l['data'].d.l.serialize() == message:
            raise Success

    @TestCase
    def test_compression_block():
        from ptypes import dynamic,pint,pstruct,ptype
        class zlibblock(ptype.encoded_t):
            def encode(self, object):
                return object.serialize().encode('zlib')
            def decode(self, string):
                return super(zlibblock,self).decode(string.decode('zlib'))

        class mymessage(ptype.block): pass
        message = 'hi there.'
        data = mymessage().set(message)

        source = prov.string('\x00'*1000)
        a = zlibblock(source=source).reference(data)
        if a.d.l.serialize() == message:
            raise Success

    @TestCase
    def test_equality_type_same():
        from ptypes import ptype,provider as prov
        class type1(ptype.type): length=4
        class type2(ptype.type): length=4
        data = 'ABCDEFGHIJKLMNOP'
        a = type1(source=prov.string(data)).l
        b = type2(source=prov.string(data), offset=a.getoffset()).l
        if cmp(a,b) == 0:
            raise Success
        
    @TestCase
    def test_equality_type_different():
        from ptypes import ptype,provider as prov
        class type1(ptype.type): length=4
        data = 'ABCDEFGHIJKLMNOP'
        a = type1(source=prov.string(data))
        b = a.copy(offset=1)
        c = a.copy().l
        d = c.copy().load(offset=1)
        if cmp(a,b) != 0 and cmp(c,d) != 0:
            raise Success

    @TestCase
    def test_compare_type():
        from ptypes import pstr,provider as prov
        a = pstr.string().set('this sentence is over the top!')
        b = pstr.string().set('this sentence is unpunctuaTed')
        getstr = lambda s,(i,(x,y)): s[i:i+len(x)].serialize()
        result = list(a.compare(b))
        c,d = result
        if getstr(a, c) == 'over the top' and getstr(b,c) == 'unpunctuaTed' and d[0] >= b.size() and getstr(a,d) == '!':
            raise Success

    @TestCase
    def test_compare_container_types():
        from ptypes import ptype,provider as prov,pint
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,b,c,d,e) )
        z.value.extend( (a,b,a,a,e) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset()+10, recurse=True)
        z.setoffset(z.getoffset(), recurse=True)

        result = dict(y.compare(z))
        if result.keys() == [2]:
            s,o = result[2]
            if c.serialize()+d.serialize() == ''.join(_.serialize() for _ in s) and a.serialize()+a.serialize() == ''.join(_.serialize() for _ in o):
                raise Success

    @TestCase
    def test_compare_container_sizes():
        from ptypes import ptype,provider as prov,pint
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)
        f = pint.uint8_t().set(120)
        g = pint.uint32_t().set(0xdead)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,g,f) )
        z.value.extend( (a,b,c,d,e,f) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset(), recurse=True)
        z.setoffset(z.getoffset()+0x1000, recurse=True)

        result = dict(y.compare(z))
        if result.keys() == [1]:
            s,o = tuple(reduce(lambda a,b:a+b,map(lambda x:x.serialize(),X),'') for X in result[1])
            if s == g.serialize() and o == ''.join(map(chr,(40,60,80,100))):
                raise Success

    @TestCase
    def test_compare_container_tail():
        from ptypes import ptype,provider as prov,pint
        a = pint.uint8_t().set(20)
        b = pint.uint8_t().set(40)
        c = pint.uint8_t().set(60)
        d = pint.uint8_t().set(80)
        e = pint.uint8_t().set(100)
        f = pint.uint8_t().set(120)
        g = pint.uint32_t().set(0xdead)

        y = ptype.container(value=[], __name__='y')
        z = ptype.container(value=[], __name__='z')
        y.value.extend( (a,b,c) )
        z.value.extend( (a,b,c,g,c.copy().set(0x40)) )
        y.value = [_.copy() for _ in y.value]
        z.value = [_.copy() for _ in z.value]
        y.setoffset(y.getoffset()+100, recurse=True)
        z.setoffset(z.getoffset()-0x1000, recurse=True)

        result = dict(y.compare(z))
        if result.keys() == [3]:
            s,o = result[3]
            if s is None and reduce(lambda a,b:a+b,map(lambda x:x.serialize(),o),'') == g.serialize()+'\x40':
                raise Success

    #@TestCase
    def test_collect_pointers():
        from ptypes import ptype,pint,provider
        ptype.source = provider.string(provider.random().consume(0x1000))
        a = pint.uint32_t
        b = ptype.clone(ptype.pointer_t, _object_=a)
        c = ptype.clone(ptype.pointer_t, _object_=b)
        d = ptype.clone(ptype.pointer_t, _object_=c)

        z = ptype.container(value=[], __name__='z')
        z.value.append(a())
        z.value.append(b())
        z.value.append(c())
        z.value.append(d())
        z.setoffset(z.getoffset(), True)

        a = z.value[0].set(0xfeeddead)
        b = z.value[1].set(a.getoffset())
        c = z.value[2].set(b.getoffset())
        d = z.value[3].set(c.getoffset())
        z.commit()

        result = [z.v[-1].num()]
        for x in z.v[-1].collect():
            result.append(x.l.num())

        if result == [8,4,0,0xfeeddead]:
            raise Success

    #@TestCase
    def test_collect_pointers2():
        import pecoff
        from ptypes import pint,ptype
        #a = pint.uint32_t()
        #b = a.new(ptype.pointer_t)
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or isinstance(other, ptype.encoded_t) or issubclass(other.__class__, ptype.encoded_t)
        parentTester = parentTester()
        #c = b.getparent(parentTester())
        #print isinstance(b, ptype.encoded_t)
        a = pecoff.Executable.open('c:/users/user/mshtml.dll')

        global result
        result = list(a.collect())
        for n in result:
            print n
        #for n in a.traverse(filter=lambda n: parentTester == n):
        #    if isinstance(n, ptype.encoded_t):
        #        b = n.d.getparent(parentTester)
        #        print b.l
        #        continue
        #    assert n.parent is None
        #    print n.l

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

