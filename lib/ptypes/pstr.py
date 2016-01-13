import __builtin__,itertools
from . import ptype,parray,pint,dynamic,utils,error,pstruct,provider,config
Config = config.defaults

class _char_t(pint.integer_t):
    length = 1
    def str(self):
        return self.v

    def summary(self, **options):
        return repr(self.str())

    @classmethod
    def typename(cls):
        return cls.__name__

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
        return __builtin__.unicode(self.value, 'utf-16').encode('utf-8')

class string(ptype.type):
    '''String of characters'''
    length = 0
    _object_ = char_t
    initializedQ = lambda self: self.value is not None    # bool

    def at(self, offset, **kwds):
        ofs = offset - self.getoffset()
        return self[ ofs / self._object_.length ]

    def blocksize(self):
        return self._object_.length * self.length

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
        if index.__class__ is slice:
            raise error.ImplementationError(self, 'string.__delitem__', message='slice support not implemented')
        self.__delete(index)
    def __getitem__(self, index):
        if index.__class__ is slice:
            result = [self[_] for _ in xrange(*index.indices(len(self)))]

            # ..and now it's an array
            type = ptype.clone(parray.type, typename=lambda s:self.typename(), length=len(result), _object_=self._object_)
            return self.new(type, offset=result[0].getoffset(), value=result)

        if index < -len(self) or index >= len(self):
            raise error.UserError(self, 'string.__getitem__', message='list index %d out of range'% index)

        index %= len(self)
        res = self.new(self._object_, __name__=str(index))
        ofs = index*res.blocksize()
        res.setoffset(self.getoffset()+ofs)
        return res.load(offset=ofs,source=provider.string(self.serialize()))

    def __setitem__(self, index, value):
        if index.__class__ is slice:
            raise error.ImplementationError(self, 'string.__setitem__', message='slice support not implemented')
        if value.__class__ is not self._object_:
            raise error.TypeError(self, 'string.__setitem__', message='expected value of type %s. received %s'% (repr(self._object_),repr(value.__class__)))
        self.__replace(index, value.serialize())
    def insert(self, index, object):
        if object.__class__ is not self._object_:
            raise error.TypeError(self, 'string.insert', message='expected value of type %s. received %s'% (repr(self._object_),repr(object.__class__)))
        self.__insert(index, value.serialize())
    def append(self, object):
        if object.__class__ is not self._object_:
            raise error.TypeError(self, 'string.append', message='expected value of type %s. received %s'% (repr(self._object_),repr(object.__class__)))
        self.value += object.serialize()
    def extend(self, iterable):
        for x in iterable:
            self.append(x)
        return

    def set(self, value):
        chararray = [x for x in value]
        _ = dynamic.array(self._object_, len(chararray))
        result = _()

        for character,element in zip(value,result.alloc()):
            element.set(character)
        self.length = len(result)
        self.value = result.serialize()
        return self

    def get(self):
        return self.serialize()

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
            raise error.LoadError(self, len(block))
        self.value = block
        return self

    def serialize(self):
        if self.initializedQ():
            return str(self.value)
        raise error.InitializationError(self, 'string.serialize')

    def summary(self, **options):
        try:
            result = repr(self.str())
        except UnicodeDecodeError:
            Config.log.debug('%s.summary : %s : Unable to decode unicode string. Rendering as hexdump instead.'% (self.classname(),self.instance()))
            return super(string,self).summary(**options)
        return result

    def repr(self, **options):
        return self.details(**options)

class szstring(string):
    '''Standard null-terminated string'''
    _object_ = char_t
    length = None
    def isTerminator(self, value):
        return value.num() == 0

    def set(self, value):
        if not value.endswith('\x00'):
            value += '\x00'

        result = dynamic.array(self._object_, len(value))().alloc()
        for element,character in zip(result, value):
            element.set(character)
        self.value = result.serialize()
        return self

    def deserialize_block(self, block):
        return self.deserialize_stream(iter(block))

    def load(self, **attrs):
        with utils.assign(self, **attrs):
            self.source.seek(self.getoffset())
            producer = (self.source.consume(1) for _ in itertools.count())
            result = self.deserialize_stream(producer)
        return result

    def deserialize_stream(self, stream):
        ofs = self.getoffset()
        obj = self.new(self._object_, offset=ofs)
        size = obj.blocksize()

        getchar = lambda: ''.join([stream.next() for _ in range(size)])

        self.value = ''
        while True:
            char = getchar()
            obj.setoffset(ofs)
            obj.deserialize_block(char)
            self.value += obj.serialize()
            if self.isTerminator(obj):
                break
            ofs += size
        return self

    def blocksize(self):
        return self.load().size()

class wstring(string):
    '''String of wide-characters'''
    _object_ = wchar_t
    def str(self):
        data = __builtin__.unicode(self.value, 'utf-16').encode('utf-8')
        return utils.strdup(data)

class szwstring(szstring, wstring):
    '''Standard null-terminated string of wide-characters'''
    _object_ = wchar_t

    def set(self, value):
        if not value.endswith('\x00'):
            value += '\x00'

        result = dynamic.array(self._object_, len(value))().alloc()
        for characeter,element in zip(value, result):
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
                raise Failure
            except Success,e:
                print '%s: %r'% (name,e)
                return True
            except Failure,e:
                print '%s: %r'% (name,e)
            except Exception,e:
                print '%s: %r : %r'% (name,Failure(), e)
            return False
        TestCaseList.append(harness)
        return fn

    @TestCase
    def test_str_char():
        x = pstr.char_t(source=provider.string('hello')).l
        if x.get() == 'h':
            raise Success

    @TestCase
    def test_str_wchar():
        x = pstr.wchar_t(source=provider.string('\x43\x00')).l
        if x.get() == '\x43':
            raise Success

    @TestCase
    def test_str_string():
        x = pstr.string()
        string = "helllo world ok, i'm hungry for some sushi\x00"
        x.length = len(string)/2
        x.source = provider.string(string)
        x.load()
        if x.str() == string[:len(string)/2]:
            raise Success

    @TestCase
    def test_str_wstring():
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
    def test_str_szstring():
        string = 'null-terminated\x00ok'
        x = pstr.szstring(source=provider.string(string)).l
        if x.str() == 'null-terminated':
            raise Success

    @TestCase
    def test_str_array_szstring():
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
    def test_str_struct_szstring():
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
    def test_str_szwstring():
        s = 'C\x00:\x00\\\x00P\x00y\x00t\x00h\x00o\x00n\x002\x006\x00\\\x00D\x00L\x00L\x00s\x00\\\x00_\x00c\x00t\x00y\x00p\x00e\x00s\x00.\x00p\x00y\x00d\x00\x00\x00'
        v = pstr.szwstring(source=provider.string(s)).l
        if v.str() == 'C:\Python26\DLLs\_ctypes.pyd':
            raise Success

    @TestCase
    def test_str_szwstring_customchar():
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
                s = __builtin__.unicode(self.value, 'utf-16-be').encode('utf-8')
                return utils.strdup(s)[:len(self)]

        class unicodespeech_packet(pstruct.type):
            _fields_ = [
                (unicodestring, 'msg'),
            ]

        a = unicodestring(source=provider.string(data)).l
        if a.l.str() == 'Welcome':
            raise Success
        raise Failure

    @TestCase
    def test_str_szstring_customterm():
        class fuq(pstr.szstring):
            def isTerminator(self, value):
                return value.num() == 0x3f

        s = provider.string('hello world\x3f..................')
        a = fuq(source=s)
        a = a.l
        if a.size() == 12:
            raise Success

    @TestCase
    def test_wstr_struct():
        import ptypes
        from ptypes import pint,dyn,pstr
        class record0085(pstruct.type):
            _fields_ = [
                (pint.uint16_t, 'unknown'),
                (pint.uint32_t, 'skipped'),
                (pint.uint16_t, 'sheetname_length'),
                (lambda s: dyn.clone(pstr.wstring, length=s['sheetname_length'].li.num()), 'sheetname'),
            ]
        s = ptypes.prov.string('85001400e511000000000600530068006500650074003100'.decode('hex')[4:])
        a = record0085(source=s)
        a=a.l
        if a['sheetname'].str() == 'Sheet1':
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
