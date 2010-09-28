import bitmap
import optable,decoder
from decoder import isprefix,consume
lookup = optable.Lookup

decode = lambda string: consume(iter(string))

def disassemble(codeblock):
    result = []
    code = iter(codeblock)
    try:
        while True:
            result.append( consume(code) )

    except StopIteration:
        pass

    return result

def new():
    return ('','','','','','')
def length(instruction):
    return len(''.join(instruction))

def stringToNumber(string):
    '''given a string encoded in the native byte-order, will produce an integer'''
    res = bitmap.new(0,0)
    for ch in string:
        res = bitmap.insert(res, (ord(ch),8))
    res,_ = res
    return res

def numberToString(number, bytes):
    '''given an integer and a number of bytes, will return a string encoded in the native endianness'''
    counter = bitmap.new(number,bytes*8)
    res = ''
    while counter[1] > 0:
        counter,_ = bitmap.consume(counter,8)
        res += chr(_)
    return res

#instruction = (prefix, opcode, modrm, sib, disp, immediate)
def getPrefix(instruction): return instruction[0]
def getOpcode(instruction): return instruction[1]
def getModrm(instruction): return instruction[2]
def getSIB(instruction): return instruction[3]
def getDisplacement(instruction): return instruction[4]
def getImmediate(instruction): return instruction[5]

#instruction = (prefix, opcode, modrm, sib, disp, immediate)
def setPrefix(instruction, value):
    n = instruction
    return (value, n[1], n[2], n[3], n[4], n[5])
def setOpcode(instruction, value):
    n = instruction
    return (n[0], value, n[2], n[3], n[4], n[5])
def setModrm(instruction, value):
    n = instruction
    return (n[0], n[1], value, n[3], n[4], n[5])
def setSIB(instruction, value):
    n = instruction
    return (n[0], n[1], n[2], value, n[4], n[5])
def setDisplacement(instruction, value):
    n = instruction
    return (n[0], n[1], n[2], n[3], value, n[5])
def setImmediate(instruction, value):
    n = instruction
    return (n[0], n[1], n[2], n[3], n[4], value)

def isInstruction(value):
    '''returns true if provided a valid instruction'''
    return type(value) is tuple and len(value) == 6

def getRelativeAddress(pc, instruction):
    res = stringToNumber(getImmediate(instruction))
    pc += length(instruction)
    if res & 0x80000000:
        return pc - (0x100000000 - res)
    return pc + res

def isConditionalBranch8(instruction):
    opcode = getOpcode(instruction)
    if len(opcode) == 1:
        ch = ord(opcode[0])
        return ch & 0xf0 == 0x70
    return False

def isConditionalBranch32(instruction):
    opcode = getOpcode(instruction)
    if len(opcode) == 2:
        ch = ord(opcode[1])
        return ch & 0xf0 == 0x80
    return False

def isConditionalBranch(instruction):
    return isConditionalBranch8(instruction) or isConditionalBranch32(instruction)

## regular branches
def isUnconditionalBranch8(instruction):
    '''jmp Jb'''
    return getOpcode(instruction) == '\xeb'
def isUnconditionalBranch32(instruction):
    '''jmp Jz'''
    return getOpcode(instruction) == '\xe9'
def isUnconditionalBranch(instruction):
    return isUnconditionalBranch8(instruction) or isUnconditionalBranch32(instruction)

def isJmpFF(instruction):
    opcode = getOpcode(instruction)
    if opcode == '\xff':
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return reg in [4,5]
    return False
def isShortJmp(instruction):
    opcode = getOpcode(instruction)
    if opcode == '\xff':
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return reg == 4
    return False
def isFarJmp(instruction):
    opcode = getOpcode(instruction)
    if opcode == '\xff':
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return reg == 5
    return False

### XXX: these branch tests will need to be tested
def isRegisterBranch(instruction):
    if isJmpFF(instruction):
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return mod == 3
    return False

def isMemoryBranch(instruction):
    if isJmpFF(instruction):
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return mod < 3
    return False

def isDispBranch(instruction):
    if isJmpFF(instruction):
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return rm == 5 and mod in [1,2]
    return False

def isSibBranch(instruction):
    if isJmpFF(instruction):
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return rm == 4 and mod < 3
    return False

def isAbsoluteBranch(instruction):
    '''jmp Ap'''
    opcode = getOpcode(instruction)
    return opcode == '\xea'

def isRelativeBranch(instruction):
    return isUnconditionalBranch(instruction) or isConditionalBranch(instruction)

def isBranch(instruction):
    return isRelativeBranch(instruction) or isAbsoluteBranch(instruction) or \
        isRegisterBranch(instruction) or isMemoryBranch(instruction) or \
        isDispBranch(instruction) or isSibBranch(instruction)

## calls
def isAbsoluteCall(instruction):
    '''call Ap'''
    return getOpcode(instruction) == '\x9a'

def isRelativeCall(instruction):
    '''call Jz'''
    return getOpcode(instruction) == '\xe8'

def isRegisterCall(instruction):
    '''call Ev'''
    if getOpcode(instruction) == '\xff':
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return reg == 2 and mod == 3
    return False

def isMemoryCall(instruction):
    '''call Mp'''
    if getOpcode(instruction) == '\xff':
        modrm = getModrm(instruction)
        mod,reg,rm = decoder.extractmodrm(ord(modrm))
        return reg in [2,3] and mod < 3
    return False

def isCall(instruction):
    return isRelativeCall(instruction) or isMemoryCall(instruction) or isRegisterCall(instruction) or isAbsoluteCall(instruction)

def isReturn(instruction):
    return getOpcode(instruction) in ['\xc2', '\xc3', '\xca', '\xcb', '\xcf']

if __name__ == '__main__':
    # relative
    if False:
        code = '\xE8\x72\xFB\xFF\xFF'
        insn = decode(code)
        print 'rel',isRelativeCall(insn)

    # register
    # 11 010 110
    if False:
        code = '\xff\xd6'
        insn = decode(code)
        print 'reg',isRegisterCall(insn)

    # memory
    # 00 010 101
    if False:
        code = '\xFF\x15\xC0\x52\x5C\x00'
        insn = decode(code)
        print 'mem',isMemoryCall(insn)

    # forgot
    # 00 100 101
    if False:
        code = '\xFF\x25\xB0\x51\x5C\x00'
        insn = decode(code)
        print repr(insn)
        print 'mem',isBranch(insn),isMemoryBranch(insn)
    
