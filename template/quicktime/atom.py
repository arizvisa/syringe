from primitives import *

### for searching and creating atoms out of our defined
def newAtom(atomType, atomLength):
    res = []
    for k,v in globals().items():
        if type(v) == type and v is not AtomType and issubclass(v, AtomType):
            if atomType == v.type:
                return dyn.clone(v, blocksize=lambda s:atomLength)
            pass
        continue

    class unkunkunk(Unknown):
        type = atomType
        length = atomLength

    unkunkunk.__name__ = 'Unknown<%s>'% repr(atomType.serialize())
    return unkunkunk

### main atom structures
class AtomType(object): pass
class Atom(pstruct.type):
    def __data(self):
        t = self['type'].l

        try:
            self.getparent(MDAT)

        except ValueError:
            return newAtom(t, self.blocksize() - self.getheadersize())

        class unk(Unknown): pass

        unk.type = t
        unk.__name__ = 'Unknown<%s>'% repr(t.serialize())
        unk.length = self.blocksize() - self.getheadersize()
        return unk

    def __extended_size(self):
        s = int(self['size'].l)
        if s == 1:
            return pint.uint64_t
        return dyn.clone(pint.uint_t, length=0)

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

    def __slack(self):
        t,s = (self['type'].l, self.getsize())
        s = self.getsize() - self.getheadersize()
        datasize = self['data'].size()

        if self.parent is not None:
            if s >= datasize:
                return dyn.block(s - datasize)

            container = self.parent.parent
            print 'miscalculated slack:',hex(s),'<',hex(datasize)
            path = self.traverse(lambda n: n.parent)
            path = [ 'type:%s name:%s offset:%x size:%x'%(x.name(), getattr(x, '__name__', repr(None.__class__)), x.getoffset(), x.size()) for x in path ]
            path = ' ->\n\t'.join(reversed(path))
            print path
        return dyn.block(0)

    def blocksize(self):
        return self.getsize()

    _fields_ = [
        (pQTInt, 'size'),
        (pQTType, 'type'),
        (__extended_size, 'extended_size'),
        (__data, 'data'),
        (__slack, 'slack')
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

### list of atoms
class Unknown(dyn.block(0)):
    type = None

## container atoms
class MOOV(AtomList, AtomType): type = 'moov'
class TRAK(AtomList, AtomType): type = 'trak'
class EDTS(AtomList, AtomType): type = 'edts'
class MDIA(AtomList, AtomType): type = 'mdia'
class MINF(AtomList, AtomType): type = 'minf'
class DINF(AtomList, AtomType): type = 'dinf'
#class UDTA(AtomList, AtomType): type = 'udta'
class STBL(AtomList, AtomType): type = 'stbl'
class GMHD(AtomList, AtomType): type = 'gmhd'
#class MDAT(AtomList, AtomType): type = 'mdat'  # XXX: sometimes this is not a container
class MDAT(dyn.block(0), AtomType):
    type = 'mdat'
    length = property(fget=lambda s: s.blocksize())

## empty atoms
class WIDE(ptype.type, AtomType): type = 'wide'

## WLOC
class WLOC(pstruct.type, AtomType):
    type = 'WLOC'
    _fields_ = [
        (pint.uint16_t, 'X'),
        (pint.uint16_t, 'Y')
    ]

## ftyp
class FileType(pstruct.type, AtomType):
    type = 'ftyp'
    _fields_ = [
        (pQTInt, 'Major_Brand'),
        (pQTInt, 'Minor_Version'),
        (lambda s: dyn.clone(pQTIntArray,blocksize=lambda s: s.parent.blocksize()-8), 'Compatible_Brands')      # XXX: this isn't working
    ]

class MVHD(pstruct.type, AtomType):
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

class TKHD(pstruct.type, AtomType):
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

class ELST(pstruct.type, AtomType):
    type = 'elst'

    def __Entry(self):
        count = self['Number of entries'].l
        return dyn.array(pint.uint32_t, int(count))

    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (__Entry, 'Entry')
    ]

class MDHD(pstruct.type, AtomType):
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

class HDLR(pstruct.type, AtomType):
    type = 'hdlr'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pint.uint32_t, 'Component type'),
        (pint.uint32_t, 'Component subtype'),
        (pint.uint32_t, 'Component manufacturer'),
        (pint.uint32_t, 'Component flags'),
        (pint.uint32_t, 'Component Flags mask'),
    ]

## stsd
if False:
    class MediaVideo(pstruct.type, AtomType):   #XXX: might need to be renamed
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

class stsd_entry(pstruct.type):
    _fields_ = [
        (pQTInt, 'Sample description size'),
        (pQTType, 'Data format'),
        (dyn.block(6), 'Reserved'),
        (pint.uint16_t, 'Data reference index')
    ]

class stsd(pstruct.type, AtomType):
    '''Sample description atom'''
    type = 'stsd'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of Entries'),
        (lambda x: dyn.array(stsd_entry, int(x['Number of Entries'].l)), 'Entries')
    ]

### stts
class stts_entry(pstruct.type):
    _fields_ = [
        (pQTInt, 'Sample count'),
        (pQTInt, 'Sample duration')
    ]

class stts(pstruct.type, AtomType):
    '''Time-to-sample atom'''
    type = 'stts'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(stts_entry, int(x['Number of entries'].l)), 'Entries')
    ]

if False:
    class stss(pstruct.type, AtomType):
        '''Sync Sample Atom'''
        _fields_ = [
            (pint.uint8_t, 'Version'),
            (dyn.block(3), 'Flags'),
            (pQTInt, 'Number of entries'),
            (lambda x: dyn.array(pQTInt, int(x['Number of entries'].l)), 'Entries')
        ]

## stsc
class stsc_entry(pstruct.type):
    _fields_ = [
        (pQTInt, 'First chunk'),
        (pQTInt, 'Samples per chunk'),
        (pQTInt, 'Sample description ID')
    ]

class stsc(pstruct.type, AtomType):
    '''Sample-to-chunk atom'''
    type = 'stsc'
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(stsc_entry, int(x['Number of entries'].l)), 'Entries')
    ]

## stsz
class stsz(pstruct.type, AtomType):
    '''Sample size atom'''
    type = 'stsz'

    def __Entries(self):
        count = int(self['Number of entries'].l)
        return dyn.array(pQTInt, count)
        
    _fields_ = [
        (pint.uint8_t, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Sample size'),
        (pQTInt, 'Number of entries'),
        (__Entries, 'Entries'),
    ]

## stco
class stco(pstruct.type, AtomType):
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
    class stsh(pstruct.type, AtomType):
        '''Shadow sync atom'''
        _fields_ = [
            (pint.uint8_t, 'Version'),
            (dyn.block(3), 'Flags'),
            (pQTInt, 'Number of entries'),
            (lambda x: dyn.array(pQTInt, int(x['Number of entries'].l)), 'Entries')
        ]

