import functools, itertools, types, builtins, operator, six
from . import store

class Shdr(store.Segment):
    def __init__(self, sh):
        self._shdr = sh

    def name(self):
        res = self._shdr['sh_name']
        return res.str()

    def offset(self):
        res = self._shdr['sh_offset']
        return res.int()

    def length(self):
        hdr = self._shdr
        return hdr.getloadedsize()

    def data(self):
        hdr = self._shdr
        res, cb = hdr['sh_offset'].d, hdr.getloadedsize()
        padding = cb - res.size()
        return res.l.serialize() + padding * b'\0'

    def protection(self):
        raise NotImplementedError
        return set()

    def symbols(self):
        raise NotImplementedError
        while False:
            yield ()
        return

class Phdr(store.Segment):
    def __init__(self, sh):
        self._phdr = sh

    def name(self):
        hdr = self._phdr
        return hdr.name()

    def offset(self):
        hdr = self._phdr
        return hdr['p_vaddr'].int()

    def length(self):
        hdr = self._phdr
        return hdr.getloadedsize()

    def data(self):
        hdr = self._phdr
        res, cb = hdr['p_offset'].d, hdr.getloadedsize()
        padding = cb - res.size()
        return res.l.serialize() + b'\0' * padding

    def protection(self):
        raise NotImplementedError
        return set()

    def symbols(self):
        raise NotImplementedError
        while False:
            yield ()
        return

if __name__ == '__main__':
    import sys, os.path
    import ptypes, elf

    library_dir = os.path.dirname(__file__)
    samples_dir = os.path.join(library_dir, 'samples')
    ptypes.setsource(ptypes.prov.file(os.path.join(samples_dir, 'write.out'), 'rb'))

    z = elf.File().l
    z = z['e_data']
    ph = z['e_phoff'].d.l
    sh = z['e_shoff'].d.l
    print(sh)

    print(sh[5])

    self = Shdr(sh[5])
    print(self.data())

    class ElfObjectStore(store.Store):
        pass
