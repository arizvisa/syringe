# http://www.freebsd.org/cgi/man.cgi?query=tar&sektion=5&manpath=FreeBSD+8-current
from ptypes import *

class stringinteger(pstr.string):
    def int(self):
        return int(self.str())
    def long(self):
        return long(self.str())
    def __int__(self):
        return self.int()
    def __long__(self):
        return self.long()
    def set(self, integer):
        n = str(integer)
        prefix = '0'*(self.length-1 - len(n))
        return super(stringinteger,self).set(prefix+n+'\x00')

class stringoctal(stringinteger):
    def int(self):
        try:
            return int(self.str(),8)
        except ValueError:
            return 0
    def long(self):
        try:
            return long(self.str(),8)
        except ValueError:
            return 0

    def set(self, integer):
        n = oct(integer)[1:]
        prefix = '0'*(self.length-1 - len(n))
        return super(stringoctal,self).set(prefix+n+'\x00')

class stream_t(parray.infinite):
    def summary(self):
        return '%s size: %x, %d files.'% (repr(self._object_), self.size(), len(self))

    terminated = 0
    def isTerminator(self, value):
        if value.iseof():
            self.terminated += 1
        else:
            self.terminated = 0
        return self.terminated == 2

class header_t(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string,length=100), 'name'),
        (dyn.clone(stringoctal,length=8), 'mode'),
        (dyn.clone(stringoctal,length=8), 'uid'),
        (dyn.clone(stringoctal,length=8), 'gid'),
        (dyn.clone(stringoctal,length=12), 'size'),
        (dyn.clone(stringoctal,length=12), 'mtime'),
        (dyn.clone(stringoctal,length=8), 'checksum'),
        (pstr.char_t, 'linkflag'),
        (dyn.clone(pstr.string,length=100), 'linkname'),
    ]

    def isempty(self):
        return self['name'].str() == ''

# FIXME: we can auto-detect which header we are by checking 'magic'
class header_extended_t(pstruct.type):
    _fields_ = [
        (dyn.clone(pstr.string,length=6), 'magic'),
        (dyn.clone(stringinteger,length=2), 'version'),
        (dyn.clone(pstr.string,length=32), 'uname'),
        (dyn.clone(pstr.string,length=32), 'gname'),
        (dyn.clone(stringinteger,length=8), 'devmajor'),
        (dyn.clone(stringinteger,length=8), 'devminor'),
    ]
    
class member_t(pstruct.type):
    def iseof(self):
        n = reduce(lambda x,y:x+y, (ord(x) for x in self.serialize()), 0)
        return n == 0
        
    def summary(self):
        common = self['header']['common']
        filename = common['name']
        mode = common['mode']
        uid,gid = common['uid'],common['gid']
        sz,rsz = common['size'],self['data'].size()
        return '\n'.join(map(repr,(filename,mode,uid,gid,sz))) + '\n' + self['data'].hexdump(rows=4)

### old
class header_old(pstruct.type):
    _fields_ = [
        (header_t, 'common'),
        (dyn.clone(pstr.string,length=255), 'pad'),
    ]

    def getsize(self):
        return self['common']['size'].int()

class old(stream_t):
    class member(member_t):
        _fields_=[(header_old,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

### ustar
class header_ustar(header_old):
    _fields_ = [
        (header_t, 'common'),
        (header_extended_t, 'extended'),

        (dyn.clone(pstr.string,length=155), 'prefix'),
        (dyn.block(12), 'padding'),
    ]

    def getsize(self):
        sz = self['common']['size'].int()
        return (sz+511)/512*512

class ustar(stream_t):
    class member(member_t):
        _fields_=[(header_ustar,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

### gnu
class gnu_sparse(pstruct.type):
    _fields_ = [
           (dyn.clone(stringoctal,length=12), 'offset'),
           (dyn.clone(stringoctal,length=12), 'numbytes'),
    ]
        
class gnu_sparse_header(pstruct.type):
    _fields_ = [
        (dyn.array(gnu_sparse,21), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string,length=7), 'padding'),
    ]

class gnu_sparse_array(parray.terminated):
    _object_ = gnu_sparse_header
    def isTerminator(self, value):
        v = value['isextended'].str()
        return v == '\x00'

class header_gnu(header_old):
    def __extended_data(self):
        v = self['isextended'].li.str()
        if v == '\x00':
            return dyn.clone(parray.type,_object_=gnu_sparse_header)
        return gnu_sparse_array

    _fields_ = [
        (header_t, 'common'),
        (header_extended_t, 'extended'),

        (dyn.clone(stringoctal,length=12), 'atime'),
        (dyn.clone(stringoctal,length=12), 'ctime'),
        (dyn.clone(stringoctal,length=12), 'offset'),
        (dyn.clone(pstr.string,length=4), 'longnames'),
        (pstr.char_t, 'unused'),
        (dyn.array(gnu_sparse,4), 'sparse'),
        (pstr.char_t, 'isextended'),
        (dyn.clone(pstr.string,length=12), 'realsize'),
        (dyn.clone(pstr.string,length=17), 'pad'),
        (__extended_data, 'extended_data'),
    ]

class gnu(stream_t):
    class member(member_t):
        _fields_=[(header_gnu,'header'),(lambda s: dyn.block(s['header'].getsize()),'data')]
    _object_ = member

if __name__ == '__main__':
    import ptypes,tar
    class streamfile(object):
        def __init__(self, file):
            self.file = file
            self.offset = 0
        def read(self, amount):
            self.file.seek(self.offset)
            self.offset += amount
            return self.file.read(amount)
        def write(self, data):
            self.file.seek(self.offset)
            offset+=len(data)
            return self.file.write(data)
        def tell(self):
            return self.file.tell()

#    ptypes.setsource(ptypes.provider.stream(streamfile(file('./test.tar', 'rb+'))))
#    ptypes.setsource(ptypes.provider.stream(file('./test.tar', 'rb+')))
    ptypes.setsource(ptypes.provider.file('./test.tar'))
    reload(tar)

    a = tar.ustar(offset=0)
    a=a.l
    print a

#    print a[0]
#    print a[1]
#    b = tar.old(offset=0)
#
#    c = tar.gnu(offset=0)
   
