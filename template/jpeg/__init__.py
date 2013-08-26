import ptypes
from ptypes import *
from ptypes import utils

ptypes.setbyteorder(ptypes.bigendian)

def CBinary(args):
    class _CBinary(pbinary.struct):
        _fields_ = args[:]
    return _CBinary

if False:
    def jpegerator(iterable):
        iterable=iter(iterable)
        while True:
            x = iterable.next()
            if x == '\xff':
                x = iterable.next()
                if x == '\x00':
                    yield x
                    continue
                if x == '\xff':
                    yield '\xff'
                    continue
                yield '\xff'

            # FIXME: check to see if we need to do anything else with \xff's,
            # because this hack doesn't feel right.
            yield x

    class header(pstruct.type):
        marker = ''

        _fields_ = [
            (pint.uint16_t, 'marker'),
            (pint.uint16_t, 'length'),
            (lambda self: dyn.block(self['length'].l - 2), 'data'),
        ]

        @classmethod
        def lookupByMarker(cls, marker):
            res = globals().values()
            res = [ x for x in res if type(x) is type ]
            res = [ x for x in res if issubclass(x, header) and x is not cls ]
            for x in res:
                if x.marker == marker:
                    return x
            if marker[0] == '\xff':
                return unknown
            raise KeyError(marker)

        def deserialize(self, iterable):
            iterable = jpegerator(iterable)
            super(header, self).deserialize(iterable)

### markers
class marker(ptype.definition):
    cache = {}
    unknown = ptype.block

class markerlength(ptype.definition):
    cache = {}
    unknown = ptype.block

### header chunks
class header(pstruct.type):
    def __data(self):
        m = self['marker'].l.serialize()
        try:
            return marker.lookup(m)
        except KeyError:
            pass
        return dyn.clone(headerlength, type=m)

    _fields_ = [
        (pint.uint16_t, 'marker'),
        (__data, 'data'),
    ]

class headerlength(pstruct.type):
    def __data(self):
        bs = self['length'].l.int() - 2
        t = self.type
        return dyn.clone(coded, _object_=markerlength.get(t, length=bs), blocksize=lambda s:bs)

    _fields_ = [
        (pint.uint16_t, 'length'),
        (__data, 'data'),
    ]

class coded(ptype.encoded_t):
    _object_ = None
    def decode(self, **attr):
        name = '*%s'% self.name()
        s = self.serialize()
        return self.newelement(self._object_, name, 0, source=provider.string(s))
    def encode(self, object):
        raise NotImplementedError

### entire file
class File(parray.terminated):
    _object_ = header
    def isTerminator(self, value):
        return type(value) is SOS

### list of headers
@markerlength.define
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
        (lambda self: dyn.block( 3 * (self['Xthumbnail'].l.int()*self['Ythumbnail'].l.int())), 'RGB')
    ]

@marker.define
class SOI(ptype.empty):
    type = '\xff\xd8'

@marker.define
class EOI(ptype.empty):
    type = '\xff\xd9'

@markerlength.define
class SOF(pstruct.type):
    type = '\xff\xc0'

    class component(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'id'),
            (CBinary([(4,'H'), (4,'V')]), 'sampling factors'),
            (pint.uint8_t, 'quantization table number')
        ]

    _fields_ = [
        (pint.uint8_t, 'precision'),
        (pint.uint16_t, 'height'),
        (pint.uint16_t, 'width'),
        (pint.uint8_t, 'number of components'),
        (lambda self: dyn.array( SOF.component, self['number of components'].l), 'components')
    ]

#@markerlength.define   # XXX
class APP12(ptype.block):
    type = '\xff\xec'

#@markerlength.define   # XXX
class APP14(ptype.block):
    type = '\xff\xee'

class DQTPrecisionAndIndex(pbinary.struct):
    _fields_ = [
        (4, 'precision'),
        (4, 'index')
    ]

class DQTTable(pstruct.type):
    _fields_ = [
        (DQTPrecisionAndIndex, 'precision/index'),
        (dyn.block(64), 'value')
    ]

    def dumpValue(self):
        return utils.hexdump(self['value'].value, length=8)

    def __repr__(self):
        res = ['[%08x] %s %s'% (self.getoffset(k), k, v) for k,v in self.items()]
        res = []
        res.append('[%x<0..3>] precision: %d'% (self.getoffset('precision/index'), self['precision/index']['precision']))
        res.append('[%x<4..7>] index: %d'% (self.getoffset('precision/index'), self['precision/index']['index']))
        res.append('[%x] value ->'% (self.getoffset('value')))
        res.append( self.dumpValue() )
        return '%s\n%s\n'% (repr(type(self)), '\n'.join(res))

class DQTTableArray(parray.terminated):
    _object_ = DQTTable
    def isTerminator(self, value):
        return False

#@markerlength.define   # XXX
class DQT(pstruct.type):
    type = '\xff\xdb'
    _fields_ = [
        (lambda self: dyn.clone(DQTTableArray, blocksize=lambda:self['length'].l-2), 'table')    # FIXME: get this shit working too
    ]

class HuffmanTable(pstruct.type):
    _fields_ = [
        (CBinary([(4, 'class'), (4, 'destination')]), 'table'),
        (dyn.block(16), 'count'),
        (lambda self: dyn.block(reduce(lambda x,y:x+y, [ord(x) for x in self['count'].l.serialize()])), 'symbols') # FIXME: this needs to be calculated correctly somehow, but i can't find the docs for it
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

    def __repr__(self):
        res = ['[%08x] %s %s'% (self.getOffset(k), k, v) for k,v in self.items()]
        res = []
        res.append('[%08x<0..3>] [table][class]: %d'% (self.getOffset('table'), self['table']['class']))
        res.append('[%08x<4..7>] [table][destination]: %d'% (self.getOffset('table'), self['table']['destination']))
        res.append('[%08x] [count]: %s'% (self.getOffset('count'), repr(self['count'])))
        res.append('[%08x] [symbols]: %s'% (self.getOffset('symbols'), repr(self['symbols'])))
        res.append('value ->\n%s'% (self.dumpValue('    ')))
        return '%s\n%s\n'% (repr(type(self)), '\n'.join(res))

class HuffmanTableArray(parray.terminated):
    _object_ = HuffmanTable

#@markerlength.define   # XXX
class DHT(pstruct.type):
    type = '\xff\xc4'
    _fields_ = [
        (lambda self: dyn.clone(HuffmanTableArray,blocksize=lambda:self['length'].l-2), 'table')
    ]

@markerlength.define
class SOS(pstruct.type):
    type = '\xff\xda'

    class component(pbinary.struct):
        _fields_ = [
            (8, 'id'),
            (4, 'DC'),
            (4, 'AC')
        ]

    _fields_ = [
        (pint.uint8_t, 'number of components'),
        (lambda self: dyn.array(SOS.component, self['number of components'].l), 'component'),
        (pint.uint8_t, 'start of spectral selection'),
        (pint.uint8_t, 'end of spectral selection'),
        (CBinary([(4,'high'),(4,'low')]), 'successive approximation')
    ]

@markerlength.define
class Comment(pstruct.type):
    type = '\xff\xfe'
    _fields_ = [
        (lambda self: dyn.block( self['length'] - 2 ), 'data')
    ]

if False:
    class Jpeg(parray.type):
        length = 0

        def deserialize(self, string):
            ## yes, i know i'm doing this clumsily
            self.value = []
            ofs = 0
            self._fields_ = []

            while string:
                x = header.lookupByMarker(string[:2])()
                x.deserialize(string)
                x.setoffset(ofs)
                self.append(x)

                ofs += x.size()
                string = string[x.size():]
                if type(x) is SOS:
                    break

            iterable = iter(string)
            count = 0
            for count,v in enumerate(iterable):
                count += 1
                if v == '\xff':
                    v = iterable.next()
                    if v == '\xda':
                        break

            sosdata = dyn.block(count, name='SCANDATA')()
            sosdata.deserialize(string[:count])
            sosdata.setoffset(ofs)
            self.append(sosdata)

            string = string[count:]
            ofs += count

            x = header.lookupByMarker(string)()
            x.deserialize(string)
            x.setoffset(ofs)
            self.append(x)

if False:
    class File(Jpeg): pass

if False:
    def getFileContents(path):
        f = file(path, 'rb')
        res = f.read()
        f.close()
        return res

    def writeFileContents(path, value):
        f = file(path, 'wb')
        f.write(value)
        f.close()

if __name__ == '__main__' and False:
    #input = getFileContents('Q100-2.JPG')
    input = getFileContents('huff_simple0.jpg')
    input = str(input.replace('\xff\x00', '\xff'))
    jpegfile = Jpeg()
    jpegfile.deserialize(input)
    lookup = dict([(type(x).__name__, x) for x in jpegfile])

    print jpegfile[0]
    print jpegfile[1]

#    print '\n'.join([repr(x) for x in jpegfile])
#    dqt = lookup['DQT']['table']
#    dht = lookup['DHT']['table']
#    sosdata = lookup['SCANDATA']
#    print repr(dqt)
#    print repr(dht)
#    print repr(sosdata)
#    print '\n'.join([repr(x) for x in dht])
#    print '\n'.join([repr(x) for x in dqt])

    ### load_quant_table
    zigzag = [
        0, 1, 5, 6,14,15,27,28,
        2, 4, 7,13,16,26,29,42,
        3, 8,12,17,25,30,41,43,
        9,11,18,24,31,40,44,53,
       10,19,23,32,39,45,52,54,
       20,22,33,38,46,51,55,60,
       21,34,37,47,50,56,59,61,
       35,36,48,49,57,58,62,63
    ]

    scalefactor = [
        1.0, 1.387039845, 1.306562965, 1.175875602,
        1.0, 0.785694958, 0.541196100, 0.275899379
    ]

    self = lookup['DQT']['table'][0]
    quantizationTable = [ord(x) for x in self['value'].serialize()]
    res = []
    table = iter(quantizationTable)
    for y in range(8):
        for x in range(8):
            res.append( table.next() * scalefactor[y] * scalefactor[x] )

    scaledQuantizationTable = res

    ### decode_huffman ->
    ###     decode AC coefficient
    ###     decode DC coefficient

    ## process dht table
    self = lookup['DHT']['table'][3]
    print repr(self)
    
    ### process scan data
    self = lookup['SOS']
    print repr(self)
    print self['component'][0]

    self = lookup['SOF']
    self = lookup['SOS']

if __name__ == '__main__':
    import sys
    import ptypes,jpeg
    ptypes.setsource( ptypes.file(sys.argv[1]) )

    z = jpeg.File()
    z = z.l
