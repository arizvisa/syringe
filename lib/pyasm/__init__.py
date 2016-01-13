import marshal,opcode
import utils
from assemble import assemble,oplength,assemble_insn
from disassemble import disassemble,fetch_op,fetch_insn

# for lazy typists...
asm = assemble
dis = disassemble

def pretty_dis(obj, address=0):
    ''' returns a disassembly w/ labels '''

    insns = []
    labels = {}

    # collect labels and other fun stuff
    for ofs,mnem,arg,op in disassemble(obj):
        opnum,oparg = op

        if opnum in opcode.hasjrel:
            labels[arg] = ofs
        elif opnum in opcode.hasjabs:
            labels[oparg] = ofs

        insns.append( (ofs, mnem, arg, (opnum,oparg)) )

    insns = iter(insns)
    # format results (might want to align this into some columns
    ## yes, i know the function name is really ironic. ;)
    res = []

    for i in insns:
        ofs, mnem, arg, op = i
        opnum,oparg = op
        mnem = mnem.lower()

        if ofs in labels.keys() and ofs > 0:
            res.append('\nlabel_%x:'% (ofs+address))
        elif ofs in labels.keys():
            res.append('label_%x:'% (ofs+address))

        if oparg == None:
            res.append('    %s'% mnem.ljust(16) )
            continue

        comment = repr(arg)
        if opnum in opcode.hasjrel and arg in labels.keys():
            comment = ''
            arg = 'label_%x'% arg

        elif opnum in opcode.hasjabs and oparg in labels.keys():
            comment = ''
            arg = 'label_%x'% oparg

        else:
            arg = oparg

        if comment:
            comment = '# -> %s'% repr(comment)

        # FIXME: hardcoded length is 32. (why would you need such huge names for a label anyways)
        res.append('    %s %s    %s'% (mnem.ljust(16), str(arg).ljust(32), comment))

        if ofs not in labels.keys():
            if opnum in opcode.hasjrel or mnem.startswith('store') or mnem.startswith('call'):
                res.append('')

    return '\n'.join(res)

if __name__ == '__main__':
    pass
