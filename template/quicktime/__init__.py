import atom,ptypes
from atom import Atom,AtomList

class File(ptypes.parray.infinite):
    _object_ = Atom
    currentsize = maxsize = 0   # copied from powerpoint

    def isTerminator(self, value):
        self.currentsize += value.size()
        if (self.currentsize + 8 <= self.maxsize):
            return False
        return True

    def __init__(self, **kwds):
        self.maxsize = self.source.size()
        return super(File, self).__init__(**kwds)

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

    def load(self):
        self.currentsize = 0
        return super(File, self).load()

