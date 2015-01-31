### this code should provide the environment in order to allocate pages of memory
### in a process without tampering with the stack

.section .data
topstack:   .long 0
dllname:            .string16 "kernel32.dll"
importmodulename:   .string "ntdll.dll"
importname:         .string "NtAllocateVirtualMemory"

.section .text
    .global _Spin
_Spin: jmp .

    .global _Loader
_Loader:

    ## level 0, we have no stack
loader_0:
    # find a tls entry that we can use for a stack
    # XXX: hopefully the operating system does not dispatch a window message
    #      to the thread, heh. ;)
    cld

#    jmp .

    # assign tlsbitmap(%esi) location and size(%edx)
    movl %fs:0x18, %ebx     # tib->teb
    movl 0x30(%ebx), %eax   # teb->peb
    mov 0x40(%eax), %eax     # peb->TlsBitmap
    movl (%eax), %edx        # RTL_BITMAP->size
    movl 4(%eax), %esi        # RTL_BITMAP->buffer

    # find out which tlsindex is free (in multiples of 8. ;) )
    #   XXX: this can fail if the bitmap's size isn't statically 64
    xorl %eax, %eax
    movl %edx, %ecx
    movl %esi, %edi
    repnz scasb
    decl %edi
    subl %edx, %ecx
    negl %ecx
    decl %ecx
    #shl $3, %ecx

    # occupy a few slots (8 slots)
    leal (%esi, %ecx, 1), %edi
    decb %al
    stosb

    # times number of bits
    shl $3, %ecx

    # get a pointer to our bottom-most TlsSlot
    leal 0xe10(%ebx, %ecx, 4), %edx
    movl $0x0d0e0a0d, (%edx)    # canary...heh

    # seek back to the top
    addl $(7*4), %edx

    # write our old esp there, and switch stack
    movl %esp, (%edx)
    movl %edx, %esp         # woo, 7 slots of stack
    movl %esp, topstack

    ## level 1, we should have a temporary stack allocated on the tls
    ##          now esp should point to the top of some playspace (7 dwords)

loader_1:
    pushl $dllname
    call _getbaseaddress
    addl $4, %esp

    pushl %eax

    pushl $importmodulename
    pushl %eax
    call _getimportmodulebyname
    addl $8, %esp

    movl 0(%esp), %edx

    pushl $importname
    pushl %eax
    pushl %edx
    call _getimportbyname
    addl $0xc, %esp


    ## level 2, now we should have getprocaddress, loadlibrary, and ntallocatevirtualmemory
    ##          just have to allocate ourselves a stack, and then we're done
loader_2:
    jmp .

loader_3:
    ## free our stack that we allocated in the tls

loader_4:
    ## return our stack
    movl topstack, %eax
    movl (%eax), %esp

    ret


## address space searching shit
# gets the base address of a module by it's unicode name
# in: 4(%esp) -> pointer to unicode module name; out: %eax -> base address of module
# mangles: everything due to the necessity of tampering with the stack as little as possible
_getbaseaddress:
    movl %fs:0x30, %eax     #_PEB 
    movl 0xc(%eax), %eax    #_PEB.Ldr
    movl 0xc(%eax), %eax    #_PEB_LDR_DATA.InLoadOrderModuleList.Flink

    # iterate through all _LDR_DATA_TABLE_ENTRYs
    movl %eax, %ebx         # _LIST_ENTRY.Flink
1:
    # check to see BaseDllName matches kernel32.dll (hopefully not kernel32.dll.txt :) 
    xorl %ecx, %ecx
    movw 0x2c(%ebx), %cx    # _LDR_DATA_TABLE_ENTRY.BaseDllName.Length
    shrl $1, %ecx

    movl 0x30(%ebx), %edi   # _LDR_DATA_TABLE_ENTRY.BaseDllName.Buffer
    movl 4(%esp), %esi         # module name
    repe cmpsw

    andl %ecx, %ecx
    jz 2f

    movl (%ebx), %ebx
    cmp %ebx, %edx
    jne 1b

    # FIXME: unable to find library
    .word 0x01cd

2:
    movl 0x18(%ebx), %eax   # fetch module's base address
    ret

# gets the address of an import module given a module base address and a name
# in: 4(%esp) -> module base address, 8(%esp) -> import name; out: %eax -> import module
_getimportmodulebyname:
    movl 4(%esp), %ebx

    # get length of import name specified in argument 
    movl 4(%esp), %edi
    xorl %ecx, %ecx
    decl %ecx
    xorl %eax, %eax
    repnz scasb (%edi)
    incl %ecx
    neg %ecx
    
    # navigate to the import table
    movl %ebx, %eax
    addl 0x3c(%eax), %eax   # PE header
    movl 0x80(%eax), %eax   # get rva of data directory[IMPORT]
    addl %ebx, %eax         # rva 2 real addy, for our import table address
    movl %eax, %edx

    # look through module's list of imports looking for name
    # %ebx = imagebase, %edx = import table address

    movl 8(%esp), %ebp      # the name we're looking for
    jmp .importModuleNameSearch_enter

    .global .importModuleNameSearch_loop
.importModuleNameSearch_loop:
    movl 0xc(%edx), %esi    # import table name rva
    addl %ebx, %esi

    # our strncmp
    pushl %ecx          # STACK +1,
    movl %ebp, %edi
    repe cmpsb

    # if our string matches
    andl %ecx, %ecx
    popl %ecx
    jz 2f

    addl $20, %edx

.importModuleNameSearch_enter:
    movl (%edx), %eax
    andl %eax, %eax
    jnz .importModuleNameSearch_loop

    ## FIXME: unable to find specified import name
    .word 0x01cd

2:
    movl %edx, %eax
    ret

# gets the address of an import given an import module address and it's name
# in: 4(%esp) = base address, 8(%esp) = import module address, c(%esp) = import name
    .global _getimportbyname
_getimportbyname:
    
    movl 4(%esp), %ebx
    movl 8(%esp), %edx
    movl 0xc(%esp), %ebp

    # calculate name length
    movl 0xc(%esp), %edi
    xorl %ecx, %ecx
    decl %ecx
    xorl %eax, %eax
    repnz scasb (%edi)
    incl %ecx
    neg %ecx

    movl 0(%edx), %edx  # import name table rva
    addl %ebx, %edx
    xorl %eax,%eax      # index

.get_index_into_nametable:
    movl (%edx, %eax, 4), %esi
    andl %esi, %esi
    jz 2f

    addl %ebx, %esi
    addl $2, %esi   # skip past the hint
    movl %ebp, %edi
    pushl %ecx      # stack + 1
    
    repe cmpsb
    andl %ecx, %ecx
    popl %ecx       # stack - 1
    jz 1f

    incl %eax
    jmp .get_index_into_nametable

2:
    ## FIXME: unable to find import function
    .word 0x01cd
1:
    movl 8(%esp), %edx
    movl 0x10(%edx), %edx       # import address table rva
    addl %ebx, %edx
    movl (%edx, %eax, 4), %eax
    ret

