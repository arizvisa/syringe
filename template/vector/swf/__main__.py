import sys
if __name__ == '__main__':
    import sys
    import ptypes,vector.swf as swf
    ptypes.setsource(ptypes.provider.file(sys.argv[1], mode='rb'))

    z = swf.File()
    z = z.l
    a = z['data'].d
    a = a.l
    tags = a['tags']
    print(tags)
    sys.exit(0)

