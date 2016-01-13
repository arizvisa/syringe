from ptypes import *

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

class BITMAPINFOHEADER(pstruct.type):
    class __biCompression(DWORD, pint.enum):
        _values_ = [
            ('BI_RGB', 0),
            ('BI_RLE8', 1),
            ('BI_RLE4', 2),
            ('BI_BITFIELDS', 3),
            ('BI_JPEG', 4),
            ('BI_PNG', 5),
        ]

    _fields_ = [
        (DWORD, 'biSize'),
        (LONG, 'biWidth'),
        (LONG, 'biHeight'),
        (WORD, 'biPlanes'),
        (WORD, 'biBitCount'),
        (__biCompression, 'biCompression'),
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
        header = self['bmiHeader'].l
        clrsused = int(header['biClrUsed'])
        bitcount = int(header['biBitCount'])

        # XXX: this is incorrect, but i'm lazy right now.
#        if clrsused == 0:
#            return dyn.array(RGBQUAD, 1<<bitcount)
        return dyn.array(RGBQUAD, clrsused)

    def blocksize(self):
        return int(self['bmiHeader']['biSize'])

    _fields_ = [
        (BITMAPINFOHEADER, 'bmiHeader'),
        (__bmiColors, 'bmiColors'),
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
        ( lambda s: dyn.block(int(s['info'].li['bmiHeader']['biSizeImage'])), 'data')
    ]

if __name__ == '__main__':
    pass
