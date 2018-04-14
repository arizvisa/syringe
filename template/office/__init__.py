import ptypes
from ptypes import *
import itertools,functools,operator

ptypes.Config.ptype.clone_name = '{}'
ptypes.Config.pbinary.littleendian_name = '{}'
ptypes.Config.pbinary.bigendian_name = 'be({})'
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
        names = self.shortname().split('.')
        if self.type is None:
            res = '?'
        elif isinstance(self.type, (int,long)):
            res = hex(self.type)
        elif hasattr(self.type, '__iter__'):
            res = '({:s})'.format(','.join('{:#x}'.format(x) if isinstance(x, (int,long)) else '{!r}'.format(x) for x in self.type))
        else:
            res = repr(self.type)
        names[-1] = '{:s}<{:s}>[size:{:#x}]'.format(names[-1], res, self.blocksize())
        return '.'.join(names)

# record type lookup
class Record(ptype.definition):
    cache = {}
    class RT_Unknown(ptype.definition): cache,unknown = {},RecordUnknown
    unknown = RT_Unknown

class Instance(ptype.definition):
    @classmethod
    def define(cls, *definition, **attributes):
        res = super(Instance, cls).define(*definition, **attributes)
        res.__instance__ = cls.type
        return res

### Record type
class RecordType(pint.enum, pint.littleendian(pint.uint16_t)):
    _values_ = []

    @classmethod
    def define(cls,(name,value)):
        res = type(name, (Instance,), {'type':value, 'cache':{}})
        cls._values_.append((res.__name__,res.type))
        return (name, Record.define(res))

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
                    return self.set(dict(instance=instance, version=version))
                return super(RecordGeneral.Header.VersionInstance, self).set(iterable, **fields)
        _fields_ = [
            (VersionInstance, 'Version/Instance'),
            (lambda s: s.RecordType, 'Type'),
            (pint.uint32_t, 'Length')
        ]

        def Type(self):
            return self['Type'].int()
        def Instance(self):
            res = self['Version/Instance']
            return res['version'],res['instance']
        def Length(self):
            return self['Length'].int()

        def summary(self):
            v = self['Version/Instance'].int()
            t,l = self['Type'].int(),self['Length'].int()
            return 'version={:d} instance={:#05x} type={:#06x} length={length:#x}({length:x})'.format(v & 0xf, (v&0xfff0) / 0x10, t, length=l)

    def __data(self):
        res = self['header'].li
        t, vi, length = res.Type(), res.Instance(), res.Length()
        Type = self.Record.lookup(t, dyn.clone(self.Record.unknown, type=t))

        # look for an explicit instance
        try:
            res = Type.lookup(vi)

        # otherwise, the instance might modify the Instance in some way
        except KeyError:
            ver, _ = vi
            res = Type.lookup((ver, None), dyn.clone(Type.unknown, type=(ver, None), length=length))

        # something good had to come out of that
        if getattr(self, 'lazy', False):
            class RecordData(ptype.encoded_t):
                @classmethod
                def typename(cls):
                    return cls._object_.typename()
            RecordData._value_ = dyn.block(length)
            RecordData._object_ = res
            return RecordData
        return dyn.clone(res, blocksize=lambda s, length=length: length)

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

    h = property(fget=lambda s: s['header'])

    def Data(self):
        return self['data'].d if getattr(self, 'lazy', False) else self['data']
    d = property(fget=Data)

    def blocksize(self):
        res = self['header'].li
        return res.size() + res.Length()

    def previousRecord(self, type, **count):
        container = self.p
        idx = container.value.index(self)

        # Seek backwards from index to find record
        count = count.get('count', -1)
        if count > 0:
            for i in range(count):
                if isinstance(container[idx - i].d, type):
                    break
                continue
        else:
            i = 0
            while idx >= i and not isinstance(container[idx - i].d, type):
                i += 1

        if not isinstance(container[idx - i].d, type):
            raise ptypes.error.NotFoundError(self, 'previousRecord', message='Unable to locate previous record : {!r}'.format(type))
        return container[idx - i]


class RecordContainer(parray.block):
    _object_ = RecordGeneral

    def repr(self): return self.details() + '\n'
    def details(self):
        emit = lambda data: ptypes.utils.emit_repr(data, ptypes.Config.display.threshold.summary)
        f = lambda (_,item): (lambda recordType:'{:s}[{:04x}]'.format(item.classname(), recordType))(item.getparent(RecordGeneral)['header']['type'].int())
        res = ((lambda records:'[{:x}] {:s}[{:d}] : {:s} : \'{:s}\''.format(records[0][1].getparent(RecordGeneral).getoffset(), self.classname(), records[0][0], ('{:s} * {length:d}' if len(records) > 1 else '{:s}').format(ty, length=len(records)), emit(ptype.container(value=map(operator.itemgetter(1), records)).serialize())))(list(records)) for ty, records in itertools.groupby(enumerate(self.walk()), f))
        return '\n'.join(res)

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
        res = [x for x in self if x['header']['recType'].int() == type]
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
            if n.initializedQ() and n.size() == n.blocksize():
                continue
            yield n
        return

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
    def repr(self): return self.details() + '\n'
    def details(self):
        emit = lambda data: ptypes.utils.emit_repr(data, ptypes.Config.display.threshold.summary)
        f = lambda (_,item): (lambda recordType:'{:s}[{:x}]'.format(item.classname(), recordType))(item.getparent(RecordGeneral)['header']['type'].int())
        res = ((lambda records:'[{:x}] {:s}[{:d}] : {:s} : \'{:s}\''.format(records[0][1].getparent(RecordGeneral).getoffset(), self.classname(), records[0][0], ('{:s} * {length:d}' if len(records) > 1 else '{:s}').format(ty, length=len(records)), emit(ptype.container(value=map(operator.itemgetter(1), records)).serialize())))(list(records)) for ty, records in itertools.groupby(enumerate(self.walk()), f))
        return '\n'.join(res)

    def blocksize(self):
        return self.source.size() if hasattr(self.source, 'size') else super(File, self).blocksize()

    def properties(self):
        res = super(File, self).properties()
        try: res['size'] = self.size()
        except ptypes.error.InitializationError: pass
        try: res['blocksize'] = self.blocksize()
        except ptypes.error.InitializationError: pass
        return res

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
