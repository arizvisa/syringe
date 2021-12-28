# XXX: these might be useful...
# https://kirin-say.top/2020/01/01/Heap-in-Windows/
# https://github.com/0x00ach/stuff/blob/master/heap_walk_test.c
# https://n0nop.com/2021/04/15/Learning-Windows-pwn-Nt-Heap/#%E5%8F%82%E8%80%83%E9%93%BE%E6%8E%A5
import functools, itertools, types, builtins, operator
import sys, math, logging

import ptypes
from ptypes import bitmap

from . import sdkddkver, rtltypes, error
from .datatypes import *

class SIZE_T64(ULONGLONG): pass

class HEAP_LOCK(pint.uint32_t): pass
class HEAP_SIGNATURE(pint.enum, ULONG):
    _fields_ = [
        ('SegmentHeap', 0xddeeddee),
        ('Heap', 0xeeffeeff),
    ]

if 'HeapMeta':
    class HEAP_BUCKET_COUNTERS(pstruct.type):
        _fields_ = [
            (ULONG, 'TotalBlocks'),
            (ULONG, 'SubSegmentCounts'),
        ]
        def summary(self):
            return "TotalBlocks:{:#x} SubSegmentCounts:{:#x}".format(self['TotalBlocks'].int(), self['SubSegmentCounts'].int())

    class HEAP_COUNTERS(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(HEAP_COUNTERS, self).__init__(**attrs)
            f = self._fields_ = []
            integral = pint.uint64_t if getattr(self, 'WIN64', False) else SIZE_T

            f.extend([
                (integral, 'TotalMemoryReserved'),
                (integral, 'TotalMemoryCommitted'),
                (integral, 'TotalMemoryLargeUCR'),
                (integral, 'TotalSizeInVirtualBlocks'),
                (ULONG, 'TotalSegments'),
                (ULONG, 'TotalUCRs'),
                (ULONG, 'CommittOps'),
                (ULONG, 'DeCommitOps'),
                (ULONG, 'LockAcquires'),
                (ULONG, 'LockCollisions'),
                (ULONG, 'CommitRate'),
                (ULONG, 'DecommittRate'),
                (ULONG, 'CommitFailures'),
                (ULONG, 'InBlockCommitFailures'),
            ])

            # < Windows 8.0
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (ULONG, 'CompactHeapCalls'),
                    (ULONG, 'CompactedUCRs'),
                    (ULONG, 'AllocAndFreeOps'),
                ])

            # >= Windows 8.0
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (ULONG, 'PollIntervalCounter'),
                    (ULONG, 'DecommitsSinceLastCheck'),
                    (ULONG, 'HeapPollInterval'),
                    (ULONG, 'AllocAndFreeOps'),
                    (ULONG, 'AllocationIndicesActive'),
                ])

            f.extend([
                (ULONG, 'InBlockDeccommits'),
                (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'InBlockDeccomitSize'),
                (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'HighWatermarkSize'),
                (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'LastPolledSize'),
            ])

    class HEAP_TUNING_PARAMETERS(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(HEAP_TUNING_PARAMETERS, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (ULONG, 'CommittThresholdShift'),
                (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(CommittThresholdShift)'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MaxPreCommittThreshold')
            ])

        def summary(self):
            return ' '.join("{:s}={:s}".format(k, v.summary()) for k, v in self.items())

    class HEAP_PSEUDO_TAG_ENTRY(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(HEAP_PSEUDO_TAG_ENTRY, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (ULONG, 'Allocs'),
                (ULONG, 'Frees'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'Size'),
            ])

    class HEAP_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (ULONG, 'Size'),
            (USHORT, 'TagIndex'),
            (USHORT, 'CreatorBackTraceIndex'),
            (dyn.clone(pstr.wstring, length=24), 'TagName')
        ]

    class HEAP_DEBUGGING_INFORMATION(pstruct.type, versioned):
        # http://blog.airesoft.co.uk/2010/01/a-whole-heap-of-trouble-part-1/
        _fields_ = [
            (PVOID, 'InterceptorFunction'),
            (WORD, 'InterceptorValue'),
            (ULONG, 'ExtendedOptions'),
            (ULONG, 'StackTraceDepth'),
            (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MinTotalBlockSize'),
            (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MaxTotalBlockSize'),
            (PVOID, 'HeapLeakEnumerationRoutine'),
        ]

    class DPH_BLOCK_INFORMATION(pstruct.type, versioned):
        '''Structure of a Page Heap Block when Full Page Heap is Enabled'''
        # http://msdn.microsoft.com/en-us/library/ms220938(VS.80).aspx
        # http://blogs.cisco.com/security/exploring_heap-based_buffer_overflows_with_the_application_verifier
        class StackTraceInfo(pstruct.type):
            # http://blog.airesoft.co.uk/2010/01/a-whole-heap-of-trouble-part-1/
            _fields_ = [
                (ULONG, 'unk'),
                (ULONG_PTR, 'unk2'),
                (ULONG, 'numFrames'),
                (PVOID, 'ips'),
            ]
        def __init__(self, **attrs):
            super(DPH_BLOCK_INFORMATION, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (ULONG, 'StartStamp'),  # 0xabcdaaaa
                (PVOID, 'Heap'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'RequestedSize'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'ActualSize'),
                (LIST_ENTRY, 'FreeQueue'),
                (PVOID, 'StackTrace'),
                (dyn.block(4) if getattr(self, 'WIN64', False) else dyn.block(0), 'Padding'),
                (ULONG, 'EndStamp'),    # 0xdcbaaaaa
            ])

    class DPH_HEAP_BLOCK(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(DPH_HEAP_BLOCK, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (LIST_ENTRY, 'AvailableEntry'),
                (P(UCHAR), 'pUserAllocation'),
                (P(UCHAR), 'pVirtualBlock'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'nVirtualBlockSize'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'nVirtualAccessSize'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'nUserRequestedSize'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'nUserActualSize'),
                (PVOID, 'UserValue'),
                (ULONG, 'UserFlags'),
                (P(rtltypes.RTL_TRACE_BLOCK), 'StackTrace'),
                (LIST_ENTRY, 'AdjacencyEntry'),
                (P(UCHAR), 'pVirtualRegion'),
            ])

    class DPH_HEAP_ROOT(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(DPH_HEAP_ROOT, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (ULONG, 'HeapFlags'),
                (P(HEAP_LOCK), 'HeapCritSect'),
                (ULONG, 'nRemoteLockAcquired'),
                (P(DPH_HEAP_BLOCK), 'pVirtualStorageListHead'),
                (P(DPH_HEAP_BLOCK), 'pVirtualStorageListTail'),
                (ULONG, 'nVirtualStorageRanges'),
                (SIZE_T, 'nVirtualStorageBytes'),
                (rtltypes.RTL_AVL_TABLE, 'BusyNodesTable'),
                (P(DPH_HEAP_BLOCK), 'NodeToAllocate'),
                (ULONG, 'nBusyAllocations'),
                (SIZE_T, 'nBusyAllocationBytesCommitted'),
                (P(DPH_HEAP_BLOCK), 'pFreeAllocationListHead'),
                (P(DPH_HEAP_BLOCK), 'pFreeAllocationListTail'),
                (ULONG, 'nFreeAllocations'),
                (SIZE_T, 'nFreeAllocationBytesCommitted'),
                (LIST_ENTRY, 'AvailableAllocationHead'),
                (ULONG, 'nAvailableAllocations'),
                (SIZE_T, 'nAvailableAllocationBytesCommitted'),
                (P(DPH_HEAP_BLOCK), 'pUnusedNodeListHead'),
                (P(DPH_HEAP_BLOCK), 'pUnusedNodeListTail'),
                (ULONG, 'nUnusedNodes'),
                (SIZE_T, 'nBusyAllocationBytesAccessible'),
                (P(DPH_HEAP_BLOCK), 'pNodePoolListHead'),
                (P(DPH_HEAP_BLOCK), 'pNodePoolListTail'),
                (ULONG, 'nNodePools'),
                (SIZE_T, 'nNodePoolBytes'),
                (LIST_ENTRY, 'NextHeap'),
                (ULONG, 'ExtraFlags'),
                (ULONG, 'Seed'),
                (PVOID, 'NormalHeap'),
                (P(rtltypes.RTL_TRACE_BLOCK), 'CreateStackTrace'),
                (PVOID, 'FirstThread'),
            ])

if 'EncodingKeys':
    def __RtlpHeapKey__(self):
        '''Try and resolve ntdll!RtlpHeapKey using the debugger or an attribute attached to the HEAP.'''
        if not isinstance(self.source, ptypes.provider.debuggerbase):

            # First check for any attributes on our HEAP
            p = self.getparent(HEAP)
            if not hasattr(p, 'RtlpHeapKey'):
                logging.warning("Failure while attempting to determine address of {:s}".format('ntdll!RtlpHeapKey'))
                return 0

            # Found one that we can use, so use it.
            logging.info("Using address of {:s} ({:#x}) from attribute {:s}.{:s}".format('ntdll!RtlpHeapKey', p.RtlpHeapKey, p.instance(), 'RtlpHeapKey'))
            RtlpHeapKey = p.RtlpHeapKey

        # We can simply use the debugger to evaluate the expression for our key
        else:
            RtlpHeapKey = self.source.expr('ntdll!RtlpHeapKey')

        t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
        res = self.new(t, offset=RtlpHeapKey)
        return res.l.int()

    def __RtlpLFHKey__(self):
        '''Try and resolve ntdll!RtlpLFHKey using the debugger or an attribute attached to the HEAP.'''
        if not isinstance(self.source, ptypes.provider.debuggerbase):

            # First check for any attributes on our HEAP
            p = self.getparent(HEAP)
            if not hasattr(p, 'RtlpLFHKey'):
                logging.warning("Failure while attempting to determine address of {:s}".format('ntdll!RtlpLFHKey'))
                return 0

            # Found one that we can use, so use it.
            logging.info("Using address of {:s} ({:#x}) from attribute {:s}.{:s}".format('ntdll!RtlpLFHKey', p.RtlpLFHKey, p.instance(), 'RtlpLFHKey'))
            RtlpLFHKey = p.RtlpLFHKeya

        # We can simply use the debugger to evaluate the expression for our key
        else:
            RtlpLFHKey = self.source.expr('ntdll!RtlpLFHKey')

        t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
        res = self.new(t, offset=RtlpLFHKey)
        return res.l.int()

if 'HeapEntry':
    class HEAP_BUCKET(pstruct.type):
        @pbinary.littleendian
        class _BucketFlags(pbinary.flags):
            _fields_ = [
                (5, 'Reserved'),
                (2, 'DebugFlags'),
                (1, 'UseAffinity'),
            ]

        _fields_ = [
            (WORD, 'BlockUnits'),
            (UCHAR, 'SizeIndex'),
            (_BucketFlags, 'BucketFlags'),
        ]

        def AllocationCount(self):
            return self['BlockUnits'].li.int() >> 1

    class HEAP_ENTRY_EXTRA(pstruct.type):
        def __padding(self):
            size = 8 if getattr(self, 'WIN64', False) else 4
            res = sum(self[fld].li.size() for fld in ['AllocatorBacktraceIndex', 'TagIndex'])
            return dyn.block(size - res)

        _fields_ = [
            (USHORT, 'AllocatorBacktraceIndex'),
            (USHORT, 'TagIndex'),
            (__padding, 'padding(AllocatorBacktraceIndex,TagIndex)'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'Settable'),
        ]

    class HEAP_ENTRY_(pbinary.flags):
        _fields_ = [
            (1, 'NO_COALESCE'),     # SETTABLE_FLAG3
            (1, 'FFU2'),            # SETTABLE_FLAG2
            (1, 'FFU1'),            # SETTABLE_FLAG1
            (1, 'LAST_ENTRY'),
            (1, 'VIRTUAL_ALLOC'),
            (1, 'FILL_PATTERN'),
            (1, 'EXTRA_PRESENT'),
            (1, 'BUSY'),
        ]

    class HEAP_ENTRY(pstruct.type, versioned):
        class UnusedBytes(pbinary.flags):
            # FIXME: we need to implement both backend and frontend versions of UnusedBytes
            class _Type(pbinary.enum):
                length, _values_ = 3, [
                    ('Chunk', 0),
                    ('Segment', 1),
                    ('LargeChunk', 4),
                    ('Linked', 5),
                ]

            _fields_ = [
                (1, 'AllocatedByFrontend'),
                (3, 'Unknown'),             # UnusedBytes == 1
                (1, 'Busy'),                # UnusedBytes
                (_Type, 'Type'),            # UnusedBytes
            ]

            def FrontEndQ(self):
                return True if self['AllocatedByFrontend'] else False

            def BackEndQ(self):
                return not self.FrontEndQ()

            def BusyQ(self):
                return True if self['Busy'] else False

            def FreeQ(self):
                return not self.BusyQ()

            def summary(self):
                frontend = 'FE' if self.FrontEndQ() else 'BE'
                busy = 'BUSY' if self.BusyQ() else 'FREE'
                res = self.item('Type')
                return "{:s} {:s} Type:{:s}".format(frontend, busy, res.str())

        def __init__(self, **attrs):
            super(HEAP_ENTRY, self).__init__(**attrs)
            f = [
                (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData')
            ]

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
                f.extend([
                   (USHORT, 'Size'),
                   (USHORT, 'PreviousSize'),
                   (UCHAR, 'SegmentIndex'),
                   (HEAP_ENTRY_, 'Flags'),
                   (UCHAR, 'UnusedBytes'),
                   (UCHAR, 'TagIndex'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                f.extend([
                    (USHORT, 'Size'),
                    (HEAP_ENTRY_, 'Flags'),
                    (UCHAR, 'SmallTagIndex'),    # Checksum
                    (USHORT, 'PreviousSize'),
                    (UCHAR, 'SegmentOffset'),    # Size // blocksize
                    (HEAP_ENTRY.UnusedBytes, 'UnusedBytes'),  # XXX: for some reason this is explicitly checked against 0x05
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

        def Flags(self):
            return self['UnusedBytes']

        def Type(self):
            res = self.Flags()
            return res.item('Type')

        def Extra(self):
            # Since this is just a regular HEAP_ENTRY, there's no way to
            # determine extra bytes used by the block. So just return 0 here.
            return 0

        def FrontEndQ(self):
            res = self.Flags()
            return True if res['AllocatedByFrontend'] else False
        def BackEndQ(self):
            return not self.FrontEndQ()

        def BusyQ(self):
            res = self.Flags()
            return True if res['Busy'] else False
        def FreeQ(self):
            return not self.BusyQ()

        def summary(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WS03):
                res = "Size={:x} SegmentIndex={:x} PreviousSize={:x} TagIndex={:x}"
                res = [res.format(self['Size'].int(), self['SegmentIndex'].int(), self['PreviousSize'].int(), self['TagIndex'].int())]

                res+= ["UnusedBytes=({:s})".format(self['UnusedBytes'].summary())]
                res+= ["Flags=({:s})".format(self['Flags'].summary())]
                return ' '.join(res)

            # Display only the relevant fields for the LF heap that's part of NTDDI_WIN7
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                res = "Size={:x} SmallTagIndex={:x} PreviousSize={:x} SegmentOffset={:x}"
                res = [res.format(self['Size'].int(), self['SmallTagIndex'].int(), self['PreviousSize'].int(), self['SegmentOffset'].int())]

                res+= ["UnusedBytes=({:s})".format(self['UnusedBytes'].summary())]
                res+= ["Flags=({:s})".format(self['Flags'].summary())]
                return ' '.join(res)
            return super(HEAP_ENTRY, self).summary()

    class _HEAP_ENTRY(ptype.encoded_t):
        '''
        This is an internal version of _HEAP_ENTRY that supports encoding/decoding
        the HEAP_ENTRY from either the frontend or the backend.
        '''
        _value_ = HEAP_ENTRY

        ## If the user tries to access any field, look in the decoded version first
        def __getitem__(self, name):
            res = self.d.li
            return operator.getitem(res, name)
        def __setitem__(self, name, value):
            res = self.d.li
            return operator.setitem(res, name, value)

        ## Output details that correspond to our decoded entry
        def classname(self):
            return self.typename()
        def repr(self):
            return self.details()
        def details(self):
            res = self.d.li.copy(offset=self.getoffset())
            return res.details()
        def summary(self):
            if self.FrontEndQ():
                res = self.serialize()
                return res.encode('hex') if sys.version_info.major < 3 else res.hex()
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            data, res = self.serialize(), self.d.li
            return "{:s} : {:-#x} <-> {:+#x} : Flags:{:s}".format(data.encode('hex') if sys.version_info.major < 3 else data.hex(), -res['PreviousSize'].int() * blocksize, res['Size'].int() * blocksize, res['Flags'].summary())

        def Flags(self):
            '''Unencoded flags grabbed from the original HEAP_ENTRY'''
            res = self.d.li
            return res.Flags()

        def Type(self):
            '''Unencoded type grabbed from the original HEAP_ENTRY'''
            res = self.object
            return res.Type()

        def FrontEndQ(self):
            res = self.object
            return res.FrontEndQ()

        def BackEndQ(self):
            # Back-to-Front(242)
            res = self.object
            return res.BackEndQ()

        def BusyQ(self):
            '''Returns whether the chunk (decoded) is in use or not'''
            # XXX: this can be optimized by checking FrontEndQ which requires decoding
            res = self.d.li
            return res.BusyQ()

        def FreeQ(self):
            '''Returns whether the chunk (decoded) is free or not'''
            # FIXME: this can be optimized by checking FrontEndQ which requires decoding
            res = self.d.li
            return res.FreeQ()

        def Extra(self):
            res = self.object

            # If this is a backend chunk, then there's no way to determinue
            # extra bytes. So simply return 0.
            if res.BackEndQ():
                return 0

            # Check the bottom 6-bits to determine the unused bytes used by
            # the frontend block
            f = res.Flags()
            unused = f.int() & 0x3f

            # Subtract from the header size so we know how many extra bytes
            # are used by the chunk instead of subtracting from the block.
            hs = self.size()
            return hs - (unused or hs)

        ## Backend
        class __BE_HEAP_ENTRY(HEAP_ENTRY):
            '''HEAP_ENTRY after decoding'''
            _fields_ = [
                (lambda self: pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'ReservedForAlignment'),
                (USHORT, 'Size'),
                (USHORT, 'Checksum'),
                (USHORT, 'PreviousSize'),
                (UCHAR, 'SegmentOffset'),
                (HEAP_ENTRY.UnusedBytes, 'Flags'),
            ]

            def Flags(self):
                return self['Flags']

            def Extra(self):
                # The backend allocator doesn't support the concept of having
                # extra bytes, so return 0 here.
                return 0

            def __init__(self, **attrs):
                return super(HEAP_ENTRY, self).__init__(**attrs)

            def summary(self):
                blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
                return "{:s} PreviousSize={:+#x} Size={:+#x} SegmentOffset={:#x} Checksum={:#x}".format(self['Flags'].summary(), -self['PreviousSize'].int() * blocksize, self['Size'].int() * blocksize, self['SegmentOffset'].int(), self['Checksum'].int())

        class _BE_Encoded(pstruct.type):
            '''
            This type is used strictly for encoding/decoding and is used when
            casting the backing type.
            '''
            _fields_ = [
                (lambda self: pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'Unencoded'),
                (dyn.array(pint.uint32_t, 2), 'Encoded'),
            ]

        def __GetEncoding(self):
            heap = self.getparent(type=HEAP)
            encoding = heap['Encoding'].li
            return heap['EncodeFlagMask'].li.int(), tuple(item.int() for item in encoding['Keys'])

        def __be_encode(self, object, **attrs):
            object = object.cast(self._BE_Encoded)

            # Cache some attributes
            if any(not hasattr(self, "_HEAP_ENTRY_{:s}".format(name)) for name in {'EncodeFlagMask', 'Encoding'}):
                self._HEAP_ENTRY_EncodeFlagMask, self._HEAP_ENTRY_Encoding = self.__GetEncoding()

            # If HEAP.EncodeFlagMask has been set to something, then we'll just use it
            if self._HEAP_ENTRY_EncodeFlagMask:
                iterable = (bitmap.data((encoder ^ item.int(), 32), reversed=True) for item, encoder in zip(object['Encoded'], self._HEAP_ENTRY_Encoding))
                data = object['Unencoded'].serialize() + functools.reduce(operator.add, iterable)
                res = ptype.block().set(data)
                return super(_HEAP_ENTRY, self).encode(res)
            return super(_HEAP_ENTRY, self).encode(object)

        def __be_decode(self, object, **attrs):
            object = object.cast(self._BE_Encoded)

            # Cache some attributes
            if any(not hasattr(self, "_HEAP_ENTRY_{:s}".format(name)) for name in {'EncodeFlagMask', 'Encoding'}):
                self._HEAP_ENTRY_EncodeFlagMask, self._HEAP_ENTRY_Encoding = self.__GetEncoding()

            # Now determine if we're encoded, and decode it if so.
            if object['Encoded'][0].int() & self._HEAP_ENTRY_EncodeFlagMask:
                iterable = (bitmap.data((encoder ^ item.int(), 32), reversed=True) for item, encoder in zip(object['Encoded'], self._HEAP_ENTRY_Encoding))
                data = object['Unencoded'].serialize() + functools.reduce(operator.add, iterable)
                res = ptype.block().set(data)
                return super(_HEAP_ENTRY, self).decode(res)

            # Otherwise, we're not encoded. So, just pass-through...
            return super(_HEAP_ENTRY, self).decode(object, **attrs)

        def __be_summary(self):
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            data, res = self.serialize(), self.d.li
            return "{:s} : {:-#x} <-> {:+#x} : Flags:{:s}".format(data.encode('hex') if sys.version_info.major < 3 else data.hex(), -res['PreviousSize'].int() * blocksize, res['Size'].int() * blocksize, res['Flags'].summary())

        def ChecksumQ(self):
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'ChecksumQ', message='Unable to calculate the checksum for a non-backend type')

            # No checksum is used for anything earlier than NTDDI_WIN7
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                raise error.IncorrectChunkVersion(self, 'ChecksumQ', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))

            # Calculate checksum (a^9^8 == b)
            res = self.d.li.cast(self._BE_Encoded)
            data = bytearray(res['Encoded'].serialize())
            chk = functools.reduce(operator.xor, data[:3], 0)
            return chk == data[3]

        def Size(self):
            '''Return the decoded Size field'''
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'Size')
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8

            # Use the "Size" from our decoded value and combine it with the blocksize.
            self = self.d.li
            return blocksize * self['Size'].int()

        def PreviousSize(self):
            '''Return the decoded PreviousSize field'''
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'Size')
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8

            # Use the "PreviousSize" from our decoded value and combine it with the blocksize.
            self = self.d.li
            return blocksize * self['PreviousSize'].int()

        ## Frontend
        class __FE_HEAP_ENTRY(HEAP_ENTRY):
            '''HEAP_ENTRY after decoding'''
            class UnusedBytes(HEAP_ENTRY.UnusedBytes):
                # XXX: I think one of these bits (Unknown) is for
                #      RtlpLogHeapFailure because this byte is &'d
                #      by RtlpAllocateHeap with 0x3f...
                _fields_ = [
                    (1, 'AllocatedByFrontend'),
                    (1, 'LogFailure'),
                    (6, 'Busy'),
                ]

                def BusyQ(self):
                    return True if self['Busy'] else False

                def FreeQ(self):
                    return not self.BusyQ()

                def Unused(self):
                    '''Return the number of unused bytes for the chunk.'''
                    # Subtract it from our HEAP_ENTRY size so that we convert
                    # it from the block's unused bytes to the chunk's unused.
                    res = 0x10 if getattr(self, 'WIN64', False) else 8
                    return (self['Busy'] or res) - res

                def summary(self):
                    frontend = 'FE' if self.FrontEndQ() else 'BE'
                    busy = 'BUSY' if self.BusyQ() else 'FREE'
                    return "{:s} {:s}".format(frontend, busy)

            _fields_ = [
                (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData'),
                (lambda self: dyn.clone(PHEAP_SUBSEGMENT, _value_=UINT32), 'SubSegment'),
                (USHORT, 'Unknown'),     # seems to be diff on 32-bit?
                (UCHAR, 'EntryOffset'),
                (UnusedBytes, 'Flags'),
            ]

            def Flags(self):
                return self['Flags']

            def BusyQ(self):
                res = self.Flags()
                return res.BusyQ()

            def Extra(self):
                res = self.Flags()
                return -res.Unused()

            def __init__(self, **attrs):
                return super(HEAP_ENTRY, self).__init__(**attrs)

            def summary(self):
                return "{:s} Extra={:+d} SubSegment=*{:#x} EntryOffset={:#x}".format(self['Flags'].summary(), self.Extra(), self['SubSegment'].int(), self['EntryOffset'].int())

        class _FE_Encoded(pstruct.type):
            '''
            This type is used strictly for encoding/decoding and is used when
            casting the backing type.
            '''
            def __init__(self, **attrs):
                super(_HEAP_ENTRY._FE_Encoded, self).__init__(**attrs)
                f = self._fields_ = []

                if getattr(self, 'WIN64', False):
                    f.extend([
                        (pint.uint64_t, 'Unencoded'),
                        (pint.uint64_t, 'Encoded'),
                    ])

                # 32-bit seems to swap the Encoded/Decoded fields.
                else:
                    f.extend([
                        (pint.uint32_t, 'Encoded'),
                        (pint.uint32_t, 'Unencoded'),
                    ])
                return

            def EncodedValue(self):
                res = self['Encoded'].int()
                return res & 0xffffffffff

            def EncodedUntouchedValue(self):
                res = self['Encoded'].int()
                return res & ~0xffffffffff

        def __fe_encode(self, object, **attrs):
            object = object.cast(self._FE_Encoded)

            # Cache some attributes
            if any(not hasattr(self, "_HEAP_ENTRY_{:s}".format(name)) for name in {'Heap', 'LFHKey'}):
                try:
                    self._HEAP_ENTRY_Heap, self._HEAP_ENTRY_LFHKey = self.getparent(type=HEAP), __RtlpLFHKey__(self)
                except (ptypes.error.ItemNotFoundError, AttributeError):
                    # FIXME: Log that this heap-entry is non-encoded due to inability to determine required keys
                    pass

            # If we were able to find the LFHKey, then use it to encode our object
            if hasattr(self, "_HEAP_ENTRY_{:s}".format('LFHKey')):

                # Now to encode our 64-bit header
                if getattr(self, 'WIN64', False):
                    dn = self.getoffset()
                    dn ^= self._HEAP_ENTRY_Heap.getoffset()
                    dn >>= 4
                    dn ^= object.EncodedValue()
                    dn ^= self._HEAP_ENTRY_LFHKey
                    dn <<= 4
                    dn |= object.EncodedUntouchedValue()

                # Encode the 32-bit header
                else:
                    dn = object.EncodedValue()
                    dn = self.getoffset() >> 3
                    dn ^= self._HEAP_ENTRY_LFHKey
                    dn ^= self._HEAP_ENTRY_Heap.getoffset()

                res = object.copy().set(Encoded=dn)
                return super(_HEAP_ENTRY, self).decode(res)

            # FIXME: We should probably throw an exception here since the header
            #        is _required_ to be encoded.
            return super(_HEAP_ENTRY, self).encode(object)

        def __fe_decode(self, object, **attrs):
            object = object.cast(self._FE_Encoded)

            # Cache some attributes
            if any(not hasattr(self, "_HEAP_ENTRY_{:s}".format(name)) for name in {'Heap', 'LFHKey'}):
                self._HEAP_ENTRY_Heap, self._HEAP_ENTRY_LFHKey = self.getparent(type=HEAP), __RtlpLFHKey__(self)

            # Now we can decode our 64-bit header
            if getattr(self, 'WIN64', False):
                dn = self.getoffset()
                dn ^= self._HEAP_ENTRY_Heap.getoffset()
                dn >>= 4
                dn ^= object.EncodedValue()
                dn ^= self._HEAP_ENTRY_LFHKey
                dn <<= 4
                dn |= object.EncodedUntouchedValue()

            # Decode the 32-bit header
            else:
                dn = object.EncodedValue()
                dn ^= self.getoffset() >> 3
                dn ^= self._HEAP_ENTRY_LFHKey
                dn ^= self._HEAP_ENTRY_Heap.getoffset()

            res = object.copy().set(Encoded=dn)
            return super(_HEAP_ENTRY, self).decode(res)

        def EntryOffsetQ(self):
            if not self.FrontEndQ():
                raise error.InvalidHeapType(self, 'EntryOffsetQ', message='Unable to query the entry-offset for a non-frontend type')

            # Grab the unencoded Flags and the decoded _HEAP_ENTRY
            f, res = self.object.Flags(), self.d.li

            # We have an EntryOffset if the "EntryOffset" field is
            # set and our unencoded Flags is set to 5.
            if res['EntryOffset'].int():
                return f.int() == 5
            return False

        def EntryOffset(self):
            if not self.FrontEndQ():
                raise error.InvalidHeapType(self, 'EntryOffset', message='Unable to fetch the entry-offset for a non-frontend type')

            # FIXME: this should probably return an rpointer_t to a _HEAP_ENTRY
            res = self.d.li
            return res['EntryOffset'].int() * res.size()

        def SubSegment(self):
            if not self.FrontEndQ():
                raise error.InvalidHeapType(self, 'SubSegment', message='Unable to dereference the subsegment for a non-frontend type')

            # Decode the header, and return the "SubSegment" from it.
            header = self.d.li
            return header['SubSegment'].d

        ## encoded_t properties/methods
        def properties(self):
            res = super(_HEAP_ENTRY, self).properties()
            if not self.initializedQ():
                return res

            # properties for frontend HEAP_ENTRY
            if self.FrontEndQ():
                res['EntryOffsetQ'] = self.EntryOffsetQ()
                return res

            # properties for backend HEAP_ENTRY
            try:
                res['ChecksumOkay'] = self.ChecksumQ()
            except (ptypes.error.InitializationError, error.NdkHeapException):
                pass
            return res

        def _object_(self):
            res = self.object
            if res.FrontEndQ():
                return self.__FE_HEAP_ENTRY
            return self.__BE_HEAP_ENTRY

        def encode(self, object, **attrs):
            res = self.object
            if res['UnusedBytes'].int() == 5:
                # FIXME: figure out what to do with the new chunk header
                offset = self.getoffset() - res['SegmentOffset'] * res.size()
                raise error.InvalidHeapType(self, 'encode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)

            # If this is a front-end chunk then use the front-end encoder.
            elif res.FrontEndQ():
                return self.__fe_encode(object, **attrs)
            return self.__be_encode(object, **attrs)

        def decode(self, object, **attrs):
            res = self.object
            if res['UnusedBytes'].int() == 5:
                # FIXME: we shouldn't need to decode anything since our chunk
                #        header is elsewhere.
                offset = self.getoffset() - res['SegmentOffset'] * res.size()
                raise error.InvalidHeapType(self, 'decode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)

            # If this is a front-end chunk, then use the front-end decoder.
            elif res.FrontEndQ():
                return self.__fe_decode(object, **attrs)
            return self.__be_decode(object, **attrs)

        def summary(self):
            res = self.d
            if res.initializedQ():
                return res.l.summary()
            return super(_HEAP_ENTRY, self).summary()

    class ENCODED_POINTER(PVOID):
        '''
        This is a pointer that's encoded/decoded with ntdll!RtlpHeapKey and as
        such can be used to dereference/reference things with a tweaked pointer.
        '''
        def __HeapPointerKey(self):
            heap = self.getparent(HEAP)
            return heap['PointerKey'].int()

        def __GetPointerKey(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                return __RtlpHeapKey__(self)
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
                return self.__HeapPointerKey()
            raise error.InvalidPlatformException(self, '__GetPointerKey', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), expected=sdkddkver.NTDDI_WIN7)

        def encode(self, object, **attrs):
            try:
                res = self.__GetPointerKey()
                self._EncodedPointerKey = res

            # An exception means that we can't satisfy the user's encoding request.
            except Exception:
                logging.warning("{:s} : Unable to encode the pointer due to a failure while getting the pointer key.".format(self.instance()), exc_info=True)

            # If the pointer key was found, then we can encode the pointer with it.
            if hasattr(self, '_EncodedPointerKey'):
                return super(ENCODED_POINTER, self).encode(self._value_().set(object.get() ^ self._EncodedPointerKey))
            return super(ENCODED_POINTER, self).encode(object)

        def decode(self, object, **attrs):
            if not hasattr(self, '_EncodedPointerKey'):
                res = self.__GetPointerKey()
                self._EncodedPointerKey = res

            # Now that we grabbed the pointer key, we can simply xor it with our object's value.
            res = object.get() ^ self._EncodedPointerKey
            return super(ENCODED_POINTER, self).decode(self._value_().set(res))

        def summary(self):
            return "*{:#x} -> *{:#x}".format(self.get(), self.d.getoffset())

if 'HeapChunk':
    class HEAP_UNCOMMITTED_DATA(ptype.block):
        def blocksize(self):
            return 0
        def summary(self):
            return "...{:d} bytes...".format(self.length)
        def dereference(self, **attrs):
            attrs.setdefault('length', self.length)
            return self.cast(ptype.block, **attrs)
        d = property(fget=lambda self, **attrs: self.dereference(**attrs))

    class HEAP_BLOCK_UNCOMMITTED(HEAP_UNCOMMITTED_DATA):
        pass

    class HEAP_CHUNK_LARGE(pstruct.type):
        length = 0
        def __Data(self):
            res = self['Header'].li.size()
            return dyn.clone(HEAP_UNCOMMITTED_DATA, length=max(0, self.length - res))

        _fields_ = [
            (HEAP_ENTRY, 'Header'),
            (__Data, 'Data'),
        ]

        def summary(self):
            res = map("\\x{:02x}".format, bytearray(self['Header'].serialize()))
            return "Header=\"{:s}\" Data=...{:d} bytes...".format(str().join(res), self['Data'].length)

    class _HEAP_CHUNK(pstruct.type):
        '''
        This is an internal definition that isn't defined by Microsoft, but is
        intended to distinguish chunks that exist in either the frontend or the
        backend heap.
        '''
        def __ListEntry(self):
            '''Return the "ListEntry" field if the chunk is free and in the backend.'''

            # If we have a .__SubSegment__ attribute, then this is a frontend
            # chunk and this there's no linked-list for any free'd chunks.
            if hasattr(self, '__SubSegment__'):
                return ptype.undefined

            # Use the backing object here to check the busy flag since there's
            # really no need to decode anything when loading
            header = self['Header'].li
            if header.object.Type()['Chunk'] and header.object.FreeQ():
                return dyn.clone(LIST_ENTRY, _object_=fpointer(self.__class__, 'ListEntry'), _path_=['ListEntry'])

            # No linked-list as the chunk is busy or not a chunk
            return ptype.undefined

        def __ChunkFreeEntryOffset(self):
            '''Return the "ChunkFreeEntryOffset" field if the chunk is supposed to contain it.'''

            # If we have a .__SubSegment__ attribute, then this should
            # definitely be a front-end chunk and so we need to check
            # if it's in-use or not.
            if hasattr(self, '__SubSegment__'):
                header = self['Header'].li

                # Use the backing object here to grab the UnusedBytes field
                # since it doesn't need to be decoded in order to determine
                # whether the frontend is actually using the chunk or not.
                unusedBytes = header.object['UnusedBytes']
                return pint.uint_t if unusedBytes.int() & 0x0f else pint.uint16_t

            # Backend heap doesn't use a chunk offset, so just return an
            # unsized integer.
            return pint.uint_t

        def __Data(self):
            header = self['Header'].li

            # Grab the heap type from the header's backing type since it's only
            # a single unencoded bit that distinguishes between how the sizes
            # are calculated
            if hasattr(self, '__SubSegment__'):
                ss = self.__SubSegment__
                size = ss['BlockSize'].int() * (0x10 if getattr(self, 'WIN64', False) else 8)

            else:
                size = header.Size()

            res = sum(self[fld].li.size() for fld in ['Header', 'ListEntry', 'ChunkFreeEntryOffset'])
            return dyn.block(max(0, size - res))

        _fields_ = [
            (_HEAP_ENTRY, 'Header'),
            (__ListEntry, 'ListEntry'),
            (__ChunkFreeEntryOffset, 'ChunkFreeEntryOffset'),
            (__Data, 'Data'),
        ]

        def BusyQ(self):
            return self['Header'].BusyQ()

        def FreeQ(self):
            return self['Header'].FreeQ()

        def properties(self):
            res = super(_HEAP_CHUNK, self).properties()
            if self.initializedQ():
                header = self['Header']
                res['Busy'] = header.BusyQ()
                if header.FrontEndQ():
                    res['Type'] = 'FE'
                    return res
                t = header.Type()
                res['Type'] = t.str()
            return res

        def next(self):
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.InvalidHeapType(self, 'next', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            parent = self.getparent(HEAP)
            return parent.new(cls, offset=self.getoffset() + self['Header'].Size())

        def previous(self):
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.InvalidHeapType(self, 'previous', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            parent = self.getparent(HEAP)
            return parent.new(cls, offset=self.getoffset() - header.PreviousSize())
        prev = previous

        def nextfree(self):
            '''Walk to the next entry in the free-list (recent)'''
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.InvalidHeapType(self, 'nextfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            t = header.Type()
            if not t['Chunk']:
                raise error.IncorrectChunkType(self, 'nextfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            link = self['ListEntry']
            return link['Flink'].d.l

        def previousfree(self):
            '''Moonwalk to the previous entry in the free-list (recent)'''
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.InvalidHeapType(self, 'previousfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            t = header.Type()
            if not t['Chunk']:
                raise error.IncorrectChunkType(self, 'previousfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            link = self['ListEntry']
            return link['Blink'].d.l
        prevfree = previousfree

if 'Frontend':
    class FrontEndHeap(ptype.definition):
        cache = {}

        class Type(pint.enum, UCHAR):
            _values_ = [
                ('Backend', 0),
                ('LAL', 1),
                ('LFH', 2),
            ]

    class FreeListBucket(LIST_ENTRY):
        class _HeapBucketLink(ptype.pointer_t):
            class _HeapBucketCounter(pstruct.type):
                _fields_ = [
                    (USHORT, 'UnknownEvenCount'),
                    (USHORT, 'AllocationCount'),
                    (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'Padding'),
                ]

                def get(self):
                    t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                    res = self.cast(t)
                    return res.int()

            _value_ = _HeapBucketCounter
            _object_ = HEAP_BUCKET

            def decode(self, object, **attrs):
                t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                res = object.cast(t)
                if res.int() & 1:
                    res.set(res.int() & ~1)

                else:
                    res.set(res.int() & ~0)
                    raise error.InvalidHeapType(self, 'decode', message="Address {:#x} is not a valid HEAP_BUCKET".format(res.int()))
                return super(FreeListBucket._HeapBucketLink, self).decode(res, **attrs)

            def FrontEndQ(self):
                res = self.object.cast(pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t)
                return True if res.int() & 1 else False

            def BackEndQ(self):
                return not self.BackEndQ()

            def summary(self):
                t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                res = self.object
                if res.cast(t).int() & 1:
                    return "(FRONTEND) {:s}".format(super(FreeListBucket._HeapBucketLink, self).summary())
                return "(BACKEND) AllocationCount={:#x} UnknownEvenCount={:#x}".format(res['AllocationCount'].int(), res['UnknownEvenCount'].int())

            def details(self):
                t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                res = self.object.cast(t)
                if res.int() & 1:
                    return super(FreeListBucket._HeapBucketLink, self).summary()
                return self.object.details()
            repr = details

        _fields_ = [
            (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Flink'),
            (_HeapBucketLink, 'Blink'),
        ]

        def FrontEndQ(self):
            return self['Blink'].FrontEndQ()
        def BackEndQ(self):
            return self['Blink'].BackEndQ()

        def properties(self):
            res = super(FreeListBucket, self).properties()
            if self.initializedQ():
                res['Type'] = 'FE' if self.FrontEndQ() else 'BE'
            return res

        def collect(self, size=None):
            '''Collect chunks beginning at the current chunk which are less than ``size``'''
            for item in self.walk():
                if size is None:
                    size = item['Header'].Size()
                if item['Header'].Size() > size:
                    break
                yield item
            return

    class ListsInUseUlong(BitmapBitsUlong):
        _object_, length = ULONG, 0

    class ListsInUseBytes(BitmapBitsBytes):
        _object_, length = UCHAR, 0

if 'LookasideList':
    class HEAP_LOOKASIDE(pstruct.type):
        _fields_ = [
            (dyn.clone(SLIST_HEADER, _object_=fpointer(_HEAP_CHUNK, 'ListHead'), _path_=['ListHead']), 'ListHead'),
            (USHORT, 'Depth'),
            (USHORT, 'MaximumDepth'),
            (ULONG, 'TotalAllocates'),
            (ULONG, 'AllocateMisses'),
            (ULONG, 'TotalFrees'),
            (ULONG, 'FreeMisses'),
            (ULONG, 'LastTotalAllocates'),
            (ULONG, 'LastAllocateMisses'),
            (dyn.array(ULONG, 2), 'Counters'),
            (ULONG, 'Unknown'),     # XXX: missing from all definitions
            (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'Padding'),
        ]

    @FrontEndHeap.define
    class LAL(parray.type):
        type = 1
        HEAP_MAX_FREELIST = 0x80
        length, _object_ = HEAP_MAX_FREELIST, HEAP_LOOKASIDE

    class HeapCache(pstruct.type):
        # ISS X-Force - Heap Cache Exploitation
        # ftp://ftp.software.ibm.com/common/ssi/sa/wh/n/sew03014usen/SEW03014USEN.PDF
        def __Bitmap(self):
            p = self.getparent(HeapCache)
            res = p['NumBuckets'].li
            return dyn.clone(ListsInUseUlong, length=res.int() // 32)

        def __Buckets(self):
            p = self.getparent(HeapCache)
            res = self['NumBuckets'].li
            return dyn.array(_HEAP_CHUNK, res.int())

        _fields_ = [
            (ULONG, 'NumBuckets'),
            (LONG, 'CommittedSize'),
            (LARGE_INTEGER, 'CounterFrequency'),
            (LARGE_INTEGER, 'AverageAllocTime'),
            (LARGE_INTEGER, 'AverageFreeTime'),
            (LONG, 'SampleCounter'),
            (LONG, 'field_24'),
            (LARGE_INTEGER, 'AllocTimeRunningTotal'),
            (LARGE_INTEGER, 'FreeTimeRunningTotal'),
            (LONG, 'AllocTimeCount'),
            (LONG, 'FreeTimeCount'),
            (LONG, 'Depth'),
            (LONG, 'HighDepth'),
            (LONG, 'LowDepth'),
            (LONG, 'Sequence'),
            (LONG, 'ExtendCount'),
            (LONG, 'CreateUCRCount'),
            (LONG, 'LargestHighDepth'),
            (LONG, 'HighLowDifference'),

            (P(__Bitmap), 'pBitmap'), # XXX
            (P(__Buckets), 'pBucket'),  # XXX

            (__Buckets, 'Buckets'),
            (__Bitmap, 'Bitmap'),
        ]

if 'SegmentHeap':
    # XXX: https://www.sstic.org/media/SSTIC2020/SSTIC-actes/pool_overflow_exploitation_since_windows_10_19h1/SSTIC2020-Article-pool_overflow_exploitation_since_windows_10_19h1-bayet_fariello.pdf
    class HEAP_VS_DELAY_FREE_CONTEXT(pstruct.type):
        _fields_ = [
            (SLIST_HEADER, 'ListHead'),
        ]

    class HEAP_SUBALLOCATOR_CALLBACKS(pstruct.type, versioned):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        _fields_ = [
            (__ULONG3264, 'Allocate'),
            (__ULONG3264, 'Free'),
            (__ULONG3264, 'Commit'),
            (__ULONG3264, 'Decommit'),
            (__ULONG3264, 'ExtendContext'),
        ]
    class HEAP_VS_CONTEXT(pstruct.type, versioned):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        class _LockType32(rtltypes.RTLP_HP_LOCK_TYPE, ULONG):
            pass

        class _LockType64(rtltypes.RTLP_HP_LOCK_TYPE, ULONGLONG):
            pass

        def __ForceOffset(field, offset):
            def __padding(self):
                predicate = functools.partial(operator.ne, field)
                iterable = itertools.chain(itertools.takewhile(predicate, iter(self.keys())))
                return dyn.block(max(0, offset - sum(self[fld].li.size() for fld in iterable)))
            return __padding

        _fields_ = [
            (__ULONG3264, 'Lock'),
            (lambda self: self._LockType64 if getattr(self, 'WIN64', False) else self._LockType32, 'LockType'),
            (rtltypes.RTL_RB_TREE, 'FreeChunkTree'),
            (LIST_ENTRY, 'SubsegmentList'),
            (__ULONG3264, 'TotalCommittedUnits'),
            (__ULONG3264, 'FreeCommittedUnits'),
            (__ForceOffset('offset(DelayFreeContext)', 0x40), 'offset(DelayFreeContext)'),
            (HEAP_VS_DELAY_FREE_CONTEXT, 'DelayFreeContext'),
            (__ForceOffset('offset(BackendCtx)', 0x80), 'offset(BackendCtx)'),
            (PVOID, 'BackendCtx'),
            (HEAP_SUBALLOCATOR_CALLBACKS, 'Callbacks'),
            (rtltypes.RTL_HP_VS_CONFIG, 'Config'),
            (ULONG, 'Flags'),
            (__ForceOffset('size(HEAP_VS_CONTEXT)', 0xc0), 'size(HEAP_VS_CONTEXT)'),
        ]

    class HEAP_LFH_SUBSEGMENT_STAT(pstruct.type):
        _fields_ = [
            (UCHAR, 'Index'),
            (UCHAR, 'Count'),
        ]

    class HEAP_LFH_SUBSEGMENT_STATS(dynamic.union, versioned):
        _fields_ = [
            (lambda self: dyn.array(HEAP_LFH_SUBSEGMENT_STAT, 4 if getattr(self, 'WIN64', False) else 2), 'Buckets'),
            (PVOID, 'AllStats'),
        ]

    class HEAP_LFH_SUBSEGMENT_OWNER(pstruct.type):
        class _Spare0(pbinary.flags):
            _fields_ = [
                (7, 'Spare'),
                (1, 'IsBucket'),
            ]
        class _Slot(dynamic.union):
            _fields_ = [
                (UCHAR, 'SlotCount'),
                (UCHAR, 'SlotIndex'),
            ]
        _fields_ = [
            (_Spare0, 'Spare0'),
            (UCHAR, 'BucketIndex'),
            (_Slot, 'Slot'),
            (UCHAR, 'Spare1'),
            (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(AvailableSubsegmentCount)'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'AvailableSubsegmentCount'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'Lock'),
            (LIST_ENTRY, 'AvailableSubsegmentList'),    # FIXME: points to something
            (LIST_ENTRY, 'FullSubsegmentList'),         # FIXME: points to something
        ]

    class HEAP_LFH_SUBSEGMENT_ENCODED_OFFSETS(pstruct.type):
        # FIXME: this is encoded LfhKey ^ self ^ (subsegment >> 12)
        _fields_ = [
            (USHORT, 'BlockSize'),
            (USHORT, 'FirstBlockOffset'),
        ]

    class HEAP_LFH_SUBSEGMENT(pstruct.type):
        class _Location(pint.enum, UCHAR):
            _values_ = [
                ('AvailableSubsegmentList', 0),
                ('FullSubsegmentList', 1),
                ('Backend', 2),
            ]
        class _BlockBitmap(pbinary.array):
            class BlockBitmapElement(pbinary.flags):
                _fields_ = [
                    (1, 'UnusedBytes'),
                    (1, 'Busy'),
                ]
            _object_ = BlockBitmapElement

        def __BlockBitmap(self):
            '''dyn.array(ULONGLONG, 0)'''
            # FIXME: BlockCount * 2bits
            count = self['BlockCount'].li
            return dyn.clone(self._BlockBitmap, length=count.int())

        def __padding_BlockBitmap(self):
            blockoffsets = self['BlockOffsets'].li
            firstoffset = blockoffsets['FirstBlockOffset']
            #FIXME: calculate size with offset to get to blocks
            return dyn.block(0)

        def __Blocks(self):
            count = self['BlockCount'].li
            # FIXME: calculate chunk size
            chunk = dyn.block(0)
            return dyn.array(chunk, count.int())

        _fields_ = [
            (lambda self: dyn.clone(LIST_ENTRY, _object_=P(HEAP_LFH_SUBSEGMENT), _path_=['ListEntry']), 'ListEntry'),
            (P(HEAP_LFH_SUBSEGMENT_OWNER), 'Owner'),
            (PVOID, 'CommitLock'),
            (USHORT, 'FreeCount'),
            (USHORT, 'BlockCount'),
            (USHORT, 'FreeHint'),
            (_Location, 'Location'),
            (UCHAR, 'WitheldBlockCount'),
            (HEAP_LFH_SUBSEGMENT_ENCODED_OFFSETS, 'BlockOffsets'),  # FIXME: encoded
            (UCHAR, 'CommitUnitShift'),
            (UCHAR, 'CommitUnitCount'),
            (USHORT, 'CommitStateOffset'),
            (__BlockBitmap, 'BlockBitmap'),
            (__padding_BlockBitmap, 'padding(BlockBitmap)'),
            (__Blocks, 'Blocks'),
        ]

    class HEAP_LFH_FAST_REF(dynamic.union):
        # FIXME: check this
        @pbinary.littleendian
        class _RefCount(pbinary.struct):
            _fields_ = [
                (lambda self: 52 if getattr(self, 'WIN64', False) else 20, 'Unknown'),
                (12, 'RefCount'),
            ]
        _fields_ = [
            (PVOID, 'Target'),  # FIXME: points at something
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'Value'),
            (_RefCount, 'RefCount'),
        ]

    class HEAP_LFH_AFFINITY_SLOT(pstruct.type):
        _fields_ = [
            (HEAP_LFH_SUBSEGMENT_OWNER, 'State'),
            (HEAP_LFH_FAST_REF, 'ActiveSubsegment'),
        ]

    class HEAP_LFH_BUCKET(pstruct.type, versioned):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        def __AffinitySlots(self):
            t = P(HEAP_LFH_AFFINITY_SLOT)
            return dyn.array(t, 1)  # FIXME: number of affinity cores

        _fields_ = [
            (HEAP_LFH_SUBSEGMENT_OWNER, 'State'),
            (__ULONG3264, 'TotalBlockCount'),
            (__ULONG3264, 'TotalSubsegmentCount'),
            (ULONG, 'ReciprocalBlockSize'),
            (UCHAR, 'Shift'),
            (UCHAR, 'ContentionCount'),
            (lambda self: dyn.block(2 if getattr(self, 'WIN64', False) else 2), 'Padding(ContentionCount)'),
            (__ULONG3264, 'AffinityMappingLock'),
            (P(UCHAR), 'ProcAffinityMapping'),
            (P(__AffinitySlots), 'AffinitySlots'),
        ]

    class HEAP_LFH_CONTEXT(pstruct.type, versioned):
        def __ForceOffset(field, offset):
            def __padding(self):
                predicate = functools.partial(operator.ne, field)
                iterable = itertools.chain(itertools.takewhile(predicate, iter(self.keys())))
                return dyn.block(max(0, offset - sum(self[fld].li.size() for fld in iterable)))
            return __padding

        _fields_ = [
            (PVOID, 'BackendCtx'),
            (HEAP_SUBALLOCATOR_CALLBACKS, 'Callbacks'),
            (P(UCHAR), 'AffinityModArray'),
            (UCHAR, 'MaxAffinity'),
            (UCHAR, 'LockType'),
            (SHORT, 'MemStatsOffset'),
            (rtltypes.RTL_HP_LFH_CONFIG, 'Config'),
            (__ForceOffset('offset(BucketStats)', 0x40), 'offset(BucketStats)'),
            (HEAP_LFH_SUBSEGMENT_STATS, 'BucketStats'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SubsegmentCreationLock'),
            (__ForceOffset('offset(Buckets)', 0x80), 'offset(Buckets)'),
            (dyn.array(P(HEAP_LFH_BUCKET), 129), 'Buckets'),
            (lambda self: dyn.block(0x38 if getattr(self, 'WIN64', False) else 0x3c), 'size(HEAP_LFH_CONTEXT)')
        ]

    class HEAP_OPPORTUNISTIC_LARGE_PAGE_STATS(pstruct.type):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        _fields_ = [
            (__ULONG3264, 'SmallPagesInUseWithinLarge'),
            (__ULONG3264, 'OpportunisticLargePageCount'),
        ]

    class HEAP_RUNTIME_MEMORY_STATS(pstruct.type, versioned):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        _fields_ = [
            (__ULONG3264, 'TotalReservedPages'),
            (__ULONG3264, 'TotalCommittedPages'),
            (__ULONG3264, 'FreeCommittedPages'),
            (__ULONG3264, 'LfhFreeCommittedPages'),
            (dyn.array(HEAP_OPPORTUNISTIC_LARGE_PAGE_STATS, 2), 'LargePageStats'),
            (rtltypes.RTL_HP_SEG_ALLOC_POLICY, 'LargePageUtilizationPolicy'),
        ]

    class HEAP_SEG_CONTEXT(pstruct.type, versioned):
        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        class _Flags(pstruct.type):
            _fields_ = [
                #(UCHAR, 'LargePagePolicy'),         # UCHAR LargePagePolicy:3
                #(UCHAR, 'FullDecommit'),            # UCHAR FullDecommit:1
                #(UCHAR, 'ReleaseEmptySegments'),    # UCHAR ReleaseEmptySegments:1
                (UCHAR, 'AllFlags'),
                (dyn.block(2), 'padding(AllFlags)'),
            ]
        _fields_ = [
            (__ULONG3264, 'SegmentMask'),
            (UCHAR, 'UnitShift'),
            (UCHAR, 'PagesPerUnitShift'),
            (UCHAR, 'FirstDescriptorIndex'),
            (UCHAR, 'CachedCommitSoftShift'),
            (UCHAR, 'CachedCommitHighShift'),
            (_Flags, 'Flags'),
            (ULONG, 'MaxAllocationSize'),
            (SHORT, 'OlpStatsOffset'),
            (SHORT, 'MemStatsOffset'),
            (PVOID, 'LfhContext'),
            (PVOID, 'VsContext'),
            (rtltypes.RTL_HP_ENV_HANDLE, 'EnvHandle'),
            (PVOID, 'Heap'),
            (lambda self: dyn.block(0 if getattr(self, 'WIN64', False) else 0x18), 'padding(Heap)'),
            (__ULONG3264, 'SegmentLock'),
            (LIST_ENTRY, 'SegmentListHead'),
            (__ULONG3264, 'SegmentCount'),
            (rtltypes.RTL_RB_TREE, 'FreePageRanges'),
            (__ULONG3264, 'FreeSegmentListLock'),
            (dyn.array(SINGLE_LIST_ENTRY, 2), 'FreeSegmentList'),
            (lambda self: dyn.block(0x38 if getattr(self, 'WIN64', False) else 0x1c), 'Padding'),
        ]

    class SEGMENT_HEAP(pstruct.type, versioned):
        length = 0x5f0
        class _CommitLimitMetadata(pstruct.type):
            def __ULONG3264(self):
                return ULONGLONG if getattr(self, 'WIN64', False) else ULONG
            _fields_ = [
                (__ULONG3264, 'ReservedMustBeZero1'),
                (PVOID, 'UserContext'),
                (__ULONG3264, 'ReservedMustBeZero2'),
                (PVOID, 'Spare'),
            ]

        def __ULONG3264(self):
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        def __ForceOffset(field, offset):
            def __padding(self):
                predicate = functools.partial(operator.ne, field)
                iterable = itertools.chain(itertools.takewhile(predicate, iter(self.keys())))
                return dyn.block(max(0, offset - sum(self[fld].li.size() for fld in iterable)))
            return __padding

        _fields_ = [
            (rtltypes.RTL_HP_ENV_HANDLE, 'EnvHandle'),
            (ULONG, 'Signature'),
            (ULONG, 'GlobalFlags'),
            (ULONG, 'Interceptor'),
            (USHORT, 'ProcessHeapIndex'),
            (USHORT, 'AllocatedFromMetadata'),  # USHORT AllocatedFromMetadata:1
            # XXX: union {
            (lambda self: ptype.undefined if self['AllocatedFromMetadata'].li.int() & 1 else rtltypes.RTL_HEAP_MEMORY_LIMIT_DATA, 'CommitLimitData'),
            (lambda self: _CommitLimitMetadata if self['AllocatedFromMetadata'].li.int() & 1 else ptype.undefined, 'CommitLimitMetadata?'),
            # XXX: }
            (__ForceOffset('offset(LargeMetadataLock)', 0x40), 'offset(LargeMetadataLock)'),
            (__ULONG3264, 'LargeMetadataLock'),
            (rtltypes.RTL_RB_TREE, 'LargeAllocMetadata'),
            (__ULONG3264, 'LargeReservedPages'),
            (__ULONG3264, 'LargeCommitedPages'),
            (rtltypes.RTL_RUN_ONCE, 'StackTraceInitVar'),
            (__ForceOffset('offset(MemStats)', 0x80), 'offset(MemStats)'),
            (HEAP_RUNTIME_MEMORY_STATS, 'MemStats'),
            (USHORT, 'GlobalLockCount'),
            (dyn.block(2), 'padding(GlobalLockCount)'),
            (ULONG, 'GlobalLockOwner'),
            (__ULONG3264, 'ContextExtendLock'),
            (P(UCHAR), 'AllocatedBase'),
            (P(UCHAR), 'UncommittedBase'),
            (P(UCHAR), 'ReservedLimit'),
            (__ForceOffset('offset(SegContexts)', 0x100), 'offset(SegContexts)'),
            (dyn.array(HEAP_SEG_CONTEXT, 2), 'SegContexts'),
            (HEAP_VS_CONTEXT, 'VsContext'),
            (HEAP_LFH_CONTEXT, 'LfhContext'),
        ]

if 'LFH':
    class INTERLOCK_SEQ(pstruct.type):
        def __init__(self, **attrs):
            super(INTERLOCK_SEQ, self).__init__(**attrs)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (USHORT, 'Depth'),
                    (USHORT, 'FreeEntryOffset'),
                    (ULONG, 'Sequence'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (USHORT, 'Depth'),
                    (USHORT, 'FreeEntryOffset'),    # XXX: the high-bit of this seems to be a flag for locking
                    (pint.uint_t, 'Sequence'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def summary(self):
            return "Depth:{:#x} FreeEntryOffset:{:#x} Sequence:{:#x}".format(self['Depth'].int(), self['FreeEntryOffset'].int(), self['Sequence'].int())

    @pbinary.littleendian
    class HEAP_LFH_MEM_POLICIES(pbinary.flags):
        _fields_ = [
            (30, 'Spare'),
            (1, 'SlowSubsegmentGrowth'),
            (1, 'DisableAffinity'),
        ]

    class HEAP_USERDATA_OFFSETS(pstruct.type):
        _fields_ = [
            (USHORT, 'FirstAllocationOffset'),
            (USHORT, 'BlockStride'),
        ]
        def summary(self):
            iterable = ((item.int(), 2 + 2 * item.size()) for item in self.value)
            return "FirstAllocationOffset={:#0{:d}x} BlockStride={:#0{:d}x}".format(*itertools.chain(*iterable))

    class HEAP_USERDATA_ENCODED_OFFSETS(ptype.encoded_t):
        _value_, _object_ = ULONG,  HEAP_USERDATA_OFFSETS

        def __cache_lfheap(self):
            if hasattr(self, '_LFH_HEAP'):
                return self._LFH_HEAP
            result = self.getparent(LFH_HEAP)
            self._LFH_HEAP = result
            return result

        def __cache_lfhkey(self):
            if hasattr(self, '_LFH_KEY'):
                return self._RtlpLFHKey
            result = __RtlpLFHKey__(self)
            self._RtlpLFHKey = result
            return result

        def decode(self, object, **attrs):
            lfheap, lfhkey = self.__cache_lfheap(), self.__cache_lfhkey()
            header = self.getparent(HEAP_USERDATA_HEADER)

            # decode our object using all of the values that we cached
            res = object.get() ^ header.getoffset() ^ lfheap.getoffset() ^ lfhkey
            return super(HEAP_USERDATA_ENCODED_OFFSETS, self).decode(self._value_().set(res))

        def encode(self, object, **attrs):
            lfheap, lfhkey = self.__cache_lfheap(), self.__cache_lfhkey()
            header = self.getparent(HEAP_USERDATA_HEADER)

            # encode our object using all of the values that we cached
            res = object.get() ^ header.getoffset() ^ lfheap.getoffset() ^ lfhkey
            return super(HEAP_USERDATA_ENCODED_OFFSETS, self).encode(self._value_().set(res))

        def summary(self):
            decoded = self.d.l
            return "{:#x} :({:s})> {:s}".format(self.get(), decoded.classname(), decoded.summary())

    class HEAP_USERDATA_HEADER(pstruct.type):
        def ByOffset(self, entryoffset):
            '''Return the field at the specified `entryoffset`.'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            return self.field(blocksize * entryoffset, recurse=True)

        def HeaderByOffset(self, offset):
            '''Return the header for the given entry offset.'''
            res = self.ByOffset(offset)
            if isinstance(res, _HEAP_ENTRY):
                return res
            raise error.NotFoundException(self, 'HeaderByOffset', message="Object at entry offset {:#x} does not point to a header ({:s}). An invalid entry offset was specified.".format(offset, _HEAP_ENTRY.typename()))
        def BlockByOffset(self, offset):
            '''Return the block at the given entry offset.'''
            res = self.HeaderByOffset(offset)
            return res.getparent(_HEAP_CHUNK)
        def ChunkByOffset(self, offset):
            '''Return the chunk (data) for the entry offset.'''
            res = self.BlockByOffset(offset)
            return res['Data']

        def NextIndex(self):
            '''Return the next UserBlock index that will be allocated from this structure's segment'''
            ss = self['SubSegment'].d.li
            return ss.FreeEntryBlockIndex()
        def NextBlock(self):
            '''Return the next block that will be allocated from this structure's segment'''
            index = self.NextIndex()
            return self['Blocks'][index]
        def NextChunk(self):
            '''Return a pointer to the next chunk (data) that will be returned from this structure's segment.'''
            res = self.NextBlock()
            return res['Data']

        def UsageBitmap(self):
            '''Return a bitmap showing the busy/free chunks that are available'''
            iterable = ((1 if item['Header'].BusyQ() else 0) for item in self['Blocks'])
            iterable = (bitmap.new(item, 1) for item in iterable)
            return functools.reduce(bitmap.push, iterable, bitmap.zero)

        def __Blocks(self):
            pss = self['SubSegment'].li
            ss = pss.d.li

            # Copy the SubSegment as a hidden attribute so that the
            # chunk can quickly lookup any associated information.
            chunk = dyn.clone(_HEAP_CHUNK, __SubSegment__=ss)
            return dyn.array(chunk, ss['BlockCount'].int())

        def __BitmapData(self):
            res = self['BusyBitmap'].li
            bits = 64 if getattr(self, 'WIN64', False) else 32
            fractionQ = 1 if res['SizeOfBitmap'].int() % bits else 0
            return dyn.clone(res._Buffer, length=fractionQ + res['SizeOfBitmap'].int() // bits)

        def __align_Blocks(self):
            '''Decode the "EncodedOffsets" field to figure out how far we need to pad before the actual blocks.'''
            encodedoffsets = self['EncodedOffsets'].li
            offsets = encodedoffsets.d.l

            # Now that the offsets have been decoded, grab the first offset and pad the structure to it.
            first = offsets['FirstAllocationOffset']
            return dyn.padding(first.int())

        def __init__(self, **attrs):
            super(HEAP_USERDATA_HEADER, self).__init__(**attrs)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (lambda self: P(HEAP_SUBSEGMENT), 'SubSegment'),
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),   # FIXME: figure out what this actually points to
                    (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SizeIndex'),
                    (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(Signature)'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (self.__Blocks, 'Blocks'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (lambda self: P(HEAP_SUBSEGMENT), 'SubSegment'),
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),   # FIXME: figure out what this actually points to
                    (UCHAR, 'SizeIndex'),
                    (UCHAR, 'GuardPagePresent'),
                    (USHORT, 'PaddingBytes'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (HEAP_USERDATA_ENCODED_OFFSETS, 'EncodedOffsets'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(EncodedOffsets)'),
                    (rtltypes.RTL_BITMAP_EX if getattr(self, 'WIN64', False) else rtltypes.RTL_BITMAP, 'BusyBitmap'),
                    (self.__BitmapData, 'BitmapData'),
                    # XXX: there's some padding here which we'll need to grab from EncodedOffsets
                    (self.__align_Blocks, 'align(Blocks)'),
                    (self.__Blocks, 'Blocks'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            return

    class HEAP_LOCAL_SEGMENT_INFO(pstruct.type):
        def __init__(self, **attrs):
            super(HEAP_LOCAL_SEGMENT_INFO, self).__init__(**attrs)
            f = self._fields_ = []
            integral = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t

            # FIXME NTDDI_WIN8 changes the order of these
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_SUBSEGMENT), 'Hint'),
                    (P(HEAP_SUBSEGMENT), 'ActiveSubSegment'),
                    (dyn.array(P(HEAP_SUBSEGMENT), 16), 'CachedItems'),
                    (SLIST_HEADER, 'SListHeader'),
                    (HEAP_BUCKET_COUNTERS, 'Counters'),
                    (P(HEAP_LOCAL_DATA), 'LocalData'),
                    (ULONG, 'LastOpSequence'),
                    (USHORT, 'BucketIndex'),
                    (USHORT, 'LastUsed'),
                    (integral, 'Reserved'),         # FIXME: Is this right?
                ])

            # FIXME: this is where our lfh segment comes from
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_LOCAL_DATA), 'LocalData'),
                    (P(HEAP_SUBSEGMENT), 'ActiveSubSegment'),
                    (dyn.array(P(HEAP_SUBSEGMENT), 16), 'CachedItems'),
                    (SLIST_HEADER, 'SListHeader'),
                    (HEAP_BUCKET_COUNTERS, 'Counters'),
                    (ULONG, 'LastOpSequence'),
                    (USHORT, 'BucketIndex'),
                    (USHORT, 'LastUsed'),
                    (USHORT, 'NoThrashCount'),

                    (USHORT, 'Reserved'),           # XXX: added manually
                    (dyn.block(0xc if getattr(self, 'WIN64', False) else 4), 'unknown'), # XXX: there's got to be another field here
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def Bucket(self):
            '''Return the LFH bin associated with the current HEAP_LOCAL_SEGMENT_INFO'''
            bi = self['BucketIndex'].int()
            lfh = self.getparent(LFH_HEAP)
            return lfh['Buckets'][bi]

        def Segment(self):
            '''
            Return the correct HEAP_SUBSEGMENT by checking "Hint" first, and then
            falling back to "ActiveSubSegment".
            '''

            # FIXME: CachedItems seems to point to segments that have previously
            #        been in the 'Hint' field. However, when this happens the
            #        current segment to honor for allocations is 'ActiveSubSegment'.

            if operator.contains(self, 'Hint') and self['Hint'].int():
                return self['Hint'].d
            elif self['ActiveSubSegment'].int():
                return self['ActiveSubSegment'].d
            raise error.MissingSegmentException(self, 'Segment', heap=self.getparent(HEAP), localdata=self.getparent(HEAP_LOCAL_DATA))

        def LastSegment(self):
            '''
            Return the last-used HEAP_SUBSEGMENT from the cache.
            '''
            res = self['LastUsed']
            return self['CachedItems'][res.int()].d

    class LFH_BLOCK_ZONE(pstruct.type):
        def __SubSegments(self):
            try:
                fh = self.getparent(LFH_HEAP)
                cb = fh['ZoneBlockSize'].int()

            # If we couldn't find the subsegment size in the LFH_HEAP, then just
            # fake-allocate it in order to grab its size
            except ptypes.error.ItemNotFoundError:
                cb = self.new(HEAP_SUBSEGMENT).a.size()

            # Calculate the offset to our current field so that we can determine
            # how many subsegments are in use.
            base = self.getoffset() + sum(self[fld].li.size() for fld in ['ListEntry', 'FreePointer', 'Limit'])

            # Figure out how many HEAP_SUBSEGMENT elements are in use.
            res = self['FreePointer'].li.int() - base
            return dyn.array(HEAP_SUBSEGMENT, res // cb)

        def __Available(self):
            try:
                fh = self.getparent(LFH_HEAP)
                cb = fh['ZoneBlockSize'].int()

            # If we couldn't find the subsegment size in the LFH_HEAP, then just
            # fake-allocate it in order to grab its size
            except ptypes.error.ItemNotFoundError:
                cb = self.new(HEAP_SUBSEGMENT).a.size()

            # Take the free pointer (points to a chunk), and subtract a HEAP_ENTRY
            # so that we divide evenly as for some reason there's about that
            # amount of space between its value and the last segment
            base = self['FreePointer'].li.int() - (0x10 if getattr(self, 'WIN64', False) else 8)

            # Calculate the number of elements before we hit the limit
            res = self['Limit'].li.int() - base
            return dyn.array(HEAP_SUBSEGMENT, res // cb)

        def __init__(self, **attrs):
            super(LFH_BLOCK_ZONE, self).__init__(**attrs)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(LIST_ENTRY, _object_=P(LFH_BLOCK_ZONE), _path_=['ListEntry']), 'ListEntry'),
                    (P(HEAP_SUBSEGMENT), 'FreePointer'),         # Points to the next HEAP_SUBSEGMENT to use
                    (P(_HEAP_CHUNK), 'Limit'),                   # End of HEAP_SUBSEGMENTs

                    (self.__SubSegments, 'SubSegments'),
                    (self.__Available, 'Available'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(LIST_ENTRY, _object_=P(LFH_BLOCK_ZONE), _path_=['ListEntry']), 'ListEntry'),
                    (ULONG, 'NextIndex'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(NextIndex)'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def iterate(self):
            '''Iterate through all the used subsegments in this particular zone.'''
            for item in self['SubSegments']:
                yield item
            return

    class HEAP_BUCKET_RUN_INFO(pstruct.type):
        _fields_ = [
            (ULONG, 'Bucket'),
            (ULONG, 'RunLength'),
        ]
        def summary(self):
            return "Bucket:{:#x} RunLength:{:#x}".format(self['Bucket'].int(), self['RunLength'].int())

    class USER_MEMORY_CACHE_ENTRY(pstruct.type, versioned):
        # FIXME: Figure out which SizeIndex is used for a specific cache entry
        class _UserBlocks(pstruct.type):
            # FIXME: Is this the correct structure for USER_MEMORY_CACHE_ENTRY's
            #        SLIST_HEADER?
            def __Blocks(self):
                entry = self.getparent(USER_MEMORY_CACHE_ENTRY)

                res = [ item.getoffset() for item in entry.p.value ]
                idx = res.index(entry.getoffset()) + 1

                blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
                rees = idx * blocksize + blocksize

                block = dyn.clone(_HEAP_CHUNK, blocksize=lambda s, sz=res: sz)
                return dyn.array(block, entry['AvailableBlocks'].int() * 8)

            _fields_ = [
                (dyn.array(pint.uint32_t, 4), 'unknown'),
                (__Blocks, 'Blocks'),
            ]

        def __init__(self, **attrs):
            super(USER_MEMORY_CACHE_ENTRY, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                #(dyn.clone(SLIST_HEADER, _object_=_UserBlocks), 'UserBlocks'),
                (SLIST_HEADER, 'UserBlocks'),   # XXX: check this offset
                (ULONG, 'AvailableBlocks'),     # AvailableBlocks * 8 seems to be the actual size
                (ULONG, 'MinimumDepth'),
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'Padding')
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                # XXX: win10
                f.extend([
                    (ULONG, 'CacheShiftThreshold'),
                    (USHORT, 'Allocations'),
                    (USHORT, 'Frees'),
                    (USHORT, 'CacheHits'),

                    # XXX: The following fields have been manually added to deal
                    #      with padding, but they've got to be some undocumented
                    #      fields or something...
                    (USHORT, 'Unknown'),
                    (ULONG, 'Reserved'),
                    (dyn.block(0x8 if getattr(self, 'WIN64', False) else 0), 'Padding'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)

    class HEAP_SUBSEGMENT(pstruct.type):
        def BlockSize(self):
            '''Returns the size of each block (data + header) within the subsegment'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            return self['BlockSize'].int() * blocksize
        def ChunkSize(self):
            '''Return the size of the chunks (data) that this HEAP_SUBSEGMENT is responsible for providing'''
            res = self.new(_HEAP_ENTRY).a
            return self.BlockSize() - res.size()

        def BlockIndexByOffset(self, offset):
            '''Return the expected block index for the given offset.'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            fo = offset * blocksize
            shift = self.new(HEAP_USERDATA_HEADER).a.size()
            return (fo - shift) // self.BlockSize()

        def FreeEntryBlockIndex(self):
            '''Returns the index into UserBlocks of the next block to allocate given the `FreeEntryOffset` of the current HEAP_SUBSEGMENT'''
            res = self['AggregateExchg']['FreeEntryOffset']
            return self.BlockIndexByOffset(res.int())

        def NextFreeBlock(self):
            '''Return the next block HeapAllocate will return for the current segment.'''
            index = self.FreeEntryBlockIndex()
            ub = self['UserBlocks'].d.li
            return ub['Blocks'][index]

        def UsedBlockCount(self):
            '''Return the total number of UserBlocks that have been allocated'''
            return self['BlockCount'].int() - self['AggregateExchg']['Depth'].int()
        def UnusedBlockCount(self):
            '''Return the number of UserBlocks that have been either freed or unallocated'''
            return self['AggregateExchg']['Depth'].int()
        def Usage(self):
            '''Return a bitmap showing the busy/free chunks that are available within `UserBlocks`'''
            ub = self['UserBlocks'].d.li
            return ub.UsageBitmap()
        def UsageString(self):
            '''Return a binary string showing the busy/free chunks that are available within `UserBlocks`'''
            res = self.Usage()
            return bitmap.string(res)

        def properties(self):
            res = super(HEAP_SUBSEGMENT, self).properties()
            if self.initializedQ():
                res['SegmentIsFull'] = self['AggregateExchg']['Depth'].int() == 0
                res['AvailableBlocks'] = self.UnusedBlockCount()
                res['BusyBlocks'] = self.UsedBlockCount()
            return res

        def __init__(self, **attrs):
            super(HEAP_SUBSEGMENT, self).__init__(**attrs)
            f = self._fields_ = []

            # FIXME: NTDDI_WIN8 moves the DelayFreeList to a different place
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
                    (P(HEAP_USERDATA_HEADER), 'UserBlocks'),

                    (INTERLOCK_SEQ, 'AggregateExchg'),
                    (USHORT, 'BlockSize'),
                    (USHORT, 'Flags'),
                    (USHORT, 'BlockCount'),
                    (UCHAR, 'SizeIndex'),
                    (UCHAR, 'AffinityIndex'),

                    (dyn.clone(SLIST_ENTRY, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'SFreeListEntry'),    # XXX: DelayFreeList
                    (ULONG, 'Lock'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(Lock)'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                # XXX: win10
                f.extend([
                    (P(HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
                    (P(HEAP_USERDATA_HEADER), 'UserBlocks'),
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DelayFreeList'),

                    (INTERLOCK_SEQ, 'AggregateExchg'),
                    (USHORT, 'BlockSize'),
                    (USHORT, 'Flags'),
                    (USHORT, 'BlockCount'),
                    (UCHAR, 'SizeIndex'),
                    (UCHAR, 'AffinityIndex'),

                    (ULONG, 'Lock'),
                    (dyn.clone(SLIST_ENTRY, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'SFreeListEntry'),    # XXX: DelayFreeList
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(SFreeListEntry)'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)

    class PHEAP_SUBSEGMENT(ptype.pointer_t):
        '''
        This points to a HEAP_SUBSEGMENT, but ensures that it uses the same
        source of any ptype.encoded_t that parented it.
        '''
        _object_ = HEAP_SUBSEGMENT
        def dereference(self, **attrs):
            if isinstance(self.source, ptypes.provider.proxy) and self.parent is not None:
                p = self.parent.getparent(ptype.encoded_t)
                attrs.setdefault('source', p.source)
            return super(PHEAP_SUBSEGMENT, self).dereference(**attrs)

    class HEAP_LOCAL_DATA(pstruct.type):
        def CrtZone(self):
            '''Return the SubSegmentZone that's correctly associated with the value of the CrtZone field'''
            fe = self.getparent(LFH_HEAP)
            zone = self['CrtZone'].int()
            zoneiterator = (z for z in fe['SubSegmentZones'].walk() if z.getoffset() == zone)
            try:
                res = next(zoneiterator)
            except StopIteration:
                raise error.CrtZoneNotFoundError(self, 'CrtZone', zone=zone, frontendheap=fe.getoffset(), heap=fe.p.p.getoffset())
            return res

        def __init__(self, **attrs):
            super(HEAP_LOCAL_DATA, self).__init__(**attrs)
            f = self._fields_ = []
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DeletedSubSegments'),
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'DeleteRateThreshold'),
                    (aligned, 'align(SegmentInfo)'),
                    (dyn.array(HEAP_LOCAL_SEGMENT_INFO, 128), 'SegmentInfo'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                # XXX: win10
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DeletedSubSegments'),
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONG, 'DeleteRateThreshold'),
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(DeleteRateThreshold)'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)

    @FrontEndHeap.define
    class LFH_HEAP(pstruct.type, versioned):
        type = 2

        # FIXME: Figure out how the "UserBlockCache" actually works

        # FIXME: It seems that the HEAP_LOCAL_DATA is defined as an array due to
        #        processor affinity when it's enabled in the flags. This is why
        #        all of the available LFH material references it as a single-element.

        def BlockUnits(self, size):
            '''Return the block units when given a ``size``'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8

            # Figure out what the proper size should be when adding the
            # size of the header and a value for rounding.
            size_and_header = size + blocksize + 7

            # Now we can divide the total size by the blocksize in order
            # to get the actual number of units.
            units = math.floor(size_and_header / (1. * blocksize))
            return math.trunc(units)

        def BucketByUnits(self, units):
            '''Iterate through all of the buckets finding the smallest one that can contain the requested number of units.'''
            for index, item in enumerate(self['Buckets']):
                if units <= item['BlockUnits'].int():
                    return item
                continue
            raise error.NotFoundException(self, 'BucketByUnits', message="Unable to find a Bucket for the requested units ({:#x})".format(units))

        def Bucket(self, size):
            '''Return the Bucket given a ``size``'''
            units = self.BlockUnits(size)
            return self.BucketByUnits(units)

        def SegmentInfo(self, size):
            '''Return the HEAP_LOCAL_SEGMENT_INFO for a specific ``size``'''
            bucket = self.Bucket(size)
            index = bucket['SizeIndex'].int()

            # If we are using the "SegmentInfoArrays" pointer array, then index into it.
            if 'SegmentInfoArrays' in self:
                segmentinfoarray = self['SegmentInfoArrays']
                segmentinfo = segmentinfoarray[index]

                # If the pointer is defined, then we can dereference it.
                if segmentinfo.int():
                    return segmentinfo.d.li

                # Otherwise we'll just return the pointer and warn the user about it.
                units = bucket['BlockUnits'].int()
                logging.warning("{:s} : Returning SegmentInfoArrays[{:d}] for BlockUnits {:#x} (size {:#x}) despite it being unset".format(self.instance(), index, units, size))
                return segmentinfo

            # Otherwise we need to descend into the LocalData before we find our array.
            localdata = self['LocalData']
            segmentinfoarray = localdata['SegmentInfo']
            return segmentinfoarray[index]

        def __init__(self, **attrs):
            super(LFH_HEAP, self).__init__(**attrs)
            integral = ULONGLONG if getattr(self, 'WIN64', False) else ULONG
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (rtltypes.RTL_CRITICAL_SECTION, 'Lock'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(LFH_BLOCK_ZONE)), 'SubSegmentZones'),
                    (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'ZoneBlockSize'),
                    (P(HEAP), 'Heap'),
                    (ULONG, 'SegmentChange'),
                    (ULONG, 'SegmentCreate'),
                    (ULONG, 'SegmentInsertInFree'),
                    (ULONG, 'SegmentDelete'),
                    (ULONG, 'CacheAllocs'),                                     # sum(item['AvailableBlocks'] for item in self['UserBlockCache'])
                    (ULONG, 'CacheFrees'),
                    (integral, 'SizeInCache'),
                    (dyn.block(0 if getattr(self, 'WIN64', False) else 4), 'padding(SizeInCache)'),
                    (HEAP_BUCKET_RUN_INFO, 'RunInfo'),
                    (dyn.array(USER_MEMORY_CACHE_ENTRY, 12), 'UserBlockCache'), # FIXME: Not sure what this cache is used for
                    (dyn.array(HEAP_BUCKET, 128), 'Buckets'),
                    (HEAP_LOCAL_DATA, 'LocalData'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                f.extend([
                    (rtltypes.RTL_SRWLOCK, 'Lock'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(LFH_BLOCK_ZONE)), 'SubSegmentZones'),
                    (P(HEAP), 'Heap'),

                    (P(ptype.undefined), 'NextSegmentInfoArrayAddress'),        # XXX: this might be an array that terminates at self['FirstUncommittedAddress']
                    (P(ptype.undefined), 'FirstUncommittedAddress'),
                    (P(ptype.undefined), 'ReservedAddressLimit'),
                    (ULONG, 'SegmentCreate'),
                    (ULONG, 'SegmentDelete'),
                    (ULONG, 'MinimumCacheDepth'),
                    (ULONG, 'CacheShiftThreshold'),
                    (integral, 'SizeInCache'),
                    (HEAP_BUCKET_RUN_INFO, 'RunInfo'),
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(RunInfo)'),
                    (dyn.array(USER_MEMORY_CACHE_ENTRY, 12), 'UserBlockCache'), # FIXME: Not sure what this cache is used for
                    (HEAP_LFH_MEM_POLICIES, 'MemoryPolicies'),
                    (dyn.array(HEAP_BUCKET, 129), 'Buckets'),
                    (dyn.array(P(HEAP_LOCAL_SEGMENT_INFO), 129), 'SegmentInfoArrays'),
                    (dyn.array(P(HEAP_LOCAL_SEGMENT_INFO), 129), 'AffinitizedInfoArrays'),
                    (P(SEGMENT_HEAP), 'SegmentAllocator'),
                    (dyn.align(8), 'align(LocalData)'),
                    (HEAP_LOCAL_DATA, 'LocalData'),
                ])
            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

if 'Heap':
    class HEAP_SEGMENT(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(HEAP_SEGMENT, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            f = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
                f.extend([
                    (_HEAP_ENTRY, 'Entry'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (ULONG, 'Flags'),
                    (P(HEAP), 'Heap'),
                    (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'LargestUnCommittedRange'),
                    (PVOID, 'BaseAddress'),
                    (ULONG, 'NumberOfPages'),
                    (P(_HEAP_CHUNK), 'FirstEntry'),
                    (P(_HEAP_CHUNK), 'LastValidEntry'),
                    (ULONG, 'NumberOfUnCommittedPages'),
                    (ULONG, 'NumberOfUnCommittedRanges'),
                    (P(HEAP_UNCOMMMTTED_RANGE), 'UnCommittedRanges'),
                    (USHORT, 'AllocatorBackTraceIndex'),
                    (USHORT, 'Reserved'),
                    (P(_HEAP_CHUNK), 'LastEntryInSegment'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
                f.extend([
                    (_HEAP_ENTRY, 'Entry'),
                    (HEAP_SIGNATURE, 'SegmentSignature'),
                    (ULONG, 'SegmentFlags'),
                    (lambda s: dyn.clone(LIST_ENTRY, _sentinel_='Blink', _path_=['SegmentListEntry'], _object_=fpointer(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentListEntry'),   # XXX: entry comes from HEAP
                    (P(HEAP), 'Heap'),
                    (PVOID, 'BaseAddress'),
                    (ULONG, 'NumberOfPages'),
                    (aligned, 'align(FirstEntry)'),     # FIXME: padding, or alignment?
                    (P(_HEAP_CHUNK), 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (ULONG, 'NumberOfUnCommittedPages'),
                    (ULONG, 'NumberOfUnCommittedRanges'),
                    (USHORT, 'AllocatorBackTraceIndex'),
                    (USHORT, 'Reserved'),
                    (aligned, 'align(UCRSegmentList)'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(HEAP_UCR_DESCRIPTOR, 'SegmentEntry')), 'UCRSegmentList'),
                ])

            else:
                # XXX: win10
                # XXX: https://lzeroyuee.cn/old-blog/%E5%88%9D%E8%AF%86win32%E5%A0%86%20-%20lZeroyuee%27s%20Blog.html
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

        def Bounds(self):
            PAGE_SIZE = 0x1000
            ucr = self['NumberOfUncommittedPages'].int() * PAGE_SIZE
            start, end = (self[fld].li for fld in ['FirstEntry', 'LastValidEntry'])
            return start.int(), end.int() - ucr

        def Chunk(self, address):
            start, end = self.Bounds()
            if start <= address < end:
                # FIXME: implement this
                raise NotImplementedError
            cls = self.__class__
            raise error.InvalidChunkAddress(self, 'Chunk', message="The requested address ({:#x}) is not within the boundaries of the current {:s} ({:#x}<>{:#x}).".format(address, cls.typename(), start, end), Segment=self)

        def iterate(self):
            '''Iterate through all the chunks in the current segment.'''
            start, end = self.Bounds()
            res = self['FirstEntry'].d
            while res.getoffset() < end:
                yield res.l
                res = res.next()
            return

        def walk(self):
            yield self
            for item in self['SegmentListEntry'].walk():
                yield item
            return

    class HEAP_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (ULONG, 'Size'),
            (USHORT, 'TagIndex'),
            (USHORT, 'CreatorBackTraceIndex'),
            (dyn.array(USHORT, 24), 'TagName'),
        ]

    class HEAP_UCR_SEGMENT(pstruct.type):
        _fields_ = [
            (lambda self: P(HEAP_UCR_SEGMENT), 'Next'),
            (ULONG, 'ReservedSize'),
            (ULONG, 'CommittedSize'),
            (ULONG, 'filler'),
        ]

    class HEAP_UNCOMMMTTED_RANGE(pstruct.type):
        _fields_ = [
            (lambda self: P(HEAP_UNCOMMMTTED_RANGE), 'Next'),
            (PVOID, 'Address'),
            (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'Size'),
            (ULONG, 'filler'),
        ]

    class HEAP_PSEUDO_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (ULONG, 'Size'),
        ]

    class HEAP_UCR_DESCRIPTOR(pstruct.type):
        def __ListEntry(self):
            res = P(HEAP_UCR_DESCRIPTOR)
            return dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=res)

        def __Address(self):
            def target(self):
                p = self.getparent(HEAP_UCR_DESCRIPTOR)
                res = p['Size'].li
                return dyn.clone(HEAP_BLOCK_UNCOMMITTED, length=res.int())
            return P(target)

        _fields_ = [
            (__ListEntry, 'ListEntry'),
            (dyn.clone(LIST_ENTRY, _path_=['UCRSegmentList'], _object_=fpointer(HEAP_SEGMENT, 'UCRSegmentList')), 'SegmentEntry'),
            (__Address, 'Address'),  # Sentinel Address
            (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'Size'),
        ]

    class HEAP_VIRTUAL_ALLOC_ENTRY(pstruct.type):
        def __ListEntry(self):
            res = P(HEAP_VIRTUAL_ALLOC_ENTRY)
            return dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=res)

        def __BusyBlock(self):
            cb = self['CommitSize'].li
            res = sum(self[fld].li.size() for fld in ['ListEntry', 'ExtraStuff', 'CommitSize', 'ReserveSize'])
            return dyn.clone(HEAP_CHUNK_LARGE, length=max(0, cb.int() - res))

        _fields_ = [
            (__ListEntry, 'ListEntry'),
            (HEAP_ENTRY_EXTRA, 'ExtraStuff'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'CommitSize'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'ReserveSize'),
            (__BusyBlock, 'BusyBlock'),
        ]

    class HEAP(pstruct.type, versioned):
        def UncommittedRanges(self):
            '''Iterate through the list of UncommittedRanges(UCRList) for the HEAP'''
            for item in self['UCRList'].walk():
                yield item
            return

        def Segments(self):
            '''Iterate through the list of Segments(SegmentList) for the HEAP'''
            for item in self['SegmentList'].walk():
                yield item
            return

        def HeapListLookup(self, blockindex):
            '''Return the correct (recent) HEAP_LIST_LOOKUP structure according to the ``blockindex`` (size / blocksize)'''
            if not self['FrontEndHeapType']['LFH']:
                raise error.IncorrectHeapType(self, 'HeapListLookup', message="Invalid value for FrontEndHeapType ({:s})".format(self['FrontEndHeapType'].summary()), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))

            # FIXME: factor in BlocksIndex.BaseIndex and BlocksIndex.ExtraItem
            p = self['BlocksIndex'].d.l
            while blockindex >= p['ArraySize'].int():
                if p['ExtendedLookup'].int() == 0:
                    raise error.ListHintException(self, 'HeapListLookup', message='Unable to locate ListHint for blockindex', blockindex=blockindex, index=p['ArraySize'].int()-1, lookup=p)
                p = p['ExtendedLookup'].d.l
            return p

        def ListHint(self, size):
            '''Return the ListHint from the BlockIndex according to the specified ``size``'''
            if not self['FrontEndHeapType']['LFH']:
                raise error.IncorrectHeapType(self, 'ListHint', message="Invalid value for FrontEndHeapType ({:s})".format(self['FrontEndHeapType'].summary()), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8

            # Figure out what the proper size would be if we add
            # the size of the header and a value for rounding.
            size_and_header = size + blocksize + 7

            # Now with the total size, we can divide it by the blocksize
            # in order to get the BlockIndex.
            bi = math.trunc(math.floor(size_and_header / (1. * blocksize)))

            # Use the BlockIndex with the correct BlockList in order
            # to get the ListHint for the desired size.
            blocklist = self.HeapListLookup(bi)
            return blocklist.ListHint(bi)

        def Bucket(self, size):
            '''Find the correct Heap Bucket from the ListHint for the given ``size``'''
            entry = self.ListHint(size)

            # If our list entry is pointing to a FreeListBucket, then we need
            # to dereference the Blink pointer to get to the actual bucket.
            if isinstance(entry, FreeListBucket):
                if entry['Blink'].int() == 0:
                    raise error.NotFoundException(self, 'Bucket', message="Unable to find a Bucket for the requested size ({:#x})".format(size), entry=entry, size=size)
                return entry['Blink'].d.li

            # Otherwise this is a linked-list of heap chunks that will need to be walked.
            return entry

        class _FreeLists(parray.type):
            _object_, length = fpointer(_HEAP_CHUNK, 'ListEntry'), 128

        def FreeLists(self, size):
            freelists = self['FreeLists']
            if isinstance(freelists, self._FreeLists):
                listhints = self['FreeListsInUseUlong']
                raise error.InvalidHeapType(self, 'FreeLists', message='Unable to walk all the entries in the lookaside lists')

            # FIXME: properly walk through the BlocksIndex.ListHints to find the next entry
            #        that has its Flink set so that we can start closer to our goal.

            # walk through the freelists until we find one that will fit our requested size
            iterable = (item for item in freelists.walk() if size <= item['Header'].Size())
            result = next(iterable)
            return result

        class _Encoding(pstruct.type, versioned):
            _fields_ = [
                (lambda self: pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'ReservedForAlignment'),
                (dyn.array(pint.uint32_t, 2), 'Keys')
            ]

        def __PointerKeyEncoding(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN7:
                raise error.InvalidPlatformException(self, '__PointerKeyEncoding', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), expected=sdkddkver.NTDDI_WIN7)

            # If the "EncodeFlagMask" is set, then we'll need to store some
            # attributes to assist with decoding things.
            if self['EncodeFlagMask']:
                self.attributes['_HEAP_ENTRY_EncodeFlagMask'] = self['EncodeFlagMask'].li.int()
                self.attributes['_HEAP_ENTRY_Encoding'] = tuple(item.int() for item in self['Encoding'].li['Keys'])
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        class _FrontEndHeapUsageData(parray.type):
            _object_, length = USHORT, 0

        def __FrontEndHeapUsageData(self):
            def FrontEndHeapUsageDataArray(this):
                index = self['FrontEndHeapMaximumIndex'].li
                return dyn.clone(self._FrontEndHeapUsageData, length=index.int())
            return P(FrontEndHeapUsageDataArray)

        def __init__(self, **attrs):
            super(HEAP, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            integral = ULONGLONG if getattr(self, 'WIN64', False) else ULONG
            size_t = SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T
            f = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
                f.extend([
                    (HEAP_ENTRY, 'Entry'),

                    (HEAP_SIGNATURE, 'Signature'),
                    (ULONG, 'Flags'),
                    (ULONG, 'ForceFlags'),
                    (ULONG, 'VirtualMemoryThreshold'),
                    (integral, 'SegmentReserve'),
                    (integral, 'SegmentCommit'),
                    (integral, 'DeCommitFreeBlockThreshold'),
                    (integral, 'DeCommitTotalFreeThreshold'),
                    (integral, 'TotalFreeSize'),
                    (integral, 'MaximumAllocationSize'),
                    (USHORT, 'ProcessHeapsListIndex'),
                    (USHORT, 'HeaderValidateLength'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(HeaderValidateLength)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (USHORT, 'NextAvailableTagIndex'),
                    (USHORT, 'MaximumTagIndex'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(MaximumTagIndex)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),         # XXX: likely points to an array
                    (P(HEAP_UCR_SEGMENT), 'UCRSegments'),
                    (P(HEAP_UNCOMMMTTED_RANGE), 'UnusedUnCommittedRanges'),
                    (ULONG_PTR, 'AlignRound'),
                    (ULONG_PTR, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocdBlocks'),
                    (dyn.array(P(HEAP_SEGMENT), 64), 'Segments'),
                    (dyn.clone(ListsInUseUlong, length=4), 'FreeListsInUseUlong'),
                    (USHORT, 'FreeListsInUseTerminate'),
                    (USHORT, 'AllocatorBackTraceIndex'),
                    (ULONG, 'NonDedicatedListLength'),
                    (PVOID, 'LargeBlocksIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),     # FIXME: probably an array
                    (self._FreeLists, 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (PVOID, 'CommitRoutine'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (UCHAR, 'LastSegmentIndex'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (ULONG, 'Flags'),
                    (ULONG, 'ForceFlags'),
                    (ULONG, 'CompatibilityFlags'),
                    (ULONG, 'EncodeFlagMask'),
                    (HEAP._Encoding, 'Encoding'),
                    (self.__PointerKeyEncoding, 'PointerKey'),
                    (ULONG, 'Interceptor'),
                    (ULONG, 'VirtualMemoryThreshold'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (aligned, 'align(SegmentReserve)'), # FIXME: alignment or padding?
                    (size_t, 'SegmentReserve'),
                    (size_t, 'SegmentCommit'),
                    (size_t, 'DeCommitFreeBlockThreshold'),
                    (size_t, 'DeCommitTotalFreeThreshold'),
                    (size_t, 'TotalFreeSize'),
                    (size_t, 'MaximumAllocationSize'),
                    (USHORT, 'ProcessHeapsListIndex'),
                    (USHORT, 'HeaderValidateLength'),
                    (aligned, 'align(HeaderValidateCopy)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (USHORT, 'NextAvailableTagIndex'),
                    (USHORT, 'MaximumTagIndex'),
                    (aligned, 'align(TagEntries)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (ULONG_PTR, 'AlignRound'),
                    (ULONG_PTR, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_=['SegmentListEntry'], _object_=fpointer(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentList'),
                    (USHORT, 'AllocatorBackTraceIndex'),
                    (USHORT, 'FreeListInUseTerminate'),  # XXX: Is this for real?
                    (ULONG, 'NonDedicatedListLength'),
                    (P(HEAP_LIST_LOOKUP), 'BlocksIndex'),
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'UCRIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(_HEAP_CHUNK, 'ListEntry')), 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN10:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (ULONG, 'Flags'),
                    (ULONG, 'ForceFlags'),
                    (ULONG, 'CompatibilityFlags'),
                    (ULONG, 'EncodeFlagMask'),
                    (HEAP._Encoding, 'Encoding'),
                    (ULONG, 'Interceptor'),
                    (ULONG, 'VirtualMemoryThreshold'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (aligned, 'align(SegmentReserve)'), # FIXME: alignment or padding?
                    (size_t, 'SegmentReserve'),
                    (size_t, 'SegmentCommit'),
                    (size_t, 'DeCommitFreeBlockThreshold'),
                    (size_t, 'DeCommitTotalFreeThreshold'),
                    (size_t, 'TotalFreeSize'),
                    (size_t, 'MaximumAllocationSize'),
                    (USHORT, 'ProcessHeapsListIndex'),
                    (USHORT, 'HeaderValidateLength'),
                    (aligned, 'align(HeaderValidateCopy)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (USHORT, 'NextAvailableTagIndex'),
                    (USHORT, 'MaximumTagIndex'),
                    (aligned, 'align(TagEntries)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (ULONG_PTR, 'AlignRound'),
                    (ULONG_PTR, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocdBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_=['SegmentListEntry'], _object_=fpointer(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentList'),
                    (USHORT, 'AllocatorBackTraceIndex'),
                    (dyn.block(2), 'padding(AllocatorBackTraceIndex)'), # XXX
                    (ULONG, 'NonDedicatedListLength'),
                    (P(HEAP_LIST_LOOKUP), 'BlocksIndex'),
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'UCRIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(_HEAP_CHUNK, 'ListEntry')), 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (FrontEndHeap.Type, 'RequestedFrontEndHeapType'),

                    (aligned, 'align(FrontEndHeapUsageData)'),
                    (self.__FrontEndHeapUsageData, 'FrontEndHeapUsageData'),    # XXX: this pointer target doesn't seem right
                    (USHORT, 'FrontEndHeapMaximumIndex'),
                    (dyn.clone(ListsInUseBytes, length=129 if getattr(self, 'WIN64', False) else 257), 'FrontEndHeapStatusBitmap'),

                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                # XXX: win10
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (ULONG, 'Flags'),
                    (ULONG, 'ForceFlags'),
                    (ULONG, 'CompatibilityFlags'),
                    (ULONG, 'EncodeFlagMask'),
                    (HEAP._Encoding, 'Encoding'),
                    (ULONG, 'Interceptor'),
                    (ULONG, 'VirtualMemoryThreshold'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (aligned, 'align(SegmentReserve)'), # FIXME: alignment or padding?
                    (size_t, 'SegmentReserve'),
                    (size_t, 'SegmentCommit'),
                    (size_t, 'DeCommitFreeBlockThreshold'),
                    (size_t, 'DeCommitTotalFreeThreshold'),
                    (size_t, 'TotalFreeSize'),
                    (size_t, 'MaximumAllocationSize'),
                    (USHORT, 'ProcessHeapsListIndex'),
                    (USHORT, 'HeaderValidateLength'),
                    (aligned, 'align(HeaderValidateCopy)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (USHORT, 'NextAvailableTagIndex'),
                    (USHORT, 'MaximumTagIndex'),
                    (aligned, 'align(TagEntries)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (size_t, 'AlignRound'),
                    (size_t, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_=['SegmentListEntry'], _object_=fpointer(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentList'),
                    (ULONG, 'AllocatorBackTraceIndex'),
                    (ULONG, 'NonDedicatedListLength'),
                    (P(HEAP_LIST_LOOKUP), 'BlocksIndex'),
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'UCRIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(_HEAP_CHUNK, 'ListEntry')), 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),   # FIXME: this is encoded with something somewhere
                    (rtltypes.RTL_RUN_ONCE, 'StackTraceInitVar'),
                    (rtltypes.RTL_HEAP_MEMORY_LIMIT_DATA, 'CommitLimitData'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (FrontEndHeap.Type, 'RequestedFrontEndHeapType'),

                    (aligned, 'align(FrontEndHeapUsageData)'),
                    (self.__FrontEndHeapUsageData, 'FrontEndHeapUsageData'),    # XXX: this pointer target doesn't seem right
                    (USHORT, 'FrontEndHeapMaximumIndex'),
                    (dyn.clone(ListsInUseBytes, length=129 if getattr(self, 'WIN64', False) else 257), 'FrontEndHeapStatusBitmap'),

                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

    class HEAP_LIST_LOOKUP(pstruct.type, versioned):
        def __ListsInUseUlong(self):
            count = self.ListHintsCount()
            target = dyn.clone(ListsInUseUlong, length=count >> 5)
            return P(target)

        class _ListHints(parray.type):
            _object_, length = PVOID, 0

        def __ListHints(self):
            count, sentinel = self.ListHintsCount(), self['ListHead'].li
            ptr = fpointer(_HEAP_CHUNK, 'ListEntry')
            element = dyn.clone(FreeListBucket, _object_=ptr, _path_=['ListEntry'], _sentinel_=sentinel.int())
            target = dyn.clone(self._ListHints, _object_=element, length=count)
            return P(target)

        def __ListHints_WIN8(self):
            count, sentinel = self.ListHintsCount(), self['ListHead'].li
            ptr = fpointer(_HEAP_CHUNK, 'ListEntry')    # FIXME: we need to assign the sentinel address for these free chunks
            target = dyn.clone(self._ListHints, _object_=ptr, length=count)
            return P(target)

        def __init__(self, **attrs):
            super(HEAP_LIST_LOOKUP, self).__init__(**attrs)
            f = self._fields_ = []
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

            f.extend([
                (P(HEAP_LIST_LOOKUP), 'ExtendedLookup'),

                (ULONG, 'ArraySize'),
                (ULONG, 'ExtraItem'),                           # XXX: is this what causes the different type for ListHints?
                (ULONG, 'ItemCount'),
                (ULONG, 'OutOfRangeItems'),
                (ULONG, 'BaseIndex'),

                (aligned, 'align(ListHead)'),
                #(P(dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(_HEAP_CHUNK, 'ListEntry'))), 'ListHead'),
                #(P(dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(HEAP, 'FreeLists'))), 'ListHead'),
                (fpointer(HEAP, 'FreeLists'), 'ListHead'),      # FIXME: points to HEAP.FreeLists (used as sentinel address)
                (self.__ListsInUseUlong, 'ListsInUseUlong'),
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (self.__ListHints, 'ListHints'),
                ])
            else:
                f.extend([
                    (self.__ListHints_WIN8, 'ListHints'),
                ])
            return

        def ListHintsCount(self):
            '''Return the number of FreeLists entries within this structure'''
            return self['ArraySize'].li.int() - self['BaseIndex'].li.int()

        def ListHint(self, blockindex):
            '''Find the correct (recent) ListHint for the specified ``blockindex``'''
            res = blockindex - self['BaseIndex'].int()
            if 0 > res or self.ListHintsCount() < res:
                raise error.NdkAssertionError(self, 'ListHint', message="Requested BlockIndex is out of bounds : {:d} <= {:d} < {:d}".format(self['BaseIndex'].int(), blockindex, self['ArraySize'].int()))

            # First we'll check to see if the blockindex that the user gave us
            # is actually set in our "ListHints".
            freelist = self['ListsInUseUlong'].d.l
            hints = self['ListHints'].d.l
            if freelist.check(res):
                return hints[res]

            # Otherwise we'll just warn the user and return it anyways.
            logging.warning("{:s} : Returning ListHint[{:d}] despite ListsInUseUlong[{:d}] being unset".format(self.instance(), res, res))
            return hints[res]

        def enumerate(self):
            inuse, hints = (self[fld].d.li for fld in ['ListsInUseUlong', 'ListHints'])
            if inuse.bits() != len(hints):
                raise error.NdkAssertionError(self, 'ListHint', message="ListsInUseUlong ({:d}) is a different length than ListHints ({:d})".format(inuse.bits(), len(hints)))

            # Lazily walk through the "ListHints" yielding only the indices
            # that are set in the "ListInUseUlong" bitmap.
            for index, item in enumerate(hints):
                if inuse.check(index):
                    yield index, item
                continue
            return

        def iterate(self):
            for _, item in self.enumerate():
                yield item
            return

class ProcessHeapEntries(parray.type):
    _object_ = P(HEAP)

    def walk(self):
        for x in self:
            yield x.d
        return

if __name__ == '__main__':
    import sys
    import ptypes, ndk
    import ctypes
    def openprocess (pid):
        k32 = ctypes.WinDLL('kernel32.dll')
        res = k32.OpenProcess(0x30 | 0x0400, False, pid)
        return res

    def getcurrentprocess ():
        k32 = ctypes.WinDLL('kernel32.dll')
        return k32.GetCurrentProcess()

    def GetProcessBasicInformation (handle):
        nt = ctypes.WinDLL('ntdll.dll')
        class ProcessBasicInformation(ctypes.Structure):
            _fields_ = [('Reserved1', ctypes.c_uint32),
                        ('PebBaseAddress', ctypes.c_uint32),
                        ('Reserved2', ctypes.c_uint32 * 2),
                        ('UniqueProcessId', ctypes.c_uint32),
                        ('Reserved3', ctypes.c_uint32)]

        pbi = ProcessBasicInformation()
        res = nt.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
        return pbi

    # grab process handle
    if len(sys.argv) > 1:
        pid = builtins.int(sys.argv[1])
        print("opening process {:d}".format(pid))
        handle = openprocess(pid)
    else:
        handle = getcurrentprocess()
        print('using current process')
    ptypes.setsource(ptypes.provider.WindowsProcessHandle(handle))

    # grab peb
    import ndk
    pebaddress = GetProcessBasicInformation(handle).PebBaseAddress
    z = ndk.PEB(offset=pebaddress).l

    # grab heap
    if len(sys.argv) > 2:
        heaphandle = eval(sys.argv[2])
        for x in z['ProcessHeaps'].d.l:
            print(hex(x.int()), hex(heaphandle))
            if x.int() == heaphandle:
                b = x
                break
            continue
        if x.int() != heaphandle:
            raise ValueError(hex(heaphandle))
    else:
        b = z['ProcessHeap'].d.l

    a = ndk.heaptypes.HEAP(offset=b.getoffset())
    a=a.l
#    print(a.l)
#    b = a['Segment']
#    print(a['BlocksIndex'])
#    print(a['UCRIndex'])
#    print(list(b.walk()))

    c = a['FreeLists']

#    list(c.walk())
 #   x = c['Flink'].d.l

 #   print(x['Value']['a'])
 #   x =  x['Entry']['Flink'].d.l
#    print([x for x in c.walk()])
#    print(a['BlocksIndex'])

#    print(a['FrontEndHeap'].d.l)
#
#    print(a['CommitRoutine'])

#    print(c['Flink'].d.l)

#    print(list(c.walk()))
#    print(c['Flink'].d.l['Flink'].d.l['Flink'].d.l)
#    d = [x for x in c.walk()]
#    print(help(d[1]))
