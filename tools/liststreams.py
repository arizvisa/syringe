import sys,os
import ptypes,office.storage

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {:s} file'.format(sys.argv[0]))
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        raise OSError("The specified file ({:s}) does not exist.".format(sys.argv[1]))

    path, = sys.argv[1:]
    source = ptypes.prov.file(path, mode='r')
    z = office.storage.File(source=source)
    z = z.l
    D = z.Directory()
    df, f, mf = z.DiFat(), z.Fat(), z.MiniFat()
    print(repr(D))
