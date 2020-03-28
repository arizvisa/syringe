import sys, logging, array
import six,functools,operator,itertools,types

import ptypes
from ptypes import *

__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

intofdata = lambda data: six.moves.reduce(lambda t, c: t * 256 | c, bytearray(data), 0)
dataofint = lambda integer: ((integer == 0) and b'\0') or (dataofint(integer // 256).lstrip(b'\0') + six.int2byte(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Marker list and table
class Marker(ptype.definition):
    attribute, cache = '__name__', {}
    Table = [
        ('STUFF', b'\xff\x00'),
        ('SOF0', b'\xff\xc0'),
        ('SOF0', b'\xff\xc1'),
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

### Marker types
class MarkerType(pint.enum, pint.uint16_t): pass
MarkerType._values_ = [(name, intofdata(data)) for name, data in Marker.Table]

### Marker definitions
@Marker.define
class SOI(ptype.block): length = 0

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

@Marker.define
class DHT(parray.block):
    type = b'\xff\xc4'

    class Table(pstruct.type):
        class ClassAndDestination(pbinary.struct):
            _fields_ = [
                (4, 'class'),
                (4, 'destination'),
            ]

        def __symbols(self):
            return ptype.block
            # FIXME: this needs to be calculated correctly somehow, but i can't find the docs for it
            #return dyn.block(six.moves.reduce(lambda t, c: t + c, map(ord, self['count'].li.serialize())))

        _fields_ = [
            (ClassAndDestination, 'table'),
            (dyn.block(16), 'count'),
            (__symbols, 'symbols')
        ]

        def dump(self, indent=''):
            # XXX: this code sucks
            def consume(iterable, count):
                return [iterable.next() for index in six.moves.range(count)]
            F = functools.partial(consume, symbols)

            symbols = iter(bytearray(self['symbols'].serialize()))
            counts = bytearray(self['count'].serialize())
            codes = [ consume(symbols, count) for count in counts ]

            res = [ 'codes of length[{:d}] bits ({:d} total): {:s}'.format(index, len(code), utils.hexdump(''.join(code))) for ((index, code), count) in zip(enumerate(codes), counts) ]
            return '\n'.join(indent + row for row in res)

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
class COM(ptype.block): pass

@Marker.define
class EOI(ptype.block): length = 0

### Stream decoders
class StreamMarker(pstruct.type):
    Type, Table = MarkerType, Marker

    def __Type(self):
        return self.Type

    def __Value(self):
        return self.Table.withdefault(self['Type'].li.str()) if getattr(self, 'Table', None) else ptype.block

    def __Extra(self):
        fields = ['Type', 'Value']
        return dyn.block(self.blocksize() - sum(self[fld].li.size() for fld in fields))

    _fields_ = [
        (__Type, 'Type'),
        (__Value, 'Value'),
        (__Extra, 'Extra'),
    ]

class DecodedStream(parray.block):
    _marker_ = StreamMarker
    def __init__(self, **attrs):
        super(DecodedStream, self).__init__(**attrs)

        # Make a copy of our bounds as we'll use this to bound each element of our array
        self.__bounds__ = getattr(self, '__bounds__', [])[:]

    def _object_(self):
        bounds = self.__bounds__[len(self.value)]

        # First figure out if we're a delimited marker
        t = dyn.clone(self._marker_.Type, length=0) if bounds < 0 else self._marker_.Type

        # Using the bounds, construct a new marker using it as the blocksize
        Fsize = lambda self, cb=abs(bounds): cb
        return dyn.clone(self._marker_, Type=t, blocksize=Fsize)

    def blocksize(self):
        return sum(self.__bounds__)

class Stream(ptype.encoded_t):
    _object_ = DecodedStream

    def __init__(self, **attrs):
        self.__bounds__ = bounds = []

        # Tie our bounds attribute to the object used for each element
        attrs.setdefault('_object_', dyn.clone(self._object_, __bounds__=bounds))
        super(Stream, self).__init__(**attrs)

    # Copy from ptype.encoded_t so that it looks like the same interface
    def decode(self, object, **attrs):
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'decode')
        data, result = b'', []

        # decode stream into its components
        source = array.array('B', object.serialize())
        iterable = iter(source)
        try:
            while True:
                m = next(iterable)
                if m == 0xff:
                    n = next(iterable)
                    if n == 0x00:
                        data += b'\xff'
                        continue
                    result.append(data)
                    result.append(six.int2byte(m) + six.int2byte(n))
                    data = b''
                    continue
                data += six.int2byte(m)

        except StopIteration:
            result.append(data)

        ## if we found extra data before a marker, then prefix our results
        ## with a dummy marker so that we can add it to our list
        if len(result[0]) > 0:
            result.insert(0, b'')
        else:
            result.pop(0)

        ## pair up each marker with its data
        iterable = __izip_longest__(*[iter(result)] * 2)

        ## figure out the bounds of each element. If the marker is empty, then
        ## this element is just data and we'll use a negative length to mark it
        bounds = []
        for marker, data in iterable:
            size = len(marker) + len(data)
            bounds.append(+size if marker else -size)

        self.__bounds__[:] = bounds
        return super(Stream, self).decode(object)

if __name__ == '__main__':
    blah = z[3]['data'].copy()
    #source = array.array('B', blah.serialize())

    x = Stream(source=ptypes.prov.string(blah.serialize()), blocksize=lambda :blah.size()).l
    y = x.decode()
    for x in y: print(x['type'])
    print(y[9])
    for n in y:
        print(n['type'])
