import struct

## XXX: not quite pTypes, but it'll have to do.
class pType(object):
    pass

class pBinary(pType):
    _fields_ = []
    value = ''

    def __getindex(self, key):
        index = 0
        for i,x in zip(range(len(self._fields_)), self._fields_):
            st,k = x
            if k == key:
                return i

        raise KeyError(key)

    def serialize(self):
        raise NotImplementedError

    def deserialize(self, iterable):
        iterable = iter(iterable)
        raise NotImplementedError

    def __getitem__(self, k):
        idx = self.__getindex(k)
        raise NotImplementedError

    def __setitem__(self, k, v):
        idx = self.__getindex(k)
        raise NotImplementedError

    def size(self):
        raise NotImplementedError
        
    def keys(self):
        raise NotImplementedError

    def values(self):
        raise NotImplementedError

class pArray(pType):
    length = 0
    object = None
    value = []

    def size(self):
        return struct.calcsize(self.object) * self.length

    def __len__(self):
        return self.length

    def deserialize(self, iterable):
        iterable = iter(iterable)
        objsize = struct.calcsize(self.object)

        res = []
        for x in range( self.size() ):
            val = [v for i,v in zip(range(objsize), iterable)]
            if len(val) == 0:
                break

            val, = struct.unpack(self.object, ''.join(val))
            res.append(val)

        self.value = res

    def serialize(self):
        return ''.join([ struct.pack(self.object, v) for v in self.value ])

    def __getitem__(self, k):
        return self.value[k]

    def __setitem__(self, k, v):
        self.value[k] = v

    def __repr__(self):
        return "[%s (%s[%d])]"% (self.__class__, self.object, self.length)

class pTerminatedArray(pArray):
    def isTerminator(self, value):
        raise NotImplementedError

    def deserialize(self, iterable):
        iterable = iter(iterable)

        value = []
        while True:
            val, = struct.unpack(self.object, iterable)
            if self.isTerminator(val):
                break

            value.append(val)

        self.length = length(value)
        self.value = value

class pNullTerminatedArray(pArray):
    isTerminator = lambda self,value: value.count('\x00') == len(value)

class pStruct(pType):
    _fields_ = [] 
    value = []

    def __getindex(self, key):
        index = 0
        for i,x in zip(range(len(self._fields_)), self._fields_):
            st,k = x
            if k == key:
                return i

        raise KeyError(key)

    def serialize(self):
        return ''.join([ struct.pack(st, v) for (st,k),v in zip(self._fields_, self.value)])

    def deserialize(self, iterable):
        iterable = iter(iterable)
        value = []
        for st,k in self._fields_:
            s = ''.join([x for i,x in zip(range(struct.calcsize(st)), iterable)])
            res = struct.unpack(st,s)
            if len(res) == 1:
                res, = res
            value.append(res)
        self.value = value

    def size(self):
        return reduce( lambda x,y:x+y, [struct.calcsize(st) for st,k in self._fields_] )
#        return struct.calcsize(''.join([st for st,k in self._fields_]))

    def keys(self):
        return [k for st,k in self._fields_]

    def values(self):
        return [self[k] for k in self.keys()]

    def __getitem__(self, key):
        idx = self.__getindex(key)
        return self.value[idx]

    def __setitem__(self, key, value):
        idx = self.__getindex(key)
        st,k = self._fields_[idx]

        # force-fit value into the specified fmt
        value, = struct.unpack(st, struct.pack(st, value))

        self.value[idx] = value

    def __repr__(self):
        res = []
        ofs = 0
        for st,k in self._fields_:
            size = struct.calcsize(st)

            blah = repr(self[k])
            if (type(self[k]) == int) or (type(self[k]) == long):
                fmt = "%%0%dx"% (size*2)
                hexnum = fmt% self[k]
                blah = "0x%s (%d)"% (hexnum, self[k])

            res.append("%x: <%s> %s"% (ofs, k, blah))
            ofs += size

        # indent res
        res = ['    %s'% x for x in res]

        return '<%s\n%s\n>'% (repr(self.__class__), '\n'.join(res))

if __name__ == '__main__':
    class test(pStruct):
        _fields_ = [
            ('<B', 'byte'),
            ('<H', 'short'),
            ('<L', 'long')
        ]

    v = test()
    res = "\x80\xcc\xcc\x0d\x0a\x0e\x0d"
    v.deserialize(res)

    ## test size
    assert v.size() == 7

    ## serialize/deserialize test
    assert v.serialize() == res

    ## fetches
    assert v['byte'] == 0x80
    assert v['short'] == 0xcccc
    assert v['long'] == 0x0d0e0a0d

    ## assign and verify
    v['byte'] = 0x41
    assert v['byte'] == 0x41

    v['short'] = 0x4242
    assert v['short'] == 0x4242

    v['long'] = 0x43434343
    assert v['long'] == 0x43434343

    ## is .serialize() returning what we expect?
    assert v.serialize() == '\x41\x42\x42\x43\x43\x43\x43'
