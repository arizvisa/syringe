'''serialize/deserialize almost any kind of python object'''

# TODO:
#       memoryview -- not possible? .tolist or .tobytes will return the data, but i haven't found a way to get the object that it references
#       bytearray -- use str() to get the data
#       operator.methodcaller -- can be done by using an object with __getattr__ for the name, and grabbing the method's *args,**kwds for the default args. hopefully doing this doesn't influence state...

# TODO: add a decorator that can transform anything into an object that will pass an instance of self
#          to serialization service

import __builtin__,itertools
__all__ = ['caller','pack','unpack','loads','dumps']

VERSION = '0.7'

## FIXME: none of these are enabled due to their hackiness, search for XXX
# attribute[ignore=list of fu type names] -- ignore serializing/deserializing these types
# attribute[globals=dict] -- use the provided dict as the globals for deserialized objects

# attribute[exclude=list of var names] -- ignore serializing/deserializing these specific names
# attribute[local=list of module names] -- use the local versions of these modules

# attribute[recurse={type name : [list of types]}] -- only recurse into these types from this type
# attribute[norecurse={type name : [list of types]}] -- don't recurse into these types from this type

########
class package:
    '''
    This class is responsible for exposing the interface used to marshal/unmarshal
    an object. The reason for the class is to close around the internals of this
    module hiding the functionality that is used for serialization. The only
    interfaces that are exposed are the pack() and unpack() classmethods.
    '''

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

    ### stuff that's hidden within this namespace
    class cache(object):
        '''
        This class is used to handle the registration of the different serializers
        and deserializers for a python type/constant. The registration of the
        different implementations is done via decorator at which point one can
        use the .by*() classmethods to identify the handler for their type or
        instance.
        '''
        class registration:
            id,const,type = {},{},{}

            @staticmethod
            def hash(data):
                return reduce(lambda x,y: (((x<<5)+x)^ord(y)) & 0xffffffff, iter(data), 5381)

        ## registration of a cls into cache
        @classmethod
        def register(cls, definition):
            id = cls.registration.hash(definition.__name__)
            if id in cls.registration.id:
                raise KeyError, "Duplicate id %x in cache"% id

            cls.registration.id[id] = definition
            definition.id = id
            return definition

        @classmethod
        def register_type(cls, definition):
            '''registers the definition with the specified builtin type'''
            type = definition.getclass()
            if type in cls.registration.type:
                raise KeyError, "Duplicate type %r in cache"% type

            definition = cls.register(definition)
            cls.registration.type[type] = definition
            return definition

        @classmethod
        def register_const(cls, definition):
            const = definition.getclass()
            if const in cls.registration.const:
                raise KeyError, "Duplicate constant %r in cache"% const
            definition = cls.register(definition)
            cls.registration.const[const] = definition
            return definition

        ## determining a registered cls from various types
        @classmethod
        def byid(cls, id):
            '''search through globastate.id for a definition'''
            return cls.registration.id[id]

        @classmethod
        def byclass(cls, type):
            '''search through registration.type for a definition'''
            return cls.registration.type[type]

        @classmethod
        def byconst(cls, const):
            '''search through registration.const for a definition'''
            result = cls.registration.const[const]
            if result.getclass() is not const:
                raise KeyError, const
            return result

        @classmethod
        def byinstance(cls, instance):
            '''iterate through all registered definitions to determine which one can work for serialization/deserialization'''
            global package,object_,module_
            type,object,module = __builtin__.type,__builtin__.object,__builtin__.__class__
            t = type(instance)

            # any constant
            try:
                return package.cache.byconst(instance)
            except (KeyError,TypeError):
                pass

            # special types
            if t is module and instance is not module:
                # XXX: implement binary modules
                if hasattr(instance, '__file__'):
                    if instance.__file__.endswith('.pyd'):
                        raise NotImplementedError, 'Binary modules are un-supported'
                    return module_
                return module_local

            # by type
            try:
                return package.cache.byclass(t)
            except (KeyError,TypeError):
                pass

            # builtins for known-modules that can be copied from
            if t == builtin_.getclass():
                if instance.__module__ is None:
                    return partial  # XXX
                    raise KeyError, (instance,'Unable to determine module name from builtin method')
                return builtin_

            # catch-all object
            if hasattr(instance, '__dict__') or hasattr(instance, '__slots__'):     # is this an okay assumption?
                return object_

            # FIXME: if it follows the pickle protocol..
            if hasattr(instance, '__getstate__'):
                raise NotImplementedError, 'Pickle protocol for type %r is unimplemented'% instance
                pickle.loads(pickle.dumps(instance))
                return partial

            raise KeyError, instance

    class stash(__builtin__.object):
        '''
        This class is used to recursively serialize/deserialize an instance or
        type. It is temporarily constructed and will use the cache to identify
        how to serialize/deserialize the data that is passed to it. Once all
        the references are processed, a tuple of the objects and constants are
        then returned. This can then be re-packed into a bytestream which can
        then be transported wherever the user needs it.
        '''

        def __init__(self):
            # cache for .fetch
            self.fetch_cache = {}
            self.store_cache = __builtin__.set()

            # caches for .store
            self.cons_data = {}
            self.inst_data = {}

        @staticmethod
        def clsbyid(n): return package.cache.byid(n)
        @staticmethod
        def clsbyinstance(n): return package.cache.byinstance(n)

        def __repr__(self):
            cons = [(k,(self.clsbyid(clsid).__name__,v)) for k,(clsid,v) in self.cons_data.iteritems()]
            inst = [(k,(self.clsbyid(clsid).__name__,v)) for k,(clsid,v) in self.inst_data.iteritems()]
            return "<class '%s'> %s"%(self.__class__.__name__, repr(__builtin__.dict(cons)))

        ## serializing/deserializing entire state
        def packed(self):
            return self.cons_data,self.inst_data

        def unpack(self, data):
            cons,inst = data

            self.cons_data.clear()
            self.inst_data.clear()

            self.cons_data.update(cons)
            self.inst_data.update(inst)
            return True

        ## packing/unpacking of id's
        def pack_references(self, data, **attributes):
            '''converts object data into reference id's'''
            if data.__class__ is __builtin__.tuple:
                return __builtin__.tuple(self.store(x,**attributes) for x in data)
            elif data.__class__ is __builtin__.dict:
                return __builtin__.dict((self.store(k,**attributes),self.store(v,**attributes)) for k,v in data.items())
            elif data.__class__ is __builtin__.list:
                # a list contains multiple packed objects
                return [self.pack_references(x, **attributes) for x in data]
            return data

        def unpack_references(self, data, **attributes):
            '''converts packed references into objects'''
            if data.__class__ is __builtin__.tuple:
                return __builtin__.tuple(self.fetch(x,**attributes) for x in data)
            elif data.__class__ is __builtin__.dict:
                return __builtin__.dict((self.fetch(k,**attributes),self.fetch(v,**attributes)) for k,v in data.items())
            elif data.__class__ is __builtin__.list:
                return [self.unpack_references(x, **attributes) for x in data]
            return data

        def identify(self, object):
            return id(object)

            # unique id generator for .identify if id is not guaranteed to be unique (python 2.6?)
            #if not hasattr(self, '__identity'):
            #    self.__identity = []

            #if object in self.__identity:
            #    return self.__identity.index(object)
            #self.__identity.append(object)
            #return self.identify(object)

        def __getitem__(self, name):
            return self.identify(name)

        ### stashing/fetching of objects
        def store(self, object, **attributes):
            identity = self.identify(object)
            if identity in self.store_cache:
                return identity
            cls = self.clsbyinstance(object)

            if False:       # XXX: if we want to make the module and name part of the protocol. (for assistance with attributes)
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
#            self.cons_data[identity] = cls.id,(modulename,name),data   # XXX: for attributes by name

            # recurse into instance data
            data = cls.p_instance(object,**attributes)
            data = self.pack_references(data,**attributes)

            self.inst_data[identity] = cls.id,data
            return identity

        def fetch(self, identity, **attributes):
            if identity in self.fetch_cache:
                return self.fetch_cache[identity]

            # unpack constructor
#            _,(modulename,name),data = self.cons_data[identity]    # XXX: for attributes by name
            _,data = self.cons_data[identity]
            cls,data = self.clsbyid(_),self.unpack_references(data,**attributes)

            if False:   # XXX: attributes
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
            cls,data = self.clsbyid(_),self.unpack_references(data,**attributes)
            _ = cls.u_instance(instance,data,**attributes)
            assert instance is _, '%s.fetch(%d) : constructed instance is different from updated instance'% (__builtin__.object.__repr__(self), identity)
            return instance

class __type__(__builtin__.object):
    '''
    This base class is used to help register an instance of a type. Once
    identifying the type of an instance, the class will be responsible for
    returning any attributes that are necessary to re-construct or
    re-instantiate that object.
    '''

    @classmethod
    def getclass(cls, *args, **kwds):
        '''
        This returns the type to search for. The type is snuck from an instance
        by using the __class__ attribute.
        '''
        raise NotImplementedError, cls

    @classmethod
    def new(cls):
        '''
        This method returns an instance of the type that the class is supposed
        to be responsible for.
        '''
        return cls.getclass()

    @classmethod
    def repr(cls, object):
        '''
        This method will output an instance in a readable manner.
        '''
        return repr(object)

    @classmethod
    def p_constructor(cls, object, **attributes):
        '''
        This method will extract any attributees that are required to create
        the initial instance of a type. The necessary attributes are then
        returned as a tuple.
        '''
        return ()

    @classmethod
    def p_instance(cls, object, **attributes):
        '''
        This method will extract any attributes that will be updated after
        the type has been instantiated. It is prudent to note that these
        attributes are not necessary to construct the object, only that the
        object's users expect these fields to be set. The necessary attributes
        are then returned as a tuple.
        '''
        raise NotImplementedError, cls

    @classmethod
    def u_constructor(cls, data, **attributes):
        '''
        This method will take the tuple that is provided by the data parameter,
        and use it to re-instantiate the specified type. The tuple in data is
        the same as the tuple returned by the p_constructor() classmethod. The
        method will return the properly instantiated type.
        '''
        raise NotImplementedError, cls

    @classmethod
    def u_instance(cls, instance, data, **attributes):
        '''
        This method will take the tuple that is provided by the data parameter,
        and do whatever is necessary to update the instance parameter with it.
        This can include (but is not limited to), assigning any attributes with
        the setattr() keyword, calling any methods to update the state, etc.
        The tuple in data corresponds to the tuple returned by the p_instance()
        classmethod. The method will then return the instance that was updated.
        '''
        return instance

@package.cache.register_type
class partial(__type__):
    '''just a general type for incomplete objects'''
    class partialinstance(object):
        __name__ = '--incomplete--'
        def __getattr__(self, attribute):
            message = 'unable to access attribute "%s" from partial type "%s"'
            raise Exception, message% (attribute, self.__name__)
        def __call__(self, *args, **kwds):
            message = 'unable to call partial type "%s"'
            raise Exception, message% (self.__name__)
        def __repr__(self):
            return "%s %s"%( self.__class__, self.__name__ )

    @classmethod
    def getclass(cls):
        return cls.partialinstance
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
    class __constant(__type__):
        '''
        This parent class is used to assist defining a constant. A constant
        will typically not have any attributes or anything and in most cases
        will only exist once in an interpreter. These are things like the
        "object" type, or "float" type, etc.
        '''

        @classmethod
        def new(cls, *args, **kwds):
            '''
            This method will create a new instance of the class returned by
            the getclass() classmethod with the parameters provided as its
            arguments.
            '''
            return cls.getclass()(*args, **kwds)
        @classmethod
        def p_instance(cls, object, **attributes):
            '''
            As the type is a constant, there are no attributes that are needed
            to update the type. This method will simply return an empty tuple.
            '''
            return ()
        @classmethod
        def u_constructor(cls, data, **attributes):
            '''
            As the type is a constant, there are no parameters needed to
            construct it. this method will simply return the type returned by
            the getclass() classmethod.
            '''
            return cls.getclass()

    @package.cache.register_const
    class type(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.type

    @package.cache.register_const
    class object(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.object

    @package.cache.register_const
    class module(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.__class__

        @classmethod
        def instancelocal(cls, modulename, **kwds):
            # XXX: this might be broken when re-constructing package modules
            #      where relative imports are used.
            return __import__(modulename)

        @classmethod
        def instance(cls, modulename, doc=None):
            try:
                return cls.instancelocal(modulename, doc=doc)
            except ImportError:
                pass
            return cls.new(modulename, doc)

    @package.cache.register_const
    class bool(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.True.__class__

    @package.cache.register_const
    class int(__constant):
        @classmethod
        def getclass(cls):
            return (0).__class__

    @package.cache.register_const
    class float(__constant):
        @classmethod
        def getclass(cls):
            return 0.0.__class__

    @package.cache.register_const
    class long(__constant):
        @classmethod
        def getclass(cls):
            return 0L.__class__

    @package.cache.register_const
    class complex(__constant):
        @classmethod
        def getclass(cls):
            return 0j.__class__

    @package.cache.register_const
    class str(__constant):
        @classmethod
        def getclass(cls):
            return ''.__class__

    @package.cache.register_const
    class unicode(__constant):
        @classmethod
        def getclass(cls):
            return u''.__class__

    @package.cache.register_const
    class buffer(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.buffer('').__class__

    @package.cache.register_const
    class tuple(__constant):
        @classmethod
        def getclass(cls):
            return (().__class__)

    @package.cache.register_const
    class list(__constant):
        @classmethod
        def getclass(cls):
            return [].__class__

    @package.cache.register_const
    class dict(__constant):
        @classmethod
        def getclass(cls):
            return {}.__class__

    @package.cache.register_const
    class set(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.set

    @package.cache.register_const
    class frozenset(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.frozenset

    @package.cache.register_const
    class instancemethod(__constant):
        @classmethod
        def getclass(cls):
            return cls.getclass.__class__

    @package.cache.register_const
    class property(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.property

    @package.cache.register_const
    class code(__constant):
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

    @package.cache.register_const
    class function(__constant):
        @classmethod
        def getclass(cls):
            return (lambda:0).__class__

        @classmethod
        def new(cls, code, globs, **attributes):
            '''Create a new function'''
            name = attributes.get('name', code.co_name)
            argdefs = attributes.get('argdefs', ())
            closure = attributes.get('closure', ())
            c = cls.getclass()
            return c(code, globs, name, argdefs, closure)

    @package.cache.register_const
    class builtin(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.setattr.__class__

    @package.cache.register_const
    class generator(__constant):
        @classmethod
        def getclass(cls):
            return (x for x in (0,)).__class__

    @package.cache.register_const
    class frame(__constant):
        @classmethod
        def getclass(cls):
            return (x for x in (0,)).gi_frame.__class__

    @package.cache.register_const
    class Staticmethod(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.staticmethod

    @package.cache.register_const
    class Classmethod(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.classmethod

    ## real constant
    @package.cache.register_const
    class none(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.None

    @package.cache.register_const
    class true(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.True

    @package.cache.register_const
    class false(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.False

    @package.cache.register_const
    class notImplemented(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.NotImplemented

    @package.cache.register_const
    class ellipsis(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.Ellipsis

    @package.cache.register_const
    class file(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.file

    import _weakref
    @package.cache.register_const
    class weakref(__constant):
        @classmethod
        def getclass(cls):
            return _weakref.ReferenceType

    @package.cache.register_const
    class super(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.super

    import thread
    @package.cache.register_const
    class threadlock(__constant):
        @classmethod
        def getclass(cls):
            return thread.LockType

try:
    import imp
    @package.cache.register_const
    class NullImporter(__constant):
        @classmethod
        def getclass(cls):
            return imp.NullImporter

except ImportError:
    pass

if 'core':
    @package.cache.register_type
    class type_(__type__):
        '''any generic python type'''

        # FIXME: when instantiating the hierarchy of types, this fails to associate
        #        the method with the proper parent class. this is apparent if you
        #        compare the help() of the original object to the deserialized object
        @classmethod
        def getclass(cls):
            return type.getclass()

        @classmethod
        def subclasses(cls, type):
            '''return all subclasses of type'''
            assert __builtin__.type(type) is __builtin__.type, '%s is not a valid python type'% __builtin__.type(type)
            if type.__bases__ == ():
                return ()
            result = type.__bases__
            for x in type.__bases__:
                result += cls.subclasses(x)
            return result

        @classmethod
        def p_constructor(cls, object, **attributes):
            name,bases,slots = (object.__name__,object.__bases__,__builtin__.tuple(getattr(object,'__slots__')) if hasattr(object,'__slots__') else None)
            result = [slots,name]
            result.extend(bases)
            return __builtin__.tuple(result)

        @classmethod
        def u_constructor(cls, data, **attributes):
            result = __builtin__.list(data)
            slots,name = result.pop(0),result.pop(0)
            if slots is None:
                return __builtin__.type(name, __builtin__.tuple(result), {})
            return __builtin__.type(name, __builtin__.tuple(result), {'__slots__':slots})

        @classmethod
        def p_instance(cls, object, **attributes):
            state = __builtin__.dict(getattr(object,'__dict__', {}))
            if hasattr(object,'__slots__'):
                state.update((k,getattr(object,k)) for k in object.__slots__ if hasattr(object,k))

            # non-serializeable descriptors
            getset_descriptor = cls.__weakref__.__class__
            method_descriptor = cls.__reduce_ex__.__class__
            wrapper_descriptor = cls.__setattr__.__class__
            member_descriptor = __builtin__.type(lambda:wat).func_globals.__class__
            classmethod_descriptor = __builtin__.type(__builtin__.float.__dict__['fromhex'])

            result = {}
            for k,v in state.iteritems():
                if __builtin__.type(v) in (getset_descriptor,method_descriptor,wrapper_descriptor,member_descriptor,classmethod_descriptor,generator_.getclass()):
                    continue

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

    @package.cache.register_type
    class classobj(type_):
        '''an old-style python class'''
        @classmethod
        def getclass(cls):
            return __builtin__.type(package)

    @package.cache.register_type
    class Object(__constant):
        @classmethod
        def getclass(cls):
            return __builtin__.object
        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new()

    @package.cache.register
    class object_(type_):
        '''a generic python object and all it's parentclass' properties'''
        @classmethod
        def p_constructor(cls, object, **attributes):
            name,type = getattr(object,'__name__',None),object.__class__
            return (name,type,)

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,type = data
            type.__name__ = name or ''

#            class type(type): pass  # XXX: this type-change might mess up something
            # FIXME: create an instance illegitimately
            # TODO: bniemczyk would like a hint here for customizing __new__
            _ = type.__init__
            type.__init__ = lambda s: None
            if hasattr(type, '__new__'):
                # FIXME: abc.ABCMeta
                raise Exception, 'Unable to support custom-defined .__new__ operators'
            type.__new__ = lambda *a: a
            result = type()
            type.__init__ = _

            #result.__name__ = name
            return result

        @classmethod
        def p_instance(cls, object, **attributes):
            c = type_
            result = [(c.id,c.p_instance(object,**attributes))]

            for t in type_.subclasses(__builtin__.type(object)):
                try:
                    c = package.cache.byclass(t)
                except KeyError:
                    continue
                result.append( (c.id, c.p_instance(object, **attributes)) )
            return result

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            if len(data) == 0:
                return instance
            for id,data in data:
                c = package.cache.byid(id)
                instance = c.u_instance(instance, data, **attributes)
            return instance

    @package.cache.register
    class module_local(__constant):
        '''module that is locally stored in the filesystem'''
        @classmethod
        def getclass(cls):
            return module.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__name__

        @classmethod
        def u_constructor(cls, data, **attributes):
            name = data
            return module.instancelocal(name)

    @package.cache.register_type
    class module_(module_local):
        '''a module and it's attributes in memory'''
        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__name__,object.__doc__

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,doc = data
            return cls.new(name,doc)

        @classmethod
        def p_instance(cls, object, **attributes):
            ignored = ('__builtins__',)
            return __builtin__.dict((k,v) for k,v in object.__dict__.items() if k not in ignored)

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,doc = data
            return module.new(name,doc)

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            for k,v in data.items():
                setattr(instance, k, v)
            return instance

if 'builtin':
    class __builtin(__type__):
        @classmethod
        def p_constructor(cls, object, **attributes):
            return object
        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data)
        @classmethod
        def p_instance(cls, object, **attributes):
            return ()
        @classmethod
        def new(cls, *args, **kwds):
            return cls.getclass()(*args, **kwds)

    @package.cache.register_type
    class bool_(__builtin):
        '''standard boolean type'''
        @classmethod
        def getclass(cls):
            return bool.getclass()

    @package.cache.register_type
    class int_(__builtin):
        '''integral value'''
        @classmethod
        def getclass(cls):
            return int.getclass()

    @package.cache.register_type
    class float_(__builtin):
        '''float value'''
        @classmethod
        def getclass(cls):
            return float.getclass()

    @package.cache.register_type
    class long_(__builtin):
        '''long value'''
        @classmethod
        def getclass(cls):
            return long.getclass()

    @package.cache.register_type
    class complex_(__builtin):
        '''complex value'''
        @classmethod
        def getclass(cls):
            return complex.getclass()

    ## sequence types
    @package.cache.register_type
    class str_(__builtin):
        '''str value'''
        @classmethod
        def getclass(cls):
            return str.getclass()

    @package.cache.register_type
    class unicode_(__builtin):
        '''unicode string'''
        @classmethod
        def getclass(cls):
            return unicode.getclass()

    @package.cache.register_type
    class buffer_(__builtin):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return buffer.getclass()

if 'custom':
    @package.cache.register_type
    class NullImporter_(__builtin):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return NullImporter.getclass()

    try:
        import _sre
        @package.cache.register_type
        class SRE_Pattern(__builtin):
            @classmethod
            def getclass(cls):
                return _sre.compile('', 0, [1], 0, {}, []).__class__

            @classmethod
            def p_constructor(cls, object, **attributes):
                #pattern, flags, code
                return (object.pattern, object.flags, code, )

            @classmethod
            def u_constructor(cls, data, **attributes):
                pass
    #            return _sre.compile(
    #                pattern, flags | p.pattern.flags, code,
    #                p.pattern.groups-1,
    #                groupindex, indexgroup
    #                )

            @classmethod
            def p_instance(cls, object, **attributes):
                return ()

            @classmethod
            def u_instance(cls, instance, data, **attributes):
                return instance
        raise ImportError

    except ImportError:
        print '_sre serialization not really completed yet'

if 'immutable':
    @package.cache.register_type
    class tuple_(__type__):
        '''an immutable tuple'''
        @classmethod
        def getclass(cls):
            return tuple.getclass()

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
    class __muteable(__type__):
        @classmethod
        def p_constructor(cls, object, **attributes):
            return ()
        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data)
        @classmethod
        def new(cls, *args, **kwds):
            return cls.getclass()(*args, **kwds)

    @package.cache.register_type
    class list_(__muteable):
        '''a list'''
        @classmethod
        def getclass(cls):
            return list.getclass()
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

    @package.cache.register_type
    class dict_(__muteable):
        '''a dictionary'''
        @classmethod
        def getclass(cls):
            return dict.getclass()
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

    @package.cache.register_type
    class set_(__muteable):
        '''a set'''
        @classmethod
        def getclass(cls):
            return set.getclass()
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return __builtin__.tuple(object)
        @classmethod
        def u_instance(cls, instance, data, **attributes):
            instance.clear()
            instance.update(data)
            return instance

    @package.cache.register_type
    class frozenset_(__muteable):
        '''a frozenset'''
        @classmethod
        def getclass(cls):
            return frozenset.getclass()
        @classmethod
        def p_instance(cls, object, **attributes):
            '''return attributes of type that will be used to update'''
            return __builtin__.tuple(object)

if 'special':
    class __special(__type__):
        attributes = None

        @classmethod
        def getclass(cls):
            raise NotImplementedError, cls

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

    @package.cache.register_type
    class instancemethod_(__special):
        '''a python class method'''
        attributes = ['im_func', 'im_self', 'im_class']

        @classmethod
        def getclass(cls):
            return instancemethod.getclass()

        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data['im_func'], data['im_self'], data['im_class'])

    @package.cache.register_type
    class property_(__special):
        '''a python class property'''
        attributes=['fdel','fset','fget']
        @classmethod
        def getclass(cls):
            return property.getclass()

        @classmethod
        def u_constructor(cls, data, **attributes):
            return property.new(fget=data['fget'], fset=data['fset'], fdel=data['fdel'])

    @package.cache.register_type
    class code_(__special):
        '''a python code type'''
        attributes = [
            'co_argcount', 'co_nlocals', 'co_stacksize', 'co_flags', 'co_code',
            'co_consts', 'co_names', 'co_varnames', 'co_filename', 'co_name',
            'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
        ]

        @classmethod
        def getclass(cls):
            return code.getclass()

        @classmethod
        def u_constructor(cls, data, **attributes):
            result = (data[k] for k in cls.attributes)
            return code.new(*result)

    @package.cache.register_type
    class function_(__type__):
        '''a python function'''
        @classmethod
        def getclass(cls):
            return function.getclass()

        # FIXME: having to include the globals for an unbound function (__module__ is undefined) might be weird
        @classmethod
        def p_constructor(cls, object, **attributes):
            # so...it turns out that only the closure property is immutable
            func_closure = object.func_closure if object.func_closure is not None else ()
            assert object.__module__ is not None, 'FIXME: Unable to pack an unbound function'
#            return object.__module__,object.func_code,__builtin__.tuple(x.cell_contents for x in func_closure),object.func_globals
            return object.__module__,object.func_code,__builtin__.tuple(x.cell_contents for x in func_closure)

        @classmethod
        def u_constructor(cls, data, **attributes):
#            modulename,code,closure,globals = data
            modulename,code,closure = data
            assert object.__module__ is not None, 'FIXME: Unable to unpack an unbound function'

            # XXX: assign the globals from hints if requested
            globs = attributes['globals'] if 'globals' in attributes else module.instance(modulename).__dict__
            result = cls.cell(*closure)
            return function.new(code, globs, closure=result)

        @classmethod
        def p_instance(cls, object, **attributes):
            return object.func_code,object.func_name,object.func_defaults

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            instance.func_code,instance.func_name,instance.func_defaults = data
            return instance

        @classmethod
        def cell(cls, *args):
            '''Convert args into a cell tuple'''
            return __builtin__.tuple(((lambda n: lambda : n)(n).func_closure[0]) for n in args)

    @package.cache.register
    class builtin_(__constant):
        '''copy from local module and name'''
        @classmethod
        def getclass(cls):
            return builtin.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return (object.__module__, object.__name__)

        @classmethod
        def u_constructor(cls, data, **attributes):
            mod,name = data
            m = module.instancelocal(mod)
            return getattr(m,name)

    @package.cache.register
    class file_(__constant):
        '''A file..for serializing the contents of the file look at file_contents'''
        @classmethod
        def getclass(cls):
            return file.getclass()

        @classmethod
        def p_constructor(cls, file, **attributes):
            offset = file.tell()
            return file.name, file.mode, offset

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,mode,offset = data
            file = open(name, mode)
            file.seek(offset)
            return file

    @package.cache.register
    class file_contents(file_):
        # FIXME: save the whole file.. (should be selected via a hint)
        @classmethod
        def getclass(cls):
            return file.getclass()

        @classmethod
        def p_constructor(cls, file, **attributes):
            offset = file.tell()
            file.seek(0)
            content = file.read()
            file.seek(offset)
            return (file.name, file.mode, offset, content)

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,mode,offset,content = data
            file = open(name, "w")
            file.write(content)
            file.close()

            file = open(name,mode)
            file.seek(offset)
            return file

    import _weakref
    @package.cache.register_type
    class weakref_(__type__):
        @classmethod
        def getclass(cls):
            return _weakref.ReferenceType
        @classmethod
        def p_constructor(cls, object, **attributes):
            return (object(),)
        @classmethod
        def u_constructor(cls, data, **attributes):
            object, = data
            class extref(_weakref.ref):
                def __new__(self, object):
                    self.__cycle__ = object
                    return _weakref.ref(object)
#                    return super(extref,self)(object)
            return extref(object)
        @classmethod
        def p_instance(cls, object, **attributes):
            return ()

    @package.cache.register_type
    class super_(__type__):
        @classmethod
        def getclass(cls):
            return __builtin__.super
        @classmethod
        def p_constructor(cls, object, **attributes):
            return (object.__thisclass__, object.__self__)
        @classmethod
        def u_constructor(cls, data, **attributes):
            thisclass,self = data
            return __builtin__.super(thisclass,self)
        @classmethod
        def p_instance(cls, object, **attributes):
            return ()

    import thread
    @package.cache.register_type
    class threadlock_(__type__):
        @classmethod
        def getclass(cls):
            return thread.LockType  # XXX
        @classmethod
        def p_constructor(cls, object, **attributes):
            return ()
        @classmethod
        def u_constructor(cls, data, **attributes):
            return thread.allocate_lock()
        @classmethod
        def p_instance(cls, object, **attributes):
            return ()

    # XXX: the following aren't completed...maybe never will be
    @package.cache.register_type
    class generator_(__type__):
        @classmethod
        def getclass(cls):
            return generator.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            raise NotImplementedError, 'Unable to pack objects of type generator_'  # Due to the gi_frame property
            return object.gi_running,object.gi_code,object.gi_frame

        @classmethod
        def u_constructor(cls, data, **attributes):
            co,fr = data
            result = function.new(co, fr.f_globals)
            raise NotImplementedError, 'Unable to unpack objects of type generator_'
            return result

        @classmethod
        def p_instance(cls, object, **attributes):
            return ()

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            return instance

    @package.cache.register_type
    class frame_(partial):  # FIXME: can't construct these, we can create a shell object for these tho maybe
        attributes = ['f_back', 'f_builtins', 'f_code', 'f_exc_traceback', 'f_exc_type', 'f_exc_value', 'f_globals', 'f_lasti', 'f_lineno', 'f_locals', 'f_restricted', 'f_trace']
        @classmethod
        def getclass(cls):
            return frame.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            raise NotImplementedError, 'Unable to pack objects of type frame_'

        @classmethod
        def u_constructor(cls, data, **attributes):
            raise NotImplementedError, 'Unable to unpack objects of type frame_'

    @package.cache.register_type
    class staticmethod_(__constant):
        @classmethod
        def getclass(cls):
            return Staticmethod.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__func__,

        @classmethod
        def u_constructor(cls, data, **attributes):
            fn, = data
            return cls.new(fn)

    @package.cache.register_type
    class classmethod_(__constant):
        @classmethod
        def getclass(cls):
            return Classmethod.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__func__,

        @classmethod
        def u_constructor(cls, data, **attributes):
            fn, = data
            return cls.new(fn)

if 'operator':
    import operator

    @package.cache.register_const
    class attrgetter(__constant):
        @classmethod
        def getclass(cls):
            return operator.attrgetter

    class __attrgetter_helper(object):
        def __getattribute__(self, name):
            raise Exception(name)
    _attrgetter_helper = __attrgetter_helper()

    @package.cache.register_type
    class attrgetter_(__constant):
        @classmethod
        def getclass(cls):
            return operator.attrgetter

        @classmethod
        def p_constructor(cls, object, **attributes):
            try:
                object(_attrgetter_helper)
            except Exception as E:
                name, = E
            return (name,)

        @classmethod
        def u_constructor(cls, data, **attributes):
            name, = data
            return cls.new(name)

## regular functions
#import cPickle as pickle
import marshal as pickle
def dumps(object, **attributes):
    '''Convert any python object into a string.'''
    return pickle.dumps(package.pack(object,**attributes))

def loads(data, **attributes):
    '''Convert a string back into a python object.'''
    return package.unpack(pickle.loads(data), **attributes)

def pack(object, **attributes):
    '''Serialize an instance of a python object into a tuple'''
    return package.pack(object, **attributes)

def unpack(data, **attributes):
    '''Deserialize a tuple back into an instance'''
    return package.unpack(data, **attributes)

import sys
def caller(frame=None):
    """Return the (module, name) of the requested frame.

    This will default to the calling function if a frame is not supplied.
    """
    import sys
    fr = sys._getframe().f_back if frame is None else frame
    source,name = fr.f_code.co_filename,fr.f_code.co_name
    module = [x for x in sys.modules.itervalues() if hasattr(x, '__file__') and (x.__file__.endswith(source) or x.__file__.endswith('%sc'%source))]
    module, = (None,) if not module else module
    return module,name

if __name__ == '__main__':
    import traceback
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass
    Werror = True

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
            print traceback.format_exc()
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
        input = make_package(fu.bool_,True,())
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

#    @TestCase  # FIXME
    def test_unknown_type():
        # error while serializing a 'TypeInfo' object which comes from a module implemented in C
        #   if we can
        import xml.dom.minidom
        a = fu.package.pack(xml.dom.minidom)
        b = fu.package.unpack(a)

    @TestCase
    def test_inheritance_native():
        class blah(list): pass
        x = blah()
        x.append(5)
        a = fu.package.pack(x)
        b = fu.package.unpack(a)
        if len(x) == len(b):
            raise Success

    @TestCase
    def test_const_list():
        t = type([])
        a = fu.package.pack(t)
        b = fu.package.unpack(a)
        if b is t:
            raise Success

    @TestCase
    def test_type_intbool():
        v = 1
        a = fu.package.pack(v)
        b = fu.package.unpack(a)
        if b == v and type(b) == type(v):
            raise Success

    @TestCase
    def test_module_builtin():
        import sys
        a = fu.pack(sys)
        b = fu.unpack(a)
        if b is sys:
            raise Success

    @TestCase
    def test_module_general():
        import re
        a = re
        b = fu.pack(a)
        c = fu.unpack(b)
        if c is not a:
            raise Success

#    @TestCase
    def test_module():
        import fu
        a = fu.package.pack(fu)
        b = fu.package.unpack(a)
        if b.VERSION == fu.VERSION and b is not fu:
            raise Success

#    @TestCase
    def test_ignore_modulepack():
        import sys
        a = fu.package.pack(sys, local=('sys',))
        _,x,y = a
        if y[0][x][0] is not fu.module.id:
            raise Failure

        b = fu.package.unpack(a)
        if sys.winver is b.winver:
            raise Success

#    @TestCase
    def test_ignore_moduleunpack():
        import _ast as testpackage
        a = fu.package.pack(testpackage)
        _,x,y = a
        if y[0][x][0] is not fu.module_.id:
            raise Failure

        b = fu.package.unpack(a, local=('_ast',))
        if b is testpackage:
            raise Success

    #@TestCase
    def test_ptype_pack():
        from ptypes import pint
        a = pint.uint32_t()
        a.setoffset(id(__builtin__.type))
        result = a.l.value
        b = fu.package.unpack(fu.package.pack(a))
        if b.value == result:
            raise Success

    #@TestCase
    def test_continuation_yield():
        def fn():
            yield 1
            yield 2
        global a,b,c
        a = fn()
        assert a.next() == 1
        b = fu.package.pack(a)
        c = fu.package.unpack(b)
        if c.next() == 2:
            raise Success

    @TestCase
    def test_weakref_packunpack():
        import fu,_weakref
        reload(fu)
        a = set(('hello',))
        b = _weakref.ref(a)
        c = fu.pack(b)
        d = fu.unpack(c)
        if list(b()) == list(d()):
            raise Success

    @TestCase
    def test_super_packunpack():
        import fu,__builtin__
        class blah(set):
            def huh(self):
                return 5
        class blahsub(blah):
            def huh(self):
                return super(blahsub, self)
        a = blahsub((20,40,60))
        b = a.huh()
        c = fu.pack(b)
        d = fu.unpack(c)
        if d.huh() == b.huh():
            raise Success

    @TestCase
    def test_threadlock_packunpack():
        import thread,fu
        a = thread.allocate_lock()
        b = fu.pack(a)
        c = fu.unpack(b)
        if type(a) == type(c):
            raise Success

    @TestCase
    def test_object_instance_packunpack():
        import fu
        a = object()
        b = fu.pack(a)
        c = fu.unpack(b)
        if type(a) == type(c) and isinstance(c,type(a)):
            raise Success

    @TestCase
    def test_instancevalue_slots_packunpack():
        import fu
        class mytype(object):
            __slots__ = ['blargh','huh']
            readonly = 20
            #blargh = 500
            #huh = 20

        a = mytype()
        b = fu.unpack(fu.pack(a))

        try:
            b.blargh = 500
            b.huh = 500
        except AttributeError:
            raise Failure, "Unable to assign to slots"

        try:
            b.readonly = 20
            raise Failure, "Successfully assigned to a readonly property"
        except AttributeError:
            pass

        try:
            b.nope = None
            raise Failure, "Assigned a property to a __dict__ instead of an allocated slot"
        except AttributeError:
            pass

        if b.blargh == b.huh == 500 and b.readonly == 20:
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )

if __name__ == 'bootstrap':
    import importlib, fu
    from fu import package

    ## figure out which type methods we need
    st = package.stash()
    n = st.store(package)

    t1 = set()
    t1.update(n for n,_ in st.cons_data.values())
    t1.update(n for n,_ in st.inst_data.values())
    print len(t1)
    [st.store(fu.package.cache.byid(n)) for n in t]
    t2 = set()
    t2.update(n for n,_ in st.cons_data.values())
    t2.update(n for n,_ in st.inst_data.values())
    print len(t2)
    print sum(map(len,(fu.package.cache.registration.id,fu.package.cache.registration.type,fu.package.cache.registration.const)))
    t = t2

    mymethod = type(fu.function.new)
    myfunc = type(fu.function.new.im_func)

    ## serialize the stash methods
    stashed_up,stashed_fe = (getattr(st,attr).im_func.func_code for attr in ('unpack_references','fetch'))
    res = stashed_up,stashed_fe,st.packed()
    #marshal.dumps(res)

    class mystash:
        cons_data = {}
        inst_data = {}
        def fetch(self, identity, **attributes):
            _,data = self.cons_data[identity]
            cls,data = self.byid(_),self.unpack_references(data,**attributes)
            instance = cls.u_constructor(data,**attributes)
            self.fetch_cache[identity] = instance
            _,data = self.inst_data[identity]
            cls,data = self.byid(_),self.unpack_References(data,**attributes)
            _ = cls.u_instance(instance,data,**attributes)
            assert instance is _
            return instance

    mystash.unpack_references = myfunc(stashed_up, namespace)
    mystash.fetch = myfunc(stashed_fe, namespace)
    x = mystash()
    x.cons_data,x.inst_data = st.packed()

    ## serialize the necessary type methods
    classes = [(n,fu.package.cache.byid(n)) for n in t]
    methods = [(n,(cls.__name__,cls.new.im_func.func_code,cls.getclass.im_func.func_code,cls.u_constructor.im_func.func_code,cls.u_instance.im_func.func_code)) for n,cls in classes]
    marshal.dumps(methods)

    ## ensure that we can recreate all these type methods
    result,namespace = {},{}
    namespace['thread'] = importlib.import_module('thread')
    namespace['imp'] = importlib.import_module('imp')
    namespace['_weakref'] = importlib.import_module('_weakref')
    for n,(name,new,get,cons,inst) in methods:
        objspace = {
            'new' : myfunc(new,namespace),
            'getclass' : myfunc(get,namespace),
            'u_constructor' : myfunc(cons,namespace),
            'u_instance' : myfunc(inst,namespace),
        }
        o = type(name, (object,), objspace)()
        result[n] = namespace[name] = o

    #for attr in ['func_closure', 'func_code', 'func_defaults', 'func_dict', 'func_doc', 'func_globals', 'func_name']:
    #for n,(new,cons,inst) in methods:
    #    if any(x.func_closure is not None for x in (cons,inst)):
    #        raise Exception, n
    #    if any(x.func_defaults is not None for x in (cons,inst)):
    #        raise Exception, n
    #    if any(len(x.func_dict) != 0 for x in (cons,inst)):
    #        raise Exception, n
    #    for attr in ['func_code', 'func_name']:
    #        print n, attr, repr(getattr(cons, attr))
    #        print n, attr, repr(getattr(inst, attr))

    consdata = st.cons_data
    instances = {}
    for _,(t,v) in consdata.iteritems():
        result[t].u_constructor(v, globals=namespace)
