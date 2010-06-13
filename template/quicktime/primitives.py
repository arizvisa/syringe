import sys
sys.path.append('/home/salc/code/ptypes.git')

import ptypes
from ptypes import *

class pQTInt(pDword): pass
class pQTType(pQTInt):
    def __repr__(self):
        return "%s '%c%c%c%c' (%08x)"% ( repr(self.__class__), self.value[0], self.value[1], self.value[2], self.value[3], int(self) )

    def __cmp__(self, x):
        if type(x) is str:
            return cmp('%c%c%c%c'% tuple(self.value[:4]), x)
        return cmp(int(self), x)

class pQTIntArray(pInfiniteArray):
    _object_ = pQTInt


