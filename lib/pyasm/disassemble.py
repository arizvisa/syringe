import opcode

### instruction fetching
def fetch_op(iterable):
    length = 0

    opnum = ord( iterable.next() )
    oparg = None
    
    length += 1
    
    if opnum >= opcode.HAVE_ARGUMENT:
        oparg = ord(iterable.next()) + ord(iterable.next())*256
        length += 2
        
    return (opnum, oparg, length)

def fetch_insn(iterable):
    '''fetch next instruction also handling the EXTENDED_ARG opcode'''
    oparg = length = 0
    while True:
        
        op, arg, n = fetch_op(iterable)
        length += n
        
        if arg is None:
            oparg = arg
            break

        oparg += arg
        if op == opcode.EXTENDED_ARG:
            oparg *= 0x10000
            continue

        break

    return (op, oparg, length)

def dis_insns(iterable):
    '''yield op,arg,offset given some bytecode'''
    offset = 0
    while True:
        op, arg, length = fetch_insn(iterable)
        yield op, arg, offset
        offset += length

def disassemble(object):
    '''
    given a code object, yield (address, opname, arg, op) for each instruction

    address: current address into bytecode
    opname: text mnemonic of opcode
    arg: resolved oparg
    op: (opnum, oparg) - a tuple containing the actual instruction
    '''
    code = iter(object.co_code)
    free = object.co_cellvars + object.co_freevars
    
    for op,oparg,offset in dis_insns(code):
        arg = None
        
        # if the opcode # is in the opcode module's list of opcodes that have a constant
        # then grab the constant
        if op in opcode.hasconst:
            arg = object.co_consts[oparg]
    
        # if the opcode # is in the opcode module's list of opcodes that have a name
        # grab the name by its index
        elif op in opcode.hasname:
            arg = object.co_names[oparg]
    
        elif op in opcode.hasjrel:
            arg = offset + oparg + 3
            if oparg > 0xffff:    #XXX: this is for EXTENDED_ARG
                arg += 3

        elif op in opcode.hasjabs:
            arg = oparg
    
        elif op in opcode.haslocal:
            arg = object.co_varnames[oparg]
    
        elif op in opcode.hascompare:
            arg = opcode.cmp_op[oparg]
    
        elif op in opcode.hasfree:
            arg = free[oparg]
    
        yield offset, opcode.opname[op], arg, (op,oparg)

if __name__ == '__main__':
    blah = '''
    def fn():
        print 'wtf'
    '''

    import compiler
    cobj = compiler.compile(blah.strip(), 'none', 'single')

    cobj = cobj.co_consts[1]
    res = [repr(x) for x in disassemble(cobj)]
    print '\n'.join(res)
