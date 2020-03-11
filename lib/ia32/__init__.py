''' lol, i really really wasn't expecting this to turn into a serious disassembler...  '''

import optable,decoder,modrm

# XXX: figure out how to add these explicit imports to the doc output
#      for this module. (without having to use __all__)

from decoder import isprefix,consume,decodeInteger,encodeInteger
lookup = optable.Lookup

# equivalent to decoder.consume(iter(string)) ->
#     (prefix, opcode, modrm, sib, disp, immediate)
decode = lambda string: consume(iter(string))

def extractmodrm(instruction):
    '''Return the (Mod, Reg, r/m) components of an instruction'''
    modrm = getModrm(instruction)
    return decoder.extractmodrm( decodeInteger(modrm) )

def extractsib(instruction):
    '''Returns (scale,index,base) of an instruction'''
    sib = getSib(instruction)
    return decoder.extractsib( decodeInteger(sib) )

def disassemble(codeblock):
    '''Disassembles string into a list of instruction tuples'''
    result = []
    code = iter(codeblock)
    try:
        while True:
            result.append( consume(code) )

    except StopIteration:
        pass

    return result

def new():
    '''A new empty instruction'''
    return ('','','','','','')

def length(instruction):
    return len(''.join(instruction))

def stringToNumber(string):
    '''This function name is deprecated in favor of encodeInteger'''
    return decodeInteger(string)
def numberToString(number, bytes):
    '''This function name is deprecated in favor of encodeInteger'''
    return encodeInteger(number, bytes)

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
    return isinstance(value, tuple) and len(value) == 6

def promoteBranch(instruction, size):
    return { 1 : promoteBranch_8, 2 : promoteBranch_16, 4 : promoteBranch_32 }[size](instruction)

def promoteBranch_8(instruction):
    '''Promote(?) instruction to an 8-bit branch'''
    imm = getImmediate(instruction)
    offset = decodeInteger(imm, True)
    prefix = ''.join([x for x in getPrefix(instruction) if x != '\x66'])

    if isConditionalBranch8(instruction) or isUnconditionalBranch8(instruction) or isRelativeCall(instruction):
        result = instruction
        offset += length(result)

    elif isUnconditionalBranch(instruction):
        result = setOpcode(instruction, '\xeb')

    elif isConditionalBranch(instruction):
        column = ord(getOpcode(instruction)[1]) & 0xf
        result = setOpcode(instruction, chr(column | 0x70))
    else:
        raise NotImplementedError('Unable to promote a non-branch instruction to 8-bits: {!r}'.format(n))

    result = setPrefix(setImmediate(result, '\x00'), prefix)
    return setImmediate(result, encodeInteger(offset-length(result), 1))

def promoteBranch_32(instruction):
    imm = getImmediate(instruction)
    offset = decodeInteger(imm, True) + length(instruction)
    prefix = ''.join([x for x in getPrefix(instruction) if x != '\x66'])

    if isConditionalBranch8(instruction):
        column = ord(getOpcode(instruction)) & 0xf
        result = setOpcode(instruction, '\x0f'+chr(column | 0x80))

    elif isUnconditionalBranch8(instruction):
        result = setOpcode(instruction, '\xe9')

    elif isRelativeCall(instruction) or isUnconditionalBranch(instruction) or isConditionalBranch(instruction):
        result = instruction
    else:
        raise NotImplementedError('Unable to promote a non-branch instruction to 32-bits: {!r}'.format(n))

    result = setPrefix(setImmediate(result, '\x00\x00\x00\x00'), prefix)
    return setImmediate(result, encodeInteger(offset-length(result), 4))

def promoteBranch_16(instruction):
    raise NotImplementedError("16-bit absolute branches not implemented really")
    result = promoteBranch_32(instruction)

    imm = getImmediate(result)
    offset = decodeInteger(imm, True) - length(result)

    # downgrade the opcode
    prefix = getPrefix(result)
    if '\x66' not in prefix:
        prefix += '\x66'
    result = setPrefix(result, prefix)

    offset += length(result)

    return setImmediate(result, encodeInteger(offset, 2))

def getRelativeAddress(pc, instruction):
    '''Given the specified instruction and address, will return the target branch address'''
    imm = getImmediate(instruction)
    l = len(imm)

    ofs = decodeInteger(imm)
    pc += length(instruction)

    if (l == 4) and (ofs & 0x80000000):
        return pc - (0x100000000 - ofs)

    elif (l == 2) and (ofs & 0x8000):
        return pc - (0x10000 - ofs)

    elif (l == 1) and (ofs & 0x80):
        return pc - (0x100 - ofs)

    # otherwise we're just jumping forward
    return pc + ofs

def setRelativeAddress(source, instruction, target):
    # subtract the old instruction length
    instructionlength = length(instruction)
    res = target - source - instructionlength

    if res >= -0x80 and res < 0x80:
        result = promoteBranch_8(instruction)
        sz = length(result) - length(instruction)
        return setImmediate(result, encodeInteger(res-sz, 1))

#    elif res >= -0x8000 and res < 0x8000:
#        result = promoteBranch_16(instruction)
#        sz = length(result) - length(instruction)
#        return setImmediate(result, encodeInteger(res-sz, 2))

    elif res >= -0x80000000 and res < 0x80000000:
        result = promoteBranch_32(instruction)
        sz = length(result) - length(instruction)
        return setImmediate(result, encodeInteger(res-sz, 4))

    raise NotImplementedError("Unable to figure out immediate value size for %x"% res)

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

### XXX: these branch tests will need to be legitimately tested
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
    '''retn and friends'''
    return getOpcode(instruction) in ['\xc2', '\xc3', '\xca', '\xcb', '\xcf']

if __name__ == '__main__':
    import ia32

    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)

            except Success:
                print('%s: Success'% name)
                return True

            except Failure as E:
                pass

            print('%s: Failure'% name)
            return False

        TestCaseList.append(harness)
        return fn

    # relative
    if False:
        code = '\xE8\x72\xFB\xFF\xFF'
        insn = decode(code)
        print('rel',isRelativeCall(insn))

    # register
    # 11 010 110
    if False:
        code = '\xff\xd6'
        insn = decode(code)
        print('reg',isRegisterCall(insn))

    # memory
    # 00 010 101
    if False:
        code = '\xFF\x15\xC0\x52\x5C\x00'
        insn = decode(code)
        print('mem',isMemoryCall(insn))

    # forgot
    # 00 100 101
    if False:
        code = '\xFF\x25\xB0\x51\x5C\x00'
        insn = decode(code)
        print(repr(insn))
        print('mem',isBranch(insn),isMemoryBranch(insn))

    if False:
        code = '\x0f\x0f\xe1\xb4'
        insn = decode(code)
        print(getOpcode(insn) == '\x0f\x0f')
        print(getModrm(insn) == '\xe1')
        print(getImmediate(insn) == '\xb4')

    @TestCase
    def relative_0():
        code = '\x0f\x85\x16\x01\x00\x00'
        n = decode(code)
        address = 0x100ee82a
        target = 0x100ee946
        if getRelativeAddress(address, n) == target:
            raise Success
        return

    @TestCase
    def relative_1():
        code = '\x74\x26'
        n = decode(code)
        address = 0x100EE836
        target = 0x100EE85E
        if getRelativeAddress(address, n) == target:
            raise Success
        return

    @TestCase
    def relative_2():
        code = '\x75\xdb'
        n = decode(code)
        address = 0x100EED78
        target = 0x100EED55
        if getRelativeAddress(address, n) == target:
            raise Success
        return

    @TestCase
    def relative_3():
        code = '\x0f\x86\xa2\x05\x00\x00'
        n = decode(code)
        address = 0x101781a3
        target = 0x1017874B
        if getRelativeAddress(address, n) == target:
            raise Success
        return

    @TestCase
    def relative_4():
        code = '\x0f\x8c\x97\xfa\xff\xff'
        n = decode(code)
        address = 0x10178743
        target = 0x101781E0
        if getRelativeAddress(address, n) == target:
            raise Success
        return

    @TestCase
    def promote_0():
        '''8b to 8b'''
        a = decode('\xeb\xfe')
        b = promoteBranch_8(a)
        if a == b:
            raise Success
        return

#    @TestCase
    def promote_1():
        '''16b to 16b'''
        a = decode('\x66\xe9\xfe\xff')
        b = promoteBranch_16(a)
        if a == b:
            raise Success
        print(repr(a))
        print(repr(b))
        return

    @TestCase
    def promote_2():
        '''32b to 32b'''
        a = decode('\x0F\x84\x14\x2D\xFC\xFF')
        b = promoteBranch_32(a)
        if a == b:
            raise Success
        return

    @TestCase
    def promote_3():
        '''8b to 32b forwards'''
        a = decode('\x7f\x0c')
        b = decode('\x0f\x8f\x08\x00\x00\x00')
        if promoteBranch_32(a) == b:
            raise Success
        return

#    @TestCase
    def promote_4():
        '''8b to 16b'''
        # XXX: this doesn't disassemble correctly in windbg
        a = decode('\xeb\x0b')
        b = decode('\x66\xe9\x08\x00f')
        a = promoteBranch_16(a)
        if a == b:
            raise Success
        print(repr(a))
        print(repr(b))
        return

    @TestCase
    def promote_5():
        '''8b to 32b backwards'''
        a = decode('\xeb\xe1')
        b = decode('\xe9\xde\xff\xff\xff')
        if promoteBranch_32(a) == b:
            raise Success
        return

    @TestCase
    def Test_0():
        code = '\xeb\xfe'

        n = setRelativeAddress(0x77be0000, decode(code), 0x77be0000)
        if ''.join(n) == '\xeb\xfe':
            raise Success
        return

    def test_set(source, instruction, target):
        n = decode(instruction)
        x = setRelativeAddress(source, n, target)
        res = getRelativeAddress(source, n)

        if res != target:
            print('%x -- %x != %x'% (source,res,target))
            raise Failure
        raise Success

    @TestCase
    def Test_1():
        code = '\xE9\x9F\x91\xFF\xFF'
        test_set(0x7deb7534, code, 0x7deb06d8)

    @TestCase
    def Test_2():
        code = '\x0F\x85\xEC\x6D\x00\x00'
        test_set(0x7deb073f, code, 0x7deb7531)

    @TestCase
    def Test_3():
        code = '\x75\x18'
        test_set(0x7deb0927, code, 0x7deb0941)

    @TestCase
    def Test_4():
        code = '\x72\xd3'
        test_set(0x7deafc45, code, 0x7deafc1a)

    @TestCase
    def Test_5():
        code = '\x75\x09'
        test_set(0x1000d6ae, code, 0x1000d6b9)

    @TestCase
    def Test_6():
        code = '\x75\xde'
        test_set(0x1000d670, code, 0x1000d650)

    @TestCase
    def Test_7():
        code = '\xe8\x47\x4f\x37\x00'
        test_set(0x1000d6b4, code, 0x10382600)

    @TestCase
    def Test_8():
        code = '\x66\xe9\x42\x03'
        test_set(0x1000e1b5, code, 0x1000e4fb)

    @TestCase
    def Test_9():
        code = '\x66\xe9\x42\xd3'
        test_set(0x10006418, code, 0x1000375e)

    @TestCase
    def Test_a():
        code = '\x0F\x85\xAE\xF1\xFF\xFF'
        test_set(0x7deb0aca, code, 0x7deafc7e)

    @TestCase
    def Test_b():
        code = '\xe9\xfa\xfe\x54\x89'
        test_set(0x76ec010f, code, 0x41000e)

    @TestCase
    def Test_c():
        code = '\xe9\xec\xff\xff\xff'
        test_set(0x40000f, code, 0x400000)

    @TestCase
    def Test_d():
        code = '\xeb\xf0'
        n = ia32.promoteBranch_32( ia32.decode(code) )
        if ''.join(n) == '\xe9\xed\xff\xff\xff':
            raise Success
        print(repr(decode(code)), repr(n))
        raise Failure

    @TestCase
    def Test_e():
        code = '\xe9\xc1\xfe\xff\xff'
        test_set( 0x101d70e9, code, 0x101d6faf )

    @TestCase
    def Test_f():
        code = '\xe9\xa6\x00\x00\x00'
        test_set( 0x101dc252, code, 0x101dc2fd )

    if False:
        code = '\x0f\x85\x7f\xff\xff\xff'
        n = setRelativeAddress(0, decode(code), -5)
        print(hex(getRelativeAddress(0, n)))
        n = setRelativeAddress(0, decode(code), 0x2)
        print(repr(n))
        print(hex(getRelativeAddress(0, n)))
        print(hex(decodeInteger(getImmediate(n)) + length(n)))

    if False:
        code = '\x77\x08'
        code = '\x0f\x87\x04\x00\x00\x00'
        n = decode(code)
        x = promoteBranch_8(n)
        print(repr(x))

        print('%x:%x -> %x'% (0x70, 0x72, 0x7a))

    @TestCase
    def Test_10():
        res = '''
        b8b5000000ba0003fe7fff12c20c00b8b6000000ba0003fe7fff12c21800b8b7000000ba0003fe7fff12c22400b8b8000000ba0003fe7fff12c22400b8b9000000ba0003fe7fff12c21800b8ba000000ba0003fe7fff12c21400b8bb000000ba0003fe7fff12c20400b8bc000000ba0003fe7fff12c20800b8bd000000ba0003fe7fff12c20c00b8be000000ba0003fe7fff12c21400
        6a1468082d917ce85cbcffff8a1dc0e1977c8b750c33d23bf20f85f81602008b7d103bfa740289178b4d08f7c1fcffffff0f851cbb02003bfa0f842dbb02008bc183e0020f85d416020084db754a33db4384cb0f84821d00006878e1977c3bc20f8597170200e832e3feff85f60f8536bb020064a118000000b9d8e0977cf00fc1194381e3ffff00008b402425ff0f0000c1e0100bd8891f33f68bc6e802bcffffc20c0090ffffffff43e8937c5ee8937c90909090906a0c68802d917ce8a6bbffff8b5508f7c2feffffff0f85b8bb02008b4d0c85c97436f7c1000000f00f85bebb020064a118000000c1e91033482466f7c1ff0f0f85a7bb0200f6c2010f84107a01006878e1977ce86fe3feff33c0e88ebbffffc208009090909090ffffffff23e9937c3ee9937c90909090908bff558bec8b45145333db3bc3568b75080f8c04b60200895e048bc8c1e1100bc88b
        6a186868d7917ce8c411ffff33db895de4895de0a0c0e1977c895ddc895dd8381dc4e0977c0f8599db0000895dfc3ac374528d45e050ff7508e8ce56ffff84c074118b45e06639583a0f85f0e6010080483604834dfcffe8220000008b45e4e8a711ffffc20400909090909090ffffffff000000004bbe937c9090909090395ddc751cc38d45d8505353e8d954ffff8945e43bc37cbdc745dc01000000eb93ff75d86a01e87555ffffebd88b85f0fdffff56ffb5e8fdffffc603006a016a00ff7004ffb5ecfdffffe8c0e6ffff8bf885ff0f8cae550200ff36e8b5eaffffff36ffb5ecfdffffe8ebe8ffff8bf885ff0f8d76f9ffffe9c85502008b4df88b4508
        ddd8d9eec3ddd8ddd8d9e8c3dbbd62ffffffdbad62fffffff68569ffffff407408c68570ffffff07c3c68570ffffff01dc05c80e987cc3d9c9dbbd62ffffffdbad62fffffff68569ffffff407409c68570ffffff07eb07c68570ffffff01dec1c3dbbd62ffffffdbad62fffffff68569ffffff407420d9c9dbbd62ffffffdbad62fffffff68569ffffff407409c68570ffffff07eb07c68570ffffff01dec1c3ddd8ddd8db2d68e0977c80bd70ffffff007f07c68570ffffff010ac9c30ac97402d9e0c390ccccccccccccc68570ffff
        ddd8ddd8d9e8c3dbbd62ffffffdbad62fffffff68569ffffff407408c68570ffffff07c3c68570ffffff01dc05c80e987cc3d9c9dbbd62ffffffdbad62fffffff68569ffffff407409c68570ffffff07eb07c68570ffffff01dec1c3dbbd62ffffffdbad62fffffff68569ffffff407420d9c9dbbd62ffffffdbad62fffffff68569ffffff407409c68570ffffff07eb07c68570ffffff01dec1c3ddd8ddd8db2d68e0977c80bd70ffffff007f07c68570ffffff010ac9c30ac97402d9e0c390ccccccccccccc68570fffffffe0aed75
        ddd8ddd8db2d68e0977c80bd70ffffff007f07c68570ffffff010ac9c30ac97402d9e0c390ccccccccccccc68570fffffffe0aed753fd9c9d9f1eb0dc68570fffffffe32edd9eadec9e83f010000d9e8dec1f68561ffffff017404d9e8def1f6c2407502d9fd0aed0f84e4feffffd9e0e9ddfeffffe8560100000bc0748232ed83f8027402f6d5d9c9d9e1ebabe9d3feffffe969ffffffddd8ddd8db2d80e0977cc68570ffffff02c3d9edd9c9d9e49bddbd60ffffff9bf68561ffffff410f853cffffffd9f1c3c68570ffffff02ddd8
        ddd8db2d68e0977c80bd70ffffff007f07c68570ffffff010ac9c30ac97402d9e0c390ccccccccccccc68570fffffffe0aed753fd9c9d9f1eb0dc68570fffffffe32edd9eadec9e83f010000d9e8dec1f68561ffffff017404d9e8def1f6c2407502d9fd0aed0f84e4feffffd9e0e9ddfeffffe8560100000bc0748232ed83f8027402f6d5d9c9d9e1ebabe9d3feffffe969ffffffddd8ddd8db2d80e0977cc68570ffffff02c3d9edd9c9d9e49bddbd60ffffff9bf68561ffffff410f853cffffffd9f1c3c68570ffffff02ddd8db2d8ae0977cc30ac90f8523ffffffc3d9ec
        c68570ffffff010ac9c30ac97402d9e0c390ccccccccccccc68570fffffffe0aed753fd9c9d9f1eb0dc68570fffffffe32edd9eadec9e83f010000d9e8dec1f68561ffffff017404d9e8def1f6c2407502d9fd0aed0f84e4feffffd9e0e9ddfeffffe8560100000bc0748232ed83f8027402f6d5d9c9d9e1ebabe9d3feffffe969ffffffddd8ddd8db2d80e0977cc68570ffffff02c3d9edd9c9d9e49bddbd60ffffff9bf68561ffffff410f853cffffffd9f1c3c68570ffffff02ddd8db2d8ae0977cc30ac90f8523ffffffc3d9eceb02d9edd9c90ac90f8510ffffffd9f1c3
        d9c0d9fcd8d99bdfe09e751ad9c0dc0dea0e987cd9c0d9fcded99bdfe09e740db801000000c3b800000000ebf8b802000000ebf15683ec748bf45683ec08dd1c2483ec08dd1c249bdd7608e8d988030083c414dd6608dd0683c4745e85c00f85dffdffffeb05e9d8fdffffc3cccccccccc558bec5756538b4d100bc974408b75088b7d0cb741b35ab6208d098a26468a07473ae074183ae772063ae3770202e63ac772063ac3770202c63ae0750749740debd9eb09b9ffffffff7202f7d98bc15b5e5fc9c38b442404538b4c240c56578b5004558b70088b780c8b298bdf33de23da33df03dd8b288d9c1d78a46ad7c1c3078bc603da33c223c38b690433c603fd0556b7c7e803f8c1c70c8bc203fb33c323c78b690833c203f505db70202403
        8bff558bec5151dd450856dc15f817957c33d233f6dfe0f6c4057a02d9e0b80000f07fdd5df8394514b90000f0ff753e3955107578dd45f8dc1de817957cdfe0f6c4410f8482000000dd45f8dc1de817957cdfe0f6c4058b45180f8b89000000dd05f80f987c33f646e9ef000000394d14753a3955107535dd45f8dc1de817957cdfe0f6c4417507d9eee9cb000000dd45f8dc1de817957cdfe0f6c4058b45187abedd05f00f987ce9b000000039450c753f3955080f85a4000000dd4510dc1df817957cdfe0f6c441750bdd05f00f987ce984000000dd4510dc1df817957cdf
        '''.strip().split('\n')

        source = iter(res[0].decode('hex'))

        import ia32
        print(repr(ia32.consume(source)))
        raise NotImplementedError


if __name__ == '__main__':
    results = []
    for t in TestCaseList:
        results.append( t() )
    pass
