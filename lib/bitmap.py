#bitmap = (integer, bits)
import sys

## start somewhere
def new(value, size):
    '''creates a new bitmap object'''
    return (value & (2**size-1), size)

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
    count = 0
    while size > 0:
        if bool(integer & 1) == value:
            count += 1
        continue
    return count

def size(integer):
    '''returns the log(2) of the specified integer'''
    count = 0
    while integer >= 2:
        count += 1
        integer >>= 1
    return count + 1

def string(bitmap):
    '''returns bitmap as a formatted binary string'''
    integer, size = bitmap

    res = ''
    for position in range(size):
        res += ['0', '1'][integer & 1 != 0]
        integer >>= 1
    return res

def scan(bitmap, value=True, position=0):
    '''searches through bitmap for specified /value/ and returns it's position'''
    assert position >= 0

    integer, size = bitmap
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
    value = integer & 1
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
    mask = reduce(lambda r,v: 1<<v | r, range(position, position+count), 0)
    if value:
        return (integer | mask, size)
    return (integer & ~mask, size)

def get(bitmap, position, count):
    '''fetch /count/ number of bits from /bitmap/ starting at /position/'''
    integer, size = bitmap
    mask = reduce(lambda r,v: 1<<v | r, range(position, position+count), 0)
    return ((integer & mask) >> position, count)

def add(bitmap, integer):
    n,sz = bitmap
    mask = (1<<sz)-1
    return (integer+n) & mask,sz

def sub(bitmap, integer):
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n-integer) & mask,sz
def mul(bitmap, integer):
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n*integer) & mask,sz
def div(bitmap, integer):
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n/integer) & mask,sz
def mod(bitmap, integer):
    n,sz = bitmap
    mask = (1<<sz)-1
    return (n%integer) & mask,sz

def grow(bitmap, count):
    '''Grow bitmap by some specified number of bits'''
    assert count >= 0
    integer,size = bitmap
    return (integer << count, size + count)

def shrink(bitmap, count):
    '''Shrink a bitmap by some specified size'''
    assert count >= 0
    integer,size = bitmap
    return (integer >> count, size - count)

## for treating a bitmap like an integer stream
def push(bitmap, operand):
    '''Append bitmap data to the current bitmap'''
    (result, rbits) = bitmap
    (number, nbits) = operand
    rmask = 2**rbits - 1
    nmask = 2**nbits - 1

    res = result & rmask
    res <<= nbits
    res |= number & nmask
    return (res, nbits+rbits)

def insert(bitmap, operand):
    '''Insert bitmap data at the front of the bitmap'''
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
    assert bits >= 0
    bmask = 2**bits - 1
    res = bitmap[0] & bmask
    return ( (bitmap[0] >> bits, bitmap[1] - bits), res)

def shift(bitmap, bits):
    '''Shift some number of bits off of the beginning of a bitmap. Returns tuple(new bitmap, integer shifted off)'''
    # FIXME
    assert bits >= 0 and bitmap[1] >= bits
    shifty = bitmap[1] - bits
    bmask = 2**bits-1 << shifty
    res = (bitmap[0] & bmask) >> shifty
    return ((bitmap[0] & ~bmask, shifty), res)

class consumer(object):
    '''Given an iterable, provide an interface to supply bits'''
    def __init__(self, iterable):
        self.source = iter(iterable)
        self.cache = new(0, 0)

    def read(self, bytes):
        '''read specified number of bytes from iterable'''
        data = ''.join([self.source.next() for x in range(bytes)])
        data = reduce(lambda x,y: x*256+ord(y), data, 0)
        self.cache = push(self.cache, new(data, bytes*8))

    def consume(self, bits):
        if bits > self.cache[1]:
            count = bits - self.cache[1]
            self.read((count + 7) / 8)
            return self.consume(bits)

        self.cache,result = shift(self.cache, bits)
        return result

    def __repr__(self):
        return ' '.join([self.__class__.__repr__(), self.cache.__repr__(), string(self.cache)])

def repr(object):
    integer,size = object
    return "<type 'bitmap'> (0x%x, %d)"% (integer,size)

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

    x = consumer('\x12\x34')
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
