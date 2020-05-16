import functools, itertools, types, builtins, operator, six
import abc, collections, copy
from . import base

# do we need to implement hooking on symbol assignment?

# do we need 2 types of addreses to assign a symbol or section or store? relative, absolute

class Scope:
    """Symbol scope"""
    class Local(object): pass
    class Global(object): pass
    class External(object): pass

class Permissions(set):
    """Segment permissions"""
    S, R, W, X, Unmapped = 8, 4, 2, 1, 0

    __map = {Unmapped: 'Unmapped', R: 'R', W: 'W', X: 'X', S: 'S'}
    __unmap = {value : key for key, value in __map.items()}

    def add(self, value):
        if value in self.__unmap.keys():
            return self.add(self.__unmap[value])

        if value not in {self.R, self.W, self.X, self.S, self.Unmapped}:
            raise AssertionError

        if value == self.Unmapped:
            return self.clear()

        return super(Segments.Permissions, self).add(value)

    def __repr__(self):
        cls = self.__class__
        return '{:s}({!r})'.format(cls.__name__, map(self.__map.get, self))

class Relocations(base.OrderedSet): # ordered-set?
    """This represents relocations that are in a store.

    There should be multiple relocation types that a store implementor must add to
    this set.

    (?) To implement the IAT, could one relocation type be an "allocate" type?
        In this case, the symbol value would be what gets written to the allocated
        spot. The addresses of each allocated entry will need to be flattened to
        determine what is contiguous in order to allocate for it.

    relocation = name, size, relo_type, base_type, target(?)
    name = symbolic identity
    size = number of bytes (16/32/64)
    relo_type = virtual address, absolute address, offset, exact, specifc instruction
    base_type = relative to segment, relative to image, relative to target, relative to import table(?), relative to export table(?), relative to thunk table(?)
    target = some symbol, address, or index
    """
#    owner = store
#
#    add             # adds a new relocation type that points to a target(s?) using the value of a symbol
#    getbysymbol     # gets the relocations for a specific symbol
#    getbysegment    # gets the relocations for a specific segment
#

class Symbols(base.MutableMapping):
    """This object contains a symboltable.

    Symbols here can be modified to different addresses. This values here will be used
    by the relocations object.

    (?) Each symbol is represented by (module, name, scope).
    If there is no module, then None will be used.

    There's 3 scopes available. Global,Local,External,Alias

    (?) External symbols might require some way to determine the "glue" symbol that is
        used to contain the plt code to branch correctly out of a function.

    (?) It should be possible to assign an alias symbol to any symbol. This way if a
        symbol is updated, all it's aliases will contain the same value.

    All symbol assignments are done by offset from base of parent.
    """

    __slots__ = '_data', '_scope', '_store'

    def __init__(self, store):
        self._data = base.AliasMapping()
        self._scope = {
            Scope.Global : base.OrderedSet(),
            Scope.Local : base.OrderedSet(),
            Scope.External : base.OrderedSet(),
        }
        self._store = store

    # implementations
    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for item in self._data:
            yield item
        return

    def __getitem__(self, name):
        return self._data[name]

    def __setitem__(self, name, value):
        if name in self._data:
            self._data[name] = value
            return
        raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))

    def __delitem__(self, name):
        raise KeyError("Refusing to remove symbol {!r} from {!s}".format(name, object.__repr__(self)))

    # properties
    data = property(fget=lambda self: self._data)
    scope = property(fget=lambda self: self._scope)
    store = property(fget=lambda self: self._store)

    # tools
    def _findscope(self, name):
        for sc, set in self._scope.items():
            if name in set:
                return sc
            continue
        raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))

    # single symbols
    def add(self, name, scope=Scope.Local):
        """Reserve a slot in `scope` for the symbol `name`"""

        try:
            sc = self._findscope(name)

        except KeyError:
            pass

        else:
            raise KeyError("Symbol {!r} already exists in {!r}: {!s}".format(name, sc, object.__repr__(self._scope[scope])))

        self._scope[scope].add(name)
        self._data[name] = None

    def remove(self, name):
        """Remove the slot allocated for symbol `name`. This will also remove it from its scope."""
        sc = self._findscope(name)
        self._scope[sc].remove(name)
        return self._data.pop(name)

    # multiple symbols
    def apply(self, fn, scope=None):
        if scope is None:
            for item in self._data.keys():
                self._data[item] = fn(self._data[item])
            return

        for item in self._scope[scope]:
            self._data[item] = fn(self._data[item])
        return

    def update(self, iterable):
        """Update the table with the specified `iterable`."""
        res = {}
        for name, value in iterable:
            if name not in self._data:
                raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))
            res[name] = self._data[name]
            self._data[name] = value
        return res

    def merge(self, other):
        if not isinstance(other, base.AliasDict):
            raise AssertionError

        count = set(self._data) - set(other._data)
        self._data.update(other)
        [self._scope[sc].update(data) for sc, data in other._scope]
        return count

    # aliases
    def alias(self, target, name):
        self._data.alias(target, name)
        return self._data[target]

    def unalias(self, name):
        return self._data.unalias(name)[0]

    # general
    def getglobals(self):
        return self._scope[Scope.Global]
    def getlocals(self):
        return self._scope[Scope.Local]
    def getexternals(self):
        return self._scope[Scope.External]
    def getaliases(self):
        return self._data.aliases()
    def getundefined(self):
        return {key for key in self._data if self._data[key] is None}

#class Segments(base.Mapping):
#    """This object contains the segments for a store.
#
#    It is responsible for fetching and modifying segment data. If a segment is rebased,
#    then this will update all the relative symbols to the new base address.
#
#    This is responsible for populating the symbol table with the section addresses too.
#
#    Searching for an address is defined here.
#    """
#    # getsegmentinfo(identifier) = (symbolname, offset, length, permissions)
#    # getsegmentdata(index) = buffer(...)
#
#    @property
#    def symbols(self):
#        return self._symbols
#
#    @property
#    def store(self):
#        return self._store
#
#    def __init__(self, *symbols):
#        # current symbols and their values
#        self._data = base.HookedDict()
#
#        # list of segments and their segmentinfo
#        self._info = base.OrderedDict()
#
#        # list of original symbols for the segment
#        self._symbols = Symbols()
#
#        # backing file
#        self._store = symbols.store
#
#    # implementations
#    def __iter__(self):
#        for item in self._info:
#            yield item
#        return
#
#    def __getitem__(self, name):
#        return self._info[name]
#
#    # single segment creation and enumeration
#    def allocate(self, identifier):
#        # store the properties for the segment
#        name, perms, ofs, length = self.store.getsegmentinfo(identifier)
#        self._info[name] = identifier, perms, length
#
#        # add a symbol for identifier
#        self.symbols.add(name, scope=Scope.Local)
#        self.symbols[name] = ofs
#
#        self.hook(name, updatesymbols)
#        return name
#
#    def addsymbol(self, name, offset):
#        # FIXME: fetch symbols from store related to segment
#        raise NotImplementedError
#
#    def list(self):
#        return self._segments.keys()
#
#    def copy(self, identifier):
#        return self._segments[identifier]
#
#    def drop(self, identifier):
#        return self._segments.pop(identifier)
#
#    # FIXME
#    def findsegmentbyoffset(self, ofs):
#        ranges = [(ofs, self.getsegmentlength(item)) for item in self.listsegments()]
#
#    #owner = store
#    #listsegments
#    #getsegmentlength
#    #getsegmentprotection
#    #getsegment
#    #findsegmentbyoffset
#    #getsymbols
#    #__getitem__[index or name] = offset or baseaddress

class Segment(base.AbstractBaseClass):
    @abc.abstractmethod
    def name(self):
        '''Return the name of the segment.'''
        raise NotImplementedError

    @abc.abstractmethod
    def data(self):
        '''Return the bytes of the segment.'''
        raise NotImplementedError

    @abc.abstractmethod
    def offset(self):
        '''Return the offset of the segment.'''
        raise NotImplementedError

    @abc.abstractmethod
    def length(self):
        '''Return the size of the segment.'''
        raise NotImplementedError

    @abc.abstractmethod
    def protection(self):
        '''Return the permissions of the segment as a set.'''
        raise NotImplementedError

    @abc.abstractmethod
    def symbols(self):
        """Yield the identifer, offset or value, size, relocation of each symbol within the segment.

        The `relocation` that is yielded is specific to the implementation and is up to the implementor.
        """
        raise NotImplementedError

class Store(base.OrderedMapping, base.ReferenceFrom):
    @abc.abstractmethod
    def __init__(self):
        self._segments = base.OrderedSet()
        return super(Store, self).__init__()

    @abc.abstractmethod
    def segments(self):
        '''Yields each Segment contained within the store (non-cacheable).'''
        raise NotImplementedError

    @abc.abstractmethod
    def load_segment(self, seg):
        '''Load the symbols for the given segment into store.'''
        if seg in self._segments:
            raise KeyError("Refusing to load already existing segment {!s} into store.".format(seg))

        # Add our segment and return it so that an implementor can add its symbols
        self._segments.add(seg)
        return seg

    @abc.abstractmethod
    def load(self, *args):
        '''Load any symbols specific to the store.'''
        for seg in self.segments():
            seg = self.load_segment(seg)
            self[seg.name()] = seg.offset()

        # After loading the symbols for each segment, we need to lock our hash in
        # place. We do this by make a copy of ourselves and then referencing that
        # new copy since the keys shouldn't change anymore.
        return self.of(copy.copy(self))

#class Store(base.OrderedMapping):
#    """This is the base class that a user must implement to perform the work of a store.
#
#    This object will be used to generate segments, and apply relocations using the symbols
#    parsed out of the user's implementation.
#    """
#    #symbol = object
#    #relocations = object
#    #segments = object
#
#    #baseaddress = int   # assigning here will update all symbols (?)
#    #name = str
#
#    ## properties
#    __baseaddress = None
#    @property
#    def baseaddress(self):
#        return self.__baseaddress
#    @baseaddress.setter
#    def baseaddress(self, address):
#        (res, self.__baseaddress) = (self.__baseaddress, address)
#        return res
#
#    __name = None
#    @property
#    def name(self):
#        return self.__name or '<unnamed>'
#
#    ## methods
#    def __init__(self):
#        self.relocations = Relocations()
#        self.segments = Segments()
#        self.symbol = Symbols()
#
#    def load(self, data):
#        self._data = data
#
#        for i in range(self.getsegments()):
#            symbol, ofs, length, perms = self.getsegmentinfo(i)
#            self.segments.new(symbol)
#        return self
#
#    ## abstract methods an implementor must implement
#    @abc.abstractmethod
#    def getsegment(self, name):
#        '''Return the bytes associated with the segment of the specified `name`.'''
#        raise NotImplementedError
#
#    @abc.abstractmethod
#    def getsegmentlength(self, name):
#        '''Return the size of the segment with the specified `name`.'''
#        return 0
#
#    @abc.abstractmethod
#    def getsegmentprotection(self, name):
#        '''Return the permissions of the segment with the specified `name` as a set.'''
#        empty = []
#        return {item for item in empty}

class container(Store):
    """This object contains multiple stores.

    This should wrap a number of stores. Fetching segments and things will return the contents
    contiguously. Adding another store will be merged into the container's symbol table. Each
    symbol will a (module, name) that points to the actual symbol located in the store.
    This way updating a symbol will update the correct store, and relocating any store contained
    within will update the correct symbols.

    Symbols
    """
#    symbol = object # updating anything here will locate the correct store, and update it there
#    stores = list   #, or ordered-set
#    segments = proxy
#    relocations = proxy
#
#    add     # add a store
#    get     # get a store by some identity

if __name__ == '__main__':
    # symbols
    self = a = Symbols(None)
    b = a._data
    print(a.add('_main'))
    print(a.add('start'))
    print(a.add('localfunction'))
    print(a.getundefined())
    print(a.getlocals())
    print(a.getglobals())
    print(a.getexternals())
    a['_main'] = 0x14
    a['start'] = 0
    print(a.alias('start', 'EntryPoint'))
    print(a._scope)
    print(a._data)
    #a.unalias('EntryPoint')
    print(a['EntryPoint'])
    print(self.remove('start'))
