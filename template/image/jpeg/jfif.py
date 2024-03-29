import ptypes, operator

from ptypes import *
from . import codestream, intofdata, dataofint

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### JFIF Markers
class Marker(codestream.Marker):
    cache, table = {}, [
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

class MarkerType(codestream.MarkerType):
    _values_ = Marker.table

class StreamData(codestream.StreamData):
    _fields_ = codestream.StreamData._fields_[:1] + [
        (pint.uint_t, 'Lp')
    ] + codestream.StreamData._fields_[1:]

class StreamMarker(codestream.StreamMarker):
    Type, Table = MarkerType, Marker

    def __Type(self):
        return self.Type

    def __Value(self):
        if self.blocksize() <= sum(self[fld].li.size() for fld in ['Type', 'Lp']):
            return ptype.undefined

        t, res = self.Table.withdefault(self['Type'].li.serialize()), self['Lp'].li
        if issubclass(t, ptype.block):
            return dyn.clone(t, length=res.int() - self['Type'].size())
        return dyn.clone(t, blocksize=lambda self, cb=res.int() - self['Type'].size(): cb)

    def __Extra(self):
        fields = ['Type', 'Lp', 'Value']
        t = dyn.block(self.blocksize() - sum(self[fld].li.size() for fld in fields))
        if hasattr(self['Value'], 'EncodedQ') and self['Value'].EncodedQ():
            return dyn.clone(codestream.ByteStuffer, _value_=t)
        return t

    _fields_ = [
        (__Type, 'Type'),
        (lambda self: pint.uint_t if self.blocksize() < 4 else pint.uint16_t, 'Lp'),
        (__Value, 'Value'),
        (__Extra, 'Extra'),
    ]

    def alloc(self, **fields):
        res = super(StreamMarker, self).alloc(**fields)
        return res if operator.contains(fields, 'Lp') else res.set(Lp=res['Value'].size())

### Marker definitions
@Marker.define
class SOI(ptype.block):
    pass

class SOF(pstruct.type):
    class _Cn(pstruct.type):
        class _F(pbinary.struct):
            _fields_ = [
                (4, 'H'),
                (4, 'V'),
            ]
        _fields_ = [
            (pint.uint8_t, 'C'),
            (_F, 'F'),
            (pint.uint8_t, 'Tq')
        ]

    _fields_ = [
        (pint.uint8_t, 'P'),
        (pint.uint16_t, 'Y'),
        (pint.uint16_t, 'X'),
        (pint.uint8_t, 'Nf'),
        (lambda self, Cn=_Cn: dyn.array(Cn, self['Nf'].li.int()), 'Cn')
    ]

    def alloc(self, **fields):
        res = super(SOF, self).alloc(**fields)
        return res if operator.contains(fields, 'Nf') else res.set(Nf=len(res['Cn']))

@Marker.define
class SOF0(SOF): pass
@Marker.define
class SOF1(SOF): pass
@Marker.define
class SOF2(SOF): pass
@Marker.define
class SOF3(SOF): pass
#@Marker.define
#class SOF4(SOF): pass
@Marker.define
class SOF5(SOF): pass
@Marker.define
class SOF6(SOF): pass
@Marker.define
class SOF7(SOF): pass
#@Marker.define
#class SOF8(SOF): pass
@Marker.define
class SOF9(SOF): pass
@Marker.define
class SOF10(SOF): pass
@Marker.define
class SOF11(SOF): pass
#@Marker.define
#class SOF12(SOF): pass
@Marker.define
class SOF13(SOF): pass
@Marker.define
class SOF14(SOF): pass
@Marker.define
class SOF15(SOF): pass

@Marker.define
class DQT(parray.block):
    class Table(pstruct.type):
        class _Y(pbinary.struct):
            _fields_ = [
                (4, 'Pq'),
                (4, 'Tq')
            ]

        class _Qk(parray.type):
            length, _object_ = 64, pint.uint8_t

            def matrix(self):
                iterable = (item.int() for item in self)
                rows = 8 * [iter(iterable)]
                return [ list(item) for item in zip(*rows) ]

        _fields_ = [
            (_Y, 'Y'),
            (_Qk, 'Qk')
        ]

        def repr(self):
            Fprefix = lambda instance, name: "[{:#x}] {:s}{:s}".format(instance.getoffset(), ptypes.utils.repr_instance(instance.classname(), name), " {{{:s}}}".format(','.join(u"{:s}={!r}".format(k, v) for k, v in instance.properties().items())) if instance.properties() else '')

            res = ["{:s} {:s}".format(Fprefix(self['Y'], self['Y'].name()), self['Y'].summary())]
            for index, Mk in enumerate(self['Qk'].matrix()):
                offset = 8 * index
                item = self['Qk'][offset : len(Mk) + offset]
                row = ','.join(map("{:>3d}".format, Mk))
                res.append("{:s} {:s} [{:s}]".format(Fprefix(item, "Qk[{:>2d}:{:<2d}]".format(offset, len(Mk) + offset - 1)), item.__element__(), row))
            return '\n'.join(res)

    _object_ = Table

@Marker.define
class DHT(parray.block):
    class Table(pstruct.type):
        class _Th(pbinary.struct):
            class _Tc(pbinary.enum):
                length, _values_ = 1, [
                    ('DC', 0),
                    ('AC', 1),
                ]
            _fields_ = [
                (3, 'Reserved'),
                (_Tc, 'Tc'),
                (4, 'Td'),
            ]

        class _Li(parray.type):
            length, _object_ = 16, pint.uint8_t

            def summary(self):
                iterable = map("{:+d}".format, (item.int() for item in self))
                return "[ {:s} ]".format(', '.join(iterable))

        class _Vij(parray.type):
            length = 16

            class V(parray.type):
                _object_ = pint.uint8_t

                def summary(self):
                    iterable = map("{:02x}".format, bytearray(self.serialize()))
                    return "symbols: ({:d}) {:s}".format(self.size(), ' '.join(iterable) or 'none')
            _object_ = V

            def repr(self):
                Fprefix = lambda instance, name: "[{:#x}] {:s}{:s}".format(instance.getoffset(), ptypes.utils.repr_instance(instance.classname(), name), " {{{:s}}}".format(','.join(u"{:s}={!r}".format(k, v) for k, v in instance.properties().items())) if instance.properties() else '')

                if len(self) > 1:
                    offset, res = 0, []
                    for index, symbols in enumerate(self):
                        if len(symbols) > 0:
                            iterable = map("{:02x}".format, bytearray(symbols.serialize()))
                            res.append("{:s} symbols of size {:+d}: ({:d}) {:s}".format(Fprefix(symbols, symbols.name()), index, len(symbols), ' '.join(iterable)))
                        offset += len(symbols)
                    return '\n'.join(res)
                return super(DHT.Table._Vij, self).repr()

        def __Vij(self):
            count = [item.int() for item in self['Li'].li]
            def _object_(self, _object_=self._Vij._object_, count=count):
                return dyn.clone(_object_, length=count[len(self.value)])
            return dyn.clone(self._Vij, _object_=_object_)

        _fields_ = [
            (_Th, 'Th'),
            (_Li, 'Li'),
            (__Vij, 'Vij')
        ]

        def alloc(self, **fields):
            res = super(DHT.Table, self).alloc(**fields)
            if operator.contains(fields, 'Li'):
                return res
            res.set(Li=[item.size() for item in res['Vij']]) if isinstance(res['Vij'], parray.type) else res

    _object_ = Table

@Marker.define
class SOS(pstruct.type):
    class _Cs(pbinary.struct):
        _fields_ = [
            (8, 'Cs'),
            (4, 'Td'),
            (4, 'Ta')
        ]

    class _A(pbinary.struct):
        _fields_ = [
            (4, 'Ah'),
            (4, 'Al'),
        ]

    _fields_ = [
        (pint.uint8_t, 'Ns'),
        (lambda self, Cs=_Cs: dyn.array(Cs, self['Ns'].li.int()), 'Csn'),
        (pint.uint8_t, 'Ss'),
        (pint.uint8_t, 'Se'),
        (_A, 'A')
    ]

    def alloc(self, **fields):
        res = super(SOS, self).alloc(**fields)
        return res if operator.contains(fields, 'Ns') else res.set(Ns=len(res['Csn']))

    @classmethod
    def EncodedQ(cls):
        return True

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
class DRI(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'Ri'),
    ]

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

class ImageResourceBlock(pstruct.type):
    class _name(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'length'),
            (lambda self: dyn.clone(pstr.string, length=1 + self['length'].li.int()), 'string'),
        ]

    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'signature'),
        (pint.uint16_t, 'identifier'),
        (_name, 'name'),
        (pint.uint32_t, 'size'),
        (lambda self: dyn.block(self['size'].li.int()), 'data'),
        (dyn.padding(2), 'padding(data)'),
    ]

@Marker.define
class APP13(pstruct.type):
    def __extra(self):
        bs, res = self.blocksize(), sum(self[fld].li.size() for fld in ['identifier', 'resources'])
        return dyn.block(max(0, bs - res))

    def __resources(self):
        bs, res = self.blocksize(), self['identifier'].li.size()
        return dyn.blockarray(ImageResourceBlock, bs - res)

    _fields_ = [
        (pstr.szstring, 'identifier'),
        (__resources, 'resources'),
        (__extra, 'extra'),
    ]

class File(codestream.Stream):
    class _object_(codestream.DecodedStream):
        Element, Data = StreamMarker, StreamData

    def StartOfDataMarkerQ(self, marker):
        # If we see the SOS code, then that's our data marker and the rest of our data
        # are all compressed scanlines.
        return intofdata(marker) in {0xffda}

    def DataMarkerQ(self, marker):
        res = intofdata(marker)
        if 0xffc0 <= res < 0xffff:
            # FIXME: it'd be nice if we could split our image data across these RST codes, but
            #        our codestream.Stream implementation doesn't support it.
            return res not in {0xffd0, 0xffd1, 0xffd2, 0xffd3, 0xffd4, 0xffd5, 0xffd6, 0xffd7}
        return False

    def EndOfDataMarkerQ(self, marker):
        # This EOI marker represents the end of our image data.
        return intofdata(marker) in {0xffd9}

    def _value_(self):
        return dyn.clone(ptype.block, length=self.source.size())

if __name__ == '__main__':
    import sys, ptypes, image.jpeg.jfif as jfif
    source = ptypes.setsource(ptypes.prov.file(sys.argv[1], 'rb'))

    # Read the contents of the jfif file as an individual stream
    z = jfif.File(source=source)
    z = z.l

    # Decode the jfif's codestream into its separate chunks
    a = z.d
    a = a.l

    if False:
        #input = getFileContents('Q100-2.JPG')
        input = getFileContents('huff_simple0.jpg')
        input = bytes(input.replace(b'\xff\x00', b'\xff'))

        jpegfile = File()
        jpegfile.deserialize(input)
        lookup = {type(item).__name__ : item for item in jpegfile}

        print(jpegfile[0])
        print(jpegfile[1])

    else:
        lookup = {}

    if all(operator.contains(lookup, name) for name in ['DQT', 'DHT', 'SCANDATA']):
        print('\n'.join(map("{!r}".format, jpegfile)))
        dqt = lookup['DQT']['table']
        dht = lookup['DHT']['table']
        sosdata = lookup['SCANDATA']
        print("{!r}".format(dqt))
        print("{!r}".format(dht))
        print("{!r}".format(sosdata))
        print('\n'.join(map("{!r}".format, dht)))
        print('\n'.join(map("{!r}".format, dqt)))

    ### load_quant_table
    if operator.contains(lookup, 'DQT'):
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
        quantizationTable = bytearray(self['value'].serialize())
        res, table = [], iter(quantizationTable)
        for y in range(8):
            for x in range(8):
                res.append( next(table) * scalefactor[y] * scalefactor[x] )
            continue

        scaledQuantizationTable = res

    ### decode_huffman ->
    ###     decode AC coefficient
    ###     decode DC coefficient

    ## process dht table
    if operator.contains(lookup, 'DHT'):
        self = lookup['DHT']['table'][3]
        print("{!r}".format(self))

    ### process scan data
    if operator.contains(lookup, 'SOS'):
        self = lookup['SOS']
        print("{!r}".format(self))
        print(self['component'][0])
        self = lookup['SOS']

    if operator.contains(lookup, 'SOF'):
        self = lookup['SOF']
