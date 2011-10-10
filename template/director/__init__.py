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

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if self.initialized:
            res = repr(self.str())
        else:
            res = '???'
        name = [lambda:'__name__:%s'%self.__name__, lambda:''][self.__name__ is None]()
        return  ' '.join([ofs, self.name(), name, res])

class HEX(pint.integer_t):
    def __int__(self):
        return int(self.serialize(),16)

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
        size = int(self['ckSize'].l)
        return Record.Generate(self['ckID'].l.str(), blocksize=lambda s:size)

    def ckSize(self):
        return self.endian(LONG)

    _fields_ = [
        (ID, 'ckID'),
        (ckSize, 'ckSize'),
#        (ckData, 'ckData'),
        (lambda self: Record.Generate(self['ckID'].l.str(), blocksize=lambda s:int(self['ckSize'])), 'ckData'),
        (ckExtra, 'ckExtra'),
    ]

class ChunkList(parray.block):
    _object_ = Chunk

    def __repr__(self):
        ele = [ x['ckID'].serialize() for x in self.v ]
        return ' '.join([ self.name(), '[%x]'% len(ele), ','.join(('%s'%x for x in ele))])

### record definition class
class Record(object):
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

    class Unknown(dyn.block(0)):
        length=property(fget=lambda s:s.blocksize())
        shortname=lambda s: 'Unknown{%x}<%s>'% (s.length, s.type)

    @classmethod
    def Generate(cls, t, **attrs):
        try:
            return dyn.clone( cls.Lookup(t), **attrs )
        except KeyError:
            pass

        res = dyn.clone(cls.Unknown, **attrs)
        res.type = t
        return res

###
class File(pstruct.type):
    def __Size(self):
        byteorder = pint.bigendian
        if self['Type'].l.serialize() == 'XFIR':
            byteorder = pint.littleendian

        self.attrs['endian'] = byteorder    # FIXME: i should probably do this in the respective header for RIFX or XFIR
        return byteorder(pint.uint32_t)

    def __Data(self):
        type = self['Type'].l.serialize()
        size = int(self['Size'].l)
        return Record.Generate(type, blocksize=lambda s:size)

    _fields_ = [
        (dyn.block(4), 'Type'),
        (__Size, 'Size'),
        (lambda self: Record.Generate(self['Type'].l.serialize(), blocksize=lambda s:int(self['Size'].l)), 'Data'),
#        (__Data, 'Data'),
    ]

@Record.Define
class RIFX(pstruct.type):
    type = 'RIFX'
    def __Data(self):
        l = int(self.blocksize() - self['Format'].l.size())
        return dyn.clone(ChunkList, blocksize=lambda s: l)

    _fields_ = [
        (ID, 'Format'),
        (__Data, 'Elements'),
    ]

@Record.Define
class XFIR(pstruct.type):
    type = 'XFIR'
    def __Data(self):
        l = int(self.blocksize() - self['Format'].l.size())
        return dyn.clone(ChunkList, blocksize=lambda s: l)

    _fields_ = [
        (ID, 'Format'),
        (__Data, 'Elements'),
    ]

### records
if False:
    @Record.Define
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
        (lambda s: s.endian(dyn.pointer(Chunk, type=LONG)), 'ckOffset'),
        (ULONG, 'reservedValue1'),
        (ULONG, 'reservedValue2'),
    ]

@Record.Define
class pamm(pstruct.type):
    type = 'mmap'
    _fields_ = [
        (ChunkHeader, 'header'),
        (lambda x: dyn.array(IndexNode, int(x['header'].l['numIndexNodes'])), 'nodes'),
    ]

@Record.Define
class demx(parray.block):
    type = 'XMED'
    class chunk(pstruct.type):
        _fields_ = [
            (dyn.clone(HEX,length=4),'type'),
            (dyn.clone(HEX,length=8),'size'),
            (dyn.clone(HEX,length=8),'count'),
            (lambda s: dyn.block(int(s['size'].l)),'data')         # FIXME: add a chunktype lookup for this too
        ]
    _object_ = chunk

if __name__ == '__main__':
    import ptypes,director; reload(director)
    ptypes.setsource( ptypes.provider.file('./sample.dir', mode='r') )

    z = director.File()
    z = z.load()

    print z['Data'][1]['ckData']['header']['unknown']

    print 'Number of Records:', len(z['Data'])

    a = z['Data']
