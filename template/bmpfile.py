import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

class BYTE(pint.uint8_t): pass
class DWORD(pint.uint32_t): pass
class LONG(pint.int32_t): pass
class WORD(pint.uint16_t): pass

class BITMAPFILEHEADER(pstruct.type):
    _fields_ = [
        ( WORD, 'bfType' ),
        ( DWORD, 'bfSize' ),
        ( WORD, 'bfReserved1' ),
        ( WORD, 'bfReserved2' ),
        ( DWORD, 'bfOffBits' )
    ]

class biCompression(pint.enum, DWORD):
    _values_ = [
        ('BI_RGB', 0),
        ('BI_RLE8', 1),
        ('BI_RLE4', 2),
        ('BI_BITFIELDS', 3),
        ('BI_JPEG', 4),
        ('BI_PNG', 5),
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

class BITMAPINFO(pstruct.type):
    def __bmiColors(self):
        header = self['bmiHeader'].li
        clrsused = header['biClrUsed'].int()
        bitcount = header['biBitCount'].int()

        # XXX: this is incorrect, but i'm lazy right now.
#        if clrsused == 0:
#            return dyn.array(RGBQUAD, 1<<bitcount)
        return dyn.array(RGBQUAD, clrsused)

    def __bmiExtra(self):
        hdr = self['bmiHeader'].li
        cb = hdr.size() + self['bmiColors'].li.size()
        return dyn.block(max((hdr['biSize'].int() - cb, 0)))

    _fields_ = [
        (BITMAPINFOHEADER, 'bmiHeader'),
        (__bmiColors, 'bmiColors'),
        (__bmiExtra, 'bmiExtra'),
    ]

class BITMAPCOREHEADER(pstruct.type):
    _fields_ = [
        (DWORD, 'bcSize'),
        (WORD, 'bcWidth'),
        (WORD, 'bcHeight'),
        (WORD, 'bcPlanes'),
        (WORD, 'bcBitcount'),
    ]

class File(pstruct.type):
    _fields_ = [
        ( BITMAPFILEHEADER, 'header'),
        ( BITMAPINFO, 'info'),
        # XXX: this size is only valid for jpeg and png. but i'm trusting it for rle8 too
        ( lambda s: dyn.block(s['info'].li['bmiHeader']['biSizeImage'].int()), 'data')
    ]

if __name__ == '__main__':
    pass
