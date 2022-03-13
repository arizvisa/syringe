#instruction = (prefix( opcode, modrm, sib, disp, immediate))
from itertools import islice
from ptypes import bitmap
from . import optable, typesize

prefix_string = b'\x26\x2e\x36\x3e\x64\x65\x66\x67\xf0\xf2\xf3'
prefix_lookup = {bytes(bytearray([item])[:]) : None for item in prefix_string}

def isprefix(byte):
    try:
        prefix_lookup[byte]
        return True
    except KeyError:
        return False

def extractmodrm(byte):
    '''Return (mod,reg,rm)'''
    mod, reg, rm = (byte & 0xc0) >> 6, (byte & 0x38) >> 3, (byte & 7) >> 0
    return mod, reg, rm
def extractsib(byte):
    '''Return (scale,index,byte)'''
    return extractmodrm(byte)
def getsiblength(modrm, sib, prefixes):
    by, = bytearray([modrm])
    mod, reg, rm = extractmodrm(by)
    assert rm == 4

    by, = bytearray([sib])
    scale, index, base = extractsib(by)
    if base == 5:
        return [typesize.word, typesize.byte, typesize.word, 0][mod]
    return 0

def getdisp16length(modrm, prefixes):
    by, = bytearray([modrm])
    return [0, typesize.byte, typesize.halfword, 0][(by & 0xc0) >> 6]
def getdisp32length(modrm, prefixes):
    by, = bytearray(modrm)
    return [0, typesize.byte, typesize.word, 0][(by & 0xc0) >> 6]

def decodeInteger(bytes, signed=False):
    '''given some bytes encoded in the native byte-order, will produce an integer'''
    res, octets = bitmap.new(0,0), bytearray(bytes)
    for octet in octets:
        res = bitmap.append(res, (octet, 8))
    res,_ = res
    if not signed:
        return res

    bitflag = pow(0x100, len(octets)) // 2
    signbit,value = res & bitflag, res & (bitflag - 1)
    if res & signbit:
        return value - bitflag
    return value

def encodeInteger(number, count):
    '''given an integer and a number of bytes, will return a bytes encoded in the native endianness'''
    number &= pow(0x100, count) - 1    # convert to absolute using side-effect of &

    counter = bitmap.new(number, count * 8)
    res = bytearray()
    while counter[1] > 0:
        counter, _ = bitmap.consume(counter, 8)
        res.append(_)
    return bytes(res)

def consume(iterable):
    '''given a byte generator, will consume an instruction'''
    iterable = (bytes(bytearray(by if isinstance(by, bytes) else [by])) for by in iter(iterable))

    ## prefixes and instruction
    instruction, prefixes = b'', b''
    while len(prefixes) < 4:    # XXX: i forgot what the max number of executed prefixes is
        x = next(iterable)
        if isprefix(x):
            prefixes += x
            continue
        instruction += x
        break

    ## instruction
    if not instruction:
        instruction += next(iterable)
    if bytes(instruction) == b'\x0f':
        instruction += next(iterable)

    ## initialize all defaults
    modrm, sib, disp, imm = (b'', b'', b'', b'')
    immlength = displength = 0

    ## modrm
    lookup = optable.LookupTableValue(instruction)
    if optable.HasModrm(lookup):
        modrm = next(iterable)

        by, = bytearray(modrm)
        mod, reg, rm = extractmodrm(by)

        if mod < 3:
            if b'\x67' not in prefixes:
                displength = getdisp32length(modrm, prefixes)
            else:
                displength = getdisp16length(modrm, prefixes)

            if (mod, rm) == (0, 5):
                displength = typesize.word

            elif rm == 4:
                sib = next(iterable)
                #print('modrm',hex(ord(modrm)),extractmodrm(ord(modrm)))
                #print('sib',hex(ord(sib)),extractsib(ord(sib)))

                displength = getdisp32length(modrm, prefixes)   # XXX: i feel like this was hacked in
                if displength == 0:
                    displength = getsiblength(modrm, sib, prefixes)
                pass
            pass
        pass
#    print('disp',displength)
    disp = bytes().join(islice(iterable, displength))

    ## immediates
    if optable.HasImmediate(lookup):
        immlength = optable.GetImmediateLength(lookup, prefixes)

        ## design hack for modrm instructions that don't get an imm due to modrm
        if instruction in [b'\xf6', b'\xf7']:
            if reg not in [0, 1]:
                immlength = 0
            pass

        ## design hack for the 'Ob' operand
        elif instruction in [b'\xa0', b'\xa1', b'\xa2', b'\xa3']:
            immlength = 4
        pass

    imm = bytes().join(islice(iterable, immlength))

    ## done
    return (prefixes, instruction, modrm, sib, disp, imm)

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

    import decoder; reload(decoder)

    def checkinsn():
        if len(''.join(insn)) != len(code):
            print(repr(code))
            print(repr(insn))
            raise ValueError
        return
    def checklist():
        for n in list:
            code = ''.join([chr(int(x,16)) for x in n.split(' ')])
            insn = decoder.consume(code)
            checkinsn()
        return

    if False:
        code = "55 89 e5 83 ec 08 a1 48 26 05 08 85 c0 74 12 b8 00 00 00 00 85 c0 74 09 c7 04 24 48 26 05 08 ff d0 c9 c3"
        code = ''.join([chr(int(x,16)) for x in code.split(' ')])

        print(decoder.consume(b'\xff\x15\xe0\x11\xde\x77'))
    #    import optable
    #    opcode = b'\xff'
    #    lookup = optable.LookupTableValue(opcode)
    #    print(optable.HasImmediate(lookup))

    #    mov edi, [esp+10]
    #    mov [esp], ebx

    if False:
        code = '8b 7c 24 10| 89 1c 24| 90 90 90 90'.replace('|','')
        code = ''.join([chr(int(x,16)) for x in code.split(' ')])

        x = iter(code)
        print(repr(''.join(decoder.consume(x))))

        # i think these should be paired together, and should return a tuple of opcode, argument, type
        labels = ('prefixes', 'instruction', 'modrm', 'disp', 'sib', 'imm')

        list = []
        while code:
            opcode = decoder.consume(code)
            res = {lbl : op for lbl, op in zip(labels, opcode)}
            list.append(res)
            code = code[ len(''.join(opcode)) : ]

        print('\n'.join(['%s -> %d'% (repr(x), len(''.join(x.values()))) for x in list]))

    if True:
        code = '3D 5D 74 D1 05'
        code = ''.join([chr(int(x,16)) for x in code.split(' ')])
        insn = decoder.consume(code)
        checkinsn()

    if True:
        list = ['90 FF 75 0C', 'FF 75 08', 'FF 15 5C 11 60 74']
        checklist()

    if True:
        list = ['6B C0 2C', '50', 'FF 75 0c', 'ff 75 08']
        checklist()

    if True:
        code = b'\x8b\x04\x85\xd0\xe7\xa9\x6f'
#        code = b'\x8d\x0c\xb5\xd8\x8b\xae\x6f'

        source = iter(code + 'a'*80)
        insn = decoder.consume(source)
        checkinsn()

    if True:
        code = b'\x8b\x74\x24\x08'
        code = b'\x8b\x44\x24\x0c'
        code = b'\x8B\x4C\x24\x04'

        source = iter(code)
        insn = decoder.consume(source)
        checkinsn()

    if True:
        code = b'\x8b\x4c\x85\x64'
        code = b'\x89\x7c\x85\x64'
#        code += b'\xcc'*80

        source = iter(code)
        insn = decoder.consume(source)
        checkinsn()

    if True:
        code = 'C7 05 6C B0 88 30 A0 BC 88 30'
        code = [ chr(int(x,16)) for x in code.split(' ') ]
        source = iter(code)

        insn = decoder.consume(source)
        checkinsn()

    if False:
        code = b'\x6b\xc0\x2c'
        lookup = optable.LookupTableValue(b'\x6b')
#        print(optable.HasModrm(lookup),optable.HasImmediate(lookup))

        modrm = b'\xc0'
        mod,reg,rm = decoder.extractmodrm(bytearray([modrm])[0])
#        print(mod,reg,rm)

    if True:
        list = ['f7 d8', '1a c0', '68 80 00 00 00']
        checklist()

    if True:
        code = 'F7 C1 00 01 00 00'
        code = [ chr(int(x,16)) for x in code.split(' ') ]
        source = iter(code)

        insn = decoder.consume(source)
        checkinsn()

    if True:
        code = '80 7C 24 18 01'
        code = [ chr(int(x,16)) for x in code.split(' ') ]
        source = iter(code)

        insn = decoder.consume(source)
        checkinsn()

    if True:
        code = b'\xa0\x50\xc0\xa8\x6f' + b'\xa8\x08' + b'\x75\x18'
        source = iter(code)
        insn = decoder.consume(source)
#        print(insn)

        lookup = optable.LookupTableValue(b'\xa0')
#        print(optable.HasModrm(lookup),optable.HasImmediate(lookup))

    if True:
        import struct
        structed = { 1 : 'b', 2 : 'h', 4 : 'l' }

        def test(number, size):
            n = encodeInteger(number, size)
            a, = struct.unpack(structed[size], n)
            return a == number

        print('1 byte')
        for n in range(-0x80, 0x7f):
            res = test(n, 1)
            if res is True:
                continue
            print(n, 1)

        print('2 byte')
        for n in range(-0x8000, 0x7fff):
            res = test(n, 2)
            if res is True:
                continue
            print(n, 1)

    if False:
        print('4 byte')
        for n in range(-0x80000000, 0x7fffffff):
            res = test(n, 4)
            if res is True:
                continue
            print(n, 1)

    if True:
        code = b'\x9b\xd9\x7d\xfc'
        source = iter(code)
        insn = decoder.consume(source)
        print(insn)
        lookup = optable.LookupTableValue(b'\x9b')
        print(optable.HasModrm(lookup),optable.HasImmediate(lookup))
