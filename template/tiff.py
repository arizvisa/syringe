import ptypes
from ptypes import *

ptypes.setbyteorder( pint.bigendian )

class Record(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

class Directory(pstruct.type):
    class Entry(pstruct.type):
        def _offset(self):
            id = int(self['id'].li)

            t = self['type'].l
            type = t.lookup[int(t)]
            c = int(self['count'].li)

            try:
                return Record.Lookup(id)
            except KeyError:
                pass
            return dyn.block( type().alloc().size() * c )

        class type(pint.enum, pint.uint16_t):
            _values_ = [
                ('byte',1), ('ascii',2), ('short',3), ('long',4),
                ('rational',5), ('sbyte',6), ('undefined',7), ('sshort',8),
                ('slong',9), ('srational',10), ('float',11), ('double',12)
            ]
            lookup = {
                1:pint.uint8_t,
                2:pstr.char_t,
                3:pint.uint16_t,
                4:pint.uint32_t,
                5:dyn.array(pint.uint32_t,2),
                6:pint.int8_t,
                7:pint.uint8_t,
                8:pint.int16_t,
                9:pint.int32_t,
                10:dyn.array(pint.int32_t,2),
                11:pfloat.single,
                12:pfloat.double,
            }

        _fields_ = [
            (pint.uint16_t, 'id'),
            (type, 'type'),
            (pint.uint32_t, 'count'),
            (dyn.pointer(lambda s: s.parent._offset()), 'offset'),
        ]

    _fields_ = NotImplementedError("defined further below")

    def iterate(self):
        while True:
            for x in self['entry']:
                yield x

            if int(self['next']) == 0:
                break

            self = self['next'].d.l
        return

Directory._fields_ = [
        (pint.uint16_t, 'count'),
        (lambda s: dyn.array(s.Entry, int(s['count'].li)), 'entry'),
        (dyn.pointer(Directory,type=pint.uint32_t), 'next')
    ]

class Header(pstruct.type):
    def __directory(self):
        signature = self['signature'].li.serialize()
        if signature == '\x4d\x4d\x00\x2a':     # bigendian
            return dyn.pointer(Directory)
        if signature == '\x49\x49\x2a\x00':     # little-endian
            pass
            # XXX: I haven't encountered this yet
        raise NotImplementedError(signature)

    _fields_ = [
#        (pint.uint16_t, 'byteorder'),
#        (pint.uint16_t, 'id'),
        (pint.uint32_t, 'signature'),      # ('\x49\x49\x2a\x00', '\x4d\x4d\x00\x2a')
        (dyn.pointer(Directory,type=pint.uint32_t), 'directory'),
    ]

class File(Header): pass

if __name__ == '__main__':
    import ptypes,tiff
    ptypes.setsource( ptypes.file('./0.tif') )

    a = tiff.File()
    a = a.l
    
