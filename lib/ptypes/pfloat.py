import pint

class float_t(pint.integer_t):
    components = None    #(sign, exponent, fraction)

    def __consume_bits(self, int, bits):
        mask = (1<<bits) - 1
        return (int>>bits, int&mask)

    def getcomponents(self, integer):
        sign,exponent,fraction = self.components
        res = integer
        res,fraction = self.__consume_bits(res, fraction)
        res,exponent = self.__consume_bits(res, exponent)
        res,sign = self.__consume_bits(res, sign)
        return sign,exponent,fraction

    def __float__(self):
        bits = reduce(lambda x,y:x+y, self.components, 0)
        bitmask = (1<<bits) - 1

        res = int(self)
        sign,exponent,fraction = self.getcomponents(res)
        exponentshift = (2*self.components[1]) / 2 - 1
        fractionscale = 2**self.components[2]

        # convert to float()
        negative = -1*sign
        e = exponent - (2**exponentshift-1)
        mantissa = 1.0+(fraction*(1.0/fractionscale))
        
        # and now we stack up imprecision
        if sign:
            return -1 * mantissa * (2**e)
        return mantissa * (2**e)

    def __repr__(self):
        return '%s %s (%x)'% (self.name(), float(self), int(self))

if False:
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

    def test(integer, f1, f2):
        if f1 == f2:
            print "SUCCESS : %x : %s == %s"%( integer, repr(f1), repr(f2))
            return
        print "FAIL : %x : %s == %s"%( integer, repr(f1), repr(f2))

    singles = [
        (0x3f800000, 1.0),
        (0xc0000000, -2.0),
        (0x7f7fffff, 3.4028234663852886e+38),
        #        (0x00000000, 0.0),
        #        (0x80000000, -0.0),
        #        (0x7f800000, 0),
        #        (0xff800000, -0),
        (0x3eaaaaaa, 1.0/3),
        (0x41c80000, 25.0),
    ]

    self = single()
    for number,result in singles:
        self.set(number)
        test( number, float(self), result )


    ######3#
    doubles = [
        (0x3ff0000000000000, 1.0),
        (0x3ff0000000000001, 1.0000000000000002),
        (0x3ff0000000000002, 1.0000000000000004),
        (0x4000000000000000, 2.0),
        (0xc000000000000000, -2.0),
        (0x3fd5555555555555, 0.3333333333333333),
    ]

    self = double()
    for number,result in doubles:
        self.set(number)
        test( number, float(self), result )
    pass
