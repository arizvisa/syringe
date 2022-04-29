"""Primitive integral types.

A pint.integer_t is an atomic type that is used to describe integer types within
a complex data structure. They contain only one attribute which is the length.
The methods they expose are related to setting or getting the integer value.
This module includes functions for transforming the integer type to an
endian-ness that is different than the platform that the python interpreter is
built for.

At the time of importing this module, the default byteorder is that of the one
specifed by the python interpreter. Within this module, there are 3 methods that
are responsible for adjusting the endianness. They are as follows:

    setbyteorder(order) -- Set the byte-order for all the types in this module
                           globally. This function will modify the byteorder of
                           any type at the time a subtype is made to inherit
                           from it.

    bigendian(type) -- Return the provided pint.integer_t with the byteorder set
                       to bigendian.

    littleendian(type) -- Return the provided pint.integer_t with the byteorder
                          set to littleendian.

The base type within this module that all integral types are based on is labelled
integer_t. This base type includes methods for performing a few operations upon
the integer_t. The interface is as follows:

    class interface(pint.integer_t):
        length = number-of-bytes
        def int(self):
            '''Return the integer_t as an integer'''
        def set(self, integer):
            '''Set the integer_t to the value ``integer``'''
        def flip(self):
            '''Return the integer_t with the alternate byteorder'''

There are two basic integer_t's that each type in this module is based on. They
are the pint.uint_t, and pint.sint_t types. pint.sint_t is a signed integer with
the high-bit representing signedness and pint.uint_t is an unsigned integer. Each
subtype defined in this module is based on one of these two types.

The default types that are provided by this module are as follows:

    pint.uint8_t,pint.uint16_t,pint.uint32_t,pint.uint64_t -- Unsigned integers
    pint.sint8_t,pint.sint16_t,pint.sint32_t,pint.sint64_t -- Signed integers

Each default type is also defined within a ptype.definition that can be used to
locate a type given a particular size. The two definitions are pint.uinteger,
and pint.sinteger. These types are also aliased to pint.uint and pint.sint.

    # find a pint.uint_t that is 2 bytes in length
    type = pint.uinteger.get(2)

    # find a pint.sint_t that is 1 byte in length
    type = pint.sinteger.get(1)

Also included in this module is an enumeration type called `pint.enum`. In some
cases a developer might describe a complex data structure as having an integer
with a named identifier. The `pint.enum` type can be used to represent these
types of definitions. This enumeration type has the following interface:

    class type(pint.enum, integral-subtype):
        _values_ = [
            ('name1', 0xvalue1),
            ('name2', 0xvalue2),
        ]

        @classmethod
        def mapping(cls):
            '''Return the enumeration values as a dictionary.'''
        @classmethod
        def enumerations(cls):
            '''Return the values of each enumeration.'''
        @classmethod
        def byvalue(cls, value):
            '''Return the enumeration name based on the ``value``.'''
        @classmethod
        def byname(cls, name):
            '''Return the enumeration value based on the ``name``.'''

Example usage:
    # change the endianness to little-endian globally
    from ptypes import pint
    pint.setbyteorder(pint.littleendian)

    # define an integral type of 3 bytes in length
    class type(pint.uint_t):
        length = 3

    # define a signed integral type of 8 bytes in length
    class type(pint.sint_t):
        length = 8

    # define a little-endian dword type using the decorative form
    @pint.bigendian
    class type(pint.uint32_t):
        pass

    # transform a type to bigendian form after defining
    type = pint.bigendian(type)

    # instantiate and load a 16-bit signed word in little-endian
    type = pint.littleendian(pint.uint16_t)
    instance = type()
    instance.load()

    # change the value of instance
    instance.set(57005)

    # output the value of instance as a numerical value
    print(instance.int())

    # return instance in it's alternative byteorder
    flipped = instance.flip()

Example usage of pint.enum:
    # define an enumeration for a uint32_t
    from ptypes import pint
    class enumeration(pint.enum, pint.uint32_t):
        _values_ = [
            ('name1', 0x00000000),
            ('name2', 0x00000001),
            ('name3', 0x00000002),
            ...
        ]

    # instantiate and load an enumeration
    instance = enumeration()
    instance.load()

    # assign the instance by an enumeration name
    instance.set('name1')

    # return the instance as a name or an integer in string form
    print(instance.str())
"""
import functools, itertools, math, builtins
from . import ptype, bitmap, error, utils

from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'pint']))

# Setup some version-agnostic types that we can perform checks with
integer_types, string_types = bitmap.integer_types, utils.string_types

__state__ = {}
def setbyteorder(order):
    if order in {config.byteorder.bigendian, config.byteorder.littleendian}:
        transform = {config.byteorder.bigendian : bigendian, config.byteorder.littleendian : littleendian}[order]

        # Iterate through all of the types defined within our module, and
        # filter them to only get actual class definitions.
        for name, definition in globals().items():
            if definition in [type] or getattr(definition, '__base__', type) is type:
                continue

            # Now we need to prove they're a type and that they're an integer
            # definition. If so, then we can transform it with our decorator.
            if isinstance(definition, builtins.type) and issubclass(definition, type):
                if getattr(definition, 'byteorder', config.defaults.integer.order) != order:
                    globals()[name] = transform(definition)
                pass
            continue
        return

    # If we were given a string as the byteorder, then check the prefix to use.
    elif isinstance(order, string_types):
        if order.startswith('big'):
            return setbyteorder(config.byteorder.bigendian)
        elif order.startswith('little'):
            return setbyteorder(config.byteorder.littleendian)
        raise ValueError("An unknown byteorder was specified ({:s}) for integral types.".format(order))

    # Otherwise try to figure it out by checking the order's name.
    elif getattr(order, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(order, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise TypeError("An unknown type ({!s}) with the value ({!r}) was specified as the byteorder for integral types.".format(order.__class__, order))

def bigendian(integral, **attrs):
    '''Will convert an integer_t to bigendian form'''
    if not issubclass(integral, type):
        raise error.TypeError(integral, 'bigendian')
    if getattr(integral, 'byteorder', None) == config.byteorder.bigendian:
        return integral

    le, be = __state__.setdefault(config.byteorder.littleendian, {}), __state__.setdefault(config.byteorder.bigendian, {})
    if any(integral in state for state in [be, le]):
        integral = be.get(integral, le.get(integral, type))
        class newintegral(integral):
            __doc__ = getattr(integral, '__doc__', '')
            byteorder = config.byteorder.bigendian

        if hasattr(integral, '__module__'):
            newintegral.__module__ = integral.__module__

        newintegral.__name__ = integral.__name__
        be.setdefault(newintegral, integral)
        return ptype.clone(newintegral, **attrs) if attrs else newintegral

    attrs.setdefault('byteorder', config.byteorder.bigendian)
    return ptype.clone(integral, **attrs)

def littleendian(integral, **attrs):
    '''Will convert an integer_t to littleendian form'''
    if not issubclass(integral, type):
        raise error.TypeError(integral, 'littleendian')
    if getattr(integral, 'byteorder', None) == config.byteorder.littleendian:
        return integral

    le, be = __state__.setdefault(config.byteorder.littleendian, {}), __state__.setdefault(config.byteorder.bigendian, {})
    if any(integral in state for state in [be, le]):
        integral = le.get(integral, be.get(integral, type))
        class newintegral(integral):
            __doc__ = getattr(integral, '__doc__', '')
            byteorder = config.byteorder.littleendian

        if hasattr(integral, '__module__'):
            newintegral.__module__ = integral.__module__

        newintegral.__name__ = integral.__name__
        be.setdefault(newintegral, integral)
        return ptype.clone(newintegral, **attrs) if attrs else newintegral

    attrs.setdefault('byteorder', config.byteorder.littleendian)
    return ptype.clone(integral, **attrs)

class type(ptype.type):
    """Provides basic integer-like support

    Not intended to really be inherited from as it doesn't implement .summary
    """
    byteorder = config.defaults.integer.order

    def __generalize_byteorder(self):
        order = self.byteorder

        # First we need to figure out the byteorder which we do by
        # explicitly checking for the types.
        if order in {config.byteorder.bigendian, config.byteorder.littleendian}:
            return order

        # If we were assigned a string, though, then check which
        # prefix is said string using.
        elif isinstance(order, string_types):

            if order.startswith('big'):
                return config.byteorder.bigendian
            elif order.startswith('little'):
                return config.byteorder.littleendian
            raise error.TypeError(self, 'integer_t.byteorder', message="An unknown byteorder ({:s}) was assigned to the object.".format(order))

        # Anything else is an incorrect type, which we do not understand.
        cls = order.__class__
        raise error.SyntaxError(self, 'integer_t.byteorder', message="An unknown type ({!s}) with the value ({!r}) was assigned as the object byteorder.".format(cls.__name__, order))

    def classname(self):
        typename = self.typename()
        try:
            order = self.__generalize_byteorder()
        except Exception:
            #Log.warning("{:s}.classname : {:s} : Using the default typename as the byteorder attribute is using an unknown value {!r}.".format(__name__, typename, self.byteorder))
            return typename
        else:
            format = config.defaults.pint.littleendian_name.format if order is config.byteorder.bigendian else config.defaults.pint.littleendian_name.format
        return format(typename, **(utils.attributes(self) if config.defaults.display.mangle_with_attributes else {}))

    def flip(self):
        '''Returns an integer with the endianness flipped'''
        try:
            order = self.__generalize_byteorder()
        except Exception:
            raise error.UserError(self, 'type.flip', message="An unknown byteorder ({!s}) is currently assigned to the current type.".format(self.byteorder))
        if order is config.byteorder.bigendian:
            Finvert = littleendian
        elif order is config.byteorder.littleendian:
            Finvert = bigendian
        else:
            raise error.AssertionError(self, 'type.flip', message="An unexpected byteorder ({!s}) was returned by an internal function.".format(order))
        return self.cast(Finvert(self.__class__))

    def __getvalue__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'int')

        data, order = bytearray(self.serialize()), self.__generalize_byteorder()
        Ftransform = reversed if order is config.byteorder.littleendian else iter
        return functools.reduce(lambda agg, item: agg << 8 | item, Ftransform(data), 0)

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(type, self).__setvalue__(*values, **attrs)

        integer, = values
        Ftransform = iter if self.__generalize_byteorder() is config.byteorder.littleendian else reversed

        # First we need to get the values that we were passed within our
        # parameters. If we were given bytes instead of an integer, then
        # just toss them up the chain for someone else to decode it.
        if isinstance(integer, (bytes, bytearray)):
            return super(type, self).__setvalue__(bytes(integer) if isinstance(integer, bytearray) else integer, **attrs)

        mask = pow(2, 8 * self.blocksize()) - 1
        integer &= mask

        bc = bitmap.new(integer, 8 * self.blocksize())
        res = []
        while bc[1] > 0:
            bc, x = bitmap.consume(bc, 8)
            res.append(x)
        res = res + [0] * (self.blocksize() - len(res))   # FIXME: use padding
        return super(type, self).__setvalue__(bytes(bytearray(Ftransform(res))), **attrs)

    def int(self):
        return self.__getvalue__()
    get = int

class uinteger_t(type):
    '''Provides unsigned integer support'''
    def summary(self, **options):
        res = self.int()
        return '{:-#0{:d}x} ({:d})'.format(res, 2 + self.blocksize() * 2, res)

class sinteger_t(type):
    '''Provides signed integer support'''
    def summary(self, **options):
        res = self.int()
        return u"{:+#0{:d}x} ({:d})".format(res, 3 + self.blocksize() * 2, res)

    def __getvalue__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'int')
        signmask = math.trunc(pow(2, 8 * self.blocksize() - 1))
        num = super(sinteger_t, self).__getvalue__()
        res = num & (signmask - 1)
        if num & signmask:
            return (signmask - res) * -1
        return res & (signmask - 1)

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(sinteger_t, self).__setvalue__(*values, **attrs)

        integer, = values
        signmask = math.trunc(pow(2, 8 * self.blocksize()))
        res = integer & (signmask - 1)
        if integer < 0:
            res |= signmask
        return super(sinteger_t, self).__setvalue__(res, **attrs)

class uinteger(ptype.definition):
    attribute, cache = 'length', {}
class sinteger(ptype.definition):
    attribute, cache = 'length', {}

uint, sint = uinteger, sinteger
integer_t, integer = sinteger_t, sinteger

@uint.define
class uint_t(uinteger_t): length = 0
@uint.define
class uint8_t(uinteger_t): length = 1
@uint.define
class uint16_t(uinteger_t): length = 2
@uint.define
class uint32_t(uinteger_t): length = 4
@uint.define
class uint64_t(uinteger_t): length = 8
@uint.define
class uint128_t(uinteger_t): length = 16

@sint.define
class sint_t(sinteger_t): length = 0
@sint.define
class sint8_t(sinteger_t): length = 1
@sint.define
class sint16_t(sinteger_t): length = 2
@sint.define
class sint32_t(sinteger_t): length = 4
@sint.define
class sint64_t(sinteger_t): length = 8
@sint.define
class sint128_t(sinteger_t): length = 16

int_t, int8_t, int16_t, int32_t, int64_t, int128_t = sint_t, sint8_t, sint16_t, sint32_t, sint64_t, sint128_t

class enum(type):
    '''
    An integer_t for managing constants used when you define your integer.
    i.e. class myinteger(pint.enum, pint.uint32_t): pass

    Settable properties:
        _values_:array( tuple( name, value ), ... )
            This contains which enumerations are defined.
    '''

    def __init__(self, *args, **kwds):
        super(enum, self).__init__(*args, **kwds)

        # ensure that the enumeration has enum._values_ defined
        if not hasattr(self, '_values_'):
            self._values_ = []

        # check that enumeration's ._values_ are defined correctly
        if any(not isinstance(name, string_types) or not isinstance(value, integer_types) for name, value in self._values_):
            res = [item.__name__ for item in string_types]
            stringtypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            res = [item.__name__ for item in integer_types]
            integraltypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            raise error.TypeError(self, "{:s}.enum.__init__".format(__name__), "The definition of `{:s}` is of an incorrect format and should be a list of tuples with the following types. : [({:s}, {:s}), ...]".format('.'.join([self.typename(), '_values_']), stringtypes, integraltypes))

        # collect duplicate values and give a warning if there are any found for a name
        res = {}
        for value, items in itertools.groupby(self._values_, utils.operator.itemgetter(0)):
            res.setdefault(value, set()).update(map(utils.operator.itemgetter(1), items))

        for value, items in res.items():
            if len(items) > 1:
                Log.warning("{:s}.enum : {:s} : The definition for `{:s}` has more than one value ({!s}) defined for the enumeration \"{:s}\".".format(__name__, self.classname(), '.'.join([self.typename(), '_values_']), ', '.join(map("{!s}".format, items)), value))
            continue

        # XXX: we could constrain all the constants within ._values_ by validating that
        #      they're within the boundaries of our type
        return

    def has(self, *value):
        '''Return True if the provided parameter is contained by the enumeration. If no value is provided, then use the current instance.'''
        if not value:
            value = (self.get(),)
        res, = value

        if isinstance(res, string_types):
            return self.__byname__(res, None) == self.get()
        return self.__byvalue__(res, False) and True or False

    def __byvalue__(self, value, *default):
        '''Internal method to search the enumeration for the name representing the provided value.'''
        if len(default) > 1:
            raise error.TypeError(self, "{:s}.enum.byvalue".format(__name__), "{:s}.byvalue expected at most 3 arguments, got {:d}".format(self.typename(), 2 + len(default)))

        iterable = (name for name, item in self._values_ if item == value)
        try:
            res = utils.next(iterable, *default)

        except StopIteration:
            raise KeyError(value)
        return res

    def __byname__(self, name, *default):
        '''Internal method to search the enumeration for the value corresponding to the provided name.'''
        if len(default) > 1:
            raise error.TypeError(self, "{:s}.enum.byname".format(__name__), "{:s}.byname expected at most 3 arguments, got {:d}".format(self.typename(), 2 + len(default)))

        iterable = (value for item, value in self._values_ if item == name)
        try:
            res = utils.next(iterable, *default)

        except StopIteration:
            raise KeyError(name)
        return res

    def __getattr__(self, name):

        # until we deprecate this method of accessing enumerations, we need to
        # raise an AttributeError if the enum._values_ attribute is missing.
        if name in {'_values_'}:
            raise AttributeError(enum, self, name)

        # if getattr fails, then assume the user wants the value of
        # a particular enum value
        try:
            # FIXME: this has been deprecated and should probably be completely
            #        removed at some point.
            res = self.__byname__(name)
            Log.warning("{:s}.enum : {:s} : Using `{:s}` for fetching the value of \"{:s}\" is deprecated.".format(__name__, self.classname(), '.'.join([self.typename(), '__getattr__']), name))
            return res
        except KeyError: pass
        raise AttributeError(enum, self, name)

    def str(self):
        '''Return enumeration as a string or just the integer if unknown.'''
        res = self.get()
        return self.__byvalue__(res, u"{:x}".format(res))

    def summary(self, **options):
        res = self.get()
        try: return u"{:s}({:#x})".format(self.__byvalue__(res), res)
        except (ValueError, KeyError): pass
        return super(enum, self).summary()

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(enum, self).__setvalue__(*values, **attrs)

        integer, = values
        res = self.__byname__(integer) if isinstance(integer, string_types) else integer
        return super(enum, self).__setvalue__(res, **attrs)

    def __getitem__(self, name):
        '''Return True if the enumeration matches the value of the constant specified by name.'''
        if isinstance(name, string_types):
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
            return utils.next(name for name, item in cls._values_ if item == value)

        except StopIteration:
            if default: return utils.next(iter(default))

        raise KeyError(cls, 'enum.byvalue', value)

    @classmethod
    def byname(cls, name, *default):
        '''Lookup the value in an enumeration by it's first-defined name'''
        if len(default) > 1:
            raise TypeError("{:s}.byname expected at most 3 arguments, got {:d}".format(cls.typename(), 2+len(default)))

        try:
            return utils.next(value for item, value in cls._values_ if item == name)

        except StopIteration:
            if default: return utils.next(iter(default))

        raise KeyError(cls, 'enum.byname', name)

# update our current state
for _, definition in sorted(globals().items()):
    if definition in [type] or getattr(definition, '__base__', type) is type:
        continue
    if isinstance(definition, builtins.type) and issubclass(definition, type):
        __state__.setdefault(Config.integer.order, {})[definition] = definition
    continue
del(definition)

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
    import ptypes, sys, struct
    from ptypes import provider, utils, pint
    from ptypes.utils import operator

    string1 = b'\x0a\xbc\xde\xf0'
    string2 = b'\xf0\xde\xbc\x0a'

    tohex = operator.methodcaller('encode', 'hex') if sys.version_info[0] < 3 else operator.methodcaller('hex')

    @TestCase
    def test_int_bigendian_uint32_load():
        a = pint.bigendian(pint.uint32_t)(source=provider.bytes(string1))
        a = a.l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print(a, tohex(a.serialize()))

    @TestCase
    def test_int_bigendian_uint32_set():
        a = pint.bigendian(pint.uint32_t)(source=provider.bytes(string1)).l
        a.set(0x0abcdef0)
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print(a, tohex(a.serialize()))

    @TestCase
    def test_int_littleendian_load():
        b = pint.littleendian(pint.uint32_t)(source=provider.bytes(string2)).l
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print(b, tohex(b.serialize()))

    @TestCase
    def test_int_littleendian_set():
        b = pint.littleendian(pint.uint32_t)(source=provider.bytes(string2)).l
        b.set(0x0abcdef0)
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print(b, tohex(b.serialize()))

    @TestCase
    def test_int_revert_bigendian_uint32_load():
        pint.setbyteorder(config.byteorder.bigendian)
        a = pint.uint32_t(source=provider.bytes(string1)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print(a, tohex(a.serialize()))

    @TestCase
    def test_int_revert_littleendian_uint32_load():
        pint.setbyteorder(config.byteorder.littleendian)
        a = pint.uint32_t(source=provider.bytes(string2)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string2:
            raise Success
        print(a, tohex(a.serialize()))

    @TestCase
    def test_int_littleendian_int32_signed_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = b'\xff\xff\xff\xff'
        a = pint.int32_t(source=provider.bytes(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print(b, a, tohex(a.serialize()))

    @TestCase
    def test_int_littleendian_int32_unsigned_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = b'\x00\x00\x00\x80'
        a = pint.int32_t(source=provider.bytes(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print(b, a, tohex(a.serialize()))

    @TestCase
    def test_int_littleendian_int32_unsigned_highedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = b'\xff\xff\xff\x7f'
        a = pint.int32_t(source=provider.bytes(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print(b, a, tohex(a.serialize()))

    @TestCase
    def test_int_littleendian_int32_unsigned_lowedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = b'\x00\x00\x00\x00'
        a = pint.int32_t(source=provider.bytes(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print(b, a, tohex(a.serialize()))

    @TestCase
    def test_enum_set_integer():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]

        a = e().set(0xaaaaaaaa)
        if a['aa']: raise Success

    @TestCase
    def test_enum_set_name():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]

        a = e().set('aa')
        if a['aa']: raise Success

    @TestCase
    def test_enum_unknown_name():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]
        a = e().a
        if not a['aa'] and not a['bb'] and not a['cc']:
            raise Success

    @TestCase
    def test_enum_check_attributes():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]
        a = e()
        if a.aa == 0xaaaaaaaa and a.bb == 0xbbbbbbbb and a.cc == 0xcccccccc:
            raise Success

    @TestCase
    def test_enum_check_output_name():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]
        a = e().set('cc')
        if a.str() == 'cc':
            raise Success

    @TestCase
    def test_enum_check_output_number():
        class e(pint.enum, pint.uint32_t):
            _values_ = [
                ('aa', 0xaaaaaaaa),
                ('bb', 0xbbbbbbbb),
                ('cc', 0xcccccccc),
            ]
        res = 0xdddddddd
        a = e().set(res)
        if a.str() == '{:x}'.format(res):
            raise Success

    @TestCase
    def test_int_flip_bigendian():
        integer, expected, input = 0x41424344, 0x44434241, b'\x41\x42\x43\x44'
        t = pint.bigendian(pint.uint32_t)
        x = t(source=ptypes.prov.bytes(input)).l
        if x.int() == integer and x.serialize() == input and x.flip().int() == expected and x.flip().serialize() == input:
            raise Success

    @TestCase
    def test_int_flip_littleendian():
        integer, expected, input = 0x41424344, 0x44434241, b'\x44\x43\x42\x41'
        t = pint.littleendian(pint.uint32_t)
        x = t(source=ptypes.prov.bytes(input)).l
        if x.int() == integer and x.serialize() == input and x.flip().int() == expected and x.flip().serialize() == input:
            raise Success

    @TestCase
    def test_int_doubleflip():
        integer, expected, input = 0x41424344, 0x44434241, b'\x41\x42\x43\x44'
        t = pint.bigendian(pint.uint32_t)
        x = t(source=ptypes.prov.bytes(input)).l
        flipped = x.flip().flip()
        if x.int() == integer and x.serialize() == flipped.serialize() == input:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
