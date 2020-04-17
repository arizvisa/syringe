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
    attribute, cache, table = '__name__', {}, []

### Marker types
class MarkerType(pint.enum, pint.uint16_t): pass
MarkerType._values_ = [(name, intofdata(data)) for name, data in Marker.table]

### Stream decoders
class StreamMarker(pstruct.type):
    Type, Table = MarkerType, Marker

    def __Type(self):
        return self.Type

    def __Value(self):
        t = self.Table.withdefault(self['Type'].li.str())
        if issubclass(t, ptype.block):
            return dyn.clone(t, length=self.blocksize() - self['Type'].li.size())
        return t

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
        self.__bounds__ = getattr(self, '__bounds__', [])

    def _object_(self):
        bounds = self.__bounds__[len(self.value)]

        # First figure out if we're a delimited marker
        t = dyn.clone(self._marker_.Type, length=0) if bounds < 0 else self._marker_.Type

        # Using the bounds, construct a new marker using it as the blocksize
        Fsize = lambda self, cb=abs(bounds): cb
        return dyn.clone(self._marker_, Type=t, blocksize=Fsize)

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
                    if n == 0x00:
                        state += b'\xff'
                        continue
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
        _object_ = self._object_
        marker = _object_._marker_
        supported = { dataofint(integer) for _, integer in marker.Type._values_ }

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

    def isDelimiter(self, marker):
        raise NotImplementedError

if __name__ == '__main__':
    blah = z[3]['data'].copy()
    #source = array.array('B', blah.serialize())

    x = Stream(source=ptypes.prov.string(blah.serialize()), blocksize=lambda :blah.size()).l
    y = x.decode()
    for x in y: print(x['type'])
    print(y[9])
    for n in y:
        print(n['type'])
