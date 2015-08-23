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

class File(pstruct.type, ptype.boundary):
    class cdata(ptype.encoded_t):
        _object_ = Data
        def encode(self, object, **attrs):
            block = object.serialize()
            compressed_block = zlib.compress(block)
            print 'zlib: compressed %x to %x bytes'%(len(block),len(compressed_block))
            return compressed_block
        def decode(self, **attrs):
            block = self.serialize()
            decompressed_block = zlib.decompress(block)
            print 'zlib: decompressed %x to %x bytes'%(len(block),len(decompressed_block))
            attrs['source'] = ptypes.prov.string(decompressed_block)
            return super(File.cdata,self).decode(**attrs)

    class data(ptype.encoded_t):
        _object_ = Data
        def decode(self, **attrs):
            attrs['source'] = ptypes.prov.string(block)
            return super(File.data,self).decode(**attrs)
            
    def __data(self):
        # if it's compressed then use the 'cdata' structure
        header = self['Header'].li
        if header['Signature'][0].num() == ord('C'):
            length = min(header['FileLength'].num(),self.source.size()) - header.size()
            return dyn.clone(self.cdata, _value_=dyn.block(length))
        return Data
    
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
