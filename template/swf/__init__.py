import zlib
from tags import *
from stypes import *

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
            block = self.source.consume(self._size)

            # XXX: modify ours and our parent's source with the new decompressed file
            self.parent.source = self.source = ptypes.provider.string(self.parent['header'].serialize() + zlib.decompress(block))
            return self.deserialize(block)

        def deserialize(self, source):
            block = ''.join([x for i,x in zip(xrange(self._size), source)])
            s = zlib.decompress(block)
            print 'zlib: decompressed %x to %x bytes'%(len(block),len(s))
            return super(File.cdata, self).deserialize(s)

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
            maxsize = self.source.size()
            current = maxsize - self['header'].size() + self['header'].getoffset()

            # File.cdata decompresses and changes our source, so we fix our header here
            self['header']['Signature'][0].set( ord('F') )
            return dyn.clone(File.cdata, _size=current)

        return self.data
    
    _fields_ = [
        (Header, 'header'),
        (__data, 'data')
    ]


if __name__ == '__main__':
    import sys
    fin = File()
    fin.open(sys.argv[1])
    for x in fin:
        print x

    sys.exit(0)
    
    ## in chunks
    x = ifile('sorenson.swf', 'rb')
    data = iter(x)

    x = Header()
    x.deserialize(data)
    print repr(x)

    x = FrameInfo()
    x.deserialize(data)
    print repr(x)

    while True:
        x = Tag()
        x.deserialize(data)
        print repr(x)

