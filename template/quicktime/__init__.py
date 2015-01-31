import atom,ptypes
from atom import AtomType,Atom,AtomList

class File(ptypes.parray.block):
    _object_ = Atom

    def blocksize(self):
        return self.getsize()

    def getsize(self):
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

    def summary(self):
        types = ','.join([x['type'].serialize() for x in self])
        return ' '.join([self.name(), 'atoms[%d] ->'% len(self), types])

    def repr(self):
        return self.summary()
