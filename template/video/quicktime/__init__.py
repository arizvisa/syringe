import ptypes
from . import atom
from .atom import AtomType, Atom, AtomList

class File(ptypes.parray.block):
    _object_ = Atom

    def blocksize(self):
        if isinstance(self.source, ptypes.prov.bounded):
            return self.source.size()
        raise NotImplementedError("Source is unbounded, a blocksize must be assigned to instance")

    def getsize(self):
        return self.blocksize()

    def search(self, type):
        '''Search through a list of atoms for a particular fourcc type'''
        return (item for item in self if item['type'] == type)

    def lookup(self, type):
        '''Return the first instance of specified atom type'''
        res = [item for item in self if item['type'] == type]
        if not res:
            raise KeyError(type)
        if len(res) == 1:
            return res[0]
        raise AssertionError("Unable to search for atom of type {!r}".format(res))

    def summary(self):
        iterable = (item['type'].serialize().decode('latin1') for item in self)
        types = ','.join(iterable)
        return ' '.join([self.name(), 'atoms[%d] ->'% len(self), types])

    def repr(self):
        return self.summary()
