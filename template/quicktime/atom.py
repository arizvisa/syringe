from primitives import *

class AtomType(ptype.definition):
    cache = {}

class Atom(pstruct.type):
    def __data(self):
        type = self['type'].li.serialize()
        size = self.blocksize() - self.getheadersize()
        t = AtomType.get(type, __name__='Unknown<%s>'% repr(type), length=size)
        return dyn.clone(t, blocksize=lambda s:size)

    def getheadersize(self):
        return 4 + 4 + self['extended_size'].li.size()

    def getsize(self):
        s = self['size'].li.int()
        if s == 1:
            s = self['extended_size'].li.int()

        if s >= self.getheadersize():
            return s

        container = self.parent.parent
        if s == 0:
            if container is None:
                return self.source.size() - (self.getoffset())

            position = self.getoffset() - container.getoffset()
            return container.getsize() - position

        raise NotImplementedError(repr(self['type']),repr(s))

    def blocksize(self):
        return self.getsize()

    _fields_ = [
        (pQTInt, 'size'),
        (pQTType, 'type'),
        (lambda s: pint.uint64_t if s['size'].li.int() == 1 else pint.uint_t, 'extended_size'),
        (__data, 'data'),
    ]

    def summary(self):
        if not self.initialized and self.v is None:
            return "[%x] %s UNINITIALIZED expected:0x%x keys:(%s)"%( self.getoffset(), self.name(), 0, ','.join(self.keys()))
        discrepancy = self.size() != self.blocksize()
        if discrepancy:
            return "%r ERR size:0x%x expected:0x%x keys:(%s)"%( self['type'].serialize(), self.size(), self.getsize(), ','.join(self.keys()))
        return "%r size:0x%x (%s)"%( self['type'].serialize(), self.getsize(), ','.join(self.keys()))

class AtomList(parray.block):
    _object_ = Atom

    def search(self, type):
        '''Search through a list of atoms for a particular fourcc type'''
        return (x for x in self if x['type'] == type)

    def lookup(self, type):
        '''Return the first instance of specified atom type'''
        res = [x for x in self if x['type'] == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

    def summary(self):
        types = ','.join([x['type'].serialize() for x in self])
        return ' '.join(['atoms[%d] ->'% len(self), types])

## container atoms
@AtomType.define
class MOOV(AtomList): type = 'moov'

@AtomType.define
class TRAK(AtomList): type = 'trak'

@AtomType.define
class EDTS(AtomList): type = 'edts'

@AtomType.define
class MDIA(AtomList): type = 'mdia'

@AtomType.define
class MINF(AtomList): type = 'minf'

@AtomType.define
class DINF(AtomList): type = 'dinf'

@AtomType.define
class UDTA(Atom): type = 'udta'

@AtomType.define
class STBL(AtomList): type = 'stbl'

@AtomType.define
class GMHD(AtomList): type = 'gmhd'

@AtomType.define
class META(AtomList): type = 'meta'

@AtomType.define
class RMRA(AtomList): type = 'rmra'

@AtomType.define
class RMRA(AtomList): type = 'rmda'

#@AtomType.define
#class MDAT(AtomList): type = 'mdat'  # XXX: sometimes this is not a container

@AtomType.define
class MDAT(ptype.block):
    type = 'mdat'
    length = property(fget=lambda s: s.blocksize())

## empty atoms
@AtomType.define
class WIDE(pstruct.type):
    type = 'wide'
    _fields_ = []

## WLOC
@AtomType.define
class WLOC(pstruct.type):
    type = 'WLOC'
    _fields_ = [
        (pint.uint16_t, 'X'),
        (pint.uint16_t, 'Y')
    ]

## ftyp
@AtomType.define
class FileType(pstruct.type):
    type = 'ftyp'
    class __Compatible_Brands(parray.block):
        _object_ = pQTInt
        def blocksize(self):
            p = self.getparent(Atom)
            return p.blocksize() - p.getheadersize() - 8
        
    _fields_ = [
        (pQTInt, 'Major_Brand'),
        (pQTInt, 'Minor_Version'),
        (__Compatible_Brands, 'Compatible_Brands')
    ]

@AtomType.define
class MVHD(pstruct.type):
    type = 'mvhd'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
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
class TKHD(pstruct.type):
    type = 'tkhd'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
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
        (pint.uint32_t, 'Track width'),
        (pint.uint32_t, 'Track height'),
    ]

@AtomType.define
class ELST(pstruct.type):
    type = 'elst'

    class Entry(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'duration'),
            (pint.uint32_t, 'time'),
            (pint.uint32_t, 'rate'),
        ]

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda s: dyn.array(s.Entry, s['Number of entries'].li.int()), 'Entry')
    ]

@AtomType.define
class MDHD(pstruct.type):
    type = 'mdhd'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pint.uint32_t, 'Creation time'),
        (pint.uint32_t, 'Modification time'),
        (pint.uint32_t, 'Time scale'),
        (pint.uint32_t, 'Duration'),
        (pint.uint16_t, 'Language'),
        (pint.uint16_t, 'Quality')
    ]

@AtomType.define
class HDLR(pstruct.type):
    type = 'hdlr'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pint.uint32_t, 'Component type'),
        (pint.uint32_t, 'Component subtype'),
        (pint.uint32_t, 'Component manufacturer'),
        (pint.uint32_t, 'Component flags'),
        (pint.uint32_t, 'Component Flags mask'),
        (pQTString, 'Component name')
    ]

## stsd
#@MediaType.Define
class MediaVideo(pstruct.type):   #XXX: might need to be renamed
    type = 'vide'
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
        (pQTInt, 'Data size'),
        (pint.uint16_t, 'Frame count'),
        (dyn.block(32), 'Compressor Name'),
        (pint.uint16_t, 'Depth'),
        (pint.uint16_t, 'Color table ID')
    ]

# FIXME: this isn't decoding mpeg audio yet.
class esds(pstruct.type):
    type = 'esds'
    _fields_ = [
        (pint.uint32_t, 'Version'),
        (ptype.type, 'Elementary Stream Descriptor'),
    ]

#@MediaType.Define
class MediaAudio_v0(pstruct.type):
    type = 'soun'
    version = 0
    _fields_ = [
        (pint.uint16_t, 'Version'),
        (pint.uint16_t, 'Revision level'),
        (pQTType, 'Vendor'),
        (pint.uint16_t, 'Number of channels'),
        (pint.uint16_t, 'Sample size'),
        (pint.uint16_t, 'Compression ID'),
        (pint.uint16_t, 'Packet size'),
        (pint.uint32_t, 'Sample rate'),
    ]
#@MediaType.Define
class MediaAudio_v1(pstruct.type):
    type = 'soun'
    version = 1
    _fields_ = [
        (pint.uint16_t, 'Version'),
        (pint.uint16_t, 'Revision level'),
        (pQTType, 'Vendor'),
        (pint.uint16_t, 'Number of channels'),
        (pint.uint16_t, 'Sample size'),
        (pint.uint16_t, 'Compression ID'),
        (pint.uint16_t, 'Packet size'),
        (pint.uint32_t, 'Sample rate'),
        (pint.uint32_t, 'Samples per packet'),
        (pint.uint32_t, 'Bytes per packet'),
        (pint.uint32_t, 'Bytes per frame'),
        (pint.uint32_t, 'Bytes per sample'),
    ]

@AtomType.define
class stsd(pstruct.type):
    '''Sample description atom'''
    type = 'stsd'
    class entry(pstruct.type):
        def __Data_specific(self):
            sz = self['Sample description size'].li.num()
            return dyn.block(sz - 4 - 4 - 6 - 2)
        _fields_ = [
            (pQTInt, 'Sample description size'),
            (pQTType, 'Data format'),
            (dyn.block(6), 'Reserved'),
            (pint.uint16_t, 'Data reference index'),
            (__Data_specific, 'Data specific'),
        ]

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of Entries'),
        (lambda x: dyn.array(stsd.entry, x['Number of Entries'].li.int()), 'Entries'),
    ]

### stts
@AtomType.define
class stts(pstruct.type):
    '''Time-to-sample atom'''
    type = 'stts'
    class entry(pstruct.type):
        _fields_ = [
            (pQTInt, 'Sample count'),
            (pQTInt, 'Sample duration')
        ]

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(stts.entry, x['Number of entries'].li.int()), 'Entries')
    ]

## stsc
@AtomType.define
class stsc(pstruct.type):
    '''Sample-to-chunk atom'''
    type = 'stsc'
    class entry(pstruct.type):
        _fields_ = [
            (pQTInt, 'First chunk'),
            (pQTInt, 'Samples per chunk'),
            (pQTInt, 'Sample description ID')
        ]

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda s: dyn.array(s.entry, s['Number of entries'].li.int()), 'Entries')
    ]

## stsz
@AtomType.define
class stsz(pstruct.type):
    '''Sample size atom'''
    type = 'stsz'

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Sample size'),
        (pQTInt, 'Number of entries'),
        (lambda s: dyn.array(pQTInt, s['Number of entries'].li.int()), 'Entries'),
    ]

## stco
@AtomType.define
class stco(pstruct.type):
    '''Chunk offset atom'''
    type = 'stco'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(pQTInt, x['Number of entries'].li.int()), 'Entries')
    ]

# XXX: this doesn't exist (?)
@AtomType.define
class stsh(pstruct.type):
    '''Shadow sync atom'''
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(pQTInt, x['Number of entries'].li.int()), 'Entries')
    ]

@AtomType.define
class gmin(pstruct.type):
    '''Base media info atom'''
    type = 'gmin'

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pint.uint16_t, 'Graphics mode'),
        (dyn.array(pint.uint16_t,3), 'Opcolor'),
        (pint.uint16_t, 'Balance'),
        (pint.uint16_t, 'Reserved'),
    ]

@AtomType.define
class dref(pstruct.type):
    '''Chunk offset atom'''
    type = 'dref'

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda s: dyn.array(Atom, s['Number of entries'].li.int()), 'Data references')
    ]
