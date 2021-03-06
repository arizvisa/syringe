"""Binary-type primitives and containers.

Some parts of a complex data structure are described at a granularity that is
smaller than the atomic "byte" provided by an architecture. This module provides
binary primitives to assist with those types of definitions. Within this module
are 3 basic types. The atomic type that specifies an atomic range of bits. The
array type, which allows one to describe a contiguous list of binary types. And
a structure type, which allows one to describe a container of bits keyed by an
identifier. Each binary type is internally stored as a bitmap. A bitmap is simply
a tuple of (integer-value,number-of-bits). This tuple is abstracted away from the
user, but in some case may be useful to know about.

Each binary type has the same methods as defined by the core ptype module. However,
due to binary types being of different size primitive than the byte type..some of
the methods contain variations that are used to describe the dimensions of a type
by the number of bits. The basic interface for these is:

    class interface(pbinary.type):
        def bitmap(self):
            '''Return ``self`` as a bitmap type'''
        def bits(self):
            '''Return the number of bits. Parallel to .size()'''
        def blockbits(self):
            '''Return the expected number of bits. Parallel to .blocksize()'''
        def setposition(self, position):
            '''Move the binary type to the specified (offset, bit-offset)'''
        def getposition(self):
            '''Return the position of ``self`` as (offset, bit-offset)'''

        .suboffset -- bit offset of ptype

Due to the dimensions of data-structures being along a byte-granularity instead
of a bit-granularity, this module provides an intermediary type that is responsible
for containing any kind of pbinary type. This type is abstracted away from the
user and is created internally when inserting a pbinary type into a regular
byte-granularity ptype. The type is named pbinary.partial, and exposes the
following interface:

    class interface(pbinary.partial):
        byteorder = byte-order-of-type
        _object_ = pbinary-type-that-is-contained

        .object = Returns the pbinary-type that pbinary.partial wraps

Within this module, are two internal types similar to the two types defined within
ptype. These are the .type and .container types. pbinary.type is used to describe
a contiguous range of bits, and pbinary.container is used to describe a container
of pbinary types. When defining a pbinary structure, one can specify either
another pbinary.container or an integer. If an integer is specified, this will
describe the number of bits that the type will represent. These types can be used
in the following two interfaces.

    class interface(pbinary.array):
        _object_ = type
        length = number-of-elements

    class interface(pbinary.struct):
        _fields_ = [
            (type1, 'name1'),
            (integer1, 'name2'),
        ]

Similar to parray, there are types that provided support for sentinel-terminated
and block-sized arrays. These are listed as:

    pbinary.terminatedarray -- .isTerminator(self, value) specifies the sentinel value.
    pbinary.blockarray -- .blockbits(self) returns the number of bits to terminate at.

Another type included by this module is named pbinary.flags. This type is defined
like a pbinary.struct definition, only when it's display..any of it's single bit
fields are displayed when they're True.

Example usage:
# set the byteorder to bigendian
    from ptypes import pbinary,config
    pbinary.setbyteorder(pbinary.config.byteorder.bigendian)

# define an 32-element array of 4-bit sized elements
    class type(pbinary.array):
        _object_ = 4
        length = 32

# define a 2-byte structure
    class type(pbinary.struct):
        _fields_ = [
            (4, 'field1'),
            (2, 'field2'),
            (6, 'field3'),
            (4, 'field4'),
        ]

# define a 16-bit blockarray
    class type(pbinary.blockarray):
        _object_ = 2
        def blockbits(self):
            return 16

# define an array that's terminated when 3 bits are set to 1.
    class type(pbinary.terminatedarray):
        _object_ = 3
        def isTerminator(self, value):
            return value == 7

# define a pbinary flag type
    class type(pbinary.flags):
        _fields_ = [
            (1, 'flag1'),
            (1, 'flag2'),
            (6, 'padding'),
        ]

# instantiate and load a type
    instance = pbinary.new(type)
    instance.load()
"""
import sys, math, types, inspect
import itertools, operator, functools
import six

try:
    from . import ptype

except ImportError:
    # XXX: recursive. yay.
    import ptype

from . import utils, bitmap, config, error, provider

Config = config.defaults
Log = Config.log.getChild('pbinary')
__all__ = 'setbyteorder,istype,iscontainer,new,bigendian,littleendian,align,type,container,array,struct,terminatedarray,blockarray,partial'.split(',')
__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

def setbyteorder(endianness):
    '''Sets the _global_ byte order for any pbinary.type.

    ``endianness`` can be either pbinary.bigendian or pbinary.littleendian
    '''
    global partial
    if endianness in [config.byteorder.bigendian, config.byteorder.littleendian]:
        result = partial.byteorder
        partial.byteorder = config.byteorder.bigendian if endianness is config.byteorder.bigendian else config.byteorder.littleendian
        return result

    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)

    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness {!r}".format(endianness))

## instance tests
if sys.version_info.major < 3:
    @utils.memoize('t')
    def istype(t):
        return t.__class__ is t.__class__.__class__ and not ptype.isresolveable(t) and (isinstance(t, types.ClassType) or hasattr(object, '__bases__')) and issubclass(t, type)
else:
    @utils.memoize('t')
    def istype(t):
        return t.__class__ is t.__class__.__class__ and not ptype.isresolveable(t) and issubclass(t, type)

@utils.memoize('t')
def iscontainer(t):
    return istype(t) and issubclass(t, container)

def force(t, self, chain=[]):
    """Resolve type ``t`` into a pbinary.type for the provided object ``self``"""
    chain = chain[:]
    chain.append(t)

    # conversions
    if bitmap.isinteger(t):
        return ptype.clone(integer, value=(0, t))
    if bitmap.isinstance(t):
        return ptype.clone(integer, value=t)

    # passthrough
    if istype(t) or isinstance(t, type):
        return t

    # functions
    if isinstance(t, types.FunctionType):
        return force(t(self), self, chain)
    if isinstance(t, types.MethodType):
        return force(t(), self, chain)

    if inspect.isgenerator(t):
        return force(six.next(t), self, chain)

    path = str().join(map("<{:s}>".format, self.backtrace()))
    chain_s = "{!s}".format(chain)
    raise error.TypeError(self, 'force<pbinary>', message='chain={!s} : refusing request to resolve {!s} to a type that does not inherit from pbinary.type : {:s}'.format(chain_s, t, path))

class base(ptype.generic):
    """A base class that all binary types with position/size must inherit from.

    This class is responsible for keeping track of the position
    and size of a binary type. Some generic methods are also
    included.
    """

    @classmethod
    def __hash__(cls):
        return hash(cls)

    def new(self, pbinarytype, **attrs):
        res = force(pbinarytype, self)
        return super(base, self).new(res, **attrs)

    ## Methods for fetching and altering the position of a binary type
    __position__ = (0, 0)
    def setoffset(self, value, **options):
        (_, suboffset) = self.getposition()
        return self.setposition((value, suboffset))[0]

    def getoffset(self, **options):
        return self.getposition()[0]

    def getposition(self, **options):
        return self.__position__[:]

    def setposition(self, position, **options):
        (offset, suboffset) = position
        if suboffset >= 8:
            (offset, suboffset) = (offset + (suboffset // 8), suboffset % 8)
        (res, self.__position__) = self.__position__, (offset, suboffset)
        return res

    @property
    def suboffset(self):
        _, suboffset = self.getposition()
        return suboffset
    @suboffset.setter
    def suboffset(self, value):
        offset, _ = self.getposition()
        return self.setposition((offset, value))
    bofs = boffset = suboffset

    def size(self):
        raise error.ImplementationError(self, 'base.size')

    def blocksize(self):
        raise error.ImplementationError(self, 'base.blocksize')

    def contains(self, offset):
        if isinstance(offset, six.integer_types):
            nmin = self.getoffset()
            nmax = nmin + self.blocksize()
            return nmin <= offset < nmax

        offset, sub = offset
        res = offset * 8 + sub
        nmin = self.getoffset() * 8 + self.suboffset
        nmax = nmin + self.blockbits()
        return nmin <= res < nmax

    def initializedQ(self):
        raise error.ImplementationError(self, 'base.initializedQ')

    def copy(self, **attrs):
        result = self.new(self.__class__, position=self.getposition())
        if hasattr(self, '__name__'):
            attrs.setdefault('__name__', self.__name__)
        return result.__update__(attrs)

    def bitmap(self):
        raise error.ImplementationError(self, 'base.bitmap')

    def update(self, value):
        raise error.ImplementationError(self, 'base.update')

    def cast(self, type, **attrs):
        raise error.ImplementationError(self, 'base.cast')

    def __deserialize_consumer__(self, consumer):
        raise error.ImplementationError(self, 'base.__deserialize_consumer__')

    def alloc(self, **attrs):
        raise error.ImplementationError(self, 'base.alloc')

    def load(self, **attrs):
        raise error.ImplementationError(self, 'base.load')

    def commit(self, **attrs):
        raise error.ImplementationError(self, 'base.commit')

    def repr(self, **options):
        raise error.ImplementationError(self, 'base.repr')

    def __getvalue__(self):
        raise error.ImplementationError(self, 'base.__getvalue__')

    def __setvalue__(self, *values, **attrs):
        raise error.ImplementationError(self, 'base.__setvalue__')

    #def __getstate__(self):
    #    return super(type, self).__getstate__(), self.value, self.position,

    #def __setstate__(self, state):
    #    state, self.value, self.position, = state
    #    super(type, self).__setstate__(state)

class type(base):
    """The base instance that all pbinary types with values must inherit from.

    This class is responsible for keeping track of the value
    which should be backed by a bitmap of some kind. Some
    generic methods involving the bitmapped value or the
    display of the bitmapped value is also included.
    """

    def __hash__(self):
        return super(type, self).__hash__() ^ hash(tuple(self.value))

    def size(self):
        return math.trunc(math.ceil(self.bits() / 8.0))

    def blocksize(self):
        return math.trunc(math.ceil(self.blockbits() / 8.0))

    value = None
    def initializedQ(self):
        return self.value is not None

    def copy(self, **attrs):
        return super(type, self).copy(**attrs)

    def __eq__(self, other):
        return isinstance(other, type) and self.initializedQ() and other.initializedQ() and self.__getvalue__() == other.__getvalue__()

    def bitmap(self):
        raise error.ImplementationError(self, 'type.bitmap')

    def __getvalue__(self):
        raise error.ImplementationError(self, 'type.__getvalue__')

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self

        value, = values
        if not bitmap.isinstance(value):
            raise error.TypeError(self, 'type.set', message='The specified value {!r} is not a bitmap'.format(value.__class__))

        self.value = bitmap.new(*value)
        return self

    def repr(self, **options):
        return self.details(**options) if self.initializedQ() else '???'

    def cast(self, type, **attrs):
        if not istype(type):
            raise error.UserError(self, 'type.cast', message='Unable to cast binary type to a none-binary type. : {:s}'.format(type.typename()))

        source = bitmap.consumer()
        source.push(self.bitmap())

        target = self.new(type, __name__=self.name(), position=self.getposition(), **attrs)
        try:
            target.__deserialize_consumer__(source)
        except StopIteration:
            Log.warn('type.cast : {:s} : Incomplete cast to {:s}. Target has been left partially initialized.'.format(self.classname(), target.typename()))
        return target

    def alloc(self, **attrs):
        '''Initialize the binary type with provider.empty()'''
        attrs.setdefault('source', provider.empty())

        with utils.assign(self, **attrs):
            position = self.getposition()
            def repeat(position=position):
                offset, _ = position
                self.source.seek(offset)
                while True:
                    yield self.source.consume(1)
                return

            iterable = repeat()
            consumer = bitmap.consumer(iterable)
            _, boffset = position
            try:
                consumer.consume(boffset)
                result = self.__deserialize_consumer__(consumer)
            except (StopIteration, error.ProviderError) as E:
                raise error.LoadError(self, exception=E)
        return result

    def load(self, **attrs):
        raise error.UserError(self, 'type.load', "Unable to load from a binary-type when reading from a byte-stream. Promote to a partial type and then .load().")

    def commit(self, **attrs):
        raise error.UserError(self, 'type.commit', "Unable to commit from a binary-type when writing to a byte-stream. Promote to a partial type and then .commit().")

    def serialize(self):
        Log.warn('container.serialize : {:s} : Returning a potentially unaligned binary structure as a string'.format(self.classname()))
        return bitmap.data(self.bitmap())

class integer(type):
    """An atomic component of any binary array or structure.

    This type is used internally to represent an element of any binary container.
    """

    def int(self):
        res = self.bitmap()
        return bitmap.value(res)

    def bits(self):
        if self.value is None:
            Log.info("integer.size : {:s} : Refusing to get size of uninitialized type.".format(self.instance()))
            return 0
        res = self.bitmap()
        return bitmap.size(res)

    def blockbits(self):
        if self.value is None:
            return 0
        res = self.bitmap()
        return bitmap.size(res)

    def __deserialize_consumer__(self, consumer):
        try: self.__setvalue__(consumer.consume(self.blockbits()))
        except (StopIteration, error.ProviderError) as E: raise E
        return self

    def summary(self, **options):
        res = self.bitmap()
        return u"({:s},{:d})".format(bitmap.hex(res), bitmap.size(res))

    def details(self, **options):
        res = self.bitmap()
        return bitmap.string(res)

    def __properties__(self):
        result = super(type, self).__properties__()
        if self.initializedQ() and bitmap.signed(self.bitmap()):
            result['signed'] = True
        return result

    def __getvalue__(self):
        if self.value is None:
            raise error.InitializationError(self, '__getvalue__')
        return self.bitmap()

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(integer, self).__setvalue__(*values, **attrs)

        # If an integer was passed to us, then convert it to a bitmap and try again
        value, = values
        if isinstance(value, six.integer_types):

            # check signedness value by the attribute (for backwards compatibility) or the value
            smult = -1 if getattr(self, 'signed', value < 0) else +1

            try: _, size = self.value or (0, self.blockbits() * smult)
            except: size = 0

            res = bitmap.new(value, size)
            return self.__setvalue__(res, **attrs)

        # Otherwise, this is a bitmap and we can proceed to assign it
        if not bitmap.isinstance(value):
            raise error.UserError(self, 'integer.__setvalue__', message='tried to call .__setvalue__ with an unknown type. : {:s}'.format(value.__class__))

        size = bitmap.size(value)
        if size != self.blockbits():
            Log.info("type.__setvalue__ : {:s} : Specified bitmap width is different from typed bitmap width. : {:#x} != {:#x}".format(self.instance(), size, self.blockbits()))

        # check signedness value by the attribute (for backwards compatibility) or the bitmap size
        smult = -1 if getattr(self, 'signed', bitmap.signed(value)) else +1

        res = bitmap.new(bitmap.value(value), size * smult)
        return super(integer, self).__setvalue__(res, **attrs)

    def bitmap(self):
        if self.value is None:
            return None
        return bitmap.new(*self.value)

    def update(self, value):
        if bitmap.isinstance(value):
            self.value = bitmap.new(*value)
            return self
        raise error.UserError(self, 'type.update', message='tried to call .update with an unknown type {:s}'.format(value.__class__))

    def copy(self, **attrs):
        attrs.setdefault('value', self.value[:])
        return super(integer, self).copy(**attrs)

class enum(integer):
    '''
    A pbinary.integer for managing constants used when definiing a binary type.
    i.e. class myinteger(pbinary.enum): width = N

    Settable properties:
        width:int
            This defines the width of the enumeration.
        _values_:array( tuple( name, value ), ... )
            This contains which enumerations are defined.
    '''

    def __init__(self, *args, **kwds):
        super(enum, self).__init__(*args, **kwds)

        # ensure that the enumeration has ._values_ defined
        if not hasattr(self, '_values_'):
            self._values_ = []

        # check that enumeration's ._values_ are defined correctly
        if any(not isinstance(name, six.string_types) or not isinstance(value, six.integer_types) for name, value in self._values_):
            res = map(operator.attrgetter('__name__'), six.string_types)
            stringtypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            res = map(operator.attrgetter('__name__'), six.integer_types)
            inttypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            raise error.TypeError(self, "{:s}.enum.__init__".format(__name__), "{:s}._values_ is of an incorrect format. Should be a list of tuples with the following types. : [({:s}, {:s}), ...]".format(self.typename(), stringtypes, inttypes))

        # collect duplicate values and give a warning if there are any found for a name
        res = {}
        for value, items in itertools.groupby(self._values_, operator.itemgetter(0)):
            res.setdefault(value, set()).update(map(operator.itemgetter(1), items))

        for value, items in res.items():
            if len(items) > 1:
                Log.warning("{:s}.enum : {:s} : {:s}._values_ has more than one value defined for key `{:s}` : {:s}".format(__name__, self.classname(), self.typename(), value, value, ', '.join(res)))
            continue

        # XXX: we could fix all the constants within ._values_ by validating that
        #      they're within the boundaries of our type
        return

    def blockbits(self):
        return getattr(self, 'width', 0 if self.value is None else bitmap.size(self.value))

    def has(self, *value):
        '''Return True if the provided parameter is contained by the enumeration. If no value is provided, then use the current instance.'''
        if not value:
            value = (bitmap.value(self.get()),)
        res, = value

        if isinstance(res, six.string_types):
            return self.__byname__(res, None) == bitmap.value(self.get())
        return self.__byvalue__(res, False) and True or False

    def __byvalue__(self, value, *default):
        '''Internal method to search the enumeration for the name representing the provided value.'''
        if len(default) > 1:
            raise error.TypeError(self, "{:s}.enum.byvalue".format(__name__), "{:s}.byvalue expected at most 3 arguments, got {:d}".format(self.typename(), 2 + len(default)))

        iterable = (name for name, item in self._values_ if item == value)
        try:
            res = six.next(iterable, *default)

        except StopIteration:
            raise KeyError(value)
        return res

    def __byname__(self, name, *default):
        '''Internal method to search the enumeration for the value corresponding to the provided name.'''
        if len(default) > 1:
            raise error.TypeError(self, "{:s}.enum.byname".format(__name__), "{:s}.byname expected at most 3 arguments, got {:d}".format(self.typename(), 2 + len(default)))

        iterable = (value for item, value in self._values_ if item == name)
        try:
            res = six.next(iterable, *default)

        except StopIteration:
            raise KeyError(name)
        return res

    def __getattr__(self, name):
        # if getattr fails, then assume the user wants the value of
        #     a particular enum value
        try:
            res = self.__byname__(name)
            Log.warning("{:s}.enum : {:s} : Using {:s}.attribute for fetching the value for `{:s}` is deprecated.".format(__name__, self.classname(), self.typename(), name))
            return res
        except KeyError: pass
        raise AttributeError(enum, self, name)

    def str(self):
        '''Return enumeration as a string or just the integer if unknown.'''
        res = bitmap.value(self.get())
        return self.__byvalue__(res, u"{:x}".format(res))

    def summary(self, **options):
        res = self.bitmap()
        try: return u"{:s}({:s},{:d})".format(self.__byvalue__(bitmap.value(res)), bitmap.hex(res), bitmap.size(res))
        except (ValueError, KeyError): pass
        return super(enum, self).summary()

    def details(self, **options):
        res = self.get()
        try: return u"{:s} : {:s}".format(self.__byvalue__(bitmap.value(res)), bitmap.string(res))
        except (ValueError, KeyError): pass
        return super(enum, self).details()

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(enum, self).__setvalue__(*values, **attrs)
        value, = values
        res = self.__byname__(value) if isinstance(value, six.string_types) else value
        return super(enum, self).__setvalue__(res, **attrs)

    def __getitem__(self, name):
        '''If a key is specified, then return True if the enumeration actually matches the specified constant'''
        if isinstance(name, six.string_types):
            return self.has(name)
        return False

    @classmethod
    def enumerations(cls):
        '''Return all values in enumeration as a set.'''
        return {value for name, value in cls._values_}

    @classmethod
    def mapping(cls):
        '''Return potential enumeration values as a dictionary.'''
        return {name : value for name, value in cls._values_}

    @classmethod
    def byvalue(cls, value, *default):
        '''Lookup the string in an enumeration by it's first-defined value'''
        if len(default) > 1:
            raise TypeError("{:s}.byvalue expected at most 3 arguments, got {:d}".format(cls.typename(), 2+len(default)))

        try:
            return six.next(name for name, item in cls._values_ if item == value)

        except StopIteration:
            if default: return six.next(iter(default))

        raise KeyError(cls, 'enum.byvalue', value)

    @classmethod
    def byname(cls, name, *default):
        '''Lookup the value in an enumeration by it's first-defined name'''
        if len(default) > 1:
            raise TypeError("{:s}.byname expected at most 3 arguments, got {:d}".format(cls.typename(), 2+len(default)))

        try:
            return six.next(value for item, value in cls._values_ if item == name)

        except StopIteration:
            if default: return six.next(iter(default))

        raise KeyError(cls, 'enum.byname', name)

class container(type):
    '''contains a list of variable-bit integers'''

    ## positioning
    def getposition(self, *field, **options):
        if not len(field):
            return super(container, self).getposition()
        (field,) = field

        # if a path is specified, then recursively get the offset
        if isinstance(field, (tuple, list)):
            (field, res) = (lambda hd, *tl:(hd, tl))(*field)
            return self.__field__(field).getposition(res) if len(res) > 0 else self.getposition(field)

        index = self.__getindex__(field)
        if 0 <= index < len(self.value):
            return self.value[index].getposition()

        # If no fields exist, then just return our current position.
        if not len(self.value):
            return super(container, self).getposition()

        # If our field does not exist, then we must be being asked for the end
        # of the container. So use the last member to calculate the position.
        res = self.value[-1]
        offset, suboffset = res.getposition()
        offset, suboffset = offset, suboffset + res.blockbits()
        return offset + (suboffset // 8), suboffset % 8

    def setposition(self, position, recurse=False):
        (offset, suboffset) = position
        if suboffset >= 8:
            (offset, suboffset) = offset + (suboffset // 8), suboffset % 8
        res = super(container, self).setposition((offset, suboffset))

        if recurse and self.value is not None:
            # FIXME: if the byteorder is little-endian, then this fucks up
            #        the positions pretty hard
            for item in self.value:
                item.setposition((offset, suboffset), recurse=recurse)
                suboffset += item.bits() if item.initializedQ() else item.blockbits()
            pass
        return res

    def copy(self, **attrs):
        """Performs a deep-copy of self repopulating the new instance if self is initialized
        """
        # create an instance of self and update with requested attributes
        result = super(container, self).copy(**attrs)
        result.value = map(operator.methodcaller('copy', **attrs), self.value)
        return result

    def initializedQ(self):
        return super(container, self).initializedQ() and all(item is not None and isinstance(item, type) and item.initializedQ() for item in self.value)

    ### standard stuff
    def int(self):
        res = self.bitmap()
        return bitmap.value(res)

    def bitmap(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.bitmap')
        res = map(operator.methodcaller('bitmap'), self.value)
        return functools.reduce(bitmap.push, filter(None, res), bitmap.new(0, 0))

    def bits(self):
        return sum(item.bits() for item in self.value or [])

    def blockbits(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.blockbits')
        return sum(item.blockbits() for item in self.value)

    def __getindex__(self, key):
        raise error.ImplementationError(self, 'container.__getindex__')

    def __field__(self, key):
        index = self.__getindex__(key)
        if self.value is None:
            raise error.InitializationError(self, 'container.__field__')
        return self.value[index]

    def __getitem__(self, key):
        '''x.__getitem__(y) <==> x[y]'''
        res = self.__field__(key)
        return res if isinstance(res, container) else res.int()

    def item(self, key):
        return self.__field__(key)

    def __getvalue__(self):
        return tuple(item.int() if isinstance(item, type) else item.get() for item in self.value)

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self
        elif len(values) > 1:
            raise error.UserError(self, 'container.set', message="Too many values ({:d}) passed to .set()".format(len(value)))
        value, = values

        # If a bitmap or an integer was passed to us, then break it down and assign
        # to each of our members using the lower-level .__setvalue__() method
        if (bitmap.isinstance(value) or isinstance(value, six.integer_types)):
            result = value if bitmap.isinstance(value) else bitmap.new(value, self.blockbits())
            for item in self.value:
                result, number = bitmap.shift(result, item.bits())
                item.__setvalue__(number)

            if bitmap.size(result) > 0:
                raise error.AssertionError(self, 'container.__setvalue__', message="Some bits were still left over while trying to update bitmap container. : {!r}".format(result))
            return self

        # If a list was passed to us, then just .set() the value to each member
        elif isinstance(value, list):
            for val, item in zip(value, self.value):
                item.set(val)
            return self

        # Otherwise, we'll just fail here because we don't know what to do
        raise error.UserError(self, 'container.set', message='Unable to apply value with an unsupported type ({:s})'.format(value.__class__.__name__))

    def update(self, value):
        result = value if bitmap.isinstance(value) else (value, self.blockbits())
        if bitmap.size(result) != self.blockbits():
            raise error.UserError(self, 'container.update', message="Unable to change size of bitmap container. : {:d} != {:d}".format(bitmap.size(result), self.blockbits()))

        value = self.value if self.initializedQ() else self.a.value
        for item in value:
            result, number = bitmap.shift(result, item.bits())
            item.set(number)

        if bitmap.size(result) > 0:
            raise error.AssertionError(self, 'container.update', message="Some bits were still left over while trying to update bitmap container. : {!r}".format(result))
        return self

    ## loading
    def __deserialize_consumer__(self, consumer, generator):
        '''initialize container object with bitmap /consumer/ using the type produced by /generator/'''
        if self.value is None:
            raise error.SyntaxError(self, 'container.__deserialize_consumer__', message='caller is responsible for pre-allocating the elements in self.value')
        self.value = []

        # FIXME: We should be reading this data at the byte (8bit) boundary and
        #        so we can probably consume objects that have a hardcoded blocksize
        #        first as long as it fits within a byte (or the consumer already has
        #        data cached) so that we can read a field that depends on bits
        #        that follow it
        position = self.getposition()
        for item in generator:
            self.__append__(item)
            item.setposition(position)
            item.__deserialize_consumer__(consumer)

            # FIXME: if the byteorder is little-endian, then this fucks up
            #        the positions pretty hard
            size = item.blockbits()
            offset, suboffset = position
            suboffset += size
            offset, suboffset = (offset + suboffset // 8, suboffset % 8)
            position = (offset, suboffset)
        return self

    def __append__(self, object):
        size = 0 if self.value is None else self.bits()
        offset, suboffset = self.getposition()
        offset, suboffset = res = offset + (size // 8), suboffset + (size % 8)

        object.parent, object.source = self, None
        if object.getposition() != res:
            object.setposition(res, recurse=True)

        if self.value is None:
            self.value = []

        self.value.append(object)
        return res

    ## method overloads
    def __iter__(self):
        if self.value is None:
            raise error.InitializationError(self, 'container.__iter__')

        for item in self.value:
            yield item
        return

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        ## validate the index
        #if not (0 <= index < len(self.value)):
        #    raise IndexError(self, 'container.__setitem__', index)

        # if it's a pbinary element
        if isinstance(value, type):
            res = self.value[index].getposition()
            if value.getposition() != res:
                value.setposition(res, recurse=True)
            value.parent, value.source = self, None
            self.value[index] = value
            return value

        # if element it's being assigned to is a container
        res = self.value[index]
        if not isinstance(res, type):
            raise error.AssertionError(self, 'container.__setitem__', message='Unknown {:s} at index {:d} while trying to assign to it'.format(res.__class__, index))

        # if value is a bitmap
        if bitmap.isinstance(value):
            size = res.blockbits()
            res.update(value)
            if bitmap.size(value) != size:
                self.setposition(self.getposition(), recurse=True)
            return value

        # try update the element with the provided value, because if
        # it doesn't work than it should fail
        return res.set(value)

### generics
class __array_interface__(container):
    length = 0

    def alloc(self, fields=(), **attrs):
        result = super(__array_interface__, self).alloc(**attrs)
        if len(fields) > 0 and isinstance(fields[0], tuple):
            for name, val in fields:
                idx = result.__getindex__(name)
                #if any((istype(val), isinstance(val, type), ptype.isresolveable(val))):
                if istype(val) or ptype.isresolveable(val):
                    result.value[idx] = result.new(val, __name__=name).a
                elif isinstance(val, type):
                    result.value[idx] = result.new(val, __name__=name)
                elif bitmap.isinstance(val):
                    result.value[idx] = result.new(integer, __name__=name).__setvalue__(val)
                else:
                    result.value[idx].set(val)
                continue

        else:
            for idx, val in enumerate(fields):
                name = "{:d}".format(idx)
                #if any((istype(val), isinstance(val, type), ptype.isresolveable(val))):
                if istype(val) or ptype.isresolveable(val) or isinstance(val, type):
                    result.value[idx] = result.new(val, __name__=name)
                elif bitmap.isinstance(val):
                    result.value[idx] = result.new(integer, __name__=name).__setvalue__(val)
                else:
                    result.value[idx].set(val)
                continue

        result.setposition(result.getposition(), recurse=True)
        return result

    def summary(self, **options):
        element, value = self.__element__(), self.bitmap()
        result = bitmap.hex(value) if bitmap.size(value) else '...'
        return ' '.join([element, result])

    def repr(self, **options):
        return self.summary(**options) if self.initializedQ() else ' '.join([self.__element__(), '???'])

    def details(self, **options):
        return self.__details_initialized() if self.initializedQ() else self.__details_uninitialized()

    def __details_initialized(self):
        _hex, _precision, value = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0, self.bitmap()
        # FIXME: instead of emitting just a consolidated bitmap, emit one for each element
        result = "{:#0{:d}b}".format(bitmap.value(value), 2 + bitmap.size(value))
        return u"[{:s}] {:s} ({:s},{:d})".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), self.__element__(), result, bitmap.size(value))

    def __details_uninitialized(self):
        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        return u"[{:s}] {:s} (???,{:d})".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), self.__element__(), self.blockbits())

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        # If we got an InitializationError while fetching the properties (due to
        # a bunk user implementation), then we simply fall back to the internal
        # implementation.
        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        result, element = self.repr(), self.__element__()

        # multiline (includes element description)
        if result.count('\n') > 0 or utils.callable_eq(self.repr, __array_interface__.details):
            result = result.rstrip('\n') # remove trailing newlines
            if prop:
                return "{:s} '{:s}' {{{:s}}} {:s}\n{:s}".format(utils.repr_class(self.classname()), self.name(), prop, element, result)
            return "{:s} '{:s}' {:s}\n{:s}".format(utils.repr_class(self.classname()), self.name(), element, result)

        # if the user chose to not use the default summary, then prefix the element description.
        if all(not utils.callable_eq(self.repr, item) for item in [__array_interface__.repr, __array_interface__.summary, __array_interface__.details]):
            result = ' '.join([element, result])

        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

    def __element__(self):
        try: count = len(self)
        except TypeError: count = None

        object = getattr(self, '_object_', 0)
        if bitmap.isinstance(object):
            result = ('signed<{:d}>' if bitmap.signed(object) else 'unsigned<{:d}>').format(bitmap.size(object))
        elif istype(object):
            result = object.typename()
        elif isinstance(object, six.integer_types):
            result = ('signed<{:d}>' if object < 0 else 'unsigned<{:d}>').format(abs(object))
        else:
            result = object.__name__
        return u"{:s}[{:s}]".format(result, str(count))

    def __getindex__(self, index):
        # check to see if the user gave us a bad type
        if not isinstance(index, six.integer_types):
            raise TypeError(self, '__array_interface__.__getindex__', "Invalid type {!s} specified for index of {:s}.".format(index.__class__, self.typename()))

        ## validate the index
        #if not(0 <= index < len(self.value)):
        #    raise IndexError(self, '__array_interface__.__getindex__', index)

        return index

    ## method overloads
    def __len__(self):
        '''x.__len__() <==> len(x)'''
        if not self.initializedQ():
            return self.length
        return len(self.value)

    def append(self, object):
        '''L.append(object) -- append an element to a pbinary.array and return its position'''
        name = "{!s}".format(len(self.value))
        if bitmap.isinstance(object):
            res = self.new(integer, __name__=name).__setvalue__(object)
        elif isinstance(object, type):
            res = object
        elif istype(object) or ptype.isresolveable(object):
            res = self.new(object, __name__=name).a
        else:
            res = self.new(self._object_, __name__=name).__setvalue__(object)
        return self.__append__(res)

    def __iter__(self):
        '''x.__iter__() <==> iter(x)'''
        for res in super(__array_interface__, self).__iter__():
            yield res if isinstance(res, container) else res.int()
        return

    def __getitem__(self, index):
        '''x.__getitem__(y) <==> x[y]'''
        if isinstance(index, slice):
            res = [ self.value[self.__getindex__(idx)] for idx in range(*index.indices(len(self))) ]
            t = ptype.clone(array, length=len(res), _object_=self._object_)
            return self.new(t, offset=res[0].getoffset(), value=res)
        return super(__array_interface__, self).__getitem__(index)

    def __setitem__(self, index, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if isinstance(index, slice):
            val = itertools.repeat(value) if (isinstance(value, (six.integer_types, type)) or bitmap.isinstance(value)) else iter(value)
            for idx in range(*slice(index.start or 0, index.stop, index.step or 1).indices(index.stop)):
                super(__array_interface__, self).__setitem__(idx, six.next(val))
            return

        value = super(__array_interface__, self).__setitem__(index, value)
        if isinstance(value, type):
            value.__name__ = str(index)
        return

class __structure_interface__(container):
    def __init__(self, *args, **kwds):
        super(__structure_interface__, self).__init__(*args, **kwds)
        self.__fastindex = {}

    def alloc(self, **fields):
        result = super(__structure_interface__, self).alloc()
        if fields:
            for idx, (t, name) in enumerate(self._fields_ or []):
                if name not in fields:
                    if ptype.isresolveable(t):
                        result.value[idx] = result.new(t, __name__=name).a
                    continue
                item = fields[name]
                #if any((istype(item), isinstance(item, type), ptype.isresolveable(item))):
                if istype(item) or ptype.isresolveable(item):
                    result.value[idx] = result.new(item, __name__=name).a
                elif isinstance(item, type):
                    result.value[idx] = result.new(item, __name__=name)
                elif bitmap.isinstance(item):
                    result.value[idx] = result.new(integer, __name__=name).__setvalue__(item)
                elif isinstance(item, dict):
                    result.value[idx].alloc(**item)
                else:
                    result.value[idx].set(item)
                continue
            self.setposition(self.getposition(), recurse=True)
        return result

    def __append__(self, object):
        current = len(self.value)
        position = super(__structure_interface__, self).__append__(object)
        self.__fastindex[object.name().lower()] = current
        return position

    def alias(self, alias, target):
        """Add an alias from /alias/ to the field /target/"""
        res = self.__getindex__(target)
        self.__fastindex[alias.lower()] = res
    def unalias(self, alias):
        """Remove the alias /alias/ as long as it's not defined in self._fields_"""
        if any(alias.lower() == name.lower() for _, name in self._fields_ or []):
            raise error.UserError(self, '__structure_interface__.__contains__', message='Not allowed to remove {:s} from list of aliases.'.format(alias.lower()))
        del self.__fastindex[alias.lower()]

    def __getindex__(self, name):
        if not isinstance(name, six.string_types):
            raise error.UserError(self, '__structure_interface__.__getindex__', message='Element names must be a string type. : {!r}'.format(name.__class__))
        try:
            return self.__fastindex[name.lower()]
        except KeyError:
            for index, (_, fld) in enumerate(self._fields_ or []):
                if fld.lower() == name.lower():
                    return self.__fastindex.setdefault(name.lower(), index)
                continue
        raise KeyError(name)

    def details(self, **options):
        return self.__details_initialized(**options) if self.initializedQ() else self.__details_uninitialized(**options)

    def repr(self, **options):
        return self.details() + '\n'

    def summary(self, **options):
        if self.value is None:
            return u"???"
        res = self.bitmap()

        items = [u"{:s}={:s}".format(value.name() if fld is None else fld[1], u"???" if value is None else value.summary()) for fld, value in __izip_longest__(self._fields_ or [], self.value)]
        if items:
            return u"({:s},{:d}) :> {:s}".format(bitmap.hex(res), bitmap.size(res), ' '.join(items))
        return u"({:s},{:d})".format(bitmap.hex(res), bitmap.size(res))

    def __details_initialized(self):
        result = []

        for fld, value in __izip_longest__(self._fields_ or [], self.value):
            t, name = fld or (value.__class__, value.name())
            if value is None:
                if istype(t):
                    typename = t.typename()
                elif bitmap.isinstance(t):
                    typename = 'signed<{:s}>'.format(bitmap.size(t)) if bitmap.signed(t) else 'unsigned<{:s}>'.format(bitmap.size(t))
                elif isinstance(t, six.integer_types):
                    typename = 'signed<{:d}>'.format(t) if t < 0 else 'unsigned<{:d}>'.format(t)
                else:
                    typename = 'unknown<{!r}>'.format(t)

                i, position = utils.repr_class(typename), self.getposition(name)
                _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
                result.append(u"[{:s}] {:s} {:s} ???".format(utils.repr_position(position, hex=_hex, precision=_precision), i, name))
                continue

            b = value.bitmap()
            i, position = utils.repr_instance(value.classname(), value.name() or name), self.getposition(value.__name__ or name)
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in value.properties().items())
            _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
            result.append(u"[{:s}] {:s}{:s} {:s}".format(utils.repr_position(position, hex=_hex, precision=_precision), i, u' {{{:s}}}'.format(prop) if prop else u'', value.summary()))
        if result:
            return '\n'.join(result)
        return u"[{:x}] Empty[]".format(self.getoffset())

    def __details_uninitialized(self):
        result = []
        for t, name in self._fields_ or []:
            if istype(t):
                cb, typename = self.new(t).blockbits(), t.typename()
            elif bitmap.isinstance(t):
                cb, typename = bitmap.size(t), 'signed' if bitmap.signed(t) else 'unsigned'
            elif isinstance(t, six.integer_types):
                cb, typename = abs(t), 'signed' if t < 0 else 'unsigned'
            else:
                cb, typename = 0, 'unknown'

            i = utils.repr_class(typename)
            _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
            result.append(u"[{:s}] {:s} {:s}{{{:d}}} ???".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), i, name, cb))
        if result:
            return '\n'.join(result)
        return u"[{:x}] Empty{{}} ???".format(self.getoffset())

    ## list methods
    def keys(self):
        '''D.keys() -> list of all of the names of D's fields'''
        return [name for name in self.__keys__()]
    def values(self):
        '''D.keys() -> list of all of the values of D's fields'''
        return [res for res in self.__values__()]
    def items(self):
        '''D.items() -> list of D's (name, value) fields, as 2-tuples'''
        return [(name, item) for name, item in self.__items__()]

    ## iterator methods
    def iterkeys(self):
        '''D.iterkeys() -> an iterator over the names of D's fields'''
        for name in self.__keys__(): yield name
    def itervalues(self):
        '''D.itervalues() -> an iterator over the values of D's fields'''
        for res in self.__values__(): yield res
    def iteritems(self):
        '''D.iteritems() -> an iterator over the (name, value) fields of D'''
        for name, value in self.__items__(): yield name, value

    ## internal dict methods
    def __keys__(self):
        for _, name in self._fields_ or []:
            yield name
        return
    def __values__(self):
        for item in self.value:
            yield item if isinstance(item, container) else item.int()
        return
    def __items__(self):
        #for (_, name), item in zip(self._fields_ or [], self.__values__()):
        for (_, name), item in zip(self._fields_ or [], self.value):
            yield name, item
        return

    ## method overloads
    def __contains__(self, name):
        '''D.__contains__(k) -> True if D has a field named k, else False'''
        if not isinstance(name, six.string_types):
            raise error.UserError(self, '__structure_interface__.__contains__', message='Element names must be of a str type.')
        return name in self.__fastindex

    def __iter__(self):
        '''D.__iter__() <==> iter(D)'''
        if self.value is None:
            raise error.InitializationError(self, '__structure_interface__.__iter__')

        for name in six.iterkeys(self):
            yield name
        return

    def __setitem__(self, name, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        index = self.__getindex__(name)
        value = super(__structure_interface__, self).__setitem__(index, value)
        if isinstance(value, type):
            value.__name__ = name
        return value

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        # If we got an InitializationError while fetching the properties (due to
        # a bunk user implementation), then we simply fall back to the internal
        # implementation.
        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        result = self.repr()

        # multline
        if result.count('\n') > 0:
            result = result.rstrip('\n') # removing trailing newlines

            if prop:
                return u"{:s} '{:s}' {{{:s}}}\n{:s}".format(utils.repr_class(self.classname()), self.name(), prop, result)
            return u"{:s} '{:s}'\n{:s}".format(utils.repr_class(self.classname()), self.name(), result)

        _hex, _precision = Config.pbinary.offset == config.partial.hex, 3 if Config.pbinary.offset == config.partial.fractional else 0
        # single-line
        descr = u"{:s} '{:s}'".format(utils.repr_class(self.classname()), self.name()) if self.value is None else utils.repr_instance(self.classname(), self.name())
        if prop:
            return u"[{:s}] {:s} {{{:s}}} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr,  prop, result)
        return u"[{:s}] {:s} {:s}".format(utils.repr_position(self.getposition(), hex=_hex, precision=_precision), descr, result)

    #def __getstate__(self):
    #    return super(__structure_interface__, self).__getstate__(), self.__fastindex

    #def __setstate__(self, state):
    #    state, self.__fastindex, = state
    #    super(__structure_interface__, self).__setstate__(state)

class array(__array_interface__):
    length = 0

    def copy(self, **attrs):
        """Performs a deep-copy of self repopulating the new instance if self is initialized"""
        result = super(array, self).copy(**attrs)
        result._object_ = self._object_
        result.length = self.length
        return result

    def __setvalue__(self, *values, **attrs):
        if not values:
            return self

        items, = values
        if self.initializedQ():
            iterable = iter(items) if isinstance(items, (tuple, list)) and len(items) > 0 and isinstance(items[0], tuple) else iter(enumerate(items))
            for idx, value in iterable:
                if istype(value) or ptype.isresolveable(value) or isinstance(value, type):
                    self.value[idx] = self.new(value, __name__=str(idx))
                else:
                    self[idx] = value
                continue
            self.setposition(self.getposition(), recurse=True)
            return self

        self.value = result = []
        for idx, value in enumerate(items):
            name = "{:d}".format(idx)
            if istype(value) or ptype.isresolveable(value):
                res = self.new(value, __name__=name).a
            elif isinstance(value, type):
                res = self.new(value, __name__=name)
            else:
                res = self.new(self._object_, __name__=name).a.set(value)
            self.value.append(res)

        self.length = len(self.value)
        return self

    def __deserialize_consumer__(self, consumer):
        position = self.getposition()
        obj = getattr(self, '_object_', 0)
        self.value = []
        generator = (self.new(obj, __name__=str(index), position=position) for index in range(self.length))
        return super(array, self).__deserialize_consumer__(consumer, generator)

    def blockbits(self):
        if self.initializedQ():
            return super(array, self).blockbits()

        res = self._object_
        if isinstance(res, six.integer_types):
            size = abs(res)
        elif bitmap.isinstance(res):
            size = bitmap.size(res)
        elif istype(res):
            size = self.new(res).blockbits()
        else:
            raise error.InitializationError(self, 'array.blockbits')
        return size * len(self)

    #def __getstate__(self):
    #    return super(array, self).__getstate__(), self._object_, self.length

    #def __setstate__(self, state):
    #    state, self._object_, self.length, = state
    #    super(array, self).__setstate__(state)

class struct(__structure_interface__):
    _fields_ = None

    def copy(self, **attrs):
        result = super(struct, self).copy(**attrs)
        result._fields_ = self._fields_[:]
        return result

    def __deserialize_consumer__(self, consumer):
        self.value = []
        position = self.getposition()
        generator = (self.new(t, __name__=name, position=position) for t, name in self._fields_ or [])
        return super(struct, self).__deserialize_consumer__(consumer, generator)

    def blockbits(self):
        if self.initializedQ():
            return super(struct, self).blockbits()
        # FIXME: self.new(t) can potentially execute a function that it shouldn't
        #        when .blockbits() is called by .__load_littleendian
        return sum((abs(t) if isinstance(t, six.integer_types) else bitmap.size(t) if bitmap.isinstance(t) else self.new(t).blockbits()) for t, _ in self._fields_ or [])

    def __and__(self, field):
        '''Used to test the value of the specified field'''
        return operator.getitem(self, field)

    def __setvalue__(self, *values, **fields):
        result = self
        value, = values or ((),)

        def assign(pack_indexvalue):
            (index, value) = pack_indexvalue
            if istype(value) or ptype.isresolveable(value):
                name = result.value[index].__name__
                result.value[index] = result.new(value, __name__=name).a
            elif isinstance(value, type):
                name = result.value[index].__name__
                result.value[index] = result.new(value, __name__=name)
            elif isinstance(value, dict):
                result.value[index].set(**value)
            else:
                result.value[index].set(value)
            return

        if result.initializedQ():
            if isinstance(value, dict):
                value = fields.update(value)

            if value:
                if len(result._fields_) != len(value):
                    raise error.UserError(result, 'struct.set', message='Refusing to assign iterable to instance due to different lengths')
                [ assign((index, value)) for index, value in enumerate(value) ]

            [ assign((self.__getindex__(name), item)) for name, item in fields.items() ]
            result.setposition(result.getposition(), recurse=True)
            return result
        return result.a.__setvalue__(value, **fields)

    #def __getstate__(self):
    #    return super(struct, self).__getstate__(), self._fields_,

    #def __setstate__(self, state):
    #    state, self._fields_, = state
    #    super(struct, self).__setstate__(state)

class terminatedarray(__array_interface__):
    length = None

    def alloc(self, fields=(), **attrs):
        attrs.setdefault('length', len(fields))
        attrs.setdefault('isTerminator', lambda value: False)
        return super(terminatedarray, self).alloc(fields, **attrs)

    def __deserialize_consumer__(self, consumer):
        self.value = []
        obj = self._object_
        forever = itertools.count() if self.length is None else range(self.length)
        position = self.getposition()

        def generator():
            for index in forever:
                item = self.new(obj, __name__=str(index), position=position)
                yield item
                if self.isTerminator(item):
                    break
                continue
            return

        iterable = generator()
        try:
            return super(terminatedarray, self).__deserialize_consumer__(consumer, iterable)

        # terminated arrays can also stop when out-of-data
        except StopIteration as E:
            item = self.value[-1]
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.info("terminatedarray : {:s} : Terminated at {:s}<{:x}:+??>\n\t{:s}".format(self.instance(), item.typename(), item.getoffset(), path))

        return self

    def isTerminator(self, item):
        '''Intended to be overloaded. Should return True if value ``item`` represents the end of the array.'''
        raise error.ImplementationError(self, 'terminatedarray.isTerminator')

    def blockbits(self):

        # If the user implement a custom .blocksize() method, then use that to
        # calculate the number of bits.
        if not utils.callable_eq(self.blocksize, container.blocksize):
            return 8 * self.blocksize()

        # If we're initialized, we can figure out how many bits we are by
        # asking our parent class.
        if self.initializedQ():
            return super(terminatedarray, self).blockbits()

        # Otherwise, we need to calculate this ourselves. We do this by taking
        # the product of our length and our element size.
        return 0 if self.length is None else self.new(self._object_).blockbits() * len(self)

class blockarray(terminatedarray):
    length = None

    def alloc(self, fields=(), **attrs):
        # Make sure we use the regular allocator that doesn't set any
        # attributes required for the terminated array.
        return super(terminatedarray, self).alloc(fields, **attrs)

    def isTerminator(self, value):
        return False

    def __deserialize_consumer__(self, consumer):
        obj, position = getattr(self, '_object_', 0), self.getposition()
        total = self.blockbits()
        value = self.value = []
        forever = itertools.count() if self.length is None else range(self.length)
        generator = (self.new(obj, __name__=str(index), position=position) for index in forever)

        # fork the consumer
        consumer = bitmap.consumer().push((consumer.consume(total), total))

        try:
            while total > 0:
                item = six.next(generator, None)
                if item is None:
                    break

                item.setposition(position)
                value.append(item)

                item.__deserialize_consumer__(consumer)
                if self.isTerminator(item):
                    break

                size = item.blockbits()
                total -= size

                # FIXME: if the byteorder is little-endian, then this fucks up
                #        the positions pretty hard
                (offset, suboffset) = position
                suboffset += size
                offset, suboffset = (offset + suboffset // 8, suboffset % 8)
                position = (offset, suboffset)

            if total < 0:
                Log.info('blockarray.__deserialize_consumer__ : {:s} : Read {:d} extra bits'.format(self.instance(), -total))

        except StopIteration as E:
            # FIXME: fix this error: total bits, bits left, byte offset: bit offset
            Log.warn('blockarray.__deserialize_consumer__ : {:s} : Incomplete read at {!r} while consuming {:d} bits'.format(self.instance(), position, item.blockbits()))
        return self

class partial(ptype.container):
    value = None
    _object_ = None
    byteorder = config.byteorder.bigendian
    initializedQ = lambda s: isinstance(s.value, list) and len(s.value) > 0 and s.value[0].initializedQ()
    __pb_attribute = None

    def __pb_object(self, **attrs):
        offset, obj = self.getoffset(), force(self._object_, self)
        res = {}

        # first include the type's attributes, then any user-supplied ones
        [ res.update(item) for item in [self.attributes, attrs] ]

        # then we'll add our current position, and our parent for the trie
        list(itertools.starmap(res.__setitem__, (('position', (offset, 0)), ('parent', self))))

        # if the user added a custom blocksize, then propagate that too
        if not utils.callable_eq(self.blocksize, partial.blocksize):
            res.setdefault('blocksize', self.blocksize)

        # if we're named either by a field or explicitly, then propagate this
        # name to our attributes as well
        if getattr(self, '__name__', ''):
            res.setdefault('__name__', self.__name__)

        # now we can finally construct our object using the attributes we
        # determined
        return obj(**res)

    def __update__(self, attrs={}, **moreattrs):
        res = dict(attrs)
        res.update(moreattrs)

        localkey, pbkey = set(), set()
        for key in res.keys():
            F = localkey.add if hasattr(self, key) else pbkey.add
            F(key)

        localdata = {key : res[key] for key in localkey}
        pbdata = {key : res[key] for key in pbkey}
        if 'recurse' in res:
            localdata['recurse'] = pbdata['recurse'] = res['recurse']

        super(partial, self).__update__(localdata)
        if self.initializedQ():
            self.object.__update__(pbdata)
        return self

    def copy(self, **attrs):
        result = super(partial, self).copy(**attrs)
        result._object_ = self._object_
        result.byteorder = self.byteorder
        return result

    @property
    def object(self):
        if isinstance(self.value, list) and len(self.value):
            res, = self.value
            return res
        return None

    @object.setter
    def object(self, obj):

        # Figure out the attributes we need to copy
        res = dict(self.attributes)

        # now we'll add our current position, and our parent for the trie
        list(itertools.starmap(res.__setitem__, (('position', (self.getoffset(), 0)), ('parent', self))))

        # if the user added a custom blocksize, then propagate that too
        if not utils.callable_eq(self.blocksize, partial.blocksize):
            res.setdefault('blocksize', self.blocksize)

        # if we're named either by a field or explicitly, then propagate this
        # name to our attributes as well
        if getattr(self, '__name__', ''):
            res.setdefault('__name__', self.__name__)

        # now we can pivot our object using the attributes we determined
        self.value = [ obj.__update__(**res) ]

    o = object

    def serialize(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.serialize')

        res = self.object.bitmap()
        if self.byteorder is config.byteorder.bigendian:
            return bitmap.data(res)
        if self.byteorder is not config.byteorder.littleendian:
            raise error.AssertionError(self, 'partial.serialize', message='byteorder {:s} is invalid'.format(self.byteorder))
        return bytes(bytearray(reversed(bitmap.data(res))))

    def __deserialize_block__(self, block):
        self.value = res = [self.__pb_object()]
        data = iter(block) if self.byteorder is config.byteorder.bigendian else reversed(block)
        res = res[0].__deserialize_consumer__(bitmap.consumer(data))
        if res.parent is not self:
            raise error.AssertionError(self, 'partial.__deserialize_block__', message="parent for binary type {:s} is not {:s}".format(res[0].instance(), self.instance()))
        return res.parent

    def load(self, **attrs):
        '''Load a pbinary.partial using the current source'''
        try:
            self.value = [self.__pb_object()]
            result = self.__load_bigendian(**attrs) if self.byteorder is config.byteorder.bigendian else self.__load_littleendian(**attrs)
            result.setoffset(result.getoffset())
            return result

        except (StopIteration, error.ProviderError) as E:
            raise error.LoadError(self, exception=E)

    def __load_bigendian(self, **attrs):
        # big-endian. stream-based
        if self.byteorder is not config.byteorder.bigendian:
            raise error.AssertionError(self, 'partial.load', message='byteorder {:s} is invalid'.format(self.byteorder))

        with utils.assign(self, **attrs):
            offset = self.getoffset()
            self.source.seek(offset)
            bc = bitmap.consumer(self.source.consume(1) for index in itertools.count())
            self.object.__deserialize_consumer__(bc)
        return self

    def __load_littleendian(self, **attrs):
        # little-endian. block-based
        if self.byteorder is not config.byteorder.littleendian:
            raise error.AssertionError(self, 'partial.load', message='byteorder {:s} is invalid'.format(self.byteorder))

        # XXX: self.new(t) can potentially get called due to this call to self.blocksize().
        #      This can cause a field's closure to get called and raise an InitializationError().

        # FIXME: check to see if there's a dynamic type that needs to be resolved
        #        and if so, throw up an error that explains why you can't use dynamic
        #        types with a non-constant in a little-endian binary type.
        with utils.assign(self, **attrs):
            offset, size = self.getoffset(), self.blocksize()
            self.source.seek(offset)
            data = bytes(bytearray(reversed(self.source.consume(size))))
            bc = bitmap.consumer(data)
            self.object.__deserialize_consumer__(bc)
        return self

    def commit(self, **attrs):
        try:
            with utils.assign(self, **attrs):
                self.source.seek(self.getoffset())
                data = self.serialize()
                self.source.store(data)
            return self

        except (StopIteration, error.ProviderError) as E:
            raise error.CommitError(self, exception=E)

    def alloc(self, *args, **attrs):
        '''Load a pbinary.partial using the provider.empty source'''
        try:
            self.value = [self.__pb_object()]
            self.object.alloc(*args, **attrs)
            return self

        except (StopIteration, error.ProviderError) as E:
            raise error.LoadError(self, exception=E)

    def bits(self):
        return 8 * self.size()
    def blockbits(self):
        return 8 * self.blocksize()

    def size(self):
        value = self.value[0] if self.initializedQ() else self.__pb_object()
        size = value.bits()
        res = (size) if (size & 7) == 0x0 else ((size + 8) & ~7)
        return res // 8
    def blocksize(self):
        value = self.value[0] if self.initializedQ() else self.__pb_object()
        size = value.blockbits()
        res = (size) if (size & 7) == 0x0 else ((size + 8) & ~7)
        return res // 8

    def __properties__(self):
        result = super(partial, self).__properties__()
        if self.initializedQ():
            res, = self.value
            if res.bits() != self.blockbits():
                result['unaligned'] = True
            result['bits'] = res.bits()
        result['partial'] = True

        # endianness
        if 'bits' not in result or result['bits'] > 8:
            if self.byteorder is config.byteorder.bigendian:
                result['byteorder'] = 'big'
            else:
                if self.byteorder is not config.byteorder.littleendian:
                    raise error.AssertionError(self, 'partial.properties', message='byteorder {:s} is invalid'.format(self.byteorder))
                result['byteorder'] = 'little'
        return result

    ## methods to passthrough if the object is initialized
    def summary(self, **options):
        return u"???" if not self.initializedQ() else self.object.summary(**options)
    def details(self, **options):
        return u"???" if not self.initializedQ() else self.object.details(**options)
    def repr(self, **options):
        return u"???" if not self.initializedQ() else self.object.repr(**options)

    def __len__(self):
        '''x.__len__() <==> len(x)'''
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__len__')
        return len(self.object)

    def __field__(self, key):
        return self.object.__field__(key)

    def __getitem__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__getitem__')
        return self.object[name]
    def __setitem__(self, name, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__setitem__')
        self.object[name] = value

    def __iter__(self):
        '''x.__iter__() <==> iter(x)'''
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__iter__')

        for item in self.object:
            yield item
        return

    def __repr__(self):
        """Calls .repr() to display the details of a specific object"""
        try:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.properties().items())

        # If we got an InitializationError while fetching the properties (due to
        # a bunk user implementation), then we simply fall back to the internal
        # implementation.
        except error.InitializationError:
            prop = ','.join(u"{:s}={!r}".format(k, v) for k, v in self.__properties__().items())

        result = self.object.repr() if self.initializedQ() else self.repr()

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

    def __getvalue__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__getvalue__')
        return self.object.get()
    def __setvalue__(self, *values, **attrs):
        if not self.initializedQ():
            raise error.InitializationError(self, 'partial.__setvalue__')
        return self.object.set(*values, **attrs)
    def __getattr__(self, name):
        if not self.initializedQ():
            return object.__getattribute__(self, name)
        return getattr(self.object, name)

    def classname(self):
        fmt = {
            config.byteorder.littleendian : Config.pbinary.littleendian_name,
            config.byteorder.bigendian : Config.pbinary.bigendian_name,
        }
        if self.initializedQ():
            res, = self.value
            cn = res.classname()
        else:
            cn = self._object_.typename() if istype(self._object_) else self._object_ if isinstance(self._object_, six.integer_types) else self._object_.__name__
        return fmt[self.byteorder].format(cn, **(utils.attributes(self) if Config.display.mangle_with_attributes else {}))

    def contains(self, offset):
        """True if the specified ``offset`` is contained within"""
        nmin = self.getoffset()
        nmax = nmin + self.blocksize()
        return (offset >= nmin) and (offset < nmax)

    #def __getstate__(self):
    #    return super(partial, self).__getstate__(), self._object_, self.position, self.byteorder,

    #def __setstate__(self, state):
    #    state, self._object_, self.position, self.byteorder, = state
    #    super(type, self).__setstate__(state)

    def setposition(self, offset, recurse=False):
        if self.initializedQ():
            self.object.setposition((offset[0], 0), recurse=recurse)
        return super(partial, self).setposition(offset, recurse=False)

class flags(struct):
    '''represents bit flags that can be toggled'''
    def summary(self, **options):
        return self.__summary_initialized() if self.initializedQ() else self.__summary_uninitialized()

    def __summary_initialized(self):
        flags = []
        for (t, name), value in zip(self._fields_ or [], self.value):
            flags.append((name, value))
        res, fval = self.bitmap(), lambda item: '?' if item is None else '={:s}'.format(item.str()) if isinstance(item, enum) else '={:d}'.format(item.int()) if item.int() > 1 else ''
        items = [(name, item) for name, item in flags if item is None or isinstance(item, enum) or item.int() > 0]
        if items:
            return u"({:s},{:d}) :> {:s}".format(bitmap.hex(res), bitmap.size(res), ' '.join(map(str().join, ((name, fval(item)) for name, item in items))))
        return u"({:s},{:d})".format(bitmap.hex(res), bitmap.size(res))

    def __summary_uninitialized(self):
        return u"(?,{:d}) :> {:s}".format(self.blockbits(), ','.join(u"?{:s}".format(name) for t, name in self._fields_ or []))

    def __and__(self, field):
        '''Used to test the value of the specified field'''
        res = operator.getitem(self, field)
        return bool(res > 0)

## binary type conversion/generation
def new(pb, **attrs):
    '''Create a new instance of /pb/ applying the attributes specified by /attrs/'''
    # create a partial type
    if istype(pb):
        Log.debug("{:s}.new : Explicitly instantiating partial container for binary type `{:s}`.".format(__name__, pb.typename()))
        t = ptype.clone(partial, _object_=pb)
        return t(**attrs)

    # create a partial type for the specified pbinary instance
    if isinstance(pb, type):
        Log.debug("{:s}.new : Promoting binary type for `{:s}` to a partial type.".format(__name__, pb.typename()))
        attrs.setdefault('object', pb)
        attrs.setdefault('offset', pb.getposition()[0])
        t = ptype.clone(partial, _object_=pb.__class__)
        return t(**attrs)

    return pb(**attrs)

def bigendian(p, **attrs):
    '''Force binary type /p/ to be ordered in the bigendian integer format'''
    attrs.setdefault('byteorder', config.byteorder.bigendian)
    attrs.setdefault('__name__', p._object_.__name__ if issubclass(p, partial) else p.__name__)

    if not issubclass(p, partial):
        Log.debug("{:s}.bigendian : Explicitly promoting binary type for `{:s}` to a partial type.".format(__name__, p.typename()))
        return ptype.clone(partial, _object_=p, **attrs)
    return ptype.clone(p, **attrs)

def littleendian(p, **attrs):
    '''Force binary type /p/ to be ordered in the littleendian integer format'''
    attrs.setdefault('byteorder', config.byteorder.littleendian)
    attrs.setdefault('__name__', p._object_.__name__ if issubclass(p, partial) else p.__name__)

    if not issubclass(p, partial):
        Log.debug("{:s}.littleendian : Explicitly promoting binary type for `{:s}` to a partial type.".format(__name__, p.typename()))
        return ptype.clone(partial, _object_=p, **attrs)
    return ptype.clone(p, **attrs)

def align(bits):
    '''Returns a type that will align fields to the specified bit size'''
    def align(self):
        b = self.bits()
        r = b % bits
        if r == 0:
            return 0
        return bits - r
    return align

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
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes,struct
    from ptypes import pbinary,provider,pstruct,pint,bitmap
    prov = provider

    TESTDATA = b'ABCDIEAHFLSDFDLKADSJFLASKDJFALKDSFJ'

    def fn(self):
        return self['size']

    class RECT(pbinary.struct):
        _fields_ = [
            (4, 'size'),
            (fn, 'value1'),
            (fn, 'value2'),
            (fn, 'value3'),
        ]

    class nibble(pbinary.struct):
        _fields_ = [
            (4, 'value')
        ]

    class byte(pbinary.struct):
        _fields_ = [
            (8, 'value')
        ]

    class word(pbinary.struct):
        _fields_ = [
            (8, 'high'),
            (8, 'low'),
        ]

    class dword(pbinary.struct):
        _fields_ = [
            (16, 'high'),
            (16, 'low')
        ]

    @TestCase
    def test_pbinary_struct_load_be_global_1():
        pbinary.setbyteorder(config.byteorder.bigendian)
        x = pbinary.new(RECT,source=provider.bytes(b'\x4a\xbc\xde\xf0'))
        x = x.l

        if (x['size'],x['value1'],x['value2'],x['value3']) == (4,0xa,0xb,0xc):
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_struct_dynamic_load_2():
        ### inline bitcontainer pbinary.structures
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'header'),
                (RECT, 'rectangle'),
                (lambda self: self['rectangle']['size'], 'heh')
            ]

        s = b'\x44\xab\xcd\xef\x00'

        a = pbinary.new(blah,source=provider.bytes(s)).l

        b = a['rectangle']

        if a['header'] == 4 and (b['size'],b['value1'],b['value2'],b['value3']) == (4,0xa,0xb,0xc):
            raise Success

    @TestCase
    def test_pbinary_struct_be_3():
        #### test for integer endianness
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 0000 0001 1011 1111
        data = b'\x01\xbf'
        res = pbinary.new(blah,source=provider.bytes(data)).l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

    @TestCase
    def test_pbinary_struct_le_4():
        class blah(pbinary.struct):
            _fields_ = [
                (10, 'type'),
                (6, 'size')
            ]

        # 1011 1111 0000 0001
        data = b'\xbf\x01'
        a = blah
        res = pbinary.littleendian(blah)
        b = res
        res = res()

        data = itertools.islice(data, res.a.size())
        res.source = provider.bytes(bytes(bytearray(data)))
        res.l

        if res['type'] == 6 and res['size'] == 0x3f:
            raise Success

    @TestCase
    def test_pbinary_struct_be_5():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (4, 'blah1'),
                (4, 'blah2'),
                (4, 'blah3'),
                (4, 'blah4'),
                (8, 'blah5'),
                (4, 'blah6')
            ]

        data = b'\xaa\xbb\xcc\xdd\x11\x11'

        res = pbinary.new(blah,source=provider.bytes(data)).l

        if res.values() == [0xa,0xa,0xb,0xb,0xc,0xcd, 0xd]:
            raise Success

    @TestCase
    def test_pbinary_struct_le_6():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (4, 'blah1'),
                (4, 'blah2'),
                (4, 'blah3'),
                (4, 'blah4'),
                (8, 'blah5'),
                (4, 'blah6')
            ]
        data = b'\xdd\xcc\xbb\xaa\x11\x11'
        res = blah
        res = pbinary.littleendian(res)
        res = res(source=provider.bytes(data))
        res = res.l

        if res.values() == [0xa, 0xa, 0xb, 0xb, 0xc, 0xcd, 0xd]:
            raise Success

    @TestCase
    def test_pbinary_struct_unaligned_7():
        x = pbinary.new(RECT, source=provider.bytes(b'hello world')).l
        if x['size'] == 6 and x.size() == (4 + 6*3 + 7)//8:
            raise Success
        return

    @TestCase
    def test_pbinary_array_int_load_8():
        class blah(pbinary.array):
            _object_ = bitmap.new(0, 3)
            length = 3

        s = b'\xaa\xbb\xcc'

        x = pbinary.new(blah,source=provider.bytes(s)).l
        if list(x.object) == [5, 2, 5]:
            raise Success

    @TestCase
    def test_pbinary_struct_bitoffsets_9():
        # print out bit offsets for a pbinary.struct

        class halfnibble(pbinary.struct): _fields_ = [(2, 'value')]
        class tribble(pbinary.struct): _fields_ = [(3, 'value')]
        class nibble(pbinary.struct): _fields_ = [(4, 'value')]

        class byte(pbinary.array):
            _object_ = halfnibble
            length = 4

        class largearray(pbinary.array):
            _object_ = byte
            length = 16

        res = functools.reduce(lambda x,y: x<<1 | [0,1][int(y)], ('11001100'), 0)
        items = bytearray([res] * 63)

        x = pbinary.new(largearray, source=provider.bytes(bytes(items))).l
        if x[5].int() == res:
            raise Success

    @TestCase
    def test_pbinary_struct_load_10():
        self = pbinary.new(dword,source=provider.bytes(b'\xde\xad\xde\xaf')).l
        if self['high'] == 0xdead and self['low'] == 0xdeaf:
            raise Success

    @TestCase
    def test_pbinary_struct_recurse_11():
        ## a struct containing a struct
        class blah(pbinary.struct):
            _fields_ = [
                (word, 'higher'),
                (word, 'lower'),
            ]
        self = pbinary.new(blah,source=provider.bytes(b'\xde\xad\xde\xaf')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower']['high'] == 0xde and self['lower']['low'] == 0xaf:
            raise Success

    @TestCase
    def test_pbinary_struct_dynamic_12():
        ## a struct containing functions
        class blah(pbinary.struct):
            _fields_ = [
                (lambda s: word, 'higher'),
                (lambda s: 8, 'lower')
            ]

        self = pbinary.new(blah,source=provider.bytes(b'\xde\xad\x80')).l
        if self['higher']['high'] == 0xde and self['higher']['low'] == 0xad and self['lower'] == 0x80:
            raise Success

    @TestCase
    def test_pbinary_array_int_load_13():
        ## an array containing a bit size
        class blah(pbinary.array):
            _object_ = 4
            length = 8

        data = b'\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.bytes(data)).l

        if list(self.object) == [0xa,0xb,0xc,0xd,0xe,0xf,0x1,0x2]:
            raise Success

    @TestCase
    def test_pbinary_array_struct_load_14():
        ## an array containing a pbinary
        class blah(pbinary.array):
            _object_ = byte
            length = 4

        data = b'\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.bytes(data)).l

        l = [ x['value'] for x in self.value[0] ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test_pbinary_array_dynamic_15():
        class blah(pbinary.array):
            _object_ = lambda s: byte
            length = 4

        data = b'\xab\xcd\xef\x12'
        self = pbinary.new(blah,source=provider.bytes(data)).l

        l = [ x['value'] for x in self.value[0] ]
        if [0xab,0xcd,0xef,0x12] == l:
            raise Success

    @TestCase
    def test_pbinary_struct_struct_load_16():
        class blah(pbinary.struct):
            _fields_ = [
                (byte, 'first'),
                (byte, 'second'),
                (byte, 'third'),
                (byte, 'fourth'),
            ]

        self = pbinary.new(blah)

        self.source = provider.bytes(TESTDATA)
        self.load()

        l = [ v['value'] for v in self.values() ]

        if l == list(bytearray(TESTDATA)[:len(l)]):
            raise Success

    @TestCase
    def test_pbinary_struct_struct_load_17():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'heh'),
                (dword, 'dw'),
                (4, 'hehhh')
            ]

        self = pbinary.new(blah)
        self.source = provider.bytes(TESTDATA)
        self.load()
        if self['heh'] == 4 and self['dw']['high'] == 0x1424 and self['dw']['low'] == 0x3444 and self['hehhh'] == 9:
            raise Success

    @TestCase
    def test_pbinary_struct_dynamic_load_18():
        class RECT(pbinary.struct):
            _fields_ = [
                (5, 'Nbits'),
                (lambda self: self['Nbits'], 'Xmin'),
                (lambda self: self['Nbits'], 'Xmax'),
                (lambda self: self['Nbits'], 'Ymin'),
                (lambda self: self['Nbits'], 'Ymax')
            ]

        n = int('1110001110001110', 2)
        b = bitmap.new(n,16)

        a = bitmap.new(0,0)
        a = bitmap.push(a, (4, 5))
        a = bitmap.push(a, (0xd, 4))
        a = bitmap.push(a, (0xe, 4))
        a = bitmap.push(a, (0xa, 4))
        a = bitmap.push(a, (0xd, 4))

        s = bitmap.data(a)
        z = pbinary.new(RECT,source=provider.bytes(s)).l

        if z['Nbits'] == 4 and z['Xmin'] == 0xd and z['Xmax'] == 0xe and z['Ymin'] == 0xa and z['Ymax'] == 0xd:
            raise Success

    @TestCase
    def test_pbinary_terminatedarray_19():
        class myarray(pbinary.terminatedarray):
            _object_ = 4

            def isTerminator(self, v):
                if v.int() == 0:
                    return True
                return False

        z = pbinary.new(myarray,source=provider.bytes(b'\x44\x43\x42\x41\x3f\x0f\xee\xde')).l
        if z.serialize() == b'DCBA?\x00':
            raise Success

    @TestCase
    def test_pbinary_struct_aggregatenum_20():
        class mystruct(pbinary.struct):
            _fields_ = [
                (4, 'high'),
                (4, 'low'),
                (4, 'lower'),
                (4, 'hell'),
            ]

        z = pbinary.new(mystruct,source=provider.bytes(b'\x41\x40')).l
        if z.int() == 0x4140:
            raise Success

    @TestCase
    def test_pbinary_partial_hierarchy_21():
        class mychild1(pbinary.struct):
            _fields_ = [(4, 'len')]

        class mychild2(pbinary.struct):
            _fields_ = [(4, 'len')]

        class myparent(pbinary.struct):
            _fields_ = [(mychild1, 'a'), (mychild2, 'b')]

        z = pbinary.new(myparent)
        z.source = provider.bytes(b'A'*5000)
        z.l

        a,b = z['a'],z['b']
        if (a.parent is b.parent) and (a.parent is z.object):
            raise Success
        raise Failure

    @TestCase
    def test_pstruct_partial_load_22():
        correct=b'\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.uint32_t, 'v')]

        z = broken(source=provider.bytes(correct))
        z = z.l
        a = z['h']

        if a['t'] == 69 and a['l'] == 4:
            raise Success
        raise Failure

    @TestCase
    def test_pstruct_partial_le_set_23():
        correct=b'\x44\x11\x08\x00\x00\x00'
        class RECORDHEADER(pbinary.struct):
            _fields_ = [ (10, 't'), (6, 'l') ]

        class broken(pstruct.type):
            _fields_ = [(pbinary.littleendian(RECORDHEADER), 'h'), (pint.littleendian(pint.uint32_t), 'v')]

        z = broken().alloc()
        z['v'].set(8)

        z['h']['l'] = 4
        z['h']['t'] = 0x45

        if z.serialize() == correct:
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_struct_partial_load_24():
        correct = b'\x0f\x00'
        class header(pbinary.struct):
            _fields_ = [
                (12, 'instance'),
                (4, 'version'),
            ]

        z = pbinary.littleendian(header)(source=provider.bytes(correct)).l

        if z.serialize() != correct:
            raise Failure
        if z['version'] == 15 and z['instance'] == 0:
            raise Success
        raise Failure

    @TestCase
    def test_pbinary_align_load_25():
        class blah(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (pbinary.align(8), 'b'),
                (4, 'c')
            ]

        x = pbinary.new(blah,source=provider.bytes(b'\xde\xad')).l
        if x['a'] == 13 and x['b'] == 14 and x['c'] == 10:
            raise Success
        raise Failure

    class blah(pbinary.struct):
        _fields_ = [
            (-16, 'a'),
        ]

    @TestCase
    def test_pbinary_struct_signed_load_26():
        s = b'\xff\xff'
        a = pbinary.new(blah,source=provider.bytes(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_27():
        s = b'\x80\x00'
        a = pbinary.new(blah,source=provider.bytes(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_28():
        s = b'\x7f\xff'
        a = pbinary.new(blah,source=provider.bytes(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_signed_load_29():
        s = b'\x00\x00'
        a = pbinary.new(blah,source=provider.bytes(s)).l
        b, = struct.unpack('>h',s)
        if a['a'] == b:
            raise Success

    @TestCase
    def test_pbinary_struct_load_le_conf_30():
        class blah2(pbinary.struct):
            _fields_ = [
                (4, 'a0'),
                (1, 'a1'),
                (1, 'a2'),
                (1, 'a3'),
                (1, 'a4'),
                (8, 'b'),
                (8, 'c'),
                (8, 'd'),
            ]

        s = b'\x00\x00\x00\x04'
        a = pbinary.littleendian(blah2)(source=provider.bytes(s)).l
        if a['a2'] == 1:
            raise Success

    @TestCase
    def test_pbinary_struct_load_31():
        s = b'\x04\x00'
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.bytes(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test_pbinary_struct_load_global_le_32():
        s = b'\x00\x04'
        pbinary.setbyteorder(config.byteorder.littleendian)
        class fuq(pbinary.struct):
            _fields_ = [
                (4, 'zero'),
                (1, 'a'),
                (1, 'b'),
                (1, 'c'),
                (1, 'd'),
                (8, 'padding'),
            ]

        a = pbinary.new(fuq,source=provider.bytes(s)).l
        if a['b'] == 1:
            raise Success

    @TestCase
    def test_pbinary_array_load_iter_33():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        src = provider.bytes(b'\xaa'*2)
        x = pbinary.new(test,source=src).l
        if tuple(x.object) == (1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0):
            raise Success

    @TestCase
    def test_pbinary_array_set_34():
        class test(pbinary.array):
            _object_ = 1
            length = 16

        a = b'\xaa'*2
        b = pbinary.new(test).a

        for i,x in enumerate((1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0)):
            b[i] = x

        if b.serialize() == a:
            raise Success

    @TestCase
    def test_pbinary_struct_load_be_conv_35():
        class test(pbinary.struct):
            _fields_ = [(8,'i'),(8,'v')]

        test = pbinary.bigendian(test)
        a = b'\x00\x0f'
        b = test(source=provider.bytes(a)).l
        if b.serialize() == a:
            raise Success

    @TestCase
    def test_pbinary_terminatedarray_multiple_load_36():
        pbinary.setbyteorder(config.byteorder.bigendian)

        # terminated-array
        class part(pbinary.struct):
            _fields_ = [(4,'a'),(4,'b')]

        class encompassing(pbinary.terminatedarray):
            _object_ = part
            def isTerminator(self, value):
                return value['a'] == value['b'] and value['a'] == 0xf

        class complete(pbinary.terminatedarray):
            _object_ = encompassing
            def isTerminator(self, value):
                v = value[0]
                return v['a'] == v['b'] and v['a'] == 0x0

        string = b'ABCD\xffEFGH\xffIJKL\xffMNOP\xffQRST\xffUVWX\xffYZ..\xff\x00!!!!!!!!\xffuhhh'
        a = pbinary.new(complete,source=ptypes.prov.bytes(string))
        a = a.l
        if len(a) == 8 and a.object[-1][0].bitmap() == (0,8):
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_37():
        pbinary.setbyteorder(config.byteorder.bigendian)

        string = b'ABCDEFGHIJKL'
        src = provider.bytes(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.object) == 8 and a[-1].bitmap() == (0xb4c,12):
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_38():
        pbinary.setbyteorder(config.byteorder.littleendian)

        string = b'ABCDEFGHIJKL'
        src = provider.bytes(string)
        class st(pbinary.struct):
            _fields_ = [(4,'nib1'),(4,'nib2'),(4,'nib3')]

        class argh(pbinary.array):
            length = 8
            _object_ = st

        a = pbinary.new(argh,source=src)
        a = a.l
        if len(a.object) == 8 and a.object[-1].bitmap() == (0x241,12):
            raise Success

    @TestCase
    def test_pbinary_blockarray_load_global_be_39():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class st(pbinary.struct):
            _fields_ = [
                (word, 'mz'),
                (word, 'l'),
                (dword, 'ptr'),
            ]

        class argh(pbinary.blockarray):
            _object_ = st
            def blockbits(self):
                return 32*8

        data = bytes(bytearray(range(48, 48 + 75)))
        src = provider.bytes(data)
        a = pbinary.new(argh, source=src)
        a = a.l
        if len(a) == 32/8 and a.size() == 32 and a.serialize() == data[:a.size()]:
            raise Success

    @TestCase
    def test_pbinary_array_blockarray_load_global_be_40():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.blockarray):
            _object_ = 32

            def blockbits(self):
                return 32*4

        class ack(pbinary.array):
            _object_ = argh
            length = 4

        data = bytearray(itertools.chain(*[4 * [x] for x in range(48, 48 + 75)] * 500))
        src = provider.bytes(bytes(data))
        a = pbinary.new(ack, source=src)
        a = a.l
        if a[0].bits() == 128 and len(a[0]) == 4 and a.blockbits() == 4*32*4 and a[0][-1] == 0x33333333:
            raise Success

    @TestCase
    def test_pbinary_struct_load_signed_global_be_41():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.struct):
            _fields_ = [
                (-8, 'a'),
                (+8, 'b'),
                (-8, 'c'),
                (-8, 'd'),
            ]

        data = b'\xff\xff\x7f\x80'
        a = pbinary.new(argh, source=provider.bytes(data))
        a = a.l
        if a.values() == [-1,255,127,-128]:
            raise Success

    @TestCase
    def test_pbinary_array_load_global_be_42():
        pbinary.setbyteorder(config.byteorder.bigendian)

        class argh(pbinary.array):
            _object_ = -8
            length = 4

        data = b'\xff\x01\x7f\x80'
        a = pbinary.new(argh, source=provider.bytes(data))
        a = a.l
        if list(a.object) == [-1,1,127,-128]:
            raise Success

    @TestCase
    def test_pbinary_struct_samesize_casting_43():
        class p1(pbinary.struct):
            _fields_ = [(2,'a'),(2,'b'),(4,'c')]
        class p2(pbinary.struct):
            _fields_ = [(4,'a'),(2,'b'),(2,'c')]

        data = b'\x5f'
        a = pbinary.new(p1, source=prov.bytes(data))
        a = a.l
        b = a.cast(p2)
        c = a.object
        d = a.object.cast(p2)
        if b['a'] == d['a'] and b['b'] == d['b'] and b['c'] == d['c']:
            raise Success

    @TestCase
    def test_pbinary_struct_casting_incomplete_44():
        class p1(pbinary.struct):
            _fields_ = [(2,'a'),(2,'b')]
        class p2(pbinary.struct):
            _fields_ = [(4,'a'),(2,'b')]
        data = b'\x5f'
        a = pbinary.new(p1, source=prov.bytes(data))
        a = a.l
        b = a.object.cast(p2)
        x,_ = a.bitmap()
        if b['a'] == x:
            raise Success

    @TestCase
    def test_pbinary_flags_load_45():
        class p(pbinary.flags):
            _fields_ = [
                (1,'set0'),
                (1,'notset1'),
                (1,'set1'),
                (1,'notset2'),
                (1,'set2'),
            ]

        data = b'\xa8'
        a = pbinary.new(pbinary.bigendian(p, source=prov.bytes(data)))
        a = a.l
        if 'notset' not in a.summary() and all(('set{:d}'.format(x)) in a.summary() for x in range(3)):
            raise Success

    @TestCase
    def test_pbinary_partial_terminatedarray_dynamic_load_46():
        class vle(pbinary.terminatedarray):
            class _continue_(pbinary.struct):
                _fields_ = [(1, 'continue'), (7, 'value')]
            class _sentinel_(pbinary.struct):
                _fields_ = [(0, 'continue'), (8, 'value')]

            def _object_(self):
                if len(self.value) < 4:
                    return self._continue_
                return self._sentinel_

            length = 5
            def isTerminator(self, value):
                if value['continue'] == 0:
                    return True
                return False

        source = b'\x80\x80\x80\x80\xff'
        a = pbinary.new(vle, source=ptypes.provider.bytes(source))
        a = a.load()

        if a.serialize() == b'\x80\x80\x80\x80\xff':
            raise Success

    @TestCase
    def test_pbinary_pstruct_set_num_47():
        class structure(pbinary.struct):
            _fields_ = [
                (4, 'a'),(4,'b')
            ]
        x = structure()
        res = x.set(a=4,b=8)
        if res.int() == 0x48:
            raise Success

    def test_pbinary_parray_set_tuple_48():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        x = array(length=4).set((0,0xabcd),(3,0xdcba))
        if x[0].int() == 0xabcd and x[-1].int()==0xdcba:
            raise Success

    def test_pbinary_parray_set_iterable_49():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        x = array(length=4).set(0xabcd,0xdcba)
        if x[0].int() == 0xabcd and x[1].int()==0xdcba:
            raise Success

    @TestCase
    def test_pbinary_pstruct_set_container_50():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        class structure(pbinary.struct):
            _fields_ = [
                (array, 'a'),(4,'b')
            ]

        x = array(length=2).set([0xdead,0xdead])
        res = structure().set(a=x, b=3)
        if res['a'].int() == 0xdeaddead:
            raise Success

    @TestCase
    def test_pbinary_parray_set_container_51():
        class array(pbinary.array):
            _object_ = 16
            length = 0
        class structure(pbinary.struct):
            _fields_ = [
                (8, 'a'),(8,'b')
            ]

        x = array(length=2).set((1,structure().set(a=0x41,b=0x42)))
        if x[1].int() == 0x4142:
            raise Success

    @TestCase
    def test_pbinary_parray_getslice_atomic_52():
        class array(pbinary.array):
            _object_ = 8
        data = b'hola mundo'
        x = array(length=len(data)).set(list(bytearray(data)))
        if all(a == b for a, b in zip(x[2 : 8], bytearray(data[2 : 8]))):
            raise Success

    @TestCase
    def test_pbinary_parray_getslice_array_53():
        class array(pbinary.array):
            class _object_(pbinary.array):
                length = 2
                _object_ = 4
        data = 0x1122334455abcdef
        result = map(bitmap.value, bitmap.split(bitmap.new(data, 64), 4))
        result = list(zip(*((iter(result),)*2)))
        x = array().set(result)
        if all(a[0] == b[0] and a[1] == b[1] for a, b in zip(x[2 : 8], result[2 : 8])):
            raise Success

    @TestCase
    def test_pbinary_parray_getslice_struct_54():
        class array(pbinary.array):
            class _object_(pbinary.struct):
                _fields_ = [(4,'a'),(4,'b')]
            length = 4

        data = 0x1122334455abcdef
        result = map(bitmap.value, bitmap.split(bitmap.new(data,64), 4))
        result = list(zip(*((iter(result),)*2)))
        x = array().set(result)
        if all(a['a'] == b[0] and a['b'] == b[1] for a,b in zip(x[2:8],result[2:8])):
            raise Success

    @TestCase
    def test_pbinary_parray_setslice_atomic_55():
        class array(pbinary.array):
            _object_ = length = 8
        x = array().a
        x[2:6] = [item for item in bytearray(b'hola')]
        if bytes(bytearray(x)) == b'\x00\x00hola\x00\x00':
            raise Success

    @TestCase
    def test_pbinary_parray_setslice_array_56():
        class array(pbinary.array):
            class _object_(pbinary.array):
                _object_ = 8
                length = 4
            length = 4
        x = array().a
        v1 = array._object_().set((0x41,0x41,0x41,0x41))
        v2 = array._object_().set((0x42,0x42,0x42,0x42))
        x[1:3] = [v1,v2]
        if x[0].bitmap() == (0,32) and x[1].bitmap() == (0x41414141,32) and x[2].bitmap() == (0x42424242,32) and x[3].bitmap() == (0,32):
            raise Success

    @TestCase
    def test_pbinary_parray_setslice_struct_57():
        class array(pbinary.array):
            class _object_(pbinary.struct):
                _fields_ = [(8,'a'),(8,'b')]
        x = array(length=4).a
        value = array._object_().set(a=0x41, b=0x42)
        x[1:3] = value
        if x[0].bitmap() == (0,16) and x[1].bitmap() == (0x4142,16) and x[2].bitmap() == (0x4142,16) and x[3].bitmap() == (0,16):
            raise Success

    @TestCase
    def test_pbinary_enum_set_integer_58():
        class e(pbinary.enum):
            width = 4
            _values_ = [
                ('aa', 0xa),
                ('bb', 0xb),
                ('cc', 0xc),
            ]

        x = e().a.set(0xb)
        if x['bb']: raise Success

    @TestCase
    def test_pbinary_enum_set_name_59():
        class e(pbinary.enum):
            width = 8
            _values_ = [
                ('aa', 0xaa),
                ('bb', 0xbb),
                ('cc', 0xcc),
            ]

        x = e().a.set('cc')
        if x['cc']: raise Success

    @TestCase
    def test_pbinary_enum_set_unknown_name_60():
        class e(pbinary.enum):
            width = 8
            _values_ = [
                ('aa', 0xaa),
                ('bb', 0xbb),
                ('cc', 0xcc),
            ]

        x = e().a
        if not x['aa'] and not x['bb'] and not x['cc']: raise Success

    @TestCase
    def test_pbinary_enum_check_attributes_61():
        class e(pbinary.enum):
            width = 8
            _values_ = [
                ('aa', 0xaa),
                ('bb', 0xbb),
                ('cc', 0xcc),
            ]

        x = e()
        if x.aa == 0xaa and x.bb == 0xbb and x.cc == 0xcc:
            raise Success

    @TestCase
    def test_pbinary_enum_check_output_name_62():
        class e(pbinary.enum):
            width = 8
            _values_ = [
                ('aa', 0xaa),
                ('bb', 0xbb),
                ('cc', 0xcc),
            ]

        x = e().set('cc')
        if x.str() == 'cc':
            raise Success

    @TestCase
    def test_pbinary_enum_check_output_number_63():
        class e(pbinary.enum):
            width = 8
            _values_ = [
                ('aa', 0xaa),
                ('bb', 0xbb),
                ('cc', 0xcc),
            ]

        res = 0xff
        x = e().set(res)
        if x.str() == '{:x}'.format(res):
            raise Success

    @TestCase
    def test_pbinary_integer_clamped_64():
        class v(pbinary.integer):
            def blockbits(self):
                return 7*4
        x = v().set(0xfaaaaaaa)
        if x.int() == 0xaaaaaaa:
            raise Success

    @TestCase
    def test_pbinary_integer_clamped_sign_65():
        class v(pbinary.integer):
            signed = True
            def blockbits(self):
                return 8*4
        x = v().set(-0xffffffffffffff)
        if x.int() == +1:
            raise Success

    @TestCase
    def test_pbinary_enum_signed_66():
        class e(pbinary.enum):
            width, signed = 8, True
            _values_ = [
                ('0xff', -1),
                ('0xfe', -2),
                ('0xfd', -3),
            ]
        x = e().set('0xff')
        if x['0xff'] and x.int() == -1:
            raise Success

    @TestCase
    def test_pbinary_struct_clamped_67():
        class s(pbinary.struct):
            _fields_ = [
                (4, 'first'),
                (8, 'second'),
                (4, 'third'),
            ]
        x = pbinary.new(pbinary.bigendian(s), source=ptypes.prov.bytes(b'\xde\xad')).l
        x['first'] = 0xfff
        if x['first'] == 0xf:
            raise Success

    @TestCase
    def test_pbinary_struct_enum_68():
        class e(pbinary.enum):
            width, signed = 4, True
            _values_ = [
                ('a', -6),
                ('b', -5),
                ('c', -4),
                ('d', -3),

            ]
        class s(pbinary.struct):
            _fields_ = [
                (4, 'first'),
                (8, 'second'),
                (e, 'third'),
            ]
        x = pbinary.new(pbinary.bigendian(s), source=ptypes.prov.bytes(b'\xde\xad')).l
        if x.item('third').str() == 'd':
            raise Success

    @TestCase
    def test_pbinary_array_enum_69():
        class e(pbinary.enum):
            width, signed = 4, True
            _values_ = [
                ('a', -6),
                ('b', -5),
                ('c', -4),
                ('d', -3),
                ('e', -2),
                ('f', -1),
            ]
        class s(pbinary.array):
            length, _object_ = 4, e

        x = pbinary.new(pbinary.bigendian(s), source=ptypes.prov.bytes(b'\xde\xad')).l
        if ''.join(map(operator.methodcaller('str'), map(x.item, range(len(x))))) == 'dead':
            raise Success

    @TestCase
    def test_pbinary_array_struct_set_dict_70():
        class s(pbinary.struct):
            _fields_ = [
                (1, 'k'),
                (15, 'n'),
            ]

        class argh(pbinary.array):
            length, _object_ = 5, s

        x = pbinary.new(argh).load(source=ptypes.prov.bytes(b'\x8f\xff'*5))
        x.set([dict(k=0)]*5)
        if all(item['k'] == 0 and item['n'] == 0xfff for item in x):
            raise Success

    def test_pbinary_struct_postbyte_71():
        # TODO
        class s(pbinary.struct):
            def __type(self):
                print('not found', self.value)
                return 4
            _fields_ = [
                (__type, 'type'),
                (4, 'enum'),
            ]

        x = pbinary.new(s, source=ptypes.prov.bytes(b'\x77')).l
        raise Failure

    @TestCase
    def test_pbinary_array_append_bitmap_72():
        x = pbinary.array(length=2, _object_=8).a
        x.append(bitmap.new(0xa, 4))
        if x.bitmap() == bitmap.new(0x0000a, 8+8+4):
            raise Success

    @TestCase
    def test_pbinary_array_append_integer_73():
        x = pbinary.array(length=2, _object_=8).a
        x.append(0xaa)
        if x.bitmap() == bitmap.new(0x0000aa, 8+8+8):
            raise Success

    @TestCase
    def test_pbinary_array_append_integerinstance_73():
        n = pbinary.integer(blockbits=lambda: 4).set(0xf)
        x = pbinary.array(length=2, _object_=8).a
        x.append(n)
        if x.bitmap() == bitmap.new(0x0000f, 8+8+n.bits()):
            raise Success

    @TestCase
    def test_pbinary_array_append_instance_74():
        class t(pbinary.struct):
            _fields_ = [
                (4, 'a'),
                (4, 'b'),
            ]
        n = t().a.set(a=0xa, b=0x5)
        x = pbinary.array(length=2, _object_=8).a
        x.append(n)
        if x.bitmap() == bitmap.new(0x0000a5, 8+8+n.bits()):
            raise Success

    @TestCase
    def test_pbinary_array_append_type_75():
        n = ptype.clone(pbinary.integer, blockbits=lambda _: 8)
        x = pbinary.array(length=2, _object_=8).a
        x.append(n)
        if x.bitmap() == bitmap.new(0x000000, 8+8+n().blockbits()):
            raise Success

    @TestCase
    def test_pbinary_array_append_getoffset_76():
        x = pbinary.array(length=2, _object_=8, offset=0x10).a
        position = x.append(bitmap.new(0, 0x200))
        if position == (x.getoffset() + 2, 0):
            raise Success

    @TestCase
    def test_pbinary_blockarray_custom_blockbits_77():
        data = b'ABCDXXXX'
        class t(pbinary.blockarray):
            _object_ = 8
            def blockbits(self):
                return len(data) // 2 * 8

        x = pbinary.new(t, source=ptypes.prov.bytes(data)).l
        if x.serialize() == data[0 : len(data) // 2]:
            raise Success

    @TestCase
    def test_pbinary_blockarray_custom_blocksize_78():
        data = b'ABCDXXXX'
        class t(pbinary.blockarray):
            _object_ = 8
            def blocksize(self):
                return len(data) // 2

        x = pbinary.new(t, source=ptypes.prov.bytes(data)).l
        if x.serialize() == data[0 : len(data) // 2]:
            raise Success

    @TestCase
    def test_pbinary_blockarray_custom_blockbits_alloc_78():
        class t(pbinary.blockarray):
            _object_ = 8
            def blockbits(self):
                return 8 * 32

        x = t().a
        if len(x) == 32:
            raise Success

    @TestCase
    def test_pbinary_blockarray_custom_blocksize_alloc_79():
        class t(pbinary.blockarray):
            _object_ = 8
            def blocksize(self):
                return 32

        x = t().a
        if len(x) == 32:
            raise Success

    @TestCase
    def test_pbinary_struct_uninitialized_field_position_80():
        class t(pbinary.struct):
            _fields_ = [
                (32, 'initialized'),
                (4, 'uninitialized'),
            ]
        a = t().a
        del(a.v[1])
        if len(a.v) == 1 and a.getposition('uninitialized') == (4, 0):
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

