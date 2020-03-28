import logging
import ptypes
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

class char(pint.uint8_t): pass
class short(pint.sint16_t): pass
class ushort(pint.uint16_t): pass
class long(pint.sint32_t): pass

class Header(pstruct.type):
    class Magic(short):
        @classmethod
        def default(cls):
            return cls().set(0o732)
        def valid(self):
            return self.int() == self.default().int()
        def properties(self):
            res = super(Header.Magic, self).properties()
            res['valid'] = self.valid()
            return res

    class Storage(pint.enum, char):
        _values_ = [
            ('RLE', 1),
            ('VERBATIM', 0),
        ]

    class Colormap(pint.enum, long):
        _values_ = [
            ('NORMAL', 0),
            ('DITHERED', 1),
            ('SCREEN', 2),
            ('COLORMAP', 3),
        ]

    _fields_ = [
        (Magic, 'MAGIC'),
        (Storage, 'STORAGE'),
        (char, 'BPC'),
        (ushort, 'DIMENSION'),
        (ushort, 'XSIZE'),
        (ushort, 'YSIZE'),
        (ushort, 'ZSIZE'),
        (long, 'PIXMIN'),
        (long, 'PIXMAX'),
        (dyn.block(4), 'DUMMY'),
        (dyn.clone(pstr.string, length=80), 'IMAGENAME'),
        (Colormap, 'COLORMAP'),
        (dyn.block(404), 'DUMMY'),
    ]

class Table(parray.type): _object_ = long

class File(pstruct.type):
    def __table(self):
        res = self['header'].li
        boolean = res['STORAGE']
        if boolean.int() not in (0, 1):
            cls = self.__class__
            logging.warn('{:s}.__table : Unknown storage type. : {!r}'.format('.'.join((__name__,cls.__name__)), boolean.summary()))
            boolean = 0
        return dyn.clone(Table, length=res['XSIZE'].int()*res['YSIZE'].int() * boolean.int())

    def __data(self):
        res = self['header'].li
        return dyn.clone(ptype.block, length=0)

    _fields_ = [
        (Header, 'header'),
        (__table, 'starttab'),
        (__table, 'lengthtab'),
        (__data, 'data'),
    ]

if __name__ == '__main__':
    import sys
    import ptypes, image.iris

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else __file__))
        sys.exit(0)

    ptypes.setsource(ptypes.prov.file(sys.argv[1]))
    a = image.iris.File()
    a = a.l
