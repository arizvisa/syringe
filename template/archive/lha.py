import ptypes
from ptypes import *

# integral types
class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u32(pint.uint32_t): pass
class u64(pint.uint64_t): pass

class s8(pint.sint8_t): pass
class s16(pint.sint16_t): pass
class s32(pint.sint32_t): pass
class s64(pint.sint64_t): pass

# lzh-specific integrals
class method_id(pstr.string):
    length = 5

    def set(self, value):
        if not isinstance(value, tuple):
            return super(Signature._method, self).set(value)

        type, version = value
        if type == 'lh':
            versionmap = '0123456789abcdef'
            if version is None:
                version = versionmap.index('d')
            elif version == 'x':
                return super(Signature._method, self).set('-lhx-')

            try:
                res = '-lh{:s}-'.format(versionmap[version])
            except (IndexError, TypeError):
                raise NotImplementedError((type, version))
            return super(Signature._method, self).set(res)

        elif type in ('pc', 'pm'):
            versionmap = '012'
            if version is None:
                res = '-{:s}0-'.format(type)
                return super(Signature._method, self).set(res)
            elif version == 's':
                res = '-{:s}s-'.format(type)
                return super(Signature._method, self).set(res)
            try:
                res = '-{:s}{:s}-'.format(type, versionmap[version])
            except (IndexError, TypeError):
                raise NotImplementedError((type, version))
            return super(Signature._method, self).set(res)

        elif type == 'lz':
            versionmap = '012345678'
            if version == 's':
                res = '-lzs-'
                return super(Signature._method, self).set(res)
            elif version is None:
                res = '-lz4-'
                return super(Signature._method, self).set(res)

            try:
                res = '-lz{:s}-'.format(versionmap[version])
            except (IndexError, TypeError):
                raise NotImplementedError((type, version))
            return super(Signature._method, self).set(res)
        raise NotImplementedError((type, version))

    def get(self):
        res = self.str()
        if res.startswith('-') and res.endswith('-'):
            res = res[1:-1]
            if res.startswith('lh'):
                versionmap = '0123456789abcdef'
                res = res[2:]
                if res == 'd':
                    return 'lh', None
                elif res == 'x':
                    return 'lh', 'x'
                return 'lh', versionmap.index(res)
            elif res.startswith('pc') or res.startswith('pm'):
                type, version = res[:2], res[2:]
                versionmap = '012'
                if version == 's':
                    return type, version
                return type, versionmap.index(version)

            elif res.startswith('lz'):
                versionmap = '012345678'
                type, version = res[:2], res[2:]
                if version == 's':
                    return 'lz', version
                elif version == '4':
                    return 'lz', None
                return 'lz', versionmap.index(version)
            raise NotImplementedError
        raise ValueError(res)

# extension header levels
class Level(ptype.definition): cache = {}

@Level.define
class Level0(pstruct.type):
    type = 0
    _fields_ = [
        (u8, 'filename-length'),
        (__filename, 'filename'),
        (u16, 'crc'),
    ]

@Level.define
class Level1(pstruct.type):
    type = 1
    _fields_ = [
        (u8, 'filename-length'),
        (__filename, 'filename'),
        (u16, 'crc'),
        (u8, 'os-identifier'),
        (u16, 'next-header-size'),
    ]

# base structures
class Signature(pstruct.type):
    _fields_ = [
        (u8, 'size'),
        (u8, 'checksum'),
        (method_id, 'method'),
    ]

class Attributes(pstruct.type):
    class _timestamp(u32): pass
    class _attribute(u8): pass

    _fields_ = [
        (u32, 'compressed-size'),
        (u32, 'uncompressed-size'),
        (_timestamp, 'timestamp'),
        (_attribute, 'file-attribute'),
        (u8, 'level-identifier'),
    ]

    def Level(self):
        return self['level-identifier'].int()

class Header(pstruct.type):
    def __extended(self):
        res = self['attributes'].li
        return Level.lookup(res.Level())

    def __padding_header(self):
        res = self['signature'].li
        cb = res['size'].int()
        fields = (self[fld].li.size() for fld in ('signature', 'attributes', 'extended'))
        return dyn.block(max((0, cb - (sum(fields)+2))))

    _fields_ = [
        (Signature, 'signature'),
        (Attributes, 'attributes'),
        (__extended, 'extended'),
        (__padding_header, 'padding'),
    ]

class File(pstruct.type):
    def __data(self):
        res = self['header'].li
        return dyn.block(res['attributes']['compressed-size'].int())

    _fields_ = [
        (Header, 'header'),
        (__data, 'data'),
    ]

if __name__ == '__main__':
    import ptypes, archive.lha
    reload(archive.lha)
    ptypes.setsource(ptypes.prov.file('c:/users/user/Downloads/fcgb2.lzh', mode='r'))
    z = archive.lha.File()
    z = z.l

    print z.source.size()
    print z['header']['signature']
    print z['header']['attributes']
    print z['header']
    print z['header']['filename']
