import array
import store

class linker(store.container):
    def __repr__(self):
        return '%s modules %s'% ( super(linker,self).__repr__(), repr([st.modulename for st in self.stores]) )

if False:
    class linker(container):
        def __setitem__(self, key, value):
            '''
            This function is a giant fucking hack for a design that i want..god dammit
            FIXME: rewrite this fucking thing. dammit.
            '''
            if key == '.idata' and value is not None:   # XXX: hack
                o = value
                for st in self.stores:
                    if key not in st.listsegments():
                        continue
                    st[key] = o

                    # back into our namespace
                    for n in st.getglobalsbysegmentname('.idata'):
                        self[n] = st[n]

                    o += st.getsegmentlength(key)
                return super(linker, self).__setitem__(key, value)

            # if it's an external then copy it's value and everything from the
            #    store back to us
            # XXX: this is a hack
            if key in self.__externalcache:
                for st in self.__externalcache[key]:
                    st[key] = value
                for k in st.getglobals():
                    super(store, self).__setitem__(k,st[k])  #FIXME: PRAYTOO: this causes a dupe symbol
                pass
            return super(linker, self).__setitem__(key, value)

        def __repr__(self):
            return super(linker,self).__repr__() + " modules " + repr([st.modulename for st in self.__getsortedstores()])
                
        def add(self, store):
            if len(self.stores) == 0:
                self.__externalcache = {}

            self.stores.append(store)
            self.__mergestore(store)

        def getstore(self, modulename):
            for x in self.stores:
                if x.modulename == modulename:
                    return x
                continue
            return None

        def __mergestore(self, store):
            add = super(container,self).add

            # add externals
            print '..externals'
            cache = self.__externalcache
            for fullname in store.getexternals():
                try:
                    self[fullname]
    #                print 'External symbol %s has already been defined'% fullname
                except KeyError:
                    add(fullname, None)
    #                print 'Adding external symbol %s'% fullname

                # add stores for a cache to update on an external assignment  XXX: hack
                try:
                    cache[fullname] 
                except KeyError:
                    cache[fullname] = []
                cache[fullname].append(store)

            # collect globals
            print '..globals'
            for name in store.getglobals():
                try:
                    self[name]
                    if self[name] is not None:
    #                    print 'Duplicate symbol %s:%x is already defined as %s:%x'% (name, store[name], name, self[name])  # XXX: uncomment this
                        continue
                except KeyError:
                    add(name, store[name])
    #                print 'Adding global symbol %s'% name
                    continue
                self[name] = store[name]

            # and now segments just cause
            print '..segments'
            for name in store.listsegments():
                try:
                    self[name]
                except KeyError:
                    add(name, None)
                continue
            return

        def getsegment(self, name):
            result = []
            for st in self.__getsortedstores():
                for n in st.getexternals():
                    st[n] = self[n]
                continue
            return super(linker, self).getsegment(name)

        def getsegmentlength(self, name):
            result = []
            for st in self.stores:
                for n in st.getexternals():
                    st[n] = self[n]
                continue
            return super(linker, self).getsegmentlength(name)

        def listsegments(self):
            # OMG, i fucking hate this code
            res = list()
            for v in self.__getsortedstores():
                for s in v.listsegments():
                    if s in res:
                        continue
                    res.append(s)
                continue
            return res

        def __getstorelist(self, name):
            result = []
            ofs = 0
            for st in self.stores:
                length = 0
                if name in st.listsegments():
                    length = st.getsegmentlength(name)
                result.append( (st, (ofs, length)) )
                ofs += length
            return result

        def __getsizelookupbyname(self):
            return dict( ((name, dict(self.__getstorelist(name))) for name in self.listsegments()) )

        def __getsizelookupbystore(self):
            result = dict(((id(st),{}) for st in self.stores))
            for name in self.listsegments():
                for st,v in self.__getstorelist(name):
                    r = result[id(st)]
                    r[name] = v
                continue
            return result

        def __getsortedstores(self):
            undefinedmodulecache = dict()       # dict of store's dependencies and the store
            definedmodules = set()

            # iterate through all stores adding and removing modules from our cache
            for st in self.stores:
                modules = st.externalmodules()
                for n in modules:
                    try:
                        undefinedmodulecache[n].append( st )
                    except KeyError:
                        undefinedmodulecache[n] = [ st ]
                    continue

                if st.modulename in undefinedmodulecache:
                    definedmodules.add( st.modulename )
                continue

            # figure out which ones need to be deferred-done (this contains a case with multiple modules that will break this "algo")
            delay = []
            for n in definedmodules:
                delay.extend(undefinedmodulecache[n])

            # put all these stores at the end
            res = []
            for st in self.stores:
                if st in delay:
                    continue
                res.append( st )
            res.extend(delay)
            return res

        def relocatesegment(self, name, data, baseaddress):
            self[name] = baseaddress
            storeLookup = self.__getsizelookupbystore()   # heh.

            # sort this list by dependencies...heh...
            stores = self.__getsortedstores()

            # update symbols first
            print 'symbol'
            for st in stores:
                sectionlookup = storeLookup[ id(st) ]
                offset,length = sectionlookup[name]
                if length == 0:
                    continue
                self._updatestoresymbols(st, name, sectionlookup, baseaddress+offset)

    #        raise NotImplementedError("Will need to sort by dependencies/externals...dammit")  # FIXME

            # do relocation
            print 'relocate'
            data = array.array('c', data) 
            for st in stores:
                print st
                lookup = storeLookup[ id(st) ]
                offset,length = lookup[name]
                if length == 0:
                    continue

                chunk = data[offset:offset+length]
                chunk = st.relocatesegment(name, chunk.tostring(), baseaddress+offset)
                chunk = array.array('c', chunk)
                data[offset:offset+length] = chunk
            data = data.tostring()

            # restore symbols
            for st in stores:
                lookup = storeLookup[ id(st) ]
                offset,length = lookup[name]
                if length == 0:
                    continue
                self._updateoursymbolsfromstore(st, name, lookup)
            print 'done'
        
            return data

        def _updateoursymbolsfromstore(self, st, name, lookup):
            for n in st.getglobalsbysegmentname(name):
                self[n] = st[n]

            # XXX: because i'm a horrible programmer and i hook __setitem__/__getitem__
            for n in st.getexternals():
                self[n] = st[n]
            return
        
        def _updatestoresymbols(self, st, name, lookup, baseaddress):
            # externals
            for k in st.getexternals():
                st[k] = self[k]

            # segments
            try:
                for n in st.listsegments():
                    o,l = lookup[n]
                    st[n] = [lambda:self[n]+o, lambda:baseaddress+o][n == name]()   #yes, look carefully
                pass
            except (TypeError,KeyError):
                raise KeyError('Segment %s undefined'% n)

            # globals
            for n in st.getglobalsbysegmentname(name):
                st[n] = self[n]
            return

def new(**kwds):
    return linker()

if __name__ == '__main__':
    if False:
        import sys
        sys.path.append('f:/work')
        sys.path.append('f:/work/syringe.git/lib')

    import pecoff,ptypes,bitmap
    from warnings import warn       # XXX: i really should learn to use this module correctly...

    import linker
    coffstore = linker.coffstore
    coffexecutable = linker.coffexecutable

#    raise NotImplementedError("Still haven't successfully calculated the target addresses when linking with _everything_")

    if False:
        self = coffstore()
        self.open('../obj/python-test.obj')

        print self.keys()
        segments = [
            ('.data', 0xccccc000),
            ('.text', 0xaaaaa000),
        ]

        self['__imp__Py_Initialize'] = 0xdddddddd
        self['__imp__PyRun_SimpleStringFlags'] = 0xdddddddd
        self['__imp__Py_Finalize'] = 0xdddddddd

        print self.listsegments()
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
            r = self.relocatesegment(name, data, baseaddress)
            print repr(r)
            print ptypes.utils.hexdump(r, offset=baseaddress)

            continue
        pass

    if False:
        self = coffexecutable()
        #self.open('../obj/test.exe')
        self.open('c:/windows/system32/kernel32.dll')
        #self.open('c:/windows/system32/python26.dll')

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
        filename = "out/blah.bin"
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
            r = self.relocatesegment(name, data, self[name])
            out.write(r)

        out.close()

        if False:
            addresses = file('out/blah.txt', 'wt')
            for x in self.getglobals():
                addresses.write( ','.join([x,hex(self[x])]) + "\n")
            addresses.close()

        if False:
            import idc
            input = file('f:/work/syringe.git/work/out/blah.txt', 'rt')
            lines = input.read().split("\n")
            input.close()

            l = ( x.split(',') for x in lines if x)
            l = ( (a,int(b,16)) for a,b in l )
            for name,offset in l:
             idc.MakeNameEx(offset, name, 0x2)
             idc.MakeCode(offset)

    if False:
        self = coffexecutable()
        self.open('c:/windows/system32/python26.dll')
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
        self = coffexecutable()
        self.open(dllname)

#        raise NotImplementedError("Need to figure out how to import ordinal numbers, and enumerate import modules')
        for n in self.getglobals():
            if self[n]:
                print n, repr(self[n])
            continue
        pass

    if True:
        print '-'*50
        print 'loading .obj file'
        obj = coffstore()
        obj.open('f:/work/syringe.git/obj/test.obj')

        print '-'*50
        print 'loading .lib file'
        lib = coffcontainer()
        lib.open('c:/python26/libs/python26.lib')

        print '-'*50
        print 'linking them'
        self = linker.new()
        self.add(obj)
        self.add(lib)

    if True:
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
            dll = coffexecutable()
            dll.open('c:/windows/syswow64/%s'%name)
            lookup[dll.modulename] = dll

            print 'linking .dll file %s'% name
            self.add(dll)
        pass

    if False:
        for k in self.keys():
            if k.startswith('python26.dll!'):
                self[k] = 0xcccccccc
            continue

    if True:
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

    if True:
        print '-'*50
        for n in self.keys():
            if self[n] is None:
                print n, repr(self[n])
            continue

    if True:
        print '-'*50
        for n in self.keys():
            if not n.startswith('__imp__') and '!' not in n:
                print n, hex(self[n])
            continue
