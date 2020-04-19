import ptypes, six, operator, itertools

from ptypes import *
from . import intofdata, dataofint, __izip_longest__

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### Marker list and table
class MarkerType(pint.enum, pint.uint16_t):
    _values_ = []

    def __init__(self, **attrs):
        res = [(name, intofdata(integer) if isinstance(integer, bytes) else integer) for name, integer in self._values_]
        attrs.setdefault('_values_', res)
        return super(MarkerType, self).__init__(**attrs)

class Marker(ptype.definition):
    cache, table = {}, MarkerType._values_

    @classmethod
    def define(cls, definition):
        try:
            index = next(index for index, (name, _) in enumerate(cls.table) if name == definition.__name__)

        # If we couldn't find anything, then there's nothing to do. So we can
        # just leave.
        except StopIteration:
            pass

        # Use the index to find the element in our table. This way we can convert
        # any bytes into integer for the enumeration, and assign the bytes to
        # the attribute for the definition.
        else:
            name, res = cls.table[index]
            if isinstance(res, bytes):
                cls.table[index] = name, intofdata(res)
            setattr(definition, cls.attribute, res if isinstance(res, bytes) else dataofint(res))
        return super(Marker, cls).define(definition)

### Encoding types
class ByteStuffer(ptype.encoded_t):
    def encode(self, object, **attrs):
        res, iterable = b'', iter(bytearray(object.serialize()))
        for by in iterable:
            res += six.int2byte(by)
            if by == 0xff:
                res += six.int2byte(0)
            continue
        return ptype.block().set(res)

    def decode(self, object, **attrs):
        state, iterable = b'', iter(bytearray(object.serialize()))

        try:
            while True:
                m = next(iterable)
                if m == 0xff:
                    n = next(iterable)
                    if n == 0:
                        state += six.int2byte(0xff)
                        continue
                    state += six.int2byte(m) + six.int2byte(n)
                else:
                    state += six.int2byte(m)
                continue

        except StopIteration:
            pass

        res = ptype.block().set(state)
        return super(ByteStuffer, self).decode(res, **attrs)

### Stream decoders
class StreamMarker(pstruct.type):
    Type, Table = MarkerType, Marker

    def __Type(self):
        return self.Type

    def __Value(self):
        res = self['Type'].li
        return self.Table.withdefault(res.serialize())

    def __Extra(self):
        fields = ['Type', 'Value']
        t = dyn.block(self.blocksize() - sum(self[fld].li.size() for fld in fields))
        if hasattr(self['Value'], 'EncodedQ') and self['Value'].EncodedQ():
            return dyn.clone(ByteStuffer, _value_=t)
        return t

    _fields_ = [
        (__Type, 'Type'),
        (__Value, 'Value'),
        (__Extra, 'Extra'),
    ]

    def alloc(self, **fields):
        attribute = self.Table.attribute
        Fattribute = operator.attrgetter(attribute)
        res = super(StreamMarker, self).alloc(**fields)

        if operator.contains(fields, 'Type'):
            return res

        return res.set(Type=intofdata(Fattribute(res['Value']))) if hasattr(res['Value'], attribute) else res

class DecodedStream(parray.block):
    Element = StreamMarker
    def __init__(self, **attrs):
        super(DecodedStream, self).__init__(**attrs)

        # Make a copy of our bounds as we'll use this to bound each element of our array
        self.__bounds__ = getattr(self, '__bounds__', [])

    def _object_(self):
        bounds = self.__bounds__[len(self.value)]

        # First figure out if we're a delimited marker
        t = dyn.clone(self.Element.Type, length=0) if bounds < 0 else self.Element.Type

        # Using the bounds, construct a new marker using it as the blocksize
        Fsize = lambda self, cb=abs(bounds): cb
        return dyn.clone(self.Element, Type=t, blocksize=Fsize)

    def blocksize(self):
        return sum(map(abs, self.__bounds__))

class Stream(ptype.encoded_t):
    _object_ = DecodedStream

    def __init__(self, **attrs):
        self.__bounds__ = bounds = []

        # Tie our bounds attribute to the object used for each element
        attrs.setdefault('_object_', dyn.clone(self._object_, __bounds__=bounds))
        super(Stream, self).__init__(**attrs)

    @classmethod
    def __split_stream(cls, data):
        result = []

        # decode stream into its components
        state, iterable = b'', iter(bytearray(data))
        try:
            while True:
                m = next(iterable)
                if m == 0xff:
                    n = next(iterable)
                    result.append(state)
                    result.append(six.int2byte(m) + six.int2byte(n))
                    state = b''
                    continue
                state += six.int2byte(m)

        except StopIteration:
            result.append(state)

        ## if we found extra data before a marker, then prefix our results
        ## with a dummy marker so that we can add it to our list
        if len(result[0]) > 0:
            result.insert(0, b'')
        else:
            result.pop(0)

        return result

    def decode(self, object, **attrs):
        if not self.initializedQ():
            raise ptypes.error.InitializationError(self, 'decode')

        ## enumerate all of the markers that we support
        markerElementTable = self._object_.Element.Table
        supported = { integer if isinstance(integer, bytes) else dataofint(integer) for _, integer in markerElementTable.table }

        ## chunk out our stream
        result = self.__split_stream(object.serialize())

        ## pair up each marker with its data
        iterable = __izip_longest__(*[iter(result)] * 2)

        ## figure out the bounds of each element. If the marker is empty, then
        ## this element is just data and we'll use a negative length to mark it
        bounds = []
        for marker, data in iterable:
            size = len(marker) + len(data)

            ## check to see if our marker is supporteed
            if operator.contains(supported, marker):
                bounds.append(+size if marker else -size)

            ## otherwise, just extend the previous record
            else:
                bounds[-1] = (bounds[-1] - size) if bounds[-1] < 0 else (bounds[-1] + size)
            continue
        self.__bounds__[:] = bounds

        ## last thing to do is to cast our decoded data into an object
        data = bytes(bytearray(itertools.chain(*result)))
        decoded = ptype.block().set(data)
        return super(Stream, self).decode(decoded)

if __name__ == '__main__':
    blah = z[3]['data'].copy()

    x = Stream(source=ptypes.prov.string(blah.serialize()), blocksize=lambda :blah.size()).l
    y = x.decode()
    for x in y: print(x['type'])
    print(y[9])
    for n in y:
        print(n['type'])
