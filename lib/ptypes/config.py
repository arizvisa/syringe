import os,sys,math
__all__ = 'defaults,byteorder'.split(',')
class field:
    class descriptor(object):
        def __init__(self):
            self.__value__ = {}
        def __set__(self, instance, value):
            self.__value__[instance] = value
        def __get__(self, instance, type=None):
            return self.__value__.get(instance)
        def __delete__(self, instance):
            raise AttributeError

    class __enum_descriptor(descriptor):
        __option = set
        def option(self, name, doc=''):
            cls = type(self)
            res = type(name, cls, {'__doc__':doc})
            self.__option__.add(res)
            return res
        def __set__(self, instance, value):
            if value in self.__option__:
                return field.descriptor.__set__(self, instance, value)
            raise ValueError, '{!r} is not a member of {!r}'.format(value, self.__option__)

    class __type_descriptor(descriptor):
        __type__ = type
        def __set__(self, instance, value):
            if (hasattr(self.__type__, '__iter__') and type(value) in self.__type__) or isinstance(value, self.__type__):
                return field.descriptor.__set__(self, instance, value)
            raise ValueError, '{!r} is not an instance of {!r}'.format(value, self.__type__)

    class __set_descriptor(descriptor):
        set,get = None,None
        def __init__(self): pass
        def __set__(self, instance, value):
            return self.__getattribute__('set').im_func(value)
        def __get__(self, instance, type=None):
            return self.__getattribute__('get').im_func()

    class __bool_descriptor(descriptor):
        def __set__(self, instance, value):
            return field.descriptor.__set__(self, instance, bool(value))

    @classmethod
    def enum(cls, name, options=(), doc=''):
        base = cls.__enum_descriptor
        attrs = dict(base.__dict__)
        attrs['__option__'] = set(options)
        attrs['__doc__'] = doc
        return type(name, (base,), attrs)()
    @classmethod
    def option(cls, name, doc='', base=object):
        return type(name, (base,), {'__doc__':doc})
    @classmethod
    def type(cls, name, subtype, doc=''):
        base = cls.__type_descriptor
        attrs = dict(base.__dict__)
        attrs['__type__'] = subtype
        attrs['__doc__'] = doc
        return type(name, (base,), attrs)()
    @classmethod
    def set(cls, name, fetch, store, doc=''):
        base = cls.__set_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = doc
        attrs['set'] = store
        attrs['get'] = fetch
        return type(name, (base,), attrs)()
    @classmethod
    def constant(cls, name, value, doc=''):
        base = cls.descriptor
        attrs = dict(base.__dict__)
        def raiseAttributeError(self, instance, value):
            raise AttributeError
        attrs['__set__'] = raiseAttributeError
        attrs['__doc__'] = doc
        return type(name, (base,), attrs)()
    @classmethod
    def bool(cls, name, doc=''):
        base = cls.__bool_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = doc
        return type(name, (base,), attrs)()

def namespace(cls):
    # turn all instances of things into read-only attributes
    attrs,properties,subclass = {},{},{}
    for k,v in cls.__dict__.items():
        if hasattr(v, '__name__'):
            v.__name__ = '{}.{}'.format(cls.__name__,k)
        if k.startswith('_') or type(v) is property:
            attrs[k] = v
        elif not callable(v) or isinstance(v,type):
            properties[k] = v
        elif not hasattr(v, '__class__'):
            subclass[k] = namespace(v)
        else:
            attrs[k] = v
        continue

    def getprops(obj):
        result = []
        col1,col2 = 0,0
        for k,v in obj.items():
            col1 = max((col1,len(k)))
            if isinstance(v, type):
                val = '<>'
            elif hasattr(v, '__class__'):
                val = repr(v)
            else:
                raise ValueError,k
            doc = v.__doc__.split('\n')[0] if v.__doc__ else None
            col2 = max((col2,len(val)))
            result.append((k, val, doc))
        return [(('{name:%d} : {val:%d} # {doc}' if d else '{name:%d} : {val:%d}')%(col1,col2)).format(name=k,val=v,doc=d) for k,v,d in result]

    def __repr__(self):
        props = getprops(properties)
        descr = ('{{{!s}}} # {}\n' if cls.__doc__ else '{{{!s}}}\n')
        subs = ['{{{}.{}}}\n...'.format(cls.__name__,k) for k in subclass.keys()]
        res = descr.format(cls.__name__,cls.__doc__) + '\n'.join(props)
        if subs:
            return res + '\n' + '\n'.join(subs) + '\n'
        return res + '\n'

    attrs['__repr__'] = __repr__
    attrs.update((k,property(fget=lambda s,k=k:properties[k])) for k in properties.viewkeys())
    attrs.update((k,property(fget=lambda s,k=k:subclass[k])) for k in subclass.viewkeys())
    result = type(cls.__name__, cls.__bases__, attrs)
    return result()

def configuration(cls):
    attrs,properties,subclass = dict(cls.__dict__),{},{}
    for k,v in attrs.items():
        if isinstance(v, field.descriptor):
            properties[k] = v
        elif not hasattr(v, '__class__'):
            subclass[k] = configuration(v)
        continue

    def getprops(obj,val):
        result = []
        col1,col2 = 0,0
        for k,v in obj.items():
            col1 = max((col1,len(k)))
            doc = v.__doc__.split('\n')[0] if v.__doc__ else None
            col2 = max((col2,len(repr(val[k]))))
            result.append((k, val[k], doc))
        return [(('{name:%d} = {val:<%d} # {doc}' if d else '{name:%d} = {val:<%d}')%(col1,col2)).format(name=k,val=v,doc=d) for k,v,d in result]

    def __repr__(self):
        descr = ('[{!s}] # {}\n' if cls.__doc__ else '[{!s}]\n')
        values = dict((k,getattr(self,k,None)) for k in properties.viewkeys())
        res = descr.format(cls.__name__,cls.__doc__.split('\n')[0] if cls.__doc__ else None) + '\n'.join(getprops(properties,values))
        subs = ['[{}.{}]\n...'.format(cls.__name__,k) for k in subclass.keys()]
        if subs:
            return res + '\n' + '\n'.join(subs) + '\n'
        return res + '\n'

    attrs['__repr__'] = __repr__
    attrs.update((k,property(fget=lambda s,k=k:subclass[k])) for k in subclass.viewkeys())
    result = type(cls.__name__, cls.__bases__, attrs)
    return result()

### constants that can be used as options
@namespace
class byteorder:
    '''Byte order constants'''
    bigendian = field.option('bigendian', 'Big-endian')
    littleendian = field.option('littleendian', 'Little-endian')

### new-config
import logging
@configuration
class defaults:
    log = field.type('default-logger', logging.Filterer, 'Default place to log progress')

    class integer:
        size = field.type('integersize', (int,long), 'The word-size of the architecture')
        order = field.enum('byteorder', (byteorder.bigendian,byteorder.littleendian), 'The endianness of integers/pointers')

    class display:
        show_module_name = field.bool('show_module_name', 'display the module name in the summary')
        show_parent_name = field.bool('show_parent_name', 'display the parent name in the summary')

        class hexdump:
            width = field.type('width', int)
            threshold = field.type('threshold', int)

        class threshold:
            summary = field.type('summary_threshold', int)
            summary_message = field.type('summary_threshold_message', str)
            details = field.type('details_threshold', int)
            details_message = field.type('details_threshold_message', str)

    def __getsource():
        global ptype
        return ptype.source
    def __setsource(value):
        global ptype
        if all(hasattr(value, method) for method in ('seek','store','consume')) or isinstance(value, provider.base):
            ptype.source = value
            return
        raise ValueError, "Invalid source object"
    source = field.set('default-source', __getsource, __setsource, 'Default source to load/commit data from/to')

import ptype # recursive

### defaults
root = logging.getLogger()
if len(root.handlers) == 0:
    logging.basicConfig(format='[%(created).3f] <%(process)x.%(thread)x> [%(levelname)s:%(name)s.%(module)s] %(message)s', level=logging.WARNING)
defaults.log = root.getChild('ptypes')

defaults.integer.size = long(math.log((sys.maxsize+1)*2,2)/8)
defaults.integer.order = byteorder.littleendian if sys.byteorder == 'little' else byteorder.bigendian if sys.byteorder == 'big' else None
defaults.display.show_module_name = False
defaults.display.show_parent_name = False
defaults.display.hexdump.width = 16
defaults.display.hexdump.threshold = 8
defaults.display.threshold.summary = 80
defaults.display.threshold.details = 8
defaults.display.threshold.summary_message = ' ..skipped ~{leftover} bytes.. '
defaults.display.threshold.details_message = ' ..skipped {leftover} rows, {skipped} bytes.. '

if __name__ == '__main__':
    @namespace
    class consts:
        bigendian = field.option('bigendian', 'Big-endian integers')
        littleendian = field.option('littleendian', 'Little-endian integers')
        size = 20
        whatever = object()
        class huh:
            what = 5
            default = 10
            blah = object()
            class more:
                whee = object()

        class blah:
            pass

    import logging
    @configuration
    class config(object):
        byteorder = field.enum('byteorder', (byteorder.bigendian,byteorder.littleendian), 'The endianness of integers/pointers')
        integersize = field.type('integersize', (int,long), 'The word-size of the architecture')

        class display:
            summary = field.type('single-line', int)
            details = field.type('multi-line', int)
            show_module = field.bool('show-module-name')

        def __getlogger():
            return logging.root
        def __setlogger(value):
            logging.root = value
        logger = field.set('default-logger', __getlogger, __setlogger, 'Default place to log progress')
        #logger = field.type('default-logger', logging.Filterer, 'Default place to log progress')

        def __getsource():
            return ptype.source
        def __setsource(value):
            if not isinstance(value, provider.base):
                raise ValueError, "Invalid source object"
            ptype.source = value
        source = field.set('default-source', __getsource, __setsource, 'Default source to load/commit data from/to')

    #config.logger = logging.root
    print repr(consts)
    print repr(config)
