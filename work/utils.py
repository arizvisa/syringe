import ctypes
k32 = ctypes.WinDLL('kernel32.dll')

def printable(s):
    '''
    return a string of only printable characters
    '''
    r = ''
    for c in s:
        if ord(c) >= 32 and ord(c) < 127:
            r += c
        else:
            r += '.'

    return r

def hexrow(value, offset=0, length=16, breaks=[8]):
    '''
    return a formatted hexrow. guaranteed to always return the same length string...i hope.
    '''
    value = str(value)[:length]
    extra = length - len(value)

    ## left
    left = '%04x'% offset

    ## middle
    res = [ '%02x'%ord(x) for x in value ]
    if len(value) < length:
        res += ['  ' for x in range(extra)]

    for x in breaks:
        if x < len(res):
            res[x] = ' %s'% res[x]
    middle = ' '.join(res)

    ## right
    right = printable(value) + ' '*extra

    return '%s  %s  %s'% (left, middle, right)

def hexdump(value, offset=0, length=16, **kwds):
    '''
    return a formatted hexdump
    logic _not_ ripped from scapy.py
    '''
    value = iter(value)

    def tryRead(iterable, length):
        res = ''
        try:
            for i,x in zip(xrange(length), iterable):
                res += x

        except StopIteration:
            pass
        return res

    getRow = lambda o: hexrow(data, offset=o, **kwds)
    res = []
    (ofs, data) = offset, tryRead(value, length)
    while len(data) == length:
        res.append( getRow(ofs) )
        ofs, data = (ofs + length, tryRead(value, length))

    if len(data) > 0:
        res.append( getRow(ofs) )
    return '\n'.join(res)

def getLastErrorTuple():
    errorCode = k32.GetLastError()
    p_string = ctypes.c_void_p(0)

    # FORMAT_MESSAGE_
    ALLOCATE_BUFFER = 0x100
    FROM_SYSTEM = 0x1000
    res = k32.FormatMessageA(
        ALLOCATE_BUFFER | FROM_SYSTEM, 0, errorCode,
        0, ctypes.pointer(p_string), 0, None
    )
    res = ctypes.cast(p_string, ctypes.c_char_p)
    errorString = str(res.value)
    res = k32.LocalFree(res)
    assert res == 0, "kernel32!LocalFree failed. Error 0x%08x."% k32.GetLastError()

    return (errorCode, errorString)

def getLastErrorString():
    code, string = getLastErrorTuple()
    return string

