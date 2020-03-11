'''
don't know why i wrote this....but in case anybody wants to see the internal mechanics of what
you have to work with if you want to implement your own symbol store.

definitions
    store
        an abstraction over any kind of object that can be a symbol storage facility for a module

    symbolname
        a tuple representing symbol.  i.e. symbolname = (modulename,localname)
        if modulename is None, then the symbol references locally to the current module

objects
    symboltable
        this is the the lowest-level class is intended to be inherited from.
        provides the ability for a dictionary to have support for aliases, hooking, and bulk \
            symbol management

        in order to use aliasing, both the aliasname and the targetname must exist in the \
            dictionary. if you unalias the very last reference to an object, the object will be \
            deleted.

        hooking takes a symbolname and a closure as a parameter. the closure is called after \
            the assignment of the symbol using the modified symbolname as the second parameter. \
            the .hook method will also return a reference to the previous closure the \
            symbolname was hooked with. it is advised that when the situation arises the \
            developer save the previous closure and when they overwrite it with their new one, \
            they call the original closure with the same parameters before or afterwards.

    symbolcontainer
        lower-level class that abstracts managing groups of symboltables.

    base
        main class that provides symbol storage facilities.

        this class enforces rampant symboltable population due to it being a dictionary. in \
            order to add a symbol to the dictionary, one will have to use the .add(...) method \
            to also attach the scope and segmentname of the symbol. this has the prototype of:

            self.add(symbolname, initialvalue, scope, segmentname)

            there are 3 main scopes to choose from, although a developer is allowed to use any \
                scope they want. the 3 type are store.LocalScope, store.GlobalScope, and \
                store.ExternalScope.

        to use the store.base, use .open(your_filename), or .load(ptype, your_modulename) on \
            any classes that inherit from it. all symbols can be accessed as if the object \
            was a dictionary using the symbolname tuple as the key.

        to get symbolnames in particular scopes or segments, there are a few methods provided.
            getlocals(), getglobals(), getexternals(). get{locals,globals}bysegmentname(n)

        to query the module for segmentation information, some more methods are:
            listsegments(), getsegmentlength(n), getsegmentprotection(n), getsegment(n), relocatesegment(n, data)

        when you ask the object for a symbolname, there's another symbolname called \
            store.BaseAddress that is defined in this module. if you assign an address to it,
            the object will align all the segments next to each other using the loaded segment \
            size. if you assign a value to any of the segments listed in .listsegments(), all of \
            the symbols in that segment will also get recalculated with the new base address.

    the only thing in this module to care about is the base.
'''

import logging,warnings,array,bisect
class DuplicateSymbol(Warning): pass
class UninitializedSymbol(Warning): pass

logging.root=logging.RootLogger(logging.DEBUG)

# symbol scopes
class Scope(object): pass
class LocalScope(Scope): '''A symbol that is local to a symboltable'''
class GlobalScope(Scope): '''A symbol that is global and available to other symboltables'''
class ExternalScope(Scope): '''A symbol that is defined in an external symboltable'''

# special symbols
class Symbol(object): pass
class BaseAddress(Symbol): '''The magical Base Address key. If you assign this, it will align all segments on the address you specify'''

# and we go...
class symboltable(dict):
    '''
    This base class provides the following functionality to a store:
        symbol aliasing. more than one symbol can point to the same data
        symbol hooking. if an assignment is made to a symbol, a callback can be made to occur.
        symbol merging. will merge 2 symbol tables together. user can specify names.
    '''

    aliases = None        # key of id's
    __hooks = None        # key'd by id
    modulename = None     # str of the modulename. subclasses should set this when they figure it out
    def __init__(self):
        super(symboltable, self).__init__()
        self.aliases = {}
        self.__hooks = {}
        self.modulename = '%s_%x'%(self.__class__.__name__, id(self))

    def name(self):
        '''quick short name to describe to a human what's in this obj'''
        return '{!r}{{{:s}}}'.format(type(self), self.modulename)

    ### iterables
    def iterkeys(self):
        return iter(self.aliases.keys())

    def viewkeys(self):
        return set(self.aliases.keys())

    def iteritems(self):
        for k in self.iterkeys():
            yield k,self[k]
        return

    ### overloads
    def clear(self):
        super(symboltable, self).clear()
        self.aliases = {}
        self.__hooks = {}

    def update(self, dict):
        for k in dict.iterkeys():
            self[k] = dict[k]
        return

    def __contains__(self, k):
        return k in self.aliases

    has_key = lambda self: self.aliases.has_key(k)
    items = lambda self: list(self.iteritems())
    keys = lambda self: list(self.iterkeys())

    __item_id = 0
    def __new_record(self):
        '''Allocates an id, and creates a new record initialized as None'''
        id = self.__item_id
        self.__item_id += 1
        super(symboltable, self).__setitem__(id, None)
        self.__hooks[id] = lambda symboltable,symbolname:True
        return id

    def __del_record(self, id):
        super(symboltable, self).__delitem__(id)
        del(self.__hooks[id])
        return True

    def __getitem__direct(self, (module,symbolname)):
        return super(symboltable,self).__getitem__(self.aliases[(module,symbolname)])

    def __setitem__direct(self, (module,symbolname), value):
        key = (module,symbolname)
        if key not in self.aliases:
            id = self.__new_record()
            self.aliases[key] = id
        else:
            id = self.aliases[key]
        super(symboltable, self).__setitem__(id, value)

        p = self.__hooks[id]
        self.__hooks[id] = lambda symboltable,symbolname:True
        p(self, key)
        self.__hooks[id] = p

    def __delitem__direct(self, (module,symbolname)):
        id = self.aliases[(module,symbolname)]
        aliases = (k for k,v in self.aliases.items() if v == id)
        for name in aliases:
            del(self.aliases[name])
        self.__del_record(id)

    def __getitem__(self, key):
        key = [(None,key), key][ isinstance(key, tuple) and len(key) == 2 ]
        return self.__getitem__direct(key)

    def __setitem__(self, key, value):
        key = [(None,key), key][ isinstance(key, tuple) and len(key) == 2 ]
        return self.__setitem__direct(key, value)

    def __delitem__(self, key):
        '''Delete a symbol from the store. Warning: This will delete all aliases and hooks to the symbol as well'''
        key = [(None,key), key][ isinstance(key, tuple) and len(key) == 2 ]
        return self.__delitem__direct(key)

    ### aliases
    def __alias_expand(self, names):
        for x in ([(None,n),n][isinstance(key, tuple) and len(n) == 2] for n in names):
            yield x
        return

    def alias(self, name, target):
        '''Add an alias from one symbol name to another'''
        name,target = tuple(self.__alias_expand([name,target]))
        self.aliases[name] = self.aliases[target]
        return True

    def unalias(self, name):
        '''Remove a symbol alias. Free the record when there's no aliases left.'''
        name, = tuple(self.__alias_expand([name]))

        id = self.aliases[name]
        del(self.aliases[name])

        count = len([1 for k,v in self.aliases.items() if v == id])
        if count == 0:
            self.__del_record(id)
        return True

    ### hooks. yes lame, but in case an implementation needs to update more symbols on update of one.
    def hook(self, name, fn):
        '''
        Adds a symbol merge hook for the specified symbol
        Note: Be careful when accessing things in your closure as your namespace might change on you.
        '''
        name, = tuple(self.__alias_expand([name]))
        id = self.aliases[name]
        old = self.__hooks[id]
        self.__hooks[id] = fn
        return old

    def unhook(self, name):
        '''Remove a symbol merge hook for the specified symbol'''
        name, = tuple(self.__alias_expand([name]))
        id = self.aliases[name]
        old = self.__hooks[id]
        del(self.__hooks[id])
        return old

    ### operations
    def updatesymbols(self, dict, symbolnames=None):
        '''Update specified symbols using the provided dictionary as input. Return the symbolnames updated.'''
        raise NotImplementedError
        dictnames = [symbolnames, dict.iterkeys()][symbolnames is None]
        symbolnames = self.__alias_expand(dict.iterkeys())
        for name,source in zip(symbolnames,dictnames):
            self[name] = dict[source]
        return symbolnames

    def merge(self, store, symbolnames=None):
        '''merge symboltables'''
        if symbolnames is None:
            symbolnames = store.aliases.keys()
        localnames = symbolnames = set(self.__alias_expand(symbolnames))
        #localnames = set((([module,store.modulename][module is None],symbolname) for module,symbolname in symbolnames))

        def generate_key2alias_lookup(st, symbolnames):
            for key in symbolnames:
                yield (key, tuple((name for name,x in st.aliases.iteritems() if x == st.aliases[key])))
            return

        def generate_id2value_lookup(st, symbolnames):
            for key in symbolnames:
                id = st.aliases[key]
                yield (id, super(symboltable, st).__getitem__(id))    # (id, value)
            return

        def generate_name2id_lookup(st, symbolnames):
            for key in symbolnames:
                yield (key, st.aliases[key])
            return

        # for importing values by id
        store_lookup_value_by_id = dict(generate_id2value_lookup(store, symbolnames))
        store_lookup_aliases_by_key = dict(generate_key2alias_lookup(store, symbolnames))

        # add new elements that we're merging in
        for n in localnames.difference(self.viewkeys()):
            self.__setitem__direct(n, None)

        local_lookup_aliases_by_key = dict(generate_key2alias_lookup(self, localnames))

        result = set()
        for ln,id in generate_name2id_lookup(self, localnames):
            module,symbolname=ln
            check = super(symboltable, self).__getitem__(id)
            sn = ([module,None][module==store.modulename],symbolname)
            value = store_lookup_value_by_id[store.aliases[sn]]

            # FIXME: I should break this function into two parts in order to pre-check for symbol issues
#            if check is not None:
#                logging.debug('%s : merge : Destination symbol %s has already been initialized with %s'% (self.name(), ln, repr(check)))
            if value is None:
                logging.debug('{:s} : merge : Source symbol {!r} is uninitialized'.format(self.name(), sn))

            # copy value, and call it's hook
            super(symboltable, self).__setitem__(id, value)
            self.__hooks[id](self, ln)

            # add aliases
            a,b = set(local_lookup_aliases_by_key[ln]),set(store_lookup_aliases_by_key[sn])
            [ self.alias(x,ln) for x in b ]

            # remove other aliases
            [ self.unalias(x) for x in b.difference(a) ]

            # save the symbolname we updated
            result.add(ln)
        return result

    def __repr__(self):
       return ' '.join((self.name(), '{!r}'.format(dict((([([k,(self.modulename,k[1])][k[0] is None],v) for k,v in self.iteritems()]))))))

#####################
class base(symboltable):
    '''
    Abstraction over a file-source that contains segmented symbol information

    if a segment of None is provided, this will be a segment of all unallocated data in the store
    '''

    scopesegment = None     # dict keyed by segmentname of sets of strings that contain symbolnames
    scope = None        # dict keyed by scope of symbolnames

    ## initialization
    def __init__(self, **kwds):
        super(base, self).__init__(**kwds)
        self.scopesegment = {}      # cache for organizing symbolname by segment

        self.scope = {}         # cache for searching symbolname by scope
        for x in (LocalScope,GlobalScope,ExternalScope):
            self.scope[x] = set()

        # add the baseaddress
        self.add((None,BaseAddress), 0, LocalScope)
        self.hook((None,BaseAddress), lambda s,n: self.__sym_realign(s[n]))

    def __delitem__(self, key):
        '''Delete a symbol from the store. This will also delete scopes.'''
        key = [(None,key), key][ isinstance(key, tuple) and len(key) == 2 ]

        for sc,names in self.scope.iteritems():
            names.discard(key)

        return super(base, self).__delitem__(key)

    def __sym_realign(self, baseaddress):
        '''hook: If the base address was modified, then auto-update each segment'''
        sections = self.listsegments()
        for n in sections:
            self[n] = baseaddress
            baseaddress += self.getsegmentlength(n)
        logging.debug('%s : relocated %d sections to %x'% (self.modulename,len(sections),baseaddress))
        return

    @classmethod
    def open(cls, path):
        raise NotImplementedError
        result = cls()
        result.modulename = path
        return result.do()

    @classmethod
    def load(cls, pointer, modulename):
        raise NotImplementedError
        self.modulename = modulename
        result = cls()
        return result.do()

    def loadsymbols(self, segmentname):
        '''initialize each symbol to contain the offset into the segment'''
        raise NotImplementedError('This should be inherited by a subclass')

    ## symboltable updating and enforcement
    def do(self):
        '''
        Read symbols and .add each one to the symbol table
        Adds hooks for updating symbols on segment relocation
        '''
        def __sym_relocate(s, name):
            '''hook: If a segmentname is updated, reinitialize it's symbols with the new base'''
            assert self == s, 'break if our self changes from our closure''s version'

            symbols = self.scopesegment[name[1]]
            baseaddress = self[name]
            if baseaddress is None:
                logging.debug('%s : relocating %d symbols in %s to None'% (s.name(), len(symbols), name[1]))
                for n in symbols:
                    self[n] = None
                return

            logging.debug('%s : relocating %d symbols in %s to %x'% (s.name(), len(symbols), name[1], baseaddress))

            symbols = self.loadsymbols(name[1])
            for n in symbols:
                self[n] = baseaddress + self[n]
            return

        # add hooks to update each segment
        for segmentname in self.listsegments():
            oldhook = self.hook(segmentname, None)
            def newhook(s,n):
                __sym_relocate(s,n)
                return oldhook(s,n)
            self.hook(segmentname, newhook)
        return self

    def __setitem__(self, name, value):
        '''Update symbol value iff the symbol has been defined somewhere'''
        try:
            super(base,self).__getitem__(name)
        except KeyError:
            raise KeyError('Symbol {!r} is unknown in {:s}'.format(name, self.modulename))

        super(base,self).__setitem__(name, value)

    def add(self, (module,symbolname), value, scope=GlobalScope, segment=None):
        '''Store the specified symbol in the symbol store'''
        if (module,symbolname) in self.keys():
            raise KeyError('Symbol {!r} is already defined as {!r} in {:s}'.format(symbolname, self[module,symbolname], self.modulename))

        # store our symbol and its value
        super(base, self).__setitem__((module,symbolname), value)

        # store in our segment index
        try:
            self.scopesegment[segment].add((module,symbolname))
        except KeyError:
            self.scopesegment[segment] = set([(module,symbolname)])

        # store it in our scope index
        try:
            self.scope[scope].add((module,symbolname))
        except KeyError:
            self.scope[scope] = set((module,symbolname))
        return

    ## general functions
    def __repr__(self):
        try:
            values = self.values()
            count = [0 for x in values if x is not None]
            return '{:s} -> [{:d} symbols, {:d} defined]'.format(self.name(), len(values), len(count))
        except AttributeError:
            pass
        return super(object, self).__repr__()

    def getglobals(self):
        result = set().union(*(self.scopesegment.values()))
        return list(result.intersection(self.scope[GlobalScope]))
    def getlocals(self):
        result = set().union(*(self.scopesegment.values()))
        return list(result.intersection(self.scope[LocalScope]))
    def getexternals(self):
        result = set().union(*(self.scopesegment.values()))
        return list(result.intersection(self.scope[ExternalScope]))

    def dump(self):
        g = [(k, (lambda:'{!r}'.format(self[k]),lambda:'{:#x}'.format(self[k]))[type(self[k]) in (int,long)]()) for k in self.getglobals()]
        l = [(k, (lambda:'{!r}'.format(self[k]),lambda:'{:#x}'.format(self[k]))[type(self[k]) in (int,long)]()) for k in self.getlocals()]
        gs = "globals:{!r}".format(g)
        ls = "locals:{:d}".format(len(l))
        return '\n'.join((gs,ls))

    def getundefined(self):
        return [ k for k,v in self.iteritems() if v is None ]

    globals = property(fget=lambda s:set(s.getglobals()))
    locals = property(fget=lambda s:set(s.getlocals()))
    externals = property(fget=lambda s:set(s.getexternals()))
    undefined = property(fget=lambda s:set(s.getundefined()))

    def getglobalsbysegmentname(self, segmentname):
        result = self.scopesegment[segmentname]
        return list(result.intersection(self.scope[GlobalScope]))
    def getlocalsbysegmentname(self, segmentname):
        result = self.scopesegment[segmentname]
        return list(result.intersection(self.scope[LocalScope]))

    ## for peering at what info is given to us
    def listsegments(self):
        '''Intended to be overloaded. list names of all available segments that are contained in this store'''
        warnings.warn('default method called', UserWarning)
        return []
    segments = property(fget=lambda s:s.listsegments())

    def getsegmentlength(self, name):
        '''Intended to be overloaded. get a segment's length so one can allocate for it...'''
        raise NotImplementedError
    def getsegmentprotection(self, name):
        '''Intended to be overloaded. get a segment's protection flags in binary rwx format.'''
        raise NotImplementedError
    def getsegment(self, name):
        '''Intended to be overloaded. get a segment from this store, relocated, and then return a string representing the segment data'''
        raise NotImplementedError
    def relocatesegment(self, name, data):
        raise NotImplementedError

    def merge(self, store, symbolnames=None):
        '''
        import the specified symbolnames from store into self.
        XXX: ensure your segment symbolnames exist before calling this.
        '''
        if symbolnames is None:
            symbolnames = store.aliases.keys()
        symbolnames = set(symbolnames)

        # segments
        store_segments = set((None,x) for x in store.scopesegment.iterkeys() if x is not None)

        # now actually merge the symbol values
        storenames = symbolnames = super(base,self).merge(store,symbolnames)
        #storenames = set((([module, None][module == store.modulename],name) for module,name in symbolnames))

        # copy scopes that we share from the store into ourselves
        my_scope = set(self.scope.keys())
        store_scope = set(store.scope.keys())
        for sc in my_scope.intersection(store_scope):        # (Local,Global,External)
            common = storenames.intersection(store.scope[sc])
            #common = set((([module,store.modulename][module is None],name) for module,name in common))
            self.scope[sc] = self.scope[sc].union(common)

        # copy segment scopes
        self_segments = set((None,x) for x in self.scopesegment.iterkeys())
        for m,n in store_segments.intersection(self_segments):
            common = storenames.intersection(store.scopesegment[n])
            #common = set((([module,store.modulename][module is None],name) for module,name in common))
            self.scopesegment[n] = self.scopesegment[n].union(common)

        return symbolnames

    def findsegment(self, address):
        '''Searches the symbol table for the segment containing the specified address'''
        for name in self.segments:
            b,l = self[None,name], self.getsegmentlength(name)
            if address >= b and address < b+l:
                return name
        raise ValueError("Unable to locate a segment containing address %x"% address)

class container(base):
    '''
    This class should contain sub-stores, and provides a single store containing all the merged symbols
    '''
    stores = None
    def __init__(self):
        super(container, self).__init__()
        self.stores = []
        self.storesegments = {}     # for splitting 1 segment to multiple segments

    def getmember(self, name):
        return self.stores[name]

    def getmembercount(self):
        return len(self.stores)

    def addstore(self, store):
        '''add a store to a container'''
        self.stores.append(store)
        self.prepare(store)

    def do(self):
        '''Execute something when initializing this container'''
        raise NotImplementedError

    def prepare(self, store):
        '''Imports symbol/segment info from the provided store'''
        # segments
        for n in store.listsegments():
            self.addsegment(n, -1, n, store)

        # import some globals from a store
        self.merge(store, store.getglobals())

        externals = store.getexternals()
        # now import externals from the store
        self.merge(store, externals)
        self.scopesegment[None].update(externals)
        return self

    ## ordered segment stuff
    storesegments = None
    def addsegment(self, segmentname, index, storesegmentname, store):
        '''Add a segment to the container's segment list'''

        def __seg_align(self, name):
            offset = self[name]
            if offset is None:
                logging.debug('%s : clearing segment %s address'% (self.name(), name[1]))
                for index,segmentname,store in self.storesegments[name[1]]:
                    store[segmentname] = None
                return

            logging.debug('%s : recalculating segment %s address %x'% (self.name(), name[1], offset))
            for index,segmentname,store in self.storesegments[name[1]]:
                store[segmentname] = offset
                offset += store.getsegmentlength(segmentname)
            return

        a = (index, storesegmentname, store)
        try:
            v = self.storesegments[segmentname]

        except KeyError:
            # doesn't exist, so create a new segment
            self.add((None, segmentname), None, LocalScope, segmentname)
            self.hook((None, segmentname), __seg_align)

            v = []
            self.storesegments[segmentname] = v

        v.insert(bisect.bisect(v, a), a)
        return

    ## segment stuff
    def listsegments(self):
        return self.storesegments.keys()

    def getsegment(self, segmentname):
        segments = self.storesegments[segmentname]
        data = array.array('c','')
        for index,sectionname,store in segments:
            data.fromstring( store.getsegment(sectionname) )
        return data.tostring()

    def getsegmentlength(self, name):
        segments = self.storesegments[name]
        return reduce(lambda a,b:a+b, (st.getsegmentlength(n) for i,n,st in segments))

    def getsegmentprotection(self, name):
        segments = self.storesegments[name]
        protections = set()
        for st in index,sectionname,store in segments:
            try:
                protections.add(st.getsegmentprotection(name))
            except KeyError as E:
                pass
            continue

        protections.discard(0)

        if len(protections) > 1:
            logging.error('{:s} : segment {:s} protection {:s} is inconsistent. defaulting to rw-. {!r}'.format(self.name(),name,protections))
            return 6
        return protections[0]

    def relocatesegment(self, segmentname, data):
        assert self[segmentname] is not None, '%s : segment %s address is undefined'%(self.name(), segmentname)

        # reset our symbol addresses
        self[segmentname] = self[segmentname]

        # preppin..
        segments = self.storesegments[segmentname]
        data = array.array('c',data)
        offset,baseaddress = 0,self[segmentname]

        for index,name,store in segments:

            size = store.getsegmentlength(name)
            globals = store.getglobalsbysegmentname(name)
            externals = store.getexternals()

            # merge in externals
            print(index,store,externals)
            store.merge(self, externals)

            # grab chunk
            chunk = data[offset:offset+size]

            # relocate all the symbols in the store just in case
            store[name] = baseaddress

            # relocate each chunk
            chunk = store.relocatesegment(name, chunk)

            # write it back
            data[offset:offset+size] = array.array('c',chunk)

            # import any globals that were calculated
            localnames = set((([module,store.modulename][module is None],symbolname) for module,symbolname in globals))
            for gname,lname in zip(globals,localnames):
                self[lname] = store[gname]

            offset += size
            baseaddress += size
        return data.tostring()

    def loadsymbols(self, segmentname):
        segments = self.storesegments[segmentname]
        symbols = self.scopesegment[segmentname]

        logging.debug('%s : reloading %d symbols'% (self.name(),len(symbols)))
        result = set()
        for index,sectionname,store in segments:
            updated = self.merge(store, store.loadsymbols(sectionname))
            result = result.union(updated.intersection(symbols))
        return result

if __name__ == '__main__':
    import store
    if False:
        z = store.symboltable()
        z['test'] = True
        z['blah'] = False
        print(z)
        print(z.aliases)

        print('whee -> blah')
        z.alias('whee', 'blah')
        print('whoo -> test')
        z.alias('whoo', 'test')

        print('test',z['test'])
        print('blah',z['blah'])
        print('whee',z['whee'])
        print('whoo',z['whoo'])

    if False:
        import random
        names = '_main,start,init_scheduler,init_sound,init_display,run'.split(',')
        externals  = 'GameInit,GameRun,Blah'.split(',')

        address = lambda:random.randint(0x15c0000,0x1f00000)
        a = store.symboltable()
        for x in names:
            a[x] = address()
        for x in externals:
            a[x] = None

        address = lambda:random.randint(0x6710000,0x6890000)
        b = store.symboltable()
        for x in externals:
            b[x] = address()

        print(a.merge(b, a.getglobals()+a.getexternals()))
        print(a['GameInit'] == b['GameInit'])

    if False:
        import random
        names = '_main,start,init_scheduler,init_sound,init_display,run'.split(',')
        externals  = 'GameInit,GameRun,Blah'.split(',')
        address = lambda:random.randint(0,0x7fffffff)


        a,b=store.symboltable(),store.symboltable()
        for x in names: a[x] = address()
        for x in externals: a[x] = None
        for x in externals: b[x] = 0

    if False:
        codes = '0,1,2,3,4,5,6,7,8,9,a,b,c,d,e,f'.split(',')
        codes = codes[len(codes)/2:]

        def updatesymbols(store, name):
            o = store[name]
            print('hook called with base %s:%x'%(name,o))
            for i,x in enumerate(codes):
                store[x] = o + 1000*i
            return

        a = store.symboltable()
        a['.text'] = 0x1000
        a['.data'] = 0x2000
        a['.rdata'] = 0x4000
        a.hook('.rdata', updatesymbols)

        print(a)
        a['.rdata'] = 0
        print(a)

    if False:
        a = store.symboltable()
        b = {'_main':100,'_exit':400}
        a.updatesymbols(b)
        print(a)
        c = {'_main':0xdeaddead,'_exit':0}
        a.updatesymbols(c, ['_exit'])

    if False:
        a,b = store.base(),store.base()

        s=lambda x:(None,x)
        a.add( s('globally'), 0, store.GlobalScope )
        a.add( s('locally'), 0, store.LocalScope )
        a.add( s('externally'), 0, store.ExternalScope )
        a['locally']=0x10101010
        a['globally']=0x02020202
        a['externally']=0x30303030

        b.merge(a, 'locally,globally,externally'.split(','))

        locally = (a.modulename,'locally')
        globally = (a.modulename,'globally')
        externally = (a.modulename,'externally')

        print(b[locally] == 0x10101010)
        print(b[globally] == 0x02020202)
        print(b[externally] == 0x30303030)

        scopes = [store.LocalScope, store.GlobalScope, store.ExternalScope]

        print(locally in b.scope[store.LocalScope] and locally not in (b.scope[store.GlobalScope], b.scope[store.ExternalScope]))
        print(globally in b.scope[store.GlobalScope] and globally not in (b.scope[store.LocalScope], b.scope[store.ExternalScope]))
        print(externally in b.scope[store.ExternalScope] and externally not in (b.scope[store.GlobalScope], b.scope[store.ExternalScope]))

    if False:
        import coff
        a = store.container()
        b = coff.object.open('../../obj/test.obj')
        a.addstore(b)

        print(a.listsegments() == b.listsegments())

#        print(a.getglobals())
#        print(b.getglobals())

    if False:
        import coff
        a = coff.object.open('../../obj/test.obj').do()

        a['.text'] = 0x10000000
        a['.data'] = 0xdeaddead

        b = a.getsegment('.data')
        b = a.relocatesegment('.data', b)

    if True:
        import coff
        a = coff.library.open('../../obj/test.lib').do()
        raise NotImplementedError("I need to write an actual test for coff.library, instead of doing it all at the command prompt")

        # need to confirm that when updating a segment in the main coff.library, it will update the segment in each of the container's stores
        #     each of those stores will also need to their new segment addresses confirmed.
        #     each store will also need to get the addresses of their relocated symbols also confirmed
        # then the last thing to check is that the coff.library's symbol table was updated correctly.

        # last thing will be doing relocation

        # a coff.library object is somehow getting the locals from one of its stores \
        #     being duplicated into its namespace..
