import pint

class float_t(pint.integer_t):
    components = None    #(sign, exponent, fraction)

    def __consume_bits(self, int, bits):
        mask = (1<<bits) - 1
        return (int>>bits, int&mask)

    def __getcomponents(self, integer):
        sign,exponent,fraction = self.components
        res,fraction = self.__consume_bits(res, fraction)
        res,exponent = self.__consume_bits(res, exponent)
        res,sign = self.__consume_bits(res, sign)
        return sign,exponent,fraction

    def __float__(self):
        bits = reduce(lambda x,y:x+y, self.components, 0)
        bitmask = (1<<bits) - 1

        res = int(self)
        sign,exponent,fraction = self.__getcomponents(res)
        exponentshift = (2**self.components[1]) / 2 - 1
        fractionscale = 2**self.components[2]

        # convert to float()
        sign = -1**sign
        exponent = 2**exponentshift
        fraction = 1.0 + (1.0/fractionscale)

        raise NotImplementedError( repr((sign,exponent,fraction)) )

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
