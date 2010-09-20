import ptypes
from ptypes import *

## primitive types
class BYTE(pint.uint8_t): pass
class WORD(pint.littleendian(pint.uint16_t)): pass
class DWORD(pint.littleendian(pint.uint32_t)): pass
class short(pint.int16_t): pass
class ushort(pint.uint16_t): pass

class ChunkHeader(pstruct.type):
    _fields_ = [
        (DWORD, 'size'),
        (WORD, 'type')
    ]
chunkLookup = dict()

def createUnknownChunk(t, s):
    class Unknown(dyn.block(0)):
        pass
    Unknown.__name__ = 'Unknown<0x%x>'% t
    Unknown.length = s
    return Unknown

class Chunk(pstruct.type): pass
class ChunkGeneral(pstruct.type):
    def __data(self):
        t = int(self['header']['type'])
        try:
            y = chunkLookup[t]

        except KeyError:
            y = createUnknownChunk(t, self.blocksize() - self['header'].size())
        return y

    _fields_ = [
        (ChunkHeader, 'header'),
        (__data, 'data')
    ]

    def blocksize(self):
        return int(self['header']['size'])

class ChunkArray(parray.type):
    _object_ = ChunkGeneral

## structures
class FlicHeader(pstruct.type):
    _fields_ = [
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

class File(pstruct.type):
    type = 0xaf11

    class _chunks(parray.block):
        _object_ = ChunkGeneral
        def isTerminator(self, value):
            print "Loading element %s from offset %x with type %x"% (value.__name__, value.getoffset(), value['header']['type'])
            return super(File._chunks, self).isTerminator(value)

    _fields_ = [
        (ChunkHeader, 'header'),
        (FlicHeader, 'flicheader'),
        (lambda s: dyn.clone(s._chunks, blocksize=lambda x: int(s['header'].l['size'])-s['flicheader'].size()-s['header'].size()), 'data'),
    ]

    def __repr__(self):
        if self.initialized:
            lookup = {}
            for n in self['data']:
                t = int(n['header']['type'])
                try:
                    lookup[t] += 1
                except KeyError:
                    lookup[t] = 1
                continue
            s = ','.join([ '(%x, %d)'% (k,v) for k,v in lookup.items() ])
            return '%s header=%x flicheader=. data=%s'% (self.name(), int(self['header']['type']), s)
        return super(File, self).__repr__()

class PREFIX_TYPE(Chunk):
    type = 0xf100
    _fields_ = [
        (WORD, 'chunks'),
        (dyn.array(BYTE, 8), 'reserved')
    ]

class CEL_DATA(Chunk):
    type = 3
    _fields_ = [
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
        (WORD, 'segments')
    ]

class SEGMENT(Chunk):
    type = 34
    _fields_ = [
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

class HUFFMAN_CODE(pstruct.type):
    _fields_ = [
        (WORD, 'code'),
        (BYTE, 'length'),
        (BYTE, 'value')
    ]

class HUFFMAN_TABLE(Chunk):
    type = 0xf1fc
    _fields_ = [
        (WORD,  'codelength'),
        (WORD,  'numcodes'),
        (dyn.array(BYTE,6),  'reserved'),
        (lambda s: dyn.array(HUFFMAN_CODE, int(s['numcodes'].l)), 'code')
    ]

class FRAME_TYPE(Chunk):
    type = 0xf1fa
    _fields_ = [
        (WORD,  'chunks'),
        (WORD,  'delay'),
        (short, 'reserved'),
        (ushort, 'width'),
        (ushort, 'height'),
        (lambda s: dyn.clone(ChunkArray, length=int(s['chunks'].l)), 'data')
    ]

class PSTAMP(Chunk):
    type = 18
    _fields_ = [
        (WORD,  'height'),
        (WORD,  'width'),
        (WORD,  'xlate'),
    ]

class LABEL(Chunk):
    type = 31
    _fields_ = [
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved')
    ]

class LABELEX(Chunk):
    type = 41
    _fields_ = [
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved'),
        (lambda s: dyn.block( int(s['size'].l) - 4 - 2 - 2 - 2), 'name')
    ]

class REGION(Chunk):
    type = 37
    _fields_ = [
        (WORD, 'number'),
        (WORD, 'x'),
        (WORD, 'y'),
        (WORD, 'width'),
        (WORD, 'height'),
    ]

class WAVE(Chunk):
    type = 38
    _fields_ = [
        (WORD,  'flags'),
        (WORD,  'samplefreq'),
        (DWORD, 'overlap'),
        (dyn.array(BYTE,6),  'reserved'),
    ]

class FRAMESHIFT(Chunk):
    type = 42
    _fields_ = [
        (BYTE,  'img_id'),
        (BYTE,  'flags'),
        (WORD,  'prio_list'),
    ]

class RGB(pbinary.struct):
    _fields_ = [(8, 'r'), (8, 'g'), (8, 'b')]

class ColorPacket(pstruct.type):
    _fields_ = [
        (BYTE, 'skip'),
        (BYTE, 'count'),
        (lambda s: dyn.array(RGB, int(s['count'].l) or 256), 'color')
    ]

class COLOR_64(Chunk):
    type = 11
    _fields_ = [
        (WORD, 'numpackets'),
        (lambda s: dyn.array(ColorPacket, int(s['numpackets'].l)), 'packets')
    ]

class LinePacket(pstruct.type):
    _fields_ = [
        (BYTE, 'skip'),
        (BYTE, 'count'),
        (lambda s: dyn.block((int(s['count'].l)&0x80) and 1 or int(s['count'].l)&0x7f ), 'data') #XXX
    ]

class Line(pstruct.type):
    _fields_ = [
        (BYTE, 'numpackets'),
        (lambda s: dyn.array(LinePacket, int(s['numpackets'].l)), 'packets')
    ]

class DELTA_FLI(Chunk):
    type = 12
    _fields_ = [
        (WORD, 'skip'),
        (WORD, 'numlines'),
        (lambda s: dyn.array(Line, int(s['numlines'].l)), 'lines')
    ]

chunkLookup = dict([(cls.type, cls) for cls in globals().values() if type(cls) is type and cls is not Chunk and issubclass(cls, Chunk)])

if __name__ == '__main__':
    import ptypes,flic
    reload(flic)
    ptypes.setsource( ptypes.file('./test.fli') )
#    ptypes.setsource( ptypes.file('./janmar90.flc') )

    z = ptypes.debugrecurse(flic.File)()
    z = z.l
    print z
