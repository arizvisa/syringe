import sys, math, logging

__all__ = 'defaults,byteorder,partial'.split(',')

# Setup some version-agnostic types that we can perform checks with
integer_types = (int, long) if sys.version_info[0] < 3 else (int,)
string_types = (str, unicode) if sys.version_info[0] < 3 else (str,)

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
        def option(self, name, documentation=''):
            cls = type(self)
            res = type(name, cls, {'__doc__': documentation})
            self.__option__.add(res)
            return res
        def __set__(self, instance, value):
            if value in self.__option__:
                return field.descriptor.__set__(self, instance, value)
            raise ValueError("{!r} is not a member of {!r}".format(value, self.__option__))

    class __type_descriptor(descriptor):
        __type__ = type
        def __set__(self, instance, value):
            if (hasattr(self.__type__, '__iter__') and type(value) in self.__type__) or isinstance(value, self.__type__):
                return field.descriptor.__set__(self, instance, value)
            raise ValueError("{!r} is not an instance of {!r}".format(value, self.__type__))

    class __set_descriptor(descriptor):
        set, get = None, None
        def __init__(self):
            return
        def __set__(self, instance, value):
            res = self.__getattribute__('set')
            return res.im_func(value) if sys.version_info[0] < 3 else res.__func__(value)
        def __get__(self, instance, type=None):
            res = self.__getattribute__('get')
            return res.im_func() if sys.version_info[0] < 3 else res.__func__()

    class __bool_descriptor(descriptor):
        def __set__(self, instance, value):
            if not isinstance(value, bool):
                logging.warning("rvalue {!r} is not of boolean type. Coercing it into one : ({:s} != {:s})".format(value, type(value).__name__, bool.__name__))
            return field.descriptor.__set__(self, instance, bool(value))

    class option_t(object): pass

    @classmethod
    def enum(cls, name, options=(), documentation=''):
        base = cls.__enum_descriptor
        attrs = dict(base.__dict__)
        attrs['__option__'] = set(options)
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def option(cls, name, documentation=''):
        base = field.option_t
        return type(name, (base,), {'__doc__': documentation})
    @classmethod
    def type(cls, name, subtype, documentation=''):
        base = cls.__type_descriptor
        attrs = dict(base.__dict__)
        attrs['__type__'] = subtype
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def set(cls, name, fetch, store, documentation=''):
        base = cls.__set_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = documentation
        attrs['set'] = store
        attrs['get'] = fetch
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def constant(cls, name, value, documentation=''):
        base = cls.descriptor
        attrs = dict(base.__dict__)
        def raiseAttributeError(self, instance, value):
            raise AttributeError
        attrs['__set__'] = raiseAttributeError
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()
    @classmethod
    def bool(cls, name, documentation=''):
        base = cls.__bool_descriptor
        attrs = dict(base.__dict__)
        attrs['__doc__'] = documentation
        cons = type(name, (base,), attrs)
        return cons()

def namespace(cls):
    # turn all instances of things into read-only attributes
    readonly = []
    if hasattr(property, '__isabstractmethod__'):
        readonly.append(property.__isabstractmethod__)
    readonly.append(property.deleter)

    attributes, properties, subclass = {}, {}, {}
    for name, value in cls.__dict__.items():
        if hasattr(value, '__name__') and all(not isinstance(value, item.__class__) for item in readonly):
            value.__name__ = '.'.join([cls.__name__, name])
        if name.startswith('_') or isinstance(value, property):
            attributes[name] = value
        elif not callable(value) or issubclass(value, field.option_t):
            properties[name] = value
        else:
            subclass[name] = namespace(value)
        continue

    def collectproperties(object):
        result = []
        for name, value in object.items():
            if isinstance(value, type):
                fmt = '<iota>'
            elif hasattr(value, '__class__'):
                fmt = "{!s}".format(value)
            else:
                raise ValueError(name)
            doc = value.__doc__.split('\n')[0] if getattr(value, '__doc__', '') else None
            result.append((name, fmt, doc))
        return result

    def formatproperties(items):
        namewidth = max(len(name) for name, _, _ in items) if items else 0
        formatwidth = max(len(fmt) for _, fmt, _ in items) if items else 0

        result = []
        for name, value, documentation in items:
            fmt = ("{name:{:d}s} : {value:{:d}s} # {documentation:s}" if documentation else "{name:{:d}s} : {value:{:d}s}").format
            result.append(fmt(namewidth, formatwidth, name=name, value=value, documentation=documentation))
        return result

    def __repr__(self):
        formatdescription = ("{{{!s}}} # {}\n" if getattr(cls, '__doc__', '') else "{{{!s}}}\n").format

        items = collectproperties(properties)
        props = formatproperties(items)

        subclasses = ["{{{:s}}}\n...".format('.'.join([cls.__name__, name])) for name in subclass.keys()]
        res = formatdescription(cls.__name__, *([cls.__doc__] if getattr(cls, '__doc__', '') else [])) + '\n'.join(props)
        if subclasses:
            return res + '\n' + '\n'.join(subclasses) + '\n'
        return res + '\n'

    def __setattr__(self, name, value):
        if name in attributes:
            object.__setattr__(self, name, value)
            return
        raise AttributeError("Configuration '{:s}' does not have field named '{:s}'".format(cls.__name__, name))

    attributes['__repr__'] = __repr__
    attributes['__setattr__'] = __setattr__
    attributes.update((name, property(lambda _, name=name: properties[name])) for name in properties)
    attributes.update((name, property(lambda _, name=name: subclass[name])) for name in subclass)
    cons = type(cls.__name__, cls.__bases__, attributes)
    result = cons()

    # Go through the attributes and fix their names so that they display properly
    # on both Python2 _and_ Python3. This is because Py3 fucks up their display
    # by not including the full contents of the .__name__ property in their output.
    for name in properties:
        value = getattr(result, name)
        fullname = name if not hasattr(value, '__name__') and isinstance(value, object) else value.__name__
        components = fullname.rsplit('.', 1)
        if len(components) > 1:
            prefix, name = components
            value.__module__, value.__name__ = '.'.join([value.__module__, prefix]), name
        continue

    return result

def configuration(cls):
    attributes, properties, subclass = dict(cls.__dict__), {}, {}
    for name, value in attributes.items():
        if name.startswith('_'):
            continue
        elif isinstance(value, field.descriptor):
            properties[name] = value
        elif not hasattr(value, '__class__'):
            subclass[name] = configuration(value)
        elif hasattr(object, '__sizeof__') and object.__sizeof__(value) == object.__sizeof__(type):
            subclass[name] = configuration(value)

        # we should never be here if we're running in cpython (py2 or py3)
        elif getattr(sys, 'implementation', ['cpython'])[0] in {'cpython'}:
            raise TypeError(name, value)

        # if we fallthrough, then we should be micropython or something else
        else:
            subclass[name] = configuration(value)
        continue

    def collectproperties(object, values):
        result = []
        for name, value in object.items():
            documentation = value.__doc__.split('\n')[0] if value.__doc__ else None
            result.append((name, values[name], documentation))
        return result

    def formatproperties(items):
        namewidth = max(len(name) for name, _, _ in items)
        formatwidth = max(len("{!r}".format(format)) for _, format, _ in items)

        result = []
        for name, value, documentation in items:
            fmt = ("{name:{:d}s} = {value:<{:d}s} # {doc:s}" if documentation else "{name:{:d}s} = {value:<{:d}s}").format
            result.append(fmt(namewidth, formatwidth, name=name, value="{!r}".format(value), doc=documentation))
        return result

    def __repr__(self):
        formatdescription = ('[{!s}] # {}\n' if getattr(cls, '__doc__', '') else '[{!s}]\n').format

        values = {name : getattr(self, name, None) for name in properties}
        items = collectproperties(properties, values)

        res = formatdescription(cls.__name__, *([cls.__doc__.split('\n')[0]] if getattr(cls, '__doc__', '') else [])) + '\n'.join(formatproperties(items))
        subclasses = ["[{:s}]\n...".format('.'.join([cls.__name__, name])) for name in subclass.keys()]
        if subclasses:
            return res + '\n' + '\n'.join(subclasses) + '\n'
        return res + '\n'

    def __setattr__(self, name, value):
        if name in attributes:
            object.__setattr__(self, name, value)
            return
        raise AttributeError("Namespace '{:s}' does not have a field named '{:s}'".format(cls.__name__, name))

    attributes['__repr__'] = __repr__
    attributes['__setattr__'] = __setattr__
    attributes.update({name : property(lambda _, name=name: subclass[name]) for name in subclass})
    result = type(cls.__name__, cls.__bases__, attributes)
    return result()

### constants that can be used as options
@namespace
class byteorder:
    '''Byte order constants'''
    bigendian = field.option('bigendian', 'Specify big-endian ordering')
    littleendian = field.option('littleendian', 'Specify little-endian ordering')

@namespace
class partial:
    fractional = field.option('fractional', 'Display the sub-offset as a fraction of a bit (0.0, 0.125, 0.25, ..., 0.875)')
    hex = field.option('hex', 'Display the sub-offset in hexadecimal (0.0, 0.2, 0.4, ..., 0.c, 0.e)')
    bit = field.option('bit', 'Display the sub-offset as just the bit number (0.0, 0.1, 0.2, ..., 0.7)')

### new-config
@configuration
class defaults:
    log = field.type('default-logger', logging.Logger, 'Default logging facility and level.')

    class integer:
        size = field.type('integersize', integer_types, 'The word-size of the architecture.')
        order = field.enum('byteorder', (byteorder.bigendian, byteorder.littleendian), 'The byteorder to use for new integers and pointers.')

    class ptype:
        clone_name = field.type('clone_name', string_types, 'The formatspec to use when mangling the name during the cloning a type (will only affect newly cloned).')
        noncontiguous = field.bool('noncontiguous', 'Allow optimization for non-contiguous ptype.container elements.')

    class pint:
        bigendian_name = field.type('bigendian_name', string_types, 'The formatspec to use when mangling the names for integers that are big-endian.')
        littleendian_name = field.type('littleendian_name', string_types, 'The formatspec to use when mangling the names for integers that are little-endian.')

    class parray:
        break_on_max_count = field.bool('break_on_max_count', 'If a dynamic array is larger than max_count, then raise an exception.')
        max_count = field.type('max_count', integer_types, 'Notify via a warning (exception if \'break_on_max_count\') when length is larger than max_count.')

    class pstruct:
        use_offset_on_duplicate = field.bool('use_offset_on_duplicate', 'If a name is duplicated, suffix it with the field offset (otherwise its index).')

    class display:
        show_module_name = field.bool('show_module_name', 'Include the full module name when displaying a summary.')
        show_parent_name = field.bool('show_parent_name', 'Include the parent name when displaying a summary.')
        mangle_with_attributes = field.bool('mangle_with_attributes', 'Allow instance attribute names to be used in the name-mangling formatspecs (cloning or byteorder).')

        class hexdump:
            '''Formatting for a hexdump'''
            width = field.type('width', integer_types)
            threshold = field.type('threshold', integer_types)

        class threshold:
            '''Width and Row thresholds for displaying summaries'''
            summary = field.type('summary_threshold', integer_types, 'Maximum number of bytes for a summary before shortening it with \'summary_message\'.')
            summary_message = field.type('summary_threshold_message', string_types, 'Formatspec to use before summary has reached its threshold.')
            details = field.type('details_threshold', integer_types, 'Maximum number of bytes for details before replacing it with \'details_message\'.')
            details_message = field.type('details_threshold_message', string_types, 'Formatspec to use before details have reached their threshold.')

    class pbinary:
        '''How to display attributes of an element containing binary fields which might not be byte-aligned'''
        offset = field.enum('offset', (partial.bit, partial.fractional, partial.hex), 'The format to use when displaying the sub-offset for binary types.')

        bigendian_name = field.type('bigendian_name', string_types, 'The formatspec to use for elements which are read most-significant to least-significant.')
        littleendian_name = field.type('littleendian_name', string_types, 'The formatspec to use for elements which are read least-significant to most-significant.')

    def __getsource():
        import ptypes.ptype
        return ptypes.ptype.source
    def __setsource(value):
        import ptypes.ptype
        if all(hasattr(value, method) for method in ('seek','store','consume')) or isinstance(value, provider.base):
            ptypes.ptype.source = value
            return
        raise ValueError("Invalid source object")
    source = field.set('default-source', __getsource, __setsource, 'Default source used that data will be load from or committed to in new instances.')

### defaults
# logging
defaults.log = log = logging.getLogger('ptypes')
log.setLevel(log.level)
log.propagate = 1

if 'micropython' and hasattr(logging, 'StreamHandler'):
    res = logging.StreamHandler(None)
    res.setFormatter(logging.Formatter("[%(created).3f] <%(process)x.%(thread)x> [%(levelname)s:%(name)s] %(message)s", None))
    log.addHandler(res)
    del(res)
del(log)

# general integers
defaults.integer.size = math.trunc(math.log(2 * (sys.maxsize + 1), 2) // 8)
defaults.integer.order = byteorder.littleendian if sys.byteorder == 'little' else byteorder.bigendian if sys.byteorder == 'big' else None

# display
defaults.display.show_module_name = False
defaults.display.show_parent_name = False
defaults.display.hexdump.width = 16
defaults.display.hexdump.threshold = 8
defaults.display.threshold.summary = 80
defaults.display.threshold.details = 8
defaults.display.threshold.summary_message = ' ..skipped ~{leftover} bytes.. '
defaults.display.threshold.details_message = ' ..skipped {leftover} rows, {skipped} bytes.. '
defaults.display.mangle_with_attributes = False

# array types
defaults.parray.break_on_max_count = False
defaults.parray.max_count = sys.maxsize

# structures
defaults.pstruct.use_offset_on_duplicate = True

# root types
defaults.ptype.noncontiguous = False
#defaults.ptype.clone_name = 'clone({})'
#defaults.pint.bigendian_name = 'bigendian({})'
#defaults.pint.littleendian_name = 'littleendian({})'
defaults.ptype.clone_name = 'c({})'

# integer types
defaults.pint.bigendian_name = 'be({})' if sys.byteorder.startswith('little') else '{}'
defaults.pint.littleendian_name = 'le({})' if sys.byteorder.startswith('big') else '{}'

# pbinary types
defaults.pbinary.offset = partial.hex
defaults.pbinary.bigendian_name = 'pb({})'
defaults.pbinary.littleendian_name = 'pble({})'

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
        byteorder = field.enum('byteorder', (consts.bigendian, consts.littleendian), 'The endianness of integers/pointers')
        integersize = field.type('integersize', integer_types, 'The word-size of the architecture')

        class display:
            summary = field.type('single-line', integer_types)
            details = field.type('multi-line', integer_types)
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
                raise ValueError("Invalid source object")
            ptype.source = value
        source = field.set('default-source', __getsource, __setsource, 'Default source to load/commit data from/to')

    #ptypes.config.logger = logging.root
    print("{!r}".format(consts))
    print("{!r}".format(consts.blah))
    print("{!r}".format(consts.huh))
    print("{!r}".format(config))
    print("{!r}".format(config.display))
