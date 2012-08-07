from WinNT import *
import ptypes,sdkddkver
import logging

class HEAP_LOCK(pint.uint32_t): pass

if 'UCR':
    class HEAP_UNCOMMMTTED_RANGE(pstruct.type):
        def walk(self):
            yield self
            while True:
                p = self['Next'].d
                if int(p) == 0:
                    break
                yield p.l
            return

    HEAP_UNCOMMMTTED_RANGE._fields_ = [
        (dyn.pointer(HEAP_UNCOMMMTTED_RANGE), 'Next'),
        (pint.uint32_t, 'Address'),
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'Filler')
    ]

if False:
    class _HEAP_ENTRY_FLAGS(pbinary.struct):
        _fields_ = [
            (1, 'Busy'), (1, 'ExtraPresent'), (1, 'FillPattern'), (1, 'VirtualAlloc'),
            (1, 'LastEntry'), (1, 'FFU1'), (1, 'FFU2'), (1, 'NoCoalesce')
        ]

    class _HEAP_ENTRY(pstruct.type):
        _fields_ = [
            (USHORT, 'Size'),
            (USHORT, 'PreviousSize'),
            (UCHAR, 'Cookie'),
            (_HEAP_ENTRY_FLAGS, 'Flags'),
            (UCHAR, 'UnusedBytes'),
            (UCHAR, 'SegmentIndex'),
        ]

    class _HEAP_ENTRY(pstruct.type):
        _fields_ = [
            (USHORT, 'Size'),
            (USHORT, 'PreviousSize'),
            (UCHAR, 'SegmentIndex'),
            (_HEAP_ENTRY_FLAGS, 'Flags'),
            (UCHAR, 'UnusedBytes'),
            (UCHAR, 'SmallTagIndex'),
        ]

    class _HEAP_ENTRY(pstruct.type, versioned):
        class XP_ENTRY(pstruct.type):
            _fields_ = [
                (USHORT, 'Size'),
                (UCHAR, 'Flags'),
                (UCHAR, 'SmallTagIndex'),
            ]

        class LF_ENTRY(pstruct.type):
            class __union(dyn.union): _fields_ = [(UCHAR,'SegmentOffset'),(UCHAR,'LFHFlags')]

            _fields_ = [
                (PVOID, 'SubSegmentCode'),
                (USHORT, 'PreviousSize'),
                (__union, 'Union'),         # FIXME: This naming scheme is lame
                (UCHAR, 'UnusedBytes'),
            ]

        class unknown_entry_b(pstruct.type):
            _fields_ = [(USHORT, 'FunctionIndex'), (USHORT, 'ContextValue')]

        class unknown_entry_c(pstruct.type):
            _fields_ = [(ULONG, 'InterceptorValue'), (USHORT, 'UnusedBytesLength'), (UCHAR, 'EntryOffset'), (UCHAR, 'ExtendedBlockSignature')]

        class unknown_entry_d(pstruct.type):
            _fields_ = [(ULONG, 'Code1'), (USHORT, 'Code2'), (UCHAR, 'Code3'), (UCHAR, 'Code4')]

        def __init__(self, **attrs):
            super(_HEAP_ENTRY, self).__init__(**attrs)
            f = []
            if True:
                f.extend(self.XP_ENTRY._fields_)
            elif True:
                f.extend(self.LF_ENTRY._fields_)
            elif True:
                f.extend(self.unknown_entry_b)
            elif True:
                f.extend(self.unknown_entry_c)
            elif True:
                f.extend(self.unknown_entry_d)
            else:   
                f.append((ULONGLONG,'AggregateCode'))
            self._fields_ = f

    class HEAP_ENTRY(pstruct.type):
        _fields_ = [
            (SIZE_T, 'Size'),
            (USHORT, 'Flags'),
            (USHORT, 'Checksum')
        ]

    class _HEAP_ENTRY(ULONGLONG): pass

    class HEAP_FREE_ENTRY(pstruct.type):
        _fields_ = [
            (_HEAP_ENTRY, 'Entry'),
            (LIST_ENTRY, 'FreeList'),
        ]

class _HEAP_ENTRY(dyn.block(8)): pass

if 'HeapMeta':
    class HEAP_COUNTERS(pstruct.type):
        _fields_ = [
            (SIZE_T, 'TotalMemoryReserved'),
            (SIZE_T, 'TotalMemoryCommitted'),
            (SIZE_T, 'TotalMemoryLargeUCR'),
            (SIZE_T, 'TotalSizeInVirtualBlocks'),
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
            (ULONG, 'CompactHeapCalls'),
            (ULONG, 'CompactedUCRs'),
            (ULONG, 'AllocAndFreeOps'),
            (ULONG, 'InBlockDeccommits'),
            (ULONG, 'InBlockDeccomitSize'),
            (ULONG, 'HighWatermarkSize'),
            (ULONG, 'LastPolledSize'),
        ]

    class HEAP_TUNING_PARAMETERS(pstruct.type):
        _fields_ = [(ULONG, 'CommitThresholdShift'),(SIZE_T, 'MaxPreCommittThreshold')]

    class HEAP_LIST_LOOKUP(pstruct.type): pass
    HEAP_LIST_LOOKUP._fields_ = [
        (dyn.pointer(HEAP_LIST_LOOKUP), 'ExtendedLookup'),

        (ULONG, 'ArraySize'),
        (ULONG, 'ExtraItem'),
        (ULONG, 'ItemCount'),
        (ULONG, 'OutOfRangeItems'),
        (ULONG, 'BaseIndex'),

        (dyn.pointer(LIST_ENTRY), 'ListHead'),
        (dyn.pointer(ULONG), 'ListsInUseUlong'),
        (dyn.pointer(LIST_ENTRY), 'ListHints'),
    ]

    class HEAP_PSEUDO_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (SIZE_T, 'Size'),
        ]

    class HEAP_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (ULONG, 'Size'),
            (USHORT, 'TagIndex'),
            (USHORT, 'CreatorBackTraceIndex'),
            (dyn.clone(pstr.wstring, length=24), 'TagName')
        ]

if False:
    class HEAP_ENTRY(dyn.union):
        #FIXME: It'd be cool to version this so there's no unions

        class LF_ENTRY(pstruct.type):
            class __union(dyn.union):
                root = dyn.block(8)
                class __a(pstruct.type):
                    _fields_ = [(pint.uint8_t, 'LFHFlags'), (pint.uint8_t, 'UnusedBytes')]
                    
                class __b(pstruct.type):
                    _fields_ = [(pint.uint16_t, 'FunctionIndex'), (pint.uint16_t, 'ContextValue')]

                class __c(pstruct.type):
                    _fields_ = [(pint.uint32_t, 'InterceptorValue'), (pint.uint16_t, 'UnusedBytesLength')]

                class __d(pstruct.type):
                    _fields_ = [(pint.uint8_t, 'EntryOffset'), (pint.uint8_t, 'ExtendedBlockSignature')]

                class __e(pstruct.type):
                    _fields_ = [(pint.uint32_t, 'Code1'), (pint.uint16_t, 'Code2')]

    #            # FIXME: I need to label each of these subsegment codes somehow
                _fields_ = [
                    (__a, 'a'),
                    (__b, 'b'),
                    (__c, 'c'),
                    (__d, 'd'),
                    (__e, 'e'),
                    (pint.uint8_t, 'Code3'),
                ]

            _fields_ = [
                (dyn.pointer(ptype.type), 'SubSegmentCode'),
                (pint.uint16_t, 'PreviousSize'),
                (__union, 'Union'),         # FIXME: This naming scheme is lame
                (pint.uint8_t, 'Code4'),
            ]

        class LF_ENTRY(pstruct.type):
            _fields_ = [
            ]

        _fields_ = [
            (pint.uint64_t, 'AggregateCode'),
            (XP_ENTRY, 'a'),
#            (LF_ENTRY, 'b'),
        ]

    class HEAP_ENTRY(LIST_ENTRY): pass

    class imm_Blocks(pstruct.type):
        _fields_ = [
            (pint.uint32_t, 'ExtendedLookup'),
            (pint.uint32_t, 'ArraySize'),
            (pint.uint32_t, 'ExtraItem'),
            (pint.uint32_t, 'ItemCount'),
            (pint.uint32_t, 'OutOfRangeItems'),
            (pint.uint32_t, 'BaseIndex'),
            (pint.uint32_t, 'ListHead'),
            (pint.uint32_t, 'ListsInUseUlong'),
            (pint.uint32_t, 'ListHints'),
        ]

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

            (dyn.pointer(pint.uint8_t), 'pBitmap'), # XXX

            (dyn.pointer(HEAP_FREE_ENTRY), 'pBucket'),  # XXX
            (lambda s: dyn.pointer(dyn.array(HEAP_FREE_ENTRY, s['NumBuckets'].l.int())), 'Buckets'),
            (lambda s: dyn.array(pint.uint32_t, s['NumBuckets'].l.int()/32), 'Bitmap'),
        ]

if True:
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

            (lambda s: dyn.array(dyn.pointer(HEAP_FREE_ENTRY), int(s['NumBuckets'].l)), 'Buckets'),
            (lambda s: dyn.clone(pbinary.array, _object_=1, length=int(s['NumBuckets'].l)), 'Bitmask'),    # XXX: This array is too huge
    #        (lambda s: dyn.block(int(s['NumBuckets'].l)/8), 'Bitmask'),
        ]

    class LAL(parray.type):
        class __object_(pstruct.type):
            _fields_ = [
                (pint.uint32_t, 'ListHead'),
                (pint.uint16_t, 'Depth'),
                (pint.uint16_t, 'MaxDepth'),
                (pint.uint32_t, 'none'),
                (pint.uint32_t, 'TotalAlloc'),
                (pint.uint32_t, 'AllocMiss'),
                (pint.uint32_t, 'TotalFrees'),
                (pint.uint32_t, 'FreeMiss'),
                (pint.uint32_t, 'AllocLastTotal'),
                (pint.uint32_t, 'LastAllocateMiss'),
                (dyn.block(12), 'Unknown'),
            ]

        _object_ = __object_
        HEAP_MAX_FREELIST = 0x80
        length = HEAP_MAX_FREELIST

    class LF(pstruct.type):
        class HeapBucketRunInfo(pstruct.type):
            _fields_ = [(pint.uint32_t, 'Bucket'), (pint.uint32_t, 'RunLength')]

        class UserMemoryCache(pstruct.type):
            _fields_ = [(pint.uint32_t, 'Next'), (pint.uint16_t, 'Depth'), (pint.uint16_t, 'Sequence'), (pint.uint32_t, 'AvailableBlocks'), (pint.uint32_t, 'Reserved')]

        class Bucket(pstruct.type):
            class __Flag(pbinary.struct):
                _fields_ = [(1, 'UseAffinity'), (2, 'DebugFlags')]

            _fields_ = [
                (pint.uint16_t, 'BlockUnits'),
                (pint.uint8_t, 'SizeIndex'),
                (__Flag, 'Flag')
            ]

        class LocalData(pstruct.type):
            class LocalSegmentInfo(pstruct.type):
    #            FIXME: I stopped here
                _fields_ = [
                    (pint.uint32_t, 'Hint'),
                    (pint.uint32_t, 'ActiveSubSegment'),

                    (pint.uint32_t, 'Next'),
                    (pint.uint16_t, 'Depth'),
                    (pint.uint16_t, 'Seq'),
                    (pint.uint32_t, 'TotalBlocks'),
                    (pint.uint32_t, 'SubSegmentCounts'),
                    (pint.uint32_t, 'LocalData'),
                    (pint.uint32_t, 'LastOpSequence'),
                    (pint.uint16_t, 'BucketIndex'),
                    (pint.uint16_t, 'LastUsed'),
                    (pint.uint32_t, 'Reserved'),
                ]

                def blocksize(self):
                    return 0x68

            _fields_ = [
                (pint.uint32_t, 'Next'),
                (pint.uint16_t, 'Depth'),
                (pint.uint16_t, 'Seq'),
                (pint.uint32_t, 'CtrZone'),
                (pint.uint32_t, 'LowFragHeap'),
                (pint.uint32_t, 'Sequence1'),
                (pint.uint32_t, 'Sequence2'),
                (dyn.array(LocalSegmentInfo, 128), 'SegmentInfo')
            ]

        _fields_ = [
            (pint.uint32_t, 'Lock'),
            (pint.uint32_t, 'field_4'),
            (pint.uint32_t, 'field_8'),
            (pint.uint32_t, 'field_c'),
            (pint.uint32_t, 'field_10'),
            (pint.uint32_t, 'field_14'),
            (pint.uint32_t, 'SubSegmentZone_Flink'),
            (pint.uint32_t, 'SubSegmentZone_Blink'),
            (pint.uint32_t, 'ZoneBlockSize'),
            (pint.uint32_t, 'Heap'),
            (pint.uint32_t, 'SegmentChange'),
            (pint.uint32_t, 'SegmentCreate'),
            (pint.uint32_t, 'SegmentInsertInFree'),
            (pint.uint32_t, 'SegmentDelete'),
            (pint.uint32_t, 'CacheAllocs'),
            (pint.uint32_t, 'CacheFrees'),
            (pint.uint32_t, 'SizeInCache'),
            (pint.uint32_t, 'Padding'),

            (HeapBucketRunInfo, 'RunInfo'),
            (dyn.array(UserMemoryCache, 12), 'UserBlockCache'),
            (dyn.array(Bucket, 128), 'Buckets'),
            (LocalData, 'LocalData')
        ]
 
if 'PageHeap':
    class DPH_BLOCK_INFORMATION(pstruct.type):
        '''Structure of a Page Heap Block when Full Page Heap is Enabled'''
        # http://msdn.microsoft.com/en-us/library/ms220938(VS.80).aspx
        _fields_ = [
            (ULONG, 'StartStamp'),
            (PVOID, 'Heap'),
            (SIZE_T, 'RequestedSize'),
            (SIZE_T, 'ActualSize'),
            (LIST_ENTRY, 'FreeQueue'),
            (PVOID, 'StackTrace'),
            (ULONG, 'EndStamp'),
        ]

if 'Heap':
    class _HEAP_UCR_DESCRIPTOR(pstruct.type):
        _fields_ = [
            (LIST_ENTRY, 'ListEntry'),
            (LIST_ENTRY, 'SegmentEntry'),
            (PVOID, 'Address'),
            (SIZE_T, 'Size'),
        ]
    
    # FIXME: ensure this is complete
    class _HEAP_SEGMENT(pstruct.type, versioned):
        def __init__(self, **attrs):
            super(_HEAP_SEGMENT, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_VISTA:
                raise NotImplementedError
                f.extend([
                    (LIST_ENTRY, 'ListEntry'),
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'Flags'),
                    (dyn.pointer(HEAP), 'Heap'),
                    (pint.uint32_t, 'LargestUnCommittedRange'),
                    (PVOID, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (dyn.pointer(_HEAP_ENTRY), 'FirstEntry'),
                    (dyn.pointer(_HEAP_ENTRY), 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (dyn.pointer(HEAP_UNCOMMMTTED_RANGE), 'UnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (dyn.pointer(_HEAP_ENTRY), 'LastEntryInSegment'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (_HEAP_ENTRY, 'Entry'),
                    (pint.uint32_t, 'SegmentSignature'),
                    (pint.uint32_t, 'SegmentFlags'),
                    (LIST_ENTRY, 'SegmentListEntry'),
                    (dyn.pointer(HEAP), 'Heap'),
                    (pint.uint32_t, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (dyn.pointer(_HEAP_ENTRY), 'FirstEntry'),
                    (dyn.pointer(_HEAP_ENTRY), 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (dyn.clone(LIST_ENTRY, _object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR)), 'UCRSegmentList'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                raise NotImplementedError
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
                    (dyn.pointer(HEAP_TAG_ENTRY), 'TagEntries'),
                    (LIST_ENTRY, 'UCRSegments'),
                ])
            else:
                raise NotImplementedError
            self._fields_ = f

    class HEAP(pstruct.type, versioned):
        class __FrontEndHeapType(pint.uint8_t, pint.enum):
            _values_ = [
                (0, 'unknown'),
            ]

        def __FrontEndHeap(self):
            t = int(self['FrontEndHeapType'].l)
            if t == 0:
                return LAL
            elif t == 2:
                return LF
            logging.warn('Unknown FrontEndHeapType 0x%x'% t)
            return ptype.type

        def __init__(self, **attrs):
            super(HEAP, self).__init__(**attrs)

            f = [
                (_HEAP_SEGMENT, 'Segment'),
            ]

            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_VISTA:
                raise NotImplementedError
                f.extend([
                    (pint.uint32_t, 'Flags'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'CompatibilityFlags'),
                    (pint.uint32_t, 'EncodeFlagMask'),
                    (LIST_ENTRY, 'Encoding'),
                    (pint.uint32_t, 'PointerKey'),
                    (pint.uint32_t, 'Interceptor'),
                    (pint.uint32_t, 'VirtualMemoryThreshold'),
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'SegmentReserve'),
                    (pint.uint32_t, 'SegmentCommit'),
                    (pint.uint32_t, 'DeCommitFreeBlockThreshold'),
                    (pint.uint32_t, 'DeCommitTotalFreeThreshold'),
                    (pint.uint32_t, 'TotalFreeSize'),
                    (pint.uint32_t, 'MaximumAllocationSize'),
                    (pint.uint16_t, 'ProcessHeapsListIndex'),
                    (pint.uint16_t, 'HeaderValidateLength'),
                    (dyn.pointer(ptype.type), 'HeaderValidateCopy'),
                    (pint.uint16_t, 'NextAvailableTagIndex'),
                    (pint.uint16_t, 'MaximumTagIndex'),
                    (dyn.pointer(HEAP_TAG_ENTRY), 'TagEntries'),
                    (LIST_ENTRY, 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (LIST_ENTRY, 'VirtualAllocedBlocks'),   # XXX: unknown type
                    (LIST_ENTRY, 'SegmentList'),
                    (pint.uint32_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (dyn.pointer(HeapCache), 'LargeBlocksIndex'),
                    (dyn.pointer(ptype.type), 'UCRIndex'),
                    (dyn.pointer(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _object_=dyn.pointer(HEAP_FREE_ENTRY)), 'FreeLists'),      # XXX:
                    (dyn.pointer(HEAP_LOCK), 'LockVariable'),
                    (dyn.pointer(pint.uint32_t), 'CommitRoutine'),
#                    (dyn.pointer(self.__FrontEndHeap), 'FrontEndHeap'),
                    (PVOID, 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (self.__FrontEndHeapType, 'FrontEndHeapType'),
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (pint.uint32_t, 'Flags'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'CompatibilityFlags'),
                    (pint.uint32_t, 'EncodeFlagMask'),
                    (LIST_ENTRY, 'Encoding'),
                    (pint.uint32_t, 'PointerKey'),
                    (pint.uint32_t, 'Interceptor'),
                    (pint.uint32_t, 'VirtualMemoryThreshold'),
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'SegmentReserve'),
                    (pint.uint32_t, 'SegmentCommit'),
                    (pint.uint32_t, 'DeCommitFreeBlockThreshold'),
                    (pint.uint32_t, 'DeCommitTotalFreeThreshold'),
                    (pint.uint32_t, 'TotalFreeSize'),
                    (pint.uint32_t, 'MaximumAllocationSize'),
                    (pint.uint16_t, 'ProcessHeapsListIndex'),
                    (pint.uint16_t, 'HeaderValidateLength'),
                    (dyn.pointer(ptype.type), 'HeaderValidateCopy'),
                    (pint.uint16_t, 'NextAvailableTagIndex'),
                    (pint.uint16_t, 'MaximumTagIndex'),
                    (dyn.pointer(HEAP_TAG_ENTRY), 'TagEntries'),
                    (LIST_ENTRY, 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (LIST_ENTRY, 'VirtualAllocedBlocks'),   # XXX: unknown type
    #                (LIST_ENTRY, 'SegmentList'),    # XXX: always points to +10
                    (LIST_ENTRY, 'SegmentList'),
                    (pint.uint16_t, 'FreeListInUseTerminate'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
#                    (dyn.pointer(HeapCache), 'LargeBlocksIndex'),
                    (PVOID, 'LargeBlocksIndex'),
                    (dyn.pointer(ptype.type), 'UCRIndex'),  # XXX
                    (dyn.pointer(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (LIST_ENTRY, 'FreeLists'),      # XXX:
                    (dyn.pointer(HEAP_LOCK), 'LockVariable'),
                    (dyn.pointer(ptype.type), 'CommitRoutine'),
#                    (dyn.pointer(self.__FrontEndHeap), 'FrontEndHeap'),
                    (PVOID, 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (self.__FrontEndHeapType, 'FrontEndHeapType'),
                    (pint.uint8_t, 'FrontEndAlignment'),
                    (HEAP_COUNTERS, 'Counters'),
                    (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                raise NotImplementedError
                f.extend([
                    (dyn.pointer(HEAP_UNCOMMMTTED_RANGE), 'UnusedUnCommittedRanges'),   # FIXME
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (LIST_ENTRY, 'VirtualAllocdBlocks'),
                    (dyn.array(dyn.pointer(_HEAP_SEGMENT), 64), 'Segments'),
                    (dyn.block(0x10), 'FreeListInUseLong'),
                    (pint.uint16_t, 'FreeListInUseTerminate'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),

                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (pint.uint32_t, 'LargeBlocksIndex'),

    #                (pint.uint32_t, 'PsuedoTagentries'),
    #                (dyn.array(LIST_ENTRY, 128), 'FreeLists'),

    #                (pint.uint32_t, 'LockVariable'),
    #                (pint.uint32_t, 'CommitRoutine'),
    #                (pint.uint32_t, 'FrontEndHeap'),
    #                (pint.uint32_t, 'FrontHeapLockCount'),
    #                (pint.uint8_t, 'FrontEndHeapType'),
    #                (pint.uint8_t, 'LastSegmentIndex'),
                ])

            self._fields_ = f

class ProcessHeapEntries(parray.type):
    _object_ = dyn.pointer(HEAP)

    def walk(self):
        for x in self:
            yield x.d
        return

if __name__ == '__main__':
    import sys
    import ptypes,ndk
    import ctypes
    def openprocess (pid):
        k32 = ctypes.WinDLL('kernel32.dll')
        res = k32.OpenProcess(0x30 | 0x0400, False, pid)
        return res

    def getcurrentprocess ():
        k32 = ctypes.WinDLL('kernel32.dll')
        return k32.GetCurrentProcess()

    def getPBIObj (handle):
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
        print 'opening process %d'% pid
        handle = openprocess(pid)
    else:
        handle = getcurrentprocess()
        print 'using current process'
    ptypes.setsource(ptypes.provider.WindowsProcessHandle(handle))

    # grab peb
    import ndk
    pebaddress = getPBIObj(handle).PebBaseAddress
    z = ndk.PEB(offset=pebaddress).l

    # grab heap
    if len(sys.argv) > 2:
        heaphandle = eval(sys.argv[2])
        for x in z['ProcessHeaps'].d.l:
            print hex(x.int()),hex(heaphandle)
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
#    print a['LargeBlocksIndex']
#    print a['UCRIndex']
#    print list(b.walk())

    c = a['FreeLists']

#    list(c.walk())
 #   x = c['Flink'].d.l

 #   print x['Value']['a']
 #   x =  x['Entry']['Flink'].d.l
#    print [x for x in c.walk()]
#    print a['LargeBlocksIndex']

#    print a['FrontEndHeap'].d.l
#
#    print a['CommitRoutine']

#    print c['Flink'].d.l

#    print list(c.walk())
#    print c['Flink'].d.l['Flink'].d.l['Flink'].d.l
#    d = [x for x in c.walk()]
#    print help(d[1])
