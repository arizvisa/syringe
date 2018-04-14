import ptypes
from ptypes import *
import array,functools

# big-endian
intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, data), 0)
dataofint = lambda integer: ((integer == 0) and '\x00') or (dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### ripped from the png specification
def make_crc_table():
    res = array.array('L', (0,)*256)
    for n in range(len(res)):
        c = n
        for k in range(8):
            c = (0xedb88320 ^ (c>>1)) if c&1 else c>>1
        res[n] = c
    return res

Table = make_crc_table()

def update_crc(crc, data, table):
    res = crc
    for b in array.array('B', data):
        res = table[(res ^ b) & 0xff] ^ (res >> 8)
    return res

def crc(data, table):
    return update_crc(0xffffffff, data, table) ^ 0xffffffff

####333
class ChunkUnknown(ptype.block):
    type, length = None, 0

    def classname(self):
        res = super(ChunkUnknown, self).classname()
        return '{:s}<{:s}>[size:{:#x}]'.format(res, self.type, self.blocksize())

class Chunk(ptype.definition):
    cache = {}
    unknown = ChunkUnknown

class ChunkType(pint.enum, pint.uint32_t): pass

######
class signature(dyn.block(8)):
    valid = property(fget=lambda s: s.serialize() == s.default())
    @classmethod
    def default(cls):
        return str().join(map(chr, (137,80,78,71,13,10,26,10)))

class chunk(pstruct.type):
    def __data(self):
        cb, t = self['length'].li, self['type'].li
        return Chunk.lookup(t.serialize(), dyn.clone(Chunk.default, length=cb.int()))

    def __data(self):
        type, length = self['type'].li, self['length'].li
        result = Chunk.lookup(type.serialize(), dyn.clone(Chunk.default, type=type.serialize(), length=length.int()))
        if ptype.iscontainer(result):
            return dyn.clone(result, blocksize=lambda s,cb=length.int():cb)
        return result

    def Calculate(self):
        res = self['type'].serialize() + self['data'].serialize()
        return crc(res, Table)

    @property
    def valid(self):
        return self.Calculate() == self['crc'].int()

    def properties(self):
        res = super(chunk, self).properties()
        res['CRC'] = self.Calculate()
        res['Valid'] = res['CRC'] == self['crc'].int()
        return res

    _fields_ = [
        (pint.uint32_t, 'length'),
        (ChunkType, 'type'),
        (__data, 'data'),
        (pint.uint32_t, 'crc'),
    ]

class File(pstruct.type):
    class chunks(parray.terminated):
        _object_ = chunk
        def isTerminator(self, value):
            return value['type'].serialize() == IEND.type

    _fields_ = [
        (signature, 'signature'),
        (chunks, 'data'),
    ]

@Chunk.define
class IHDR(pstruct.type):
    type = 'IHDR'

    _fields_ = [
        (pint.uint32_t, 'Width'),
        (pint.uint32_t, 'Height'),
        (pint.uint8_t, 'Bit depth'),
        (pint.uint8_t, 'Colour type'),
        (pint.uint8_t, 'Compression method'),
        (pint.uint8_t, 'Filter method'),
        (pint.uint8_t, 'Interlace method'),
    ]

@Chunk.define
class PLTE(parray.block):
    type = 'PLTE'
    class Entry(pstruct.type):
        _fields_ = [(pint.uint8_t,x) for x in 'rgb']
    _object_ = Entry

@Chunk.define
class IEND(ptype.type):
    type = 'IEND'

ChunkType._values_[:] = [(t.__name__, intofdata(key)) for key, t in Chunk.cache.iteritems()]

if __name__ == '__main__':
    import ptypes,png
    ptypes.setsource(ptypes.file('Chimera_Laboratory.png'))
    a = png.File()
    a = a.l
