import os,array
import pecoff,ptypes
import logging,warnings
import store

raise NotImplementedError(".do and .loadsymbol logic needs to be redesigned")

#logging.root=logging.RootLogger(logging.ERROR)
logging.root=logging.RootLogger(logging.DEBUG)

class coff(store.base):
    '''Provides functionality common to most(heh) coff derived formats'''

    @classmethod
    def load(cls, pointer, modulename):
        result = cls()
        result.modulename = modulename
        result.value = pointer
        return result

    def getsegment(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        data = section['PointerToRawData'].d.load().serialize()

        diff = section.getloadedsize() - len(data)
        assert diff >= 0, 'Loaded size (%x) < Segment size (%x)'% (section.getloadedsize(), len(data))
        data += '\x00' * diff
        return data

    def getsegmentlength(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        return section.getloadedsize()

    def getsegmentprotection(self, name):
        section = self.value['Sections'].getsectionbyname(name)
        chars = section['Characteristics']
        x = int(chars)

        if x&chars.CNT_CODE:
            readable,writeable,executable = True, False, True
        elif x&chars.CNT_INITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        elif x&chars.CNT_UNINITIALIZED_DATA:
            readable,writeable,executable = True, True, False
        else:
            raise NotImplementedError('Unknown protection for %s'% repr(characteristics))

        binarydigits = ['0', '1']
        res = [ binarydigits[x] for x in (readable,writeable,executable)]
        return int(''.join(res), 2)

class linktable(dict):
    '''
    This table is keyed by the mangled version of a symbolname, and is repsonsible for updating the attached
    symboltable. It is used specifically for hiding the type information for each entry in the specified table,
    and is intended for implementation of the export and import address tables
    '''

    type = ptypes.dyn.addr_t(ptypes.pint.uint32_t)
    table = store.base

    def __init__(self, symboltable):
        self.table = symboltable

    def mangle(self, (module,name)):
        '''
        converts a symbolname to a mangled version which is used internally
        by just the linktable. this name is used to correlate symbol entries
        with the symboltable and should be assigned locally
        '''
        return None,'%s!%s'%(module, name)

    def new_entry(self, name, address=0):
        '''allocates space for a new entry, and updates the store's symboltable scope'''

        n = self.mangle(name)
        if n in self.keys():
            raise KeyError('symbol %s for %s already exists'% (n, name))

        st = self.table
        result = st.value.newelement(n, self.type, address)
#        result = self.type(__name__=n, offset=address)  # XXX

        # figure out which segment the iat entry is stored at
        segmentname = st.findsegment(result.getoffset())
        if segmentname is None:
            raise NotImplementedError("support for hidden segments has been removed")

        # update the symboltable with the mangled name
        st.add(n, result.getoffset(), store.LocalScope, segmentname)
        oldhook = st.hook(n, None)
        def update_local(symboltable,localname):
            self[name].setoffset(symboltable[localname])
            return oldhook(symboltable,localname)
        st.hook(n, update_local)

        # update the lookuptable with the data type
        self[name] = result
        return result

    def get_entry(self, name):
        '''returns a ptype associated with the specified name. this will allow one to manipualte it'''
        n = self.mangle(name)
        return self[name]

    def set_entry(self, name, value):
        '''updates an entry in the entry table with the specified value, and updates the symboltable's reference to it'''
        n = self.mangle(name)
        entry = self[name].set(value)
        self.table[n] = entry.getoffset()
        return entry

    def add_entry(self, name, address):
        # creates localname (None,whatever). Any assignment to localname will
        #     cause globalname to update its value with the current address of localname

        st = self.table
        segmentname = st.findsegment(address)
        if segmentname is None:
            raise NotImplementedError("support for hidden segments has been removed")

        result = self.new_entry(name, address)
        st.add(name, None, store.GlobalScope, segmentname)

        oldhook = st.hook(name, None)
        def update_entry(symboltable, localname):
            self.set_entry(localname, st[localname])
            return oldhook(symboltable, localname)
        st.hook(name, update_entry)
        return result

    def add_forward(self, aliases, name, address):
        # creates localname, and aliases it to the forwardedname symbol
        st = self.table
        segmentname = st.findsegment(address)

        st.add(name, None, store.ExternalScope, segmentname)
        try:
            result = self.new_entry(name, address)
        except KeyError:
            logging.warning('%s : import %s has already been defined in the linktable '% (self.name(), repr(name)))
            result = self.get_entry(name)

        st.scope[store.GlobalScope].update(aliases)
        st.scopesegment[segmentname].update(aliases)
        [st.alias(x, name) for x in aliases]

        oldhook = st.hook(name, None)
        def update_forward(symboltable, externalname):
            result = self.set_entry(externalname, st[externalname])
            st[aliases[0]] = result.getoffset()
            return oldhook(symboltable,externalname)
        st.hook(name, update_forward)
        return result

    def size(self):
        return reduce(lambda x,y: x+y.size(), self.itervalues())

class table_eat(linktable):
    '''coff export address table'''
    def mangle(self, (module,name)):
        return None,'%s!%s'%(module,name)

class table_iat(linktable):
    '''coff import address table'''
    def mangle(self, (module,name)):
        '''
        convert a name tuple into an internally mangled name, because microsot
        is weird with their __imp_ name prefix, so i'll be weirder
        '''
        return None,'__imp__<%s!%s>'% (module,name)      # include the full module name

class executable(coff):
    relocations = None          # cache of relocations
    iat = table_iat
    eat = table_eat

    def __init__(self):
        self.iat,self.eat = table_iat(self),table_eat(self)
        return super(executable, self).__init__()

    @classmethod
    def open(cls, path):    
        p = pecoff.Executable.open(path, mode='r')

        result = cls()
        result.modulename = os.path.basename(path)
        result.value = p
        return result

    def do(self):
        self.value = self.value['Next']

        logging.info('reading %s from %s'%(type(self).__name__, self.value.source))
        logging.info('%s : .....loading segments'% self.name())
        self.do_segments()
        logging.info('%s : ....loading exports'% self.name())
        self.do_exports()
        logging.info('%s : ...loading iat'% self.name())
        self.do_iat()
#        logging.info('%s : ..loading imports'% self.name())
#        self.do_imports()
        logging.info('%s : .loading relocations'% self.name())
        # exe parsing is kind of slow too
        self.do_relocations()
        logging.info('%s : done'% self.name())

        return super(executable, self).do()

    def listsegments(self):
        sections = self.value['Sections']
        return [ x['Name'].str() for x in sections if int(x['Characteristics']) & 0x2000000 == 0]

    def do_segments(self):
        for n in self.listsegments():
            self.add((None,n), None, store.LocalScope, n)
        self.load_segments()

    def load_segments(self):
        for n in self.listsegments():
            section = self.value['Sections'].getsectionbyname(n)
            self[n] = section['PointerToRawData'].int()
        return
            
    def do_iat(self):
        '''preload the iat symbols from the binary'''
        importDirectory = self.value['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        # precollect a list of all imports and the address they should be pointed to
        importaddress = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            importaddress.extend( (((modulename,name),address) for hint,name,address in module.fetchimports()) )

        # copy the iat from the one in the file
        for name,address in importaddress:
            try:
                self.iat.add_entry(name, address)
            except KeyError:
                logging.warning('%s : iat entry for %s already exists due to forward rva'% (self.name(), repr((modulename,name))))
            continue
        return

    def load_iat(self, symbolnames=None):
        '''initialize the iat with default values from the executable's import directory'''
        importDirectory = self.value['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        importaddress = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            importaddress.extend( (((modulename,name),address) for hint,name,address in module.fetchimports()) )

        result = set()
        for name,address in importaddress:
            self[name] = address
            result.add(name)
        return result

###
    def do_imports(self):
        importDirectory = self.value['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        # create a list of all imports and the address they should be pointed to
        importaddress = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            for hint,name,address in module.fetchimports():
                self[modulename,name] = address
            continue
        return

    def load_imports(self, symbolnames=None):
        importDirectory = self.value['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        symbols = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            for hint,name,address in module.fetchimports():
                if symbolnames is None or (modulename,name) in symbolnames: #
                    symbols.append((modulename,name))
                    self[modulename,name] = None        # reset all externals to None?
                continue
            continue
        return symbols

###
    def do_exports(self):
        '''Adds the symbolname as a global'''
        exportDirectory = self.value['DataDirectory'][0]
        if not exportDirectory.valid():
            return
        exportDirectory = exportDirectory.get().l

        for (ofs,ordinal,name,ordinalstring,value) in exportDirectory.enumerateAllExports():
            if type(value) is str:
                externalname = self.__split_modulename(value, (ordinal,name))
                if externalname[0] == self.modulename:
                    raise NotImplementedError("Self-referencing RVA's not implemented")
                    externalname = None,externalname[1]

                self.eat.add_forward([(None,name),(None,ordinalstring)], externalname, ofs)
                continue

            try:
                section = self.value['Sections'].getsectionbyaddress(value)

            except KeyError:
                # XXX: if our address is not in a section, then our EAT entry
                #      might already point to the correct address.
                #       this handles that case.

                section = self.value['Sections'].getsectionbyaddress(ofs)
                self.add((None,ordinalstring), None, store.ExternalScope, section['Name'].str())
                self.alias((None,name),(None,ordinalstring))
                continue

            self.add((None,ordinalstring), value, store.GlobalScope, section['Name'].str())
            self.alias((None,name),(None,ordinalstring))
        return

    def load_exports(self, symbolnames=None):
        exportDirectory = self.value['DataDirectory'][0]
        if not exportDirectory.valid():
            return

        symbols = []

        exportDirectory = exportDirectory.get().l
        baseaddress = self.value['OptionalHeader']['ImageBase'].int()
        for (ofs,ordinal,name,ordinalstring,value) in exportDirectory.enumerateAllExports():
            if type(value) is str:
                # FIXME: should we assign to externalname, because i'm still not sure how
                #        to get the external name while staying within a module
                continue

            try:
                section = self.value['Sections'].getsectionbyaddress(value)
            except KeyError:
                if symbolnames is None or (None,ordinalstring) or (None,name) in symbolnames:   #
                    self[None,ordinalstring] = value+baseaddress
                    symbols.extend([(None,name),(None,ordinalstring)])
                continue

            if symbolnames is None or ((None,ordinalstring) in symbolnames) or ((None,name) in symbolnames):    #
                self[None,ordinalstring] = value
                symbols.extend([(None,name),(None,ordinalstring)])
        return symbols                
###
    def do_relocations(self):
        relo = self.value['DataDirectory'][5]
        if not relo.valid():
            return
        self.relocations = relo.get().load()

    def __split_modulename(self, n, stuffinscope):
        module,name = n.split('.', 1)
        if name.startswith('#'):
            try:
                name = 'Ordinal%d'% int(n[1:])
            except ValueError:
                logging.error('%s : unresolveable Forwarded Export %s at ordinal %d found at %s'%(self.name(), repr(n), stuffinscope[0], stuffinscope[1]))
                name = n[1:]        # XXX: for HUNIMPL.#UNIMPL_SHCreateStreamWrapper
            pass
        return module.lower() + '.dll',name

    def loadsymbols(self, segmentname):
        symbolnames = set(self.getglobalsbysegmentname(segmentname))
        if segmentname is None:
            result = self.load_iat(symbolnames)
            self[None,None] = None
            return result

        section = self.value['Sections'].getsectionbyname(segmentname)

        result = set()
        result.update(self.load_exports(symbolnames))
        result.update(self.load_imports(symbolnames))
        return symbolnames.intersection(result)

    def relocatesegment(self, segmentname, data):
        data = array.array('c',data)
        section = self.value['Sections'].getsectionbyname(segmentname)

        # sanity
        if len(data) != self.getsegmentlength(segmentname):
            warnings.warn('argument data length is different than expected (%d != %d)'%(len(data), self.getsegmentlength(segmentname)),UserWarning)

        # XXX: update the segment data with whatever is in the import or export table
        # if we're in the import section
        importsection = self.value['Sections'].getsectionbyaddress(self.hiddensegment.getoffset())
        if section == importsection:
            offset = self.hiddensegment.getoffset() - importsection['VirtualAddress']     # XXX: it might be better to initialize the segment in .getsegment, so someone can modify the import table
            data[offset:offset+self.hiddensegment.size()] = array.array('c',self.hiddensegment.serialize())

        # finally, relocations.
        if self.relocations:
            data = self.relocations.relocate(data, section, self)

        # call the hook to set the addresses for the symbols in the curent segment
        self[segmentname] = self[segmentname]

        return data.tostring()

class object(coff):
    symbols = None

    '''
    there is no concept of external modules here. that should be provided by an import lib.
    '''
    iat = table_iat

    def __init__(self):
        self.iat = table_iat(self)
        return super(object, self).__init__()

    @classmethod
    def open(cls, path):    
        p = pecoff.Object.open(path, mode='r')

        result = cls()
        result.modulename = os.path.basename(path)
        result.value = p
        return result

    def listsegments(self):
        # i suppose that we should trust the sectionlist instead of the symboltable
        result = []
        for section in self.value['Sections']:
            n = int(section['Characteristics'])
            if n&0x800 or n&0x2000000 or n&0x200 or n&0x80:    #LNK_REMOVE or MEM_DISCARDABLE or LNK_INFO 
                continue
            result.append( section['Name'].str() )
        return result

    def listsegments(self):
        sections = self.value['Sections']
        sectionnames = set((x['Name'].str() for x in sections))
        result = []
        for s in self.symbols.get():
            name,storageclass = s['Name'].str(),int(s['StorageClass'])
            if name in sectionnames and ((storageclass == 104) or (storageclass == 3 and int(s['Value']) == 0)):
                result.append(name)
            continue
        return result

    def do(self):
        self.symbols = self.value['Header'].getsymbols().l
        self.do_segments()
        self.do_locals()
        self.do_globals()
        self.do_externs()
        return super(object, self).do()

    def do_segments(self):
        for s in self.listsegments():
            o = self.value
            self.add((None,s), None, store.LocalScope, s)
        self.load_segments()

    def load_segments(self):
        for n in self.listsegments():
            section = self.value['Sections'].getsectionbyname(n)
            self[n] = section['PointerToRawData'].int()
        return

    def do_locals(self):
        sections = self.value['Sections']
        sectionnames = set((x['Name'].str() for x in sections))

        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            value = int(s['Value'])
            symbolname = (None, s['Name'].str())

            # static symbols
            if storageclass != 3:
                continue

            # if it's a section
            if value == 0 and symbolname[1] in sectionnames:
                logging.debug('%s : skipping segment %s'%( self.name(), s.friendly()))
                continue

            if sectionnumber is None:
                logging.info('%s : skipping undefined local %s'%( self.name(), s.friendly()))
                continue

            symbolname = (None, s['Name'].str())
            self.add(symbolname, 0, store.LocalScope, sections[sectionnumber]['Name'].str())
        return

    def do_globals(self):
        sections = self.value['Sections']
        sectionnames = set((x['Name'].str() for x in sections))
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            value = int(s['Value'])
            symbolname = (None, s['Name'].str())

            # exported symbols will only have a storageclass of 2
            if storageclass != 2:
                continue

            # not a segment name
            if value == 0 and symbolname[1] in sectionnames:
                logging.debug('%s : skipping segment %s'%( self.name(), s.friendly()))
                continue

            # not an externally defined symbol
            if sectionnumber is None:
#                logging.info('%s : skipping undefined global %s'%( self.name(), s.friendly()))
                continue

            self.add(symbolname, 0, store.GlobalScope, sections[sectionnumber]['Name'].str())
        return

    def do_externs(self):
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if storageclass == 2 and sectionnumber is None and int(s['Value']) == 0:
                self.add((None, s['Name'].str()), None, store.ExternalScope, None)
            continue
        return

    def loadsymbols(self, segmentname):
        sections = self.value['Sections']
        sectionnames = set((x['Name'].str() for x in sections))

        section = sections.getsectionbyname(segmentname)
        sectionnumber = sections.v.index(section)
        sectionva = int(section['VirtualAddress'])
        result = set()

        symbolnames = self.getglobalsbysegmentname(segmentname)

        logging.debug('restoring symbols for %s'% section['Name'].str())
#        raise NotImplementedError("This doesn't get the correct symbols out of the user-specified section")
        for s in self.symbols.get():
            value = int(s['Value'])
            symbolname = (None, s['Name'].str())

            # not the right section
            if sectionnumber != s['SectionNumber'].get():
                continue

            # if it's a global or local
            storageclass = int(s['StorageClass'])
            if storageclass not in (2,3):
                continue

            # and not a section name
            if value == 0 and symbolname[1] in sectionnames:
                continue

            logging.debug('assigned %s to %x'%( repr(symbolname), value))
            # save it
            if symbolname in symbolnames:   #
                self[symbolname] = value
                result.add(symbolname)
        return result

    def relocatesegment(self, segmentname, data):
        section = self.value['Sections'].getsectionbyname(segmentname)
        relocations = section.getrelocations()
        symboltable = self.symbols['Symbols']

        # call the hook to reset our symbol addresses
        self[segmentname] = self[segmentname]

        # do each relocation entry
        for r in relocations.l:
            sym = symboltable[ int(r['SymbolTableIndex']) ]
            print r, sym
            data = r.relocate(data, symboltable, self)
        return data

class library(store.container, coff):
    '''
    FIXME: this should only allocate iat entries on demand with whatever object
            it's linked with
    '''
    iat = table_iat

    def __init__(self):
        self.iat = table_iat(self)
        return super(library, self).__init__()

    @classmethod
    def open(cls, path):    
        p = pecoff.Archive.open(path, mode='r')

        result = cls()
        result.modulename = os.path.basename(path)
        result.value = p
        return result

    def do(self):
        logging.info('%s : parsing iat'% self.name())
        self.do_iat()
        logging.info('%s : merging members'% self.name())
        for obj in self.value.fetchmembers():
            st = object.load(obj.l, obj.__name__)      # FIXME: this .__name__ isn't the correct module name
            self.addstore(st)
        return self

    def prepare(self, st):
        # Merge the segments from the provided store
        segments = set((n for n in st.listsegments()))

        result = []
        for n in st.listsegments():
            try:
                first = n[:n.rindex('$')]
                index = int(n[n.rindex('$')+1:])

            except ValueError, e:
                first = n
                index = 0           # default to 0 to give section first priority

            self.addsegment(first, index, n, st)

        # merge in the symbols from the store
        self.merge(st, st.getglobals())
        return self

    def do_iat(self):
        logging.info('%s : doing iat'% self.name())
        ofs = 0
#        print self.listsegments()
        for module,symbol,ordinal,type in self.value.fetchimports():
            assert symbol[0] == '_', 'malformed import library symbol name?'
            name = module,symbol[1:]
            self.iat.add_entry(name, ofs)
            ofs += 4
        return

if __name__ == '__main__':
    import coff
    reload(coff)

    '''
    what's been tested ( )/not-tested (X):
        initializing the symbol table with imports,exports,relocations
        creation of the iat, and adding new entries to the iat

        assignments to externals will update the iat entry
        assignments to forward rva's will create an alias for the export, and update the iat entry
        assignments the store.BaseAddress will recalculate the base address for the binary

    X   updating the iat in the segment, or creating a segment specifically for it
    X   the hook on each segment name relocates all the segment's symbols correctly
    X   segments are 

    X   pecoff's relocation code getting the correct symbols out of the symboltable
            i think this is like mostly segment names.
    X   after the relocations have occurred, there's the code that updates the namespace with the
            new relocated value.
    X   relocations being applied properly
    X   speed

    what i think i need to do next:
        look at setting up something for testing the "allocated" segment. This will have a \
            segmentname of None

    '''

    if False:
        #globalname = ('ntdll.dll', 'RtlAddVectoredContinueHandler')
        #localname = (None, 'AddVectoredContinueHandler')
        #importname = '__imp__<%s!%s>'%(globalname)

        #globalname = ('ntdll.dll', 'RtlSizeHeap')
        #localname = (None, 'HeapSize')

        globalname = ('api-ms-win-core-rtlsupport-l1-1-0.dll', 'RtlUnwind')
        localname = (None, 'RtlUnwind')

        importname = '__imp__<%s!%s>'%(globalname)

        z = coff.executable.open('~/../../windows/syswow64/kernel32.dll')
        #a = z.value['DataDirectory'][1].get().l[1]
        #b = z.value['DataDirectory'][0].get().l

        for x in z.getexternals():
            z[x] = 1

        raise NotImplementedError('Test to ensure relocating and symbols and everything work ok')

        # kernel32.dll!VerSetConditionMask -> ntdll.dll!VerSetConditionMask
        # __imp__<kernel32.dll!VerSetConditionMask>

    if False:
        a = coff.object.open('~/work/syringe/obj/test.obj')
        print len(a.globals) == 3
        print len(a.externals) == 3

    if False:
        import ptypes,pecoff
    #    ptypes.setsource(ptypes.provider.file('~/work/syringe/src/blah.lib'))
        ptypes.setsource(ptypes.provider.file('~/python26/libs/python26.lib'))
        z = pecoff.Archive.File()
        z=z.l
        for x in z.fetchimports():
            print x

    if False:
        z = coff.library.open('~/python26/libs/python26.lib')
        print z.stores[2]
    #    z['.idata']=5

    if False:
        import store,coff
        reload(coff)
        reload(store)
        class dumbsymboltable(store.base):
            def listsegments(self):
                return 'default'
            def findsegment(self, address):
                return 'default'

        s = self = dumbsymboltable()
#        z = coff.table_eat(self)
        z = coff.table_iat(self)

#        print type(z)
#        print z.table

#        print z
#        z.add_export( (None,'somesymbol1') )
#        z.add_forward( ('kernel32.dll', 'Whee'), [(None,'remote1')] )
#        a=(None,'remote1') 
#        b=('kernel32.dll','Whee') 
                
#        a=(None,'somesymbol1') 
#        b=(None,'remote1') 
#        c=('kernel32.dll','whee') 

        a = ('ntdll.dll','RtlAllocateHeap')
        b = ('kernel32.dll', 'forwarded')
#        z.add_import( ('ntdll.dll','RtlAllocateHeap') )
#        z.add_forward( ('ntdll.dll','RtlAllocateHeap') )
#        self.add_forward(externalname, [(None,name),(None,ordinalstring)])
#        z.add_import(a)
        z.add_forward(b, [a])

    if False:
        import coff
        z = coff.executable.open('~/../../windows/syswow64/kernel32.dll')

    if False:
        import coff
        z = coff.library.open('~/python26/libs/python26.lib')

    if True:
        import coff
        a = coff.object.open('../../obj/python-test.obj')
        print a.do()
        print a

        
