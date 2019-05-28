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
    print instance.int()

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
    print instance.str()
"""
import six
import functools, operator, itertools
from six.moves import builtins

from . import ptype,bitmap,config,error,utils
Config = config.defaults
Log = Config.log.getChild(__name__[len(__package__)+1:])

__state__ = {}
def setbyteorder(endianness):
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        transform = {config.byteorder.bigendian:bigendian, config.byteorder.littleendian:littleendian}[endianness]
        for k,v in globals().items():
            if v in (type,) or getattr(v,'__base__',type) is type:
                continue
            if isinstance(v, builtins.type) and issubclass(v, type):
                if getattr(v, 'byteorder', config.defaults.integer.order) != endianness:
                    globals()[k] = transform(v)
                pass
            continue
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness {!r}".format(endianness))

def bigendian(integral):
    '''Will convert an integer_t to bigendian form'''
    if not issubclass(integral, type):
        raise error.TypeError(integral, 'bigendian')
    if getattr(integral, 'byteorder', None) == config.byteorder.bigendian:
        return integral

    le, be = __state__.setdefault(config.byteorder.littleendian, {}), __state__.setdefault(config.byteorder.bigendian, {})
    if any(integral in n for n in (be,le)):
        integral = be.get(integral, le.get(integral, type))
        class newintegral(integral):
            __doc__ = integral.__doc__
            byteorder = config.byteorder.bigendian
        if hasattr(integral, '__module__'): newintegral.__module__ = integral.__module__
        newintegral.__name__ = integral.__name__
        be.setdefault(newintegral, integral)
        return newintegral
    return ptype.clone(integral, byteorder=config.byteorder.bigendian)

def littleendian(integral):
    '''Will convert an integer_t to littleendian form'''
    if not issubclass(integral, type):
        raise error.TypeError(integral, 'littleendian')
    if getattr(integral, 'byteorder', None) == config.byteorder.littleendian:
        return integral

    le, be = __state__.setdefault(config.byteorder.littleendian, {}), __state__.setdefault(config.byteorder.bigendian, {})
    if any(integral in n for n in (be,le)):
        integral = le.get(integral, be.get(integral, type))
        class newintegral(integral):
            __doc__ = integral.__doc__
            byteorder = config.byteorder.littleendian
        if hasattr(integral, '__module__'): newintegral.__module__ = integral.__module__
        newintegral.__name__ = integral.__name__
        be.setdefault(newintegral, integral)
        return newintegral
    return ptype.clone(integral, byteorder=config.byteorder.littleendian)

class type(ptype.type):
    """Provides basic integer-like support

    Not intended to really be inherited from as it doesn't implement .summary
    """
    byteorder = config.defaults.integer.order

    def classname(self):
        typename = self.typename()
        if self.byteorder is config.byteorder.bigendian:
            return config.defaults.pint.bigendian_name.format(typename, **(utils.attributes(self) if config.defaults.display.mangle_with_attributes else {}))
        elif self.byteorder is config.byteorder.littleendian:
            return config.defaults.pint.littleendian_name.format(typename, **(utils.attributes(self) if config.defaults.display.mangle_with_attributes else {}))
        else:
            raise error.SyntaxError(self, 'type.classname', message='Unknown integer endianness {!r}'.format(self.byteorder))
        return typename

    def flip(self):
        '''Returns an integer with the endianness flipped'''
        if self.byteorder is config.byteorder.bigendian:
            return self.cast(littleendian(self.__class__))
        elif self.byteorder is config.byteorder.littleendian:
            return self.cast(bigendian(self.__class__))
        raise error.UserError(self, 'type.flip', message='Unexpected byte order {!r}'.format(self.byteorder))

    def __getvalue__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'int')
        if self.byteorder is config.byteorder.bigendian:
            return six.moves.reduce(lambda x,y: x << 8 | six.byte2int(y), self.serialize(), 0)
        elif self.byteorder is config.byteorder.littleendian:
            return six.moves.reduce(lambda x,y: x << 8 | six.byte2int(y), reversed(self.serialize()), 0)
        raise error.SyntaxError(self, 'integer_t.int', message='Unknown integer endianness {!r}'.format(self.byteorder))

    def __setvalue__(self, integer, **attrs):
        if self.byteorder is config.byteorder.bigendian:
            transform = lambda x: reversed(x)
        elif self.byteorder is config.byteorder.littleendian:
            transform = lambda x: x
        else:
            raise error.SyntaxError(self, 'integer_t.set', message='Unknown integer endianness {!r}'.format(self.byteorder))
        mask = (1<<self.blocksize()*8) - 1
        integer &= mask
        bc = bitmap.new(integer, self.blocksize() * 8)
        res = []
        while bc[1] > 0:
            bc,x = bitmap.consume(bc,8)
            res.append(x)
        res = res + [0]*(self.blocksize() - len(res))   # FIXME: use padding
        return super(type, self).__setvalue__(str().join(transform(map(six.int2byte,res))), **attrs)

    def get(self):
        return self.__getvalue__()
    num = number = __int__ = int = get

class uinteger_t(type):
    '''Provides unsigned integer support'''
    def summary(self, **options):
        res = self.int()
        return '{:-#0{:d}x} ({:d})'.format(res, 2+self.blocksize()*2, res)

    def __getvalue__(self):
        '''Convert integer type into a number'''
        return super(uinteger_t, self).__getvalue__()

    def __setvalue__(self, integer, **attrs):
        return super(uinteger_t, self).__setvalue__(integer, **attrs)

class sinteger_t(type):
    '''Provides signed integer support'''
    def summary(self, **options):
        res = self.int()
        return u"{:+#0{:d}x} ({:d})".format(res, 3+self.blocksize()*2, res)

    def __getvalue__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'int')
        signmask = int(2**(8*self.blocksize()-1))
        num = super(sinteger_t, self).__getvalue__()
        res = num&(signmask-1)
        if num&signmask:
            return (signmask-res)*-1
        return res & (signmask-1)

    def __setvalue__(self, integer, **attrs):
        signmask = int(2**(8*self.blocksize()))
        res = integer & (signmask-1)
        if integer < 0:
            res |= signmask
        return super(sinteger_t, self).__setvalue__(res, **attrs)

class uinteger(ptype.definition): attribute,cache = 'length',{}
class sinteger(ptype.definition): attribute,cache = 'length',{}
uint,sint = uinteger,sinteger
integer_t,integer = sinteger_t, sinteger

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

int_t,int8_t,int16_t,int32_t,int64_t,int128_t = sint_t,sint8_t,sint16_t,sint32_t,sint64_t,sint128_t

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

        if getattr(self.__class__, '__pint_enum_validated__', False):
            return
        cls = self.__class__

        # ensure that the enumeration has ._values_ defined
        if not hasattr(cls, '_values_'):
            Log.warning("{:s}.enum : {:s} : {:s}._values_ has no enumerations defined. Assigning a default empty list to class.".format(__name__, self.classname(), self.typename()))
            self._values_ = cls._values_ = []

        # invert ._values_ if they're defined backwards
        if len(cls._values_):
            name, value = cls._values_[0]
            if isinstance(value, six.string_types):
                Log.warning("{:s}.enum : {:s} : {:s}._values_ is defined backwards. Inverting it's values.".format(__name__, self.classname(), self.typename()))
                self._values_ = cls._values_ = [(k, v) for v, k in cls._values_[:]]
            pass

        # check that enumeration's ._values_ are defined correctly
        if any(not isinstance(k, six.string_types) or not isinstance(v, six.integer_types) for k, v in cls._values_):
            res = map(operator.attrgetter('__name__'), six.string_types)
            stringtypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            res = map(operator.attrgetter('__name__'), six.integer_types)
            inttypes = '({:s})'.format(','.join(res)) if len(res) > 1 else res[0]

            raise TypeError(self, '{:s}.enum.__init__'.format(__name__), "{:s}._values_ is of an incorrect format. Should be a list of tuples with the following types. : [({:s}, {:s}), ...]".format(self.typename(), stringtypes, inttypes))

        # collect duplicate values and give a warning if there are any found for a name
        res = {}
        for val, items in itertools.groupby(cls._values_, operator.itemgetter(0)):
            res.setdefault(val, set()).update(map(operator.itemgetter(1), items))
        for val, items in res.viewitems():
            if len(items) > 1:
                Log.warning("{:s}.enum : {:s} : {:s}._values_ has more than one value defined for key `{:s}` : {:s}".format(__name__, self.classname(), self.typename(), val, val, ', '.join(res)))
            continue

        # FIXME: fix constants within ._values_ by checking to see if they're out of bounds of our type

        # cache the validation for the class so we don't need to check anything again
        if cls is not enum:
            cls.__pint_enum_validated__ = True
        return

    @classmethod
    def byvalue(cls, value, *default):
        '''Lookup the string in an enumeration by it's first-defined value'''
        if len(default) > 1:
            raise TypeError("{:s}.byvalue expected at most 3 arguments, got {:d}".format(cls.typename(), 2+len(default)))

        try:
            return six.next(k for k, v in cls._values_ if v == value)
        except StopIteration:
            if default: return six.next(iter(default))
        raise KeyError(cls, 'enum.byvalue', value)
    byValue = byvalue

    @classmethod
    def byname(cls, name, *default):
        '''Lookup the value in an enumeration by it's first-defined name'''
        if len(default) > 1:
            raise TypeError("{:s}.byname expected at most 3 arguments, got {:d}".format(cls.typename(), 2+len(default)))

        try:
            return six.next(v for k, v in cls._values_ if k == name)
        except StopIteration:
            if default: return six.next(iter(default))
        raise KeyError(cls, 'enum.byname', name)
    byName = byname

    def __getattr__(self, name):
        # if getattr fails, then assume the user wants the value of
        #     a particular enum value
        try:
            res = self.byname(name)
            Log.warning("{:s}.enum : {:s} : Using {:s}.attribute for fetching the value for `{:s}` is deprecated.".format(__name__, self.classname(), self.typename(), name))
            return res
        except KeyError: pass
        raise AttributeError(enum, self, name)

    def str(self):
        '''Return enumeration as a string or just the integer if unknown.'''
        res = self.get()
        return self.byvalue(res, u"{:x}".format(res))

    def summary(self, **options):
        res = self.get()
        try: return u"{:s}({:#x})".format(self.byvalue(res), res)
        except (ValueError,KeyError): pass
        return super(enum, self).summary()

    def __setvalue__(self, value, **attrs):
        if isinstance(value, six.string_types):
            value = self.byname(value)
        return super(enum, self).__setvalue__(value, **attrs)

    def __getitem__(self, name):
        '''Return True if the enumeration matches the value of the constant specified by name.'''
        res = self.byname(name)
        return res == self.get()

    @classmethod
    def enumerations(cls):
        '''Return all values in enumeration as a set.'''
        return {v : k for k, v in cls._values_}

    @classmethod
    def mapping(cls):
        '''Return potential enumeration values as a dictionary.'''
        return {k : v for k, v in cls._values_}

# update our current state
for k, v in globals().items():
    if v in (type,) or getattr(v,'__base__',type) is type:
        continue
    if isinstance(v, builtins.type) and issubclass(v, type):
        __state__.setdefault(Config.integer.order, {})[v] = v
    continue
del(k, v)

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
    import ptypes,struct
    from ptypes import provider,utils,pint
    string1 = '\x0a\xbc\xde\xf0'
    string2 = '\xf0\xde\xbc\x0a'

    @TestCase
    def test_int_bigendian_uint32_load():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1))
        a = a.l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print a, a.serialize().encode('hex')

    @TestCase
    def test_int_bigendian_uint32_set():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1)).l
        a.set(0x0abcdef0)
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print a, a.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_load():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, b.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_set():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        b.set(0x0abcdef0)
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, b.serialize().encode('hex')

    @TestCase
    def test_int_revert_bigendian_uint32_load():
        pint.setbyteorder(config.byteorder.bigendian)
        a = pint.uint32_t(source=provider.string(string1)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print a, a.serialize().encode('hex')

    @TestCase
    def test_int_revert_littleendian_uint32_load():
        pint.setbyteorder(config.byteorder.littleendian)
        a = pint.uint32_t(source=provider.string(string2)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string2:
            raise Success
        print a, a.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_int32_signed_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\xff\xff\xff\xff'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b, a, a.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_int32_unsigned_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\x00\x00\x00\x80'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b, a, a.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_int32_unsigned_highedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\xff\xff\xff\x7f'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b, a, a.serialize().encode('hex')

    @TestCase
    def test_int_littleendian_int32_unsigned_lowedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\x00\x00\x00\x00'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('i',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b, a, a.serialize().encode('hex')

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

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
