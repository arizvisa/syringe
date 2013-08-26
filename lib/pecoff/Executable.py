import logging

import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.littleendian)
import definitions
from definitions import *

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

    def __MemData(self):
        '''Calculate the size of executable in memory'''
        optionalheader = self['Pe'].l['OptionalHeader']
        alignment = optionalheader['SectionAlignment'].number()
        s = optionalheader['SizeOfImage'].number()
        return dyn.block(s - self.size())
#        return dyn.block(s - self.size(), summary=lambda s:s.hexdump(oneline=1))

    def __FileData(self):
        '''Calculate the size of executable on disk'''
        pe = self['Pe'].l
        endings = sorted(((x['PointerToRawData'].number()+x['SizeOfRawData'].number()) for x in pe['Sections']))
        s = endings[-1]
        return dyn.block(s - self.size())

    def __Data(self):
        if issubclass(self.source.__class__, ptypes.provider.file):
            return self.__FileData()
        return self.__MemData()

    _fields_ = [
        (headers.DosHeader, 'Dos'),
        (__Stub, 'Stub'),
        (headers.NtHeader, 'Pe'),
        (__Data, 'Data')
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
    import sys
    import Executable
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        v = Executable.open(filename)
    else:
        filename = 'obj/kernel32.dll'
        for x in range(10):
            print filename
            try:
                v = Executable.open(filename)
                break
            except IOError:
                pass
            filename = '../'+filename

    sections = v['Pe']['Sections']

    exports = v['Pe']['OptionalHeader']['DataDirectory'][0]
    while exports['VirtualAddress'].int() != 0:
        exports = exports.get()
        print exports.l
        break

    imports = v['Pe']['OptionalHeader']['DataDirectory'][1]
    while imports['VirtualAddress'].int() != 0:
        imports = imports.get()
        print imports.l
        break

    relo = v['Pe']['OptionalHeader']['DataDirectory'][5].get().load()
    baseaddress = v['Pe']['OptionalHeader']['ImageBase']
    section = sections[0]
    data = section.get()
    for e in relo.getbysection(section):
        for a,r in e.getrelocations(section):
            print e
            data = r.relocate(data, 0, section)

