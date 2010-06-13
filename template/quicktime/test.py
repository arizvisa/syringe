import atom
from atom import Atom,AtomList

import ptypes
from ptypes import *
config.WIDTH = 180

def getFileContents(filename):
    input = file(filename, 'rb')
    res = input.read()
    input.close()
    return res

if __name__ == '__main__':
    input = getFileContents('poc.mov')
    iterable = iter(input)

#    atoms = AtomList()
#    atoms.deserialize(iterable)
#    print atoms

    ftyp = Atom()
    ftyp.deserialize(iterable)

    wide = Atom()
    wide.deserialize(iterable)

    mdat = Atom()
    mdat.deserialize(iterable)

    moov = Atom()
    moov.deserialize(iterable)

    mvhd = moov['data'][0]
    trak = moov['data'][1]
    mdia = trak['data'][1]
    minf = mdia['data'][2]

    stbl = minf['data'][3]
    stsd = stbl['data'][0]
    stsz = stbl['data'][4]
    stco = stbl['data'][5]

#    for x in stsz['data']['Entries']:
#        print x
    print stsd['data']['Entries'][0]
    print stsz['data']['Entries'][18]
    print stco['data']['Entries'][18]

    for x in stbl['data']:
        print repr(x)
    stsz = stbl['data'][4]

#    v = atoms
#    print v
#    print '\n'.join([repr(x) for x in v])
#    print '\n'.join([repr(x['data'].getOffset()) for x in v])

    # moov
    v = atoms.lookup('moov')

    # trak
    v = v['data'].lookup('trak')

    # mdia
    v = v['data'].lookup('mdia')

    # minf
    v = v['data'].lookup('minf')

    # stbl
    v = v['data'].lookup('stbl')

    # stsd
    v = v['data'].lookup('stsd')

    print utils.hexdump(atoms.serialize())

