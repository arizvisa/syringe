import zlib
from tags import *
from stypes import *
pbinary.setbyteorder(pbinary.bigendian)

class Header(pstruct.type):
    _fields_ = [
        (dyn.array(UI8,3), 'Signature'),
        (UI8, 'Version'),
        (UI32, 'FileLength'),
    ]

class FrameInfo(pstruct.type):
    _fields_ = [
        (RECT, 'FrameSize'),
        (pint.bigendian(UI16), 'FrameRate'),
        (UI16, 'FrameCount')
    ]

class File(pstruct.type):
    class cdata(pstruct.type):
        _fields_ = [
            (FrameInfo, 'frameinfo'),
            (TagList, 'tags')
        ]

        def load(self):
            self.source.seek(self.getoffset())
            block = self.source.consume(self.blocksize())

            # XXX: modify ours and our parent's source with the new decompressed file
            self.parent.source = self.source = ptypes.provider.string(self.parent['header'].serialize() + zlib.decompress(block))
            print 'zlib: decompressed %x to %x bytes'%(len(block),self.source.size())
            return super(File.cdata, self).load()

        def blocksize(self):
            raise NotImplementedError

    class data(pstruct.type):
        _fields_ = [
            (FrameInfo, 'frameinfo'),
            (TagList, 'tags')
        ]

    def __data(self):
        # if it's compressed then use the 'cdata' structure
        if int( self['header'].l['Signature'][0]) == ord('C'):
            r = int(self['header'].l['FileLength'])
            size = r - self['header'].size()
            current = self.source.size() - self['header'].size() + self['header'].getoffset()

            # File.cdata decompresses and changes our source, so we fix our header here
            self['header']['Signature'][0].set( ord('F') )
            return dyn.clone(File.cdata, blocksize=lambda x:current)

        return self.data
    
    _fields_ = [
        (Header, 'header'),
        (__data, 'data')
    ]

if __name__ == '__main__':
    import sys
    import ptypes,__init__ as swf
    ptypes.setsource(ptypes.file('./test.swf'))

    z = File
#    z = ptypes.debugrecurse(z)
    z = z()
    z = z.l
    for x in z['data']['tags']:
        print '-'*32
        print x

    a = z['data']['tags'][0]
    print a.hexdump()
    print a.l.hexdump()
    print repr(a.l['Header'].serialize())

    correct='\x44\x11\x08\x00\x00\x00'
    print ptypes.utils.hexdump(correct)

    print a.serialize() == correct
