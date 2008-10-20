#####################################################################
.section .drectve
	.ascii " -export:DllMain"
	.ascii " -export:pause"
	.ascii " -export:alloc"
	.ascii " -export:read"
	.ascii " -export:write"
	.ascii " -export:call"
	.ascii " -export:findsymbol"

#####################################################################
.section .data

globalHeap:
    .long 0

#####################################################################
.section .text

initialize:
    andl %eax, %eax
    jnz 1f

    pushl $0
    pushl $0x1000
    pushl $0x10000
    call _HeapCreate@12
    movl %eax, globalHeap

1:
    ret

deinitialize:
    andl %eax, %eax
    jnz 1f

    pushl globalHeap
    call _HeapDestroy@4

1:
    ret

.global _DllMain    #(HINSTANCE hInstDll, DWORD fdwReason, LPVOID lpvReserved)
_DllMain:
    pushl %ebp
    movl %esp, %ebp

    movl 0xc(%ebp), %eax
    andl %eax, %eax
    jz @procDetach

    decl %eax
    jz @procAttach

    decl %eax
    jz @threadAttach

    decl %eax
    jz @threadDetach

    # XXX: wtf
    int3

    popl %ebp
    ret

@procDetach:
    call deinitialize
    jmp 0f
@procAttach:
    call initialize
    jmp 0f

@threadAttach:
    call _pause
    jmp 0f
@threadDetach:
#    call pause
#    jmp 0f

0:
    popl %ebp
    ret
    
#######
.global _pause  #()
.global _alloc  #(%eax)
.global _write  #(%edi, %eax)
.global _read   #(%esi, %eax)

_pause:
    jmp .

_alloc:
    pushl %eax
    movl globalHeap, %eax
    
    pushl (%esp)
    pushl $8    # HEAP_ZERO_MEMORY
    pushl %eax
    call _HeapAlloc@12
    call _pause

_write:
    stosl
    call _pause

_read:
    lodsl
    call _pause

#######
.global _call   #(%edi)
.global _findsymbol #(%edi)

_call:
    call *%edi
    call _pause

# XXX: findsymbol   (need to write a lot of code, maybe just hash it and hope)
_findsymbol:
    int3
    call _pause

######################################################################
.section .stager
    call 1f
.string "k" "e" "r" "n" "e" "l" "3" "2" "." "d" "l" "l"
1:
    popl %ebp

# look through initializationorder list
    # %edx == PEB.Ldr.InInitializationOrderLinks
    movl %fs:0x30, %edx
    movl 0xc(%edx), %edx
    movl 0x10(%edx), %edx

# iterate through all _LDR_DATA_TABLE_ENTRYs

    movl %edx, %ebx       # _LIST_ENTRY.Flink
1:
# check to see BaseDllName matches kernel32.dll
    xorl %ecx, %ecx
    movw 0x2c(%ebx), %cx
    movl 0x30(%ebx), %edi
    movl %ebp, %esi
    repe cmpsw

    andl %ecx, %ecx
    jz 2f

    movl (%ebx), %ebx
    cmp %ebx, %edx
    jne 1b

    # FIXME: unable to find kernel32.dll
    int3

2:
    movl 0x18(%ebx), %ebx

### we've found kernel32.dll's base address
# %ebx = executable base address
    movl 0x3c(%ebx), %edx   # %edx = at PE
    movl 0x68(%ebx), %edx   # %edx = import directory rva

    movw 2(%edx), %ax       # number of sections
    cwde

# find which section %edx is in
    movl %ecx, %edi
    imul $0x28, %edi
    addl $0xe0, %edi        # %edi = bottom of sections

    leal 0xe0(%edx), %esi   # sections
@section_loop:
    movl 0xc(%esi), %eax    # virtualaddress
    cmpl %eax, %edx
    jb 1f

    addl 8(%esi), %eax      # size
    cmpl %eax, %edx
    jb 2f

1:
    addl $0x28, %esi
    cmpl %edi, %esi
    jb @section_loop

    # FIXME: section not found
    int3

## %esi = section
2:
    movl 0x14(%esi), %eax
    leal (%ebx, %eax, 1), %ebx

    # %ebx points to section
    int3
