import v1,v2
from base import *

class Header(pstruct.type):
    _fields_ = [
        (Integer, 'filesize'),
        (Integer, 'x1'),
        (Integer, 'y1'),
        (Integer, 'x2'),
        (Integer, 'y2'),
    ]

class File(pstruct.type):
    def __file(self):
        v = int(self['version'].l)
        if v == 0x1101:
            return v1.File
        elif v == 0x0011:
            return v2.File
        raise NotImplementedError('Unknown version %x'% v)
            
    _fields_ = [
        (dyn.block(0x200), 'padding'),
        (Header, 'header'),
        (Integer, 'version'),
        (__file, 'file'),
    ]
