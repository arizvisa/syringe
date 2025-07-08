import ptypes
from ptypes import *

pint.setbyteorder('little')

class Window(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'Xmin'),
        (pint.uint16_t, 'Ymin'),
        (pint.uint16_t, 'Xmax'),
        (pint.uint16_t, 'Ymax'),
    ]
    def Width(self):
        xmin, xmax = (self[fld].int() for fld in ['Xmin', 'Xmax'])
        return xmax - xmin + 1
    def Height(self):
        ymin, ymax = (self[fld].int() for fld in ['Ymin', 'Ymax'])
        return ymax - ymin + 1

class RGB(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'R'),
        (pint.uint8_t, 'G'),
        (pint.uint8_t, 'B'),
    ]
    def set(self, *values, **fields):
        if not(values):
            return super(RGB, self).set(**fields)
        [rgb] = values
        red, _   = divmod(rgb & 0x00FF0000, 16)
        green, _ = divmod(rgb & 0x0000FF00, 8)
        blue, _  = divmod(rgb & 0x000000FF, 0)
        return super(RGB, self).set(R=red, G=green, B=blue)

class Colormap(parray.type):
    length, _object_ = 16, RGB

class Header(pstruct.type):
    class _manufacturer(pint.enum, pint.uint8_t):
        _values_ = [
            ('ZSoft', 10),  # ZSoft .pcx
        ]
    class _version(pint.enum, pint.uint8_t):
        _values_ = [
            ('2.5', 0),         # Version 2.5 of PC Paintbrush
            ('2.8 palette', 2), # Version 2.8 w/palette information
            ('2.8', 3),         # Version 2.8 w/o palette information
            ('Paintbrush', 4),  # PC Paintbrush for Windows(Plus for Windows uses Ver 5)
            ('3.0', 5),         # Version 3.0 and > of PC Paintbrush and PC Paintbrush +, includes Publisher's Paintbrush.
        ]
    class _encoding(pint.enum, pint.uint8_t):
        _values_ = [
            ('Uncompressed', 0),
            ('RLE', 1),
        ]
    class _paletteInfo(pint.enum, pint.uint16_t):
        _values_ = [
            ('Color', 1),       # Color/BW
            ('Grayscale', 2),   # Grayscale (ignored in PB IV/ IV +)
        ]
    _fields_ = [
        (_manufacturer, 'Manufacturer'),    # Constant Flag
        (_version, 'Version'),              # Version information
        (_encoding, 'Encoding'),            # .PCX run length encoding
        (pint.uint8_t, 'BitsPerPixel'),     # Number of bits to represent a pixel (per Plane) - 1, 2, 4, or 8
        (Window, 'Window'),                 # Image Dimensions: Xmin,Ymin,Xmax,Ymax
        (pint.uint16_t, 'HDpi'),            # Horizontal Resolution of image in DPI*
        (pint.uint16_t, 'VDpi'),            # Vertical Resolution of image in DPI*
        (Colormap, 'Colormap'),             # Color palette setting, see text
        (pint.uint8_t, 'Reserved'),         # Should be set to 0.
        (pint.uint8_t, 'NPlanes'),          # Number of color planes
        (pint.uint16_t, 'BytesPerLine'),    # Number of bytes to allocate for a scanline plane.  MUST be an EVEN number.  Do NOT calculate from Xmax-Xmin.
        (_paletteInfo, 'PaletteInfo'),      # How to interpret palette
        (pint.uint16_t, 'HscreenSize'),     # Horizontal screen size in pixels. New field found only in PB IV/IV Plus
        (pint.uint16_t, 'VscreenSize'),     # Vertical screen size in pixels. New field found only in PB IV/IV Plus
        (dyn.block(54), 'Filler'),          # Blank to fill out 128 byte header.
    ]

    def alloc(self, **fields):
        res = super(Header, self).alloc(**fields)
        if 'Manufacturer' not in fields:
            res['Manufacturer'].set(0x0A)
        if 'Version' not in fields:
            res['Version'].set(5)
        if 'Encoding' not in fields:
            res['Encoding'].set('Uncompressed')
        if 'BitsPerPixel' not in fields:
            res['BitsPerPixel'].set(8)
        if 'Reserved' not in fields:
            res['Reserved'].set(0)
        if 'NPlanes' not in fields:
            res['NPlanes'].set(1)
        if 'BytesPerLine' not in fields:
            bytesperpixel = res['BitsPerPixel'].int() // 8
            width = res['Window'].Width()
            res['BytesPerLine'].set(width * bytesperpixel)
        return res

class RLEMarker(pbinary.struct):
    class _marker(pbinary.enum):
        length, _values_ = 2, [
            ('SAIL_PCX_RLE_MARKER', 0b11),
        ]
    _fields_ = [
        (_marker, 'marker'),
        (6, 'count'),
    ]
    def alloc(self, **fields):
        fields.setdefault('marker', 'SAIL_PCX_RLE_MARKER')
        return super(RLEMarker, self).alloc(**fields)

class RLE(pstruct.type):
    def __value(self):
        res = self['marker'].li
        if res.field('marker')['SAIL_PCX_RLE_MARKER']:
            return pint.uint8_t
        return pint.uint_t
    _fields_ = [
        (RLEMarker, 'marker'),
        (__value, 'value'),
    ]
    def alloc(self, **fields):
        count = fields.pop('count', 0)
        newfields = fields.copy()
        newfields.setdefault('marker', RLEMarker)
        res = super(RLE, self).alloc(**newfields)
        if 'marker' not in fields:
            res['marker'].set(count=count)
        return res
    def GetPixelCount(self):
        marker = self['marker']
        if marker['marker']['SAIL_PCX_RLE_MARKER']:
            return marker['count'], self['value'].int()
        return 1, self['marker'].int()

class PaletteWithSignature(pstruct.type):
    def __Entries(self):
        res = self['Signature'].li
        if res.int() == 12:
            return dyn.array(RGB, 0x100)
        return dyn.array(RGB, 0)
    _fields_ = [
        (pint.uint8_t, 'Signature'),
        (__Entries, 'Entries'),
    ]
    def alloc(self, **fields):
        fields.setdefault('Signature', 12)
        return super(PaletteWithSignature, self).alloc(**fields)

class File(pstruct.type):
    def __ImageData(self):
        res = self['Header'].li
        planes = res['NPlanes']
        return ptype.block

    def __Palette(self):
        res = self['Header'].li
        planes, bits = (res[fld].li.int() for fld in ['NPlanes', 'BitsPerPixel'])
        if (planes, bits) == (1, 8):
            return PaletteWithSignature
        return pstruct.type

    _fields_ = [
        (Header, 'Header'),
        (__ImageData, 'Image'),
        (ptype.block, 'Padding'),
        (__Palette, 'Palette'),
        (ptype.block, 'Extra'),
    ]

    def alloc(self, **fields):
        fields.setdefault('Header', Header)
        return super(File, self).alloc(**fields)

if __name__ == '__main__':
    import sys
    import ptypes, image.pcx as pcx

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='rb'))

    z = pcx.File()
    z = z.l
    print(z.size() == z.source.size(), z.size(), z.source.size())

    print(z)
    print(z['Header'])

    sys.exit(0 if z.size() == z.source.size() else 1)
