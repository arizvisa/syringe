import ptypes
from . import atom
from .atom import AtomType, Atom, AtomList, FullBox, EntriesAtom
import logging

class File(ptypes.parray.block):
    _object_ = Atom

    def blocksize(self):
        if isinstance(self.source, ptypes.prov.bounded):
            return self.source.size()
        if self.value is not None:
            return self.size()
        logging.warning("Source is unbounded, a blocksize must be assigned to {:s}".format(self.instance()))
        return 0

    def Size(self):
        return self.blocksize()

    def search(self, type):
        '''Search through a list of atoms for a particular fourcc type'''
        return (item for item in self if item['type'] == type)

    def lookup(self, type):
        '''Return the first instance of specified atom type'''
        return next(item for item in self if item['type'] == type)

    def summary(self):
        iterable = (item['type'].serialize().decode('latin1') for item in self)
        return ' '.join([self.name(), "atoms[{:d}] ->".format(len(self)), ', '.join(iterable)])

    def repr(self):
        return self.summary()
