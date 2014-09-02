import logging,ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
import __base__,headers

def open(filename, **kwds):
    res = File()
    res.source = ptypes.provider.file(filename, **kwds)
    res.load()
    res.filename = filename     # ;)
    return res

class File(pstruct.type, ptype.boundary):
    def __Stub(self):
        #ofs = self['Dos']['e_misc']['General']['e_lfanew'].num()
        ofs = self['Dos']['e_misc']['e_lfanew'].num()
        sz = self['Dos'].size()
        if (ofs >= sz):
            return dyn.block(ofs - sz)
        logging.info("%s : Stub : PE Offset is uninitialized. Defaulting Stub Size to 0"% (self.name()))
        return dyn.block(0)

    def __Padding(self):
        '''Calculate the size of executable on disk'''
        opt = self['Pe'].l['OptionalHeader']
        return dyn.block(opt['SizeOfHeaders'].num() - self.size())

    def __Data(self):
        pe = self['Pe'].l
        # file
        if issubclass(self.source.__class__, ptypes.provider.file):
            sz = max(((x['PointerToRawData'].num()+x['SizeOfRawData'].num()) for x in pe['Sections']))
            return dyn.block(sz - self.blocksize())

        # memory
        class result(parray.type):
            length = len(pe['Sections'])
            class _object_(pstruct.type):
                def __Padding(self):
                    p = self.getparent(File)['Pe']
                    alignment = p['OptionalHeader']['SectionAlignment'].num()
                    return dyn.align(alignment, undefined=True)
                def __Data(self):
                    p = self.getparent(File)['Pe']
                    index = len(self.parent.value)
                    sect = p['Sections'][index-1]
                    return dyn.block(sect.getloadedsize())
                _fields_ = [
                    (__Padding, 'Padding'),
                    (__Data, 'Data'),
                ]
        return result

    _fields_ = [
        (headers.DosHeader, 'Dos'),
        (__Stub, 'Stub'),
        (headers.NtHeader, 'Pe'),
        (__Padding, 'Padding'),
        (lambda s: dyn.align(1 if issubclass(s.source.__class__, ptypes.provider.file) else 0x1000), 'Alignment'),
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
        continue

