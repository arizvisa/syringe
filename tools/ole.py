import sys,os.path,inspect

__file__ = os.path.abspath(inspect.getfile(inspect.currentframe()))
sys.path.append('%s/lib'% os.path.dirname(__file__))
sys.path.append('%s/template'% os.path.dirname(__file__))

def log(s, *fmt):
    string = s%fmt
    sys.stderr.write(string + "\n")

def liststreams(paths):
    from office.OleFileIO_PL import OleFileIO

    result = {}
    for filename in paths:
        if not os.path.exists(filename):
            log('%s : file not found',filename)
            continue
        try:
            ole = OleFileIO(filename)
        except IOError,msg:
            log('%s : not an ole file : %s',filename,msg)
            continue
        streams = ['/'.join(x) for x in ole.listdir()]

        for x in streams:
            if x not in result:
                result[x] = 0
            result[x] += 1
        continue

    result = result.items()
    result.sort(lambda a,b:cmp(a[1],b[1]))
    print '\n'.join('%d : %s'%(v,repr(k)) for k,v in result)

def dumpstreams(stream, paths, out):
    from office.OleFileIO_PL import OleFileIO

    stream = stream.split('/')

    out = out if out.endswith('/') else '%s/'%out
    if not os.path.exists(out):
        raise OSError('path "%s" not found'% out)

    for filename in paths:
        if not os.path.exists(filename):
            log('%s : file not found',filename)
            continue

        try:
            ole = OleFileIO(filename)
        except IOError,msg:
            log('%s : not an ole file : %s',filename,msg)
            continue

        if stream not in ole.listdir():
#            log('%s : stream "%s" not found'%(filename, repr(stream)))
            continue

        name = '%s.stream'%(os.path.basename(filename))
        path = '%s%s'%(out,name)
        log('%s : writing stream "%s"'%(filename, path))
        try:
            stm = ole.openstream(stream)
        except IOError, msg:
            log('%s : stream %s error : %s', filename,stream,msg)
            continue

        file(path,'wb').write(stm.read())
    return

if __name__ == '__main__':
    import glob,argparse

    argh = argparse.ArgumentParser(description='list and extract streams from any compound document files')
    argh.add_argument('file', nargs='*')
    argh.add_argument('-name', metavar='STREAMNAME', action='store', nargs=1, help='specify the streamname to extract')
    m = argh.add_mutually_exclusive_group(required=True)
    m.add_argument('-list', action='store_true', default=None, help='list all streams in files')
    m.add_argument('-extract', metavar='PATH', action='store', nargs=1, default=None, help='extract the STREAMNAME from files to PATH')
    _ =argh.parse_args()

    result = []
    for x in map(glob.iglob, _.file):
        result.extend(x)
    paths = result

    if _.list:
        liststreams(paths)
    elif _.extract:
        streamname = eval('"%s"'% _.name[0])
        target, = _.extract
        dumpstreams(streamname, paths, target)
    else:
        assert False

