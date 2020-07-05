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
        traversing the specified instance. The specified instance will also be
        traversed. Duplicate pointers to the same target are not detected and
        will need to be handled by the caller.
        """
        yield None, cinstance

        def iterate_structure(cstruct):
            for name, type in cstruct._fields_:
                value = getattr(cstruct, name)
                yield type, name, value
            return

        def iterate_array(carray):
            type, length = carray._type_, carray._length_
            for index, value in enumerate(carray):
                yield type, index, value
            return

        def recurse(current):

            # First thing is to check if it has a _type_ attribute, if it doesn't
            # then it simply has to be a structure with a _fields_ attribute.
            if not hasattr(current, '_type_'):
                for type, name, value in iterate_structure(current):
                    if not isinstance(type, six.string_types):
                        continue

                    # Found a non-atomic type that we need to recurse through in
                    # order to find all the pointers.
                    for item in recurse(value):
                        yield item
                    continue
                return

            # Otherwise, this is an array or atomic type and so we need to
            # determine which one it is.
            ctype = current._type_

            # If we're an atomic type, then we aren't important and can leave
            if isinstance(ctype, six.string_types):
                return

            # If we're at a pointer, then yield it and its contents.
            if hasattr(current, 'contents'):
                yield current
                return

            # If we're an array type, then we need to check the type to see if
            # we're an array of atomic types in order to determine whether we
            # need to traverse it or not.
            if hasattr(current, '_length_'):
                if not isinstance(ctype._type_, six.string_types):
                    return

                for type, name, value in iterate_array(current):
                    if not isinstance(type, six.string_types):
                        continue

                    # We just double-checked the type, so recurse to find all
                    # pointers so we can let the caller know.
                    for item in recurse(value):
                        yield item
                    continue
                return

            # We have no idea what this is...
            raise TypeError(current)

        # All the hard work was done, so just recurse and return every pointer
        # along with its target contents.
        for item in recurse(cinstance):
            yield item, item.contents
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
    def test_pointer_ctypes_contiguous_1():
        t = ctypes.c_uint16
        val = t(57005)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1 and memoryview(items[0][1]).tobytes() == b'\xad\xde':
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_2():
        t = ctypes.c_uint16 * 4
        val = t(*[57005] * 4)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1 and memoryview(items[0][1]).tobytes() == b'\xad\xde' * 4:
            raise Success

    @TestCase
    def test_pointer_ctypes_contiguous_3():
        class t(ctypes.Structure):
            _fields_ = [
                ('LowPart', ctypes.c_uint32),
                ('HighPart', ctypes.c_uint32),
            ]

        val = t(0xa5a5a5a5, 0x5a5a5a5a)

        res = pcode.pointer_t()
        items = [ item for item in res.__cblocks__(val) ]
        if len(items) == 1 and memoryview(items[0][1]).tobytes() == 4 * b'\xa5' + b'ZZZZ':
            raise Success

if __name__ == '__main__':
    import logging
    ptypes.config.defaults.log.setLevel(logging.DEBUG)

    results = []
    for t in TestCaseList:
        results.append( t() )
