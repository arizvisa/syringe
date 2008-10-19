.section .data

gp_pythonDllName: .string "python24.dll"
gv_pythonDllHandle: .long 0

## function names

pythonExportCount = 10
_gp_pythonExportNames:
@1: .string "PyDict_New"
@2: .string "PyDict_SetItemString"
@3: .string "PyInt_FromLong"
@4: .string "PyObject_Repr"
@5: .string "PyString_AsString"
@6: .string "PyDict_GetItemString"
@7: .string "PyInt_AsLong"
@8: .string "Py_DecRef"
@9: .string "Py_Initialize"
@10: .string "Py_Finalize"

gp_pythonExportNames:
    .long @1, @2, @3, @4, @5, @6, @7, @8, @9, @10

gp_pythonExports:
    gpf_PyDict_New:   .long 0
    gpf_PyDict_SetItemString:    .long 0
    gpf_PyInt_FromLong:  .long 0
    gpf_PyObject_Repr:   .long 0
    gpf_PyString_AsString:   .long 0
    gpf_PyDict_GetItemString:    .long 0
    gpf_PyInt_AsLong:   .long 0
    gpf_Py_DecRef:   .long 0
    gpf_Py_Initialize:   .long 0
    gpf_Py_Finalize:   .long 0


registerNamesCount = 8
gp_registerNames:
#    .string "eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"
    .string "edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax"

.section .text

    .global hookstub
hookstub:
    pusha
    movl %esp, %ebp
    subl $4, %esp
    
# XXX: we can use a new stack if we want for some reason

## store processor state into a dictionary
    call *(gpf_PyDict_New)
    movl %eax, (%esp)

    movl $gp_registerNames, %esi
    pushl $registerNamesCount - 1

1:
    movl (%esp), %ecx
    pushl (%ebp, %ecx, 4)
    call *(gpf_PyInt_FromLong)
    
    movl 4(%esp), %ecx
    pushl %eax
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl 0x10(%esp)
    call *(gpf_PyDict_SetItemString)

    addl $0x10, %esp
    decl (%esp)
    jns 1b
    addl $4, %esp

###################
## XXX: print out dictionary in python
    pushl (%esp)
    call *(gpf_PyObject_Repr)
    movl %eax, %esi

    pushl %esi
    call *(gpf_PyString_AsString)

## XXX: print out %eax
    pushl %esi
    call *(gpf_Py_DecRef)
    addl $0xc, %esp

#################
## restore processor state from dictionary
    leal gp_registerNames, %esi
    pushl $registerNamesCount - 1
1:
    movl (%esp), %ecx
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl 8(%esp)
    call *(gpf_PyDict_GetItemString)

    pushl %eax
    call *(gpf_PyInt_AsLong)
    addl $0xc, %esp

    movl (%esp), %ecx
    movl %eax, (%ebp, %ecx, 4)

    decl (%esp)
    jns 1b
    addl $4, %esp

    pushl (%esp)
    call *(gpf_Py_DecRef)
    addl $8, %esp

    movl %ebp, %esp
    popa
    ret

    .global _WinMain@16
_WinMain@16:
    pushl %ebp
    movl %esp, %ebp

    ## load important shit from python module
    call initImports
    call *(gpf_Py_Initialize)

    ## perform test
    movl $0xa, %eax
    movl $0xb, %ebx
    movl $0xc, %ecx
    movl $0xd, %edx
    movl $0xe, %esi
    movl $0xf, %edi
    mov $0xfeeddead, %ebp
    call hookstub

    call *(gpf_Py_Finalize)

    popl %ebp
    ret

initImports:
    pushl %ebp
    movl %esp, %ebp

    pushl $gp_pythonDllName
    call _LoadLibraryA@4
    movl %eax, gv_pythonDllHandle

    leal gp_pythonExportNames, %esi
    leal gp_pythonExports, %edi

    ## getprocaddr all gp_pythonExportNames, and write them to gp_pythonExports
    pushl %eax
    pushl $pythonExportCount - 1
1:
    movl (%esp), %ecx

    pushl (%esi, %ecx, 4)
    pushl 8(%esp)
    call _GetProcAddress@8

    andl %eax, %eax
    jz 2f

    movl (%esp), %ecx
    movl %eax, (%edi, %ecx, 4)

    decl (%esp)
    jns 1b

    addl $8, %esp
    movl %ebp, %esp
    popl %ebp
    ret

    # XXX: error with getprocaddress
2:
    int3
    jmp .
