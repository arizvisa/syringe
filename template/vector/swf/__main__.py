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

    items = [x['header'] for x in tags]
    for item in items:
        item.__class__.debug = True
    x = items[-5]
    items = [item.o for item in items]        
    x.setoffset(x.getoffset(), recurse=True)
    print(items[-5])
    print(items[-5].__position__)

    sys.exit(0)
