import ptypes
from ptypes import *

pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

class selector(pbinary.struct):
    _fields_ = [(13, 'Index'), (1, 'TI'), (2, 'RPL')]
class systemtable(pstruct.type):
    _fields_ = [(pint.uint32_t, 'base'), (pint.uint16_t, 'limit')]
class systemsegment(pstruct.type):
    _fields_ = [(selector, 'selector'), (systemtable, 'address')]

class descriptor(pbinary.struct):
    class flags(pbinary.struct):
        _fields_ = [(1, 'G'), (1, 'D/B'), (1, 'L'), (1, 'AVL')]
    class access(pbinary.struct):
        _fields_ = [(1, 'P'), (2, 'DPL'), (1, 'S'), (4, 'Type')]

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
    _fields_ = [(32, 'Reserved'), (32, 'Base[High]')] + descriptor._fields_

class general(pbinary.struct):
    _fields_ = [(32, regname) for regname in ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']]

class rex(pbinary.struct):
    _fields_ = [(64, regname) for regname in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp']]
    _fields_+= [(64, "r{:d}".format(regnum)) for regnum in range(8, 16)]

class segment(pbinary.struct):
    _fields_ = [(16, regname) for regname in ['cs', 'ds', 'ss', 'es', 'fs', 'gs']]

class flags(pbinary.flags):
    _fields_ = [
        (1, '0'),
        (1, 'NT'), #Nested Task Flag
        (2, 'IOPL'), #I/O Privilege Level
        (1, 'OF'), #Overflow Flag
        (1, 'DF'), #Direction Flag
        (1, 'IF'), #Interrupt-enable Flag
        (1, 'TF'), #Trap Flag
        (1, 'SF'), #Sign Flag
        (1, 'ZF'), #Zero Flag
        (1, '0'),
        (1, 'AF'), #Adjust Flag
        (1, '0'),
        (1, 'PF'), #Parity Flag
        (1, '1'),
        (1, 'CF'), #Carry Flag
    ]

class eflags(pbinary.flags):
    _fields_ = [
        (10, 'reserved'),
        (1, 'ID'), #CPUID-Available
        (1, 'VIP'), #Virtual Interrupt Pending
        (1, 'VIF'), #Virtual Interrupt Flag
        (1, 'AC'), #Alignment Check
        (1, 'VM'), #V8086 Mode
        (1, 'RF'), #Resume Flag
    ] + flags._fields_

class rflags(pbinary.flags):
    _fields_ = [(10+32, 'reserved')]+eflags._fields_[1:]

class fpstate(pbinary.struct):
    """
    Intel FPU register-space/region
    https://software.intel.com/en-us/articles/x87-and-sse-floating-point-assists-in-ia-32-flush-to-zero-ftz-and-denormals-are-zero-daz
    """
    default = 0x37f
    _fields_ = [
        (1, 'B'),   # FPU Busy
        (1, 'C3'),  # condition-code (cc)
        (3, 'TOP'), # Top of Stack Pointer (ST*)
        (1, 'C2'),  # cc
        (1, 'C1'),  # cc
        (1, 'C0'),  # cc
        (1, 'ES'),  # Error Summary
        (1, 'SF'),  # Fault from Stack
        (1, 'PM'),  # Precision
        (1, 'UM'),  # Underflow
        (1, 'OM'),  # Overflow
        (1, 'ZM'),  # Divided by Zero
        (1, 'DM'),  # Denormal(?) Operand
        (1, 'IM'),  # Invalid Operand
    ]

class sse(pbinary.array):
    _object_, length = 32 * 8, 8
class mmx(pbinary.array):
    _object_, length = 16 * 8, 8
class fpu(pbinary.array):
    _object_, length = 10 * 8, 8

class fpctrl(pbinary.struct):
    _fields_ = [
        (3, 'reserved0'),
        (1, 'X'),   # Infinity control (0=Projective,1=Affine)
        (2, 'RC'),  # Rounding control (00=Round to nearest even,01=Round down towards infinity,10=Round up towards infinity,11=Round towards zero)
        (2, 'PC'),  # Precision control (00=Single(24),01=Reserved,10=Double(53),11=Extended(64))
        (2, 'reserved1'),
        (1, 'PM'),  # Precision mask
        (1, 'UM'),  # Underflow mask
        (1, 'OM'),  # Overflow mask
        (1, 'ZM'),  # Zero Dvide mask
        (1, 'DM'),  # Denormalized Operand mask
        (1, 'IM'),  # Invalid Operation mask
    ]

class frstor(pbinary.struct):
    # FIXME: this size should be 108 bytes, not 100
    _fields_ = [
        (fpctrl, 'ControlWord'),
        (fpstate, 'StatusWord'),
        (16, 'TagWord'),
        (48, 'DataPointer'),
        (48, 'InstructionPointer'),
        (16, 'LastInstructionOpcode'),
        (fpu, 'ST'),
    ]

class gdt(pbinary.array):
    #length = 8192
    _object_ = descriptor
class ldt(pbinary.array):
    #length = 8192
    _object_ = descriptor

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

class cr3(pbinary.flags):
    _fields_ = [
        (20, 'Directory'),
        (7, 'Ignored'),
        (1, 'PCD'),
        (1, 'PWT'),
        (3, 'Ignored'),
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

class tss16(pstruct.type):
    class SPSS(pstruct.type):
        _fields_ = [(pint.uint16_t, 'SP'), (pint.uint16_t, 'SS')]

    class general(pstruct.type):
        _fields_ = [(pint.uint16_t, regname) for regname in ['AX', 'CX', 'DX', 'BX', 'SP', 'BP', 'SI', 'DI']]
    class segment(pstruct.type):
        _fields_ = [(pint.uint16_t, regname) for regname in ['ES', 'CS', 'SS', 'DS']]

    _fields_ = [
        (pint.uint16_t, 'Previous Task Link'),
        (dyn.clone(parray.type, length=3, _object_=SPSS), 'SPSS'),

        (pint.uint16_t, 'IP'),
        (flags, 'FLAG'),

        (general, 'general'),
        (segment, 'segment'),

        (pint.uint16_t, 'LDT'),
    ]

class align16(pstruct.type):
    _fields_ = [(pint.uint16_t, 'reserved'), (pint.uint16_t, 'value')]

class tss32(pstruct.type):
    class general(pstruct.type):
        _fields_ = [(pint.uint32_t, regname) for regname in ['EAX', 'ECX', 'EDX', 'EBX', 'ESP', 'EBP', 'ESI', 'EDI']]
    class segment(pstruct.type):
        _fields_ = [(align16, regname) for regname in ['ES', 'CS', 'SS', 'DS', 'FS', 'GS']]
    class ESPSS(pstruct.type):
        _fields_ = [(align16, 'SS'), (pint.uint32_t, 'ESP')]

    _fields_ = [
        (align16, 'Previous Task Link'),
        (dyn.clone(parray.type, length=3, _object_=ESPSS), 'ESPSS'),
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

class linear32(pbinary.struct):
    _fields_ = [
        (10, 'directory'),
        (10, 'table'),
        (12, 'offset'),
    ]

class linear32ps(pbinary.struct):
    _fields_ = [
        (10, 'directory'),
        (22, 'offset'),
    ]

class linear32pae(pbinary.struct):
    _fields_ = [
        (2, 'directory pointer'),
        (9, 'directory'),
        (9, 'table'),
        (12, 'offset'),
    ]

class linear64(pbinary.struct):
    _fields_ = [
        (16, 'reserved'),
        (9, 'pml4'),
        (9, 'directory ptr'),
        (9, 'directory'),
        (9, 'table'),
        (12, 'offset'),
    ]

class linear64ps(pbinary.struct):
    _fields_ = [
        (16, 'reserved'),
        (9, 'pml4'),
        (9, 'directory ptr'),
        (9, 'directory'),
        (21, 'offset'),
    ]

class linear64pae(pbinary.struct):
    _fields_ = [
        (16, 'reserved'),
        (9, 'pml4'),
        (9, 'directory ptr'),
        (30, 'offset'),
    ]

class pde(pbinary.flags):
    _fields_ = [
        (3, 'Ignored'),
        (1, 'G'),
        (1, 'PS'),
        (1, 'D'),
        (1, 'A'),
        (1, 'PCD'),
        (1, 'PWT'),
        (1, 'U/S'),
        (1, 'R/W'),
        (1, 'P'),
    ]

class pte(pbinary.flags):
    _fields_ = [
        (3, 'Ignored'),
        (1, 'G'),
        (1, 'PAT'),
        (1, 'D'),
        (1, 'A'),
        (1, 'PCD'),
        (1, 'PWT'),
        (1, 'U/S'),
        (1, 'R/W'),
        (1, 'P'),
    ]

class pde32(pbinary.struct):
    _fields_ = [
        (20, 'Address'),
        (pde, 'Flags'),
    ]

class pde32ps(pbinary.struct):
    _fields_ = [
        (10, 'Address(Lo)'),
        (9, 'Address(Hi)'),
        (1, 'PAT'),
        (pde, 'Flags'),
    ]

class pte32(pbinary.struct):
    _fields_ = [
        (20, 'Address'),
        (pte, 'Flags'),
    ]

class pde64(pbinary.struct):
    _fields_ = [
        (1, 'XD'),
        (11, 'M'),
        (40, 'Address'),
        (pde, 'Flags'),
    ]

class pde64ps(pbinary.struct):
    _fields_ = [
        (1, 'XD'),
        (4, 'PKE'),
        (7, 'Ignored'),
        (40, 'Address'),
        (pde, 'Flags'),
    ]

class pte64(pbinary.flags):
    _fields_ = [
        (1, 'XD'),
        (4, 'PKE'),
        (7, 'Ignored'),
        (40, 'Address'),
        (pte, 'Flags'),
    ]
