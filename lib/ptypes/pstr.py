import ptype,parray
import pint,pstr,dyn,utils

class _char_t(pint.integer_t):
    length = 1

class char_t(_char_t):
    def set(self, value):
        self.value = value
        return self

    def get(self):
        return str(self.value)

    def __repr__(self):
        return ' '.join([super(_char_t, self).__repr__(), ' ', repr(self.get())])

uchar_t = char_t    # yeah, secretly there's no difference..

class wchar_t(_char_t):
    length = 2

    def set(self, value):
        self.value = value + '\x00'
        return self

    def get(self):
        return unicode(self.value, 'utf-16').encode('utf-8')

    def __repr__(self):
        if self.initialized:
            return ' '.join([super(_char_t, self).__repr__(), ' ', repr(self.get())])
        return ' '.join([super(_char_t, self).__repr__(), ' ???'])

class string(ptype.type):
    '''String of characters'''
    length = 0
    _object_ = pstr.char_t
    initialized = property(fget=lambda self: self.value is not None)    # bool

    def at(self, offset):
        raise AttributeError    # we don't exist..

    def size(self):
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
        return self.newelement(self._object_, str(index), self.getoffset() + offset)
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
        result = dyn.array(self._object_, len(value))()
        result.alloc()
        for element,character in zip(result, value):
            element.set(character)
        self.value = result.serialize()
        return self

    def get(self):
        s = self.value
        return utils.strdup(s)[:len(self)]

    def load(self):
        sz = self._object_.length
        self.source.seek(self.getoffset())
        block = self.source.consume( self.blocksize() )
        return self.deserialize_block(block)

    def deserialize_block(self, block):
        if len(block) != self.blocksize():
            raise StopIteration("unable to continue reading (byte %d out of %d)"% (len(self.value), self.size()))
        self.value = block
        return self

    def serialize(self):
        return str(self.value)

    def setoffset(self, value, **kwds):
        return super(string, self).setoffset(value)

    def __repr__(self):
        if self.initialized:
            return ' '.join([self.name(), self.get()])
        return ' '.join([self.name()])

class szstring(string):
    '''Standard null-terminated string'''
    _object_ = char_t
    length=None
    def isTerminator(self, v):
        return int(v) == 0

    def set(self, value):
        o = self._object_().alloc().serialize()
        return super(szstring, self).set(value+'\x00')

    def deserialize_block(self, block):
        return self.deserialize_stream(iter(block))

    def load(self):
        sz = self._object_.length
        self.source.seek(self.getoffset())
        producer = (self.source.consume(sz) for x in utils.infiniterange(0))
        return self.deserialize_stream(producer)

    def deserialize_stream(self, stream):
        o = self.getoffset()
        obj = self.newelement(self._object_, '', o)

        self.value = ''
        for char in stream:
            self.value += char

            obj.setoffset(o)
            obj.deserialize_block(char)
            if self.isTerminator(obj):
                break
            o += len(char)
        return self

    def blocksize(self):
        return self.load().size()       # XXX: heh

class wstring(string):
    '''String of wide-characters'''
    _object_ = wchar_t
    def get(self):
        s = unicode(self.value, 'utf-16').encode('utf-8')
        return utils.strdup(s)[:len(self)]

class szwstring(szstring, wstring):
    '''Standard null-terminated string of wide-characters'''
    _object_ = wchar_t

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
        if x.get() == string[:len(string)/2]:
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
        if x.get() == oldstring[:len(oldstring)/2]:
            raise Success

    @TestCase
    def Test5():
        string = 'null-terminated\x00ok'
        x = pstr.szstring(source=provider.string(string)).l
        if x.get() == 'null-terminated':
            raise Success

    @TestCase
    def Test6():
        import parray
        data = 'here\x00is\x00my\x00null-terminated\x00strings\x00eof\x00stop here okay plz'

        class stringarray(parray.terminated):
            _object_ = pstr.szstring

            def isTerminator(self, value):
                if value.get() == 'eof':
                    return True
                return False

        x = stringarray(source=provider.string(data)).l
        if x[3].get() == 'null-terminated':
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

        if x['String'].get() == 'Hello world this is a zero0-terminated string':
            raise Success


    @TestCase
    def Test8():
        h = '43 00 3a 00 5c 00 50 00 79 00 74 00 68 00 6f 00 6e 00 32 00 36 00 5c 00 44 00 4c 00 4c 00 73 00 5c 00 5f 00 63 00 74 00 79 00 70 00 65 00 73 00 2e 00 70 00 79 00 64 00 00 00'
        h = h.split(' ')
        h = [int(x,16) for x in h]
        h = ''.join( [chr(x) for x in h] )

        s = 'C\x00:\x00\\\x00P\x00y\x00t\x00h\x00o\x00n\x002\x006\x00\\\x00D\x00L\x00L\x00s\x00\\\x00_\x00c\x00t\x00y\x00p\x00e\x00s\x00.\x00p\x00y\x00d\x00\x00\x00'
        v = pstr.szwstring(source=provider.string(s)).l
        if v.get() == 'C:\Python26\DLLs\_ctypes.pyd':
            raise Success

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
