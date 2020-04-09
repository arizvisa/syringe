from ._optable import OperandLookupTable
from . import typesize

def Lookup(opcode):
    '''Lookup specified opcode in the lookup table'''
    res = ord(opcode[0])
    if res == 0x0f:
        res = ord(opcode[1])
        return OperandLookupTable[res+0x100]
    return OperandLookupTable[res]

def HasModrm(lookup):
    '''Returns True if specified opcode requires a modrm byte'''
    return bool(ord(lookup) & 0x80)
def HasImmediate(lookup):
    '''Returns True if specified opcode contains an immediate value'''
    return bool(ord(lookup) & 0x40)

def GetImmediateLength(lookup, prefixes):
    res = ord(lookup) & 0x3f

    opsizeindex = not int(b'\x66' in prefixes)

    if res == 0x3f:    # it sucks because i know python has such a horrible optimizer, and i need to redo this as a dict for that reason
        size = [ 2*typesize.halfword, 2*typesize.word ][opsizeindex]
    elif res == 0x3e:
        size = [ typesize.byte, typesize.halfword ][opsizeindex]
    elif res == 0x3d:
        size = [ typesize.halfword, typesize.word ][opsizeindex]
    elif res == 0x3c:
        size = [ typesize.word, typesize.word*2][opsizeindex]
    elif res == 0x3b:
        size = [ typesize.word*2, typesize.halfword ][opsizeindex]
    elif res == 0x3a:
        size = [ typesize.halfword + typesize.word, typesize.word ][opsizeindex]
    else:
        size = res
    return size
