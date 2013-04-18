import bitmap

def consume(iterable, bits=(32-6,)):
    source = bitmap.consumer(iterable)
    special = source.consume(6)

    result = []
    for b in bits:
        s = abs(b)

        sf,mask = 2**(s-1), (2**(s-1))-1
        x = source.consume(s)

        if b < 0:
            if x & sf:
                x = x & mask
                x *= -1
            else:
                x &= mask

        result.append(x)

    return special,tuple(result)

def decode(string, *args, **kwds):
    return consume( iter(string), *args, **kwds )

if True:
    a = bitmap.new(0x0b058547, 32)
    b = bitmap.data(a)

    print bitmap.string(a)
    j,(instr_index,) = decode(b)
    print hex(instr_index<<2)

    #RAM:8C161580 0B 05 85 47                             j       loc_9FC7A134     # [note] simulator branches to 8c16151c
    #AC 82 00 00
    #ROM:9FC7A138 14 40 FF D0                             bnez    $v0, loc_9FC7A07C
    #RAM:8C161560 14 40 FF D0                             bnez    $v0, loc_9FC7A0BC  # 8c1614a4 #8c161564

if True:
    a = bitmap.new(0x1440ffd0, 32)
    b = bitmap.data(a)

    addr,(bne,(rs,rt,offset)) = 0x8c161560, decode(b, (5,5,-16))
    print '%x: bne $%d, $%d, %x   # %x'%(addr, rs,rt,offset, addr+4+(offset*4))

    print hex(0x8c161560+4 + -0x1ff40)

if True:
    a = bitmap.new(0x11000003, 32)
    b = bitmap.data(a)
    addr,(beq,(rs,rt,offset)) = (0x8C100048,decode(b, (5,5,-16)))
    print '%x: beq $%d, $%d, %x   # %x'%(addr, rs,rt,offset, addr+4+(offset*4))
