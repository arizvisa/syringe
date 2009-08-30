OperandLookupTable = ''.join([
        '\x81\xbd\x81\xbd\x41\x7d\x00\x00\x81\xbd\x81\xbd\x41\x7d\x00\x00',
        '\x81\xbd\x81\xbd\x41\x7d\x00\x00\x81\xbd\x81\xbd\x41\x7d\x00\x00',
        '\x81\xbd\x81\xbd\x41\x7d\x00\x00\x81\xbd\x81\xbd\x41\x7d\x00\x00',
        '\x81\xbd\x81\xbd\x41\x7d\x00\x00\x81\xbd\x81\xbd\x00\x00\x00\x00',
        '\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d',
        '\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d',
        '\x00\x00\xbd\x82\x00\x00\x00\x00\x7d\xbd\x41\xbd\x01\x02\x01\x02',
        '\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41\x41',
        '\xc1\xfd\xc1\xc1\x81\xbd\x81\xbd\x81\xbd\x81\xbd\x82\xbd\xbd\xbd',
        '\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x00\x00\x7a\x00\x00\x00\x00\x00',
        '\x41\x7d\x41\x7d\x01\x02\x01\x02\x00\x00\x01\x02\x01\x02\x01\x02',
        '\x41\x41\x41\x41\x41\x41\x41\x41\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d',
        '\xc1\xc1\x42\x00\xba\xba\xc1\xfd\x42\x00\x42\x00\x00\x41\x00\x00',
        '\x81\xbd\x81\xbd\x41\x41\x00\x01\x84\x84\x84\x84\x84\x84\x82\x82',
        '\x41\x41\x41\x41\x41\x41\x41\x41\x7d\x7d\x7a\x41\x00\x00\x00\x00',
        '\x00\x00\x00\x00\x00\x00\x81\xbd\x00\x00\x00\x00\x00\x00\x81\xbd',
        '\x82\x84\x82\x82\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        '\x84\x84\x88\x88\x88\x88\x88\x88\x81\x00\x00\x00\x00\x00\x00\xbd',
        '\x84\xbc\x84\xbc\x84\x00\x84\x00\x84\x84\x88\x84\x84\x84\x84\x84',
        '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        '\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd\xbd',
        '\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x84\x90\x84\x84\x84\x84',
        '\x84\x84\x84\x84\x84\x84\x84\x88\x88\x88\x88\x88\x90\x90\x84\x88',
        '\x88\xc1\xc1\xc1\x88\x88\x88\x00\x00\x00\x00\x00\x84\x84\x88\x88',
        '\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d\x7d',
        '\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81\x81',
        '\x00\x00\x00\xbd\xbd\xbd\x00\x00\x00\x00\x00\xbd\xbd\xbd\x84\xbd',
        '\x81\xbd\xba\xbd\xba\xba\x81\x82\x00\x00\xbd\xbd\xbd\xbd\x81\x82',
        '\x81\xbd\x84\xbc\xbc\x88\x84\x88\x3d\x3d\x3d\x3d\x3d\x3d\x3d\x3d',
        '\x84\x88\x88\x88\x88\x88\x88\x88\x88\x88\x88\x84\x88\x88\x88\x88',
        '\x88\x88\x88\x88\x88\x88\x84\x88\x88\x88\x88\x88\x88\x88\x88\x88',
        '\x90\x88\x88\x88\x88\x84\x88\x88\x88\x88\x88\x88\x88\x88\x88\x00',
])

## our sizes
wordsize = 4
halfwordsize = wordsize/2
bytesize = halfwordsize/1

prefixes = "\x26\x2e\x36\x3e\x64\x65\x66\x67\xf0\xf2\xf3"
def getPrefixes(string):
    '''given a string, return the prefixes part of the instruction'''
    ## XXX: i'm pretty sure the intel arch only allows a certain number of prefixes
    res = ''
    for x in string:
        if x in prefixes:
            res += x
            continue
        break
    return res

def opcodeLookup(instruction):
    '''given an instruction, return the result of the table lookup'''
    res = ord(instruction[0])
    if res == 0x0f:
        res = ord(instruction[1])
        return OperandLookupTable[res+0x100]
    return OperandLookupTable[res]

def operandHasModrm(v):
    return bool(ord(v[0]) & 0x80)
def operandHasImmediate(v):
    return bool(ord(v[0]) & 0x40)
def operandGetImmediate(string, lookup, prefixes):
    res = ord(lookup) & 0x3f

    opsizeindex = not int('\x66' in prefixes)

    if res == 0x3f:    # it sucks because i know python has such a horrible optimizer, and i need to redo this as a dict for that reason
        size = [ 2*halfwordsize, 2*wordsize ][opsizeindex]
    elif res == 0x3e:
        size = [ bytesize, halfwordsize ][opsizeindex]
    elif res == 0x3d:
        size = [ halfwordsize, wordsize ][opsizeindex]
    elif res == 0x3c:
        size = [ wordsize, wordsize*2][opsizeindex]
    elif res == 0x3b:
        size = [ wordsize*2, halfwordsize ][opsizeindex]
    elif res == 0x3a:
        size = [ halfwordsize + wordsize, wordsize ][opsizeindex]
    else:
        size = res

    return string[:size]

def getInstruction(string):
    '''return the full opcodes (up to 2 bytes)'''
    res = string[0]
    if res == '\x0f':
        res += string[1]
    return res

## prefixes, opcode, modrm, sib, disp, imm
def decode32(string):
    '''given a string to some bytecode, will return a tuple of (prefix, instruction, modrm, disp, sib, immediate)'''
    prefixes = getPrefixes(string)
    string = string[len(prefixes):]

    instruction = getInstruction(string)
    string = string[len(instruction):]

    lookup = opcodeLookup(instruction)

    # initialize all results
    modrm, sib, disp, imm = ('', '', '', '')

    if operandHasModrm(lookup):
        modrm = string[0]
        string = string[1:]

        if '\x67' not in prefixes:
            # get sib
            res = ord(modrm)
            mod,reg,rm = ((res&0xc0) >> 6, (res&0x38) >> 3, (res&7) >> 0)
            if mod < 3 and rm == 4:
                sib = string[0]
                string = string[1:]

            disp = getDisp32(string, modrm, prefixes)
            string = string[len(disp):]

        else:
            disp = getDisp16(string, modrm, prefixes)
            string = string[len(disp):]

    if operandHasImmediate(lookup):
        imm = operandGetImmediate(string, lookup, prefixes)
        string = string[len(imm):]

    return (prefixes, instruction, modrm, disp, sib, imm)

def getSib(string, modrm, prefixes):
    res = [0, wordsize][ (ord(modrm) & 0x7) == 4 ]
    return string[:res]

def getDisp16(string, modrm, prefixes):
    res = [0, bytesize, halfwordsize, 0][ (ord(modrm) & 0xc0)>>6 ]
    return string[:res]

def getDisp32(string, modrm, prefixes):
    res = [0, bytesize, wordsize, 0][ (ord(modrm) & 0xc0)>>6 ]
    return string[:res]

## XXX: default
decode = decode32

if __name__ == '__main__':
    '''
    804876b:       55                      push   %ebp
    804876c:       89 e5                   mov    %esp,%ebp
    804876e:       83 ec 08                sub    $0x8,%esp
    8048771:       a1 48 26 05 08          mov    0x8052648,%eax
    8048776:       85 c0                   test   %eax,%eax
    8048778:       74 12                   je     804878c <read@plt+0xac>
    804877a:       b8 00 00 00 00          mov    $0x0,%eax
    804877f:       85 c0                   test   %eax,%eax
    8048781:       74 09                   je     804878c <read@plt+0xac>
    8048783:       c7 04 24 48 26 05 08    movl   $0x8052648,(%esp)
    804878a:       ff d0                   call   *%eax
    804878c:       c9                      leave
    804878d:       c3                      ret
    '''

    code = "55 89 e5 83 ec 08 a1 48 26 05 08 85 c0 74 12 b8 00 00 00 00 85 c0 74 09 c7 04 24 48 26 05 08 ff d0 c9 c3"
    code = ''.join([chr(int(x,16)) for x in code.split(' ')])

    # i think these should be paired together, and should return a tuple of opcode, argument, type
    labels = ('prefixes', 'instruction', 'modrm', 'disp', 'sib', 'imm')

    list = []
    while code:
        opcode = decode32(code)
        res = dict( zip(labels, opcode) )
        list.append(res)
        code = code[ len(''.join(opcode)) : ]

    print '\n'.join(['%s -> %d'% (repr(x), len(''.join(x.values()))) for x in list])
