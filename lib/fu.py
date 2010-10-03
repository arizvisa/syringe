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
        t = kwds.get('type', cls.byid(id))
        return t.loads(data, **kwds)

    @classmethod
    def dumps(cls, object, **kwds):
        t = kwds.get('type', cls.byclass(__builtins__['type'](object)))
        return marshal.dumps((t.id, t.dumps(object, **kwds)))

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
        object = __builtins__['dict'](object)
        return cls.deserialize_dict(object, **kwds)

class function(special):
    id = 8
    attributes = ['func_code', 'func_name', 'func_defaults']

    @classmethod
    def serialize(cls, object, **kwds):
        result = [(lookup.dumps(k,**kwds), lookup.dumps(getattr(object, k),**kwds)) for k in cls.attributes]

        func_closure = getattr(object, 'func_closure')
        if func_closure is None:
            return result + [(lookup.dumps('func_closure'), lookup.dumps(func_closure, type=none))]
        return result + [(lookup.dumps('func_closure'), lookup.dumps(func_closure, type=cell))]

    @classmethod
    def getclass(cls):
        return (lambda:False).__class__

    @classmethod
    def new(cls, code, globals, **kwds):
        '''Create a new function'''
        name = kwds.get('name', code.co_name)
        argdefs = kwds.get('argdefs', ())
        closure = kwds.get('closure', ())
        c = cls.getclass()
        return c(code, globals, name, argdefs, closure)

    @classmethod
    def deserialize_dict(cls, object, **kwds):
        '''Create a new function based on supplied attributes'''
        namespace = kwds.get('namespace', globals())
        return cls.new( object['func_code'], namespace, name=object['func_name'], argdefs=object['func_defaults'], closure=object['func_closure'])

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
    def deserialize_dict(cls, object, **kwds):
        result = (object[k] for k in cls.attributes)
        result = __builtins__['tuple'](result)
        return cls.new(*result)

    @classmethod
    def new(cls, argcount, nlocals, stacksize, flags, codestring, constants, names, varnames, filename='<memory>', name='<unnamed>', firstlineno=0, lnotab='', freevars=(), cellvars=()):
        i,s,t = __builtins__['int'],__builtins__['str'],__builtins__['tuple']
        types = [ i, i, i, i, s, t, t, t, s, s, i, s, t, t ]
        values = [ argcount, nlocals, stacksize, flags, codestring, constants, names, varnames, filename, name, firstlineno, lnotab, freevars, cellvars ]

        for i,t in enumerate(types):
            values[i] = t( values[i] )

        return cls.getclass()(*values)

class instancemethod(special):
    id = 10
#    attributes = ['im_func', 'im_self', 'im_class']
    attributes = ['im_func']
    @classmethod
    def getclass(cls):
        return instancemethod.getclass.__class__

    @classmethod
    def deserialize_dict(cls, object, **kwds):
        c = cls.getclass()
        namespace = kwds.get('namespace', globals())
        return c( object['im_func'], kwds.get('instance', None), kwds.get('class', None) )

    @classmethod
    def new(cls, func, inst, class_):
        return cls.getclass()(function, instance, class_)

class type(special):
    '''A class....fuck'''
    id = 11
    attributes = ['__name__', '__bases__']
    exclude = set(['__doc__'])

    @classmethod
    def getclass(cls):
        return type.__class__

    @classmethod
    def deserialize_dict(cls, object, **kwds):
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

        res = cls.deserialize_dict(attrs, **kwds)

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

class bool(marshallable):
    id = 13
    @classmethod
    def getclass(cls):
        return True.__class__

class cell(marshallable):
    id = 14

    class tuple(object):
        '''class that always produces a cell container'''
        def __new__(name, *args):
            return cell.new(*args)

    @classmethod
    def getclass(cls):
        return cell.tuple

    @classmethod
    def loads(cls, s, **kwds):
        cells = lookup.loads(s)
        return cell.new( *cells )

    @classmethod
    def dumps(cls, object, **kwds):
        result = ( x.cell_contents for x in object )
        return lookup.dumps( __builtins__['tuple'](result) )

    @classmethod
    def new(cls, *args):
        '''Convert args into a cell tuple'''
        # create a closure that we can rip its cell list from
        newinstruction = lambda op,i: op + chr(i&0x00ff) + chr((i&0xff00)/0x100)

        LOAD_CONST = '\x64'     # LOAD_CONST /co_consts/
        LOAD_DEREF = '\x88'     # LOAD_DEREF /co_freevars/
        STORE_DEREF = '\x89'    # STORE_DEREF  /co_cellvars/
        LOAD_CLOSURE = '\x87'   # LOAD_CLOSURE /co_cellvars/
        MAKE_CLOSURE = '\x86'   # MAKE_CLOSURE /number/ ???
        STORE_FAST = '\x7d'     # STORE_FAST /co_varnames/
        LOAD_FAST = '\x7c'      # LOAD_FAST /co_varnames/
        BUILD_TUPLE = '\x66'    # BUILD_TUPLE /length/
        POP_TOP = '\x01'
        RETURN_VALUE = '\x53'

        # generate inner code object
        result = []
        for i in range(len(args)):
            result.append(newinstruction(LOAD_DEREF, i))
            result.append(POP_TOP)
        result.append(newinstruction(LOAD_CONST, 0))
        result.append(RETURN_VALUE)

        freevars = tuple.getclass()( chr(x+65) for x in range(len(args)) )
        innercodeobj = code.new(0, 0, 0, 0, ''.join(result), (None,), (), (), '', '<closure>', 0, '', freevars, ())
    
        # generate outer code object for >= 2.5
        result = []
        for i in range(len(args)):
            result.append( newinstruction(LOAD_CONST, i+1) )
            result.append( newinstruction(STORE_DEREF, i) )
            result.append( newinstruction(LOAD_CLOSURE, i) )

        result.append( newinstruction(BUILD_TUPLE, len(args)) )
        result.append( newinstruction(LOAD_CONST, 0) )
        result.append( newinstruction(MAKE_CLOSURE, 0) )    # XXX: different for <= 2.4
        result.append( RETURN_VALUE )

        outercodestring = ''.join(result)

        # build constants list
        result = list.getclass()(args)
        result.insert(0, innercodeobj)
        constants = tuple.getclass()(result)

        # names within outer code object
        cellvars = tuple.getclass()( chr(x+65) for x in range(len(args)) )
        outercodeobj = code.new(0, 0, 0, 0, outercodestring, constants, (), (), '', '<function>', 0, '', (), cellvars)

        # finally fucking got it
        namespace = globals()
        fn = function.new(outercodeobj, namespace)
        return fn().func_closure

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
lookup.add(bool)
lookup.add(cell)

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

    def test(x):
        def closure():
            print 'hello', x
        return closure

    f = test('computer')

    a = fu.function.dumps(f)
    b = fu.function.loads(a)
    b()

