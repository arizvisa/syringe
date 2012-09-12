'''serialize/deserialize almost any kind of python object'''

# TODO: add a decorator that can transform anything into an object that will pass an instance of self
#          to serialization service

import __builtin__
import cPickle as pickle

VERSION = '0.6'

# attribute[ignore=list of fu type names] -- ignore serializing/deserializing these types
# attribute[globals=dict] -- use the provided dict as the globals for deserialized objects

# attribute[exclude=list of var names] -- ignore serializing/deserializing these specific names
# attribute[local=list of module names] -- use the local versions of these modules

## FIXME: none of the recurse attributes have been implemented
# attribute[recurse={type name : [list of types]}] -- only recurse into these types from this type
# attribute[norecurse={type name : [list of types]}] -- don't recurse into these types from this type

########
class package:
    @classmethod
    def pack(cls, object, **attributes):
        '''convert any python object into a packable format'''
        st = cls.stash()
        id = st.store(object,**attributes)
        return VERSION,id,st.packed()

    @classmethod
    def unpack(cls, data, **attributes):
        '''unpack data into a real python object'''
        ver,id,data = data
        assert ver == VERSION,'fu.package.unpack : invalid version %s != %s'%(ver,VERSION)
        st = cls.stash()
        st.unpack(data)
        return st.fetch(id,**attributes)

    ### friendly interfaces
    @classmethod
    def dumps(cls, object, **attributes):
        '''convert any python object into a bzip2 encoded string'''
        return pickle.dumps(cls.pack(object,**attributes)).encode('bz2')

    @classmethod
    def loads(cls, data, **attributes):
        '''convert a bzip2 encoded string back into a python object'''
        return cls.unpack(pickle.loads(data.decode('bz2')), **attributes)

    ### stuff that's hidden within this namespace
    class cache(object):
        '''static class for looking up a class used for serializing a particular object'''
        class registration:
            id,type = {},{}

            @staticmethod
            def hash(data):
                return reduce(lambda x,y: (((x<<5)+x)^ord(y)) & 0xffffffff, iter(data), 5381)

        @classmethod
        def register(cls, definition):
            id = cls.registration.hash(definition.__name__)
            if id in cls.registration.id:
                raise KeyError("Duplicate id %x in cache"% id)

            cls.registration.id[id] = definition
            definition.id = id
            return definition

        @classmethod
        def register_type(cls, type):
            '''registers the definition with the specified builtin type'''
            def __register_type_closure(definition):
                if type in cls.registration.type:
                    raise KeyError("Duplicate type %s in cache"% repr(type))

                definition = cls.register(definition)
                cls.registration.type[type] = definition
                return definition
            return __register_type_closure

        @classmethod
        def byid(cls, id):
            '''search through globastate.id for a definition'''
            return cls.registration.id[id]

        @classmethod
        def byclass(cls, type):
            '''search through registration.type for a definition'''
            return cls.registration.type[type]

        @classmethod
        def byinstance(cls, instance):
            '''iterate through all registered definitions to determine which one can work for serialization/deserialization'''

            global package,type_,object_,module_
            type,object,module = __builtin__.type,__builtin__.object,__builtin__.__class__
            t = type(instance)

            # special constants
            if instance in (type, object, module):
                return package.cache.byclass(instance)

            # special types
            if t is type:
                return type_
            elif t is module:
                # FIXME: differentiate between binary modules and pythonic modules
                raise KeyError('module serialization has not been tested to completion yet : %s'% repr(instance))
                return module_

            # any constant
            try:
                return package.cache.byclass(instance)
            except (KeyError,TypeError):
                pass

            # by type
            try:
                return package.cache.byclass(t)
            except (KeyError,TypeError):
                pass

            # builtins for known-modules that can be copied from
            if t == builtin_.getclass():
                if instance.__module__ is None:
                    raise KeyError(instance)
                return builtin_

            # non-serializeable descriptors
            getset_descriptor = cls.__weakref__.__class__
            method_descriptor = cls.__reduce_ex__.__class__
            wrapper_descriptor = cls.__setattr__.__class__
            member_descriptor = type(lambda:wat).func_globals.__class__
            classmethod_descriptor = type(__builtin__.float.__dict__['fromhex'])
            if t in (getset_descriptor,method_descriptor,wrapper_descriptor,member_descriptor,classmethod_descriptor,generator.getclass()):
                raise KeyError(instance)

            # catch-all object
            if hasattr(instance, '__dict__'):
                return object_

            # FIXME: if it follows the pickle protocol..
            if hasattr(instance, '__getstate__'):
                print 'pickled',instance
                import cPickle as pickle
                pickle.loads(pickle.dumps(instance))
                return partial

            raise KeyError(instance)

    class stash(__builtin__.object):
        def __init__(self):
            # cache for .fetch
            self.fetch_cache = {}
            self.store_cache = __builtin__.set()

            # caches for .store
            self.cons_data = {}
            self.inst_data = {}

            # id lookup for .identify
            self.__identity = []

        def __repr__(self):
            cons = [(k,(package.cache.byid(clsid).__name__,v)) for k,(clsid,v) in self.cons_data.iteritems()]
            inst = [(k,(package.cache.byid(clsid).__name__,v)) for k,(clsid,v) in self.inst_data.iteritems()]
            return "<class '%s'> %s"%(self.__class__.__name__, repr(__builtin__.dict(cons)))

        ## packing
        def packed(self):
            return self.cons_data,self.inst_data

        def unpack(self, data):
            cons,inst = data
     
            self.cons_data.clear()
            self.inst_data.clear()
     
            self.cons_data.update(cons)
            self.inst_data.update(inst)
            return True

        def pack_references(self, data, **attributes):
            '''converts object data into reference id's'''
            if data.__class__ is __builtin__.tuple:
                return __builtin__.tuple(self.store(x,**attributes) for x in data)
            elif data.__class__ is __builtin__.dict:
                return __builtin__.dict([(self.store(k,**attributes),self.store(v,**attributes)) for k,v in data.items()])
            return data

        def unpack_references(self, data, **attributes):
            '''converts packed references into objects'''
            if data.__class__ is __builtin__.tuple:
                return __builtin__.tuple([self.fetch(x,**attributes) for x in data])
            elif data.__class__ is __builtin__.dict:
                return __builtin__.dict((self.fetch(k,**attributes),self.fetch(v,**attributes)) for k,v in data.items())
            return data

        def identify(self, object):
            if object in self.__identity:
                return self.__identity.index(object)
            self.__identity.append(object)
            return self.identify(object)

        def __getitem__(self, name):
            return self.identify(name)

        def store(self, object, **attributes):
            identity = self.identify(object)
            if identity in self.store_cache:
                return identity
            cls = package.cache.byinstance(object)

            if True:
                # get naming info
                modulename,name = getattr(object,'__module__',None),getattr(object,'__name__',None)
                fullname = ('%s.%s'% (modulename,name)) if modulename else name

                # attribute[ignore=list of types,exclude=list of names]
                if (cls.__name__ in __builtin__.set(attributes.get('ignore',()))) or \
                    (fullname in __builtin__.set(attributes.get('exclude',()))):
                    cls = partial
                # attribute[local=list of names]
                if name in __builtin__.set(attributes.get('local',())):
                    cls = module

            # store constructor info
            data = cls.p_constructor(object,**attributes)
            self.store_cache.add(identity)
            data = self.pack_references(data,**attributes)
            self.cons_data[identity] = cls.id,data
#            self.cons_data[identity] = cls.id,(modulename,name),data

            # recurse into instance data
            data = cls.p_instance(object,**attributes)
            data = self.pack_references(data,**attributes)

            self.inst_data[identity] = cls.id,data
            return identity

        def fetch(self, identity, **attributes):
            if identity in self.fetch_cache:
                return self.fetch_cache[identity]

            # unpack constructor
#            _,(modulename,name),data = self.cons_data[identity]
            _,data = self.cons_data[identity]
            cls,data = package.cache.byid(_),self.unpack_references(data,**attributes)

            if False:
                # naming info
                fullname = ('%s.%s'% (modulename,name)) if modulename else name

                # attribute[ignore=list of types,exclude=list of names]
                if (cls.__name__ in __builtin__.set(attributes.get('ignore',()))) or \
                    (fullname in __builtin__.set(attributes.get('exclude',()))):
                    cls = partial
                    instance = partial.new()
                    self.fetch_cache[identity] = instance
                    return instance

                # attribute[local=list of names]
                if name in __builtin__.set(attributes.get('local',())):
                    cls = module

            # create an instance of packed object
            instance = cls.u_constructor(data,**attributes)
            self.fetch_cache[identity] = instance

            # update instance with packed attributes
            _,data = self.inst_data[identity]
            cls,data = package.cache.byid(_),self.unpack_references(data,**attributes)
            _ = cls.u_instance(instance,data,**attributes)
            assert instance is _, '%s.fetch(%d) : constructed instance is different from updated instance'% (__builtin__.object.__repr__(self), identity)
            return instance

    class partialinstance(object):
        __name__ = '--incomplete--'
        def __getattr__(self, attribute):
            message = 'unable to access attribute "%s" from partial type "%s"'
            raise Exception(message% (attribute, self.__name__))
        def __call__(self, *args, **kwds):
            message = 'unable to call partial type "%s"'
            raise Exception(message% (self.__name__))
        def __repr__(self):
            return "%s %s"%( self.__class__, self.__name__ )

class __type__(__builtin__.object):
    @classmethod
    def new(cls, *args, **kwds):
        '''instantiate a new instance of the object'''
        return cls.getclass()(*args, **kwds)
    @classmethod
    def getclass(cls):
        raise NotImplementedError(cls)
    @classmethod
    def repr(cls, object):
        '''default method for displaying a repr of an object'''
        return repr(object)

class __marshallable(__type__):
    @classmethod
    def p_constructor(cls, object, **attributes):
        '''returns all arguments required to construct this type'''
        return ()
    @classmethod
    def p_instance(cls, object, **attributes):
        '''return attributes of type that will be used to update'''
        raise NotImplementedError(cls)

    @classmethod
    def u_constructor(cls, data, **attributes):
        '''using the provided data, construct an instance of the object'''
        raise NotImplementedError(cls)

    @classmethod
    def u_instance(cls, instance, data, **attributes):
        '''update the object with the provided data'''
        return instance

class __constant(__marshallable):
    @classmethod
    def new(cls, *args, **kwds):
        return cls.getclass()
    @classmethod
    def p_instance(cls, object, **attributes):
        return ()
    @classmethod
    def u_constructor(cls, data, **attributes):
        return cls.new()

class __builtin(__marshallable):
    @classmethod
    def new(cls, *args, **kwds):
        return cls.getclass()(*args,**kwds)
    @classmethod
    def p_constructor(cls, object, **attributes):
        return object
    @classmethod
    def u_constructor(cls, data, **attributes):
        return cls.new(data)
    @classmethod
    def p_instance(cls, object, **attributes):
        return ()

class __muteable(__marshallable):
    @classmethod
    def p_constructor(cls, object, **attributes):
        return ()
    @classmethod
    def u_constructor(cls, data, **attributes):
        return cls.new(data)

class __special(__marshallable):
    attributes = None

    @classmethod
    def getclass(cls):
        raise NotImplementedError(cls)

    @classmethod
    def p_constructor(cls, object, **attributes):
        result = {}
        if cls.attributes.__class__ == {}.__class__:
            result.update((k,getattr(object,k, cls.attributes[k])) for k in cls.attributes)
        else:
            result.update((k,getattr(object,k)) for k in cls.attributes)
        return result

    @classmethod
    def p_instance(cls, object, **attributes):
        return ()

@package.cache.register_type(package.partialinstance)
class partial(__marshallable):
    '''just a general type for incomplete objects'''
    @classmethod
    def getclass(cls):
        return package.partialinstance
    @classmethod
    def p_constructor(cls, object, **attributes):
        return ()
    @classmethod
    def u_constructor(cls, data, **attributes):
        return cls.new()
    @classmethod
    def p_instance(cls, object, **attributes):
        return ()

### constants
if 'constants':
    @package.cache.register_type(__builtin__.None)
    class none(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.None

    @package.cache.register_type(__builtin__.True)
    class true(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.True

    @package.cache.register_type(__builtin__.False)
    class false(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.False
        
    @package.cache.register_type(__builtin__.type)
    class type(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.type

    @package.cache.register_type(__builtin__.object)
    class object(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.object

    @package.cache.register_type(__builtin__.__class__)
    class module(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.__class__

    @package.cache.register_type(__builtin__.NotImplemented)
    class notImplemented(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.NotImplemented

    @package.cache.register_type(__builtin__.Ellipsis)
    class ellipsis(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.Ellipsis

if 'core':
    @package.cache.register
    class type_(__marshallable):
        # FIXME: when instantiating a hierarchy of types, this fails to associate
        #        the method with the proper parent class. this is apparent if you
        #        compare the help() of the original object to the deserialized object

        @classmethod
        def p_constructor(cls, object, **attributes):
            name,bases = (object.__name__,object.__bases__)
            result = [name]
            result.extend(bases)
            return __builtin__.tuple(result)

        @classmethod
        def u_constructor(cls, data, **attributes):
            result = __builtin__.list(data)
            return __builtin__.type(result.pop(0), __builtin__.tuple(result), {})

        @classmethod
        def p_instance(cls, object, **attributes):
            result = {}

            for k,v in object.__dict__.iteritems():
                try:
                    _ = package.cache.byinstance(v)

                except (KeyError,TypeError):
                    continue

                result[k] = v
            return result

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            for k,v in data.items():
                try:
                    setattr(instance, k, v)
                except (TypeError,AttributeError):
                    pass
            return instance

    @package.cache.register_type(__builtin__.type(package))
    class classobj(type_):
        @classmethod
        def getclass(cls):
            return __builtin__.type(package)

    @package.cache.register
    class object_(type_):
        @classmethod
        def p_constructor(cls, object, **attributes):
            name,type = getattr(object,'__name__',None),object.__class__
            return (name,type,)

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,type = data

            # FIXME: figure out some elegant way to instantiate a type when doing so will actually raise an exception
            #argcount = type.__init__.func_code.co_argcount  # XXX
            #argh = __builtin__.tuple(None for x in range(argcount-1))
            #result = type(*arghs)

            # create an instance illegitimately
            _ = type.__init__ 
            type.__init__ = lambda s: None
            result = type()
            type.__init__ = _

            result.__name__ = name
            return result

if 'builtin':
    @package.cache.register_type(True.__class__)
    class bool(__builtin):
        '''standard boolean type'''
        @classmethod
        def getclass(cls):
            return __builtin__.True.__class__

    @package.cache.register_type((0).__class__)
    class int(__builtin):
        '''integral value'''
        @classmethod
        def getclass(cls):
            return (0).__class__

    @package.cache.register_type(0.0.__class__ )
    class float(__builtin):
        '''float value'''
        @classmethod
        def getclass(cls):
            return 0.0.__class__

    @package.cache.register_type((0L).__class__)
    class long(__builtin):
        '''long value'''
        @classmethod
        def getclass(cls):
            return 0L.__class__

    @package.cache.register_type(0j.__class__)
    class complex(__builtin):
        '''complex value'''
        @classmethod
        def getclass(cls):
            return 0j.__class__

    ## sequence types
    @package.cache.register_type(''.__class__)
    class str(__builtin):
        '''str value'''
        @classmethod
        def getclass(cls):
            return ''.__class__

    @package.cache.register_type(u''.__class__)
    class unicode(__builtin):
        '''unicode string'''
        @classmethod
        def getclass(cls):
            return u''.__class__

    @package.cache.register_type(__builtin__.buffer('').__class__)
    class buffer(__builtin):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return __builtin__.buffer('').__class__

if 'immuteable':
    @package.cache.register_type(().__class__)
    class tuple(__marshallable):
        @classmethod
        def p_constructor(cls, object, **attributes):
            return object
        @classmethod
        def u_constructor(cls, data, **attributes):
            return __builtin__.tuple(data)
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return ()
        @classmethod
        def u_instance(cls, instance, data, **attributes):
            return instance

if 'muteable':
    @package.cache.register_type([].__class__)
    class list(__muteable):
        @classmethod
        def getclass(cls):
            return __builtin__.list
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return __builtin__.tuple(object)
        @classmethod
        def u_instance(cls, instance, data, **attributes):
            '''update the object with the provided data'''
            del(instance[:])
            instance.extend(data)
            return instance

    @package.cache.register_type({}.__class__)
    class dict(__muteable):
        @classmethod
        def getclass(cls):
            return __builtin__.dict
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return object
        @classmethod
        def u_instance(cls, instance, data, **attributes):
            '''update the object with the provided data'''
            instance.clear()
            instance.update(data)
            return instance

    @package.cache.register_type(__builtin__.set)
    class set(__muteable):
        @classmethod
        def getclass(cls):
            return __builtin__.set
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return __builtin__.tuple(object)
        @classmethod
        def u_instance(cls, instance, data, **attributes):
            instance.clear()
            instance.update(data)
            return instance

    @package.cache.register_type(__builtin__.frozenset)
    class frozenset(__muteable):
        @classmethod
        def getclass(cls):
            return __builtin__.frozenset
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return __builtin__.tuple(object)

if 'special':
    @package.cache.register_type(package.cache.register.__class__)
    class instancemethod(__special):
        attributes = ['im_func', 'im_self', 'im_class']

        @classmethod
        def getclass(cls):
            return cls.getclass.__class__

        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data['im_func'], data['im_self'], data['im_class'])

    @package.cache.register_type(__builtin__.property)
    class property(__special):
        attributes=['fdel','fset','fget']
        @classmethod
        def getclass(cls):
            return __builtin__.property

        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(fget=data['fget'], fset=data['fset'], fdel=data['fdel'])

    @package.cache.register_type(eval('lambda:False').func_code.__class__)
    class code(__special):
        attributes = [
            'co_argcount', 'co_nlocals', 'co_stacksize', 'co_flags', 'co_code',
            'co_consts', 'co_names', 'co_varnames', 'co_filename', 'co_name',
            'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
        ] 
        
        @classmethod
        def getclass(cls):
            return eval('lambda:fake').func_code.__class__

        @classmethod
        def new(cls, argcount, nlocals, stacksize, flags, codestring, constants, names, varnames, filename='<memory>', name='<unnamed>', firstlineno=0, lnotab='', freevars=(), cellvars=()):
            i,s,t = __builtin__.int,__builtin__.str,__builtin__.tuple
            optional = lambda x: lambda y: (y,())[y is None]    # FIXME: it'd be less stupid to not ignore the provided type in 'x'
            types = [ i, i, i, i, s, t, t, t, s, s, i, s, optional(t), optional(t) ]
            values = [ argcount, nlocals, stacksize, flags, codestring, constants, names, varnames, filename, name, firstlineno, lnotab, freevars, cellvars ]
            for i,t in enumerate(types):
                values[i] = t( values[i] )
            return cls.getclass()(*values)

        @classmethod
        def u_constructor(cls, data, **attributes):
            result = (data[k] for k in cls.attributes)
            return cls.new(*result)

    @package.cache.register_type((lambda:0).__class__)
    class function(__marshallable):
        @classmethod
        def getclass(cls):
            return (lambda:0).__class__

        @classmethod
        def new(cls, code, globals, **attributes):
            '''Create a new function'''
            name = attributes.get('name', code.co_name)
            argdefs = attributes.get('argdefs', ())
            closure = attributes.get('closure', ())
            c = cls.getclass()
            return c(code, globals, name, argdefs, closure)

        @classmethod
        def p_constructor(cls, object, **attributes):
            # so...it turns out that only the closure property is immuteable
            func_closure = object.func_closure if object.func_closure is not None else ()

            assert object.__module__ is not None, 'FIXME: Unable to serialize an unbound function'
#            return object.__module__,object.func_code,__builtin__.tuple(x.cell_contents for x in func_closure),object.func_globals
            return object.__module__,object.func_code,__builtin__.tuple(x.cell_contents for x in func_closure)

        @classmethod
        def u_constructor(cls, data, **attributes):
#            modulename,code,closure,globals = data
            modulename,code,closure = data
            assert object.__module__ is not None, 'FIXME: Unable to deserialize an unbound function'

            # XXX: assign the globals from commandline
            globals = attributes['globals'] if 'globals' in attributes else module_.search(modulename).__dict__
            result = cls.__new_closure(*closure)
            return cls.new(code, globals, closure=result)
       
        @classmethod
        def p_instance(cls, object, **attributes):
            return object.func_code,object.func_name,object.func_defaults

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            instance.func_code,instance.func_name,instance.func_defaults = data
            return instance

        @classmethod
        def __new_closure(cls, *args):
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

            freevars = __builtin__.tuple( chr(x+65) for x in range(len(args)) )
            innercodeobj = code.new(0, 0, 0, 0, ''.join(result), (None,), (), (), '', '<closure>', 0, '', freevars, ())
        
            # generate outer code object for >= 2.5
            result = []
            for i in range(len(args)):
                result.append( newinstruction(LOAD_CONST, i+1) )
                result.append( newinstruction(STORE_DEREF, i) )
                result.append( newinstruction(LOAD_CLOSURE, i) )

            result.append( newinstruction(BUILD_TUPLE, len(args)) )
            result.append( newinstruction(LOAD_CONST, 0) )
            result.append( newinstruction(MAKE_CLOSURE, 0) )    # XXX: these opcodes are different for <= 2.4
            result.append( RETURN_VALUE )

            outercodestring = ''.join(result)

            # build constants list
            result = list.new(args)
            result.insert(0, innercodeobj)
            constants = __builtin__.tuple(result)

            # names within outer code object
            cellvars = __builtin__.tuple( chr(x+65) for x in range(len(args)) )
            outercodeobj = code.new(0, 0, 0, 0, outercodestring, constants, (), (), '', '<function>', 0, '', (), cellvars)

            # finally fucking got it
            fn = function.new(outercodeobj, {})
            return fn().func_closure

    @package.cache.register
    class module_local(__constant):
        # module that is locally stored
        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__name__,object.__doc__

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,doc = data
            return __import__(name)

        @classmethod
        def search(cls, modulename, doc=None):
            try:
                return __import__(modulename)
            except ImportError:
                pass
            return cls.new(modulename, doc)

    @package.cache.register
    class module_(module_local):
        # a module and it's attributes
        @classmethod
        def u_constructor(cls, data, **attributes):
            name,doc = data
            return cls.new(name,doc)

        @classmethod
        def p_instance(cls, object, **attributes):
            return object.__dict__

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            for k,v in data.items():
                setattr(instance, k, v)
            return instance

if True:
#    @package.cache.register_type(__builtin__.setattr.__class__)
    @package.cache.register
    class builtin_(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.setattr.__class__

        @classmethod
        def p_constructor(cls, object, **attributes):
            return (object.__module__, object.__name__)

        @classmethod
        def u_constructor(cls, data, **attributes):
            m,n = data
            return getattr(__import__(m),n)

#    @package.cache.register_type( (x for x in (0,)) )
    @package.cache.register
    class generator(__marshallable):
        @classmethod
        def getclass(cls):
            return (x for x in (0,)).__class__

#    @package.cache.register_type( (x for x in (0,)).gi_frame.__class__ )
    @package.cache.register
    class frame(__marshallable):
        @classmethod
        def getclass(cls):
            return (x for x in (0,)).gi_frame.__class__

    @package.cache.register_type(__builtin__.staticmethod)
    class staticmethod_(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.staticmethod

    @package.cache.register_type(__builtin__.classmethod)
    class classmethod_(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.classmethod

def dumps(object, **attributes):
    '''convert a python object to a string'''
    return package.dumps(object, **attributes)
def loads(data, **attributes):
    '''convert a string back into a python object'''
    return package.loads(data, **attributes)

if __name__ == '__main__':
    import traceback
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass
    Werror = True

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            global Werror
            name = fn.__name__
            try:
                res = fn(**kwds)

            except Success:
                print '%s: Success'% name
                return True

            except Failure,e:
                pass

            except Exception,e:
                print '%s: Exception raised'% name
                if Werror:
                    raise

                print traceback.format_exc()

            print '%s: Failure'% name
            return False

        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    from __builtin__ import *
    import fu

    # lame helpers for testcases
    def make_package(cls, cons, inst):
        m,n = '__main__', 'unnamed'
        result = (fu.VERSION, 0, ({0:(cls.id,cons)},{0:(cls.id,inst)})) 
#        result = (fu.VERSION, 0, ({0:(cls.id,(m,n),cons)},{0:(cls.id,inst)})) 
        return result
    def extract_package(package):
        _,id,(cons,inst) = package
        return id,cons,inst
    def check_package(package):
        ver,id,(cons,inst) = package
        if set(cons.keys()) != set(inst.keys()):
            return False
        if ver != fu.VERSION:
            return False
        return id in cons

    class A(object): pass
    class B(A):
        def method(self):
            return 'B'
    class C1(B):
        def method_c1(self):
            return 'C1'
    class C2(B):
        def method_c2(self):
            return 'C2'
    class D(C1, C2):
        def method_c1(self):
            return 'D'

if __name__ == '__main__':
    @TestCase
    def test_pack_type():
        input = True
        result = fu.package.pack(input)
        if check_package(result):
            raise Success

    @TestCase
    def test_builtin_pack():
        input = 0x40
        result = fu.package.pack(input)
        id,cons,inst = extract_package(result)
        if cons[id][-1] == input:
            raise Success

    @TestCase
    def test_builtin_unpack():
        input = make_package(fu.bool,True,())
        result = fu.package.unpack(input)
        if result == True:
            raise Success

    @TestCase
    def test_constant_unpack():
        input = make_package(fu.none,(),())
        result = fu.package.unpack(input)
        if result == None:
            raise Success

    @TestCase
    def test_list_pack():
        l = range(5)
        result = fu.package.pack(l)
        id,cons,inst = extract_package(result)
        if check_package(result) and len(cons) == len(l)+1:
            raise Success

    @TestCase
    def test_listref_pack():
        a = range(5)
        l = [a,a,a,a]
        result = fu.package.pack(l)
        id,cons,inst = extract_package(result)
        if check_package(result) and len(cons) == len(a)+1+1:
            raise Success

    @TestCase
    def test_listrecurse_pack():
        a = []
        a.append(a)
        result = fu.package.pack(a)
        id,cons,inst = extract_package(result)
        if inst[id][1][0] == id:
            raise Success

    @TestCase
    def test_dict_pack():
        l = {'hello':'world', 5:10, True:False}
        result = fu.package.pack(l)
        id,cons,inst = extract_package(result)
        if check_package(result) and len(cons) == len(l)*2 + 1:
            raise Success

    @TestCase
    def test_dictref_pack():
        a = range(5)
        l = {'hello':a, 'world':a}
        result = fu.package.pack(l)
        id,cons,inst = extract_package(result)
        if len(inst) == len(a)+1 + len(l)+1:
            raise Success

    @TestCase
    def test_dictrecurse_pack():
        a = {}
        a[5] = a
        result = fu.package.pack(a)
        id,cons,inst = extract_package(result)
        if len(a) == 1 and check_package(result) and inst[id][1].values()[0] == id:
            raise Success

    @TestCase
    def test_listref_unpack():
        a = [5]
        a.append(a)
        data = fu.package.pack(a)
        y = fu.package.unpack(data)
        if y[1][1][0] == 5:
            raise Success

    @TestCase
    def test_dictref_unpack():
        a = {}
        a[5] = __builtin__.None
        a[6] = a
        data = fu.package.pack(a)
        y = fu.package.unpack(data)
        if y[6][5] is __builtin__.None:
            raise Success

    @TestCase
    def test_code_packunpack():
        def func(*args):
            return ' '.join(args)
        a = fu.package.pack(func.func_code)
        b = fu.package.unpack(a)
        if func.func_code.co_name == b.co_name and func.func_code is not b:
            raise Success
        
    @TestCase
    def test_func_packunpack():
        def func(*args):
            return ' '.join(args)
        a = fu.package.pack(func)
        b = fu.package.unpack(a)
        if func is not b and b('hello','world') == 'hello world':
            raise Success

    @TestCase
    def test_type_packunpack():
        class blah(object):
            def func(self, *args):
                return ' '.join(args)
        a = fu.package.pack(blah)
        b = fu.package.unpack(a)
        b = b()
        if b.func('hello','world') == 'hello world':
            raise Success

    @TestCase
    def test_instance_packunpack():
        class blah(object):
            def func(self, *args):
                return ' '.join(args)
        a = fu.package.pack(blah())
        b = fu.package.unpack(a)
        if b.func('hello','world') == 'hello world':
            raise Success

    @TestCase
    def test_typevalue_packunpack():
        class blah(object):
            junk = 'whee'
        a = fu.package.pack(blah)
        b = fu.package.unpack(a)
        if b.junk == 'whee':
            raise Success

    @TestCase
    def test_instancevalue_packunpack():
        class blah(object):
            junk = 'whee'
        a = fu.package.pack(blah())
        b = fu.package.unpack(a)
        if b.junk == 'whee':
            raise Success

    @TestCase
    def test_class_packunpack():
        p = fu.package.pack(A)
        result = fu.package.unpack(p)
        if result.__name__ == 'A':
            raise Success

    @TestCase
    def test_multiclass_packunpack():
        p = fu.package.pack(B)
        result = fu.package.unpack(p)
        if result().method() == 'B':
            raise Success

    @TestCase
    def test_derived_packunpack():
        p = fu.package.pack(C1)
        result = fu.package.unpack(p)
        if result().method() == 'B':
            raise Success

    @TestCase
    def test_multiclass_packunpack():
        p = fu.package.pack(C1)
        result = fu.package.unpack(p)
        if result().method_c1() == 'C1' and result().method() == 'B':
            raise Success

    @TestCase
    def test_multiinheritance_packunpack():
        p = fu.package.pack(D)
        result = fu.package.unpack(p)
        if result().method_c1() == 'D' and result().method_c2() == 'C2':
            raise Success

    @TestCase
    def test_python_gay():
        class test(object):
            def fiver(self):
                return 5

        class test2(test):
            def tenor(self):
                return 10

        a = test2()
        identity = id(a.tenor) == id(a.fiver)
        assert identity is True, "yay, your python isn't lying about id being unique"
        if a.tenor() != a.fiver():
            raise Success

    @TestCase
    def test_func_closure():
        def fn(a1,a2):
            def closure(a3):
                return (a1+a2)*a3
            return closure

        a = fn(1,2)
        b = fu.package.pack(a)
        c = fu.package.unpack(b)
        if a(222) == int(c('6')):
            raise Success

    @TestCase
    def test_ignore_modulepack():
        import sys
        a = fu.package.pack(sys, local=('sys',))
        _,x,y = a
        if y[0][x][0] is not fu.module.id:
            raise Failure

        b = fu.package.unpack(a)
        if sys.winver is b.winver:
            raise Success

    @TestCase
    def test_ignore_moduleunpack():
        import _ast
        a = fu.package.pack(_ast)
        _,x,y = a
        if y[0][x][0] is not fu.module_.id:
            raise Failure

        b = fu.package.unpack(a, local=('_ast',))
        if b is _ast:
            raise Success

    @TestCase
    def test_ptype_pack():
        from ptypes import pint
        a = pint.uint32_t()
        a.setoffset(id(__builtin__.type))
        result = a.l.value
        b = fu.package.unpack(fu.package.pack(a))
        if b.value == result:
            raise Success

    @TestCase
    def test_unknown_type():
        # error while serializing a 'TypeInfo' object which comes from a module implemented in C
        #   if we can 
        import xml.dom.minidom
        global a,b
        a = fu.package.pack(xml.dom.minidom)
        b = fu.package.unpack(a)

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

