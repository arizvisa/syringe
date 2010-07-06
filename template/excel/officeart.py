from ptypes import *
class parray_sized(parray.type):
    maxsize = 0
    def load_container(self):
        ofs = self.getoffset()
        sz = 0
        while sz < self.maxsize:
            n = self.newelement(self._object_, str(len(self.value)), ofs)
            self.append(n)
            n.load()
            ofs += n.size()
            sz += n.size()
        return self

    def deserialize(self, source):
        source = iter(source)
        self.value = []
        ofs = self.getoffset()
        sz = 0
        while sz < self.maxsize:
            n = self.newelement(self._object_, str(len(self.value)), ofs)
            self.append(n)
            n.deserialize(source)
            ofs += n.size()
            sz += n.size()
        return self

    load_block = load_container

class RecordHeader(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'rec'),
        (pint.uint16_t, 'recType'),
        (pint.uint32_t, 'recLen'),
    ]

class OfficeArt(object):
    rectype = int

class Property(pstruct.type):
    def autoRecordType(self):
        global LookupArtType
        t = int(self['rh']['recType'])
        try:
            return LookupArtType[t]
        except KeyError:
            pass
        return dyn.block( int(self['rh'].l['recLen']) )

    def figureextra(self):
        total = int(self['rh'].l['recLen'])
        current = self['r'].size()
        return dyn.block(total-current)

    _fields_ = [
        (RecordHeader, 'rh'),
        (autoRecordType, 'r'),
        (figureextra, '_')
    ]

class PropertyList(parray_sized):
    _object_ = Property
    maxsize = 0

class SpContainer(pstruct.type):
    rectype = 0xf004
    _fields_ = [
        (RecordHeader, 'rh'),
        (lambda s: dyn.clone(PropertyList,maxsize=int(s['rh'].l['recLen'])-s['rh'].size()), 'r')
    ]

class FSP(pstruct.type, OfficeArt):
    rectype = 0xf00a
    class __flags(pbinary.struct):
        _fields_ = [(1, 'fGroup'),(1,'fChild'),(1,'fPatriarch'),(1,'fDeleted'),(1,'fOleShape'),(1,'fHaveMaster'),(1,'fFlipH'),(1,'fFlipV'),(1,'fConnector'),(1,'fHaveAnchor'),(1,'fBackground'),(1,'fHaveSpt'),(20,'unused1')]
        
    _fields_ = [
        (pint.uint32_t, 'spid'),
        (__flags, 'f')
    ]

class FOPT(pstruct.type, OfficeArt):
    rectype = 0xf00b
    _fields_ = [
        (lambda s: dyn.array(FOPTE, int(s.parent['rh']['recLen']) / 6), 'fopt')
    ]

class FOPTE(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'opid'),
        (pint.uint32_t, 'op')
    ]

### build lookup table
LookupArtType = {}
import inspect
for cls in globals().values():
    if inspect.isclass(cls) and issubclass(cls, OfficeArt):
        LookupArtType[cls.rectype] = cls
    continue

def lazy(object, size=None):
    class lazy(dyn.addr_t):
        length = int
        _object_ = object

        def dereference(self):
            v = self.newelement(self._object_, self.name(), self.getoffset())
            v.deserialize(self.value)
            return v
        
        deref = dereference
        d = property(fget=lambda s: s.dereference())

    if size is None:
        size = object().size()

    lazy.length = size
    lazy.__name__ = object.__name__
    return lazy

if __name__ == '__main__':
    import ptypes    
    ptypes.setsource( ptypes.provider.file('poc.xls') )

    x = SpContainer()
#    x.setoffset(66100)
    x.setoffset(66360)
    print x.l
