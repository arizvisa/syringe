from ptypes import *

class Header(pstruct.type):
    _fields_ = [
        (dyn.block(3), 'Signature'),
        (dyn.block(3), 'Version'),
    ]

class LogicalScreenDescriptor(pstruct.type):
    class _Flags(pbinary.struct):
        _fields_ = [(1, 'Global Color Table'), (3, 'Color Resolution'), (1, 'Sort'), (3, 'Size')]

    def optional(self):
        if self['Flags'].li['Global Color Table'] > 0:
            return dyn.clone(ColorTable, length=2**(self['Flags']['Size']+1))
        return dyn.clone(ColorTable, length=0)

    _fields_ = [
        (pint.uint16_t, 'Width'),
        (pint.uint16_t, 'Height'),
        (_Flags, 'Flags'),
        (pint.uint8_t, 'BackgroundColorIndex'),
        (pint.uint8_t, 'PixelAspectRatio'),
        (optional, 'Global Color Table')
    ]

class Color(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'r'),
        (pint.uint8_t, 'g'),
        (pint.uint8_t, 'b'),
    ]

class ColorTable(parray.type):
    length = 0
    _object_ = Color

class ImageDescriptor(pstruct.type):
    class _Flags(pbinary.struct):
        _fields_ = [(1, 'Local Color Table'), (1, 'Interlace'), (1, 'Sort'), (2, 'Reserved'), (3, 'Size')]

    def optional(self):
        if self['Flags'].li['Local Color Table'] > 0:
            return dyn.clone(ColorTable, length=2**(self['Flags']['Size']+1))
        return dyn.clone(ColorTable, length=0)

    _fields_ = [
        (pint.uint8_t, 'Separator'),
        (pint.uint16_t, 'Left'),
        (pint.uint16_t, 'Top'),
        (pint.uint16_t, 'Width'),
        (pint.uint16_t, 'Height'),
        (_Flags, 'Flags'),
        (optional, 'Color Table')
    ]

class Trailer(pint.uint8_t): pass
    # value == 0x3b

class ImageTableData_Chunk(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'CodeSize'),
        (ptype.type, 'something')
    ]

class ImageData_Chunk(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'Block Size'),
        (lambda s: dyn.block(int(s['Block Size'].li)), 'Data Values')
    ]

class ImageData( parray.type ):
    length = 1
    _object_ = ImageData_Chunk
    def isTerminator(self, v):
        if int(v['Block Size']) == 0:
            return True
        return False

class File(pstruct.type):
    _fields_ = [
        (Header, 'header'),
        (LogicalScreenDescriptor, 'screen'),
        (ImageDescriptor, 'image'),
        (ImageData, 'data')
    ]

if __name__ == '__main__':
    import ptypes,gif
    reload(gif)
    ptypes.setsource( ptypes.provider.file('./poc.gif') )

    z = gif.File()
    print z.l
