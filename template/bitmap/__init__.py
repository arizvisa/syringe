from ptypes import *

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
    _fields_ = [
        (DWORD, 'biSize'),
        (LONG, 'biWidth'),
        (LONG, 'biHeight'),
        (WORD, 'biPlanes'),
        (WORD, 'biBitCount'),
        (DWORD, 'biCompression'),
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

if __name__ == '__main__':
    pass
