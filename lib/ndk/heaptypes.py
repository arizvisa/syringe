### Implement the WIN64 version of this.

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

class NotFoundException(HeapException): pass
class ListHintException(HeapException): pass
class InvalidPlatformException(HeapException): pass
class IncorrectHeapType(HeapException): pass
class IncorrectChunkType(HeapException): pass
class IncorrectChunkVersion(HeapException): pass
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
            return 'TotalBlocks:{:#x} SubSegmentCounts:{:#x}'.format(self['TotalBlocks'].int(), self['SubSegmentCounts'].int())

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
        _fields_ = [(ULONG,'CommittThresholdShift'), (SIZE_T,'MaxPreCommittThreshold')]

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

            (dyn.pointer(_HEAP_FREE_CHUNK), 'pBucket'),  # XXX
            (lambda s: dyn.pointer(dyn.array(_HEAP_FREE_CHUNK, s['NumBuckets'].li.int())), 'Buckets'),
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

            (lambda s: dyn.array(dyn.pointer(_HEAP_FREE_CHUNK), s['NumBuckets'].li.int()), 'Buckets'),
            (lambda s: dyn.clone(pbinary.array, _object_=1, length=s['NumBuckets'].li.int()), 'Bitmask'),    # XXX: This array is too huge
    #        (lambda s: dyn.block(s['NumBuckets'].li.int()/8), 'Bitmask'),
        ]

if 'HeapEntry':
    class _HEAP_BUCKET(pstruct.type):
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
            return self['BlockUnits'].li.int() // 2

    class _HEAP_ENTRY_EXTRA(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'AllocatorBacktraceIndex'),
            (pint.uint64_t, 'ZeroInit'),
            (pint.uint16_t, 'TagIndex'),
            (pint.uint32_t, 'Settable'),
        ]

    class _HEAP_ENTRY(pstruct.type, versioned):
        class Flags(pbinary.flags):
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

        class UnusedBytes(pbinary.flags):
            _fields_ = [
                (1, 'AllocatedByFrontend'),
                (3, 'Unknown'),
                (1, 'Busy'),
                (3, 'Type'),
            ]
            def summary(self):
                frontend = 'FE' if self['AllocatedByFrontend'] else 'BE'
                busy = 'BUSY' if self['Busy'] else 'FREE'
                return '{:s} {:s} Type:{:d}'.format(frontend, busy, self['Type'])

        def __init__(self, **attrs):
            super(_HEAP_ENTRY, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
                #f.extend([
                #   (pint.uint16_t, 'Size'),
                #   (pint.uint16_t, 'PreviousSize'),
                #   (pint.uint8_t, 'SmallTagIndex'),
                #   (_HEAP_ENTRY.Flags, 'Flags'),
                #   (pint.uint8_t, 'UnusedBytes'),
                #   (pint.uint8_t, 'SegmentIndex'),
                #   (pint.uint8_t, 'SegmentOffset'),
                #])
                f.extend([
                    (pint.uint16_t, 'Size'),
                    (pint.uint16_t, 'PreviousSize'),
                    (pint.uint8_t, 'SegmentIndex'),
                    (_HEAP_ENTRY.Flags, 'Flags'),
                    (pint.uint8_t, 'Index'),
                    (pint.uint8_t, 'Mask'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                f.extend([
                    (pint.uint16_t, 'Size'),
                    (_HEAP_ENTRY.Flags, 'Flags'),
                    (pint.uint8_t, 'SmallTagIndex'),    # Checksum
                    (pint.uint16_t, 'PreviousSize'),
                    (pint.uint8_t, 'SegmentOffset'),    # Size // 8
                    (_HEAP_ENTRY.UnusedBytes, 'UnusedBytes'),  # XXX: for some reason this is checked against 0x055
                ])
            else:
                raise NotImplementedError((sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION)))
            self._fields_ = f

        def summary(self):
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                res = 'Size={:x} SmallTagIndex={:x} PreviousSize={:x} SegmentOffset={:x}'
                res = [res.format(self['Size'].int(), self['SmallTagIndex'].int(), self['PreviousSize'].int(), self['SegmentOffset'].int())]
                res+= ['UnusedBytes ({:s})'.format(self['UnusedBytes'].summary())]
                res+= ['Flags ({:s})'.format(self['Flags'].summary())]
                return ' : '.join(res)
            return super(_HEAP_ENTRY, self).summary()

        def properties(self):
            res = super(_HEAP_ENTRY, self).properties()
            res['Encoded'] = False
            return res

    class _ENCODED_POINTER(ptype.pointer_t):
        def encode(self, object, **attrs):
            try:
                heap = self.getparent(type=_HEAP)
                self._HEAP_PointerKey = heap['PointerKey'].int()
            except ptypes.NotFoundError:
                # FIXME: Log that this encoded-pointer is non-encoded due to not being able to find a _HEAP
                pass
            if hasattr(self, '_HEAP_PointerKey'):
                return super(_ENCODED_HEAP_ENTRY,self).encode(self._value_().set(object.get() ^ self._HEAP_PointerKey))
            return super(_ENCODED_HEAP_ENTRY,self).encode(object)

        def decode(self, object, **attrs):
            if not hasattr(self, '_HEAP_PointerKey'):
                heap = self.getparent(type=_HEAP)
                self._HEAP_PointerKey = heap['PointerKey'].int()
            res = object.get() ^ self._HEAP_PointerKey
            return super(_ENCODED_POINTER, self).decode(self._value_().set(res))

        def summary(self):
            return '*{:#x} -> *{:#x}'.format(self.get(), self.d.getoffset())

    class _ENCODED_HEAP_ENTRY(ptype.encoded_t):
        _value_ = dyn.array(pint.uint32_t, 2)

        def FrontEndQ(self):
            self = self.d.li
            return bool(self['Flags']['AllocatedByFrontend'])
        def BackEndQ(self):
            # Back-to-Front(242)
            return not self.FrontEndQ()

        def Type(self):
            self = self.d.li
            return self['Flags']['Type']

        def BusyQ(self):
            '''Returns whether the chunk is in use or not'''
            self = self.d.li
            return bool(self['Flags']['Busy'])

        def properties(self):
            res = super(_ENCODED_HEAP_ENTRY, self).properties()
            res['Encoded'] = True
            return res

        def classname(self): return self.typename()
        def repr(self): return self.details()
        def __getitem__(self, name): return self.d.li.__getitem__(name)
        def __setitem__(self, name, value): return self.d.li.__setitem__(name, value)

        def details(self):
            res = self.d.li.copy(offset=self.getoffset())
            return res.details()

    class _BACKEND_HEAP_ENTRY(_ENCODED_HEAP_ENTRY):
        class _HEAP_ENTRY(pstruct.type):
            def __init__(self, **attrs):
                super(_BACKEND_HEAP_ENTRY._HEAP_ENTRY, self).__init__(**attrs)
                self._fields_ = [
                    (pint.uint16_t, 'Size'),
                    (pint.uint16_t, 'Checksum'),
                    (pint.uint16_t, 'PreviousSize'),
                    (pint.uint8_t, 'SegmentOffset'),
                    (_HEAP_ENTRY.UnusedBytes, 'Flags'),
                ]
        _object_ = _HEAP_ENTRY

        def encode(self, object, **attrs):
            try:
                heap = self.getparent(type=_HEAP)
                self._HEAP_ENTRY_Encoding = tuple(n.int() for n in heap['Encoding'].li.values())
                self._HEAP_ENTRY_EncodeFlagMask = heap['EncodeFlagMask'].li.int()
            except ptypes.NotFoundError:
                # FIXME: Log that this heap-entry is non-encoded due to not being able to find a _HEAP
                pass

            if hasattr(self, '_HEAP_ENTRY_EncodeFlagMask') and hasattr(self, '_HEAP_ENTRY_Encoding'):
                o1,o2 = self._HEAP_ENTRY_Encoding
                n1,n2 = object[0].int(),object[1].int()
                d1 = ptypes.bitmap.data((n1^o1 | self._HEAP_ENTRY_EncodeFlagMask,32), reversed=True)
                d2 = ptypes.bitmap.data((n2^o2,32), reversed=True)
                return super(_BACKEND_HEAP_ENTRY,self).encode(ptype.block(length=len(d1+d2)).set(ptypes.bitmap.data(d1+d2)))
            return super(_BACKEND_HEAP_ENTRY,self).encode(object)

        def decode(self, object, **attrs):
            # cache some attributes
            if not hasattr(self, '_HEAP_ENTRY_Encoding'):
                heap = self.getparent(type=_HEAP)
                self._HEAP_ENTRY_Encoding = tuple(n.int() for n in heap['Encoding'].li.values())
                self._HEAP_ENTRY_EncodeFlagMask = heap['EncodeFlagMask'].li.int()

            # Now determine if we're encoded, and decode it if so.
            if object[0].int() & self._HEAP_ENTRY_EncodeFlagMask:
                n1,n2 = object[0].int(),object[1].int()
                o1,o2 = self._HEAP_ENTRY_Encoding
                d1 = ptypes.bitmap.data((n1^o1,32), reversed=True)
                d2 = ptypes.bitmap.data((n2^o2,32), reversed=True)
                return super(_BACKEND_HEAP_ENTRY, self).decode( ptype.block(length=len(d1+d2)).set(d1+d2) )

            # Otherwise, we're not encoded. So, just pass-through...
            return super(_BACKEND_HEAP_ENTRY, self).decode(object, **attrs)

        def summary(self):
            # FIXME: log a warning suggesting that the flags are incorrect
            if self.BackEndQ(): pass

            data, res = self.serialize().encode('hex'), self.d.li
            return '{:s} : {:-#x} <-> {:+#x} : Flags:{:s}'.format(data, -res['PreviousSize'].int()*8, res['Size'].int()*8, res['Flags'].summary())

        def ChecksumQ(self):
            cls = self.__class__
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) != sdkddkver.NTDDI_MAJOR(sdkddkver.NTDDI_WIN7):
                raise IncorrectChunkVersion(self, '{:s}.ChecksumQ'.format(cls.__name__), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            res = map(ord, self.d.li.serialize())
            chk = reduce(operator.xor, res[:3], 0)
            return chk == res[3]

        def properties(self):
            res = super(_BACKEND_HEAP_ENTRY, self).properties()
            if self.initializedQ():
                try: res['ChecksumOkay'] = self.ChecksumQ()
                except HeapException: pass
            return res

        def Size(self):
            '''Return the decoded Size field'''
            self = self.d.li
            return self['Size'].int()*8

        def PreviousSize(self):
            '''Return the decoded PreviousSize field'''
            self = self.d.li
            return self['PreviousSize'].int()*8

    class _FRONTEND_HEAP_ENTRY(_ENCODED_HEAP_ENTRY):
        class _HEAP_ENTRY(pstruct.type):
            def __init__(self, **attrs):
                super(_FRONTEND_HEAP_ENTRY._HEAP_ENTRY, self).__init__(**attrs)
                self._fields_ = [
                    (pint.uint32_t, 'SubSegment'),
                    (pint.uint16_t, 'Unknown'),
                    (pint.uint8_t, 'EntryOffset'),
                    (_HEAP_ENTRY.UnusedBytes, 'Flags'),
                ]
        _object_ = _HEAP_ENTRY

        def encode(self, object, **attrs):
            try:
                # FIXME: _HEAP_USERDATA_HEADER['SubSegment'].d.l['LocalInfo'].d.l['LocalData'].d.l['LowFragHeap'].d.l['Heap'].d.l
                self._HEAP_ENTRY_Heap = heap = self.getparent(type=_HEAP)
                res = self.source.expr('ntdll!RtlpLFHKey')
                self._HEAP_ENTRY_LFHKey = self.new(pint.uint32_t, offset=res).l.int()

            except ptypes.NotFoundError:
                # FIXME: Log that this heap-entry is non-encoded due to not being able to find a _HEAP
                pass
            except AttributeError:
                # FIXME: Log that this heap-entry is non-encoded due to not being to determine LFHKey
                pass

            if hasattr(self, '_HEAP_ENTRY_LFHKey'):
                dn = self._HEAP_ENTRY_Heap.getoffset()
                dn ^= self._HEAP_ENTRY_LFHKey
                dn ^= object[0].int()
                dn ^= self.getoffset()
                d = pint.uint32_t().set(dn)
                return super(_FRONTEND_HEAP_ENTRY, self).decode(ptype.block(length=d.size()+object[1].size()).set(d.serialize()+object[1].serialize()))
            return super(_FRONTEND_HEAP_ENTRY,self).encode(object)

        def decode(self, object, **attrs):
            # cache some attributes
            try:
                if any(not hasattr(self, '_HEAP_ENTRY_'+attr) for attr in ('Heap','LFHKey')):
                    # FIXME: _HEAP_USERDATA_HEADER['SubSegment'].d.l['LocalInfo'].d.l['LocalData'].d.l['LowFragHeap'].d.l['Heap'].d.l
                    self._HEAP_ENTRY_Heap = heap = self.getparent(type=_HEAP)
                    res = self.source.expr('ntdll!RtlpLFHKey')
                    self._HEAP_ENTRY_LFHKey = self.new(pint.uint32_t, offset=res).l.int()

            except ptypes.NotFoundError:
                # FIXME: Log that this heap-entry is non-encoded due to not being able to find a _HEAP
                pass
            except AttributeError:
                # FIXME: Log that this heap-entry is non-encoded due to not being to determine LFHKey
                pass

            # Now we can decode us
            dn = self.getoffset() >> 3
            dn ^= object[0].int()
            dn ^= self._HEAP_ENTRY_LFHKey
            dn ^= self._HEAP_ENTRY_Heap.getoffset()
            d = pint.uint32_t().set(dn)
            return super(_FRONTEND_HEAP_ENTRY, self).decode(ptype.block(length=d.size()+object[1].size()).set(d.serialize()+object[1].serialize()))

        def summary(self):
            # FIXME: log a warning suggesting that the flags are incorrect
            if not self.FrontEndQ(): pass
            return self.serialize().encode('hex')

        def EntryOffsetQ(self):
            return self['Flags']['Type'] == 5

        def EntryOffset(self):
            if not self.EntryOffsetQ():
                logging.warn('{:s}.__EntryOffset : {:s} : Flags.Type != 5'.format( '.'.join((__name__, self.__class__.__name__)), self.instance()))
            return self['EntryOffset'].int() * 8

        def SubSegment(self):
            header = self.d.l
            offset = header['SubSegment'].int()
            res = self.new(dyn.pointer(_HEAP_SUBSEGMENT)).a
            return res.set(offset).d

        def properties(self):
            res = super(_FRONTEND_HEAP_ENTRY, self).properties()
            if self.initializedQ():
                res['EntryOffsetQ'] = self.EntryOffsetQ()
            return res

if 'HeapChunk':
    class Chunk(pstruct.type):
        def __ChunkFreeEntryOffset(self):
            header = self['Header'].li
            if header.FrontEndQ():
                if not hasattr(self, '_FrontEndHeapType'):
                    heap = self.getparent(type=_HEAP)
                    self._FrontEndHeapType = heap['FrontEndHeapType'].li.int()
                if self._FrontEndHeapType == 2:
                    return pint.uint_t if header.BusyQ() else pint.uint16_t
                raise NotImplementedError(self._FrontEndHeapType)
            return pint.uint_t

        def __ListEntry(self):
            header = self['Header'].li
            if header.Type() == 0 and all(not q for q in (header.BusyQ(), header.FrontEndQ())):
                return dyn.clone(LIST_ENTRY,_object_=fpointer(self.__class__, 'ListEntry'),_path_=('ListEntry',))
            return ptype.undefined

        def __Data(self):
            header = self['Header'].li
            if self.HEADER == _BACKEND_HEAP_ENTRY and header.FrontEndQ():
                logging.warn('{:s}.__Data : Header.Flags.AllocatedByFrontend bit is set on a chunk within the Backend. Potential corruption of HEAP_ENTRY. : {:s}'.format( '.'.join((__name__, self.__class__.__name__)), header['Flags'].summary()))
                size = header.Size()
            elif self.HEADER == _FRONTEND_HEAP_ENTRY and not header.FrontEndQ():
                logging.warn('{:s}.__Data : Header.Flags.AllocatedByFrontend bit is clear on a chunk within the Frontend. Potential corruption of HEAP_ENTRY. : {:s}'.format( '.'.join((__name__, self.__class__.__name__)), header['Flags'].summary()))
                size = self.blocksize()
            else:
                size = self.blocksize() if header.FrontEndQ() else header.Size()
            total = self['Header'].li.size() + self['ListEntry'].li.size() + self['ChunkFreeEntryOffset'].li.size()
            res = size - total
            return dyn.block(res if res >= 0 else 0)

        def properties(self):
            res = super(Chunk, self).properties()
            if self.initializedQ():
                res['Busy'] = self['Header'].BusyQ()
                res['Type'] = 'FE' if self['Header'].FrontEndQ() else 'BE'
            return res

        _fields_ = [
            (lambda s: s.HEADER, 'Header'),
            (__ListEntry, 'ListEntry'),
            (__ChunkFreeEntryOffset, 'ChunkFreeEntryOffset'),
            (__Data, 'Data'),
        ]

        def FreeQ(self): return not self.BusyQ()
        def BusyQ(self):
            return self['Header'].BusyQ()
        def BackEndQ(self): return not self.FrontEndQ()
        def FrontEndQ(self):
            return self['Header'].FrontEndQ()

        def next(self):
            cls, header = self.__class__, self['Header']
            if header.FrontEndQ():
                raise IncorrectChunkType(self, '{:s}.next'.format(cls.__name__), FrontEndQ=header.FrontEndQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            return self.new(cls, offset=self.getoffset() + header.Size())
        def previous(self):
            cls, header = self.__class__, self['Header']
            if header.FrontEndQ():
                raise IncorrectChunkType(self, '{:s}.previous'.format(cls.__name__), FrontEndQ=header.FrontEndQ(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            return self.new(cls, offset=self.getoffset() - header.PreviousSize())
        prev = previous

        def nextfree(self):
            '''Walk to the next entry in the free-list'''
            cls, header = self.__class__, self['Header']
            if header.Type() != 0 or header.FrontEndQ() or header.BusyQ():
                raise IncorrectChunkType(self, '{:s}.nextfree'.format(cls.__name__), FrontEndQ=header.FrontEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            link = self['ListEntry']
            return link['Flink'].d.l

        def previousfree(self):
            '''Moonwalk to the previous entry in the free-list'''
            cls, header = self.__class__, self['Header']
            if header.Type() != 0 or header.FrontEndQ() or header.BusyQ():
                raise IncorrectChunkType(self, '{:s}.previousfree'.format(cls.__name__), FrontEndQ=header.FrontEndQ(), BusyQ=header.BusyQ(), Type=header.Type(), version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            link = self['ListEntry']
            return link['Blink'].d.l
        prevfree = previousfree

    class _BE_HEAP_CHUNK(Chunk): HEADER = _BACKEND_HEAP_ENTRY
    class _FE_HEAP_CHUNK(Chunk): HEADER = _FRONTEND_HEAP_ENTRY

    class _HEAP_CHUNK(_BE_HEAP_CHUNK): pass
    class _HEAP_FREE_CHUNK(_HEAP_CHUNK): pass

    class ChunkLookaside(Chunk): HEADER = _HEAP_ENTRY

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
                ]
                def get(self):
                    return self.cast(pint.uint32_t).int()
            _value_ = _HeapBucketCounter
            _object_ = _HEAP_BUCKET
            def decode(self, object, **attrs):
                res = object.cast(pint.uint32_t)
                if res.int() & 1:
                    res.set(res.int() & ~1)
                else:
                    res.set(res.int() & ~0)
                    raise ValueError('{:s}.decode : Address {:x} is not a valid _HEAP_BUCKET'.format('.'.join((__name__,'FreeListBucket','_HeapBucketUnion',self.__class__.__name__)),res.int()))
                return super(FreeListBucket._HeapBucketLink,self).decode(res, **attrs)
            def summary(self):
                res = self.object
                if res.cast(pint.uint32_t).int() & 1:
                    return super(FreeListBucket._HeapBucketLink,self).summary()
                return 'AllocationCount={:#x} UnknownEvenCount={:#x}'.format(res['AllocationCount'].int(), res['UnknownEvenCount'].int())
            def details(self):
                res = self.object
                if res.cast(pint.uint32_t).int() & 1:
                    return super(FreeListBucket._HeapBucketLink,self).summary()
                return self.object.details()
            repr = details

        _fields_ = [
            (fpointer(_HEAP_FREE_CHUNK, 'ListEntry'), 'Flink'),
            (_HeapBucketLink, 'Blink'),
        ]

        def collect(self, size=None):
            '''Collect chunks that begin at the current chunk that are less than ``size``'''
            for n in self.walk():
                if size is None: size = n['Header'].Size()
                if n['Header'].Size() > size:
                    break
                yield n
            return

if 'LookasideList':
    @FrontEndHeap.define
    class LAL(parray.type):
        type = 1
        attributes = {'_FrontEndHeapType':type}

        class _object_(pstruct.type):
            _fields_ = [
                (dyn.clone(SLIST_ENTRY,_object_=fpointer(ChunkLookaside,'ListHead'),_path_=('ListHead',)), 'ListHead'),
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
            return 'Depth:{:#x} FreeEntryOffset:{:#x} Sequence:{:#x}'.format(self['Depth'].int(), self['FreeEntryOffset'].int(), self['Sequence'].int())

    class _HEAP_USERDATA_HEADER(pstruct.type):
        def __Blocks(self):
            ss = self['SubSegment'].li.d.l
            cs = ss['BlockSize'].int() * 8
            t = dyn.clone(_FE_HEAP_CHUNK, blocksize=lambda s:cs)
            return dyn.array(t, ss['BlockCount'].int())

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
                res = ptypes.bitmap.push(res, (int(block['Header'].BusyQ()),1))
            return res

        def __init__(self, **attrs):
            super(_HEAP_USERDATA_HEADER, self).__init__(**attrs)

            # FIXME: NTDDI_WIN8 changes this structure entirely
            self._fields_ = [
                (dyn.pointer(_HEAP_SUBSEGMENT), 'SubSegment'),
                (fpointer(_HEAP_CHUNK, 'ListEntry'), 'Reserved'),    # FIXME: figure out what this actually points to
                (ULONG, 'SizeIndex'),
                (ULONG, 'Signature'),
                (lambda s: s.__Blocks(), 'Blocks'),

            #    (pint.uint16_t, 'FirstAllocationOffset'),
            #    (pint.uint16_t, 'BlockStride'),
            #    (rtltypes._RTL_BITMAP, 'BusyBitmap'),
            #    (ULONG, 'BitmapData'),
            ]

    class _HEAP_LOCAL_SEGMENT_INFO(pstruct.type):

        # FIXME: Figure out how and what to use 'CachedItems' for. This might
        #        be used by the 'LastUsed' field.

        # FIXME: Implement the logic to find the correct _HEAP_SUBSEGMENT by
        #        starting with 'Hint', and then falling back to 'ActiveSubSegment'

        def Bucket(self):
            '''Return the LFH bin associated with the current _HEAP_LOCAL_SEGMENT_INFO'''
            bin = self['BucketIndex'].int()
            lfh = self.getparent(_LFH_HEAP)
            return lfh['Buckets'][bin]

        def __init__(self, **attrs):
            super(_HEAP_LOCAL_SEGMENT_INFO, self).__init__(**attrs)

            # FIXME NTDDI_WIN8 changes the order of these
            self._fields_ = [
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

    class _LFH_BLOCK_ZONE(pstruct.type):
        def __init__(self, **attrs):
            super(_LFH_BLOCK_ZONE, self).__init__(**attrs)
            self._fields_ = [
                (dyn.clone(LIST_ENTRY,_object_=dyn.pointer(_LFH_BLOCK_ZONE),_path_=('ListEntry',)), 'ListEntry'),
                (PVOID, 'FreePointer'),
                (dyn.pointer(_HEAP_CHUNK), 'Limit'),        # XXX
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
            return 'Bucket:{:#x} RunLength:{:#x}'.format(self['Bucket'].int(), self['RunLength'].int())

    class _USER_MEMORY_CACHE_ENTRY(pstruct.type):
        # FIXME: Figure out which SizeIndex is used for a specific cache entry
        class _UserBlocks(pstruct.type):
            def __Blocks(self):
                entry = self.getparent(_USER_MEMORY_CACHE_ENTRY)
                idx = [n.getoffset() for n in entry.p.value].index(entry.getoffset())+1
                sz = idx * 8 + _HEAP_ENTRY().a.size()
                block = dyn.clone(_FE_HEAP_CHUNK, blocksize=lambda s,sz=sz:sz)
                return dyn.array(block, entry['AvailableBlocks'].int() * 8)

            _fields_ = [
                (dyn.array(pint.uint32_t,4), 'unknown'),
                (__Blocks, 'Blocks'),
            ]
        _fields_ = [
            #(dyn.clone(SLIST_HEADER,_object_=UserBlocks), 'UserBlocks'),
            (SLIST_HEADER, 'UserBlocks'),   # XXX
            (ULONG, 'AvailableBlocks'),     # AvailableBlocks*8 seems to be the actual size
            (ULONG, 'MinimumDepth'),
        ]

    class _HEAP_SUBSEGMENT(pstruct.type):
        def BlockSize(self):
            '''Returns the size of each block within the subsegment'''
            return self['BlockSize'].int() * 8
        def ChunkSize(self):
            '''Return the size of the chunks that this _HEAP_SUBSEGMENT is responsible for providing'''
            return self.BlockSize() - 8
        def GetFreeBlockIndex(self):
            '''Returns the index into UserBlocks of the next block to allocate given the `FreeEntryOffset` of the current _HEAP_SUBSEGMENT'''
            fo = self['AggregateExchg']['FreeEntryOffset'].int() * 8
            return fo / self.BlockSize()
        def NextBlock(self):
            '''Return the next block HeapAllocate will return if there's no free chunks available to return'''
            index = self.GetFreeBlockIndex()
            ub = self['UserBlocks'].d.l
            return ub['Blocks'][index]
        NextChunk = NextBlock

        def UsedBlockCount(self):
            '''Return the total number of UserBlocks that have been allocated'''
            return self['BlockCount'].int() - self['AggregateExchg']['Depth'].int()
        def UnusedBlockCount(self):
            '''Return the number of UserBlocks that have been either freed or unallocated'''
            return self['AggregateExchg']['Depth'].int()
        def Usage(self):
            '''Return a binary string showing the busy/free chunks that are available within `UserBlocks`'''
            ub = self['UserBlocks'].d.l
            res = ub.UsageBitmap()
            return ptypes.bitmap.string(res)

        def properties(self):
            res = super(_HEAP_SUBSEGMENT, self).properties()
            if self.initializedQ():
                res['SegmentIsFull'] = self['AggregateExchg']['Depth'].int() == 0
                res['AvailableBlocks'] = self.UnusedBlockCount()
                res['BusyBlocks'] = self.UsedBlockCount()
            return res

        def __init__(self, **attrs):
            super(_HEAP_SUBSEGMENT, self).__init__(**attrs)

            # FIXME: NTDDI_WIN8 moves the DelayFreeList
            self._fields_ = [
                (dyn.pointer(_HEAP_LOCAL_SEGMENT_INFO), 'LocalInfo'),
                (dyn.pointer(_HEAP_USERDATA_HEADER), 'UserBlocks'),
                (_INTERLOCK_SEQ, 'AggregateExchg'),
                (pint.uint16_t, 'BlockSize'),
                (pint.uint16_t, 'Flags'),
                (pint.uint16_t, 'BlockCount'),
                (pint.uint8_t, 'SizeIndex'),
                (pint.uint8_t, 'AffinityIndex'),
                (dyn.clone(SLIST_ENTRY, _object_=fpointer(_HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'SFreeListEntry'),    # XXX: DelayFreeList
                #(SLIST_ENTRY, 'SFreeListEntry'),    # XXX: DelayFreeList
                (ULONG, 'Lock'),
            ]


    class _HEAP_LOCAL_DATA(pstruct.type):
        def CrtZone(self):
            '''Return the SubSegmentZone that's correctly associated with the value of the CrtZone field'''
            fe = self.getparent(_LFH_HEAP)
            zone = self['CrtZone'].int()
            zoneiterator = (z for z in fe['SubSegmentZones'].walk() if z.getoffset() == zone)
            try:
                res = next(zoneiterator)
            except StopIteration:
                raise CrtZoneNotFoundError(self, '_HEAP_LOCAL_DATA.CrtZone', zone=zone, frontendheap=fe.getoffset(), heap=fe.p.p.getoffset())
            return res

        def __init__(self, **attrs):
            super(_HEAP_LOCAL_DATA, self).__init__(**attrs)

            self._fields_ = [
                (dyn.clone(SLIST_HEADER, _object_=fpointer(_HEAP_SUBSEGMENT, 'SFreeListEntry'), _path_=('SFreeListEntry',)), 'DeletedSubSegments'),
                (dyn.pointer(_LFH_BLOCK_ZONE), 'CrtZone'),
                (dyn.pointer(_LFH_HEAP), 'LowFragHeap'),
                (ULONG, 'Sequence'),
                (ULONG, 'DeleteRateThreshold'),
                (dyn.array(_HEAP_LOCAL_SEGMENT_INFO,128), 'SegmentInfo'),
            ]


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
            return bucket['SizeIndex'].int()
        def GetBucket(self, size):
            '''Return the LFH bin given a ``size``'''
            index = self.GetSizeIndex(size)
            return self['Buckets'][index]
        def GetSegmentInfo(self, size):
            '''Return the _HEAP_LOCAL_SEGMENT_INFO for a specific ``size``'''
            bin = self.GetBucket(size)
            index = bin['SizeIndex'].int()
            return self['LocalData']['SegmentInfo'][index]

        def __init__(self, **attrs):
            super(_LFH_HEAP, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN7:
                f.extend([
                    (rtltypes._RTL_CRITICAL_SECTION, 'Lock'),
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_LFH_BLOCK_ZONE)), 'SubSegmentZones'),
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
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                raise NotImplementedError
            else:
                raise NotImplementedError
            self._fields_ = f

if 'Heap':
    class _HEAP_UCR_DESCRIPTOR(pstruct.type):
        def __init__(self, **attrs):
            super(_HEAP_UCR_DESCRIPTOR, self).__init__(**attrs)
            self._fields_ = [
                (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR)), 'ListEntry'),
                (dyn.clone(LIST_ENTRY,_path_=('UCRSegmentList',),_object_=fpointer(_HEAP_SEGMENT,'UCRSegmentList')), 'SegmentEntry'),
                (dyn.pointer(lambda s: dyn.clone(ptype.undefined, length=s.p['Size'].li.int())), 'Address'),
                (SIZE_T, 'Size'),
            ]

    class _HEAP_SEGMENT(pstruct.type, versioned):
        def Bounds(self):
            ucr = self['NumberOfUncommittedPages'].int() * 0x1000
            start,end = self['FirstEntry'],self['LastValidEntry']
            return start.li.int(),end.li.int() - ucr

        def Chunks(self):
            start, end = self.Bounds()
            res = self['FirstEntry'].d
            while res.getoffset() < end:
                yield res.l
                res = res.next()
            return

        def walk(self):
            yield self
            for n in self['SegmentListEntry'].walk(): yield n

        def __init__(self, **attrs):
            super(_HEAP_SEGMENT, self).__init__(**attrs)
            f = []
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WINXP:
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
                    (dyn.pointer(_ENCODED_HEAP_ENTRY), 'LastEntryInSegment'),
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
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_WIN7:
                f.extend([
                    (_BACKEND_HEAP_ENTRY, 'Entry'),
                    (pint.uint32_t, 'SegmentSignature'),
                    (pint.uint32_t, 'SegmentFlags'),
                    (lambda s: dyn.clone(LIST_ENTRY,_sentinel_='Blink',_path_=('SegmentListEntry',),_object_=fpointer(_HEAP_SEGMENT,'SegmentListEntry')), 'SegmentListEntry'),   # XXX: entry comes from _HEAP
                    (dyn.pointer(_HEAP), 'Heap'),
                    (pint.uint32_t, 'BaseAddress'),
                    (pint.uint32_t, 'NumberOfPages'),
                    (dyn.pointer(_BE_HEAP_CHUNK), 'FirstEntry'),
                    (PVOID, 'LastValidEntry'),
                    (pint.uint32_t, 'NumberOfUnCommittedPages'),
                    (pint.uint32_t, 'NumberOfUnCommittedRanges'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint16_t, 'Reserved'),
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=fpointer(_HEAP_UCR_DESCRIPTOR,'SegmentEntry')), 'UCRSegmentList'),
                ])
            else:
                raise NotImplementedError
            self._fields_ = f

    class _HEAP_VIRTUAL_ALLOC_ENTRY(pstruct.type):
        def __init__(self, **attrs):
            super(_HEAP_VIRTUAL_ALLOC_ENTRY, self).__init__(**attrs)
            # FIXME: is this right that _HEAP.UCRIndex points to this?
            self._fields_ = [
                (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_HEAP_VIRTUAL_ALLOC_ENTRY)), 'ListEntry'),
                (_HEAP_ENTRY_EXTRA, 'ExtraStuff'),
                (pint.uint32_t, 'CommitSize'),
                (pint.uint32_t, 'ReserveSize'),
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
            for n in self['SegmentListEntry'].walk():
                yield n
            return

        def FindHeapListLookup(self, blockindex):
            '''Return the correct _HEAP_LIST_LOOKUP structure according to the ``blockindex`` (size / 8)'''
            if not self['FrontEndHeapType']['LFH']:
                raise IncorrectHeapType(self, '_HEAP.FindHeapListLookup', self['FrontEndHeapType'], version=sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION))
            p = self['LargeBlocksIndex'].d.l
            while blockindex >= p['ArraySize'].int():
                if p['ExtendedLookup'].int() == 0:
                    raise ListHintException(self, '_HEAP.FindHeapListLookup', 'Unable to locate ListHint for blockindex', blockindex=blockindex, index=p['ArraySize'].int()-1, lookup=p)
                p = p['ExtendedLookup'].d.l
            return p

        def FindHeapBucket(self, size):
            '''Find the correct Heap Bucket from the FreeListEntry for the given ``size``'''
            entry = self.FindFreeListEntry(size)
            if entry['Blink'].int() == 0:
                raise NotFoundException(self, '_HEAP.FindHeapBucket', 'Unable to find a Heap Bucket for the requested size : 0x%x'% size, entry=entry, size=size)
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
                self.attributes['_HEAP_ENTRY_EncodeFlagMask'] = self['EncodeFlagMask'].li.int()
                self.attributes['_HEAP_ENTRY_Encoding'] = tuple(n.int() for n in self['Encoding'].li)
            return pint.uint32_t

        def __init__(self, **attrs):
            super(_HEAP, self).__init__(**attrs)
            f = [(_HEAP_SEGMENT, 'Segment')]
            if sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) >= sdkddkver.NTDDI_VISTA:
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
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_HEAP_VIRTUAL_ALLOC_ENTRY)), 'VirtualAllocedBlocks'),
                    (dyn.clone(LIST_ENTRY,_path_=('SegmentListEntry',),_object_=fpointer(_HEAP_SEGMENT,'SegmentListEntry')), 'SegmentListEntry'),
                    (pint.uint32_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (dyn.pointer(_HEAP_LIST_LOOKUP), 'LargeBlocksIndex'),
                    (fpointer(_BE_HEAP_CHUNK,'ListEntry'), 'UCRIndex'),
                    (dyn.pointer(_HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=fpointer(_HEAP_FREE_CHUNK,'ListEntry')), 'FreeLists'),      # XXX:
                    (dyn.pointer(_HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(_ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),
                    (dyn.pointer(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
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
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=dyn.pointer(_HEAP_UCR_DESCRIPTOR)), 'UCRList'),
                    (pint.uint32_t, 'AlignRound'),
                    (pint.uint32_t, 'AlignMask'),

                    (LIST_ENTRY, 'VirtualAllocedBlocks'),   # XXX: unknown type
                    (dyn.clone(LIST_ENTRY,_path_=('SegmentListEntry',),_object_=fpointer(_HEAP_SEGMENT,'SegmentListEntry')), 'SegmentList'),
                    (pint.uint16_t, 'FreeListInUseTerminate'),
                    (pint.uint16_t, 'AllocatorBackTraceIndex'),
                    (pint.uint32_t, 'NonDedicatedListLength'),
                    (dyn.pointer(_HEAP_LIST_LOOKUP), 'LargeBlocksIndex'),
                    (dyn.pointer(ptype.type), 'UCRIndex'),  # XXX
                    (dyn.pointer(_HEAP_PSEUDO_TAG_ENTRY), 'PseudoTagEntries'),
                    (dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=fpointer(_HEAP_FREE_CHUNK,'ListEntry')), 'FreeLists'),
                    (dyn.pointer(_HEAP_LOCK), 'LockVariable'),
                    (dyn.clone(_ENCODED_POINTER, _object_=ptype.undefined), 'CommitRoutine'),
                    (dyn.pointer(lambda s: FrontEndHeap.lookup(s.p['FrontEndHeapType'].li.int())), 'FrontEndHeap'),
                    (pint.uint16_t, 'FrontHeapLockCount'),
                    (FrontEndHeapType, 'FrontEndHeapType'),
                    (pint.uint8_t, 'FrontEndAlignment'),
                    (_HEAP_COUNTERS, 'Counters'),
                    (_HEAP_TUNING_PARAMETERS, 'TuningParameters'),
                ])
            elif sdkddkver.NTDDI_MAJOR(self.NTDDI_VERSION) == sdkddkver.NTDDI_WIN8:
                # http://illmatics.com/Windows%208%20Heap%20Internals.pdf
                raise NotImplementedError
            else:
                raise NotImplementedError
            self._fields_ = f

    class _HEAP_LIST_LOOKUP(pstruct.type):
        def GetFreeListsCount(self):
            '''Return the number of FreeLists entries within this structure'''
            return self['ArraySize'].li.int() - self['BaseIndex'].li.int()

        def FindFreeListEntry(self, blockindex):
            '''Find the correct ListHint for the specified ``blockindex``'''
            res = blockindex - self['BaseIndex'].int()
            assert 0 <= res < self.GetFreeListsCount(), '_HEAP_LIST_LOOKUP.FindFreeListEntry : Requested BlockIndex is out of bounds : %d <= %d < %d'% (self['BaseIndex'].int(), blockindex, self['ArraySize'].int())
            freelist = self['ListsInUseUlong'].d.l
            list = self['ListHints'].d.l
            if freelist[res] == 1:
                return list[res]
            return list[res]

        class _ListsInUseUlong(pbinary.array):
            _object_ = 1
            def run(self):
                return self.bitmap()
            def summary(self):
                objectname,_ = super(_HEAP_LIST_LOOKUP._ListsInUseUlong,self).summary().split(' ', 2)
                res = self.run()
                return ' '.join((objectname, ptypes.bitmap.hex(res)))
            def details(self):
                bits = 32 if self.bits() < 256 else 64
                w = len('{:x}'.format(self.bits()))
                res = ptypes.bitmap.split(self.run(), bits)
                return '\n'.join(('[{:x}] {{{:0{:d}x}:{:0{:d}x}}} {:s}'.format(self.getoffset() + bits*i, bits*i, w, bits*i+bits-1, w, ptypes.bitmap.string(n)) for i,n in enumerate(reversed(res))))
            def repr(self):
                return self.details()
        def __init__(self, **attrs):
            super(_HEAP_LIST_LOOKUP, self).__init__(**attrs)
            f = []

            f.extend([
                (dyn.pointer(_HEAP_LIST_LOOKUP), 'ExtendedLookup'),

                (ULONG, 'ArraySize'),
                (ULONG, 'ExtraItem'),
                (ULONG, 'ItemCount'),
                (ULONG, 'OutOfRangeItems'),
                (ULONG, 'BaseIndex'),

                (dyn.pointer(dyn.clone(LIST_ENTRY,_path_=('ListEntry',),_object_=fpointer(_HEAP_FREE_CHUNK,'ListEntry'))), 'ListHead'),
                (dyn.pointer(lambda s: dyn.clone(_HEAP_LIST_LOOKUP._ListsInUseUlong, length=s.p.GetFreeListsCount())), 'ListsInUseUlong'),
                (dyn.pointer(lambda s: dyn.array(dyn.clone(FreeListBucket,_object_=fpointer(_HEAP_FREE_CHUNK,'ListEntry'),_path_=('ListEntry',),_sentinel_=s.p['ListHead'].int()), s.p.GetFreeListsCount())), 'ListHints'),
            ])
            self._fields_ = f

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
