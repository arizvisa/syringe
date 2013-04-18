from ptypes import *

####333
class ChunkUnknown(dyn.block(0)):
    type = None
    def __repr__(self):
        if self.initialized:
            return self.name()
        return super(ChunkUnknown, self).__repr__()

    def shortname(self):
        s = super(ChunkUnknown, self).shortname()
        names = s.split('.')
        names[-1] = '%s<%s>[size:0x%x]'%(names[-1], self.type, self.blocksize())
        return '.'.join(names)

if False:
    class ChunkHeader(pstruct.type):
        class __verinstance(pbinary.struct):
            _fields_=[(12,'instance'),(4,'ver')]
        __verinstance = pbinary.littleendian(__verinstance)

        _fields_ = [
            (__verinstance, 'ver/inst'),
            (pint.littleendian(pint.uint16_t), 'type'),
            (pint.littleendian(pint.uint32_t), 'length')
        ]

        def __repr__(self):
            if self.initialized:
                v = self['ver/inst'].number()
                t = int(self['type'])
                l = int(self['length'])
                return '%s ver/inst=%04x type=0x%04x length=0x%08x'% (self.name(), v,t,l)
            return super(ChunkHeader, self).__repr__()

if False:
    class Chunk(object):
        cache = {}
        @classmethod
        def Lookup(cls, type):
            return cls.cache[type]

        @classmethod
        def Define(cls, pt):
            t = pt.type
            cls.cache[t] = pt
            return pt

class Chunk(ptype.definition):
    cache = {}
    unknown = ChunkUnknown

######
class signature(dyn.block(8)):
    valid = property(fget=lambda s: s.serialize() == map(chr,(137,80,78,71,13,10,26,10)))

class chunk(pstruct.type):
    def __data(self):
        s = self['length'].l.int()
        t = self['type'].l.serialize()
        try:
            result = Chunk.Lookup(t)
        except KeyError:
            result = dyn.block(s)
        return result

    def __data(self):
        id = self['type'].l.serialize()
        length = self['length'].l.int()
        result = Chunk.get(id, length=length)
        return dyn.clone(result, blocksize=lambda s:length)

    _fields_ = [
        (pint.bigendian(pint.uint32_t), 'length'),
        (dyn.block(4), 'type'),
        (__data, 'data'),
        (pint.uint32_t, 'crc'),
    ]

class File(pstruct.type):
    class chunks(parray.terminated):
        _object_ = chunk
        def isTerminator(self, value):
            return value['data'].type == IEND.type

        def shortname(self):
            return 'dyn.array(chunk,%d)'% len(self)

        def summary(self):
            return repr(self.serialize()[:20])+'...'

    _fields_ = [
        (signature, 'signature'),
        (chunks, 'data'),
    ]

    def summary(self):
        data = self['data']
        return '\n'.join(( repr(self['signature']), '[%x] %s data %s...'%(data.getoffset(),data.name(), repr(data.serialize()[:20]))))

@Chunk.define
class IHDR(pstruct.type):
    type = 'IHDR'

    _fields_ = [
        (pint.uint32_t, 'Width'),
        (pint.uint32_t, 'Height'),
        (pint.uint8_t, 'Bit depth'),
        (pint.uint8_t, 'Colour type'),
        (pint.uint8_t, 'Compression method'),
        (pint.uint8_t, 'Filter method'),
        (pint.uint8_t, 'Interlace method'),
    ]

@Chunk.define
class PLTE(parray.block):
    type = 'PLTE'
    class entry(pstruct.type):
        _fields_ = [(pint.uint8_t,x) for x in 'rgb']
    _object_ = entry

@Chunk.define
class IEND(ptype.empty):
    type = 'IEND'

if __name__ == '__main__':
    import ptypes,png
    ptypes.setsource(ptypes.file('Chimera_Laboratory.png'))
    a = png.File()
    a = a.l
