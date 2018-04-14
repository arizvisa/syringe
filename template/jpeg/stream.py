import logging, array
import functools,operator,itertools

import ptypes
from ptypes import *

intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, data), 0)
dataofint = lambda integer: ((integer == 0) and '\x00') or (dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Marker list and table
class Marker(ptype.definition):
    attribute, cache = '__name__', {}
    Table = [
        ('STUFF', '\xff\x00'),
        ('SOF0', '\xff\xc0'),
        ('SOF0', '\xff\xc1'),
        ('SOF2', '\xff\xc2'),
        ('SOF3', '\xff\xc3'),
        ('DHT', '\xff\xc4'),
        ('SOF5', '\xff\xc5'),
        ('SOF6', '\xff\xc6'),
        ('SOF7', '\xff\xc7'),
        ('JPG', '\xff\xc8'),
        ('SOF9', '\xff\xc9'),
        ('SOF10', '\xff\xca'),
        ('SOF11', '\xff\xcb'),
        ('DAC', '\xff\xcc'),
        ('SOF13', '\xff\xcd'),
        ('SOF14', '\xff\xce'),
        ('SOF15', '\xff\xcf'),
        ('RST0', '\xff\xd0'),
        ('RST1', '\xff\xd1'),
        ('RST2', '\xff\xd2'),
        ('RST3', '\xff\xd3'),
        ('RST4', '\xff\xd4'),
        ('RST5', '\xff\xd5'),
        ('RST6', '\xff\xd6'),
        ('RST7', '\xff\xd7'),
        ('SOI', '\xff\xd8'),
        ('EOI', '\xff\xd9'),
        ('SOS', '\xff\xda'),
        ('DQT', '\xff\xdb'),
        ('DNL', '\xff\xdc'),
        ('DRI', '\xff\xdd'),
        ('DHP', '\xff\xde'),
        ('EXP', '\xff\xdf'),
        ('APP0', '\xff\xe0'),
        ('APP1', '\xff\xe1'),
        ('APP2', '\xff\xe2'),
        ('APP3', '\xff\xe3'),
        ('APP4', '\xff\xe4'),
        ('APP5', '\xff\xe5'),
        ('APP6', '\xff\xe6'),
        ('APP7', '\xff\xe7'),
        ('APP8', '\xff\xe8'),
        ('APP9', '\xff\xe9'),
        ('APP10', '\xff\xea'),
        ('APP11', '\xff\xeb'),
        ('APP12', '\xff\xec'),
        ('APP13', '\xff\xed'),
        ('APP14', '\xff\xee'),
        ('APP15', '\xff\xef'),
        ('JPG0', '\xff\xf0'),
        ('JPG1', '\xff\xf1'),
        ('JPG2', '\xff\xf2'),
        ('JPG3', '\xff\xf3'),
        ('JPG4', '\xff\xf4'),
        ('JPG5', '\xff\xf5'),
        ('JPG6', '\xff\xf6'),
        ('SOF48', '\xff\xf7'),
        ('LSE', '\xff\xf8'),
        ('JPG9', '\xff\xf9'),
        ('JPG10', '\xff\xfa'),
        ('JPG11', '\xff\xfb'),
        ('JPG12', '\xff\xfc'),
        ('JPG13', '\xff\xfd'),
        ('COM', '\xff\xfe'),
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
        (lambda self: dyn.array( SOF.component, self['number of components'].li.int()), 'components')
    ]

@Marker.define   # XXX
class DQT(parray.block):
    type = '\xff\xdb'
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
    type = '\xff\xc4'

    class Table(pstruct.type):
        class ClassAndDestination(pbinary.struct):
            _fields_ = [
                (4, 'class'),
                (4, 'destination'),
            ]
        def __symbols(self):
            return ptype.block
            # FIXME: this needs to be calculated correctly somehow, but i can't find the docs for it
            #return dyn.block(reduce(lambda x,y:x+y, [ord(x) for x in self['count'].li.serialize()]))
        _fields_ = [
            (ClassAndDestination, 'table'),
            (dyn.block(16), 'count'),
            (__symbols, 'symbols')
        ]

        def dumpValue(self, indent=''):
            # XXX: this code sucks
            symbols = iter(self['symbols'].value)
            def consume(iterable, count):
                return [iterable.next() for x in xrange(count)]

            res = [ord(x) for x in self['count'].value]
            counts = res
            res = [consume(symbols, x) for x in res]
            codes = res

            res = [ indent+'codes of length[%d] bits (%d total): %s'% (index, len(code), utils.hexdump(''.join(code))) for ((index, code), count) in zip(enumerate(codes), counts)]
            return '\n'.join(res)

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

@Marker.define
class COM(ptype.block): pass

@Marker.define
class EOI(ptype.block): length = 0

### Stream decoders
class MarkerStream(pstruct.type):
    Type, Table = MarkerType, Marker

    def __Value(self):
        res = self.Table.lookup(self['Type'].li.str(), self.Table.default)
        return res

    def __Extra(self):
        cb = self['Type'].li.size() + self['Value'].li.size()
        return dyn.block(self.blocksize() - cb)

    _fields_ = [
        (lambda self: self.Type, 'Type'),
        (__Value, 'Value'),
        (__Extra, 'Extra'),
    ]

class DecodedStream(parray.terminated):
    _object_ = MarkerStream
    def isTerminator(self, value):
        return value['Type'].int() == 0xffd9

class Stream(ptype.block):
    _object_ = DecodedStream

    # Copy from ptype.encoded_t so that it looks like the same interface
    d = property(fget=lambda self,**attrs: self.decode(**attrs))
    deref = lambda self,**attrs: self.decode(**attrs)
    dereference = deref

    def decode(self):
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'decode')
        data, result = '', []

        # decode stream into its components
        source = array.array('B', self.serialize())
        iterable = iter(source)
        try:
            while True:
                m = next(iterable)
                if m == 0xff:
                    n = next(iterable)
                    if n == 0x00:
                        data += '\xff'
                        continue
                    result.append(data)
                    result.append(chr(m)+chr(n))
                    data = ''
                    continue
                data += chr(m)
                
        except StopIteration:
            result.append(data)
        result = result[1:]

        ## build decoded object
        stream = self.new(self._object_, offset=self.getoffset(), source=self.__source__, value=[])
        for m, data in map(None, *(iter(result),)*2):
            edata = m + (data or '')
            res = stream._object_(blocksize=lambda cb=len(edata):cb)
            stream.append(res.load(offset=0, source=ptypes.prov.string(edata)))
        return stream

if __name__ == '__main__':
    blah = z[3]['data'].copy()
    #source = array.array('B', blah.serialize())
    
    x = Stream(source=ptypes.prov.string(blah.serialize()), blocksize=lambda :blah.size()).l
    y = x.decode()
    for x in y: print x['type']
    print y[9]
    for n in y:
        print n['type']
