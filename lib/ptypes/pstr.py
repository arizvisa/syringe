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

class string(ptype.type):     # XXX: this isn't right to be treated as a container
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
            element.set(ord(character))
        self.value = result.serialize()
        return self

    def get(self):
        s = self.value
        return utils.strdup(s)[:len(self)]

    def deserialize_stream(self, source):
        '''initializes self with input from from the specified iterator 'source\''''
        totallength = int(self.length)
        chunklength = self._object_.length
        assert chunklength > 0

        self.value = ''
        chunk = ''
        try:
            for i,byte in zip(xrange(totallength), source):
                chunk += byte
                if len(chunk) == chunklength:
                    self.value += chunk
                    chunk = ''
                continue

        except MemoryError:
            raise MemoryError('Out of memory trying to allocate %d bytes'% self.size())

        if len(self.value) != self.size():
            raise StopIteration("unable to continue reading (byte %d out of %d)"% (len(self.value), self.size()))
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
    def isTerminator(self, v):
        return int(v) == 0

    def load(self):
        self.source.seek(self.getoffset())
        producer = ( self.source.consume(1) for x in utils.infiniterange(0) )
        return self.deserialize_stream( producer )

    def deserialize_stream(self, stream):
        source = iter(stream)
        chunklength = self._object_.length
        o = self.getoffset()

        obj = self.newelement(self._object_, '', o)

        self.value = ''

        chunk = ''
        for byte in source:
            chunk += byte
            if len(chunk) < chunklength:
                continue

            self.value += chunk

            obj.setoffset(o)
            obj.deserialize(chunk)
            if self.isTerminator(obj):
                break
            o += len(chunk)
            chunk = ''
        return self

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

    if True:
        x = pstr.char_t()
        x.deserialize('hello')
        print x.get() == 'h'

    if True:
        x = pstr.wchar_t()
        x.deserialize('\x43\x00')
        print x.get() == '\x43'

    if True:
        x = pstr.string()
        string = "helllo world ok, i'm hungry for some sushi\x00"
        x.length = len(string)/2
        x.source = provider.string(string)
        x.load()
        print x.get() == string[:len(string)/2]

    if True:
        x = pstr.wstring()
        oldstring = "ok, this is unicode"
        string = oldstring
        x.length = len(string)
        string = ''.join([c+'\x00' for c in string])
        x.source = provider.string(string)
        x.load()
        print x.get() == oldstring[:len(oldstring)/2]

    if True:
        x = pstr.szstring()
        string = 'null-terminated\x00ok'
        x.deserialize(string)
        print x.get() == 'null-terminated'

    if True:
        import parray
        data = 'here\x00is\x00my\x00null-terminated\x00strings\x00eof\x00stop here okay plz'

        class stringarray(parray.terminated):
            _object_ = pstr.szstring

            def isTerminator(self, value):
                if value.get() == 'eof':
                    return True
                return False

        x = stringarray()
        x.deserialize(data)
        print x[3].get() == 'null-terminated'

    if True:
        import pstruct,pint,pstr
        class IMAGE_IMPORT_HINT(pstruct.type):
            _fields_ = [
                ( pint.uint16_t, 'Hint' ),
                ( pstr.szstring, 'String' )
            ]

        x = IMAGE_IMPORT_HINT()
        x.deserialize('AAHello world this is a zero0-terminated string\x00this didnt work')
        print x['String'].get() == 'Hello world this is a zero0-terminated string'

        source = provider.string( x.serialize() )

    import provider
    if True:
        x = IMAGE_IMPORT_HINT()
        x.source = source

    if False:
        x = pstr.szstring()
        x.source = source

        x.load()
        print x

    if False:
        h = '43 00 3a 00 5c 00 50 00 79 00 74 00 68 00 6f 00 6e 00 32 00 36 00 5c 00 44 00 4c 00 4c 00 73 00 5c 00 5f 00 63 00 74 00 79 00 70 00 65 00 73 00 2e 00 70 00 79 00 64 00 00 00'
        h = h.split(' ')
        h = [int(x,16) for x in h]
        h = ''.join( [chr(x) for x in h] )
        print repr(h)

    s = 'C\x00:\x00\\\x00P\x00y\x00t\x00h\x00o\x00n\x002\x006\x00\\\x00D\x00L\x00L\x00s\x00\\\x00_\x00c\x00t\x00y\x00p\x00e\x00s\x00.\x00p\x00y\x00d\x00\x00\x00'
    v = pstr.szwstring()
    v.deserialize(s)
    print v.get() == 'C:\Python26\DLLs\_ctypes.pyd'
