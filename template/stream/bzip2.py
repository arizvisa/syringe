import ptypes
from ptypes import *

import bz2
class bz2provider(ptypes.provider.iterable):
    compressor = decompressor = None
    def __init__(self, producer, compresslevel=9, **kwds):
        self.compressor = bz2.BZ2Compressor(compresslevel)
        self.decompressor = bz2.BZ2Decompressor()
        return super(bz2provider,self).__init__(producer, **kwds)

    def _read(self, amount):
        result = ''
        while len(result) < amount:
            c = self.source.next()
            if len(c) == 0:
                break
            r = self.decompressor.decompress(c)
            result += r

        assert len(self.decompressor.unused_data) == 0
        return result

    def _write(self, data):
        data = self.compressor.compress(data)
        return super(bz2provider,self)._write(data)

    def flush(self):
        # XXX: probably worthwhile to check this in case we output
        #      an incomplete .bz2 stream
        super(bz2provider,self)._write(self.compressor.flush())

class type(ptype.encoded_t):
    _object_ = ptype.undefined
    length = 0

    def decode(self, string, **attrs):
        def producer():
            self.source.seek(self.getoffset())
            while True:
                yield self.source.consume(1)

        with ptype.assign(self, *attrs):
            name = '*%s'% self.name()
            n = self.newelement(self._object_, name, 0)

            p = bz2provider(producer())
            return n.load(source=p)

    def encode(self, object, **kwds):
        '''encodes initialized object to block'''
        return bz2.compress(object.serialize())

if __name__ == '__main__':
    import ptypes
    from ptypes import *

    from . import bzip2
    import bz2

    a = bz2.BZ2Compressor(9)
    for x in 'hello world':
        a.compress(x)
    s = a.flush()
    print(repr(s))
    print(s.decode('bz2'))

    b = bz2.BZ2Decompressor()
    for x in s:
        c = b.decompress(x)
        if len(c) > 0:
            print(c)

    c = bzip2.type(_object_=dyn.clone(pstr.string,length=5))
    c.source = ptypes.provider.string(s)
    c.set(s)
    d = c.d
    print(d.l)
