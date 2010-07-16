import sys
sys.path.append('f:/work')

import ptypes
from ptypes import *
import definitions
from definitions import *

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class File(pstruct.type, definitions.__base__.BaseHeader):
    _fields_ = [
        (headers.DosHeader, 'Dos'),
        (lambda s: dyn.block( int(s['Dos']['e_lfanew']) - s['Dos'].size()), 'Stub'),
        (headers.NtHeader, 'Pe')
    ]

if __name__ == '__main__':
    import Executable
    v = Executable.open('./test.dll')
    sections = v['Pe']['Sections']

    if False:
        exports = v['Pe']['OptionalHeader']['DataDirectory'][0].get()
        print exports.load()
        print exports.get()

    relo = v['Pe']['OptionalHeader']['DataDirectory'][5].get().load()


    baseaddress = v['Pe']['OptionalHeader']['ImageBase']
    section = sections[0]
    data = section.get()
    for a,r in relo.getrelocationsbysection(section):
        print hex(a), repr(r)
        data = r.relocate(data, 0, section)

