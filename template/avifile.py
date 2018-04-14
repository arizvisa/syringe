import ptypes
from ptypes import *

# little-endian
intofdata = lambda data: reduce(lambda t, c: t * 256 | c, map(ord, reversed(data)), 0)
_dataofint = lambda integer: ((integer == 0) and '\x00') or (_dataofint(integer // 256).lstrip('\x00') + chr(integer % 256))
dataofint = lambda integer, le=_dataofint: str().join(reversed(le(integer)))

## primitive types
class Frame(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'left'),
        (pint.uint16_t, 'top'),
        (pint.uint16_t, 'right'),
        (pint.uint16_t, 'bottom'),
    ]
    def summary(self):
        left = self['left'].li.summary()
        top = self['top'].li.summary()
        right = self['right'].li.summary()
        bottom = self['bottom'].li.summary()
        return 'left={:s} top={:s} right={:s} bottom={:s}'.format(left, top, right, bottom)

class AviBitmapInfoHeader(pstruct.type):
    _fields_ = [
        (pint.sint32_t, 'Size'),
        (pint.sint32_t, 'Width'),
        (pint.sint32_t, 'Height'),
        (pint.sint16_t, 'Planes'),
        (pint.sint16_t, 'BitCount'),
        (pint.sint32_t, 'Compression'),
        (pint.sint32_t, 'SizeImage'),
        (pint.sint32_t, 'XPelsPerMeter'),
        (pint.sint32_t, 'YPelsPerMeter'),
        (pint.sint32_t, 'ClrUsed'),
        (pint.sint32_t, 'ClrImportant'),
    ]

## FOURCC generic types
class FOURCC(ptype.definition): attribute, cache = '__name__', {}
class LISTTYPE(ptype.definition): cache = {}

class ID(pint.uint32_t):
    def summary(self):
        return '{!r} {:#010x}'.format(self.bytes(), self.int())
    def bytes(self):
        return self.value[:]
    def __setvalue__(self, value):
        if isinstance(value, bytes):
            self.value = value[:]
            return self
        return super(ID, self).__setvalue__(value)

class FOURCCID(pint.enum, ID): pass
class LISTID(pint.enum, ID): pass

class Chunk(pstruct.type):
    def __ckData(self):
        t, cb = self['ckID'].li, self['ckSize'].li
        tid, length = t.bytes(), cb.int()
        return FOURCC.lookup(tid, dyn.clone(FOURCC.default, type=tid, length=length))
        
    _fields_ = [
        (FOURCCID, 'ckID'),
        (pint.uint32_t, 'ckSize'),
        (__ckData, 'ckData'),
    ]

class LISTDATA(parray.block):
    type, _object_ = '\x00\x00\x00\x00', Chunk
    def blocksize(self):
        try:
            res = self.getparent(LIST).p
            if res is not None:
                if isinstance(res, File):
                    return res['fileSize'].li.int() - self.p['listType'].li.size()
                return res['ckSize'].li.int() - self.p['listType'].li.size()
        except ptypes.error.NotFoundError: pass
        return super(LISTDATA, self).blocksize()
    def classname(self):
        cls = self.__class__
        return '{:s}({:s})'.format(cls.__name__, self.type)
LISTTYPE.default = LISTDATA

## FOURCC definitions
@FOURCC.define
class LIST(pstruct.type):
    _fields_ = [
        (LISTID, 'listType'),
        (lambda s: LISTTYPE.lookup(s['listType'].li.bytes(), dyn.clone(LISTTYPE.default, type=s['listType'].bytes())), 'listData'),
    ]

    def classname(self):
        cls, res = self.__class__, self['listType'].bytes() if len(self.value) else '???'
        return '{:s}({:s})'.format(cls.__name__, res)

    def summary(self):
        t = self['listType'].bytes()
        res = ((res['ckID'].bytes(),res['ckSize'].int()) for res in self['listData'])
        return '{!r} [ {:s} ]'.format(t, ', '.join('{:s}={:#x}'.format(fcc, cb) for fcc,cb in res))

@FOURCC.define
class avih(pstruct.type):
    class AVIF(pbinary.flags):
        _fields_ = [
            (14, 'reserved_0(14)'),
            (1, 'COPYRIGHTED'),
            (1, 'WASCAPTUREFILE'),
            (4, 'reserved_10(4)'),
            (1, 'TRUSTCKTYPE'),
            (2, 'reserved_15(2)'),
            (1, 'ISINTERLEAVED'),
            (2, 'reserved_18(2)'),
            (1, 'MUSTUSEINDEX'),
            (1, 'HASINDEX'),
            (4, 'reserved_1c(4)'),
        ]
    _fields_ = [
        (pint.uint32_t, 'dwMicroSecPerFrame'),
        (pint.uint32_t, 'dwMaxBytesPerSec'),
        (pint.uint32_t, 'dwPaddingGranularity'),
        (pbinary.littleendian(AVIF), 'dwFlags'),
        (pint.uint32_t, 'dwTotalFrames'),
        (pint.uint32_t, 'dwInitialFrames'),
        (pint.uint32_t, 'dwStreams'),
        (pint.uint32_t, 'dwSuggestedBufferSize'),
        (pint.uint32_t, 'dwWidth'),
        (pint.uint32_t, 'dwHeight'),
        (dyn.array(pint.uint32_t,4), 'dwReserved'),
    ]

@FOURCC.define
class strh(pstruct.type):
    _fields_ = [
        (ID, 'fccType'),
        (ID, 'fccHandler'),
        (pint.uint32_t, 'dwFlags'),
        (pint.uint16_t, 'wPriority'),
        (pint.uint16_t, 'wLanguage'),
        (pint.uint32_t, 'dwInitialFrames'),
        (pint.uint32_t, 'dwScale'),
        (pint.uint32_t, 'dwRate'),
        (pint.uint32_t, 'dwStart'),
        (pint.uint32_t, 'dwLength'),
        (pint.uint32_t, 'dwSuggestedBufferSize'),
        (pint.uint32_t, 'dwQuality'),
        (pint.uint32_t, 'dwSampleSize'),
        (Frame, 'rcFrame'),
    ]

@FOURCC.define
class strf(ptype.block):
    pass

class Sample(Chunk):
    @classmethod
    def uncompressed(cls, number, **fields):
        res = cls().set(stID='{:02d}db'.format(number), **fields)
        res['stSize'].set(res['stData'].size())
        return res
    @classmethod
    def compressed(cls, number, **fields):
        res = cls().set(stID='{:02d}dc'.format(number), **fields)
        res['stSize'].set(res['stData'].size())
        return res
    @classmethod
    def palette(cls, number, **fields):
        res = cls().set(stID='{:02d}pc'.format(number), **fields)
        res['stSize'].set(res['stData'].size())
        return res
    @classmethod
    def audio(cls, number, **fields):
        res = cls().set(stID='{:02d}wb'.format(number), **fields)
        res['stSize'].set(res['stData'].size())
        return res

    def __init__(self, **attrs):
        super(Sample, self).__init__(**attrs)
        self.alias('ckID', 'stID'),
        self.alias('ckSize', 'stSize'),
        self.alias('ckData', 'stData'),

    _fields_ = [
        (ID, 'stID'),
        (pint.uint32_t, 'stSize'),
        (ptype.block, 'stData'),
    ]

class AviIndexEntry(pstruct.type):
    class AVIIF(pbinary.flags):
        _fields_ = [
            (4, 'reserved_0(4)'),
            (12, 'COMPRESSOR'),
            (7, 'unknown_10(7)'),
            (1, 'NO_TIME'),
            (3, 'unknown_18(3)'),
            (1, 'KEYFRAME'),
            (3, 'unknown_1c(3)'),
            (1, 'LIST'),
        ]
    _fields_ = [
        (pint.sint32_t, 'ChunkId'),
        (pbinary.littleendian(AVIIF), 'Flags'),
        (pint.sint32_t, 'Offset'),
        (pint.sint32_t, 'Size'),
    ]

class AVIOLDINDEX(pstruct.type):
    @classmethod
    def db(cls, number, **fields):
        return cls().set(dwChunkID='{:02d}db'.format(number), **fields)
    @classmethod
    def dc(cls, number, **fields):
        return cls().set(dwChunkID='{:02d}dc'.format(number), **fields)
    @classmethod
    def pc(cls, number, **fields):
        return cls().set(dwChunkID='{:02d}pc'.format(number), **fields)
    @classmethod
    def wb(cls, number, **fields):
        return cls().set(dwChunkID='{:02d}wb'.format(number), **fields)
    _fields_ = [
        (ID, 'dwChunkID'),
        (pbinary.littleendian(AviIndexEntry.AVIIF), 'dwFlags'),
        (pint.uint32_t, 'dwOffset'),
        (pint.uint32_t, 'dwSize'),
    ]

class AVIMETAINDEX(pstruct.type):
    class _adwIndex(parray.block):
        _object_ = pint.uint32_t    # FIXME: this depends on bIndexType

    def __adwIndex(self):
        try:
            res = self.getparent(Chunk)
        except ptypes.error.NotFoundError:
            return super(idx1, self).blocksize()
        cb = sum(self[n].size() for n in ('wLongsPerEntry', 'bIndexSubType', 'bIndexType', 'nEntriesInUse', 'dwChunkId', 'dwReserved'))
        return dyn.clone(AVIMETAINDEX._adwIndex, blocksize=lambda s, cb=res['ckSize'].li.int() - cb: cb)

    class AVI_INDEX(pint.uint8_t):
        _values_ = [
            ('OF_INDEXES', 0),
            ('OF_CHUNKS', 1),
            ('IS_DATA', 0x80),
        ]

    _fields_ = [
        #(FOURCCID, 'fcc'),
        #(pint.uint32_t, 'cb'),
        (pint.uint16_t, 'wLongsPerEntry'),
        (pint.uint8_t, 'bIndexSubType'),
        (AVI_INDEX, 'bIndexType'),
        (pint.uint32_t, 'nEntriesInUse'),
        (ID, 'dwChunkId'),
        (dyn.array(pint.uint32_t, 3), 'dwReserved'),
        (__adwIndex, 'adwIndex'),
    ]

@FOURCC.define
class idx1(parray.block):
    _object_ = AVIOLDINDEX

    def blocksize(self):
        try:
            res = self.getparent(Chunk)
            return res['fileSize'].li.int() if isinstance(res, File) else res['ckSize'].li.int()
        except ptypes.error.NotFoundError: pass
        return super(idx1, self).blocksize()

## FOURCC LISTDATA types
@LISTTYPE.define
class AVI(LISTDATA): type= 'AVI '
@LISTTYPE.define
class hdrl(LISTDATA): type = 'hdrl'
@LISTTYPE.define
class strl(LISTDATA): type = 'strl'
@LISTTYPE.define
class movi(LISTDATA): type = 'movi'

## FOURCC file
FOURCCID._values_ = [(v.__name__, intofdata(k)) for k, v in FOURCC.cache.iteritems()]
LISTID._values_ = [(v.type, intofdata(k)) for k, v in LISTTYPE.cache.iteritems()]
class File(pstruct.type):
    class _fileData(parray.block):
        _object_ = Chunk
        def summary(self):
            res = ((res['ckID'].bytes(),res['ckSize'].int()) for res in self)
            return ', '.join('{:s}={:#x}'.format(fcc, cb) for fcc,cb in res)

    def __fileData(self):
        cb = self['fileSize'].li.int()
        return dyn.clone(self._fileData, blocksize=lambda s,cb=cb-self['fileType'].li.size(): cb)

    _fields_ = [
        (ID, 'fileID'),
        (pint.uint32_t, 'fileSize'),
        (LIST, 'fileData'),
    ]
