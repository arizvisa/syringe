import os,array
import pecoff,ptypes,bitmap
import logging,warnings
import store

class coff(store.base):
    '''Provides functionality common to most(heh) coff derived formats'''

    @classmethod
    def load(cls, pointer, modulename):
        result = cls()
        result.modulename = modulename
        result.value = pointer
        return result

    def parse(self):
        self.value = self.value
        return super(coff, self).parse()

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

class coffimporttable(store.base):
    '''Intended to be treated as a mix-in'''
    
    iat = None                  # the resulting iat that gets serialized
    importaddresstable = None   # a quick lookup for identifying iat entry by symbolname

    def new_iat(self, **attrs):
        '''allocate a new iat and importaddresstable lookup'''
        self.importaddresstable = {}
        self.iat = pecoff.definitions.imports.IMAGE_IMPORT_ADDRESS_TABLE(source=ptypes.provider.empty(), isTerminator=lambda v:False, **attrs)
        self.iat.length = 0
        return self.iat.alloc()

    def set_iat_entry(self, externalname, address):
        '''update the iat entry, and initialize the local importname symbol with a pointer to the iat entry'''
        importname = '__imp__<%s!%s>'% externalname
        entry = self.importaddresstable[importname]
        entry.set(address)
        self[(None, importname)] = entry.getoffset()
        return entry

    def get_iat_entry(self, externalname):
        importname = '__imp__<%s!%s>'% externalname
        return self.importaddresstable[importname]

    def new_iat_entry(self, externalname):
        '''allocates an import in the iat and symboltable for the specified external name'''
        importname = '__imp__<%s!%s>'% externalname
        if importname in self.importaddresstable:
            raise KeyError('symbol %s already exists'% importname)

        # create the iat entry, and update the pointer
        result = self.iat.newelement(self.iat._object_, 'IAT', self.iat.getoffset()+self.iat.size()).alloc()
        self.iat.append(result)
        self.importaddresstable[importname] = result

        # add the symbol
        try:
            segmentname = self.value['Sections'].getsectionbyaddress(result.getoffset())['Name'].str()
        except KeyError:
            segmentname = None

        self.add( (None,importname), result.getoffset(), store.LocalScope, segmentname)
        return result

    def add_import(self, externalname):
        '''adds an import to the symbol table and the iat'''
        result = self.new_iat_entry(externalname)

        # add the external symbol
        self.add(externalname, None, store.ExternalScope, None)

        # updating the external name will set the iat entry
        oldhook = self.hook(externalname, None)
        def update_iat(s,x):
            result = s.set_iat_entry(x, s[x])
            return oldhook(s,x)
        self.hook(externalname, update_iat)
        return

    def add_forward(self, externalname, localnames):
        '''adds a forward import to the symbol table. this will create the import, aliases, and hooks'''
        try:
            self.add_import(externalname)
        except KeyError:
            logging.warning('%s : import %s has already been specified by the IAT'% (self.name(), repr(externalname)))

        [self.alias(x, externalname) for x in localnames]

        oldhook = self.hook(externalname, None)
        def update_iat(s,x):
            s.set_iat_entry(x, s[x])
            return oldhook(s,x)
        self.hook(externalname, update_iat)

class executable(coff,coffimporttable):
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

    relocations = None          # cache of relocations

    @classmethod
    def open(cls, path):    
        p = pecoff.Executable.open(path, mode='rb')

        result = cls()
        result.modulename = os.path.basename(path)
        result.value = p
        return result

    def parse(self):
        self.value = self.value['Pe']

        logging.info('reading %s from %s'%(type(self).__name__, self.value.source))
        logging.info('%s : .....loading segments'% self.name())
        self.do_segments()
        logging.info('%s : ....loading iat'% self.name())
        self.do_iat()
        logging.info('%s : ...loading imports'% self.name())
        self.do_imports()
        logging.info('%s : ..loading exports'% self.name())
        self.do_exports()
        logging.info('%s : .loading relocations'% self.name())
        self.do_relocations()
        logging.info('%s : done'% self.name())

        return super(executable, self).parse()

    def listsegments(self):
        sections = self.value['Sections']
        return [ x['Name'].str() for x in sections if int(x['Characteristics']) & 0x2000000 == 0]

    def do_segments(self):
        for n in self.listsegments():
            self.add((None,n), None, store.LocalScope, None)
        return

    def do_iat(self):
        '''preload the iat from the file'''
        importDirectory = self.value['OptionalHeader']['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        # create a list of all imports and the address they should be pointed to
        importaddress = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            importaddress.extend( (((modulename,name),address) for hint,name,address in module.fetchimports()) )

        # create the iat from the initial one in the file
        left,right=min((v for k,v in importaddress)),max((v for k,v in importaddress))

        iat = self.new_iat(offset=left)

        # default the import address table lookup
        for name,address in importaddress:
            self.add_import(name)
            self.set_iat_entry(name, address)
        return

    def do_imports(self):
        importDirectory = self.value['OptionalHeader']['DataDirectory'][1]
        if not importDirectory.valid():
            return
        importDirectory = importDirectory.get().l

        # create a list of all imports and the address they should be pointed to
        importaddress = []
        for module in importDirectory.l.walk():
            modulename = module['Name'].d.l.str().lower()
            for hint,name,address in module.fetchimports():
                try:
                    self.add_import((modulename,name))
                except KeyError:
                    logging.warning('%s : internal import name for %s already exists'% (self.name(), repr((modulename,name))))
                continue
            continue
        return

    def do_exports(self):
        '''Adds the symbolname as a global'''
        exportDirectory = self.value['OptionalHeader']['DataDirectory'][0]
        if not exportDirectory.valid():
            return

        exportDirectory = exportDirectory.get().l

        for (ordinal,name,ordinalstring,value) in exportDirectory.enumerateAllExports():
            if type(value) is str:
                externalname = self.__split_modulename(value, (ordinal,name))
                self.add_forward(externalname, [(None,name),(None,ordinalstring)])
                continue
            
            segmentname = self.value['Sections'].getsectionbyaddress(value)['Name'].str()
            self.add((None,name), value, store.GlobalScope, segmentname)
        return

    def do_relocations(self):
        relo = self.value['OptionalHeader']['DataDirectory'][5]
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

    if False:
        def load_symbols(self, segmentname):
            raise NotImplementedError
            symbolnames = self.getglobalsbysegmentname(segmentname)
            section = self.value['Sections'].getsectionbyname(segmentname)

            if segmentname is not None:
                exportDirectory = self.value['OptionalHeader']['DataDirectory'][0]
                assert exportDirectory.valid()
                exportDirectory = exportDirectory.get().l

                lookup = ((name,value) for ordinal,name,ordinalstring,value in exportDirectory.enumerateAllExports() if ordinalstring in symbolnames)
                lookup=dict(lookup)

                for name in symbolnames:
                    self[name] = lookup[name]
                return symbolnames

    def relocatesegment(self, segmentname, data):
        data = array.array('c',data)
        section = self.value['Sections'].getsectionbyname(segmentname)

        # sanity
        if len(data) != self.getsegmentlength(segmentname):
            warnings.warn('argument data length is different than expected (%d != %d)'%(len(data), self.getsegmentlength(segmentname)),UserWarning)

        # if we're in the import section
        importsection = self.value['Sections'].getsectionbyaddress(self.iat.getoffset())
        if section == importsection:
            offset = self.iat.getoffset() - importsection['VirtualAddress']     # XXX: it might be better to initialize the segment in .getsegment, so someone can modify the import table
            data[offset:offset+self.iat.size()] = array.array('c',self.iat.serialize())

        # finally, relocations.
        if self.relocations:
            data = self.relocations.relocate(data, section, self)

        # call the hook to reset our addresses
        self[segmentname] = self[segmentname]

        return data.tostring()

class object(coff):
    symbols = None

    '''
    there is no concept of external modules here, that is provided by an import lib.
    a hidden segment will have a name of None, this segment will contain all the allocations
        of an object.
    '''

    @classmethod
    def open(cls, path):    
        p = pecoff.Object.open(path, mode='rb')

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

    def parse(self):
        self.symbols = self.value['Header'].getsymbols().l

        self.do_segments()
        
        raise NotImplementedError("object : locals/globals/externals aren't being enumerated correctly")
#        self.do_locals()
#        self.do_globals()
#        self.do_externs()

        return super(object, self).parse()

    def do_segments(self):
        for s in self.listsegments():
            self.add((None,s), None, store.LocalScope, None)
        return

    def do_locals(self):
        sections = self.value['Sections']
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])

            # static symbols
            if storageclass != 3:
                continue

            # if it's a section
            if int(s['Value']) == 0 and int(s['NumberOfAuxSymbols']) == 0:
                continue

            if sectionnumber is None:
                logging.info('%s : skipping undefined local %s'%( self.name(), s.friendly()))
                continue

            symbolname = (None, s['Name'].str())
            self.add(symbolname, 0, store.LocalScope, sections[sectionnumber]['Name'].str())
        return

    def do_globals(self):
        sections = self.value['Sections']
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            value = int(s['Value'])

            # exported symbols
            if storageclass != 2:
                continue

            # not an externally defined symbol
            if (sectionnumber is None):
                continue

            # not a segment name
            if value == 0 and int(s['NumberOfAuxSymbols']) > 0:
                logging.debug('%s : skipping segment %s'%( self.name(), repr(s)))
                continue

            symbolname = (None, s['Name'].str())
            self.add(symbolname, 0, store.GlobalScope, sections[sectionnumber]['Name'].str())
        return

    def do_externs(self):
        for s in self.symbols.get():
            sectionnumber,storageclass = s['SectionNumber'].get(), int(s['StorageClass'])
            if sectionnumber is None and storageclass == 2 and int(s['Value']) == 0:
                self.add((None, s['Name'].str()), None, store.ExternalScope, None)
            continue
        return

    def loadsymbols(self, segmentname):
        section = self.value['Sections'].getsectionbyname(segmentname)
        sectionnumber = self.value['Sections'].v.index(section)
        sectionva = int(section['VirtualAddress'])
        result = set()

        raise NotImplementedError("This doesn't get the correct symbols out of the user-specified section")
        for s in self.symbols.get():
            # not the right section
            if sectionnumber != s['SectionNumber'].get():
                continue

            # if it's a global or local
            storageclass = int(s['StorageClass'])
            if storageclass not in (2,3):
                continue

            symbolname = (None, s['Name'].str())
            value = int(s['Value'])

            print symbolname, s.friendly()  # XXX

            # and not a section
            if value == 0 and int(s['NumberOfAuxSymbols']) > 0:
                continue

            # save it
            self[symbolname] = value
            result.add(symbolname)
        return result

    def relocatesegment(self, segmentname, data):
        section = self.value['Sections'].getsectionbyname(segmentname)
        relocations = section.getrelocations().load()
        symboltable = self.symbols['Symbols']

        symbols = self.segments[segmentname]
        namespace = dict(((k,self[k]) for m,k in symbols if m is None))

        for r in relocations:
            sym = symboltable[ int(r['SymbolTableIndex']) ]
            data = r.relocate(data, symboltable, namespace)

        self.updatesymbols(namespace)
        return data

class library(store.container, coffimporttable):
    '''
    this will need an iat object also.
    '''
    @classmethod
    def open(cls, path):    
        p = pecoff.Archive.open(path, mode='rb')

        result = cls()
        result.modulename = os.path.basename(path)
        result.value = p
        return result

    def parse(self):
        logging.info('%s : parsing iat'% self.name())
        self.do_iat()
        logging.info('%s : merging members'% self.name())
        for obj in self.value.fetchmembers():
            st = object.load(obj.l, obj.__name__)      # XXX: this .__name__ isn't the correct module name
            self.addstore(st)
        return super(library, self).parse()

    def process(self, store):
        result = store.parse()
        self.process_segments(store)
        self.merge(store, store.getglobals())
        return result

    def process_segments(self, store):
        '''Merge the segments from the provided store'''
        segments = set((n for n in store.listsegments()))

        result = []
        for n in store.listsegments():
            try:
                first = n[:n.rindex('$')]
                index = int(n[n.rindex('$')+1:])

            except ValueError, e:
                first = n
                index = 0           # default to 0 to give section first priority

            self.addsegment(first, index, n, store)
        return

    def do_iat(self):
        logging.info('%s : doing iat'% self.name())
        self.new_iat()
        for module,symbol,ordinal,type in self.value.fetchimports():
            self.add_import((module,symbol))
        return

    def getsegment(self, segmentname):
        data = super(library, self).getsegment(segmentname)
        if segmentname == '.idata':
            data = array.array('c', data)
            left = self.iat.getoffset() - self[segmentname]
            data[left:left+self.iat.size()] = iat.serialize()
            data = data.tostring()
        return data

if __name__ == '__main__':
    if False:
        #globalname = ('ntdll.dll', 'RtlAddVectoredContinueHandler')
        #localname = (None, 'AddVectoredContinueHandler')
        #importname = '__imp__<%s!%s>'%(globalname)

        #globalname = ('ntdll.dll', 'RtlSizeHeap')
        #localname = (None, 'HeapSize')

        globalname = ('api-ms-win-core-rtlsupport-l1-1-0.dll', 'RtlUnwind')
        localname = (None, 'RtlUnwind')

        importname = '__imp__<%s!%s>'%(globalname)

        z = executable.open('c:/windows/syswow64/kernel32.dll')
        #a = z.value['OptionalHeader']['DataDirectory'][1].get().l[1]
        #b = z.value['OptionalHeader']['DataDirectory'][0].get().l

        for x in z.getexternals():
            z[x] = 1

        raise NotImplementedError('Test to ensure relocating and symbols and everything work ok')

        # kernel32.dll!VerSetConditionMask -> ntdll.dll!VerSetConditionMask
        # __imp__<kernel32.dll!VerSetConditionMask>

    if False:
        a = object.open('f:/work/syringe/src/test.obj')
        a.parse()

    if False:
    #    ptypes.setsource(ptypes.provider.file('f:/work/syringe/src/blah.lib'))
        ptypes.setsource(ptypes.provider.file('c:/python26/libs/python26.lib'))
        z = pecoff.Archive.File()
        z=z.l
        for x in z.fetchimports():
            print x

    if True:
        z = library.open('c:/python26/libs/python26.lib')
        z.parse()
        print z.stores[0]
    #    z['.idata']=5

