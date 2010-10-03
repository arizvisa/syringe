import ptypes
from ptypes import *

class int8(pint.int8_t): pass
class uint8(pint.uint8_t): pass
class Fixed(pint.uint32_t): pass
class Integer(pint.uint16_t): pass
class Long(pint.uint32_t): pass
class Mode(pint.uint16_t): pass
class Opcode(pint.uint16_t): pass
class Pattern(pint.uint64_t): pass
class Point(pint.uint32_t): pass
class Rect(dyn.block(8)): pass

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass
class SHORT(pint.int16_t): pass
class LONG(pint.int32_t): pass

class header(pstruct.type):
    _fields_ = [
        (SHORT, 'filesize'),
        (SHORT, 'x1'),
        (SHORT, 'y1'),
        (SHORT, 'x2'),
        (SHORT, 'y2'),
    ]

class header_v1(pstruct.type):
    _fields_ = [
        (BYTE, 'operator'),
        (BYTE, 'number'),
    ]

class header_v2(pstruct.type):
    _fields_ = [
        (SHORT, 'operator'),
        (SHORT, 'number'),
    ]

class header_ext_v2(pstruct.type):
    _fields_ = [
        (SHORT, 'opcode'),
        (SHORT, 'ffee'),
        (SHORT, 'reserved_8'),
        (LONG, 'horizontal res'),
        (LONG, 'vertical res'),
        (SHORT, 'x1'),
        (SHORT, 'y1'),
        (SHORT, 'x2'),
        (SHORT, 'y2'),
        (LONG, 'reserved'),
    ]

class picSize(pstruct.type):
    _fields_ = [
        (WORD, 'size'),
        (WORD, 'top'),
        (WORD, 'left'),
        (WORD, 'bottom'),
        (WORD, 'right'),
    ]

class picFrame_v1(pstruct.type):
    _fields_ = [
        (BYTE, 'version'),
        (BYTE, 'picture'),
    ]

class picFrame_v2(pstruct.type):
    _fields_ = [
        (WORD, 'version'),
        (WORD, 'picture'),
        (WORD, 'opcode'),
        (DWORD, 'size'),
        (DWORD, 'hres'),
        (DWORD, 'vres'),
        (WORD, 'x1'),
        (WORD, 'y1'),
        (WORD, 'x2'),
        (WORD, 'y2'),
        (DWORD, 'reserved'),
    ]

class bounds(pstruct.type):
    _fields_ = [
        (WORD, 'top'),
        (WORD, 'left'),
        (WORD, 'bottom'),
        (WORD, 'right'),
    ]

class pixMap(pstruct.type):
    _fields_ = [
        (DWORD, 'baseAddr'),
        (WORD, 'rowBytes'),
        (bounds, 'bounds'),
        (WORD, 'pmVersion'),
        (WORD, 'packType'),
        (DWORD, 'packSize'),
        (DWORD, 'hRes'),
        (DWORD, 'vRes'),
        (WORD, 'pixelType'),
        (WORD, 'pixelSize'),
        (WORD, 'cmpCount'),
        (WORD, 'cmpSize'),
        (DWORD, 'planeBytes'),
        (DWORD, 'pmTable'),
        (DWORD, 'pmReserved'),
    ]

class directBitsRect(pstruct.type):
    opcode = 0x009a
    _fields_ = [
        (pixMap, 'pixMap'),
        (bounds, 'srcRect'),
        (bounds, 'dstRect'),
        (WORD, 'mode'),
    ]

class File_v2(pstruct.type):
    _fields_ = [
        (dyn.block(0x200), 'padding'),
        (header, 'h'),
        (header_v2, 'v2'),
        (header_ext_v2, 'ext_v2'),
        (picSize, 'picSize'),
        (picFrame_v2, 'picFrame_v2'),
        (directBitsRect, 'bits'),
    ]

# default to v2
class File(File_v2): pass

if __name__ == '__main__':
    input = ptypes.provider.file('y:/cases/pucik0044/pict_pixdata_heap/poc.pict')
    
    if False:
        import sys
        sys.path.append('f:/work/syringe.git/lib')

    x = header()
    x.source = input
    x.setoffset(512)
    print x.load()
    print x['filesize']

    x = x.newelement(header_v2, 'v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(header_ext_v2, 'ext_v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(picSize, 'picsize', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(picFrame_v2, 'picframe_v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(directBitsRect, 'directBitsRect', 0x250+2)
    print x.load()
