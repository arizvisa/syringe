# this makes ctypes friendlier (for me, anyways)

from ctypes import *

## constants
CONTEXT_i386 = 0x00010000    # this assumes that i386 and
CONTEXT_i486 = 0x00010000    # i486 have identical context records
CONTEXT_CONTROL = (CONTEXT_i386 | 0x00000001L) # SS:SP, CS:IP, FLAGS, BP
CONTEXT_INTEGER = (CONTEXT_i386 | 0x00000002L) # AX, BX, CX, DX, SI, DI
CONTEXT_SEGMENTS = (CONTEXT_i386 | 0x00000004L)           # DS, ES, FS, GS
CONTEXT_FLOATING_POINT = (CONTEXT_i386 | 0x00000008L)     # 387 state
CONTEXT_DEBUG_REGISTERS = (CONTEXT_i386 | 0x00000010L)    # DB 0-3,6,7
CONTEXT_EXTENDED_REGISTERS = (CONTEXT_i386 | 0x00000020L) # cpu specific extensions

CONTEXT_FULL  = (CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS)

CONTEXT_ALL = CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS
CONTEXT_ALL |= CONTEXT_FLOATING_POINT | CONTEXT_DEBUG_REGISTERS
CONTEXT_ALL |= CONTEXT_EXTENDED_REGISTERS

## basic types
DWORD64 = c_uint64
DWORD = c_uint32
WORD = c_uint16
BYTE = c_uint8
ULONGLONG = c_uint64
LONGLONG = c_int64

## complex structures
class M128A(Structure):
    _fields_ = [
        ('Low', ULONGLONG),
        ('High', LONGLONG)
    ]

class MMX(Structure):
    _fields_ = [
        ('Header', ARRAY(M128A, 2)),
        ('Legacy', ARRAY(M128A, 8)),
        ('Xmm0', M128A),
        ('Xmm1', M128A),
        ('Xmm2', M128A),
        ('Xmm3', M128A),
        ('Xmm4', M128A),
        ('Xmm5', M128A),
        ('Xmm6', M128A),
        ('Xmm7', M128A),
        ('Xmm8', M128A),
        ('Xmm9', M128A),
        ('Xmm10', M128A),
        ('Xmm11', M128A),
        ('Xmm12', M128A),
        ('Xmm13', M128A),
        ('Xmm14', M128A),
        ('Xmm15', M128A)
    ]

class XMM_SAVE_AREA32(Structure):
    _fields_ = [
        ('ControlWord', WORD),
        ('StatusWord', WORD),
        ('TagWord', BYTE),
        ('Reserved1', BYTE),
        ('ErrorOpcode', WORD),
        ('ErrorOffset', DWORD),
        ('ErrorSelector', WORD),
        ('Reserved2', WORD),
        ('DataOffset', DWORD),
        ('DataSelector', WORD),
        ('Reserved3', WORD),
        ('MxCsr', DWORD),
        ('MxCsr_Mask', DWORD),
        ('FloatRegisters', ARRAY(M128A, 8)),
        ('XmmRegisters', ARRAY(M128A, 16)),
        ('Reserved4', ARRAY(BYTE, 96))
    ]

SIZE_OF_80387_REGISTERS = 80
class FLOATING_SAVE_AREA(Structure):
    _fields_ = [
        ('ControlWord', DWORD),
        ('StatusWord', DWORD),
        ('TagWord', DWORD),
        ('ErrorOffset', DWORD),
        ('ErrorSelector', DWORD),
        ('DataOffset', DWORD),
        ('DataSelector', DWORD),
        ('RegisterArea', ARRAY(BYTE, SIZE_OF_80387_REGISTERS)),
        ('Cr0NpxState', DWORD)
    ]

MAXIMUM_SUPPORTED_EXTENSION = 512
class CONTEXT(Structure):
    _fields_ = [
        ('ContextFlags', DWORD),
        ('Dr0', DWORD),
        ('Dr1', DWORD),
        ('Dr2', DWORD),
        ('Dr3', DWORD),
        ('Dr6', DWORD),
        ('Dr7', DWORD),
        ('FloatSave', FLOATING_SAVE_AREA),
        ('SegGs', DWORD),
        ('SegFs', DWORD),
        ('SegEs', DWORD),
        ('SegDs', DWORD),
        ('Edi', DWORD),
        ('Esi', DWORD),
        ('Ebx', DWORD),
        ('Edx', DWORD),
        ('Ecx', DWORD),
        ('Eax', DWORD),
        ('Ebp', DWORD),
        ('Eip', DWORD),
        ('SegCs', DWORD),
        ('EFlags', DWORD),
        ('Esp', DWORD),
        ('SegSs', DWORD),
        ('ExtendedRegisters', ARRAY(BYTE, MAXIMUM_SUPPORTED_EXTENSION))
    ]

def isNumber(n):
    return isinstance(n, int) or isinstance(n, long)

def resolve(v):
    if '_length_' in dir(v):
        return yourFriendlyList(v)
    if '_fields_' in dir(v):
        return yourFriendlyDictionary(v)
    return v

class yourFriendlyList(list):
    me = None
    def __init__(self, array):
        super(yourFriendlyList, self).__init__()
        self.me = array

    def __iter__(self):
        for x in range(len(self)):
            yield self[x]

    def __len__(self):
        return self.me._length_

    def __setitem__(self, k, v):
        if isNumber(v):
            self.me[k] = self.me._type_(v)
            return
        self.me[k] = resolve(v)

    def __getitem__(self, k):
        res = self.me[k]
        if isNumber(res):
            return self.type()(res)
        return resolve(res)

    def __repr__(self):
        return repr(list(self))

    def type(self):
        return self.me._type_

class yourFriendlyDictionary(dict):
    me = None
    def __init__(self, structure):
        super(yourFriendlyDictionary, self).__init__()
        self.me = structure

    def keys(self):
        return [k for k,t in self.me._fields_]

    def values(self):
        return [self[k] for k,t in self.me._fields_]

    def items(self):
        return list(zip(self.keys(), self.values()))

    def __getitem__(self, k):
        res = getattr(self.me, k)
        if isNumber(res):
            return res
        return resolve(res)

    def __setitem__(self, k, v):
        res = getattr(self.me, k)
        if isNumber(res):
            cls = type(res)
            setattr(self.me, k, cls(v))
        setattr(self.me, k, v)

    def __repr__(self):
        res = []
        for k,t in self.me._fields_:
            v = self[k]
            if isNumber(v):
                res.append( (k, t(self[k])) )
                continue
            res.append( (k, t(*self[k])) )
        
        return repr(dict([(k,resolve(v)) for (k,v) in res]))

if __name__ == '__main__':
    ## primitives
    print '- type'
    a = DWORD()
    print resolve(a)

    print '- array'
    a = ARRAY(DWORD, 2)()
    print resolve(a)

    print '- struct'
    a = M128A()
    print resolve(a)

    print '- arrays of arrays'
    a = ARRAY( ARRAY(BYTE, 2), 5 )()
    print resolve(a)

    print '- arrays of structs'
    a = ARRAY( M128A, 2 )()
    print resolve(a)
    print resolve(a)[0]
    print resolve(a)[0]['Low']

    print '- structs of arrays'
    class fuck(Structure):
        _fields_ = [
            ('test', ARRAY(BYTE, 2))
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test'][0]

    print '- structs of structs'
    class fuck(Structure):
        _fields_ = [
            ('test', M128A)
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test']['High']

    print '- structs of arrays of structs'
    class fuck(Structure):
        _fields_ = [
            ('test', ARRAY(M128A, 2))
        ]

    a = fuck()
    print resolve(a)
    print resolve(a)['test']
    print resolve(a)['test'][0]
    print resolve(a)['test'][0]['Low']


    print '- arrays of of arrays of structs'
    a = ARRAY( ARRAY(2, M128A), 5)()
    print resolve(a)
    print resolve(a)[0]

    a = CONTEXT()
    v = resolve(a)
