import functools, operator, os, types, sys, itertools
import datetime, cgi, time
import six, mimetypes
WIN32 = True if sys.platform == 'win32' else False

try:
    # Python3
    from http.server import BaseHTTPRequestHandler, HTTPServer

except ImportError:
    # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


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
        f = open(filename, 'rb')
        res = f.read()
        f.close()
        return res, mime
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
        return ''.join(result).encode('latin1'),'text/html'
    return l

def find(path='.'+os.sep, depth=None, root='.'+os.sep):
    if isinstance(depth, six.integer_types):
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

def parse_args():
    import argparse
    res = argparse.ArgumentParser(description='Serve up some explicit files over the HTTP protocol and its derivatives')
    res.add_argument('-ssl', dest='use_ssl', action='store_true', default=False, help='Use SSL when binding to requested port.')

    ssl = res.add_argument_group('available ssl options', description='Options available when binding to a port with SSL.')
    ssl.add_argument('-key', dest='keyfile', metavar='FILE', action='store', help='Use the specified key when serving SSL (generate one if none specified)')
    ssl.add_argument('-keysize', dest='keysize', metavar='BITS', default=1024, action='store', help='Use the specified number of bits when generating the key')
    ssl.add_argument('-keyout', dest='keypath', metavar='PATH', action='store', help='Write the key that is used to the path that is specified')

    ssl.add_argument('-cert', dest='certificate', metavar='FILE', action='store', help='Use the specified x509 certificate when serving SSL (self-sign one using key if none specified)')
    ssl.add_argument('-param', dest='parameters', metavar=('ATTRIBUTE', 'VALUE'), action='append', nargs=2, help='Use the specified parameters (attribute name = attribute value) when generating the x509 certificate')
    ssl.add_argument('-certout', dest='certificatepath', metavar='PATH', action='store', help='Write the certificate that is used to the path that is specified')

    res.add_argument(dest='hostport', metavar='host:port', action='store')
    return res.parse_args()

def gen_key(e=65537, bits=1024):
    import cryptography.hazmat.primitives.asymmetric.rsa as chpar
    import cryptography.hazmat.primitives.serialization as chps
    import cryptography.hazmat.backends as chb

    print("generating an RSA key of {:d}-bit{:s} using e={:d}.".format(bits, '' if bits == 1 else 's', e))
    key = chpar.generate_private_key(public_exponent=e, key_size=bits, backend=chb.default_backend())
    pem = key.private_bytes(encoding=chps.Encoding.PEM, format=chps.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=chps.NoEncryption())

    return key, pem

def load_key(content, password=None):
    import cryptography.hazmat.primitives.serialization as chps
    import cryptography.hazmat.backends as chb

    print("loading RSA key from {:d} bytes worth of file.".format(len(content)))
    try:
        key = chps.load_pem_private_key(data=content, password=password, backend=chb.default_backend())

    except ValueError:
        print('critical: error while decoding key, generating a temporary one instead.\n')
        return gen_key()

    except TypeError:
        pass

    else:
        pem = key.private_bytes(encoding=chps.Encoding.PEM, format=chps.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=chps.NoEncryption())
        return key, pem

    try:
        password = input("key is encrypted, please type in your password (ctrl+c to give up): ")

    except KeyboardInterrupt:
        print("warning: user aborted key decryption, generating a temporary one instead.\n")
        return gen_key()
    return load_key(content, password)

def gen_certificate(private, **params):
    from datetime import datetime as delirium_tremens

    now = delirium_tremens.utcnow()
    params.setdefault('serial_number', 1024)
    params.setdefault('not_valid_before', now)
    params.setdefault('not_valid_after', params['not_valid_before'] + datetime.timedelta(days=42))
    params.setdefault('hashAlgorithm', 'sha256')

    import cryptography.x509 as X
    import ipaddress as inet

    hostname = os.environ.get('HOSTNAME', 'localhost')
    cn = X.Name([X.NameAttribute(X.oid.NameOID.COMMON_NAME, hostname)])
    params['subject_name'] = cn
    params.setdefault('issuer_name', cn)

    global host, port
    address = inet.ip_address(host)
    alts = [token(item) for token, item in zip([X.DNSName, X.IPAddress], [host, address])]
    an = X.SubjectAlternativeName(alts)

    bc = X.BasicConstraints(ca=True, path_length=0)

    import cryptography.hazmat.primitives as chp
    namespace = map(functools.partial(getattr, chp.hashes), dir(chp.hashes))
    algorithm_types = (item for item in namespace if isinstance(item, type))
    algorithms = {cons.name : cons for cons in algorithm_types if issubclass(cons, chp.hashes.HashAlgorithm) and cons is not chp.hashes.HashAlgorithm}
    suggestion = params.pop('hashAlgorithm')
    if operator.contains(algorithms, suggestion):
        hashAlgorithm = algorithms[suggestion]

    else:
        print("critical: suggested hash algorithm ({:s}) was not found in the available algoritms ({:s}).".format(suggestion, ', '.join(sorted(algorithms))))
        hashAlgorithm = algorithms[next(name for name in itertools.chain(['sha1', 'md5'], algorithms) if operator.contains(algorithms, name))]
        print("warning: ended up falling back to an alternative one ({:s}).\n".format(hashAlgorithm.name))

    import cryptography.hazmat.backends as chb
    import cryptography.hazmat.primitives as chp

    params['issuer_name'] = X.Name([X.NameAttribute(X.oid.NameOID.COMMON_NAME, params['issuer_name'])]) if isinstance(params['issuer_name'], six.string_types) else params['issuer_name']
    print("generating {:s}certificate issued by {:s} for {:s} ({:s}).".format('self-signed ' if params['issuer_name'] == params['subject_name'] else '', params['issuer_name'].rfc4514_string(), params['subject_name'].rfc4514_string(), ', '.join(map("{!s}".format, an))))
    try:
        x509 = functools.reduce(lambda agg, attribute_value: (lambda attribute, value: getattr(agg, attribute)(int(value) if isinstance(value, six.string_types) and value.isdigit() else value))(*attribute_value), params.items(), X.CertificateBuilder())

    except AttributeError:
        available = {attribute for attribute in dir(X.CertificateBuilder) if not attribute.startswith('_')} | {'hashAlgorithm'}
        misses = {choice for choice in params} - available
        print("critical: unable to generate certificate due to the explicitly given parameters ({:s}) not being within the ones available ({:s}).".format(', '.join(misses), ', '.join(available)))
        print('trying again without the invalid parameters.\n')
        [ params.pop(attribute) for attribute in misses ]
        params['hashAlgorithm'] = hashAlgorithm.name
        return gen_certificate(private, **params)

    else:
        print('adding necessary extensions to certificate and signing it.')
        extended = x509.add_extension(bc, False).add_extension(an, False).public_key(private.public_key())

    try:
        certificate = extended.sign(private_key=private, algorithm=hashAlgorithm(), backend=chb.default_backend())

    except (ValueError, TypeError):
        print("critical: error signing certificate likely due to the hashAlgorithm ({:s}) not being viable.".format(hashAlgorithm.name))
        print('trying again using a default algorithm.\n')
        return gen_certificate(private, **params)

    assert isinstance(certificate, X.Certificate)
    return certificate, certificate.public_key()

def load_certificate(private, content):
    import cryptography.x509 as X
    import cryptography.hazmat.primitives.asymmetric.padding as chpap
    import cryptography.hazmat.primitives.serialization as chps

    print("reading an X509 certificate from {:d} bytes worth of PEM.".format(len(content)))
    try:
        certificate = X.load_pem_x509_certificate(data=content)

    except ValueError:
        print("critical: error while decoding certificate, generating one instead.\n")
        return gen_certificate(private)

    import cryptography
    print('verifying the private key matches the following public key from the certificate.\n')
    print(certificate.public_key().public_bytes(encoding=chps.Encoding.PEM, format=chps.PublicFormat.SubjectPublicKeyInfo).decode(sys.getdefaultencoding()))

    try:
        private.public_key().verify(signature=certificate.signature, data=certificate.tbs_certificate_bytes, padding=chpap.PKCS1v15(), algorithm=certificate.signature_hash_algorithm)

    except cryptography.exceptions.InvalidSignature:
        print("critical: the certificate's public key does not match the private key, generating a new certificate instead.\n")
        return gen_certificate(private)

    else:
        print('which definitely seems to be the case.')

    return certificate, certificate.public_key()

def hardlink(src, dst):
    if os.path.isfile(dst):
        print("warning: removing file at the specified target path ({:s}).".format(dst))
        os.unlink(dst)

    elif os.path.exists(dst):
        print("critical: refusing to overwrite target path ({:s}) due to target not being a file.".format(dst))
        return

    return os.link(src, dst)

def setup_ssl(socket, arguments):
    try:
        import cryptography, ssl
        import cryptography.hazmat.primitives.serialization as chps

    except ImportError:
        print('warning: ignoring request for SSL support due to an error importing the necessary libraries.')
        return socket

    python_ssl_is_fucking_stupid = {}

    if arguments.keyfile:
        with open(arguments.keyfile, 'rb') as infile:
            content = infile.read()
        key, pem = load_key(content)

    else:
        key, pem = gen_key(bits=arguments.keysize)

    print("using the following {:d}-bit key.\n".format(key.key_size))
    print(pem.decode(sys.getdefaultencoding()))

    python_ssl_is_fucking_stupid['keydata'] = pem

    parameters = {attribute : value for attribute, value in arguments.parameters or []}

    if arguments.certificate:
        if parameters:
            print('warning: ignoring the provided certificate parameters due to being asked to load certificate from file.\n')

        with open(arguments.certificate, 'rb') as infile:
            content = infile.read()
        cert, pk = load_certificate(key, content)

    else:
        cert, pk = gen_certificate(key, **parameters)

    sig = bytearray(cert.fingerprint(algorithm=cert.signature_hash_algorithm))
    pem = cert.public_bytes(encoding=chps.Encoding.PEM)
    print("\nusing certificate with a {:d}-bit {:s} ({:s})\n{:s}\n".format(8 * len(sig), cert.signature_hash_algorithm.name, cert.signature_algorithm_oid.dotted_string, ':'.join(map("{:02x}".format, sig))))
    print(pem.decode(sys.getdefaultencoding()))

    python_ssl_is_fucking_stupid['certdata'] = pem

    import tempfile
    with tempfile.NamedTemporaryFile(prefix='poc', delete=not WIN32) as keyfile, tempfile.NamedTemporaryFile(prefix='poc', delete=not WIN32) as certfile:

        keyfile.write(python_ssl_is_fucking_stupid['keydata'])
        if arguments.keypath:
            hardlink(keyfile.name, arguments.keypath)
            print("wrote key data to {:s}.".format(arguments.keypath))

        certfile.write(python_ssl_is_fucking_stupid['certdata'])
        if arguments.certificatepath:
            hardlink(certfile.name, arguments.certificatepath)
            print("wrote certificate data to {:s}.".format(arguments.certificatepath))

        if WIN32: [ file.close() for file in [keyfile, certfile] ]
        wrap_the_bitch_using_filenames_because_python_is_fucking_stupid = ssl.wrap_socket(socket, server_side=True, keyfile=keyfile.name, certfile=certfile.name)
        if WIN32: keyfile, certfile = (open(file.name) for file in [keyfile, certfile])
    return wrap_the_bitch_using_filenames_because_python_is_fucking_stupid

if __name__ == '__main__':
    arguments = parse_args()

    host, port = arguments.hostport.split(':')
    port = int(port)

    httpd = HTTPServer((host, port), fileserver)

    if arguments.use_ssl:
        print('setting up ssl on socket as per user request.\n')
        httpd.socket = setup_ssl(httpd.socket, arguments)

    print('bound to %s:%d'% (host, port))
    print('...and we\'re off.')
    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        pass
    sys.exit(0)
