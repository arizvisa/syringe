import sys,os
import ptypes,office.storage

if __name__ == '__main__':
    if len(sys.argv) > 1:
        path, = sys.argv[1:]
        source = ptypes.prov.file(path,mode='r')
    else:
        print('Usage: {:s} file'.format(sys.argv[0]))
        sys.exit(1)
    z = office.storage.File(source=source)
    z = z.l
    directory = z.getDirectory()
    print(repr(directory))
