### Implement the WIN64 version of this.
import functools, itertools, types, builtins, operator, six
import math, logging

import ptypes
from . import sdkddkver, rtltypes, error
from .datatypes import *

class HEAP_LOCK(pint.uint32_t): pass

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
            return ' '.join("{:s}={:s}".format(k, v.summary()) for k, v in self.iteritems())

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
        def __init__(self, **attrs):
            super(HEAP_DEBUGGING_INFORMATION, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (PVOID, 'InterceptorFunction'),
                (WORD, 'InterceptorValue'),
                (DWORD, 'ExtendedOptions'),
                (DWORD, 'StackTraceDepth'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MinTotalBlockSize'),
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'MaxTotalBlockSize'),
                (PVOID, 'HeapLeakEnumerationRoutine'),
            ])

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

if False and 'HeapCache':
    class HeapCache(pstruct.type):
        _fields_ = [
            (ULONG, 'NumBuckets'),
            (pint.int32_t, 'CommittedSize'),
            (LARGE_INTEGER, 'CounterFrequency'),
            (LARGE_INTEGER, 'AverageAllocTime'),
            (LARGE_INTEGER, 'AverageFreeTime'),
            (pint.int32_t, 'SampleCounter'),
            (pint.int32_t, 'field_24'),
            (LARGE_INTEGER, 'AllocTimeRunningTotal'),
            (LARGE_INTEGER, 'FreeTimeRunningTotal'),
            (pint.int32_t, 'AllocTimeCount'),
            (pint.int32_t, 'FreeTimeCount'),
            (pint.int32_t, 'Depth'),
            (pint.int32_t, 'HighDepth'),
            (pint.int32_t, 'LowDepth'),
            (pint.int32_t, 'Sequence'),
            (pint.int32_t, 'ExtendCount'),
            (pint.int32_t, 'CreateUCRCount'),
            (pint.int32_t, 'LargestHighDepth'),
            (pint.int32_t, 'HighLowDifference'),

            (P(pint.uint8_t), 'pBitmap'), # XXX

            (P(_HEAP_CHUNK), 'pBucket'),  # XXX
            (lambda s: P(dyn.array(_HEAP_CHUNK, s['NumBuckets'].li.int())), 'Buckets'),
            (lambda s: dyn.array(pint.uint32_t, s['NumBuckets'].li.int() / 32), 'Bitmap'),
        ]

    class imm_HeapCache(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'NumBuckets'),
            (pint.uint32_t, 'CommittedSize'),
            (pint.uint64_t, 'CounterFrequency'),
            (pint.uint64_t, 'AverageAllocTime'),
            (pint.uint64_t, 'AverageFreeTime'),
            (pint.uint32_t, 'SampleCounter'),
            (pint.uint32_t, 'field_24'),
            (pint.uint64_t, 'AllocTimeRunningTotal'),
            (pint.uint64_t, 'FreeTimeRunningTotal'),
            (pint.uint32_t, 'AllocTimeCount'),
            (pint.uint32_t, 'FreeTimeCount'),
            (pint.uint32_t, 'Depth'),
            (pint.uint32_t, 'HighDepth'),
            (pint.uint32_t, 'LowDepth'),
            (pint.uint32_t, 'Sequence'),
            (pint.uint32_t, 'ExtendCount'),
            (pint.uint32_t, 'CreateUCRCount'),
            (pint.uint32_t, 'LargestHighDepth'),
            (pint.uint32_t, 'HighLowDifference'),
            (pint.uint64_t, 'pBitmap'),

            (lambda s: dyn.array(P(_HEAP_CHUNK), s['NumBuckets'].li.int()), 'Buckets'),
            (lambda s: dyn.clone(pbinary.array, _object_=1, length=s['NumBuckets'].li.int()), 'Bitmask'),    # XXX: This array can be too large and should be a simulated pbinary.array
    #        (lambda s: dyn.block(s['NumBuckets'].li.int() / 8), 'Bitmask'),
        ]

if 'HeapEntry':
    class HEAP_BUCKET(pstruct.type):
        class BucketFlags(pbinary.flags):
            _fields_ = [
                (5, 'Reserved'),
                (2, 'DebugFlags'),
                (1, 'UseAffinity'),
            ]

        _fields_ = [
            (pint.uint16_t, 'BlockUnits'),
            (pint.uint8_t, 'SizeIndex'),
            (BucketFlags, 'BucketFlags'),
        ]

        def AllocationCount(self):
            return self['BlockUnits'].li.int() >> 1

    class HEAP_ENTRY_EXTRA(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'AllocatorBacktraceIndex'),
            (pint.uint64_t, 'ZeroInit'),
            (pint.uint16_t, 'TagIndex'),
            (pint.uint32_t, 'Settable'),
        ]

    class HEAP_ENTRY_(pbinary.flags):
        _fields_ = [
            (1, 'SETTABLE_FLAG3'),   # No Coalesce
            (1, 'SETTABLE_FLAG2'),   # FFU2
            (1, 'SETTABLE_FLAG1'),   # FFU1
            (1, 'LAST_ENTRY'),
            (1, 'VIRTUAL_ALLOC'),
            (1, 'FILL_PATTERN'),
            (1, 'EXTRA_PRESENT'),
            (1, 'BUSY'),
        ]

    class HEAP_ENTRY(pstruct.type, versioned):
        class UnusedBytes(pbinary.flags):
            class _Type(pbinary.enum):
                width, _values_ = 3, [
                    ('Chunk', 0),
                    ('Segment', 1),
                    ('Linked', 5),
                ]
            _fields_ = [
                (1, 'AllocatedByFrontend'),
                (3, 'Unknown'),
                (1, 'Busy'),
                (_Type, 'Type'),
            ]
            def FrontEndQ(self):
                return bool(self['AllocatedByFrontend'])
            def BackEndQ(self):
                return not self.FrontEndQ()

            def BusyQ(self):
                return bool(self['Busy'])
            def FreeQ(self):
                return not self.BusyQ()

            def summary(self):
                frontend = 'FE' if self.FrontEndQ() else 'BE'
                busy = 'BUSY' if self.BusyQ() else 'FREE'
                return "{:s} {:s} Type:{:d}".format(frontend, busy, self['Type'])

        def __init__(self, **attrs):
            super(HEAP_ENTRY, self).__init__(**attrs)
            f = []
            f.append((pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'ReservedForAlignment'))

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
                #f.extend([
                #   (pint.uint16_t, 'Size'),
                #   (pint.uint16_t, 'PreviousSize'),
                #   (pint.uint8_t, 'SmallTagIndex'),
                #   (HEAP_ENTRY_, 'Flags'),
                #   (pint.uint8_t, 'UnusedBytes'),
                #   (pint.uint8_t, 'SegmentIndex'),
                #   (pint.uint8_t, 'SegmentOffset'),
                #])
                f.extend([
                    (pint.uint16_t, 'Size'),
                    (pint.uint16_t, 'PreviousSize'),
                    (pint.uint8_t, 'SegmentIndex'),
                    (HEAP_ENTRY_, 'Flags'),
                    (pint.uint8_t, 'Index'),
                    (pint.uint8_t, 'Mask'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                f.extend([
                    (pint.uint16_t, 'Size'),
                    (HEAP_ENTRY_, 'Flags'),
                    (pint.uint8_t, 'SmallTagIndex'),    # Checksum
                    (pint.uint16_t, 'PreviousSize'),
                    (pint.uint8_t, 'SegmentOffset'),    # Size // blocksize
                    (HEAP_ENTRY.UnusedBytes, 'UnusedBytes'),  # XXX: for some reason this is checked against 0x05
                ])

            else:
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
            return bool(res['AllocatedByFrontend'])
        def BackEndQ(self):
            return not self.FrontEndQ()

        def BusyQ(self):
            res = self.Flags()
            return bool(res['Busy'])
        def FreeQ(self):
            return not self.BusyQ()

        def summary(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                res = "Size={:x} SmallTagIndex={:x} PreviousSize={:x} SegmentOffset={:x}"
                res = [res.format(self['Size'].int(), self['SmallTagIndex'].int(), self['PreviousSize'].int(), self['SegmentOffset'].int())]
                res+= ["UnusedBytes ({:s})".format(self['UnusedBytes'].summary())]
                res+= ["Flags ({:s})".format(self['Flags'].summary())]
                return ' : '.join(res)
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
                return res.encode('hex')
            bs = 0x10 if getattr(self, 'WIN64', False) else 8
            data, res = self.serialize(), self.d.li
            return "{:s} : {:-#x} <-> {:+#x} : Flags:{:s}".format(data.encode('hex'), -res['PreviousSize'].int() * bs, res['Size'].int() * bs, res['Flags'].summary())

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
            # XXX: optimize by checking FrontEndQ which requires decoding
            res = self.d.li
            return res.BusyQ()

        def FreeQ(self):
            '''Returns whether the chunk (decoded) is free or not'''
            # XXX: optimize by checking FrontEndQ which requires decoding
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
                (pint.uint16_t, 'Size'),
                (pint.uint16_t, 'Checksum'),
                (pint.uint16_t, 'PreviousSize'),
                (pint.uint8_t, 'SegmentOffset'),
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
                bs = 0x10 if getattr(self, 'WIN64', False) else 8
                return "{:s} PreviousSize={:+#x} Size={:+#x} SegmentOffset={:#x} Checksum={:#x}".format(self['Flags'].summary(), -self['PreviousSize'].int() * bs, self['Size'].int() * bs, self['SegmentOffset'].int(), self['Checksum'].int())

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
                iterable = (ptypes.bitmap.data((encoder ^ item.int(), 32), reversed=True) for item, encoder in zip(object['Encoded'], self._HEAP_ENTRY_Encoding))
                data = object['Unencoded'].serialize() + reduce(operator.add, iterable)
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
                iterable = (ptypes.bitmap.data((encoder ^ item.int(), 32), reversed=True) for item, encoder in zip(object['Encoded'], self._HEAP_ENTRY_Encoding))
                data = object['Unencoded'].serialize() + reduce(operator.add, iterable)
                res = ptype.block().set(data)
                return super(_HEAP_ENTRY, self).decode(res)

            # Otherwise, we're not encoded. So, just pass-through...
            return super(_HEAP_ENTRY, self).decode(object, **attrs)

        def __be_summary(self):
            bs = 0x10 if getattr(self, 'WIN64', False) else 8
            data, res = self.serialize(), self.d.li
            return "{:s} : {:-#x} <-> {:+#x} : Flags:{:s}".format(data.encode('hex'), -res['PreviousSize'].int() * bs, res['Size'].int() * bs, res['Flags'].summary())

        def ChecksumQ(self):
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'ChecksumQ', message='Unable to calculate the checksum for a non-backend type')

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) != sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                raise error.IncorrectChunkVersion(self, 'ChecksumQ', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))

            # Calculate checksum (a^9^8 == b)
            res = self.d.li.cast(self._BE_Encoded)
            data = map(six.byte2int, res['Encoded'].serialize())
            chk = reduce(operator.xor, data[:3], 0)
            return chk == data[3]

        def Size(self):
            '''Return the decoded Size field'''
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'Size')
            self = self.d.li
            bs = 0x10 if getattr(self, 'WIN64', False) else 8
            return bs * self['Size'].int()

        def PreviousSize(self):
            '''Return the decoded PreviousSize field'''
            if not self.BackEndQ():
                raise error.InvalidHeapType(self, 'Size')
            self = self.d.li
            bs = 0x10 if getattr(self, 'WIN64', False) else 8
            return bs * self['PreviousSize'].int()

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
                    return bool(self['Busy'])
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
                (lambda self: dyn.clone(PHEAP_SUBSEGMENT, _value_=PVALUE32), 'SubSegment'),
                (pint.uint16_t, 'Unknown'),     # seems to be diff on 32-bit?
                (pint.uint8_t, 'EntryOffset'),
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

        def __RtlpLFHKey(self):
            RtlpLFHKey = self.source.expr('ntdll!RtlpLFHKey')
            t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
            res = self.new(t, offset=RtlpLFHKey)
            return res.l.int()

        def __fe_encode(self, object, **attrs):
            object = object.cast(self._FE_Encoded)

            # Cache some attributes
            if any(not hasattr(self, "_HEAP_ENTRY_{:s}".format(name)) for name in {'Heap', 'LFHKey'}):
                try:
                    self._HEAP_ENTRY_Heap, self._HEAP_ENTRY_LFHKey = self.getparent(type=HEAP), self.__RtlpLFHKey()
                except (ptypes.error.NotFoundError, AttributeError):
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
                self._HEAP_ENTRY_Heap, self._HEAP_ENTRY_LFHKey = self.getparent(type=HEAP), self.__RtlpLFHKey()

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
            res = self.d.li
            return bool(res['EntryOffset'].int())

        def EntryOffset(self):
            if not self.FrontEndQ():
                raise error.InvalidHeapType(self, 'EntryOffset', message='Unable to fetch the entry-offset for a non-frontend type')
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            res = self.d.li
            return res['EntryOffset'].int() * blocksize

        def SubSegment(self):
            if not self.FrontEndQ():
                raise error.InvalidHeapType(self, 'SubSegment', message='Unable to dereference the subsegment for a non-frontend type')
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
                raise error.InvalidHeapType(self, 'encode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)
            elif res.FrontEndQ():
                return self.__fe_encode(object, **attrs)
            return self.__be_encode(object, **attrs)

        def decode(self, object, **attrs):
            res = self.object
            if res['UnusedBytes'].int() == 5:
                raise error.InvalidHeapType(self, 'decode', message='_HEAP_ENTRY.UnusedBytes == 5 is currently unimplemented.', HEAP_ENTRY=self.object)
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

        def __RtlpHeapKey(self):
            RtlpHeapKey = self.source.expr('ntdll!RtlpHeapKey')
            t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
            res = self.new(t, offset=RtlpHeapKey)
            return res.l.int()

        def __GetPointerKey(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                return self.__RtlpHeapKey()
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                return self.__HeapPointerKey()
            raise error.InvalidPlatformException(self, '__GetPointerKey', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), expected=sdkddkver.NTDDI_WIN7)

        def encode(self, object, **attrs):
            try:
                res = self.__GetPointerKey()
                self._EncodedPointerKey = res

            # FIXME: Log that this encoded-pointer is non-encoded due to being unable to locate the key
            except:
                pass

            if hasattr(self, '_EncodedPointerKey'):
                return super(ENCODED_POINTER, self).encode(self._value_().set(object.get() ^ self._EncodedPointerKey))
            return super(ENCODED_POINTER, self).encode(object)

        def decode(self, object, **attrs):
            if not hasattr(self, '_EncodedPointerKey'):
                res = self.__GetPointerKey()
                self._EncodedPointerKey = res

            res = object.get() ^ self._EncodedPointerKey
            return super(ENCODED_POINTER, self).decode(self._value_().set(res))

        def summary(self):
            return "*{:#x} -> *{:#x}".format(self.get(), self.d.getoffset())

if 'HeapChunk':
    class _HEAP_CHUNK(pstruct.type):
        '''
        This is an internal definition that isn't defined by Microsoft, but is
        intended to support chunks that exist in either the frontend or the
        backend heap.
        '''
        def __ListEntry(self):

            # If we have a .__SubSegment__ attribute, then this is a frontend
            # chunk and this there's no linked-list for any free'd chunks.
            if hasattr(self, '__SubSegment__'):
                return ptype.undefined

            # Use the backing object here to check the busy flag since there's
            # really no need to decode anything when loading
            header = self['Header'].li
            if header.object.FreeQ():
                return dyn.clone(LIST_ENTRY, _object_=fptr(self.__class__, 'ListEntry'), _path_=('ListEntry',))

            # No linked-list as the chunk is busy
            return ptype.undefined

        def __ChunkFreeEntryOffset(self):

            # If we have a .__SubSegment__ attribute, then this should
            # definitely be a front-end chunk, and so we need to check
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
            return dyn.block(max({0, size - res}))

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
            t = header.Type()
            if not t['Chunk']:
                raise error.IncorrectChunkType(self, 'next', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            parent = self.getparent(HEAP)
            return parent.new(cls, offset=self.getoffset() + self['Header'].Size())

        def previous(self):
            cls, header = self.__class__, self['Header']
            if not header.BackEndQ():
                raise error.InvalidHeapType(self, 'previous', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            t = header.Type()
            if not t['Chunk']:
                raise error.IncorrectChunkType(self, 'previous', BackEndQ=header.BackEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
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
    class FrontEndHeapType(pint.enum, pint.uint8_t):
        _values_ = [
            ('Backend', 0),
            ('LAL', 1),
            ('LFH', 2),
        ]

    class FrontEndHeap(ptype.definition):
        cache = {}

    class FreeListBucket(LIST_ENTRY):
        class _HeapBucketLink(ptype.pointer_t):
            class _HeapBucketCounter(pstruct.type):
                _fields_ = [
                    (pint.uint16_t, 'UnknownEvenCount'),
                    (pint.uint16_t, 'AllocationCount'),
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
                    cls = self.__class__
                    raise error.InvalidHeapType(self, 'decode', message="Address {:#x} is not a valid HEAP_BUCKET".format(res.int()))
                return super(FreeListBucket._HeapBucketLink, self).decode(res, **attrs)

            def FrontEndQ(self):
                res = self.object.cast(pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t)
                return bool(res.int() & 1)
            def BackEndQ(self):
                return not self.BackEndQ()

            def summary(self):
                t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                res = self.object
                if res.cast(t).int() & 1:
                    return "FE :> {:s}".format(super(FreeListBucket._HeapBucketLink, self).summary())
                return "BE :> AllocationCount={:#x} UnknownEvenCount={:#x}".format(res['AllocationCount'].int(), res['UnknownEvenCount'].int())
            def details(self):
                t = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
                res = self.object.cast(t)
                if res.int() & 1:
                    return super(FreeListBucket._HeapBucketLink, self).summary()
                return self.object.details()
            repr = details

        _fields_ = [
            (fptr(_HEAP_CHUNK, 'ListEntry'), 'Flink'),
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

if 'LookasideList':
    @FrontEndHeap.define
    class LAL(parray.type):
        type = 1

        class _object_(pstruct.type):
            _fields_ = [
                (dyn.clone(SLIST_ENTRY, _object_=fptr(_HEAP_CHUNK, 'ListHead'), _path_=('ListHead',)), 'ListHead'),
                (pint.uint16_t, 'Depth'),
                (pint.uint16_t, 'MaximumDepth'),
                #(pint.uint32_t, 'none'),
                (pint.uint32_t, 'TotalAlloc'),
                (pint.uint32_t, 'AllocateMisses'),
                (pint.uint32_t, 'TotalFrees'),
                (pint.uint32_t, 'FreeMisses'),
                (pint.uint32_t, 'LastTotalAllocates'),
                (pint.uint32_t, 'LastAllocateMisses'),
                (dyn.array(pint.uint32_t, 2), 'Counters'),
                (dyn.block(4), 'Unknown'),
            ]

        HEAP_MAX_FREELIST = 0x80
        length = HEAP_MAX_FREELIST

if 'SegmentHeap':
    # FIXME: These are just placeholders for now
    class SEGMENT_HEAP(ptype.block):
        length = 0x5f0

    class HEAP_VS_CONTEXT(ptype.block):
        length = 0x48

    class HEAP_LFH_CONTEXT(ptype.block):
        length = 0x4d0

if 'LFH':
    class INTERLOCK_SEQ(pstruct.type):
        def __init__(self, **attrs):
            super(INTERLOCK_SEQ, self).__init__(**attrs)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (pint.uint16_t, 'Depth'),
                    (pint.uint16_t, 'FreeEntryOffset'),
                    (ULONG, 'Sequence'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (pint.uint16_t, 'Depth'),
                    (pint.uint16_t, 'FreeEntryOffset'),
                    (pint.uint_t, 'Sequence'),
                ])

            else:
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
            res = (0, 0)
            for block in self['Blocks']:
                res = ptypes.bitmap.push(res, (int(block['Header'].BusyQ()), 1))
            return res

        def __Blocks(self):
            pss = self['SubSegment'].li
            ss = pss.d.li

            # Copy the SubSegment as a hidden attribute so that the
            # chunk can quickly lookup what it's related to.
            chunk = dyn.clone(_HEAP_CHUNK, __SubSegment__=ss)
            return dyn.array(chunk, ss['BlockCount'].int())

        _fields_ = [
            (lambda self: P(HEAP_SUBSEGMENT), 'SubSegment'),
            (fptr(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),    # FIXME: figure out what this actually points to
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'SizeIndex'),
            (lambda self: ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'Signature'),
            (__Blocks, 'Blocks'),
        ]

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

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
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

            if self['Hint'].int():
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
        def __init__(self, **attrs):
            super(LFH_BLOCK_ZONE, self).__init__(**attrs)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (dyn.clone(LIST_ENTRY, _object_=P(LFH_BLOCK_ZONE), _path_=('ListEntry',)), 'ListEntry'),
                    (PVOID, 'FreePointer'),         # XXX: wtf is this for
                    (P(_HEAP_CHUNK), 'Limit'),
                    (P(HEAP_LOCAL_SEGMENT_INFO), 'SegmentInfo'),
                    (P(HEAP_USERDATA_HEADER), 'UserBlocks'),
                    (INTERLOCK_SEQ, 'AggregateExchg'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (dyn.clone(LIST_ENTRY, _object_=P(LFH_BLOCK_ZONE), _path_=('ListEntry',)), 'ListEntry'),
                    (ULONG, 'NextIndex'),
                    (dyn.block(4 if getattr(self, 'WIN64', False) else 0), 'padding(NextIndex)'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)

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
            def __Blocks(self):
                entry = self.getparent(USER_MEMORY_CACHE_ENTRY)
                res = [n.getoffset() for n in entry.p.value]
                idx = res.index(entry.getoffset()) + 1
                blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
                sz = idx * blocksize + self.new(_HEAP_ENTRY).a.size()
                block = dyn.clone(_HEAP_CHUNK, blocksize=lambda s, sz=sz: sz)
                return dyn.array(block, entry['AvailableBlocks'].int() * 8)

            _fields_ = [
                (dyn.array(pint.uint32_t, 4), 'unknown'),
                (__Blocks, 'Blocks'),
            ]
        def __init__(self, **attrs):
            super(USER_MEMORY_CACHE_ENTRY, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            f = self._fields_ = []
            f.extend([
                #(dyn.clone(SLIST_HEADER, _object_=UserBlocks), 'UserBlocks'),
                (SLIST_HEADER, 'UserBlocks'),   # XXX: check this offset
                (ULONG, 'AvailableBlocks'),     # AvailableBlocks * 8 seems to be the actual size
                (ULONG, 'MinimumDepth'),
            ])

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) <= sdkddkver.NTDDI_WIN8:
                f.extend([
                    (pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'Padding')
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
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
            return (fo - shift) / self.BlockSize()

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
            return ptypes.bitmap.string(res)

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
                    (pint.uint16_t, 'BlockSize'),
                    (pint.uint16_t, 'Flags'),
                    (pint.uint16_t, 'BlockCount'),
                    (pint.uint8_t, 'SizeIndex'),
                    (pint.uint8_t, 'AffinityIndex'),
                    (dyn.clone(SLIST_ENTRY, _object_=fptr(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'SFreeListEntry'),    # XXX: DelayFreeList
                    (ULONG, 'Lock'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (P(HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
                    (P(HEAP_USERDATA_HEADER), 'UserBlocks'),
                    (dyn.clone(SLIST_ENTRY, _object_=fptr(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'DelayFreeList'),
                    (INTERLOCK_SEQ, 'AggregateExchg'),
                    (USHORT, 'BlockSize'),
                    (USHORT, 'Flags'),
                    (USHORT, 'BlockCount'),
                    (pint.uint8_t, 'SizeIndex'),
                    (pint.uint8_t, 'AffinityIndex'),
                    (dyn.array(ULONG, 2), 'Alignment'),     # XXX: This is not really an alignment as claimed
                    (ULONG, 'Lock'),
                    (dyn.clone(SLIST_ENTRY, _object_=fptr(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'SFreeListEntry'),    # XXX: DelayFreeList
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

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN10:
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fptr(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'DeletedSubSegments'),
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'DeleteRateThreshold'),
                    (aligned, 'align(SegmentInfo)'),
                    (dyn.array(HEAP_LOCAL_SEGMENT_INFO, 128), 'SegmentInfo'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (dyn.clone(SLIST_HEADER, _object_=fptr(HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'DeletedSubSegments'),
                    (P(LFH_BLOCK_ZONE), 'CrtZone'),
                    (P(LFH_HEAP), 'LowFragHeap'),
                    (ULONG, 'Sequence'),
                    (ULONG, 'DeleteRateThreshold'),
                    (pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'padding(DeleteRateThreshold)'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)

    @FrontEndHeap.define
    class LFH_HEAP(pstruct.type, versioned):
        type = 2

        # FIXME: Figure out how caching in 'UserBlockCache' works

        # FIXME: Figure out why HEAP_LOCAL_DATA is defined as an array in all
        #        LFH material but only gets referenced as a single-element.

        def __SizeIndex(self, size):
            '''Return the size index when given a ``size``'''
            heap = self.getparent(HEAP)
            bucket = heap.Bucket(size)
            return bucket['SizeIndex'].int()
        def BucketByIndex(self, index):
            return self['Buckets'][index]
        def SegmentInfoByIndex(self, index):
            return self['LocalData']['SegmentInfo'][index]
        def Bucket(self, size):
            '''Return the LFH bin given a ``size``'''
            index = self.__SizeIndex(size)
            return self.BucketByIndex(index)
        def SegmentInfo(self, size):
            '''Return the HEAP_LOCAL_SEGMENT_INFO for a specific ``size``'''
            bin = self.Bucket(size)
            index = bin['SizeIndex'].int()
            return SegmentInfoByIndex(index)

        def __init__(self, **attrs):
            super(LFH_HEAP, self).__init__(**attrs)
            integral = ULONGLONG if getattr(self, 'WIN64', False) else ULONG
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            f = self._fields_ = []

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (rtltypes.RTL_CRITICAL_SECTION, 'Lock'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(LFH_BLOCK_ZONE)), 'SubSegmentZones'),
                    (ULONGLONG if getattr(self, 'WIN64', False) else ULONG, 'ZoneBlockSize'),
                    (P(HEAP), 'Heap'),
                    (ULONG, 'SegmentChange'),
                    (ULONG, 'SegmentCreate'),
                    (ULONG, 'SegmentInsertInFree'),
                    (ULONG, 'SegmentDelete'),
                    (ULONG, 'CacheAllocs'),
                    (ULONG, 'CacheFrees'),
                    (integral, 'SizeInCache'),
                    (HEAP_BUCKET_RUN_INFO, 'RunInfo'),
                    (aligned, 'align(UserBlockCache)'),
                    (dyn.array(USER_MEMORY_CACHE_ENTRY, 12), 'UserBlockCache'), # FIXME: Not sure what this cache is used for
                    (dyn.array(HEAP_BUCKET, 128), 'Buckets'),
                    (HEAP_LOCAL_DATA, 'LocalData'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                raise error.NdkUnsupportedVersion(self)

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (rtltypes.RTL_SRWLOCK, 'Lock'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(LFH_BLOCK_ZONE)), 'SubSegmentZones'),
                    (P(HEAP), 'Heap'),

                    (P(ptype.undefined), 'NextSegmentInfoArrayAddress'),
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
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

if 'Heap':
    class HEAP_UCR_DESCRIPTOR(pstruct.type):
        def __init__(self, **attrs):
            super(HEAP_UCR_DESCRIPTOR, self).__init__(**attrs)
            f = self._fields_ = []
            f.extend([
                (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_UCR_DESCRIPTOR)), 'ListEntry'),
                (dyn.clone(LIST_ENTRY, _path_=('UCRSegmentList',), _object_=fptr(HEAP_SEGMENT, 'UCRSegmentList')), 'SegmentEntry'),
                (P(lambda s: dyn.clone(ptype.undefined, length=s.p['Size'].li.int())), 'Address'),  # Sentinel Address
                (SIZE_T64 if getattr(self, 'WIN64', False) else SIZE_T, 'Size'),
            ])

    class HEAP_SEGMENT(pstruct.type, versioned):
        def Bounds(self):
            PAGE_SIZE = 0x1000
            ucr = self['NumberOfUncommittedPages'].int() * PAGE_SIZE
            start, end = (self[fld].li for fld in ['FirstEntry', 'LastValidEntry'])
            return start.int(), end.int() - ucr

        def Chunks(self):
            start, end = self.Bounds()
            res = self['FirstEntry'].d
            while res.getoffset() < end:
                yield res.l
                res = res.next()
            return

        def walk(self):
            yield self
            for n in self['SegmentListEntry'].walk():
                yield n
            return

        def __init__(self, **attrs):
            super(HEAP_SEGMENT, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
                raise error.NdkUnsupportedVersion(self)
                f.extend([
                    (LIST_ENTRY, 'ListEntry'),
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'Flags'),
                    (P(HEAP), 'Heap'),
                    (pint.uint32_t, 'LargestUnCommittedRange'),
                    (PVOID, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (PVOID, 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (P(_HEAP_UNCOMMMTTED_RANGE), 'UnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (P(_HEAP_ENTRY), 'LastEntryInSegment'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7+1:
                raise error.NdkUnsupportedVersion(self)
                f.extend([
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'Flags'),
                    (LIST_ENTRY, 'ListEntry'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'VirtualMemoryThreshold'),

                    (pint.uint32_t, 'SegmentReserve'),
                    (pint.uint32_t, 'SegmentCommit'),
                    (pint.uint32_t, 'DeCommitFreeBlockThreshold'),
                    (pint.uint32_t, 'DeCommitTotalFreeThreshold'),
                    (pint.uint32_t, 'TotalFreeSize'),
                    (pint.uint32_t, 'MaximumAllocationSize'),

                    (pint.uint16_t, 'ProcessHeapsListIndex'),
                    (pint.uint16_t, 'HeaderValidateLength'),
                    (pint.uint32_t, 'HeaderValidateCopy'),
                    (pint.uint16_t, 'NextAvailableTagIndex'),
                    (pint.uint16_t, 'MaximumTagIndex'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (LIST_ENTRY, 'UCRSegments'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
                f.extend([
                    (_HEAP_ENTRY, 'Entry'),
                    (pint.uint32_t, 'SegmentSignature'),
                    (pint.uint32_t, 'SegmentFlags'),
                    (lambda s: dyn.clone(LIST_ENTRY, _sentinel_='Blink', _path_=('SegmentListEntry',), _object_=fptr(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentListEntry'),   # XXX: entry comes from HEAP
                    (P(HEAP), 'Heap'),
                    (PVOID, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (aligned, 'align(FirstEntry)'),     # FIXME: padding, or alignment?
                    (P(_HEAP_CHUNK), 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (aligned, 'align(UCRSegmentList)'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=fptr(HEAP_UCR_DESCRIPTOR, 'SegmentEntry')), 'UCRSegmentList'),
                ])
            else:
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

    class HEAP_VIRTUAL_ALLOC_ENTRY(pstruct.type):
        def __init__(self, **attrs):
            super(HEAP_VIRTUAL_ALLOC_ENTRY, self).__init__(**attrs)
            f = self._fields_ = []

            # FIXME: is this right that HEAP.UCRIndex points to this?
            f.extend([
                (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'ListEntry'),
                (HEAP_ENTRY_EXTRA, 'ExtraStuff'),
                (pint.uint32_t, 'CommitSize'),
                (pint.uint32_t, 'ReserveSize'),
                (_HEAP_ENTRY, 'BusyBlock'),
            ])

    class HEAP(pstruct.type, versioned):
        def UncommittedRanges(self):
            '''Iterate through the list of UncommittedRanges(UCRList) for the HEAP'''
            for n in self['UCRList'].walk():
                yield n
            return

        def Segments(self):
            '''Iterate through the list of Segments(SegmentList) for the HEAP'''
            for n in self['SegmentList'].walk():
                yield n
            return

        def __HeapList(self, blockindex):
            '''Return the correct (recent) HEAP_LIST_LOOKUP structure according to the ``blockindex`` (size / blocksize)'''
            if not self['FrontEndHeapType']['LFH']:
                raise error.IncorrectHeapType(self, '__HeapList', message="Invalid value for FrontEndHeapType ({:s})".format(self['FrontEndHeapType'].summary()), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            p = self['BlocksIndex'].d.l
            while blockindex >= p['ArraySize'].int():
                if p['ExtendedLookup'].int() == 0:
                    raise error.ListHintException(self, '__HeapList', message='Unable to locate ListHint for blockindex', blockindex=blockindex, index=p['ArraySize'].int()-1, lookup=p)
                p = p['ExtendedLookup'].d.l
            return p

        def Bucket(self, size):
            '''Find the correct Heap Bucket from the ListHint for the given ``size``'''
            entry = self.ListHint(size)
            if entry['Blink'].int() == 0:
                raise error.NotFoundException(self, 'Bucket', message="Unable to find a Bucket for the requested size ({:#x})".format(size), entry=entry, size=size)
            return entry['Blink'].d.li

        def ListHint(self, size):
            '''Return the ListHint according to the specified ``size``'''
            if not self['FrontEndHeapType']['LFH']:
                raise error.IncorrectHeapType(self, 'ListHint', message="Invalid value for FrontEndHeapType ({:s})".format(self['FrontEndHeapType'].summary()), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            blocksize = 0x10 if getattr(self, 'WIN64', False) else 8
            size_and_header = size + blocksize
            bi = math.trunc(math.floor(size_and_header / float(blocksize)))
            heaplist = self.__HeapList(bi)
            return heaplist.ListHint(bi)

        class _Encoding(pstruct.type, versioned):
            _fields_ = [
                (lambda self: pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint_t, 'ReservedForAlignment'),
                (dyn.array(pint.uint32_t, 2), 'Keys')
            ]

        def __PointerKeyEncoding(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) != sdkddkver.NTDDI_WIN7:
                raise error.InvalidPlatformException(self, '__PointerKeyEncoding', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), expected=sdkddkver.NTDDI_WIN7)
            if self['EncodeFlagMask']:
                self.attributes['_HEAP_ENTRY_EncodeFlagMask'] = self['EncodeFlagMask'].li.int()
                self.attributes['_HEAP_ENTRY_Encoding'] = tuple(n.int() for n in self['Encoding'].li['Keys'])
            return ULONGLONG if getattr(self, 'WIN64', False) else ULONG

        class _HeapStatusBitmap(ptype.block):
            def bits(self):
                return self.size() << 3
            def bitmap(self):
                iterable = (ptypes.bitmap.new(six.byte2int(item), 8) for item in self.serialize())
                return reduce(ptypes.bitmap.push, map(ptypes.bitmap.reverse, iterable))
            def check(self, index):
                res, offset = self[index >> 3], index & 7
                return six.byte2int(res) & (2 ** offset) and 1
            def run(self):
                return self.bitmap()

            def details(self):
                bytes_per_row = 8
                iterable = iter(ptypes.bitmap.string(self.bitmap()))
                res = zip(*(iterable,) * 8 * bytes_per_row)
                items = map(str().join, res)
                width = len("{:x}".format(self.bits()))
                return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, 8 * i * bytes_per_row, width, 8 * i * bytes_per_row + 8 * bytes_per_row - 1, width, item) for i, item in enumerate(items)))

        def __init__(self, **attrs):
            super(HEAP, self).__init__(**attrs)
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)
            integral = pint.uint64_t if getattr(self, 'WIN64', False) else pint.uint32_t
            f = [(HEAP_SEGMENT, 'Segment')]

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) < sdkddkver.NTDDI_WIN8:
                f.extend([
                    (pint.uint32_t, 'Flags'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'CompatibilityFlags'),
                    (pint.uint32_t, 'EncodeFlagMask'),
                    (HEAP._Encoding, 'Encoding'),
                    (self.__PointerKeyEncoding, 'PointerKey'),
                    (pint.uint32_t, 'Interceptor'),
                    (pint.uint32_t, 'VirtualMemoryThreshold'),
                    (pint.uint32_t, 'Signature'),
                    (aligned, 'align(SegmentReserve)'), # FIXME: alignment or padding?
                    (integral, 'SegmentReserve'),
                    (integral, 'SegmentCommit'),
                    (integral, 'DeCommitFreeBlockThreshold'),
                    (integral, 'DeCommitTotalFreeThreshold'),
                    (integral, 'TotalFreeSize'),
                    (integral, 'MaximumAllocationSize'),
                    (pint.uint16_t, 'ProcessHeapsListIndex'),
                    (pint.uint16_t, 'HeaderValidateLength'),
                    (aligned, 'align(HeaderValidateCopy)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (pint.uint16_t, 'NextAvailableTagIndex'),
                    (pint.uint16_t, 'MaximumTagIndex'),
                    (aligned, 'align(TagEntries)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (integral, 'AlignRound'),
                    (integral, 'AlignMask'),

                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_=('SegmentListEntry',), _object_=fptr(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentList'),
                    (pint.uint16_t, 'FreeListInUseTerminate'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (P(HEAP_LIST_LOOKUP), 'BlocksIndex'),
                    (fptr(_HEAP_CHUNK, 'ListEntry'), 'UCRIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=fptr(_HEAP_CHUNK, 'ListEntry')), 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (FrontEndHeapType, 'FrontEndHeapType'),
                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                raise error.NdkUnsupportedVersion(self)

            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN10:
                f.extend([
                    (pint.uint32_t, 'Flags'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'CompatibilityFlags'),
                    (pint.uint32_t, 'EncodeFlagMask'),
                    (HEAP._Encoding, 'Encoding'),
                    (pint.uint32_t, 'Interceptor'),
                    (pint.uint32_t, 'VirtualMemoryThreshold'),
                    (pint.uint32_t, 'Signature'),
                    (aligned, 'align(SegmentReserve)'), # FIXME: alignment or padding?
                    (integral, 'SegmentReserve'),
                    (integral, 'SegmentCommit'),
                    (integral, 'DeCommitFreeBlockThreshold'),
                    (integral, 'DeCommitTotalFreeThreshold'),
                    (integral, 'TotalFreeSize'),
                    (integral, 'MaximumAllocationSize'),
                    (pint.uint16_t, 'ProcessHeapsListIndex'),
                    (pint.uint16_t, 'HeaderValidateLength'),
                    (aligned, 'align(HeaderValidateCopy)'),
                    (PVOID, 'HeaderValidateCopy'),
                    (pint.uint16_t, 'NextAvailableTagIndex'),
                    (pint.uint16_t, 'MaximumTagIndex'),
                    (aligned, 'align(TagEntries)'),
                    (P(HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (integral, 'AlignRound'),
                    (integral, 'AlignMask'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=P(HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_=('SegmentListEntry',), _object_=fptr(HEAP_SEGMENT, 'SegmentListEntry')), 'SegmentList'),
                    (pint.uint32_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (P(HEAP_LIST_LOOKUP), 'BlocksIndex'),
                    (fptr(_HEAP_CHUNK, 'ListEntry'), 'UCRIndex'),
                    (P(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=fptr(_HEAP_CHUNK, 'ListEntry')), 'FreeLists'),
                    (P(HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),   # FIXME: this is encoded with something somewhere
                    #(P(ptype.undefined), 'CommitRoutine'),
                    (rtltypes.RTL_RUN_ONCE, 'StackTraceInitVar'),
                    (P(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (FrontEndHeapType, 'FrontEndHeapType'),
                    (FrontEndHeapType, 'RequestedFrontEndHeapType'),

                    (aligned, 'align(FrontEndHeapUsageData)'),
                    (P(pint.uint16_t), 'FrontEndHeapUsageData'),    # XXX: this target doesn't seem right
                    (pint.uint16_t, 'FrontEndHeapMaximumIndex'),
                    (dyn.clone(self._HeapStatusBitmap, length=129 if getattr(self, 'WIN64', False) else 257), 'FrontEndHeapStatusBitmap'),

                    (aligned, 'align(Counters)'),   # FIXME: used to be a byte
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])

            else:
                raise error.NdkUnsupportedVersion(self)
            self._fields_ = f

    class HEAP_LIST_LOOKUP(pstruct.type):
        class _ListsInUseUlong(pbinary.array):
            _object_ = 1
            def run(self):
                return self.bitmap()
            def summary(self):
                objectname, _ = super(HEAP_LIST_LOOKUP._ListsInUseUlong, self).summary().split(' ', 2)
                res = self.run()
                return ' '.join((objectname, ptypes.bitmap.hex(res)))
            def details(self):
                bits = 32 if self.bits() < 256 else 64
                w = len("{:x}".format(self.bits()))
                res = ptypes.bitmap.split(self.run(), bits)
                return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + bits*i, bits*i, w, bits*i+bits-1, w, ptypes.bitmap.string(n)) for i, n in enumerate(reversed(res))))
            def repr(self):
                return self.details()

        class _ListsInUseUlong(parray.type):
            _object_ = pint.uint32_t

            # Make this type look like a pbinary.array sorta
            def bits(self):
                return self.size() << 3
            def bitmap(self):
                iterable = (ptypes.bitmap.new(item.int(), 32) for item in self)
                return reduce(ptypes.bitmap.push, map(ptypes.bitmap.reverse, iterable))

            def check(self, index):
                res, offset = self[index >> 5], index & 0x1f
                return res.int() & (2 ** offset) and 1
            def run(self):
                return self.bitmap()
            def summary(self):
                objectname, _ = super(HEAP_LIST_LOOKUP._ListsInUseUlong, self).summary().split(' ', 2)
                res = self.bitmap()
                return ' '.join((objectname, ptypes.bitmap.hex(res)))
            def details(self):
                bytes_per_item = self._object_().a.size()
                bits_per_item = bytes_per_item * 8
                bytes_per_row = bytes_per_item * (1 if self.bits() < 0x200 else 2)
                bits_per_row = bits_per_item * (1 if self.bits() < 0x200 else 2)

                items = ptypes.bitmap.split(self.bitmap(), bits_per_row)

                width = len("{:x}".format(self.bits()))
                return '\n'.join(("[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}".format(self.getoffset() + i * bytes_per_row, i * bits_per_row, width, i * bits_per_row + bits_per_row - 1, width, ptypes.bitmap.string(item)) for i, item in enumerate(items)))

            def repr(self):
                return self.details()

        def __init__(self, **attrs):
            super(HEAP_LIST_LOOKUP, self).__init__(**attrs)
            f = self._fields_ = []
            aligned = dyn.align(8 if getattr(self, 'WIN64', False) else 4)

            f.extend([
                (P(HEAP_LIST_LOOKUP), 'ExtendedLookup'),

                (ULONG, 'ArraySize'),
                (ULONG, 'ExtraItem'),
                (ULONG, 'ItemCount'),
                (ULONG, 'OutOfRangeItems'),
                (ULONG, 'BaseIndex'),

                (aligned, 'align(ListHead)'),
                (P(dyn.clone(LIST_ENTRY, _path_=('ListEntry',), _object_=fptr(_HEAP_CHUNK, 'ListEntry'))), 'ListHead'),
                (P(lambda s: dyn.clone(HEAP_LIST_LOOKUP._ListsInUseUlong, length=s.p.ListHintsCount() >> 5)), 'ListsInUseUlong'),
                (P(lambda s: dyn.array(dyn.clone(FreeListBucket, _object_=fptr(_HEAP_CHUNK, 'ListEntry'), _path_=('ListEntry',), _sentinel_=s.p['ListHead'].int()), s.p.ListHintsCount())), 'ListHints'),
            ])

        def ListHintsCount(self):
            '''Return the number of FreeLists entries within this structure'''
            return self['ArraySize'].li.int() - self['BaseIndex'].li.int()

        def ListHint(self, blockindex):
            '''Find the correct (recent) ListHint for the specified ``blockindex``'''
            res = blockindex - self['BaseIndex'].int()
            if 0 > res or self.ListHintsCount() < res:
                raise error.NdkAssertionError(self, 'ListHint', message="Requested BlockIndex is out of bounds : {:d} <= {:d} < {:d}".format(self['BaseIndex'].int(), blockindex, self['ArraySize'].int()))
            freelist = self['ListsInUseUlong'].d.l
            list = self['ListHints'].d.l
            if freelist.check(res):
                return list[res]
            return list[res]

        def enumerate(self):
            inuse, hints = (self[fld].d.li for fld in ['ListsInUseUlong', 'ListHints'])
            if inuse.bits() != len(hints):
                raise error.NdkAssertionError(self, 'ListHint', message="ListsInUseUlong ({:d}) is a different length than ListHints ({:d})".format(inuse.bits(), len(hints)))
            for i, item in enumerate(hints):
                if inuse.check(i):
                    yield i, item
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
        pid = int(sys.argv[1])
        print "opening process {:d}".format(pid)
        handle = openprocess(pid)
    else:
        handle = getcurrentprocess()
        print 'using current process'
    ptypes.setsource(ptypes.provider.WindowsProcessHandle(handle))

    # grab peb
    import ndk
    pebaddress = GetProcessBasicInformation(handle).PebBaseAddress
    z = ndk.PEB(offset=pebaddress).l

    # grab heap
    if len(sys.argv) > 2:
        heaphandle = eval(sys.argv[2])
        for x in z['ProcessHeaps'].d.l:
            print hex(x.int()), hex(heaphandle)
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
#    print a.l
#    b = a['Segment']
#    print a['BlocksIndex']
#    print a['UCRIndex']
#    print list(b.walk())

    c = a['FreeLists']

#    list(c.walk())
 #   x = c['Flink'].d.l

 #   print x['Value']['a']
 #   x =  x['Entry']['Flink'].d.l
#    print [x for x in c.walk()]
#    print a['BlocksIndex']

#    print a['FrontEndHeap'].d.l
#
#    print a['CommitRoutine']

#    print c['Flink'].d.l

#    print list(c.walk())
#    print c['Flink'].d.l['Flink'].d.l['Flink'].d.l
#    d = [x for x in c.walk()]
#    print help(d[1])
