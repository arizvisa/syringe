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
            return Riff_Header_Lookup[t]
        except KeyError:
            pass
        return dyn.block( int(self['ckSize'].l) )

    def blocksize(self):
        size = int(self['ckSize']) + 8
        if size & 1:
            size += 1
        return size

    def __ckSize(self):
        p = list(self.walkparent())[-1]   # yea, so we're slow. so what.

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

###
def getparentclasslookup(parent, key):
    import inspect
    res = {}
    for cls in globals().values():
        if inspect.isclass(cls) and cls is not parent and issubclass(cls, parent):
            res[ key(cls) ] = cls
        continue
    return res

Riff_Header_Lookup = getparentclasslookup(Chunk_Type, lambda cls: (cls.id))

if __name__ == '__main__':
    import ptypes,director; reload(director)
    ptypes.setsource( ptypes.provider.file('./sample.dir', mode='r') )

    z = director.File()
    z = z.load()

    print 'Number of Records:', len(z['Data'])

    a = z['Data']
