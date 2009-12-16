import sys
sys.path.append('/Users/arizvisa')
sys.path.append('/Users/arizvisa/ped-inject.git/work')

import ptypes
import psapi,inject
import debugger,memorymanager
import linker

if True:
    print '-'*20 + 'looking for calc.exe'
    ### attach to process
    ps = psapi.getInterface()
    ps.attach()
    processId = inject.getProcessIdByName(ps, 'calc.exe')
    x = ps.enumerateThreads(processId)  # XX: this is slow as fuck

    print '-'*20 + 'attaching to process %d'% processId
    threadId = x[0][0]
    dbg = debugger.Default()
    dbg.enablePrivileges()
    dbg.attach(threadId)

if True:
    print '-'*20 + 'loading sections into memory'
    ld = linker.new()
#    names = ['shit/obj1.obj', 'shit/obj2.obj', 'shit/obj3.obj']
#    for n in names:
#        ld.add( linker.coffstore(n) )
#    ld['_printf'] = 0xcccccccc

    ld.add( linker.coffstore('../obj/inject-helper.obj') )
    ld['_TlsAlloc@0'] = 0x76c02969
    print '\n'.join([repr((k, v is None or hex(v))) for k,v in ld.items()])

if True:
    mm = memorymanager.Default(dbg)

    data = mm.alloc(ld.getsegmentlength('.data'))
    dbg.write(data, ld.getsegment('.data', data))

    text = mm.load(ld.getsegmentlength('.text'))
    dbg.write(text, ld.getsegment('.text', text))
    code = mm.commit(text)

    print '\n'.join([repr((k, hex(v))) for k,v in ld.items()])
    for st in ld.symbolstores:
        print '\n'.join([repr((k, hex(v))) for k,v in st.items()])

if True:
    print 'starting loader'
    stack = mm.alloc(0x40000)
    dbg.write(stack, '\xaa'*0x40000)

    dbg.suspend()
    ctx = dbg.getcontext()
#    ctx['Esp'] = stack + 0x40000 - 4
    ctx['Eip'] = ld['_loader']
#    ctx['Eip'] = ld['_pause']
    l = dbg.setcontext(ctx)
    dbg.resume() 

#if True:
#    mm.free(stack)
#    mm.free(data)
#    mm.unload(text)

#dbg.attach(threadId)
dbg.detach()
