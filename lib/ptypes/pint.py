'''ptypes with a numerical sort of feel'''
import ptype,bitmap

def setbyteorder(endianness):
    for k,v in globals().items():
        if hasattr(v, '__bases__') and issubclass(v, integer_t) and v is not integer_t:
            globals()[k] = endianness(v)
        continue
    return

def bigendian(ptype):
    '''Will convert an integer_t to bigendian form'''
    assert type(ptype) is type and issubclass(ptype, integer_t)
    class newptype(ptype):
        byteorder = property(fget=lambda s:bigendian)
        def shortname(self):
            return 'bigendian(%s)'% self.__class__.__name__

        def number(self):
            return reduce(lambda x,y: x << 8 | ord(y), self.serialize(), 0)

        def set(self, integer):
            mask = (1<<self.size()*8) - 1
            integer &= mask

            bc = bitmap.new(integer, self.size() * 8)
            res = []
    
            while bc[1] > 0:
                bc,x = bitmap.consume(bc,8)
                res.append(x)

            res = res + [0]*(self.size() - len(res))
            res = ''.join(map(chr, reversed(res)))
            self.value = res
            return self

    newptype.__name__ = ptype.__name__
    return newptype

def littleendian(ptype):
    '''Will convert an integer_t to littleendian form'''
    assert type(ptype) is type and issubclass(ptype, integer_t)
    class newptype(ptype):
        byteorder = property(fget=lambda s:littleendian)
        def shortname(self):
            return 'littleendian(%s)'% self.__class__.__name__

        def number(self):
            return reduce(lambda x,y: x << 8 | ord(y), reversed(self.serialize()), 0)

        def set(self, integer):
            mask = (1<<self.size()*8) - 1
            integer &= mask

            bc = bitmap.new(integer, self.size() * 8)
            res = []
    
            while bc[1] > 0:
                bc,x = bitmap.consume(bc,8)
                res.append(x)

            res = res + [0]*(self.size() - len(res))
            res = ''.join(map(chr, res))
            self.value = res
            return self

    newptype.__name__ = ptype.__name__
    return newptype

class integer_t(ptype.type):
    '''Provides basic integer-like support'''

    def int(self): return int(self.number())
    def long(self): return long(self.number())
    def __int__(self): return self.int()
    def __long__(self): return self.long()

    def get(self):
        raise DeprecationWarning('.get has been replaced with .number')
        return int(self)

    def number(self):
        '''Convert integer type into a number'''
        raise NotImplementedError('Unknown integer conversion')

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if self.initialized:
            res = int(self)

            fmt = '0x%%0%dx (%%d)'% (int(self.length)*2)
            res = fmt% (res, res)
        else:
            res = '???'
        return ' '.join([ofs,self.name(), res])

    def flip(self):
        '''Returns an integer with the endianness flipped'''
        if self.byteorder is bigendian:
            return self.cast(littleendian(self.__class__))
        elif self.byteorder is littleendian:
            return self.cast(bigendian(self.__class__))
        assert False is True, 'Unexpected byte order'''

integer_t = bigendian(integer_t)

class sint_t(integer_t):
    '''Provides signed integer support'''
    def number(self):
        signmask = 1 << 8*self.size()
        res = super(sint_t, self).long()
        
        res = res & (signmask-1)
        return [res, res*-1][bool(res&signmask)]

    def set(self, integer):
        signmask = 1 << 8*self.size()
        res = integer & (signmask-1)
        if integer < 0:
            res |= signmask
        return super(sint_t, self).set(res)

class uint_t(integer_t): pass
class int_t(sint_t): pass

class uint8_t(uint_t): length = 1
class uint16_t(uint_t): length = 2
class uint32_t(uint_t): length = 4
class uint64_t(uint_t): length = 8
class int8_t(int_t): length = 1
class int16_t(int_t): length = 2
class int32_t(int_t): length = 4
class int64_t(int_t): length = 8

class enum(integer_t):
    '''
    An integer_t for managing constants used when you define your integer.
    i.e. class myinteger(pint.enum, pint.uint32_t): pass

    Settable properties:
        _values_:array( tuple( name, value ), ... )<w>
            This contains which enumerations are defined.
    '''
    _values_ = list( tuple(('name', 'constant')) )

    @classmethod
    def lookupByValue(cls, value):
        '''Lookup the string in an enumeration by it's first-defined value'''
        for k,v in cls._values_:
            if v == value:
                return k
        raise KeyError

    @classmethod
    def lookupByName(cls, name):
        '''Lookup the value in an enumeration by it's first-defined name'''
        for k,v in cls._values_:
            if k == name:
                return v
        raise KeyError

    def __cmp__(self, value):
        '''Can compare an enumeration as it's string or integral representation'''
        try:
            if type(value) == str:
                return cmp(self.lookupByValue(int(self)), value)

        except KeyError:
            pass

        return super(integer_t, self).__cmp__(value)

    def __getattr__(self, name):
        try:
            # if getattr fails, then assume the user wants the value of
            #     a particular enum value
            return self.lookupByName(name)

        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'"% (self.name(), name))
        raise Exception('wtf')

    def get(self):
        '''Return value as a string'''
        res = int(self)
        try:
            value = self.lookupByValue(res) + '(0x%x)'% res
        except KeyError:
            value = '0x%x'% res
        return value

    def __repr__(self):
        ofs = '[%x]'% self.getoffset()
        if self.initialized:
            res = int(self)
            try:
                value = self.lookupByValue(res)
            except KeyError:
                value = '0x%x'% res

            res = '(' + str(res) + ')'
            return ' '.join([repr(self.__class__), value, res])
        return ' '.join([ofs, repr(self.__class__), '???'])

    def __getitem__(self, name):
        return self.lookupByName(name)

    ## XXX: not sure what to name these 2 methods, but i've needed them on numerous occasions
    ##      for readability purposes
    @classmethod
    def names(cls):
        '''Return all the names that have been defined'''
        return [k for k,v in cls._values_]

    @classmethod
    def enumerations(cls):
        '''Return all values that have been defined in this'''
        return [v for k,v in cls._values_]

if __name__ == '__main__':
    import provider,utils

    string = '\x0a\xbc\xde\xf0'

    a = bigendian(uint32_t)(source=provider.string(string)).l
    print a, repr(a.serialize())
    a.set(0x0abcdef0)
    print a, repr(a.serialize())

    b = littleendian(uint32_t)(source=provider.string(string)).l
    print b, repr(b.serialize())
    b.set(0x0abcdef0)
    print b, repr(b.serialize())

