from __init__ import *
'''
this module prints out a code object in alternate representations:
    1: marshal.dumps(...)
    2: dis(...)
    3: .co_code
    4: hexdump
    5: pretty_dis

it's pointless, but it was to prove to myself that my assembler worked
'''

import marshal

# get a pretty disassembly
cobj = pretty_dis.func_code
input = pretty_dis(cobj)

## marshal 2 code objects
out1 = file('test_1a.out', 'wb')
out1.write( marshal.dumps(cobj) )
out1.close()
out2 = file('test_1b.out', 'wb')

code = type(eval("lambda:True").func_code)

res = 'argcount nlocals stacksize flags code consts names varnames filename'
res+= ' name firstlineno lnotab freevars cellvars'
res = res.split(' ')
cargs = [ getattr(cobj, 'co_%s'% x) for x in res ]
cargs[4] = asm(input)
# print code.__doc__
reassembled_cobj = code(*cargs)
res = marshal.dumps( reassembled_cobj )
out2.write(res)
out2.close()

### unmarshal them back into an obj
a = marshal.loads( file('test_1a.out', 'rb').read() )
b = marshal.loads( file('test_1b.out', 'rb').read() )

if False:
    function = type(eval("lambda:False"))
    fn_1 = function(a, globals())

### disassembler output
out1 = file('test_2a.out', 'wt')
out2 = file('test_2b.out', 'wt')
out1.write('\n'.join([repr(x) for x in dis(a)]))
out2.write('\n'.join([repr(x) for x in dis(b)]))
out2.close()
out1.close()

### bytecode output
out1 = file('test_3a.out', 'wb')
out2 = file('test_3b.out', 'wb')
out1.write(a.co_code)
out2.write(b.co_code)
out2.close()
out1.close()

### hexdump output
out1 = file('test_4a.out', 'wb')
out2 = file('test_4b.out', 'wb')
out1.write(hexdump(a.co_code))
out2.write(hexdump(b.co_code))
out2.close()
out1.close()

### pretty_dis output
out1 = file('test_5a.out', 'wb')
out2 = file('test_5b.out', 'wb')
out1.write(pretty_dis(a))
out2.write(pretty_dis(b))
out2.close()
out1.close()
