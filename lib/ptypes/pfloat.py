import math
from . import ptype,pint,bitmap,config,error

def setbyteorder(endianness):
    import __builtin__
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        for k,v in globals().iteritems():
            if v is not type and isinstance(v,__builtin__.type) and issubclass(v,type) and getattr(v, 'byteorder', config.defaults.integer.order) != endianness:
                d = dict(v.__dict__)
                d['byteorder'] = endianness
                globals()[k] = __builtin__.type(v.__name__, v.__bases__, d)     # re-instantiate types
            continue
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness %s"% repr(endianness))

def bigendian(ptype):
    '''Will convert an pfloat_t to bigendian form'''
    import __builtin__
    if not issubclass(ptype, type) or ptype is type:
        raise error.TypeError(ptype, 'bigendian')
    d = dict(ptype.__dict__)
    d['byteorder'] = config.byteorder.bigendian
    return __builtin__.type(ptype.__name__, ptype.__bases__, d)

def littleendian(ptype):
    '''Will convert an pfloat_t to littleendian form'''
    import __builtin__
    if not issubclass(ptype, type) or ptype is type:
        raise error.TypeError(ptype, 'littleendian')
    d = dict(ptype.__dict__)
    d['byteorder'] = config.byteorder.littleendian
    return __builtin__.type(ptype.__name__, ptype.__bases__, d)

class type(pint.integer_t):
    def summary(self, **options):
        return '%s (%x)'% (self.getf(), self.num())

    def setf(self, value):
        raise error.ImplementationError(self, 'type.setf')

    def getf(self):
        raise error.ImplementationError(self, 'type.getf')

    float = __float__ = lambda s: s.getf()
    set = lambda s,v,**a: s.setf(v)
    get = lambda s: s.getf()

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

    def setf(self, value):
        """store /value/ into a binary format"""
        exponentbias = (2**self.components[1])/2 - 1
        m,e = math.frexp(value)

        # extract components from value
        s = math.copysign(1.0, m)
        m = abs(m)

        # convert to integrals
        sf = 1 if s < 0 else 0
        exponent = e + exponentbias - 1
        m = m*2.0 - 1.0     # remove the implicit bit
        mantissa = long(m * (2**self.components[2]))

        # store components
        result = bitmap.zero
        result = bitmap.push( result, bitmap.new(sf,self.components[0]) )
        result = bitmap.push( result, bitmap.new(exponent,self.components[1]) )
        result = bitmap.push( result, bitmap.new(mantissa,self.components[2]) )

        return super(type, self).set( result[0] )

    def getf(self):
        """convert the stored floating-point number into a python native float"""
        exponentbias = (2**self.components[1])/2 - 1
        res = bitmap.new( self.num(), sum(self.components) )

        # extract components
        res,sign = bitmap.shift(res, self.components[0])
        res,exponent = bitmap.shift(res, self.components[1])
        res,mantissa = bitmap.shift(res, self.components[2])

        if exponent > 0 and exponent < (2**self.components[2]-1):
            # convert to float
            s = -1 if sign else +1
            e = exponent - exponentbias
            m = 1.0 + (float(mantissa) / 2**self.components[2])

            # done
            return math.ldexp( math.copysign(m,s), e)

        # FIXME: this should return NaN or something
        config.defaults.log.warn('float_t.getf : %s : Invalid exponent value : %d'% (self.instance(), exponent))
        return 0.0

class sfixed_t(type):
    """Represents a signed fixed-point number.

    sign = number of bits containing sign flag
    fractional = number of bits for fractional component
    length = size in bytes of type
    """
    length = 0
    sign = fractional = 0

    def getf(self):
        mask = 2**(8*self.length) - 1
        intm = 2**(8*self.length - self.sign) - 1
        shift = 2**self.fractional
        n = self.num()
        #return float(n & intm) / shift * (-1 if n & (mask ^ intm) else +1)
        if n & (mask ^ intm):
            return float((n & intm) - (mask&intm+1)) / shift
        return float(n & intm) / shift

    def setf(self, value):
        integral,fraction = math.trunc(value),value-math.trunc(value)
        magnitude = 2**(8*self.length - self.fractional)
        shift = 2**self.fractional

        mask = 2 ** (8*self.length) - 1
        intm = 2 ** (8*self.length - self.sign) - 1

        integral &= (magnitude-1) # clamp
        integral *= magnitude
        #integral |= (mask ^ intm)

        n = integral + math.trunc(fraction*shift)
        return super(type, self).set(n)

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
    import struct,pint,config
    pint.setbyteorder(config.byteorder.bigendian)

    ## data
    single_precision = [
        (0x3f800000, 1.0),
        (0xc0000000, -2.0),
        (0x7f7fffff, 3.4028234663852886e+38),
        #        (0x00000000, 0.0),
        #        (0x80000000, -0.0),
        #        (0x7f800000, 0),
        #        (0xff800000, -0),
        (0x3eaaaaab, 1.0/3),
        (0x41c80000, 25.0),
    ]

    double_precision = [
        (0x3ff0000000000000, 1.0),
        (0x3ff0000000000001, 1.0000000000000002),
        (0x3ff0000000000002, 1.0000000000000004),
        (0x4000000000000000, 2.0),
        (0xc000000000000000, -2.0),
        (0x3fd5555555555555, 0.3333333333333333),
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

        a = cls()
        a.setf(float)
        n = a.long()

        if n == expected:
            raise Success
        raise Failure, 'setf: %s == 0x%x? %s (0x%x) %s'%(float, expected, result, n, f)

    def test_load(cls, integer, expected):
        if cls.length == 4:
            expected, = struct.unpack('f', struct.pack('f', expected))
            i,_ = bitmap.join(bitmap.new(ord(x),8) for x in reversed(struct.pack('f',expected)))
        elif cls.length == 8:
            expected, = struct.unpack('d', struct.pack('d', expected))
            i,_ = bitmap.join(bitmap.new(ord(x),8) for x in reversed(struct.pack('d',expected)))
        else:
            i = 0

        a = cls()
        super(type, a).set(integer)
        n = a.getf()

        if n == expected:
            raise Success
        raise Failure, 'getf: 0x%x == %s? %s (%s) %x'%( integer, expected, result, n, i)

    ## tests for floating-point
    for i,(n,f) in enumerate(single_precision):
        testcase = lambda cls=single,integer=f,value=n:test_load(cls,value,integer)
        testcase.__name__ = 'single_precision_load_%d'% i
        TestCase(testcase)
    for i,(n,f) in enumerate(single_precision):
        testcase = lambda cls=single,integer=f,value=n:test_assignment(cls,integer,value)
        testcase.__name__ = 'single_precision_assignment_%d'% i
        TestCase(testcase)

    for i,(n,f) in enumerate(double_precision):
        testcase = lambda cls=double,integer=f,value=n:test_load(cls,value,integer)
        testcase.__name__ = 'double_precision_load_%d'% i
        TestCase(testcase)
    for i,(n,f) in enumerate(double_precision):
        testcase = lambda cls=double,integer=f,value=n:test_assignment(cls,integer,value)
        testcase.__name__ = 'double_precision_assignment_%d'% i
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

    import ptypes
    reload(ptypes.pfloat)
    from ptypes.pfloat import sfixed_t
    ## sfixed_t
    class sword(sfixed_t):
        length,fractional,sign = 2,8,1
    class sdword(sfixed_t):
        length,fractional,sign = 4,16,1

    @TestCase
    def sfixed_point_word_get():
        x = sword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\xff\x40')
        if x.l.getf() == -0.75: raise Success
        print x.getf()
    @TestCase
    def sfixed_point_dword_get():
        x = sdword(byteorder=config.byteorder.bigendian)
        x.source = ptypes.prov.string('\xff\xff\xc0\x00')
        if x.l.getf() == -0.25: raise Success
        print x.getf()

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
    results = []
    for t in TestCaseList:
        results.append( t() )

