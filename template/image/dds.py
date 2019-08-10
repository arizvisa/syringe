import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, reversed(data)), 0)
_dataofint = lambda integer: ((integer == 0) and '\x00') or (_dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))
dataofint = lambda integer, be=_dataofint: str().join(reversed(be(integer)))

## primitive types
class uint(pint.uint32_t): pass

## enumerations
class fourcc(pint.enum, uint):
    _values_ = [
        ('NVTT', intofdata('NVTT')),
        ('DDS',  intofdata('DDS ')),
        ('DXT1', intofdata('DXT1')),
        ('DXT2', intofdata('DXT2')),
        ('DXT3', intofdata('DXT3')),
        ('DXT4', intofdata('DXT4')),
        ('DXT5', intofdata('DXT5')),
        ('RXGB', intofdata('RXGB')),
        ('ATI1', intofdata('ATI1')),
        ('ATI2', intofdata('ATI2')),
        ('A2XY', intofdata('A2XY')),
        ('DX10', intofdata('DX10')),
        ('UVER', intofdata('UVER')),
    ]

class DXGI_FORMAT(pint.enum, uint):
    _values_ = [
        ('UNKNOWN', 0),
        ('R32G32B32A32_TYPELESS', 1),
        ('R32G32B32A32_FLOAT', 2),
        ('R32G32B32A32_UINT', 3),
        ('R32G32B32A32_SINT', 4),
        ('R32G32B32_TYPELESS', 5),
        ('R32G32B32_FLOAT', 6),
        ('R32G32B32_UINT', 7),
        ('R32G32B32_SINT', 8),
        ('R16G16B16A16_TYPELESS', 9),
        ('R16G16B16A16_FLOAT', 10),
        ('R16G16B16A16_UNORM', 11),
        ('R16G16B16A16_UINT', 12),
        ('R16G16B16A16_SNORM', 13),
        ('R16G16B16A16_SINT', 14),
        ('R32G32_TYPELESS', 15),
        ('R32G32_FLOAT', 16),
        ('R32G32_UINT', 17),
        ('R32G32_SINT', 18),
        ('R32G8X24_TYPELESS', 19),
        ('D32_FLOAT_S8X24_UINT', 20),
        ('R32_FLOAT_X8X24_TYPELESS', 21),
        ('X32_TYPELESS_G8X24_UINT', 22),
        ('R10G10B10A2_TYPELESS', 23),
        ('R10G10B10A2_UNORM', 24),
        ('R10G10B10A2_UINT', 25),
        ('R11G11B10_FLOAT', 26),
        ('R8G8B8A8_TYPELESS', 27),
        ('R8G8B8A8_UNORM', 28),
        ('R8G8B8A8_UNORM_SRGB', 29),
        ('R8G8B8A8_UINT', 30),
        ('R8G8B8A8_SNORM', 31),
        ('R8G8B8A8_SINT', 32),
        ('R16G16_TYPELESS', 33),
        ('R16G16_FLOAT', 34),
        ('R16G16_UNORM', 35),
        ('R16G16_UINT', 36),
        ('R16G16_SNORM', 37),
        ('R16G16_SINT', 38),
        ('R32_TYPELESS', 39),
        ('D32_FLOAT', 40),
        ('R32_FLOAT', 41),
        ('R32_UINT', 42),
        ('R32_SINT', 43),
        ('R24G8_TYPELESS', 44),
        ('D24_UNORM_S8_UINT', 45),
        ('R24_UNORM_X8_TYPELESS', 46),
        ('X24_TYPELESS_G8_UINT', 47),
        ('R8G8_TYPELESS', 48),
        ('R8G8_UNORM', 49),
        ('R8G8_UINT', 50),
        ('R8G8_SNORM', 51),
        ('R8G8_SINT', 52),
        ('R16_TYPELESS', 53),
        ('R16_FLOAT', 54),
        ('D16_UNORM', 55),
        ('R16_UNORM', 56),
        ('R16_UINT', 57),
        ('R16_SNORM', 58),
        ('R16_SINT', 59),
        ('R8_TYPELESS', 60),
        ('R8_UNORM', 61),
        ('R8_UINT', 62),
        ('R8_SNORM', 63),
        ('R8_SINT', 64),
        ('A8_UNORM', 65),
        ('R1_UNORM', 66),
        ('R9G9B9E5_SHAREDEXP', 67),
        ('R8G8_B8G8_UNORM', 68),
        ('G8R8_G8B8_UNORM', 69),
        ('BC1_TYPELESS', 70),
        ('BC1_UNORM', 71),
        ('BC1_UNORM_SRGB', 72),
        ('BC2_TYPELESS', 73),
        ('BC2_UNORM', 74),
        ('BC2_UNORM_SRGB', 75),
        ('BC3_TYPELESS', 76),
        ('BC3_UNORM', 77),
        ('BC3_UNORM_SRGB', 78),
        ('BC4_TYPELESS', 79),
        ('BC4_UNORM', 80),
        ('BC4_SNORM', 81),
        ('BC5_TYPELESS', 82),
        ('BC5_UNORM', 83),
        ('BC5_SNORM', 84),
        ('B5G6R5_UNORM', 85),
        ('B5G5R5A1_UNORM', 86),
        ('B8G8R8A8_UNORM', 87),
        ('B8G8R8X8_UNORM', 88),
        ('R10G10B10_XR_BIAS_A2_UNORM', 89),
        ('B8G8R8A8_TYPELESS', 90),
        ('B8G8R8A8_UNORM_SRGB', 91),
        ('B8G8R8X8_TYPELESS', 92),
        ('B8G8R8X8_UNORM_SRGB', 93),
        ('BC6H_TYPELESS', 94),
        ('BC6H_UF16', 95),
        ('BC6H_SF16', 96),
        ('BC7_TYPELESS', 97),
        ('BC7_UNORM', 98),
        ('BC7_UNORM_SRGB', 99),
    ]

class D3D10_RESOURCE_DIMENSION(pint.enum, uint):
    _values_ = [
		('UNKNOWN', 0),
		('BUFFER', 1),
		('TEXTURE1D', 2),
		('TEXTURE2D', 3),
		('TEXTURE3D', 4),
    ]

class DDPF(pbinary.flags):
    _fields_ = [
        (14, 'reserved_0(e)'),
        (1, 'LUMINANCE'),
        (1, 'reserved_f(1)'),
        (1, 'ALPHAPREMULT'),
        (2, 'reserved_11(2)'),
        (1, 'PALETTEINDEXED2'),
        (1, 'PALETTEINDEXED1'),
        (4, 'reserved_15(4)'),
        (1, 'RGB'),
        (1, 'PALETTEINDEXED8'),
        (1, 'reserved_1b(1)'),
        (1, 'PALETTEINDEXED4'),
        (1, 'FOURCC'),
        (1, 'ALPHA'),
        (1, 'ALPHAPIXELS'),
    ]

class DDSCAPS(pbinary.flags):
    _fields_ = [
        (9, 'reserved_0(9)'),
        (1, 'MIPMAP'),
        (9, 'reserved_a(9)'),
        (1, 'TEXTURE'),
        (8, 'reserved_14(8)'),
        (1, 'COMPLEX'),
        (3, 'reserved_1d(3)'),
    ]

class DDSCAPS2(pbinary.flags):
    _fields_ = [
        (10, 'reserved_0(a)'),
        (1, 'VOLUME'),
        (5, 'reserved_b(5)'),
        (1, 'CUBEMAP_NEGATIVEZ'),
        (1, 'CUBEMAP_POSITIVEZ'),
        (1, 'CUBEMAP_NEGATIVEY'),
        (1, 'CUBEMAP_POSITIVEY'),
        (1, 'CUBEMAP_NEGATIVEX'),
        (1, 'CUBEMAP_POSITIVEX'),
        (1, 'CUBEMAP'),
        (7, 'reserved_17(7)'),
    ]

class DDSD(pbinary.flags):
    _fields_ = [
        (8, 'reserved_0(8)'),
        (1, 'DEPTH'),
        (3, 'reserved_9(3)'),
        (1, 'LINEARSIZE'),
        (1, 'reserved_d(1)'),
        (1, 'MIPMAPCOUNT'),
        (4, 'reserved_f(4)'),
        (1, 'PIXELFORMAT'),
        (8, 'reserved_14(8)'),
        (1, 'PITCH'),
        (1, 'WIDTH'),
        (1, 'HEIGHT'),
        (1, 'CAPS'),
    ]

class DDSPixelFormat(pstruct.type):
    class _size(uint):
        @classmethod
        def default(cls):
            return cls().set(32)

    class _fourcc(fourcc):
        @classmethod
        def default(cls):
            return cls().set('DX10')

    _fields_ = [
        (_size, 'size'),
        (DDPF, 'flags'),
        (_fourcc, 'fourcc'),
        (uint, 'bitcount'),
        (uint, 'rmask'),
        (uint, 'gmask'),
        (uint, 'bmask'),
        (uint, 'amask'),
    ]

class DDSCaps(pstruct.type):
    _fields_ = [
        (DDSCAPS, 'caps1'),    # DDSCAPS_TEXTURE
        (DDSCAPS2, 'caps2'),
        (uint, 'caps3'),
        (uint, 'caps4'),
    ]

class DDSHeader10(pstruct.type):
    _fields_ = [
        (DXGI_FORMAT, 'dxgiFormat'),    # DXGI_FORMAT_UNKNOWN
        (D3D10_RESOURCE_DIMENSION, 'resourceDimension'),    # D3D10_RESOURCE_DIMENSION_UNKNOWN
        (uint, 'miscFlag'),
        (uint, 'arraySize'),
        (uint, 'reserved'),
    ]

class DDSHeader(pstruct.type):
    class _magic(fourcc):
        @classmethod
        def default(cls):
            return cls().set('DDS')
        def valid(self):
            return self.default().int() == self.int()
        def properties(self):
            res = super(DDSHeader._magic, self).properties()
            res['valid'] = self.valid()
            return res

    class _size(pint.uint32_t):
        @classmethod
        def default(cls):
            return cls().set(124)

    def __header10(self):
        pf = self['pf'].li
        return DDSHeader10 if pf['fourcc'] == 'DX10' else ptype.undefined

    _fields_ = [
        (_magic, 'fourcc'),   # FOURCC_DDS
        (_size, 'size'),     # 124
        (DDSD, 'flags'),
        (uint, 'height'),
        (uint, 'width'),
        (uint, 'pitch'),
        (uint, 'depth'),
        (uint, 'mipmapcount'),
        (dyn.array(uint,11), 'reserved'),   # 9->FOURCC_NVT, 10->major(16).minor(8).revision(0)
        (DDSPixelFormat, 'pf'),
        (DDSCaps, 'caps'),
        (uint, 'notused'),
        (__header10, 'header10'),
    ]

class Color32(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'b'),
        (pint.uint8_t, 'g'),
        (pint.uint8_t, 'r'),
        (pint.uint8_t, 'a'),
    ]

class File(pstruct.type):
    _fields_ = [
        (DDSHeader, 'header'),
        (ptype.block, 'data'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, image.dds

    if len(sys.argv) != 2:
        print "Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__)
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.dds.File()
    a = a.l
