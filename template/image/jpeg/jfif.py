import logging
import functools,operator,itertools,six

import ptypes
from ptypes import *

from . import stream as jpegstream
from .stream import intofdata, dataofint

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### JFIF Markers
class Marker(jpegstream.Marker):
    attribute, cache, table = '__name__', {}, [
        ('SOF0', b'\xff\xc0'),
        ('SOF1', b'\xff\xc1'),
        ('SOF2', b'\xff\xc2'),
        ('SOF3', b'\xff\xc3'),
        ('DHT', b'\xff\xc4'),
        ('SOF5', b'\xff\xc5'),
        ('SOF6', b'\xff\xc6'),
        ('SOF7', b'\xff\xc7'),
        ('JPG', b'\xff\xc8'),
        ('SOF9', b'\xff\xc9'),
        ('SOF10', b'\xff\xca'),
        ('SOF11', b'\xff\xcb'),
        ('DAC', b'\xff\xcc'),
        ('SOF13', b'\xff\xcd'),
        ('SOF14', b'\xff\xce'),
        ('SOF15', b'\xff\xcf'),
        ('RST0', b'\xff\xd0'),
        ('RST1', b'\xff\xd1'),
        ('RST2', b'\xff\xd2'),
        ('RST3', b'\xff\xd3'),
        ('RST4', b'\xff\xd4'),
        ('RST5', b'\xff\xd5'),
        ('RST6', b'\xff\xd6'),
        ('RST7', b'\xff\xd7'),
        ('SOI', b'\xff\xd8'),
        ('EOI', b'\xff\xd9'),
        ('SOS', b'\xff\xda'),
        ('DQT', b'\xff\xdb'),
        ('DNL', b'\xff\xdc'),
        ('DRI', b'\xff\xdd'),
        ('DHP', b'\xff\xde'),
        ('EXP', b'\xff\xdf'),
        ('APP0', b'\xff\xe0'),
        ('APP1', b'\xff\xe1'),
        ('APP2', b'\xff\xe2'),
        ('APP3', b'\xff\xe3'),
        ('APP4', b'\xff\xe4'),
        ('APP5', b'\xff\xe5'),
        ('APP6', b'\xff\xe6'),
        ('APP7', b'\xff\xe7'),
        ('APP8', b'\xff\xe8'),
        ('APP9', b'\xff\xe9'),
        ('APP10', b'\xff\xea'),
        ('APP11', b'\xff\xeb'),
        ('APP12', b'\xff\xec'),
        ('APP13', b'\xff\xed'),
        ('APP14', b'\xff\xee'),
        ('APP15', b'\xff\xef'),
        ('JPG0', b'\xff\xf0'),
        ('JPG1', b'\xff\xf1'),
        ('JPG2', b'\xff\xf2'),
        ('JPG3', b'\xff\xf3'),
        ('JPG4', b'\xff\xf4'),
        ('JPG5', b'\xff\xf5'),
        ('JPG6', b'\xff\xf6'),
        ('SOF48', b'\xff\xf7'),
        ('LSE', b'\xff\xf8'),
        ('JPG9', b'\xff\xf9'),
        ('JPG10', b'\xff\xfa'),
        ('JPG11', b'\xff\xfb'),
        ('JPG12', b'\xff\xfc'),
        ('JPG13', b'\xff\xfd'),
        ('COM', b'\xff\xfe'),
    ]

class MarkerType(jpegstream.MarkerType): pass
MarkerType._values_ = [(name, intofdata(data)) for name, data in Marker.table]

class StreamMarker(jpegstream.StreamMarker):
    Type, Table = MarkerType, Marker

    def __Type(self):
        return self.Type

    def __Value(self):
        if self.blocksize() <= sum(self[fld].li.size() for fld in ['Type', 'Lp']):
            return ptype.undefined

        t, res = self.Table.withdefault(self['Type'].li.str()), self['Lp'].li
        if issubclass(t, ptype.block):
            return dyn.clone(t, length=res.int() - res.size())
        return dyn.clone(t, blocksize=lambda self, cb=res.int() - res.size(): cb)

    def __Extra(self):
        fields = ['Type', 'Lp', 'Value']
        return dyn.block(self.blocksize() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (__Type, 'Type'),
        (lambda self: pint.uint_t if self.blocksize() < 4 else pint.uint16_t, 'Lp'),
        (__Value, 'Value'),
        (__Extra, 'Extra'),
    ]

### Marker definitions
@Marker.define
class SOI(ptype.block):
    pass

@Marker.define
class SOF0(pstruct.type):
    class component(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'id'),
            (dyn.clone(pbinary.struct, _fields_=[(4,'H'), (4,'V')]), 'sampling factors'),
            (pint.uint8_t, 'quantization table number')
        ]

    _fields_ = [
        (pint.uint8_t, 'precision'),
        (pint.uint16_t, 'height'),
        (pint.uint16_t, 'width'),
        (pint.uint8_t, 'number of components'),
        (lambda self: dyn.array( self.component, self['number of components'].li.int()), 'components')
    ]

@Marker.define   # XXX
class DQT(parray.block):
    type = b'\xff\xdb'
    class Table(pstruct.type):
        class DQTPrecisionAndIndex(pbinary.struct):
            _fields_ = [
                (4, 'precision'),
                (4, 'index')
            ]
        _fields_ = [
            (DQTPrecisionAndIndex, 'precision/index'),
            (dyn.block(64), 'value')
        ]

    _object_ = Table

@Marker.define   # XXX
class DHT(parray.block):
    type = b'\xff\xc4'

    class Table(pstruct.type):
        class _Th(pbinary.struct):
            _fields_ = [
                (4, 'Tc'),
                (4, 'Td'),
            ]

        class _Li(parray.type):
            length, _object_ = 16, pint.uint8_t

        class _Vij(parray.type):
            length = 16

        def __Vij(self):
            count = [item.int() for item in self['Li'].li]
            def _object_(self, count=count):
                return dyn.array(pint.uint8_t, count[len(self.value)])
            return dyn.clone(self._Vij, _object_=_object_)

        _fields_ = [
            (_Th, 'Th'),
            (_Li, 'Li'),
            (__Vij, 'Vij')
        ]

        def dump(self, indent=''):
            res = [ "code-length ({:#x}) bits ({:d}): {:s}".format(index, len(code), ' '.join(map("{:02x}".format, bytearray(code.serialize())))) for ((index, code), count) in zip(enumerate(self['Vij']), self['Li']) ]
            return '\n'.join(indent + row for row in [ "[Table {!s} : Tc={:d} Td={:d}]".format(self.name(), self['Th']['Tc'], self['Th']['Td']) ] + res)

    _object_ = Table

@Marker.define
class SOS(pstruct.type):
    class component(pbinary.struct):
        _fields_ = [
            (8, 'id'),
            (4, 'DC'),
            (4, 'AC')
        ]

    _fields_ = [
        (pint.uint8_t, 'number of components'),
        (lambda self: dyn.array(SOS.component, self['number of components'].li.int()), 'component'),
        (pint.uint8_t, 'start of spectral selection'),
        (pint.uint8_t, 'end of spectral selection'),
        (dyn.clone(pbinary.struct, _fields_=[(4,'high'),(4,'low')]), 'successive approximation')
    ]

#@Marker.define
class APP0(pstruct.type):
    class _Format(pint.enum, pint.uint8_t):
        _values_ = [
            ('JPEG format', 10),
            ('1 byte per pixel palettized', 11),
            ('3 byte per pixel RGB format', 13),
        ]
    _fields_ = [
        (pint.uint16_t, 'Length'),
        (dyn.clone(pstr.string, length=5), 'Identifier'),
        (_Format, 'Format'),
        (ptype.undefined, 'Thumbnail'),
    ]

@Marker.define
class COM(ptype.block):
    pass

@Marker.define
class EOI(ptype.block):
    pass

### JFIF Structures
class extension_type(ptype.definition):
    cache = {}

@extension_type.define
class X10(pstruct.type):
    type = 0
    class _C(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'Y'),
            (pint.uint8_t, 'Cb'),
            (pint.uint8_t, 'Cr'),
        ]
    _fields_ = [
        (pint.uint8_t, 'Nf'),
        (lambda self: dyn.array(_C, self['Nf'].li.int()), 'C'),
    ]

class RGB(pstruct.type):
    _fields_ = [(pint.uint8_t, item) for item in 'RGB']

@extension_type.define
class X11(pstruct.type):
    type = 1
    _fields_ = [
        (pint.uint8_t, 'HthumbnailB'),
        (pint.uint8_t, 'VthumbnailB'),
        (dyn.array(RGB, 0x100), 'Palette'),
        (lambda self: dyn.block(self['HthumbnailB'].li.int() * self['VthumbnailB'].li.int()), 'm'),
    ]

@extension_type.define
class X13(pstruct.type):
    type = 3
    _fields_ = [
        (pint.uint8_t, 'HthumbnailC'),
        (pint.uint8_t, 'VthumbnailC'),
        (lambda self: dyn.block(self['HthumbnailC'].li.int() * self['VthumbnailC'].li.int()), 'n'),
    ]

class APP0(pstruct.type):
    def __extension_data(self):
        res = self['extension_code'].li
        return extension_type.lookup(res.int())

    _fields_ = [
        (dyn.block(5), 'identifier'),
        (pint.uint8_t, 'extension_code'),
        (__extension_data, 'extension_data'),
    ]

@Marker.define
class APP0(pstruct.type):
    _fields_ = [
        (dyn.block(5), 'identifier'),
        (pint.uint16_t, 'version'),
        (pint.uint8_t, 'units'),
        (pint.uint16_t, 'Hdensity'),
        (pint.uint16_t, 'Vdensity'),
        (lambda self: ptype.undefined if self.blocksize() < 10 else pint.uint8_t, 'HthumbnailA'),
        (lambda self: ptype.undefined if self.blocksize() < 11 else pint.uint8_t, 'VthumbnailA'),
        (lambda self: ptype.undefined if self.blocksize() < 12 else dyn.array(RGB, self['HthumbnailA'].li.int() * self['VthumbnailA'].li.int()), 'k'),
    ]

class File(jpegstream.Stream):
    class _object_(jpegstream.DecodedStream):
        _marker_ = StreamMarker

    def _value_(self):
        return dyn.clone(ptype.block, length=self.source.size())

if __name__ == '__main__':
    pass
