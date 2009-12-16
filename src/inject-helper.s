#####################################################################
.section .todo

#TODO:
## stage 1
#    all process management functions will be using only the following 4 api calls
#        for resolving kernel32 exports, our own GetProcAddress(name)
#        for storing our alternative stack pointer, our own TlsAlloc()
#
#        for calling code and ensuring we aren't mangling the stack, kernel32!QueueUserAPC
#            * we're going to assume that anything queueuserapc does to the stack is perfectly valid
#        for loading more code, we'll need kernel32!LoadLibrary
#    this'll give us the tools we need for calling code without modifying the stack.
#
## stage 2
#    we'll need to prep an alternative stack that we can call with
#
#    queueuserapc an allocation, and then branch to _pause
#        (make sure we suspend ourselves so no more calls get queued to us?)
#    now we can switch to our alternative stack
#    call TlsAlloc()
#    and store our stack pointer here
#    we'll store our tlsindex at the top of our stack
#
## stage 3
#    we now have an alternative stack. woot.
#
#    select a thread and then call loadlibrary to map more code into the process
#        * can even create a COM object to do this also if wanted
#
#    start initializing python

# ??? need to get ntdll!NtQueueApcThread

#.text:7C8098EB                   GetCurrentThread proc near
#.text:7C8098EB 6A FE                             push    0FFFFFFFEh
#.text:7C8098ED 58                                pop     eax
#.text:7C8098EE C3                                retn

.section .drectve
#	.ascii " -export:pause"
#	.ascii " -export:call"

#####################################################################
.section .text
# our function lookup table
    .long _pause
    .long _call

#######
.global _pause  #()
_pause:
    jmp .

.global _call   #(%edi)
_call:
_call_nostack:
    # FIXME: this should be using QueueUserAPC to dispatch a call, but with only reg parameters
    call *%edi
    call _pause

_call_altstack:
    # XXX: this switches to the alternative stack
    call *%edi
    call _pause

TlsFill:
    movl $16, %ecx
1:
    pushl %ecx
    call _TlsAlloc@0
    popl %ecx
    leal 0xe10(%ebx, %eax, 4), %edx
    movl $0x0d0e0a0d, (%edx)
    decl %ecx
    jnz 1b

######################################################################
    .global _loader

#this code supposedly performs the following:
#look through PEB Ldr Initialization list looking for kernel32.dll
#iterate through the imports section looking for ntdll
#look through the ntdll imports for NtAllocateVirtualMemory
#write the esp and the return address somewhere, set esp to that dword, and
#then jmp to NtAllocateVirtualMemory. This should give us a page to set esp to
#and then we can call whatever we want unhindered
#
#i'm doing it the kernel32->ntdll way because on some platforms i've had
#problems looking for ntdll.dll in the Ldr list.
#
# XXX: todo, optimize for u-v pipe, and other such things

_loader:

    ## find a tls entry that we can use for a stack
    ## XXX: hopefully the operating system does not dispatch a window message
    ##      to the thread, heh. ;)
    cld

    # assign tlsbitmap(%esi) location and size(%edx)
    movl %fs:0x18, %ebx     # tib->teb
    movl 0x30(%ebx), %eax   # teb->peb
    mov 0x40(%eax), %eax     # peb->TlsBitmap
    movl (%eax), %edx        # RTL_BITMAP->size
    movl 4(%eax), %esi        # RTL_BITMAP->buffer

    # find out which tlsindex is free (in multipiles of 8. ;) )
    #   XXX: this can fail if the bitmap size isn't statically 64
    xorl %eax, %eax
    movl %edx, %ecx
    movl %esi, %edi
    repnz scasb
    decl %edi
    subl %edx, %ecx
    negl %ecx
    decl %ecx
    #shl $3, %ecx

    # occupy a few slots
    leal (%esi, %ecx, 1), %edi
    decb %al
    stosb

    # get a pointer to our bottom-most TlsSlot
    leal 0xe10(%ebx, %ecx, 4), %edx
    movl $0x0d0e0a0d, (%edx)    # canary...heh
    addl $(7*4), %edx

    # write our old esp there, and switch stack
    movl %esp, (%edx)
    movl %edx, %esp         # woo, 7 slots of stack
#    movl $topStack, %esp

####### lvl 0 stack is initialized

    call 1f
kernel32_unicode:
    .string "k" "e" "r" "n" "e" "l" "3" "2" "." "d" "l" "l" ""
1:
    #movl $kernel32_unicode, %ebp
    popl %ebp

breakhere:
    int3
####### find the base address for kernel32.dll -> %ebx
    # look through initializationorder list
    # %edx == PEB.Ldr.InInitializationOrderLinks
    movl %fs:0x30, %eax
    movl 0xc(%eax), %eax
    movl 0x10(%eax), %eax

    # iterate through all _LDR_DATA_TABLE_ENTRYs
    movl %eax, %ebx       # _LIST_ENTRY.Flink
1:
    # check to see BaseDllName matches kernel32.dll
    xorl %ecx, %ecx
    movw 0x2c(%ebx), %cx
    shrl $1, %ecx

    movl 0x30(%ebx), %edi   # Ldr name
    movl %ebp, %esi         # module name
    repe cmpsw

    andl %ecx, %ecx
    jz 2f

    movl (%ebx), %ebx
    cmp %ebx, %edx
    jne 1b

    # FIXME: unable to find library
    .word 0x01cd

2:

####### set %edx to import table address of module in %ebx
#### XXX: need to not trash esp with this code
    movl 0x18(%ebx), %ebx   # module's base address
    pushl %ebx      # XXX: STACK +1
    movl %ebx, %eax
    
    addl 0x3c(%eax), %eax   # PE header
    movl 0x80(%eax), %eax   # data directory[IMPORT], or rather our import table
    addl %ebx, %eax         # rva 2 real addy

    pushl %eax      # XXX: STACK +2

######## strlen('ntdll.dll')...
    call 1f
ntdll_ascii:
    .string "ntdll.dll"
1:
    #movl $ntdll_ascii, %ebp
    popl %ebp

    ## get length of import name in %edi
    movl %ebp, %edi
    xorl %ecx, %ecx
    decl %ecx
    xorl %eax, %eax
    repnz scasb (%edi)
    incl %ecx
    neg %ecx
    
######## look through list of imports for specified import module
# ebx = imagebase
# ebp = import name
# returns %eax for importm odule

    movl (%esp), %eax     # import table at +2
.importNameSearch_loop:
    movl 0xc(%eax), %esi
    addl %ebx, %esi #rva2addr

    # our strncmp
    pushl %ecx
    movl %ebp, %edi
    repe cmpsb

    andl %ecx, %ecx
    popl %ecx
    jz 2f

    addl $20, %eax
    movl (%eax), %eax

    andl %ecx, %ecx
    jnz .importNameSearch_loop

    ## FIXME: unable to find specified import name
    .word 0x01cd

######## strlen('NtAllocateVirtualMemory')
2:
    call 1f
NtAllocateVirtualMemory_ascii:
    .string "NtAllocateVirtualMemory"
1:
    #movl $NtAllocateVirtualMemory_ascii, %ebp
    popl %ebp

    movl %ebp, %edi
    xorl %ecx, %ecx
    decl %ecx
    xorl %eax, %eax
    repnz scasb (%edi)
    incl %ecx
    neg %ecx

### XXX: finish this
######## now look for NtAllocateVirtualMemory in the import's function list
# %ebx = base address
# %ebp = import search string
# %ecx = import function name length

# %ebx = import rva entry (???)

jmp .
# XXX: everything after this is wrong (writing asm sucks)

    # get pointer to name table
    movl 0(%esp), %eax
    addl %ebx, %eax

    # get pointer to address table
    movl 0x10(%ebx), %ecx
    addl %ebx, %ecx

    # assign them
    movl %eax, %esp #name table
    movl %ecx, %ebx #address table

# %eax = counter
    xorl %eax, %eax
    movl (%ecx), %ecx
    jmp 1f

.importFunctionSearch_loop:
    movl (%esp, %eax, 4), %esi
    leal 2(%esi), %esi
    movl %ebp, %edi
    movl %edx, %ecx
    repe cmpsb

    andl %ecx, %ecx
    jz 2f

    incl %eax

    # until a null
    movl (%esp, %eax, 4), %ecx
1:
    andl %ecx, %ecx
    jnz .importFunctionSearch_loop

    ## FIXME: unable to find import function
    .word 0x01cd

2:

# %eax = index
# %ebx = import address table

    ret

