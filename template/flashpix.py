from ptypes import *

class BYTE(pint.uint8_t): pass
class WORD(pint.uint16_t): pass
class DWORD(pint.uint32_t): pass

class CLSID(pstruct.type):
    from ptypes.pint import littleendian,bigendian
    _fields_ = [
        (littleendian(pint.uint32_t), 'a'),
        (littleendian(pint.uint16_t), 'b'),
        (littleendian(pint.uint16_t), 'c'),#   64
        (bigendian(pint.uint16_t), 'd'),
        (bigendian(dyn.clone(pint.uint_t, length=6)), 'e')
    ]

    def summary(self):
        result = []
        for k,v in self.items():
            count = v.size()*2
            fmt = '%0' + str(count) + 'x'
            result.append(fmt% int(v) )
        return '{'+ '-'.join(result) + '}'

if False:
    res = [
        0x00, 0x64, 0x61, 0x56, 0x54, 0xc1, 0xce, 0x11, 0x85, 0x53, 0x00, 0xaa, 0x00, 0xa1, 0xf9, 0x5b,
        0x30, 0x00, 0x00, 0x00, 0x38, 0x0b, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
        0x08, 0x01, 0x00, 0x00, 0x01, 0x00, 0x04, 0x03, 0x10, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03,
        0x4c, 0x03, 0x00, 0x00
    ]
    argh = (chr(x) for x in res)

    x = CLSID(source=provider.string(argh))
    print x

class HEADER(pstruct.type):
    _fields_ = [
        (WORD, 'wByteOrder'),
        (WORD, 'wFormat'),
        (DWORD, 'dwOSVer'),
        (CLSID, 'clsid'),   # XXX
        (DWORD, 'reserved')
    ]

class FMTID(dyn.block(16)): pass

class FMTIDOFFSET(pstruct.type):
    _fields_ = [
        (FMTID, 'fmtid'),   # XXX
        (DWORD, 'dwOffset'),
    ]

class PROPERTYSECTIONHEADER(pstruct.type):
    _fields_ = [
        (DWORD, 'cbSection'),
        (DWORD, 'cProperties'),
        (lambda s: dyn.array(PROPERTYIDOFFSET, s['cProperties'].li.int()), 'rgprop'),
        (lambda s: dyn.block( s['cbSection'].li.int() - (8+s['rgprop'].li.blocksize())), 'data')
    ]

    def __getslice__(self, i, j):
        i,j = (i - 8, j - 8)
        return self['data'][i:j]

class PROPERTYIDOFFSET(pstruct.type):
    _fields_ = [
        (DWORD, 'propid'),
        (DWORD, 'dwOffset')
    ]

class SERIALIZEDPROPERTYVALUE(pstruct.type):
    _fields_ = [
        (DWORD, 'dwType'),
        (lambda s: dyn.array(BYTE, 0), 'rgb')   # XXX
    ]

## property/tag dictionary or something
class ENTRY(pstruct.type):
    _fields_ = [
        (DWORD, 'propid'),
        (DWORD, 'cb'),
        (lambda s: dyn.array(tchar, int(s['cb'].li)), 'tsz')
    ]

class DICTIONARY(pstruct.type):
    _fields_ = [
        (DWORD, 'cEntries'),
        (lambda s: dyn.array(ENTRY, int(s['cEntries'].li)), 'rgEntry')
    ]

###
class PropertySetStream(pstruct.type):
    _fields_ = [
        (HEADER, 'header'),
        (FMTIDOFFSET, 'format'),
        (PROPERTYSECTIONHEADER, 'section')
    ]

###
class SUBIMAGEHEADER(pstruct.type):
    _fields_ = [
        (DWORD, 'length'),
        (DWORD, 'width'),
        (DWORD, 'height'),
        (DWORD, 'number of tiles'),
        (DWORD, 'tile width'),
        (DWORD, 'tile height'),
        (DWORD, 'number of channels'),
        (DWORD, 'offset to tile header table'),
        (DWORD, 'length of tile header entry'),
    ]

class TILEHEADER(pstruct.type):
    class TileHeaderCompressionType(pint.enum, DWORD):
        _values_ = [
            ('Uncompressed data', 0),
            ('Single color compression', 1),
            ('JPEG', 2),
            ('Invalid tile', 0xffffffff),
        ]
    _fields_ = [
        (DWORD, 'tile offset'),
        (DWORD, 'tile size'),
        (TileHeaderCompressionType, 'compression type'),
        (DWORD, 'compression subtype'),
    ]

class SubimageHeaderStream(pstruct.type):
    _fields_ = [
        (HEADER, 'header'),
        (SUBIMAGEHEADER, 'subimage'),
        (lambda s: dyn.array(TILEHEADER, int(s['subimage'].li['number of tiles'])), 'tiles')
    ]

if __name__ == '__main__':
    import ptypes
    self = SubimageHeaderStream()
#    self.source = provider.file('./poc.fpx.old')
#    self.setoffset(0x1080)
    self.source = provider.file('./org.fpx')
    self.setoffset(0x1040)
    self.load()

#    print self['subimage']['offset to tile header table']
#    print hex(self['subimage']['offset to tile header table'].getoffset())
