"""Primitive types for representing blocks of code that may be executed.

The pcode.block_t is an atomic type that is used to describe blocks of code
within a data structure. They only need the length, and can be used to
disassemble the referenced code. Depending on the currently selected architecture
the code can be disassembled or reassembled in arbitrary ways and thus the
relocations will be recalculated when the type is moved around. This can of
course change its size and thus this will need to be considered in whatever
the user uses the type for.

The other type that's defined is the pcode.pointer_t. This type is pretty much
the same as the ptype.pointer_t definition with the addition of the specification
of the calling convention. The initial value of the calling convention for all
types is assigned globally along with the architecture, but can be changed when
defining the type. If the user wishes to execute the code pointer, the user is
responsible for not only properly describing how to "interpret" the code pointer
for the defined architecture but for also ensuring that the executed code will
return back to the Python interpreter after its execution.
"""
import functools, itertools, types, operator, six
from six.moves import builtins

import ctypes

from . import ptype, bitmap, config, error, utils
Config = config.defaults
Log = Config.log.getChild('pcode')

class block_t(ptype.block):
    @classmethod
    def disassemble(self, offset, data):
        '''Given some bytes in ``data`` and their ``offset``, return a list of each instruction that composes it.'''
        iterable = bytearray(data)
        return [item for item in iterable]

    @classmethod
    def assemble(self, offset, input):
        '''Given a list of instructions in ``input`` and ``offset`` corresponding to the result from the block_t.disassemble method, return a block of bytes representing the assembled instructions.'''
        iterable = iter(map(six.int2byte, input))
        return bytes().join(iterable)

    def __getvalue__(self):
        offset, data = self.getoffset(), self.serialize()
        return self.disassemble(offset, data)

    def __setvalue__(self, *instructions, **attrs):
        offset, parameters = self.getoffset(), instructions
        if len(parameters) == 1 and builtins.isinstance(parameters[0], (tuple, list)):
            instructions, = parameters
            data = self.assemble(attrs.get('offset', offset), instructions)
            return super(block_t, self).__setvalue__(data, **attrs)
        return super(block_t, self).__setvalue__(*parameters, **attrs)

    def __getitem__(self, index):
        baseoffset, data = self.getoffset(), self.serialize()
        instructions = self.disassemble(baseoffset, data)
        if not builtins.isinstance(index, slice):
            item = instructions[index]
            return self.assemble(baseoffset + index, item)

        # First of all, grab the bounds that the user is trying to snag and
        # use them to fetch the items we're going to include. If any of the
        # indices are -1, then handle them specially because otherwise Python
        # will think we want a negative index when we really don't.
        start, stop, stride = index.indices(len(instructions))

        if stride > 0:
            direction = +1
            available = instructions[:stop : +1] if start < 0 else instructions[start : stop : direction]
            selected = instructions[:stop : stride] if start < 0 else instructions[start : stop : stride]

        elif stride < 0:
            direction = -1
            available = instructions[start : stop : -1] if stop > 0 else instructions[start :: direction]
            selected = instructions[start : stop : stride] if stop > 0 else instructions[start :: stride]

        else:
            raise ValueError(index)

        # Now we need to figure out the lengths of these indices so that we can
        # determine which bytes represent which instructions.
        start_offset = len(self.assemble(baseoffset, instructions[:start if start < stop else stop]))
        stop_offset = start_offset + len(self.assemble(start_offset + baseoffset, instructions[start : stop : direction] if start < stop else instructions[stop : start : direction]))

        # If there's no stride, then we can simply assemble it and add the
        # offset that they wanted. This should give them what they asked for
        # and allow us to break out of the more complex implementation of
        # having to figure out the sizes of the instruction in each stride.
        if abs(stride) == 1:
            return self.assemble(baseoffset + start_offset, selected)

        # Now we'll need to figure out the sizes in between each stride. To get
        # this, we'll need to iterate through our list of items as indices and
        # and then just exclude what was grabbed. We'll return a list of all
        # the indices that are included so that we can figure out how to
        # assemble and pad it.
        groups, consumable, sentinels = [], iter(range(start, stop, direction)), range(start, stop, stride)
        for index in sentinels:
            iterable = itertools.takewhile(lambda item, sentinel=index: item != sentinel, consumable)
            groups.append([item for item in iterable])

        # Figure out whether we're traversing instructions backwards or forwards
        items = [item for item in (instructions if stride > 0 else reversed(instructions))]

        # Now we have a list of indices that we'll need to figure out the sizes
        # for. To simplify things, we'll simply map our groups into lengths since
        # that'll be the number of instructions we'll need to feed to the
        # block_t.assemble method in order to determine their sizes.
        position, offset = 0, start_offset
        lengths, counts = [], map(len, groups)
        for index, count in enumerate(counts):
            strip = 0

            # Figure out the size of the instructions that we're skipping so we
            # can add it to our result list of sizes to skip.
            item = self.assemble(baseoffset + offset + strip, available[position : position + count])
            strip += len(item)

            # Figure out the size of the instruction that we're including.
            item = self.assemble(baseoffset + offset + strip, selected[index : 1 + index])
            strip += len(item)

            # Store the length of our strip, and continue to the next iteration.
            lengths.append(strip - len(item))
            position, offset = (position + count + 1, offset + strip)

        # We can finally figure out the boundaries of all the instructions
        # in our items now. First step is to adjust our offset to move past
        # our skipped instructions, and then we can grab our real instruction.
        offset, result, data = 0, [], self.assemble(baseoffset + start_offset, available)
        for index, length in enumerate(lengths):
            offset += length

            # Now we can assemble our instruction and grab it.
            item = self.assemble(baseoffset + start_offset + offset, selected[index : 1 + index])
            result.append(data[offset : offset + len(item)])
            offset += len(item)

        return bytes().join(result)

    def __setitem__(self, index, value):
        baseoffset, data = self.getoffset(), self.serialize()
        instructions = self.disassemble(baseoffset, data)
        if not builtins.isinstance(index, slice):
            start = len(self.assemble(baseoffset, instructions[:index]))
            item = self.assemble(baseoffset, instructions[index : 1 + index])
            if isinstance(value, bytes):
                return super(block_t, self).__setitem__(slice(start, start + len(item), 1), value)
            res = self.assemble(baseoffset + start, value if isinstance(value, (tuple, list)) else [value])
            return super(block_t, self).__setitem__(slice(start, start + len(item), 1), res)

        # This is pretty similar logic to __getitem__, so we start with figuring
        # out the bounds the user is trying to reassign and handle the -1
        # specifically because Python is kind of weird with it.
        start, stop, stride = index.indices(len(instructions))

        if stride > 0:
            direction = +1
            available = instructions[:stop : +1] if start < 0 else instructions[start : stop : direction]
            selected = instructions[:stop : stride] if start < 0 else instructions[start : stop : stride]

        elif stride < 0:
            direction = -1
            available = instructions[start : stop : -1] if stop > 0 else instructions[start :: direction]
            selected = instructions[start : stop : stride] if stop > 0 else instructions[start :: stride]

        else:
            raise ValueError(index)

        # Now we have to figure out the lengths of the indices in order to
        # identify which bytes represent each instruction.
        start_offset = len(self.assemble(baseoffset, instructions[:start if start < stop else stop]))
        stop_offset = start_offset + len(self.assemble(baseoffset + start_offset, instructions[start : stop : direction] if start < stop else instructions[stop : start : direction]))

        # If there's no stride, then this is simple as all we need to do is
        # figure out the bounds, and either replace them with the assembled
        # bytes or the bytes that were given to us.
        if abs(stride) == 1:
            length = len(self.assemble(baseoffset + start_offset, selected))
            data = value if isinstance(value, bytes) else self.assemble(baseoffset + start_offset, value)

            if start < stop:
                position = slice(None if start < 0 else start, stop, direction)
            else:
                position = slice(start, None if stop < 0 else stop, direction)
            return super(block_t, self).__setitem__(position, data)

        # Now comes the tedious part. We need to figure out the sizes in between
        # each stride. To accomplish this, we need to get the index of each
        # instruction in the stride because we're going to zip our assembled
        # instructions using them.
        groups, consumable, sentinels = [], iter(range(start, stop, direction)), range(start, stop, stride)
        for index in sentinels:
            iterable = itertools.takewhile(lambda item, sentinel=index: item != sentinel, consumable)
            groups.append([item for item in iterable])

        # Grab the instructions we're going to replace and sort them depending
        # on whether we're traversing frontwards or backwards.
        items = [item for item in (instructions if stride > 0 else reversed(instructions))]

        # Okay, so we should have a list of instruction indices that we're going
        # to skip over. To accomplish this, we'll sum up their sizes so that we
        # can later extract the bytes and assign the slice in one go.
        position, offset, lengths = 0, start_offset, []
        for index, group in enumerate(groups):
            strip = 0

            # Figure out the size of the instructions we need to leave untouched.
            item = self.assemble(baseoffset + offset + strip, available[position : position + len(group)])
            strip += len(item)

            # Figure out the size of the instruction that we're replacing.
            item = self.assemble(baseoffset + offset + strip, selected[index : 1 + index])
            strip += len(item)

            # Store the length of our untouched, and continue to the next iteration.
            lengths.append(strip - len(item))
            position, offset = (position + len(group) + 1, offset + strip)

        # Check to see that we were given the correct data (instructions or bytes)
        if isinstance(value, bytes):
            raise TypeError(value)
        if len(value) != len(selected):
            raise ValueError(value)
        values = [item for item in value]

        # From these lengths, we should be able to figure out our boundaries for
        # any untouched data. So assemble everything that's available in order
        # to figure out the run of data that we're going to replace.
        offset, result, data = 0, [], self.assemble(baseoffset + start_offset, available)
        for index, length in enumerate(lengths):

            # First add the untampered data to our results
            item = data[offset : offset + length]
            result.append(item)
            offset += length

            # Now we need to figure out the length of the instruction here so
            # that we can rewrite it with our new assembled instruction or data.
            item = self.assemble(baseoffset + start_offset + offset, selected[index : 1 + index])
            value = values[index] if isinstance(values[index], bytes) else self.assemble(baseoffset + start_offset + offset, [values[index]])
            result.append(value)
            offset += len(item)

        # Append any data that we ended up missing. We can figure this out by
        # just taking any data after our current offset.
        result.append(data[start_offset + offset:])

        # Now we have our data that we'll just reassign back into the block.
        data = bytes().join(result)
        position = slice(start_offset, start_offset + len(data), direction) if stride > 0 else slice(start_offset, start_offset - len(data), direction)
        return super(block_t, self).__setitem__(position, data)

    def repr(self, **options):
        if not self.initializedQ():
            return u"???"
        if self.blocksize() > 0:
            return self.details(**options) + '\n'
        return self.summary(**options)

    def summary(self):
        listable = self.disassemble(self.getoffset(), self.serialize())
        bytes = map("\\x{:02x}".format, listable)
        return "\"{:s}\"".format(str().join(bytes))

class __ctools__(object):
    @staticmethod
    def is_structure(cinstance):
        return not hasattr(cinstance, '_type_') and hasattr(cinstance, '_fields_')

    @staticmethod
    def iterate_structure(cstruct):
        for name, type in cstruct._fields_:
            value = getattr(cstruct, name)
            yield type, name, value
        return

    @staticmethod
    def is_array(cinstance):
        return hasattr(cinstance, '_type_') and hasattr(cinstance, '_length_')

    @staticmethod
    def iterate_array(carray):
        type, length = carray._type_, carray._length_
        for index, value in enumerate(carray):
            yield type, index, value
        return

    @staticmethod
    def is_pointer(cinstance):
        return hasattr(cinstance, '_type_') and hasattr(cinstance, 'contents')

    @staticmethod
    def is_atomic_t(cinstance):
        return hasattr(cinstance, '_type_') and isinstance(cinstance._type_, six.string_types)

    @staticmethod
    def resolve(cinstance, path):
        '''Traverse the specified `cinstance` using the list specified in `path`.'''
        path = path[:]

        # If we're processing an empty path, then we simply can return
        # our instance since we don't need to traverse anything.
        if not len(path):
            return cinstance

        # If it's a array, then figuring its type is easy. Our next
        # path should be an index, so use it to fetch an array element.
        elif __ctools__.is_array(cinstance):
            type, current = cinstance._type_, cinstance[path.pop(0)]

        # If it's a structure, then we'll need to parse its fields and
        # get the type and member from whatever field matches it.
        elif __ctools__.is_structure(cinstance):
            item = path.pop(0)
            type, current = next((type, getattr(cinstance, item)) for field, type in cinstance._fields_ if field == item)

        # If we're a pointer, then our path needs to be of the None
        # type in order for us to traverse it.
        elif __ctools__.is_pointer(cinstance):
            if not isinstance(path.pop(0), None.__class__):
                raise TypeError([None] + path, cinstance.__class__, cinstance)

            # Now we can dereference the pointer as requested
            type, current = cinstance._type_, cinstance.contents

        else:
            raise TypeError(path, cinstance.__class__, cinstance)
        return __ctools__.resolve(current, path)

    @staticmethod
    def collect_array(path, cinstance):
        type = cinstance._type_

        # If this is an array of pointers, then yield everything
        if __ctools__.is_pointer(type):
            for type, index, value in __ctools__.iterate_array(cinstance):
                for item in __ctools__.collect(type, value, path + [index]):
                    yield item
                continue

        # If's a structure, then yield those too with our new path
        elif __ctools__.is_structure(type):
            for type, field, value in __ctools__.iterate_structure(cinstance):
                for item in __ctools__.collect(type, value, path + [field]):
                    yield item
                continue
        return

    @staticmethod
    def collect_structure(path, cinstance):
        for type, field, value in __ctools__.iterate_structure(cinstance):
            for item in __ctools__.collect(type, value, path + [field]):
                yield item
            continue
        return

    @staticmethod
    def collect(type, value, path=[]):
        '''Start at `type` and `value` collecting all pointers.'''

        # We're straight-up looking for pointers, so yield those
        if __ctools__.is_pointer(value):
            yield path

            for item in __ctools__.collect(value._type_, value.contents, path + [None]):
                yield item

        # If it's atomic, then we can just drop it
        elif __ctools__.is_atomic_t(type):
            return

        # If it's a structure, then we need to traverse it
        elif __ctools__.is_structure(value):
            for item in __ctools__.collect_structure(path, value):
                yield item

        # If it's an array, then we also need to traverse it
        elif __ctools__.is_array(value):
            for item in __ctools__.collect_array(path, value):
                yield item

        # We really have no idea what type this is and we need to
        # bitch and complain about it.
        else:
            raise TypeError
        return

class pointer_t(ptype.pointer_t):
    #_parameters_ = []
    #_result_ = ptype.type

    # XXX: this method is likely to change in order to support resuming
    def dispatch(self, **parameters):
        data = self.__frame_arguments(**parameters)
        frame_t = (ctypes.c_ubyte * frame.size())
        frame = frame_t(*bytearray(data))

        frameptr_t = ctypes.POINTER(frame_t)

        instance.set(**parameters)
        raise NotImplementedError

    # XXX: this method might not get used
    @classmethod
    def __pointer_of_instance(cls, instance):
        view = memoryview(instance.serialize())

        buffer_t = len(view) * ctypes.c_ubyte
        buffer = buffer_t(*view.tolist())

        return ctypes.pointer(buffer)

    # XXX: this method might not get used
    @classmethod
    def __instance_of_pointer(cls, type, pointer, **kwds):
        view = memoryview(pointer.contents)

        kwds.setdefault('source', ptypes.provider.bytes(view.tobytes()))
        return self.new(type, **kwds)

    # XXX: this method will likely change as there's currently no need for it
    def __frame__(self, *args, **parameters):
        '''Create a new instance of `pointer_t._parameters_` with the specified values.'''
        instance = self.new(self._parameters_)
        return instance.set(*args, **parameters)

    # XXX: this method will change in order to support non-contiguous pointers
    def __frame_result__(self, cinstance, type):
        view_t = ctypes.sizeof(cinstance) * ctypes.c_ubyte
        viewptr_t = ctypes.POINTER(view_t)

        cptr = ctypes.pointer(cinstance)
        ptr = cptr.cast(viewptr_t)

        view = memoryview(ptr.contents)
        return self.new(type, offset=ctypes.addressof(cinstance), source=ptypes.prov.bytes(view.tobytes()))

    def __cblocks__(self, cinstance):
        """Yield a tuple of every (pointer, data) from the specified ctypes instance.

        This will return all non-contiguous blocks that can be discovered by
        traversing the specified instance. The root object is listed with a pointer
        type of `None`. Unfortunately due to ctypes constructing a pointer's contents
        dynamically whenever it is accessed, there's no way to determine the location
        of a given pointer. This will be fixed in a future refactor of this implementation.
        """

        # First figure out our type and if we're an atomic. If so, then we
        # only need to yield that and then leave.
        if __ctools__.is_atomic_t(type(cinstance)):
            yield [], cinstance
            return

        # If we're an array, then also check that it's an array of atomics,
        # because we don't have to do anything for that situation too.
        elif __ctools__.is_array(cinstance) and __ctools__.is_atomic_t(cinstance._type_):
            yield [], cinstance
            return

        # If it's a structure, then we need to check that all its fields are
        # atomic. If so, then we can terminate ahead of time.
        elif __ctools__.is_structure(cinstance) and all(__ctools__.is_atomic_t(t) for t, _, _ in __ctools__.iterate_structure(cinstance)):
            yield [], cinstance
            return

        # We always need to yield the base element because it's a guaranteed
        # block of memory.
        else:
            yield [], cinstance

        # Now we can simply start at our instance and proceed to
        # iterate through all of the paths to pointers from it.
        for path in __ctools__.collect(type(cinstance), cinstance):
            item = __ctools__.resolve(cinstance, path)

            # If we ended up resolving a pointer, then we need to derference
            # it and yield its dereferenced path too
            if __ctools__.is_pointer(item):
                yield path + [None], item.contents

            # Otherwise it's a regular path that we can just use
            else:
                yield path, item
            continue
        return

    def __blocks__(self, instance):
        """Yield a tuple of every (pointer, target) from the specified instance.

        This will return all potential non-contiguous blocks that can be
        discovered by traversing the specified instance. Duplicate pointers to
        the same target are not detected.
        """

        # This function will help us traverse an instance and grab all
        # contiguous blocks (by their pointers) that it references.
        def edges(node, pointers={item for item in []}):

            ## If we're processing a pointer, we need to dereference it
            if isinstance(node, ptype.pointer_t):

                # So first we need to make sure we haven't processed it
                if operator.contains(pointers, node):
                    return []

                # If we haven't processed it.. then add it to our list,
                # and yield it back to traverse so we can grab its
                # contiguous block too.
                pointers |= {node}
                return [node.d]

            # Anything that's not a container, we can simply skip.
            if not isinstance(node, ptype.container):
                return []

            # Yield any and all children contained by this node.
            return node.value

        # We only care about pointers
        fpointerQ = lambda node: isinstance(node, ptype.pointer_t)

        # Traverse the entire trie starting from the instance and yield
        # only pointers that we've found along with their data.
        result = {item for item in []}
        for node in instance.traverse(edges, fpointerQ, pointers=result):
            yield node, node.d
        return

if __name__ == '__main__':
    class Result(Exception): pass
    class Success(Result): pass
    class Failure(Result): pass

    TestCaseList = []
    def TestCase(fn):
        def harness(**kwds):
            name = fn.__name__
            try:
                res = fn(**kwds)
                raise Failure
            except Success as E:
                print('%s: %r'% (name, E))
                return True
            except Failure as E:
                print('%s: %r'% (name, E))
            except Exception as E:
                print('%s: %r : %r'% (name, Failure(), E))
            return False
        TestCaseList.append(harness)
        return fn

if __name__ == '__main__':
    import six, ptypes
    from ptypes import *

    ptypes.setsource(ptypes.prov.random())

    @TestCase
    def test_construct_block():
        class t(pcode.block_t):
            length = 16

        res = t()
        if res.blocksize() == res.a.size() == t.length:
            raise Success

    @TestCase
    def test_block_get():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data)).l
        if res.get() == result[:res.size()]:
            raise Success

    @TestCase
    def test_block_set_bytes():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t().set(data[0x20:])
        if res.serialize() == data[0x20:]:
            raise Success

    @TestCase
    def test_block_set_instructions():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t().set(result[0x10 : 0x30])
        if res.serialize() == data[0x10 : 0x30]:
            raise Success

    @TestCase
    def test_block_getitem_singlestride():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        if res[:0x10] == data[0x10 : 0x20]:
            raise Success

    @TestCase
    def test_block_getitem_reversedsinglestride():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x0).l
        if res[0x10::-1] == bytes().join(map(six.int2byte, range(0x10)[::-1])):
            raise Success

    @TestCase
    def test_block_getitem_empty():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        if res[0 : 0] == b'':
            raise Success

    @TestCase
    def test_block_getitem_reversedempty():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x0).l
        if res[0x10 : 0x10 : -1] == b'':
            raise Success

    @TestCase
    def test_block_getitem_multiplestride():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        if res[0 : 0x10 : 4] == data[0x10 : 0x20 : 4]:
            raise Success

    @TestCase
    def test_block_getitem_reversedmultiplestride():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        if data[res.getoffset() : res.getoffset() + res.size()] != res.serialize():
            raise Failure
        if data[res.getoffset() + res.size() - 1 : res.getoffset() - 1 : -1] != bytes().join(map(six.int2byte, reversed(bytearray(res.serialize())))):
            raise Failure

        comparison = data[res.getoffset() + res.size() - 1 : res.getoffset() - 1 : -4]
        if res[:: -4] == comparison:
            raise Success

    @TestCase
    def test_block_setitem_singlestride_bytes():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        res[:] = b'ABCDABCDABCDABCD'
        if res.serialize() == b'ABCDABCDABCDABCD':
            raise Success

    @TestCase
    def test_block_setitem_singlestride_instructions():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 8

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        res[:] = range(0x41, 0x41 + 8)
        if res.serialize() == b'ABCDEFGH':
            raise Success

    @TestCase
    def test_block_setitem_reversedsinglestride_bytes():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 8

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        res[::-1] = b'ABCDABCD'
        if res.serialize() == b'DCBADCBA':
            raise Success

    @TestCase
    def test_block_setitem_reversedsinglestride_instructions():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 8

        res = t(source=ptypes.prov.bytes(data), offset=0x10).l
        res[::-1] = range(0x41, 0x41 + 8)
        if res[:] == b'HGFEDCBA':
            raise Success

    @TestCase
    def test_block_setitem_multiplestride_arrayofbytes():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 16

        res = t(source=ptypes.prov.bytes(data), offset=0x10).a
        res[::2] = [b'\1'] * 8
        if res.serialize() == b'\1\0'*8:
            raise Success

    @TestCase
    def test_block_setitem_multiplestride_arrayofinstructions():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 15

        res = t(source=ptypes.prov.bytes(data), offset=0x10).a
        res[::3] = [1] * 5
        if res.serialize() == b'\1\0\0'*5:
            raise Success

    @TestCase
    def test_block_setitem_reversedmultiplestride_arrayofbytes():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 15

        res = t(source=ptypes.prov.bytes(data), offset=0x10).a
        res[::-3] = [six.int2byte(item) for item in range(5)]
        compare = bytes().join(map(six.int2byte, functools.reduce(operator.add, (zip([0]*5, [0]*5, reversed(range(5)))))))
        if res.serialize() == compare:
            raise Success

    @TestCase
    def test_block_setitem_reversedmultiplestride_arrayofinstructions():
        result = [item for item in range(0x40)]
        data = bytes().join(map(six.int2byte, result))

        class t(pcode.block_t):
            length = 15

        res = t(source=ptypes.prov.bytes(data), offset=0x10).a
        res[::-3] = range(5)
        compare = bytes().join(map(six.int2byte, functools.reduce(operator.add, (zip([0]*5, [0]*5, reversed(range(5)))))))
        if res.serialize() == compare:
            raise Success

    @TestCase
    def test_pointer_parameters_contiguous():
        class params(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (pint.uint32_t, 'b'),
                (pint.uint32_t, 'c'),
            ]

        P = params().set(a=0x21, b=0x22, c=0x33)

        res = pcode.pointer_t()
        items = [item for item in res.__blocks__(P)]
        if len(items):
            raise Failure
        raise Success

    @TestCase
    def test_pointer_parameters_noncontiguous_1():
        class params(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (dyn.pointer(pint.uint32_t), 'b'),
                (pint.uint32_t, 'c'),
            ]

        P = params().set(a=0x21, b=0x22, c=0x33)

        res = pcode.pointer_t()
        items = [item for item in res.__blocks__(P)]
        if len(items) != 1:
            raise Failure

        ptr, data = items[0]
        if P['b'] is ptr and ptr.int() == data.getoffset() and not data.initializedQ():
            raise Success

    @TestCase
    def test_pointer_parameters_noncontiguous_2():
        ptr = dyn.clone(ptype.pointer_t, _value_=pint.uint32_t, _object_=ptype.undefined)

        class block_2(pstruct.type):
            _fields_ = [
                (dyn.block(8), 'padding'),
                (pint.uint64_t, 'goal'),
            ]

        class block_1(pstruct.type):
            _fields_ = [
                (dyn.block(4), 'padding'),
                (dyn.clone(ptr, _object_=block_2), 'ptr(block2)'),
            ]

        class params(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (dyn.clone(ptr, _object_=block_1), 'ptr(block1)'),
                (pint.uint32_t, 'b'),
            ]

        P = params().set(a=0x21, b=0x22)
        refblock1 = P['ptr(block1)'].reference(block_1().a)
        refblock2 = refblock1['ptr(block2)'].reference(block_2().a.set(goal=57005))

        res = pcode.pointer_t()
        items = [item for item in res.__blocks__(P)]

        if len(items) != 2:
            raise Failure

        # Calculate where all our data is at so that we can assign pointers to
        # point to the next block.
        blocks, offset = [P], P.size()
        for ptr, block in items:
            ptr.set(offset)
            blocks.append(block)
            offset += block.size()

        # Now we can combine them together into a single source
        data = bytes().join(item.serialize() for item in blocks)

        # Okay, we should now have a source that we can load from and check
        # everything with.
        a = params(source=ptypes.prov.bytes(data)).l
        if (a['a'].int(), a['b'].int()) != (0x21, 0x22):
            raise Failure

        b = a['ptr(block1)'].d.l
        if b['padding'].serialize() != b'\0\0\0\0':
            raise Failure

        c = b['ptr(block2)'].d.l
        if c['goal'].int() == 57005:
            raise Success

    @TestCase
    def test_pointer_parameters_noncontiguous_3():
        ptr = dyn.clone(ptype.pointer_t, _value_=pint.uint32_t, _object_=pint.uint64_t)

        class argh(parray.type):
            length, _object_ = 4, ptr

        class params(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'a'),
                (dyn.clone(ptr, _object_=argh), 'ptr(array)'),
            ]

        P = params().set(a=0x27)
        refarray = P['ptr(array)'].reference(argh().a)
        for i, item in enumerate(refarray):
            item.d.a.set(0x11 + i * 0x11)

        res = pcode.pointer_t()
        items = [item for item in res.__blocks__(P)]

        if len(items) != 1 + 4:
            raise Failure

        # Figure out our data layout..the same as before.
        blocks, offset = [P], P.size()
        for ptr, block in items:
            ptr.set(offset)
            blocks.append(block)
            offset += block.size()

        # Glue them together so we can make a source to load from
        data = bytes().join(item.serialize() for item in blocks)

        # ...and here we go!
        a = params(source=ptypes.prov.bytes(data)).l

        if a['a'].int() != 0x27:
            raise Failure

        b = a['ptr(array)'].d.l
        if len(b) != 4:
            raise Success

        res = []
        for i, p in enumerate(b):
            val = p.d.li
            res.append(val)

        if all(item.int() == 0x11 + i * 0x11 for i, item in enumerate(res)):
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_0_uint16():
        t = ctypes.c_uint16
        val = t(57005)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1:
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_0_array():
        t = ctypes.c_uint16 * 4
        val = t(*[57005] * 4)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1:
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_0_structure():
        class t(ctypes.Structure):
            _fields_ = [
                ('LowPart', ctypes.c_uint32),
                ('HighPart', ctypes.c_uint32),
            ]

        val = t(0xa5a5a5a5, 0x5a5a5a5a)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1:
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_1():
        t = ctypes.c_uint16
        val = t(57005)
        p = ctypes.pointer(val)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(p) ]
        if len(items) != 2:
            raise Failure

        # Get our first block which should be a pointer
        start, item = items
        _, block1ptr = start

        # Now we can check the pointer against the path, and that its contents
        # correspond to our expected value
        path, contents = item
        ptr = __ctools__.resolve(p, path[:-1])
        if block1ptr == ptr and memoryview(contents).tobytes() == b'\xad\xde':
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_2():
        t = ctypes.c_uint16 * 4
        val = t(*[57005] * 4)
        p = ctypes.pointer(val)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(p) ]
        if len(items) != 2:
            raise Failure

        # Get our first block which should be a pointer
        start, item = items
        _, block1ptr = start

        # Check that our block1ptr corresponds to the path that we've found
        path, contents = item
        ptr = __ctools__.resolve(p, path[:-1])
        if block1ptr == ptr and memoryview(contents).tobytes() == b'\xad\xde' * 4:
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_3():
        class t(ctypes.Structure):
            _fields_ = [
                ('LowPart', ctypes.c_uint32),
                ('HighPart', ctypes.c_uint32),
            ]

        val = t(0xa5a5a5a5, 0x5a5a5a5a)
        p = ctypes.pointer(val)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(p) ]
        if len(items) != 2:
            raise Failure

        # Get our first block which should be a pointer
        start, item = items
        _, block1ptr = start

        # Check that our block1ptr corresponds to the path that we've found
        path, contents = item
        ptr = __ctools__.resolve(p, path[:-1])
        if block1ptr == ptr and memoryview(contents).tobytes() == 4 * b'\xa5' + b'ZZZZ':
            raise Success

    @TestCase
    def test_pointer_ctypes_noncontiguous_0():
        class t(ctypes.Structure):
            _fields_ = [
                ('fuck', ctypes.POINTER(ctypes.c_uint16)),
            ]

        root = t(ctypes.pointer(ctypes.c_uint16(57005)))

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(root) ]

        if len(items) != 2:
            raise Failure

        # Now we'll need to re-use our items to recreate a pointer lookup table.
        # None of our types are hashable...because ctypes, so we resolve each
        # pointer to an integer that we use as our key. We'll also create a
        # table for each block keyed by its address since we've already stored
        # a reference to it in our items list.
        ptrlookup = {}
        for index, (path, contents) in enumerate(items):
            if len(path) and path[-1] is None:
                ptr = __ctools__.resolve(root, path[:-1])
                key = memoryview(ptr).tobytes()
                ptrlookup[key] = index
            continue

        # Now we'll copy our types into this buffer, and re-create an array of
        # the contents so that we can update the buffer with our new pointer values.
        result = []
        for index, (path, contents) in enumerate(items):
            t, block = type(contents), contents
            data = memoryview(block).tobytes()
            value = (len(data) * ctypes.c_ubyte)(*data)
            result.append(ctypes.cast(ctypes.pointer(value), ctypes.POINTER(t)).contents)

        # Now we will iterate through our pointers, find their target (index) using the
        # ptrlookup dict, and then update its contents to point at the correct result.
        base = result[0]
        for index, (path, contents) in enumerate(items):
            if len(path):
                ptr = __ctools__.resolve(base, path[:-1])
                key = memoryview(ptr).tobytes()
                ptr.contents = result[ptrlookup[key]]

            # If we received an empty path for the non-first element, then something is busted.
            elif index > 0:
                raise AssertionError("Received an empty path that is not the root object")
            continue

        # Ensure our root elements are different, our pointers are different, and our values are the same
        if memoryview(base).tobytes() == memoryview(root).tobytes():
            raise Failure
        if memoryview(base.fuck).tobytes() == memoryview(root.fuck).tobytes():
            raise Failure
        if base.fuck.contents is not root.fuck.contents and memoryview(base.fuck.contents).tobytes() == memoryview(root.fuck.contents).tobytes():
            raise Success

    @TestCase
    def test_pointer_ctypes_noncontiguous_1():
        class t(ctypes.Structure):
            _fields_ = [
                ('LowPart', ctypes.c_uint16),
                ('HighPart', ctypes.c_uint16),
            ]
        val_t = ctypes.POINTER(t)

        target = t(57005, 65261)
        val = val_t(target)

        res = pcode.pointer_t()
        items = [item for item in res.__cblocks__(val)]

        if len(items) != 2:
            raise Failure

        # Everything here is copied from test_pointer_ctypes_noncontiguous_0
        root, ptrlookup = val, {}
        for index, (path, contents) in enumerate(items):
            if len(path) and path[-1] is None:
                ptr = __ctools__.resolve(root, path[:-1])
                key = memoryview(ptr).tobytes()
                ptrlookup[key] = index
            continue

        result = []
        for index, (path, contents) in enumerate(items):
            t, block = type(contents), contents
            data = memoryview(block).tobytes()
            value = (len(data) * ctypes.c_ubyte)(*data)
            result.append(ctypes.cast(ctypes.pointer(value), ctypes.POINTER(t)).contents)

        base = result[0]
        for index, (path, contents) in enumerate(items):
            if len(path):
                ptr = __ctools__.resolve(base, path[:-1])
                key = memoryview(ptr).tobytes()
                ptr.contents = result[ptrlookup[key]]

            # If we received an empty path for the non-first element, then something is busted.
            elif index > 0:
                raise AssertionError("Received an empty path that is not the root object")
            continue

        # Ensure everything is different but all the values match
        if memoryview(base).tobytes() == memoryview(root).tobytes():
            raise Failure
        if base.contents is not root.contents and memoryview(base.contents).tobytes() == memoryview(root.contents).tobytes():
            raise Success

    @TestCase
    def test_pointer_ctypes_noncontiguous_2():
        class LUID(ctypes.Structure):
            _fields_ = [
                ('LowPart', ctypes.c_uint32),
                ('HighPart', ctypes.c_long),
                ('Ptr', ctypes.POINTER(ctypes.c_uint32)),
            ]

        val = LUID(1024, 2048, ctypes.pointer(ctypes.c_uint32(57005)))

        res = pcode.pointer_t()
        items = [item for item in res.__cblocks__(val)]

        if len(items) != 2:
            raise Failure

        # Everything here is copied from test_pointer_ctypes_noncontiguous_0
        root, ptrlookup = val, {}
        for index, (path, contents) in enumerate(items):
            if len(path) and path[-1] is None:
                ptr = __ctools__.resolve(root, path[:-1])
                key = memoryview(ptr).tobytes()
                ptrlookup[key] = index
            continue

        result = []
        for index, (path, contents) in enumerate(items):
            t, block = type(contents), contents
            data = memoryview(block).tobytes()
            value = (len(data) * ctypes.c_ubyte)(*data)
            result.append(ctypes.cast(ctypes.pointer(value), ctypes.POINTER(t)).contents)

        base = result[0]
        for index, (path, contents) in enumerate(items):
            if len(path):
                ptr = __ctools__.resolve(base, path[:-1])
                key = memoryview(ptr).tobytes()
                ptr.contents = result[ptrlookup[key]]

            # If we received an empty path for the non-first element, then something is busted.
            elif index > 0:
                raise AssertionError("Received an empty path that is not the root object")
            continue

        # Ensure that we made an exact copy of the entire type.
        if any(getattr(root, fld) != getattr(base, fld) for fld in ['LowPart', 'HighPart']):
            raise Failure
        if memoryview(base).tobytes() == memoryview(root).tobytes():
            raise Failure
        if memoryview(base.Ptr).tobytes() == memoryview(root.Ptr).tobytes():
            raise Failure
        if memoryview(base.Ptr.contents).tobytes() == memoryview(root.Ptr.contents).tobytes():
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
