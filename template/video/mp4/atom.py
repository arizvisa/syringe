from .primitives import *

class AtomType(ptype.definition):
    cache = {}

class Atom(pstruct.type):
    def __data(self):
        type = self['type'].li.serialize()
        typename = bytes(filter(None, bytearray(type))).decode('latin1')

        # Load all our size fields so we can figure out the size that
        # we're supposed to be using.
        res = sum(self[fld].li.size() for fld in ['size', 'type', 'extended_size'])
        expected = self.Size() - res if self.Size() > res else 0

        # Figure out the type that we're supposed to return and return it.
        t = AtomType.withdefault(type, type=type, __name__="Unknown<{!s}>".format(typename), length=expected)
        if issubclass(t, parray.block):
            return dyn.clone(t, blocksize=lambda _, cb=expected: cb)
        return t

    def __missing(self):
        res = sum(self[fld].li.size() for fld in ['size', 'type', 'extended_size'])
        expected = self.Size() - res
        leftover = expected - self['data'].li.size()
        return dyn.block(max(0, leftover))

    _fields_ = [
        (pQTInt, 'size'),
        (pQTType, 'type'),
        (lambda self: pint.uint64_t if self['size'].li.int() == 1 else pint.uint_t, 'extended_size'),
        (__data, 'data'),
        (__missing, 'missing'),
    ]

    def ExtendedSizeQ(self):
        return self['size'].int() == 1

    def HeaderSize(self):
        return sum(self[fld].size() for fld in ['size', 'type', 'extended_size'])

    def Size(self):
        res = self['size'].int()
        if res == 1:
            return self['extended_size'].li.int()

        p = self.parent
        if res == 0 and isinstance(p, parray.block):
            container = p.parent
            if container:
                position = self.getoffset() - container.getoffset()
                return max(0, container.Size() - position)
            if isinstance(self.source, ptypes.prov.bounded):
                return max(0, self.source.size() - self.getoffset())
            return res
        return res

    def summary(self):
        if not self.initializedQ() and self.value is None:
            return "UNINITIALIZED expected:{:#x} keys:({:s})".format(0, ','.join(self.keys()))

        discrepancy = self.size() != self.blocksize()
        if discrepancy:
            return "{!s} ERR size:{:#x} expected:{:#x} keys:({:s})".format(self['type'].serialize().decode('latin1'), self.size(), self.Size(), ','.join(self.keys()))
        return "{!s} size:{:#x} ({:s})".format(self['type'].serialize().decode('latin1'), self.Size(), ','.join(self.keys()))

    def alloc(self, **fields):
        res = super(Atom, self).alloc(**fields)
        if all(fld not in fields for fld in ['size', 'extended_size']):
            cb = self['data'].size()
            return self.alloc(size=cb, **fields) if cb < pow(2,32) else self.alloc(size=1, extended_size=pint.uint64_t().set(cb), type=res['type'], data=res['data'], **fields)
        return res.set(type=res['data'].type) if hasattr(res['data'], 'type') else res

class AtomList(parray.block):
    _object_ = Atom

    def search(self, type):
        '''Search through a list of atoms for a particular fourcc type'''
        return (item for item in self if item['type'] == type)

    def lookup(self, type):
        '''Return the first instance of specified atom type'''
        return next(item for item in self if item['type'] == type)

    def summary(self):
        types = ','.join([x['type'].serialize().decode('latin1') for x in self])
        return ' '.join(["atoms[{:d}] ->".format(len(self)), types])

## atom templates
class FullBox(pstruct.type):
    Box = ptype.undefined
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.clone(pint.uint_t, length=3), 'Flags'),
        (lambda self: self.Box, 'Box'),
    ]
    def Version(self):
        return self['Version']
    def Flags(self):
        return self['Flags']

class EntriesAtom(FullBox):
    class Box(pstruct.type):
        def __Header(self):
            p = self.getparent(EntriesAtom)
            return p.Header
        def __Entry(self):
            p = self.getparent(EntriesAtom)
            entry, count = p.Entry, self['Count'].li
            if issubclass(entry, pbinary.base):
                return dyn.clone(pbinary.array, _object_=entry, length=count.int())
            return dyn.clone(parray.type, _object_=entry, length=count.int())
        _fields_ = [
            (__Header, 'Header'),
            (pQTInt, 'Count'),
            (__Entry, 'Entry'),
        ]
    class Header(pstruct.type):
        _fields_ = []
    class Entry(ptypes.undefined):
        pass

## container atoms
@AtomType.define
class MovieBox(AtomList):
    type = b'moov'

@AtomType.define
class TrackBox(AtomList):
    type = b'trak'

@AtomType.define
class EditBox(AtomList):
    type = b'edts'

@AtomType.define
class MediaBox(AtomList):
    type = b'mdia'

@AtomType.define
class MediaInformationBox(AtomList):
    type = b'minf'

@AtomType.define
class DataInformationBox(AtomList):
    type = b'dinf'

@AtomType.define
class UserDataBox(Atom):
    type = b'udta'

@AtomType.define
class SampleTableBox(AtomList):
    type = b'stbl'

@AtomType.define
class GenericMediaHeaderBox(AtomList):
    type = b'gmhd'

@AtomType.define
class MetaBox(AtomList):
    type = b'meta'

@AtomType.define
class ReferenceMovieAtom(AtomList):
    type = b'rmra'

@AtomType.define
class ReferenceMovieDescriptorAtom(AtomList):
    type = b'rmda'

#@AtomType.define
#class MediaDataBox(AtomList):
#    'sometimes this is not a container'
#    type = b'mdat'

@AtomType.define
class MediaDataBox(ptype.block):
    type = b'mdat'

## empty atoms
@AtomType.define
class ExpansionSpaceReservationAtom(pstruct.type):
    type = b'wide'
    _fields_ = []

## WLOC
@AtomType.define
class WindowLocationBox(pstruct.type):
    type = b'WLOC'
    _fields_ = [
        (pint.uint16_t, 'X'),
        (pint.uint16_t, 'Y')
    ]

## ftyp
@AtomType.define
class FileTypeBox(pstruct.type):
    type = b'ftyp'
    class _Compatible_Brands(parray.block):
        _object_ = pQTInt

    def __Compatible_Brands(self):
        try:
            p = self.getparent(Atom)
        except ptypes.error.ItemNotFoundError:
            return self._Compatible_Brands
        expected = p.Size() - p.HeaderSize()

        res = sum(self[fld].li.size() for fld in ['Major_Brand', 'Minor_Version'])
        return dyn.clone(self._Compatible_Brands, blocksize=lambda _, cb=max(0, expected -res): cb)

    _fields_ = [
        (pQTInt, 'Major_Brand'),
        (pQTInt, 'Minor_Version'),
        (__Compatible_Brands, 'Compatible_Brands')
    ]

@AtomType.define
class MovieHeaderBox(FullBox):
    type = b'mvhd'
    class Box(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'Creation time'),
            (pint.uint32_t, 'Modification time'),
            (pint.uint32_t, 'Time scale'),
            (pint.uint32_t, 'Duration'),
            (pint.uint32_t, 'Preferred rate'),
            (pint.uint16_t, 'Preferred volume'),
            (dyn.block(10), 'Reserved'),
            (Matrix, 'Matrix structure'),
            (pint.uint32_t, 'Preview time'),
            (pint.uint32_t, 'Preview duration'),
            (pint.uint32_t, 'Poster time'),
            (pint.uint32_t, 'Selection time'),
            (pint.uint32_t, 'Selection duration'),
            (pint.uint32_t, 'Current time'),
            (pint.uint32_t, 'Next track ID'),
        ]

@AtomType.define
class TrackHeaderBox(FullBox):
    type = b'tkhd'
    class Box(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'Creation time'),
            (pint.uint32_t, 'Modification time'),
            (pint.uint32_t, 'Track ID'),
            (pint.uint32_t, 'Reserved'),
            (pint.uint32_t, 'Duration'),    # XXX: is this right?
            (pint.uint64_t, 'Reserved'),
            (pint.uint16_t, 'Layer'),
            (pint.uint16_t, 'Alternate group'),
            (pint.uint16_t, 'Volume'),
            (pint.uint16_t, 'Reserved'),
            (Matrix, 'Matrix structure'),
            (Fixed, 'Track width'),
            (Fixed, 'Track height'),
        ]

@AtomType.define
class EditListBox(EntriesAtom):
    type = b'elst'
    class Entry(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'duration'),
            (pint.uint32_t, 'time'),
            (pint.uint32_t, 'rate'),
        ]

@AtomType.define
class MediaHeaderBox(FullBox):
    type = b'mdhd'
    class Box_v0(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'Creation time'),
            (pint.uint32_t, 'Modification time'),
            (pint.uint32_t, 'Time scale'),
            (pint.uint32_t, 'Duration'),
        ]
    class Box_v1(pstruct.type):
        _fields_ = [
            (pint.uint64_t, 'Creation time'),
            (pint.uint64_t, 'Modification time'),
            (pint.uint32_t, 'Time scale'),
            (pint.uint64_t, 'Duration'),
        ]

    class Box(pstruct.type):
        def __Time(self):
            p = self.getparent(FullBox)
            version = p.Version()
            if version.int() == 1:
                return p.Box_v1
            elif version.int() == 0:
                return p.Box_v0
            raise NotImplementedError(version)
        _fields_ = [
            (__Time, 'Time'),
            (pint.uint16_t, 'Language'),
            (pint.uint16_t, 'Quality')
        ]

@AtomType.define
class HandlerBox(FullBox):
    type = b'hdlr'
    class Box(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'Component type'),
            (pint.uint32_t, 'Component subtype'),
            (pint.uint32_t, 'Component manufacturer'),
            (pint.uint32_t, 'Component flags'),
            (pint.uint32_t, 'Component Flags mask'),
            (pQTString, 'Component name')
        ]

## stsd
class MediaVideo(ptype.definition):
    attribute, cache = 'version', {}

@MediaVideo.define
class MediaVideo_v1(pstruct.type):
    'might need to be renamed'
    version, type = 1, 'vide'
    class CompressorName(pstruct.type):
        _fields_ = [
            (pint.uint8_t, 'length'),
            (lambda self: dyn.clone(pstr.string, length=self['length'].li.int()), 'string'),
            (lambda self: dyn.block(0x20 - self['length'].li.int()), 'padding')
        ]
    class ColorTable(pstruct.type):
        class argb(pstruct.type):
            _fields_ = [(pint.uint16_t, item) for item in 'irgb']
            def summary(self):
                i, r, g, b = (self[item].int() for item in 'irgb')
                return '{:d} ({:04x},{:04x},{:04x})'.format(i, r, g, b)
            repr = summary
        def __entries(self):
            n = self['end'].li.int() - self['start'].li.int()
            return dyn.array(self.argb, n+1)
        _fields_ = [
            (pint.uint32_t, 'start'),
            (pint.uint8_t, 'count'),
            (pint.uint16_t, 'end'),
            (__entries, 'entries'),
        ]
    def __ColorTable(self):
        n = self['Depth'].li.int()
        return self.ColorTable if n in (2,4,8) else ptype.undefined

    _fields_ = [
        (pQTInt, 'Data size'),
        (pint.uint16_t, 'Frame Count'),
        (CompressorName, 'Compressor Name'),
        (pint.littleendian(pint.uint16_t), 'Depth'),
        (pint.uint16_t, 'Color Table ID'),
        (__ColorTable, 'Color Table'),
    ]

# FIXME: this isn't decoding mpeg audio yet.
class ElementaryStreamDescriptorAtom(pstruct.type):
    type = b'esds'
    _fields_ = [
        (pint.uint32_t, 'Version'),
        (ptype.type, 'Elementary Stream Descriptor'),
    ]

class MediaAudio(ptype.definition):
    attribute, cache = 'version', {}

@MediaAudio.define
class MediaAudio_v0(pstruct.type):
    version, type = 0, 'soun'
    _fields_ = []

@MediaAudio.define
class MediaAudio_v1(pstruct.type):
    version, type = 1, 'soun'
    _fields_ = [
        (pint.uint32_t, 'Samples per packet'),
        (pint.uint32_t, 'Bytes per packet'),
        (pint.uint32_t, 'Bytes per frame'),
        (pint.uint32_t, 'Bytes per sample'),
    ]
@MediaAudio.define
class MediaAudio_v2(pstruct.type):
    version, type = 2, 'soun'
    _fields_ = [
        (pint.uint32_t, 'Size'),
        (pfloat.double, 'Sample rate2'),
        (pint.uint32_t, 'Channels2'),
        (pint.uint32_t, 'Reserved'),
        (pint.uint32_t, 'Bits per coded sample'),
        (pint.uint32_t, 'Lpcm'),
        (pint.uint32_t, 'Bytes per frame'),
        (pint.uint32_t, 'Samples per frame'),
    ]

@AtomType.define
class SampleDescriptionBox(EntriesAtom):
    '''Sample description atom'''
    type = b'stsd'
    class Audio(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Version'),
            (pint.uint16_t, 'Revision level'),
            (pQTType, 'Vendor'),
            (pint.uint16_t, 'Number of channels'),
            (pint.uint16_t, 'Sample size'),
            (pint.uint16_t, 'Compression ID'),
            (pint.uint16_t, 'Packet size'),
            (pint.uint32_t, 'Sample rate'),
            (lambda self: MediaAudio.withdefault(self['Version'].li.int(), type=self['Version'].int()), 'Versioned'),
        ]

    class Video(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Version'),
            (pint.uint16_t, 'Revision level'),
            (pQTType, 'Vendor'),
            (pQTInt, 'Temporal Quality'),
            (pQTInt, 'Spatial Quality'),
            (pint.uint16_t, 'Width'),
            (pint.uint16_t, 'Height'),
            (pQTInt, 'Horizontal Resolution'),
            (pQTInt, 'Vertical Resolution'),
            (lambda self: MediaVideo.withdefault(self['Version'].li.int(), type=self['Version'].int()), 'Versioned'),
        ]

    class Entry(pstruct.type):
        def __Data_specific(self):
            sz = self['Sample description size'].li.int()
            return dyn.block(sz - 4 - 4 - 6 - 2)

        _fields_ = [
            (pQTInt, 'Sample description size'),
            (pQTType, 'Data format'),
            (dyn.block(6), 'Reserved'),
            (pint.uint16_t, 'Data reference index'),
            (__Data_specific, 'Data specific'),
        ]

### stts
@AtomType.define
class TimeToSampleBox(EntriesAtom):
    '''Time-to-sample atom'''
    type = b'stts'
    class Entry(pstruct.type):
        _fields_ = [
            (pQTInt, 'Sample count'),
            (pQTInt, 'Sample duration')
        ]

## stsc
@AtomType.define
class SampleToChunkBox(EntriesAtom):
    '''Sample-to-chunk atom'''
    type = b'stsc'
    class Entry(pstruct.type):
        _fields_ = [
            (pQTInt, 'First chunk'),
            (pQTInt, 'Samples per chunk'),
            (pQTInt, 'Sample description ID')
        ]

## stss
@AtomType.define
class SyncSampleBox(EntriesAtom):
    type = b'stss'
    class Entry(pQTInt):
        pass

## stsz
@AtomType.define
class SampleSizeBox(EntriesAtom):
    '''Sample size atom'''
    type = b'stsz'
    class Entry(pQTInt):
        pass
    class Header(pstruct.type):
        _fields_ = [
            (pQTInt, 'Sample size'),
        ]

## stco
@AtomType.define
class ChunkOffsetBox(EntriesAtom):
    '''32-bit Chunk offset atom'''
    type = b'stco'
    class Entry(dyn.pointer(ptype.undefined, pQTInt)):
        pass

@AtomType.define
class ChunkLargeOffsetBox(EntriesAtom):
    '''64-bit Chunk offset atom'''
    type = b'co64'
    class Entry(dyn.pointer(ptype.undefined, pQTInt64)):
        pass

# XXX: this doesn't exist (?)
@AtomType.define
class ShadowSyncSampleBox(EntriesAtom):
    '''Shadow sync atom'''
    type = b'stsh'
    class Entry(pQTInt):
        pass

@AtomType.define
class BaseMediaInformationAtom(FullBox):
    '''Base media info atom'''
    type = b'gmin'
    class Box(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Graphics mode'),
            (dyn.array(pint.uint16_t,3), 'Opcolor'),
            (pint.uint16_t, 'Balance'),
            (pint.uint16_t, 'Reserved'),
        ]

@AtomType.define
class DataReferenceBox(EntriesAtom):
    '''Chunk offset atom'''
    type = b'dref'
    class Entry(Atom):
        pass
