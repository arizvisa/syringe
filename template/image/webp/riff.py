import functools, ptypes
from ptypes import *

pint.setbyteorder('little')

class u0(pint.uint_t): pass
class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u24(pint.uint_t): length = 3
class u32(pint.uint32_t): pass
class s0(pint.sint_t): pass
class s8(pint.sint8_t): pass
class s16(pint.sint16_t): pass
class s24(pint.sint_t): length = 3
class s32(pint.sint32_t): pass

class ColorBGRA(pstruct.type):
    _fields_ = [
        (u8, 'B'),
        (u8, 'G'),
        (u8, 'R'),
        (u8, 'A'),
    ]

class ChunkType(ptype.definition):
    attribute, cache = 'type', {}

    @classmethod
    def to_integer(self, key):
        if isinstance(key, ptypes.integer_types):
            integer = key
        elif isinstance(key, (bytes, bytearray)):
            integer = functools.reduce(lambda agg, item: agg * 0x100 + item, bytearray(key), 0)
        elif isinstance(key, ptypes.string_types):
            encoded = key.encode('latin1')
            integer = functools.reduce(lambda agg, item: agg * 0x100 + item, bytearray(encoded), 0)
        else:
            raise TypeError(key)
        return integer

    @classmethod
    def __set__(cls, key, object, **kwargs):
        integer = cls.to_integer(key)
        return super(ChunkType, cls).__set__(integer, object, **kwargs)

    @classmethod
    def __get__(cls, key, default, **kwargs):
        integer = cls.to_integer(key)
        return super(ChunkType, cls).__get__(integer, default, **kwargs)

    @pint.bigendian
    class _enum_(pint.enum, u32):
        pass

class Id(ChunkType.enum):
    def summary(self):
        res = self.serialize()
        return "{:#x} {!r}".format(self, res.decode('latin1'))

class Chunk(pstruct.type):
    def __data(self):
        res, length = (self[fld].li for fld in ['id', 'size'])
        data_t = self._object_ if hasattr(self, '_object_') else ChunkType.withdefault(res.serialize(), type=res.serialize(), length=length.int())
        if isinstance(data_t, parray.block):
            return dyn.clone(data_t, blocksize=lambda self, size=length.int(): size)
        elif isinstance(data_t, ptype.block):
            return dyn.clone(data_t, length=length.int()) if length.int() else data_t
        return data_t
    def __extra(self):
        res, fields = self['size'].li, ['data']
        length = max(0, res.int() - sum(self[fld].li.size() for fld in fields))
        _, odd = divmod(length, 2)
        if odd and length:
            return dyn.block(1 + length)
        return dyn.block(length) if length else ptype.block
    _fields_ = [
        (Id, 'id'),
        (u32, 'size'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]
    def alloc(self, **fields):
        res = super(Chunk, self).alloc(**fields)
        if 'size' not in fields:
            res['size'].set(sum(res[fld].size() for fld in ['data', 'extra']))
        if 'id' not in fields and hasattr(res['data'], ChunkType.attribute):
            res['id'].set(getattr(res['data'], ChunkType.attribute))
        return res

class SizedChunkArray(parray.block):
    _object_ = Chunk

class ChunkArray(parray.type):
    _object_ = Chunk

@ChunkType.define
class RIFF(pstruct.type):
    type = b'RIFF'
    def __Chunks(self):
        if not(self.parent) or not(isinstance(self.parent, Chunk)):
            return ChunkArray
        sig = self['Signature'].li
        length = max(0, self.parent['size'].int() - sig.size())
        return dyn.clone(SizedChunkArray, blocksize=lambda self, size=length: size) if length else ChunkArray

    _fields_ = [
        (Id, 'Signature'),
        (__Chunks, 'Chunks'),
    ]

    def alloc(self, *values, **fields):
        fields.setdefault('Signature', b'WEBP')
        if not(values):
            fields.setdefault('Chunks', ChunkArray)
            return super(RIFF, self).alloc(**fields)

        [chunks] = values
        fields['Chunks'] = chunks
        return super(RIFF, self).alloc(**fields)

@ChunkType.define
class VP8(ptype.block):
    type = b'VP8 '

@ChunkType.define
class VP8L(ptype.block):
    type = b'VP8L'

@ChunkType.define
class VP8X(pstruct.type):
    type = b'VP8X'
    class _Flags(pbinary.flags):
        _fields_ = [
            (2, 'Rsv'),         # Reserved (Rsv)
            (1, 'I'),           # ICC profile (I)
            (1, 'L'),           # Alpha (L)
            (1, 'E'),           # Exif metadata (E)
            (1, 'X'),           # XMP metadata (X)
            (1, 'A'),           # Animation (A)
            (1, 'R'),           # Reserved (R)
        ]
    _fields_ = [
        (_Flags, 'Flags'),
        (u24, 'Reserved'),      # Reserved
        (u24, 'WidthMinus1'),   # Canvas Width Minus One
        (u24, 'HeightMinus1'),  # Canvas Height Minus One
    ]

@ChunkType.define
class ICCP(pstruct.type):
    type = b'ICCP'

    def __ColorProfile(self):
        if not(self.parent) or not(isinstance(self.parent, Chunk)):
            return ptype.block
        res, fields = self.parent['size'].int(), ['Bits']
        length = max(0, res - sum(self[fld].li.size() for fld in fields))
        return dyn.block(length) if length else ptype.block

    # FIXME: we should be able to decode the color profile here too...
    _fields_ = [
        (__ColorProfile, 'ColorProfile'),
    ]

@ChunkType.define
class ANIM(pstruct.type):
    type = b'ANIM'
    _fields_ = [
        (ColorBGRA, 'BackgroundColor'),
        (u16, 'LoopCount'),
    ]

@ChunkType.define
class ANMF(pstruct.type):
    type = b'ANMF'

    class _methodBits(pbinary.flags):
        _fields_ = [
            (6, 'Reserved'),
            (1, 'NOBLEND'),
            (1, 'DISPOSE'),
        ]

    def __FrameData(self):
        if not(self.parent) or not(isinstance(self.parent, Chunk)):
            return ChunkArray
        res, fields = self.parent['size'].int(), ['X', 'Y', 'Width', 'Height', 'Duration']
        length = max(0, res - sum(self[fld].li.size() for fld in fields))
        return dyn.clone(SizedChunkArray, blocksize=lambda self, size=length: size) if length else ChunkArray

    _fields_ = [
        (u24, 'X'),
        (u24, 'Y'),
        (u24, 'WidthMinus1'),
        (u24, 'HeightMinus1'),
        (u24, 'Duration'),
        (_methodBits, 'Method'),
        (__FrameData, 'FrameData'),
    ]

@ChunkType.define
class Alpha(pstruct.type):
    type = b'ALPH'

    class _Bits(pbinary.flags):
        class _FilteringMethod(pbinary.enum):
            length, _values_ = 2, [
                ('None', 0),
                ('Horizontal', 1),
                ('Vertical', 2),
                ('Gradient', 3),
            ]
        _fields_ = [
            (2, 'Reserved'),
            (2, 'Preprocessing'),
            (_FilteringMethod, 'FilteringMethod'),
            (2, 'CompressionMethod'),
        ]

    def __Bitstream(self):
        if not(self.parent) or not(isinstance(self.parent, Chunk)):
            return ptype.block
        res, fields = self.parent['size'].int(), ['Bits']
        length = max(0, res - sum(self[fld].li.size() for fld in fields))
        return dyn.block(length) if length else ptype.block

    _fields_ = [
        (_Bits, 'Bits'),
        (__Bitstream, 'Bitstream'),
    ]

@ChunkType.define
class EXIF(ptype.block):
    type = b'EXIF'

@ChunkType.define
class XMP(ptype.block):
    type = b'XMP '
