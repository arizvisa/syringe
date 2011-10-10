import ptypes
from ptypes import *
import definitions
from definitions import *
import logging

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class File(pstruct.type, definitions.__base__.BaseHeader):
    def __Stub(self):
        ofs = int(self['Dos']['e_lfanew'])
        sz = self['Dos'].size()
        if (ofs >= sz):
            return dyn.block(ofs - sz)
        logging.info("%s : Stub : PE Offset is uninitialized. Defaulting Stub Size to 0"% (self.name()))
        return dyn.block(0)

    _fields_ = [
        (headers.DosHeader, 'Dos'),
#        (lambda s: dyn.block( int(s['Dos']['e_lfanew']) - s['Dos'].size()), 'Stub'),
        (__Stub, 'Stub'),
        (headers.NtHeader, 'Pe')
    ]

    def loadconfig(self):
        return self['Pe']['OptionalHeader']['DataDirectory'][10].get()

    def tls(self):
        return self['Pe']['OptionalHeader']['DataDirectory'][9].get()

    def relocateable(self):
        characteristics = self['Pe']['OptionalHeader']['DllCharacteristics']
        return 'DYNAMIC_BASE' in characteristics

    def has_seh(self):
        characteristics = self['Pe']['OptionalHeader']['DllCharacteristics']
        return 'NO_SEH' not in characteristics

    def has_nx(self):
        characteristics = self['Pe']['OptionalHeader']['DllCharacteristics']
        return 'NX_COMPAT' in characteristics

    def has_integrity(self):
        characteristics = self['Pe']['OptionalHeader']['DllCharacteristics']
        return 'FORCE_INTEGRITY' in characteristics

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

