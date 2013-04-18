"""
This abstracts memory allocations for a target allocator, so you can
allocate/free arbitrarily sized blocks of memory, which it will
manage for you.

To use this, call:
memorymanager.new(pid=yourpid)
memorymanager.new(handle=yourhandle)
"""

### this module intends to provide an interface for managing address space inside another /context/ (whatever that may be, like a process)
### this includes things like allocations, frees, file mappings, code page creation...(using that one module or whatever that i wrote)

import allocator
import bitmap

# XXX: it might be cool to add an option to duplicate attributes from
#      another MemoryManager instance

def new(*args, **kwds):
    if len(args) == 1:
        alloc = args[0]
        return Managed(alloc)
    return Managed( allocator.new(**kwds) )

def provider(mm):
    '''Convert a memorymanager to a provider'''
    return mm

class __provider(object):
    '''Sort of makes it like a ptype provider'''
    __address = 0
    def seek(self, address):
        result = self.__address
        self.__address = address
        return result

    def consume(self, length):
        res = self.read(self.__address, length)
        self.__address += length
        return res

    def store(self, data):
        res = self.write(self.__address, data)
        self.__address += len(data)
        return res

class MemoryManager(__provider):
    allocator = None
    loaded = committed = dict

    def __init__(self, allocator):
        self.allocator = allocator
        self.loaded = {}
        self.committed = {}

    def read(self, address, length):
        '''Read /length/ bytes starting at /address/'''
        return self.allocator.read(address, length)     # XXX: we can probably optimize this so it does it by page size

    def write(self, address, data):
        '''Write /data/ to the location specified by /address/'''
        return self.allocator.write(address, data)

    def alloc(self, size):
        # keep track of how memory is organized, return a pointer to them
        raise NotImplementedError

    def free(self, pointer):
        # free that pointer
        raise NotImplementedError

    def load(self, size):
        '''Allocate some number of writeable bytes for later making executable'''
        allocator = self.allocator

        # allocate size
        pages = (size / allocator.getPageSize())+1

        # get a writeable page, and then write our code to it
        pointer = self.allocator.getWriteable(None, pages)
        assert pointer not in self.loaded.keys()  # heh

        # add pointer to lookup
        self.loaded[pointer] = pages

        return pointer

    def commit(self, pointer):
        '''Commit some pointer allocated via .load() to an executable page'''
        # fetch an executable version of the specified data, and add it to our committed list
        pages = self.loaded[pointer]

        pointer_executable = self.allocator.getExecutable(pointer, pages)
        assert pointer_executable not in self.committed.keys()

        self.committed[pointer_executable] = pages

        # if our page has been moved, then free the other one
        if pointer != pointer_executable:
            self.allocator.freeWriteable(pointer, pages)

        # we've marked the pages to executable, so they're nonwriteable anymore
        del(self.loaded[pointer])
        return pointer

    def __unload_committed(self, pointer, pages):
        self.allocator.freeExecutable(pointer, pages)
        del( self.committed[pointer] )

    def __unload_loaded(self, pointer, pages):
        self.allocator.freeWriteable(pointer, pages)
        del( self.loaded[pointer] )

    def unload(self, pointer):
        '''Unload memory that's been loaded or committed'''
        if pointer in self.committed:
            pages = self.committed[pointer] # assume it's farther along in its lifetime
            self.__unload_committed(pointer, pages)
            return

        pages = self.loaded[pointer]
        self.__unload_loaded(pointer, pages)

class Managed(MemoryManager):
    # XXX: i feel like this was largely influenced by my pathetic phk research from like 8 years ago
    arenas = dict
    allocations = dict    # lookup all page occupancy

    def __init__(self, allocator):
        super(Managed, self).__init__(allocator)

        self.allocations = {}
        self.arenas = {}

    def __alloc_dochunks(self, size):
        # initialize an arena if it doesn't exist
        k = 1<<bitmap.fit(size-1)

        try:
            self.arenas[k]

        except KeyError:
            self.arenas[k] = [ self.__alloc_arena(k) ]

        arena = self.arenas[k]

        # try really hard to allocate from it
        try:
            res = self.__alloc_from_bucket(arena, size)

        except ValueError:
            arena.append( self.__alloc_arena(k) )
            return self.__alloc_from_bucket(arena, size)

        return res

    def alloc(self, size):
        pagesize = self.allocator.getPageSize()
        if size < pagesize>>1:
            res = self.__alloc_dochunks(size)
        else:
            res = self.__alloc_pages((size+pagesize-1)/pagesize)

        # assign to page lookup
        pointer,type = res
        pagemask = self.allocator.getPageSize()-1
        page = pointer & ~pagemask

        self.allocations[page] = type
        return pointer

    def __alloc_pages(self, count):
        return (self.allocator.getWriteable(None, count), count)

    def __alloc_arena(self, elementsize, pages=1):
        '''allocates an arena for elements of /elementsize/'''
        allocator = self.allocator

        size = allocator.getPageSize()*pages
        pointer = allocator.getWriteable(None, pages)
        res = bitmap.new(0, size / elementsize )
        return (pointer, (int(elementsize), res))

    # XXX: this modifies /bucket/ directly...just a heads up.
    def __alloc_from_bucket(self, bucket, size):
        for i,n in zip(range(len(bucket)), bucket):
            pointer,(chunksize,layout) = n
            count = (size / chunksize)+1

            try:
                freeslot = bitmap.runscan(layout, 0, count)
            except ValueError:
                raise NotImplementedError('none free in index %d -> %s'% (i, bitmap.string(layout)))    # just because i haven't done this test case yet
                continue

            layout = bitmap.set(layout, freeslot, 1, count)

            # found a free slot, write it directly into bucket
            bucket[i] = (pointer, (chunksize, layout))
            return pointer + freeslot*chunksize, bucket[i]

        raise ValueError('Unable to allocate %d bytes out of bucket %s'% (size, repr(bucket)))

    def free(self, pointer):
        pagemask = self.allocator.getPageSize()-1
        page = pointer & ~pagemask

        # free that pointer
        allocation = self.allocations[page]
        if type(allocation) is tuple:
            chunksize,bitmap = allocation
            # we're a smaller chunk
            self.__free_arena(pointer)
            return

        # free those pages
        allocationPages = allocation
        self.allocator.freeWriteable(page, allocationPages)
        del( self.allocations[page] )
        return

    def __free_arena(self, pointer):
        pagemask = self.allocator.getPageSize()-1
        page = pointer & ~pagemask
        
        arena = self.allocations[page]
        basepointer,(chunksize,layout) = arena

        # convert pointer into index
        offset = pointer - basepointer
        index = offset / chunksize

        # clear the bit
        layout = bitmap.set(layout, index, False)
        self.allocations[page] = (basepointer,(chunksize,layout))

        # if all the bits are clear, we can remove this page
        if bitmap.empty(layout):
            self.allocator.freeWriteable(page, 1)
            del(self.allocations[page])
            return

        # perhaps zero the buffer out?
        return

if False and __name__ == '__main__':
    import sys
    import memorymanager,debugger

    debugger = debugger.Local()
#    debugger.attach(int(sys.argv[1], 0x10))

    v = memorymanager.new()

    list = []
    for n in range(4):
        res = v.alloc(0x400)
        list.append(res)

    print '\n'.join(map(hex,list))

    print '=' * 80
    for n in list:
        print 'free(%x)'% n
        v.free(n)

    print '.' * 80
    page = v.alloc(0x4000)
    print 'malloc(0x4000) = %x'% page
    v.free(page)
    print 'free(%x)'% page

#    debugger.detach()

if __name__ == '__main__':
    import memorymanager
    mm = memorymanager.new()

    a = mm.alloc(84)
    b = mm.alloc(88)
    print hex(a),hex(b)
