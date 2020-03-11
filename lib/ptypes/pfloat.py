"""Primitive floating and fixed-point types.

A pfloat.float_t is an atomic type that is used to describe real numbers within a
complex data structure. This is used to describe the different components
of a floating-point number that are encoded according to the ieee-754 standard.
A float_t includes space for defining the signflag, mantissa, and the exponent
of a floating-point number. This type has the following interface:

    class interface(pfloat.float_t):
        components = (sign-bits, exponent-bits, fractional-bits)
        length = number-of-bytes

        def set(self, number):
            '''Assign the decimal ``number`` to the value of ``self``.'''
        def float(self):
            '''Return ``self`` as a 'float' type in python.'''
        def __float__(self):
            '''Method overload for the 'float' keyword.'''

Another type, pfloat.fixed_t, is also included that can be used to describe real
numbers encoded using fixed-point arithmetic. This type allows a user to specify
the number of bits that represent the fractional part of a fixed-point number. A
similar type, pfloat.sfixed_t, lets one specify whether the fixed-point number
has a bit dedicated to it's signedness. Both the fixed_t and sfixed_t have the
following interfaces:

    class interface(pfloat.fixed_t):
        fraction = number-of-bits-for-decimal
        length = size-in-bytes

    class interface(pfloat.sfixed_t):
        fraction = number-of-bits-for-decimal
        sign = number-of-bits-for-signflag
        length = size-in-bytes

A floating-point type within a data-structure can also be of varying byteorders.
Provided within this module are functions that can be used to transform the
byteorder of the types defined within or declared elsewhere. These functions are:

    setbyteorder(order) -- Set the byte-order for all the types in this module
                           globally. This function will modify the byteorder of
                           any type at the time a subtype is made to inherit
                           from it.

    bigendian(type) -- Return the provided pfloat.type with the byteorder set
                       to bigendian.

    littleendian(type) -- Return the provided pfloat.type with the byteorder
                          set to littleendian.

Within this module, the following ieee-754 types are defined:

    half -- 16-bit real number. 5-bits for the exponent, 10 for the fraction.
    single -- 32-bit real number. 8-bits for the exponent, 23 for the fraction.
    double -- 64-bit real number. 11-bits for the exponent, 52 for the fraction.

Also defined within this module is a ptype.definition that can be used to locate
a specific float_t that matches a particular size. It can be used as such:

    # find a pfloat.float_t that is 4 bytes in length
    type = pfloat.ieee.get(4)

Example usage:
    # change the endianness to big-endian globally
    from ptypes import pfloat
    pfloat.setbyteorder(pfloat.bigendian)

    # define an ieee-754 single type
    class type(pfloat.float_t):
        length = 4
        components = (1, 8, 23)

    # define a fixed-point 16.16 type
    class type(pfloat.fixed_t):
        length = 4
        fraction = 16

    # transform a type's byteorder to bigendian using decorator
    @pfloat.bigendian
    class type(pfloat.float_t):
        length = 8
        components = (1, 11, 52)

    # transform the byteorder of a type to littleendian after definition
    type = pfloat.littleendian(type)

    # instantiate and load a type
    instance = type()
    instance.load()

    # assign a floating-point number to a instance
    instance.set(22 / 7.0)

    # return the floating-point number of an instance
    print(instance.float())
    print(float(instance))
"""
import six,math
from six.moves import builtins

from . import ptype,pint,bitmap,config,error
Config = config.defaults
Log = Config.log.getChild(__name__[len(__package__)+1:])

def setbyteorder(endianness):
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        for k,v in globals().iteritems():
            if v is not type and isinstance(v,builtins.type) and issubclass(v,type) and getattr(v, 'byteorder', config.defaults.integer.order) != endianness:
                d = dict(v.__dict__)
                d['byteorder'] = endianness
                globals()[k] = builtins.type(v.__name__, v.__bases__, d)     # re-instantiate types
            continue
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness {!r}".format(endianness))

def bigendian(ptype):
    '''Will convert an pfloat_t to bigendian form'''
    if not issubclass(ptype, type) or ptype is type:
        raise error.TypeError(ptype, 'bigendian')
    d = dict(ptype.__dict__)
    d['byteorder'] = config.byteorder.bigendian
    return builtins.type(ptype.__name__, ptype.__bases__, d)

def littleendian(ptype):
    '''Will convert an pfloat_t to littleendian form'''
    if not issubclass(ptype, type) or ptype is type:
        raise error.TypeError(ptype, 'littleendian')
    d = dict(ptype.__dict__)
    d['byteorder'] = config.byteorder.littleendian
    return builtins.type(ptype.__name__, ptype.__bases__, d)

class type(pint.type):
    def summary(self, **options):
        res = super(type, self).__getvalue__()
        return '{:f} ({:#x})'.format(self.float(), res)

    def __setvalue__(self, *values, **attrs):
        raise error.ImplementationError(self, 'type.__setvalue__')

    def __getvalue__(self):
        raise error.ImplementationError(self, 'type.__getvalue__')

    float = __float__ = lambda self: self.get()
    int = __int__ = lambda self: super(type, self).__getvalue__()

    # wrappers for backwards compatibility
    setf = lambda self, value: self.__setvalue__(value)
    getf = lambda self: self.__getvalue__()

class float_t(type):
    """Represents a packed floating-point number.

    components = (signflag, exponent, fraction)
    """

    # FIXME: include support for NaN, and {+,-}infinity (special exponents)
    #        include support for unsignedness (binary32)
    #        round up as per ieee-754
    #        handle errors (clamp numbers that are out of range as per spec)

    components = None    #(sign, exponent, fraction)

    def round(self, bits):
        """round the floating-point number to the specified number of bits"""
        raise error.ImplementationError(self, 'float_t.round')

    def __setvalue__(self, *values, **attrs):
        """store ``value`` into a binary format"""
        if not values:
            return super(type, self).__setvalue__(*values, **attrs)

        exponentbias = (2**self.components[1])/2 - 1
        number, = values

        # convert to integrals
        if math.isnan(number):
            sf, exponent, mantissa = 0, 2**self.components[1] - 1, ~0
        elif math.isinf(number):
            sf, exponent, mantissa = 1 if number < 0 else 0, 2**self.components[1] - 1, 0
        elif number == 0.0 and math.atan2(number, number) < 0.0:
            sf, exponent, mantissa = 1, 0, 0
        elif number == 0.0 and math.atan2(number, number) == 0.0:
            sf, exponent, mantissa = 0, 0, 0
        else:
            # extract the exponent and mantissa
            m, e = math.frexp(number)

            # grab the sign flag
            s = math.copysign(1.0, m)
            sf = 1 if s < 0 else 0

            # adjust the exponent and remove the implicit bit
            m = abs(m)
            exponent = e + exponentbias - 1
            if exponent != 0:
                m = m * 2.0 - 1.0

            # convert the fractional mantissa into a binary number
            mantissa = math.trunc(m * (2**self.components[2]))

        # store components
        result = bitmap.zero
        result = bitmap.push( result, bitmap.new(sf,self.components[0]) )
        result = bitmap.push( result, bitmap.new(exponent,self.components[1]) )
        result = bitmap.push( result, bitmap.new(mantissa,self.components[2]) )

        return super(type, self).__setvalue__(result[0], **attrs)

    def __getvalue__(self):
        """convert the stored floating-point number into a python native float"""
        exponentbias = (2**self.components[1])/2 - 1
        integer = super(type, self).__getvalue__()
        res = bitmap.new(integer, sum(self.components))

        # extract components
        res,sign = bitmap.shift(res, self.components[0])
        res,exponent = bitmap.shift(res, self.components[1])
        res,mantissa = bitmap.shift(res, self.components[2])

        if exponent > 0 and exponent < (2**self.components[1]-1):
            # convert to float
            s = -1 if sign else +1
            e = exponent - exponentbias
            m = 1.0 + (float(mantissa) / 2**self.components[2])

            # done
            return math.ldexp( math.copysign(m,s), e)

        if exponent == 2**self.components[1]-1 and mantissa == 0:
            return float('-inf') if sign else float('+inf')
        elif exponent in (0,2**self.components[1]-1) and mantissa != 0:
            return float('-nan') if sign else float('+nan')
        elif exponent == 0 and mantissa == 0:
            return float('-0') if sign else float('+0')

        # FIXME: this should return NaN or something
        Log.warn('float_t.__getvalue__ : {:s} : invalid components value : {:d} : {:d} : {:d}'.format(self.instance(), sign, exponent, mantissa))
        raise NotImplementedError

class sfixed_t(type):
    """Represents a signed fixed-point number.

    sign = number of bits containing sign flag
    fractional = number of bits for fractional component
    length = size in bytes of type
    """
    length = 0
    sign = fractional = 0

    def __getvalue__(self):
        mask = 2**(8*self.length) - 1
        intm = 2**(8*self.length - self.sign) - 1
        shift = 2**self.fractional
        value = super(type, self).__getvalue__()
        #return float(value & intm) / shift * (-1 if value & (mask ^ intm) else +1)
        if value & (mask ^ intm):
            return float((value & intm) - (mask&intm+1)) / shift
        return float(value & intm) / shift

    def __setvalue__(self, *values, **attrs):
        if not values:
            return super(type, self).__setvalue__(*values, **attrs)

        number, = values
        integral, fraction = math.trunc(number), number - math.trunc(number)
        magnitude = 2**(8*self.length - self.fractional)
        shift = 2**self.fractional

        mask = 2 ** (8*self.length) - 1
        intm = 2 ** (8*self.length - self.sign) - 1

        integral &= (magnitude-1) # clamp
        integral *= magnitude
        #integral |= (mask ^ intm)

        return super(type, self).__setvalue__(integral + math.trunc(fraction * shift), **attrs)

class fixed_t(sfixed_t):
    """Represents an unsigned fixed-point number.

    fractional = number of bits for fractional component
    length = size in bytes of type
    """
    length = 0          # size in bytes of integer
    fractional = 0      # number of bits to represent fractional part

    @property
    def sign(self):
        return 0

###
class ieee(ptype.definition): attribute,cache = 'length',{}

@ieee.define
class half(float_t):
    length = 2
    components = (1, 5, 10)

@ieee.define
class single(float_t):
    length = 4
    components = (1, 8, 23)

@ieee.define
class double(float_t):
    length = 8
    components = (1, 11, 52)

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
                print('%s: %r'% (name,e))
                return True
            except Failure,e:
                print('%s: %r'% (name,e))
            except Exception,e:
                print('%s: %r : %r'% (name,Failure(), e))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes, struct
    from ptypes import pint,config,pfloat
    pint.setbyteorder(config.byteorder.bigendian)

    ## data
    single_precision = [
        (0x3f800000, 1.0),
        (0xc0000000, -2.0),
        (0x7f7fffff, 3.4028234663852886e+38),
        (0x3eaaaaab, 1.0/3),
        (0x41c80000, 25.0),
        (0xc0b80aa6, -5.7513),

        (0xffc00000, +float('NaN')),
        (0x7fc00000, -float('NaN')),
        (0x7f800000, +float('inf')),
        (0xff800000, -float('inf')),
        (0x00000000, float('+0')),
        (0x80000000, float('-0')),
    ]

    double_precision = [
        (0x0000000000000000, 0.0),
        (0x3ff0000000000000, 1.0),
        (0x3ff0000000000001, 1.0000000000000002),
        (0x3ff0000000000002, 1.0000000000000004),
        (0x4000000000000000, 2.0),
        (0xc000000000000000, -2.0),
        (0x3fd5555555555555, 0.3333333333333333),
        (0xc00921fb54443000, -3.1415926535901235),

        (0xfff8000000000000, +float('NaN')),
        (0x7ff8000000000000, -float('NaN')),
        (0x7ff0000000000000, +float('inf')),
        (0xfff0000000000000, -float('inf')),
        (0x0000000000000000, float('+0')),
        (0x8000000000000000, float('-0')),
    ]

    def test_assignment(cls, float, expected):
        if cls.length == 4:
            float, = struct.unpack('f', struct.pack('f', float))
            f, = struct.unpack('f',bitmap.data(bitmap.new(expected,cls.length*8), reversed=True))
        elif cls.length == 8:
            float, = struct.unpack('d', struct.pack('d', float))
            f, = struct.unpack('d',bitmap.data(bitmap.new(expected,cls.length*8), reversed=True))
        else:
            f = float('NaN')

        res = cls()
        res.set(float)
        n = res.int()

        if n == expected:
            raise Success
        elif math.isnan(float) and math.isnan(res.getf()):
            raise Success
        elif math.isinf(float) and math.isinf(res.getf()) and float < 0 and res.getf() < 0:
            raise Success
        elif math.isinf(float) and math.isinf(res.getf()) and float >= 0 and res.getf() >= 0:
            raise Success
        raise Failure('setf: {:f} == {:#x}? {:d} ({:#x}) {:f}'.format(float, expected, res.int(), n, f))

    def test_load(cls, integer, expected):
        if cls.length == 4:
            expected, = struct.unpack('f', struct.pack('f', expected))
            i,_ = bitmap.join(bitmap.new(six.byte2int(x),8) for x in reversed(struct.pack('f',expected)))
        elif cls.length == 8:
            expected, = struct.unpack('d', struct.pack('d', expected))
            i,_ = bitmap.join(bitmap.new(six.byte2int(x),8) for x in reversed(struct.pack('d',expected)))
        else:
            i = 0

        res = cls()
        super(type, res).__setvalue__(integer)
        n = res.get()

        if n == expected:
            raise Success
        elif math.isnan(n) and math.isnan(expected):
            raise Success
        elif math.isinf(n) and math.isinf(expected) and n < 0 and expected < 0:
            raise Success
        elif math.isinf(n) and math.isinf(expected) and n >= 0 and expected >= 0:
            raise Success
        raise Failure('getf: {:#x} == {:f}? pfloat-int:{:#x} pfloat-get:{:f} python-expected:{:#x}'.format(integer, expected, res.int(), n, i))

    ## tests for floating-point
    for i,(n,f) in enumerate(single_precision):
        testcase = lambda cls=single,integer=n,value=f:test_load(cls,integer,value)
        testcase.__name__ = 'single_precision_load_{:d}'.format(i)
        TestCase(testcase)
    for i,(n,f) in enumerate(single_precision):
        testcase = lambda cls=single,integer=n,value=f:test_assignment(cls,value,integer)
        testcase.__name__ = 'single_precision_assignment_{:d}'.format(i)
        TestCase(testcase)

    for i,(n,f) in enumerate(double_precision):
        testcase = lambda cls=double,integer=n,value=f:test_load(cls,integer,value)
        testcase.__name__ = 'double_precision_load_{:d}'.format(i)
        TestCase(testcase)
    for i,(n,f) in enumerate(double_precision):
        testcase = lambda cls=double,integer=n,value=f:test_assignment(cls,value,integer)
        testcase.__name__ = 'double_precision_assignment_{:d}'.format(i)
        TestCase(testcase)

    ## fixed
    class word(fixed_t):
        length,fractional = 2,8
    class dword(fixed_t):
        length,fractional = 4,16

    @TestCase
    def ufixed_point_word_get():
        x = word(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\x80\x80')
        if x.l.getf() == 128.5: raise Success
    @TestCase
    def ufixed_point_dword_get():
        x = dword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\x00\x64\x40\x00')
        if x.l.getf() == 100.25: raise Success

    @TestCase
    def ufixed_point_word_integral_set():
        x = word(byteorder=config.byteorder.bigendian)
        x.set(30.5)
        if x.serialize()[0] == '\x1e': raise Success
    @TestCase
    def ufixed_point_word_fractional_set():
        x = word(byteorder=config.byteorder.bigendian)
        x.set(30.5)
        if x.serialize()[1] == '\x80': raise Success

    @TestCase
    def ufixed_point_dword_integral_set():
        x = dword(byteorder=config.byteorder.bigendian)
        x.set(1.25)
        if x.serialize()[:2] == '\x00\x01': raise Success
    @TestCase
    def ufixed_point_dword_fractional_set():
        x = dword(byteorder=config.byteorder.bigendian)
        x.set(1.25)
        if x.serialize()[2:] == '\x40\x00': raise Success

    ## sfixed_t
    class sword(pfloat.sfixed_t):
        length,fractional,sign = 2,8,1
    class sdword(pfloat.sfixed_t):
        length,fractional,sign = 4,16,1

    @TestCase
    def sfixed_point_word_get():
        x = sword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\xff\x40')
        if x.l.getf() == -0.75: raise Success
        print(x.getf())
    @TestCase
    def sfixed_point_dword_get():
        x = sdword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\xff\xff\xc0\x00')
        if x.l.getf() == -0.25: raise Success
        print(x.getf())

    @TestCase
    def sfixed_point_word_integral_set():
        x = sword(byteorder=config.byteorder.bigendian)
        x.set(-0.5)
        if x.serialize()[0] == '\xff': raise Success
    @TestCase
    def sfixed_point_word_fractional_set():
        x = sword(byteorder=config.byteorder.bigendian)
        x.set(-0.75)
        if x.serialize()[1] == '\x40': raise Success

    @TestCase
    def sfixed_point_dword_integral_set():
        x = sdword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\xff\xfe\x40\x00')
        x.set(-1.75)
        if x.serialize()[:2] == '\xff\xfe': raise Success
    @TestCase
    def sfixed_point_dword_fractional_set():
        x = sdword(byteorder=config.byteorder.bigendian)
        x.set(-1.25)
        if x.serialize()[2:] == '\xc0\x00': raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

