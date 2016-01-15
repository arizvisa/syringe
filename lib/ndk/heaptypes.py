import ptypes,sdkddkver,rtltypes
from WinNT import *
import itertools,functools,operator,math
import logging

class HeapException(ptypes.error.RequestError):
    '''Base class for exceptions raised by the heap types'''
    def __init__(self, o, m, *args, **kwds):
        super(HeapException,self).__init__(o, m)
        map(None,itertools.starmap(functools.partial(setattr, self), kwds.items()))
        self.__iterdata__ = tuple(args)
        self.__mapdata__ = dict(kwds)
    def __iter__(self):
        for n in self.__iterdata__: yield n
    def __str__(self):
        iterdata = (repr(v) for v in self.__iterdata__)
        mapdata = ('%s=%r'%(k,v) for k,v in self.__mapdata__.iteritems())
        self.message = '({:s})'.format(', '.join(itertools.chain(iterdata, mapdata)) if self.__iterdata__ or self.__mapdata__ else '')
        return super(HeapException, self).__str__()

class ListHintException(HeapException): pass
class InvalidPlatformException(HeapException): pass
class IncorrectHeapType(HeapException): pass
class InvalidBlockSize(HeapException): pass
class CorruptStructureException(HeapException): pass
class CrtZoneNotFoundError(HeapException): pass

class _HEAP_LOCK(pint.uint32_t): pass

if 'HeapMeta':
    class _HEAP_BUCKET_COUNTERS(pstruct.type):
        _fields_ = [
            (ULONG, 'TotalBlocks'),
            (ULONG, 'SubSegmentCounts'),
        ]
        def summary(self):
            return 'TotalBlocks:0x{:x} SubSegmentCounts:0x{:x}'.format(self['TotalBlocks'].num(), self['SubSegmentCounts'].num())

    class _HEAP_COUNTERS(pstruct.type):
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

    class _HEAP_TUNING_PARAMETERS(pstruct.type):
        _fields_ = [(ULONG, 'CommitThresholdShift'),(SIZE_T, 'MaxPreCommittThreshold')]

    class _HEAP_PSEUDO_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (SIZE_T, 'Size'),
        ]

    class _HEAP_TAG_ENTRY(pstruct.type):
        _fields_ = [
            (ULONG, 'Allocs'),
            (ULONG, 'Frees'),
            (ULONG, 'Size'),
            (USHORT, 'TagIndex'),
            (USHORT, 'CreatorBackTraceIndex'),
            (dyn.clone(pstr.wstring, length=24), 'TagName')
        ]

    class _HEAP_DEBUGGING_INFORMATION(pstruct.type):
        # http://blog.airesoft.co.uk/2010/01/a-whole-heap-of-trouble-part-1/
        _fields_ = [
            (PVOID, 'InterceptorFunction'),
            (WORD, 'InterceptorValue'),
            (DWORD, 'ExtendedOptions'),
            (DWORD, 'StackTraceDepth'),
            (SIZE_T, 'MinTotalBlockSize'),
            (SIZE_T, 'MaxTotalBlockSize'),
            (PVOID, 'HeapLeakEnumerationRoutine'),
        ]

    class _DPH_BLOCK_INFORMATION(pstruct.type):
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
        _fields_ = [
            (ULONG, 'StartStamp'),  # 0xabcdaaaa
            (PVOID, 'Heap'),
            (SIZE_T, 'RequestedSize'),
            (SIZE_T, 'ActualSize'),
            (LIST_ENTRY, 'FreeQueue'),
            (PVOID, 'StackTrace'),
            (ULONG, 'EndStamp'),    # 0xdcbaaaaa
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

            (dyn.pointer(_HEAP_FREE_ENTRY), 'pBucket'),  # XXX
            (lambda s: dyn.pointer(dyn.array(_HEAP_FREE_ENTRY, s['NumBuckets'].li.int())), 'Buckets'),
            (lambda s: dyn.array(pint.uint32_t, s['NumBuckets'].li.int()/32), 'Bitmap'),
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

            (lambda s: dyn.array(dyn.pointer(_HEAP_FREE_ENTRY), int(s['NumBuckets'].li)), 'Buckets'),
            (lambda s: dyn.clone(pbinary.array, _object_=1, length=int(s['NumBuckets'].li)), 'Bitmask'),    # XXX: This array is too huge
    #        (lambda s: dyn.block(int(s['NumBuckets'].li)/8), 'Bitmask'),
        ]

if 'HeapEntry':
    class _HEAP_ENTRY_EXTRA(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'AllocatorBacktraceIndex'),
            (pint.uint64_t, 'ZeroInit'),
            (pint.uint16_t, 'TagIndex'),
            (PVOID, 'Settable'),
        ]

    class _HEAP_ENTRY(ptype.encoded_t):
        _value_ = dyn.array(pint.uint32_t, 2)

        class _Flags(pbinary.flags):
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

        class _UnusedBytes(pbinary.struct):
            _fields_ = [
                (1, 'AllocatedByFrontend'),
                (3, 'Unknown'),
                (1, 'Busy'),
                (3, 'Unused'),
            ]
            def summary(self):
                frontend = 'FE' if self['AllocatedByFrontend'] else 'BE'
                busy = 'BUSY' if self['Busy'] else 'FREE'
                return '{:s} {:s} Unused:{:d}'.format(frontend, busy, self['Unused'])

        class _object_(pstruct.type, versioned):
            def __init__(self, **attrs):
                super(_HEAP_ENTRY._object_, self).__init__(**attrs)
                f = []
                if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
                    f.extend([
                        (pint.uint16_t, 'Size'),
                        (pint.uint16_t, 'PreviousSize'),
                        (pint.uint8_t, 'SmallTagIndex'),
                        (_HEAP_ENTRY._Flags, 'Flags'),
                        (pint.uint8_t, 'UnusedBytes'),
                        #(pint.uint8_t, 'SegmentIndex'),
                        (pint.uint8_t, 'SegmentOffset'),
                    ])
                elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                    f.extend([
                        (pint.uint16_t, 'Size'),
                        (_HEAP_ENTRY._Flags, 'Flags'),
                        (pint.uint8_t, 'SmallTagIndex'),    # Checksum
                        (pint.uint16_t, 'PreviousSize'),
                        (pint.uint8_t, 'SegmentOffset'),
                        (_HEAP_ENTRY._UnusedBytes, 'UnusedBytes'),
                    ])
                else:
                    raise NotImplementedError
                self._fields_ = f

        def __EncodedQ(self):
            return hasattr(self, '_HEAP_ENTRY_EncodeFlagMask') and (self.object[0].num() & self._HEAP_ENTRY_EncodeFlagMask)

        def encode(self, object, **attrs):
            frontend = getattr(self, '_FrontEndHeapType', 0)
            if hasattr(self, '_HEAP_ENTRY_Encoding'):
                if self.__EncodedQ() and frontend == 0:

                    o1,o2 = self._HEAP_ENTRY_Encoding
                    n1,n2 = object[0].num(),object[1].num()
                    d1 = ptypes.bitmap.data((n1^o1,32), reversed=True)
                    d2 = ptypes.bitmap.data((n2^o2,32), reversed=True)
                    return ptypes.bitmap.data(d1+d2)

                elif frontend == 2:
                    # LFH Frontend
                    data = map(ord,self.object.serialize())
                    data[3] = data[0]^data[1]^data[2]
                    n = (data[0]<<0) | (data[1]<<8) | (data[2]<<16) | (data[3]<<24)
                    n ^= self._HEAP_ENTRY_Encoding[0]
                    data[0] = (n & 0x000000ff) >> 0
                    data[1] = (n & 0x0000ff00) >> 8
                    data[2] = (n & 0x00ff0000) >> 16
                    data[3] = (n & 0xff000000) >> 24
                    return ''.join(map(chr,data))

                else:
                    raise NotImplementedError, frontend
            return object.serialize()

        def decode(self, **attrs):
            frontend = getattr(self, '_FrontEndHeapType', 0)
            if hasattr(self, '_HEAP_ENTRY_Encoding'):
                if self.__EncodedQ() and frontend == 0:
                    n1,n2 = self.object[0].num(),self.object[1].num()
                    o1,o2 = self._HEAP_ENTRY_Encoding
                    d1 = ptypes.bitmap.data((n1^o1,32), reversed=True)
                    d2 = ptypes.bitmap.data((n2^o2,32), reversed=True)
                    attrs['source'] = ptypes.prov.string(d1+d2)
                    return super(_HEAP_ENTRY, self).decode(**attrs)

                elif frontend == 2:
                    # LFH Frontend
                    n = self.object[0].num()
                    o,_ = self._HEAP_ENTRY_Encoding
                    d = ptypes.bitmap.data((n^o,32), reversed=True)
                    attrs['source'] = ptypes.prov.string(d + self.object[1].serialize())

                else:
                    raise NotImplementedError, frontend
            return super(_HEAP_ENTRY, self).decode(**attrs)

        def Size(self):
            '''Return the decoded Size field'''
            self = self.d.l
            return self['Size'].num()*8

        def PreviousSize(self):
            '''Return the decoded PreviousSize field'''
            self = self.d.l
            return self['PreviousSize'].num()*8

        def SegmentIndex(self):
            '''Return the decoded SegmentIndex field'''
            self = self.d.l
            return self['SegmentOffset'].num()

        def Busy(self):
            '''Returns whether the chunk is in use or not'''
            frontend = getattr(self, '_FrontEndHeapType', 0)
            if frontend == 2:
                res = self.d.l
                return bool(res['UnusedBytes']['Busy'])
            raise NotImplementedError, frontend

        def summary(self):
            res = self.d.l
            frontend = getattr(self, '_FrontEndHeapType', 0)
            if frontend == 2:
                #sz = self.p['Data'].size()
                sz = 0
                return 'LFH: Size:0x{:x} Summary:{:s} ({:08x}{:08x})'.format(sz, res['UnusedBytes'].summary(), self.object[0].num(), self.object[1].num())
            return 'Backend: Flags:{:s} Size:0x{:x} PreviousSize:0x{:x} SmallTagIndex:0x{:x} SegmentIndex:0x{:x}'.format(res['Flags'].summary(),res['Size'].num()*8,res['PreviousSize'].num()*8,res['SmallTagIndex'].num(),res['SegmentOffset'].num())

    class FreeListBucket(LIST_ENTRY):
        class _HeapBucketLink(ptype.pointer_t):
            _object_ = _HEAP_BUCKET_COUNTERS
            def decode(self, **attrs):
                ofs = self.decode_offset()
                if ofs & 1:
                    attrs.setdefault('source', self.source)
                    attrs.setdefault('offset', self.decode_offset()-1)
                    return self.new(_HEAP_BUCKET, **attrs)
                    #return dyn.clone(_HEAP_BUCKET,_fields_=[(dyn.block(1),'Padding')]+_HEAP_BUCKET._fields_[:])
                return super(FreeListBucket._HeapBucketLink,self).decode(**attrs)
        _fields_ = LIST_ENTRY._fields_[:]
        _fields_[1] = (_HeapBucketLink, 'Blink')

        def collect(self, size=None):
            '''Collect chunks that begin at the current chunk that are less than ``size``'''
            for n in self.walk():
                if size is None: size = n['Header'].Size()
                if n['Header'].Size() > size:
                    break
                yield n
            return

if 'HeapChunk':
    class ChunkUserBlock(pstruct.type):
        def __ChunkFreeEntryOffset(self):
            header = self['Header'].li
            frontend = getattr(header, '_FrontEndHeapType', 0)
            if frontend == 2 and header.d.li['UnusedBytes']['Busy'] == 0:
                return pint.uint16_t
            return pint.uint_t

        _fields_ = [
            (_HEAP_ENTRY, 'Header'),
            (__ChunkFreeEntryOffset, 'ChunkFreeEntryOffset'),
            (lambda s: dyn.block(s.blocksize() - s['Header'].li.size() - s['ChunkFreeEntryOffset'].li.size()), 'Data'),
        ]

    class ChunkFreeList(pstruct.type):
        def next(self):
            '''Walk to the next entry in the free-list'''
            link = self['ListEntry']
            return link['Flink'].d.l
        def prev(self):
            '''Moonwalk to the previous entry in the free-list'''
            link = self['ListEntry']
            return link['Blink'].d.l

    ChunkFreeList._fields_ = [
        (_HEAP_ENTRY, 'Header'),
        (dyn.clone(LIST_ENTRY,_object_=fpointer(ChunkFreeList,'ListEntry'),_path_=('ListEntry',)), 'ListEntry'),
        (lambda s: dyn.block(s['Header'].li.Size()), 'Data')
    ]

    class ChunkLookaside(ChunkFreeList): pass

if 'Frontend':
    class FrontEndHeapType(pint.enum, pint.uint8_t):
        _values_ = [
            ('Backend', 0),
            ('LAL', 1),
            ('LFH', 2),
        ]

    class FrontEndHeap(ptype.definition):
        cache = {}

if 'LookasideList':
    @FrontEndHeap.define
    class LAL(parray.type):
        type = 1
        attributes = {'_FrontEndHeapType':type}

        class _object_(pstruct.type):
            _fields_ = [
                (dyn.clone(SLIST_ENTRY,_object_=fpointer(ChunkLookaside,'ListHead'),_path_=('ListHead',)), 'ListHead'),
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

        HEAP_MAX_FREELIST = 0x80
        length = HEAP_MAX_FREELIST

    class FreeListsInUseBitmap(pbinary.array):
        _object_ = 1
        length = 0x80

if 'LFH':
    class _INTERLOCK_SEQ(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Depth'),
            (pint.uint16_t, 'FreeEntryOffset'),
            (ULONG, 'Sequence'),
        ]
        def summary(self):
            return 'Depth:0x{:x} FreeEntryOffset:0x{:x} Sequence:0x{:x}'.format(self['Depth'].num(), self['FreeEntryOffset'].num(), self['Sequence'].num())

    class _HEAP_USERDATA_HEADER(pstruct.type):
        def _Blocks(self):
            ss = self['SubSegment'].li.d.l
            cs = ss['BlockSize'].num() * 8
            t = dyn.clone(ChunkUserBlock, blocksize=lambda s:cs)
            return dyn.array(t, ss['BlockCount'].num())

        def NextIndex(self):
            '''Return the next UserBlock index that will be allocated from this structure'''
            ss = self['SubSegment'].d.l
            return ss.GetFreeBlockIndex()

        def NextBlock(self):
            '''Return the next block that will be allocated from this segment'''
            index = self.NextIndex()
            return self['Blocks'][index]
        NextChunk = NextBlock

        def UsageBitmap(self):
            '''Return a bitmap showing the busy/free chunks that are available'''
            res = (0,0)
            for block in self['Blocks']:
                res = ptypes.bitmap.push(res, (int(block['Header'].Busy()),1))
            return res

    class _HEAP_LOCAL_SEGMENT_INFO(pstruct.type):

        # FIXME: Figure out how and what to use 'CachedItems' for. This might
        #        be used by the 'LastUsed' field.

        # FIXME: Implement the logic to find the correct _HEAP_SUBSEGMENT by
        #        starting with 'Hint', and then falling back to 'ActiveSubSegment'

        def Bucket(self):
            '''Return the LFH bin associated with the current _HEAP_LOCAL_SEGMENT_INFO'''
            bin = self['BucketIndex'].num()
            lfh = self.getparent(_LFH_HEAP)
            return lfh['Buckets'][bin]

    class _LFH_BLOCK_ZONE(pstruct.type): pass

    _LFH_BLOCK_ZONE._fields_ = [
        (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_LFH_BLOCK_ZONE),_path_=('ListEntry',)), 'ListEntry'),
        (PVOID, 'FreePointer'),
        (PVOID, 'Limit'),
#        (dyn.pointer(ChunkUsed), 'FreePointer'),
#        (dyn.pointer(ChunkUsed), 'Limit'),
        (dyn.pointer(_HEAP_LOCAL_SEGMENT_INFO), 'SegmentInfo'),
        (dyn.pointer(_HEAP_USERDATA_HEADER), 'UserBlocks'),
        (_INTERLOCK_SEQ, 'AggregateExchg'),
    ]

    class _HEAP_BUCKET_RUN_INFO(pstruct.type):
        _fields_ = [
            (ULONG, 'Bucket'),
            (ULONG, 'RunLength'),
        ]
        def summary(self):
            return 'Bucket:0x{:x} RunLength:0x{:x}'.format(self['Bucket'].num(), self['RunLength'].num())

    class _USER_MEMORY_CACHE_ENTRY(pstruct.type):
        # FIXME: Figure out which SizeIndex is used for a specific cache entry
        class _UserBlocks(pstruct.type):
            def __Blocks(self):
                entry = self.getparent(_USER_MEMORY_CACHE_ENTRY)
                idx = [n.getoffset() for n in entry.p.value].index(entry.getoffset())+1
                sz = idx * 8 + _HEAP_ENTRY().a.size()
                block = dyn.clone(ChunkUserBlock, blocksize=lambda s:sz)
                return dyn.array(block, entry['AvailableBlocks'].num() * 8)

            _fields_ = [
                (dyn.array(pint.uint32_t,4), 'unknown'),
                (__Blocks, 'Blocks'),
            ]
        _fields_ = [
            #(dyn.clone(SLIST_HEADER,_object_=UserBlocks), 'UserBlocks'),
            (SLIST_HEADER, 'UserBlocks'),
            (ULONG, 'AvailableBlocks'),     # AvailableBlocks*8 seems to be the actual size
            (ULONG, 'MinimumDepth'),
        ]

    class _HEAP_BUCKET(pstruct.type):
        class _BucketFlags(pbinary.flags):
            _fields_ = [
                (5, 'Reserved'),
                (2, 'DebugFlags'),
                (1, 'UseAffinity'),
            ]
        _fields_ = [
            (pint.uint16_t, 'BlockUnits'),
            (pint.uint8_t, 'SizeIndex'),
            (_BucketFlags, 'BucketFlags'),
        ]
        def AllocationCount(self):
            return self['BlockUnits'].li.num() // 2

    class _HEAP_SUBSEGMENT(pstruct.type):
        def BlockSize(self):
            '''Returns the size of each block within the subsegment'''
            return self['BlockSize'].num() * 8
        def ChunkSize(self):
            '''Return the size of the chunks that this _HEAP_SUBSEGMENT is responsible for providing'''
            return self.BlockSize() - 8
        def GetFreeBlockIndex(self):
            '''Returns the index into UserBlocks of the next block to allocate given the `FreeEntryOffset` of the current _HEAP_SUBSEGMENT'''
            fo = self['AggregateExchg']['FreeEntryOffset'].num() * 8
            return fo / self.BlockSize()
        def NextBlock(self):
            '''Return the next block HeapAllocate will return if there's no free chunks available to return'''
            index = self.GetFreeBlockIndex()
            ub = self['UserBlocks'].d.l
            return ub['Blocks'][index]
        NextChunk = NextBlock

        def UsedBlockCount(self):
            '''Return the total number of UserBlocks that have been allocated'''
            return self['BlockCount'].num() - self['AggregateExchg']['Depth'].num()
        def UnusedBlockCount(self):
            '''Return the number of UserBlocks that have been either freed or unallocated'''
            return self['AggregateExchg']['Depth'].num()
        def Usage(self):
            '''Return a binary string showing the busy/free chunks that are available within `UserBlocks`'''
            ub = self['UserBlocks'].d.l
            res = ub.UsageBitmap()
            return ptypes.bitmap.string(res)

        def properties(self):
            res = super(_HEAP_SUBSEGMENT, self).properties()
            if self.initializedQ():
                res['SegmentIsFull'] = self['AggregateExchg']['Depth'].num() == 0
                res['AvailableBlocks'] = self.UnusedBlockCount()
                res['BusyBlocks'] = self.UsedBlockCount()
            return res

    _HEAP_USERDATA_HEADER._fields_ = [
        (dyn.pointer(_HEAP_SUBSEGMENT), 'SubSegment'),
        (PVOID, 'Reserved'),    # FIXME: figure out what this actually points to
        (ULONG, 'SizeIndex'),
        (ULONG, 'Signature'),
        (lambda s: s._Blocks(), 'Blocks'),

#        (pint.uint16_t, 'FirstAllocationOffset'),
#        (pint.uint16_t, 'BlockStride'),
#        (rtltypes._RTL_BITMAP, 'BusyBitmap'),
#        (ULONG, 'BitmapData'),
    ]

    class _HEAP_LOCAL_DATA(pstruct.type):
        def CrtZone(self):
            '''Return the SubSegmentZone that's correctly associated with the value of the CrtZone field'''
            fe = self.getparent(_LFH_HEAP)
            zone = self['CrtZone'].num()
            zoneiterator = (z for z in fe['SubSegmentZones'].walk() if z.getoffset() == zone)
            try:
                res = zoneiterator.next()
            except StopIteration:
                raise CrtZoneNotFoundError(self, '_HEAP_LOCAL_DATA.CrtZone', zone=zone, frontendheap=fe.getoffset(), heap=fe.p.p.getoffset())
            return res

    @FrontEndHeap.define
    class _LFH_HEAP(pstruct.type,versioned):
        type = 2
        attributes = {'_FrontEndHeapType':type}

        # FIXME: Figure out how caching in 'UserBlockCache' works

        # FIXME: Figure out why _HEAP_LOCAL_DATA is defined as an array in all lfh material
        #        but only referenced as a single-element array

        def GetSizeIndex(self, size):
            '''Return the size index when given a ``size``'''
            heap = self.getparent(_HEAP)
            bucket = heap.FindHeapBucket(size)
            return bucket['SizeIndex'].num()
        def GetBucket(self, size):
            '''Return the LFH bin given a ``size``'''
            index = self.GetSizeIndex(size)
            return self['Buckets'][index]
        def GetSegmentInfo(self, size):
            '''Return the _HEAP_LOCAL_SEGMENT_INFO for a specific ``size``'''
            bin = self.GetBucket(size)
            index = bin['SizeIndex'].num()
            return self['LocalData']['SegmentInfo'][index]

        def __init__(self, **attrs):
            super(_LFH_HEAP, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (rtltypes._RTL_CRITICAL_SECTION, 'Lock'),
                    (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_LFH_BLOCK_ZONE),_path_=('ListEntry',)), 'SubSegmentZones'),
                    (ULONG, 'ZoneBlockSize'),
                    (dyn.pointer(_HEAP), 'Heap'),
                    (ULONG, 'SegmentChange'),
                    (ULONG, 'SegmentCreate'),
                    (ULONG, 'SegmentInsertInFree'),
                    (ULONG, 'SegmentDelete'),
                    (ULONG, 'CacheAllocs'),
                    (ULONG, 'CacheFrees'),
                    (ULONG, 'SizeInCache'),
                    (dyn.block(4), 'Padding'),
                    (_HEAP_BUCKET_RUN_INFO, 'RunInfo'),
                    (dyn.array(_USER_MEMORY_CACHE_ENTRY,12), 'UserBlockCache'), # FIXME: Not sure what this cache is used for
                    (dyn.array(_HEAP_BUCKET,128), 'Buckets'),
                    (_HEAP_LOCAL_DATA, 'LocalData'),
                ])
            else:
                raise NotImplementedError
            self._fields_ = f

    _HEAP_LOCAL_DATA._fields_ = [
        (SLIST_HEADER, 'DeletedSubSegments'),       # FIXME: figure out how this actually points to a subsegment
        (dyn.pointer(_LFH_BLOCK_ZONE), 'CrtZone'),
        (dyn.pointer(_LFH_HEAP), 'LowFragHeap'),
        (ULONG, 'Sequence'),
        (ULONG, 'DeleteRateThreshold'),
        (dyn.array(_HEAP_LOCAL_SEGMENT_INFO,128), 'SegmentInfo'),
    ]

    _HEAP_SUBSEGMENT._fields_ = [
        (dyn.pointer(_HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
        (dyn.pointer(_HEAP_USERDATA_HEADER), 'UserBlocks'),
        (_INTERLOCK_SEQ, 'AggregateExchg'),
        (pint.uint16_t, 'BlockSize'),
        (pint.uint16_t, 'Flags'),
        (pint.uint16_t, 'BlockCount'),
        (pint.uint8_t, 'SizeIndex'),
        (pint.uint8_t, 'AffinityIndex'),
        (SLIST_ENTRY, 'SFreeListEntry'),    # XXX: DelayFreeList
        (ULONG, 'Lock'),
    ]

    _HEAP_LOCAL_SEGMENT_INFO._fields_ = [
        (dyn.pointer(_HEAP_SUBSEGMENT), 'Hint'),
        (dyn.pointer(_HEAP_SUBSEGMENT), 'ActiveSubSegment'),
        (dyn.array(dyn.pointer(_HEAP_SUBSEGMENT),16), 'CachedItems'),
        (SLIST_HEADER, 'SListHeader'),
        (_HEAP_BUCKET_COUNTERS, 'Counters'),
        (dyn.pointer(_HEAP_LOCAL_DATA), 'LocalData'),
        (ULONG, 'LastOpSequence'),
        (pint.uint16_t, 'BucketIndex'),
        (pint.uint16_t, 'LastUsed'),    # FIXME: Does this point into CachedItems?
        (dyn.block(4), 'Reserved'),
    ]

if 'Heap':
    class _HEAP_UCR_DESCRIPTOR(pstruct.type): pass
    _HEAP_UCR_DESCRIPTOR._fields_ = [
            (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR),_path_=('ListEntry',)), 'ListEntry'),
            (LIST_ENTRY, 'SegmentEntry'),
#            (PVOID, 'Address'),
            (dyn.pointer(lambda s: dyn.clone(ptype.undefined, length=s.p['Size'].li.num())), 'Address'),
            (SIZE_T, 'Size'),
        ]

    class _HEAP_SEGMENT(pstruct.type, versioned):
        def Bounds(self):
            start,end = self['FirstEntry'],self['LastValidEntry']
            return start.li.num(),end.li.num()

        def __init__(self, **attrs):
            super(_HEAP_SEGMENT, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_VISTA:
                raise NotImplementedError
                f.extend([
                    (LIST_ENTRY, 'ListEntry'),
                    (pint.uint32_t, 'Signature'),
                    (pint.uint32_t, 'Flags'),
                    (dyn.pointer(_HEAP), 'Heap'),
                    (pint.uint32_t, 'LargestUnCommittedRange'),
                    (PVOID, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (PVOID, 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (dyn.pointer(_HEAP_UNCOMMMTTED_RANGE), 'UnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (dyn.pointer(_HEAP_ENTRY), 'LastEntryInSegment'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7+1:
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
                    (dyn.pointer(_HEAP_TAG_ENTRY), 'TagEntries'),
                    (LIST_ENTRY, 'UCRSegments'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (_HEAP_ENTRY, 'Entry'),
                    (pint.uint32_t, 'SegmentSignature'),
                    (pint.uint32_t, 'SegmentFlags'),
                    (dyn.clone(LIST_ENTRY,_object_=fpointer(_HEAP_SEGMENT,('SegmentListEntry',)),_path_=('SegmentListEntry',)), 'SegmentListEntry'),   # XXX: entry comes from _HEAP
                    (dyn.pointer(_HEAP), 'Heap'),
                    (pint.uint32_t, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (PVOID, 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (LIST_ENTRY, 'UCRSegmentList'),
                ])
            else:
                raise NotImplementedError
            self._fields_ = f

    class _HEAP_VIRTUAL_ALLOC_ENTRY(pstruct.type): pass
    _HEAP_VIRTUAL_ALLOC_ENTRY._fields_ = [
            (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_HEAP_VIRTUAL_ALLOC_ENTRY),_path_=('ListEntry',)), 'ListEntry'),
            (_HEAP_ENTRY_EXTRA, 'ExtraStuff'),
            (pint.uint64_t, 'CommitSize'),
            (pint.uint64_t, 'ReserveSize'),
            (_HEAP_ENTRY, 'BusyBlock'),
        ]

    class _HEAP(pstruct.type, versioned):
        def UncommittedRanges(self):
            '''Iterate through the list of UncommittedRanges(UCRList) for the _HEAP'''
            for n in self['UCRList'].walk():
                yield n
            return

        def Segments(self):
            '''Iterate through the list of Segments(SegmentList) for the _HEAP'''
            for n in self['SegmentList'].walk():
                yield n
            return

        def FindHeapListLookup(self, blockindex):
            '''Return the correct _HEAP_LIST_LOOKUP structure according to the ``blockindex`` (size / 8)'''
            if not self['FrontEndHeapType']['LFH']:
                raise IncorrectHeapType(self, '_HEAP.FindHeapListLookup', self['FrontEndHeapType'], version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            p = self['LargeBlocksIndex'].d.l
            while blockindex >= p['ArraySize'].num():
                if p['ExtendedLookup'].num() == 0:
                    raise ListHintException(self, '_HEAP.FindHeapListLookup', 'Unable to locate ListHint for blocksize', blocksize=blocksize, index=p['ArraySize'].num()-1, lookup=p)
                p = p['ExtendedLookup'].d.l
            return p

        def FindHeapBucket(self, size):
            '''Find the correct Heap Bucket from the FreeListEntry for the given ``size``'''
            entry = self.FindFreeListEntry(size)
            return entry['Blink'].d.l

        def FindFreeListEntry(self, size):
            '''Return the FreeListEntry according to the specified ``size``'''
            if not self['FrontEndHeapType']['LFH']:
                raise IncorrectHeapType(self, '_HEAP.FindFreeListEntry', self['FrontEndHeapType'], version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            bi = math.trunc(math.ceil(size / 8.0))
            heaplist = self.FindHeapListLookup(bi)
            return heaplist.FindFreeListEntry(bi)

        def __PointerKeyEncoding(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) != sdkddkver.NTDDI_WIN7:
                raise InvalidPlatformException(self, '_HEAP.__PointerKeyEncoding', version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION), expected=sdkddkver.NTDDI_WIN7)
            if self['EncodeFlagMask']:
                self.attributes['_HEAP_ENTRY_EncodeFlagMask'] = self['EncodeFlagMask'].li.num()
                self.attributes['_HEAP_ENTRY_Encoding'] = tuple(n.num() for n in self['Encoding'].li)
            return pint.uint32_t

        def __init__(self, **attrs):
            super(_HEAP, self).__init__(**attrs)
            f = [(_HEAP_SEGMENT, 'Segment')]
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
                    (dyn.pointer(_HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR),_path_=('ListEntry',)), 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_HEAP_VIRTUAL_ALLOC_ENTRY),_path_=('ListEntry',)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY, _path_='SegmentListEntry',_object_=fpointer(_HEAP_SEGMENT,'SegmentListEntry')), 'SegmentList'),
                    (pint.uint32_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (dyn.pointer(_HEAP_LIST_LOOKUP), 'LargeBlocksIndex'),
                    (dyn.pointer(ptype.type), 'UCRIndex'),
                    (dyn.pointer(_HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _object_=dyn.pointer(_HEAP_FREE_ENTRY)), 'FreeLists'),      # XXX:
                    (dyn.pointer(_HEAP_LOCK), 'LockVariable'),
                    (dyn.pointer(pint.uint32_t), 'CommitRoutine'),
                    (dyn.pointer(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.num())), 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (FrontEndHeapType, 'FrontEndHeapType'),
                    (_HEAP_COUNTERS, 'Counters'),
                    (_HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (pint.uint32_t, 'Flags'),
                    (pint.uint32_t, 'ForceFlags'),
                    (pint.uint32_t, 'CompatibilityFlags'),
                    (pint.uint32_t, 'EncodeFlagMask'),
                    (dyn.array(pint.uint32_t, 2), 'Encoding'),
                    (self.__PointerKeyEncoding, 'PointerKey'),
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
                    (dyn.pointer(_HEAP_TAG_ENTRY), 'TagEntries'),
                    (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR),_path_=('ListEntry',)), 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (LIST_ENTRY, 'VirtualAllocedBlocks'),   # XXX: unknown type
                    (dyn.clone(LIST_ENTRY,_object_=fpointer(_HEAP_SEGMENT,('SegmentListEntry',)),_path_=('SegmentListEntry',)), 'SegmentList'),
                    (pint.uint16_t, 'FreeListInUseTerminate'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (dyn.pointer(_HEAP_LIST_LOOKUP), 'LargeBlocksIndex'),
                    (dyn.pointer(ptype.type), 'UCRIndex'),  # XXX
                    (dyn.pointer(_HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY, _object_=fpointer(ChunkFreeList,'ListEntry'),_path_=('ListEntry',)), 'FreeLists'),
                    (dyn.pointer(_HEAP_LOCK), 'LockVariable'),
                    (dyn.pointer(ptype.type), 'CommitRoutine'),
                    (dyn.pointer(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.num())), 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (FrontEndHeapType, 'FrontEndHeapType'),
                    (pint.uint8_t, 'FrontEndAlignment'),
                    (_HEAP_COUNTERS, 'Counters'),
                    (_HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
            else:
                raise NotImplementedError
            self._fields_ = f

    class _HEAP_LIST_LOOKUP(pstruct.type):
        def GetFreeListsCount(self):
            '''Return the number of FreeLists entries within this structure'''
            return self['ArraySize'].li.num() - self['BaseIndex'].li.num()

        def FindFreeListEntry(self, blockindex):
            '''Find the correct ListHint for the specified ``blockindex``'''
            res = blockindex - self['BaseIndex'].num()
            assert 0 <= res < self.GetFreeListsCount(), '_HEAP_LIST_LOOKUP.FindFreeListEntry : Requested BlockIndex is out of bounds : %d <= %d < %d'% (self['BaseIndex'].num(), blockindex, self['ArraySize'].num())
            freelist = self['ListsInUseUlong'].d.l
            list = self['ListHints'].d.l
            if freelist[res] == 1:
                return list[res]
            return list[res]

        class _ListsInUseUlong(pbinary.array):
            _object_ = 1
            def run(self):
                return ptypes.bitmap.reverse(self.bitmap())
            def summary(self):
                objectname,_ = super(_HEAP_LIST_LOOKUP._ListsInUseUlong,self).summary().split(' ', 2)
                return ' '.join((objectname, ptypes.bitmap.hex((self.run()))))
            def details(self):
                objectname,_ = super(_HEAP_LIST_LOOKUP._ListsInUseUlong,self).summary().split(' ', 2)
                return '\n'.join((objectname + ' ->', ptypes.bitmap.string(self.run())))
            def repr(self):
                return self.details()

    _HEAP_LIST_LOOKUP._fields_ = [
        (dyn.pointer(_HEAP_LIST_LOOKUP), 'ExtendedLookup'),

        (ULONG, 'ArraySize'),
        (ULONG, 'ExtraItem'),
        (ULONG, 'ItemCount'),
        (ULONG, 'OutOfRangeItems'),
        (ULONG, 'BaseIndex'),

        (dyn.pointer(LIST_ENTRY), 'ListHead'),
        (dyn.pointer(lambda s: dyn.clone(_HEAP_LIST_LOOKUP._ListsInUseUlong, length=s.p.GetFreeListsCount())), 'ListsInUseUlong'),
        (dyn.pointer(lambda s: dyn.array(dyn.clone(FreeListBucket,_object_=fpointer(ChunkFreeList,'ListEntry'),_path_=('ListEntry',),_sentinel_=s.p['ListHead'].num()), s.p.GetFreeListsCount())), 'ListHints'),
    ]

class ProcessHeapEntries(parray.type):
    _object_ = dyn.pointer(_HEAP)

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

    a = ndk.heaptypes._HEAP(offset=b.getoffset())
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
