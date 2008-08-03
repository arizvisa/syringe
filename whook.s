.section .drectve
	.ascii " -export:disableWindowHooks"
	.ascii " -export:reenableWindowHooks"
    .ascii " -export:getCallerModuleHandle"

.section .data
messageFailure:
    .string "[%x] failure [error: %08x] "
messageSuccess:
    .string "[%x] success [handle: %08x]\n"
messageNewline:
    .string "\n"

message:
    .long messageNewline
    .long messageFailure
    .long messageSuccess

hHooks:
    .long -1
    .long -2
    .long -3
    .long -4
    .long -5
    .long -6
    .long -7
    .long -8
    .long -9
    .long -0xa
    .long -0xb
    .long -0xc
    .long -0xd
    .long -0xe
    .long -0xf
    .long -0x10
    .long 0xcc

.section .text
getLastErrorMessage:
    pushl %ebp
    movl %esp, %ebp
    subl $4, %esp

    pushl $0
    pushl $0
    leal 8(%esp), %eax
    pushl %eax
    pushl $(1 << 10 | 0)
    call _GetLastError@0
    pushl %eax
    pushl $0
    pushl $(0x1000 | 0x200 | 0x100)
    call _FormatMessageA@28

    pushl (%esp)
    call _printf
    add $4, %esp

    pushl -4(%ebp)
    call _LocalFree@4

    movl %ebp, %esp
    popl %ebp
    ret

    .global _disableWindowHooks
_disableWindowHooks:
    pushl %ebp
    movl %esp, %ebp

    pushl $0xf
1:
    call _getCallerModuleHandle

    pushl 8(%ebp)   #dwThreadId
    pushl %eax
    pushl $hookFunction
    pushl 0xc(%esp)
    call _SetWindowsHookExA@16

    andl %eax, %eax
    jnz 2f

    ## failure
    call _GetLastError@0
    movl (%esp), %ecx

    pushl %eax
    pushl %ecx
    pushl (message + 4*1)
    call _printf
    call getLastErrorMessage
    addl $0xc, %esp

    jmp 3f

2:
    movl (%esp), %ecx
    movl %eax, hHooks(, %ecx, 4)

    pushl %eax
    pushl 4(%esp)
    pushl (message + 4*2)
    call _printf
    addl $0xc, %esp

    jmp 3f

3:
    decl (%esp)
    jns 1b
    addl $4, %esp

    xorl %eax, %eax
    popl %ebp
    ret

    .global _reenableWindowHooks
_reenableWindowHooks:
    pushl $0xf
1:
    
    movl (%esp), %ecx
    pushl hHooks(, %ecx, 4)
    call _UnhookWindowsHookEx@4

    decl (%esp)
    jnz 1b
    addl $4, %esp
    ret

###########################
    .global _GetLdrModuleByAddress
_getLdrModuleByAddress:
    pushl %ebp
    movl %esp, %ebp

    # %edx == PEB.Ldr.InLoadOrderModuleList
    movl %fs:0x30, %edx
    movl 0xc(%edx), %edx
    movl 0x10(%edx), %edx
    movl %edx, %ecx

1:
    # check DllBase
    movl 0x18(%ecx), %eax
    cmpl %eax, 8(%ebp)
    jb 2f

    # add size, and then check
    addl 0x20(%ecx), %eax
    cmpl %eax, 8(%ebp)
    ja 2f
    
    movl %ecx, %eax
    popl %ebp
    ret
    
    # check if matches original
2:
    movl (%ecx), %ecx
    cmp %ecx, %edx
    jne 1b

    # unable to find a module that matches our caller
    xorl %eax, %eax
    popl %ebp
    ret

#######
    .global _getCallerModuleHandle
_getCallerModuleHandle:
    movl (%esp), %edx

    pushl %ebp
    movl %esp, %ebp

    pushl %edx
    call _getLdrModuleByAddress
    addl $4, %esp

    movl %eax, %edx
    addl $0x24, %edx    #FullDllName


    movw 2(%edx), %ax    #FullDllName.MaximumLength
    cwtl
    incl %eax
    incl %eax
    movl %eax, %ecx

    subl %ecx, %esp

    subl $3, %esp
    andl $0xfffffffc, %esp


    movw (%edx), %ax    #FullDllName.Length
    cwtl

    pushl %eax
    pushl 4(%edx)
    leal 8(%esp), %eax
    pushl %eax
    call memcpy
    addl $0xc, %esp

    movw $0, (%esp, %eax,1)

    # (%esp) now points to our name
    pushl %esp
    call _LoadLibraryW@4

    movl %ebp, %esp
    popl %ebp
    ret

memcpy:
    pushl %ebp
    movl %esp, %ebp
    pushl %esi
    pushl %edi

    movl 0x8(%ebp), %edi
    movl 0xc(%ebp), %esi
    movl 0x10(%ebp), %ecx
    movl %ecx, %edx

    shrl $2, %ecx
    rep movsd (%esi), (%edi)

    andl $3, %edx
    movl %edx, %ecx
    rep movsb (%esi), (%edi)

    movl 0x10(%ebp), %eax

    popl %edi
    popl %esi
    popl %ebp
    ret
    

#######
hookFunction:
    ret

## ensure that all hooks don't tamper w/ the current register state
    pusha
    pushl %ebp
    movl %esp, %ebp

    movl 8(%ebp), %edx
    movl hHooks(, %edx, 4), %eax

    pushl 0x10(%ebp)
    pushl 0xc(%ebp)
    pushl 0x8(%ebp)
    pushl %eax
    call _CallNextHookEx@16

    popl %ebp
    popa
    ret 
