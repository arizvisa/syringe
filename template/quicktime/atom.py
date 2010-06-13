from primitives import *

def blockread(ptype, length):
    class cls(ptype):
        def deserialize(self, iterable):
            input = ''.join([ x for i,x in zip(range(length), iterable)])
            super(cls, self).deserialize(input)

    cls.__name__ = 'blockread(%s, %d)'% (ptype.__name__, length)
    return cls

### main atom structures
class AtomType(object): pass
class Atom(pStruct):

    def slacker(self):
        x = self['size'] - self['data'].size()
        return dyn.block(x)()

    def atom(self):
        print self['type']
        return AtomAuto.new(self['type'], self['size'])

    _fields_ = [
        (pQTInt, 'size'),
        (pQTType, 'type'),
        (atom, 'data'),
#        (slacker, 'slack')
    ]

class AtomList(pInfiniteArray):
    _object_ = Atom

    def lookup(self, type):
        res = [x for x in self if x['type'] == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

class AtomAuto(pStruct):
    type = None

    @classmethod
    def find(cls, atomType):
        res = []
        for k,v in globals().items():
            if type(v) == type and v is not AtomType and issubclass(v, AtomType):
                if atomType == v.type:
                    return v
        class unkunkunk(Unknown):
            type = atomType

        unkunkunk.__name__ = 'Unknown<%s>'% repr(atomType.serialize())
        return unkunkunk

    @classmethod
    def new(cls, type, length):
        atom = cls.find(type)
        size = length - 8

        assert size >= 0, 'size %d <= 0'% size

        class _atom(atom):
            pass
        _atom.__name__ = atom.__name__
    
        _atom = blockread(_atom, size)
        return _atom()
        
    def __repr__(self):
        return '[\n%s]'% utils.hexdump(self.serialize(), offset=self.offset)

### list of atoms
class Unknown(pType):
    type = None

## container atoms
class MOOV(AtomList, AtomType): type = 'moov'
class TRAK(AtomList, AtomType): type = 'trak'
class EDTS(AtomList, AtomType): type = 'edts'
class MDIA(AtomList, AtomType): type = 'mdia'
class MINF(AtomList, AtomType): type = 'minf'
class DINF(AtomList, AtomType): type = 'dinf'
class MDAT(AtomList, AtomType): type = 'mdat'
class UDTA(AtomList, AtomType): type = 'udta'
class STBL(AtomList, AtomType): type = 'stbl'
class GMHD(AtomList, AtomType): type = 'gmhd'

## empty atoms
class WIDE(pType, AtomType): type = 'wide'

## WLOC
class WLOC(pStruct, AtomType):
    type = 'WLOC'
    _fields_ = [
        (pWord, 'X'),
        (pWord, 'Y')
    ]

## ftyp
class FileType(pStruct, AtomType):
    type = 'ftyp'
    _fields_ = [
        (pQTInt, 'Major_Brand'),
        (pQTInt, 'Minor_Version'),
        (pQTIntArray, 'Compatible_Brands')
    ]

class MVHD(pStruct, AtomType):
    type = 'mvhd'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pDword, 'Creation time'),
        (pDword, 'Modification time'),
        (pDword, 'Time scale'),
        (pDword, 'Duration'),
        (pDword, 'Preferred rate'),
        (pWord, 'Preferred volume'),
        (dyn.block(10), 'Reserved'),
        (dyn.block(36), 'Matrix structure'),
        (pDword, 'Preview time'),
        (pDword, 'Preview duration'),
        (pDword, 'Poster time'),
        (pDword, 'Selection time'),
        (pDword, 'Selection duration'),
        (pDword, 'Current time'),
        (pDword, 'Next track ID'),
    ]

class TKHD(pStruct, AtomType):
    type = 'tkhd'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pDword, 'Creation time'),
        (pDword, 'Modification time'),
        (pDword, 'Track ID'),
        (pDword, 'Reserved'),
        (time, 'Duration'),
        (pQword, 'Reserved'),
        (pWord, 'Layer'),
        (pWord, 'Alternate group'),
        (pWord, 'Volume'),
        (pWord, 'Reserved'),
        (dyn.block(36), 'Matrix structure'),
        (pDword, 'Track width'),
        (pDword, 'Track height'),
    ]

class ELST(pStruct, AtomType):
    type = 'elst'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pDword, 'Number of entries'),
        (lambda self: dyn.array(pDword, self['Number of entries'])(), 'Entry')
    ]

class MDHD(pStruct, AtomType):
    type = 'mdhd'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pDword, 'Creation time'),
        (pDword, 'Modification time'),
        (pDword, 'Time scale'),
        (pDword, 'Duration'),
        (pWord, 'Language'),
        (pWord, 'Quality')
    ]

class HDLR(pStruct, AtomType):
    type = 'hdlr'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pDword, 'Component type'),
        (pDword, 'Component subtype'),
        (pDword, 'Component manufacturer'),
        (pDword, 'Component flags'),
        (pDword, 'Component Flags mask'),
    ]

## stsd
if False:
    class MediaVideo(pStruct, AtomType):   #XXX: might need to be renamed
        _fields_ = [
            (pWord, 'Version'),
            (pWord, 'Revision level'),
            (pQTType, 'Vendor'),
            (pQTInt, 'Temporal Quality'),
            (pQTInt, 'Spatial Quality'),
            (pWord, 'Width'),
            (pWord, 'Height'),
            (pQTInt, 'Horizontal Resolution'),
            (pQTInt, 'Vertical Resolution'),
            (pQTInt, 'Data size'),
            (pWord, 'Frame count'),
            (dyn.block(32), 'Compressor Name'),
            (pWord, 'Depth'),
            (pWord, 'Color table ID')
        ]

class stsd_entry(pStruct):
    _fields_ = [
        (pQTInt, 'Sample description size'),
        (pQTType, 'Data format'),
        (dyn.block(6), 'Reserved'),
        (pWord, 'Data reference index')
    ]

class stsd(pStruct, AtomType):
    '''Sample description atom'''
    type = 'stsd'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of Entries'),
        (lambda x: dyn.array(stsd_entry, x['Number of Entries'])(), 'Entries')
    ]

### stts
class stts_entry(pStruct):
    _fields_ = [
        (pQTInt, 'Sample count'),
        (pQTInt, 'Sample duration')
    ]

class stts(pStruct, AtomType):
    '''Time-to-sample atom'''
    type = 'stts'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(stts_entry, x['Number of entries'])(), 'Entries')
    ]

if False:
    class stss(pStruct, AtomType):
        '''Sync Sample Atom'''
        _fields_ = [
            (pByte, 'Version'),
            (dyn.block(3), 'Flags'),
            (pQTInt, 'Number of entries'),
            (lambda x: dyn.array(pQTInt, x['Number of entries'])(), 'Entries')
        ]

## stsc
class stsc_entry(pStruct):
    _fields_ = [
        (pQTInt, 'First chunk'),
        (pQTInt, 'Samples per chunk'),
        (pQTInt, 'Sample description ID')
    ]

class stsc(pStruct, AtomType):
    '''Sample-to-chunk atom'''
    type = 'stsc'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(stsc_entry, x['Number of entries'])(), 'Entries')
    ]

## stsz
class stsz(pStruct, AtomType):
    '''Sample size atom'''
    type = 'stsz'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Sample size'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(pQTInt, x['Number of entries'])(), 'Entries')
    ]

## stco
class stco(pStruct, AtomType):
    '''Chunk offset atom'''
    type = 'stco'
    _fields_ = [
        (pByte, 'Version'),
        (dyn.block(3), 'Flags'),
        (pQTInt, 'Number of entries'),
        (lambda x: dyn.array(pQTInt, x['Number of entries'])(), 'Entries')
    ]

if False:
    # XXX: this doesn't exist (?)
    class stsh(pStruct, AtomType):
        '''Shadow sync atom'''
        _fields_ = [
            (pByte, 'Version'),
            (dyn.block(3), 'Flags'),
            (pQTInt, 'Number of entries'),
            (lambda x: dyn.array(pQTInt, x['Number of entries'])(), 'Entries')
        ]

