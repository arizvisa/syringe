isprint = lambda ch: (ord(ch) > 32 and (ord(ch)&0x7f == ch or True))

def hexify(data):
    return ['%02x'%ord(value) for value in data]

def header(length, separator='  '):
    res = '0123456789abcdefghijklmnopqrstuvwxyzyaywootheh..ok.'[:length]
    return separator.join(list(res))

def _hexdump(iterable, address=0, columns=16):
    iterable = iter(iterable)

    try:
        while True:
            data = []
            for x in xrange(columns):
                data.append( iterable.next() )

            row = ''
            row+='%8x: '% address
            row+= ' '.join( hexify(data) )
            row+= ' | '
            row+= ''.join([ ['.', ch][isprint(ch)] for ch in data])

            address += len(data)
            yield row

    except StopIteration:
        width = len(' '.join(['00' for x in range(columns)]))
        col = []
        col.append('%8x:'% address)
        col.append(' '.join(hexify(data)))
        col.append(''.join([ ['.', ch][isprint(ch)] for ch in data]))
        yield '%s %s | %s'%( col[0], col[1].ljust(width,' '), col[2].ljust(columns, ' '))

def hexdump(iterable, address=0):
    '''
    return a hexdump beginning at address specified
    '''
    iterable = iter(iterable)
    columns = 16
    col1_length = len('00000000: ')
    col1 = ",.-~'``'-"
    col1 = "/"*(col1_length-1)
    col1 = " "*(col1_length-1)

    res = []
    s = '%s %s | %s'%( col1.ljust(col1_length), header(columns), header(columns, ''))
    res.append(s)
    res.extend(_hexdump(iterable, address))
    return '\n'.join(res)

if __name__ == '__main__':
    print(hexify('hello world'))

    print(header(16,''))
    print('\n'.join(_hexdump(iter('hello world'), 0xfeeddead, 4)))

    print(hexdump('hello world, hehehehehhh...okayyyyy....i suck at writing testss....w.oooot....', address=0x0d0e0a0d))
