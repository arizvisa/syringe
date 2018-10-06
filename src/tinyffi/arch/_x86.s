.section .text

.global store_x86_regs_gen

.global load_x86_regs_gen

.global __ffi_x86_call //(oldsp, sp)
__ffi_x86_call:
    /// copy current sp to oldsp
    movl %esp,%eax
    movl 4(%esp),%edi
    movl %eax,(%edi)

    /// load new sp
    movl 8(%esp),%eax
    movl %eax,%esp

    /// save the location of oldsp on stack
    pushl %edi

    // 0(%esp) points to oldsp
    // 4(%esp) points to pc
    // 8(%esp) points to sp
    // c(%esp) points to rmap_array

    /// loop to load register states
    movl 0xc(%esp),%esi
1:
    movl 0(%esi),%eax   //load
    andl %eax,%eax
    jz 2f

    pushl 8(%esi)   //rtable
    call %eax
    addl $0xc, %esi
    jmp 1b
2:

    /// call function
    call 4(%esp)

    /// loop to store register states
    movl 0xc(%esp),%esi
1:
    movl 4(%esi),%eax   //store
    andl %eax,%eax
    jz 2f

    pushl 8(%esi)   //rtable
    call %eax
    addl $0xc, %esi
    jmp 1b
2:

    movl 0(%esp),%eax
    movl (%eax),%esp
    xorl %eax,%eax
    ret
