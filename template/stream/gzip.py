import ptypes
from ptypes import *

class type(ptype.encoded_t):
    length = 0
    _object_ = ptype.undefined
    def decode(self, **attr):
        name = '*%s'% self.name()
        s = self.serialize().decode('zlib')
        return self.newelement(self._object_, name, 0, source=ptypes.provider.string(s), **attr)

    def encode(self, object):
        '''encodes initialized object to block'''
        self.value = object.serialize().encode('zlib')
        self.length = len(self.value)
        return self

if __name__ == '__main__':
    import ptypes
    from ptypes import *

    import gzip
    raise NotImplementedError
