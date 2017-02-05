import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

### utility functions
R = lambda f: list(reversed(f))     # reverse a ._fields_ declaration because Micro$oft's documentation lists structures with bit 0 as the high bit

### atomic types
class bool1(pint.uint8_t): pass
class ubyte1(pint.uint8_t): pass
class uint2(pint.uint16_t): pass
class uint4(pint.uint32_t): pass
class sint2(pint.int16_t): pass
class sint4(pint.int32_t): pass

### general types
class MD4(dyn.block(16)): pass

### record generalities
class RecordUnknown(ptype.block):
    length = 0
    def classname(self):
        s = self.shortname()
        names = s.split('.')
        if self.type is None:
            tstr = '?'
        elif isinstance(self.type, (int,long)):
            tstr = hex(self.type)
        elif hasattr(self.type, '__iter__'):
            tstr = '({:s})'.format(','.join(hex(x) if isinstance(x, (int,long)) else repr(x) for x in self.type))
        else:
            tstr = repr(self.type)
        names[-1] = '%s<%s>[size:0x%x]'%(names[-1], tstr, self.blocksize())
        return '.'.join(names)

# record type lookup
class Record(ptype.definition):
    cache = {}
    class RT_Unknown(ptype.definition): cache,unknown = {},RecordUnknown
    unknown = RT_Unknown

### Record type
class RecordType(pint.enum, pint.littleendian(pint.uint16_t)):
    _values_ = []

    @classmethod
    def define(cls,(name,value)):
        res = type(name, (ptype.definition,), {'type':value, 'cache':{}})
        cls._values_.append((res.__name__,res.type))
        return (name,Record.define(res))

### Record header
class RecordGeneral(pstruct.type):
    Record = Record

    class Header(pstruct.type):
        RecordType = RecordType
        class VersionInstance(pbinary.struct):
            _fields_ = R([(4,'version'), (12,'instance')])
            def summary(self):
                return '{:d} / 0x{:03x}'.format(self['version'], self['instance'])
            def set(self, *_, **fields):
                iterable, = _ if _ else ((),)
                if not isinstance(iterable, dict):
                    version, instance = iterable
                    return self.set((instance, version))
                return super(RecordGeneral.Header.VersionInstance, self).set(iterable, **fields)
        _fields_ = [
            (VersionInstance, 'Version/Instance'),
            (lambda s: s.RecordType, 'Type'),
            (pint.uint32_t, 'Length')
        ]

        def Type(self):
            return self['Type'].num()
        def Instance(self):
            res = self['Version/Instance']
            return res['version'],res['instance']
        def Length(self):
            return self['Length'].num()

        def summary(self):
            v = self['Version/Instance'].num()
            t,l = self['Type'].num(),self['Length'].num()
            return 'version=%d instance=0x%03x type=0x%04x length=0x%08x'% (v & 0xf, (v&0xfff0) / 0x10, t, l)

    def __data(self):
        res = self['header'].li
        t,i,l = res.Type(), res.Instance(), res.Length()
        Type = self.Record.get(t)

        # look for an explicit instance
        try:
            res = Type.lookup(i)

        # otherwise, the instance might modify the Instance in some way
        except KeyError:
            ver,instance = i
            i = ver,None
            res = Type.get(i, length=l)

        # something good had to come out of that
        if getattr(self, 'lazy', False):
            class RecordData(ptype.encoded_t):
                @classmethod
                def typename(cls):
                    return cls._object_.typename()
            RecordData._value_ = dyn.block(l)
            RecordData._object_ = res
            return RecordData
        return dyn.clone(res, blocksize=lambda s: l)

    def __extra(self):
        bs = self['header'].li.Length()
        s = self['header'].size() + self['data'].li.size()
        if bs > s:
            return dyn.block(bs - s)
        return ptype.undefined

    _fields_ = [
        (lambda s: s.Header, 'header'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]

    d = property(fget=lambda s: s['data'].d if getattr(s, 'lazy', False) else s['data'])

    def blocksize(self):
        res = self['header'].li
        return res.size() + res.Length()

class RecordContainer(parray.block):
    _object_ = RecordGeneral

    def details(self):
        records = []
        for v in self.walk():
            n = '%s[%x]'%(v.__class__.__name__,v.type)
            records.append(n)
        return 'records=%d [%s]'%(len(self), ','.join(records))

    def search(self, type, recurse=False):
        '''Search through a list of records for a particular type'''
        if not recurse:
            for n in self.filter(type):
                yield n
            return

        # ourselves first
        for d in self.search(type, False):
            yield d

        flazy = (lambda n: n['data'].d.l) if getattr(self, 'lazy', False) else (lambda n: n['data'])

        # now our chidren
        for n in self:
            if not hasattr(flazy(n), 'search'):
                continue
            for d in flazy(n).search(type, True):
                yield d
            continue
        return

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        res = [x for x in self if int(x['header']['recType']) == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

    def walk(self):
        flazy = (lambda n: n['data'].d.l) if getattr(self, 'lazy', False) else (lambda n: n['data'])
        for n in self:
            yield flazy(n)
        return

    def errors(self):
        for n in self:
            if n.initialized and n.size() == n.blocksize():
                continue
            yield n
        return

    def dumperrors(self):
        result = []
        for i,x in enumerate(self.errors()):
            result.append('%d\t%s\t%d\t%d'%(i,x.classname(),x.size(),x.blocksize()))
        return '\n'.join(result)

    def filter(self, type):
        if isinstance(type, (int,long)):
            for n in self:
                if n['header']['recType'].int() == type:
                    yield n
                continue
            return
        flazy = (lambda n: n['data'].d.l) if getattr(self, 'lazy', False) else (lambda n: n['data'])
        for n in self:
            if isinstance(flazy(n), type):
                yield n
            continue
        return

    def __getitem__(self, index):
        flazy = (lambda n: n['data'].d.l) if getattr(self, 'lazy', False) else (lambda n: n['data'])
        if hasattr(self, '_values_') and isinstance(index, basestring):
            lookup = dict(self._values_)
            t = lookup[index]
            res = (i for i,n in enumerate(self) if isinstance(flazy(n), t))
            index = next(res)
        return super(RecordContainer, self).__getitem__(index)

# yea, a file really is usually just a gigantic list of records...
class File(RecordContainer):
    def details(self):
        records = []
        for v in self.walk():
            n = '%s[%x]'%(v.__class__.__name__,v.type)
            records.append(n)
        return '%s records=%d [%s]'%(self.name(), len(self), ','.join(records))

    def blocksize(self):
        return self.source.size() if hasattr(self, 'source') else super(File, self).blocksize()

if __name__ == '__main__':
    from ptypes import *

#    @Record.Define
    class r(pstruct.type):
        type = 0
        _fields_ = [
            (pint.uint32_t, 'a')
        ]

    s = '\x00\x00\x00\x00\x0c\x00\x00\x00' + 'A'*30
    z = RecordGeneral()
    z.source = provider.string(s)
    print z.l
