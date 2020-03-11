import sys,os
import string,cgi,time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import mimetypes

class config:
    root = [
#        ('/', ('./index.html', 'text/html')),
#        ('/', ('./', 'text/html')),
#        ('/sample.dir', ('./sample.dir', 'application/x-shockwave-flash')),
#        ('/test.dir', ('./test.dir', 'application/x-shockwave-flash')),
        ('/', ('goatse.cx.jpg', 'image/jpeg')),
    ]

def getfiledata(filename,mime):
    def l(q):
        f = file(filename, 'rb')
        res = f.read()
        f.close()
        return res,mime
    return l

def listdirectory(baseuri, path):
    assert baseuri.endswith('/')
    def row(*args):
        return '<tr>%s</tr>'%( ''.join(('<td>%s</td>'%x for x in args)) )

    def l(q):
        result = ['<table>']
        result.append( row(*['<i>%s</i>'%x for x in ('path','size','created','modified')]) )
        result.append( row( '<a href="%s../">..</a>'% baseuri) )
        for name in find(path, root=path, depth=0):
            contents = name.replace(os.sep, '/')
            uri = '%s%s'% (baseuri, contents)
            _,_,_,_,_,_,sz,at,mt,ct = os.stat('%s%s'%(path,name))
            result.append( row('<a href="%s">%s</a>'%(uri,contents), str(sz), time.ctime(ct),time.ctime(mt)) )
        return ''.join(result),'text/html'
    return l

def find(path='.'+os.sep, depth=None, root='.'+os.sep):
    if type(depth) in (int,long):
        if depth < 0:
            return
        depth -= 1

    for name in os.listdir(path):
        fullpath = os.path.relpath(os.path.join(path, name), start=root)
        if os.path.isdir(root+fullpath):
            yield fullpath + os.sep
            for x in find(root+fullpath, depth, root=root):
                yield x
            continue
        yield fullpath
    return

class fileserver(BaseHTTPRequestHandler):
    filesystem = None   # dict
    root = config.root
    def __init__(self, *kwds, **args):
        self.init_filesystem()
        BaseHTTPRequestHandler.__init__(self, *kwds, **args)

    def init_filesystem(self):
        self.filesystem = {}

        for path,loc in self.root:
            if not isinstance(loc, tuple):
                self.filesystem[path] = loc
                continue
            if path.endswith('/') and loc[0][-1] in (os.sep,'/'):
                directory,options = loc
                self.add_directory(path, directory)
                continue
            filename,mime = loc
            self.add_file(path, filename, mime)
        return

    def add_file(self, key, path, mime):
        if mime is None:
            (mime,encoding) = mimetypes.guess_type(path)
        self.filesystem[key] = getfiledata(path, mime)

    def add_directory(self, key, path):
        assert key.endswith('/')
        directory = path.replace('/', os.sep)
        assert directory.endswith(os.sep)

        for x in find(directory, root=directory, depth=0):
            uri = key + x.replace(os.sep, '/')
            fullpath = path+x

            if x.endswith(os.sep):
                self.add_directory(uri, fullpath)
                continue
            self.filesystem[uri] = getfiledata(fullpath, mimetypes.guess_type(x))

        self.filesystem[key] = listdirectory(key, directory)

    def send_contents(self, data, mime):
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path,query=self.path,''
        if '?' in self.path:
            path,query = self.path.split('?', 1)

        try:
            data = self.filesystem[path]
        except KeyError:
            self.send_error(404, 'File not found: %s'% self.path)
            return

        contents,mime = data(query)
        self.send_contents(contents, mime)

if __name__ == '__main__':
    host, port = sys.argv[1].split(':')
    port = int(port)
    httpd = HTTPServer((host,port), fileserver)

    print 'bound to %s:%d'% (host,port)
    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        pass
