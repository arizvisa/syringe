# -*- coding: utf-8 -*-
import sys
from office.OleFileIO_PL import OleFileIO

def liststreams(ole):
    return '\n'.join('[%d] %s'%(i,x) for i,(x,) in enumerate(ole.listdir()))

def dumpstream(ole, index):
    name = ole.listdir()[index]
    result = ole.openstream(name)
    return result.read()

def xlsoffsettostream(ole, offset):
    sectorsize=ole.sectorsize
    for x in ole.root.kids:
        left,right=x.sid*sectorsize,x.size
        if offset<left or offset>right:
            continue
        result = offset - left
        return result,x
    raise Exception

if __name__ == '__main__':
    import sys
    usage = '''
usage: %s filename [command] [args]

    if command is not provided, then dump a list of all the streams in file.

    commands:
        -d index
            dump specified stream to stdout
        -o decimal offfset
            translate the ole file offset into a stream index and it's offset
        -ox hex offset
            translate the ole file offset into a stream index and it's offset
'''%sys.argv[0]

    if len(sys.argv) <= 1:
        raise Exception(usage)

    filename = sys.argv[1]
    b = OleFileIO(filename)

    # list streams
    if len(sys.argv) == 2:
        print(liststreams(b))

    else:
        command,args = sys.argv[2],sys.argv[3:]
        # -d index
        if command == '-d':
            index, = args
            index = int(index)
            print(dumpstream(b, index))
        # -o offset
        elif command == '-o':
            offset, = args
            o,s = xlsoffsettostream(b, int(offset))
            print(b._find(s.name),s.name,hex(o+0x10))   # XXX:uh
        elif command == '-ox':
            offset, = args
            o,s = xlsoffsettostream(b, int(offset,16))
            print(b._find(s.name),s.name,hex(o+0x10))   # XXX:uh
        else:
            raise Exception(usage)
