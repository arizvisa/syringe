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

    def __repr__(self):
        types = ','.join([x['type'].serialize() for x in self])
        return ' '.join([self.name(), 'atoms[%d] ->'% len(self), types])

class AtomType(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt
