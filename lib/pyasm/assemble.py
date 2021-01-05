#!/usr/bin/env python
import six, struct
from opcode import *

class ParseError(SyntaxError): pass

def evaluate(value):
    '''automagically identify what type of int someone has fed us'''
    base = 10
    if value.startswith('0x'):
        base = 16
        value = value[2:]
    elif value.endswith('b'):
        base = 2
        value = value[:-1]

    return int(value, base)

#def evaluate(expression):
#    '''automagically identify what type of int someone has fed us'''
#    #XXX: let's lean on python's expression evaluator. ;)
#    return eval(expression)

def oplength(opnum):
    res = 1
    if opnum == EXTENDED_ARG:
        res = 6
    elif opnum >= HAVE_ARGUMENT:
        res = 3
    return res

def assemble_insn(opnum, oparg):
    res = ''
    if oparg > 0xffff:
        res += chr(EXTENDED_ARG)
        res += struct.pack('H', oparg // 0x10000)
        oparg &= 0xffff

    res += chr(opnum)
    if oparg is not None:
        res += struct.pack('H', oparg)

    return res

def valid_label(s):
    valid = 'abcdefghijklmnopqrstuvwxyz0123456789.?_'
    return six.moves.reduce( lambda x,y: x+y, [int(x in valid) for x in s] ) == len(s)

def strip_comment(s):
    comm = s.find('#')
    if s.find('#') != -1:
        s = s[ 0 : comm ]
    return s

def parse_insns(input):
    res = {
        'label' : {},
        'insn' : []         # all instructions (line-by-line)
    }

    offset = 0
    linenum = 0
    for line in input.split('\n'):
        line = strip_comment(line).strip()
        if not line:
            continue

        # store our label
        if line.endswith(':') and valid_label(line[:-1]):
            res['label'][line[:-1]] = offset
            continue

        # break an instruction into it's 2 components
        columns = line.split(' ')

        try:
            opnum = opmap[ columns[0].upper() ]

        except KeyError:
            raise ParseError("Unknown instruction '%s' at line %d"% (columns[0], linenum+1))

        res['insn'].append(line)

        # adjust our offset
        offset += oplength(opnum)
        linenum += 1

    return res

def assemble(input):
    labels = []
    instructions = []

    parsed = parse_insns(input)

    res = ''
    linenum = 0
    for insn in parsed['insn']:
        columns = [ c.strip() for c in insn.split(' ') if c ]

        oparg = None
        opnum = opmap[ columns[0].upper() ]

        # branch instructions can take a label or an address
        if opnum in hasjrel or opnum in hasjabs:
            try:
                if columns[1] in parsed['label'].keys():
                    oparg = columns[1]
                else:
                    oparg = int( evaluate(columns[1]) )

                if opnum in hasjrel:
                    oparg = parsed['label'][oparg] - (len(res) + oplength(opnum))

                if opnum in hasjabs:
                    oparg = parsed['label'][oparg]

            except:
                raise ParseError((linenum, 'unable to resolve "%s"'% columns[1]))

        elif opnum in hascompare:
            cmplookup = {value : idx for value, idx in zip(cmp_op, range(len(cmp_op)))}
            try:
                val = eval(columns[1])
                oparg = cmplookup[val]

            except KeyError:
                oparg = evaluate(columns[1])

            print(oparg)
            pass

        # all instructions w/ args
        elif opnum >= HAVE_ARGUMENT:
            oparg = evaluate(columns[1])

        res += assemble_insn(opnum, oparg)
        linenum += 1

    return res

if __name__ == '__main__':
    from disassemble import dis_insns
    input = '''
        load_fast 0
        load_global 1
        compare_op 'is'     #8
        jump_if_false something
        pop_top

        load_const 1
        print_item
        print_newline
        load_const 0
        return_value

        jump_forward check_false

    something:
        pop_top

    check_false:
        load_fast 0
        load_global 2
        compare_op 'is'         #8
        jump_if_false leave
        pop_top

        load_const 2
        print_item
        print_newline
        jump_forward leave
        pop_top

    leave:
        load_const 0
        return_value
    '''

    bytes = assemble(input)
    print(repr(bytes))

    print(input)
    print('\n'.join([ '%d> %s %s'%( x[2], opname[x[0]], x[1]) for x in dis_insns(iter(bytes)) ]))
