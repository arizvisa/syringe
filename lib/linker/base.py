import functools, itertools, types, builtins, operator, sys
import six, abc, copy, collections, weakref

if sys.version_info.major < 3:
    Hashable = collections.Hashable
    Mapping = collections.Mapping
    MutableSet = collections.MutableSet
    MutableMapping = collections.MutableMapping
    ItemsView = collections.ItemsView

else:
    import collections.abc
    Hashable = collections.abc.Hashable
    Mapping = collections.abc.Mapping
    MutableMapping = collections.abc.MutableMapping
    MutableSet = collections.abc.MutableSet
    ItemsView = collections.abc.ItemsView

### Some metaclasses to implement

# Ripped out of collections.abc
def _check_methods(C, *methods):
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True

# Standard implementation of the Copyable metaclass
if sys.version_info.major < 3:
    class AbstractBaseClass(object):
        __metaclass__ = abc.ABCMeta

        @staticmethod
        def __subclass__():
            '''Return a tuple containing the subclass and an iterable of its required methods.'''
            raise NotImplementedError

        @classmethod
        def __subclasshook__(cls, C):
            packed = cls.__subclass__()
            if packed:
                implementation, methods = packed if isinstance(packed, (tuple, list)) else (packed, ())
                return _check_methods(C, *methods) if cls is implementation else NotImplemented
            return NotImplemented

# Python2 can't parse this syntax, so we embed it in exec() to hide the
# definition from its parser
else:
    exec("""
    class AbstractBaseClass(metaclass=abc.ABCMeta):
        @staticmethod
        def __subclass__():
            '''Return a tuple containing the subclass and an iterable of its required methods.'''
            raise NotImplementedError

        @classmethod
        def __subclasshook__(cls, C):
            packed = cls.__subclass__()
            if packed:
                implementation, methods = packed if isinstance(packed, (tuple, list)) else (packed, ())
                return _check_methods(C, *methods) if cls is implementation else NotImplemented
            return NotImplemented
    """.strip())

### Abstract base classes
class Copyable(AbstractBaseClass):
    @staticmethod
    def __subclass__():
        return Copyable, ('copy', '__getstate__', '__setstate__')

    def copy(self):
        return copy.copy(self)

    @abc.abstractmethod
    def __getstate__(self):
        state = self.__dict__
        return { name : state[name] for name in state }

    @abc.abstractmethod
    def __setstate__(self, state):
        for name in state:
            attribute = state[name]
            setattr(self, name, attribute)
        return

### Core data structure implementations

# Python3 doesn't have ordered sets...so we have to implement this ourselves
class WeakLink(object):
    '''
    Ripped from http://code.activestate.com/recipes/576696/
    '''
    __slots__ = '__weakref__', 'previous', 'next', 'item'

class OrderedSet(MutableSet, Hashable, Copyable):
    __slots__ = '_data', '_order'

    def __hash__(self):
        iterable = map(hash, enumerate(self))
        return functools.reduce(operator.xor, iterable, 0)

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return not self.isdisjoint(other)

    def __getstate__(self):
        data = [ item for item in self]
        return data, dict(self._order)

    def __setstate__(self, state):
        data, self._order = state

        self._data = res = WeakLink()
        res.previous = res.next = res
        [ self.add(item) for item in data ]

    def __init__(self, iterable=None):
        items = iterable or []
        self._order = {}
        # FIXME: so it turns out that the lookdict() implementation only
        #        checks the cached version of a hash when looking for a
        #        key. if you implement your own object.__hash__ method,
        #        depending on how you insert into the dict, the cached
        #        hash for the key will not get updated resulting in all
        #        membership checks failing.

        self._data = res = WeakLink()
        res.previous = res.next = res

        self |= items

    def __contains__(self, item):
        return item in self._order

    def __len__(self):
        return len(self._order)

    def add(self, item):
        if item in self._order:
            raise TypeError("Element already exists within set {!s}: {!r}".format(object.__repr__(self), item))
        res, root, last = WeakLink(), self._data, self._data.previous
        self._order[item] = res

        res.previous, res.next, res.item = last, root, item
        last.next = root.previous = weakref.proxy(res)

    def discard(self, item):
        if item in self._order:
            res = self._order.pop(item)
            res.previous.next, res.next.previous = res.next, res.previous
        return

    def __iter__(self):
        root = self._data
        res = root.next
        while res is not root:
            yield res.item
            res = res.next
        return

    def __reversed__(self):
        root = self._data
        res = root.previous
        while res is not root:
            yield res.item
            res = res.previous
        return

    def __str__(self):
        return "{!s} {:s}".format(object.__repr__(self), ', '.join(map("{!r}".format, self)))
    __repr__ = __str__

class OrderedMappingItemsView(ItemsView):
    @classmethod
    def _from_iterable(self, it):
        return OrderedSet(it)

class OrderedMapping(MutableMapping, Hashable, Copyable):
    __slots__ = '_data', '_order', '_removed', '_update'
    def __hash__(self):
        iterable = map(hash, enumerate(self._order))
        return functools.reduce(operator.xor, iterable, 0)

    def __getstate__(self):
        available = (self._order | self._update) - self._removed
        res = { key : self._data[key] for key in available }
        return available, res

    def __setstate__(self, state):
        res, self._data = state
        self._order = OrderedSet(res)

        empty = OrderedSet()
        self._update, self._removed = empty, {item for item in empty}

    def __init__(self, iterable=None, **pairs):
        items = [item for item in pairs.items()]
        if isinstance(iterable, (dict, Mapping)):
            items += iterable.items()
        else:
            items += [(key, value) for key, value in iterable or []]

        self._data = {key : value for key, value in items}
        self._order = OrderedSet(key for key, _ in items)

        # Fields needed to implement soft-updates
        self._update = OrderedSet()
        self._removed = {None for item in self._update}

    # Python2-compatibility
    def viewkeys(self):
        return { key for key in self.keys() }
    def viewvalues(self):
        return [ value for value in self.values() ]
    def viewitems(self):
        return OrderedSet((key, value) for key, value in self.items())

    def __len__(self):
        return len(self._order - self._removed)

    def __iter__(self):
        for index, key in enumerate((self._order | self._update) - self._removed):
            yield key
        return

    def items(self):
        return OrderedMappingItemsView(self)

    def __getitem__(self, key):
        available = self._order | self._update
        if key not in available - self._removed:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key, value):

        # If our key is already missing, then we can re-enable it by removing
        # the key from our removed set.
        self._removed.discard(key)

        # Check if our key doesn't exist. If it doesn't, then we need to create
        # it. We don't want to tamper with our hash, so we simply add the key
        # to our update set.
        if all(key not in set for set in [self._order, self._update]):
            self._update.add(key)

        # Our key is either in our actual ordered set, or its in our update
        # set. So it should now be safe to update its value.
        self._data[key] = value

    def __delitem__(self, key):
        available = self._order | self._update
        if key not in available - self._removed:
            raise KeyError(key)

        # If it's in our update set, then we can remove it without concern.
        if key in self._update:
            self._update.discard(key)
            del(self._data[key])

        # Otherwise to avoid tampering with the actual dictionary, we can just
        # add it to our removed set so that the key appears to not exist.
        else:
            self._removed.add(key)
        return

    def __str__(self):
        cls = self.__class__
        return "{!s} {:s}".format(cls, ', '.join(itertools.starmap("{!s}={!r}".format, self.items())))
    __repr__ = __str__

class AliasMapping(MutableMapping, Hashable, Copyable):
    """A wrapper for a dictionary that allows one to create aliases for keys"""
    __slots__ = '_data', '_aliases', '_update', '_missing'

    def __hash__(self):
        iterable = map(hash, self._aliases.keys())
        return functools.reduce(operator.xor, iterable, hash(self._data))

    def __getstate__(self):
        used = six.viewkeys(self._aliases) | self._update
        return self._data, [(alias, self._alias[alias]) for alias in used - self._missing]

    def __setstate__(self, state):
        self._data, res = state
        self._aliases = OrderedMapping(res)

        # Reset our soft-update state
        empty = OrderedSet()
        self._update = empty
        self._missing = {item for item in empty}

    def __init__(self, backing=None):
        res = backing or {}
        if not isinstance(res, (dict, Mapping)):
            raise TypeError(res)
        self._data, self._aliases = res, OrderedMapping()

        # Fields needed to implement soft-updates
        self._update = OrderedSet()
        self._missing = {None for item in self._update}

    # tools
    def _getkey(self, key):
        used = six.viewkeys(self._aliases) | self._update
        if key in used - self._missing:
            key = self._aliases[key]
        return key

    def _getaliases(self, target):
        used = six.viewkeys(self._aliases) | self._update
        return {key for key in used - self._missing if self._aliases[key] == target}

    # implementation
    def __iter__(self):
        available = six.viewkeys(self._data)
        used = six.viewkeys(self._aliases) | self._update
        for key in available | (used - self._missing):
            yield key
        return

    def __len__(self):
        items = [ item for item in self ]
        return len(items)

    def __contains__(self, key):
        available = six.viewkeys(self._data)
        used = six.viewkeys(self._aliases) | self._update
        return key in available | (used - self._missing)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)

        # Get our actual target key in case it's an alias
        res = self._aliases.get(key, key)
        return self._data[res]

    def __setitem__(self, key, value):
        res = self._aliases.get(key, key)

        # No need to do anything special.. Just need to update our
        # backing dictionary with the new value.
        self._data[res] = value

    def __delitem__(self, key):
        res = self._aliases.get(key, key)
        del(self._data[res])

        # Go through and soft-remove our aliases since the field is gone.
        aliases = self._getaliases(key)
        self._missing |= aliases

    # overloads
    def update(self, *args, **kwds):
        raise NotImplementedError
        self, other = args[0], args[1] if len(args) >= 2 else ()
        res = super(AliasMapping, self).update(*args, **kwds)
        if isinstance(other, AliasMapping):
            self._aliases.update(other._aliases)
        return res

    # aliases
    def aliases(self):
        for key in six.viewkeys(self._aliases) - self._missing:
            yield key
        return

    def alias(self, target, *aliases):
        used = six.viewkeys(self._data) | self._update
        if any(alias in used for alias in aliases):
            raise KeyError("Alias {!r} already exists in AliasMapping {!s}".format(item, object.__repr__(self)))

        create_count = 0
        for alias in aliases:
            self._missing.discard(alias)
            if alias not in self._aliases:
                create_count += 1
            self._aliases[alias] = target
        return create_count

    def unalias(self, *aliases):
        used = six.viewkeys(self._aliases) - self._missing

        # Make sure all the aliases we're removing are actually valid
        for alias in aliases:
            if alias not in used:
                raise KeyError(alias)
            continue

        # If so, then we can safely add them to our missing set
        [self._missing.add(alias) for alias in aliases]

    # general
    def __str__(self):
        cls = self.__class__
        iterable = ((key, self[key]) for key in self.keys())
        return '{!s} {!r}'.format(cls, ', '.join(itertools.starmap("{!s}={!r}".format, iterable)))
    __repr__ = __str__

    def __getattr__(self, attribute):
        return getattr(self._data, attribute)

class HookMapping(AliasMapping):
    """A dictionary that allows one to hook assignment of a particular key"""
    def __init__(self, backing=None):
        super(HookMapping, self).__init__(backing)
        self._hooks = {}

    def hook(self, key, F, args=(), kwds={}):
        target = self._getkey(key)
        if target not in self._data:
            raise KeyError("Target {!r} does not exist within HookDict {!s}".format(key, object.__repr__(self)))

        res = self._hooks.pop(target) if target in self._hooks else None
        def closure(self, key, value, F=F, args=tuple(args), kwargs=dict(kwds)):
            return F(self, key, value, *args, **kwargs)
        self._hooks[target] = closure
        return res

    def unhook(self, key):
        target = self._getkey(key)
        return self._hooks.pop(target)

    def _execute_hook(self, key, value):
        Ffalse = lambda *args, **kwargs: False

        target = self._getkey(key)
        if target in self._hooks:
            try:
                F, self._hooks[target] = self._hooks[target], Ffalse
                res = F(self, key, value)

            finally:
                self._hooks[target] = F
            return res if isinstance(res, bool) else True
        return True

    def __iter__(self):
        return super(HookMapping, self).__iter__()

    def __len__(self):
        return super(HookMapping, self).__len__()

    def __contains__(self, key):
        return super(HookMapping, self).__contains__(key)

    def __setitem__(self, key, value):
        res = self._execute_hook(key, value)
        if res:
            target = self._getkey(key)
            return super(HookMapping, self).__setitem__(target, value)
        return

    def __getitem__(self, key):
        return super(HookMapping, self).__getitem__(key)

    def __delitem__(self, key):
        target = super(HookMapping, self)._getkey(key)
        if target in self._hooks:
            F = self.unhook(target)
        return super(HookMapping, self).__delitem__(key)

    def __getstate__(self):
        res = super(HookMapping, self).__getstate__()
        return res, self._hooks

    def __setstate__(self, state):
        res, self._hooks = state
        super(HookMapping, self).__setstate__(res)

class MergedMapping(MutableMapping, Copyable):
    """A dictionary composed of other Mapping types"""
    __slots__ = '_cache', '_data'

    def __init__(self):
        super(MergedMapping, self).__init__()

        # This is a dictionary of WeakSet. Each key is the symbol, and inside
        # each set is each dictionary that could own it
        self._cache = {}

        # This OrderedSet contains a reference to all the dictionaries that could
        # be contained in the cache. We use an ordered set so we can prioritize
        # the dicts that are updated
        self._data = OrderedSet()

    def __getstate__(self):
        Findex = functools.partial(operator.getitem, { item : index for index, item in enumerate(self._data) })

        # Pack a list of our backend mappings, and a lookup table that maps the tables in each symbol into the list.
        return [ item for item in self._data ], { symbol : tuple(map(Findex, item)) for symbol, item in self._cache.items() }

    def __setstate__(self, state):
        data, symbols = state

        # Create a closure that is responsible for converting an index into the mapping reference
        Freference = functools.partial(operator.getitem, { index : item for index, item in enumerate(data) })

        # Convert our backend mappings back into an OrderedSet, and recreate the symbol table
        # so that each symbol contains a WeakSet that references the mappings from our backend set.
        self._data, self._cache = OrderedSet(data), { symbol : weakref.WeakSet(map(Freference, items)) for symbol, items in symbols.items() }

    def _sync_cache(self, D):
        if not isinstance(D, Mapping):
            cls = type(D)
            raise TypeError(cls)

        # Check that we haven't already been inserted into our set
        if D in self._data:
            raise ValueError

        # Make a copy of the mapping, and add it into our set
        reference = D.copy()
        self._data.add(reference)

        # Iterate through all of the keys that we need to update, just
        # so we can grab the WeakSet containing all of the mappings for
        # that particular key
        res = {item for item in reference} - {item for item in self._cache}
        for key in reference:
            cache = self._cache.setdefault(key, weakref.WeakSet())

            # Now that we got the set, we can add our mapping to it
            cache.add(reference)

        # And that was it. We're synchronized, and all we need to do
        # is return the number of keys that were created for the mapping
        # that we were given
        return len(res)

    def __len__(self):
        return len(self._cache)

    def __iter__(self):
        for key in self._cache:
            yield key
        return

    def __setitem__(self, key, value):
        items = self._cache[key]

        # Iterate through the WeakSet for the key that we were given,
        # and assign the value to each mapping contained therein
        for D in items:
            D[key] = value
        return

    def __getitem__(self, key):
        items = self._cache[key]

        # Grab all of the values from each dictionary in the WeakSet
        results = [D[key] for D in items]

        # Pop off the first value so we can validate if the dictionaries
        # are not in sync for some reason
        res = results.pop(0)
        if not all(item == res for item in results):
            raise KeyError('More than one different value was returned')

        # Everything in all the dicts should be synchronized, so we can
        # simply return what the user asked for
        return res

    def __delitem__(self, key):
        items = self._cache[key]

        # Pre-validate all of our mappings from the set so we don't
        # lose our synchronization
        for D in items:
            D[key]

        # Now we can go through and safely remove each key from the
        # dictionaries that were cached
        for D in items:
            del D[key]
        return len(items)

    def add(self, D):
        if D in self._data:
            raise ReferenceError("Dictionary {!s} already exists in MergedMapping {!s}".format(object.__repr__(D), object.__repr__(self)))

        # Now we can simply update our cache with this new mapping
        return self._sync_cache(D)

    def remove(self, D):
        if D not in self._data:
            raise ReferenceError("Dictionary {!s} does not exist in MergedMapping {!s}".format(object.__repr__(D), object.__repr__(self)))

        # All we need to do here is remove the mapping from our
        # OrderedSet, as that should be the only reference to it. Doing
        # this should result in the dictionary being removed from all
        # of the WeakSets in our cache.
        self._data.remove(D)

        # Now we can go through our cache and remove every set that is
        # empty. We only should have affected keys within the dictionary,
        # so that's all we need to check for.
        res = 0
        for key in {item for item in D} & {item for item in self._cache}:
            state = self._cache[key]

            # If the WeakSet is empty, then we can just pop off the key
            # because there's no reason to keep it. The dict that was
            # being reference should already be updated by the user's
            # usage anyways.
            if not state:
                del self._cache[key]
                res += 1
            continue
        return res

    def __repr__(self):
        return '{!s} ({:d})[{:s}] {!r}'.format(object.__repr__(self), len(self._data), ','.join(map(object.__repr__, self._data)), {k:self[k] for k in self.keys()})

if __name__ == '__main__':

    ### OrderedMapping order
    if True:
        a = OrderedMapping((item, None) for item in itertools.chain(range(5), range(-5, 0)))

        if list(a.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
            raise ValueError

    if True:
        a = OrderedMapping((item, None) for item in itertools.chain(range(5), range(-5, 0)))

        h = hash(a)
        del(a[0])
        if h != hash(a):
            raise ValueError

        if list(a.keys()) != [1,2,3,4,-5,-4,-3,-2,-1]:
            raise ValueError

    if True:
        a = OrderedMapping()
        h = hash(a)
        a[0] = None
        a[1] = None
        a[2] = None
        a[3] = None
        a[4] = None
        a[-5] = None
        a[-4] = None
        a[-3] = None
        a[-2] = None
        a[-1] = None
        if h != hash(a):
            raise ValueError
        if list(a.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
            raise ValueError

    if True:
        a = OrderedMapping()
        h = hash(a)
        a[0] = None
        a[1] = None
        a[2] = None
        a[3] = None
        a[4] = None
        a[-5] = None
        a[-4] = None
        a[-3] = None
        a[-2] = None
        a[-1] = None
        if h != hash(a):
            raise ValueError

        b = a.copy()
        if hash(b) == hash(a):
            raise ValueError

        if list(b.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
            raise ValueError

        c = b.copy()
        if hash(b) != hash(c):
            raise ValueError

        if list(c.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
            raise ValueError

    ### OrderedSet order
    if True:
        a = OrderedSet( ('bla','blah','blahh') )
        a.add('meh')
        a.add('hmm')
        a.add('heh')
        a.discard('hmm')
        a.remove('meh')

        if list(a) != ['bla','blah','blahh','heh']:
            raise ValueError

    ### AliasMapping aliases
    a = AliasMapping({})
    a.alias('fuck', 'a','b','c')
    a['blah'] = 10
    a['heh'] = 20
    a['fuck'] = True

    if True:
        if not a['fuck']:
            raise ValueError
        a.alias('fuck', 'a', 'b', 'c')
        if set(a.keys()) != {'fuck', 'blah', 'heh'} | {'a', 'b', 'c'}:
            raise ValueError
        if any(a[item] != a['fuck'] for item in 'abc'):
            raise ValueError
        a['b'] = 'huh'
        if any(a[item] != 'huh' for item in 'abc') or a['fuck'] != 'huh':
            raise ValueError

    ## AliasDict unalias a non-alias
    if True:
        try:
            a.unalias('heh')
        except KeyError:
            pass
        else:
            raise ValueError

    ## AliasDict unalias an alias target (non-alias)
    if True:
        try:
            a.unalias('fuck')
        except KeyError:
            pass
        else:
            raise ValueError

    ## AliasDict unalias some aliases
    if True:
        a.unalias('a')
        a.unalias('b')
        if set(a.aliases()) != {'c'}:
            raise ValueError

        if dict(a.items()) != dict(blah=10, heh=20, fuck='huh', c='huh'):
            raise ValueError

    ### HookMapping signalling
    class Signal(OSError): pass

    def ok(self, key, value):
        raise Signal(True)
    def ignore(self, key, value):
        raise Signal(False)

    a = HookMapping({})
    a['val1'] = 1
    a.alias('val1', 'alias1')
    a['alias1'] = 10

    if True:
        a['val2'] = 0
        res = a.hook('val2', ok)
        try:
            a['val2'] = 1
        except Signal as S:
            pass
        else:
            raise ValueError

    if True:
        a.alias('val2', 'alias2')
        try:
            a['alias2'] = 500
        except Signal as S:
            pass
        else:
            raise ValueError

    if True:
        a['val3'] = 20
        a.hook('val3', ignore)
        try:
            a['val3'] = 50
        except Signal as S:
            notok, = S.args
            if notok:
                raise ValueError
        else:
            raise ValueError
        a.alias('val3', 'alias4')

        try:
            a['alias4'] = 40
        except Signal as S:
            notok, = S.args
            if notok:
                raise ValueError
        else:
            raise ValueError

    ### WeakSet reference of OrderedMapping
    if True:
        x = OrderedMapping(dict(key1=1, key2=3))
        y = OrderedMapping(dict(key1=3, key2=1))
        state = {item.copy() for item in [x, y]}
        weak = weakref.WeakSet(state)
        if set(weak) != state:
            raise ValueError
        if set(weak) != {x, y}:
            raise ValueError
        state.discard(x)
        if set(weak) != {y}:
            raise ValueError
        if set(weak) != state:
            raise ValueError
        state.discard(y)
        if set(weak) != set():
            raise ValueError
        if set(weak) != set():
            raise ValueError

    ### MergedMapping
    class MockDict(MutableMapping, Hashable, Copyable):
        def __getstate__(self):
            return super(MockDict, self).__getstate__()
        def __setstate__(self, state):
            return super(MockDict, self).__setstate__(state)
        def __hash__(self):
            iterable = map(hash, sorted(self.keys()))
            return functools.reduce(operator.xor, iterable, 0)
        def __init__(self, **items):
            self._data = items
        def __setitem__(self, key, value):
            self._data[key] = value
        def __getitem__(self, key):
            return self._data[key]
        def __delitem__(self, key):
            del self._data[key]
        def __iter__(self):
            for key in self._data:
                yield key
        def __len__(self):
            return len(self._data)
        def __str__(self):
            return "{!r}".format(sorted(self._data.items()))
        __repr__ = __str__

    a = MockDict(**{'akey1':1,'akey2':3,'akey3':5})
    b = MockDict(**{'bkey1':0,'bkey2':1,'bkey3':2})
    c = MockDict(**{'ckey1':0,'ckey2':1,'ckey3':2})
    d = MockDict(**{'dkey1':0,'dkey2':1,'dkey3':2})
    e = MockDict(**{'bkey1':0,'ckey1':0,'dkey1':0})

    ## MergedMapping single-dict auto-synchronization
    if True:
        M = MergedMapping()
        if M != {}:
            raise ValueError
        M.add(a)
        if sorted(M.keys()) != sorted(a.keys()):
            raise ValueError
        M.remove(a)
        if M != {}:
            raise ValueError

    ## MergedMapping multiple-dict auto-synchronization
    if True:
        M = MergedMapping()
        M.add(b)
        M.add(e)
        if set(M.keys()) != {item for item in itertools.chain(b.keys(), e.keys())}:
            raise ValueError
        M.remove(b)
        if set(M.keys()) != set(e.keys()):
            raise ValueError
        if any(set(M._cache[item]) != {e} for item in M._cache):
            raise ValueError

    ## MergedMapping single-dict fetch and update
    if True:
        M = MergedMapping()
        M.add(b)
        if M['bkey2'] != b['bkey2']:
            raise ValueError
        M['bkey1'] = -1
        if b['bkey1'] != -1:
            raise ValueError
        b['bkey1'] = 0

    ## MergedMapping multiple-dict fetch and update
    if True:
        M = MergedMapping()
        M.add(b)
        M.add(e)
        if set(M._cache['bkey1']) != {b, e}:
            raise ValueError

        M['bkey1'] = -1
        if b['bkey1'] != -1:
            raise ValueError
        if e['bkey1'] != -1:
            raise ValueError
        M['bkey1'] = 0

        M.remove(e)
        M.remove(b)

    ## MergedMapping non-existent key
    if True:
        M = MergedMapping()
        M.add(b)
        M.add(c)
        M.add(d)
        M.add(e)

        try:
            M['nonexist'] = -1
        except KeyError:
            pass
        else:
            raise ValueError

        M.remove(b)
        M.remove(c)
        M.remove(d)
        M.remove(e)

    ## MergedMapping multiple-dict multiple-fetch
    if True:
        M = MergedMapping()
        M.add(b)
        M.add(c)
        M.add(d)
        M.add(e)

        if b not in M._data:
            raise ValueError
        if c not in M._data:
            raise ValueError
        if d not in M._data:
            raise ValueError
        if e not in M._data:
            raise ValueError

        M['bkey1'] = 41
        M['ckey1'] = 42
        M['dkey1'] = 43

        if b['bkey1'] != 41:
            raise ValueError
        if c['ckey1'] != 42:
            raise ValueError
        if d['dkey1'] != 43:
            raise ValueError

        M.remove(e)

        M['bkey1'] = 21
        M['ckey1'] = 22
        M['dkey1'] = 23

        if e['bkey1'] != 41:
            raise ValueError
        if e['ckey1'] != 42:
            raise ValueError
        if e['dkey1'] != 43:
            raise ValueError

        if b['bkey1'] != 21:
            raise ValueError
        if c['ckey1'] != 22:
            raise ValueError
        if d['dkey1'] != 23:
            raise ValueError
