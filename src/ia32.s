/*
    patched in branch
    call python code object with saved state
    modify dict
    restore state using new dict
    return to assembly stub
    execute lifted code
    back to original
*/
    .section .rodata

    registerNamesCount = 8
gp_registerNames:
#    .string "eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"
    .string "edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax"
gp_registerEip:
    .string "eip"

    .section .data
gp_codeobject: .long 0         /* code object that gets executed with our saved cpu state */

    .section .text

/*
 *   void executestate(, global codeobject)
 *   executes global codeobject passing along a dictionary containing the register state
 */
    .global executestate
executestate:
    pusha
    movl %esp, %ebp
    subl $8, %esp

# XXX: we can use a new stack if we want for some reason

## store processor state into a dictionary
    call PyDict_New
    movl %eax, -4(%ebp)

    movl $gp_registerNames, %esi
    pushl $registerNamesCount - 1

1:
    movl (%esp), %ecx
    pushl (%ebp, %ecx, 4)
    call PyInt_FromLong

    movl 4(%esp), %ecx
    pushl %eax
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl -4(%ebp)
    call PyDict_SetItemString
    addl $0x10, %esp

    decl (%esp)
    jns 1b
    addl $4, %esp

## do eip
    pushl 0x20(%ebp)
    call PyInt_FromLong
    pushl %eax
    pushl $gp_registerEip
    pushl -4(%ebp)
    call PyDict_SetItemString
    addl $0x10, %esp

###################
@@callHook:
    pushl -4(%ebp)
    pushl $1
    call PyTuple_Pack
    addl $8, %esp
    pushl gp_codeobject
    pushl %eax
    call PyObject_CallObject
    addl $8, %esp

#################
## restore processor state from dictionary using popa
@@do_restore:
    leal gp_registerNames, %esi
    pushl $registerNamesCount - 1
1:
    movl (%esp), %ecx
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl -4(%ebp)
    call PyDict_GetItemString
    pushl %eax
    call PyInt_AsLong
    addl $0xc, %esp

    movl (%esp), %ecx
    movl %eax, (%ebp, %ecx, 4)

    decl (%esp)
    jns 1b
    addl $4, %esp

    ## restore eip
    pushl $gp_registerEip
    pushl -4(%ebp)
    call PyDict_GetItemString
    pushl %eax
    call PyInt_AsLong
    addl $0xc, %esp

    movl %eax, 0x20(%ebp)

    ## we're done, free reference and restore cpu state
    pushl -4(%ebp)
    call Py_DecRef

    addl $(4+8), %esp
    movl %ebp, %esp
    popa
    ret
