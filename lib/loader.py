from warnings import warn

class module(object):
    segments = None
    linker = None

    def __init__(self, ld):
        self.linker = ld
        self.segments = {}

    def __getattr__(self, name):
        # passthrough to the linker
        return getattr(self.linker, name)

    def __getitem__(self, name):
        return self.linker[name]

    def __setitem__(self, name, value):
        self.linker[name] = value

    def __loadsegment(self, length, load, commit):
        ld = self.linker
        data = load(length)
        yield (data,length)
        yield (commit(data),length)

    def __deallocatesegment(self, name, mm):
        address,length,protection = self.segments[name]
        if protection == 6:
            return mm.free(address)
        elif protection == 5:
            return mm.unload(address)
        raise NotImplementedError

    def __allocatesegments(self, mm):
        ld = self.linker

        # prepare allocators
        segments = {}
        for name in ld.listsegments():
            p,length = ld.getsegmentprotection(name),ld.getsegmentlength(name)
            if p & 5 == 5:   # r-x
                allocator = self.__loadsegment(length, mm.load, mm.commit)
            elif p & 6 == 6: # rw-
                allocator = self.__loadsegment(length, mm.alloc, lambda x: x)
            elif p & 4 == 4: # r--
                allocator = self.__loadsegment(length, mm.load, mm.commit)  # should probably not allow this to be +x too
            else:
                raise NotImplementedError(hex(p))

            segments[name] = (p,allocator)

        return segments

    def __writesegments(self, segments, mm):
        ld = self.linker

        # allocate space for section bases
        loadedsegments = {}
        for name,(protection,allocator) in segments.items():
            address,length = allocator.next()
            loadedsegments[name] = (address,length)
            print 'mapping %s:+%x to %x'%(name, length, address)

        # produce a lookup dict
        sectionbases = dict([(name,address) for name,(address,length) in loadedsegments.items()])
        for k in sectionbases:
            ld[k] = sectionbases[k]

        # fill sections
        for name,(address,length) in loadedsegments.items():
            print 'allocated %x:+%x bytes for segment %s'%(address,length,name)
            if length == 0:
                print '  skipping 0 length segment', name
                continue

            data = ld.getsegment(name)
            data = ld.relocatesegment(name, data, sectionbases[name])

            mm.write(sectionbases[name], data)

            # lock it
            protection,allocator = segments[name]
            address,length = allocator.next()

            segments[name] = (address, length, protection)

            print 'wrote segment %s to %x:%x'%(name,address,address+length)
        return segments

    def inject(self, mm):
        self.segments = {}
        segments = self.__allocatesegments(mm)
        self.segments = self.__writesegments(segments, mm)
        return

    def unload(self, mm):
        for name in self.segments.keys():
            self.__deallocatesegment(name, mm)
            name,address,length=self.segments[name]
            del(self.segments[name])
            print 'Unloaded segment %s at %x:%x'%(name,address,address+length)
        return

if __name__ == '__main__':
    import sys
    import linker,loader,memorymanager
    pid = 1832
    pid = int(sys.argv[1])
    mm = memorymanager.new(allocator=memorymanager.allocator.WindowsProcessId(pid))

    if True:
        import ndk
        import ctypes
        ntdll = ctypes.WinDLL('ntdll.dll')
        def getProcessBasicInformation(handle):
            class ProcessBasicInformation(ctypes.Structure):
                _fields_ = [('Reserved1', ctypes.c_uint32),
                            ('PebBaseAddress', ctypes.c_uint32),
                            ('Reserved2', ctypes.c_uint32 * 2),
                            ('UniqueProcessId', ctypes.c_uint32),
                            ('Reserved3', ctypes.c_uint32)]

            pbi = ProcessBasicInformation()
            res = ntdll.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
            assert res == 0
            return pbi

        ###
        pbi = getProcessBasicInformation(mm.allocator.handle)
        baseaddress = pbi.PebBaseAddress
        print 'peb',hex(baseaddress)

        import ndk
        peb = ndk.pstypes.PEB()
        peb.source = mm.allocator
        peb.setoffset(baseaddress)
        peb.load()

    if True:
        import os
        print 'collecting all modules'
        modulelookup = {}
        for module in peb['Ldr'].d.load()['InLoadOrderModuleList'].walk():
            modulename = os.path.basename( module['FullDllName'].get() ).lower()
            modulelookup[modulename] = module['DllBase'].d
        pass

    searchpath = ['./', '../obj', 'c:/windows/syswow64']
    def openmodule(modulename, lnk):
        st = linker.coffexecutable()

        failure = True
        search = list(searchpath)
        path = search.pop(0)
        while failure:
            fullpath = (path + '/' + modulename)
            try:
                st.open(fullpath)
                print 'loaded module from %s'% fullpath
                failure = False
            except IOError:
                print 'unable to locate %s, trying next searchpath'% fullpath
                path = search.pop(0)
                continue
            continue
        return st

    def loadmodule(modulename, lnk):
        st = linker.coffexecutable()
        symlookup = {}

        pe = modulelookup[modulename].load()['Pe']
        print 'using',modulename,'from memory address', '%x'% pe.parent.getoffset()

        st.load(pe.parent,modulename)
        symlookup[modulename] = dict( ((k, st[k]) for k in st.getglobals()) )

        for module,name in ( tuple(k.split('!')) for k in lnk.getglobals() if '!' in k and lnk[k] is None ):
            if module != modulename:
                continue
            fullname = '%s!%s'%(module,name)
            s = symlookup[module]

            try:
                lnk[fullname] = s[fullname]
            except KeyError:
                # XXX: shell32.dll tries to import from user32.dll!Ordinal2000...which doesn't exist
                #      OFT: 800007d0 FT: 77D15AA6 HINT: N/A Name: Ordinal: 000007d0
                print "Some crazy module wants to import from %s"% fullname
            continue
        return st

    if False:
        def loadmodule(modulename, lnk, lookup):
            st = linker.coffexecutable()

            symlookup = {}
            if modulename in lookup:
                pe = modulelookup[modulename].load()['Pe']
                print 'using',modulename,'from memory address', '%x'% pe.parent.getoffset()

                st.load(pe.parent,modulename)
                symlookup[modulename] = dict( ((k, st[k]) for k in st.getglobals()) )

                #            raise NotImplementedError
                # Somehow a few of our exports in the iat don't get set
                # this is in coffexecutable

                for module,name in ( tuple(k.split('!')) for k in lnk.getglobals() if '!' in k and lnk[k] is None ):
                    if module != modulename:
                        continue
                    fullname = '%s!%s'%(module,name)
                    s = symlookup[module]

                    try:
                        lnk[fullname] = s[fullname]
                    except KeyError:
                        # XXX: shell32.dll tries to import from user32.dll!Ordinal2000...which doesn't exist
                        #      OFT: 800007d0 FT: 77D15AA6 HINT: N/A Name: Ordinal: 000007d0
                        print "Some crazy module wants to import from %s"% fullname

                return

            #        print 'reading',modulename,'from disk'

            failure = True
            search = list(searchpath)
            path = search.pop(0)
            while failure:
                fullpath = (path + '/' + modulename)
                try:
                    st.open(fullpath)
                    print 'loaded module from %s'% fullpath
                    failure = False
                except IOError:
                    print 'unable to locate %s, trying next searchpath'% fullpath
                    path = search.pop(0)
                    continue
                continue
            lnk.add(st)

    ############
    link = linker.new()

    stores = [
        (linker.coffstore, '../obj/test.obj'),
        (linker.coffcontainer, 'c:/python26/libs/python26.lib')
    ]

    # add all initial symbols
    for s,n in stores:
        o = s()
        o.open(n)
        print 'linking %s'% n
        link.add(o)

    # load everything we can
    if True:
        # XXX: rewrite this
        definedmodules = set()
        while True:
            undefinedsymbols = [tuple(k.split('!')) for k in link.keys() if '!' in k and link[k] is None]
            undefinedmodules = set((module for module,name in undefinedsymbols))

            res = set(undefinedmodules)
            res.difference_update(definedmodules)
            if not res:
                break

            undefinedsymbols = [k for k in link.keys() if '!' in k and link[k] is None]
#            print '\n'.join(undefinedsymbols)

            for m in undefinedmodules:
                if m in definedmodules:
                    continue

                print 'loading %s'% m
                if m in modulelookup:
                    st = loadmodule(m, link)
                else:
                    st = openmodule(m, link)
                link.add(st)
                definedmodules.add(m)
            continue
        pass

    if True:
        print '-'*50, 'shooting up'
        ld = loader.module(link)
        ld.inject(mm)

    if 0:
        print '\n'.join([repr((k,ld[k])) for k in ld.getglobals()])

    if 1:
        name = '__imp__PySys_SetArgv'
        print name,hex(ld[name])

        name = 'python26.dll!PySys_SetArgv'
        print name,hex(ld[name])

    if 1:
        name = '_main'
        print name,hex(ld[name])
