import pickle,marshal

class __type__(object):
    '''Every marshallable type should inherit from this'''
    @classmethod
    def getclass(cls):
        '''Return the class that can be used to construct the object'''
        raise NotImplementedError(cls)

    @classmethod
    def loads(cls, s, **kwds):
        raise NotImplementedError(cls)

    @classmethod
    def dumps(cls, object, **kwds):
        raise NotImplementedError(cls)

    @classmethod
    def repr(cls, object):
        '''Default method for displaying a repr of the object'''
        return repr(object)

class marshallable(__type__):
    import marshal
    @classmethod
    def loads(cls, s, **kwds):
        return marshal.loads(s)

    @classmethod
    def dumps(cls, object, **kwds):
        return marshal.dumps(object)

class container(marshallable):  ## heh, again? really?
    '''A container of dumpable objects'''
    @classmethod
    def loads(cls, s, **kwds):
        object = marshal.loads(s)
        return cls.deserialize(object, **kwds)

    @classmethod
    def dumps(cls, object, **kwds):
        # convert contents to a container of strings
        serialized = cls.serialize(object)
        return marshallable.dumps(serialized, **kwds)

    @classmethod
    def serialize(cls, object, **kwds):
        '''Should need to convert object into a marshallable container of marshallable types'''
        raise NotImplementedError(cls)

    @classmethod
    def deserialize(cls, object, **kwds):
        '''Should expand serializeable object back into it's native type'''
        raise NotImplementedError(cls)

class lookup(object):
    '''Used to search the marshall table'''

    __lookupbyidcache = {}
    __lookupbyclasscache = {}

    @classmethod
    def byid(cls, id):
        return cls.__lookupbyidcache[id]

    @classmethod
    def byclass(cls, type):
        return cls.__lookupbyclasscache[type]

    @classmethod
    def add(cls, type):
        t = type.getclass()
        assert type.id not in cls.__lookupbyidcache, 'attempted duplicate id %s for %s. original type was %s'% (repr(type.id), repr(type), cls.__lookupbyidcache[type.id])
        assert t not in cls.__lookupbyclasscache, 'attempted duplicate class %s for %s. original type was %s'% (repr(t), repr(type), cls.__lookupbyidcache[type.id])
        cls.__lookupbyidcache[type.id] = cls.__lookupbyclasscache[t] = type

    @classmethod
    def loads(cls, s, **kwds):
        id,data = marshal.loads(s)
        t = cls.byid(id)
        return t.loads(data, **kwds)

    @classmethod
    def dumps(cls, object, **kwds):
        t = cls.byclass( __builtins__['type'](object) )
        return marshal.dumps((t.id, t.dumps(object)), **kwds)

### atomic marshallable types

class int(marshallable):
    id = 1
    @classmethod
    def getclass(cls):
        return (0).__class__

class str(marshallable):
    id = 2
    @classmethod
    def getclass(cls):
        return ''.__class__

class none(marshallable):
    id = 0
    @classmethod
    def getclass(cls):
        return None.__class__

class long(marshallable):
    id = 3
    @classmethod
    def getclass(cls):
        return (0L).__class__

### containers of types
class list(container):
    id = 4
    @classmethod
    def getclass(cls):
        return [].__class__

    @classmethod
    def serialize(cls, object, **kwds):
        return [ lookup.dumps(x, **kwds) for x in object ]

    @classmethod
    def deserialize(cls, object, **kwds):
        return [ lookup.loads(x, **kwds) for x in object ]

class tuple(container):
    id = 5
    @classmethod
    def getclass(cls):
        return ().__class__

    @classmethod
    def serialize(cls, object, **kwds):
        return __builtins__['tuple']([lookup.dumps(x, **kwds) for x in object])

    @classmethod
    def deserialize(cls, object, **kwds):
        return __builtins__['tuple']([lookup.loads(x) for x in object])

class dict(container):
    id = 6
    @classmethod
    def getclass(cls):
        return {}.__class__

    @classmethod
    def serialize(cls, object, **kwds):
        return [ (lookup.dumps(k, **kwds), lookup.dumps(v, **kwds)) for k,v in object.items() ]

    @classmethod
    def deserialize(cls, object, **kwds):
        return __builtins__['dict']( (lookup.loads(k, **kwds), lookup.loads(v, **kwds)) for k,v in object )

if False:
    class module(container):
        id = 7
        @classmethod
        def getclass(cls):
            return __builtins__.__class__

        # TODO: need to store each module's contents along with its name
        @classmethod
        def serialize(cls, object, **kwds):
            return [ (lookup.dumps(k, **kwds), lookup.dumps(v, **kwds)) for k,v in object.__dict__.items() ]

        # TODO: instantiate a new module, and then set all of its attributes
        #       (or modify it's __dict__)
        @classmethod
        def deserialize(cls, object, **kwds):
            c = cls.getclass()
            return __builtins__['dict']( (lookup.loads(k, **kwds), lookup.loads(v, **kwds)) for k,v in object )

### special types
class special(container):
    @classmethod
    def serialize(cls, object, **kwds):
        return [(lookup.dumps(k,**kwds), lookup.dumps(getattr(object, k),**kwds)) for k in cls.attributes]

    @classmethod
    def deserialize(cls, object, **kwds):
        object = [((lookup.loads(k,**kwds)), (lookup.loads(v,**kwds))) for k,v in object]
        return cls.new(object, **kwds)

class function(special):
    id = 8
    attributes = ['func_code', 'func_name', 'func_defaults', 'func_closure']

    @classmethod
    def getclass(cls):
        return (lambda:False).__class__

    @classmethod
    def new(cls, object, **kwds):
        c = cls.getclass()
        namespace = kwds.get('namespace', globals())
        object = __builtins__['dict'](object)
        return c(object['func_code'], namespace, object['func_name'], object['func_defaults'], object['func_closure'])

class code(special):
    id = 9
    attributes = [
        'co_argcount', 'co_nlocals', 'co_stacksize', 'co_flags', 'co_code',
        'co_consts', 'co_names', 'co_varnames', 'co_filename', 'co_name',
        'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
    ]

    @classmethod
    def getclass(cls):
        return eval('lambda:False').func_code.__class__

    @classmethod
    def new(cls, object, **kwds):
        c = cls.getclass()
        return c( *(v for k,v in object) )

class instancemethod(special):
    id = 10
#    attributes = ['im_func', 'im_self', 'im_class']
    attributes = ['im_func']
    @classmethod
    def getclass(cls):
        return instancemethod.getclass.__class__

    @classmethod
    def new(cls, object, **kwds):
        c = cls.getclass()
        namespace = kwds.get('namespace', globals())
        object = __builtins__['dict'](object)

        return c( object['im_func'], kwds.get('instance', None), kwds.get('class', None) )

class type(special):
    '''A class....fuck'''
    id = 11
    attributes = ['__name__', '__bases__']
    exclude = set(['__doc__'])

    @classmethod
    def getclass(cls):
        return type.__class__

    @classmethod
    def new(cls, object, **kwds):
        namespace = __builtins__['dict'](object)
        return type.__class__(namespace['__name__'], namespace['__bases__'], namespace)

    @classmethod
    def serialize(cls, object, **kwds):
        # all the attributes we care about
        attrs = [(lookup.dumps(k,**kwds), lookup.dumps(getattr(object, k),**kwds)) for k in cls.attributes]

        # figure out what methods and properties we can copy
        props = []
        for n in dir(object):
            v = getattr(object, n)
            try:
                t = lookup.byclass(v.__class__)
            except KeyError:
                continue

            if (t is type) or (n in cls.exclude):
                continue

            n,v = lookup.dumps(n, **kwds), lookup.dumps(v, **kwds)
            props.append( (n,v) )
        
        return marshal.dumps( (attrs,props) )

    @classmethod
    def deserialize(cls, object, **kwds):
        attrs,props = marshal.loads(object)
        attrs = [((lookup.loads(k,**kwds)), (lookup.loads(v,**kwds))) for k,v in attrs]

        res = cls.new(attrs, **kwds)

        kwds['class'] = res

        for k,v in props:
            k,v = lookup.loads(k,**kwds),lookup.loads(v,**kwds)
            setattr(res, k, v)
        return res

class classobj(type):
    '''A class....fuck'''
    id = 12

    @classmethod
    def getclass(cls):
        t = cls.__class__.__class__
        class obj: pass
        return t(obj)

lookup.add(int)
lookup.add(str)
lookup.add(none)
lookup.add(long)
lookup.add(list)
lookup.add(tuple)
lookup.add(dict)
lookup.add(function)
lookup.add(code)
lookup.add(instancemethod)
lookup.add(type)
lookup.add(classobj)

def dumps(object, **kwds):
    return lookup.dumps(object, **kwds)
def loads(s, **kwds):
    return lookup.loads(s, **kwds)

if __name__ == '__main__':
    import fu; reload(fu)

    data = { 'name' : 'me', 'integer': 1 , 'tuple' : (5,4,3,2, {1:2,3:4})}
    class junk(object):
        property = data
        def test(self):
            return "hi, i'm %x"% id(self)

        def dosomething(self):
            print self.property

    class junk2:
        def test(self):
            return 'ok'
        property = {'name' : 1}


    a = junk
    s = fu.dumps(a)
    b = fu.loads(s)

    _a = a()
    _b = b()

    print a,_a.test(),_a.property
    print b,_b.test(),_b.property
    print a is b

    
