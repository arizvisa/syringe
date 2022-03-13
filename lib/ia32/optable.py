from ._optable import OperandLookupTable
from . import typesize

def LookupTableValue(opcode):
    '''Lookup specified opcode in the lookup table'''
    bytes = bytearray(opcode)
    index = bytes[0]
    if index == 0x0f:
        index = bytes[1]
        result, = bytearray([OperandLookupTable[index + 0x100]])
    else:
        result, = bytearray([OperandLookupTable[index]])
    return result

def HasModrm(tval):
    '''Returns True if specified opcode requires a modrm byte'''
    return bool(tval & 0x80)
def HasImmediate(tval):
    '''Returns True if specified opcode contains an immediate value'''
    return bool(tval & 0x40)

def GetImmediateLength(tval, prefixes):
    res = tval & 0x3f

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
