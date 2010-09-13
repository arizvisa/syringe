import atom,ptypes
from atom import Atom,AtomList

class File(ptypes.parray.infinite):
    _object_ = Atom

    def blocksize(self):
        return self.source.size()

    def search(self, type):
        '''Search through a list of atoms for a particular fourcc type'''
        return (x for x in self if x['type'] == type)

    def lookup(self, type):
        '''Return the first instance of specified atom type'''
        res = [x for x in self if x['type'] == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

