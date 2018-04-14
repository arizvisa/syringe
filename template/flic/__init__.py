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

class ChunkType(ptype.definition):
    cache = {}
    class unknown(ptype.block):
        def classname(self):
            return 'Unknown<0x%x>'% self.type
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
        t = self['header'].li['type'].int()
        return ChunkType.get(t, type=t, length=self.blocksize()-self['header'].size())

    _fields_ = [
        (ChunkHeader, 'header'),
        (__data, 'data')
    ]

    def blocksize(self):
        return self['header']['size'].int()

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
        (lambda s: dyn.clone(s._chunks, blocksize=lambda x: s['header'].li['size'].int()-s['flicheader'].size()-s['header'].size()), 'data'),
    ]

    def summary(self):
        if self.initialized:
            lookup = {}
            for n in self['data']:
                t = n['header']['type'].int()
                try:
                    lookup[t] += 1
                except KeyError:
                    lookup[t] = 1
                continue
            s = ','.join([ '(%x, %d)'% (k,v) for k,v in lookup.items() ])
            return 'header=%x flicheader=. data=%s'% (self['header']['type'].int(), s)
        return super(File, self).summary()
    repr = summary

@ChunkType.define
class PREFIX_TYPE(pstruct.type):
    type = 0xf100
    _fields_ = [
        (WORD, 'chunks'),
        (dyn.array(BYTE, 8), 'reserved')
    ]

@ChunkType.define
class CEL_DATA(pstruct.type):
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

@ChunkType.define
class SEGMENT_TABLE(pstruct.type):
    type = 0xf1fb
    _fields_ = [
        (WORD, 'segments')
    ]

@ChunkType.define
class SEGMENT(pstruct.type):
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

@ChunkType.define
class HUFFMAN_TABLE(pstruct.type):
    type = 0xf1fc
    _fields_ = [
        (WORD,  'codelength'),
        (WORD,  'numcodes'),
        (dyn.array(BYTE,6),  'reserved'),
        (lambda s: dyn.array(HUFFMAN_CODE, s['numcodes'].li.int()), 'code')
    ]

@ChunkType.define
class FRAME_TYPE(pstruct.type):
    type = 0xf1fa
    _fields_ = [
        (WORD,  'chunks'),
        (WORD,  'delay'),
        (short, 'reserved'),
        (ushort, 'width'),
        (ushort, 'height'),
        (lambda s: dyn.clone(ChunkArray, length=s['chunks'].li.int()), 'data')
    ]

@ChunkType.define
class PSTAMP(pstruct.type):
    type = 18
    _fields_ = [
        (WORD,  'height'),
        (WORD,  'width'),
        (WORD,  'xlate'),
    ]

@ChunkType.define
class LABEL(pstruct.type):
    type = 31
    _fields_ = [
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved')
    ]

@ChunkType.define
class LABELEX(pstruct.type):
    type = 41
    _fields_ = [
        (WORD, 'label'),
        (dyn.array(BYTE, 2), 'reserved'),
        (lambda s: dyn.block( s['size'].li.int() - 4 - 2 - 2 - 2), 'name')
    ]

@ChunkType.define
class REGION(pstruct.type):
    type = 37
    _fields_ = [
        (WORD, 'number'),
        (WORD, 'x'),
        (WORD, 'y'),
        (WORD, 'width'),
        (WORD, 'height'),
    ]

@ChunkType.define
class WAVE(pstruct.type):
    type = 38
    _fields_ = [
        (WORD,  'flags'),
        (WORD,  'samplefreq'),
        (DWORD, 'overlap'),
        (dyn.array(BYTE,6),  'reserved'),
    ]

@ChunkType.define
class FRAMESHIFT(pstruct.type):
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
        (lambda s: dyn.array(RGB, s['count'].li.int() or 256), 'color')
    ]

@ChunkType.define
class COLOR_64(pstruct.type):
    type = 11
    _fields_ = [
        (WORD, 'numpackets'),
        (lambda s: dyn.array(ColorPacket, s['numpackets'].li.int()), 'packets')
    ]

class LinePacket(pstruct.type):
    _fields_ = [
        (BYTE, 'skip'),
        (BYTE, 'count'),
        (lambda s: dyn.block((s['count'].li.int()&0x80) and 1 or s['count'].li.int()&0x7f), 'data') #XXX
    ]

class Line(pstruct.type):
    _fields_ = [
        (BYTE, 'numpackets'),
        (lambda s: dyn.array(LinePacket, s['numpackets'].li.int()), 'packets')
    ]

@ChunkType.define
class DELTA_FLI(pstruct.type):
    type = 12
    _fields_ = [
        (WORD, 'skip'),
        (WORD, 'numlines'),
        (lambda s: dyn.array(Line, s['numlines'].li.int()), 'lines')
    ]

if __name__ == '__main__':
    import ptypes,flic
    reload(flic)
    ptypes.setsource( ptypes.file('./test.fli') )
#    ptypes.setsource( ptypes.file('./janmar90.flc') )

    z = ptypes.debugrecurse(flic.File)()
    z = z.l
    print z
