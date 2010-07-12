from ptypes import *

### sort of based on http://www.martinreddy.net/gfx/2d/IFF.txt
class UBYTE(pint.uint8_t): pass
class WORD(pint.int16_t): pass
class UWORD(pint.uint16_t): pass
class LONG(pint.bigendian(pint.int32_t)): pass

class ID( dyn.block(4) ): pass

### yay
class Chunk_Type(object): pass
class Chunk(pstruct.type):
    def ckExtra(self):
        expectedsize = int(self['ckSize'])
        if expectedsize & 1:
            expectedsize += 1
        realsize = self['ckData'].size()
        return dyn.block( expectedsize - realsize )

    def ckData(self):
        t = self['ckID'].l.serialize()
        try:
            return Riff_Header_Lookup[t]
        except KeyError:
            pass
        return dyn.block( int(self['ckSize'].l) )

    def size(self):
        size = int(self['ckSize']) + 8
        if size & 1:
            size += 1
        return size

    _fields_ = [
        (ID, 'ckID'),
        (LONG, 'ckSize'),
        (ckData, 'ckData'),
        (ckExtra, 'ckExtra'),
    ]

class ChunkList(parray.infinite):
    _object_ = Chunk

###
class File(pstruct.type):
    def __Data(self):
        return dyn.block( int(self['Size'].l) - 4 )

    _fields_ = [
        (ID, 'ID'),
        (LONG, 'Size'),
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
    import sys
    sys.path.append('f:/work/syringe/lib')
    sys.path.append('f:/work/syringe/template')

    import ptypes,director; reload(director)
    ptypes.setsource( ptypes.provider.file('./sample.dir', mode='r') )

    z = director.File()
    self = z.load()['Data'].cast(director.ChunkList)

    print 'Number of Records:', len(self)
