from base import *

class OpStash(object):
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

class OpRecord(pstruct.type):
    def __data(self):
        return OpStash.Lookup( int(self['code'].li) )

    _fields_ = [
        (Opcode_v1, 'code'),
        (__data, 'data'),
    ]

class picSize(pstruct.type):
    _fields_ = [
        (Integer, 'size'),
        (Integer, 'top'),
        (Integer, 'left'),
        (Integer, 'bottom'),
        (Integer, 'right'),
    ]

class picFrame(pstruct.type):
    _fields_ = [
        (uint8, 'version'),
        (uint8, 'picture'),
    ]

class bounds(pstruct.type):
    _fields_ = [
        (Integer, 'top'),
        (Integer, 'left'),
        (Integer, 'bottom'),
        (Integer, 'right'),
    ]

class pixMap(pstruct.type):
    _fields_ = [
        (Long, 'baseAddr'),
        (Integer, 'rowBytes'),
        (bounds, 'bounds'),
        (Integer, 'pmVersion'),
        (Integer, 'packType'),
        (Long, 'packSize'),
        (Long, 'hRes'),
        (Long, 'vRes'),
        (Integer, 'pixelType'),
        (Integer, 'pixelSize'),
        (Integer, 'cmpCount'),
        (Integer, 'cmpSize'),
        (Long, 'planeBytes'),
        (Long, 'pmTable'),
        (Long, 'pmReserved'),
    ]

class directBitsRect(pstruct.type):
    opcode = 0x009a
    _fields_ = [
        (pixMap, 'pixMap'),
        (bounds, 'srcRect'),
        (bounds, 'dstRect'),
        (Integer, 'mode'),
    ]

class File(parray.terminated):
    _object_ = OpRecord
    def isTerminator(self, value):
        return int(value['code']) == 0xff

