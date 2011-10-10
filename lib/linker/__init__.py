import array,store
import coff,elf

from store import BaseAddress

class linker(store.container):
    def __repr__(self):
        return '%s modules %s'% ( super(linker,self).__repr__(), repr([st.modulename for st in self.stores]) )

    def getlocals(self):
        return []
    def getexternals(self):
        return []
    def getglobals(self):
        return super(linker,self).getglobals() + super(linker,self).getexternals()

    def prepare(self, store):
        '''Imports symbol/segment info from the provided store'''
        # segments
        for n in store.listsegments():
            self.addsegment(n, -1, n, store)

        # import externals from the store, but without name translation
        externals = store.getexternals()
        self.merge(store, externals)
        self.scopesegment[None].update(externals)

        # import some globals from a store
        self.merge(store, store.getglobals())

        return self

def new(**kwds):
    return linker()

if __name__ == '__main__':
    import pecoff,ptypes,bitmap,os
    root = bitmap.__file__
    root = root[:root.rindex(os.sep)] + os.sep + '..' + os.sep
    root = root.replace('\\','/')

    import linker
    from linker import coff

#    raise NotImplementedError("Still haven't successfully calculated the target addresses when linking with _everything_")

    # smoke test for coff.object
    if False:
        self = coff.object.open('%s/obj/python-test.obj'%root)

        print self.keys()
        segments = [
            ('.data', 0xccccc000),
            ('.text', 0xaaaaa000),
        ]

        self['__imp_Py_Initialize'] = 0xdddddddd
        self['__imp_PyRun_SimpleStringFlags'] = 0xdddddddd
        self['__imp_Py_Finalize'] = 0xdddddddd

        print self.listsegments()
        for name,baseaddress in segments:
            self[name] = baseaddress

        for name,baseaddress in segments:
            print '-'*70
            ## get useful shit
            data = self.getsegment(name)
            globals = self.getglobalsbysegmentname(name)
            locals = self.getlocalsbysegmentname(name)
            externals = self.getexternals()

            ## output it
            print 'globals', globals
            print 'locals', locals
            print 'externals', externals

            ## relocate segment
            r = self.relocatesegment(name, data)
            print repr(r)
            print ptypes.utils.hexdump(r, offset=baseaddress)
        pass

    # smoke test for coff.executable
    if True:
        #self = coff.executable.open('c:/windows/system32/kernel32.dll')
        #self.open('../obj/test.exe')
        self = coff.executable.open('c:/windows/system32/python26.dll')

        print self.listsegments()

        # assign default segment bases
        ofs = 0
        for name in self.listsegments():
            self[name] = ofs
            ofs += self.getsegmentlength(name)

        # assign externals
        for x in self.getexternals():
            self[x] = 0xdeaddead

#        self['msvcr71.dll!strstr'] = 0x42424242
    
        # write file
        filename = "%s/obj/blah.bin"%root
        out = file(filename, 'wb')

        for name in self.listsegments():
            print '-'*70
            ## get useful shit
            data = self.getsegment(name)
            globals = self.getglobalsbysegmentname(name)
            locals = self.getlocalsbysegmentname(name)
            externals = self.getexternals()

            ## relocate segment
            print 'relocating %s to %08x'% (name, self[name])
            r = self.relocatesegment(name, data)
            out.write(r)

        out.close()

    # FIXME: these addresses are wrong

        if False:
            addresses = file('%s/obj/blah.txt'%(root), 'wt')
            for x in self.globals:
                addresses.write('%s - %x'% (x,self[x]) + "\n")
            addresses.close()

        if False:
            import idc
            input = file('%s/obj/blah.txt'%(root), 'rt')
            lines = input.read().split("\n")
            input.close()

            l = ( x.split(',') for x in lines if x)
            l = ( (a,int(b,16)) for a,b in l )
            for name,offset in l:
             idc.MakeNameEx(offset, name, 0x2)
             idc.MakeCode(offset)

#    raise NotImplementedError

    if False:
        self = coff.executable.open('c:/windows/system32/python26.dll')
        data = self.getsegment('.rdata')

        for x in self.getexternals():
            self[x] = 0x41414141
        data = self.relocatesegment('.rdata', data, 0xdddddddd)
#        print repr(data)

        out = file('out/blah.bin', 'wb')
        out.write(data)
        out.close()

    if False:
        print 'opening file'
        self = pecoff.Archive.open('c:/Python25/libs/python26.lib')
        print 'fetching members'
        for i in self.fetchmembers():
            print repr(i.load())
        print 'fetching imports'
        for i in self.fetchimports():
            print repr(i)
        pass

    if False:
        import random
        names = random.sample(self.getexternals(), 5)
        for n in names:
            self[n] = 0x0abcdef

#        print self.getexternals()
#        print self.getlocals()

        print self.listsegments()

        data = self.getsegment('.idata')
        print self.getglobals()

        data = self.relocatesegment('.idata', data, 0xcccccccc)
        print self.getglobals()
        
        print ptypes.utils.hexdump(data,offset=0xcccccccc)

    if False:
        # this is in shell32.dll
        fullname = 'shlwapi.dll!Ordinal546'
        module,name = fullname.split('!')
        print name

        print 'linker:'
        print fullname in self.keys()
        print fullname,self[fullname]

        print 'store:'
        ugh = lookup[module]
        print name in ugh.keys()
        print name,ugh[name]

    if False:
        dllname = 'c:/windows/syswow64/user32.dll'
        self = coff.executable.open(dllname)

#        raise NotImplementedError("Need to figure out how to import ordinal numbers, and enumerate import modules')
        for n in self.getglobals():
            if self[n]:
                print n, repr(self[n])
            continue
        pass

    if False:
        print '-'*50
        print 'loading .obj file'
        obj = coff.object.open('f:/work/syringe/obj/test.obj')

        print '-'*50
        print 'loading .lib file'
        lib = coff.library.open('c:/python26/libs/python26.lib')

        print '-'*50
        print 'linking them'
        self = linker.new()
        self.add(obj)
        self.add(lib)

    if False:
        dllnames = [
            'msvcr71.dll', 'python26.dll', 'kernel32.dll', 'ntdll.dll', 'advapi32.dll',
            'kernelbase.dll', 'rpcrt4.dll', 'shell32.dll', 'user32.dll', 'msvcrt.dll',
            'gdi32.dll', 'lpk.dll', 'usp10.dll', 'sspicli.dll', 'cryptbase.dll',
            'shlwapi.dll',
            'api-ms-win-core-synch-l1-1-0.dll',
            'api-ms-win-core-fibers-l1-1-0.dll',
            'api-ms-win-core-processthreads-l1-1-0.dll',
            'api-ms-win-core-file-l1-1-0.dll',
            'api-ms-win-core-localregistry-l1-1-0.dll',
            'api-ms-win-core-localization-l1-1-0.dll',
            'api-ms-win-core-libraryloader-l1-1-0.dll',
            'api-ms-win-core-namedpipe-l1-1-0.dll',
            'api-ms-win-core-string-l1-1-0.dll',
            'api-ms-win-core-threadpool-l1-1-0.dll',
            'api-ms-win-core-util-l1-1-0.dll',
            'api-ms-win-core-errorhandling-l1-1-0.dll',
            'api-ms-win-core-sysinfo-l1-1-0.dll',
            'api-ms-win-core-io-l1-1-0.dll',
            'api-ms-win-core-processenvironment-l1-1-0.dll',
            'api-ms-win-core-heap-l1-1-0.dll',
            'api-ms-win-core-misc-l1-1-0.dll',
            'api-ms-win-core-interlocked-l1-1-0.dll',
            'api-ms-win-core-memory-l1-1-0.dll',
            'api-ms-win-core-console-l1-1-0.dll',
            'api-ms-win-core-debug-l1-1-0.dll',
            'api-ms-win-core-profile-l1-1-0.dll',
            'api-ms-win-core-handle-l1-1-0.dll',
            'api-ms-win-core-delayload-l1-1-0.dll',
            'api-ms-win-core-datetime-l1-1-0.dll',
            'api-ms-win-core-rtlsupport-l1-1-0.dll',
            'api-ms-win-security-base-l1-1-0.dll',
            'api-ms-win-security-lsalookup-l1-1-0.dll',
            'api-ms-win-service-core-l1-1-0.dll',
            'api-ms-win-service-management-l1-1-0.dll',
            'api-ms-win-service-management-l2-1-0.dll',
            'api-ms-win-service-winsvc-l1-1-0.dll',
        ]

        lookup = {}
        for name in dllnames:
            print 'loading .dll file %s'% name
            dll = coff.executable.open('c:/windows/syswow64/%s'%name)
            lookup[dll.modulename] = dll

            print 'linking .dll file %s'% name
            self.add(dll)
        pass

    if False:
        for k in self.keys():
            if k.startswith('python26.dll!'):
                self[k] = 0xcccccccc
            continue

    if False:
        segmentnames = self.listsegments()
        segments = {}
        segmentaddress = {}

        # build locations
        address = 0x80000000
        for n in segmentnames:
            segmentaddress[n] = address
            address += 0x1000000

        # output
        print 'segment->(name,address)'
        for n in segmentnames:
            print repr( (n, hex(segmentaddress[n])) )

        # collect segments
        for n in segmentnames:
            segments[n] = self.getsegment(n)
            self[n] = segmentaddress[n]

        # output
        print 'segment->(name,size)'
        for n in segmentnames:
            print (n,len(segments[n]))

        # join things
#        self['__imp__Py_Initialize'] = self['python26.dll!Py_Initialize']  #XXX
#        self['__imp__PyRun_SimpleStringFlags'] = self['python26.dll!PyRun_SimpleStringFlags']  #XXX
#        self['__imp__Py_Finalize'] = self['python26.dll!Py_Finalize']  #XXX

        # relocations
        for n in segmentnames:
            print 'relocating segment',n
            segments[n] = self.relocatesegment(n, segments[n], segmentaddress[n])

        # output of .text
        from ptypes.utils import hexdump
#        print hexdump(segments['.text'], offset=segmentaddress['.text'])

    if False:
        print '-'*50
        for n in self.keys():
            if self[n] is None:
                print n, repr(self[n])
            continue

    if False:
        print '-'*50
        for n in self.keys():
            if not n.startswith('__imp__') and '!' not in n:
                print n, hex(self[n])
            continue
