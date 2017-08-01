import logging
import functools,operator,itertools

import ptypes, jpeg.stream
from ptypes import *

intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, data), 0)
dataofint = lambda integer: ((integer == 0) and '\x00') or (dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### JFIF Markers
class Marker(jpeg.stream.Marker):
    attribute, cache = '__name__', {}
    Table = [
        # FIXME: Figure out which markers are JPEG-stream specific and
        #        which are JFIF-specific
    ]

class MarkerType(jpeg.stream.MarkerType): pass
MarkerType._values_ = [(name, intofdata(data)) for name, data in Marker.Table]

class MarkerStream(jpeg.stream.MarkerStream):
    Type, Table = MarkerType, Marker

### JFIF Structures
class JFIF(pstruct.type):
    type = '\xff\xe0'
    _fields_ = [
        (dyn.block(5), 'identiier'),
        (pint.uint16_t, 'version'),
        (pint.uint8_t, 'units'),
        (pint.uint16_t, 'Xdensity'),
        (pint.uint16_t, 'Ydensity'),
        (pint.uint8_t, 'Xthumbnail'),
        (pint.uint8_t, 'Ythumbnail'),
        (lambda self: dyn.block( 3 * (self['Xthumbnail'].li.int()*self['Ythumbnail'].li.int())), 'RGB')
    ]

class File(pstruct.type):
    _fields_ = []
    def __init__(self, **attrs):
        raise NotImplementedError

if __name__ == '__main__':
    pass
