import ptypes, logging
from ptypes import *
import array,functools

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
    for b in bytearray(data):
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
            res, type = super(Chunks.UnknownChunk, self).classname(), self.type.decode('latin1') if isinstance(self.type, bytes) else (self.type or '????')
            return '{:s}<{:s}>[size:{:#x}]'.format(res, type, self.blocksize())

    default = UnknownChunk
    class _enum_(pint.enum, pint.uint32_t): pass

class ChunkType(Chunks.enum):
    pass

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
        except Exception: res['Valid'] = False
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

@Chunks.define
class bKGD(ptype.block):
    type = b'bKGD'

@Chunks.define
class tIME(ptype.block):
    type = b'tIME'

@Chunks.define
class hIST(ptype.block):
    type = b'hIST'

@Chunks.define
class sPLT(ptype.block):
    type = b'sPLT'

@Chunks.define
class sBIT(ptype.block):
    type = b'sBIT'

@Chunks.define
class oFFs(ptype.block):
    type = b'oFFs'

@Chunks.define
class pCAL(ptype.block):
    type = b'pCAL'

@Chunks.define
class fRAc(ptype.block):
    type = b'fRAc'

@Chunks.define
class gIFg(ptype.block):
    type = b'gIFg'

@Chunks.define
class gIFx(ptype.block):
    type = b'gIFx'

@Chunks.define
class gIFt(ptype.block):
    type = b'gIFt'

@Chunks.define
class aLIG(ptype.block):
    type = b'aLIG'

@Chunks.define
class fING(ptype.block):
    type = b'fING'

@Chunks.define
class fALS(ptype.block):
    type = b'fALS'

@Chunks.define
class xSCL(ptype.block):
    type = b'xSCL'

@Chunks.define
class ySCL(ptype.block):
    type = b'ySCL'

@Chunks.define
class acTL(pstruct.type):
    type = b'acTL'
    _fields_ = [
        (pint.uint32_t, 'num_frames'),  # Number of frames
        (pint.uint32_t, 'num_plays'),   # Number of times to loop this APNG.  0 indicates infinite looping.
    ]

@Chunks.define
class fcTL(pstruct.type):
    type = b'fcTL'
    class APNG_DISPOSE_OP_(pint.enum, pint.uint8_t):
        _values_ = [
            (0, 'NONE'),
            (1, 'BACKGROUND'),
            (2, 'PREVIOUS'),
        ]
    class APNG_BLEND_OP_(pint.enum, pint.uint8_t):
        _values_ = [
            (0, 'SOURCE'),
            (1, 'OVER'),
        ]
    _fields_ = [
        (pint.uint32_t, 'sequence_number'),     # Sequence number of the animation chunk, starting from 0
        (pint.uint32_t, 'width'),               # Width of the following frame
        (pint.uint32_t, 'height'),              # Height of the following frame
        (pint.uint32_t, 'x_offset'),            # X position at which to render the following frame
        (pint.uint32_t, 'y_offset'),            # Y position at which to render the following frame
        (pint.uint16_t, 'delay_num'),           # Frame delay fraction numerator
        (pint.uint16_t, 'delay_den'),           # Frame delay fraction denominator
        (pint.uint8_t, 'dispose_op'),           # Type of frame area disposal to be done after rendering this frame
        (pint.uint8_t, 'blend_op'),             # Type of frame area rendering for this frame
    ]

@Chunks.define
class fdAT(ptype.block):
    type = b'fdAT'

if __name__ == '__main__':
    import sys
    import ptypes, image.png

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.png.File()
    a = a.l
