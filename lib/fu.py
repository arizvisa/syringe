'''serialize/deserialize almost any kind of python object'''

# TODO: add a decorator that can transform anything into an object that will pass an instance of self
#          to serialization service

import __builtin__

VERSION = '0.7'

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

    ### stuff that's hidden within this namespace
    class cache(object):
        '''static class for looking up a class used for serializing a particular object'''
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
                raise KeyError("Duplicate id %x in cache"% id)

            cls.registration.id[id] = definition
            definition.id = id
            return definition

        @classmethod
        def register_type(cls, definition):
            '''registers the definition with the specified builtin type'''
            type = definition.getclass()
            if type in cls.registration.type:
                raise KeyError("Duplicate type %s in cache"% repr(type))

            definition = cls.register(definition)
            cls.registration.type[type] = definition
            return definition

        @classmethod
        def register_const(cls, definition):
            const = definition.getclass()
            if const in cls.registration.const:
                raise KeyError("Duplicate constant %s in cache"% repr(const))
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
                raise KeyError(const)
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
                        raise NotImplementedError('binary modules not supported')
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
#                    return partial  # XXX
                    globals()['error'] = instance
                    raise KeyError(instance)
                return builtin_

            # non-serializeable descriptors
            getset_descriptor = cls.__weakref__.__class__
            method_descriptor = cls.__reduce_ex__.__class__
            wrapper_descriptor = cls.__setattr__.__class__
            member_descriptor = type(lambda:wat).func_globals.__class__
            classmethod_descriptor = type(__builtin__.float.__dict__['fromhex'])
            if t in (getset_descriptor,method_descriptor,wrapper_descriptor,member_descriptor,classmethod_descriptor,generator_.getclass()):
#                return partial  # XXX
                globals()['error'] = instance
                raise KeyError(instance)

            # catch-all object
            if hasattr(instance, '__dict__'): # or hasattr(instance, '__slots__'):  # XXX
                return object_

            # FIXME: if it follows the pickle protocol..
            if hasattr(instance, '__getstate__'):
                pickle.loads(pickle.dumps(instance))
                return partial

            globals()['error'] = instance
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
            if object in self.__identity:
                return self.__identity.index(object)
            self.__identity.append(object)
            return self.identify(object)

        def __getitem__(self, name):
            return self.identify(name)

        ### stashing/fetching of objects
        def store(self, object, **attributes):
            identity = self.identify(object)
            if identity in self.store_cache:
                return identity
            cls = package.cache.byinstance(object)

            if False:       # XXX
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

            if False:   # XXX
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

class __type__(__builtin__.object):
    @classmethod
    def getclass(cls, *args, **kwds):
        raise NotImplementedError(cls)

    @classmethod
    def new(cls):
        return cls.getclass()

    @classmethod
    def repr(cls, object):
        '''default method for displaying a repr of an object'''
        return repr(object)

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

@package.cache.register_type
class partial(__type__):
    '''just a general type for incomplete objects'''
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
        @classmethod
        def new(cls, *args, **kwds):
            '''instantiate a new instance of the object'''
            return cls.getclass()(*args, **kwds)
        @classmethod
        def p_instance(cls, object, **attributes):
            return ()
        @classmethod
        def u_constructor(cls, data, **attributes):
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
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return (().__class__)

    @package.cache.register_const
    class list(__constant):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return [].__class__

    @package.cache.register_const
    class dict(__constant):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return {}.__class__

    @package.cache.register_const
    class set(__constant):
        '''string buffer'''
        @classmethod
        def getclass(cls):
            return __builtin__.set

    @package.cache.register_const
    class frozenset(__constant):
        '''string buffer'''
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
        def new(cls, code, globals, **attributes):
            '''Create a new function'''
            name = attributes.get('name', code.co_name)
            argdefs = attributes.get('argdefs', ())
            closure = attributes.get('closure', ())
            c = cls.getclass()
            return c(code, globals, name, argdefs, closure)

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

        # FIXME: when instantiating a hierarchy of types, this fails to associate
        #        the method with the proper parent class. this is apparent if you
        #        compare the help() of the original object to the deserialized object
        @classmethod
        def getclass(cls):
            return type.getclass()

        @classmethod
        def subclasses(cls, type):
            '''return all subclasses of type'''
            assert __builtin__.type(type) is __builtin__.type
            if type.__bases__ == ():
                return ()
            result = type.__bases__
            for x in type.__bases__:
                result += cls.subclasses(x)
            return result

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

        def u_constructor(cls, data, **attributes):
            return self.new()

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

#            class type(type): pass  # XXX: this type-change might mess up something
            # create an instance illegitimately
            _ = type.__init__
            type.__init__ = lambda s: None
            result = type()
            type.__init__ = _

            result.__name__ = name
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
        '''module that is locally stored'''
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
        '''a module and it's attributes'''
        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__name__,object.__doc__

        @classmethod
        def u_constructor(cls, data, **attributes):
            name,doc = data
            return cls.new(name,doc)

        @classmethod
        def p_instance(cls, object, **attributes):
            return object.__dict__

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
        print 'unable to do _sre serialization'

if 'immuteable':
    @package.cache.register_type
    class tuple_(__type__):
        '''an immuteable tuple'''
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
            globals = attributes['globals'] if 'globals' in attributes else module.instance(modulename).__dict__
            result = cls.__new_closure(*closure)
            return function.new(code, globals, closure=result)

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
            result = list_.new(args)
            result.insert(0, innercodeobj)
            constants = __builtin__.tuple(result)

            # names within outer code object
            cellvars = __builtin__.tuple( chr(x+65) for x in range(len(args)) )
            outercodeobj = code.new(0, 0, 0, 0, outercodestring, constants, (), (), '', '<function>', 0, '', (), cellvars)

            # finally fucking got it
            fn = function.new(outercodeobj, {})
            return fn().func_closure

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

    # XXX: the following aren't tested
    raise NotImplementedError
    @package.cache.register_type
    class generator_(__type__):
        @classmethod
        def getclass(cls):
            return generator.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.gi_code,object.gi_frame

        @classmethod
        def u_constructor(cls, data, **attributes):
            co,fr = data
            result = function.new(co, fr.f_globals)
            raise NotImplementedError
            return result

        @classmethod
        def p_instance(cls, object, **attributes):
            return ()

        @classmethod
        def u_instance(cls, instance, data, **attributes):
            return instance

    @package.cache.register_type
    class frame_(partial):  # FIXME: can't construct these
        attributes = ['f_back', 'f_builtins', 'f_code', 'f_exc_traceback', 'f_exc_type', 'f_exc_value', 'f_globals', 'f_lasti', 'f_lineno', 'f_locals', 'f_restricted', 'f_trace']
        @classmethod
        def getclass(cls):
            return frame.getclass()

    @package.cache.register_type
    class staticmethod_(__constant):
        @classmethod
        def getclass(cls):
            return Staticmethod.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__func__

        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data)

    @package.cache.register_type
    class classmethod_(__constant):
        @classmethod
        def getclass(cls):
            return Classmethod.getclass()

        @classmethod
        def p_constructor(cls, object, **attributes):
            return object.__func__

        @classmethod
        def u_constructor(cls, data, **attributes):
            return cls.new(data)

## regular functions
import cPickle as pickle
def dumps(object, **attributes):
    '''convert any python object into a bzip2 encoded string'''
    return pickle.dumps(package.pack(object,**attributes)).encode('bz2')

def loads(cls, data, **attributes):
    '''convert a bzip2 encoded string back into a python object'''
    return package.unpack(pickle.loads(data.decode('bz2')), **attributes)

def pack(object, **attributes):
    return package.pack(object, **attributes)

def unpack(data, **attributes):
    return package.unpack(data, **attributes)

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
        global a,b
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

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
