import ptypes, logging
from ptypes import *
import six,array,functools

# big-endian
intofdata = lambda data: six.moves.reduce(lambda t, c: t * 256 | c, bytearray(data), 0)
dataofint = lambda integer: ((integer == 0) and b'\0') or (dataofint(integer // 256).lstrip(b'\0') + six.int2byte(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### ripped from the png specification
def make_crc_table():
    res = array.array('L' if len(array.array('I', 4 * b'\0')) > 1 else 'I', (0,)*256)
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

def make_crc(data, table):
    return update_crc(0xffffffff, data, table) ^ 0xffffffff

###
class Chunks(ptype.definition):
    cache = {}
    class UnknownChunk(ptype.block):
        type, length = None, 0

        def classname(self):
            res = super(Chunks.UnknownChunk, self).classname()
            return '{:s}<{:s}>[size:{:#x}]'.format(res, self.type, self.blocksize())

    default = UnknownChunk

class ChunkType(pint.enum, pint.uint32_t):
    _values_ = []

######
class Signature(dyn.block(8)):
    Valid = property(fget=lambda s: s.serialize() == s.default())
    @classmethod
    def default(cls):
        return bytes(bytearray([137,80,78,71,13,10,26,10]))

class Chunk(pstruct.type):
    def __data(self):
        cb, res = self['length'].li, self['type'].li
        return Chunks.withdefault(res.serialize(), length=cb.int())

    def __data(self):
        type, length = self['type'].li, self['length'].li
        result = Chunks.withdefault(type.serialize(), type=type.serialize(), length=length.int())
        if issubclass(result, (ptype.block, parray.block)):

            # check if chunk data length seeks outside of file
            if isinstance(self.source, ptypes.provider.bounded):
                chunk = 0xc
                default = self.source.size() - chunk - self.getoffset() - (type.size() + length.size() + 4)
                if self.getoffset() + type.size() + 2*length.size() + length.int() < self.source.size():
                    res = length.int()
                elif default > 0:
                    logging.fatal("{:s}: Size of data {:x}{:+x} for chunk type {:s} is larger than file contents and IEND chunk. Using {:+x} for data length instead to keep this included.".format(self.instance(), self.getoffset() + type.size() + length.size(), length.int(), type.str(), default))
                    res = default
                else:
                    res = 0
                return dyn.clone(result, blocksize=lambda _, cb=res: cb)

            # otherwise we're just safe to use it
            return dyn.clone(result, blocksize=lambda _, cb=length.int(): cb)
        return result

    def Calculate(self):
        res = self['type'].serialize() + self['data'].serialize()
        return make_crc(res, Table)

    @property
    def Valid(self):
        return self.Calculate() == self['crc'].int()

    def properties(self):
        res = super(Chunk, self).properties()
        res['CRC'] = self.Calculate()
        try: res['Valid'] = res['CRC'] == self['crc'].int()
        except: res['Valid'] = False
        return res

    _fields_ = [
        (pint.uint32_t, 'length'),
        (ChunkType, 'type'),
        (__data, 'data'),
        (pint.uint32_t, 'crc'),
    ]

class File(pstruct.type):
    class Data(parray.terminated):
        _object_ = Chunk
        def isTerminator(self, value):
            return value['type'].serialize() == IEND.type

    _fields_ = [
        (Signature, 'signature'),
        (Data, 'data'),
    ]

@Chunks.define
class IHDR(pstruct.type):
    type = b'IHDR'

    class ColorType(pint.enum, pint.uint8_t):
        _values_ = [
            ('Grayscale', 0),
            ('TrueColor', 2),
            ('Palette', 3),
            ('Grayscale/Alpha', 4),
            ('TrueColor/Alpha', 6),
        ]

    class CompressionMethod(pint.enum, pint.uint8_t):
        _values_ = [
            ('Deflate/Inflate', 0),
        ]

    class FilterMethod(pint.enum, pint.uint8_t):
        _values_ = [
            ('Adaptive', 0),
        ]

    class InterlaceMethod(pint.enum, pint.uint8_t):
        _values_ = [
            ('None', 0),
            ('Adam7', 1),
        ]

    _fields_ = [
        (pint.uint32_t, 'Width'),
        (pint.uint32_t, 'Height'),
        (pint.uint8_t, 'Bit depth'),
        (ColorType, 'Colour type'),
        (CompressionMethod, 'Compression method'),
        (FilterMethod, 'Filter method'),
        (InterlaceMethod, 'Interlace method'),
    ]

@Chunks.define
class pHYs(pstruct.type):
    type = b'pHYs'
    class _unit(pint.enum, pint.uint8_t):
        _values_ = [
            ('unspecified', 0),
            ('meters', 1),
        ]
    _fields_ = [
        (pint.uint32_t, 'X-axis'),
        (pint.uint32_t, 'Y-axis'),
        (_unit, 'Unit Specifier'),
    ]

@Chunks.define
class sCAL(pstruct.type):
    type = b'sCAL'
    class _unit(pint.enum, pint.uint8_t):
        _values_ = [
            ('meters', 1),
            ('radians', 2),
        ]
    _fields_ = [
        (_unit, 'Unit Specifier'),
        (pstr.szstring, 'X-axis'),
        (pint.uint8_t, 'Null Separator'),
        (pstr.szstring, 'Y-axis'),
    ]

@Chunks.define
class IDAT(ptype.block):
    type = b'IDAT'

@Chunks.define
class tEXt(pstruct.type):
    type = b'tEXt'
    def __Text(self):
        res = self.getparent(Chunk)
        cb, length = self['Keyword'].li.size(), res['length'].li
        return dyn.clone(pstr.string, length=length.int() - cb)

    _fields_ = [
        (pstr.szstring, 'Keyword'),
        (__Text, 'Text'),
    ]

@Chunks.define
class zTXt(pstruct.type):
    type = b'zTXt'
    def __CompressedText(self):
        res = self.getparent(Chunk)
        cb, length = self['Keyword'].li.size() + self['Compression method'].li.size(), res['length'].li
        return dyn.block(length.int() - cb)

    _fields_ = [
        (pstr.szstring, 'Keyword'),
        (IHDR.CompressionMethod, 'Compression method'),
        (__CompressedText, 'Compressed text'),
    ]

@Chunks.define
class PLTE(parray.block):
    type = b'PLTE'
    class Entry(pstruct.type):
        _fields_ = [(pint.uint8_t,x) for x in 'rgb']
    _object_ = Entry

@Chunks.define
class IEND(ptype.block):
    type = b'IEND'

ChunkType._values_[:] = [(t.__name__, intofdata(key)) for key, t in Chunks.cache.items()]

if __name__ == '__main__':
    import sys
    import ptypes, image.png

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.png.File()
    a = a.l
