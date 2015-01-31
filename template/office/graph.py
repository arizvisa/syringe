from ptypes import *
import __init__
class Record(__init__.Record): cache = {}
class RecordGeneral(__init__.RecordGeneral):
    Record=Record
    class __header(pbinary.struct):
        _fields_ = [
            (12, 'instance'),
            (4, 'version'),
        ]
    __header = pbinary.littleendian(__header)

    def __data(self):
        t = int(self['type'].li)
        l = int(self['length'].li)
        try:
            cls = self.Record.Lookup(t)
        except KeyError:
            return dyn.clone(__init__.RecordUnknown, type=t, length=l)
        return dyn.clone(cls, blocksize=lambda s:l)

    def __extra(self):
        t = int(self['type'].li)
        name = '[%s]'% ','.join(self.backtrace()[1:])

        used = self['data'].size()
        total = int(self['length'].li)

        if total > used:
            l = total-used
            print "graph object at %x (type %x) %s has %x bytes unused"% (self.getoffset(), t, name, l)
            return dyn.block(l)

        if used > total:
            print "graph object at %x (type %x) %s's contents are larger than expected (%x>%x)"% (self.getoffset(), t, name, used, total)
        return dyn.block(0)

    _fields_ = [
        (__header, 'version'),
        (pint.littleendian(pint.uint16_t), 'type'),
        (pint.uint32_t, 'length'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]

    def blocksize(self):
        return 8 + int(self['length'])

class RecordContainer(__init__.RecordContainer): _object_ = RecordGeneral
class File(__init__.File): _object_ = RecordGeneral

@Record.define
class DataFormat(pstruct.type):
    type = 0x1006
    _fields_ = [
        (pint.uint16_t, 'xi'),
        (pint.uint16_t, 'yi'),
        (pint.uint16_t, 'iss'),
        (pint.uint16_t, 'fXL4iss'),     # XXX: this should be a pbinary.struct
    ]

if __name__ == '__main__':
    from ptypes import *
    import graph

