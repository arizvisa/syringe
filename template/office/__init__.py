from ptypes import *

### atomic types
class bool1(pint.uint8_t): pass
class ubyte1(pint.uint8_t): pass
class uint2(pint.uint16_t): pass
class uint4(pint.uint32_t): pass
class sint2(pint.int16_t): pass
class sint4(pint.int32_t): pass

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
            _fields_=[(12,'instance'),(4,'version')]
            def summary(self):
                return '{:d} / 0x{:03x}'.format(self['version'], self['instance'])
        _fields_ = [
            (pbinary.littleendian(VersionInstance), 'Version/Instance'),
            (lambda s: s.RecordType, 'Type'),
            (pint.littleendian(pint.uint32_t), 'Length')
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
            for x in self:
                if int(x['header']['recType']) == type:
                    yield x
                continue
            return

        # ourselves first
        for d in self.search(type, False):
            yield d

        # now our chidren
        for x in self:
            try:
                x['data'].search
            except AttributeError:
                continue

            for d in x['data'].search(type, True):
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
        for x in self:
            yield x['data']
        return

    def errors(self):
        for x in self:
            if x.initialized and x.size() == x.blocksize():
                continue
            yield x
        return

    def dumperrors(self):
        result = []
        for i,x in enumerate(self.errors()):
            result.append('%d\t%s\t%d\t%d'%(i,x.classname(),x.size(),x.blocksize()))
        return '\n'.join(result)

# yea, a file really is usually just a gigantic list of records...
class File(RecordContainer):
    def details(self):
        records = []
        for v in self.walk():
            n = '%s[%x]'%(v.__class__.__name__,v.type)
            records.append(n)
        return '%s records=%d [%s]'%(self.name(), len(self), ','.join(records))

    def blocksize(self):
        return self.source.size()

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
