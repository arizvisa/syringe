import zlib
from tags import *
from stypes import *
pbinary.setbyteorder(pbinary.bigendian)

class Header(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string,length=3), 'Signature'),
        (UI8, 'Version'),
        (UI32, 'FileLength'),
    ]

class FrameInfo(pstruct.type):
    _fields_ = [
        (RECT, 'FrameSize'),
        (pint.bigendian(UI16), 'FrameRate'),
        (UI16, 'FrameCount')
    ]

class Data(pstruct.type):
    _fields_ = [
        (FrameInfo, 'frameinfo'),
        (TagList, 'tags')
    ]

## Encoded data types
class EncodedDataType(ptype.definition):
    cache = {}

@EncodedDataType.define
class UncompressedData(ptype.encoded_t):
    type = 'FWS'
    _value_ = ptype.block
    _object_ = Data

EncodedDataType.unknown = UncompressedData

class CompressedData(ptype.encoded_t):
    _value_ = ptype.block
    _object_ = Data

    _compress = lambda s: s
    _decompress = lambda s: s
    def encode(self, object, **attrs):
        block = object.serialize()
        compressed_block = self._compress(block)
        print '%s: compressed %x to %x bytes'%(self.__class__.__name__,len(block),len(compressed_block))
        return super(CompressedData,self).encode(ptype.block(length=len(compressed_block)).set(compressed_block))
    def decode(self, object, **attrs):
        block = object.serialize()
        decompressed_block = self._decompress(block)
        print '%s: decompressed %x to %x bytes'%(self.__class__.__name__,len(block),len(decompressed_block))
        return super(CompressedData,self).decode(ptype.block(length=len(decompressed_block)).set(decompressed_block))

@EncodedDataType.define
class ZlibData(CompressedData):
    type = 'CWS'
    _compress = zlib.compress
    _decompress = zlib.decompress

try:
    import pylzma
    @EncodedDataType.define
    class LzmaData(CompressedData):
        type = 'ZWS'
        _compress = pylzma.compress
        _decompress = pylzma.decompress

except ImportError:
    # logging.warn("swf.%s : Unable to import pylzma. lzma support not available."% __name__)
    pass

class File(pstruct.type, ptype.boundary):
    def __data(self):
        header = self['Header'].li
        sig = header['Signature'].str()

        # if it's compressed then use the 'zlib' structure
        t = EncodedDataType.get(sig)
        length = min(header['FileLength'].num(),self.source.size()) - header.size()
        return dyn.clone(t, _value_=dyn.clone(t._value_, length=length))

    _fields_ = [
        (Header, 'header'),
        (__data, 'data')
    ]

if __name__ == '__main__':
    import sys
    import ptypes,__init__ as swf
    ptypes.setsource(ptypes.file('./test.swf', mode='r'))

    z = File
#    z = ptypes.debugrecurse(z)
    z = z()
    z = z.l
    for x in z['data']['tags']:
        print '-'*32
        print x

    a = z['data']['tags'][0]
    print a.hexdump()
    print a.li.hexdump()
    print repr(a.l['Header'].serialize())

    correct='\x44\x11\x08\x00\x00\x00'
    print ptypes.utils.hexdump(correct)

    print a.serialize() == correct
