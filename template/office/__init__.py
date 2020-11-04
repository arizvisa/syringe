import ptypes
from ptypes import *
import six,itertools,functools,operator

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
class undefined(ptype.block):
    def summary(self):
        return super(undefined, self).summary() if self.size() else '...'

### general types
class MD4(dyn.block(16)): pass

### record generalities
class RecordUnknown(ptype.block):
    length = 0
    def classname(self):
        names = self.shortname().split('.')
        if self.type is None:
            res = '?'
        elif isinstance(self.type, six.integer_types):
            res = "{:#x}".format(self.type)
        elif hasattr(self.type, '__iter__'):
            res = "({:s})".format(','.join("{:#x}".format(item) if isinstance(item, six.integer_types) else "{!r}".format(item) for item in self.type))
        else:
            res = repr(self.type)
        names[-1] = "{:s}<{:s}>[size:{:#x}]".format(names[-1], res, self.blocksize())
        return '.'.join(names)

# record type lookup
class Record(ptype.definition):
    cache = {}
    class RT_Unknown(ptype.definition): cache, default = {}, RecordUnknown
    default = RT_Unknown

    @classmethod
    def get_recordtype(cls, instance):
        '''Search through all definitions for whichever one contains the class for the specified instance.'''
        klass = type(instance) if ptype.isinstance(instance) else instance
        for rt, definition in cls.cache.items():
            if klass in definition.cache.values():
                return rt
            continue
        raise KeyError(klass)

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
    def define(cls,pack_namevalue):
        name, value = pack_namevalue
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
                return "{:d} / {:#0{:d}x}".format(self['version'], self['instance'], 2 + 3)

            def set(self, *versioninstance, **fields):
                iterable, = versioninstance if versioninstance else ((),)
                if iterable and not isinstance(iterable, dict):
                    version, instance = iterable
                    return self.set({'instance': instance, 'version': version})
                return super(RecordGeneral.Header.VersionInstance, self).set(iterable, **fields)

        _fields_ = [
            (VersionInstance, 'Version/Instance'),
            (lambda self: self.RecordType, 'Type'),
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
            return "version={:d} instance={:#05x} type={:#06x} length={length:#x}({length:x})".format(v & 0xf, (v&0xfff0) // 0x10, t, length=l)

    def __data(self):
        header = self['header'].li
        t, vi, length = header.Type(), header.Instance(), header.Length()
        Type = self.Record.withdefault(t, type=t)

        # look for an explicit instance
        try:
            res = Type.lookup(vi)

        # otherwise, the instance might modify the Instance in some way
        except KeyError:
            ver, _ = vi
            res = Type.withdefault((ver, None), type=(ver, None), length=length)

        # something good had to come out of that
        if getattr(self, 'lazy', False):
            class RecordData(ptype.encoded_t):
                @classmethod
                def typename(cls):
                    return cls._object_.typename()
            RecordData._value_ = dyn.block(length)
            RecordData._object_ = res
            return RecordData
        return dyn.clone(res, blocksize=lambda _, bs=length: bs) if length < self.new(res).a.size() else res

    def __extra(self):
        header, size = self['header'].li, self['data'].li.size()
        return dyn.block(max(0, header.Length() - size))

    _fields_ = [
        (lambda self: self.Header, 'header'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]

    def alloc(self, **fields):
        res = super(RecordGeneral, self).alloc(**fields)
        if operator.contains(fields, 'header'):
            return res
        if hasattr(res.d, 'type'):
            version, instance = res.d.type
            versioninstance = dict(version=version) if instance is None else dict(version=version, instance=instance)

            header = {'Version/Instance': versioninstance}
            try:
                rt = self.Record.get_recordtype(res.d)
            except KeyError:
                pass
            else:
                header['Type'] = rt

            print(header)
        header['Length'] = sum(item.size() for item in [res.d, res['extra']])
        res.h.set(**header)
        return res

    h = property(fget=lambda self: self['header'])

    def Data(self):
        return self['data'].d if getattr(self, 'lazy', False) else self['data']
    d = property(fget=Data)

    def Extra(self):
        return self['extra']

    def previousRecord(self, record_t, **count):
        container = self.parent
        idx = container.value.index(self)

        # Seek backwards from index to find record
        count = count.get('count', -1)
        if count > 0:
            for i in range(count):
                if isinstance(container[idx - i].d, record_t):
                    break
                continue
        else:
            i = 0
            while idx >= i and not isinstance(container[idx - i].d, record_t):
                i += 1

        if not isinstance(container[idx - i].d, record_t):
            raise ptypes.error.ItemNotFoundError(self, 'previousRecord', message="Unable to locate previous record type : {!r}".format(record_t))
        return container[idx - i]

class RecordContainer(parray.block):
    _object_ = RecordGeneral

    def repr(self):
        try:
            res = self.details()
        except ptypes.error.InitializationError:
            return super(RecordContainer, self).repr()
        return res + ('\n' if res else '')

    def summary(self):
        if len(self) > 1:
            first, last = items = [self[idx] for idx in [0, -1]]
            instances = ("{:s}[{:x}:{:+x}]".format(item.Data().classname(), item.getoffset(), item.size()) for item in items)
            instancedata = zip(instances, items)

        elif len(self):
            item = self[0]
            instance = "{:s}[{:x}:{:+x}]".format(item.Data().classname(), item.getoffset(), item.size())
            instancedata = [(instance, item)]

        else:
            return super(RecordContainer, self).summary()

        return ' : '.join(["{:d} record{:s}".format(len(self), '' if len(self) == 1 else 's'), ' ... '.join("{!s} {:s}".format(instance, data.summary()) for instance, data in instancedata)])

    def details(self):
        def Fkey(object):
            '''lambda (_,item): (lambda recordType:"{:s}[{:04x}]".format(item.classname(), recordType))(item.getparent(RecordGeneral)['header']['type'].int())'''
            index, item = object
            record, Fclassname = item.parent, functools.partial("{:s}[{:04x}]".format, item.classname())
            return Fclassname(record['header']['type'].int())
        def emit_prefix(_, records):
            index, record = records[0]
            ok = not any(item.parent.Extra().size() for _, item in records)
            return "[{:x}] {:s}{:s}[{:d}]".format(record.getparent(RecordGeneral).getoffset(), '' if ok else '*', self.classname(), index)
        def emit_classname(classname, records):
            if len(records) > 1:
                return "{length:d} * {:s}".format(classname, length=len(records))
            return classname
        def emit_summary(_, records):
            if len(records) > 1:
                res = bytes().join(item.serialize() for index, item in records)
                return ptypes.utils.emit_repr(res, ptypes.Config.display.threshold.summary) or '...'
            (_, record), = records
            return record.summary()

        groups = [(typename, [item for item in items]) for typename, items in itertools.groupby(enumerate(self.walk()), key=Fkey)]
        iterable = ([emit_prefix(*item), emit_classname(*item), emit_summary(*item)] for item in groups)
        return '\n'.join(map(' : '.join, iterable))

    def search(self, type, recurse=False):
        '''Search through a list of records for a particular type'''
        if not recurse:
            for item in self.filter(type):
                yield item
            return

        # ourselves first
        for d in self.search(type, False):
            yield d

        flazy = (lambda item: item['data'].d.l) if getattr(self, 'lazy', False) else (lambda item: item['data'])

        # now our chidren
        for item in self:
            if not hasattr(flazy(item), 'search'):
                continue
            for d in flazy(item).search(type, True):
                yield d
            continue
        return

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        items = [item for item in self if item['header'].Instance() == type]
        if not items:
            raise KeyError(type)
        if len(items) != 1:
            raise AssertionError("Unexpected number of items ({:d}) of the specified type ({:#x}) was returned".format(len(items), type))
        return items[0]

    def walk(self):
        flazy = (lambda item: item['data'].d.l) if getattr(self, 'lazy', False) else (lambda item: item['data'])
        for item in self:
            yield flazy(item)
        return

    def errors(self):
        for item in self:
            if item.initializedQ() and item.size() == item.blocksize():
                continue
            yield item
        return

    def filter(self, type):
        if isinstance(type, six.integer_types):
            for item in self:
                if item['header'].Instance() == type:
                    yield item
                continue
            return
        flazy = (lambda item: item['data'].d.li) if getattr(self, 'lazy', False) else (lambda item: item['data'])
        for item in self:
            if isinstance(flazy(item), type):
                yield item
            continue
        return

    def __getitem__(self, index):
        flazy = (lambda item: item['data'].d.li) if getattr(self, 'lazy', False) else (lambda item: item['data'])
        if hasattr(self, '_values_') and isinstance(index, six.string_types):
            lookup = { name : value for name, value in self._values_ }
            t = lookup[index]
            iterable = (index for index, item in enumerate(self) if isinstance(flazy(item), t))
            index = next(iterable)
        return super(RecordContainer, self).__getitem__(index)

# yea, a file really is usually just a gigantic list of records...
class File(RecordContainer):
    def blocksize(self):
        return self.source.size() if isinstance(self.source, ptypes.provider.bounded) else super(File, self).blocksize()

    def properties(self):
        res = super(File, self).properties()
        try: res['size'] = self.size()
        except ptypes.error.InitializationError: pass

        try:
            if not operator.contains(res, 'size'):
                res['blocksize'] = self.blocksize()
        except ptypes.error.InitializationError:
            pass
        return res

if __name__ == '__main__':
    from ptypes import *

#    @Record.Define
    class r(pstruct.type):
        type = 0
        _fields_ = [
            (pint.uint32_t, 'a')
        ]

    s = b'\x00\x00\x00\x00\x0c\x00\x00\x00' + b'A'*30
    z = RecordGeneral()
    z.source = provider.string(s)
    print(z.l)
