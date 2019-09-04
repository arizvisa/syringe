'''
PER-encoding utilities
'''
import ptypes
import math

from . import ber
from ptypes import *

### PER-encoded length
class LengthDeterminant(pbinary.struct):
    # FIXME: This might not be correct, but it works for now..
    def __second(self):
        return 8 if self['check'] else 0

    _fields_ = [
        (1, 'check'),
        (7, 'first'),
        (__second, 'second'),
    ]

    def int(self):
        if self['check']:
            return self['first'] * 2**8 + self['second']
        return self['first']

    def set(self, *integer, **fields):
        if not fields:
            if not self.initializedQ():
                return self.a.set(*integer)
            integer, = integer
            if self['check']:
                res = integer / 2**8
                return self.set(first=res, second=integer - res * 2**8)
            return self.set(first=integer) if integer < 2**7 else self.alloc(check=1).set(integer)
        return super(LengthDeterminant, self).set(**fields)

    def summary(self):
        return "check={:d} length={:d} first={:d} second={:d}".format(self['check'], self.int(), self['first'], self['second'])

### PER-encoded integer (prefixed with a length)
class INTEGER(pstruct.type):
    _fields_ = [
        (pbinary.bigendian(LengthDeterminant), 'length'),
        (lambda self: dyn.clone(ber.INTEGER, length=self['length'].li.int()), 'integer'),
    ]

    def int(self):
        return self['integer'].int()

    def set(self, *integer, **fields):
        if not fields:
            integer, = integer
            count = math.floor(math.log(integer) / math.log(2**8) + 1) if integer else 1
            return self.alloc(length=math.trunc(count)).set(integer=integer)
        return super(INTEGER, self).set(*integer, **fields)

