import psyco
psyco.full()

import linker.coff
from linker import store

m,n='python26.dll','Py_DecRef'
localname = None,'__imp__<%s!%s>'%(m,n)

if True:
    # this should import from python26.lib,Py_DecRef
    # this should export ia32.obj,stuff
    a = linker.coff.object.open('~/work/syringe/src/ia32.obj')
    # imports None,Py_DecRef

    # this should import from python26.dll,Py_DecRef
    # this should export Py_DecRef
    b = linker.coff.library.open('~/python26/libs/python26.lib')
    # imports python26.dll,Py_DecRef
    # exports None,Py_DecRef

    # this should import from whatever
    # and export whatever
    c = linker.coff.executable.open('~/../../windows/syswow64/python26.dll')
    # expots python26.dll,Py_DecRef

    d = linker.coff.executable.open('~/../../windows/syswow64/msvcr100.dll')

#    raise NotImplementedError("symbol consolidation isn't working")
if True:
    z = b

    z[store.BaseAddress] = 0x10000000
    for x in z.undefined:
        z[x] = 0xbbbbbbbb

    out = file('blah','wb')
    for x in z.segments:
        y = z.getsegment(x)
        y = z.relocatesegment(x, y)
        out.write(y)
    out.close()

if False:
    #print a
    #print c

    if True:
        z = linker.new()
        print a
        z.addstore(a)
        print b
        z.addstore(b)
        print c
        z.addstore(c)
        print d
        z.addstore(d)

    if False:
        m,n='msvcr100.dll','_heapmin'
        print True,(None,n) in d.globals
        print False,(None,n) in z.globals

        print False,(m,n) in d.globals
        print True,(m,n) in z.globals

    if False:
        paths = '~/../../windows/syswow64','~/python26/dlls'
#        dlls = 'ntdll.dll','kernel32.dll','python26.dll','msvcr100.dll','shell32.dll','user32.dll','gdi32.dll','pcwum.dll','advapi32.dll','shlwapi.dll','cryptsp.dll','msvcrt.dll','kernelbase.dll','shunimpl.dll','sspicli.dll'
        dlls = 'msvcr100.dll',
        for filename in dlls:
            print 'loading %s'% filename
            for p in paths:
                try:
                    z.addstore(linker.coff.executable.open('%s/%s'%(p,filename)))
                    break
                except IOError:
                    pass
                continue
            continue
        print [(m,n) for m,n in z.undefined if m is None]

    if False:
        modules = set((m for m,n in z.undefined if m is not None))
        print [(m,n) for m,n in z.undefined if m is None]

        for filename in modules:
            if '-' in filename:
                continue

            print 'loading %s'% filename
            for p in paths:
                try:
                    z.addstore(linker.coff.executable.open('%s/%s'%(p,filename)))
                    break
                except IOError:
                    pass
                continue
            continue

    if True:
        z[store.BaseAddress] = 0x10000000
        for x in z.undefined:
            z[x] = 0xbbbbbbbb

    if True:
        print '-'*25
        out = file('blah','wb')
        for x in z.segments:
            y = z.getsegment(x)
            y = z.relocatesegment(x, y)
            out.write(y)
        out.close()

    if False:
        print '-'*25
        for x in a.externals:
            a[x] = 0xbbbbbbbb
        a[store.BaseAddress] = 0x10000000
        b = a.getsegment('.text')
        c = a.relocatesegment('.text',b)
    #    import ptypes
    #    print ptypes.hexdump(c, a['.text'])
