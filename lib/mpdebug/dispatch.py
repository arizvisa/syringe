import logging
#logging.root=logging.RootLogger(logging.DEBUG)

class event(list):
    '''Set of callbacks that will get executed'''
    def __init__(self, status):
        self.status = status
    def execute(self, *args, **kwds):
        result = self.status.userignore
        for fn in list(self):
            try:
                res = fn(*args, **kwds)
                if res is self.status.userbreak:
                    result = self.status.userbreak
                continue
            except:
                logging.exception("debug.dispatch.event raised an Exception and will break to the user:")
                result = self.status.userbreak
        return result

    def add(self, function):
        self.append(function)
        return function

    def remove(self, function):
        for i,x in enumerate(self):
            if x == function:
                del(self[i])
            continue
        return function

    def clear(self):
        del(self[:])

class system(dict):
    defaultfields = list     # functions that are used to dynamically generate each component of the 'id'

    # custom event handlers
    userbreak = object()       # break to the user
    userignore = object()      # ignore (this isn't used since userbreak is compared for explicitly

    def __init__(self, **kwds):
        self.scope = kwds

    def register(self, id, function):
        if not isinstance(id, tuple):
            id = id,
        if id not in self:
            self[id] = event(self)
        self[id].add(function)
        return function

    def unregister(self, id, function):
        if not isinstance(id, tuple):
            id = id,
        self[id].remove(function)
        if len(self[id]) == 0:
            del(self[id])
        return function

    def unregister_all(self, id):
        if not isinstance(id, tuple):
            id = id,
        self[id].clear()
        del(self[id])
        return id

    def dispatch(self, id, *args, **kwds):
        if not isinstance(id, tuple):
            id = id,

        # globals
        result = self.__dispatch(id, args, kwds)
        if result is self.userbreak:
            logging.debug('dispatch.system - global returned user-break - %s'%repr(id))

        # execute a search for every defaultitem
        for function in self.defaultfields:
            id += function(**self.scope),

            res = self.__dispatch(id, args, kwds)
            if res is self.userbreak:
                result = self.userbreak
            continue

        if result is self.userbreak:
            logging.debug('dispatch.system - return user-break = %s'%repr(id))
        return result

    def __dispatch(self, id, args, kwds):
        # no handlers for it
        if id not in self:
            return self.userignore

        # execute the event
        ev = self[id]
        kwds.update(self.scope)
        result = ev.execute(*args, **kwds)

        # process the result
        if result is self.userbreak:
            logging.debug("dispatch.system -> user-break - %s"%repr(id))
        logging.debug("dispatch.system -> ignore - %s"%repr(id))
        return result

    def new_dispatch(self, id):
        return lambda *args,**kwds: self.dispatch(id, *args, **kwds)

if __name__ == '__main__':
    import dispatch
    reload(dispatch)

    class number(object):
        numb = 'A'
        @classmethod
        def next(cls):
            cls.numb = chr(ord(cls.numb)+1)
            print('just switched to %s'%cls.numb)
            return cls.numb
        @classmethod
        def reset(cls):
            cls.numb = 'A'

    class test_d(dispatch.system):
        defaultitems = [ lambda s: s.next() ]

    def printid(n):
        def callback(*args, **kwds):
            print('dispatched to callback %s'% n)
            return dispatch.userignore
        return callback

    def printidbreak(n):
        def callback(*args, **kwds):
            print('dispatched to callback %s'% n)
            return dispatch.userbreak
        return callback

    a = test_d(number)
    a.register('!', printid("# !"))
    a.register(('!','C'), printidbreak("# !C"))

#    a.dispatch('!')
    print(number.numb)

