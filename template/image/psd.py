'''
https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/#50577409_19840
'''
import ptypes
from ptypes import *

pint.setbyteorder('big')

class u0(pint.uint_t): pass
class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u32(pint.uint32_t): pass
class s0(pint.sint_t): pass
class s8(pint.sint8_t): pass
class s16(pint.sint16_t): pass
class s32(pint.sint32_t): pass

class Header(pstruct.type):
    class _Signature(pint.enum, u32):
        _values_ = [
            ('Default', 0x38425053),
        ]
    class _Mode(pint.enum, u16):
        _values_ = [
            ('Bitmap', 0),
            ('Grayscale', 1),
            ('Indexed', 2),
            ('RGB', 3),
            ('CMYK', 4),
            ('Multichannel', 7),
            ('Duotone', 8),
            ('Lab', 9),
        ]

    _fields_ = [
        (_Signature, 'Signature'),      # always equal to '8BPS'.
        (u16, 'Version'),               # always equal to 1.
        (dyn.block(6), 'Reserved'),     # must be zero.
        (u16, 'Channels'),              # The number of channels in the image, including any alpha channels.
        (u32, 'Height'),                # The height of the image in pixels.
        (u32, 'Width'),                 # The width of the image in pixels.
        (u16, 'Depth'),                 # The number of bits per channel.
        (_Mode, 'Mode'),                # The color mode of the file.
    ]
    def alloc(self, **fields):
        fields.setdefault('Signature', 'Default')
        fields.setdefault('Version', 1),
        res = super(Header, self).alloc(**fields)

        if any(res['Mode'][fld] for fld in ['Bitmap', 'Indexed', 'Grayscale']) and 'Channels' not in fields:
            res['Channels'].set(1)
        elif res['Mode']['RGB'] and 'Channels' not in fields:
            res['Channels'].set(3)
        elif res['Mode']['CMYK'] and 'Channels' not in fields:
            res['Channels'].set(4)

        if 'Depth' not in fields:
            res['Depth'].set(8)
        return res

class SectionBlock(pstruct.type):
    _fields_ = [
        (u32, 'length'),
        (lambda self: dyn.block(self['length'].li.int()), 'data'),
    ]
    def alloc(self, **fields):
        res = super(SectionBlock, self).alloc(**fields)
        return res if 'length' in fields else res.set(length=res['data'].size())

class ColorModeData(SectionBlock): pass
class ImageResources(SectionBlock): pass
class LayerAndMaskInformation(SectionBlock): pass

class ImageData(pstruct.type):
    class _Compression(pint.enum, u16):
        _values_ = [
            ('Raw', 0),
            ('RLE', 1),
            ('ZIP/prediction', 2),
            ('ZIP', 3),
        ]
    _fields_ = [
        (_Compression, 'Compression'),  # Compression method
        (ptype.block, 'Data'),
    ]

class File(pstruct.type):
    _fields_ = [
        (Header, 'Header'),
        (ColorModeData, 'ColorModeData'),
        (ImageResources, 'ImageResources'),
        (LayerAndMaskInformation, 'LayerAndMaskInformation'),
        (ImageData, 'ImageData'),
        (ptype.block, 'Extra'),
    ]
    def alloc(self, **fields):
        fields.setdefault('Header', Header)
        return super(File, self).alloc(**fields)

if __name__ == '__main__':
    import sys
    import ptypes, image.psd as psd

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='rb'))

    z = psd.File()
    z = z.l
    print(z.size() == z.source.size(), z.size(), z.source.size())

    print(z)
    print(z['Header'])

    sys.exit(0 if z.size() == z.source.size() else 1)
