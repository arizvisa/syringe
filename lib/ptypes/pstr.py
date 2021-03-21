"""Primitive string types.

A pstr.type is an atomic type that is used to describe string types within a
data structure. They are treated internally as atomic types, but expose an
interface that allows one to modify each of it's particular characters.

The base type is named pstr.string and is sized according to the `.length`
property. An implied char_t type is assigned to the `._object_` property and is
used to determine what the size of each glyph in the string is. The dynamically
sized string types have no length due to them being terminated according to a
specific character terminator. Generally, string types have the following
interface:

    class interface(pstr.string):
        length = length-of-string
        def set(self, string):
            '''Set the string to the value of ``string``.'''
        def get(self):
            '''Return the value of ``self``'''
        def str(self):
            '''Return the string as a python str type.'''
        def insert(self, index, character):
            '''Insert the specified ``character`` at ``index`` of the pstr.string.'''
        def append(self, character):
            '''Append the ``character`` to the pstr.string'''
        def extend(self, iterable):
            '''Append each character in ``iterable`` to the pstr.string'''
        def __getitem__(self, index):
            '''Return the glyph at the specified ``index``'''
        def __getslice__(self, slice):
            '''Return the glyphs at the specified ``slice``'''
        def __len__(self):
            '''Return the number of characters within the string.'''

There are a few types that this module provides:

char_t -- a single character
wchar_t -- a single wide-character
string -- an ascii string of /self.length/ characters in length
wstring -- a wide-character string of /self.length/ characters in length
szstring -- a zero-terminated ascii string
szwstring -- a zero-terminated wide-character string
unicode -- an alias to wstring
szunicode -- an alias to szwstring

Example usage:
    # define a type
    from ptypes import pstr
    class type(pstr.string):
        length = 0x20

    # instantiate and load a type
    instance = type()
    instance.load()

    # fetch a specific character
    print(instance[1])

    # re-assign a new string
    instance.set("new string contents")

    # return the length of the type
    print(len(instance))

    # return the type in ascii
    value = instance.str()
"""
import sys, six
import itertools, operator, functools
import codecs

from . import ptype, parray, pint, utils, error, pstruct, provider, config
Config = config.defaults
Log = Config.log.getChild('pstr')

__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

def __ensure_text__(s, encoding='utf-8', errors='strict'):
    '''ripped from six v1.12.0'''
    if isinstance(s, six.binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, six.text_type):
        return s
    raise TypeError("not expecting type '%s'"% type(s))

class _char_t(pint.type):
    encoding = codecs.lookup('latin1')

    def __init__(self, **attrs):
        super(_char_t, self).__init__(**attrs)

        # calculate the size of .length based on .encoding
        null = b'\0'.decode('latin1')
        res = null.encode(self.encoding.name)
        self.length = len(res)

    def __setvalue__(self, *values, **attrs):
        '''Set the _char_t to the str ``value``.'''
        if not values:
            return super(pint.type, self).__setvalue__(*values, **attrs)

        value, = values

        if isinstance(value, six.integer_types):
            return super(_char_t, self).__setvalue__(value)

        elif isinstance(value, bytes):
            return super(pint.type, self).__setvalue__(value)

        elif isinstance(value, six.string_types):
            res = value.encode(self.encoding.name)
            return super(pint.type, self).__setvalue__(res, **attrs)

        raise ValueError(self, '_char_t.set', 'User tried to set a value with an incorrect type : {:s}'.format(value.__class__))

    def str(self):
        '''Try to decode the _char_t to a character.'''
        data = self.serialize()
        try:
            res = data.decode(self.encoding.name)
        except UnicodeDecodeError as E:
            raise UnicodeDecodeError(E.encoding, E.object, E.start, E.end, 'Unable to decode string {!r} to requested encoding : {:s}'.format(data, self.encoding.name))
        return res

    def __getvalue__(self):
        '''Decode the _char_t to a character replacing any invalid characters if they don't decode.'''
        data = self.serialize()
        try:
            res = data.decode(self.encoding.name)
        except UnicodeDecodeError:
            Log.warn('{:s}.get : {:s} : Unable to decode to {:s}. Replacing invalid characters. : {!r}'.format(self.classname(), self.instance(), self.encoding.name, data))
            res = data.decode(self.encoding.name, 'replace')
        return res

    def int(self):
        return super(_char_t, self).__getvalue__()

    def summary(self, **options):
        res = self.__getvalue__()
        escaped = res.encode('unicode_escape').decode(sys.getdefaultencoding())
        q, escaped = ('"', escaped) if "'" in escaped and '"' not in escaped else ('\'', escaped.replace('\'', '\\\''))
        #q, escaped = ('"', res) if "'" in res and '"' not in res else ('\'', res.replace('\'', '\\\''))
        return u"{:#0{:d}x} {:s}".format(ord(res), 2 + 2 * self.size(), q + escaped + q)

    @classmethod
    def typename(cls):
        return '{:s}<{:s}>'.format(cls.__name__, cls.encoding.name)

class char_t(_char_t):
    '''Single character type'''

    def str(self):
        '''Return the character instance as a str type.'''
        return str(super(char_t, self).str())

    @classmethod
    def typename(cls):
        return cls.__name__

uchar_t = char_t    # yeah, secretly there's no difference..

class wchar_t(_char_t):
    '''Single wide-character type'''

    # try and figure out what type
    if Config.integer.order == config.byteorder.littleendian:
        encoding = codecs.lookup('utf-16-le')
    elif Config.integer.order == config.byteorder.bigendian:
        encoding = codecs.lookup('utf-16-be')
    else:
        raise SystemError('wchar_t', 'Unable to determine default encoding type based on platform byteorder : {!r}'.format(Config.integer.order))

class string(ptype.type):
    '''String of characters'''
    length = 0
    _object_ = char_t
    initializedQ = lambda self: self.value is not None    # bool

    def __init__(self, **attrs):
        res = super(string, self).__init__(**attrs)

        # ensure that self._object_ is using a fixed-width encoding
        _object_ = self._object_

        # encode 3 types of strings and ensure that their lengths scale up with their string sizes
        res, single, double = ( __ensure_text__(item, 'ascii').encode(_object_.encoding.name) for item in ('\0', 'A', 'AA') )
        if len(res) * 2 == len(single) * 2 == len(double):
            return
        raise ValueError(self.classname(), 'string.__init__', 'User tried to specify a variable-width character encoding : {:s}'.format(_object_.encoding.name))

    def at(self, offset, **kwds):
        ofs = offset - self.getoffset()
        return self[ ofs // self._object_().blocksize() ]

    def blocksize(self):
        return self._object_().blocksize() * self.length

    def __insert(self, index, string):
        l = self._object_().blocksize()
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset:]

    def __delete(self, index):
        l = self._object_().blocksize()
        offset = index * l
        self.value = self.value[:offset] + self.value[offset+l:]

    def __replace(self, index, string):
        l = self._object_().blocksize()
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset+l:]

    def __fetch(self, index):
        l = self._object_().blocksize()
        offset = index * l
        return self.value[offset:offset+l]

    def __len__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'string.__len__')
        return len(self.value) // self._object_().blocksize()

    def __delitem__(self, index):
        '''Remove the character at the specified ``index``.'''
        if isinstance(index, slice):
            raise error.ImplementationError(self, 'string.__delitem__', message='slice support not implemented')
        self.__delete(index)

    def __getitem__(self, index):
        '''Return the character at the specified ``index``.'''
        res = self.cast(ptype.clone(parray.type, _object_=self._object_, length=len(self)))

        # handle a slice of glyphs
        if isinstance(index, slice):
            result = [res.value[i] for i in range(*index.indices(len(res)))]

            # ..and now turn the slice into an array
            type = ptype.clone(parray.type, length=len(result), _object_=self._object_)
            return self.new(type, offset=result[0].getoffset() if result else self.getoffset(), value=result, parent=self)

        if index < -len(self) or index >= len(self):
            raise error.UserError(self, 'string.__getitem__', message='list index {:d} out of range'.format(index))

        # otherwise, returning a single element from the array should be good
        index %= len(self)
        res[index].parent = self
        return res[index]

    def __setitem__(self, index, value):
        '''Replace the character at ``index`` with the character ``value``'''

        # convert self into an array we can modify
        res = self.cast(ptype.clone(parray.type, _object_=self._object_, length=len(self)))

        # handle a slice of glyphs
        if isinstance(index, slice):
            indices = range(*index.indices(len(res)))
            [ res[index].set(glyph) for glyph, index in __izip_longest__(value, indices) ]

        # handle a single glyph
        else:
            res[index].set(value)

        # now we can re-load ourselves from it
        return self.load(offset=0, source=provider.proxy(res))

    def insert(self, index, object):
        '''Insert the character ``object`` into the string at index ``index`` of the string.'''
        if not isinstance(object, self._object_):
            raise error.TypeError(self, 'string.insert', message='expected value of type {!r}. received {!r}'.format(self._object_, object.__class__))
        self.__insert(index, value.serialize())

    def append(self, object):
        '''Append the character ``object`` to the string and return its offset.'''
        return self.__append__(object)

    def __append__(self, object):
        if not isinstance(object, self._object_):
            raise error.TypeError(self, 'string.append', message='expected value of type {!r}. received {!r}'.format(self._object_, object.__class__))
        offset = self.getoffset() + self.size()
        self.value += object.serialize()
        return offset

    def extend(self, iterable):
        '''Extend the string ``self`` with the characters provided by ``iterable``.'''
        [ self.append(item) for item in iterable ]
        return self

    def __setvalue__(self, *values, **retain):
        """Replaces the contents of ``self`` with the string ``value``.

        Does not resize the string according to the length of ``value`` unless the ``retain`` attribute is cleared.
        """
        if not values:
            return self

        value, = values

        size, esize = self.size() if self.initializedQ() else self.blocksize(), self.new(self._object_).a.size()
        glyphs = [ item for item in value ]

        t = ptype.clone(parray.type, _object_=self._object_)
        result = t(length=size // esize) if retain.get('retain', True) else t(length=len(glyphs))

        # Now we can finally izip_longest here...
        for element, glyph in __izip_longest__(result.alloc(), value):
            if element is None:
                break
            element.set(glyph or '\0')

        if retain.get('retain', True):
            return self.load(offset=0, source=provider.proxy(result), blocksize=(lambda cb=result.blocksize(): cb))

        self.length = len(result)
        return self.load(offset=0, source=provider.proxy(result))

    def alloc(self, *args, **fields):
        res = super(string, self).alloc(**fields)
        return res.set(*args) if args else res

    def str(self):
        '''Decode the string into the specified encoding type.'''
        res = self.__getvalue__()
        return utils.strdup(res)

    def __getvalue__(self):
        '''Try and decode the string into the specified encoding type.'''
        t = ptype.clone(parray.type, _object_=self._object_, length=len(self))
        data = self.cast(t).serialize()
        try:
            res = data.decode(t._object_.encoding.name)
        except UnicodeDecodeError:
            Log.warn('{:s}.str : {:s} : Unable to decode {:s} to {:s}. Defaulting to unencoded string.'.format(self.classname(), self.instance(), self._object_.typename(), t._object_.encoding.name))
            res = data.decode(t._object_.encoding.name, 'ignore')
        return res

    def get(self):
        res = self.__getvalue__()
        return utils.strdup(res)

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            offset, blocksize = self.getoffset(), self.blocksize()
            self.source.seek(offset)
            try:
                block = self.source.consume(blocksize)
                result = self.__deserialize_block__(block)

            # If the provider gave us an error, then recast it as a load
            # error due to being an exception while loading a block
            except (StopIteration, error.ProviderError) as E:
                self.source.seek(offset + self.size())
                raise error.LoadError(self, consumed=blocksize, exception=E)
        return result

    def __deserialize_block__(self, block):
        if len(block) != self.blocksize():
            raise error.ConsumeError(self, self.getoffset(), self.blocksize(), amount=len(block))
        self.value = block
        return self

    def serialize(self):
        if self.initializedQ():
            return bytes(self.value)
        raise error.InitializationError(self, 'string.serialize')

    def summary(self, **options):
        try:
            res = self.__getvalue__()

        except UnicodeDecodeError:
            Log.debug('{:s}.summary : {:s} : Unable to decode unicode string. Rendering as hexdump instead.'.format(self.classname(), self.instance()))
            return super(string, self).summary(**options)

        escaped = res.encode('unicode_escape').decode(sys.getdefaultencoding())
        q, escaped = ('"', escaped) if '\'' in escaped and '"' not in escaped else ('\'', escaped.replace('\'', '\\\''))
        return u"({:d}) {:s}".format(len(res), q + escaped + q)

    def repr(self, **options):
        return self.summary(**options) if self.initializedQ() else '???'

    def classname(self):
        return '{:s}<{:s}>'.format(super(string, self).classname(), self._object_.typename())
type = string

class szstring(string):
    '''Standard null-terminated string'''
    _object_ = char_t
    length = None
    def isTerminator(self, value):
        return value.int() == 0

    def __setvalue__(self, *values, **attrs):
        """Set the null-terminated string to ``value``.

        Resizes the string according to the length of ``value``.
        """
        if not values:
            return self

        value, = values

        # FIXME: if .isTerminator() is altered for any reason, this won't work.
        null = self.new(self._object_).a
        if not value.endswith(null.str()):
            value += null.str()

        t = ptype.clone(parray.type, _object_=self._object_, length=len(value))
        result = t()

        # iterate through everything
        for element, glyph in __izip_longest__(result.alloc(), value):
            if element is None or glyph is None: break
            element.set(glyph)

        return self.load(offset=0, source=provider.proxy(result))

    def __deserialize_block__(self, block):
        data = bytearray(block)
        stream = (bytes(data[idx : idx + 1]) for idx, _ in enumerate(data))
        return self.__deserialize_stream__(stream)

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            offset = self.getoffset()
            self.source.seek(offset)
            try:
                producer = (self.source.consume(1) for byte in itertools.count())
                result = self.__deserialize_stream__(producer)

            # If the provider gave us an error, then recast it as a load
            # error due to being an exception while loading a block
            except (StopIteration, error.ProviderError) as E:
                self.source.seek(offset + self.size())
                raise error.LoadError(self, consumed=self.size(), exception=E)
        return result

    def __deserialize_stream__(self, stream):
        self.value = b''

        # instantiate a new character object that we will reuse when
        # deserializing any input and checking for a terminator.
        item = self.new(self._object_, offset=self.getoffset())
        while True:
            res = itertools.islice(stream, item.blocksize())
            item.__deserialize_block__(bytes().join(res))

            # we now have a character to deserialize into our value
            # after which we can check to see if it's a sentinel.
            offset = self.__append__(item)
            if self.isTerminator(item):
                break
            continue
        return self

    def blocksize(self):
        return self.size() if self.initializedQ() else self.load().size()

    def summary(self, **options):
        try:
            res = self.__getvalue__()

        except UnicodeDecodeError:
            Log.debug('{:s}.summary : {:s} : Unable to decode unicode string. Rendering as hexdump instead.'.format(self.classname(), self.instance()))
            return super(szstring, self).summary(**options)

        escaped = utils.strdup(res).encode('unicode_escape').decode(sys.getdefaultencoding())
        q, escaped = ('"', escaped) if '\'' in escaped and '"' not in escaped else ('\'', escaped.replace('\'', '\\\''))
        return u"({:d}) {:s}".format(len(res), q + escaped + q)

class wstring(string):
    '''String of wide-characters'''
    _object_ = wchar_t

class szwstring(szstring, wstring):
    '''Standard null-terminated string of wide-characters'''
    _object_ = wchar_t

## aliases that should probably be improved
unicode = wstring
szunicode = szwstring

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
                raise
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import six, ptypes
    from ptypes import pint,pstr,parray,pstruct,dyn,provider,utils

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info.major < 3 else bytes.fromhex

    @TestCase
    def test_str_char():
        x = pstr.char_t(source=provider.bytes(b'hello')).l
        if x.get() == 'h':
            raise Success

    @TestCase
    def test_str_wchar():
        x = pstr.wchar_t(source=provider.bytes(b'\x43\x00')).l
        if x.get() == '\x43':
            raise Success

    @TestCase
    def test_str_string():
        x = pstr.string()
        string = b'helllo world ok, i\'m hungry for some sushi\0'
        x.length = len(string) // 2
        x.source = provider.bytes(string)
        x.load()
        if x.str() == string[:len(string) // 2].decode(x[0].encoding.name):
            raise Success

    @TestCase
    def test_str_wstring():
        x = pstr.wstring()
        oldstring = b'ok, this is unicode'
        string = oldstring
        x.length = len(string) // 2
        string = bytes(bytearray(functools.reduce(operator.add, ([c, 0] for c in bytearray(string)))))
        x.source = provider.bytes(string)
        x.load()
        if x.str() == oldstring[:len(oldstring) // 2].decode('ascii'):
            raise Success

    @TestCase
    def test_str_szstring():
        string = b'null-terminated\0ok'
        x = pstr.szstring(source=provider.bytes(string)).l
        if x.str() == 'null-terminated':
            raise Success

    @TestCase
    def test_str_array_szstring():
        data = b'here\0is\0my\0null-terminated\0strings\0eof\0stop here okay plz'

        class stringarray(parray.terminated):
            _object_ = pstr.szstring

            def isTerminator(self, value):
                if value.str() == 'eof':
                    return True
                return False

        x = stringarray(source=provider.bytes(data)).l
        if x[3].str() == 'null-terminated':
            raise Success

    @TestCase
    def test_str_struct_szstring():
        class IMAGE_IMPORT_HINT(pstruct.type):
            _fields_ = [
                ( pint.uint16_t, 'Hint' ),
                ( pstr.szstring, 'String' )
            ]

        x = IMAGE_IMPORT_HINT(source=provider.bytes(b'AAHello world this is a zero0-terminated string\0this didnt work')).l
        if x['String'].str() == 'Hello world this is a zero0-terminated string':
            raise Success

    @TestCase
    def test_str_szwstring():
        s = b'C\x00:\x00\\\x00P\x00y\x00t\x00h\x00o\x00n\x002\x006\x00\\\x00D\x00L\x00L\x00s\x00\\\x00_\x00c\x00t\x00y\x00p\x00e\x00s\x00.\x00p\x00y\x00d\x00\x00\x00'
        v = pstr.szwstring(source=provider.bytes(s)).l
        if v.str() == 'C:\Python26\DLLs\_ctypes.pyd':
            raise Success

    @TestCase
    def test_str_szwstring_customchar():
        data = ' '.join(map(operator.methodcaller('strip'), '''
            00 57 00 65 00 6c 00 63 00 6f 00 6d 00 65 00 00
        '''.split('\n'))).strip()
        data = bytes(bytearray(int(item, 16) for item in data.split(' ')))

        def __ensure_binary__(s, encoding='utf-8', errors='strict'):
            '''ripped from six v1.12.0'''
            if isinstance(s, six.text_type):
                return s.encode(encoding, errors)
            elif isinstance(s, six.binary_type):
                return s
            raise TypeError("not expecting type '%s'"% type(s))

        class wbechar_t(pstr.wchar_t):
            def set(self, value):
                self.value = b'\0' + __ensure_binary__(value)
                return self

            def get(self):
                return __ensure_text__(self.value, 'utf-16-be').encode('utf-8')

        class unicodestring(pstr.szwstring):
            _object_ = wbechar_t
            def str(self):
                s = self.value.decode('utf-16-be')
                return utils.strdup(s)[:len(self)]

        class unicodespeech_packet(pstruct.type):
            _fields_ = [
                (unicodestring, 'msg'),
            ]

        a = unicodestring(source=provider.bytes(data)).l
        if a.l.str() == 'Welcome':
            raise Success
        raise Failure

    @TestCase
    def test_str_szstring_customterm():
        class fuq(pstr.szstring):
            def isTerminator(self, value):
                return value.int() == 0x3f

        s = provider.bytes(b'hello world\x3f..................')
        a = fuq(source=s)
        a = a.l
        if a.size() == 12:
            raise Success

    @TestCase
    def test_wstr_struct():
        class record0085(pstruct.type):
            _fields_ = [
                (pint.uint16_t, 'unknown'),
                (pint.uint32_t, 'skipped'),
                (pint.uint16_t, 'sheetname_length'),
                (lambda s: dyn.clone(pstr.wstring, length=s['sheetname_length'].li.int()), 'sheetname'),
            ]
        s = ptypes.prov.bytes(fromhex('85001400e511000000000600530068006500650074003100')[4:])
        a = record0085(source=s)
        a=a.l
        if a['sheetname'].str() == 'Sheet1':
            raise Success

    @TestCase
    def test_str_szwstring_blockarray():
        data = fromhex('3d 00 3a 00 3a 00 3d 00 3a 00 3a 00 5c 00 00 00 65 00 2e 00 6c 00 6f 00 67 00 00 00 00 00 ab ab ab ab ab ab ab ab'.replace(' ', ''))
        source = ptypes.prov.bytes(data)
        t = dyn.blockarray(pstr.szwstring, 30)
        a = t(source=source).l
        if (a[0].str(),a[1].str(),a[2].str()) == ('=::=::\\','e.log','') and a[2].blocksize() == 2 and len(a) == 3:
            raise Success

    @TestCase
    def test_str_append_data():
        global x
        x = pstr.string(length=5).a
        data = 'hola mundo'
        [ x.append(pstr.char_t().set(by)) for by in data ]
        if x[5:].serialize() == data.encode('ascii'):
            raise Success

    @TestCase
    def test_str_append_data_getoffset():
        x = pstr.string(length=5, offset=0x10).a
        offset = x.append(pstr.char_t().set('F'))
        if offset == x.getoffset() + 5:
            raise Success

    @TestCase
    def test_str_set_retained():
        data = 'hola'
        x = pstr.string(length=10).a
        if x.serialize() != b'\0\0\0\0\0\0\0\0\0\0':
            raise Failure
        x.set(data, retain=True)
        if x.serialize() == b'hola\0\0\0\0\0\0':
            raise Success

    @TestCase
    def test_str_set_resized():
        data = 'hola'
        x = pstr.string(length=10).a
        if x.serialize() != b'\0\0\0\0\0\0\0\0\0\0':
            raise Failure
        x.set(data, retain=False)
        if x.serialize() == b'hola':
            raise Success

    @TestCase
    def test_str_set_default():
        data = 'hola'
        x = pstr.string(length=10).a
        if x.serialize() != b'\0\0\0\0\0\0\0\0\0\0':
            raise Failure
        x.set(data)
        if x.serialize() == b'hola\0\0\0\0\0\0':
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
