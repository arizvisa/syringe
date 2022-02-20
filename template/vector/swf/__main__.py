import sys
if __name__ == '__main__':
    import sys
    import ptypes,vector.swf as swf
    ptypes.setsource(ptypes.provider.file(sys.argv[1], mode='rb'))

    a = swf.File()
    a = a.l
    z = a['data'].d
    z = z.l
    for x in z['tags']:
        print('-'*32)
        print(x)

    #a = z['data']['tags'][0]
    #print(a.hexdump())
    #print(a.li.hexdump())
    #print(repr(a.l['Header'].serialize()))

    #correct=b'\x44\x11\x08\x00\x00\x00'
    #print(ptypes.utils.hexdump(correct))

    #print(a.serialize() == correct)

