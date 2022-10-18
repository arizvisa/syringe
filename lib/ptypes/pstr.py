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
import sys, itertools
import codecs

from . import ptype, parray, pint, bitmap, utils, error, pstruct, provider

from . import config
Config = config.defaults
Log = config.logging.getLogger('.'.join([Config.log.name, 'pstr']))

# Setup some version-agnostic types that we can perform checks with
__izip_longest__ = utils.izip_longest
integer_types, string_types, text_types = bitmap.integer_types, utils.string_types, utils.text_types

def __ensure_text__(input, encoding='utf-8', errors='strict'):
    '''ripped from six v1.12.0'''
    if isinstance(input, (bytes, bytearray)):
        unencoded = bytes(input) if isinstance(input, bytearray) else input
        return input.decode(encoding, errors)
    elif isinstance(input, text_types):
        return input
    raise TypeError("not expecting type '{!s}'".format(input.__class__))

def guess_character_encoding(self):
    if hasattr(self, 'encoding'):
        res = self.encoding
    elif isinstance(self.parent, string):
        res = self.parent.encoding
    elif hasattr(self, 'length'):
        table = {1: Config.pstr.encoding, 2: Config.pstr.wide_encoding}
        res = table[self.length]
    else:
        res = sys.getdefaultencoding()
    return codecs.lookup(res) if isinstance(res, string_types) else res

def guess_string_encoding(self):
    if hasattr(self, 'encoding'):
        res = self.encoding
    elif hasattr(self._object_, 'encoding'):
        res = self._object_.encoding
    elif hasattr(self, 'length'):
        table = {1: Config.pstr.encoding, 2: Config.pstr.wide_encoding}
        res = table[self.length]
    else:
        res = sys.getdefaultencoding()
    return codecs.lookup(res) if isinstance(res, string_types) else res

unicode_escape = codecs.lookup('unicode_escape')
def string_escape(string, encoding=codecs.lookup(sys.getdefaultencoding())):
    encoded, _ = unicode_escape.encode(string)
    res, _ = encoding.decode(encoded)
    return res

class _char_t(pint.type):
    def __init__(self, **attrs):
        super(_char_t, self).__init__(**attrs)
        self.encoding = encoding = guess_character_encoding(self)

        # if we weren't given a length, then calculate the size of
        # .length based on the .encoding that we're using.
        if not hasattr(self, 'length'):
            res, _ = encoding.encode('\0')
            self.length = len(res)
        return

    def __setvalue__(self, *values, **attrs):
        '''Set the _char_t to the str ``value``.'''
        if not values:
            return super(pint.type, self).__setvalue__(*values, **attrs)

        value, = values

        if isinstance(value, integer_types):
            return super(_char_t, self).__setvalue__(value)

        elif isinstance(value, (bytes, bytearray)):
            return super(pint.type, self).__setvalue__(bytes(value) if isinstance(value, bytearray) else value)

        elif isinstance(value, string_types):
            res, _ = self.encoding.encode(value)
            return super(pint.type, self).__setvalue__(res, **attrs)

        raise ValueError(self, '_char_t.set', 'User tried to set a value with an unsupported type : {:s}'.format(value.__class__))

    def str(self):
        '''Try to decode the _char_t to a character.'''
        data = self.serialize()
        try:
            res, _ = self.encoding.decode(data, errors='replace')
        except UnicodeDecodeError as E:
            raise UnicodeDecodeError(E.encoding, E.object, E.start, E.end, 'Unable to decode string {!r} with requested encoding : {!s}'.format(data, getattr(self.encoding, 'name', self.encoding)))
        return res

    def __getvalue__(self):
        '''Decode the _char_t to a character replacing any invalid characters if they don't decode.'''
        data, decode = self.serialize(), self.encoding.incrementaldecoder('strict').decode
        res = decode(data)
        return res if len(res) else data

    def int(self):
        return super(_char_t, self).__getvalue__()

    def summary(self, **options):
        res, integer = self.__getvalue__(), self.int()
        if isinstance(res, string_types):
            escaped = string_escape(res)
            q, escaped = ('"', escaped) if "'" in escaped and '"' not in escaped else ('\'', escaped.replace('\'', '\\\''))
            #q, escaped = ('"', res) if "'" in res and '"' not in res else ('\'', res.replace('\'', '\\\''))
            return u"{:#0{:d}x} {:s}".format(integer, 2 + 2 * self.size(), q + escaped + q)
        return u"{:#0{:d}x} {!s}".format(integer, 2 + 2 * self.size(), res)

    @classmethod
    def typename(cls):
        return '{:s}<{:s}>'.format(cls.__name__, getattr(cls.encoding, 'name', cls.encoding))

class char_t(_char_t):
    '''Single character type'''
    length, encoding = 1, Config.pstr.encoding

    def str(self):
        '''Return the character instance as a str type.'''
        return str(super(char_t, self).str())

    @classmethod
    def typename(cls):
        return cls.__name__

uchar_t = char_t    # yeah, secretly there's no difference..

class wchar_t(_char_t):
    '''Single wide-character type'''
    length, encoding = 2, Config.pstr.wide_encoding

class string(ptype.type):
    '''String of characters'''
    length = None
    _object_ = char_t
    initializedQ = lambda self: self.value is not None    # bool

    def __init__(self, **attrs):
        res = super(string, self).__init__(**attrs)

        # update the encoding property in case we were given a string and cache the
        # element object that's responsible for interacting with individual elements.
        encoding = self.encoding = guess_string_encoding(self)

        # ensure that self._object_ is using a character type that matches our string encoding.
        bytes, length = encoding.encode('\0')

        # check that the load size of the encoding corresponds to the character size.
        if (self.new(self._object_).blocksize(), 1) != (len(bytes), length):
            raise ValueError(self.classname(), 'string.__init__', 'User tried to specify an encoding that does not match the character size : {:s}'.format(encoding if isinstance(encoding, string_types) else encoding.name))
        return

    def at(self, offset, **kwds):
        ofs = offset - self.getoffset()
        return self[ ofs // self._object_(encoding=self.encoding).blocksize() ]

    def __blocksize_originalQ__(self):
        '''Return whether the instance's blocksize has been rewritten by a definition.'''
        cls = self.__class__
        return utils.callable_eq(self, self.blocksize, cls, cls.blocksize) and utils.callable_eq(cls, cls.blocksize, string, string.blocksize)
    def blocksize(self):
        length = self.length or 0
        cb, _ = self.encoding.encode('\0')
        return len(cb) * length

    def __insert(self, index, string):
        l, _ = self.encoding.encode('\0')
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset:]

    def __delete(self, index):
        l, _ = self.encoding.encode('\0')
        offset = index * l
        self.value = self.value[:offset] + self.value[offset+l:]

    def __replace(self, index, string):
        l, _ = self.encoding.encode('\0')
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset+l:]

    def __fetch(self, index):
        l, _ = self.encoding.encode('\0')
        offset = index * l
        return self.value[offset : offset + l]

    def __len__(self):
        if not self.initializedQ():
            raise error.InitializationError(self, 'string.__len__')
        cb, _ = self.encoding.encode('\0')
        return len(self.value) // len(cb)

    def __delitem__(self, index):
        '''Remove the character at the specified ``index``.'''
        if isinstance(index, slice):
            raise error.ImplementationError(self, 'string.__delitem__', message='slice support not implemented')
        self.__delete(index)

    def __getitem__(self, index):
        '''Return the character at the specified ``index``.'''
        cb, _ = self.encoding.encode('\0')
        count, object = len(self.value) // len(cb), ptype.clone(self._object_, encoding=self.encoding)
        res = self.cast(ptype.clone(parray.type, _object_=object, length=count))

        # handle a slice of glyphs
        if isinstance(index, slice):
            result = [res.value[i] for i in range(*index.indices(count))]

            # ..and now turn the slice into an array
            type = ptype.clone(parray.type, length=count, _object_=object)
            return self.new(type, offset=result[0].getoffset() if result else self.getoffset(), value=result, parent=self)

        if index < -len(self) or index >= len(self):
            raise error.UserError(self, 'string.__getitem__', message='list index {:d} out of range'.format(index))

        # otherwise, returning a single element from the array should be good
        index %= len(self)
        res[index].parent = self
        return res[index]

    def __setitem__(self, index, value):
        '''Replace the character at ``index`` with the character ``value``'''
        cb, _ = self.encoding.encode('\0')
        count, object = len(self.value) // cb, ptype.clone(self._object_, encoding=self.encoding)

        # convert self into an array we can modify
        res = self.cast(ptype.clone(parray.type, _object_=object, length=count))

        # handle a slice of glyphs
        if isinstance(index, slice):
            indices = range(*index.indices(count))
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
        self.__insert(index, object.serialize())

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

    def __setvalue__(self, *values, **attrs):
        '''Replaces the contents of ``self`` with the string ``value``.'''
        if not values:
            return super(string, self).__setvalue__(*values, **attrs)

        value, = values
        cb, _ = self.encoding.encode('\0')

        size, esize = self.size() if self.initializedQ() else self.blocksize(), len(cb)
        encoded, _ = self.encoding.encode(value) if isinstance(value, string_types) else value

        object = ptype.clone(self._object_, encoding=self.encoding)
        result = parray.type(_object_=object, length=size // esize)

        # Now we can finally izip_longest here...
        iterable = zip(*[iter(bytearray(encoded))] * esize)
        for element, glyph in __izip_longest__(result.alloc(), iterable):
            if element is None:
                break
            element.set(bytes(bytearray(glyph or cb)))
        return self.load(offset=0, source=provider.proxy(result), blocksize=(lambda cb=result.blocksize(): cb))

    def alloc(self, *values, **attrs):
        '''Allocate the instance using the provided string and attributes.'''
        if not values:
            return super(string, self).alloc(*values, **attrs)

        object = ptype.clone(self._object_, encoding=self.encoding)
        value, = values

        size, esize = self.size() if self.initializedQ() else self.blocksize(), self.new(object).a.size()
        glyphs = [ item for item in value ]

        t = ptype.clone(parray.type, _object_=object)
        result = t(length=len(glyphs))

        # Now we can finally izip_longest here...
        for element, glyph in __izip_longest__(result.alloc(), value):
            if element is None:
                break
            element.set(glyph or '\0')

        self.length = len(result)
        return self.load(offset=0, source=provider.proxy(result))

    def str(self):
        '''Decode the string into the specified encoding type.'''
        return self.__getvalue__()

    def __getvalue__(self):
        '''Try and decode the string into the specified encoding type.'''
        encoding = self.encoding
        cb, _ = encoding.encode('\0')
        t = ptype.clone(parray.type, _object_=self._object_, length=self.size() // len(cb))
        data = self.cast(t).serialize()
        try:
            res, length = encoding.decode(data)
        except UnicodeDecodeError:
            Log.warning('{:s}.str : {:s} : Unable to decode {:s} to {:s}. Defaulting to unencoded string.'.format(self.classname(), self.instance(), self._object_.typename(), encoding.name))
            res, length = data.decode(encoding.name, errors='replace')
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

        escaped = string_escape(res)
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
        nullbytes, _ = self.encoding.encode('\0')
        nullstr, _ = self.encoding.decode(nullbytes)

        if isinstance(value, string_types) and value.endswith(nullstr):
            value += nullstr
        elif isinstance(value, bytes) and value.endswith(nullbytes):
            value += nullbytes

        data, _ = self.encoding.encode(value)
        result = parray.type(_object_=self._object_, length=len(data) // len(nullbytes))

        # iterate through everything
        iterable = zip(*[iter(bytearray(data))] * len(nullbytes))
        for element, glyph in __izip_longest__(result.alloc(), iterable):
            if element is None or glyph is None: break
            element.set(bytes(bytearray(glyph)))

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

    def str(self):
        res = self.__getvalue__()
        return utils.strdup(res)

    def __deserialize_stream__(self, stream):
        self.value = b''

        # instantiate a new character object that we will reuse when
        # deserializing any input and checking for a terminator.
        item = self.new(self._object_, offset=self.getoffset())
        while True:
            res = utils.islice(stream, item.blocksize())
            item.__deserialize_block__(bytes().join(res))

            # we now have a character to deserialize into our value
            # after which we can check to see if it's a sentinel.
            offset = self.__append__(item)
            if self.isTerminator(item):
                break
            continue
        return self

    def __blocksize_originalQ__(self):
        '''Return whether the instance's blocksize has been rewritten by a definition.'''
        cls = self.__class__
        return utils.callable_eq(self, self.blocksize, cls, cls.blocksize) and utils.callable_eq(cls, cls.blocksize, szstring, szstring.blocksize)
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
    import ptypes, functools
    from ptypes import pint, pstr, parray, pstruct, dyn, provider, utils
    from ptypes.utils import operator

    fromhex = operator.methodcaller('decode', 'hex') if sys.version_info[0] < 3 else bytes.fromhex

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
        if x.str() == string[:len(string) // 2].decode(getattr(x[0].encoding, 'name', x[0].encoding)):
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
            if isinstance(s, text_types):
                return s.encode(encoding, errors)
            elif isinstance(s, bytes):
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
        x.set(data)
        if x.serialize() == b'hola\0\0\0\0\0\0':
            raise Success

    @TestCase
    def test_str_set_resized():
        data = 'hola'
        x = pstr.string(length=10).a
        if x.serialize() != b'\0\0\0\0\0\0\0\0\0\0':
            raise Failure
        x.alloc(data)
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

    @TestCase
    def test_str_mb_loading_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        x = pstr.string(encoding='shift-jis', length=len(data), source=ptypes.provider.bytes(data)).l
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_str_mb_decoding_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        s = data.decode('shiftjis')
        x = pstr.string(length=len(data) - 1, encoding='shift-jis').a.set(s)
        if x.size() == len(data) - 1 and x.str() == s[:-1]:
            raise Success

    @TestCase
    def test_str_mb_encoding_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        x = pstr.string(encoding='shift-jis', length=len(data)).a.set(data.decode('shift-jis'))
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_str_wb_loading_utf16():
        data = b'\xd50\xa10\xa40\xeb0\rT\x00\x00'
        x = pstr.wstring(length=len(data) // 2, source=ptypes.provider.bytes(data)).l
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_str_wb_decoding_utf16():
        data = b'\xd50\xa10\xa40\xeb0\rT\x00\x00'
        s = data.decode('utf-16-le')
        x = pstr.wstring(length=len(data) // 2, encoding='utf-16-le').a.set(s)
        if x.size() == len(data) and x.str() == s:
            raise Success

    @TestCase
    def test_str_wb_encoding_utf16():
        data = b'\xd50\xa10\xa40\xeb0\rT\x00\x00'
        x = pstr.wstring(length=len(data) // 2, encoding='utf-16-le').a.set(data.decode('utf-16'))
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_str_szstring_loading_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        x = pstr.szstring(encoding='shift-jis', source=ptypes.provider.bytes(data + b'\0'*10)).l
        if x.serialize() == data:
            raise Success

    @TestCase
    def test_str_szstring_decoding_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        s = data.decode('shiftjis')
        x = pstr.szstring(encoding='shift-jis').a.set(s)
        if x.size() == len(data) and x.str() == s.rstrip('\0'):
            raise Success

    @TestCase
    def test_str_szstring_encoding_shiftjis():
        data = b'\x88\xea\x91\xbe\x98Y 2022-8/Pro/Government \x95\xb6\x8f\x91\x00'
        x = pstr.szstring(encoding='shift-jis').a.set(data.decode('shift-jis'))
        if x.serialize() == data:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
