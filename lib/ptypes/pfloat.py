import pint
import bitmap,math

class float_t(pint.integer_t):
    # FIXME: include support for NaN, and {+,-}infinity (special exponents)
    #        include support for unsignedness (binary32)
    #        round up as per ieee-754
    #        handle errors (clamp numbers that are out of range as per spec)

    components = None    #(sign, exponent, fraction)

    def details(self):
        return '%s (%x)'% (float(self), int(self))

    def round(self, bits):
        # round the floating point number to the specified number of bits
        raise NotImplementedError

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

        return super(float_t, self).set( result[0] )

    def getf(self):
        """convert the stored floating point number into a python native float"""
        exponentbias = (2**self.components[1])/2 - 1
        res = bitmap.new( self.number(), sum(self.components) )

        # extract components
        res,sign = bitmap.shift(res, self.components[0])
        res,exponent = bitmap.shift(res, self.components[1])
        res,mantissa = bitmap.shift(res, self.components[2])

        assert exponent > 0 and exponent < (2**self.components[2]-1)

        # convert to float
        s = -1 if sign else +1
        e = exponent - exponentbias
        m = 1.0 + (float(mantissa) / 2**self.components[2])

        # done
        return math.ldexp( math.copysign(m,s), e)

    float = __float__ = getf
    set = setf

class half(float_t):
    length = 2
    components = (1, 5, 10)

class single(float_t):
    length = 4
    components = (1, 8, 23)

class double(float_t):
    length = 8
    components = (1, 11, 52)

if __name__ == '__main__':
    import struct
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

        result = bool(n == expected)
        if result:
            print 'setf: %s == 0x%x? %s'%( float, expected, result)
        else:
            print 'setf: %s == 0x%x? %s (0x%x) %s'%( float, expected, result, n, f)
        return result

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
        super(float_t, a).set(integer)
        n = a.getf()

        result = bool(n == expected)
        if result:
            print 'getf: 0x%x == %s? %s'%( integer, expected, result)
        else:
            print 'getf: 0x%x == %s? %s (%s) %x'%( integer, expected, result, n, i)
        return result

    def try_assignments(cls, data):
        result = True
        for n,f in data:
            _ = test_assignment(cls, f, n)
            if not _:
                result = False
        return result

    def try_loads(cls, data):
        result = True
        for n,f in data:
            _ = test_load(cls, n, f)
            if not _:
                result = False
        return result

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

    ## tests
    print '[single precision loads]'
    _=try_loads(single, single_precision)
    print 'Success\n' if _ else 'Failure\n'

    print '[single precision assignments]'
    _=try_assignments(single, single_precision)
    print 'Success\n' if _ else 'Failure\n'

    print '[double precision loads]'
    _=try_loads(double, double_precision)
    print 'Success\n' if _ else 'Failure\n'

    print '[double precision assignments]'
    _=try_assignments(double, double_precision)
    print 'Success\n' if _ else 'Failure\n'
