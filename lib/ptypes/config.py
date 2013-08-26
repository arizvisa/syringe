## byteorder options
class byteorder:
    class bigendian(object): pass
    class littleendian(object): pass
    bigendian=bigendian()
    littleendian=littleendian()

## integer sizes
import sys,math
class integer:
    wordsize = 0
    byteorder = None

integer.wordsize = long(math.log((sys.maxsize+1)*2, 2) / 8)
if sys.byteorder == 'little':
    integer.byteorder = byteorder.littleendian
elif sys.byteorder == 'big':
    integer.byteorder = byteorder.bigendian
else:
    assert False is True, sys.byteorder

## output
class summary:
    oneline = 0x20
    multiline = 0x8

