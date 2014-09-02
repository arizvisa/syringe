'''base structure element'''
from . import ptype,utils,config,pbinary,error
Config = config.defaults
__all__ = 'type,make'.split(',')

class _pstruct_generic(ptype.container):
    def __init__(self, *args, **kwds):
        super(_pstruct_generic,self).__init__(*args, **kwds)
        self.clear()

    def append(self, object):
        """Add an element to a pstruct.type. Return it's index."""
        name = object.shortname()
        current = super(_pstruct_generic,self).append(object)
        self.__fastindex[name.lower()] = current
        return current

    def getindex(self, name):
        if name.__class__ is not str:
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Element names must be of a str type.')
        return self.__fastindex[name.lower()]

    def clear(self):
        self.__fastindex = {}

    def __contains__(self, name):
        if name.__class__ is not str:
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Element names must be of a str type.')
        return name in self.__fastindex

    def keys(self):
        return [name for type,name in self._fields_]

    def values(self):
        return list(self.value)

    def items(self):
        return [(k,v) for k,v in zip(self.keys(), self.values())]

    def __getitem__(self, name):
        if name.__class__ is not str:
            raise error.UserError(self, '_pstruct_generic.__contains__', message='Element names must be of a str type.')
        return super(_pstruct_generic, self).__getitem__(name)

    def __setitem__(self, name, value):
        if not isinstance(value, ptype.type):
            raise error.TypeError(self, '_pstruct_generic.__setitem__', message='Cannot assign a non-ptype (%s) to an element of a container. Use .set instead.'% repr(value.__class__))

        index = self.getindex(name)
        offset = self.value[index].getoffset()

        value.setoffset(offset, recurse=True)
        self.value[index] = value

    def __getstate__(self):
        return super(_pstruct_generic,self).__getstate__(),self.__fastindex,

    def __setstate__(self, state):
        state,self.__fastindex, = state
        super(_pstruct_generic,self).__setstate__(state)

class type(_pstruct_generic):
    '''
    A container for managing structured/named data

    Settable properties:
        _fields_:array( tuple( ptype, name ), ... )<w>
            This contains which elements the structure is composed of
    '''
    _fields_ = None     # list of (type,name) tuples
    initializedQ = lambda s: super(type, s).initializedQ() and len(s.value) == len(s._fields_)
    ignored = ptype.container.ignored.union(('_fields_',))

    def contains(self, offset):
        return super(ptype.container, self).contains(offset)

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.value,path = [],' -> '.join(self.backtrace())
            self.clear()

            try:
                ofs = self.getoffset()
                index = 0
                for i,(t,name) in enumerate(self._fields_):
                    if name in self:
                        _,name = name,'%s_%x'%(name, len(self.value))
                        Config.log.warn("type.load : %s : Duplicate element name %s. Using new name %s : %s", self.instance(), _, name, path)

                    # create each element
                    n = self.new(t, __name__=name, offset=ofs)
                    self.append(n)
                    if ptype.iscontainer(t) or ptype.isresolveable(t):
                        n.load()
                    ofs += n.blocksize()

            except KeyboardInterrupt:
                # XXX: some of these variables might not be defined due to a race. who cares...
                path = ' -> '.join(self.backtrace())
                Config.log.warn("type.load : %s : User interrupt at element %s : %s", self.instance(), n.instance(), path)
                return self

            except error.LoadError, e:
                raise error.LoadError(self, exception=e)
            result = super(type, self).load()
        return result

    def details(self, **options):
        if self.initializedQ():
            return self.__details_initialized(**options)
        return self.__details_uninitialized(**options)

    def repr(self, **options):
        return self.details(**options)

    def __details_uninitialized(self, **options):
        gettypename = lambda t: t.typename() if ptype.istype(t) else t.__name__
        if self.value is None:
            return '\n'.join('[%x] %s %s ???'%(self.getoffset(), utils.repr_class(gettypename(t)), name) for t,name in self._fields_)

        result,o = [],self.getoffset()
        for (t,name),value in map(None,self._fields_,self.value):
            if value is None:
                o = o
                i = utils.repr_class(gettypename(t))
                v = '???' 
                result.append('[%x] %s %s %s'%(o, i, name, v))
                continue
            o = self.getoffset(name)
            i = utils.repr_instance(value.classname(), value.name())
            v = value.summary(**options) if value.initializedQ() else '???' 
            result.append('[%x] %s %s'%( o, i, v ))
        return '\n'.join(result)

    def __details_initialized(self, **options):
        result = ['[%x] %s %s'%(self.getoffset(name), utils.repr_instance(value.classname(),value.name()), value.summary(**options)) for (t,name),value in zip(self._fields_,self.value)]
        if len(result) > 0:
            return '\n'.join(result)
        return '[%x] Empty []'%self.getoffset()

    def set(self, *tuples, **allocator):
        # allocate type if we're asked to
        for name,cls in allocator.items():
            try:
                value = self.new(cls, offset=0, __name__=name)
                value = value.a

            except error.TypeError,e:
                value = cls

            self[name] = value

        # set each value in tuple
        for name,value in tuples:
            self[name].set(value)

        self.setoffset( self.getoffset(), recurse=True )
        return self

    def set(self, value=(), **individual):
        result = self
        if result.initializedQ():
            if value:
                if len(result.value) != len(value):
                    raise error.UserError(result, 'type.set', message='value to assign not of the same length as struct')
                result = super(type,result).set(*value)
            for k,v in individual.iteritems():
                result[k].set(v)
            result.setoffset(result.getoffset(), recurse=True)
            return result
        return result.a.set(value, **individual)

    def __getstate__(self):
        return super(type,self).__getstate__(),self._fields_,

    def __setstate__(self, state):
        state,self._fields_, = state
        super(type,self).__setstate__(state)

def make(fields, **attrs):
    """Given a set of initialized ptype objects, return a pstruct object describing it.

    This will automatically create padding in the structure for any holes that were found.
    """
    fields = set(fields)

    # FIXME: instead of this explicit check, if more than one structure occupies the
    # same location, then we should promote them all into a union.
    if len(set([x.getoffset() for x in fields])) != len(fields):
        raise ValueError('more than one field is occupying the same location')

    types = list(fields)
    types.sort(cmp=lambda a,b: cmp(a.getoffset(),b.getoffset()))

    ofs,result = 0,[]
    for object in types:
        o,n,s = object.getoffset(), object.shortname(), object.blocksize()

        delta = o-ofs
        if delta > 0:
            result.append((ptype.clone(ptype.block,length=delta), '__padding_%x'%ofs))
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
    import ptype,pstruct,provider

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
        import pint
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
        import pint
        class sa(pstruct.type):
            _fields_ = [(pint.uint16_t,'b')]

        class st(pstruct.type):
            _fields_ = [(pint.uint32_t, 'a'),(sa,'b')]

        a = st(source=provider.empty())
        a.set((5, (10,)))
        if a['b']['b'].num() == 10:
            raise Success

if __name__ == '__main__':
    import logging,config
    config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )

