'''base ptype element'''
import sys,types,inspect,functools,itertools,__builtin__
from . import bitmap,provider,utils,config,error
Config = config.defaults

__all__ = 'istype,iscontainer,isrelated,type,container,undefined,block,definition,encoded_t,pointer_t,rpointer_t,opointer_t,boundary,debug,debugrecurse,clone,setbyteorder'.split(',')

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    # FIXME: also insure that it's not a class with these attributes
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def iscallable(t):
    """True if type ``t`` is a code object that can be called"""
    return callable(t) and hasattr(t, '__call__')

@utils.memoize('t')
def istype(t):
    """True if type ``t`` inherits from ptype.type"""
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, generic)

@utils.memoize('t')
def iscontainer(t):
    """True if type ``t`` inherits from ptype.container """
    return (istype(t) and issubclass(t, container)) or pbinary.istype(t)

@utils.memoize('t')
def isresolveable(t):
    """True if type ``t`` can be descended into"""
    return isinstance(t, (types.FunctionType, types.MethodType))    # or isiterator(t)

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
    if istype(t) or isinstance(t, base):
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
    raise error.TypeError(self, 'force<ptype>', message='chain=%r : refusing request to resolve %r to a type that does not inherit from ptype.type : {%s}'% (chain, t, path))

def debug(ptype, **attributes):
    """``rethrow`` all exceptions that occur during initialization of ``ptype``"""
    if not istype(ptype):
        raise error.UserError(ptype, 'debug', message='%r is not a ptype'% ptype)

    import time,traceback
    def logentry(string, *args):
        return (time.time(),traceback.extract_stack(), string.format(*args))

    if any((hasattr(n) for n in ('_debug_','_dump_'))):
        raise error.UserError(ptype, 'debug', message='%r has a private method name that clashes')

    class decorated_ptype(ptype):
        __doc__ = ptype.__doc__
        _debug_ = {}

        def __init__(self, *args, **kwds):
            self._debug_['creation'] = time.time(),traceback.extract_stack(),self.backtrace(lambda s:s)
            return super(decorated_ptype,self).__init__(*args,**kwds)

        def _dump_(self, file):
            dbg = self._debug_
            if 'constructed' in dbg:
                t,c = dbg['constructed']
                _,st,bt = dbg['creation']
                print >>file, "[{!r}] {:s} -> {:s} -> {:s}".format(t, c, self.instance(), self.__name__ if hasattr(self, '__name__') else '') 
            else:
                t,st,bt = dbg['creation']
                print >>file, "[{!r}] {:s} -> {:s} -> {:s}".format(t, self.typename(), self.instance(), self.__name__ if hasattr(self, '__name__') else '') 
            
            print >>file, 'Created by:'
            print >>file, format_stack(st)
            print >>file, 'Located at:'
            print >>file, '\n'.join('{:s} : {:s}'.format(x.instance(),x.name()) for x in bt)
            print >>file, 'Loads from store'
            print >>file, '\n'.join('[:d] [{:f}] {:s}'.format(i, t, string) for i,(t,_,string) in enumerate(dbg['load']))
            print >>file, 'Writes to store'
            print >>file, '\n'.join('[:d] [{:f}] {:s}'.format(i, t, string) for i,(t,_,string) in enumerate(dbg['commit']))
            print >>file, 'Serialized to a string:'
            print >>file, '\n'.join('[:d] [{:f}] {:s}'.format(i, t, string) for i,(t,_,string) in enumerate(dbg['serialize']))
            return

        def serialize(self):
            result = super(decorated, self).serialize()
            size = len(result)
            _ = logentry('serialize() -> __len__ -> 0x{:x}', self.instance(), len(size))
            Config.log.debug(' : '.join(self.instance(),_[-1]))
            self._debug_.setdefault('serialize',[]).append(_)
            return result

        def load(self, **kwds):
            start = time.time()
            result = super(decorated, self).load(**kwds)
            end = time.time()

            offset, size, source = self.getoffset(), self.blocksize(), self.source
            _ = logentry('load({:s}) {:f} seconds -> (offset=0x{:x},size=0x{:x}) -> source={!r}', ','.join('{:s}={!r}'%(k,v) for k,v in attrs.items()), end-start, offset, size, source)
            Config.log.debug(' : '.join(self.instance(),_[-1]))
            self._debug_.setdefault('load',[]).append(_)
            return result

        def commit(self, **kwds):
            start = time.time()
            result = super(decorated, self).commit(**kwds)
            end = time.time()

            _ = logentry('commit({:s}) {:f} seconds -> (offset=0x{:x},size=0x{:x}) -> source={!r}', ','.join('{:s}={!r}'%(k,v) for k,v in attrs.items()), end-start, offset, size, source)
            Config.log.debug(' : '.join(self.instance(),_[-1]))
            self._debug_.setdefault('commit',[]).append(_)
            return result

    decorated.__name__ = 'debug(%s)'% ptype.__name__
    decorated._debug_.update(attributes)
    return decorated

def debugrecurse(ptype):
    """``rethrow`` all exceptions that occur during initialization of ``ptype`` and any sub-elements"""
    import time,traceback
    class decorated(debug(ptype)):
        __doc__ = ptype.__doc__
        def new(self, t, **attrs):
            res = force(t, self)
            Config.log.debug(' '.join(('constructed :',repr(t),'->',self.classname(),self.name())))
            debugres = debug(res, constructed=(time.time(),t))
            return super(decorated,self).new(debugres, **attrs)
    decorated.__name__ = 'debug(%s,recurse=True)'% ptype.__name__
    return decorated

source = provider.memory()
class _base_generic(object):
    # XXX: this class should implement
    #           attribute inheritance
    #           addition and removal of elements to trie
    #           initial attribute creation
    #           attributes not propagated during creation
    #           XXX meta-related information
    #           instance tree navigation

    __slots__ = ('__source','attributes','ignored','parent','value','position')

    # FIXME: it'd probably be a good idea to have this not depend on globals.source,
    #        and instead have globals.source depend on this. 
    __source = None      # ptype.prov
    @property
    def source(self):
        if self.parent is None:
            global source
            return source if self.__source is None else self.__source 
        #if self.__source is None:
        return self.parent.source if self.__source is None else self.__source
        #return self.__source
    @source.setter
    def source(self, value):
        self.__source = value

    attributes = None        # {...}
    ignored = set(('source','parent','attributes','value','__name__','position'))

    parent = None       # ptype.base
    p = property(fget=lambda s: s.parent)   # abbr to get to .parent

    value = None        # _
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    def __init__(self, **attrs):
        """Create a new instance of object. Will assign provided named arguments to self.attributes"""
        self.attributes = {} if self.attributes is None else self.attributes
        self.update_attributes(attrs)

    def setposition(self, position, **kwds):
        self.position,res = position,self.position
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
        recurse = dict((k,v) for k,v in recurse.iteritems() if k not in ignored)

        # update self (for instantiated elements)
        self.attributes.update(recurse)

        # update sub-elements with recursive attributes
        if recurse and issubclass(self.__class__, container) and self.value is not None:
            for x in self.value: x.update_attributes(recurse=recurse)
        return self

    def properties(self):
        """Return a tuple of properties/characteristics describing the current state of the object to the user"""
        result = {}
        if not self.initializedQ():
            result['uninitialized'] = True
        if not hasattr(self, '__name__') or not self.__name__:
            result['unnamed'] = True
        return result

    def traverse(self, edges, filter=lambda node:True, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.
        """
        for self in edges(self, **kwds):
            if not isinstance(self, generic):
                continue

            if filter(self):
                yield self

            for y in self.traverse(edges=edges, filter=filter, **kwds):
                yield y
            continue
        return

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
        if hasattr(cls, '__module__') and cls.__module__ is not None:
            if Config.display.show_module_name:
                return '%s.%s'%( cls.__module__, cls.__name__ )
            return '%s.%s'%( cls.__module__.rsplit('.',1)[-1], cls.__name__ )
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
        """Returns a minimal string describing the type and it's location"""
        name,ofs = self.classname(),self.getoffset()
        try:
            bs = self.blocksize()
            return '%s[%x:+%x]'% (name, ofs, bs)
        except:
            pass
        return '%s[%x:+?]'% (name, ofs)

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)

        Options can provide formatting specifiers
        terse -- display the hexdump tersely if larger than a specific threshold
        threshold -- maximum number of rows to display
        """
        if not self.initializedQ():
            raise error.InitializationError(self, 'base.hexdump')

        options.setdefault('width', Config.display.hexdump.width)
        options.setdefault('offset', self.getoffset())
        return utils.hexdump(self.serialize(), **options)

    def details(self, **options):
        """Return details of the object. This can be displayed in multiple-lines."""
        if not self.initializedQ():
            return '???'

        length = options.setdefault('width', Config.display.hexdump.width)
        bs,buf = self.blocksize(),self.serialize()
        options.setdefault('offset',self.getoffset())

        # if larger than threshold...
        threshold = options.pop('threshold', Config.display.threshold.details)
        message = options.pop('threshold_message', Config.display.threshold.details_message)
        if threshold > 0 and bs/length > threshold:
            threshold = options.pop('height', threshold) # 'threshold' maps to 'height' for emit_repr
            return '\n'.join(utils.emit_hexrows(buf, threshold, message, **options))
        return utils.hexdump(buf, **options)

    def summary(self, **options):
        """Return a summary of the object. This can be displayed on a single-line."""
        if not self.initializedQ():
            return '???'

        bs,buf = self.blocksize(),self.serialize()
        options.setdefault('offset', self.getoffset())

        # if larger than threshold...
        threshold = options.pop('threshold', Config.display.threshold.summary)
        message = options.pop('threshold_message', Config.display.threshold.summary_message)
        if threshold > 0 and bs > threshold:
            threshold = options.pop('width', threshold) # 'threshold' maps to 'width' for emit_repr
            return '"{}"'.format(utils.emit_repr(buf, threshold, message, **options))
        return '"{}"'.format(utils.emit_repr(buf, **options))

    #@utils.memoize('self', self='parent', args=lambda n:n, kwds=lambda n:tuple(sorted(n.items())))
    @utils.memoize('self', self='parent', args=lambda n:(n[0],) if len(n) > 0 else (), kwds=lambda n:n.get('type',()))
    def getparent(self, *args, **kwds):
        """Returns the creator of the current type.

        If nothing is specified, return the parent element.

        If an argument is provided, return the element whose parent is the one
        specified.

        If the ``type`` argument is specified, recursively descend into .parent
        elements until encountering an instance that inherits from the one
        provided.
        """
        if len(args) == 0 and 'type' not in kwds:
            return self.parent

        t = args[0] if len(args) > 0 else kwds['type']

        if self.__class__ is t:
            return self

        #if self.__class__ == t or self is t or (isinstance(t,__builtin__.type) and (isinstance(self,t) or issubclass(self.__class__,t))):
        #    return self

        for x in self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None)):
            if x.parent is t or (isinstance(t,__builtin__.type) and (isinstance(x,t) or issubclass(x.__class__,t))):
                return x
            continue

        # XXX
        chain = ';'.join(utils.repr_instance(x.classname(),x.name()) for x in self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None)))
        try: bs = '%x'% self.blocksize()
        except: bs = '???'
        raise error.NotFoundError(self, 'base.getparent', message="match %s not found in chain : %s[%x:+%s] : %s"%(type.typename(), self.classname(), self.getoffset(), bs, chain))

    def backtrace(self, fn=lambda x:'<type:%s name:%s offset:%x>'%(x.classname(), x.name(), x.getoffset())):
        """
        Return a backtrace to the root element applying ``fn`` to each parent

        By default this returns a string describing the type and location of
        each structure.
        """
        path = self.traverse(edges=lambda node:(node.parent for x in range(1) if node.parent is not None))
        path = [ fn(x) for x in path ]
        return list(reversed(path))

    def new(self, t, **attrs):
        """Create a new instance of ``ptype`` with the provided ``attrs``

        If any ``attrs`` are provided, this will assign them to the new instance.
        The newly created instance will inherit the current object's .source and
        any .attributes designated by the current instance.
        """

        if 'recurse' in attrs:
            attrs['recurse'].update(self.attributes)
        else:
            attrs['recurse'] = self.attributes

        attrs.setdefault('parent', self)

        # instantiate an instance if we're given a type
        if not(istype(t) or isinstance(t,generic)):
            raise error.TypeError(self, 'base.new', message='%r is not a ptype class'% t.__class__)

        # if it's a type, then instantiate it
        if istype(t):
            t = t(**attrs)

        # if already instantiated, then update it's attributes
        elif isinstance(t,generic):
            t.update_attributes(**attrs)

        # give the instance a default name
        t.__name__ = attrs.get('__name__', hex(id(t)) )
        return t

class generic(_base_generic):
    '''A class shared between both pbinary.*, ptype.*'''
    initialized = property(fget=lambda s: s.initializedQ())

    def initializedQ(self):
        raise error.ImplementationError(self, 'base.initializedQ')
    def __eq__(self, other):
        return id(self) == id(other)
    def __ne__(self, other):
        return not(self == other)
    def __getstate__(self):
        return ()
    def __setstate__(self, state):
        return

    def repr(self, **options):
        """The output that __repr__ displays"""
        raise error.ImplementationError(self, 'base.repr')

    def deserialize_block(self, block):
        raise error.ImplementationError(self, 'base.deserialize_block', message='Subclass %s must implement deserialize_block'% self.classname())
    def serialize(self):
        raise error.ImplementationError(self, 'base.serialize')

    def load(self, **attrs):
        raise error.ImplementationError(self, 'base.load')
    def commit(self, **attrs):
        raise error.ImplementationError(self, 'base.commit')
    def alloc(self, **attrs):
        """Will zero the ptype instance with the provided ``attrs``.

        This can be overloaded in order to allocate space for the new ptype.
        """
        attrs.setdefault('source', provider.empty())
        return self.load(**attrs)

    # abbreviations
    a = property(fget=lambda s: s.alloc())  # alloc
    c = property(fget=lambda s: s.commit()) # commit
    l = property(fget=lambda s: s.load())   # load
    li = property(fget=lambda s: s.load() if not s.initializedQ() else s) # load if uninitialized

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

    def copy(self):
        """Return a new instance of self"""
        raise error.ImplementationError(self, 'base.copy')

    def __cmp__(self, other):
        """Returns 0 if ``other`` represents the same data as ``self``

        To compare the actual contents, see .compare(other)
        """
        if self.initializedQ() != other.initializedQ():
            return -1
        if self.initializedQ():
            return 0 if (self.getposition(),self.serialize()) == (other.getposition(),other.serialize()) else -1
        return 0 if (self.getposition(),self.blocksize()) == (other.getposition(),other.blocksize()) else +1

class base(generic):
    ignored = generic.ignored.union(('offset',))
    padding = utils.padding.source.zero()

    ## offset
    position = 0,
    offset = property(fget=lambda s: s.getoffset(), fset=lambda s,v: s.setoffset(v))
    def setoffset(self, offset, **_):
        """Changes the current offset to ``offset``"""
        return self.setposition((offset,), **_)
    def getoffset(self, **_):
        """Returns the current offset"""
        offset, = self.getposition(**_)
        return offset

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def copy(self, **attrs):
        """Return a duplicate instance of the current one."""
        result = self.new(self.__class__, __name__=self.classname(), position=self.getposition())
        result.update_attributes(attrs)
        return result.load(offset=0,source=provider.string(self.serialize()),blocksize=lambda:self.blocksize()) if self.initializedQ() else result

    def compare(self, other):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self.serialize(),other.serialize()))
        """
        if False in (self.initializedQ(),other.initializedQ()):
            Config.log.fatal('base.compare : %s : Instance not initialized (%s)'% (self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        s,o = self.serialize(),other.serialize()
        if s == o:
            return

        comparison = (bool(ord(x)^ord(y)) for x,y in zip(s,o))
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

    def cast(self, t, **kwds):
        """Cast the contents of the current instance into a differing ptype"""
        kwds.setdefault('parent', self.parent)
        kwds.setdefault('offset', self.getoffset())

        # disable propogating any attributes
        with utils.assign(self, attributes={}):
            result = self.new(t, **kwds)

        try:
            result = result.load(source=provider.proxy(self), offset=0)
            result.setoffset(result.getoffset(), recurse=True)
            result = result.deserialize_block(self.serialize())

        except Exception,e:
            Config.log.info("base.cast : %s : %s : Error during cast resulted in a partially initialized instance : %r"%(self.classname(), t.typename(), e))
            try: result = result.deserialize_block(self.serialize())
            except StopIteration: pass

        a,b = self.size(),result.size()
        if a > b:
            Config.log.info("base.cast : %s : Result %s size is smaller than source : %x < %x", self.classname(), result.classname(), result.size(), self.size())
        elif a < b:
            Config.log.warning("base.cast : %s : Result %s is partially initialized : %x > %x", self.classname(), result.classname(), result.size(), self.size())
        return result

    def traverse(self, edges=lambda node:tuple(node.value) if iscontainer(node.__class__) else (), filter=lambda node:True, **kwds):
        """
        This will traverse a tree in a top-down approach.
    
        By default this will traverse every sub-element from a given object.
        """
        return super(base,self).traverse(edges, filter, **kwds)

    def new(self, ptype, **attrs):
        res = force(ptype, self)
        return super(base,self).new(res, **attrs)

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
                ofs,data,bs = self.getoffset(),self.serialize(),self.blocksize()
                self.source.seek(ofs)
                self.source.store(data[:bs])
            return self

        except (StopIteration,error.ProviderError), e:
            raise error.CommitError(self, exception=e)

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
    ignored = generic.ignored.union(('length',))

    def copy(self, **attrs):
        attrs.setdefault('length',self.length)
        return super(type,self).copy(**attrs)

    def initializedQ(self):
        return True if self.value is not None and len(self.value) == self.blocksize() else False

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
            raise error.TypeError(self, 'type.set', message='type %r is not serialized data'% value.__class__)
        last = self.value

        res = str(value)
        self.value = res
        self.length = len(res)
        return self

    def get(self):
        return self.serialize()

    ## size boundaries
    def size(self):
        """Returns the number of bytes that have been loaded into the type.

        If type is uninitialized, issue a warning and return 0.
        """
        if self.initializedQ() or self.value:
            return len(self.value)
        Config.log.info("type.size : %s : Unable to get size of ptype.type, as object is still uninitialized."% self.instance())
        return 0

    def blocksize(self):
        """Returns the expected size of the type
    
        By default this returns self.length, but can be overloaded to define the
        size of the type. This *must* return an integral type.
        """

        # XXX: overloading will always provide a side effect o)f modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something.
        return self.length

    ## operator overloads
    def repr(self, **options):
        """Display all ptype.type instances as a single-line hexstring"""
        return self.summary(**options) if self.initializedQ() else '???'

    def __getstate__(self):
        return (super(type,self).__getstate__(),self.blocksize(),self.value,)
    def __setstate__(self, state):
        state,self.length,self.value = state
        super(type,self).__setstate__(state)

class container(base):
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
        return all(x is not None and x.initializedQ() for x in self.value) and self.size() >= self.blocksize()

    def size(self):
        """Returns a sum of the number of bytes that are currently in use by all sub-elements"""
        return sum(n.size() for n in self.value or [])

    def blocksize(self):
        """Returns a sum of the bytes that are expected to be read"""
        if self.value is None:
            raise error.InitializationError(self, 'container.blocksize')
        return sum(n.blocksize() for n in self.value)

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
        return self.getoffset() + sum(x.blocksize() for x in self.value[:index])

    def getindex(self, name):
        """Searches the .value attribute for an element with the provided ``name``

        This is intended to be overloaded by any type that inherits from
        ptype.container.
        """
        raise error.ImplementationError(self, 'container.getindex', 'Developer forgot to overload this method')

    def __getitem__(self, key):
        index = self.getindex(key)
        return self.value[index]

    def __setitem__(self, index, value):
        if not isinstance(value, base):
            raise error.TypeError(self, 'container.__setitem__',message='Cannot assign a non-ptype to an element of a container. Use .set instead.')
        offset = self.value[index].getoffset()
        value.setoffset(offset, recurse=True)
        value.parent,value.source = self,None
        self.value[index] = value
        return value

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
            Config.log.info('container.at : %s : Non-fatal exception raised : %r'% (self.instance(), ValueError(msg)))
            return self

        # drill into containees for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (error.ImplementationError, AttributeError):
            pass

        return res

    def field(self, offset, recurse=False):
        """Returns the field at the specified offset relative to the structure"""
        return self.at(self.getoffset()+offset, recurse=recurse)
        
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

    def setoffset(self, offset, recurse=False):
        """Changes the current offset to ``offset``

        If ``recurse`` is True, the update all offsets in sub-elements.
        """
        return self.setposition((offset,), recurse=recurse)

    def setposition(self, offset, recurse=False):
        offset, = offset
        res = super(container, self).setposition((offset,), recurse=recurse)
        if recurse and self.value is not None:
            for n in self.value:
                n.setposition((offset,), recurse=recurse)
                if n.initializedQ():
                    offset += n.blocksize()
                continue
            pass
        return res

    def deserialize_block(self, block):
        """Load type using the string provided by ``block``"""
        if self.value is None:
            raise error.SyntaxError(self, 'container.deserialize_block', message='caller is responsible for allocation of elements in self.value')

        ofs = self.getoffset()
        for n in self.value:
            bs = n.blocksize()
            n.setoffset(ofs),n.deserialize_block(block[:bs])
            block = block[bs:]
            ofs += bs

        expected,total = self.blocksize(),ofs-self.getoffset()
        if total < expected:
            path = ' -> '.join(self.backtrace())
            Config.log.warn('container.deserialize_block : %s : Container less than expected blocksize : %x < %x : {%s}'%(self.instance(), total, expected, path))
        elif total > expected:
            path = ' -> '.join(self.backtrace())
            Config.log.debug('container.deserialize_block : %s : Container larger than expected blocksize : %x > %x : {%s}'%(self.instance(), total, expected, path))
        return self

    def serialize(self):
        """Return contents of all sub-elements concatenated as a string"""
        #result = ''.join( (x.serialize() for x in self.value) )
        bs = self.blocksize()

        result = ''
        for x in self.value:
            result += x.serialize()
            if len(result) > bs:
                break
            continue

        if len(result) < bs:
            padding = utils.padding.fill(bs-len(result), self.padding)
            return result + padding

        if len(result) > bs:
            Config.log.debug('container.serialize : %s : Container larger than expected blocksize : %x > %x'%(self.instance(), len(result), bs))
        return result[:bs]

    def load(self, **attrs):
        """Allocate the current instance with data from the .source attributes"""
        if self.value is None and 'value' not in attrs:
            raise error.UserError(self, 'container.load', message='Parent must initialize self.value')

        try:
            # if any of the sub-elements are undefined, load each element separately
            if Config.ptype.noncontiguous and \
                    any(isinstance(n,container) or isinstance(n,undefined) for n in self.value):

                bs,sz = self.blocksize(),0
                val = list(self.value)
                while val and sz < bs:
                    sz += val.pop(0).load(**attrs).size()

                return self

            # otherwise the contents are contiguous, load them as so
            return super(container,self).load(**attrs)

        except error.LoadError, e:
            ofs,s,bs = self.getoffset(),self.size(),self.blocksize()
            if s < bs:
                Config.log.warning('container.load : %s : Unable to complete read : read {%x:+%x}', self.instance(), ofs, s)
            else:
                Config.log.debug('container.load : %s : Cropped to {%x:+%x}', self.instance(), ofs, s)
        return self

    def commit(self, **attrs):
        """Commit the current state of all children back to the .source attribute"""
        if not Config.ptype.noncontiguous and \
                all(not (isinstance(n,container) or isinstance(n,undefined)) for n in self.value):

            try:
                return super(container,self).commit(**attrs)
            except error.CommitError, e:
                ofs,bs = self.getoffset(),self.blocksize()
                Config.log.warning('container.commit : %s : Unable to complete contiguous store : write at {%x:+%x}', self.instance(), ofs, bs)

        # commit all elements of container individually
        with utils.assign(self, **attrs):
            try:
                sz,ofs,bs = 0,self.getoffset(),self.blocksize()
                for n in self.value:
                    n.commit()
                    sz += n.blocksize()
                    if sz > bs: break
            except error.CommitError, e:
                Config.log.fatal('container.commit : %s : Unable to complete noncontiguous store : write stopped at {%x:+%x}', self.instance(), ofs+sz, bs-sz)
        return self

    def copy(self, **attrs):
        """Performs a deep-copy of self repopulating the new instance if self is initialized
        """
        # create an instance of self and update with requested attributes
        if attrs.get('recurse', True):
            attrs.setdefault('value', map(operator.methodcaller('copy', **attrs),self.value) if iscontainer(self) else self.value)
        else:
            attrs.setdefault('value', self.value)
        return super(container,self).copy(**attrs)

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
                if len(s) != len(o):
                    raise error.AssertionError(self, 'container.compare', message='Invalid length between both objects : %x != %x'%(len(s), len(o)))
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
        threshold = options.pop('threshold', Config.display.threshold.summary)
        message = options.pop('threshold_message', Config.display.threshold.summary_message)
        if self.value is not None:
            res = ''.join((x.serialize() if x.initializedQ() else '?'*x.blocksize()) for x in self.value)
            return utils.emit_repr(res, threshold, message, **options)
        return '???'

    def append(self, object):
        """Add an element to a ptype.container. Return it's index."""
        if self.value is not None:
            current = len(self.value)
            self.value.append(object)
            return current
        self.value = []
        return self.append(object)

    def __len__(self):
        return len(self.value)

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
            for idx,(val,ele) in enumerate(zip(self.value,elements)):
                name = getattr(val,'__name__',None)
                if isresolveable(ele) or istype(ele):
                    self.value[idx] = self.new(ele, __name__=name).a
                elif isinstance(ele,generic):
                    self.value[idx] = self.new(ele, __name__=name) 
                else:
                    val.set(ele)
                continue
        elif all(isresolveable(x) or istype(x) or isinstance(x,generic) for x in elements):
            self.value = [ self.new(x) if isinstance(x,generic) else self.new(x).a for x in elements ]
        else:
            raise error.AssertionError(self, 'container.set', message='Invalid number or type of elements to assign with : {!r}'.format(elements))
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
    def size(self):
        return self.blocksize()
    def load(self, **attrs):
        self.value = ''
        return self
    def commit(self, **attrs):
        return self
    def initializedQ(self):
        return False if self.value is None else True
    def serialize(self):
        return self.value
        #return utils.padding.fill(self.blocksize(), self.padding)
    def summary(self, **options):
        return '...'
    def details(self, **options):
        return self.summary(**options)

class block(type):
    """A ptype that can be accessed as an array"""
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
        if not self.initializedQ():
            return '???'
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

#@utils.memoize('cls', newattrs=lambda n:tuple(sorted(n.iteritems())))
def clone(cls, **newattrs):
    '''
    will clone a class, and set its attributes to **newattrs
    intended to aid with single-line coding.
    '''
    class _clone(cls):
        __doc__ = cls.__doc__
        def classname(self):
            cn = super(_clone,self).classname()
            return Config.ptype.clone_name.format(cn, **(utils.attributes(self) if Config.display.mangle_with_attributes else {}))

    newattrs.setdefault('__name__', cls.__name__)
    if hasattr(cls, '__module__'):
        newattrs.setdefault('__module__', cls.__module__)
    for k,v in newattrs.items():
        setattr(_clone, k, v)
    return _clone

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
        """Search ``cls.cache`` for a ptype keyed by the specified value ``type``

        Raises a KeyError if unable to find the ``type`` in it's cache.
        """
        return cls.cache[type]

    @classmethod
    def contains(cls, type):
        return type in cls.cache

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
            Config.log.warn('definition.update : %s : Unable to import module %r due to multiple definitions of the same record',cls.__module__, otherdefinition)
            Config.log.warn('definition.update : %s : Duplicate records : %r', cls.__module__, a.intersection(b))
            return False

        # merge record caches into a single one
        cls.cache.update(otherdefinition.cache)
        return True

    @classmethod
    def copy(cls, otherdefinition):
        #assert issubclass(otherdefinition, cls), 'ptype.definition :%s is not inheriting from %s
        if not issubclass(otherdefinition, cls):
            raise error.AssertionError(cls, 'definition.copy', message='%s is not inheriting from %s'%(otherdefinition.__name__, cls.__name__))

        otherdefinition.cache = dict(cls.cache)
        otherdefinition.attribute = cls.attribute
        otherdefinition.unknown = cls.unknown
        return otherdefinition

    @classmethod
    def merge(cls, otherdefinition):
        """Merge contents of current ptype.definition with ``otherdefinition`` and update both with the resulting union"""
        if cls.update(otherdefinition):
            otherdefinition.cache = cls.cache
            return True
        return False

    @classmethod
    def define(cls, *definition, **attributes):
        """Add a definition to the cache keyed by the .type attribute of the definition. Return the original definition.

        If any ``attributes`` are defined, the definition is duplicated with the specified attributes before being added to the cache.
        """
        def clone(definition):
            res = dict(definition.__dict__)
            res.update(attributes)
            res = __builtin__.type(definition.__name__, definition.__bases__, res)
            cls.add(getattr(res,cls.attribute),res)
            return definition

        if attributes:
            assert len(definition) == 0, 'Unexpected positional arguments'
            return clone
        res, = definition
        cls.add(getattr(res,cls.attribute),res)
        return res

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
        if self.object.initializedQ():
            return self.__object.serialize()
        return None

    @value.setter
    def value(self, data):
        if self._value_ is None:
            self._value_ = clone(block, length=len(data))
        return self.object.load(source=provider.string(data), offset=0)

    __object = None
    @property
    def object(self):
        if self._value_ is None:
            raise error.UserError(self, 'wrapper_t.object', message='wrapper_t._value_ is undefined.')
        if (self.__object is None) or (self.__object.__class__ != self._value_):
            name = 'wrapped_object<%s>'% (self._value_.typename() if istype(self._value_) else self._value_.__name__)
            self.__object = self.new(self._value_, __name__=name, offset=0, source=provider.proxy(self))
        return self.__object
    @object.setter
    def object(self, value):
        name = 'wrapped_object<%s>'% value.name()
        self._value_ = value.__class__
        self.__object = value.copy(__name__=name, offset=0, source=provider.proxy(self), parent=self)

    def initializedQ(self):
        return self._value_ is not None and self.__object is not None and self.__object.initializedQ()

    def blocksize(self):
        if self.initializedQ():
            return self.__object.blocksize()
        if self._value_ is None:
            raise error.InitializationError(self, 'wrapper_t.blocksize')

        # if blocksize can't be calculated by loading (invalid deref)
        #   then guess the size using the unallocated version of the type
        res = self.new(self._value_, offset=self.getoffset(), source=self.source)
        try:
            bs = res.l.blocksize()
        except error.LoadError:
            bs = res.a.blocksize()
        return bs

    def deserialize_block(self, block):
        if self._value_ is None:
            self._value_ = clone(block, length=len(block))
        return self.alloc().__object.deserialize_block(block)

    # forwarded methods 
    def load(self, **attrs):
        self.object.load(**attrs)
        return super(wrapper_t,self).deserialize_block(self.value)

    def serialize(self):
        if self.initializedQ():
            return self.__object.serialize()
        raise error.InitializationError(self, 'wrapper_t.serialize')
        
    def size(self):
        if self.initializedQ():
            return self.__object.size()
        Config.log.info("wrapper_t.size : %s : Unable to get size of ptype.wrapper_t, as object is still uninitialized."% self.instance())
        return 0

    def classname(self):
        if self.initializedQ():
            return '%s<%s>'% (self.typename(),self.__object.classname())
        if self._value_ is None:
            return '%s<?>'% self.typename()
        return '%s<%s>'% (self.typename(),self._value_.typename() if istype(self._value_) else self._value_.__name__)

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

    def summary(self, **options):
        options.setdefault('offset',self.getoffset())
        return super(wrapper_t,self).summary(**options)
    def details(self, **options):
        options.setdefault(offset=self.getoffset())
        return super(wrapper_t,self).details(**options)

class encoded_t(wrapper_t):
    """This type represents an element that can be decoded/encoded to/from another element.

    To change the way a type is decoded, overload the .decode() method to return a new type from self.object
    To change the way a type is encoded to it, overwrite .encode() and return the type that self.object will become.

    _value_ = the original element type
    _object_ = the decoded element type

    .object = the actual element object represented by self
    """
    _value_ = None      # source type
    _object_ = None     # new type

    @utils.memoize('self', self=lambda n:(n._object_,n.value), attrs=lambda n:tuple(sorted(n.items())))
    def decode(self, **attrs):
        """Take self and decode it into self._object_

        To overload, return an instance of the new type.
        Default method will instantiate a self._object_ based on self.object
        """
        attrs.setdefault('source', provider.string(self.value))
        attrs.setdefault('offset', 0)
        return self.new(self._object_, **attrs)

    def encode(self, object, **attrs):
        """Take object and convert it to an encoded string"""
        return object.serialize()

    def dereference(self, **attrs):
        """Dereference object into the target type specified by self._object_"""
        attrs.setdefault('__name__', '*'+self.name())
        return self.decode(**attrs)

    def reference(self, object, **attrs):
        """Reference ``object`` and encode it into self"""
        self._object_ = object.__class__
        self.value = self.encode(object, **attrs)
        return self

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
    raise ValueError("Unknown integer endianness %r"% endianness)

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

    @utils.memoize('self', self=lambda n:(n.source, n._object_, n.decode_offset()), attrs=lambda n:tuple(sorted(n.items())))
    def decode(self, **attrs):
        attrs.setdefault('source', self.source)
        attrs.setdefault('offset', self.decode_offset())
        return super(pointer_t,self).decode(**attrs)

    def encode(self, object, **attrs):
        self.object.set( object.getoffset() )
        return super(pointer_t,self).encode(self.object, **attrs)

    def get(self):
        return self.object.get()

    def set(self, offset):
        """Sets the value of pointer to the specified offset"""
        return self.object.set(offset)

    def number(self):
        """Return the value of pointer as an integral"""
        return self.object.get()
    num = number

    def int(self):
        return int(self.num())
    def long(self):
        return long(self.num())
    def decode_offset(self):
        """Returns an integer representing the resulting object's real offset"""
        return self.object.get()

    def classname(self):
        targetname = force(self._object_, self).typename() if istype(self._object_) else getattr(self._object_, '__name__', 'None')
        return '%s<%s>'% (self.typename(),targetname)

    def summary(self, **options):
        return '*0x%x'% self.num()

    def repr(self, **options):
        """Display all pointer_t instances as an integer"""
        return self.summary(**options) if self.initializedQ() else '*???'
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
        base = root.getoffset() if isinstance(root,generic) else root().getoffset()
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
            Config.log.warn('constant.set : %s : Data did not match expected value : %r != %r', self.classname(), string, data)

        if len(string) < bs:
            self.value = string + utils.padding.fill(bs-len(string), self.padding)
            return self

        self.value = string[:bs]
        return self

    def deserialize_block(self, block):
        data = self.__doc__
        if data != block:
            Config.log.warn('constant.deserialize_block : %s : Data loaded from source did not match expected value. forced. : %r != %r', self.instance(), block, data)
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
                raise Failure
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
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

            def encode(self, object, **attrs):
                data = ''.join(chr(ord(x)^k) for x in object.serialize())
                return super(xor,self).encode(object, source=prov.string(data))
            def decode(self, **attrs):
                data = ''.join(chr(ord(x)^k) for x in self.object.serialize())
                return super(xor,self).decode(source=prov.string(data))
        
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

            def encode(self, object, **attrs):
                data = ''.join(chr(ord(x)^k) for x in object.serialize())
                return data
            def decode(self, **attrs):
                data = ''.join(chr(ord(x)^k) for x in self.object.serialize())
                return super(xor,self).decode(source=prov.string(data))

        instance = pstr.string().set(match)

        x = xor(source=ptypes.prov.string('\x00'*0x100)).l
        x.object = instance
        x = x.reference(instance)
        if x.serialize() == data:
            raise Success        

    @TestCase
    def test_encoded_b64():
        s = 'AAAABBBBCCCCDDDD'.encode('base64').strip() + '\x00' + 'A'*20
        class b64(ptype.encoded_t):
            _value_ = pstr.szstring
            _object_ = dynamic.array(pint.uint32_t, 4)

            def encode(self, object, **attrs):
                data = object.serialize().encode('base64')
                return super(b64,self).encode(object, source=prov.string(data))

            def decode(self, **attrs):
                data = self.object.serialize().decode('base64')
                return super(b64,self).decode(source=prov.string(data))
                
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

            def encode(self, object, **attrs):
                data = object.serialize().encode('base64')
                return data

            def decode(self, **attrs):
                data = self.object.serialize().decode('base64')
                return super(b64,self).decode(source=prov.string(data))

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
        a.set(bah().a, bah().a, bah().a)
        a.setoffset(a.getoffset(), recurse=True)
        if tuple(x.getoffset() for x in a.value) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_field():
        class bah(ptype.type): length=2
        class cont(ptype.container): getindex = lambda s,i: i

        a = cont()
        a.set(bah().a, bah().a, bah().a)
        if tuple(a.getoffset(i) for i in range(len(a.v))) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_iterable():
        class bah(ptype.type): length=2
        class cont(ptype.container): getindex = lambda s,i: i

        a,b = cont(),cont()
        a.set(bah,bah,bah)
        b.set(bah,bah,bah)
        a.set(bah, b.copy(), bah)
        a.setoffset(a.getoffset(), recurse=True)
        if a.getoffset((1,2)) == 6:
            raise Success

    @TestCase
    def test_decompression_block():
        from ptypes import dynamic,pint,pstruct,ptype
        class cblock(pstruct.type):
            class _zlibblock(ptype.encoded_t):
                _object_ = ptype.block
                def encode(self, object, **attrs):
                    data = object.serialize().encode('zlib')
                    return data
                def decode(self, **attrs):
                    data = self.object.serialize().decode('zlib')
                    attrs['blocksize'] = lambda:len(data)
                    return super(cblock._zlibblock,self).decode(source=prov.string(data), **attrs)

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
            def encode(self, object, **attrs):
                data = object.serialize().encode('zlib')
                return data
            def decode(self, **attrs):
                data = self.object.serialize().decode('zlib')
                return super(zlibblock,self).decode(source=prov.string(data), length=len(data))

        class mymessage(ptype.block): pass
        message = 'hi there.'
        data = mymessage().set(message)

        source = prov.string('\x00'*1000)
        a = zlibblock(source=source)
        a = a.reference(data)
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
    @TestCase
    def test_container_set_uninitialized_type():
        from ptypes import ptype,pint,provider
        class container(ptype.container): pass
        a = container().set(pint.uint32_t,pint.uint32_t)
        if a.size() == 8:
            raise Success

    @TestCase
    def test_container_set_uninitialized_instance():
        from ptypes import ptype,pint,provider
        class container(ptype.container): pass
        a = container().set(*(pint.uint8_t().set(1) for _ in range(10)))
        if sum(x.num() for x in a) == 10:
            raise Success

    @TestCase
    def test_container_set_initialized_value():
        from ptypes import ptype,pint,provider
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(4,4,4,4)
        if sum(x.num() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_type():
        from ptypes import ptype,pint,provider
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(pint.uint32_t,pint.uint32_t,pint.uint32_t,pint.uint32_t)
        if sum(x.size() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_instance():
        from ptypes import ptype,pint,provider
        class container(ptype.container): pass
        a = container().set(pint.uint8_t,pint.uint32_t)
        a.set(pint.uint32_t().set(0xfeeddead), pint.uint8_t().set(0x42))
        if (a.v[0].size(),a.v[0].num()) == (4,0xfeeddead) and (a.v[1].size(),a.v[1].num()) == (1,0x42):
            raise Success

    @TestCase
    def test_container_set_invalid():
        from ptypes import ptype,pint,provider,error
        class container(ptype.container): pass
        a = container().set(ptype.type,ptype.type)
        try: a.set(5,10,20)
        except error.AssertionError,e:
            raise Success
        raise Failure

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
        a = pecoff.Executable.open('~/mshtml.dll')

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

