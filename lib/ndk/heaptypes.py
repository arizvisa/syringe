'''Aaron's heap types'''
import ptypes
from ptypes import pstruct,pint,parray,dyn

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

class HEAP_ENTRY(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'Size'),
        (pint.uint16_t, 'PreviousSize'),
        (pint.uint32_t, 'SubSegmentCode'),
        (pint.uint8_t, 'Flags'),
        (pint.uint8_t, 'UnusedBytes'),
        (pint.uint8_t, 'SegmentIndex')
    ]
    
    def next(self):
        return self.getoffset() + int(self['Size'])*8
        
class HEAP_SEGMENT(pstruct.type):
    _fields_ = [
        (pint.uint64_t, 'Header'),
        (pint.uint32_t, 'Signature'),
        (pint.uint32_t, 'Flags'),
        (pint.uint32_t, 'Heap'),
        (pint.uint32_t, 'LargestUnCommittedRange'),
        (pint.uint32_t, 'BaseAddress'),
        (pint.uint32_t, 'NumberofPages'),
        (dyn.pointer(HEAP_ENTRY), 'FirstEntry'),
        (dyn.pointer(HEAP_ENTRY), 'LastValidEntry'),
        (pint.uint32_t, 'NumberofUnCommittedPages'),
        (pint.uint32_t, 'NumberofUnCommittedRanges'),
        (dyn.pointer(HEAP_UNCOMMITTED_RANGE), 'UncommittedRanges'),
        (pint.uint16_t, 'AllocatorBackTraceIndex'),
        (pint.uint16_t, 'Reserved'),
        (dyn.pointer(HEAP_ENTRY), 'LastEntryInSegment')
    ]
    
    def walk (self):
        #print "Starting walk of heap segment"
        
        # load the first uncommitted range entry
        first_uc_range = self['UncommittedRanges'].get()
        
        uc_list = {}
        uc_entry = first_uc_range['Next'].get()
        uc_entry.load()
        
        uc_list[int(first_uc_range['Address'])] =  int(first_uc_range['Size'])
                
        uc_next = first_uc_range['Next'].get()
        uc_next_ptr = uc_next.getoffset()
        
        while uc_next_ptr != 0:
            uc_next.load()
            uc_list[int(uc_next['Address'])] = int(uc_next['Size'])
            
            uc_next = uc_next['Next'].get()
            uc_next_ptr = uc_next.getoffset()

        last = self['LastValidEntry'].get() # XXX: end 
        first = self['FirstEntry'].get()    # XXX: start
        print first
        
        # create the segment's heap array member
        self.heaps = []
        self.heaps.append(first)
        
        current_entry_addr = first.next()
        while current_entry_addr <= last.getoffset():
            current_entry = HEAP_ENTRY()
            current_entry.source = self.source
            current_entry.setoffset(current_entry_addr)
            current_entry.load()
            print current_entry
            self.heaps.append(current_entry)
            current_entry_addr = current_entry.next()
            
            # skip uncommitted entries
            for addy, size in uc_list.iteritems():
                if addy == current_entry_addr:
                    print "[%x]: UNCOMMITTED" % addy
                    #print "Found Uncommitted Entry at 0x%08x" % addy
                    current_entry_addr += size
                    if current_entry_addr == last.getoffset(): return
        
        #print "Done walking heap segment"           
 
 
class HEAP(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'Size'),
        (pint.uint16_t, 'PreviousSize'),
        (pint.uint32_t, 'Header'),

        ### 
        (pint.uint32_t, 'Signature'),
        (pint.uint32_t, 'Flags'),
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
        (pint.uint16_t, 'HeaderValidateCopy'),
        (pint.uint32_t, 'NextAvailableTagIndex'),
        (pint.uint16_t, 'MaximumTagIndex'),
        (pint.uint32_t, 'TagEntries'),
        (pint.uint32_t, 'UCRSegments'),
        (pint.uint32_t, 'UnusedCommittedRanges'),
        (pint.uint32_t, 'AlignRound'),
        (pint.uint32_t, 'AlignMask'),
        (pint.uint64_t, 'VirtualAllocdBlocks'),
        (dyn.array(dyn.pointer(HEAP_SEGMENT), 64), 'Segments')
    ]
