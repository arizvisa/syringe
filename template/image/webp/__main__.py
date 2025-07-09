import builtins, operator, os, math, functools, itertools, sys, types

if __name__ == '__main__':
    import sys
    import ptypes, image.webp as webp

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='rb'))

    z = webp.File()
    z = z.l
    print(z.size() == z.source.size(), z.size(), z.source.size())

    print(z)

    sys.exit(0 if z.size() == z.source.size() else 1)
