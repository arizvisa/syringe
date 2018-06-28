import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

## Atomic types
class BYTE(pint.uint8_t): pass
class DWORD(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class WORD(pint.uint16_t): pass

## Core bitmap types
class bfType(pint.enum, WORD):
    _values_ = [
        ('BM', 0x4d42),
        ('BA', 0x4142),
        ('CI', 0x4943),
        ('CP', 0x5043),
        ('IC', 0x4349),
        ('PT', 0x5450),
    ]

class biCompression(pint.enum, DWORD):
    _values_ = [
        ('BI_RGB', 0),
        ('BI_RLE8', 1),
        ('BI_RLE4', 2),
        ('BI_BITFIELDS', 3),
        ('BI_JPEG', 4),
        ('BI_PNG', 5),
        ('BI_ALPHABITFIELDS', 6),
        ('BI_CMYK', 11),
        ('BI_CMYKRLE8', 12),
        ('BI_CMYKRLE4', 13),
    ]

class BITMAPFILEHEADER(pstruct.type):
    _fields_ = [
        ( bfType, 'bfType' ),
        ( DWORD, 'bfSize' ),
        ( WORD, 'bfReserved1' ),
        ( WORD, 'bfReserved2' ),
        ( DWORD, 'bfOffBits' )
    ]

class BITMAPCOREHEADER(pstruct.type):
    _fields_ = [
        (DWORD, 'bcSize'),
        (WORD, 'bcWidth'),
        (WORD, 'bcHeight'),
        (WORD, 'bcPlanes'),
        (WORD, 'bcBitcount'),
    ]

class BITMAPINFOHEADER(pstruct.type):
    _fields_ = [
        (DWORD, 'biSize'),
        (LONG, 'biWidth'),
        (LONG, 'biHeight'),
        (WORD, 'biPlanes'),
        (WORD, 'biBitCount'),
        (biCompression, 'biCompression'),
        (DWORD, 'biSizeImage'),
        (LONG, 'biXPelsPerMeter'),
        (LONG, 'biYPelsPerMeter'),
        (DWORD, 'biClrUsed'),
        (DWORD, 'biClrImportant'),
    ]

class RGBQUAD(pstruct.type):
    _fields_ = [
        ( BYTE, 'rgbBlue' ),
        ( BYTE, 'rgbGreen' ),
        ( BYTE, 'rgbRed' ),
        ( BYTE, 'rgbReserved' )
    ]

    def summary(self):
        b, g, r, a = (self[n].int() for n in self.keys())
        return "rgba={:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)

## Dynamic types
class InfoHeaderType(ptype.definition): cache = {}

class BitmapInfoHeader(pstruct.type):
    _fields_ = [
        (DWORD, 'biSize'),
        (lambda s: InfoHeaderType.lookup(s['biSize'].li.int()), 'bmHeader'),
    ]

    def Colors(self): return self['bmHeader'].Colors()
    def Width(self): return self['bmHeader'].Width()
    def Height(self): return self['bmHeader'].Height()
    def Bits(self): return self['bmHeader'].Bits()

@InfoHeaderType.define(type=12)
class BitmapCore(pstruct.type):
    _fields_ = [
        (WORD, 'bcWidth'),
        (WORD, 'bcHeight'),
        (WORD, 'bcPlanes'),
        (WORD, 'bcBitcount'),
    ]

    def Width(self): return self['bcWidth'].int()
    def Height(self): return self['bcHeight'].int()
    def Bits(self): return self['bcBitcount'].int()
    def Colors(self): return 2 ** self.Bits()

@InfoHeaderType.define(type=40)
class BitmapInfo(pstruct.type):
    _fields_ = [
        (LONG, 'biWidth'),
        (LONG, 'biHeight'),
        (WORD, 'biPlanes'),
        (WORD, 'biBitCount'),
        (biCompression, 'biCompression'),
        (DWORD, 'biSizeImage'),
        (LONG, 'biXPelsPerMeter'),
        (LONG, 'biYPelsPerMeter'),
        (DWORD, 'biClrUsed'),
        (DWORD, 'biClrImportant'),
    ]

    def Width(self): return self['biWidth'].int()
    def Height(self): return self['biHeight'].int()
    def Bits(self): return self['biBitcount'].int()
    def Colors(self):
        res = self['biClrUsed'].int()
        return 2**self.Bits() if res or self.Bits() < 24 else res

# FIXME: this might not be complete
class DIB(pstruct.type):
    def __aColors(self):
        header = self['bmih'].li
        clrsused = header['biClrUsed'].int()
        bitcount = header['biBitCount'].int()

        return dyn.array(RGBQUAD, 2**bitcount if clsused == 0 or bitcount < 24 else clrsused)

    def __aBitmapBits(self):
        header = self['bmih'].li
        bitcount = header['biBitCount'].int()
        compression = header['biCompression']
        return dyn.block(header['biSizeImage'].int())

    _fields_ = [
        (BITMAPFILEHEADER, 'bmfh'),
        (BITMAPINFOHEADER, 'bmih'),
        (__aColors, 'aColors'),
        (__aBitmapBits, 'aBitmapBits'),
    ]

## File type
class File(pstruct.type):
    def __bmiColors(self):
        res = self['bmih'].li
        return dyn.array(RGBQUAD, res.Colors())

    def __bmiExtra(self):
        res = self['bmfh'].li
        cb = self['bmfh'].li.size() + self['bmih'].li.size() + self['bmiColors'].li.size()
        return dyn.block(res['bfOffBits'].li.int() - cb)

    def __bmData(self):
        res = self['bmfh'].li
        cb = self['bmfh'].li.size() + self['bmih'].li.size() + self['bmiColors'].li.size() + self['bmiExtra'].li.size()
        return dyn.block(res['bfSize'].li.int() - cb)

    _fields_ = [
        (BITMAPFILEHEADER, 'bmfh'),
        (BitmapInfoHeader, 'bmih'),
        (__bmiColors, 'bmiColors'),
        (__bmiExtra, 'bmiExtra'),
        (__bmData, 'bmData'),
    ]

if __name__ == '__main__':
    import ptypes, bmpfile
    import sys
    if len(sys.argv) != 2:
        print "Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__)
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='rb'))

    z = bmpfile.File()
    print "source: {!r}".format(z.source)

    z = z.l
    print z.size() == z.source.size(), z.size(), z.source.size()

    h = z['bmih']['bmHeader']
    print "dimensions: {:d}x{:d}x{:d} {:s}".format(h.Width(), h.Height(), h.Bits(), h['biCompression'].str())

    print z
    print z['bmih']
    print z['bmih']['bmHeader']
    print len(z['bmiColors'])
    sys.exit(0 if z.size() == z.source.size() else 1)
