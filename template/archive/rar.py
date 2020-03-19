## mostly from http://www.rarlab.com/technote.htm
import ptypes
from ptypes import *

## Data types
pbinary.setbyteorder(ptypes.config.byteorder.bigendian)
class vint(pbinary.terminatedarray):
    class _object_(pbinary.struct):
        _fields_ = [(1,'continue'),(7,'integer')]
    def isTerminator(self, value):
        return value['continue'] == 0
#    def int(self):
#        res = 0
#        for n in self:
#            res <<= 7
#            res |= n['integer']
#        return res

pint.setbyteorder(ptypes.config.byteorder.littleendian)
class byte(pint.uint8_t): pass
class uint16(pint.uint16_t): pass
class uint32(pint.uint32_t): pass
class uint64(pint.uint64_t): pass

## Enumerations and misc
class RARFORMAT(pint.enum):
    _values_ = [
        ('RARFMT_NONE', 0),
        ('RARFMT14', 1),
        ('RARFMT15', 2),
        ('RARFMT50', 3),
        ('RARFMT_FUTURE', 4),
    ]

    @classmethod
    def signature(cls, instance):
        data = instance.serialize()
        if data.startswith('\x52\x45\x7e\x5e'):
            return cls.byname('RARFMT14'),
        elif data.startswith('\x52\x61\x72\x21\x1a\x07'):
            ver = instance[6].int()
            return cls.byname('RARFMT15') + ver
        return cls.byname('RARFMT_NONE')

class HeaderType(pint.enum):
    _values_ = [
        ('HEAD_MARK', 0x00),
        ('HEAD_MAIN', 0x01),
        ('HEAD_FILE', 0x02),
        ('HEAD_SERVICE', 0x03),
        ('HEAD_CRYPT', 0x04),
        ('HEAD_ENDARC', 0x05),
        ('HEAD_UNKNOWN', 0xff),

        ('HEAD3_MARK', 0x72),
        ('HEAD3_MAIN', 0x73),
        ('HEAD3_FILE', 0x74),
        ('HEAD3_CMT', 0x75),
        ('HEAD3_AV', 0x76),
        ('HEAD3_OLDSERVICE', 0x77),
        ('HEAD3_PROTECT', 0x78),
        ('HEAD3_SIGN', 0x79),
        ('HEAD3_SERVICE', 0x7a),
        ('HEAD3_ENDARC', 0x7b),
    ]

## Base structures
class MainHead14(pstruct.type):
    _fields_ = [
        (dyn.block(4), 'Mark'),
        (uint16, 'HeadSize'),
        (byte, 'Flags'),
    ]
class FileHead14(pstruct.type):
    _fields_ = [
        (uint32, 'DataSize'),
        (uint32, 'UnpSize'),
        (uint16, 'CRC32'),
        (uint16, 'HeadSize'),
        (uint32, 'FileTime'),
        (byte, 'FileAttr'),
        (byte, 'Flags'),
        (byte, 'UnpVer'),
        (byte, 'NameSize'),
        (byte, 'Method'),
        (lambda s: dyn.clone(pstr.string, length=s['NameSize'].li.int()), 'FileName'),
    ]

class ShortBlock15(pstruct.type):
    class _HeaderType(HeaderType, byte): pass
    _fields_ = [
        (uint16, 'HeadCRC'),
        (_HeaderType, 'HeaderType'),
        (uint16, 'Flags'),
        (uint16, 'HeadSize'),
    ]

class ShortBlock50(pstruct.type):
    _fields_ = [
        (uint32, 'HeadCRC'),
        (vint, 'BlockSize'),
        (uint32, 'Crc'),
        (vint, 'Flags'),
    ]

class Header(pstruct.type):
    _fields_ = [
        (uint32, 'CRC32'),
        (vint, 'size'),
        (vint, 'type'),
    ]

class MainArchiveHeader(pstruct.type):
    _fields_ = [
        (uint32, 'CRC32'),
        (vint, 'Header size'),
        (vint, 'Header type'),
        (vint, 'Header flags'),
        (vint, 'Extra area size'),
        (vint, 'Archive flags'),
    ]

if __name__ == '__main__':
    import ptypes,archive.rar as rar
    ptypes.setsource(ptypes.prov.filecopy('test.rar'))

    a = rar.MainArchiveHeader(offset=8).l

#    x = a.v[1].object
#    y = x[1]
#    print(x)
#    print(list(x.object)[1].keys())

    x = pbinary.new(rar.vint,offset=0xc)
    print(x)
    print(x.l)

    for k,v in x[0].iteritems():
        print(k,v)
