"""bitmap = (integer, bits)
"""
import builtins, sys, math
import functools, operator, itertools, types

# Setup some version-agnostic types that we can perform checks with
integer_types = (int, long) if sys.version_info[0] < 3 else (int,)

# We need this because micropython doesn't implement a multi-parameter next().
def builtins_next(iterable, *args):
    '''
    next(iterator[, default])

    Return the next item from the iterator. If default is given and the iterator
    '''
    if len(args) > 1:
        raise TypeError("next expected at most {:d} arguments, got {:d}".format(2, 1 + len(args)))
    try:
        result = builtins.next(iterable)
    except StopIteration as E:
        if args:
            default, = args
            return default
        raise E
    return result

# py2 and micropython
next = builtins.next if not hasattr(sys, 'implementation') else builtins.next if sys.implementation.name in {'cpython'} else builtins_next

## start somewhere
def new(value, size):
    '''creates a new bitmap object. Bitmaps "grow" to the left.'''
    mask = pow(2, abs(size)) - 1
    if size < 0:
        #signmask = pow(2, abs(size) - 1)
        return value & mask, size
    return value & mask, size

zero = new(0, 0)

def isinteger(integer):
    '''Returns true if provided variable is of type int or long'''
    return builtins.isinstance(integer, integer_types)
integerQ = isinteger

def isinstance(bitmap):
    '''Returns true if provided variable is a valid bitmap type'''

    # We really shouldn't be manually keeping track of types like this...
    return builtins.isinstance(bitmap, tuple) and len(bitmap) == 2 and all(isinteger(item) for item in bitmap)
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
    '''Returns bitmap as a formatted binary string starting with the most-significant-bits first'''
    reverse = next((kwargs[k] for k in ['reverse', 'reversed'] if k in kwargs), False)
    integer, size = bitmap
    res = "{:0{:d}b}".format(integer, abs(size))
    return str().join(reversed(res)) if reverse else res

def hex(bitmap):
    '''Return bitmap as a hex string'''
    integer, size = bitmap
    size = abs(size)
    length = math.trunc(math.ceil(size / 4.0))
    if size < 0:
        max, sign = pow(2, size), math.trunc(pow(2, size - 1))
        res = integer & (max - 1)
        return "{:+#0{:d}x}".format((res - max) if res & sign else res & (sign - 1), length + 3)
    return "{:#0{:d}x}".format(integer & pow(2, size) - 1, length + 2)

def scan(bitmap, value=True, position=0):
    '''Searches through bitmap for the specified value (least to most) and returns its position'''
    integer, size = bitmap

    if not(1 - abs(size) <= position < abs(size)):
        raise AssertionError("Invalid position {:d} : {:d}<>{:d}".format(position, -abs(size), abs(size)))
    index = position % abs(size) if size else 0

    bitmask = pow(2, index)
    for i in range(abs(size) - index):
        if bool(integer & bitmask) == value:
            return index + i
        bitmask *= 2
    raise ValueError("Unable to find a {:d} bit at position {:d} within the bitmap ({:s})".format(value, index, string(bitmap)))

def scanreverse(bitmap, value=True, position=-1):
    '''Searches through bitmap for the specified value (most to least) and returns its position'''
    integer, size = bitmap

    if not(1 - abs(size) <= position < abs(size)):
        raise AssertionError("Invalid position {:d} : {:d} <> {:d}".format(position, -abs(size), abs(size)))
    index = position % abs(size) if size else 0

    bitmask = pow(2, index)
    for i in range(index):
        if bool(integer & bitmask) == value:
            return index - i
        bitmask //= 2
    raise ValueError("Unable to find a {:d} bit from position {:d} within the bitmap ({:s})".format(value, index, string(bitmap)))

def runscan(bitmap, value, length, position=0):
    '''Will return the position of a run fulfilling the parameters in bitmap'''
    integer, size = bitmap

    if not(1 - abs(size) <= position < abs(size)):
        raise AssertionError("Invalid position {:d} : {:d} <> {:d}".format(position, -abs(size), abs(size)))
    index = position % abs(size) if size else 0

    for run_integer, run_length in run(bitmap, position=index):
        # snag a run that best fits user's reqs
        if bool(run_integer & 1) == value and length <= run_length:
            return index
        index += run_length
    raise ValueError("Unable to find a {:d} bit run of {:d} at position {:d} within the bitmap ({:s})".format(length, value, position, string(bitmap)))

def runlength(bitmap, value, position=0):
    '''Returns the count of bits, starting at position'''
    integer, size = bitmap
    if not(1 - abs(size) <= position < abs(size)):
        raise AssertionError("Invalid position {:d} : {:d} <> {:d}".format(position, -abs(size), abs(size)))
    index = position % abs(size) if size else 0
    try:
        result = scan(bitmap, not value, index) - index
    except ValueError:
        result = abs(size) - index
    return result

def run(bitmap, position=0):
    '''Iterates through all the runs in a given bitmap'''
    integer, size = bitmap
    if not(1 - abs(size) <= position < abs(size)):
        raise AssertionError("Invalid position {:d} : {:d} <> {:d}".format(position, -abs(size), abs(size)))
    index = position % abs(size) if size else 0

    value, count = integer & pow(2, index), abs(size)
    while index < count:
        length = runlength((integer, size), value, index)
        yield get(bitmap, index, length)
        index = index + length
        value = not value
    return

def set(bitmap, position, value=True, count=1):
    '''Store value into bitmap starting at position'''
    integer, size = bitmap
    index = position % abs(size) if size else 0

    if count < 0:
        raise AssertionError("A negative count ({:d}) was specified".format(count))

    mask, sizemask = functools.reduce(lambda aggregate, bit: pow(2, bit) | aggregate, range(index, index + count), 0), pow(2, abs(size)) - 1
    if value:
        return integer | mask & sizemask, size
    return integer & ~mask & sizemask, size

def get(bitmap, position, count):
    '''Fetch count number of bits from bitmap starting at position'''
    integer, size = bitmap
    index = position % abs(size) if size else 0

    if count < 0:
        raise AssertionError("A negative count ({:d}) was specified".format(count))

    mask, size = functools.reduce(lambda aggregate, bit: pow(2, bit) | aggregate, range(index, index + count), 0), abs(size)
    return (integer & mask) >> index, count

def add(bitmap, integer):
    '''Adds an integer to the specified bitmap whilst preserving signedness'''
    res, size = bitmap
    if size < 0:
        pass        # XXX: we trust that python handles signedness properly via &
    mask = pow(2, abs(size)) - 1
    return (integer + res) & mask, size
def sub(bitmap, integer):
    '''Subtracts an integer to the specified bitmap whilst preserving signedness'''
    res, size = bitmap
    if size < 0:
        pass        # XXX: we trust that python handles signedness properly via &
    mask = pow(2, abs(size)) - 1
    return (res - integer) & mask, size

def mul(bitmap, integer):
    '''Multiplies the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = pow(2, abs(size))
    if size < 0:
        sign = math.trunc(pow(2, abs(size) - 1))
        res = (res - max) if res & sign else res & (sign - 1)
    return (res * integer) & (max - 1), size
def div(bitmap, integer):
    '''Divides the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = pow(2, abs(size))
    if size < 0:
        sign = math.trunc(pow(2, abs(size) - 1))
        res = (res - max) if res & sign else res & (sign - 1)
    return (res // integer) & (max - 1), size
def mod(bitmap, integer):
    '''Modular divides the specified bitmap with an integer whilst preserving signedness'''
    res, size = bitmap
    max = pow(2, abs(size))
    if size < 0:
        sign = math.trunc(pow(2, abs(size) - 1))
        res = (res - max) if res & sign else res & (sign - 1)
    return (res % integer) & (max - 1), size

def grow(bitmap, count):
    '''Grow bitmap by some specified number of bits

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    if count < 0:
        return shrink(bitmap, -count)
    integer, size = bitmap
    shift, sign = pow(2, count), -1 if size < 0 else +1
    return integer * shift, size + count * sign

def shrink(bitmap, count):
    '''Shrink a bitmap by some specified size

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    if count < 0:
        return grow(bitmap, -count)
    integer, size = bitmap
    shift, sign = pow(2, count), -1 if size < 0 else +1
    return integer // shift, size - count * sign

## for treating a bitmap like an integer stream
def push(bitmap, operand):
    '''Push bitmap data into the front of the current bitmap (least significant).

    This treats the bitmap as a set of bits and thus ignores the signed bit.
    '''
    (result, rbits) = bitmap
    (number, nbits) = operand

    rmask = pow(2, abs(rbits)) - 1
    nmask = pow(2, abs(nbits)) - 1
    shift = pow(2, abs(nbits))

    res = (result & rmask) * shift
    res |= number & nmask
    return res, rbits + (-abs(nbits) if rbits < 0 else +abs(nbits))

def append(bitmap, operand):
    '''Append bitmap data at the end of the bitmap (most significant).

    This treats the bitmap as a complete set of bits and thus ignores the signed bit.
    '''
    (result, rbits) = bitmap
    (number, nbits) = operand

    rmask = pow(2, abs(rbits)) - 1
    nmask = pow(2, abs(nbits)) - 1
    shift = pow(2, abs(rbits))

    res = (number & nmask) * shift
    res |= result & rmask
    return res, rbits + (-abs(nbits) if rbits < 0 else +abs(nbits))
insert = append     # backwards-compatibility

def consume(bitmap, bits):
    '''Consume some number of bits off of the end of a bitmap (most significant).

    If bitmap is signed, then return a signed integer.
    '''
    if bits < 0:
        raise AssertionError("Invalid bit count < 0 : {:d}".format(bits))
    bitmapinteger, bitmapsize = bitmap

    if bits > abs(bitmapsize):
        return zero, bitmapinteger
    integersize, integershift, integermask = bits, pow(2, bits), pow(2, bits) - 1

    res = bitmapinteger & integermask
    if bitmapsize < 0:
        signmask = integershift // 2
        res = (res & (signmask - 1)) - (integershift // 2 if res & signmask else 0)
        bitmap = bitmapinteger // integershift, bitmapsize + integersize
    else:
        bitmap = bitmapinteger // integershift, bitmapsize - integersize
    return bitmap, res

def shift(bitmap, bits):
    '''Shift some number of bits off of the front of a bitmap (least significant).

    If bitmap is signed, then return a signed integer.
    '''
    if bits < 0:
        raise AssertionError("Invalid bit count < 0 : {:d}".format(bits))
    bitmapinteger, bitmapsize = bitmap

    if bits > abs(bitmapsize):
        return zero, bitmapinteger
    integersize, integershift, integermask = bits, pow(2, bits), pow(2, bits) - 1

    resultsize = abs(bitmapsize) - integersize
    resultshift = pow(2, resultsize)
    resultmask = integermask * resultshift

    if bitmapsize < 0:
        signmask = integershift // 2
        res = (bitmapinteger & resultmask) // resultshift
        res = (res & (signmask - 1)) - (integershift // 2 if res & signmask else 0)
        bitmap = bitmapinteger & ~resultmask, -resultsize
    else:
        res = (bitmapinteger & resultmask) // resultshift
        bitmap = bitmapinteger & ~resultmask, resultsize
    return bitmap, res

class consumer(object):
    '''Given an iterable of an ascii string, provide an interface that supplies bits'''

    if sys.version_info[0] < 3:
        @classmethod
        def __make_interator__(cls, iterable):
            # XXX: in python2, byte-iterators always return bytes
            F = functools.partial(itertools.imap, ord)
            return F(iterable)

    else:
        @classmethod
        def __make_interator__(cls, iterable):
            # XXX: if we're a generator, we might _actually_ be iterating
            #      through bytes...
            if builtins.isinstance(iterable, types.GeneratorType):
                return (ord(item) for item in iterable)

            # XXX: but, in python3 byte-iterators always return ints...
            return iter(iterable)

    def __init__(self, iterable=(), position=0, order='big'):
        self.source = self.__make_interator__(iterable)
        self.cache = new(0, 0)
        self.position = position

        assert(order in {'little', 'big'})
        self.order, self.__reorder = order, reverse_bits if order == 'little' else lambda *integer_size: integer_size

    def insert(self, bitmap):
        self.cache = insert(self.cache, bitmap)
        return self

    def push(self, bitmap):
        self.cache = push(self.cache, bitmap)
        return self

    if hasattr(builtins.int, 'from_bytes'):
        @staticmethod
        def __read(source, bytes, from_bytes=builtins.int.from_bytes):
            octets = bytearray(itertools.islice(source, bytes))
            return from_bytes(octets), len(octets)
    else:
        @staticmethod
        def __read(source, bytes):
            octets = bytearray(itertools.islice(source, bytes))
            result = functools.reduce(lambda agg, octet: octet | agg * 0x100, octets, 0)
            return result, len(octets)

    def read(self, bytes):
        '''Reads the specified number of bytes from iterable'''
        if bytes > 1:
            result, count = self.__read(self.source, bytes)
            self.cache = push(self.cache, self.__reorder(result, 8 * count))
            if count != bytes:
                raise StopIteration(bytes, count)
            return count

        # push an octet onto the little end of our bitmap
        elif bytes:
            integer, bits = self.cache
            result, integer = next(self.source), integer * 0x100
            self.cache = result | integer, bits + 8
            return 1

        raise AssertionError("Invalid byte count < 0 : {:d}".format(bytes))

    def slowread(self, bytes):
        '''Reads the specified number of bytes from iterable'''
        if bytes < 0:
            raise AssertionError("Invalid byte count < 0 : {:d}".format(bytes))

        result, count = 0, 0
        while bytes > 0:
            result *= 256
            result += next(self.source)
            bytes, count = bytes - 1, count + 1
        self.cache = push(self.cache, (result, count * 8))
        return count

    def consume(self, bits):
        '''Returns some number of bits as an integer'''
        #available = size(self.cache)
        integer, available = self.cache
        if bits > available:
            count = bits - available
            bs, extra = divmod(count, 8)
            self.read(bs + 1) if extra else self.read(bs)
            return self.consume(bits)

        # FIXME: not sure why i'm shifting from the front, here, because really we should be
        #        consuming from the lsb to avoid processing bigints while reading (consuming).
        self.cache, result = shift(self.cache, bits)
        self.position += bits
        return result

    def __repr__(self):
        cls = self.__class__
        return "{!s} {!r} {:s}".format(cls, self.cache, string(self.cache))

def repr(object):
    integer, length = value(object), size(object)
    if signed(object):
        return "<type 'bitmap'> ({:+#0{:d}x}, {:d})".format(integer, 3 + math.ceil(length / 4.), length)
    return "<type 'bitmap'> ({:#0{:d}x}, {:d})".format(integer, 2 + math.ceil(length / 4.), length)

def data(bitmap, **kwargs):
    '''Convert a bitmap to a string left-aligned to 8-bits. Defaults to big-endian.'''
    reverse = next((kwargs[k] for k in ['reverse', 'reversed'] if k in kwargs), False)
    integer, size = bitmap

    # align to 8-bits
    add, res = push if reversed else insert, size % 8
    if res > 0:
        bitmap = add(bitmap, (0, 8 - res))

    # convert to an array of octets
    remove, res = consume if reverse else shift, []
    while bitmap[1] != 0:
        bitmap, item = remove(bitmap, 8)
        res.append(item)

    # convert it to a bytes
    return bytes(bytearray(res))

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
    return new(integer, -abs(size))
def cast_unsigned(bitmap):
    '''Casts a bitmap to a unsigned integer'''
    integer, size = bitmap
    return new(integer, abs(size))
def value(bitmap):
    '''Return the integral part of a bitmap, handling signedness if necessary'''
    integer, size = bitmap
    if size < 0:
        signmask = math.trunc(pow(2, abs(size) - 1))
        res = integer & (signmask - 1)
        if integer & signmask:
            return (signmask - res) * -1
        return res & (signmask - 1)
    return integer & pow(2, size) - 1
int = num = number = value

def hamming(bitmap):
    '''Return the number of bits that are set (hamming distance)'''
    integer, _ = bitmap
    res = 0
    while integer > 0:
        res, integer = res + 1, integer & (integer - 1)
    return res
weight = hamming

def count(bitmap, value=False):
    '''Returns the number of bits that are set to value and returns the count'''
    _, size = bitmap
    res = hamming(bitmap)
    return res if value else (abs(size) - res)

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
    return functools.reduce(push, iterable, zero)

def groupby(sequence, count):
    '''Group sequence by number of elements'''
    idata = enumerate(sequence)
    def fkey(item):
        (index, value) = item
        return index // count

    for key, iterable in itertools.groupby(idata, fkey):
        yield builtins.map(operator.itemgetter(1), iterable)
    return

# jspelman. he's everywhere.
def ror(bitmap, shift=1):
    '''
    jspelman. he's everywhere.
    ror = lambda (v,b),shift=1: ((((v&2**shift-1) << b-shift) | (v>>shift)) & 2**b-1, b)
    '''
    (value, size) = bitmap
    return new((((value & pow(2, shift) - 1) << size - shift) | (value >> shift)) & pow(2, size) - 1, size)

def rol(bitmap, shift=1):
    '''
    jspelman. he's everywhere.
    rol = lambda (v,b),shift=1: (((v << shift) | ((v & ((2**b-1) ^ (2**(b-shift)-1))) >> (b-shift))) & 2**b-1, b)
    '''
    (value, size) = bitmap
    return new(((value << shift) | ((value & ((pow(2, size) - 1) ^ (pow(2, size - shift) - 1))) >> (size - shift))) & pow(2, size) - 1, size)

def reverse_by_bits(size):
    '''Return a function that will reverse a bitmap in chunks divided by the specified number of bits.'''
    bits, mask, start = max(1, size), pow(2, size) - 1, pow(2, size - 1)

    def reverse(integer, size):
        '''flip the bit order of the specified `integer` with `size` bits.'''
        res, counter, chunk = 0, size, 0
        while counter >= bits:
            chunk, little, big = integer & mask, 1, start
            while big > little:
                if (not(chunk & big)) != (not(chunk & little)):
                    chunk ^= big | little
                little, big = little << 1, big >> 1
            res, integer, counter = chunk | res << bits, integer >> bits, counter - bits

        # process the left over bits that were missed due to misalignment
        chunk, missed, big, little = 0, counter, 1 << counter, 1
        while counter:
            big >>= 1
            chunk |= big if integer & little else 0
            counter, little = counter - 1, little << 1
        return chunk | (res << missed) if missed else res, size
    return reverse
reverse_bits = reverse_by_bits(sys.int_info.bits_per_digit if hasattr(sys, 'int_info') else sys.long_info.bits_per_digit)

def reverse(bitmap):
    '''Flip the bit order of the bitmap (slowly)'''
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

#def levenshtein(first, second):
#    '''
#    Calculate the Levenshtein distance between two strings. ie: The number of transformations required to transform one
#    string to the other.
#    '''
#
#    if len(first) > len(second):
#        first, second = second, first
#
#    if len(second) == 0:
#        return len(first)
#
#    first_length    = len(first)  + 1
#    second_length   = len(second) + 1
#
#    distance_matrix = [range(second_length) for x in range(first_length)]
#
#    for i in range(1, first_length):
#        for j in range(1, second_length):
#            deletion     = distance_matrix[i-1][j] + 1
#            insertion    = distance_matrix[i][j-1] + 1
#            substitution = distance_matrix[i-1][j-1]
#
#            if first[i-1] != second[j-1]:
#                substitution += 1
#
#            distance_matrix[i][j] = min(insertion, deletion, substitution)
#
#    return distance_matrix[first_length-1][second_length-1]

def shannon(bitmap):
    '''Calculate the entropy for the bits in a bitmap.'''
    Flog2 = (lambda x: math.log(x, 2)) if sys.version_info[0] < 3 else math.log2
    Fx = lambda probability: -probability * Flog2(probability)
    count, weight = size(bitmap), hamming(bitmap)
    collection = [weight, count - weight]
    probabilities = [item / float(count) for item in collection if item]
    return sum(map(Fx, probabilities))

class WBitmap(object):
    '''
    A write-only bitmap for stuffing bits into.
    '''
    def __init__(self, data=b''):
        self.bits, self.data = 8 * len(data), bytearray(data)

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
            shift, mask = pow(2, bits), pow(2, bits) - 1
            self.data[-1] *= shift
            self.data[-1] |= integer & mask
            self.bits += bits
            return self.bits - current

        # If we're trying to push more than 8 bits, then we simply need
        # to consume what is left to pad our data to 8-bits and then
        # proceed through the logic that follows
        elif used:
            shift, mask = pow(2, leftover), pow(2, leftover) - 1

            # Shift the last byte of our data up by the number of bits
            # that we're going to append
            self.data[-1] *= shift

            # Extract the bits from our integer, and OR it into the
            # last byte of our data so that we should now be padded
            # along a byte boundary (multiple of 8).
            offset = bits - leftover
            res = integer & (mask * pow(2, offset))
            self.data[-1] |= res // pow(2, offset)

            # Update the bits that we've processed
            self.bits, bits = self.bits + leftover, bits - leftover

        # If our current size is aligned to 8, then we simply need to
        # just push the integer to our data and update our size. This
        # same logic should also apply if our data is empty.
        while bits >= 8:
            shift = pow(2, bits) // 0x100
            res = integer & (0xff * shift)
            self.data.append(res // shift)
            self.bits, bits = self.bits + 8, bits - 8

        # Add any extra bits that were leftover as the last byte
        if bits:
            mask = pow(2, bits) - 1
            self.data.append(integer & mask)
            self.bits += bits

        return self.bits - current

    def int(self):
        '''Return the bitmap as an integer.'''
        used = self.bits & 7
        if used:
            shift, mask = pow(2, used), pow(2, used) - 1
            res = functools.reduce(lambda agg, item: agg * 0x100 + item, self.data[:-1], 0)
            return (res * shift) | (self.data[-1] & mask)
        return functools.reduce(lambda agg, item: agg * 0x100 + item, self.data, 0)

    def size(self):
        '''Return the current number of bits that have been stored.'''
        return self.bits

    def serialize(self):
        '''Return the object rendered to a string (serialized).'''
        return bytes(self.data)

    def __repr__(self):
        cls, length = self.__class__, math.ceil(self.bits / 4.0)
        return "{!s} ({:#0{:d}x}, {:d})".format(cls, self.int(), 2 + math.trunc(length), self.bits)

class RBitmap(object):
    '''
    A read-only bitmap for consuming bits from some arbitrary data.
    '''
    def __init__(self, data):
        self.offset, self.data = 0, bytearray(data)

    def size(self):
        '''Return the number of bits that are available.'''
        return 8 * len(self.data) - self.offset

    def consume(self, bits):
        '''Consume the specified number of bits from the object.'''
        leftover = 8 - self.offset

        if self.offset and bits < leftover:
            shift, mask = pow(2, leftover - bits), pow(2, bits) - 1
            result = self.data[0] // shift
            self.offset, self.data[0] = self.offset + bits, self.data[0] & (2 * shift - 1)
            return result & mask

        elif self.offset:
            shift, mask = pow(2, leftover), pow(2, leftover) - 1
            result = self.data[0] & mask
            self.offset, bits = 0, bits - leftover
            self.data[:] = self.data[1:]

        else:
            result = 0

        shift = pow(2, 8)
        while bits >= 8:
            result *= shift
            result += self.data[0]
            bits, self.data[:] = bits - 8, self.data[1:]

        leftover = 8 - bits
        if bits > 0:
            shift, mask = pow(2, leftover), pow(2, bits) - 1
            result *= pow(2, bits)
            result += ((self.data[0] // shift) & mask) if len(self.data) else 0
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
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import ptypes
    from ptypes import bitmap
    from ptypes.utils import operator

    import sys
    if hasattr(b'', 'hex'):
        tohex = operator.methodcaller('encode', 'hex') if sys.version_info[0] < 3 else operator.methodcaller('hex')
    else:
        tohex = lambda bytes: ''.join(map("{:02x}".format, bytearray(bytes)))

    ### set
    @TestCase
    def set_bitmap_signed():
        result = bitmap.new(0, -32)
        freeslot = 0
        count = 3
        result = bitmap.set(result, freeslot, 1, count)
        if bitmap.value(result) == 7:
            raise Success

    @TestCase
    def set_bitmap_unsigned_0():
        x = bitmap.new(0xf000000000000000, 64)
        y = bitmap.set(x, 60, count=4)
        s = bitmap.string(x)
        if x == y and s.count('0') == 60 and s.count('1') == 4:
            raise Success

    @TestCase
    def set_bitmap_unsigned_1():
        x = bitmap.new(0xf000000000000000, 64)
        y, res = bitmap.shift(x, 4)
        if (res, 4) == (0xf, 4) and y == (0, 60):
            raise Success

    @TestCase
    def set_bitmap_unsigned_2():
        x = bitmap.new(0, 0)
        x = bitmap.push(x, (0x1, 4) )
        x = bitmap.push(x, (0x2, 4) )
        x = bitmap.push(x, (0x3, 4) )
        x = bitmap.push(x, (0x4, 4) )
        if bitmap.int(x) == 0x1234:
            raise Success

    @TestCase
    def set_bitmap_unsigned_3():
        x = bitmap.new(0, 0)
        x = bitmap.append(x, (0x1, 4) )
        x = bitmap.append(x, (0x2, 4) )
        x = bitmap.append(x, (0x3, 4) )
        x = bitmap.append(x, (0x4, 4) )
        if bitmap.int(x) == 0x4321:
            raise Success

    @TestCase
    def set_bitmap_unsigned_4():
        x = bitmap.consumer(b'\x12\x34')
        items = [x.consume(item) for item in 4*[4]]
        if items == [1,2,3,4]:
            raise Success

    @TestCase
    def set_bitmap_unsigned_5():
        x = bitmap.new(0, 4)
        for i in range(6):
            x = bitmap.add(x, 3)
        if x == ((6 * 3) % 0x10, 4):
            raise Success

    @TestCase
    def set_bitmap_unsigned_6():
        x = bitmap.new(2, 4)
        for i in range(6):
            x = bitmap.sub(x, 6)
        if x == (( 2 - 6 * 6) % 0x10, 4):
            raise Success

    @TestCase
    def set_bitmap_unsigned_7():
        x = bitmap.new(4, 4)
        y = bitmap.ror(bitmap.ror(bitmap.ror(x)))
        if bitmap.string(x) == '0100' and bitmap.string(y) == '1000':
            raise Success

    ### add
    @TestCase
    def signed_add_positive_wrap():
        x = bitmap.new(255, -8)
        res = bitmap.add(x, 1)
        if res == (0, -8) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def signed_add_positive_nowrap():
        x = bitmap.new(254, -8)
        res = bitmap.add(x, 1)
        if res == (255, -8) and bitmap.value(res) == -1:
            raise Success
    @TestCase
    def signed_add_negative_wrap():
        x = bitmap.new(254, -8)
        res = bitmap.add(x, 2)
        if res == (0, -8) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def signed_add_negative_nowrap():
        x = bitmap.new(250, -8)
        res = bitmap.add(x, 5)
        if res == (255, -8) and bitmap.value(res) == -1:
            raise Success

    ### sub
    @TestCase
    def signed_sub_positive_wrap():
        x = bitmap.new(5, -8)
        res = bitmap.sub(x, 10)
        if res == (251, -8) and bitmap.value(res) == -5:
            raise Success
    @TestCase
    def signed_sub_positive_nowrap():
        x = bitmap.new(10, -8)
        res = bitmap.sub(x, 5)
        if res == (5, -8) and bitmap.value(res) == 5:
            raise Success
    @TestCase
    def signed_sub_negative_nowrap():
        x = bitmap.new(156, -8)
        res = bitmap.sub(x, 10)
        if res == (146, -8) and bitmap.value(res) == -110:
            raise Success
    @TestCase
    def signed_sub_negative_wrap():
        x = bitmap.new(133, -8)
        res = bitmap.sub(x, 10)
        if res == (123, -8) and bitmap.value(res) == 123:
            raise Success

    ### grow
    @TestCase
    def grow_unsigned():
        x = bitmap.new(5, 4)
        res = bitmap.grow(x, 4)
        if res == (5 * pow(2, 4), 8) and bitmap.value(res) == 5 * pow(2, 4):
            raise Success
    @TestCase
    def grow_signed():
        x = bitmap.new(15, -4)
        res = bitmap.grow(x, 4)
        if res == (15 * pow(2, 4), -8) and bitmap.value(res) == -16:
            raise Success

    ### shrink
    @TestCase
    def shrink_unsigned():
        x = bitmap.new(0x50, 8)
        res = bitmap.shrink(x, 4)
        if res == (5, 4) and bitmap.value(res) == 5:
            raise Success
    @TestCase
    def shrink_signed():
        x = bitmap.new(0xff, -8)
        res = bitmap.shrink(x, 4)
        if res == (15, -4) and bitmap.value(res) == -1:
            raise Success

    ### push
    @TestCase
    def push_bitmap_unsigned():
        x = bitmap.new(15, 4)
        res = bitmap.push(x, (15, 4))
        if res == (0xff, 8) and bitmap.value(res) == 255:
            raise Success
    @TestCase
    def push_bitmap_signed():
        x = bitmap.new(15, -4)
        res = bitmap.push(x, (15, 4))
        if res == (0xff, -8) and bitmap.value(res) == -1:
            raise Success

    ### consume
    @TestCase
    def consume_unsigned_bitmap_unsigned():
        x = bitmap.new(0x41424344, 32)
        res, n = bitmap.consume(x, 8)
        if n == 0x44 and res == (0x414243, 24):
            raise Success
    @TestCase
    def consume_signed_bitmap_unsigned():
        x = bitmap.new(0x414243ff, 32)
        res, n = bitmap.consume(x, 8)
        if n == 0xff and res == (0x414243, 24):
            raise Success
    @TestCase
    def consume_unsigned_bitmap_signed():
        x = bitmap.new(0x41424344, -32)
        res, n = bitmap.consume(x, 8)
        if n == 0x44 and res == (0x414243, -24):
            raise Success
    @TestCase
    def consume_signed_bitmap_signed():
        x = bitmap.new(0x414243ff, -32)
        res, n = bitmap.consume(x, 8)
        if n == -1 and res == (0x414243, -24):
            raise Success
    @TestCase
    def consume_zero_bitmap_unsigned():
        x = bitmap.new(0x41424344, 32)
        res, n = bitmap.consume(x, 0)
        if n == 0 and res == x:
            raise Success
    @TestCase
    def consume_zero_bitmap_signed():
        x = bitmap.new(0x41424344, -32)
        res, n = bitmap.consume(x, 0)
        if n == 0 and res == x:
            raise Success
    @TestCase
    def consume_empty_bitmap():
        x = bitmap.zero
        res, n = bitmap.consume(x, 8)
        if n == 0 and res == x:
            raise Success

    ### shift
    @TestCase
    def shift_unsigned_bitmap_unsigned():
        x = bitmap.new(0x41424344, 32)
        res, n = bitmap.shift(x, 8)
        if n == 0x41 and res == (0x424344, 24):
            raise Success
    @TestCase
    def shift_signed_bitmap_unsigned():
        x = bitmap.new(0xff424344, 32)
        res, n = bitmap.shift(x, 8)
        if n == 0xff and res == (0x424344, 24):
            raise Success
    @TestCase
    def shift_unsigned_bitmap_signed():
        x = bitmap.new(0x41424344, -32)
        res, n = bitmap.shift(x, 8)
        if n == 0x41 and res == (0x424344, -24):
            raise Success
    @TestCase
    def shift_signed_bitmap_signed():
        x = bitmap.new(0xff424344, -32)
        res, n = bitmap.shift(x, 8)
        if n == -1 and res == (0x424344, -24):
            raise Success
    @TestCase
    def shift_zero_bitmap_unsigned():
        x = bitmap.new(0x41424344, 32)
        res, n = bitmap.shift(x, 0)
        if n == 0 and res == (0x41424344, 32):
            raise Success
    @TestCase
    def shift_zero_bitmap_signed():
        x = bitmap.new(0x41424344, -32)
        res, n = bitmap.shift(x, 0)
        if n == 0 and res == (0x41424344, -32):
            raise Success
    @TestCase
    def shift_empty_bitmap():
        x = bitmap.zero
        res, n = bitmap.shift(x, 8)
        if n == 0 and res == (0, 0):
            raise Success

    ### mul
    @TestCase
    def mul_unsigned_bitmap_unsigned():
        x = bitmap.new(0x40000000, 32)
        res = bitmap.mul(x, 4)
        if res == (0, 32) and bitmap.value(res) == 0:
            raise Success
    @TestCase
    def mul_unsigned_bitmap_signed():
        x = bitmap.new(0x40000000, 32)
        res = bitmap.mul(x, -4)
        if res == (0, 32) and bitmap.value(res) == 0:
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
        x = bitmap.new(0x10000000, 32)
        res = bitmap.div(x, 0x10)
        if bitmap.value(res) == 0x1000000:
            raise Success
    @TestCase
    def div_unsigned_bitmap_signed():
        '''0x10 / -0x10 = -1'''
        x = bitmap.new(0x10, -32)
        res = bitmap.div(x, -0x10)
        if bitmap.value(res) == -1:
            raise Success
    @TestCase
    def div_signed_bitmap_signed_1():
        x = bitmap.new(0xffffffffffffa251, -64)
        res = bitmap.div(x, 0xc1)
        if bitmap.value(res) == -125:
            raise Success
    @TestCase
    def div_signed_bitmap_signed_2():
        x = bitmap.new(0xffffffffffff1634, -64)
        res = bitmap.div(x, 0xad)
        if bitmap.value(res) == -346:
            raise Success

    @TestCase
    def div_signed_bitmap_unsigned():
        '''-0x10/-0x10 = 1'''
        x = bitmap.new(0xfffffffffffffff0, -64)
        res = bitmap.div(x, -0x10)
        if bitmap.value(res) == 1:
            raise Success

    ### mod
    @TestCase
    def mod_unsigned_bitmap_unsigned():
        '''23983 % 5 == 3'''
        mask = pow(2, 64) - 1
        x = (23983 & mask, 64)
        res = bitmap.mod(x, 5)
        if bitmap.value(res) == 3:
            raise Success
    @TestCase
    def mod_unsigned_bitmap_signed():
        '''23983 % -5 == -2'''
        mask = pow(2, 64) - 1
        x = (23983 & mask, -64)
        res = bitmap.mod(x, -5)
        if bitmap.signed(res) and bitmap.value(res) == -2:
            raise Success
    @TestCase
    def mod_signed_bitmap_unsigned():
        '''-23983 % -5 == 2'''
        mask = pow(2, 64) - 1
        x = (-23983 & mask, 64)
        res = bitmap.mod(x, -5)
        if bitmap.value(res) == 0xfffffffffffffffe:
            raise Success

    @TestCase
    def mod_signed_bitmap_signed():
        '''-23983 % -5 == -3'''
        mask = pow(2, 64) - 1
        x = (-23983 & mask, -64)
        res = bitmap.mod(x, -5)
        if bitmap.signed(res) and bitmap.value(res) == -3:
            raise Success

    @TestCase
    def data_padding():
        res = bitmap.new(0x123, 12)
        data = bitmap.data(res, reversed=0)
        if tohex(data) == '1230':
            raise Success

    @TestCase
    def data_padding_reversed():
        res = bitmap.new(0x123, 12)
        data = bitmap.data(res, reversed=1)
        if tohex(data) == '3012':
            raise Success

    @TestCase
    def bitmap_rol1_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.rol(res, 1)) == 4:
            raise Success

    @TestCase
    def bitmap_ror1_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.ror(res, 1)) == 4:
            raise Success

    @TestCase
    def bitmap_rol4_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.rol(res, 4)) == 4:
            raise Success

    @TestCase
    def bitmap_ror4_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.ror(res, 4)) == 4:
            raise Success

    # FIXME
    def bitmap_rolX_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.rol(res, 8)) == 4:
            raise Success

    # FIXME
    def bitmap_rorX_size():
        res = bitmap.new(0b0110, 4)
        if bitmap.size(bitmap.ror(res, 8)) == 4:
            raise Success

    @TestCase
    def bitmap_rol1_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.rol(res, 1)) == 0b1100:
            raise Success

    @TestCase
    def bitmap_ror1_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.ror(res, 1)) == 0b0011:
            raise Success

    @TestCase
    def bitmap_rol2_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.rol(res, 2)) == 0b1001:
            raise Success

    @TestCase
    def bitmap_ror2_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.ror(res, 2)) == 0b1001:
            raise Success

    @TestCase
    def bitmap_rol4_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.rol(res, 4)) == 0b0110:
            raise Success

    @TestCase
    def bitmap_ror4_value():
        res = bitmap.new(0b0110, 4)
        if bitmap.int(bitmap.ror(res, 4)) == 0b0110:
            raise Success

    @TestCase
    def consumer_consume1_8():
        data = b'\x80'
        valid = [1, 0, 0, 0, 0, 0, 0, 0]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            res.append(bc.consume(1))

        if res == valid:
            raise Success

    @TestCase
    def consumer_consume4_2():
        data = b'\xa0'
        valid = [0xa, 0x0]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            res.append(bc.consume(4))

        if res == valid:
            raise Success

    @TestCase
    def consumer_consume8_1():
        data = b'\xa0'
        valid = [0xa0]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            res.append(bc.consume(8))

        if res == valid:
            raise Success

    @TestCase
    def consumer_consume16_1():
        data = b'\xa5\xa5'
        valid = [0xa5a5]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            res.append(bc.consume(16))

        if res == valid:
            raise Success

    @TestCase
    def consumer_consume4_4():
        data = b'\xa5\xa5'
        valid = [0xa, 0x5, 0xa, 0x5]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            item = bc.consume(4)
            res.append(item)

        if res == valid:
            raise Success

    @TestCase
    def consumer_consumeiterable():
        data = bytes(bytearray([0xa5, 0xa5]))
        valid = [0xa, 0x5, 0xa, 0x5]

        bc = bitmap.consumer(data)
        res = []
        while len(res) < len(valid):
            item = bc.consume(4)
            res.append(item)

        if res == valid:
            raise Success

    @TestCase
    def bitmap_entropy_1():
        integer = 0b1010010110100101
        res = bitmap.new(integer, 16)
        if bitmap.shannon(res) == 1.0:
            raise Success

    @TestCase
    def bitmap_entropy_2():
        integer = 0b0000000000000000
        res = bitmap.new(integer, 16)
        if bitmap.shannon(res) == 0.0:
            raise Success
    @TestCase
    def bitmap_entropy_3():
        integer = 0b1111111111111111
        res = bitmap.new(integer, 16)
        if bitmap.shannon(res) == 0.0:
            raise Success

    @TestCase
    def rbitmap_consume_0():
        x = bitmap.RBitmap(b'\x2d')
        items = [x.consume(item) for item in [2, 3, 3]]
        if x.size() == 0 and items == [0, 5, 5]:
            raise Success

    @TestCase
    def rbitmap_consume_1():
        x = bitmap.RBitmap(b'\x15')
        items = [x.consume(item) for item in [2, 3]]
        if x.size() == 3 and items == [0, 2]:
            raise Success

    @TestCase
    def rbitmap_consume_2():
        x = bitmap.RBitmap(b'\xdf')
        if x.size() == 8 and x.consume(1) == 1 and x.consume(3) == 5 and x.consume(4) == 15:
            raise Success

    @TestCase
    def wbitmap_push_0():
        x = bitmap.WBitmap(b'\x2d')
        if x.size() == 8 and x.int() == 0x2d:
            raise Success

    @TestCase
    def wbitmap_push_1():
        x = bitmap.WBitmap()
        x.push(0xf, 4)
        if x.size() == 4 and x.int() == 0xf:
            raise Success

    @TestCase
    def wbitmap_push_2():
        x = bitmap.WBitmap()
        x.push(0x1, 4)
        x.push(0x2, 4)
        x.push(0x3, 4)
        x.push(0x4, 4)
        if x.size() == 16 and x.serialize() == b'\x12\x34':
            raise Success

    @TestCase
    def bits_reverse_1():
        import random
        size = 0x400
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse((x, size))
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

    @TestCase
    def bits_reverse_2():
        import random
        size = random.randint(0x400, 0x800)
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse((x, size))
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

    @TestCase
    def bits_reverse_3():
        import random
        size = 0x400
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse_bits(x, size)
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

    @TestCase
    def bits_reverse_4():
        import random
        size = random.randint(0x400, 0x800)
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse_bits(x, size)
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

    @TestCase
    def bits_reverse_5():
        import random
        size = 29
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse((x, size))
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

    @TestCase
    def bits_reverse_6():
        import random
        size = 29
        x = random.getrandbits(size)
        expected = "{:0{:d}b}".format(x, size)[::-1]
        y, size = bitmap.reverse_bits(x, size)
        result = "{:0{:d}b}".format(y, size)
        if expected == result:
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
