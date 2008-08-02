.section .drectve
	.ascii " -export:reenableWindowHooks"
	.ascii " -export:disableWindowHooks"

.section .data
messageFailure:
    .string "[%x] failure [error: %08x]\n"
messageSuccess:
    .string "[%x] success [handle: %08x]\n"

message:
    .long 0
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

.global _disableWindowHooks
_disableWindowHooks:
    pushl %ebp
    movl %esp, %ebp

    pushl $16
1:
    call getCallerModuleHandle

    pushl 8(%ebp)   #dwThreadId
    pushl %eax
    pushl $hookFunction
    pushl 0xc(%esp)
    call _SetWindowsHookExA@16

    andl %eax, %eax
    jnz 2f

    call _GetLastError@0
    movl (%esp), %ecx

    pushl %eax
    pushl %ecx
    pushl (message + 4*1)
    call _printf
    addl $0xc, %esp

    jmp 3f

2:
    movl (%esp), %ebx
    leal hHooks(, %ebx, 4), %edi
    stosl %eax, (%edi)

    pushl %eax
    pushl 4(%esp)
    pushl (message + 4*2)
    call _printf
    addl $0xc, %esp

    jmp 3f

3:
    decl (%esp)
    jnz 1b

    addl $4, %esp
    popl %ebp
    ret

    .global _reenableWindowHooks
_reenableWindowHooks:
    pushl $16
1:
    
    movl (%esp), %ebx
    leal hHooks(, %ebx, 4), %edi
    pushl %edi
    call _UnhookWindowsHookEx@4

    decl (%esp)
    jnz 1b

    ret

###########################
getLdrModuleByAddress:
    pushl %ebp
    movl %esp, %ebp

    # %edx == PEB.Ldr.InLoadOrderModuleList
    movl %fs:0x30, %edx
    movl 0xc(%edx), %edx
    movl 0x10(%edx), %edx
    movl %edx, %esi

1:
    # check DllBase
    movl 0x18(%esi), %eax
    cmpl %eax, 8(%ebp)
    jb 2f

    # add size, and then check
    addl 0x20(%esi), %eax
    cmpl %eax, %ebx
    ja 2f
    
    movl %esi, %eax
    popl %ebp
    ret
    
    # check if matches original
2:
    movl (%esi), %esi
    cmp %esi, %edx
    jne 1b

    # unable to find a module that matches our caller
    xorl %eax, %eax
    popl %ebp
    ret

#######
getCallerModuleHandle:
    movl (%esp), %ebx

    pushl %ebp
    movl %esp, %ebp

    pushl %ebx
    call getLdrModuleByAddress

    movl %eax, %edx
    addl $0x24, %edx    #FullDllName

    movw 2(%edx), %ax    #FullDllName.MaximumLength
    cwtl
    incl %ecx
    incl %ecx
    movl %eax, %ecx

    subl %ecx, %esp

    subl $3, %esp
    andl $0xfffffffc, %esp

    movw (%edx), %ax    #FullDllName.Length
    cwtl
    movl %eax, %ecx

    movl %esp, %edi
    movl 4(%edx), %esi  #FullDllName.Buffer
    rep movsb (%esi), (%edi)
    xorl %eax, %eax
    stosw %ax, (%edi)

    # (%esp) now points to our name
    pushl %esp
    call _LoadLibraryW@4

    movl %ebp, %esp   # restore our frame
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
    leal hHooks(, %edx, 4), %esi
    lodsl (%esi), %eax

    pushl 0x10(%ebp)
    pushl 0xc(%ebp)
    pushl 0x8(%ebp)
    pushl %eax
    call _CallNextHookEx@16

    popl %ebp
    popa
    ret

