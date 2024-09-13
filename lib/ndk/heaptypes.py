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
    _values_ = [
        ('Segment', 0xffeeffee),
        ('Heap', 0xeeffeeff),
        ('SegmentHeap', 0xddeeddee),
        ('UserBlocks', 0xf0e0d0c0),
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

            # First check for any attributes on our owner HEAP
            owner = self.getparent(HEAP)
            if not hasattr(owner, 'RtlpHeapKey'):
                logging.warning("Failure while attempting to determine address of {:s}".format('ntdll!RtlpHeapKey'))
                return 0

            # Found one that we can use, so use it.
            logging.info("Using address of {:s} ({:#x}) from attribute {:s}.{:s}".format('ntdll!RtlpHeapKey', owner.RtlpHeapKey, owner.instance(), 'RtlpHeapKey'))
            RtlpHeapKey = owner.RtlpHeapKey

        # We can simply use the debugger to evaluate the expression for our key
        else:
            RtlpHeapKey = self.source.expr('ntdll!RtlpHeapKey')

        t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
        res = self.new(t, offset=RtlpHeapKey)
        return res.l.int()

    def __RtlpLFHKey__(self):
        '''Try and resolve ntdll!RtlpLFHKey using the debugger or an attribute attached to the HEAP.'''
        if not isinstance(self.source, ptypes.provider.debuggerbase):

            # First check for any attributes on our owner HEAP
            owner = self.getparent(HEAP)
            if not hasattr(owner, 'RtlpLFHKey'):
                logging.warning("Failure while attempting to determine address of {:s}".format('ntdll!RtlpLFHKey'))
                return 0

            # Found one that we can use, so use it.
            logging.info("Using address of {:s} ({:#x}) from attribute {:s}.{:s}".format('ntdll!RtlpLFHKey', owner.RtlpLFHKey, owner.instance(), 'RtlpLFHKey'))
            RtlpLFHKey = owner.RtlpLFHKey

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
        def AffinityQ(self):
            flags = self['BucketFlags']
            return True if flags['UseAffinity'] else False
        def DebugQ(self):
            flags = self['BucketFlags']
            return True if flags['DebugFlags'] else False

    class HEAP_BUCKET_ARRAY(parray.type):
        '''This is a synthetic array type used for providing utility methods to any child definitions.'''
        _object_, length = HEAP_BUCKET, 0

        def enumerate(self):
            '''Yield the number of units and the bucket that contains it for each bucket in the array.'''
            for item in self:
                units = item['BlockUnits']
                yield units.int(), item
            return

        def ByUnits(self, units):
            '''Search through all of the buckets for the smallest one that can contain the requested number of units.'''
            for item in self:
                if units <= item['BlockUnits'].int():
                    return item
                continue
            raise error.NotFoundException(self, 'ByUnits', message="Unable to find a Bucket for the requested number of units ({:#x})".format(units))

    class HEAP_ENTRY_EXTRA(pstruct.type):
        _fields_ = [
            (USHORT, 'AllocatorBacktraceIndex'),
            (USHORT, 'TagIndex'),
            (lambda self: dyn.padding(8 if getattr(self, 'WIN64', False) else 4), 'padding(Settable)'),
            (lambda self: SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'Settable'),
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
        '''This is a general HEAP_ENTRY prior to any sort of encoding/decoding.'''
        class _UnusedBytes(pbinary.flags):
            class _Unused(pbinary.enum):
                length, _values_ = 6, [
                    ('Chunk', 0),
                    ('Segment', 1),
                    ('Uncommitted', 3), # Uncommitted?
                    ('LargeChunk', 4),  # VirtualBlocks
                    ('Linked', 5),      # linked to different HEAP_ENTRY (EntryOffset ^ Encoding.EntryOffset)
                    ('Special', 0x3f)   # if >= 0x3f, then PreviousBlockPrivateData (64-bit) or EntryOffset (32-bit) contains the unusedBytes (BlockSize - size) length
                ]

            _fields_ = [
                (1, 'AllocatedByFrontend'),
                (1, 'Extra'),           # Prior to the last refactor that broke things, this bit was
                (_Unused, 'Count'),     # used when the previous chunk's unused was larger than 0x3f
            ]

            def FrontEndQ(self):
                return True if self['AllocatedByFrontend'] else False

            def BackEndQ(self):
                return not self.FrontEndQ()

            def BusyQ(self):
                if self.FrontEndQ():
                    result = self['Count']
                    return result > 0
                return True if self['Count'] else False

            def FreeQ(self):
                return not self.BusyQ()

            def UnusedBytes(self):
                '''Return the number of unused bytes within the header.'''
                if self.FrontEndQ():
                    return self['Count']
                return self['Count']

            def Type(self, query):
                field = self.field('Count')
                return self.BackEndQ() and not self['Extra'] and field[query]

            def summary(self):
                if self.FrontEndQ():
                    return 'FE {:s} : UnusedBytes={:+#x}'.format('BUSY' if self.BusyQ() else 'FREE', self.UnusedBytes())

                # If we're using one of the defined constants, then eturn the type.
                if self['Count'] < 6:
                    type = self.field('Count')
                    return type.str()

                # Otherwise this is just a backend chunk with some unused bytes.
                return "BE : UnusedBytes={:+#x}{:s}".format(self['Count'], " Extra={:d}".format(self['Extra']) if self['Extra'] else '')

        def __init__(self, **attrs):
            super(HEAP_ENTRY, self).__init__(**attrs)
            self._fields_ = [
                (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData')
            ]

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
                self._fields_.extend([
                   (USHORT, 'Size'),
                   (USHORT, 'PreviousSize'),
                   (UCHAR, 'SmallTagIndex'),
                   (HEAP_ENTRY_, 'Flags'),
                   (UCHAR, 'UnusedBytes'),
                   (UCHAR, 'SegmentIndex'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                self._fields_.extend([
                    (USHORT, 'Size'),
                    (HEAP_ENTRY_, 'Flags'),             # XXX: this can be encoded in win10 if tracing is enabled
                    (UCHAR, 'SmallTagIndex'),
                    (USHORT, 'PreviousSize'),           # XXX: is this the right name for this field? it can also store the backtrace index...
                    (UCHAR, 'EntryOffset'),
                    (HEAP_ENTRY._UnusedBytes, 'UnusedBytes'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            return

        def FrontEndQ(self):
            return self['UnusedBytes'].FrontEndQ()

        def Type(self, query):
            return self['UnusedBytes'].Type(query)

        def LinkedQ(self):
            return self.Type('Linked')

        def Size(self):
            '''Return the number of units within the "Size" field.'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            return blocksize * self['Size'].int()

        def PreviousSize(self):
            '''Return the number of units within the "PreviousSize" field.'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            return blocksize * self['PreviousSize'].int()

        def summary(self):
            unused = self['UnusedBytes']
            if self.FrontEndQ():
                return '(FE) {:s} : UnusedBytes={:+#x}'.format('BUSY' if unused.BusyQ() else 'FREE', unused.UnusedBytes())
            type = unused.field('Count')

            # If it's a backend header, then check if it's a type
            # that doesn't depend on HEAP_ENTRY.Flags.
            if type.int() < 6:
                available, description = '', type.str()
                return "({:s}) : Size={:+#x} PreviousSize={:+#x} Flags={:s}".format(description, self['Size'].int(), -self['PreviousSize'].int(), self['Flags'].summary())

            # Otherwise it's a backend header that uses HEAP_ENTRY.UnusedBytes.
            available, description = 'BUSY' if unused.BusyQ() else 'FREE', type.byvalue(0)
            return "({:s}) UnusedBytes={:+#x} : Size={:+#x} PreviousSize={:+#x} Flags={:s}".format(description, unused.UnusedBytes(), self['Size'].int(), -self['PreviousSize'].int(), self['Flags'].summary())

    class HEAP_UNPACKED_ENTRY(pstruct.type):
        _fields_ = [
            (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData'),
            (USHORT, 'Size'),           # SubSegmentCode: checksum'd
            (HEAP_ENTRY_, 'Flags'),     # SubSegmentCode: checksum'd
            (UCHAR, 'SmallTagIndex'),   # SubSegmentCode: checksum'd

            (USHORT, 'PrevousSize'),
            (UCHAR, 'SegmentOffset'),
            (HEAP_ENTRY._UnusedBytes, 'UnusedBytes'),
        ]

    class HEAP_EXTENDED_ENTRY(pstruct.type):
        _fields_ = [
            (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'Reserved'),
            (USHORT, 'FunctionIndex'),
            (USHORT, 'ContextValue'),
            (USHORT, 'UnusedBytesLength'),
            (UCHAR, 'EntryOffset'),
            (UCHAR, 'ExtendedBlockSignature'),
        ]

    class _HEAP_ENTRY(ptype.encoded_t):
        '''
        This is an internal version of _HEAP_ENTRY that supports encoding/decoding
        the HEAP_ENTRY from either the frontend or the backend.
        '''
        _value_ = HEAP_ENTRY

        ### These methods implement all of the necessary ptypes methods that will
        ### properly switch between either the frontend version of the backend
        ### version of the HEAP_ENTRY.

        def FrontEndQ(self):
            header = self.object
            return header.FrontEndQ()

        def BackEndQ(self):
            # Back-to-Front(242)
            header = self.object
            return not header.FrontEndQ()

        def _object_(self):
            header = self.object
            if header.FrontEndQ():
                if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                    return self.__FRONTEND_ENTRY__
                return self.__FRONTEND_ENTRY8__
            return HEAP_ENTRY

        def encode(self, object, **attrs):
            header = self.object
            if header.LinkedQ():
                # FIXME: we wouldn't be able to encode anything since our chunk
                #        header is elsewhere.
                offset = self.getoffset() - header['SegmentOffset'] * header.size()
                raise error.IncorrectChunkType(self, 'encode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)

            # If this is a front-end chunk then use the front-end encoder.
            if header.FrontEndQ():
                if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                    return self.__frontend_encode(object, **attrs)
                return self.__frontend_encode8(object, **attrs)
            return self.__backend_encode(object, **attrs)

        def decode(self, object, **attrs):
            header = self.object
            if header.LinkedQ():
                # FIXME: we shouldn't need to decode anything since our chunk
                #        header is elsewhere.
                offset = self.getoffset() - header['SegmentOffset'] * header.size()
                raise error.IncorrectChunkType(self, 'decode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)

            # If this is a front-end chunk, then use the front-end decoder.
            if header.FrontEndQ():
                if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                    return self.__frontend_decode(object, **attrs)
                return self.__frontend_decode8(object, **attrs)
            return self.__backend_decode(object, **attrs)

        def summary(self):
            header = self.object
            if header.initializedQ():
                return self.d.li.summary()
            return super(_HEAP_ENTRY, self).summary()

        def properties(self):
            result = super(_HEAP_ENTRY, self).properties()
            if self.BackEndQ():
                result['CheckSumOk'] = self.CheckSumQ()
            return result

        ## Forward everything to the decoded object underneath our unencoded header.
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

        def __OwnerHeap(self):
            '''Return and cache the HEAP that this HEAP_ENTRY belongs to.'''
            result = self.__HEAP__ if hasattr(self, '__HEAP__') else self.getparent(HEAP)
            self.__HEAP__ = result
            return result

        ### Decoding for a chunk used by the backend.
        class __BACKEND_VIEW__(pstruct.type):
            '''
            This type is used strictly for encoding/decoding and is used when
            casting the backing type.
            '''
            _fields_ = [
                (lambda self: pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'Unencoded'),
                (dyn.array(pint.uint32_t, 2), 'Encoded'),
            ]
            def CheckSum(self):
                '''Calculate checksum (a^9^8 == b)'''
                encoded = self['Encoded']
                data = bytearray(encoded.serialize())
                return functools.reduce(operator.xor, data[:3], 0)

            def CheckSumQ(self):
                '''Return if the checksum passes or not.'''
                encoded = self['Encoded']
                data = bytearray(encoded.serialize())
                chk = functools.reduce(operator.xor, data[:3], 0)
                return chk == data[3]

        def __backend_cache_Encoding(self):
            OwnerHeap = self.__OwnerHeap()
            if hasattr(self, '_HEAP_ENTRY_Encoding'):
                result = self._HEAP_ENTRY_Encoding
            else:
                encoding = OwnerHeap['Encoding'].li
                result = self._HEAP_ENTRY_Encoding = OwnerHeap['EncodeFlagMask'].li.int(), tuple(item.int() for item in encoding['Keys'])
            return result

        def __backend_encode(self, object, **attrs):
            view = object.cast(self.__BACKEND_VIEW__)
            unused = object['UnusedBytes']

            # Fetch some cached attributes...
            OwnerHeap = self.__OwnerHeap()
            EncodeFlagMask, Encoding = self.__backend_cache_Encoding()

            # If there's no EncodeFlagMask, then we can just pass-it-through.
            if not EncodeFlagMask:
                return super(_HEAP_ENTRY, self).encode(view)

            # If the type in "UnusedBytes" is "Segment", "Chunk", "Uncommitted", or
            # UnusedBytes is larger than 5 then we need to use both keys when encoding:
            if any(unused.Type(name) for name in ['Segment', 'Chunk', 'Uncommitted']) or unused.int() > 5:
                values = [item.int() ^ key for item, key in zip(view['Encoded'], Encoding)]
                [ item.set(value) for item, value in zip(view['Encoded'], values) ]

            # Otherwise the first key should be enough.
            else:
                result = view['Encoded'][0].int() ^ Encoding[0]
                view['Encoded'][0].set(result)

            # Encode our view into a block so that we can complete the encoding.
            encoded = ptype.block().set(view.serialize())
            return super(_HEAP_ENTRY, self).encode(encoded)

        def __backend_decode(self, object, **attrs):
            view = object.cast(self.__BACKEND_VIEW__)
            unused = object['UnusedBytes']

            # Fetch the attributes that were cached...
            OwnerHeap = self.__OwnerHeap()
            EncodeFlagMask, Encoding = self.__backend_cache_Encoding()

            # Without an EncodeFlagMask, there is no decoding necssary.
            if not EncodeFlagMask:
                return super(_HEAP_ENTRY, self).encode(view)

            # If the type in "UnusedBytes" is "Segment", "Chunk", "Uncommitted", or it
            # has an UnusedBytes larger than 5 then use both keys for decoding the entry.
            if any(unused.Type(name) for name in ['Segment', 'Chunk', 'Uncommitted']) or unused.int() > 5:
                values = [item.int() ^ key for item, key in zip(view['Encoded'], Encoding)]
                [ item.set(value) for item, value in zip(view['Encoded'], values) ]

            # Everything else requires us to use only the first key.
            else:
                result = view['Encoded'][0].int() ^ Encoding[0]
                view['Encoded'][0].set(result)

            # Assign our decoded view into a block and complete the decoding.
            decoded = ptype.block().set(view.serialize())
            return super(_HEAP_ENTRY, self).decode(decoded)

        ### HEAP_ENTRY that's used for a frontend chunk
        class __FRONTEND_ENTRY__(pstruct.type):
            '''HEAP_ENTRY after decoding'''
            _fields_ = [
                (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData'),
                (lambda self: dyn.clone(PHEAP_SUBSEGMENT, _value_=UINT32), 'SubSegment'),
                (USHORT, 'Unknown'),     # seems to be diff on 32-bit?
                (UCHAR, 'EntryOffset'),
                (HEAP_ENTRY._UnusedBytes, 'UnusedBytes'),
            ]

            def Segment(self, reload=False):
                '''Dereference the HEAP_SUBSEGMENT that is encoded within the header.'''
                return self['SubSegment'].d

            def UserBlocks(self, reload=False):
                '''Instantiate a HEAP_USERDATA_HEADER using the "EntryOffset" that is encoded within the header.'''
                segment = self['SubSegment'].d.l if reload else self['SubSegment'].d.li
                return segment['UserBlocks'].d

            def summary(self):
                items, unused = [], self['UnusedBytes']
                items.append("(FE) {:s} UnusedBytes={:+#x}".format('BUSY', unused.UnusedBytes()) if unused.BusyQ() else "(FE) {:s}".format('FREE'))
                items.append("SubSegment=*{:#x}".format(self['SubSegment'].int()))
                if any(self[fld].int() for fld in ['EntryOffset', 'Unknown']):
                    items.append(' '.join("{:s}={:#0{:d}x}".format(fld, self[fld].int(), 2 + 2 * self[fld].size()) for fld in ['EntryOffset', 'Unknown']))
                return ' : '.join(items)

        class __FRONTEND_VIEW__(pstruct.type):
            '''
            This type is used strictly for encoding/decoding and is used when
            casting the backing type.
            '''
            def __init__(self, **attrs):
                super(_HEAP_ENTRY.__FRONTEND_VIEW__, self).__init__(**attrs)
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

        def __frontend_cache_LFHKey(self):
            if hasattr(self, '_HEAP_ENTRY_LFHKey'):
                result = self._HEAP_ENTRY_LFHKey
            else:
                result = self._HEAP_ENTRY_LFHKey = __RtlpLFHKey__(self)
            return result

        def __frontend_encode(self, object, **attrs):
            view = object.cast(self.__FRONTEND_VIEW__)

            # Fetch some cached attributes.
            OwnerHeap, LFHKey = self.__OwnerHeap(), self.__frontend_cache_LFHKey()

            # Now to encode our 64-bit header
            if getattr(self, 'WIN64', False):
                dn = self.getoffset()
                dn ^= OwnerHeap.getoffset()
                dn >>= 4
                dn ^= view.EncodedValue()
                dn ^= LFHKey
                dn <<= 4
                dn |= view.EncodedUntouchedValue()

            # Encode the 32-bit header
            else:
                dn = view.EncodedValue()
                dn = self.getoffset() >> 3
                dn ^= LFHKey
                dn ^= OwnerHeap.getoffset()

            result = view.copy().set(Encoded=dn)
            return super(_HEAP_ENTRY, self).encode(result)

        def __frontend_decode(self, object, **attrs):
            view = object.cast(self.__FRONTEND_VIEW__)

            # Fetch some cached attributes.
            OwnerHeap, LFHKey = self.__OwnerHeap(), self.__frontend_cache_LFHKey()

            # Now we can decode our 64-bit header
            if getattr(self, 'WIN64', False):
                dn = self.getoffset()
                dn ^= OwnerHeap.getoffset()
                dn >>= 4
                dn ^= view.EncodedValue()
                dn ^= LFHKey
                dn <<= 4
                dn |= view.EncodedUntouchedValue()

            # Decode the 32-bit header
            else:
                dn = view.EncodedValue()
                dn ^= self.getoffset() >> 3
                dn ^= LFHKey
                dn ^= OwnerHeap.getoffset()
                dn |= view.EncodedUntouchedValue()

            res = view.copy().set(Encoded=dn)
            return super(_HEAP_ENTRY, self).decode(res)

        class __FRONTEND_ENTRY8__(pstruct.type):
            '''HEAP_ENTRY after decoding on win8'''
            _fields_ = [
                (lambda self: dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'PreviousBlockPrivateData'),
                (lambda self: dyn.clone(PENTRY_OFFSET, _value_=ULONG), 'EntryOffset'),  # distance from userdataheader (checksum?)
                                                                                        # if this is free'd, this seems to get xor'd?
                (UCHAR, 'PreviousSize'),                                                # FF
                (USHORT, 'SmallTagIndex'),                                              # block index
                (HEAP_ENTRY._UnusedBytes, 'UnusedBytes'),                               # FF
            ]

            def UserBlocks(self, reload=False):
                '''Instantiate a HEAP_USERDATA_HEADER using the "EntryOffset" that is encoded within the header.'''
                return self['EntryOffset'].d

            def Segment(self, reload=False):
                '''Dereference the HEAP_SUBSEGMENT from the HEAP_USERDATA_HEADER that is encoded within the header.'''
                ub = self['EntryOffset'].d.l if reload else self['EntryOffset'].d.li
                return ub['SubSegment'].d

            def summary(self):
                items, unused = [], self['UnusedBytes']
                items.append("(FE) {:s} UnusedBytes={:+#x}".format('BUSY', unused.UnusedBytes()) if unused.BusyQ() else "(FE) {:s}".format('FREE'))
                items.append("SmallTagIndex={:d} EntryOffset={:+#x}".format(self['SmallTagIndex'].int(), self['EntryOffset'].int()))
                if self['PreviousSize'].int():
                    items.append("PreviousSize={:#0{:d}x}".format(self['PreviousSize'].int(), 2 + 2 * self['PreviousSize'].size()))
                return ' : '.join(items)

        class __FRONTEND_VIEW8__(__FRONTEND_VIEW__):
            '''
            This type is used strictly for encoding/decoding and is used when
            casting the backing type.
            '''
            def EncodedValue(self):
                return self['Encoded'].int() & 0xffffffff

            def EncodedUntouchedValue(self):
                return self['Encoded'].int() & ~0xffffffff

        def __frontend_encode8(self, object, **attrs):
            view = object.cast(self.__FRONTEND_VIEW8__)

            # Fetch some cached attributes.
            OwnerHeap, LFHKey = self.__OwnerHeap(), self.__frontend_cache_LFHKey()

            # Now to encode our first 32-bits.
            if getattr(self, 'WIN64', False):
                dn = OwnerHeap.getoffset() ^ LFHKey
                dn ^= self.getoffset() >> 4
                dn &= 0xffffffff
                dn ^= view.EncodedValue() << 0xc

            # Encode the 32-bit entry offset.
            else:
                dn = OwnerHeap.getoffset() ^ LFHKey
                dn ^= self.getoffset() >> 3
                dn ^= view.EncodedValue() << 0xd

            result = view.copy().set(Encoded=dn | view.EncodedUntouchedValue())
            return super(_HEAP_ENTRY, self).encode(result)

        def __frontend_decode8(self, object, **attrs):
            view = object.cast(self.__FRONTEND_VIEW8__)

            # Fetch some cached attributes.
            OwnerHeap, LFHKey = self.__OwnerHeap(), self.__frontend_cache_LFHKey()

            # Decode the 32-bit dword from the entry.
            if getattr(self, 'WIN64', False):
                dn = OwnerHeap.getoffset() ^ LFHKey
                dn ^= self.getoffset() >> 4
                dn &= 0xffffffff
                dn ^= view.EncodedValue()
                dn >>= 0xc

            # Decode the 32-bit header from the entry.
            else:
                dn = OwnerHeap.getoffset() ^ LFHKey
                dn ^= self.getoffset() >> 3
                dn ^= view.EncodedValue()
                dn >>= 0xd

            result = view.copy().set(Encoded=dn | view.EncodedUntouchedValue())
            return super(_HEAP_ENTRY, self).decode(result)

        ### Utility functions
        def BusyQ(self):
            '''Returns whether the chunk (decoded) is in use or not'''
            unused = self.object['UnusedBytes']

            # If we're using a frontend chunk, then just check its unused bytes.
            if self.FrontEndQ():
                return unused.BusyQ()

            # If we're using a segment type, then check the actual decoded flags.
            if unused.Type('Segment'):
                decoded = self.d.li
                return True if decoded['Flags']['BUSY'] else False

            # Otherwise we just trust what the original HEAP_ENTRY would return.
            return unused.BusyQ()

        def FreeQ(self):
            '''Returns whether the chunk (decoded) is free or not'''
            return not self.BusyQ()

        def CheckSum(self):
            '''Return the CheckSum for the current header.'''
            header = self.object
            if not header.FrontEndQ():
                decoded = self.d.li
                view = decoded.cast(self.__BACKEND_VIEW__)
                return view.CheckSum()
            raise error.IncorrectChunkType(self, 'CheckSum', message='Unable to calculate the checksum for a chunk belonging to the frontend allocator.')

        def CheckSumQ(self):
            '''Return whether the checksum for the chunk is valid.'''
            header = self.object
            if not self.FrontEndQ():
                decoded = self.d.li
                view = decoded.cast(self.__BACKEND_VIEW__)
                return view.CheckSumQ()
            return False

        def Size(self):
            '''Return the size of the chunk according to the _HEAP_ENTRY.'''

            # If our header is pointing to a frontend chunk, then first check
            # if we've cached the HEAP_SUBSEGMENT.
            if self.FrontEndQ():
                if hasattr(self, '__SubSegment__'):
                    segment = self.__SubSegment__

                # If we haven't, then that's okay because we can decode it from the header.
                else:
                    decoded = self.d.li
                    segment = decoded.Segment()

                # Load the segment and then calculate the blocksize.
                loaded = segment.li
                return loaded['BlockSize'].int() * (0x10 if getattr(self, 'WIN64', False) else 8)

            # Otherwise it's a backend chunk and we can decode it out of the header.
            decoded = self.d.li
            return decoded.Size()

        def PreviousSize(self):
            '''Return the previous size of the chunk according to the _HEAP_ENTRY.'''
            if self.FrontEndQ():
                raise error.IncorrectChunkType(self, 'CheckSum', message='Unable to return the previous size for a chunk belonging to the frontend allocator.')

            # Decode the header and extract the "PreviousSize" field.
            decoded = self.d.li
            return decoded.PreviousSize()

        def FreeListQ(self):
            '''Return whether this heapentry contains a freelist entry in its contents.'''
            return False if self.FrontEndQ() else self.FreeQ()

        def UnCommittedQ(self):
            '''Return whether this chunk is a backend chunk and its memory is potentially uncommitted.'''
            if self.FreeListQ():
                flags = self.d['Flags']
                return True if flags['VIRTUAL_ALLOC'] else False
            return False

        def FreeEntryOffsetQ(self):
            '''Return whether this chunk contains a free-entry offset in its contents.'''
            header = self.object

            # The "FreeEntryOffset" only exists on versions prior to Windows 8, so
            # verify the version and return if it doesn't correspond.
            if sdkddkver.NTDDI_WIN7 < sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION):
                return False

            # All we need to do here is check that we're using the frontend header
            # and that the "UnusedBytes" field says that the chunk is busy.
            if header.FrontEndQ():
                return not header['UnusedBytes'].BusyQ()
            return False

        def Segment(self, reload=False):
            '''Return the HEAP_SUBSEGMENT that is encoded within the _HEAP_ENTRY.'''
            header = self.object
            if not header.FrontEndQ():
                raise error.IncorrectChunkType(self, 'Segment', message='Unable to decode the HEAP_SUBSEGMENT from a non-frontend chunk.', FrontEndQ=header.FrontEndQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            decoded = self.d.l if reload else self.d.li
            return decoded.Segment(reload=reload)

        def UserBlocks(self, reload=False):
            '''Return the HEAP_USERDATA_HEADER that is encoded within the _HEAP_ENTRY.'''
            header = self.object
            if not header.FrontEndQ():
                raise error.IncorrectChunkType(self, 'UserBlocks', message='Unable to decode the HEAP_USERDATA_HEADER from a non-frontend chunk.', FrontEndQ=header.FrontEndQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            decoded = self.d.l if reload else self.d.li
            return decoded.UserBlocks(reload=reload)

    class ENCODED_POINTER(PVOID):
        '''
        This is a pointer that's encoded/decoded with ntdll!RtlpHeapKey and as
        such can be used to dereference/reference things with a tweaked pointer.
        '''
        def __HeapPointerKey(self):
            heap = self.__HEAP__ if hasattr(self, '__HEAP__') else self.getparent(HEAP)
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

    class _HEAP_CHUNK_LARGE(ptype.block):
        '''
        This is an internal definition that isn't defined by Microsoft, but is
        intended to distinguish extremely large chunks such as those that are
        allocated with HEAP_ENTRY_VIRTUAL_ALLOC.
        '''
        length = 0

    class _HEAP_CHUNK(pstruct.type):
        '''
        This is an internal definition that isn't defined by Microsoft, but is
        intended to distinguish chunks that exist in either the frontend or the
        backend heap.
        '''
        def __ListEntry(self):
            '''Return the "ListEntry" field if the chunk is free and in the backend.'''
            header = self['Header'].li

            # If the _HEAP_ENTRY tells us that this chunk includes a ListEntry
            # meaning it's a backend chunk and free then return one.
            if header.FreeListQ():
                return dyn.clone(LIST_ENTRY, _object_=fpointer(self.__class__, 'ListEntry'), _path_=['ListEntry'])
            return ptype.undefined

        def __ChunkFreeEntryOffset(self):
            '''Return the "ChunkFreeEntryOffset" field if the chunk is supposed to contain it.'''
            header = self['Header'].li

            # If the _HEAP_ENTRY tells us that this chunk includes a
            # 16-bit FreeEntryOffset then include it within our fields.
            return pint.uint16_t if header.FreeEntryOffsetQ() else pint.uint_t

        def __Data(self):
            header = self['Header'].li
            size = header.Size()

            # If the chunk is uncommitted then use a chunk that doesn't load
            # its contents unless it's explicitly decoded. Otherwise a regular
            # dynamic block should be fine since the contents are committed.
            res = sum(self[fld].li.size() for fld in ['Header', 'ListEntry', 'ChunkFreeEntryOffset'])
            if header.UnCommittedQ():
                return dyn.clone(HEAP_BLOCK_UNCOMMITTED, length=max(0, size - res))
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

        def nextfree(self):
            '''Walk to the next entry in the free-list (recent)'''
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.IncorrectChunkType(self, 'nextfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))

            # If we have a free list entry, then follow its "Flink" to the next one.
            if header.FreeListQ():
                link = self['ListEntry']
                return link['Flink'].d.l

            # Otherwise, just raise an exception.
            raise error.IncorrectChunkType(self, 'nextfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))

        def previousfree(self):
            '''Moonwalk to the previous entry in the free-list (recent)'''
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.IncorrectChunkType(self, 'previousfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            decoded = header.d.li

            # If we have a free list entry, then follow its "Blink" to the next one.
            if header.FreeListQ():
                link = self['ListEntry']
                return link['Blink'].d.l

            # Otherwise, just raise an exception.
            raise error.IncorrectChunkType(self, 'previousfree', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
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
                    (USHORT, 'DoubleCount'),
                    (USHORT, 'Increment'),
                    (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'Padding'),
                ]
                def get(self):
                    integer = self.cast(pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t)
                    return integer.int()

                def FrontEndQ(self):
                    '''Return whether the counters will result in the frontend heap being used.'''

                    # First check if the DoubleCount has its lowest bit set.
                    if self['DoubleCount'].int() & 1:
                        return True

                    # Otherwise check if the Increment counter is larger than 0x1000.
                    return self['Increment'].int() >= 0x1000 and self['DoubleCount'].int()

            _value_ = _HeapBucketCounter
            _object_ = HEAP_BUCKET

            def decode(self, object, **attrs):
                result = object.cast(pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t)

                # If the low-bit is set, then we just need to mask it away before decoding.
                if result.int() & 1:
                    result.set(result.int() & ~1)
                    return super(FreeListBucket._HeapBucketLink, self).decode(result, **attrs)

                # Otherwise this is not a pointer that can be decoded.
                result.set(result.int() & ~0)
                raise error.InvalidHeapType(self, 'decode', message="Address {:#x} is not a valid HEAP_BUCKET".format(result.int()))

            def FrontEndQ(self):
                object = self.object
                return object.FrontEndQ()

            def BackEndQ(self):
                return not self.FrontEndQ()

            def Count(self):
                if self.BackEndQ():
                    res = self.object['DoubleCount'].int()
                    return res // 2
                return None

            def summary(self):
                object = self.object
                if object.FrontEndQ():
                    integer = object.get()
                    return "(FRONTEND) {:#x} -> *{:#x}".format(integer, integer & ~1)

                # Otherwise it's the backend and we need to display the counters.
                return "(BACKEND) Increment={:#x} DoubleCount={:#x}".format(object['Increment'].int(), object['DoubleCount'].int())

            def details(self):
                if self.FrontEndQ():
                    return self.summary()

                # Otherwise this is a structure and we need to place it at the right address.
                result = self.object.copy(offset=self.getoffset())
                return result.details()
            repr = details

        _fields_ = [
            (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Flink'),          # FIXME: we should be able to calculate the sentinel for this list if we're attached to HEAP_LIST_LOOKUP
            (_HeapBucketLink, 'Blink'),
        ]

        def Bucket(self):
            if self['Blink'].FrontEndQ():
                return self['Blink'].d
            raise error.IncorrectChunkType(self, 'Bucket', message="Unable to return bucket due to entry not having yet been promoted to a frontend allocator ({:d} allocations).".format(self['Blink'].Count()))

        def FreeChunk(self):
            '''Return the first free heap chunk within the bucket.'''
            if self['Flink'].int():
                return self['Flink'].d
            raise error.NotFoundException(self, 'Bucket', message="No available chunks were pointed to by this particular bucket.".format(offset, _HEAP_ENTRY.typename()))

        def Count(self):
            '''Return the number of backend allocations that were found in the FreeListBucket or None if it's pointing to a HEAP_BUCKET.'''
            return self['Blink'].Count()
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
        def summary(self):
            result = self.bitmap()
            return "({:#x}, {:d}) ...{:d} bits set...".format(*(F(result) for F in [bitmap.int, bitmap.size, bitmap.hamming]))

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
        _value_, _object_ = ULONG, HEAP_USERDATA_OFFSETS

        def __cache_lfheap(self):
            if hasattr(self, '_LFH_HEAP'):
                return self._LFH_HEAP

            # First try looking for the LFH_HEAP in our parents.
            try:
                result = self.getparent(LFH_HEAP)

            # If we couldn't find it in our parents, then we'll start
            # by grabbing the HEAP_SUBSEGMENT from our parent type.
            except ptypes.error.ItemNotFoundError:
                result = self.getparent(HEAP_USERDATA_HEADER)
                ss = result['SubSegment'].d.li

                # Now from this we can grab the HEAP_LOCAL_SEGMENT_INFO and
                # then from that dereference the HEAP_LOCAL_DATA. Afterwards,
                # the LFH_HEAP is just another dereference away.
                si = ss['LocalInfo'].d.li
                local = si['LocalData'].d.li
                result = local['LowFragHeap'].d.li

            # Now we can cache it to avoid having to do that again.
            self._LFH_HEAP = result
            return result

        def __cache_lfhkey(self):
            if hasattr(self, '_LFH_KEY'):
                return self._RtlpLFHKey

            # If there was no _LFH_KEY attribute that was assigned, then we
            # need to cheat and use a debugger or something to resolve it.
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
            return "{:#x} -> {:s}".format(self.get(), decoded.summary())

    class HEAP_USERDATA_HEADER(pstruct.type):
        def __Blocks(self):
            pss = self['SubSegment'].li
            ss = pss.d.li

            # Copy the SubSegment as a hidden attribute so that the
            # chunk can quickly lookup any associated information.
            self.attributes['__SubSegment__'] = ss

            # Now we can construct our UserBlocks.
            return dyn.array(_HEAP_CHUNK, ss['BlockCount'].int())

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

            # XXX: the allocation size of this is pow(2, SizeIndex) with a max of
            #      0xf0000 which is then resized to +PaddingBytes if the byte at
            #      "GuardPagePresent" is set.

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (lambda self: P(HEAP_SUBSEGMENT), 'SubSegment'),    # this is actually a union to an SLIST_ENTRY
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),   # uninitialized, but usually points to the previous chunk that this was allocated from
                    (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SizeIndex'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (lambda self: dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(Signature)'),
                    (self.__Blocks, 'Blocks'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (lambda self: P(HEAP_SUBSEGMENT), 'SubSegment'),    # this is actually a union to an SLIST_ENTRY
                    (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),   # uninitialized, but usually points to the previous chunk that this was allocated from
                    (UCHAR, 'SizeIndex'),
                    (UCHAR, 'GuardPagePresent'),
                    (USHORT, 'PaddingBytes'),
                    (HEAP_SIGNATURE, 'Signature'),
                    (HEAP_USERDATA_ENCODED_OFFSETS, 'EncodedOffsets'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(EncodedOffsets)'),
                    (rtltypes.RTL_BITMAP_EX if getattr(self, 'WIN64', False) else rtltypes.RTL_BITMAP, 'BusyBitmap'),
                    (self.__BitmapData, 'BitmapData'),
                    (self.__align_Blocks, 'align(Blocks)'),             # XXX: there's some padding here which we'll need to grab from EncodedOffsets
                    (self.__Blocks, 'Blocks'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            return

        def Segment(self, reload=False):
            '''Return the HEAP_SUBSEGMENT that this object is associated with.'''
            return self['SubSegment'].d

        def ByOffset(self, entryoffset):
            '''Return the field at the specified `entryoffset`.'''

            # If our offsets are encoded, then we need to grab our boundaries
            # and chunk sizes from it to use it for our calculations.
            if operator.contains(self, 'EncodedOffsets'):
                offsets = self['EncodedOffsets'].d.li
                offset, stride = (offsets[fld].int() for fld in ['FirstAllocationOffset', 'BlockStride'])
                result = offset + stride * entryoffset

            # Otherwise we can simply multiply the request by the blocksize.
            else:
                blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
                result = blocksize * entryoffset

            # ...and then we can return the correct element.
            return self.at(self.getoffset() + result, recurse=True)

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
            # FIXME: raise an exception if NTDDI_WIN8 is being used due to randomization.
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
            '''Return a bitmap showing the busy/free chunks that are available.'''
            iterable = ((1 if item['Header'].BusyQ() else 0) for item in self['Blocks'])
            iterable = (bitmap.new(item, 1) for item in iterable)
            return functools.reduce(bitmap.push, iterable, bitmap.zero)

    class HEAP_SUBSEGMENT(pstruct.type):
        def __init__(self, **attrs):
            super(HEAP_SUBSEGMENT, self).__init__(**attrs)
            f = self._fields_ = []

            # Cache a hidden __SubSegment__ attribute for any and all children.
            self.attributes['__SubSegment__'] = self

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

                    (dyn.clone(SLIST_ENTRY, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'SFreeListEntry'),    # XXX: connected to HEAP_LOCAL_SEGMENT_INFO.SListHeader
                    (ULONG, 'Lock'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(Lock)'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
                    (P(HEAP_USERDATA_HEADER), 'UserBlocks'),
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DelayFreeList'),    # XXX: points to a subsegment that will be added to the deleted subsegments???

                    (INTERLOCK_SEQ, 'AggregateExchg'),
                    (USHORT, 'BlockSize'),
                    (USHORT, 'Flags'),
                    (USHORT, 'BlockCount'),
                    (UCHAR, 'SizeIndex'),
                    (UCHAR, 'AffinityIndex'),

                    (ULONG, 'Lock'),
                    (dyn.clone(SLIST_ENTRY, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'SFreeListEntry'),    # XXX: connected to HEAP_LOCAL_SEGMENT_INFO.SListHeader
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(SFreeListEntry)'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

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

            # If our userblocks have some encoded offsets, then this
            # is easy because our offset is literally the index. So,
            # what we'll try to do instead is to validate it.
            ub = self['UserBlocks'].d.li
            if operator.contains(ub, 'EncodedOffsets'):
                index = offset
                if not (0 <= index < self['BlockCount'].int()):
                    raise IndexError(index)
                return index

            # Otherwise we'll just use an empty HEAP_USERDATA_HEADER.
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
            # FIXME: raise an exception if NTDDI_WIN8 is being used due to randomization.
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

    class PHEAP_SUBSEGMENT(ptype.pointer_t):
        '''
        This points to a HEAP_SUBSEGMENT, but ensures that it uses the same
        source of any ptype.encoded_t that parented it. This is intended to
        be used by the _HEAP_ENTRY definition that was defined earlier.
        '''
        _object_ = HEAP_SUBSEGMENT
        # FIXME: cross-check this against self.__SubSegment__
        def dereference(self, **attrs):
            if isinstance(self.source, ptypes.provider.proxy) and self.parent is not None:
                p = self.getparent(_HEAP_ENTRY)
                attrs.setdefault('source', p.source)
            return super(PHEAP_SUBSEGMENT, self).dereference(**attrs)

    class PENTRY_OFFSET(opointer_t):
        '''
        This points to a HEAP_USERDATA_HEADER, but ensures that it will use
        the source of any ptype.encoded_t that parented it. This is intended to
        be used by the _HEAP_ENTRY definition that was defined earlier.
        '''
        _object_ = HEAP_USERDATA_HEADER
        def dereference(self, **attrs):
            if isinstance(self.source, ptypes.provider.proxy) and self.parent is not None:
                p = self.getparent(_HEAP_ENTRY)
                attrs.setdefault('source', p.source)
            return super(PENTRY_OFFSET, self).dereference(**attrs)

        def _calculate_(self, offset):
            p = self.getparent(_HEAP_ENTRY)
            return p.getoffset() - offset

    class HEAP_LOCAL_SEGMENT_INFO(pstruct.type):
        class _CachedItems(parray.type):
            _object_, length = P(HEAP_SUBSEGMENT), 0x10

            def available(self):
                '''Return the first cached item that is available.'''
                # FIXME: check if segment reuse threshold is exceeded by
                #        using Counters.TotalBlocks. If it isn't, then
                #        it can be used. Otherwise a HEAP_SUBSEGMENT is
                #        popped from the "SListHeader" field belonging
                #        to the parent HEAP_LOCAL_SEGMENT_INFO, and this
                #        entry is added to the "DeletedSubSegments" in
                #        the "LocalData" from the LFH_HEAP.
                return next(item.d for item in self if item.int())

            def enumerate(self):
                for index, item in enumerate(self):
                    if item.int():
                        yield index, item.d
                    continue
                return

            def iterate(self):
                for _, item in self.enumerate():
                    yield item.d
                return

        def __init__(self, **attrs):
            super(HEAP_LOCAL_SEGMENT_INFO, self).__init__(**attrs)
            f = self._fields_ = []
            integral = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_SUBSEGMENT), 'Hint'),
                    (P(HEAP_SUBSEGMENT), 'ActiveSubSegment'),
                    (self._CachedItems, 'CachedItems'),         # This is where HEAP_SUBSEGMENTs are taken from or put into
                    (SLIST_HEADER, 'SListHeader'),              # XXX: Connected to HEAP_SUBSEGMENT.SFreeListEntry
                    (HEAP_BUCKET_COUNTERS, 'Counters'),
                    (P(HEAP_LOCAL_DATA), 'LocalData'),
                    (ULONG, 'LastOpSequence'),
                    (USHORT, 'BucketIndex'),
                    (USHORT, 'LastUsed'),
                    (integral, 'Reserved'),                     # FIXME: Is this right?
                ])

            # FIXME: this is where our lfh segment comes from
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (P(HEAP_LOCAL_DATA), 'LocalData'),
                    (P(HEAP_SUBSEGMENT), 'ActiveSubSegment'),
                    (self._CachedItems, 'CachedItems'),         # This is where cached HEAP_SUBSEGMENTs are taken from or put into
                    (SLIST_HEADER, 'SListHeader'),              # XXX: Connected to HEAP_SUBSEGMENT.SFreeListEntry
                    (HEAP_BUCKET_COUNTERS, 'Counters'),
                    (ULONG, 'LastOpSequence'),
                    (USHORT, 'BucketIndex'),
                    (USHORT, 'LastUsed'),
                    (USHORT, 'NoThrashCount'),

                    (USHORT, 'Reserved'),                       # XXX: added manually
                    (dyn.block(0xc if getattr(self, 'WIN64', False) else 4), 'unknown'), # XXX: there's got to be another field here
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def Bucket(self):
            '''Return the frontend bucket associated with the current HEAP_LOCAL_SEGMENT_INFO.'''
            index = self['BucketIndex'].int()

            # First check to see if an LFH_HEAP is available in our parents.
            try:
                lfh = self.getparent(LFH_HEAP)

            # Otherwise we'll need to do some dereferencing to get there.
            except ptypes.error.ItemNotFoundError:
                local = self['LocalData'].d.li
                lfh = local['LowFragHeap'].d.li

            # Now we can grab the bucket by its index.
            return lfh.BucketByIndex(index)

        def Segment(self):
            '''
            Return the correct HEAP_SUBSEGMENT by checking "Hint" first, and then
            falling back to "ActiveSubSegment".
            '''

            # FIXME: CachedItems seems to point to segments that have previously
            #        been in the 'Hint' field. However, when this happens the
            #        current segment to honor for allocations is 'ActiveSubSegment'.

            if operator.contains(self, 'Hint') and self['Hint'].int():
                return self['Hint'].d.li
            elif self['ActiveSubSegment'].int():
                return self['ActiveSubSegment'].d.li

            # If we couldn't find the segment, then raise an exception.
            OwnerHeap = self.__HEAP__ if hasattr(self, '__HEAP__') else self.getparent(HEAP)
            raise error.MissingSegmentException(self, 'Segment', heap=OwnerHeap, localdata=self.getparent(HEAP_LOCAL_DATA))

        def LastSegment(self):
            '''
            Return the last-used HEAP_SUBSEGMENT from the cache.
            '''
            index = self['LastUsed']
            return self['CachedItems'][index.int()].d

    class HEAP_LOCAL_SEGMENT_INFO_ARRAY(parray.terminated):
        '''This is a synthetic array type used for providing utility methods to any child definitions.'''
        _object_, length = HEAP_LOCAL_SEGMENT_INFO or P(HEAP_LOCAL_SEGMENT_INFO), 0

        def enumerate(self, reload=False):
            '''Yield each item's "BucketIndex" along with the item within the array.'''
            for index, item in enumerate(self):

                # If our element is a pointer, then we need to determine whether
                # we should automatically load it or ignore it.
                if isinstance(item, ptype.pointer_t):
                    if item.int() and (True if reload else item.d.initializedQ()):
                        item = item.d.l if reload else item.d.li
                        yield item['BucketIndex'].int(), item

                    # If we received a valid pointer, but were explicitly told
                    # that we're not allowed to load it, then issue a warning.
                    elif item.int():
                        logging.warning("{:s} : Ignoring pointer element {:s} -> {:s} at the current index ({:d}) due to its value not having yet been dereferenced.".format(self.instance(), item.instance(), item.summary(), index))
                    continue

                # Otherwise we can just yield the field that we care about.
                yield item['BucketIndex'].int(), item
            return

        def ByBucketIndex(self, index, reload=False):
            '''Slowly iterate through all of the items in the array looking for the element that is responsible for the provided bucket index.'''
            for bucketindex, item in self.enumerate(reload=reload):
                if index == bucketindex:
                    yield item
                continue
            raise error.NotFoundException(self, 'ByBucketIndex', message="Unable to find the element for the requested bucket index ({:d}).".format(index))

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

                    # These are not officially part of the structure, but are always located after the prior defined fields.
                    (self.__SubSegments, 'SubSegments'),
                    (self.__Available, 'Available'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(LIST_ENTRY, _object_=P(LFH_BLOCK_ZONE), _path_=['ListEntry']), 'ListEntry'),
                    (ULONG, 'NextIndex'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(NextIndex)'),

                    # FIXME: I'm pretty certain that the list of subsegments will follow these
                    #        fields..similarly to the older definition of this structure.
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        # FIXME: implement a method that will iterate through all of the subsegments that will be returned in the future.

        def iterate(self):
            '''Yield each of the subsegments used by this particular zone.'''
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
        class _UserBlocks(pstruct.type):
            # FIXME: Is this the correct structure for USER_MEMORY_CACHE_ENTRY's
            #        SLIST_HEADER?
            def __Blocks(self):
                entry = self.getparent(USER_MEMORY_CACHE_ENTRY)

                res = [ item.getoffset() for item in entry.p.value ]
                idx = res.index(entry.getoffset()) + 1

                blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
                res = idx * blocksize + blocksize

                block = dyn.clone(_HEAP_CHUNK, blocksize=lambda self, size=res: size)
                return dyn.array(block, entry['AvailableBlocks'].int() * 8)

            _fields_ = [
                (dyn.array(pint.uint32_t, 4), 'unknown'),
                (__Blocks, 'Blocks'),
            ]

        def __init__(self, **attrs):
            super(USER_MEMORY_CACHE_ENTRY, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                #(dyn.clone(SLIST_HEADER, _object_=_UserBlocks), 'UserBlocks'), # XXX: connected to "SubSegment" from HEAP_USERDATA_HEADER which is actually a union for SLIST_ENTRY
                (SLIST_HEADER, 'UserBlocks'),   # XXX: connected to HEAP_USERDATA_HEADER (Reserved?).
                (ULONG, 'AvailableBlocks'),     # AvailableBlocks * 8 seems to be the actual size
                (ULONG, 'MinimumDepth'),
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'Padding')
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (ULONG, 'CacheShiftThreshold'),
                    (USHORT, 'Allocations'),
                    (USHORT, 'Frees'),
                    (USHORT, 'CacheHits'),

                    # XXX: The following fields have been manually added to deal
                    #      with padding, but they're probably just some undocumented
                    #      fields or something...
                    (USHORT, 'Unknown'),
                    (ULONG, 'Reserved'),
                    (dyn.block(0x8 if getattr(self, 'WIN64', False) else 0), 'Padding'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def UserBlocks(self):
            '''Yield the _HEAP_USERDATA_HEADER entries that have been freed and pushed into "UserBlocks".'''
            raise NotImplementedError

    class HEAP_LOCAL_DATA(pstruct.type):
        def __init__(self, **attrs):
            super(HEAP_LOCAL_DATA, self).__init__(**attrs)
            f = self._fields_ = []
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DeletedSubSegments'),   # XXX: connected to HEAP_SUBSEGMENT.SFreeListEntry?
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'DeleteRateThreshold'),
                    (aligned, 'align(SegmentInfo)'),
                    (dyn.clone(HEAP_LOCAL_SEGMENT_INFO_ARRAY, _object_=HEAP_LOCAL_SEGMENT_INFO, length=128), 'SegmentInfo'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fpointer(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=['SFreeListEntry']), 'DeletedSubSegments'),   # XXX: connected to HEAP_SUBSEGMENT.SFreeListEntry?
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONG, 'DeleteRateThreshold'),
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(DeleteRateThreshold)'),
                ])

            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)

        def CrtZone(self):
            '''Return the SubSegmentZone that's correctly associated with the value of the CrtZone field'''
            try:
                fe = self.getparent(LFH_HEAP)

            # If we couldn't find the frontend heap in our parents,
            # then just dereference it from ourselves.
            except ptypes.error.NotFoundError:
                fe = self['LowFragHeap'].d.li

            zone = self['CrtZone'].int()
            zoneiterator = (z for z in fe['SubSegmentZones'].walk() if z.getoffset() == zone)
            try:
                res = next(zoneiterator)
            except StopIteration:
                raise error.CrtZoneNotFoundError(self, 'CrtZone', zone=zone, frontendheap=fe.getoffset(), heap=fe.p.p.getoffset())
            return res

        def DeletedSubSegments(self):
            '''Yield each of the available DeletedSubSegments that will be used first.'''
            # These are reused when a new HEAP_SUBSEGMENT is needed to be
            # allocated. They can get pushed to this list coming from the
            # HEAP_LOCAL_SEGMENT_INFO.CachedItems field.
            raise NotImplementedError

        def AvailableSubSegments(self):
            '''Yield each of the available SubSegments that will be returned from the CrtZone.'''
            raise NotImplementedError

        def NextSubSegment(self):
            '''Return the next HEAP_SUBSEGMENT that will be allocated.'''
            # FIXME: If there are no DeletedSubSegments, then the next available
            #        HEAP_SUBSEGMENT will be taken from the "CrtZone".
            raise NotImplementedError

    @FrontEndHeap.define
    class LFH_HEAP(pstruct.type, versioned):
        type = 2

        # FIXME: It seems that the HEAP_LOCAL_DATA is defined as an array due to
        #        processor affinity when it's enabled in the flags. This is why
        #        all of the available LFH material references it as a single-element.

        class _UserBlockCache(parray.type):
            _object_, length = USER_MEMORY_CACHE_ENTRY, 12

            # XXX: this array is used to grab HEAP_USERDATA_HEADER or "UserBlocks"
            #      that have been previously allocated. the first member of the
            #      HEAP_USERDATA_HEADER is actually a union that points to an
            #      SLIST_ENTRY when not in use and a P(HEAP_SUBSEGMENT) when it is.

            # XXX: if the "DebugFlags" are set on the HEAP_BUCKET, then the last
            #      USER_MEMORY_CACHE_ENTRY is the only one that get's used.

            def BySize(self, size):
                '''Return the correct element for the given bucket size.'''
                raise NotImplementedError

        class _NextSegmentInfoArrayAddress(HEAP_LOCAL_SEGMENT_INFO_ARRAY):
            _object_, length = HEAP_LOCAL_SEGMENT_INFO, None
            def isTerminator(self, item):
                parent, guard = self.getparent(LFH_HEAP), item.blocksize() * 2 // 3
                return parent['FirstUncommittedAddress'].int() <= item.getoffset() + item.blocksize() + guard

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
                    (self._UserBlockCache, 'UserBlockCache'),
                    (dyn.clone(HEAP_BUCKET_ARRAY, length=128), 'Buckets'),
                    (HEAP_LOCAL_DATA, 'LocalData'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                f.extend([
                    (rtltypes.RTL_SRWLOCK, 'Lock'),
                    (dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=P(LFH_BLOCK_ZONE)), 'SubSegmentZones'),
                    (P(HEAP), 'Heap'),

                    (P(self._NextSegmentInfoArrayAddress), 'NextSegmentInfoArrayAddress'),
                    (PVOID, 'FirstUncommittedAddress'),
                    (PVOID, 'ReservedAddressLimit'),
                    (ULONG, 'SegmentCreate'),
                    (ULONG, 'SegmentDelete'),
                    (ULONG, 'MinimumCacheDepth'),
                    (ULONG, 'CacheShiftThreshold'),
                    (integral, 'SizeInCache'),
                    (HEAP_BUCKET_RUN_INFO, 'RunInfo'),
                    (dyn.block(8 if getattr(self, 'WIN64', False) else 0), 'padding(RunInfo)'),
                    (self._UserBlockCache, 'UserBlockCache'),
                    (HEAP_LFH_MEM_POLICIES, 'MemoryPolicies'),
                    (dyn.clone(HEAP_BUCKET_ARRAY, length=129), 'Buckets'),
                    (dyn.clone(HEAP_LOCAL_SEGMENT_INFO_ARRAY, _object_=P(HEAP_LOCAL_SEGMENT_INFO), length=129), 'SegmentInfoArrays'),
                    (dyn.clone(HEAP_LOCAL_SEGMENT_INFO_ARRAY, _object_=P(HEAP_LOCAL_SEGMENT_INFO), length=129), 'AffinitizedInfoArrays'),
                    (P(SEGMENT_HEAP), 'SegmentAllocator'),
                    (dyn.align(8), 'align(LocalData)'),
                    (HEAP_LOCAL_DATA, 'LocalData'),
                ])
            else:
                # XXX: win10
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

        def BucketByUnits(self, units, reload=False):
            buckets = self['Buckets'].l if reload else self['Buckets'].li
            return buckets.ByUnits(units)

        def BucketByIndex(self, index, reload=False):
            '''Return the Bucket for a given index.'''
            buckets = self['Buckets'].l if reload else self['Buckets'].li
            return buckets[index]

        def SegmentInfoByUnits(self, units, reload=False):
            '''Return the HEAP_LOCAL_SEGMENT_INFO for a specific number of units.'''
            bucket = self.BucketByUnits(units, reload=reload)
            index = bucket['SizeIndex'].int()

            # FIXME: check HEAP_BUCKET.AffinityQ() to determine whether we use the
            #        "SegmentInfoArrays" or the "AffinitizedInfoArrays"

            # If we are using the "SegmentInfoArrays" pointer array, then index into it.
            if operator.contains(self, 'SegmentInfoArrays'):
                segmentinfoarray = self['SegmentInfoArrays']
                result = segmentinfoarray[index].d.li

            # Otherwise we need to descend into the LocalData before we find our array.
            else:
                localdata = self['LocalData']
                segmentinfoarray = localdata['SegmentInfo']
                result = segmentinfoarray[index]

            # ...and that was it.
            return result

        def Bucket(self, size):
            '''Return the Bucket for the requested ``size``.'''
            heap = self['Heap'].d

            # We actually don't need the heap for anything else which is why we don't load it.
            units = heap.BlockUnits(size)
            return self.BucketByUnits(units)

        def SegmentInfo(self, size):
            '''Return the HEAP_LOCAL_SEGMENT_INFO for the given ``size``.'''
            heap = self['Heap'].d

            # We actually don't need the heap for anything else which is why we don't load it.
            units = heap.BlockUnits(size)
            return self.SegmentInfoByUnits(units)

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
                    (ULONG, 'Flags'),                   # seems to come from global flags
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
                    (ULONG, 'SegmentFlags'),            # seems to come from global flags
                    (lambda self: dyn.clone(LIST_ENTRY, _sentinel_='Blink', _path_=['SegmentListEntry'], _object_=fpointer(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentListEntry'),   # XXX: entry comes from HEAP
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

        def Contains(self, address):
            '''Returns whether the current HEAP_SEGMENT contains the specified address.'''
            PAGE_SIZE, count = 0x1000, self['NumberOfPages'].int()
            return self.getoffset() <= address < self.getoffset() + PAGE_SIZE * count

        def Committed(self, address):
            '''Returns whether the given address is within the current HEAP_SEGMENT's committed memory.'''
            PAGE_SIZE, count = 0x1000, self['NumberOfPages'].int() - self['NumberOfUncommittedPages'].int()
            return self.getoffset() <= address < self.getoffset() + PAGE_SIZE * count

        def Owns(self, address):
            '''Returns whether the given address is owned by a chunk within the current HEAP_SEGMENT.'''
            start, stop = (self[fld] for fld in ['FirstEntry', 'LastValidEntry'])
            return start.int() <= address < stop.int()

        def Block(self, address):
            '''Create a _HEAP_CHUNK at the specified address.'''
            if self.Owns(address):
                return self.new(_HEAP_CHUNK, offset=address)

            # Raise an exception if the chunk is out of bounds.
            cls = self.__class__
            start, stop = (self[fld] for fld in ['FirstEntry', 'LastValidEntry'])
            raise error.InvalidChunkAddress(self, 'Chunk', message="The requested address ({:#x}) is not within the boundaries of the current {:s} ({:#x}<>{:#x}).".format(address, cls.typename(), start.int(), end.int()), Segment=self)

        def Chunk(self, address):
            '''Create a _HEAP_CHUNK that references the specified address.'''
            header = self.new(HEAP_ENTRY).a
            return self.Block(address - header.blocksize())

        def iterate(self):
            '''Yield each of the committed chunks in the current segment.'''
            res = self['FirstEntry'].d
            yield res.li

            # After yielding the first entry, walk through the entire segment
            # constructing each chunk individually and then yielding it. If we
            # encounter an "Uncommitted" type, then we can just terminate here.
            while not res['Header'].o.Type('Uncommitted') and res.getoffset() + res['Header'].Size() < self['LastValidEntry'].int():
                ea = res.getoffset() + res['Header'].Size()
                res = self.Block(ea)
                yield res.li
            return

        def enumerate(self):
            '''Enumerate all of the committed chunks within the current segment.'''
            for item in enumerate(self.iterate()):
                yield item
            return

        def walk(self):
            '''Iterate through each entry within the segment list.'''
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
        def __Entry(self):
            owner = self.__HEAP__ if hasattr(self, '__HEAP__') else self.getparent(HEAP)
            res, sentinel = P(HEAP_VIRTUAL_ALLOC_ENTRY), owner['VirtualAllocatedBlocks']
            return dyn.clone(LIST_ENTRY, _path_=['Entry'], _object_=res, _sentinel_=sentinel.getoffset())

        def __Commit(self):
            res = sum(self[fld].li.size() for fld in ['Entry', 'ExtraStuff', 'CommitSize', 'ReserveSize', 'Header'])
            return dyn.clone(_HEAP_CHUNK_LARGE, length=max(0, self['CommitSize'].int() - res))

        def __Reserve(self):
            res = self['ReserveSize'].int() - self['CommitSize'].int()
            return dyn.clone(HEAP_BLOCK_UNCOMMITTED, length=max(0, res))

        _fields_ = [
            (__Entry, 'Entry'),
            (HEAP_ENTRY_EXTRA, 'ExtraStuff'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'CommitSize'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'ReserveSize'),
            (_HEAP_ENTRY, 'Header'),
            (__Commit, 'Commit'),
            (__Reserve, 'Reserve'),
        ]

    class HEAP(pstruct.type, versioned):
        class _FreeLists(parray.type):
            _object_, length = fpointer(_HEAP_CHUNK, 'ListEntry'), 128
            # FIXME: the ListEntry that this directly points to should have its sentinel value set.

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
                self.attributes['_HEAP_ENTRY_Encoding'] = self['EncodeFlagMask'].li.int(), tuple(item.int() for item in self['Encoding'].li['Keys'])
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        class _FrontEndHeapUsageData(pbinary.array):
            class _HeapBucketCounter(pbinary.struct):
                _fields_ = [
                    (11, 'high'),
                    (5, 'low'),
                ]
                def FrontEndQ(self):
                    '''Return whether the counters will result in the frontend heap being used.'''

                    # First check the low counter.
                    if self['low'] > 0x10:
                        return True

                    # Next check the high counter.
                    return self['high'] > 0x7f8

                def BackEndQ(self):
                    return not self.FrontEndQ()

                def Count(self):
                    return self['low']

                def summary(self):
                    return "{:#04x} :> low={:d} high={:#x}".format(self.int(), self['low'], self['high'])
            _object_, length = _HeapBucketCounter, 0

            def BySize(self, size):
                owner = self.__HEAP__ if hasattr(self, '__HEAP__') else self.getparent(HEAP)
                units = owner.BlockUnits(size)
                return self[units]

        def __FrontEndHeapUsageData(self):
            def FrontEndHeapUsageDataArray(this):
                index = self['FrontEndHeapMaximumIndex'].li
                t = dyn.clone(self._FrontEndHeapUsageData, length=index.int())
                return pbinary.littleendian(t, 2)
            return P(FrontEndHeapUsageDataArray)

        def __FrontEndHeapPointer(self):
            heap_t = lambda *args, **kwargs: FrontEndHeap.lookup(self['FrontEndHeapType'].li.int(), None) or PVOID._object_
            return P(heap_t)

        def __init__(self, **attrs):
            super(HEAP, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            integral = ULONGLONG if getattr(self, 'WIN64', False) else ULONG
            size_t = SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T

            # Cache a hidden __HEAP__ attribute amongst all children.
            self.attributes['__HEAP__'] = self

            # Define all of the necessary fields for the structure.
            f = self._fields_ = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WS03:
                f.extend([
                    (HEAP_ENTRY, 'Entry'),                              # XXX: needs to be corrected since refactor
                    (HEAP_SIGNATURE, 'Signature'),
                    (rtltypes.HEAP_, 'Flags'),
                    (rtltypes.HEAP_, 'ForceFlags'),
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
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),                  # XXX: likely points to an array
                    (P(HEAP_UCR_SEGMENT), 'UCRSegments'),
                    (P(HEAP_UNCOMMMTTED_RANGE), 'UnusedUnCommittedRanges'),
                    (ULONG_PTR, 'AlignRound'),
                    (ULONG_PTR, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=['Entry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocatedBlocks'),
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
                    (self.__FrontEndHeapPointer, 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (UCHAR, 'LastSegmentIndex'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (rtltypes.HEAP_, 'Flags'),
                    (rtltypes.HEAP_, 'ForceFlags'),
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
                    (dyn.clone(LIST_ENTRY, _path_=['Entry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocatedBlocks'),
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
                    (self.__FrontEndHeapPointer, 'FrontEndHeap'),
                    (USHORT, 'FrontHeapLockCount'),
                    (FrontEndHeap.Type, 'FrontEndHeapType'),
                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
                # _HEAP.Segment.Entry contains real size

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN10:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (rtltypes.HEAP_, 'Flags'),
                    (rtltypes.HEAP_, 'ForceFlags'),
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
                    (dyn.clone(LIST_ENTRY, _path_=['Entry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocatedBlocks'),
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
                    (self.__FrontEndHeapPointer, 'FrontEndHeap'),
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
                # _HEAP.Segment.Entry contains real size

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                # XXX: win10
                f.extend([
                    (HEAP_SEGMENT, 'Segment'),
                    (rtltypes.HEAP_, 'Flags'),
                    (rtltypes.HEAP_, 'ForceFlags'),
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
                    (dyn.clone(LIST_ENTRY, _path_=['Entry'], _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocatedBlocks'),
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
                    (rtltypes.RTL_HEAP_MEMORY_LIMIT_DATA if getattr(self, 'WIN64', False) else ptype.undefined, 'CommitLimitData'),
                    (self.__FrontEndHeapPointer, 'FrontEndHeap'),
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
                # _HEAP.Segment.Entry contains real size

            else:
                raise error.NdkUnsupportedVersion(self)
            return

        def UncommittedRanges(self):
            '''Yield each of the UncommittedRanges (UCRList) for the HEAP'''
            for item in self['UCRList'].walk():
                yield item
            return

        def Segments(self):
            '''Yield each of the Segments (SegmentList) for the HEAP'''
            for item in self['SegmentList'].walk():
                yield item
            return

        def BlockUnits(self, size):
            '''Return the correct number of units when given a ``size``.'''
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8

            # Figure out what the proper size should be when adding the
            # size of the header and a value for rounding.
            size_and_header = size + blocksize + 7

            # Now we can divide the total size by the blocksize in order
            # to get the actual number of units.
            units = math.floor(size_and_header / (1. * blocksize))
            return math.trunc(units)

        def BlocksIndex(self, size, reload=False):
            '''Return the correct HeapList for the given size.'''
            units = self.BlockUnits(size)

            # Now that we have the units, dereference the BlocksIndex to start
            # and then use the number of units to figure out the correct one.
            bi = self['BlocksIndex'].d.l if reload else self['BlocksIndex'].d.li
            return bi.HeapList(units)

        def FreeList(self, size):
            '''Search the freelist for a chunk that is of the requested size.'''
            freelists = self['FreeLists']
            if isinstance(freelists, self._FreeLists):
                listhints = self['FreeListsInUseUlong']
                # FIXME: this used to be implemented somewhere before everything was consolidated.
                raise error.InvalidHeapType(self, 'FreeLists', message='Unable to walk all the entries in the lookaside list')

            # walk through the freelists until we find one that will fit our requested size
            iterable = (item for item in freelists.walk() if size <= item['Header'].Size())
            result = next(iterable)
            return result

        def ListHintByBucket(self, size, reload=False):
            '''Use the BlocksIndex to find the ListHint for a given size.'''
            units = self.BlockUnits(size)

            # We start immediately with the BlocksIndex, by finding the correct one.
            bi = self['BlocksIndex'].d.l if reload else self['BlocksIndex'].d.li
            blocklist = bi.HeapList(units, reload=reload)

            # Next, we'll check its bitmap to see if the exact slot is available
            # and return that immediately if so.
            if blocklist.Check(units, reload=reload):
                return blocklist.ListHint(units, reload=reload)

            # If the bitmap didn't have a bit set, then warn the user that we're
            # going to scan for the next largest chunk that will likely get split.
            logging.warning("{:s} : An chunk of the exact number of units ({:d}) was not found in the heap list at {:s}. Scanning for the chunk that will be split.".format(self.instance(), units, blocklist.instance()))

            # Now we can return the next largest slot for the requested size.
            return blocklist.Larger(units)

        def FreeListByBucket(self, size, reload=False):
            '''Use the BlocksIndex to find the freelist for a given size.'''
            slot = self.ListHintByBucket(size, reload=reload)

            # Now that we should have the correct slot, the last thing to do
            # is to grab the blocklist that owns it. This way we can tell
            # that if the blocklist has an ExtraItem, then we need to call
            # a method to get the list of chunks that should get split.
            blocklist = slot.getparent(HEAP_LIST_LOOKUP)
            if blocklist['ExtraItem'].int():
                return slot.FreeChunk()

            # Otherwise, it's already pointing to the list and we can just
            # dereference the pointer to get to get the next chunk.
            return slot.d

        def ListHint(self, size, reload=False):
            '''Return the ListHint from the BlockIndex according to the specified ``size``'''
            units = self.BlockUnits(size)

            # Use the BlockIndex with the correct BlockList in order
            # to get the ListHint for the desired number of units.
            bi = self['BlocksIndex'].d.l if reload else self['BlocksIndex'].d.li
            blocklist = bi.HeapList(units, reload=reload)

            # Now we can simply use it to return the ListHint that was requested.
            return blocklist.ListHint(units)

        def BackendCount(self, size, reload=False):
            '''Return the number of backend allocation counts for a given size or None if the frontend heap will be used.'''
            units = self.BlockUnits(size)

            # Use the BlockIndex with the correct BlockList in order
            # to get the ListHint for the desired number of units.
            bi = self['BlocksIndex'].d.l if reload else self['BlocksIndex'].d.li
            blocklist = bi.HeapList(units, reload=reload)

            # If there's an "ExtraItem" field in the blocklist, then we return
            # the count from the ListHint.
            if blocklist['ExtraItem'].int():
                item = blocklist.ListHint(units)
                return item.Count()

            # Otherwise, we need to fetch two fields. The first will be
            # the "FrontEndHeapStatusBitmap" which will be used with
            # the second, the "FrontEndHeapUsageData", to determine whether
            # we're getting an allocation count or a bucket index.
            if self['FrontEndHeapStatusBitmap'].check(units):
                return None

            # Now we know that the index points to an allocation count.
            usage = self['FrontEndHeapUsageData'].d.l if reload else self['FrontEndHeapUsageData'].d.li
            return usage[units].Count()

        def Buckets(self, reload=False):
            '''Yield each available bucket that will use the frontend allocator.'''
            blocklist = self['BlocksIndex'].d.l if reload else self['BlocksIndex'].d.li

            # If the BlocksIndex has an extra-item, then we need to just iterate
            # through their ListHints in order to enumerate their buckets.
            if blocklist['ExtraItem'].int():
                while blocklist.getoffset():
                    blocklist = blocklist.l if reload else blocklist.li
                    listhints = blocklist['ListHints'].d.l if reload else blocklist['ListHints'].d.li

                    # Iterate through each item while verifying that it's a
                    # frontend chunk, and then dereferencing its bucket if so.
                    for item in listhints:
                        if item.FrontEndQ():
                            yield item.Bucket()
                        continue

                    # Traverse to the next one.
                    blocklist = blocklist['ExtendedLookup'].d
                return

            # Otherwise, we need to combine the "FrontEndHeapStatusBitmap" with
            # the "FrontEndHeapUsageData", and use it with the "FrontEndHeap" to
            # identify the buckets that are being used.
            status, usage, fheap = (self[fld] for fld in ['FrontEndHeapStatusBitmap', 'FrontEndHeapUsageData', 'FrontEndHeap'])
            usage, fheap = (usage.d.l, fheap.d.l) if reload else (usage.d.li, fheap.d.li)

            # Now we can iterate through the bits in our bitmap
            usage = usage.l if reload else usage
            for units in status.iterate():
                index = usage[units].int()
                yield fheap.BucketByIndex(index)
            return

    class HEAP_LIST_LOOKUP(pstruct.type, versioned):
        def __ExtendedLookup(self):
            return P(HEAP_LIST_LOOKUP)

        def __ListsInUseUlong(self):
            arraysize, baseindex = (self[fld].li.int() for fld in ['ArraySize', 'BaseIndex'])
            bits = arraysize - baseindex
            target = dyn.clone(ListsInUseUlong, length=bits // 32)
            return P(target)

        class _ListHints(parray.type):
            _object_, length = PVOID, 0
            # FIXME: we can summarize this by showing the entries that are backend or frontend

        def __ListHints(self):
            extra, sentinel, arraysize, baseindex = (self[fld].li for fld in ['ExtraItem', 'ListHead', 'ArraySize', 'BaseIndex'])

            # If there's no "ExtraItems", then "ListHints" is just a list of pointers to free chunks.
            ptr, count = fpointer(_HEAP_CHUNK, 'ListEntry'), arraysize.int() - baseindex.int()
            if extra.int() == 0:
                result = dyn.clone(self._ListHints, _object_=ptr, length=count)

            # Otherwise, "ListHints" is a list of FreeListBucket which also contains information about the number of allocations.
            elif extra.int() == 1:
                item = dyn.clone(FreeListBucket, _object_=ptr, _path_=['ListEntry'], _sentinel_=sentinel.int())
                result = dyn.clone(self._ListHints, _object_=item, length=count)

            # We've never seen any other value, so raise an exception so that the user knows what's up.
            else:
                raise error.ListHintException(self, 'ListHints', message="Unable to determine format of \"ListHints\" field due to value of \"ExtraItem\" ({:d})".format(extra.int()))
            return P(result)

        _fields_ = [
            (__ExtendedLookup, 'ExtendedLookup'),
            (ULONG, 'ArraySize'),
            (ULONG, 'ExtraItem'),                           # XXX: is this what causes the different type for ListHints?
            (ULONG, 'ItemCount'),
            (ULONG, 'OutOfRangeItems'),
            (ULONG, 'BaseIndex'),

            (lambda self: dyn.align(8 if getattr(self, 'WIN64', False) else 4), 'align(ListHead)'),
            #(P(dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(_HEAP_CHUNK, 'ListEntry'))), 'ListHead'),
            #(P(dyn.clone(LIST_ENTRY, _path_=['ListEntry'], _object_=fpointer(HEAP, 'FreeLists'))), 'ListHead'),
            (fpointer(HEAP, 'FreeLists'), 'ListHead'),      # FIXME: points to HEAP.FreeLists (used as sentinel address)
            (__ListsInUseUlong, 'ListsInUseUlong'),
            (__ListHints, 'ListHints'),
        ]

        def HeapList(self, units, reload=False):
            '''Traverse all of the available HEAP_LIST_LOOKUP to identify the one responsible for a particular number of units.'''
            index = units

            # This heap list is indexed by the number of block units, so we can
            # linearly convert it into the slot to lookup.
            while self['ExtendedLookup'].int():
                slot = index - self['BaseIndex'].int()
                if slot < self['ArraySize'].int():
                    return self
                self = self['Extendedlookup'].d.l if reload else self['ExtendedLookup'].d.li

            # We ran out of arrays to traverse, so we need to figure out what actually
            # happened so that we can let the user know.
            slot = index - self['BaseIndex'].int()
            if slot < 0:
                raise error.ListHintException(self, 'HEAP_LIST_LOOKUP', message="Invalid index was requested ({:d}) which is not supported by the current {:s} with a minimum BaseIndex of {:d}.".format(index, self.instance(), self['BaseIndex'].int()), index=index, base=self['BaseIndex'].int(), size=self['ArraySize'].int(), lookup=self)

            elif self['ArraySize'].int() <= slot:
                logging.warning("{:s} : The requested index ({:d}) is an OutOfRangeItem and is not within the boundaries ({:d}<>{:d}) of the last {:s}.".format(self.instance(), index, self['BaseIndex'].int(), self['BaseIndex'].int() + self['ArraySize'].int(), self.classname()))

            # Return the HEAP_LIST_LOOKUP that we stopped on.
            return self

        def ListHint(self, units, reload=False):
            '''Return the correct "ListHints" entry for the given number of units.'''
            slot = units - self['BaseIndex'].int()
            if not (0 <= slot < self['ArraySize'].int()):
                raise error.ListHintException(self, 'HEAP_LIST_LOOKUP', message="Invalid number of units was requested ({:d}) which is not supported by the current {:s} with a range of {:d}<>{:d}.".format(units, self.instance(), self['BaseIndex'].int(), self['BaseIndex'].int() + self['ArraySize'].int()), index=units, base=self['BaseIndex'].int(), size=self['ArraySize'].int(), lookup=self)

            # Grab the hints and return the slot that the user requested.
            slots = self['ListHints'].d.l if reload else self['ListHints'].d.li
            return slots[slot]

        def Larger(self, units, reload=False):
            '''Return the nearest slot larger than the specified number of units that's in use.'''
            slot = units - self['BaseIndex'].int()
            if not (0 <= slot < self['ArraySize'].int()):
                raise error.ListHintException(self, 'HEAP_LIST_LOOKUP', message="Invalid number of units was requested ({:d}) which is not supported by the current {:s} with a range of {:d}<>{:d}.".format(units, self.instance(), self['BaseIndex'].int(), self['BaseIndex'].int() + self['ArraySize'].int()), index=units, base=self['BaseIndex'].int(), size=self['ArraySize'].int(), lookup=self)

            # Grab the bitmap and scan for the next slot that's in use.
            hints = self['ListsInUseUlong'].d.l if reload else self['ListsInUseUlong'].d.li
            nearest = hints.scan(slot + 1)
            return self.ListHint(self['BaseIndex'].int() + nearest, reload=reload)

        def Smaller(self, units, reload=False):
            '''Return the nearest slot smaller than the specified number of units that's in use.'''
            slot = units - self['BaseIndex'].int()
            if not (0 <= slot < self['ArraySize'].int()):
                raise error.ListHintException(self, 'HEAP_LIST_LOOKUP', message="Invalid number of units was requested ({:d}) which is not supported by the current {:s} with a range of {:d}<>{:d}.".format(units, self.instance(), self['BaseIndex'].int(), self['BaseIndex'].int() + self['ArraySize'].int()), index=units, base=self['BaseIndex'].int(), size=self['ArraySize'].int(), lookup=self)

            # Grab the bitmap and scan for the next slot that's in use.
            hints = self['ListsInUseUlong'].d.l if reload else self['ListsInUseUlong'].d.li
            nearest = hints.scanreverse(slot - 1)
            return self.ListHint(self['BaseIndex'].int() + nearest, reload=reload)

        def Check(self, units, reload=False):
            '''Return whether the specified slot is actually in use according to the bitmap.'''
            slot = units - self['BaseIndex'].int()
            if not (0 <= slot < self['ArraySize'].int()):
                raise error.ListHintException(self, 'HEAP_LIST_LOOKUP', message="Invalid number of units was requested ({:d}) which is not supported by the current {:s} with a range of {:d}<>{:d}.".format(units, self.instance(), self['BaseIndex'].int(), self['BaseIndex'].int() + self['ArraySize'].int()), index=units, base=self['BaseIndex'].int(), size=self['ArraySize'].int(), lookup=self)

            # Grab the bitmap and return whether the request slot is in use.
            hints = self['ListsInUseUlong'].d.l if reload else self['ListsInUseUlong'].d.li
            return True if hints.check(slot) else False

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
