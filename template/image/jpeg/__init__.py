import sys, itertools, functools

__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

intofdata = lambda data: functools.reduce(lambda t, c: t * 256 | c, bytearray(data), 0)
dataofint = lambda integer: ((integer == 0) and b'\0') or (dataofint(integer // 256).lstrip(b'\0') + bytes(bytearray([integer % 256])[:1]))

from . import jp2, jfif

if __name__ == '__main__':
    #input = getFileContents('Q100-2.JPG')
    input = getFileContents('huff_simple0.jpg')
    input = bytes(input.replace(b'\xff\x00', b'\xff'))
    jpegfile = Jpeg()
    jpegfile.deserialize(input)
    lookup = {type(item).__name__ : item for item in jpegfile}

    print(jpegfile[0])
    print(jpegfile[1])

#    print('\n'.join([repr(x) for x in jpegfile]))
#    dqt = lookup['DQT']['table']
#    dht = lookup['DHT']['table']
#    sosdata = lookup['SCANDATA']
#    print(repr(dqt))
#    print(repr(dht))
#    print(repr(sosdata))
#    print('\n'.join([repr(x) for x in dht]))
#    print('\n'.join([repr(x) for x in dqt]))

    ### load_quant_table
    zigzag = [
        0, 1, 5, 6,14,15,27,28,
        2, 4, 7,13,16,26,29,42,
        3, 8,12,17,25,30,41,43,
        9,11,18,24,31,40,44,53,
       10,19,23,32,39,45,52,54,
       20,22,33,38,46,51,55,60,
       21,34,37,47,50,56,59,61,
       35,36,48,49,57,58,62,63
    ]

    scalefactor = [
        1.0, 1.387039845, 1.306562965, 1.175875602,
        1.0, 0.785694958, 0.541196100, 0.275899379
    ]

    self = lookup['DQT']['table'][0]
    quantizationTable = [ord(x) for x in self['value'].serialize()]
    res = []
    table = iter(quantizationTable)
    for y in range(8):
        for x in range(8):
            res.append( table.next() * scalefactor[y] * scalefactor[x] )

    scaledQuantizationTable = res

    ### decode_huffman ->
    ###     decode AC coefficient
    ###     decode DC coefficient

    ## process dht table
    self = lookup['DHT']['table'][3]
    print(repr(self))

    ### process scan data
    self = lookup['SOS']
    print(repr(self))
    print(self['component'][0])

    self = lookup['SOF']
    self = lookup['SOS']

if __name__ == '__main__':
    import sys
    import ptypes,image.jpeg as jpeg
    ptypes.setsource( ptypes.file(sys.argv[1]) )

    z = jpeg.File()
    z = z.l
