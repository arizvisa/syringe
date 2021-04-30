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
import functools, itertools, types, builtins, operator

from . import ptype, utils, config, pbinary, error
Config = config.defaults
Log = Config.log.getChild('pstruct')
__all__ = 'type,make'.split(',')

# Setup some version-agnostic types and utilities that we can perform checks with
__izip_longest__ = utils.izip_longest
string_types = utils.string_types

class __structure_interface__(ptype.container):
    def __init__(self, *args, **kwds):
        super(__structure_interface__, self).__init__(*args, **kwds)
        self.__fastindex = {}

    def alias(self, alias, target):
        """Add an alias from /alias/ to the field /target/"""
        res = self.__getindex__(target)
        self.__fastindex[alias.lower()] = res
    def unalias(self, alias):
        """Remove the alias /alias/ as long as it's not defined in self._fields_"""
        if any(alias.lower() == name.lower() for _, name in self._fields_ or []):
            raise error.UserError(self, '__structure_interface__.__contains__', message='Not allowed to remove {:s} from aliases'.format(alias.lower()))
        del self.__fastindex[alias.lower()]

    def append(self, object):
        '''L.append(object) -- append an element to a pstruct.type and return its offset.'''
        return self.__append__(object)

    def __append__(self, object):
        current, name = len(self.value), object.shortname()
        offset = super(__structure_interface__, self).__append__(object)
        self.value[current].setoffset(offset, recurse=True)
        self.__fastindex[name.lower()] = current
        return offset

    def __getindex__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not isinstance(name, string_types):
            raise error.UserError(self, '__structure_interface__.__getindex__', message='Element names must be of a str type.')

        try:
            index = self.__fastindex[name.lower()]
            if 0 <= index < len(self.value):
                return index

        except KeyError:
            pass

        for index, (_, fld) in enumerate(self._fields_ or []):
            if fld.lower() == name.lower():
                return self.__fastindex.setdefault(name.lower(), index)
            continue
        raise KeyError(name)

    ## informational methods
    def __properties__(self):
        result = super(__structure_interface__, self).__properties__()
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
        return name in self.__fastindex

    def __iter__(self):
        '''D.__iter__() <==> iter(D)'''
        if self.value is None:
            raise error.InitializationError(self, '__structure_interface__.__iter__')

        for name in self.iterkeys(self):
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
        return super(__structure_interface__, self).__getstate__(), self.__fastindex,

    def __setstate__(self, state):
        state, self.__fastindex, = state
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

    def initializedQ(self):
        if utils.callable_eq(self.blocksize, ptype.container.blocksize):
            return super(type, self).initializedQ()

        res = self.value is not None
        try:
            res = res and self.size() >= self.blocksize()
        except Exception as E:
            path = str().join(map("<{:s}>".format, self.backtrace()))
            Log.warn("type.initializedQ : {:s} : .blocksize() raised an exception when attempting to determine the initialization state of the instance : {!s} : {:s}".format(self.instance(), E, path), exc_info=True)
        finally:
            return res

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        result._fields_ = self._fields_[:]
        return result

    def alloc(self, **fields):
        """Allocate the current instance. Attach any elements defined in **fields to container."""
        result = super(type, self).alloc()
        if fields:
            for idx, (t, name) in enumerate(self._fields_ or []):
                if name not in fields:
                    if ptype.isresolveable(t):
                        result.value[idx] = self.new(t, __name__=name).a
                    continue
                item = fields[name]
                if ptype.isresolveable(item) or ptype.istype(item):
                    result.value[idx] = self.new(item, __name__=name).a
                elif isinstance(item, ptype.generic):
                    result.value[idx] = self.new(item, __name__=name)
                elif isinstance(item, dict):
                    result.value[idx].alloc(**item)
                else:
                    result.value[idx].set(item)
                continue
            self.setoffset(self.getoffset(), recurse=True)
        return result

    def __append_type(self, offset, cons, name, **attrs):
        if name in self.__fastindex:
            _, name = name, u"{:s}_{:x}".format(name, (ofs - self.getoffset()) if Config.pstruct.use_offset_on_duplicate else len(self.value))
            Log.warn("type.load : {:s} : Duplicate element name {!r}. Using generated name {!r} : {:s}".format(self.instance(), _, name, path))

        res = self.new(cons, __name__=name, offset=offset, **attrs)
        self.value.append(res)
        if ptype.iscontainer(cons) or ptype.isresolveable(cons):
            return res.load()
        return res

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value = []
            self.__fastindex = {}

            # check if the user implement a custom blocksize so we can keep track
            # of how far to populate our structure or if we don't even need to do
            # anything

            # XXX: it might be safer to call .blocksize() and check for InitializationError
            current = None if utils.callable_eq(self.blocksize, type.blocksize) else 0
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
                        except Exception as E:
                            path = str().join(map("<{:s}>".format, self.backtrace()))
                            Log.debug("type.load : {:s} : Custom blocksize raised an exception at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, item.instance(), path), exc_info=True)
                        else:
                            if current + bs > res:
                                path = str().join(map("<{:s}>".format, self.backtrace()))
                                Log.info("type.load : {:s} : Custom blocksize caused structure to terminate at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, item.instance(), path))
                                break
                        current += bs
                    offset += bs

            except error.LoadError as E:
                raise error.LoadError(self, exception=E)

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
        return self.details(**options) + '\n'

    def details(self, **options):
        gettypename = lambda t: t.typename() if ptype.istype(t) else t.__name__
        if self.value is None:
            f = functools.partial(u"[{:x}] {:s} {:s} ???".format, self.getoffset())
            res = (f(utils.repr_class(gettypename(t)), name) for t, name in self._fields_ or [])
            return '\n'.join(res)

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
            value = u'???' if item.value is None else item.summary(**options)
            properties = ','.join(u"{:s}={!r}".format(k, v) for k, v in item.properties().items())
            result.append(u"[{:x}] {:s}{:s} {:s}".format(offset, instance, u" {{{:s}}}".format(properties) if properties else u"", value))
            offset += item.size()

        if len(result) > 0:
            return '\n'.join(result)
        return u"[{:x}] Empty[]".format(self.getoffset())
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
    fields = set(fields)

    # FIXME: instead of this explicit check, if more than one structure occupies the
    # same location, then we should promote them all into a union.
    if len({fld.getoffset() for fld in fields}) != len(fields):
        raise ValueError('more than one field is occupying the same location')

    types = sorted(fields, key=lambda instance: instance.getposition())

    ofs, result = 0, []
    for object in types:
        loc, name, size = object.getoffset(), object.shortname(), object.blocksize()

        delta = loc - ofs
        if delta > 0:
            result.append((ptype.clone(ptype.block, length=delta), u'__padding_{:x}'.format(ofs)))
            ofs += delta

        if size > 0:
            result.append((object.__class__, name))
            ofs += size
        continue
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
    from ptypes import ptype,pstruct,provider,pint

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

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

