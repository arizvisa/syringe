import functools, itertools, types, builtins, operator, six
from . import store

class ElfSection(store.Segment):
    def __init__(self, sh):
        self._hdr = sh

    def name(self):
        res = self._hdr['sh_name']
        return res.str()

    def offset(self):
        res = self._hdr['sh_offset']
        return res.int()

    def length(self):
        res = self._hdr['sh_size']
        return res.int()

    def data(self):
        res = self._hdr['sh_offset'].d
        return res.l.serialize()

    def protection(self):
        return set()

    def symbols(self):
        while False:
            yield ()
        return

if __name__ == '__main__':
    import os.path
    import ptypes, elf
    import sys

    library_dir = os.path.dirname(__file__)
    samples_dir = os.path.join(library_dir, 'samples')
    ptypes.setsource(ptypes.prov.file(os.path.join(samples_dir, 'write.o'), 'rb'))

    z = elf.File().l
    z = z['e_data']
    sh = z['e_shoff'].d.l
    print(sh)

    print(sh[5])

    self = ElfSection(sh[5])
    print(self.data())

    class ElfObjectStore(store.Store):
        pass
