import ptypes
from ptypes import *
ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class int8(pint.int8_t): pass
class uint8(pint.uint8_t): pass
class Fixed(pint.uint32_t): pass
class Integer(pint.uint16_t): pass
class Long(pint.uint32_t): pass
class Mode(pint.uint16_t): pass
class Pattern(pint.uint64_t): pass
class Point(pint.uint32_t): pass

class Rect(pstruct.type):
    _fields_ = [
        (Integer, 'top'),
        (Integer, 'left'),
        (Integer, 'bottom'),
        (Integer, 'right'),
    ]

class picSize(pstruct.type):
    _fields_ = [
        (Integer, 'size'),
        (Integer, 'top'),
        (Integer, 'left'),
        (Integer, 'bottom'),
        (Integer, 'right'),
    ]

class picFrame(pstruct.type):
    _fields_ = [
        (Integer, 'version'),
        (Integer, 'picture'),
        (Integer, 'opcode'),
        (Long, 'size'),
        (Long, 'hres'),
        (Long, 'vres'),
        (Integer, 'x1'),
        (Integer, 'y1'),
        (Integer, 'x2'),
        (Integer, 'y2'),
        (Long, 'reserved'),
    ]

class PixMap(pstruct.type):
    _fields_ = [
        (Integer, 'rowBytes'),
        (Rect, 'bounds'),
        (Integer, 'pmVersion'),
        (Integer, 'packType'),
        (Long, 'packSize'),
        (Fixed, 'hRes'),
        (Fixed, 'vRes'),
        (Integer, 'pixelType'),
        (Integer, 'pixelSize'),
        (Integer, 'cmpCount'),
        (Integer, 'cmpSize'),
        (Long, 'planeByte'),
        (Long, 'pmTable'),
        (Long, 'pmReserved'),
    ]

class Rgn(pstruct.type):
    def __data(self):
        s = int(self['size'].li)
        return dyn.block(s - 10)

    _fields_ = [
        (Integer, 'size'),
        (Rect, 'region'),
        (__data, 'data'),
    ]

    def blocksize(self):
        return int(self['size'].li)

class Opcode_v1(pint.uint8_t): pass
class Opcode_v2(pint.uint16_t): pass

class Int16Data(pstruct.type):
    _fields_ = [
        (Integer, 'size'),
        (lambda s: dyn.block(int(s['size'].li)), 'data')
    ]

class RGBColor(pstruct.type):
    _fields_ = [
        (Integer, 'red'),
        (Integer, 'green'),
        (Integer, 'blue'),
    ]

class ColorSpec(pstruct.type):
    _fields_ = [
        (Integer, 'value'),
        (RGBColor, 'rgb'),
    ]

class ColorTable(pstruct.type):
    _fields_ = [
        (Long, 'ctSeed'),
        (Integer, 'ctFlags'),
        (Integer, 'ctSize'),
        (lambda s: dyn.array(ColorSpec, int(s['ctSize'].li)), 'ctTable'),
    ]

class PixPatNonDithered(pstruct.type):
    def __pixData(self):
        self['pixMap'].l
        packtype = int(self['pixMap']['packType'])
        rowbytes = int(self['pixMap']['rowBytes'])
        height = int(self['pixMap']['bounds']['bottom']) - int(self['pixMap']['bounds']['top'])

        if packtype == 1 or rowbytes < 8:
            result = dyn.block(rowbytes * height)
        elif packtype == 2:
            result = dyn.block(math.ceil(rowbytes * height * 3 / 4 + 0.5))
        elif packtype == 3:
            result = dyn.array(self.Pack3, height)
        else:
            raise NotImplementedError(packtype)
        return dyn.clone(result, rowbytes=rowbytes)

    _fields_ = [
        (PixMap, 'PixMap'),
        (ColorTable, 'ColorTable'),
        (__pixData, 'PixData'),
    ]

class PixPat(pstruct.type):
    def __data(self):
        t = int(self['patType'].li)
        if t == 2:
            return RGBColor
        elif t == 1:
            return PixPatNonDithered
        raise StopIteration('Unexpected pattern type %d'% t)

    _fields_ = [
        (Integer, 'patType'),
        (dyn.array(int8, 8), 'pat1Data'),
        (__data, 'data'),
    ]
