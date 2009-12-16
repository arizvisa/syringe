#bitmap = (integer, bits)
import sys

def new(size):
    '''creates a new bitmap object'''
    return (0, size)

def empty(bitmap):
    integer,size = bitmap
    return not(integer > 0)

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

def get(bitmap, position, count=1):
    '''fetch /count/ number of bits from /bitmap/ starting at /position/'''
    assert count >= 0 and position >= 0

    integer, size = bitmap
    mask = reduce(lambda r,v: 1<<v | r, range(position, position+count), 0)
    return ((integer & mask) >> position, count)

def grow(bitmap, count):
    assert count >= 0
    integer,size = bitmap
    return (integer << count, size + count)

def shrink(bitmap, count):
    assert count >= 0
    integer,size = bitmap
    return (integer >> count, size - count)

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
