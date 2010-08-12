'''ptypes with a numerical sort of feel'''
import ptype,bitmap

def bigendian(ptype):
    '''Will convert an integer_t to bigendian form'''
    assert type(ptype) is type and issubclass(ptype, integer_t)
    class newptype(ptype):
        def __int__(self):  #XXX: should this be renamed to .get()?
            return reduce(lambda x,y: x << 8 | ord(y), self.serialize(), 0)

        def set(self, integer):
            mask = (1<<self.size()*8) - 1
            integer &= mask

            bc = bitmap.new(integer, self.size() * 8)
            res = []
    
            while bc[1] > 0:
                bc,x = bitmap.consume(8)
                res.append(x)

            res = res + [0]*(self.size() - len(res))
            res = ''.join(map(chr, reversed(res)))
            self.value = res
            return self

    newptype.__name__ = 'bigendian(%s)'% ptype.__name__
    return newptype

def littleendian(ptype):
    '''Will convert an integer_t to littleendian form'''
    assert type(ptype) is type and issubclass(ptype, integer_t)
    class newptype(ptype):
        def __int__(self):
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

    newptype.__name__ = 'littleendian(%s)'% ptype.__name__
    return newptype

class integer_t(ptype.type):
    '''Provides basic integer-like support'''
    def get(self):
        return int(self)

    def __repr__(self):
        if self.initialized:
            res = int(self)

            fmt = '0x%%0%dx (%%d)'% (self.length*2)
            res = fmt% (res, res)
        else:
            res = '???'
        return ' '.join([self.name(), res])

integer_t = littleendian(integer_t)

class sint_t(integer_t):
    '''Provides signed integer support'''
    def __int__(self):
        signmask = 1 << 8*self.size()
        res = super(sint_t, self).__int__()
        
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
    An integer_t for managing tagged

    Settable properties:
        _fields_:array( tuple( name, value ), ... )<w>
            This contains which enumerations are defined.
    '''
    _fields_ = list( tuple(('name', 'constant')) )

    @classmethod
    def lookupByValue(cls, value):
        for k,v in cls._fields_:
            if v == value:
                return k
        raise KeyError

    @classmethod
    def lookupByName(cls, name):
        for k,v in cls._fields_:
            if k == name:
                return v
        raise KeyError

    def __cmp__(self, value):
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

    def __str__(self):
        return self.get()

    def get(self):
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
        return ' '.join([repr(self.__class__), '???'])

    def __getitem__(self, name):
        return self.lookupByName(name)

    ## XXX: not sure what to name these 2 methods, but i've needed them on numerous occasions
    ##      for readability purposes
    @classmethod
    def names(cls):
        '''Return all the names that have been defined'''
        return [k for k,v in cls._fields_]

    @classmethod
    def enumerations(cls):
        '''Return all values that have been defined in this'''
        return [v for k,v in cls._fields_]

if __name__ == '__main__':
    import utils

    string = '\x0a\xbc\xde\xf0'

    v = bigendian(uint32_t)()
    v.deserialize(string)
    print v, repr(v.serialize())
    v.set(0x0abcdef0)
    print v, repr(v.serialize())

    v = littleendian(uint32_t)()
    v.deserialize(string)
    print v, repr(v.serialize())
    v.set(0x0abcdef0)
    print v, repr(v.serialize())

