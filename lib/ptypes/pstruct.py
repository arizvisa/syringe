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
    print instance['name1']

    # assign a sub-element
    instance['name2'] = new-instance

    # create an alias
    instance.alias('alternative-name', 'name1')

    # remove an alias
    instance.unalias('alternative-name')
"""
import itertools,operator,functools
import six

from . import ptype,utils,config,pbinary,error
Config = config.defaults
Log = Config.log.getChild(__name__[len(__package__)+1:])
__all__ = 'type,make'.split(',')

class _pstruct_generic(ptype.container):
    def __init__(self, *args, **kwds):
        super(_pstruct_generic, self).__init__(*args, **kwds)
        self.__fastindex = {}

    def alias(self, alias, target):
        """Add an alias from /alias/ to the field /target/"""
        res = self.__getindex__(target)
        self.__fastindex[alias.lower()] = res
    def unalias(self, alias):
        """Remove the alias /alias/ as long as it's not defined in self._fields_"""
        if any(alias.lower() == n.lower() for _,n in self._fields_):
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Not allowed to remove {:s} from aliases'.format(alias.lower()))
        del self.__fastindex[alias.lower()]

    def append(self, object):
        '''L.append(object) -- append an element to a pstruct.type and return its index'''
        return self.__append__(object)
    def __append__(self, object):
        name = object.shortname()
        current = super(_pstruct_generic, self).__append__(object)
        self.__fastindex[name.lower()] = current
        return current

    def __getindex__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not isinstance(name, six.string_types):
            raise error.UserError(self, '_pstruct_generic.__getindex__', message='Element names must be of a str type.')
        try:
            return self.__fastindex[name.lower()]
        except KeyError:
            for i,(_,n) in enumerate(self._fields_):
                if n.lower() == name.lower():
                    return self.__fastindex.setdefault(name.lower(), i)
                continue
        raise KeyError(name)

    ## informational methods
    def properties(self):
        result = super(_pstruct_generic, self).properties()
        if self.initializedQ():
            if len(self.value) < len(self._fields_):
                result['abated'] = True
            elif len(self.value) > len(self._fields_):
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
        return [(k, v) for k, v in self.__items__()]

    ## iterator methods
    def iterkeys(self):
        '''D.iterkeys() -> an iterator over the names of D's fields'''
        for name in self.__keys__(): yield name
    def itervalues(self):
        '''D.itervalues() -> an iterator over the values of D's fields'''
        for res in self.__values__(): yield res
    def iteritems(self):
        '''D.iteritems() -> an iterator over the (name, value) fields of D'''
        for name, value in self.__items__(): yield name, value

    ## internal dict methods
    def __keys__(self):
        for _, name in self._fields_: yield name
    def __values__(self):
        for res in self.value: yield res
    def __items__(self):
        for (_, k), v in itertools.izip(self._fields_, self.value):
            yield k, v
        return

    ## method overloads
    def __contains__(self, name):
        '''D.__contains__(k) -> True if D has a field named k, else False'''
        if not isinstance(name, six.string_types):
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Element names must be of a str type.')
        return name in self.__fastindex

    def __iter__(self):
        '''D.__contains__(k) -> True if D has a field named k, else False'''
        if self.value is None:
            raise error.InitializationError(self, '_pstruct_generic.__iter__')

        for k in six.iterkeys(self):
            yield k
        return

    def __getitem__(self, name):
        '''x.__getitem__(y) <==> x[y]'''
        if not isinstance(name, six.string_types):
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Element names must be of a str type.')
        return super(_pstruct_generic, self).__getitem__(name)

    def __setitem__(self, name, value):
        '''x.__setitem__(i, y) <==> x[i]=y'''
        index = self.__getindex__(name)
        result = super(_pstruct_generic, self).__setitem__(index, value)
        result.__name__ = name
        return result

    def __getstate__(self):
        return super(_pstruct_generic, self).__getstate__(),self.__fastindex,

    def __setstate__(self, state):
        state,self.__fastindex, = state
        super(_pstruct_generic, self).__setstate__(state)

class type(_pstruct_generic):
    '''
    A container for managing structured/named data

    Settable properties:
        _fields_:array( tuple( ptype, name ), ... )<w>
            This contains which elements the structure is composed of
    '''
    _fields_ = None     # list of (type,name) tuples
    ignored = ptype.container.ignored.union(('_fields_',))

    def initializedQ(self):
        if getattr(self.blocksize, 'im_func', None) is ptype.container.blocksize.im_func:
            return super(type, self).initializedQ()

        res = False
        try:
            res = self.size() >= self.blocksize()
        except Exception,e:
            Log.warn("type.initializedQ : {:s} : .blocksize() raised an exception when attempting to determine the initialization state of the instance : {:s} : {:s}".format(self.instance(), e, " -> ".join(self.backtrace())), exc_info=True)
        finally:
            return res

    def copy(self, **attrs):
        result = super(type, self).copy(**attrs)
        result._fields_ = self._fields_[:]
        return result

    def alloc(self, __attrs__={}, **fields):
        """Allocate the current instance. Attach any elements defined in **fields to container."""
        attrs = __attrs__
        result = super(type, self).alloc(**attrs)
        if fields:
            for idx,(t,n) in enumerate(self._fields_):
                if n not in fields:
                    if ptype.isresolveable(t): result.value[idx] = self.new(t, __name__=n).alloc(**attrs)
                    continue
                v = fields[n]
                if ptype.isresolveable(v) or ptype.istype(v):
                    result.value[idx] = self.new(v, __name__=n).alloc(**attrs)
                elif isinstance(v, ptype.generic):
                    result.value[idx] = self.new(v, __name__=n)
                else:
                    result.value[idx].__setvalue__(v)
                continue
            self.setoffset(self.getoffset(), recurse=True)
        return result

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value, path, n = [], " -> ".join(self.backtrace()), None
            self.__fastindex = {}

            try:
                ofs = self.getoffset()
                current = None if getattr(self.blocksize, 'im_func', None) is type.blocksize.im_func else 0
                for i,(t,name) in enumerate(self._fields_):
                    if name in self.__fastindex:
                        _,name = name,u"{:s}_{:x}".format(name, (ofs - self.getoffset()) if Config.pstruct.use_offset_on_duplicate else len(self.value))
                        Log.warn("type.load : {:s} : Duplicate element name {!r}. Using generated name {!r} : {:s}".format(self.instance(), _, name, path))

                    # create each element
                    n = self.new(t, __name__=name, offset=ofs)
                    self.value.append(n)
                    if ptype.iscontainer(t) or ptype.isresolveable(t):
                        n.load()
                    bs = n.blocksize()
                    if current is not None:
                        try: res = self.blocksize()
                        except Exception, e: Log.debug("type.load : {:s} : Custom blocksize raised an exception at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, n.instance(), path), exc_info=True)
                        else:
                            if current + bs >= res:
                                path = " -> ".join(self.backtrace())
                                Log.info("type.load : {:s} : Custom blocksize caused structure to terminate at offset {:#x}, field {!r} : {:s}".format(self.instance(), current, n.instance(), path))
                                break
                        current += bs
                    ofs += bs

            except KeyboardInterrupt:
                path = " -> ".join(self.backtrace())
                if n is None:
                    Log.warn("type.load : {:s} : User interrupt while attempting to load first element. : {:s}".format(self.instance(), path))
                    return self
                Log.warn("type.load : {:s} : User interrupt at element {:s} : {:s}".format(self.instance(), n.instance(), path))
                return self

            except error.LoadError, e:
                raise error.LoadError(self, exception=e)
            result = super(type, self).load()
        return result

    def repr(self, **options):
        return self.details(**options) + '\n'

    def details(self, **options):
        gettypename = lambda t: t.typename() if ptype.istype(t) else t.__name__
        if self.value is None:
            f = functools.partial(u"[{:x}] {:s} {:s} ???".format, self.getoffset())
            res = (f(utils.repr_class(gettypename(t)), name) for t,name in self._fields_)
            return '\n'.join(res)

        result,o = [],self.getoffset()
        fn = functools.partial(u"[{:x}] {:s} {:s} {:s}".format, o)
        for fld, value in map(None, self._fields_, self.value):
            t, name = fld or (value.__class__, value.name())
            if value is None:
                i = utils.repr_class(gettypename(t))
                v = self.new(ptype.type).a.summary(**options)
                result.append(fn(i, name, v))
                continue
            ofs = self.getoffset(value.__name__ or name)
            inst = utils.repr_instance(value.classname(), value.name() or name)
            val = value.summary(**options) if value.initializedQ() else u'???'
            prop = ','.join(u"{:s}={!r}".format(k,v) for k,v in value.properties().iteritems())
            result.append(u"[{:x}] {:s}{:s} {:s}".format(ofs, inst, u" {{{:s}}}".format(prop) if prop else u"", val))
            o += value.size()

        if len(result) > 0:
            return '\n'.join(result)
        return u"[{:x}] Empty[]".format(self.getoffset())

    def __setvalue__(self, *_, **individual):
        result = self
        value, = _ or ((),)

        if result.initializedQ():
            if isinstance(value, dict):
                value = individual.update(value)

            if value:
                if len(result._fields_) != len(value):
                    raise error.UserError(result, 'type.set', message='iterable value to assign with is not of the same length as struct')
                result = super(type, result).__setvalue__(*value)

            for k,v in individual.iteritems():
                idx = self.__getindex__(k)
                if ptype.isresolveable(v) or ptype.istype(v):
                    result.value[idx] = self.new(v, __name__=k).a
                elif isinstance(v, ptype.generic):
                    result.value[idx] = self.new(v, __name__=k)
                else:
                    result.value[idx].set(v)
                continue
            result.setoffset(result.getoffset(), recurse=True)
            return result
        return result.a.__setvalue__(value, **individual)

    def __getstate__(self):
        return super(type, self).__getstate__(),self._fields_,

    def __setstate__(self, state):
        state,self._fields_, = state
        super(type, self).__setstate__(state)

def make(fields, **attrs):
    """Given a set of initialized ptype objects, return a pstruct object describing it.

    This will automatically create padding in the structure for any holes that were found.
    """
    fields = set(fields)

    # FIXME: instead of this explicit check, if more than one structure occupies the
    # same location, then we should promote them all into a union.
    if len(set([x.getoffset() for x in fields])) != len(fields):
        raise ValueError('more than one field is occupying the same location')

    types = sorted(fields, cmp=lambda a,b: cmp(a.getoffset(),b.getoffset()))

    ofs,result = 0,[]
    for object in types:
        o,n,s = object.getoffset(), object.shortname(), object.blocksize()

        delta = o-ofs
        if delta > 0:
            result.append((ptype.clone(ptype.block,length=delta), u'__padding_{:x}'.format(ofs)))
            ofs += delta

        if s > 0:
            result.append((object.__class__, n))
            ofs += s
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
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
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

        global x
        source = provider.string('ABCDEFG')
        x = st(source=source)
        x = x.l
        if x.serialize() == 'ABC':
            raise Success

    @TestCase
    def test_structure_fetch():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint16, 'b'),
                (uint8, 'c'),
            ]

        source = provider.string('ABCDEFG')
        x = st(source=source)
        x = x.l
        if x['b'].serialize() == 'BC':
            raise Success

    @TestCase
    def test_structure_assign_same():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint32, 'b'),
                (uint8, 'c'),
            ]

        source = provider.string('ABCDEFG')
        v = uint32().set('XXXX')
        x = st(source=source)
        x = x.l
        x['b'] = v
        if x.serialize() == 'AXXXXF':
            raise Success

    @TestCase
    def test_structure_assign_diff():
        class st(pstruct.type):
            _fields_ = [
                (uint8, 'a'),
                (uint32, 'b'),
                (uint8, 'c'),
            ]

        source = provider.string('ABCDEFG')
        v = uint16().set('XX')
        x = st(source=source)
        x = x.l
        x['b'] = v
        x.setoffset(x.getoffset(),recurse=True)
        if x.serialize() == 'AXXF' and x['c'].getoffset() == 3:
            raise Success

    @TestCase
    def test_structure_assign_partial():
        class st(pstruct.type):
            _fields_ = [
                (uint32, 'a'),
                (uint32, 'b'),
                (uint32, 'c'),
            ]
        source = provider.string('AAAABBBBCCC')
        x = st(source=source)
        x = x.l
        if x.v is not None and not x.initialized and x['b'].serialize() == 'BBBB' and x['c'].size() == 3:
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
        if a.serialize() == '\x05\x00\x00\x00\x0a\x00\x00\x00\x14\x00\x00\x00':
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

