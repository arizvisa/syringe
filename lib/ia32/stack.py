import decoder
import modrm,sib

def PushOpsize(withprefix, withoutprefix):
    def Opsize(insn):
        return [withoutprefix, withprefix]['\x66' in insn[0]]
    return Opsize
def PopOpsize(withprefix, withoutprefix):
    def Opsize(insn):
        return -1 * [withoutprefix, withprefix]['\x66' in insn[0]]
    return Opsize

def constant(value):
    def constant(insn):
        return value
    return constant

def retn(insn):
    p,o,m,s,d,i = insn
    if len(i) == 0:
        return 4
    return 4 + decoder.decodeInteger(i)

def retf(insn):
    p,o,m,s,d,i = insn
    if len(i) == 0:
        return 6
    return 6 + decoder.decodeInteger(i)

def magicbyte(insn):
    p,o,m,s,d,i = insn
    mod,reg,rm = decoder.extractmodrm(m)

    if reg == 6:
        return [4,2]['\x66' in p]
    return 0

# "CALL /Ev/", "FF" # ext="2"             +v-v
# "CALLF /Mptp/", "FF" # ext="3"              +v-v
# "PUSH /Ev/", "FF" # ext="6"             +v

stacktable = [
    (0xff, magicbyte),

    (0x06, constant(2)),                    # push es
    (0x07, constant(-2)),                    # pop es
    (0x0e, constant(2)),                    # push cs

    (0x16, constant(2)),                    # push ss
    (0x17, constant(-2)),                    # pop ss
    (0x1e, constant(2)),                    # push ds
    (0x1f, constant(-2)),                    # pop ds

    (0x50, PushOpsize(2, 4)),            # push {ax,eax}
    (0x58, PopOpsize(2,4)),             # pop {ax,eax}

    (0x60, PushOpsize(16,32)),         # pusha
    (0x61, PopOpsize(16,32)),          # popa

    (0x68, PushOpsize(2, 4)),            # push /Ivs/
    (0x6a, constant(4)),                        # push /Ibss/
    (0x8f, PopOpsize(2,4)),             # pop /Ev/

#    (0x9a, callFar),               # callf /Ap/
    (0x9c, PushOpsize(2,4)),             # pushf
    (0x9d, PopOpsize(2,4)),              # popf
    (0xc2, retn),                 # retn /Iw/
    (0xc3, retn),                  # retn

#    (0xc8, enter),                 # enter /Iw/ /Ib/     # XXX
#    (0xc9, leave),                 # leave ebp(?)

    (0xca, retf),             # retf /Iw/
    (0xcb, retf),                      # retf

#    (0xe8, calllocal),             # call /Jvds/

    (0x1a0, constant(2)),                   # push fs
    (0x1a1, constant(-2)),                   # pop fs
    (0x1a8, constant(2)),                   # push gs
    (0x1a9, constant(-2)),                   # pop gs
]

# all the register pushes
for k in range(0x50,0x57):
    stacktable.append((k, PushOpsize(2,4)))
for k in range(0x58,0x5f):
    stacktable.append((k, PopOpsize(2,4)))

# now everything is callable
stacktable = dict(stacktable)

#instruction = (prefix, opcode, modrm, sib, disp, immediate)
def getDelta(insn):
    p,o,m,s,d,i = insn
    opcode = decoder.decodeInteger(o[-1])
    if len(o) == 2:
        opcode = 0x100 + opcode
    try:
        return stacktable[opcode](insn)
    except KeyError:
        pass

    if m:
        mod,reg,rm = modrm.decode(insn)
        if mod == 3 and reg == 4:
            raise NotImplementedError("arithmetic instruction references esp, but is not yet implemented")
        pass

    if sib:
        scale,index,base = sib.decode(insn)
        if base == 4:
            raise NotImplementedError("read from esp")
        pass
    return 0

if __name__ == '__main__':
    import stack,decoder
    from stack import getDelta

    if False:
        insn = decoder.consume('\x6a\xfe')
        print(getDelta(insn))

    if False:
        insn = decoder.consume( [chr(int(x,16)) for x in '68 88 EA 31 02'.split(' ')])
        print(getDelta(insn))

    if False:
        # shouldn't work due to lack of sib
        insn = decoder.consume( [chr(int(x,16)) for x in '64 A1 00 00 00 00'.split(' ')])
        print(getDelta(insn) == 0)

    if False:
        insn = decoder.consume('\x53')
        print(getDelta(insn))

    if False:
        insn = decoder.consume('\x56')
        print(getDelta(insn))

    # FIXME: need to find all instructions that modify esp too

    if True:
        # fail due to modrm not being fully tested
        insn = decoder.consume('\x83\xec\x50')      # sub esp,50
        print(getDelta(insn))

    if True:
        insn = decoder.consume('\x83\xc4\x04')      # add esp, 4
        print(getDelta(insn))
