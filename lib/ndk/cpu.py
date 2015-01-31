import ptypes
from ptypes import *

pbinary.setbyteorder(ptypes.config.byteorder.bigendian)
class selector(pbinary.struct):
    _fields_ = [(13, 'Index'),(1,'TI'),(2,'RPL')]
class systemtable(pstruct.type):
    _fields_ = [(pint.uint32_t,'base'),(pint.uint16_t,'limit')]
class systemsegment(pstruct.type):
    _fields_ = [(selector,'selector'),(systemtable,'address')]

class descriptor(pbinary.struct):
    class flags(pbinary.struct):
        _fields_ = [(1,n) for n in ('G','D/B','L','AVL')]
    class access(pbinary.struct):
        _fields_ = [(1,'P'),(2,'DPL'),(1,'S'),(4,'Type')]

    _fields_ = [
        (8, 'Base[3]'),
        (flags, 'Flags'),
        (4, 'Limit[High]'),
        (access, 'Access'),
        (8, 'Base[2]'),
        (16, 'Base[Low]'),
        (16, 'Limit[Low]'),
    ]
class descriptor64(descriptor):
    _fields_ = [(32,'Reserved'),(32,'Base[High]')] + descriptor._fields_

class flags(pbinary.flags):
    _fields_ = [
        (1,'0'),
        (1,'NT'), #Nested Task Flag
        (2,'IOPL'), #I/O Privilege Level
        (1,'OF'), #Overflow Flag
        (1,'DF'), #Direction Flag
        (1,'IF'), #Interrupt-enable Flag
        (1,'TF'), #Trap Flag
        (1,'SF'), #Sign Flag
        (1,'ZF'), #Zero Flag
        (1,'0'),
        (1,'AF'), #Adjust Flag
        (1,'0'),
        (1,'PF'), #Parity Flag
        (1,'1'),
        (1,'CF'), #Carry Flag
    ]

class eflags(pbinary.flags):
    _fields_ = [
        (10,'reserved'),
        (1,'ID'), #CPUID-Available
        (1,'VIP'), #Virtual Interrupt Pending
        (1,'VIF'), #Virtual Interrupt Flag
        (1,'AC'), #Alignment Check
        (1,'VM'), #V8086 Mode
        (1,'RF'), #Resume Flag
    ] + flags._fields_

class rflags(pbinary.flags):
    _fields_ = [(10+32,'reserved')]+eflags._fields_[1:]

a = pbinary.new(eflags,source=ptypes.prov.string('\xaa\xaa\xaa\xaa'))
a = pbinary.new(eflags,source=ptypes.prov.string('\x7f\x00\x00\x80'))
print a
print a.l.summary()
print a.l

class gdt(pbinary.array):
    #length = 8192
    _object_ = descriptor
class ldt(pbinary.array):
    #length = 8192
    _object_ = descriptor
    
#a=gdt.entry()
#print a

class cr0(pbinary.flags):
    _fields_ = [
        (1, 'PG'), #Paging
        (1, 'CD'), #Cache disable
        (1, 'NW'), #Not-write through
        (10, '??'),
        (1, 'AM'), #Alignment mask
        (1, '0'),
        (1, 'WP'), #Write protect
        (10, '?'),
        (1, 'NE'), #Numeric error
        (1, 'ET'), #Extension Type
        (1, 'TS'), #Task Switched
        (1, 'EM'), #Emulation
        (1, 'MP'), #Monitor co-processor
        (1, 'PE'), #Protected Mode Enable
    ]

class cr4(pbinary.flags):
    _fields_ = [
        (10, 'reserved'),
        (1, 'SMAP'), #Supervisor Mode Access Protection Enable
        (1, 'SMEP'), #Supervisor Mode Execution Protection Enable
        (1, '???'),
        (1, 'OSXSAVE'), #XSAVE and Processor Extended States Enable
        (1, 'PCIDE'), #PCID Enable
        (1, 'FSGSBASE'), #FSGSBASE-Enable bit
        (1, '??'),

        (1, 'SMXE'), #Safer Mode Extensions Enable
        (1, 'VMXE'), #Virtual Machine Extensions Enable
        (2, '0'),
        (1, 'OSXMMEXCPT'), #Operating System Support for Unmasked SIMD Floating-Point Exceptions
        (1, 'OSFXSR'), #Operating system support for FXSAVE and FXRSTOR instructions
        (1, 'PCE'), #Performance-Monitoring Counter enable
        (1, 'PGE'), #Page Global Enabled
        (1, 'MCE'), #Machine Check Exception
        (1, 'PAE'), #Physical Address Extension
        (1, 'PSE'), #Page Size Extension
        (1, 'DE'), #Debugging Extensions
        (1, 'TSD'), #Time Stamp Disable
        (1, 'PVI'), #Protected-mode Virtual Interrupts
        (1, 'VME'), #Virtual 8086 Mode Extensions
    ]

#x = eflags().a
#x.set(0xffff8fff)

class tss16(pstruct.type):
    class SPSS(pstruct.type):
        _fields_ = [(pint.uint16_t,'SP'),(pint.uint16_t,'SS')]

    class general(pstruct.type):
        _fields_ = [(pint.uint16_t,name) for name in ('AX','CX','DX','BX','SP','BP','SI','DI')]
    class segment(pstruct.type):
        _fields_ = [(pint.uint16_t,name) for name in ('ES','CS','SS','DS')]

    _fields_ = [
        (pint.uint16_t, 'Previous Task Link'),
        (dyn.clone(parray.type, length=3, _object_=SPSS), 'SPSS'),

        (pint.uint16_t, 'IP'),
        (flags, 'FLAG'),

        (general, 'general'),
        (segment, 'segment'),

        (pint.uint16_t, 'LDT'),
    ]

class tss32(pstruct.type):
    class align16(pstruct.type):
        _fields_ = [(pint.uint16_t,'reserved'),(pint.uint16_t,'value')]
    class general(pstruct.type):
        _fields_ = [(pint.uint32_t,name) for name in ('EAX','ECX','EDX','EBX','ESP','EBP','ESI','EDI')]
    class segment(pstruct.type):
        _fields_ = [(align16,name) for name in ('ES','CS','SS','DS','FS','GS')]
    class ESPSS(pstruct.type):
        _fields_ = [(align16,'SS'),(pint.uint32_t,'ESP')]

    _fields_ = [
        (align16,'Previous Task Link'),
        (dyn.clone(parray.type, length=3, _object_=SPSS), 'ESPSS'),
        (pint.uint32_t, 'CR3'),

        (pint.uint32_t, 'EIP'),
        (eflags, 'EFLAGS'),

        (general, 'general'),
        (segment, 'segment'),
        (align16, 'LDT'),

        (pint.uint16_t, 'Reserved'),
        (pint.uint16_t, 'I/O Map Base Address'),
    ]

class tss64(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'Reserved'),
        (dyn.clone(parray.type, length=3, _object_=pint.uint64_t), 'RSP'),
        (pint.uint64_t, 'Reserved'),
        (dyn.clone(parray.type, length=8, _object_=pint.uint64_t), 'IST'),
        (pint.uint64_t, 'Reserved'),
        (pint.uint16_t, 'Reserved'),
        (pint.uint16_t, 'I/O Map Base Address'),
    ]
