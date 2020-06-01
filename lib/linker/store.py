import functools, itertools, types, builtins, operator, six
import abc, collections, copy
from . import base

# do we need to implement hooking on symbol assignment?

# do we need 2 types of addreses to assign a symbol or section or store? relative, absolute

class TypeEnumeration(object):
    class Get(object): pass
    def __new__(cls, name):
        return type(name, (object,), {})

    @staticmethod
    def Is(ns, t):
        return isinstance(t, type) and issubclass(t, ns)

    @staticmethod
    def Add(ns, name):
        if hasattr(ns, name):
            raise AttributeError(name)
        value = type(name, (ns,), {})
        value.__module__ = '.'.join((ns.__module__, ns.__name__))
        class get(TypeEnumeration.Get):
            def __get__(self, instance, owner=None):
                return value
        get.__name__ = name
        setattr(ns, name, get())

    @staticmethod
    def Iterate(ns):
        for item in ns.__dict__.values():
            if isinstance(item, TypeEnumeration.Get):
                yield item.__get__(None)
            continue
        return

# This is just a namespace to contain the available scope types.
Scope = TypeEnumeration('Scope')
TypeEnumeration.Add(Scope, 'Local')
TypeEnumeration.Add(Scope, 'Global')
TypeEnumeration.Add(Scope, 'External')

class Permissions(base.Set):
    """Segment permissions"""
    __slots__ = '_object',

    # XXX: should probably include other attributes like for a guard page,
    #      mapped (to a file), reserved, or pages that grow downwards.
    _valid = {item for item in 'rwx'}

    def __init__(self, *flags):
        if len(flags) == 1 and hasattr(flags[0], '__iter__'):
            flags = {item for item in flags[0]}
        if any(item.lower() not in self._valid for item in flags if item not in '-'):
            raise ValueError("Invalid or unknown permissions were specified: {!s}".format(', '.join(item.upper() for item in flags if item.lower() not in self._valid)))
        self._object = { item.lower() for item in flags if item not in '-'}

    def __getitem__(self, flag):
        return flag.lower() in self._object

    def emptyQ(self):
        return len(self._object) == 0

    def __contains__(self, flag):
        return flag.lower() in self._object

    def __len__(self):
        return len(self._object)

    def __iter__(self):
        for flag in self._object:
            yield flag.lower()
        return

    def __str__(self):
        iterable = (flag if flag.lower() in self._object else '-' for flag in sorted(self._valid))
        return str().join(iterable)

    def __repr__(self):
        cls = self.__class__
        if self.emptyQ():
            return '{:s}({!s})'.format(cls.__name__, 'Unmapped')
        return '{:s}({!s})'.format(cls.__name__, ', '.join(item for item in sorted(self._object)))

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

#class Symbols(base.MutableMapping):
#    """This object contains a symboltable.
#
#    Symbols here can be modified to different addresses. This values here will be used
#    by the relocations object.
#
#    (?) Each symbol is represented by (module, name, scope).
#    If there is no module, then None will be used.
#
#    There's 3 scopes available. Global,Local,External,Alias
#
#    (?) External symbols might require some way to determine the "glue" symbol that is
#        used to contain the plt code to branch correctly out of a function.
#
#    (?) It should be possible to assign an alias symbol to any symbol. This way if a
#        symbol is updated, all it's aliases will contain the same value.
#
#    All symbol assignments are done by offset from base of parent.
#    """
#
#    __slots__ = '_data', '_scope', '_store'
#
#    def __init__(self, store):
#        self._data = base.AliasMapping()
#        self._scope = {
#            Scope.Global : base.OrderedSet(),
#            Scope.Local : base.OrderedSet(),
#            Scope.External : base.OrderedSet(),
#        }
#        self._store = store
#
#    # implementations
#    def __len__(self):
#        return len(self._data)
#
#    def __iter__(self):
#        for item in self._data:
#            yield item
#        return
#
#    def __getitem__(self, name):
#        return self._data[name]
#
#    def __setitem__(self, name, value):
#        if name in self._data:
#            self._data[name] = value
#            return
#        raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))
#
#    def __delitem__(self, name):
#        raise KeyError("Refusing to remove symbol {!r} from {!s}".format(name, object.__repr__(self)))
#
#    # properties
#    data = property(fget=lambda self: self._data)
#    scope = property(fget=lambda self: self._scope)
#    store = property(fget=lambda self: self._store)
#
#    # tools
#    def _findscope(self, name):
#        for sc, set in self._scope.items():
#            if name in set:
#                return sc
#            continue
#        raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))
#
#    # single symbols
#    def add(self, name, scope=Scope.Local):
#        """Reserve a slot in `scope` for the symbol `name`"""
#
#        try:
#            sc = self._findscope(name)
#
#        except KeyError:
#            pass
#
#        else:
#            raise KeyError("Symbol {!r} already exists in {!r}: {!s}".format(name, sc, object.__repr__(self._scope[scope])))
#
#        self._scope[scope].add(name)
#        self._data[name] = None
#
#    def remove(self, name):
#        """Remove the slot allocated for symbol `name`. This will also remove it from its scope."""
#        sc = self._findscope(name)
#        self._scope[sc].remove(name)
#        return self._data.pop(name)
#
#    # multiple symbols
#    def apply(self, fn, scope=None):
#        if scope is None:
#            for item in self._data.keys():
#                self._data[item] = fn(self._data[item])
#            return
#
#        for item in self._scope[scope]:
#            self._data[item] = fn(self._data[item])
#        return
#
#    def update(self, iterable):
#        """Update the table with the specified `iterable`."""
#        res = {}
#        for name, value in iterable:
#            if name not in self._data:
#                raise KeyError("Symbol {!r} does not exist in {!s}".format(name, object.__repr__(self)))
#            res[name] = self._data[name]
#            self._data[name] = value
#        return res
#
#    def merge(self, other):
#        if not isinstance(other, base.AliasDict):
#            raise AssertionError
#
#        count = set(self._data) - set(other._data)
#        self._data.update(other)
#        [self._scope[sc].update(data) for sc, data in other._scope]
#        return count
#
#    # aliases
#    def alias(self, target, name):
#        self._data.alias(target, name)
#        return self._data[target]
#
#    def unalias(self, name):
#        return self._data.unalias(name)[0]
#
#    # general
#    def getglobals(self):
#        return self._scope[Scope.Global]
#    def getlocals(self):
#        return self._scope[Scope.Local]
#    def getexternals(self):
#        return self._scope[Scope.External]
#    def getaliases(self):
#        return self._data.aliases()
#    def getundefined(self):
#        return {key for key in self._data if self._data[key] is None}

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
#    @abc.abstractmethod
#    def symbols(self):
#        """Yield the identifer, offset or value, size, relocation of each symbol within the section.
#
#        The `relocation` that is yielded is specific to the implementation and is up to the implementor.
#        """
#        raise NotImplementedError
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

class Section(base.Transitive):
    '''
    This base class is responsible for a logical section which describes
    a partition of a loadable segment. This needs to be hashable as it's
    used to keep track of symbolic information that will be applied to
    a segment.
    '''

    @abc.abstractmethod
    def name(self):
        '''Return the unique identifier that is referenced by symbols.'''
        raise NotImplementedError

    @abc.abstractmethod
    def bounds(self):
        '''Returns a tuple containing the left and right bounds within its segment.'''
        raise NotImplementedError

class Segment(base.Transitive):
    '''
    This base class is responsible for managing an actual loadable segment
    which contains the data that should be mapped into memory.
    '''

    @abc.abstractmethod
    def data(self):
        '''Return the bytes of the segment as a bytearray.'''
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

    def contains(self, address):
        '''Returns whether the specified address is within the segment.'''
        offset, length = self.offset(), self.length()
        return offset <= address < offset + length

class Symbols(base.MutableMapping):
    def __init__(self):
        # This maps a symbol name directly to a scope+section+symbol pair
        self._slotmap = {}

        # This maps a section+symbol pair to a slot (containing an integral value)
        self._slots = {}

        # This is a lookup table for all the scopes
        self._scope = { scope : base.OrderedSet() for scope in TypeEnumeration.Iterate(Scope)}

class Store(base.HookMapping):
    @abc.abstractmethod
    def __init__(self):
        self._sections = base.OrderedSet()
        self._segments = base.OrderedMapping()

        # Create our symbols backing that we're actually assigning into
        res = Symbols()
        return super(Store, self).__init__(slots)

    @abc.abstractmethod
    def segments(self):
        '''Yields each Segment contained within the store (non-cacheable).'''
        raise NotImplementedError

    @abc.abstractmethod
    def sections(self):
        '''Yields each Section contained within the store that has symbols to process.'''
        raise NotImplementedError

    def add_section(self, section):
        '''This adds a Section instance to the store.'''
        if not isinstance(section, Section):
            raise TypeError("Type for {!s} is not a {!s}".format(section.__clss__, Section))
        if section in self._sections:
            raise ValueError("Section {!s} has already been added to store")
        self._sections.add(section)

    def add_symbol(self, name, scope, section, symbol):
        """Add the specified symbol to the store.

        The `name` is used as an identifier for the symbol within the
        specified `scope`. The `section` describes the section that is
        referencing the symbol, and `symbol` is arbitrary but must be
        hashable.
        """
        raise NotImplementedError

    def add_relocation(self, relocation, section, symbol):
        """Add the specified relocation to the store.

        The `section` and `symbol` is used to reference the symbol that
        the relocation is tied to. The `relocation` parameter that is
        provided is arbitrary and only used to inform the implementor
        what kind of relocation to apply to the section's data.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load_section(self, section):
        '''Load the symbols for the given Section into store.'''
        if section not in self._sections:
            raise KeyError("Unable to load unrelated section {!s} into store".format(seg))

        # Figure out which segment this section belongs to
        left, right = section.bounds()
        try:
            segment = next(seg for seg in self._segments if seg.contains(left))
        except StopIteration:
            raise LookupError("Unable to find segment containing section address {:#x}".format(left))
        if not segment.contains(right) and segment.offset() + segment.length() != right:
            raise LookupError("Segment {!s} does not contain entire section {:#x}<>{:#x}".format(segment, left, right))

        # Now that we've figured out the segment, we can add our section that
        # has just been loaded to its section list.
        processed = self._segments.setdefault(segment, [])
        processed.append(section)

        # FIXME: Return the number of symbols from the loaded section
        return len(processed)

#    @abc.abstractmethod
#    def load(self, *args):
#        '''Load any symbols specific to the store.'''
#        for seg in self.segments():
#            seg = self.load_segment(seg)
#            self[seg.name()] = seg.offset()
#
#        # After loading the symbols for each segment, we need to lock our hash in
#        # place. We do this by make a copy of ourselves and then referencing that
#        # new copy since the keys shouldn't change anymore.
#        return self.of(copy.copy(self))

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

if __name__ == '__main__':
    import ptypes, elf
    from linker import store

    # symbols
    self = a = store.Symbols(None)
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
