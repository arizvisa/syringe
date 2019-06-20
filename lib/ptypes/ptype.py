"""Core primitives used by all ptypes.

All programs are based on various types of complex data structures. Ptypes aims
to be able to describe these data structures and assist a user with creating and
navigating through these structures. In order to do this, a ptype is used to
describe the different types within aa structure. Ptypes are composed of two basic
types of structures. One of which is an atomic type, or rather a ptype.type, and
another which is a container type, or rather a ptype.container.

Both of these types provide a number of methods for determining the relationships
between the different fields in a complex data structure. Each of these methods
are responsible for loading or storing data to a ptypes.provider or exploring
and shifting the bounds of each component of the structure. The basic methods
that define the boundaries of each type are as follows:

    def setoffset(self, offset):
        '''Change the offset of ``self`` to ``offset``'''
    def getoffset(self):
        '''Return the current offset of ``self``'''
    def blocksize(self):
        '''Return the expected size of ``self``'''
    def size(self):
        '''Return the actual size of ``self``'''
    def contains(self, offset):
        '''Returns True if ``offset`` is contained within the bounds of ``self``.'''

    .offset -- offset of ptype

Another aspect of each type is their state and position relative to other types.
These can be discovered by the following methods and properties:

    def initializedQ(self):
        '''Returns True or False based on whether or not ``self`` is initialized.'''
    def serialize(self):
        '''Return ``self`` serialized to byte-form'''
    def field(self, offset):
        '''Return the sub-element at the given ``offset`` relative to the beginning of ``self``'''
    def at(self, offset):
        '''Return the sub-element at the given ``offset``.'''
    def getparent(self, type):
        '''Traverse upwards looking for a parent type of the specified ``type``'''
    def traverse(self, edges, filter):
        '''A generator that can be used to navigate through ``self``'''

    .parent -- Return the parent instance
    .value -- Return the value of the instance

Each instance has various methods that are used for managing the state of a
of an instance and how it may modify the attributes of another given instance.
In order to assist with dynamic contruction and modification of attributes, most
of these methods contain keyword arguments. These keyword arguments are exposed
to the user in that they allow one to apply them to the newly constructed type or
instance returned by a method by modifying it's result's attributes. Another
aspect of these keyword arguments is a specific keyword, 'recurse',
modify the attributes of any sub-elements of the specific instance. The 'recurse'
keyword will be used whenever an instance creates a sub-element via the .new()
method and allows a user to customize the attributes of an instance or any
instances created by that instance.

Example:
# return a type where type.attr1 == value, and type.method() returns 'result'
    def method(self, **attrs): return type
    type = self.method(attr1=value, method1=lambda:result)
    assert type.attr1 == value and type().method() == result

# return an instance where instance.attr1 == value, and instance.method1() returns result.
    def method(self, **attrs): return instance
    instance = self.method(attr1=value, method1=lambda s: True)
    assert instance.attr1 == value and instance.method1() == True

# return an instance where any elements spawned by `self` have their attr1 set to True.
    def method(self, **attrs): return instance
    instance = self.method(recurse={'attr1':True})
    assert instance.new(type).attr1 == True

The .load and .commit methods have their ``attrs`` applied temporarily whilst
loading/committing the ptype from it's source. The other methods that implement
this style of keyword-attribute updating are as follows:

    def new(self, type, **attrs):
        '''Create an instance of ``type`` with the specified ``attrs`` applied.'''
    def cast(self, type, **attrs):
        '''Cast ``self`` to ``type`` with the specified ``attrs`` applied.'''
    def copy(self, **attrs):
        '''Return a copy of self with the value of ``attrs`` applied to it's attributes'''
    def load(self, **attrs):
        '''Initialize ``self`` with the contents of the provider.'''
    def commit(self, **attrs):
        '''Commit the contents of ``self`` to the provider.'''
    def alloc(self, **attrs):
        '''Initialize ``self`` with '\\x00' bytes.'''

To shorten the user from having to type a few very common methods, each ptype
has some aliases that point directly to methods. A list of these aliases are:

    instance.v -- alias to instance.value
    instance.p -- parent element of instance
    instance.a -- re-allocate instance with zeroes
    instance.c -- commit to default source
    instance.l -- load from default source
    instance.li -- load if uninitialized from default source
    instance.d -- dereference from instance
    instance.ref -- reference object to instance

A ptype.type interface is considered the base atomic type of the complex data
structure, and contains only one propery..it's length. The .length property affects
the result returned from the .blocksize() method. A ptype.type has the following
interface:

    class interface(ptype.type):
        length = size-of-ptype
        source = provider-of-data

        def set(self, value):
            '''Sets the contents of ``self`` to ``value``'''
        def get(self):
            '''Returns the value of ``self`` to a value that can be assigned to /.set/'''
        def summary(self):
            '''Returns a single-line description of ``self``'''
        def details(self):
            '''Returns a multi-line description of ``self``'''
        def repr(self):
            '''Returns the default description of ``self``'''

A ptype.container interface is a basic type that contains other ptype instances.
This type is intended to be a base type for other more complex types. Some of
the methods that it provides are:

    class interface(ptype.container):
        def __getitem__(self, key):
            '''Return the instance identified by ``key``.'''
        def __setitem__(self, index, value):
            '''Assign ``value`` to index ``index`` of ``self``.'''
        def append(self, object):
            '''Appends ``object`` to the end of the ``self`` container.'''
        def set(self, *iterable):
            '''Changes ``self`` to the values specified in ``iterable``'''
        def get(self):
            '''Return an iterable that can be passed to /.set/''''

Within this module, some primitive types are provided that a user can include
within their definition of a complex data structure. These types are:

    constant -- A type that's always a constant value. This constant value comes
                from it's __doc__ definition.

    boundary -- A "marker" that can be applied to a type so that .getparent can
                be used to fetch it.

    block -- A type that defines a block of unknown data. The .length property
             specifies it's bytesize.

    undefined -- A type that defines undefined data. It's .length specifies the
                 size. This type is used when a user doesn't know or care about
                 the type.

There are certain complex-structures that contain a field that is used to refer
to another part or different field. To dereference a pointer, one simply has to
call the .dereference (or .deref) method to return the new instance. If one wants
to assign a reference to an object to the pointer, one may call .reference with
the ptype as it's argument. In order to expose these various pointer types, this
moduel contains the following types:

    pointer_t -- A integral type that points to another type. The target type is
                 defined by the ._object_ attribute.

    rpointer_t -- A integral type that points to another type relative to another
                  object. Similar to pointer_t.

    opointer_t -- A integral type that is used to calculate the offset to another
                  instance. Similar to pointer_t.

    setbyteorder -- A function that is used to set the default byteorder of all
                    the pointer_t. Can use the values defined in config.byteorder.

Some other utility types provided by this module are the following:

    wrapper_t -- A type that wraps an alternative type. Any loads or commits
                 made to/from this type will use the contents of the alternative type.

    encoded_t -- A type that allows the user to encode/decode the data before
                 loading or committing.

    definition -- A utility class that allows one to look up a particular type
                  by an identifier.

One aspect of ptypes that would be prudent to describe is that during any
instance a user is allowed to specify a type, one can include a closure. This
closure takes one argument which is the ``self`` instance. From this closure,
a user can figure which type to return at which point ptypes will instantiate
the returned type.

Example core usage:
# define a ptype that's 8 bytes in length
    from ptypes import ptype
    class type(ptype.type):
        length = 8

# instantiate a ptype using a different source
    from ptypes import provider
    instance = type(source=provider.example)

# instantiate a ptype at the specified offset
    instance = type(offset=57005)

# move an instance to the specified offset
    instance.setoffset(57005)

# fetch the parent of a given instance
    parent = instance.getparent()

# determine the instance at the specified offset of instance
    subinstance = instance.at(57005, recurse=True)

Example pointer_t usage:
# define a pointer to a uint32_t
    from ptypes import ptype, pint
    class type(ptype.pointer_t):
        _object_ = pint.uint32_t

# define a pointer relative to the parent object
    from ptypes import ptype, pint
    class type(ptype.rpointer_t):
        _object_ = pint.uint32_t
        _baseobject_ = rootobject

# define a pointer that adds 0x100 to a pointer and then returns a pint.uint32_t
    class type(ptype.opointer_t):
        _object_ = pint.uint32_t
        def _calculate_(self, number):
            return number + 0x100
"""
import six
import functools, operator, itertools, types
import sys, inspect, time, traceback
from six.moves import builtins

from . import bitmap, provider, utils, config, error
Config = config.defaults
Log = Config.log.getChild(__name__[len(__package__)+1:])

__all__ = 'istype,iscontainer,isrelated,type,container,undefined,block,definition,encoded_t,pointer_t,rpointer_t,opointer_t,boundary,debug,debugrecurse,clone,setbyteorder'.split(',')

## this is all a horrible and slow way to do this...
def isiterator(t):
    """True if type ``t`` is iterable"""
    # FIXME: also insure that it's not a class with these attributes
    return hasattr(t, '__iter__') and hasattr(t, 'next')

def iscallable(t):
    """True if type ``t`` is a code object that can be called"""
    return six.callable(t) and hasattr(t, '__call__')

@utils.memoize('t')
def isinstance(t):
    return builtins.isinstance(t, generic)

@utils.memoize('t')
def istype(t):
    """True if type ``t`` inherits from ptype.type"""
    return t.__class__ is t.__class__.__class__ and not isresolveable(t) and (builtins.isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, generic)

@utils.memoize('t')
def iscontainer(t):
    """True if type ``t`` inherits from ptype.container """
    return (istype(t) and issubclass(t, container)) or pbinary.istype(t)

@utils.memoize('t')
def isresolveable(t):
    """True if type ``t`` can be descended into"""
    return builtins.isinstance(t, (types.FunctionType, types.MethodType))    # or isiterator(t)

def isrelated(t, t2):
    """True if type ``t`` is related to ``t2``"""
    def getbases(result, bases):
        for x in bases:
            if not istype(x) or x in (type, container):
                continue
            result.add(x)
            getbases(result, x.__bases__)
        return result
    return getbases(set(), t.__bases__).intersection( getbases(set(), t.__bases__) )

def force(t, self, chain=[]):
    """Resolve type ``t`` into a ptype.type for the provided object ``self``"""
    chain = chain[:]
    chain.append(t)

    ## First check if we're inserting types into our tree

    # if type is a pbinary type, we insert a partial node into the tree
    if pbinary.istype(t):
        Log.debug("{:s}.force : {:s} : Implicitly promoting binary type `{:s}` to partial for storing in non-binary container.".format(__name__, self.instance(), t.typename()))
        return clone(pbinary.partial, _object_=t)

    # if type is a straight-up ptype
    elif istype(t):
        return t

    ## Next we'll check instances (for setting and allocating)

    # if type is a pbinary instance
    if builtins.isinstance(t, pbinary.type):
        return pbinary.new(t)

    # if type is just a regular ptype instance
    elif builtins.isinstance(t, base):
        return t

    ## Now we'll try callables and see if it's one of those

    # functions
    if builtins.isinstance(t, types.FunctionType):
        res = t(self)
        return force(res, self, chain)

    # bound methods
    elif builtins.isinstance(t, types.MethodType):
        return force(t(), self, chain)

    # generators
    elif inspect.isgenerator(t):
        return force(six.next(t), self, chain)

    # and lastly iterators (unsupported)
    if False:
        if isiterator(t):
            return force(six.next(t), self, chain)

    path = str().join(map("<{:s}>".format, self.backtrace()))
    raise error.TypeError(self, 'force<ptype>', message='chain={!r} : Refusing request to resolve {!r} to a type that does not inherit from ptype.type : {{{:s}}}'.format(chain, t, path))

def debug(ptype, **attributes):
    """``rethrow`` all exceptions that occur during initialization of ``ptype``"""
    if not istype(ptype):
        raise error.UserError(ptype, 'debug', message='{!r} is not a ptype'.format(ptype))

    def logentry(string, *args):
        return (time.time(), traceback.extract_stack(), string.format(*args))

    if any((hasattr(n) for n in ('_debug_', '_dump_'))):
        raise error.UserError(ptype, 'debug', message='{!r} has a private method name that clashes'.format(ptype))

    class decorated_ptype(ptype):
        __doc__ = ptype.__doc__
        _debug_ = {}

        def __init__(self, *args, **kwds):
            self._debug_['creation'] = time.time(), traceback.extract_stack(), self.backtrace(lambda s:s)
            return super(decorated_ptype, self).__init__(*args, **kwds)

        def _dump_(self, file):
            dbg = self._debug_
            if 'constructed' in dbg:
                t, c = dbg['constructed']
                _, st, bt = dbg['creation']
                print >>file, u"[{!r}] {:s} -> {:s} -> {:s}".format(t, c, self.instance(), getattr(self, '__name__', u""))
            else:
                t, st, bt = dbg['creation']
                print >>file, u"[{!r}] {:s} -> {:s} -> {:s}".format(t, self.typename(), self.instance(), getattr(self, '__name__', u""))

            print >>file, u"Created by:"
            print >>file, format_stack(st)
            print >>file, u"Located at:"
            print >>file, '\n'.join(u"{:s} : {:s}".format(x.instance(), x.name()) for x in bt)
            print >>file, u"Loads from store"
            print >>file, '\n'.join("[:d] [{:f}] {:s}".format(i, t, string) for i, (t, _, string) in enumerate(dbg['load']))
            print >>file, u"Writes to store"
            print >>file, '\n'.join(u"[:d] [{:f}] {:s}".format(i, t, string) for i, (t, _, string) in enumerate(dbg['commit']))
            print >>file, u"Serialized to a string:"
            print >>file, '\n'.join(u"[:d] [{:f}] {:s}".format(i, t, string) for i, (t, _, string) in enumerate(dbg['serialize']))
            return

        def serialize(self):
            result = super(decorated, self).serialize()
            size = len(result)
            _ = logentry(u"serialize() -> __len__() -> {:#x}", self.instance(), len(size))
            Log.debug(" : ".join(self.instance(), _[-1]))
            self._debug_.setdefault('serialize', []).append(_)
            return result

        def load(self, **kwds):
            start = time.time()
            result = super(decorated, self).load(**kwds)
            end = time.time()

            offset, size, source = self.getoffset(), self.blocksize(), self.source
            _ = logentry(u"load({:s}) {:f} seconds -> (offset={:#x},size={:#x}) -> source={!r}", ','.join(u"{:s}={!r}".format(k, v) for k, v in attrs.items()), end-start, offset, size, source)
            Log.debug(" : ".join(self.instance(), _[-1]))
            self._debug_.setdefault('load', []).append(_)
            return result

        def commit(self, **kwds):
            start = time.time()
            result = super(decorated, self).commit(**kwds)
            end = time.time()

            _ = logentry(u"commit({:s}) {:f} seconds -> (offset={:#x},size={:#x}) -> source={!r}", ','.join(u"{:s}={!r}".format(k, v) for k, v in attrs.items()), end-start, offset, size, source)
            Log.debug(" : ".join(self.instance(), _[-1]))
            self._debug_.setdefault('commit', []).append(_)
            return result

    decorated.__name__ = "debug({:s})".format(ptype.__name__)
    decorated._debug_.update(attributes)
    return decorated

def debugrecurse(ptype):
    """``rethrow`` all exceptions that occur during initialization of ``ptype`` and any sub-elements"""
    class decorated(debug(ptype)):
        __doc__ = ptype.__doc__
        def new(self, t, **attrs):
            res = force(t, self)
            Log.debug('constructed : {!r} -> {:s} {:s}'.format(t, self.classname(), self.name()))
            debugres = debug(res, constructed=(time.time(), t))
            return super(decorated, self).new(debugres, **attrs)
    decorated.__name__ = "debug({:s},recurse=True)".format(ptype.__name__)
    return decorated

source = provider.default()
class _base_generic(object):
    # XXX: this class should implement
    #           attribute inheritance
    #           addition and removal of elements to trie
    #           initial attribute creation
    #           attributes not propagated during creation
    #           XXX meta-related information
    #           instance tree navigation

    __slots__ = ('__source__', 'attributes', 'ignored', 'parent', 'value', 'position')

    # FIXME: it'd probably be a good idea to have this not depend on globals.source,
    #        and instead have globals.source depend on this.
    __source__ = None      # ptype.prov
    @property
    def source(self):
        if self.parent is None:
            global source
            return source if self.__source__ is None else self.__source__
        return self.parent.source if self.__source__ is None else self.__source__
    @source.setter
    def source(self, value):
        self.__source__ = value

    attributes = None        # {...}
    ignored = set(('source', 'parent', 'attributes', 'value', '__name__', 'position', 'offset'))

    parent = None       # ptype.base
    p = property(fget=lambda s: s.parent)   # abbr to get to .parent

    value = None        # _
    v = property(fget=lambda s: s.value)   # abbr to get to .value

    def __init__(self, **attrs):
        """Create a new instance of object. Will assign provided named arguments to self.attributes"""
        self.attributes = {} if self.attributes is None else dict(self.attributes)
        self.__update__(attrs)

    ## offset
    def setoffset(self, offset, **_):
        raise error.ImplementationError(self, 'generic.setoffset')
    def getoffset(self, **_):
        raise error.ImplementationError(self, 'generic.setoffset')
    offset = property(fget=lambda s: s.getoffset(), fset=lambda s, v: s.setoffset(v))

    ## position
    def setposition(self, position, **_):
        raise error.ImplementationError(self, 'generic.setposition')
    def getposition(self):
        raise error.ImplementationError(self, 'generic.getposition')
    position = property(fget=lambda s: s.getposition(), fset=lambda s, v: s.setposition(v))

    def __update__(self, attrs={}, **moreattrs):
        """Update the attributes that will be assigned to object.

        Any attributes defined under the 'recurse' key will be propagated to any
        sub-elements.
        """
        attrs = dict(attrs)
        attrs.update(moreattrs)
        recurse = dict(attrs.pop('recurse', {}))
        ignored = self.ignored

        # update self with all attributes
        res = {}
        res.update(recurse)
        res.update(attrs)
        for k, v in res.iteritems():
            setattr(self, k, v)

        # filter out ignored attributes from the recurse dictionary
        recurse = dict((k, v) for k, v in recurse.iteritems() if k not in ignored)

        # update self (for instantiated elements)
        self.attributes.update(recurse)

        # update sub-elements with recursive attributes
        if recurse and issubclass(self.__class__, container) and self.value is not None:
            [n.__update__(recurse, recurse=recurse) for n in self.value]
        return self

    def properties(self):
        """Return a tuple of properties/characteristics describing the current state of the object to the user"""
        result = {}

        # Validate that we weren't constructed with a name per a field assignment,
        # or explicitly specifying the name via a property. If the name is empty,
        # then we are simply unnamed.
        if not getattr(self, '__name__', ''):
            result['unnamed'] = True

        # Check if we're initialized
        if self.initializedQ():
            try:
                size = self.size()

            # If we can't get our size because of an InitializationError, then
            # there's no reason to check our load/commit state
            except error.InitializationError:
                pass

            # Otherwise, we were successful and we need to check the state in
            # order to update the type's properties
            else:
                key = 'overcommit'  if self.blocksize() < size else 'underload' if self.blocksize() > size else None
                if key: result[key] = True

        # Otherwise, we're uninitialized and the properties should say this
        else:
            result['uninitialized'] = True
        return result

    def traverse(self, edges, filter=lambda node:True, **kwds):
        """Will walk the elements returned by the generator ``edges -> node -> ptype.type``

        This will iterate in a top-down approach.
        """
        for self in edges(self, **kwds):
            if not isinstance(self):
                continue

            if filter(self):
                yield self

            for y in self.traverse(edges=edges, filter=filter, **kwds):
                yield y
            continue
        return

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().iteritems())
        result = self.repr()

        # multiline
        if result.count('\n') > 0:
            result = result.rstrip('\n') # remove trailing newlines
            if prop:
                return u"{:s} '{:s}' {{{:s}}}\n{:s}".format(utils.repr_class(self.classname()), self.name(), prop, result)
            return u"{:s} '{:s}'\n{:s}".format(utils.repr_class(self.classname()), self.name(), result)

        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

    # naming
    @classmethod
    def typename(cls):
        """Return the name of the ptype"""
        if getattr(cls, '__module__', ''):
            if Config.display.show_module_name:
                return '.'.join((cls.__module__, cls.__name__))
            return '.'.join((cls.__module__.rsplit('.', 1)[-1], cls.__name__))
        return cls.__name__
    def classname(self):
        """Return the dynamic classname. Can be overwritten."""
        return self.typename()
    def shortname(self):
        return getattr(self, '__name__', 'unnamed_{:x}'.format(id(self)))
    def name(self):
        """Return the loaded name of the instance"""
        name = self.shortname()
        if Config.display.show_parent_name and self.parent is not None:
            return '.'.join((self.parent.name(), name))
        return name
    def instance(self):
        """Returns a minimal string describing the type and it's location"""
        name, ofs = self.classname(), self.getoffset()
        try:
            bs = self.blocksize()
            return "{:s}[{:x}:{:+x}]".format(name, ofs, bs)
        except:
            pass
        return "{:s}[{:x}:+???]".format(name, ofs)

    def hexdump(self, **options):
        """Return a hexdump of the type using utils.hexdump(**options)

        Options can provide formatting specifiers
        terse -- display the hexdump tersely if larger than a specific threshold
        threshold -- maximum number of rows to display
        """
        options.setdefault('width', Config.display.hexdump.width)
        options.setdefault('offset', self.getoffset())
        return utils.hexdump(self.serialize(), **options)

    def details(self, **options):
        """Return details of the object. This can be displayed in multiple-lines."""
        if not self.initializedQ():
            return u"???"

        buf = self.serialize()
        try: sz = self.size()
        except: sz = self.blocksize()

        length = options.setdefault('width', Config.display.hexdump.width)
        options.setdefault('offset', self.getoffset())

        # if larger than threshold...
        threshold = options.pop('threshold', Config.display.threshold.details)
        message = options.pop('threshold_message', Config.display.threshold.details_message)
        if threshold > 0 and sz/length > threshold:
            threshold = options.pop('height', threshold) # 'threshold' maps to 'height' for emit_repr
            return '\n'.join(utils.emit_hexrows(buf, threshold, message, **options))
        return utils.hexdump(buf, **options)

    def summary(self, **options):
        """Return a summary of the object. This can be displayed on a single-line."""
        if not self.initializedQ():
            return u"???"

        buf = self.serialize()
        try: sz = self.size()
        except: sz = self.blocksize()

        options.setdefault('offset', self.getoffset())

        # if larger than threshold...
        threshold = options.pop('threshold', Config.display.threshold.summary)
        message = options.pop('threshold_message', Config.display.threshold.summary_message)
        if threshold > 0 and sz > threshold:
            threshold = options.pop('width', threshold) # 'threshold' maps to 'width' for emit_repr
            return u'"' + utils.emit_repr(buf, threshold, message, **options) + u'"'
        return u'"' + utils.emit_repr(buf, **options) + u'"'

    @utils.memoize('self', self='parent', args=lambda n:(n[0],) if len(n) > 0 else (), kwds=lambda n:n.get('type', ()))
    def getparent(self, *args, **kwds):
        """Returns the creator of the current type.

        If nothing is specified, return the parent element.

        If the ``type`` argument is specified, recursively descend into .parent
        elements until encountering an instance that inherits from the one specified.

        If any arguments are provided, return the element whom either inherits
        from a type provided, or whose .parent matches the requested instance.
        """
        if not len(args) and 'type' not in kwds:
            return self.parent

        query = args if len(args) else (kwds['type'],)
        match = lambda self: lambda query: any(((builtins.isinstance(q, builtins.type) and builtins.isinstance(self, q)) or self.parent is q) for q in query)

        # check to see if user actually queried for self
        if match(self)(query):
            return self

        # now walk upwards till we find what the user is looking for
        def parents(node):
            return () if node.parent is None else (node.parent,)

        for node in self.traverse(edges=parents):
            if match(node)(query):
                return node
            continue

        # otherwise, we can bail since it wasn't found.
        chain = str().join("<{:s}>".format(node.instance()) for node in self.traverse(edges=parents))
        res = (q.typename() if istype(q) else str(q) for q in query)
        raise error.NotFoundError(self, 'base.getparent', message="The requested match ({:s}) was not found while traversing from {:s} : {:s}".format(', '.join(res), self.instance(), chain))
    def backtrace(self, fn=operator.methodcaller('instance')):
        """
        Return a backtrace to the root element applying ``fn`` to each parent

        By default this returns a string describing the type and location of
        each structure.
        """
        path = self.traverse(edges=lambda node:(node.parent for _ in (None,) if node.parent is not None))
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
        if not(istype(t) or isinstance(t)):
            raise error.TypeError(self, 'base.new', message='{!r} is not a ptype class'.format(t.__class__))

        # if it's a type, then instantiate it
        if istype(t):
            t = t(**attrs)

        # if already instantiated, then update it's attributes
        elif isinstance(t):
            t.__update__(**attrs)

        # give the instance a default name
        if '__name__' in attrs:
            t.__name__ = attrs['__name__']
        return t

class generic(_base_generic):
    '''A class shared between both pbinary.*, ptype.*'''
    initialized = property(fget=lambda s: s.initializedQ())

    def initializedQ(self):
        raise error.ImplementationError(self, 'base.initializedQ')
    def __eq__(self, other):
        '''x.__eq__(y) <==> x==y'''
        return id(self) == id(other)
    def __ne__(self, other):
        '''x.__ne__(y) <==> x!=y'''
        return not(self == other)
    def __getstate__(self):
        return ()
    def __setstate__(self, state):
        return

    def repr(self, **options):
        """The output that __repr__ displays"""
        raise error.ImplementationError(self, 'generic.repr')

    def __deserialize_block__(self, block):
        raise error.ImplementationError(self, 'generic.__deserialize_block__', message='Subclass {:s} must implement deserialize_block'.format(self.classname()))
    def serialize(self):
        raise error.ImplementationError(self, 'generic.serialize')

    def load(self, **attrs):
        raise error.ImplementationError(self, 'generic.load')
    def commit(self, **attrs):
        raise error.ImplementationError(self, 'generic.commit')
    def alloc(self, **attrs):
        """Will zero the ptype instance with the provided ``attrs``.

        This can be overloaded in order to allocate physical space for the new ptype.
        """
        attrs.setdefault('source', provider.empty())
        return self.load(**attrs)

    # abbreviations
    a = property(fget=lambda s: s.alloc())  # alloc
    c = property(fget=lambda s: s.commit()) # commit
    l = property(fget=lambda s: s.load())   # load
    li = property(fget=lambda s: s.load() if s.value is None else s) # load if uninitialized

    def get(self):
        """Return a representation of a type.

        This value should be able to be passed to .set
        """
        return self.__getvalue__()

    def set(self, *args, **kwds):
        """Set value of type to ``value``.

        Should be the same value as returned by .get
        """
        return self.__setvalue__(*args, **kwds)

    def copy(self):
        """Return a new instance of self"""
        raise error.ImplementationError(self, 'generic.copy')

    def __cmp__(self, other):
        """x.__cmp__(y) <==> cmp(x,y)

        To compare the actual contents, see .compare(other)
        """
        if not isinstance(other) or self.initializedQ() != other.initializedQ():
            return -1
        if self.initializedQ():
            return 0 if (self.getposition(), self.serialize()) == (other.getposition(), other.serialize()) else -1
        return 0 if (self.getposition(), self.blocksize()) == (other.getposition(), other.blocksize()) else +1

class base(generic):
    padding = utils.padding.source.zero()

    def setoffset(self, offset, **options):
        """Changes the current offset to ``offset``"""
        return self.setposition((offset,), **options)[0]
    def getoffset(self, **options):
        """Returns the current offset"""
        return self.getposition(**options)[0]

    __position__ = 0,
    def setposition(self, position, **kwds):
        (self.__position__, res) = position, (self.__position__) or (0,)
        return res[:]
    def getposition(self):
        return self.__position__[:]

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    def copy(self, **attrs):
        """Return a duplicate instance of the current one."""
        result = self.new(self.__class__, position=self.getposition())
        if hasattr(self, '__name__'): attrs.setdefault('__name__', self.__name__)
        attrs.setdefault('parent', self.parent)
        if 'value' not in attrs:
            if not builtins.isinstance(self.value, (str, types.NoneType)):
                raise error.AssertionError(self, 'base.copy', message='Invalid type of .value while trying to duplicate object : {!r}'.format(self.value.__class__))
            attrs['value'] = None if self.value is None else self.value[:]
        result.__update__(attrs)
        if result.parent is None:
            result.source = self.source
        return result

    def compare(self, other):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self.serialize(),other.serialize()))
        """
        if False in (self.initializedQ(), other.initializedQ()):
            Log.fatal('base.compare : {:s} : Instance not initialized ({:s})'.format(self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        s, o = self.serialize(), other.serialize()
        if s == o:
            return

        comparison = (bool(six.byte2int(x)^six.byte2int(y)) for x, y in zip(s, o))
        result = [(different, len(list(times))) for different, times in itertools.groupby(comparison)]
        index = 0
        for diff, length in result:
            #if diff: yield index, length
            if diff: yield index, (s[index:index+length], o[index:index+length])
            index += length

        if len(s) != len(o):
            #yield index, max(len(s), len(o))-index
            yield index, (s[index:], '') if len(s) > len(o) else ('', o[index:])
        return

    def cast(self, t, **kwds):
        """Cast the contents of the current instance into a differing ptype"""
        data, bs = self.serialize(), self.blocksize()

        # copy attributes that make the new instantiation similar
        kwds.setdefault('offset', self.getoffset())
        kwds.setdefault('parent', self.parent)

        # disable propagating any specific attributes when instantiating
        with utils.assign(self, attributes={}):
            result = self.new(t, **kwds)

        # update with any attributes that need to be propagated
        result.__update__(recurse=self.attributes)

        # try and load the contents using the correct blocksize
        try:
            result = result.load(offset=0, source=provider.proxy(self), blocksize=lambda:bs)
            result.setoffset(result.getoffset(), recurse=True)

        except Exception, e:
            Log.warning("base.cast : {:s} : {:s} : Error during cast resulted in a partially initialized instance : {!r}".format(self.classname(), t.typename(), e))

        # force partial or overcommited initializations
        try: result = result.__deserialize_block__(data)
        except (error.LoadError, StopIteration): pass

        # log whether our size has changed somehow
        a, b = self.size(), result.size()
        if a > b:
            Log.info("base.cast : {:s} : Result {:s} size is smaller than source type : {:#x} < {:#x}".format(self.classname(), result.classname(), result.size(), self.size()))
        elif a < b:
            Log.warning("base.cast : {:s} : Result {:s} is partially initialized : {:#x} > {:#x}".format(self.classname(), result.classname(), result.size(), self.size()))
        return result

    def traverse(self, edges=lambda node:tuple(node.value) if builtins.isinstance(node, container) else (), filter=lambda node:True, **kwds):
        """
        This will traverse a tree in a top-down approach.

        By default this will traverse every sub-element from a given object.
        """
        return super(base, self).traverse(edges, filter, **kwds)

    def new(self, ptype, **attrs):
        res = force(ptype, self)
        return super(base, self).new(res, **attrs)

    def load(self, **attrs):
        """Synchronize the current instance with data from the .source attributes"""
        with utils.assign(self, **attrs):
            ofs, bs = self.getoffset(), self.blocksize()

            try:
                self.source.seek(ofs)
                block = self.source.consume(bs)
                self = self.__deserialize_block__(block)
            except (StopIteration, error.ProviderError), e:
                self.source.seek(ofs + bs)
                raise error.LoadError(self, consumed=bs, exception=e)
        return self

    def commit(self, **attrs):
        """Commit the current state back to the .source attribute"""
        try:
            with utils.assign(self, **attrs):
                ofs, data = self.getoffset(), self.serialize()
                self.source.seek(ofs)
                self.source.store(data)
            return self

        except (StopIteration, error.ProviderError), e:
            raise error.CommitError(self, exception=e)

    def collect(self, *args, **kwds):
        global encoded_t
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or builtins.isinstance(other, encoded_t)
        parentTester = parentTester()

        #edges = lambda node:tuple(node.value) if iscontainer(node.__class__) else ()
        #encoded = lambda node: (node.d,) if builtins.isinstance(node, encoded_t) else ()
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
    ignored = generic.ignored.union(('length',))

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        if hasattr(self, 'length'):
            result.length = self.length
        return result

    def initializedQ(self):
        return True if self.value is not None and len(self.value) >= self.blocksize() else False

    ## byte stream input/output
    def __deserialize_block__(self, block):
        """Load type using the string provided by ``block``"""
        bs = self.blocksize()
        if len(block) < bs:
            self.value = block[:bs]
            raise StopIteration(self.name(), len(block))

        # all is good.
        self.value = block[:bs]
        return self

    def serialize(self):
        """Return contents of type as a string"""

        # if we're not initialized, then return a padded value up to the blocksize
        if not self.initializedQ():
            res = self.blocksize()

            try:
                parent = self.getparent(encoded_t)
            except error.NotFoundError:
                parent = self.getparent(None)

            # check if child element is child of encoded_t or we're a proxy since neither needs to get checked since the types aren't guaranteed to be related
            if builtins.isinstance(parent, encoded_t) or builtins.isinstance(self.source, provider.proxy):
                pass

            # check that child element is actually within bounds of parent
            elif parent is not None and parent.getoffset() > self.getoffset():
                Log.info("type.serialize : {:s} : child element is outside the bounds of parent element {:s}. : {:#x} > {:#x}".format(self.instance(), parent.instance(), parent.getoffset(), self.getoffset()))

            # clamp the blocksize if it pushes the child element outside the bounds of the parent
            elif builtins.isinstance(parent, container):
                parentSize = parent.blocksize()
                childOffset = self.getoffset() - parent.getoffset()
                maxElementSize = parentSize - childOffset
                if res > maxElementSize:
                    Log.warn("type.serialize : {:s} : blocksize is outside the bounds of parent element {:s}. Clamping according to parent's maximum : {:#x} > {:#x} : {:#x}".format(self.instance(), parent.instance(), res, maxElementSize, parentSize))
                    res = maxElementSize

            if res > six.MAXSIZE:
                Log.fatal('type.serialize : {:s} : blocksize is larger than maximum size. Refusing to add padding : {:#x} > {:#x}'.format(self.instance(), res, six.MAXSIZE))
                return ''

            # generate padding up to the blocksize
            Log.debug('type.serialize : {:s} : Padding data by {:+#x} bytes due to element being partially uninitialized during serialization.'.format(self.instance(), res))
            padding = utils.padding.fill(res if res > 0 else 0, self.padding)

            # prefix beginning of padding with any data that element contains
            return padding if self.value is None else self.value + padding[len(self.value):]

        # take the current value as a string, which should match up to .size()
        data = self.value

        # pad up to the .blocksize() if our length doesn't meet the minimum
        res = self.blocksize()
        if len(data) < res:
            Log.debug('type.serialize : {:s} : Padding data by {:+#x} bytes due to element being partially initialized during serialization.'.format(self.instance(), res))
            padding = utils.padding.fill(res-len(data), self.padding)
            data += padding
        return data

    ## set/get
    def __setvalue__(self, *values, **attrs):
        """Set entire type equal to ``value`` if defined."""
        if not values: return self

        value, = values
        if not builtins.isinstance(value, six.string_types):
            raise error.TypeError(self, 'type.set', message='type {!r} is not serialized data'.format(value.__class__))

        self.value = value[:]

        # If there's a length attribute, then make sure to update it with
        # the length of the value that was assigned
        if hasattr(self, 'length'):
            self.length = len(self.value)

        return self

    def __getvalue__(self):
        return self.serialize()

    ## size boundaries
    def size(self):
        """Returns the number of bytes that have been loaded into the type.

        If type is uninitialized, issue a warning and return 0.
        """
        if self.initializedQ() or self.value:
            return len(self.value)
        Log.info("type.size : {:s} : Unable to determine size of ptype.type, as object is still uninitialized.".format(self.instance()))
        return 0

    def blocksize(self):
        """Returns the expected size of the type

        By default this returns self.length, but can be overloaded to define the
        size of the type. This *must* return an integral type.
        """

        # XXX: overloading will always provide a side effect of modifying the .source's offset
        #        make sure to fetch the blocksize first before you .getoffset() on something.
        return getattr(self, 'length', len(self.value) if self.value is not None else 0)

    ## operator overloads
    def repr(self, **options):
        """Display all ptype.type instances as a single-line hexstring"""
        return self.summary(**options) if self.initializedQ() else '???'

    def __getstate__(self):
        return (super(type, self).__getstate__(), self.blocksize(), self.value,)
    def __setstate__(self, state):
        state, self.length, self.value = state
        super(type, self).__setstate__(state)

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

    def getoffset(self, *field, **options):
        """Returns the current offset.

        If ``field`` is specified as a ``str``, return the offset of the
        sub-element with the provided name. If specified as a ``list`` or
        ``tuple``, descend into sub-elements using ``field`` as the path.
        """
        if not len(field):
            return super(container, self).getoffset()
        (field,) = field

        # if a path is specified, then recursively get the offset
        if builtins.isinstance(field, (tuple, list)):
            (name, res) = (lambda hd, *tl:(hd, tl))(*field)
            return self[name].getoffset(res) if len(res) > 0 else self.getoffset(name)

        index = self.__getindex__(field)
        return self.getoffset() + sum(map(operator.methodcaller('size'), self.value[:index]))

    def __getindex__(self, name):
        """Searches the .value attribute for an element with the provided ``name``

        This is intended to be overloaded by any type that inherits from
        ptype.container.
        """
        raise error.ImplementationError(self, 'container.__getindex__', 'Developer forgot to overload this method')

    def __field__(self, key):
        index = self.__getindex__(key)
        if self.value is None:
            raise error.InitializationError(self, 'container.__field__')
        return self.value[index]
    def __getitem__(self, key):
        '''x.__getitem__(y) <==> x[y]'''
        return self.__field__(key)

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if not builtins.isinstance(value, base):
            raise error.TypeError(self, 'container.__setitem__', message='Cannot assign a non-ptype to an element of a container. Use .set instead.')
        if self.value is None:
            raise error.InitializationError(self, 'container.__setitem__')
        offset = self.value[index].getoffset()
        value.setoffset(offset, recurse=True)
        value.parent, value.source = self, None
        self.value[index] = value
        return value

    def at(self, offset, recurse=True, **kwds):
        """Returns element that contains the specified offset

        If ``recurse`` is True, then recursively descend into all sub-elements
        until an atomic type (such as ptype.type, or pbinary.partial) is encountered.
        """
        if not self.contains(offset):
            raise error.NotFoundError(self, 'container.at', 'offset {:#x} can not be located within container.'.format(offset))

        # if we weren't asked to recurse, then figure out which sub-element contains the offset
        if not recurse:
            for n in self.value:
                if n.contains(offset):
                    return n
                continue
            raise error.NotFoundError(self, 'container.at', 'offset {:#x} not found in a child element. returning encompassing parent.'.format(offset))

        # descend into the trie a single level
        try:
            res = self.at(offset, recurse=False, **kwds)

        except ValueError, msg:
            Log.info('container.at : {:s} : Non-fatal exception raised : {!r}'.format(self.instance(), ValueError(msg)), exc_info=True)
            return self

        # if we're already at a leaf of the trie, then no need to descend
        if builtins.isinstance(res, (type, pbinary.partial)):
            return res

        # drill into the trie's elements for more detail
        try:
            return res.at(offset, recurse=recurse, **kwds)
        except (error.ImplementationError, AttributeError):
            pass
        return res

    def field(self, offset, recurse=False):
        """Returns the field at the specified offset relative to the structure"""
        return self.at(self.getoffset()+offset, recurse=recurse)

    def setoffset(self, offset, recurse=False):
        """Changes the current offset to ``offset``

        If ``recurse`` is True, the update all offsets in sub-elements.
        """
        return self.setposition((offset,), recurse=recurse)[0]

    def setposition(self, offset, recurse=False):
        res = super(container, self).setposition(offset, recurse=recurse)
        if recurse and self.value is not None:
            o = offset[0]
            for n in self.value:
                n.setposition((o,), recurse=recurse)
                o += n.size() if n.initializedQ() else n.blocksize()
            return res
        return res

    def __deserialize_block__(self, block):
        """Load type using the string provided by ``block``"""
        if self.value is None:
            raise error.SyntaxError(self, 'container.__deserialize_block__', message='caller is responsible for allocation of elements in self.value')

        # read everything up to the blocksize
        value, expected, bs, total = self.value[:], self.blocksize(), 0, 0
        while value and total < expected:
            res = value.pop(0)
            bs = res.blocksize()
            res.__deserialize_block__(block[:bs])
            block = block[bs:]
            total += bs

        # ..and then fill out any zero sized elements to update any state
        while value:
            res = value.pop(0)
            bs = res.blocksize()
            if bs > 0: break
            res.__deserialize_block__(block[:bs])

        # log any information about deserialization errors
        if total < expected:
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.warn('container.__deserialize_block__ : {:s} : Container less than expected blocksize : {:#x} < {:#x} : {{{:s}}}'.format(self.instance(), total, expected, path))
            raise StopIteration(self.name(), total) # XXX
        elif total > expected:
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.debug('container.__deserialize_block__ : {:s} : Container larger than expected blocksize : {:#x} > {:#x} : {{{:s}}}'.format(self.instance(), total, expected, path))
            raise error.LoadError(self, consumed=total) # XXX
        return self

    def serialize(self):
        """Return contents of all sub-elements concatenated as a string"""
        # check the blocksize(), if it's invalid then return what we have since we can't figure out the padding anyways
        try:
            res = self.blocksize()
        except:
            return str().join(map(operator.methodcaller('serialize'), iter(self.value)))

        # if there's no blocksize, then this field is empty
        if res <= 0: return ''

        # serialize all the elements that we currently have
        data = str().join(map(operator.methodcaller('serialize'), iter(self.value)))

        try:
            parent = self.getparent(encoded_t)
        except error.NotFoundError:
            parent = self.getparent(None)

            # check to see if we should validate ourselves according to parent's boundaries
            if parent is None or not builtins.isinstance(parent.value, list) or self not in parent.value:
                return data

        # check if child element is child of encoded_t which doesn't get checked since encoded types can have their sizes changed.
        if builtins.isinstance(parent, encoded_t):
            pass

        # check that child element is actually within bounds of parent
        elif parent is not None and parent.getoffset() > self.getoffset():
            Log.info("container.serialize : {:s} : child element is outside the bounds of parent element {:s}. : {:#x} > {:#x}".format(self.instance(), parent.instance(), parent.getoffset(), self.getoffset()))

        # clamp the blocksize if we're outside the bounds of the parent
        elif builtins.isinstance(parent, container):
            parentSize = parent.blocksize()
            childOffset = self.getoffset() - parent.getoffset()
            maxElementSize = parentSize - childOffset
            if res > maxElementSize:
                Log.warn("container.serialize : {:s} : blocksize is outside the bounds of parent element {:s}. Clamping according to the parent's maximum : {:#x} > {:#x} : {:#x}".format(self.instance(), parent.instance(), res, maxElementSize, parentSize))
                res = maxElementSize

        # if the blocksize is larger than maxsize, then ignore the padding
        if res > six.MAXSIZE:
            Log.warn('container.serialize : {:s} : blocksize is larger than maximum size. Refusing to add padding : {:#x} > {:#x}'.format(self.instance(), res, six.MAXSIZE))
            return data

        # if the data is smaller then the blocksize, then pad the rest in
        if len(data) < res:
            Log.debug('container.serialize : {:s} : Padding data by {:+#x} bytes due to element being partially uninitialized during serialization.'.format(self.instance(), res))
            data += utils.padding.fill(res - len(data), self.padding)

        # if it's larger then the blocksize, then warn the user about it
        if len(data) > res:
            Log.debug('container.serialize : {:s} : Container larger than expected blocksize : {:#x} > {:#x}'.format(self.instance(), len(data), res))

        # otherwise, our data should appear correct
        return data

    def alloc(self, **attrs):
        """Will zero the ptype.container instance with the provided ``attrs``.

        This can be overloaded in order to allocate physical space for the new ptype.
        """
        return super(container, self).alloc(**attrs)

    def load(self, **attrs):
        """Allocate the current instance with data from the .source attributes"""
        if self.value is None and 'value' not in attrs:
            raise error.UserError(self, 'container.load', message='Parent must initialize self.value')

        try:
            # if any of the sub-elements are undefined, load each element separately
            if Config.ptype.noncontiguous and \
                    any(builtins.isinstance(n, container) or builtins.isinstance(n, undefined) for n in self.value):
                # load each element individually up to the blocksize
                bs, value = 0, self.value[:]
                left, right = self.getoffset(), self.getoffset()+self.blocksize()
                while value and left < right:
                    res = value.pop(0)
                    bs, ofs = res.blocksize(), res.getoffset()
                    left = res.getoffset() if left + bs < ofs else left + bs
                    res.load(**attrs)

                # ..and then load any zero-sized elements that were left to update state
                while value:
                    res = value.pop(0)
                    if res.blocksize() > 0: break
                    res.load(**attrs)
                return self

            # otherwise the contents are contiguous, load them as so
            return super(container, self).load(**attrs)

        # we failed out, log what happened according to the variable state
        except error.LoadError, e:
            ofs, s, bs = self.getoffset(), self.size(), self.blocksize()
            self.source.seek(ofs+bs)
            if s > 0 and s < bs:
                Log.warning('container.load : {:s} : Unable to complete read at {{{:x}:{:+x}}} : {!r}'.format(self.instance(), ofs, s, e))
            else:
                Log.debug('container.load : {:s} : Cropped to {{{:x}:{:+x}}} : {!r}'.format(self.instance(), ofs, s, e))
        return self

    def commit(self, **attrs):
        """Commit the current state of all children back to the .source attribute"""
        if not Config.ptype.noncontiguous and \
                all(not (builtins.isinstance(n, container) or builtins.isinstance(n, undefined)) for n in self.value):

            try:
                return super(container, self).commit(**attrs)
            except error.CommitError, e:
                Log.warning('container.commit : {:s} : Unable to complete contiguous store : write at {{{:x}:{:+x}}} : {:s}'.format(self.instance(), self.getoffset(), self.size(), e))

        # commit all elements of container individually
        with utils.assign(self, **attrs):
            current, ofs, sz = 0, self.getoffset(), self.size()
            try:
                for n in self.value:
                    n.commit(source=self.source)
                    current += n.size()
                    if current > sz: break
                pass
            except error.CommitError, e:
                Log.fatal('container.commit : {:s} : Unable to complete non-contiguous store : write stopped at {{{:x}:{:+x}}} : {!r}'.format(self.instance(), ofs+current, self.blocksize()-current, e))
        return self

    def copy(self, **attrs):
        """Performs a deep-copy of self repopulating the new instance if self is initialized"""
        attrs.setdefault('value', [])
        attrs.setdefault('parent', self.parent)
        # create an empty instance of self and update with requested attributes
        res = super(container, self).copy(**attrs)

        # now copy the children, with the same parent
        res.value = map(operator.methodcaller('copy', parent=res), self.value or [])
        return res

    def compare(self, other, *args, **kwds):
        """Returns an iterable containing the difference between ``self`` and ``other``

        Each value in the iterable is composed of (index,(self,other)). Any
        extra arguments are passed to .getparent in order to only return
        differences in elements that are of a particular type.
        """
        if False in (self.initializedQ(), other.initializedQ()):
            Log.fatal('container.compare : {:s} : Instance not initialized ({:s})'.format(self.instance(), self.instance() if not self.initializedQ() else other.instance()))
            return

        if self.value == other.value:
            return

        def between(object, (left, right)):
            objects = provider.proxy.collect(object, left, right)
            mapped = six.moves.map(lambda n: n.getparent(*args, **kwds) if kwds else n, objects)
            for n, _ in itertools.groupby(mapped):
                if left+n.size() <= right:
                    yield n
                left += n.size()
            return

        for ofs, (s, o) in super(container, self).compare(other):
            if len(s) == 0:
                i = other.value.index(other.field(ofs, recurse=False))
                yield ofs, (None, tuple(between(other, (ofs, other.blocksize()))))
            elif len(o) == 0:
                i = self.value.index(self.field(ofs, recurse=False))
                yield ofs, (tuple(between(self, (ofs, self.blocksize()))), None)
            else:
                if len(s) != len(o):
                    raise error.AssertionError(self, 'container.compare', message='Invalid length between both objects : {:x} != {:x}'.format(len(s), len(o)))
                length = len(s)
                s, o = (between(o, (ofs, ofs+length)) for o in (self, other))
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
            def blocksizeorelse(self):
                try: res = self.blocksize()
                except: res = 0
                return res

            #data = ''.join((x.serialize() if x.initializedQ() else '?'*blocksizeorelse(x)) for x in self.value)
            data = str().join(n.serialize() if n.initializedQ() else '' for n in self.value)
            return u"\"{:s}\"".format(utils.emit_repr(data, threshold, message, **options)) if len(data) > 0 else u"???"
        return u"???"

    def append(self, value):
        """Add ``object`` to the ptype.container ``self``. Return the element's index.

        When adding ``object`` to ``self``, none of the offsets are updated and
        thus will need to be manually updated before committing to a provider.
        """
        return self.__append__(value)

    def __append__(self, object):

        # if we're uninitialized, then create an empty value and try again
        if self.value is None:
            self.value = []
            return self.__append__(object)

        # if object is not an instance, then try to resolve it to one and try again
        if not isinstance(object):
            res = self.new(object)
            return self.__append__(res)

        # assume that object is now a ptype instance
        object.parent, object.source = self, None

        current = len(self.value)
        self.value.append(object if object.initializedQ() else object.a)
        return current

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        return len(self.value)

    def __iter__(self):
        '''x.__iter__() <==> iter(x)'''
        if self.value is None:
            raise error.InitializationError(self, 'container.__iter__')

        for res in self.value:
            yield res
        return

    def __setvalue__(self, *items, **attrs):
        """Set ``self`` with instances or copies of the types provided in the iterable ``items``.

        If uninitialized, this will make a copy of all the instances in ``items`` and update the
        'parent' and 'source' attributes to match. All the offsets will be
        recursively updated.

        If initialized, this will pass the argument to .set using the current contents.

        This is an internal function and is not intended to be used outside of ptypes.
        """
        if self.initializedQ() and len(self.value) == len(items):
            for idx, (value, item) in enumerate(zip(self.value, items)):
                name = getattr(value, '__name__', None)
                if isresolveable(item) or istype(item):
                    self.value[idx] = self.new(item, __name__=name).a
                elif isinstance(item):
                    self.value[idx] = self.new(item, __name__=name)
                elif builtins.isinstance(item, dict):
                    value.set(**item)
                else:
                    value.set(item)
                continue
        elif all(isresolveable(item) or istype(item) or isinstance(item) for item in items):
            self.value = [ self.new(item) if isinstance(item) else self.new(item).a for item in items ]
        else:
            raise error.AssertionError(self, 'container.set', message='Invalid number or type of elements to assign with : {!r}'.format(items))

        # Re-calculate all our offsets after applying our value iterable
        self.setoffset(self.getoffset(), recurse=True)

        return self

    def __getvalue__(self):
        return tuple((res.get() for res in self.value))

    def __getstate__(self):
        return (super(container, self).__getstate__(), self.source, self.attributes, self.ignored, self.parent, self.position)
    def __setstate__(self, state):
        state, self.source, self.attributes, self.ignored, self.parent, self.position = state
        super(container, self).__setstate__(state)

class undefined(type):
    """An empty ptype that is eternally undefined"""
    def size(self):
        return self.blocksize()
    def load(self, **attrs):
#        self.value = utils.padding.fill(self.blocksize(), self.padding)
        self.value = ''
        return self
    def commit(self, **attrs):
        return self
    def initializedQ(self):
        return False if self.value is None else True
    def serialize(self):
#        return utils.padding.fill(self.blocksize(), self.padding)
        return self.value or ''
    def summary(self, **options):
        return '...'
    def details(self, **options):
        return self.summary(**options)

class block(type):
    """A ptype that can be accessed as an array"""
    def __getslice__(self, i, j):
        '''x.__getslice__(i, j) <==> x[i:j]'''
        buffer = self.value[:]
        return buffer[i:j]
    def __getitem__(self, index):
        '''x.__getitem__(y) <==> x[y]'''
        buffer = self.value[:]
        return buffer[index]
    def repr(self, **options):
        """Display all ptype.block instances as a hexdump"""
        if not self.initializedQ():
            return u"???"
        if self.blocksize() > 0:
            return self.details(**options) + '\n'
        return self.summary(**options)
    def __setvalue__(self, *values, **attrs):
        """Set entire type equal to ``value``"""
        if not values:
            return super(block, self).__setvalue__(*values, **attrs)
        value, = values
        self.length = len(value)
        return super(block, self).__setvalue__(value, **attrs)
    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        self.value = self.value[:index] + value + self.value[index+1:]
    def __setslice__(self, i, j, value):
        '''x.__setslice__(i, j, y) <==> x[i:j]=y'''
        v = self.value
        if len(value) != j-i:
            raise ValueError('block.__setslice__ : {:s} : Unable to reassign slice outside of bounds of object : ({:d}, {:d}) : {:d}'.format(self.instance(), i, j, len(value)))
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
            cn = super(_clone, self).classname()
            return Config.ptype.clone_name.format(cn, **(utils.attributes(self) if Config.display.mangle_with_attributes else {}))

    if newattrs.get('__name__', None) is None:
        newattrs['__name__'] = cls.__name__

    if hasattr(cls, '__module__'):
        newattrs.setdefault('__module__', cls.__module__)

    ignored = cls.ignored if hasattr(cls, 'ignored') else set()
    recurse = dict(newattrs.pop('recurse', {}))

    # update class with all attributes
    res = {}
    res.update(recurse)
    res.update(newattrs)
    for k, v in res.items():
        setattr(_clone, k, v)

    # filter out ignored attributes from recurse dictionary
    recurse = dict((k, v) for k, v in recurse.iteritems() if k not in ignored)

    if hasattr(_clone, 'attributes'):
        _clone.attributes = getattr(_clone, 'attributes', None) or {}
        _clone.attributes.update(recurse)
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

    Another thing to define is the `.default` property. This will be the
    default type that is returned when an identifier is not located in the
    cache that was defined.

    i.e.
    class mytypelookup(ptype.definition):
        cache = {}
        default = ptype.block
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
    attribute = 'type'

    class default(block):
        '''default type to return an unknown class'''

        @classmethod
        def typename(cls):
            return '.'.join((__name__, 'unknown'))

    @classmethod
    def __set__(cls, type, object):
        '''Overloadable: Map the specified type to an object'''
        return cls.cache.setdefault(type, object)

    @classmethod
    def __has__(cls, type):
        '''Overloadable: Check if the specified type has been mapped to an object'''
        return type in six.viewkeys(cls.cache)

    @classmethod
    def __get__(cls, type):
        '''Overloadable: Return the object for a specified type'''
        return cls.cache[type]

    @classmethod
    def add(cls, type, object):
        """Add ``object`` to cache and key it by ``type``"""
        if not builtins.isinstance(cls.cache, dict):
            raise error.AssertionError(cls, 'definition.add', message='{:s} has an invalid .cache attribute : {!r}'.format(cls.__name__, cls.cache.__class__))
        return cls.__set__(type, object)

        """Search ``cls.cache`` for a type with the specified value ``type``."""
    @classmethod
    def lookup(cls, *type):
        """D.lookup(type[, default]) -> Lookup a ptype in the defintion D by ``type`` and return it.

        If it's not found return ``default`` or raise a KeyError if not specified.
        """
        if len(type) not in {1, 2}:
            raise TypeError("lookup() takes 1 or 2 arguments ({:d} given)".format(len(type)))
        return cls.__get__(type[0]) if len(type) == 1 else (cls.__get__(type[0]) if cls.__has__(type[0]) else type[1])

    @classmethod
    def has(cls, type):
        return cls.__has__(type)
    contains = has

    @classmethod
    def get(cls, *type, **attrs):
        """D.get(type[, default], **attrs) -> Lookup a ptype in the definition D by ``type`` and return a clone of it with ``attrs`` applied.

        If ``type`` was not found, then return ``default`` or D.default if it's undefined.
        """

        # check the arguments
        if len(type) not in {1, 2}:
            raise TypeError("get() takes 1 or 2 arguments ({:d} given)".format(len(type)))

        # extract the information from the arguments
        type, default = (type) if len(type) > 1 else (type[0], cls.default)

        # search in the cache for the specified type
        try:
            res = cls.__get__(type)
        except KeyError:
            res = default

        # now we can finally clone it
        attrs.setdefault(cls.attribute, type)
        return clone(res, **attrs)

    @classmethod
    def withdefault(cls, *type, **missingattrs):
        """D.withdefault(type[, default], **attrs) -> Lookup a ptype in the definition D by ``type``.

        If ``type`` was not found, then return ``default`` or D.default with ``missingattrs`` applied to it.
        """

        # check the arguments
        if len(type) not in {1, 2}:
            raise TypeError("withdefault() takes 1 or 2 arguments ({:d} given)".format(len(type)))

        # extract the information from the arguments
        type, default = (type) if len(type) > 1 else (type[0], cls.default)

        # search in the cache for the specified type
        try:
            res = cls.__get__(type)
        except KeyError:
            res = clone(default, **missingattrs)

        return res

    @classmethod
    def update(cls, otherdefinition):
        """Import the definition cache from ``otherdefinition``, effectively merging the contents into the current definition"""
        a, b = map(six.viewkeys, (cls.cache, otherdefinition.cache))
        if a & b:
            Log.warn('definition.update : {:s} : Unable to import module {!r} due to multiple definitions of the same record'.format(cls.__module__, otherdefinition))
            Log.warn('definition.update : {:s} : Duplicate records : {!r}'.format(cls.__module__, a & b))
            return False

        # merge record caches into a single one
        for type, object in six.viewitems(otherdefinition.cache):
            cls.__set__(type, object)
        return True

    @classmethod
    def copy(cls, otherdefinition):
        if not issubclass(otherdefinition, cls):
            raise error.AssertionError(cls, 'definition.copy', message='{:s} is not inheriting from {:s}'.format(otherdefinition.__name__, cls.__name__))

        otherdefinition.cache = dict(cls.cache)
        otherdefinition.attribute = cls.attribute
        otherdefinition.default = cls.default
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
            #res = builtins.type(res.pop('__name__', definition.__name__), definition.__bases__, res)
            res = builtins.type(res.pop('__name__', definition.__name__), (definition,), res)
            cls.add(getattr(res, cls.attribute), res)
            return definition

        if attributes:
            if len(definition):
                raise error.AssertionError(cls, 'definition.define', message='Unexpected number of positional arguments. : {:d}'.format(len(definition)))
            return clone
        res, = definition
        cls.add(getattr(res, cls.attribute), res)
        return res

class wrapper_t(type):
    '''This type represents a type that is backed and sized by another ptype.

    _value_ -- the type that will be instantiated as the wrapper_t's backend
    object -- an instance of ._value_ that the wrapper_t will use for modifying

    Modifying the instance of .object will affect the string in the .value property. If .value is modified, this will affect the state of the .object instance.
    '''

    _value_ = None

    # getter/setter that wraps .value and keeps .object and .value in sync
    __value__ = None
    @property
    def value(self):
        '''Returns the contents of the wrapper_t.'''
        return self.__value__

    @value.setter
    def value(self, data):
        '''Re-assigns the contents of the wrapper_t'''
        self.__deserialize_block__(data)

    __object__ = None
    # setters/getters for the object's backing instance
    @property
    def object(self):
        '''Returns the instance that is used to back the wrapper_t.'''

        # Check if .__object__ is undefined or of a different type than self._value_
        if self.__object__ is None or (self._value_ and not builtins.isinstance(self.__object__, self._value_)):
            if not istype(self._value_):
                raise error.UserError(self, 'wrapper_t.object', message='unable to instantiate .object due to wrapper_t._value_ is undefined.')

            res = self._value_
            name = 'wrapped<{:s}>'.format(res.typename() if istype(res) else res.__name__)
            self.__object__ = self.new(res, __name__=name, offset=0, source=provider.proxy(self))

        # Otherwise, we can simply return it
        return self.__object__

    @object.setter
    def object(self, instance):
        name = 'wrapped<{:s}>'.format(instance.name())

        # steal the type from the one the user specified
        self._value_ = instance.__class__

        # re-assign the object the user specified
        self.__object__ = res = instance.copy(__name__=name, offset=0, source=provider.proxy(self), parent=self)
        if self.__value__ is None and res.initializedQ():
            self.__deserialize_block__(res.serialize())

        # commit using the upper-level mechanics just to be sure
        res.commit()
    o = object

    def initializedQ(self):
        return self.__object__ is not None and self.__object__.initializedQ()

    def blocksize(self):
        if self.__object__ is not None:
            return self.__object__.blocksize()

        # if blocksize can't be calculated by loading (invalid dereference)
        #   then guess the size by allocating an empty version of the type
        value = self.new(self._value_ or undefined, offset=self.getoffset(), source=self.source)
        try:
            res = value.l.blocksize()
        except error.LoadError:
            res = value.a.blocksize()
        return res

    def __deserialize_block__(self, block):
        self.__value__ = block
        self.object.load(offset=0, source=provider.proxy(self))
        return self

    # forwarded methods
    def __getvalue__(self):
        return self.object.get()

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self

        value, = value
        res = self.object.set(value, **attrs)
        self.object.commit(offset=0, source=provider.proxy(self))
        return self

    def commit(self, **attrs):
        self.object.commit(offset=0, source=provider.proxy(self))
        return super(wrapper_t, self).commit(**attrs)

    def size(self):
        if self.__object__ is not None and self.__object__.initializedQ():
            return self.__object__.size()
        elif self.__value__ is not None:
            return len(self.__value__)
        Log.info("wrapper_t.size : {:s} : Unable to determine size of ptype.wrapper_t, as object is still uninitialized.".format(self.instance()))
        return 0

    def classname(self):
        if self.initializedQ():
            return "{:s}<{:s}>".format(self.typename(), self.object.classname())
        if self._value_ is None:
            return "{:s}<?>".format(self.typename())
        return "{:s}<{:s}>".format(self.typename(), self._value_.typename() if istype(self._value_) else self._value_.__name__)

    def contains(self, offset):
        left = self.getoffset()
        right = left + self.blocksize()
        return left <= offset < right

    def __getstate__(self):
        return super(wrapper_t, self).__getstate__(), self._value_, self.__object__

    def __setstate__(self, state):
        state, self._value_, self.__object__ = state
        super(wrapper_t, self).__setstate__(state)

    def summary(self, **options):
        options.setdefault('offset', self.getoffset())
        return super(wrapper_t, self).summary(**options)

    def details(self, **options):
        options.setdefault('offset', self.getoffset())
        return super(wrapper_t, self).details(**options)

class encoded_t(wrapper_t):
    """This type represents an element that can be decoded/encoded to/from another element.

    To change the way a type is decoded, overload the .decode() method and then
    call the super class' method with a dictionary of any attributes that you
    want to modify.

    To change the way a type is encoded to it, overwrite .encode() and convert
    the object parameter to an encoded string.

    _value_ = the original element type
    _object_ = the decoded element type

    .object = the actual element object represented by self
    """
    _value_ = None      # source type
    _object_ = None     # new type

    d = property(fget=lambda s, **a: s.dereference(**a), fset=lambda s, *x, **a:s.reference(*x, **a))
    deref = lambda s, **a: s.dereference(**a)
    ref = lambda s, *x, **a: s.reference(*x, **a)

    @utils.memoize('self', self=lambda n:(n._object_, n.value), attrs=lambda n:tuple(sorted(n.items())))
    def decode(self, object, **attrs):
        """Take ``data`` and decode it back to it's original form"""
        for n in ('offset', 'source', 'parent'):
            if attrs.has_key(n): attrs.pop(n)

        # attach decoded object to encoded_t
        attrs['offset'], attrs['source'], attrs['parent'] = 0, provider.proxy(self, autocommit={}), self
        object.__update__(recurse=self.attributes)
        object.__update__(attrs)
        return object

    def encode(self, object, **attrs):
        """Take ``data`` and return it in encoded form"""
        for n in ('offset', 'source', 'parent'):
            if attrs.has_key(n): attrs.pop(n)

        # attach encoded object to encoded_t
        attrs['offset'], attrs['source'], attrs['parent'] = 0, provider.proxy(self, autocommit={}), self
        object.__update__(attrs)
        return object

    def __hook(self, object):
        '''This hooks ``object`` with a .load and .commit that will write to the encoded_t'''

        prefix = '_encoded_t'
        ## overriding the `commit` method
        if hasattr(object, prefix+'_commit'):
            object.commit = getattr(object, prefix+'_commit')
            delattr(object, prefix+'_commit')

        def commit(**attrs):
            # first cast our object into a block
            res = object.cast(block, length=object.blocksize())

            # now turn it into the type that the encoded_t expects
            res = res.cast(self._value_)

            # now encode it
            enc = self.encode(res, **attrs)

            # commit it to the encoded_t
            enc.commit(offset=0, source=provider.proxy(self))
            return object
        setattr(object, prefix+'_commit', object.commit)
        object.commit = commit

        ## overloading the `load` method
        if hasattr(object, prefix+'_load'):
            object.load = getattr(object, prefix+'_load')
            delattr(object, prefix+'_load')

        def load(**attrs):
            # first cast our encoded_t into a block
            res = self.cast(block, length=self.blocksize())

            # now turn it into the type that the encoded_t expects
            res = self.cast(self._value_ or res.__class__)

            # now decode the block into an object
            dec = self.decode(res, **attrs)

            # finally load the decoded obj into self
            fn = getattr(object, prefix+'_load')
            return fn(offset=0, source=provider.proxy(dec))
        setattr(object, prefix+'_load', object.load)
        object.load = load

        # ..and we're done
        return object

    @utils.memoize('self', self=lambda n:(n.object, n.source, n._object_), attrs=lambda n:tuple(sorted(n.items())))
    def dereference(self, **attrs):
        """Dereference object into the target type specified by self._object_"""
        attrs.setdefault('__name__', '*'+self.name())
        res = self.cast(self._value_ or self.object.__class__)

        # ensure decoded object writes to self
        dec = self.decode(res, offset=0, source=provider.proxy(self, autocommit={}))

        # also ensure that decoded object will encode/decode depending on commit/load
        dec = self.__hook(dec)

        # update attributes
        dec.__update__(recurse=self.attributes)

        # tweak the blocksize so that self._object_ will use dec's entire contents
        blocksize = dec.size()
        attrs.setdefault('blocksize', lambda bs=blocksize:bs)

        # ensure that all of it's children autoload/autocommit to the decoded object
        recurse = {'source':provider.proxy(dec, autocommit={}, autoload={})}
        recurse.update(attrs.get('recurse', {}))
        attrs['recurse'] = recurse

        # and we now have a good working object
        return dec.new(self._object_, **attrs)

    def reference(self, object, **attrs):
        """Reference ``object`` and encode it into self"""
        object = self.__hook(object)

        # take object, and encode it to an encoded type
        res = self.encode(object, **attrs)

        # take encoded type and cast it to self's wrapped type in order to preserve length
        res = res.cast(self._value_ or res.__class__, **attrs)

        # now that the length is correct, write it to the wrapper_t
        res.commit(offset=0, source=provider.proxy(self))

        # assign some default attributes to object
        object.__name__ = '*'+self.name()
        self._object_ = object.__class__
        return self

def setbyteorder(endianness):
    '''Sets the byte order for any pointer_t
    can be either .bigendian or .littleendian
    '''
    global pointer_t
    if endianness in (config.byteorder.bigendian, config.byteorder.littleendian):
        pointer_t._value_.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness {!r}".format(endianness))

class pointer_t(encoded_t):
    _object_ = None

    d = property(fget=lambda s, **a: s.dereference(**a), fset=lambda s, *x, **a:s.reference(*x, **a))
    deref = lambda s, **a: s.dereference(**a)
    ref = lambda s, *x, **a: s.reference(*x, **a)

    class _value_(block):
        '''Default pointer value that can return an integer in any byteorder'''
        length, byteorder = Config.integer.size, Config.integer.order

        def __setvalue__(self, *values, **attrs):
            if not values:
                return super(pointer_t._value_, self).__setvalue__(*values, **attrs)

            offset, = values
            bs = self.blocksize()
            res = bitmap.new(offset, bs*8)
            res = bitmap.data(res, reversed=(self.byteorder is config.byteorder.littleendian))
            return super(pointer_t._value_, self).__setvalue__(res, **attrs)

        def __getvalue__(self):
            if self.value is None:
                raise error.InitializationError(self, 'pointer_t._value_.get')
            bs = self.blocksize()
            value = reversed(self.value) if self.byteorder is config.byteorder.littleendian else self.value
            res = six.moves.reduce(bitmap.push, map(None, map(six.byte2int, value), (8,) * len(self.value)), bitmap.zero)
            return bitmap.value(res)

    def decode(self, object, **attrs):
        return object.cast(self._value_, **attrs)

    def encode(self, object, **attrs):
        return object.cast(self._value_, **attrs)

    @utils.memoize('self', self=lambda n:(n.source, n._object_, n.object.__getvalue__()), attrs=lambda n:tuple(sorted(n.items())))
    def dereference(self, **attrs):
        res = self.decode(self.object)
        attrs.setdefault('__name__', '*'+self.name())
        attrs.setdefault('source', self.__source__)
        attrs.setdefault('offset', res.get())
        return self.new(self._object_, **attrs)

    def reference(self, object, **attrs):
        attrs.setdefault('__name__', '*'+self.name())
        attrs.setdefault('source', self.__source__)
        res = self.object.copy().set(object.getoffset())
        enc = self.encode(res)
        enc.commit(offset=0, source=provider.proxy(self.object))
        self._object_ = object.__class__
        self.object.commit(offset=0, source=provider.proxy(self))
        return self

    def int(self):
        """Return the value of pointer as an integral"""
        return self.object.get()
    num = number = int

    def classname(self):
        targetname = force(self._object_, self).typename() if istype(self._object_) else getattr(self._object_, '__name__', 'None')
        return '{:s}<{:s}>'.format(self.typename(), targetname)

    def summary(self, **options):
        return u'*{:#x}'.format(self.int())

    def repr(self, **options):
        """Display all pointer_t instances as an integer"""
        return self.summary(**options) if self.initializedQ() else u"*???"

    def __getstate__(self):
        return super(pointer_t, self).__getstate__(), self._object_
    def __setstate__(self, state):
        state, self._object_ = state
        super(wrapper_t, self).__setstate__(state)

class rpointer_t(pointer_t):
    """a pointer_t that's at an offset relative to a specific object"""
    _baseobject_ = None

    def classname(self):
        if self.initializedQ():
            baseobject = self._baseobject_
            basename = baseobject.classname() if builtins.isinstance(self._baseobject_, base) else baseobject.__name__
            return '{:s}({:s}, {:s})'.format(self.typename(), self.object.classname(), basename)
        res = getattr(self, '_object_', undefined) or undefined
        objectname = force(res, self).typename() if istype(res) else res.__name__
        return '{:s}({:s}, ...)'.format(self.typename(), objectname)

    def decode(self, object, **attrs):
        res = super(rpointer_t, self).decode(object, **attrs)
        root = force(self._baseobject_, self)
        base = root.getoffset() if isinstance(root) else root().getoffset()
        res.set(base + object.get())
        return res

    def __getstate__(self):
        return super(rpointer_t, self).__getstate__(), self._baseobject_
    def __setstate__(self, state):
        state, self._baseobject_, = state
        super(rpointer_t, self).__setstate__(state)

class opointer_t(pointer_t):
    """a pointer_t that's calculated via a user-provided function that takes an integer value as an argument"""
    _calculate_ = lambda self, value: value

    def classname(self):
        calcname = self._calculate_.__name__
        if self.initializedQ():
            return '{:s}({:s}, {:s})'.format(self.typename(), self.object.classname(), calcname)
        res = getattr(self, '_object_', undefined) or undefined
        objectname = force(res, self).typename() if istype(res) else res.__name__
        return '{:s}({:s}, {:s})'.format(self.typename(), objectname, calcname)

    def decode(self, object, **attrs):
        res = super(opointer_t, self).decode(object, **attrs)
        res.set(self._calculate_(object.get()))
        return res

class boundary(base):
    """Used to mark a boundary in a ptype tree. Can be used to make .getparent() stop."""

class constant(type):
    """A ptype that uses .__doc__ to describe a string constant

    This will log a warning if the loaded data does not match the expected string.
    """
    length = property(fget=lambda self: len(self.__doc__), fset=lambda self, value: None)

    def __init__(self, **attrs):
        if self.__doc__ is None:
            Log.warn('constant.__init__ : {:s} : Constant was not initialized'.format(self.classname()))
            self.__doc__ = ''
        return super(constant, self).__init__(**attrs)

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self

        newdata, = values
        bs, res, data = self.blocksize(), newdata[:], self.__doc__

        if (data != res) or (bs != len(res)):
            Log.warn('constant.set : {:s} : Data did not match expected value : {!r} != {!r}'.format(self.classname(), res, data))

        self.value = res + utils.padding.fill(bs - len(res), self.padding) if len(res) < bs else res
        return self

    def __deserialize_block__(self, block):
        data = self.__doc__
        if data != block:
            Log.warn('constant.__deserialize_block__ : {:s} : Data loaded from source did not match expected constant value : {!r} != {!r}'.format(self.instance(), block, data))
        return super(constant, self).__deserialize_block__(data)

    def alloc(self, **attrs):
        """Allocate the ptype instance with requested string"""
        attrs.setdefault('source', provider.string(self.__doc__))
        return self.load(**attrs)

    def __getstate__(self):
        return super(constant, self).__getstate__(), self.__doc__
    def __setstate__(self, state):
        state, self.__doc__ = state
        super(constant, self).__setstate__(state)

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
    from ptypes import dynamic,pint,pstr,parray,pstruct,ptype,provider,error
    prov = provider

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
        s = ''.join(six.int2byte(six.byte2int(x)^k) for x in 'hello world')
        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(s))
            _object_ = dynamic.block(len(s))
            key = k
            def encode(self, object, **attrs):
                data = ''.join(six.int2byte(six.byte2int(x)^k) for x in object.serialize())
                return super(xor, self).encode(ptype.block(length=len(data)).set(data))
            def decode(self, object, **attrs):
                data = ''.join(six.int2byte(six.byte2int(x)^k) for x in object.serialize())
                return super(xor, self).decode(ptype.block(length=len(data)).set(data))

        x = xor(source=ptypes.prov.string(s))
        x = x.l
        if x.d.l.serialize() == 'hello world':
            raise Success

    @TestCase
    def test_decoded_xorenc():
        k = 0x80
        data = 'hello world'
        match = ''.join(six.int2byte(six.byte2int(x)^k) for x in data)

        class xor(ptype.encoded_t):
            _value_ = dynamic.block(len(data))
            _object_ = dynamic.block(len(match))

            key = k

            def encode(self, object, **attrs):
                data = ''.join(six.int2byte(six.byte2int(x)^k) for x in object.serialize())
                return super(xor, self).encode(ptype.block(length=len(data)).set(data))
            def decode(self, object, **attrs):
                data = ''.join(six.int2byte(six.byte2int(x)^k) for x in object.serialize())
                return super(xor, self).decode(ptype.block(length=len(data)).set(data))

        instance = pstr.string(length=len(match)).set(match)

        x = xor(source=ptypes.prov.string('\x00'*0x100)).l
        x.reference(instance)
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
                return super(b64, self).encode(ptype.block(length=len(data)).set(data))

            def decode(self, object, **attrs):
                data = object.serialize().decode('base64')
                return super(b64, self).decode(ptype.block(length=len(data)).set(data))

        x = b64(source=ptypes.prov.string(s)).l
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
                return super(b64, self).encode(ptype.block(length=len(data)).set(data))

            def decode(self, object, **attrs):
                data = object.serialize().decode('base64')
                return super(b64, self).decode(ptype.block(length=len(data)).set(data))

        instance = pstr.szstring().set(input)

        x = b64(source=ptypes.prov.string('A'*0x100+'\x00')).l
        x = x.reference(instance)
        if x.serialize() == result:
            raise Success

    @TestCase
    def test_attributes_static_1():
        x = pint.uint32_t(a1=5).a
        if 'a1' not in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_1():
        x = pint.uint32_t(recurse={'a1':5}).a
        if 'a1' in x.attributes and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_2():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(a1=5).a
        if 'a1' not in x.attributes and 'a1' not in x.v[0].attributes and 'a1' not in dir(x.v[0]) and x.a1 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_2():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh(recurse={'a1':5}).a
        if 'a1' in x.attributes and 'a1' in x.v[0].attributes and 'a1' in dir(x.v[0]) and x.v[0].a1 == 5:
            raise Success

    @TestCase
    def test_attributes_static_3():
        x = pint.uint32_t().a
        x.__update__({'a2':5})
        if 'a2' not in x.attributes and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_3():
        argh = pint.uint32_t
        x = pint.uint32_t().a
        x.__update__(recurse={'a2':5})
        if 'a2' in x.attributes and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_static_4():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.__update__({'a2':5})
        if 'a2' not in x.attributes and 'a2' not in x.v[0].attributes and 'a2' not in dir(x.v[0]) and x.a2 == 5:
            raise Success

    @TestCase
    def test_attributes_recurse_4():
        class argh(parray.type):
            length = 5
            _object_ = pint.uint32_t

        x = argh().a
        x.__update__(recurse={'a2':5})
        if 'a2' in x.attributes and 'a2' in x.v[0].attributes and 'a2' in dir(x.v[0]) and x.v[0].a2 == 5:
            raise Success

    @TestCase
    def test_attributes_static_5():
        a = pint.uint32_t(a1=5).a
        x = a.new(pint.uint32_t)
        if 'a1' not in a.attributes and 'a1' not in x.attributes and 'a1' not in dir(x):
            raise Success

    @TestCase
    def test_attributes_recurse_5():
        a = pint.uint32_t(recurse={'a1':5}).a
        x = a.new(pint.uint32_t)
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
        if a.serialize() == "ASDFASDF":
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
        import math
        count = math.log(sys.maxint) / math.log(0x100)
        prefix = chr(math.trunc(math.ceil(count))) + '\x00'*math.trunc(count)

        data = prefix + 'AAAA'

        a = ptype.pointer_t(source=prov.string(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint32_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref():
        import math
        count = math.log(sys.maxint) / math.log(0x100)
        prefix = chr(math.trunc(math.ceil(count))) + '\x00'*math.trunc(count)

        src = prov.string(prefix + 'AAAA' + 'AAAA')

        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint32_t).l
        b = a.d.l
        if b.serialize() != '\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_pointer_deref_32():
        data = '\x04\x00\x00\x00AAAA'

        a = ptype.pointer_t(source=prov.string(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint32_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref_32():
        src = prov.string('\x04\x00\x00\x00AAAAAAAA')
        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint32_t).l
        b = a.d.l
        if b.serialize() != '\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_pointer_deref_64():
        data = '\x08\x00\x00\x00\x00\x00\x00\x00AAAA'

        a = ptype.pointer_t(source=prov.string(data), offset=0, _object_=pint.uint32_t, _value_=pint.uint64_t)
        a = a.l
        b = a.dereference()
        if b.l.int() == 0x41414141:
            raise Success

    @TestCase
    def test_pointer_ref_64():
        src = prov.string('\x08\x00\x00\x00\x00\x00\x00\x00AAAAAAAA')
        a = ptype.pointer_t(source=src, offset=0, _object_=dynamic.block(4), _value_=pint.uint64_t).l
        b = a.d.l
        if b.serialize() != '\x41\x41\x41\x41':
            raise Failure

        c = pint.uint32_t(offset=8,source=src).set(0x42424242).commit()
        a.reference(c)
        if a.getoffset() == 0 and a.int() == c.getoffset() and a.d.l.int() == 0x42424242 and a.d.getoffset() == c.getoffset():
            raise Success

    @TestCase
    def test_type_cast_same():
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = pint.uint32_t

        data = prov.string('AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_container_cast_same():
        t1 = dynamic.clone(ptype.type, length=4)
        t2 = dynamic.array(pint.uint8_t, 4)

        data = prov.string('AAAA')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.serialize() == b.serialize():
            raise Success

    @TestCase
    def test_type_cast_diff_large_to_small():
        t1 = ptype.clone(ptype.type, length=4)
        t2 = ptype.clone(ptype.type, length=2)
        data = prov.string('ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.serialize() == 'AB':
            raise Success

    @TestCase
    def test_type_cast_diff_small_to_large():
        t1 = ptype.clone(ptype.type, length=2)
        t2 = ptype.clone(ptype.type, length=4)
        data = prov.string('ABCD')
        a = t1(source=data).l
        b = a.cast(t2)
        if a.size() == b.size() and not b.initialized:
            raise Success

    @TestCase
    def test_container_cast_large_to_small():
        t1 = dynamic.array(pint.uint8_t, 8)
        t2 = dynamic.array(pint.uint8_t, 4)
        data = prov.string('ABCDEFGH')

        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and b.serialize() == 'ABCD':
            raise Success

    @TestCase
    def test_container_cast_small_to_large():
        t1 = dynamic.array(pint.uint8_t, 4)
        t2 = dynamic.array(pint.uint8_t, 8)
        data = prov.string('ABCDEFGH')
        a = t1(source=data).l
        b = a.cast(t2)
        if b.size() == 4 and not b.initialized and b.blocksize() == 8:
            raise Success

    @TestCase
    def test_type_copy():
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
        data = prov.string(map(six.int2byte,six.moves.range(six.byte2int('a'),six.byte2int('z'))))
        a = bah(offset=0,source=data)
        if a.getoffset() == 0 and a.l.serialize()=='ab':
            raise Success

    @TestCase
    def test_type_setoffset():
        class bah(ptype.type): length=2
        data = prov.string(map(six.int2byte,six.moves.range(six.byte2int('a'),six.byte2int('z'))))
        a = bah(offset=0,source=data)
        a.setoffset(20)
        if a.l.initializedQ() and a.getoffset() == 20 and a.serialize() == 'uv':
            raise Success

    @TestCase
    def test_container_setoffset_recurse():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i
        a = cont()
        a.set(bah().a, bah().a, bah().a)
        a.setoffset(a.getoffset(), recurse=True)
        if tuple(x.getoffset() for x in a.value) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_field():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i

        a = cont()
        a.set(bah().a, bah().a, bah().a)
        if tuple(a.getoffset(i) for i in six.moves.range(len(a.v))) == (0,2,4):
            raise Success

    @TestCase
    def test_container_getoffset_iterable():
        class bah(ptype.type): length=2
        class cont(ptype.container): __getindex__ = lambda s,i: i

        a,b = cont(),cont()
        a.set(bah,bah,bah)
        b.set(bah,bah,bah)
        a.set(bah, b.copy(), bah)
        a.setoffset(a.getoffset(), recurse=True)
        if a.getoffset((1,2)) == 6:
            raise Success

    @TestCase
    def test_decompression_block():
        class cblock(pstruct.type):
            class _zlibblock(ptype.encoded_t):
                _object_ = ptype.block
                def encode(self, object, **attrs):
                    data = object.serialize().encode('zlib')
                    return super(cblock._zlibblock, self).encode(ptype.block().set(data), length=len(data))
                def decode(self, object, **attrs):
                    data = object.serialize().decode('zlib')
                    return super(cblock._zlibblock, self).decode(ptype.block().set(data), length=len(data))

            def __zlibblock(self):
                return ptype.clone(self._zlibblock, _value_=dynamic.block(self['size'].l.int()))

            _fields_ = [
                (pint.uint32_t, 'size'),
                (__zlibblock, 'data'),
            ]
        message = 'hi there.'
        cmessage = message.encode('zlib')
        data = pint.uint32_t().set(len(cmessage)).serialize()+cmessage
        a = cblock(source=prov.string(data)).l
        if a['data'].d.l.serialize() == message:
            raise Success

    @TestCase
    def test_compression_block():
        class zlibblock(ptype.encoded_t):
            _object_ = ptype.block
            def encode(self, object, **attrs):
                data = object.serialize().encode('zlib')
                return super(zlibblock, self).encode(ptype.block(length=len(data)).set(data))
            def decode(self, object, **attrs):
                data = object.serialize().decode('zlib')
                return super(zlibblock, self).decode(ptype.block(length=len(data)).set(data))

        class mymessage(ptype.block): pass
        message = 'hi there.'
        data = mymessage().set(message)

        source = prov.string('\x00'*1000)
        a = zlibblock(source=source)
        a.object = pstr.string(length=1000, source=source).l
        a.reference(data)
        if a.d.l.serialize() == message:
            raise Success

    @TestCase
    def test_equality_type_same():
        class type1(ptype.type): length=4
        class type2(ptype.type): length=4
        data = 'ABCDEFGHIJKLMNOP'
        a = type1(source=prov.string(data)).l
        b = type2(source=prov.string(data), offset=a.getoffset()).l
        if cmp(a,b) == 0:
            raise Success

    @TestCase
    def test_equality_type_different():
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
        a = pstr.szstring().set('this sentence is over the top!')
        b = pstr.szstring().set('this sentence is unpunctuaTed')
        getstr = lambda s,(i,(x,_)): s[i:i+len(x)].serialize()
        result = list(a.compare(b))
        c,d = result
        if getstr(a, c) == 'over the top!' and getstr(b,c) == 'unpunctuaTed\x00' and d[0] >= b.size() and getstr(a,d) == '\x00':
            raise Success

    @TestCase
    def test_compare_container_types():
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
            s,o = tuple(six.moves.reduce(lambda a,b:a+b,map(lambda x:x.serialize(),X),'') for X in result[1])
            if s == g.serialize() and o == ''.join(map(six.int2byte,(40,60,80,100))):
                raise Success

    @TestCase
    def test_compare_container_tail():
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
            if s is None and six.moves.reduce(lambda a,b:a+b,map(lambda x:x.serialize(),o),'') == g.serialize()+'\x40':
                raise Success
    @TestCase
    def test_container_set_uninitialized_type():
        class container(ptype.container): pass
        a = container().set(pint.uint32_t,pint.uint32_t)
        if a.size() == 8:
            raise Success

    @TestCase
    def test_container_set_uninitialized_instance():
        class container(ptype.container): pass
        a = container().set(*(pint.uint8_t().set(1) for _ in six.moves.range(10)))
        if sum(x.int() for x in a) == 10:
            raise Success

    @TestCase
    def test_container_set_initialized_value():
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(4,4,4,4)
        if sum(x.int() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_type():
        class container(ptype.container): pass
        a = container().set(*((pint.uint8_t,)*4))
        a.set(pint.uint32_t,pint.uint32_t,pint.uint32_t,pint.uint32_t)
        if sum(x.size() for x in a) == 16:
            raise Success

    @TestCase
    def test_container_set_initialized_instance():
        class container(ptype.container): pass
        a = container().set(pint.uint8_t,pint.uint32_t)
        a.set(pint.uint32_t().set(0xfeeddead), pint.uint8_t().set(0x42))
        if (a.v[0].size(),a.v[0].int()) == (4,0xfeeddead) and (a.v[1].size(),a.v[1].int()) == (1,0x42):
            raise Success

    @TestCase
    def test_container_set_invalid():
        class container(ptype.container): pass
        a = container().set(ptype.type,ptype.type)
        try: a.set(5,10,20)
        except error.AssertionError,e:
            raise Success
        raise Failure

    #@TestCase
    def test_collect_pointers():
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

        result = [z.v[-1].int()]
        for x in z.v[-1].collect():
            result.append(x.l.int())

        if result == [8,4,0,0xfeeddead]:
            raise Success

    #@TestCase
    def test_collect_pointers2():
        import pecoff
        #a = pint.uint32_t()
        #b = a.new(ptype.pointer_t)
        class parentTester(object):
            def __eq__(self, other):
                return other.parent is None or builtins.isinstance(other, ptype.encoded_t) or issubclass(other.__class__, ptype.encoded_t)
        parentTester = parentTester()
        #c = b.getparent(parentTester())
        #print builtins.isinstance(b, ptype.encoded_t)
        a = pecoff.Executable.open('~/mshtml.dll')

        global result
        result = list(a.collect())
        for n in result:
            print n
        #for n in a.traverse(filter=lambda n: parentTester == n):
        #    if builtins.isinstance(n, ptype.encoded_t):
        #        b = n.d.getparent(parentTester)
        #        print b.l
        #        continue
        #    assert n.parent is None
        #    print n.l

    @TestCase
    def test_overcommit_serialize():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in 'ABCD':
            x.value.append( x.new(E).load(source=ptypes.prov.string(d*2)) )
        if x.serialize() == 'AABBCCDD':
            raise Success

    @TestCase
    def test_overcommit_write():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in 'ABCD':
            x.value.append( x.new(E).load(source=ptypes.prov.string(d*2)) )
        source = ptypes.prov.string('\x00'*16)
        x.commit(source=source)
        if source.value == 'AABBCCDD\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Success

    @TestCase
    def test_overcommit_load():
        class E(ptype.type):
            length = 2
        class block(ptype.container):
            def blocksize(self):
                return 4
        x = block(value=[])
        for d in 'ABCD':
            x.value.append( x.new(E).load(source=ptypes.prov.string(d*2)) )
        x.load(source=ptypes.prov.string('E'*16))
        if x.serialize() == 'EEEECCDD':
            raise Success

    @TestCase
    def test_container_append_type():
        class C(ptype.container): pass
        x = C()
        x.append(pint.uint32_t)
        x.append(pint.uint32_t)
        if x.serialize() == '\x00\x00\x00\x00\x00\x00\x00\x00':
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
