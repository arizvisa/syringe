import functools, itertools, types, builtins, operator, sys
import six, abc, copy, collections, weakref

if sys.version_info.major < 3:
    Hashable = collections.Hashable
    Mapping = collections.Mapping
    MutableSet = collections.MutableSet
    MutableMapping = collections.MutableMapping

else:
    import collections.abc
    Hashable = collections.abc.Hashable
    Mapping = collections.abc.Mapping
    MutableMapping = collections.abc.MutableMapping
    MutableSet = collections.abc.MutableSet

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
    class Copyable(object):
        __metaclass__ = abc.ABCMeta

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

        @classmethod
        def __subclasshook__(cls, C):
            if cls is Copyable:
                return _check_methods(C,  "__len__", "__iter__", "__contains__")
            return NotImplemented

# Python2 can't parse this syntax, so we embed it in exec() to hide the
# definition from its parser
else:
    exec("""
    class Copyable(metaclass=abc.ABCMeta):
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

        @classmethod
        def __subclasshook__(cls, C):
            if cls is Copyable:
                return _check_methods(C,  "__len__", "__iter__", "__contains__")
            return NotImplemented
    """.strip())

### Core data structure implementations

# Python3 doesn't have ordered sets...so we have to implement this ourselves
class OrderedSet(MutableSet, Hashable, Copyable):
    def __hash__(self):
        iterable = map(hash, enumerate(self._data))
        return functools.reduce(operator.xor, iterable, 0)

    def __getstate__(self):
        return self._data, self._order

    def __setstate__(self, state):
        self._data, self._order = state

    def __init__(self, iterable=None):
        items = iterable or []
        self._data = [ item for item in items ]
        self._order = { item : index for index, item in enumerate(self._data) }

    def __contains__(self, value):
        return value in self._order

    def __len__(self):
        return len(self._data)

    def add(self, value):
        if value in self._order:
            raise TypeError("Element already exists within set {!s}: {!r}".format(object.__repr__(self), value))
        self._order[value] = len(self._data)
        self._data.append(value)

    def discard(self, item):
        if item in self._order:
            index = self._order.pop(item)
            self._data.pop(index)
        return

    def __iter__(self):
        for item in self._data:
            yield item
        return

    def __str__(self):
        cls = self.__class__
        return "{!s} {:s}".format(cls, ', '.join(map("{!r}".format, self)))
    __repr__ = __str__

class OrderedDict(MutableMapping, Hashable, Copyable):
    def __hash__(self):
        iterable = map(hash, enumerate(self.items()))
        return functools.reduce(operator.xor, iterable, 0)

    def __getstate__(self):
        return self._data, self._order

    def __setstate__(self, state):
        self._data, self._order = state

    def __init__(self, iterable=None, **pairs):
        items = [item for item in pairs.items()]
        if isinstance(iterable, dict):
            items += iterable.items()
        else:
            items += [(key, value) for key, value in iterable or []]

        self._data = {key : value for key, value in items}
        self._order = [key for key, _ in items]

    # Python2-compatibility
    def viewkeys(self):
        return { key for key, value in self.items() }
    def viewvalues(self):
        return { value for key, value in self.items() }
    def viewitems(self):
        return { (key, value) for key, value in self.items() }

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        for index, key in enumerate(self._order[:]):
            if key in self._data:
                yield key
            else:
                self._order.pop(index)
            continue
        return

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key in self._data:
            # this is in linear time. we can probably optimize this out
            # with a weakref, but i'm tired right now...
            index = self._order.index(key)
            self._order.pop(index)

        self._data[key] = value
        self._order.append(key)

    def __delitem__(self, key):
        if key not in self._data:
            raise KeyError(key)

        # no need to update our _order because it'll be updated the
        # next time we iterate through it
        self._data.pop(key)

    def __str__(self):
        cls = self.__class__
        return "{!s} {:s}".format(cls, ', '.join(itertools.starmap("{!s}={!r}".format, self.items())))
    __repr__ = __str__

class AliasDict(MutableMapping, Hashable, Copyable):
    """A dictionary that allows one to create aliases for keys"""
    def __hash__(self):
        iterable = map(hash, self.items())
        return functools.reduce(operator.xor, iterable, hash(self._aliases))

    def __getstate__(self):
        return self._data, self._aliases

    def __setstate__(self, state):
        self._data, self._aliases = state

    def __init__(self, iterable=None, **pairs):
        items = [item for item in pairs.items()]
        if isinstance(iterable, dict):
            items += iterable.items()
        else:
            items += [(key, value) for key, value in iterable or []]
        self._data, self._aliases = {}, OrderedDict()

    # tools
    def _getkey(self, key):
        return self._aliases[key] if key in self._aliases else key

    def _getaliases(self, target):
        items = self._aliases.items()
        return {key for key, value in items if value == target}

    def __iter__(self):
        aliases, keys = (six.viewkeys(item) for item in [self._aliases, self._data])
        for key in keys | aliases:
            yield key
        return

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        aliases, keys = (six.viewkeys(item) for item in [self._aliases, self._data])
        return key in (keys | aliases)

    # abstract methods
    def __setitem__(self, key, value):
        res = self._getkey(key)
        self._data[res] = value

    def __getitem__(self, key):
        res = self._getkey(key)
        return self._data[res]

    def __delitem__(self, key):
        target = self._getkey(key)
        res = self._getaliases(target)
        [ self._aliases.pop(alias) for alias in res ]
        del self._data[target]

    # overloads
    def update(self, *args, **kwds):
        self, other = args[0], args[1] if len(args) >= 2 else ()
        res = super(AliasDict,self).update(*args, **kwds)
        if isinstance(other, AliasDict):
            other._aliases.update(self._aliases)
        return res

    # aliases
    def aliases(self):
        for key in self._aliases:
            yield key
        return
    def alias(self, target, *aliases):
        if any(alias in self._data for alias in aliases):
            raise KeyError("Alias {!r} already exists as a target in AliasDict {!s}".format(item, object.__repr__(self)))

        create_count = 0
        for alias in aliases:
            if alias not in self._aliases:
                create_count += 1
            self._aliases[alias] = target
        return create_count
    def unalias(self, *aliases):
        return [self._aliases.pop(alias) for alias in aliases]

    # general
    def __str__(self):
        cls = self.__class__
        iterable = ((key, self[key]) for key in self.keys())
        return '{!r} {!r}'.format(cls, ', '.join(itertools.starmap("{!s}={!r}".format, iterable)))
    __repr__ = __str__

class HookedDict(AliasDict):
    """A dictionary that allows one to hook assignment of a particular key"""
    def __init__(self, iterable=None):
        super(HookedDict, self).__init__(iterable)
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

    def __setitem__(self, key, value):
        res = self._execute_hook(key, value)
        if res:
            target = self._getkey(key)
            return super(HookedDict, self).__setitem__(target, value)
        return

    def __delitem__(self, key):
        target = self._getkey(key)
        if target in self._hooks:
            F = self.unhook(target)
        return super(HookedDict,self).__delitem__(key)

class MergedMapping(MutableMapping):
    """A dictionary composed of other Mapping types"""
    __slots__ = ['_cache', '_data']

    def __init__(self):
        super(MergedMapping, self).__init__()

        # This is a dictionary of WeakSet. Each key is the symbol, and inside
        # each set is each dictionary that could own it
        self._cache = {}

        # This OrderedSet contains a reference to all the dictionaries that could
        # be contained in the cache. We use an ordered set so we can prioritize
        # the dicts that are updated
        self._data = OrderedSet()

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
        return '{:s} {:s} {!r}'.format(object.__repr__(self), ','.join(map(object.__repr__,self._data)), {k:self[k] for k in self.keys()})

if __name__ == '__main__':

    ### OrderedDict order
    a = OrderedDict()
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
    if list(a.keys()) != [0,1,2,3,4,-5,-4,-3,-2,-1]:
        raise ValueError

    ### OrderedSet order
    a = OrderedSet( ('bla','blah','blahh') )
    a.add('meh')
    a.add('hmm')
    a.add('heh')
    a.discard('hmm')
    a.remove('meh')

    if list(a) != ['bla','blah','blahh','heh']:
        raise ValueError

    ### AliasDict aliases
    a = AliasDict()
    a.alias('fuck', 'a','b','c')
    a['blah'] = 10
    a['heh'] = 20
    a['fuck'] = True
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
    try:
        a.unalias('heh')
    except KeyError:
        pass
    else:
        raise ValueError

    ## AliasDict unalias an alias target (non-alias)
    try:
        a.unalias('fuck')
    except KeyError:
        pass
    else:
        raise ValueError

    ## AliasDict unalias some aliases
    a.unalias('a')
    a.unalias('b')
    if set(a.aliases()) != {'c'}:
        raise ValueError

    if dict(a.items()) != dict(blah=10, heh=20, fuck='huh'):
        raise ValueError

    ### HookedDict signalling
    class Signal(OSError): pass

    def ok(self, key, value):
        raise Signal(True)
    def ignore(self, key, value):
        raise Signal(False)

    a = HookedDict()
    a['val1'] = 1
    a.alias('val1', 'alias1')
    a['alias1'] = 10

    a['val2'] = 0
    res = a.hook('val2', ok)
    try:
        a['val2'] = 1
    except Signal as S:
        pass
    else:
        raise ValueError

    a.alias('val2', 'alias2')
    try:
        a['alias2'] = 500
    except Signal as S:
        pass
    else:
        raise ValueError

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

    ### WeakSet reference of OrderedDict
    x = OrderedDict(dict(key1=1, key2=3))
    y = OrderedDict(dict(key1=3, key2=1))
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
            iterable = map(hash, sorted(self.items()))
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
            return repr(self._data)
        __repr__ = __str__

    a = MockDict(**{'akey1':1,'akey2':3,'akey3':5})
    b = MockDict(**{'bkey1':0,'bkey2':1,'bkey3':2})
    c = MockDict(**{'ckey1':0,'ckey2':1,'ckey3':2})
    d = MockDict(**{'dkey1':0,'dkey2':1,'dkey3':2})
    e = MockDict(**{'bkey1':0,'ckey1':0,'dkey1':0})

    ## MergedMapping single-dict auto-synchronization
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
    M = MergedMapping()
    M.add(b)
    if M['bkey2'] != b['bkey2']:
        raise ValueError
    M['bkey1'] = -1
    if b['bkey1'] != -1:
        raise ValueError
    b['bkey1'] = 0

    ## MergedMapping multiple-dict fetch and update
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

    ## MergedMapping non-existent key
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

    ## MergedMapping multiple-dict multiple-fetch
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
