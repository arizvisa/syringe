from ptypes import bitmap

def consume(iterable, bits=32 - 6):
    source = bitmap.consumer(iterable)
    special = source.consume(6)

    result = []
    for item in [bits] if not hasattr(bits, '__iter__') else bits:
        size = abs(item)

        sf, mask = pow(2, size - 1), pow(2, size - 1) - 1
        value = source.consume(size)

        if item < 0:
            if value & sf:
                value = value & mask
                value *= -1
            else:
                value &= mask

        result.append(value)

    return special, tuple(result)

def decode(bytes, *args, **kwds):
    iterable = iter(bytes)
    return consume(iterable, *args, **kwds)

if __name__ == '__main__':
    #RAM:8C161580 0B 05 85 47                             j       loc_9FC7A134     # [note] simulator branches to 8c16151c
    #AC 82 00 00
    #ROM:9FC7A138 14 40 FF D0                             bnez    $v0, loc_9FC7A07C
    #RAM:8C161560 14 40 FF D0                             bnez    $v0, loc_9FC7A0BC  # 8c1614a4 #8c161564

    if True:
        a = bitmap.new(0x0b058547, 32)
        b = bitmap.data(a)

        print(bitmap.string(a))
        j, (instr_index,) = decode(b)
        print("{:#x}".format(instr_index * pow(2, 2)))

    if True:
        a = bitmap.new(0x1440ffd0, 32)
        b = bitmap.data(a)

        addr, (bne, (rs, rt, offset)) = 0x8c161560, decode(b, [5, 5, -16])
        print('%x: bne $%d, $%d, %x   # %x'%(addr, rs, rt, offset, addr + 4 + (4 * offset)))

        print(hex(0x8c161560+4 + -0x1ff40))

    if True:
        a = bitmap.new(0x11000003, 32)
        b = bitmap.data(a)
        addr, (beq, (rs, rt, offset)) = (0x8C100048, decode(b, [5, 5, -16]))
        print('%x: beq $%d, $%d, %x    # %x'%(addr, rs, rt, offset, addr + 4 + (4 * offset)))
