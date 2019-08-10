#bitmap = (integer, bits)
import six, math
import functools, operator, itertools, types
from six.moves import builtins

## start somewhere
def new(value, size):
    '''creates a new bitmap object. Bitmaps "grow" to the left.'''
    mask = (2 ** abs(size)) - 1
    if size < 0:
        #signmask = 2 ** (abs(size)-1)
        return value & mask, size
    return value & mask, size

zero = new(0, 0)

def isinteger(v):
    '''Returns true if provided variable is of type int or long'''
    return builtins.isinstance(v, six.integer_types)
integerQ = isinteger

def isinstance(v):
    '''Returns true if provided variable is a valid bitmap type'''

    # We really shouldn't be manually keeping track of types like this...
    return builtins.isinstance(v, tuple) and len(v) == 2 and all((builtins.isinstance(v[0], six.integer_types), builtins.isinstance(v[1], six.integer_types)))
bitmapQ = isinstance

def isempty(bitmap):
    '''Returns true if specified bitmap has none of its bits set'''
    integer, size = bitmap
    return not(integer > 0)
emptyQ = isempty

def fit(integer):
    '''Returns the number of bits necessary to contain integer'''
    return 1 + math.trunc(math.log(abs(integer), 2)) + (1 if integer < 0 else 0)

def string(bitmap, **kwargs):
    '''Returns bitmap as a formatted binary string starting with the least-significant-bits first'''
    reverse = builtins.next((kwargs[k] for k in ('reverse', 'reversed') if k in kwargs), False)
    integer, size = bitmap
    res = "{:0{:d}b}".format(integer, abs(size))
    return str().join(reversed(res) if reverse else res)

def hex(bitmap):
    '''Return bitmap as a hex string'''
    n, s = bitmap
    size = abs(s)
    length = math.trunc(math.ceil(size / 4.0))
    if s < 0:
        max, sign = 2 ** size, 2 ** (size - 1)
        res = n & (max - 1)
        return "{:+#0{:d}x}".format((res - max) if res & sign else res & (sign - 1), length + 3)
    return "{:#0{:d}x}".format(n & (2 ** size) - 1, length + 2)

def scan(bitmap, value=True, position=0):
    '''Searches through bitmap for the specified value and returns it's position'''
    integer, size = bitmap

    if position < 0 or position > abs(size):
        raise AssertionError("Invalid position : {:d}".format(position))

    size, bitmask = abs(size), 2 ** position
    for i in six.moves.range(size):
        if bool(integer & bitmask) == value or position >= size:
            return position
        bitmask *= 2
        position += 1
    return position

def runscan(bitmap, value, length, position=0):
    '''Will return the position of a run fulfilling the parameters in bitmap'''

    if length >= 0 and position >= 0:
        for run_integer, run_length in run(bitmap, position=position):
            # snag a run that best fits user's reqs
            if bool(run_integer & 1) == bool(value) and length <= run_length:
                return position
            position += run_length
    raise ValueError("Unable to find a {:s} bit run of {:d} in bitmap".format(length, value))

def runlength(bitmap, value, position=0):
    '''Returns the count of bits, starting at position'''
    integer, size = bitmap
    if position < 0 or position > abs(size):
        raise AssertionError("Invalid position : {:d}".format(position))
    return scan(bitmap, not value, position) - position

def run(bitmap, position=0):
    '''Iterates through all the runs in a given bitmap'''
    integer, size = bitmap
    if position < 0 or position > abs(size):
        raise AssertionError("Invalid position : {:d}".format(position))

    value, size = integer & 1, abs(size)
    while size > 0:
        length = runlength( (integer, size), value, position)
        yield get(bitmap, position, length)
        size -= length
        position += length
        value = not value
    return

def set(bitmap, position, value=True, count=1):
    '''Store value into bitmap starting at position'''
    integer, size = bitmap

    if count < 0 or position < 0:
        raise AssertionError("Invalid count or position : {:d} : {:d}".format(count, position))
    if position + count > abs(size):
        raise AssertionError("Attempted to set bits outside bitmap : {:d} + {:d} > {:d}".format(position, count, size))

    mask, size = six.moves.reduce(lambda r, v: 2 ** v | r, six.moves.range(position, position + count), 0), abs(size)
    if value:
        return integer | mask, size
    return integer & ~mask, size

def get(bitmap, position, count):
    '''Fetch count number of bits from bitmap starting at position'''
    integer, size = bitmap

    if count < 0 or position < 0:
        raise AssertionError("Invalid count or position : {:d} : {:d}".format(count, position))
    if position + count > abs(size):
        raise AssertionError("Attempted to fetch bits outside bitmap : {:d} + {:d} > {:d}".format(position, count, size))

    mask, size = six.moves.reduce(lambda r, v: 2 ** v | r, six.moves.range(position, position + count), 0), abs(size)
    return (integer & mask) >> position, count

def add(bitmap, integer):
    '''Adds an integer to the specified bitmap whilst preserving signedness'''
    res, size = bitmap
    if size < 0:
        pass        # XXX: we trust that python handles signedness properly via &
    mask = 2 ** abs(size) - 1
    return (integer + res) & mask, size
def sub(bitmap, integer):
    '''Subtracts an integer to the specified bitmap whilst preserving signedness'''
    res, size = bitmap
    if size < 0:
        pass        # XXX: we trust that python handles signedness properly via &
    mask = 2 ** abs(size) - 1
    return (res - integer) & mask, size

def mul(bitmap, integer):
    '''Multiplies the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = 2 ** abs(size)
    if size < 0:
        sign = 2 ** (abs(size) - 1)
        res = (res - max) if res & sign else res & (sign - 1)
    return (res * integer) & (max - 1), size
def div(bitmap, integer):
    '''Divides the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = 2 ** abs(size)
    if size < 0:
        sign = 2 ** (abs(size) - 1)
        res = (res - max) if res & sign else res & (sign - 1)
    return math.trunc(float(res) / integer) & (max - 1), size
def mod(bitmap, integer):
    '''Modular divides the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = 2 ** abs(size)
    if size < 0:
        sign = 2 ** (abs(size) - 1)
        res = (res - max) if res & sign else res & (sign - 1)
    return (res % integer) & (max - 1), size

def grow(bitmap, count):
    '''Grow bitmap by some specified number of bits

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    if count < 0:
        return shrink(bitmap, -count)
    integer, size = bitmap
    shift, sign = 2 ** count, -1 if size < 0 else +1
    return integer * shift, size + count * sign

def shrink(bitmap, count):
    '''Shrink a bitmap by some specified size

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    if count < 0:
        return grow(bitmap, -count)
    integer, size = bitmap
    shift, sign = 2 ** count, -1 if size < 0 else +1
    return integer / shift, size - count * sign

## for treating a bitmap like an integer stream
def push(bitmap, operand):
    '''Append bitmap data to the end of the current bitmap

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    (result, rbits) = bitmap
    (number, nbits) = operand

    rmask = 2 ** abs(rbits) - 1
    nmask = 2 ** abs(nbits) - 1
    shift = 2 ** abs(nbits)

    res = (result & rmask) * shift
    res |= number & nmask
    return res, rbits + (-abs(nbits) if rbits < 0 else +abs(nbits))

def insert(bitmap, operand):
    '''Insert bitmap data at the beginning of the bitmap

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    (result, rbits) = bitmap
    (number, nbits) = operand

    rmask = 2 ** abs(rbits) - 1
    nmask = 2 ** abs(nbits) - 1
    shift = 2 ** abs(rbits)

    res = (number & nmask) * shift
    res |= result & rmask
    return res, rbits + (-abs(nbits) if rbits < 0 else +abs(nbits))

def consume(bitmap, bits):
    '''Consume some number of bits off of the end of a bitmap

    If bitmap is signed, then return a signed integer.
    '''
    if bits < 0:
        raise AssertionError("Invalid bit count < 0 : {:d}".format(bits))
    bitmapinteger, bitmapsize = bitmap

    if bits > abs(bitmapsize):
        return zero, bitmapinteger
    integersize, integershift, integermask = bits, 2 ** bits, 2 ** bits - 1

    res = bitmapinteger & integermask
    if bitmapsize < 0:
        signmask = integershift / 2
        res = (res & (signmask - 1)) - (integershift / 2 if res & signmask else 0)
        bitmap = bitmapinteger / integershift, bitmapsize + integersize
    else:
        bitmap = bitmapinteger / integershift, bitmapsize - integersize
    return bitmap, res

def shift(bitmap, bits):
    '''Shift some number of bits off of the front of a bitmap

    If bitmap is signed, then return a signed integer.
    '''
    if bits < 0:
        raise AssertionError("Invalid bit count < 0 : {:d}".format(bits))
    bitmapinteger, bitmapsize = bitmap

    if bits > abs(bitmapsize):
        return zero, bitmapinteger
    integersize, integershift, integermask = bits, 2 ** bits, 2 ** bits - 1

    resultsize = abs(bitmapsize) - integersize
    resultshift = 2 ** resultsize
    resultmask = integermask * resultshift

    if bitmapsize < 0:
        signmask = integershift / 2
        res = (bitmapinteger & resultmask) / resultshift
        res = (res & (signmask - 1)) - (integershift / 2 if res & signmask else 0)
        bitmap = bitmapinteger & ~resultmask, -resultsize
    else:
        res = (bitmapinteger & resultmask) / resultshift
        bitmap = bitmapinteger & ~resultmask, resultsize
    return bitmap, res

class consumer(object):
    '''Given an iterable of an ascii string, provide an interface that supplies bits'''
    def __init__(self, iterable=()):
        self.source = iter(iterable)
        self.cache = new(0, 0)

    def insert(self, bitmap):
        self.cache = insert(self.cache, bitmap)
        return self

    def push(self, bitmap):
        self.cache = push(self.cache, bitmap)
        return self

    def read(self, bytes):
        '''Reads the specified number of bytes from iterable'''
        if bytes < 0:
            raise AssertionError("Invalid byte count < 0 : {:d}".format(bytes))

        result, count = 0, 0
        while bytes > 0:
            result *= 256
            result += six.byte2int(six.next(self.source))
            bytes, count = bytes - 1, count + 1
        self.cache = push(self.cache, new(result, count * 8))
        return count

    def consume(self, bits):
        '''Returns some number of bits as an integer'''
        if bits > self.cache[1]:
            count = bits - self.cache[1]
            bs = (count + 7) / 8
            self.read(bs)
            return self.consume(bits)
        self.cache, result = shift(self.cache, bits)
        return result

    def __repr__(self):
        cls = self.__class__
        return "{!s} {!r} {:s}".format(cls, self.cache, string(self.cache))

def repr(object):
    integer, size = object
    return "<type 'bitmap'> ({:#x}, {:d})".format(integer, size)

def data(bitmap, **kwargs):
    '''Convert a bitmap to a string left-aligned to 8-bits. Defaults to big-endian.'''
    reverse = builtins.next((kwargs[k] for k in ('reverse', 'reversed') if k in kwargs), False)
    integer, size = bitmap

    # align to 8-bits
    add, res = push if reversed else insert, size % 8
    if res > 0:
        bitmap = add(bitmap, (0, 8 - res))

    # convert to an array of octets
    remove, res = consume if reverse else shift, []
    while bitmap[1] != 0:
        bitmap, n = remove(bitmap, 8)
        res.append(n)

    # convert it to a string
    return str().join(map(six.int2byte, res))

def size(bitmap):
    '''Return the size of the bitmap, ignoring signedness'''
    integer, size = bitmap
    return abs(size)
def signed(bitmap):
    '''Returns true if bitmap is signed'''
    integer, size = bitmap
    return size < 0
def cast_signed(bitmap):
    '''Casts a bitmap to a signed integer'''
    integer, size = bitmap
    return integer, -abs(size)
def cast_unsigned(bitmap):
    '''Casts a bitmap to a unsigned integer'''
    integer, size = bitmap
    return integer, abs(size)
def value(bitmap):
    '''Return the integral part of a bitmap, handling signedness if necessary'''
    integer, size = bitmap
    if size < 0:
        signmask = 2 ** (abs(size) - 1)
        res = integer & (signmask - 1)
        if integer & signmask:
            return (signmask - res) * -1
        return res & (signmask - 1)
    return integer
int = num = number = value

def weight(bitmap):
    '''Return the number of bits that are set'''
    integer, size = bitmap
    res = 0
    while integer > 0:
        res, integer = res + 1, integer & (integer - 1)
    return res

def count(bitmap, value=False):
    '''Returns the number of bits that are set to value and returns the count'''
    _, size = bitmap
    res = weight(bitmap)
    return res if value else (size - res)

def splitter(bitmap, maxsize):
    '''Split bitmap into multiple of maxsize bits starting from the low bit.'''

    sign, maxsize = -1 if maxsize < 0 else +1, abs(maxsize)
    while True:
        integer, size = bitmap
        if size < maxsize:
            break
        bitmap, res = consume(bitmap, maxsize)
        yield res, sign * maxsize

    if size > 0:
        yield integer, sign * size
    return

def split(bitmap, maxsize):
    '''Returns a list of bitmaps resulting from the bitmap divided by maxsize bits.'''
    return list(splitter(bitmap, maxsize))[::-1]

def join(iterable):
    '''Join a list of bitmaps into a single one'''
    return six.moves.reduce(push, iterable, zero)

def groupby(sequence, count):
    '''Group sequence by number of elements'''
    key, data = lambda (index, value): index / count, enumerate(sequence)
    for key, res in itertools.groupby(data, key):
        yield builtins.map(operator.itemgetter(1), res)
    return

# jspelman. he's everywhere.
ror = lambda (v,b),shift=1: ((((v&2**shift-1) << b-shift) | (v>>shift)) & 2**b-1, b)
rol = lambda (v,b),shift=1: (((v << shift) | ((v & ((2**b-1) ^ (2**(b-shift)-1))) >> (b-shift))) & 2**b-1, b)

def reverse(bitmap):
    '''Flip the bit order of the bitmap'''
    res, (_, size) = zero, bitmap
    while res[1] < size:
        bitmap, value = consume(bitmap, 1)
        res = push(res, (value, 1))
    return res

def iterate(bitmap):
    '''Iterate through the bitmap returning True or False for each bit'''
    while bitmap[1] > 0:
        bitmap, value = shift(bitmap, 1)
        yield bool(value)
    return

def riterate(bitmap):
    '''Reverse iterate through the bitmap returning True or False for each bit'''
    while bitmap[1] > 0:
        bitmap, value = consume(bitmap, 1)
        yield bool(value)
    return

class WBitmap(object):
    '''
    A write-only bitmap for stuffing bits into.
    '''
    def __init__(self):
        import array
        self.bits, self.data = 0, array.array('B')

    def push(self, integer, bits):
        '''Stash an integer of the specified number of bits to the object.'''
        current = self.bits
        used = self.bits & 7
        leftover = 8 - used

        # If our current size is not aligned to 8, then we should just
        # need to extract the number of bits from the top of our integer
        # to pad our data to a multiple of 8 so that we can append the
        # rest of it with the logic that follows this next statement.

        if used and bits <= leftover:
            shift, mask = 2 ** bits, 2 ** bits - 1
            self.data[-1] *= shift
            self.data[-1] |= integer & mask
            self.bits += bits
            return self.bits - current

        # If we're trying to push more than 8 bits, then we simply need
        # to consume what is left to pad our data to 8-bits and then
        # proceed through the logic that follows
        elif used:
            shift, mask = 2 ** leftover, 2 ** leftover - 1

            # Shift the last byte of our data up by the number of bits
            # that we're going to append
            self.data[-1] *= shift

            # Extract the bits from our integer, and OR it into the
            # last byte of our data so that we should now be padded
            # along a byte boundary (multiple of 8).
            offset = bits - leftover
            res = integer & (mask * 2**offset)
            self.data[-1] |= res / 2**offset

            # Update the bits that we've processed
            self.bits, bits = self.bits + leftover, bits - leftover

        # If our current size is aligned to 8, then we simply need to
        # just push the integer to our data and update our size. This
        # same logic should also apply if our data is empty.
        while bits >= 8:
            shift = 2 ** bits / 0x100
            res = integer & (0xff * shift)
            self.data.append(res / shift)
            self.bits, bits = self.bits + 8, bits - 8

        # Add any extra bits that were leftover as the last byte
        if bits:
            mask = 2 ** bits - 1
            self.data.append(integer & mask)
            self.bits += bits

        return self.bits - current

    def int(self):
        '''Return the bitmap as an integer.'''
        used = self.bits & 7
        if used:
            shift, mask = 2 ** used, 2 ** used - 1
            res = reduce(lambda agg, n: agg * 0x100 + n, self.data[:-1], 0)
            return (res * shift) | (self.data[-1] & mask)
        return reduce(lambda agg, n: agg * 0x100 + n, self.data, 0)

    def size(self):
        '''Return the current number of bits that have been stored.'''
        return self.bits

    def serialize(self):
        '''Return the object rendered to a string (serialized).'''
        return self.data.tostring()

    def __repr__(self):
        cls, length = self.__class__, math.ceil(self.bits / 4.0)
        return "{!s} ({:#0{:d}x}, {:d})".format(cls, self.int(), 2 + math.trunc(length), self.bits)

class RBitmap(object):
    '''
    A read-only bitmap for consuming bits from some arbitrary data.
    '''
    def __init__(self, data):
        import array
        self.offset, self.data = 0, array.array('B', data)

    def size(self):
        '''Return the number of bits that are available.'''
        return 8 * len(self.data) - self.offset

    def consume(self, bits):
        '''Consume the specified number of bits from the object.'''
        leftover = 8 - self.offset

        if self.offset and bits < leftover:
            shift, mask = 2 ** (leftover - bits), 2 ** bits - 1
            result = self.data[0] / shift
            self.offset, self.data[0] = self.offset + bits, self.data[0] & (2 * shift - 1)
            return result & mask

        elif self.offset:
            shift, mask = 2 ** leftover, 2 ** leftover - 1
            result = self.data[0] & mask
            self.offset, bits = 0, bits - leftover
            self.data[:] = self.data[1:]

        else:
            result = 0

        shift = 2 ** 8
        while bits >= 8:
            result *= shift
            result += self.data[0]
            bits, self.data[:] = bits - 8, self.data[1:]

        leftover = 8 - bits
        if bits > 0:
            shift, mask = 2 ** leftover, 2 ** bits - 1
            result *= 2 ** bits
            result += ((self.data[0] / shift) & mask) if len(self.data) else 0
            self.offset = bits
        return result

if 'TODO':
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

if __name__ == '__main__':
    import ptypes
    from ptypes import bitmap

    ### set
    @TestCase
    def set_bitmap_signed():
        result = bitmap.new(0, -32)
        freeslot = 0
        count = 3
        result = bitmap.set(result, freeslot, 1, count)
        if bitmap.value(result) == 7:
            raise Success

#    @TestCase
    def set_bitmap_unsigned():
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
        for i in six.moves.range(6):
            print x
            x = bitmap.add(x, 3)

        for i in six.moves.range(6):
            print x
            x = bitmap.sub(x, 6)

        x = bitmap.new(4,4)
        print bitmap.string(bitmap.ror(bitmap.ror(bitmap.ror(x))))

    ### add
    @TestCase
    def signed_add_positive_wrap():
        x = (255, -8)
        res = bitmap.add(x, 1)
        if res == (0, -8) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def signed_add_positive_nowrap():
        x = (254, -8)
        res = bitmap.add(x, 1)
        if res == (255, -8) and bitmap.value(res) == -1:
            raise Success
    @TestCase
    def signed_add_negative_wrap():
        x = (254,-8)
        res = bitmap.add(x, 2)
        if res == (0,-8) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def signed_add_negative_nowrap():
        x = (250,-8)
        res = bitmap.add(x, 5)
        if res == (255,-8) and bitmap.value(res) == -1:
            raise Success

    ### sub
    @TestCase
    def signed_sub_positive_wrap():
        x = (5, -8)
        res = bitmap.sub(x, 10)
        if res == (251, -8) and bitmap.value(res) == -5:
            raise Success
    @TestCase
    def signed_sub_positive_nowrap():
        x = (10, -8)
        res = bitmap.sub(x, 5)
        if res == (5, -8) and bitmap.value(res) == 5:
            raise Success
    @TestCase
    def signed_sub_negative_nowrap():
        x = (156,-8)
        res = bitmap.sub(x, 10)
        if res == (146,-8) and bitmap.value(res) == -110:
            raise Success
    @TestCase
    def signed_sub_negative_wrap():
        x = (133,-8)
        res = bitmap.sub(x, 10)
        if res == (123,-8) and bitmap.value(res) == 123:
            raise Success

    ### grow
    @TestCase
    def grow_unsigned():
        x = (5, 4)
        res = bitmap.grow(x, 4)
        if res == (5*2**4,8) and bitmap.value(res) == 5*2**4:
            raise Success
    @TestCase
    def grow_signed():
        x = (15, -4)
        res = bitmap.grow(x, 4)
        if res == (15*2**4,-8) and bitmap.value(res) == -16:
            raise Success

    ### shrink
    @TestCase
    def shrink_unsigned():
        x = (0x50, 8)
        res = bitmap.shrink(x, 4)
        if res == (5,4) and bitmap.value(res) == 5:
            raise Success
    @TestCase
    def shrink_signed():
        x = (0xff, -8)
        res = bitmap.shrink(x, 4)
        if res == (15,-4) and bitmap.value(res) == -1:
            raise Success

    ### push
    @TestCase
    def push_bitmap_unsigned():
        x = (15,4)
        res = bitmap.push(x, (15,4))
        if res == (0xff,8) and bitmap.value(res) == 255:
            raise Success
    @TestCase
    def push_bitmap_signed():
        x = (15,-4)
        res = bitmap.push(x, (15,4))
        if res == (0xff,-8) and bitmap.value(res) == -1:
            raise Success

    ### consume
    @TestCase
    def consume_unsigned_bitmap_unsigned():
        x = (0x41424344,32)
        res,n = bitmap.consume(x, 8)
        if n == 0x44 and res == (0x414243,24):
            raise Success
    @TestCase
    def consume_signed_bitmap_unsigned():
        x = (0x414243ff,32)
        res,n = bitmap.consume(x, 8)
        if n == 0xff and res == (0x414243,24):
            raise Success
    @TestCase
    def consume_unsigned_bitmap_signed():
        x = (0x41424344,-32)
        res,n = bitmap.consume(x, 8)
        if n == 0x44 and res == (0x414243,-24):
            raise Success
    @TestCase
    def consume_signed_bitmap_signed():
        x = (0x414243ff,-32)
        res,n = bitmap.consume(x, 8)
        if n == -1 and res == (0x414243,-24):
            raise Success
    @TestCase
    def consume_zero_bitmap_unsigned():
        x = (0x41424344,32)
        res,n = bitmap.consume(x, 0)
        if n == 0 and res == x:
            raise Success
    @TestCase
    def consume_zero_bitmap_signed():
        x = (0x41424344,-32)
        res,n = bitmap.consume(x, 0)
        if n == 0 and res == x:
            raise Success
    @TestCase
    def consume_empty_bitmap():
        x = (0,0)
        res,n = bitmap.consume(x, 8)
        if n == 0 and res == x:
            raise Success

    ### shift
    @TestCase
    def shift_unsigned_bitmap_unsigned():
        x = (0x41424344,32)
        res,n = bitmap.shift(x, 8)
        if n == 0x41 and res == (0x424344,24):
            raise Success
    @TestCase
    def shift_signed_bitmap_unsigned():
        x = (0xff424344,32)
        res,n = bitmap.shift(x, 8)
        if n == 0xff and res == (0x424344,24):
            raise Success
    @TestCase
    def shift_unsigned_bitmap_signed():
        x = (0x41424344,-32)
        res,n = bitmap.shift(x, 8)
        if n == 0x41 and res == (0x424344,-24):
            raise Success
    @TestCase
    def shift_signed_bitmap_signed():
        x = (0xff424344,-32)
        res,n = bitmap.shift(x, 8)
        if n == -1 and res == (0x424344,-24):
            raise Success
    @TestCase
    def shift_zero_bitmap_unsigned():
        x = (0x41424344, 32)
        res,n = bitmap.shift(x, 0)
        if n == 0 and res == (0x41424344,32):
            raise Success
    @TestCase
    def shift_zero_bitmap_signed():
        x = (0x41424344, -32)
        res,n = bitmap.shift(x, 0)
        if n == 0 and res == (0x41424344,-32):
            raise Success
    @TestCase
    def shift_empty_bitmap():
        x = (0,0)
        res,n = bitmap.shift(x, 8)
        if n == 0 and res == (0,0):
            raise Success

    ### mul
    @TestCase
    def mul_unsigned_bitmap_unsigned():
        x = (0x40000000,32)
        res = bitmap.mul(x, 4)
        if res == (0,32) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def mul_unsigned_bitmap_signed():
        x = (0x40000000,32)
        res = bitmap.mul(x, -4)
        if res == (0,32) and bitmap.value(res) == 0:
            raise Success

    #signed_divide(4,4) == 0xc000000000000002L and signed_divide(4,-4) !=
    #signed_divide(-4,4)
    #signed_divide(0xffffffffffffa251, 0x00000000000000c1) == 0xffffffffffffff84
    #signed_divide(0xffffffffffff1634, 0x00000000000000ad) == 0xfffffffffffffea7
    #assert(signed_divide(0x0000000000000004, 0x0000000000000004) == 0x0000000000000001)
    #assert(signed_divide(0xffffffffffffa251, 0x00000000000000c1) == 0xffffffffffffff84)
    #assert(signed_divide(0xffffffffffff1634, 0x00000000000000ad) == 0xfffffffffffffea7)
    #assert(signed_divide(0x8888888800000000, 0x0000000400000000) == 0x0000000022222222)
    #assert(signed_divide(0x0000000000004000, 0x0000000000000004) == 0x0000000000001000)

    ### div
    @TestCase
    def div_unsigned_bitmap_unsigned():
        '''0x10000000 / 0x10 = 0x1000000'''

        x = (0x10000000,32)
        res = bitmap.div(x,0x10)
        if bitmap.value(res) == 0x1000000:
            raise Success
    @TestCase
    def div_unsigned_bitmap_signed():
        '''0x10 / -0x10 = -1'''
        x = (0x10,-32)
        res = bitmap.div(x,-0x10)
        if bitmap.value(res) == -1:
            raise Success
    @TestCase
    def div_signed_bitmap_signed_1():
        x = (0xffffffffffffa251,-64)
        res = bitmap.div(x, 0xc1)
        if bitmap.value(res) == -124:
            raise Success
    @TestCase
    def div_signed_bitmap_signed_2():
        x = (0xffffffffffff1634,-64)
        res = bitmap.div(x, 0xad)
        if bitmap.value(res) == -345:
            raise Success

    @TestCase
    def div_signed_bitmap_unsigned():
        '''-0x10/-0x10 = 1'''
        x = (0xfffffffffffffff0,-64)
        res = bitmap.div(x, -0x10)
        if bitmap.value(res) == 1:
            raise Success

    ### mod
    @TestCase
    def mod_unsigned_bitmap_unsigned():
        '''23983 % 5 == 3'''
        mask=2**64-1
        x = (23983&mask,64)
        res = bitmap.mod(x, 5)
        if bitmap.value(res) == 3:
            raise Success
    @TestCase
    def mod_unsigned_bitmap_signed():
        '''23983 % -5 == -2'''
        mask=2**64-1
        x = (23983&mask,-64)
        res = bitmap.mod(x, -5)
        if bitmap.signed(res) and bitmap.value(res) == -2:
            raise Success
    @TestCase
    def mod_signed_bitmap_unsigned():
        '''-23983 % -5 == 2'''
        mask=2**64-1
        x = (-23983&mask,64)
        res = bitmap.mod(x, -5)
        if bitmap.value(res) == 0xfffffffffffffffe:
            raise Success

    @TestCase
    def mod_signed_bitmap_signed():
        '''-23983 % -5 == -3'''
        mask=2**64-1
        x = (-23983&mask,-64)
        res = bitmap.mod(x, -5)
        if bitmap.signed(res) and bitmap.value(res) == -3:
            raise Success

    @TestCase
    def data_padding():
        res = bitmap.new(0x123, 12)
        data = bitmap.data(res, reversed=0)
        if data.encode('hex') == '1230':
            raise Success

    @TestCase
    def data_padding_reversed():
        res = bitmap.new(0x123, 12)
        data = bitmap.data(res, reversed=1)
        if data.encode('hex') == '3012':
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
