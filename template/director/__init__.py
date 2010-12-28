from ptypes import *

### sort of based on http://www.martinreddy.net/gfx/2d/IFF.txt
class UBYTE(pint.uint8_t): pass
class WORD(pint.int16_t): pass
class UWORD(pint.uint16_t): pass
class LONG(pint.int32_t): pass
#class LONG(pint.bigendian(pint.int32_t)): pass

class ID( dyn.block(4) ): pass

### yay
class Chunk_Type(object): pass
class Chunk(pstruct.type):
    def __ckExtra(self):
        expectedsize = self.blocksize() - 8
        realsize = self['ckData'].blocksize()
        return dyn.block( expectedsize - realsize )

    def __ckData(self):
        t = self['ckID'].l.serialize()
        try:
            return Record.Lookup(t)
        except KeyError:
            pass

        res = dyn.clone( Record.Unknown, blocksize=lambda s:int(self['ckSize'].l) )
        res.type = t
        return res

    def blocksize(self):
        size = int(self['ckSize']) + 8
        if size & 1:
            size += 1
        return size

    def __ckSize(self):
        p = list(self.walk())[-1]   # yea, so we're slow. so what.

        if p['ID'].l.serialize() == 'XFIR':
            return LONG
        return pint.bigendian(LONG)

    _fields_ = [
        (ID, 'ckID'),
        (__ckSize, 'ckSize'),
        (__ckData, 'ckData'),
        (__ckExtra, 'ckExtra'),
    ]

class ChunkList(parray.block):
    _object_ = Chunk

    def __repr__(self):
        ele = [ x['ckID'].serialize() for x in self.v ]
        return ' '.join([ self.name(), '[%x]'% len(ele), ','.join(('%s'%x for x in ele))])

###
class File(pstruct.type):
    def __Data(self):
        l = int(self['Size'].l)
        return dyn.clone(ChunkList, blocksize=lambda s: l)

    def __Size(self):
        if self['ID'].l.serialize() == 'XFIR':
            return LONG
        return pint.bigendian(LONG)

    _fields_ = [
        (ID, 'ID'),
        (__Size, 'Size'),
        (ID, 'Format'),
        (__Data, 'Data'),
    ]

    def __repr__(self):
        name = self.name()
        id,format = self['ID'], self['Format']

        self = self['Data']
        ele = [ x['ckID'].serialize() for x in self.v ]
        return ' '.join([ name, 'ID=%s,Format=%s'% (id.serialize(), format.serialize()), '[%x]'% len(ele), ','.join(('%s'%x for x in ele))])

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

### records
if False:
    @Record.Define
    class pami(pstruct.type):
        pass

if __name__ == '__main__':
    import ptypes,director; reload(director)
    ptypes.setsource( ptypes.provider.file('./sample.dir', mode='r') )

    z = director.File()
    z = z.load()

    print 'Number of Records:', len(z['Data'])

    a = z['Data']
