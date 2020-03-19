from ptypes import *

### sort of based on http://www.martinreddy.net/gfx/2d/IFF.txt

# FIXME: need to make these define their endianess based on self.endian
class UBYTE(pint.uint8_t): pass
class WORD(pint.int16_t): pass
class UWORD(pint.uint16_t): pass
class LONG(pint.int32_t): pass
class ULONG(pint.uint32_t): pass

class ID(pint.uint32_t):
    def str(self):
        n = int(self)
        string = ''
        for x in range(4):
            string += chr((n&0xff000000)>>24)
            n *= 0x100
        return string

    def summary(self):
        return self.str()

class HEX(pstr.string):
    def int(self):
        return int(self.str(),16)
    __int__ = int

### yay
class Chunk_Type(object): pass
class Chunk(pstruct.type):
    def ckExtra(self):
        expectedsize = self.blocksize() - 8
        realsize = self['ckData'].blocksize()
        return dyn.block( expectedsize - realsize )

    def blocksize(self):
        size = int(self['ckSize']) + 8
        if size & 1:
            size += 1
        return size

    def ckData(self):
        res, size = self['ckID'].li.str(), self['ckSize'].li.int()
        return Record.withdefault(res, type=res, blocksize=lambda s, size=size: size)

    def ckSize(self):
        return self.endian(LONG)

    _fields_ = [
        (ID, 'ckID'),
        (ckSize, 'ckSize'),
#        (ckData, 'ckData'),
        (lambda self: Record.withdefault(self['ckID'].li.str(), type=self['ckID'].str(), blocksize=lambda s:self['ckSize'].li.int()), 'ckData'),
        (ckExtra, 'ckExtra'),
    ]

class ChunkList(parray.block):
    _object_ = Chunk

    def summary(self):
        ele = ( x['ckID'].serialize() for x in self.v )
        return ','.join(ele)

### record definition class
class Record(ptype.definition):
    cache = {}
    class unknown(ptype.block):
        def classname(self):
            return 'Unknown{%x}<%s>'% (self.length, self.type)
    default = unknown

###
class File(pstruct.type):
    def __Size(self):
        byteorder = pint.bigendian
        if self['Type'].li.serialize() == 'XFIR':
            byteorder = pint.littleendian

        self.attrs['endian'] = byteorder    # FIXME: i should probably do this in the respective header for RIFX or XFIR
        return byteorder(pint.uint32_t)

    def __Data(self):
        type = self['Type'].li.serialize()
        size = self['Size'].li.int()
        return Record.withdefault(type, type=type, blocksize=lambda s, size=size:size)

    _fields_ = [
        (dyn.block(4), 'Type'),
        (__Size, 'Size'),
        (lambda self: Record.withdefault(self['Type'].li.serialize(), type=self['Type'].serialize(), blocksize=lambda s:self['Size'].li.int()), 'Data'),
#        (__Data, 'Data'),
    ]

@Record.define
class RIFX(pstruct.type):
    type = 'RIFX'
    def __Elements(self):
        l = self.blocksize() - self['Format'].li.size()
        return dyn.clone(ChunkList, blocksize=lambda s: l)

    _fields_ = [
        (ID, 'Format'),
        (__Elements, 'Elements'),
    ]

@Record.define
class XFIR(pstruct.type):
    type = 'XFIR'
    def __Data(self):
        l = int(self.blocksize() - self['Format'].li.size())
        return dyn.clone(ChunkList, blocksize=lambda s: l)

    _fields_ = [
        (ID, 'Format'),
        (__Data, 'Elements'),
    ]

### records
if False:
    @Record.define
    class pami(pstruct.type):
        pass

class ChunkHeader(pstruct.type):
    _fields_ = [
        (UWORD, 'ckHeaderSize'),
        (UWORD, 'indexNodeSize'),
        (lambda s: s.endian(ULONG), 'numIndexNodes'),
        (ULONG, 'numNeedProcessing'),
        (ULONG, 'unknown'),
        (ULONG, 'reserved'),
        (ULONG, 'unknown'),
    ]

class IndexNode(pstruct.type):
    _fields_ = [
        (ID, 'ckID'),
        (lambda s: s.endian(ULONG), 'ckSize'),
        (lambda s: s.endian(dyn.pointer(Chunk, LONG)), 'ckOffset'),
        (ULONG, 'reservedValue1'),
        (ULONG, 'reservedValue2'),
    ]

@Record.define
class pamm(pstruct.type):
    type = 'mmap'
    _fields_ = [
        (ChunkHeader, 'header'),
        (lambda x: dyn.array(IndexNode, int(x['header'].li['numIndexNodes'])), 'nodes'),
    ]

@Record.define
class demx(parray.block):
    type = 'XMED'
    class chunk(pstruct.type):
        _fields_ = [
            (dyn.clone(HEX,length=4),'type'),
            (dyn.clone(HEX,length=8),'size'),
            (dyn.clone(HEX,length=8),'count'),
            (lambda s: dyn.block(s['size'].li.int()),'data')         # FIXME: add a chunktype lookup for this too
        ]
    _object_ = chunk

if __name__ == '__main__':
    import ptypes,director; reload(director)
    ptypes.setsource( ptypes.provider.file('./sample.dir', mode='r') )

    z = director.File()
    z = z.load()

    print(z['Data'][1]['ckData']['header']['unknown'])

    print('Number of Records:', len(z['Data']))

    a = z['Data']
