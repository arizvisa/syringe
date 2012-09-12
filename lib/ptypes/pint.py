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
#    assert type(ptype) is type and issubclass(ptype, integer_t), 'type %s not of an integer_t'%ptype.__name__
    assert type(ptype) is type
    class newptype(ptype):
        byteorder = property(fget=lambda s:bigendian)
        def shortname(self):
            return 'bigendian(%s)'% self.__class__.__name__

        def bytenumber(self):
            return reduce(lambda x,y: x << 8 | ord(y), self.serialize(), 0)

        def set(self, integer):
            mask = (1<<self.blocksize()*8) - 1
            integer &= mask

            bc = bitmap.new(integer, self.blocksize() * 8)
            res = []
    
            while bc[1] > 0:
                bc,x = bitmap.consume(bc,8)
                res.append(x)

            res = res + [0]*(self.blocksize() - len(res))
            res = ''.join(map(chr, reversed(res)))
            self.value = res
            return self

    newptype.__name__ = ptype.__name__
    return newptype

def littleendian(ptype):
    '''Will convert an integer_t to littleendian form'''
#    assert type(ptype) is type and issubclass(ptype, integer_t), 'type %s not of an integer_t'%ptype.__name__
    assert type(ptype) is type
    class newptype(ptype):
        byteorder = property(fget=lambda s:littleendian)
        def shortname(self):
            return 'littleendian(%s)'% self.__class__.__name__

        def bytenumber(self):
            return reduce(lambda x,y: x << 8 | ord(y), reversed(self.serialize()), 0)

        def set(self, integer):
            mask = (1<<self.blocksize()*8) - 1
            integer &= mask

            bc = bitmap.new(integer, self.blocksize() * 8)
            res = []
    
            while bc[1] > 0:
                bc,x = bitmap.consume(bc,8)
                res.append(x)

            res = res + [0]*(self.blocksize() - len(res))
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

    def bytenumber(self):
        '''Convert integer type into a number'''
        raise NotImplementedError('Unknown integer conversion')

    def number(self):
        return self.bytenumber()

    def details(self):
        if self.initialized:
            res = int(self)
            if res >= 0:
                fmt = '0x%%0%dx (%%d)'% (int(self.length)*2)
            else:
                fmt = '-0x%%0%dx (-%%d)'% (int(self.length)*2)
                res = abs(res)
            return fmt% (res, res)
        return '???'

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
        signmask = 2**(8*self.blocksize()-1)
        num = self.bytenumber()
        res = num&(signmask-1)
        if num&signmask:
            return (signmask-res)*-1
        return res & (signmask-1)

    def set(self, integer):
        signmask = 2**(8*self.blocksize())
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
class sint8_t(int_t): length = 1
class sint16_t(int_t): length = 2
class sint32_t(int_t): length = 4
class sint64_t(int_t): length = 8

int8_t,int16_t,int32_t,int64_t = sint8_t,sint16_t,sint32_t,sint64_t

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

    def details(self):
        if self.initialized:
            res = int(self)
            try:
                value = self.lookupByValue(res)
            except KeyError:
                value = '0x%x'% res

            res = '(' + str(res) + ')'
            return ' '.join((value, res))
        return '???'

    def summary(self):
        return self.details()

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
    import ptype,parray
    import pstruct,parray,pint,provider

    import logging
    logging.root=logging.RootLogger(logging.DEBUG)

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

if __name__ == '__main__':
    from ptypes import *
    import provider,utils,struct
    string1 = '\x0a\xbc\xde\xf0'
    string2 = '\xf0\xde\xbc\x0a'

    @TestCase
    def Test1():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def Test2():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1)).l
        a.set(0x0abcdef0)
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def Test3():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def Test4():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        b.set(0x0abcdef0)

        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def Test5():
        pint.setbyteorder(pint.bigendian)
        a = pint.uint32_t(source=provider.string(string1)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print a, repr(a.serialize())

    @TestCase
    def Test6():
        pint.setbyteorder(pint.littleendian)
        a = pint.uint32_t(source=provider.string(string2)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string2:
            raise Success
        print a, repr(a.serialize())

    @TestCase
    def Test7():
        pint.setbyteorder(pint.littleendian)
        s = '\xff\xff\xff\xff'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def Test8():
        pint.setbyteorder(pint.littleendian)
        s = '\x00\x00\x00\x80'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def Test9():
        pint.setbyteorder(pint.littleendian)
        s = '\xff\xff\xff\x7f'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def Test10():
        pint.setbyteorder(pint.littleendian)
        s = '\x00\x00\x00\x00'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
