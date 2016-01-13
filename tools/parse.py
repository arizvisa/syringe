import time,sys,os.path,inspect,traceback

__file__ = os.path.abspath(inspect.getfile(inspect.currentframe()))
sys.path.append('%s/lib'% os.path.dirname(__file__))
sys.path.append('%s/template'% os.path.dirname(__file__))

import ptypes

def log(s, *fmt):
    string = s%fmt
    sys.stderr.write(string + "\n")

def getparser(path):
    return __import__(path,globals(),locals(),['File'],-1).File

def iterfiles(parser, paths):
    parser_name = '%s.%s'% (parser.__module__, parser.__name__)
    for i,filename in enumerate(paths):
        source = ptypes.file(filename,mode='r')
        p = parser(source=source)
        log(': %d : %s : %s : parsing...',i+1,parser_name,filename)
        t1 = time.time()
        try:
            p=p.l
        except:
            t2 = time.time()
            exception = traceback.format_exc()

            log(': %d : %s : %s : failure while parsing : %f : %s',i+1,parser_name,filename,t2-t1,exception)
            yield filename,p
            continue

        t2 = time.time()
        if p.initialized:
            log(': %d : %s : %s : completed : %f',i+1,parser_name,filename,t2-t1)
        else:
            log(': %d : %s : %s : completed partially: %f',i+1,parser_name,filename,t2-t1)
        yield filename,p
    return

def reprfiles(*args):
    print '--- parsing %d paths'% len(paths)
    for i,(filename,p) in enumerate(iterfiles(*args)):
        w = 79
        a = '-- {} '.format(i+1)
        b = '{:->%ds}'%(w-len(a))
        c = a+b.format(' %s'%(filename))
        print c

        print ptypes.utils.indent(p.repr())
        if isinstance(p, ptypes.parray.type):
            rows = ('%s %s'%(x.initialized,x.repr()) for x in p)
            print ptypes.utils.indent('\n'.join(rows),tabsize=8)
        print '='*79
        continue
    print '--- completed parsing of %d files'% i

def histogram_parser(parser,state={}):
    result = {}
    for n in parser.traverse(edges=lambda s:() if s.v is None else s.v, filter=lambda s: hasattr(s,'type')):
        name = n.shortname()
        if name not in result:
            result[name] = 0
        result[name] += 1

        if name not in state:
            state[name] = []
        state[name].append(n)
    return result

def histogram(*args):
    global result,state
    result = {}
    state = {}
    for i,(filename,p) in enumerate(iterfiles(*args)):
        _ = histogram_parser(p,state)
        for k,v in _.iteritems():
            if k in result:
                result[k] += _[k]
                continue
            result[k] = _[k]
        continue

    result = result.items()
    result.sort(lambda x,y:cmp(x[1],y[1]))
    print '='*79
    print '{:=>79s}'.format(' frequency results for %d files'%( len(paths) ))
    for x,count in result:
        print '%s %s'%(x,count)
    return

if __name__ == '__main__':
    import glob,argparse
    argh = argparse.ArgumentParser(description='run the provided parser over a list of files')
    argh.add_argument('file', nargs='*')
    argh.add_argument('-name', metavar='PARSER', required=1, action='store', nargs=1, help='specify the parser to use')
    m = argh.add_mutually_exclusive_group(required=True)
    m.add_argument('-repr', action='store_true', default=None, help='print a repr of all files')
    m.add_argument('-hist', action='store_true', default=None, help='print a histogram of all typed records in files')
    _ =argh.parse_args()

    result = []
    for x in map(glob.iglob, _.file):
        result.extend(x)
    paths = result

    parser = getparser(_.name[0])

    if _.repr:
        reprfiles(parser, paths)
    elif _.hist:
        histogram(parser, paths)
    else:
        assert False

