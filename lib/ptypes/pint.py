from . import ptype,bitmap,config,error

def setbyteorder(endianness):
    if endianness in (config.byteorder.bigendian,config.byteorder.littleendian):
        for k,v in globals().iteritems():
            if hasattr(v, '__bases__') and ptype.istype(v) and getattr(v, 'byteorder', config.defaults.integer.order) != endianness:
                d = dict(v.__dict__)
                d['byteorder'] = endianness
                globals()[k] = type(v.__name__, v.__bases__, d)     # re-instantiate types
            continue
        return
    elif getattr(endianness, '__name__', '').startswith('big'):
        return setbyteorder(config.byteorder.bigendian)
    elif getattr(endianness, '__name__', '').startswith('little'):
        return setbyteorder(config.byteorder.littleendian)
    raise ValueError("Unknown integer endianness %s"% repr(endianness))

def bigendian(ptype):
    '''Will convert an integer_t to bigendian form'''
    if type(ptype) is not type:
        raise error.TypeError(ptype, 'bigendian')
    class newptype(ptype):
        byteorder = config.byteorder.bigendian
        __doc__ = ptype.__doc__
    newptype.__name__ = ptype.__name__
    return newptype

def littleendian(ptype):
    '''Will convert an integer_t to littleendian form'''
    if type(ptype) is not type:
        raise error.TypeError(ptype, 'littleendian')
    class newptype(ptype):
        byteorder = config.byteorder.littleendian
        __doc__ = ptype.__doc__
    newptype.__name__ = ptype.__name__
    return newptype

class integer_t(ptype.type):
    '''Provides basic integer-like support'''
    byteorder = config.defaults.integer.order

    def int(self): return int(self.num())
    def long(self): return long(self.num())
    def __int__(self): return self.int()
    def __long__(self): return self.long()

    def number(self):
        return self.num()

    def classname(self):
        typename = self.typename()
        if self.byteorder is config.byteorder.bigendian:
            return 'bigendian(%s)'% typename
        elif self.byteorder is config.byteorder.littleendian:
            return 'littleendian(%s)'% typename
        else:
            raise error.SyntaxError(cls, 'integer_t.classname', message='Unknown integer endianness %s'% repr(self.byteorder))
        return typename

    def set(self, integer):
        if self.byteorder is config.byteorder.bigendian:
            transform = lambda x: reversed(x)
        elif self.byteorder is config.byteorder.littleendian:
            transform = lambda x: x
        else:
            raise error.SyntaxError(self, 'integer_t.set', message='Unknown integer endianness %s'% repr(self.byteorder))
    
        mask = (1<<self.blocksize()*8) - 1
        integer &= mask
        bc = bitmap.new(integer, self.blocksize() * 8)
        res = []
        while bc[1] > 0:
            bc,x = bitmap.consume(bc,8)
            res.append(x)
        res = res + [0]*(self.blocksize() - len(res))   # FIXME: use padding
        self.value = ''.join(transform([chr(x) for x in res]))
        return self

    def get(self):
        return self.num()

    def num(self):
        '''Convert integer type into a number'''
        if self.byteorder is config.byteorder.bigendian:
            return reduce(lambda x,y: x << 8 | ord(y), self.serialize(), 0)
        elif self.byteorder is config.byteorder.littleendian:
            return reduce(lambda x,y: x << 8 | ord(y), reversed(self.serialize()), 0)
        raise error.SyntaxError(self, 'integer_t.num', message='Unknown integer endianness %s'% repr(self.byteorder))

    def summary(self, **options):
        if self.initialized:
            res = self.num()
            if res >= 0:
                fmt = '0x%%0%dx (%%d)'% (int(self.length)*2)
            else:
                fmt = '-0x%%0%dx (-%%d)'% (int(self.length)*2)
                res = abs(res)
            return fmt% (res, res)
        return '???'

    def repr(self, **options):
        return self.summary(**options)

    def flip(self):
        '''Returns an integer with the endianness flipped'''
        if self.byteorder is config.byteorder.bigendian:
            return self.cast(littleendian(self.__class__))
        elif self.byteorder is config.byteorder.littleendian:
            return self.cast(bigendian(self.__class__))
        raise error.UserError(self, 'integer_t.flip', message='Unexpected byte order %s'% repr(self.byteorder))

class sint_t(integer_t):
    '''Provides signed integer support'''
    def num(self):
        signmask = int(2**(8*self.blocksize()-1))
        num = super([_ for _ in self.__class__.__mro__ if _.__name__ == 'sint_t'][0],self).num()
        res = num&(signmask-1)
        if num&signmask:
            return (signmask-res)*-1
        return res & (signmask-1)

    def set(self, integer):
        signmask = int(2**(8*self.blocksize()))
        res = integer & (signmask-1)
        if integer < 0:
            res |= signmask
        return super([_ for _ in self.__class__.__mro__ if _.__name__ == 'sint_t'][0], self).set(res)

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
    def byValue(cls, value):
        '''Lookup the string in an enumeration by it's first-defined value'''
        for k,v in cls._values_:
            if v == value:
                return k
        raise KeyError(value)

    @classmethod
    def byName(cls, name):
        '''Lookup the value in an enumeration by it's first-defined name'''
        for k,v in cls._values_:
            if k == name:
                return v
        raise KeyError(name)

    def __cmp__(self, value):
        '''Can compare an enumeration as it's string or integral representation'''
        try:
            if type(value) == str:
                return cmp(self.byValue(int(self)), value)

        except KeyError:
            pass

        return super([_ for _ in self.__class__.__mro__ if _.__name__ == 'integer_t'][0], self).__cmp__(value)

    def __getattr__(self, name):
        try:
            # if getattr fails, then assume the user wants the value of
            #     a particular enum value
            return self.byName(name)

        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'"% (self.classname(), name))

    def str(self):
        '''Return value as a string'''
        res = int(self)
        try:
            value = self.byValue(res) + '(0x%x)'% res
        except KeyError:
            value = '0x%x'% res
        return value

    def summary(self, **options):
        if self.initialized:
            res = int(self)
            try:
                value = self.byValue(res)
            except KeyError:
                value = '0x%x'% res

            res = '(' + str(res) + ')'
            return ' '.join((value, res))
        return '???'

    def repr(self, **options):
        return self.summary(**options)

    def __getitem__(self, name):
        return self.byName(name)

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

    import config,logging
    config.defaults.log.setLevel(logging.DEBUG)

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
    import ptypes
    from ptypes import *
    import provider,utils,struct
    string1 = '\x0a\xbc\xde\xf0'
    string2 = '\xf0\xde\xbc\x0a'

    @TestCase
    def test_int_bigendian_uint32_load():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1))
        a = a.l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def test_int_bigendian_uint32_set():
        a = pint.bigendian(pint.uint32_t)(source=provider.string(string1)).l
        a.set(0x0abcdef0)
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def test_int_littleendian_load():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def test_int_littleendian_set():
        b = pint.littleendian(pint.uint32_t)(source=provider.string(string2)).l
        b.set(0x0abcdef0)
        if b.int() == 0x0abcdef0 and b.serialize() == string2:
            raise Success
        print b, repr(b.serialize())

    @TestCase
    def test_int_revert_bigendian_uint32_load():
        pint.setbyteorder(config.byteorder.bigendian)
        a = pint.uint32_t(source=provider.string(string1)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string1:
            raise Success
        print a, repr(a.serialize())

    @TestCase
    def test_int_revert_littleendian_uint32_load():
        pint.setbyteorder(config.byteorder.littleendian)
        a = pint.uint32_t(source=provider.string(string2)).l
        if a.int() == 0x0abcdef0 and a.serialize() == string2:
            raise Success
        print a, repr(a.serialize())

    @TestCase
    def test_int_littleendian_int32_signed_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\xff\xff\xff\xff'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def test_int_littleendian_int32_unsigned_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\x00\x00\x00\x80'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def test_int_littleendian_int32_unsigned_highedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\xff\xff\xff\x7f'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

    @TestCase
    def test_int_littleendian_int32_unsigned_lowedge_load():
        pint.setbyteorder(config.byteorder.littleendian)
        s = '\x00\x00\x00\x00'
        a = pint.int32_t(source=provider.string(s)).l
        b, = struct.unpack('l',s)
        if a.int() == b and a.serialize() == s:
            raise Success
        print b,a, repr(a.serialize())

#    @TestCase
#    def Test11():
#        raise NotImplementedError

#       >>> y[3][2]['data']
#       Traceback (most recent call last):
#         File "<stdin>", line 1, in <module>
#         File "c:\Users\user\work\syringe\lib\ptypes\ptype.py", line 247, in __repr__
#           return self.repr()
#         File "c:\Users\user\work\syringe\lib\ptypes\ptype.py", line 498, in repr
#           return '[%x] %s %s %s'%( self.getoffset(), self.classname(), prop, self.details())
#         File "c:\Users\user\work\syringe\lib\ptypes\pint.py", line 205, in details
#           value = self.lookupByValue(res)
#         File "c:\Users\user\work\syringe\lib\ptypes\pint.py", line 158, in lookupByValue
#           for k,v in cls._values_:
#       ValueError: too many values to unpack
#       >>> y[3][2]['data']._values_
#       ['name', 'constant']


if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
