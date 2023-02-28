"""Structure container types.

A pstruct.type is used to create a data structure that is keyed by field names.
There are a few basic methods that are provided for a user to derive information
from an instantiated type. A pstruct.type's interface inherits from
ptype.container and will always have a .value that's a list. In most cases, a
pstruct.type can be treated as a python dict.

The pstruct interface provides the following methods on top of the methods
required to provide a mapping-type interface.

    class interface(pstruct.type):
        # the fields describing the format of the structure
        _fields_ = [
            (sub-type, 'name'),
            ...
        ]

        def alias(self, name, target)
            '''Alias the key ``name`` to ``target``.'''
        def unalias(self, name):
            '''Remove the alias ``name``.'''
        def append(self, object):
            '''Append ``object`` to structure keyed by /object.shortname()/'''

Example usage:
    # define a type
    from ptypes import pstruct
    class type(pstruct.type):
        _fields_ = [(subtype1, 'name1'),(subtype2, 'name2']

    # instantiate and load a type
    instance = type()
    instance.load()

    # fetch a particular sub-element
    print(instance['name1'])

    # assign a sub-element
    instance['name2'] = new-instance

    # create an alias
    instance.alias('alternative-name', 'name1')

    # remove an alias
    instance.unalias('alternative-name')
"""
import functools, itertools
from . import ptype, utils, pbinary, error

__all__ = ['type', 'make']

from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'pstruct']))

# Setup some version-agnostic types and utilities that we can perform checks with
__izip_longest__ = utils.izip_longest
string_types = utils.string_types

class __structure_interface__(ptype.container):
    def __init__(self, *args, **kwds):
        super(__structure_interface__, self).__init__(*args, **kwds)
        self.__fastindex__ = {}

    def alias(self, target, *aliases):
        '''Add any of the specified aliases to point to the target field.'''
        res = self.__getindex__(target)
        for item in aliases:
            self.__fastindex__[item.lower()] = res
        return res
    def unalias(self, *aliases):
        '''Remove the specified aliases from the structure.'''
        lowerfields = {name.lower() for _, name in self._fields_ or []}
        loweritems = {item.lower() for item in aliases}
        if lowerfields & loweritems:
            message = "Unable to remove the specified fields ({:s}) from the available aliases.".format(', '.join(item for item in lowerfields & loweritems))
            raise error.UserError(self, '__structure_interface__.unalias', message)
        indices = [self.__fastindex__.pop(item) for item in loweritems if item in self.__fastindex__]
        return len(indices)

    def append(self, object):
        '''L.append(object) -- append an element to a pstruct.type and return its offset.'''
        return self.__append__(object)

    def __append__(self, object):
        current, name = len(self.value), object.shortname()
        offset = super(__structure_interface__, self).__append__(object)
        self.value[current].setoffset(offset, recurse=True)
        self.__fastindex__[name.lower()] = current
        return offset

    def __getindex__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not isinstance(name, string_types):
            raise error.UserError(self, '__structure_interface__.__getindex__', message='Element names must be of a str type.')

        try:
            index = self.__fastindex__[name.lower()]
            if 0 <= index < len(self.value):
                return index

        except KeyError:
            pass

        for index, (_, fld) in enumerate(self._fields_ or []):
            if fld.lower() == name.lower():
                return self.__fastindex__.setdefault(name.lower(), index)
            continue
        raise KeyError(name)

    ## informational methods
    def initializedQ(self):
        if utils.callable_eq(self, self.blocksize, ptype.container, ptype.container.blocksize):
            return super(__structure_interface__, self).initializedQ()

        # if there's no value, we're uninitialized.. plain and simple
        if self.value is None:
            return False

        # otherwise we need to extract the actual and expected sizes.
        try:
            size, blocksize = self.size(), self.blocksize()
        except Exception as E:
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.warning("type.initializedQ : {:s} : instance.blocksize() raised an exception when attempting to determine the initialization state of the instance : {!s} : {:s}".format(self.instance(), E, path), exc_info=True)

        # if we're under the expected size, then we're uninitialized.
        else:
            if size < blocksize:
                return False

        # otherwise we need to check if the fields are initialized at least.
        return all(self.value[index].initializedQ() for index, _ in enumerate(self._fields_))

    def __properties__(self):
        result = super(__structure_interface__, self).__properties__()
        getattr(self, '_fields_', []) or result.setdefault('missing-fields', True)
        if self.initializedQ():
            if len(self.value) < len(self._fields_ or []):
                result['abated'] = True
            elif len(self.value) > len(self._fields_ or []):
                result['inflated'] = True
            return result
        return result

    ## list methods
    def keys(self):
        '''D.keys() -> list of all of the names of D's fields'''
        return [ name for name in self.__keys__() ]
    def values(self):
        '''D.keys() -> list of all of the values of D's fields'''
        return [res for res in self.__values__()]
    def items(self):
        '''D.items() -> list of D's (name, value) fields, as 2-tuples'''
        return [(name, item) for name, item in self.__items__()]

    ## iterator methods
    def iterkeys(self):
        '''D.iterkeys() -> an iterator over the names of D's fields'''
        for name in self.__keys__():
            yield name
        return
    def itervalues(self):
        '''D.itervalues() -> an iterator over the values of D's fields'''
        for res in self.__values__():
            yield res
        return
    def iteritems(self):
        '''D.iteritems() -> an iterator over the (name, value) fields of D'''
        for name, item in self.__items__():
            yield name, item
        return

    ## internal dict methods
    def __keys__(self):
        for _, name in self._fields_ or []:
            yield name
        return
    def __values__(self):
        for item in self.value:
            yield item
        return
    def __items__(self):
        for (_, name), item in zip(self._fields_ or [], self.value):
            yield name, item
        return

    ## method overloads
    def __contains__(self, name):
        '''D.__contains__(k) -> True if D has a field named k, else False'''
        if not isinstance(name, string_types):
            raise error.UserError(self, '__structure_interface__.__contains__', message='Element names must be of a str type.')
        return name.lower() in self.__fastindex__

    def __iter__(self):
        '''D.__iter__() <==> iter(D)'''
        if self.value is None:
            raise error.InitializationError(self, '__structure_interface__.__iter__')

        for name in self.iterkeys():
            yield name
        return

    def __getitem__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not isinstance(name, string_types):
            raise error.UserError(self, '__structure_interface__.__contains__', message='Element names must be of a str type.')
        return super(__structure_interface__, self).__getitem__(name)

    def __setitem__(self, name, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        index = self.__getindex__(name)
        result = super(__structure_interface__, self).__setitem__(index, value)
        result.__name__ = name
        return result

    def __getstate__(self):
        return super(__structure_interface__, self).__getstate__(), self.__fastindex__,

    def __setstate__(self, state):
        state, self.__fastindex__, = state
        super(__structure_interface__, self).__setstate__(state)

class type(__structure_interface__):
    '''
    A container for managing structured/named data

    Settable properties:
        _fields_:array( tuple( ptype, name ), ... )<w>
            This contains which elements the structure is composed of
    '''
    _fields_ = None     # list of (type, name) tuples
    ignored = ptype.container.__slots__['ignored'] | {'_fields_'}

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        result._fields_ = self._fields_[:]
        return result

    def alloc(self, **fields):
        """Allocate the current instance. Attach any elements defined in **fields to container."""
        result = super(type, self).alloc()
        if fields:
            # we need to iterate through all of the fields first
            # in order to consolidate any aliases that were specified.
            # this is a hack, and really we should first be sorting our
            # fields that were provided by the fields in the structure.
            names = [name for _, name in self._fields_ or []]
            fields = {names[self.__getindex__(name)] : item for name, item in fields.items()}

            # now we can iterate through our structure fields to allocate
            # them using the fields given to us by the caller.
            offset = result.getoffset()
            for idx, (t, name) in enumerate(self._fields_ or []):
                if name not in fields:
                    if ptype.isresolveable(t):
                        result.value[idx] = self.new(t, __name__=name, offset=offset).a
                    offset += result.value[idx].blocksize()
                    continue
                item = fields[name]
                if ptype.isresolveable(item) or ptype.istype(item):
                    result.value[idx] = self.new(item, __name__=name, offset=offset).a
                elif isinstance(item, ptype.generic):
                    result.value[idx] = self.new(item, __name__=name, offset=offset)
                elif isinstance(item, dict):
                    result.value[idx].alloc(**item)
                else:
                    result.value[idx].set(item)
                offset += result.value[idx].blocksize()
            self.setoffset(self.getoffset(), recurse=True)
        return result

    def __append_type(self, offset, cons, name, **attrs):
        lowername = name.lower()
        if lowername in self.__fastindex__ and self.__fastindex__[lowername] < len(self.value):
            _, name = name, u"{:s}_{:x}".format(name, (offset - self.getoffset()) if Config.pstruct.use_offset_on_duplicate else len(self.value))
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.warning("type.load : {:s} : Duplicate element name {!r}. Using generated name {!r} : {:s}".format(self.instance(), _, name, path))

        res = self.new(cons, __name__=name, offset=offset, **attrs)
        current = len(self.value)
        self.value.append(res)
        self.__fastindex__[lowername] = current
        if ptype.iscontainer(cons) or ptype.isresolveable(cons):
            return res.load()
        return res

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value = []

            # check if the user implement a custom blocksize so we can keep track
            # of how far to populate our structure or if we don't even need to do
            # anything

            # XXX: it might be safer to call .blocksize() and check for InitializationError
            current = None if utils.callable_eq(self, self.blocksize, type, type.blocksize) else 0
            if current is not None and self.blocksize() <= 0:
                offset = self.getoffset()

                # Populate the structure with undefined fields so that things are still
                # somewhat initialized...
                for i, (t, name) in enumerate(self._fields_ or []):
                    self.__append_type(offset, ptype.undefined, name)
                return super(type, self).load()

            try:
                offset = self.getoffset()
                for i, (t, name) in enumerate(self._fields_ or []):
                    # create each element
                    item = self.__append_type(offset, t, name)

                    # check if we've hit our blocksize
                    bs = item.blocksize()
                    if current is not None:
                        try:
                            res = self.blocksize()
                        except Exception:
                            path = str().join(map("<{:s}>".format, self.backtrace()))
                            Log.debug("type.load : {:s} : Custom blocksize raised an exception at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, item.instance(), path), exc_info=True)
                        else:
                            if current + bs > res:
                                path = str().join(map("<{:s}>".format, self.backtrace()))
                                Log.info("type.load : {:s} : Custom blocksize caused structure to terminate at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, item.instance(), path))
                                break
                        current += bs
                    offset += bs

            except error.LoadError:
                raise error.LoadError(self)

            # add any missing elements with a 0 blocksize
            count = len(self._fields_ or []) - len(self.value)
            if count > 0:
                for i, (t, name) in enumerate(self._fields_[-count:]):
                    item = self.__append_type(offset, t, name, blocksize=lambda: 0)
                    offset += item.blocksize()

            # complete the second pass
            result = super(type, self).load()
        return result

    def repr(self, **options):
        return self.details(**options)

    def details(self, **options):
        gettypename = lambda t: t.typename() if ptype.istype(t) else t.__name__
        if self.value is None:
            formatter = functools.partial(u"[{:x}] {:s} {:s} ???".format, self.getoffset())
            result = (formatter(utils.repr_class(gettypename(t)), name) for t, name in self._fields_ or [])
            return '\n'.join(itertools.chain(result, [] if len(self._fields_ or []) > 1 else ['']))

        result, offset = [], self.getoffset()
        fmt = functools.partial(u"[{:x}] {:s} {:s} {:s}".format, offset)
        for fld, item in __izip_longest__(self._fields_ or [], self.value):
            t, name = fld or (item.__class__, item.name())
            if item is None:
                i = utils.repr_class(gettypename(t))
                item = ptype.undefined().a
                result.append(fmt(i, name, item.summary(**options)))
                continue
            offset = self.getoffset(getattr(item, '__name__', None) or name)
            instance = utils.repr_instance(item.classname(), item.name() or name)
            initialized = item.initializedQ() if isinstance(item, ptype.container) else item.value is not None
            value = item.summary(**options) if initialized else u'???'
            properties = ','.join(u"{:s}={!r}".format(k, v) for k, v in item.properties().items())
            result.append(u"[{:x}] {:s}{:s} {:s}".format(offset, instance, u" {{{:s}}}".format(properties) if properties else u"", value))
            offset += item.size()

        return '\n'.join(itertools.chain(result, [] if len(result) > 1 else ['']))
    def __setvalue__(self, *values, **fields):
        result = self

        if result.initializedQ():
            value, = values or ((),)
            if isinstance(value, dict):
                value = fields.update(value)

            if value:
                if len(result._fields_) != len(value):
                    raise error.UserError(result, 'type.set', message='Refusing to assign iterable to instance due to differing lengths')
                result = super(type, result).__setvalue__(*value)

            for name, item in fields.items():
                idx = self.__getindex__(name)
                if ptype.isresolveable(item) or ptype.istype(item):
                    result.value[idx] = self.new(item, __name__=name).a
                elif isinstance(item, ptype.generic):
                    result.value[idx] = self.new(item, __name__=name)
                elif isinstance(item, dict):
                    result.value[idx].set(**item)
                else:
                    result.value[idx].set(item)
                continue
            result.setoffset(result.getoffset(), recurse=True)
            return result
        return result.a.__setvalue__(*values, **fields)

    def __getstate__(self):
        return super(type, self).__getstate__(), self._fields_,

    def __setstate__(self, state):
        state, self._fields_, = state
        super(type, self).__setstate__(state)

def make(fields, **attrs):
    """Given a set of initialized ptype objects, return a pstruct object describing it.

    This will automatically create padding in the structure for any holes that were found.
    """
    fields = [item for item in fields]
    items = sorted(fields, key=utils.operator.methodcaller('getoffset'))
    grouped = [(offset, [item for item in items]) for offset, items in itertools.groupby(items, key=utils.operator.methodcaller('getoffset'))]
    baseoffset = utils.next(position for position, _ in grouped)

    # FIXME: we need to build a segment tree of all of our items that are grouped
    #        so that we can figure out what elements are overlapped and how we
    #        should group them into a union.
    if attrs.get('offset', baseoffset) > baseoffset:
        raise ValueError("{:s}.make : Unable to specify a base offset ({:#x}) after the offset of any existing fields ({:#x} > {:#x}).".format(__name__, attrs.get('offset', baseoffset), attrs.get('offset', baseoffset), grouped[0][0]))

    # define a closure that will take the provided fields and make them into
    # a dynamic.union type that we can add into a structure.
    from . import dynamic
    def make_union(name, items):
        definition = []
        for index, instance in enumerate(items):
            definition.append((instance.__class__, "anonymous_{:d}".format(1 + index) if getattr(instance, '__name__', None) is None else instance.shortname()))

        # create the union that we plan on returning
        class union_t(dynamic.union):
            pass
        union_t.__name__ = name
        union_t._fields_ = definition
        return union_t

    # iterate through all of the fields that we've grouped, and pad them
    # into a structure type that we can return.
    result, offset = [], attrs.setdefault('offset', baseoffset)
    for expected, items in grouped:
        if len(items) > 1:
            object_t = make_union("__union_{:x}".format(expected), items)
            location, name, size = expected, "field_{:x}".format(expected), object_t().a.blocksize()

        elif len(items) > 0:
            object = items[0]
            location, size = object.getoffset(), object.blocksize()
            object_t, name = object.__class__, "field_{:x}".format(expected) if getattr(object, '__name__', None) is None else object.shortname()

        else:
            Log.warning("{:s}.make : An unexpected number of items ({:d}) were found for the specified offset ({:+#x}).".format(__name__, len(items), expected))
            continue

        delta = location - offset
        if delta > 0:
            result.append((ptype.clone(ptype.block, length=delta), u'__padding_{:x}'.format(offset)))
            offset += delta

        if size > 0:
            result.append((object_t, name))
            offset += size
        continue

    # we need to hack up the offset and place it into the position attribute
    # so that the user's choice will work appear in the constructed type.
    attrs['__position__'] = attrs.pop('offset'),
    return ptype.clone(type, _fields_=result, **attrs)

if __name__ == '__main__':
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)
                raise Failure
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes
    from ptypes import ptype, pstruct, provider, pint

    class uint8(ptype.type):
        length = 1
    class uint16(ptype.type):
        length = 2
    class uint32(ptype.type):
        length = 4

    @TestCase
    def test_structure_serialize():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint8, 'b'),
                (uint8, 'c'),
            ]

        source = provider.bytes(b'ABCDEFG')
        x = st(source=source)
        x = x.l
        if x.serialize() == b'ABC':
            raise Success

    @TestCase
    def test_structure_fetch():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint16, 'b'),
                (uint8, 'c'),
            ]

        source = provider.bytes(b'ABCDEFG')
        x = st(source=source)
        x = x.l
        if x['b'].serialize() == b'BC':
            raise Success

    @TestCase
    def test_structure_assign_same():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint32, 'b'),
                (uint8, 'c'),
            ]

        source = provider.bytes(b'ABCDEFG')
        v = uint32().set(b'XXXX')
        x = st(source=source)
        x = x.l
        x['b'] = v
        if x.serialize() == b'AXXXXF':
            raise Success

    @TestCase
    def test_structure_assign_diff():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint32, 'b'),
                (uint8, 'c'),
            ]

        source = provider.bytes(b'ABCDEFG')
        v = uint16().set(b'XX')
        x = st(source=source)
        x = x.l
        x['b'] = v
        x.setoffset(x.getoffset(),recurse=True)
        if x.serialize() == b'AXXF' and x['c'].getoffset() == 3:
            raise Success

    @TestCase
    def test_structure_assign_partial():
        class st(pstruct.type):
            _fields_ = [
                (uint32, 'a'),
                (uint32, 'b'),
                (uint32, 'c'),
            ]
        source = provider.bytes(b'AAAABBBBCCC')
        x = st(source=source)

        try:
            x = x.l
            raise Failure

        except ptypes.error.LoadError:
            pass

        if x.v is not None and not x.initializedQ() and x['b'].serialize() == b'BBBB' and x['c'].size() == 3:
            raise Success

    @TestCase
    def test_structure_set_uninitialized_flat():
        class st(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        a = st(source=provider.empty())
        a.set(a=5, b=10, c=20)
        if a.serialize() == b'\x05\x00\x00\x00\x0a\x00\x00\x00\x14\x00\x00\x00':
            raise Success

    @TestCase
    def test_structure_set_uninitialized_complex():
        class sa(pstruct.type):
            _fields_ = [(pint.uint16_t, 'b')]

        class st(pstruct.type):
            _fields_ = [(pint.uint32_t, 'a'), (sa, 'b')]

        a = st(source=provider.empty())
        a.set((5, (10,)))
        if a['b']['b'].int() == 10:
            raise Success

    @TestCase
    def test_structure_alloc_value():
        class st(pstruct.type):
            _fields_ = [(pint.uint16_t,'a'),(pint.uint32_t,'b')]
        a = st().alloc(a=0xdead,b=0x0d0e0a0d)
        if a['a'].int() == 0xdead and a['b'].int() == 0x0d0e0a0d:
            raise Success

    @TestCase
    def test_structure_alloc_instance():
        class st(pstruct.type):
            _fields_ = [(pint.uint16_t,'a'),(pint.uint32_t,'b')]
        a = st().alloc(a=pint.uint32_t().set(0x0d0e0a0d),b=0x0d0e0a0d)
        if a['a'].int() == 0x0d0e0a0d and a['b'].int() == 0x0d0e0a0d:
            raise Success

    @TestCase
    def test_structure_alloc_dynamic_value():
        class st(pstruct.type):
            def __b(self):
                return ptype.clone(pint.int_t, length=self['a'].li.int())
            _fields_ = [
                (pint.int8_t, 'a'),
                (__b, 'b'),
            ]
        a = st().alloc(a=3)
        if a['b'].size() == a['a'].int():
            raise Success

    @TestCase
    def test_structure_alloc_dynamic_instance():
        class st(pstruct.type):
            def __b(self):
                return ptype.clone(pint.int_t, length=self['a'].li.int())
            _fields_ = [
                (pint.int_t, 'a'),
                (__b, 'b'),
            ]
        a = st().alloc(a=pint.int32_t().set(4))
        if a['b'].size() == a['a'].int():
            raise Success

    @TestCase
    def test_structure_alloc_container_dynamic_instance():
        class st1(pstruct.type): _fields_=[(pint.int8_t,'a'),(lambda s: ptype.clone(pint.int_t,length=s['a'].li.int()), 'b')]
        class st2(pstruct.type):
            def __b(self):
                if self['a'].li.int() == 2:
                    return st1
                return ptype.undefined
            _fields_ = [
                (pint.int8_t, 'a'),
                (__b, 'b'),
            ]

        a = st2().alloc(b=st1().alloc(a=2))
        if a['b']['a'].int() == a['b']['b'].size():
            raise Success

    @TestCase
    def test_structure_set_initialized_value():
        class st(pstruct.type):
            _fields_ = [
                (pint.int32_t, 'a'),
            ]
        a = st().a.set(a=20)
        if a['a'].int() == 20:
            raise Success

    @TestCase
    def test_structure_set_initialized_type():
        class st(pstruct.type):
            _fields_ = [
                (pint.int_t, 'a'),
            ]
        a = st().a.set(a=pint.uint32_t)
        if a['a'].size() == 4:
            raise Success

    @TestCase
    def test_structure_set_initialized_instance():
        class st(pstruct.type):
            _fields_ = [
                (pint.int_t, 'a'),
            ]
        a = st().a.set(a=pint.uint32_t().set(20))
        if a['a'].size() == 4 and a['a'].int() == 20:
            raise Success

    @TestCase
    def test_structure_set_initialized_container():
        class st1(pstruct.type): _fields_=[(pint.int8_t,'a'),(pint.uint32_t,'b')]
        class st2(pstruct.type):
            _fields_ = [
                (pint.int32_t, 'a'),
                (ptype.undefined, 'b'),
            ]
        a = st2().a.set(b=st1)
        if isinstance(a['b'],st1):
            raise Success

    @TestCase
    def test_structure_set_uninitialized_value():
        class st2(pstruct.type):
            _fields_ = [
                (pint.int32_t, 'a'),
                (ptype.undefined, 'b'),
            ]
        a = st2().set(a=5)
        if a['a'].int() == 5:
            raise Success

    @TestCase
    def test_structure_alloc_field_blocksize():
        class t(ptype.block):
            def blocksize(self):
                res = self.getoffset()
                return 0 if res == 0 else 1

        class st(pstruct.type):
            _fields_ = [
                (pint.int8_t, 'a'),
                (t, 'b'),
            ]
        a = st().alloc(a=3)
        if a.size() == 2:
            raise Success

    @TestCase
    def test_structure_alloc_dynamic_field_blocksize():
        class t(ptype.block):
            def blocksize(self):
                res = self.getoffset()
                return 0 if res == 0 else 1

        class st(pstruct.type):
            _fields_ = [
                (pint.int8_t, 'a'),
                (lambda _: t, 'b'),
            ]
        a = st().alloc(a=3)
        if a.size() == 2:
            raise Success

    @TestCase
    def test_make_structure_padding():
        items = []
        items.append(pint.uint16_t(offset=0x10))
        items.append(pint.uint8_t(offset=0))
        t = pstruct.make(items)
        instance = t().a
        if len(instance.value) == 3 and instance.value[1].size() == 0xf:
            raise Success

    @TestCase
    def test_make_structure_offset_0():
        items = []
        items.append(pint.uint16_t(offset=0x1e))
        items.append(pint.uint8_t(offset=0x10))
        t = pstruct.make(items, offset=0)
        instance = t().a
        if len(instance.value) == 4 and instance.getoffset() == 0 and instance.value[0].size() == 0x10:
            raise Success

    @TestCase
    def test_make_structure_offset_1():
        items = []
        items.append(pint.uint8_t(offset=0x10))
        items.append(pint.uint16_t(offset=0x1e))
        t = pstruct.make(items, offset=0x8)
        instance = t().a
        if len(instance.value) == 4 and instance.getoffset() == 8 and instance.value[0].size() == 0x8:
            raise Success

    @TestCase
    def test_make_structure_offset_2():
        items = []
        items.append(pint.uint8_t(offset=0x10))
        items.append(pint.uint16_t(offset=0x1e))
        t = pstruct.make(items, offset=0x10)
        instance = t().a
        if len(instance.value) == 3 and instance.getoffset() == 0x10 and instance.value[0].size() == 0x1:
            raise Success

    @TestCase
    def test_make_structure_union():
        items = []
        items.append(pint.uint16_t(offset=0x10))
        items.append(pint.uint32_t(offset=4))
        items.append(pint.uint16_t(offset=4))
        items.append(pint.uint8_t(offset=0))
        t = pstruct.make(items)
        instance = t().a
        union, expected = instance.field(4), [4, 2]
        if len(instance.value) == 5 and union.getoffset() == 4 and union.blocksize() == union.size() == 4 and all(union[fld].size() == size for fld, size in zip(union.keys(), expected)):
            raise Success

    @TestCase
    def test_structure_alias_0():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        x = t().alloc(a=1, b=2, c=3)
        x.alias('a', 'myfield')
        if x['myfield'].int() == 1:
            raise Success

    @TestCase
    def test_structure_alias_1():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        x = t().alloc(a=1, b=2, c=3)
        x.alias('a', 'myfield')
        x.set(myfield=5)

        if x['myfield'].int() == 5:
            raise Success

    @TestCase
    def test_structure_alias_2():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]
            def __init__(self, **attrs):
                super(t, self).__init__(**attrs)
                self.alias('b', 'myfield')

        x = t().alloc(a=1, c=3, myfield=20)
        if x['myfield'].int() == 20:
            raise Success

    @TestCase
    def test_structure_unalias_0():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        x = t().alloc(a=1, b=2, c=3)
        try:
            x.unalias('a')
        except Exception:
            raise Success

    @TestCase
    def test_structure_unalias_1():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        x = t().alloc(a=1, b=2, c=3)
        if not x.unalias('item'):
            raise Success

    @TestCase
    def test_structure_unalias_2():
        class t(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        x = t().alloc(a=1, b=2, c=3)
        x.alias('a', 'fuck1', 'fuck2')
        if x.unalias('fuck1', 'fuck2') == 2:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

