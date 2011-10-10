from primitives import *

class AtomType(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

    @classmethod
    def New(cls, type, size):
        try:
            t = cls.Lookup(type)
        except KeyError:
            t = dyn.block(size)
            t.__name__ = 'Unknown<%s>'% repr(type)
        return dyn.clone(t, blocksize=lambda s:size)        

class Atom(pstruct.type):
    def __data(self):
        t = self['type'].l.serialize()
        s = self.blocksize() - self.getheadersize()
        return AtomType.New(t, s)

    def getheadersize(self):
        return 4 + 4 + self['extended_size'].size()

    def getsize(self):
        s = int(self['size'])
        if s == 1:
            s = int(self['extended_size'])

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
        (lambda s: (ptype.empty, pint.uint64_t)[int(s['size'].l) == 1], 'extended_size'),
        (__data, 'data'),
    ]

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

    def __repr__(self):
        types = ','.join([x['type'].serialize() for x in self])
        return ' '.join([self.name(), 'atoms[%d] ->'% len(self), types])

## container atoms
@AtomType.Define
class MOOV(AtomList): type = 'moov'

@AtomType.Define
class TRAK(AtomList): type = 'trak'

@AtomType.Define
class EDTS(AtomList): type = 'edts'

@AtomType.Define
class MDIA(AtomList): type = 'mdia'

@AtomType.Define
class MINF(AtomList): type = 'minf'

@AtomType.Define
class DINF(AtomList): type = 'dinf'

#@AtomType.Define
class UDTA(Atom): type = 'udta'

@AtomType.Define
class STBL(AtomList): type = 'stbl'

@AtomType.Define
class GMHD(AtomList): type = 'gmhd'

@AtomType.Define
class META(AtomList): type = 'meta'

@AtomType.Define
class RMRA(AtomList): type = 'rmra'

@AtomType.Define
class RMRA(AtomList): type = 'rmda'

#@AtomType.Define
#class MDAT(AtomList): type = 'mdat'  # XXX: sometimes this is not a container

@AtomType.Define
class MDAT(dyn.block(0)):
    type = 'mdat'
    length = property(fget=lambda s: s.blocksize())

## empty atoms
@AtomType.Define
class WIDE(ptype.type):
    type = 'wide'
    def load(self):
        # this error is raised only because i don't quite understand how this element works
        #   does it make sense for a wide element to be a structure that contains an Atom maybe?
        print "%s(%x:+%x) 'wide' loading of 64-bit elements is unimplemented at offset 0x%x ->"%(self.shortname(), self.getoffset(), self.blocksize(), self.getoffset())
        print '\t' + '\n\t'.join(self.backtrace())
        return super(WIDE, self).load()

## WLOC
@AtomType.Define
class WLOC(pstruct.type):
    type = 'WLOC'
    _fields_ = [
        (pint.uint16_t, 'X'),
        (pint.uint16_t, 'Y')
    ]

## ftyp
@AtomType.Define
class FileType(pstruct.type):
    type = 'ftyp'
    _fields_ = [
        (pQTInt, 'Major_Brand'),
        (pQTInt, 'Minor_Version'),
        (lambda s: dyn.clone(pQTIntArray,blocksize=lambda s: s.parent.blocksize()-8), 'Compatible_Brands')      # XXX: this isn't working
    ]

@AtomType.Define
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

@AtomType.Define
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

@AtomType.Define
class ELST(pstruct.type):
    type = 'elst'

    def __Entry(self):
        count = self['Number of entries'].l
        return dyn.array(pint.uint32_t, int(count))

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
        (lambda s: dyn.array(s.Entry, int(s['Number of entries'].l)), 'Entry')
    ]

@AtomType.Define
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

@AtomType.Define
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
        (ptype.empty, 'Elementary Stream Descriptor'),
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

@AtomType.Define
class stsd(pstruct.type):
    '''Sample description atom'''
    type = 'stsd'
    class entry(pstruct.type):
        _fields_ = [
            (pQTInt, 'Sample description size'),
            (pQTType, 'Data format'),
            (dyn.block(6), 'Reserved'),
            (pint.uint16_t, 'Data reference index')
        ]

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of Entries'),
        (lambda x: dyn.array(stsd.entry, int(x['Number of Entries'].l)), 'Entries')
    ]

### stts
@AtomType.Define
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
#        (lambda x: dyn.array(stts.entry, int(x['Number of entries'].l) - 1), 'Entries')
        (lambda x: dyn.array(pQTInt, int(x['Number of entries'].l)), 'Entries')
    ]

## stsc
@AtomType.Define
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
        (lambda s: dyn.array(s.entry, int(s['Number of entries'].l)), 'Entries')
    ]

## stsz
@AtomType.Define
class stsz(pstruct.type):
    '''Sample size atom'''
    type = 'stsz'

    def __Entries(self):
        count = int(self['Number of entries'].l)
        s = self.blocksize() - self.size()
        if s <= 0:
            print '%s(%x:+%x) - blocksize(%d-%d) <= 0 while trying to read sample entry table ->'%(self.shortname(), self.getoffset(), self.blocksize(), self.blocksize(), self.size())
            print '\t' + '\n\t'.join(self.backtrace())
            return ptype.empty
        return dyn.array(pQTInt, count)
        
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Sample size'),
        (pQTInt, 'Number of entries'),
        (__Entries, 'Entries'),
    ]

## stco
@AtomType.Define
class stco(pstruct.type):
    '''Chunk offset atom'''
    type = 'stco'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(pQTInt, int(x['Number of entries'].l)), 'Entries')
    ]

if False:
    # XXX: this doesn't exist (?)
    @AtomType.Define
    class stsh(pstruct.type):
        '''Shadow sync atom'''
        _fields_ = [
            (pint.uint8_t, 'Version'),
            (dyn.block(3), 'Flags'),
            (pQTInt, 'Number of entries'),
            (lambda x: dyn.array(pQTInt, int(x['Number of entries'].l)), 'Entries')
        ]

@AtomType.Define
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

@AtomType.Define
class dref(pstruct.type):
    '''Chunk offset atom'''
    type = 'dref'

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda s: dyn.array(Atom, int(s['Number of entries'].l)), 'Data references')
    ]
