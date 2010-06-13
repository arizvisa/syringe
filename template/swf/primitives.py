from ptypes import *
from ptypes.utils import biterator,bitconsume

class pFixed(pType):
    length = 0

    def __float__(self):
        v = list(reversed(self.serialize()))

        center = self.length / 2
        divisor = 2**(center*8)

        high = utils.h2i(v[:center])
        low = utils.h2i(v[center:]) / float(divisor)
        return float(high)+low

    def __repr__(self):
        if self.initialized:
            res = '%f'%self.__float__()
        else:
            res = '???'
        return '%s %s'% (self.__class__, res)

## float types
#TODO: define __repr__ for each of these types
class FLOAT16(pBinary):
    _fields_ = [
        (1, 'sign'),
        (5, 'exponent'),
        (10, 'mantissa')
    ]

class FLOAT(pBinary):
    _fields_ = [
        (1, 'sign'),
        (8, 'exponent'),
        (23, 'mantissa')
    ]

class DOUBLE(pBinary):
    _fields_ = [
        (1, 'sign'),
        (11, 'exponent'),
        (52, 'mantissa')
    ]

## int types
class SI8(pInt):
    length = 1
    signed = True

class UI8(pInt):
    length = 1
    signed = False

class SI16(pInt):
    length = 2
    signed = True

class UI16(pInt):
    length = 2
    signed = False

class SI32(pInt):
    length = 4
    signed = True

class UI32(pInt):
    length = 4
    signed = False

class UI64(pInt):
    length = 8
    signed = False

(SI8, UI8, SI16, UI16, SI32, UI32, UI64) = ( lilendian(x) for x in (SI8,UI8,SI16,UI16,SI32,UI32,UI64) )

class FIXED(pFixed):
    length = 4

class FIXED8(pFixed):
    length = 2

class RECT(pBinary):
    _fields_ = [
        (5, 'Nbits'),
        (lambda self: self['Nbits'], 'Xmin'),
        (lambda self: self['Nbits'], 'Xmax'),
        (lambda self: self['Nbits'], 'Ymin'),
        (lambda self: self['Nbits'], 'Ymax')
    ]

if False:
    x = RECT()
    x['Nbits'] = 7
    # on __setitem__ if we're dynamic, then initialize self.value with shit
    x['Xmin'] =  16

class MATRIX(pBinary):
    '''look at deserialize to see how this gets read'''
    _fields_ = [
        (1, 'HasScale'),
        (dyn.ifelse(lambda self: self['HasScale'], 5, 0), 'NScaleBits'),
        (lambda self: self['NScaleBits'], 'ScaleX'),
        (lambda self: self['NScaleBits'], 'ScaleY'),

        (1, 'HasRotate'),
        (dyn.ifelse(lambda self: self['HasRotate'], 5, 0), 'NRotateBits'),
        (lambda self: self['NRotateBits'], 'RotateSkew0'),
        (lambda self: self['NRotateBits'], 'RotateSkew1'),

        (5, 'NTranslateBits'),
        (lambda self: self['NTranslateBits'], 'TranslateX'),
        (lambda self: self['NTranslateBits'], 'TranslateY')
    ]

class STRING(pTerminatedArray):
    _object_ = UI8

    def isTerminator(self, v):
        return int(v) == 0

    def __str__(self):
        return ''.join( [str(v) for v in self] )

class Empty(pType):
    initialized = property(fget=lambda x: True, fset=lambda x,v: None)
    value = []

