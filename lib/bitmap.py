#bitmap = (integer, bits)
import sys

## start somewhere
def new(value, size):
    '''creates a new bitmap object. Bitmaps "grow" to the left.'''
    return (value & (2**abs(size)-1), size)

zero = new(0,0)

def isinteger(v):
    '''returns true if provided variable is of type int or long'''
    return isinstance(v, (int, long))

def isbitmap(v):
    '''returns true if provided variable is a valid bitmap type (i really shouldn't be keeping track of these)'''
    return v.__class__ is tuple and len(v) == 2  # and isinteger(v[0]) and isinteger(v[1])

def empty(bitmap):
    '''returns true if specified bitmap has none of its bits set'''
    integer,size = bitmap
    return not(integer > 0)

## for treating a bitmap as an array of bits
def count(bitmap, value=False):
    '''returns the number of bits that are set to value and returns the count'''
    integer,size = bitmap
    count,size = 0,abs(size)
    while size > 0:
        if bool(integer & 1) == value:
            count += 1
        continue
    return count

import math # glad this is a builtin
def fit(integer):
    '''returns the number of bits necessary to contain integer. or log(2)'''
    return int(math.log(integer,2))+1

    count = 0
    while integer >= 2:
        count += 1
        integer >>= 1
    return count + 1

def string(bitmap):
    '''returns bitmap as a formatted binary string'''
    integer, size = bitmap
    size = abs(size)
    res = []
    for position in range(size):
        res.append(['0', '1'][integer & 1 != 0])
        integer >>= 1
    return ''.join(reversed(res))

def hex(bitmap):
    '''return bitmap as a hex string'''
    v,s = bitmap
    return ('%%0%dx'% (s/4))%v

def scan(bitmap, value=True, position=0):
    '''searches through bitmap for specified /value/ and returns it's position'''
    assert position >= 0

    integer, size = bitmap
    size = abs(size)

    bitmask = 1 << position
    for i in range(size):
        if bool(integer & bitmask) == value:
            return position
        bitmask <<= 1
        position += 1
    return position

def runscan(bitmap, value, length, position=0):
    '''will return the position of a run fulfilling the paramters in /bitmap/'''

    if length >= 0 and position >= 0:
        for run_integer,run_length in run(bitmap, position=position):
            # snag a run that best fits user's reqs
            if bool(run_integer&1) == value and length <= run_length:
                return position
            position += run_length
    raise ValueError('Unable to find a %d bit run of %d in bitmap'% (length, value))

def runlength(bitmap, value, position=0):
    '''returns the count of bits, starting at /position/'''
    assert position >= 0
    return scan(bitmap, not value, position) - position

def run(bitmap, position=0):
    '''iterates through all the runs in a given bitmap'''
    assert position >= 0

    integer, size = bitmap
    value,size = integer & 1, abs(size)
    while size > 0:
        length = runlength( (integer,size), value, position)
        yield get(bitmap, position, length)
        size -= length
        position += length
        value = not value

def set(bitmap, position, value=True, count=1):
    '''store /value/ into /bitmap/ starting at /position/'''
    assert count >= 0 and position >= 0

    integer, size = bitmap
    mask,size = reduce(lambda r,v: 1<<v | r, range(position, position+count), 0), abs(size)
    if value:
        return (integer | mask, size)
    return (integer & ~mask, size)

def get(bitmap, position, count):
    '''fetch /count/ number of bits from /bitmap/ starting at /position/'''
    integer, size = bitmap
    mask,size = reduce(lambda r,v: 1<<v | r, range(position, position+count), 0), abs(size)
    return ((integer & mask) >> position, count)

def add(bitmap, integer):
    # FIXME: signedness
    n,sz = bitmap
    mask = (1<<sz)-1
    return (integer+n) & mask,sz

def sub(bitmap, integer):
    # FIXME: signedness
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n-integer) & mask,sz
def mul(bitmap, integer):
    # FIXME: signedness
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n*integer) & mask,sz
def div(bitmap, integer):
    # FIXME: signedness
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n/integer) & mask,sz
def mod(bitmap, integer):
    # FIXME: signedness
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n%integer) & mask,sz

def grow(bitmap, count):
    '''Grow bitmap by some specified number of bits'''
    # FIXME: signedness
    assert count >= 0
    integer,size = bitmap
    return (integer << count, size + (count*(1,-1)[size<0]))

def shrink(bitmap, count):
    '''Shrink a bitmap by some specified size'''
    # FIXME: signedness
    assert count >= 0
    integer,size = bitmap
    return (integer >> count, size - (count*(-1,1)[size<0]))

## for treating a bitmap like an integer stream
def push(bitmap, operand):
    '''Append bitmap data to the end of the current bitmap'''
    # FIXME: signedness
    (result, rbits) = bitmap
    (number, nbits) = operand
    rmask = 2**rbits - 1
    nmask = 2**nbits - 1

    res = result & rmask
    res <<= nbits
    res |= number & nmask
    return (res, nbits+rbits)

def insert(bitmap, operand):
    '''Insert bitmap data at the beginning of the bitmap'''
    # FIXME: signedness
    (result, rbits) = bitmap
    (number, nbits) = operand
    rmask = 2**rbits - 1
    nmask = 2**nbits - 1

    res = number & nmask
    res <<= rbits
    res |= result & rmask
    return (res, nbits+rbits)

def consume(bitmap, bits):
    '''Consume some number of bits off of the end of a bitmap. Returns tuple(new bitmap, integer consumed)'''
    # FIXME: signedness
    assert bits >= 0
    bmask = 2**bits - 1
    integer,size = bitmap
    res = integer & bmask
    if size < 0:
        return ( (integer >> bits, size + bits), res)
    return ( (integer >> bits, size - bits), res)

def shift(bitmap, bits):
    '''Shift some number of bits off of the beginning of a bitmap. Returns tuple(new bitmap, integer shifted off)'''
    # FIXME: signedness
    assert bits >= 0
    bmask = 2**bits - 1
    integer,size = bitmap
    total = abs(size)
    if bits > total:
        return shift(bitmap, total)

    shifty = total - bits
    bmask = (2**bits-1) << shifty
    res = (integer & bmask) >> shifty
    if size < 0:
        return ((integer & ~bmask, shifty), res*-1)
    return ((integer & ~bmask, shifty), res)

class consumer(object):
    '''Given an iterable of an ascii string, provide an interface that supplies bits'''
    def __init__(self, iterable=()):
        self.source = iter(iterable)
        self.cache = new(0, 0)

    def push(self, bitmap):
        self.cache = push(self.cache, bitmap)
        return self

    def insert(self, bitmap):
        self.cache = insert(self.cache, bitmap)
        return self

    def push(self, bitmap):
        self.cache = push(self.cache, bitmap)
        return self

    def read(self, bytes):
        '''read specified number of bytes from iterable'''
        assert bytes > 0
        result,count = 0,0
        while bytes > 0:
            result *= 256
            result += ord(self.source.next())
            bytes,count = bytes-1,count+1
        self.cache = push(self.cache, new(result, count*8))
        return count

    def consume(self, bits):
        '''returns some number of bits as an integer'''
        if bits > self.cache[1]:
            count = bits - self.cache[1]
            bs = (count+7)/8
            self.read(bs)
            return self.consume(bits)
        self.cache,result = shift(self.cache, bits)
        return result

    def __repr__(self):
        return ' '.join([str(self.__class__), self.cache.__repr__(), string(self.cache)])

def repr(object):
    integer,size = object
    return "<type 'bitmap'> (0x%x, %d)"% (integer,size)

def data(bitmap, reversed=False):
    '''Convert a bitmap to a string left-aligned to 8-bits'''
    fn = consume if reversed else shift
    integer,size = bitmap

    # FIXME: signedness

    l = size % 8
    if l > 0:
        bitmap = insert(bitmap,(0,8-l)) if reversed else push(bitmap,(0,8-l))

    res = []
    while bitmap[1] != 0:
        bitmap,b = fn(bitmap, 8)
        res.append(b)
    return ''.join(map(chr,res))

def signed(bitmap):
    '''returns true if bitmap is signed'''
    integer,size = bitmap
    return size < 0

def number(bitmap):
    '''return the integral part of a bitmap, handling signedness if necessary'''
    v,s = bitmap
    if s < 0:
        signmask = 2**(abs(s)-1)
        res = v & (signmask-1)
        if v&signmask:
            return (signmask-res)*-1
        return res & (signmask-1)
    return v

def size(bitmap):
    '''return the size of the bitmap'''
    v,s = bitmap
    return abs(s)

def splitter(bitmap, maxsize):
    '''split bitmap into multiple of maxsize bits'''

    # FIXME: signedness

    sf,maxsize = -1 if maxsize < 0 else +1, abs(maxsize)
    while True:
        v,s = bitmap
        if s < maxsize:
            break
        bitmap,v = shift(bitmap,maxsize)
        yield (v,maxsize*sf)

    if s > 0:
        yield (v,s*sf)
    return

def split(bitmap, maxsize):
    '''return bitmap divided into a list of maxsize bits'''
    return [x for x in splitter(bitmap,maxsize)]

def join(iterable):
    '''join a list of bitmaps into a single one'''
    return reduce(lambda x,y: push(x, y), iterable, (0,0))

import itertools
def groupby(sequence, count):
    '''group sequence by number of elements'''
    data = enumerate(sequence)
    key = lambda (index,value): index/count
    for _,res in itertools.groupby(data, key):
        yield [v for _,v in res]
    return

# jspelman. he's everywhere.
ror = lambda (value, bits), shift=1,: (((value & (2**shift-1)) << bits-shift) | (value >> shift), bits)
rol = lambda (value, bits), shift=1,: ( (value << shift) | ((value & ((2**bits-1) ^ (2**(bits-shift)-1))) >> (bits-shift)), bits)

if False:
    # are bits clear
    # are bits set
    # check bit
    # clear all bits
    # clear bits
    # find clear bits
    # find clear bits and set
    # find clear runs
    # find first run clear
    # find last backward run clear
    # find longest run clear
    # find next forward run clear
    # find set bits
    # find set bits and clear
    # number of clear bits, number of set bits
    # set all bits, set bits
    pass

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
    import bitmap; reload(bitmap)

    x = bitmap.new(0xf000000000000000,64)
    #x = bitmap.set(x, 60, count=4)
    print bitmap.string(x)

    y,res = bitmap.shift(x, 4)
    print res,bitmap.string(y)

    x = bitmap.new(0,0)
    x = bitmap.push(x, (0x1,4) )
    x = bitmap.push(x, (0x2,4) )
    x = bitmap.push(x, (0x3,4) )
    x = bitmap.push(x, (0x4,4) )
    print x,bitmap.string(x)

    x = bitmap.new(0,0)
    x = bitmap.insert(x, (0x1,4) )
    x = bitmap.insert(x, (0x2,4) )
    x = bitmap.insert(x, (0x3,4) )
    x = bitmap.insert(x, (0x4,4) )
    print x,bitmap.string(x)

    x = bitmap.consumer('\x12\x34')
    print x.consume(4)
    print x.consume(4)
    print x.consume(4)
    print x.consume(4)

    x = bitmap.new(0, 4)
    for i in range(6):
        print x
        x = bitmap.add(x, 3)

    for i in range(6):
        print x
        x = bitmap.sub(x, 6)

    x = bitmap.new(4,4)
    print bitmap.string(bitmap.ror(bitmap.ror(bitmap.ror(x))))

if __name__ == '__main__':
    import bitmap
    result = bitmap.new(0, -32)
    freeslot = 0
    count = 3
    result = bitmap.set(result, freeslot, 1, count)
    print bitmap.string(result)

if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
