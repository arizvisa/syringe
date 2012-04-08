import ptype,parray
import pint,pstr,dyn,utils

class _char_t(pint.integer_t):
    length = 1
    def str(self):
        return self.v

    def summary(self):
        if self.initialized:
            return repr(self.str())
        return '???'

class char_t(_char_t):
    def set(self, value):
        self.value = value
        return self

    def get(self):
        return str(self.value)

uchar_t = char_t    # yeah, secretly there's no difference..

class wchar_t(_char_t):
    length = 2

    def set(self, value):
        self.value = value + '\x00'
        return self

    def get(self):
        return __builtins__['unicode'](self.value, 'utf-16').encode('utf-8')

class string(ptype.type):
    '''String of characters'''
    length = 0
    _object_ = pstr.char_t
    initialized = property(fget=lambda self: self.value is not None)    # bool

    def at(self, offset, **kwds):
        ofs = offset - self.getoffset()
        return self[ ofs / self._object_.length ]

    def blocksize(self):
        return self._object_.length * len(self)

    def __insert(self, index, string):
        l = self._object_.length
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset:]
    def __delete(self, index):
        l = self._object_.length
        offset = index * l
        self.value = self.value[:offset] + self.value[offset+l:]

    def __replace(self, index, string):
        l = self._object_.length
        offset = index * l
        self.value = self.value[:offset] + string[:l] + self.value[offset+l:]
    def __fetch(self, index):
        l = self._object_.length
        offset = index * l
        return self.value[offset:offset+l]
    def __len__(self):
        if not self.initialized:
            return int(self.length)
        return len(self.value) / self._object_.length

    def __delitem__(self, index):
        self.__delete(index)
    def __getitem__(self, index):
        offset = index * self._object_.length
        return self.newelement(self._object_, str(index), self.getoffset() + offset).alloc(offset=0,source=ptype.provider.string(self.serialize()[index]))
    def __setitem__(self, index, value):
        assert value.__class__ is self._object_
        self.__replace(index, value.serialize())
    def insert(self, index, object):
        assert object.__class__ is self._object_
        self.__insert(index, value.serialize())
    def append(self, object):
        assert object.__class__ is self._object_
        self.value += object.serialize()
    def extend(self, iterable):
        for x in iterable:
            self.append(x)
        return
    def __iter__(self):
        for x in self.value:
            yield x
        return

    def set(self, value):
        result = dyn.array(self._object_, len(self))()

        for element,character in zip(result.alloc(), value):
            element.set(character)
        self.value = result.serialize()
        return self

    def get(self):
        import warnings
        warnings.warn('%s.get() is deprecated in favor of %s.str()'%(self.__class__.__name__, self.__class__.__name__), DeprecationWarning, stacklevel=2)
        return self.str()

    def str(self):
        '''return type as a str'''
        s = self.value
        return utils.strdup(s)[:len(self)]

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            sz = self._object_.length
            self.source.seek(self.getoffset())
            block = self.source.consume( self.blocksize() )
            result = self.deserialize_block(block)
        return result

    def deserialize_block(self, block):
        if len(block) != self.blocksize():
            raise StopIteration("unable to continue reading (byte %d out of %d)"% (len(block), self.blocksize()))
        self.value = block
        return self

    def serialize(self):
        return str(self.value)

    def summary(self):
        if self.initialized:
            return repr(self.str())
        return '???'

class szstring(string):
    '''Standard null-terminated string'''
    _object_ = char_t
    length=None
    def isTerminator(self, v):
        return int(v) == 0

    def set(self, value):
        if not value.endswith('\x00'):
            value += '\x00'

        result = dyn.array(self._object_, len(value))().alloc()
        for element,character in zip(result, value):
            element.set(character)
        self.value = result.serialize()
        return self

    def deserialize_block(self, block):
        return self.deserialize_stream(iter(block))

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.source.seek(self.getoffset())
            producer = (self.source.consume(1) for x in utils.infiniterange(0))
            result = self.deserialize_stream(producer)
        return result

    def deserialize_stream(self, stream):
        o = self.getoffset()
        obj = self.newelement(self._object_, '', o)
        sz = obj.blocksize()

        getchar = lambda: ''.join([stream.next() for x in range(sz)])

        self.value = ''
        while True:
            char = getchar()

            obj.setoffset(o)
            obj.deserialize_block(char)
            self.value += obj.serialize()
            if self.isTerminator(obj):
                break
            o += sz
        return self

    def blocksize(self):
        return self.load().size()       # XXX: heh

class wstring(string):
    '''String of wide-characters'''
    _object_ = wchar_t
#    unicode = __builtins__['unicode']
    def str(self):
        s = __builtins__['unicode'](self.value, 'utf-16').encode('utf-8')
        return utils.strdup(s)[:len(self)]

class szwstring(szstring, wstring):
    '''Standard null-terminated string of wide-characters'''
    _object_ = wchar_t

    def set(self, value):
        if not value.endswith('\x00'):
            value += '\x00'

        result = dyn.array(self._object_, len(value))().alloc()
        for element,character in zip(result, value):
            element.set(character)
        self.value = result.serialize()
        return self

## aliases that should probably be improved
unicode=wstring
szunicode=szwstring

if __name__ == '__main__':
    import provider
    import pstr

    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)

            except Success:
                print '%s: Success'% name
                return True

            except Failure,e:
                pass

            print '%s: Failure'% name
            return False

        TestCaseList.append(harness)
        return fn

    @TestCase
    def Test1():
        x = pstr.char_t(source=provider.string('hello')).l
        if x.get() == 'h':
            raise Success

    @TestCase
    def Test2():
        x = pstr.wchar_t(source=provider.string('\x43\x00')).l
        if x.get() == '\x43':
            raise Success

    @TestCase
    def Test3():
        x = pstr.string()
        string = "helllo world ok, i'm hungry for some sushi\x00"
        x.length = len(string)/2
        x.source = provider.string(string)
        x.load()
        if x.str() == string[:len(string)/2]:
            raise Success

    @TestCase
    def Test4():
        x = pstr.wstring()
        oldstring = "ok, this is unicode"
        string = oldstring
        x.length = len(string)/2
        string = ''.join([c+'\x00' for c in string])
        x.source = provider.string(string)
        x.load()
        if x.str() == oldstring[:len(oldstring)/2]:
            raise Success

    @TestCase
    def Test5():
        string = 'null-terminated\x00ok'
        x = pstr.szstring(source=provider.string(string)).l
        if x.str() == 'null-terminated':
            raise Success

    @TestCase
    def Test6():
        import parray
        data = 'here\x00is\x00my\x00null-terminated\x00strings\x00eof\x00stop here okay plz'

        class stringarray(parray.terminated):
            _object_ = pstr.szstring

            def isTerminator(self, value):
                if value.str() == 'eof':
                    return True
                return False

        x = stringarray(source=provider.string(data)).l
        if x[3].str() == 'null-terminated':
            raise Success

    @TestCase
    def Test7():
        import pstruct,pint,pstr
        class IMAGE_IMPORT_HINT(pstruct.type):
            _fields_ = [
                ( pint.uint16_t, 'Hint' ),
                ( pstr.szstring, 'String' )
            ]

        x = IMAGE_IMPORT_HINT(source=provider.string('AAHello world this is a zero0-terminated string\x00this didnt work')).l

        if x['String'].str() == 'Hello world this is a zero0-terminated string':
            raise Success


    @TestCase
    def Test8():
        s = 'C\x00:\x00\\\x00P\x00y\x00t\x00h\x00o\x00n\x002\x006\x00\\\x00D\x00L\x00L\x00s\x00\\\x00_\x00c\x00t\x00y\x00p\x00e\x00s\x00.\x00p\x00y\x00d\x00\x00\x00'
        v = pstr.szwstring(source=provider.string(s)).l
        if v.str() == 'C:\Python26\DLLs\_ctypes.pyd':
            raise Success

    @TestCase
    def Test9():
        data = ' '.join(map(lambda x:x.strip(),'''
            00 57 00 65 00 6c 00 63 00 6f 00 6d 00 65 00 00
        '''.split('\n'))).strip()
        data = map(lambda x: chr(int(x,16)), data.split(' '))
        data = ''.join(data)

        import pstruct,pstr,provider,utils
        class wbechar_t(pstr.wchar_t):
            def set(self, value):
                self.value = '\x00' + value
                return self

            def get(self):
                return unicode(self.value, 'utf-16-be').encode('utf-8')

        class unicodestring(pstr.szwstring):
            _object_ = wbechar_t
            def str(self):
                s = __builtins__.unicode(self.value, 'utf-16-be').encode('utf-8')
                return utils.strdup(s)[:len(self)]

        class unicodespeech_packet(pstruct.type):
            _fields_ = [
                (unicodestring, 'msg'),
            ]

        a = unicodestring(source=provider.string(data)).l
        if a.l.str() == 'Welcome':
            raise Success
        raise Failure


if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
