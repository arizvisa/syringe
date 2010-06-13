import ptypes
from ptypes import *

raise NotImplementedError("This is using an older/outdated version of ptypes")

config.WIDTH = 192

## primitive types
class BYTE(pByte): pass
class WORD(littleendian(pWord)): pass
class DWORD(littleendian(pDword)): pass
class short(WORD): pass
class ushort(WORD): pass

class chunkheader(pStruct):
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type')
    ]

chunkLookup = dict()

def consume(iterable, count):
    return ''.join([x for n,x in zip(xrange(count), iterable)])

def createUnknownChunk(t):
    class Unknown(pType):
        pass
    Unknown.__name__ = 'Unknown<0x%x>'% t
    return Unknown

class Chunk(pStruct): pass
class ChunkArray(pArray):
    _object_ = None

    def deserialize(self, iterable):
        self.value = []
        for x in range( len(self) ):
            a = getChunk(iterable)
            self.append(a)

## structures
class Header(pStruct):
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'frames'),
        (WORD,  'width'),
        (WORD,  'height'),
        (WORD,  'depth'),
        (WORD,  'flags'),
        (DWORD, 'speed'),
        (WORD,  'reserved1'),
        (DWORD, 'created'),
        (DWORD, 'creator'),
        (DWORD, 'updated'),
        (DWORD, 'updater'),
        (WORD,  'aspect_dx'),
        (WORD,  'aspect_dy'),
        (WORD,  'ext_flags'),
        (WORD,  'keyframes'),
        (WORD,  'totalframes'),
        (DWORD, 'req_memory'),
        (WORD,  'max_regions'),
        (WORD,  'transp_num'),
        (dyn.array(BYTE, 24),  'reserved2'),
        (DWORD, 'oframe1'),
        (DWORD, 'oframe2'),
        (dyn.array(BYTE,40),  'reserved3'),
    ]

class PREFIX_TYPE(Chunk):
    type = 0xf100
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'chunks'),
        (dyn.array(BYTE, 8), 'reserved')
    ]

class CEL_DATA(Chunk):
    type = 3
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (short, 'center_x'),
        (short, 'center_y'),
        (WORD,  'stretch_x'),
        (WORD,  'stretch_y'),
        (WORD,  'rot_x'),
        (WORD,  'rot_y'),
        (WORD,  'rot_z'),
        (WORD,  'cur_frame'),
        (dyn.array(BYTE, 2),  'reserved1'),
        (WORD,  'transparent'),
        (dyn.array(WORD, 16),  'overlay'),
        (dyn.array(BYTE,6), 'reserved2')
    ]

class SEGMENT_TABLE(Chunk):
    type = 0xf1fb
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'segments')
    ]

class SEGMENT(Chunk):
    type = 34
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'label'),
        (dyn.array(BYTE,2),  'reserved1'),
        (WORD,  'cont_image'),
        (WORD,  'last_image'),
        (WORD,  'flags'),
        (WORD,  'frames'),
        (DWORD, 'oframe1'),
        (DWORD, 'oframe2'),
        (WORD,  'next_segment'),
        (WORD,  'repeat'),
        (dyn.array(BYTE,2),  'reserved2'),
    ]

class HUFFMAN_CODE(pStruct):
    _fields_ = [
        (WORD, 'code'),
        (BYTE, 'length'),
        (BYTE, 'value')
    ]

class HUFFMAN_TABLE(Chunk):
    type = 0xf1fc
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'codelength'),
        (WORD,  'numcodes'),
        (dyn.array(BYTE,6),  'reserved'),
        (lambda s: dyn.array(HUFFMAN_CODE, s['numcodes'])(), 'code')
    ]


def createChunkArray(length):
    v = ChunkArray()
    v.length = length
    return v

class FRAME_TYPE(Chunk):
    type = 0xf1fa
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'chunks'),
        (WORD,  'delay'),
        (short, 'reserved'),
        (ushort, 'width'),
        (ushort, 'height'),
        (lambda s: createChunkArray(s['chunks']), 'data')
    ]

class PSTAMP(Chunk):
    type = 18
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'height'),
        (WORD,  'width'),
        (WORD,  'xlate'),
    ]

class LABEL(Chunk):
    type = 31
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved')
    ]

class LABELEX(Chunk):
    type = 41
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved'),
        (lambda s: dyn.block( s['size'] - 4 - 2 - 2 - 2), 'name')
    ]

class REGION(Chunk):
    type = 37
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'number'),
        (WORD, 'x'),
        (WORD, 'y'),
        (WORD, 'width'),
        (WORD, 'height'),
    ]

class WAVE(Chunk):
    type = 38
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (WORD,  'flags'),
        (WORD,  'samplefreq'),
        (DWORD, 'overlap'),
        (dyn.array(BYTE,6),  'reserved'),
    ]

class FRAMESHIFT(Chunk):
    type = 42
    _fields_ = [
        (DWORD, 'size'),
        (WORD,  'type'),
        (BYTE,  'img_id'),
        (BYTE,  'flags'),
        (WORD,  'prio_list'),
    ]

class RGB(pBinary):
    _fields_ = [(8, 'r'), (8, 'g'), (8, 'b')]

class ColorPacket(pStruct):
    _fields_ = [
        (BYTE, 'skip'),
        (BYTE, 'count'),
        (lambda s: dyn.array(RGB, int(s['count']) or 256)(), 'color')
    ]

class COLOR_64(Chunk):
    type = 11
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'numpackets'),
        (lambda s: dyn.array(ColorPacket, s['numpackets'])(), 'packets')
    ]

class LinePacket(pStruct):
    _fields_ = [
        (BYTE, 'skip'),
        (BYTE, 'count'),
        (lambda s: dyn.block((int(s['count'])&0x80) and 1 or int(s['count'])&0x7f )(), 'data')
    ]

class Line(pStruct):
    _fields_ = [
        (BYTE, 'numpackets'),
        (lambda s: dyn.array(LinePacket, s['numpackets'])(), 'packets')
    ]

class DELTA_FLI(Chunk):
    type = 12
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type'),
        (WORD, 'skip'),
        (WORD, 'numlines'),
        (lambda s: dyn.array(Line, s['numlines'])(), 'lines')
    ]

chunkLookup = dict([(cls.type, cls) for cls in globals().values() if type(cls) is type and cls is not Chunk and issubclass(cls, Chunk)])

def getChunk(iterable):
    iterable = iter(iterable)
    x = chunkheader()
    x.deserialize(iterable)

    # go back a step (sucks.)
    res = x.serialize() + consume(iterable, x['size'] - x.size())

    try:
        y = chunkLookup[ int(x['type']) ]()

    except KeyError:
        y = createUnknownChunk(x['type'])()
        y.length = len(res)

    y.deserialize(res)
    res = res[y.size():]
    if len(res) == 0:
        return y

    return y, res

if __name__ == '__main__':
#    x = file('janmar90.flc', 'rw')
    x = file('test.fli', 'rw')
    res = x.read()
    x.close()
    input = res

    iterable = iter(input)
    l = []

    header = Header()
    header.deserialize(iterable)
    l.append(header)

    print header

    res = input[ header.size():]

    v = getChunk(res)
    l.append(v)
    res = res[ v.size():]
    v,contents = getChunk(res)
    l.append(v)
    res = res[ v.size():]

    m = []

    v = getChunk(res)
    m.append(v)
    mangled = res[ v.size():]

#    v = getChunk(mangled)
#    m.append(v)

    v = DELTA_FLI()
    v.deserialize(mangled)
#
#    res = v[1]
#
#    x = ChunkArray()
#    x.length = 2
#    x.deserialize(res)
