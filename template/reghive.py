#!/usr/bin/env python
import ndk, ptypes
from ptypes import *

class Signature(ptype.block):
    length = 4
    def summary(self):
        iterable = bytearray(self.serialize())
        return "'{:s}'".format(str().join(map("{:c}".format, iterable)))

class Header(pstruct.type):
    class _version(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'major'),
            (pint.uint32_t, 'minor'),
        ]
        def summary(self):
            fields = ['major', 'minor']
            return "{:d}.{:d}".format(*(self[fld].int() for fld in fields))
    class _type(pint.enum, pint.uint32_t):
        _values_ = [('primary file', 0)]
    class _format(pint.enum, pint.uint32_t):
        _values_ = [('memory load', 1)]
    _fields_ = [
        (Signature, 'signature'),
        (pint.uint32_t, 'primarySequenceNumber'),
        (pint.uint32_t, 'secondarySequenceNumber'),
        (ndk.FILETIME, 'lastWritten'),
        (_version, 'version'),
        (_type, 'type'),
        (_format, 'format'),
        (pint.uint32_t, 'rootCellOffset'),
        (pint.uint32_t, 'hiveBinsDataSize'),
        (pint.uint32_t, 'clusteringFactor'),
        (dyn.clone(pstr.wstring, length=32), 'fileName'),
        (ndk.GUID, 'rmId'),
        (ndk.GUID, 'logId'),
        (pint.uint32_t, 'flags'),
        (dyn.block(4), 'guidSignature'),
        (ndk.FILETIME, 'lastReorganizedTimestamp'),
        (dyn.block(16), 'reserved_a0'),
        (dyn.block(332), 'reserved_b0'),
        (pint.uint32_t, 'checksum'),
        (dyn.block(3528), 'reserved_200'),
        (ndk.GUID, 'thawTmId'),
        (ndk.GUID, 'thawRmId'),
        (ndk.GUID, 'thawLogId'),
        (pint.uint32_t, 'bootType'),
        (pint.uint32_t, 'bootRecover'),
    ]

class BinHeader(pstruct.type):
    _fields_ = [
        (Signature, 'signature'),
        (pint.uint32_t, 'offset'),
        (pint.uint32_t, 'size'),
        (dyn.block(8), 'reserved'),
        (ndk.FILETIME, 'timestamp'),
        (pint.uint32_t, 'spare'),
    ]

class Bin(pstruct.type):
    _fields_ = [
        (BinHeader, 'header'),
        (lambda self: dyn.block(self['header'].li['size'].int() - self['header'].size()), 'data'),
    ]

class Cell(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'size'),
        (lambda self: dyn.block(self['size'].li.int()), 'data'),
    ]

if __name__ == '__main__':
    import ptypes
    source = ptypes.setsource(ptypes.prov.file('./Amcache.hve', mode='rb'))

    z = Header().l

    print(z['guidSignature'].hexdump())
    print(z['lastReorganizedTimestamp'])
    print(z['reserved_a0'].hexdump())
    print(z['reserved_b0'].hexdump())

    a = Bin(offset=z.getoffset() + z.size()).l
    print(ptype.block(offset=a.getoffset() + a.size(), length=0x40).l)
    b = Bin(offset=a.getoffset() + a.size()).l
    print(ptype.block(offset=b.getoffset() + b.size(), length=0x40).l)
