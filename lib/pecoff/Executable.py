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
        if issubclass(self.source.__class__, ptypes.provider.filebase):
            maxfilesize = self.source.size()
            sz = max(((x['PointerToRawData'].num()+x['SizeOfRawData'].num()) for x in pe['Sections']))
            ## if there's a security entry, then this can also contain an offset
            #sz = max((sz, 0 if pe['DataDirectory'][4]['Address'] == 0 else pe['DataDirectory'][4]['Address'].num()+pe['DataDirectory'][4]['Size'].num()))
            return dyn.block(sz - self.blocksize())

        # memory
        class result(parray.type):
            length = len(pe['Sections'])
            def _object_(self):
                sect = pe['Sections'][len(self.value)]
                class result(pstruct.type):
                    _fields_ = [
                        (dyn.align(pe['OptionalHeader']['SectionAlignment'].num(), undefined=True), 'Padding'),
                        (dyn.block(sect.getloadedsize()), 'Data'),
                    ]
                return result
        return result

    def __Certificate(self):
        res = self['Pe']['DataDirectory'][4]
        if res['Address'].num() == 0 or issubclass(self.source.__class__,ptypes.provider.memory):
            return ptype.undefined

        eof = res['Address'].num()+res['Size'].num()
        return dyn.block(eof-self.blocksize())

    _fields_ = [
        (headers.DosHeader, 'Dos'),
        (__Stub, 'Stub'),
        (headers.NtHeader, 'Pe'),
        (__Padding, 'Padding'),
        (lambda s: dyn.align(s['Pe']['OptionalHeader']['SectionAlignment'].num(), undefined=True) if issubclass(s.source.__class__, ptypes.provider.memory) else dyn.align(s['Pe']['OptionalHeader']['FileAlignment'].num()) , 'Alignment'),
        (__Data, 'Data'),
        (__Certificate, 'Certificate'),
    ]

    def loadconfig(self):
        return self['Pe']['DataDirectory'][10]['Address'].d.l

    def tls(self):
        return self['Pe']['DataDirectory'][9]['Address'].d.l

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
    exports = v['Pe']['DataDirectory'][0]
    while exports['Address'].int() != 0:
        exports = exports['Address'].d.l
        print exports.l
        break

    imports = v['Pe']['DataDirectory'][1]
    while imports['Address'].int() != 0:
        imports = imports['Address'].d.l
        print imports.l
        break

    relo = v['Pe']['DataDirectory'][5]['Address'].d.l
    baseaddress = v['Pe']['OptionalHeader']['ImageBase']
    section = sections[0]
    data = section.data().serialize()
    for e in relo.getbysection(section):
        for a,r in e.getrelocations(section):
            print e
            data = r.relocate(data, 0, section)
        continue

