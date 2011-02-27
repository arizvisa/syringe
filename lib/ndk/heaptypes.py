from WinNT import *
import ptypes,sdkddkver

class HEAP_LOCK(pint.uint32_t): pass

class HEAP_UNCOMMITTED_RANGE(pstruct.type):
    def walk(self):
        yield self
        while True:
            p = self['Next'].d
            if int(p) == 0:
                break
            yield p.l
        return

HEAP_UNCOMMITTED_RANGE._fields_ = [
        (dyn.pointer(HEAP_UNCOMMITTED_RANGE), 'Next'),
        (pint.uint32_t, 'Address'),
        (pint.uint32_t, 'Size'),
        (pint.uint32_t, 'Filler')
    ]

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

    class XP_ENTRY(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Size'),
            (pint.uint8_t, 'Flags'),
            (pint.uint8_t, 'SmallTagIndex'),
        ]

    _fields_ = [
        (pint.uint64_t, 'AggregateCode'),
        (XP_ENTRY, 'a'),
        (LF_ENTRY, 'b'),
    ]

class HEAP_FREE_ENTRY(pstruct.type): pass
HEAP_FREE_ENTRY._fields_ = [
        (HEAP_ENTRY, 'Entry'),
        (dyn.clone(LIST_ENTRY, _object_=HEAP_FREE_ENTRY), 'FreeList')
    ]

class HEAP_PSEUDO_TAG_ENTRY(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Allocs'),
        (pint.uint32_t, 'Frees'),
        (pint.uint32_t, 'Size'),
    ]
        
class HEAP_SEGMENT(pstruct.type):
    _fields_ = [
        (pint.uint64_t, 'Header'),
        (pint.uint32_t, 'Signature'),
        (pint.uint32_t, 'Flags'),
        (pint.uint32_t, 'Heap'),
        (pint.uint32_t, 'LargestUnCommittedRange'),
        (pint.uint32_t, 'BaseAddress'),
        (pint.uint32_t, 'NumberOfPages'),
        (dyn.pointer(HEAP_ENTRY), 'FirstEntry'),
        (dyn.pointer(HEAP_ENTRY), 'LastValidEntry'),
        (pint.uint32_t, 'NumberOfUnCommittedPages'),
        (pint.uint32_t, 'NumberOfUnCommittedRanges'),
        (dyn.pointer(HEAP_UNCOMMITTED_RANGE), 'UncommittedRanges'),
        (pint.uint16_t, 'AllocatorBackTraceIndex'),
        (pint.uint16_t, 'Reserved'),
        (dyn.pointer(HEAP_ENTRY), 'LastEntryInSegment')
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

        (lambda s: dyn.array(dyn.pointer(HEAP_FREE_ENTRY), int(s['NumBuckets'].l)), 'Buckets'),
        (lambda s: dyn.clone(pbinary.array, _object_=1, length=int(s['NumBuckets'].l)), 'Bitmask'),    # XXX: This array is too huge
#        (lambda s: dyn.block(int(s['NumBuckets'].l)/8), 'Bitmask'),
    ]

imm_HeapCache = ptypes.debugrecurse(imm_HeapCache)

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

class HEAP_TAG_ENTRY(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Allocs'),
        (pint.uint32_t, 'Frees'),
        (pint.uint32_t, 'Size'),
        (pint.uint16_t, 'TagIndex'),
        (pint.uint16_t, 'CreatorBackTraceIndex'),
        (dyn.clone(pstr.wstring, length=24), 'TagName')
    ]

class HEAP_COUNTERS(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'TotalMemoryReserved'),
        (pint.uint32_t, 'TotalMemoryCommitted'),
        (pint.uint32_t, 'TotalMemoryLargeUCR'),
        (pint.uint32_t, 'TotalSizeInVirtualBlocks'),
        (pint.uint32_t, 'TotalSegments'),
        (pint.uint32_t, 'TotalUCRs'),
        (pint.uint32_t, 'CommittOps'),
        (pint.uint32_t, 'DeCommitOps'),
        (pint.uint32_t, 'LockAcquires'),
        (pint.uint32_t, 'LockCollisions'),
        (pint.uint32_t, 'CommitRate'),
        (pint.uint32_t, 'DecommittRate'),
        (pint.uint32_t, 'CommitFailures'),
        (pint.uint32_t, 'InBlockCommitFailures'),
        (pint.uint32_t, 'CompactHeapCalls'),
        (pint.uint32_t, 'CompactedUCRs'),
        (pint.uint32_t, 'AllocAndFreeOps'),
        (pint.uint32_t, 'InBlockDeccommits'),
        (pint.uint32_t, 'InBlockDeccomitSize'),
        (pint.uint32_t, 'HighWatermarkSize'),
        (pint.uint32_t, 'LastPolledSize'),
    ]

class HEAP_TUNING_PARAMETERS(pstruct.type):
    _fields_ = [(pint.uint32_t, 'CommitThresholdShift'),(pint.uint32_t, 'MaxPreCommittThreshold')]
 
class HEAP(pstruct.type):
    class __FrontEndHeapType(pint.uint8_t, pint.enum):
        _values_ = [
            (0, 'unknown'),
        ]

    def __FrontEndHeap(self):
        t = int(self.parent['FrontEndHeapType'].l)
        if t == 0:
            return LAL
        elif t == 2:
            return LF
        raise NotImplementedError('Unknown FrontEndHeapType 0x%x'% t)

    _fields_ = [
        (HEAP_ENTRY, 'Entry'),
        (pint.uint32_t, 'SegmentSignature'),
        (pint.uint32_t, 'SegmentFlags'),
        (dyn.clone(LIST_ENTRY, _object_=HEAP_SEGMENT), 'SegmentListEntry'),
        (dyn.pointer(lambda s: HEAP), 'Heap'),
        (dyn.pointer(ptype.type), 'BaseAddress'),
        (pint.uint32_t, 'NumberOfPages'),
        (dyn.pointer(HEAP_ENTRY), 'FirstEntry'),
        (dyn.pointer(HEAP_ENTRY), 'LastValidEntry'),
        (pint.uint32_t, 'NumberOfUnCommittedPages'),
        (pint.uint32_t, 'NumberOfUnCommittedRanges'),
        (pint.uint16_t, 'SegmentAllocatorBackTraceIndex'),
        (pint.uint16_t, 'Reserved'),
        (LIST_ENTRY, 'UCRSegmentList'), # XXX: unknown type
        (pint.uint32_t, 'Flags'),
        (pint.uint32_t, 'ForceFlags'),
        (pint.uint32_t, 'CompatibilityFlags'),
        (pint.uint32_t, 'EncodeFlagMask'),
        (HEAP_ENTRY, 'Encoding'),
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
        (dyn.clone(LIST_ENTRY, _object_=HEAP_SEGMENT), 'SegmentList'),
        (pint.uint32_t, 'AllocatorBackTraceIndex'),
        (pint.uint32_t, 'NonDedicatedListLength'),
        (dyn.pointer(imm_HeapCache), 'LargeBlocksIndex'),
        (dyn.pointer(ptype.type), 'UCRIndex'),
        (dyn.pointer(HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
        (dyn.clone(LIST_ENTRY, _object_=HEAP_FREE_ENTRY), 'FreeLists'),
        (dyn.pointer(HEAP_LOCK), 'LockVariable'),
        (dyn.pointer(pint.uint32_t), 'CommitRoutine'),
        (dyn.pointer(__FrontEndHeap), 'FrontEndHeap'),
        (pint.uint16_t, 'FrontHeapLockCount'),
        (__FrontEndHeapType, 'FrontEndHeapType'),
        (HEAP_COUNTERS, 'Counters'),
        (HEAP_TUNING_PARAMETERS, 'TuningParameters'),
    ]

class ProcessHeapEntries(parray.type):
    _object_ = dyn.pointer(HEAP)

    def walk(self):
        for x in self:
            yield x.d
        return

if __name__ == '__main__':
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

    handle = getcurrentprocess()
    pebaddress = getPBIObj(handle).PebBaseAddress

    z = ndk.PEB(offset=pebaddress).l
    ldr = z['Ldr'].d.l

    print z['ProcessHeap'].d.l

    a = z['ProcessHeap'].d.l
    b = [x for x in z['ProcessHeaps'].d.l.walk()]
