#raise NotImplementedError("This is using an older version of ptypes")
raise NotImplementedError("This is still broken")

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

if False:
    class ifile(file):
        def __iter__(self):
            while True:
                res = self.read(1)
                assert len(res) > 0
                yield res
                    
    class sfile(object):
        def __init__(self, data):
            super(sfile, self).__init__()
            self.data = data
            self.offset = 0

        def __iter__(self):
            while True:
                yield self.read(1)

        def read(self, count=-1):
            if count < 0:
                res = self.data[ self.offset: ]
            else:
                res = self.data[ self.offset : self.offset+count ]

            self.offset += len(res)
            return res

        def write(self, data):
            self.data[ self.offset : self.offset+len(data) ] = data

        def seek(self, offset, whence=0):
            if whence == 0:
                self.offset = offset
            elif whence == 1:
                self.offset += offset
            elif whence == 2:
                self.offset = len(self.data) - offset
            else:
                raise ValueError('invalid whence')

        def tell(self):
            return self.offset

        def close(self):
            pass

    class File(parray.type):
        file = None

        def open(self, filename):
            self.file = ifile(filename, 'rb')
            input = iter(self.file)
            self.value = []

            x = Header()
            x.deserialize(input)
            self.append(x)
            x.setoffset(0)

            # decompress if necessary
            if int( self[0]['Signature'][0]) == ord('C'):
                self.file.seek( self[0].size() )
                data = self.file.read()
                self.file = sfile( self[0].serialize() + zlib.decompress(data) )
                self.file.seek( self[0].size() )
                input = iter(self.file)
            
            x = FrameInfo()
            x.deserialize(input)
            self.append(x)
            x.setoffset( x.getOffset(1) )

            x = TagList()
            x.deserialize(input)
            self.extend(x)
            x.setoffset( x.getOffset(2) )


if False:
    ptypes.setsource(ptypes.file('poc.spl'))
    x = swf.Header()
    print x.l

    length  = x.source.size() - x.size()
    x.source.seek(x.size())
    data = x.source.consume(x.source.size()-8)
    data = zlib.decompress(data)

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

