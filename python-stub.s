.section .data

gp_pythonDllName: .string "python24.dll"
gv_pythonDllHandle: .long 0

gp_mainModule:  .long 0
gp_hookDictionary:  .long 0

## function names
pythonExportCount = 18
_gp_pythonExportNames:
@1: .string "PyDict_New"
@2: .string "PyDict_SetItemString"
@3: .string "PyInt_FromLong"
@4: .string "PyTuple_Pack"
@5: .string "PyObject_CallObject"
@6: .string "PyString_AsString"
@7: .string "PyDict_GetItem"
@8: .string "PyDict_GetItemString"
@9: .string "PyInt_AsLong"
@10: .string "Py_DecRef"
@11: .string "Py_Initialize"
@12: .string "Py_Finalize"
@13: .string "PyRun_SimpleString"
@14: .string "PyEval_GetGlobals"
@15: .string "PyDict_SetItem"
@16: .string "PyEval_GetFrame"
@17: .string "PyImport_AddModule"
@18: .string "PyModule_GetDict"
@19: .string "Py_IncRef"

gp_pythonExportNames:
    .long @1, @2, @3, @4, @5, @6, @7, @8, @9, @10, @11, @12, @13, @14, @15, @16
    .long @17, @18, @19

gp_pythonExports:
    gpf_PyDict_New:   .long 0
    gpf_PyDict_SetItemString:    .long 0
    gpf_PyInt_FromLong:  .long 0
    gpf_PyTuple_Pack:   .long 0
    gpf_PyObject_CallObject:   .long 0
    gpf_PyString_AsString:   .long 0
    gpf_PyDict_GetItem:    .long 0
    gpf_PyDict_GetItemString:    .long 0
    gpf_PyInt_AsLong:   .long 0
    gpf_Py_DecRef:   .long 0
    gpf_Py_Initialize:   .long 0
    gpf_Py_Finalize:   .long 0
    gpf_PyRun_SimpleString:   .long 0
    gpf_PyEval_GetGlobals:  .long 0
    gpf_PyDict_SetItem:  .long 0
    gpf_PyEval_GetFrame:  .long 0
    gpf_PyImport_AddModule: .long 0
    gpf_PyModule_GetDict:   .long 0
    gpf_Py_IncRef:  .long 0

    registerNamesCount = 8
gp_registerNames:
#    .string "eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"
    .string "edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax"
gp_registerEip:
    .string "eip"

gp_testHook:    .string "testHook"
gp_pythonApplication:
    .string "def testHook(ctx):\n    print repr(ctx)\n\n\nprint 'hello world'\n"

##############################################################################
.section .text

    .global hookstub
hookstub:
    pusha
    movl %esp, %ebp
    subl $8, %esp
    
# XXX: we can use a new stack if we want for some reason

## store processor state into a dictionary
    call *(gpf_PyDict_New)
    movl %eax, -4(%ebp)

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
    pushl -4(%ebp)
    call *(gpf_PyDict_SetItemString)
    addl $0x10, %esp

    decl (%esp)
    jns 1b
    addl $4, %esp

## do eip
    pushl 0x20(%ebp)
    call *(gpf_PyInt_FromLong)
    pushl %eax
    pushl $gp_registerEip
    pushl -4(%ebp)
    call *(gpf_PyDict_SetItemString)
    addl $0x10, %esp

###################
@@callHook:
    int3
    movl 0x20(%ebp), %eax
    pushl %eax
    call *(gpf_PyInt_FromLong)
    pushl %eax
    movl gp_hookDictionary, %eax
    pushl %eax
    call *(gpf_PyDict_GetItem)
    addl $0xc, %esp

    andl %eax, %eax
    jz @@do_restore

    pushl %eax
    pushl -4(%ebp)
    pushl $1
    call *(gpf_PyTuple_Pack)
    addl $8, %esp
    pushl %eax
    call *(gpf_PyObject_CallObject)
    addl $8, %esp

#################
## restore processor state from dictionary
@@do_restore:
    leal gp_registerNames, %esi
    pushl $registerNamesCount - 1
1:
    movl (%esp), %ecx
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl -4(%ebp)
    call *(gpf_PyDict_GetItemString)
    pushl %eax
    call *(gpf_PyInt_AsLong)
    addl $0xc, %esp

    movl (%esp), %ecx
    movl %eax, (%ebp, %ecx, 4)

    decl (%esp)
    jns 1b
    addl $4, %esp

    ## restore eip
    pushl $gp_registerEip
    pushl -4(%ebp)
    call *(gpf_PyDict_GetItemString)
    pushl %eax
    call *(gpf_PyInt_AsLong)
    addl $0xc, %esp

    movl %eax, 0x20(%ebp)

    ## we're done
    pushl -4(%ebp)
    call *(gpf_Py_DecRef)
    addl $4, %esp

    addl $8, %esp
    movl %ebp, %esp
    popa
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
    jmp .

#############
#uhookah[address] = fn
#
#class uhookah(dict):
#    def __setitem__(self, key, value):
#        assert callable(value)
#        self[key] = value
#        # XXX: set hook
#
#    def __delitem__(self, key):
#        # XXX: remove hook

setItemByInt:
    pushl %ebp
    movl %esp, %ebp

    pushl 8(%ebp)
    call *(gpf_PyInt_FromLong)
    
    pushl 0xc(%ebp)
    pushl %eax
    pushl gp_hookDictionary
    call *(gpf_PyDict_SetItem)
    addl $0x10, %esp

    popl %ebp
    ret $8

getGlobal:
    pushl %ebp
    movl %esp, %ebp

    movl gp_mainModule, %eax
    
    pushl 8(%ebp)
    pushl %eax
    call *(gpf_PyDict_GetItemString)
    addl $8, %esp

    popl %ebp
    ret $4

    .global _WinMain@16
_WinMain@16:
    pushl %ebp
    movl %esp, %ebp

    ## load important shit from python module
    call initImports
    call *(gpf_Py_Initialize)

    ## create a dictionary for storing hook functions
    call *(gpf_PyDict_New)
    movl %eax, gp_hookDictionary

    ## create main
    call 1f
    .string "__main__"
1:
    call *(gpf_PyImport_AddModule)
    pushl %eax
    call *(gpf_PyModule_GetDict)
    addl $8, %esp
    movl %eax, gp_mainModule

    ## load hook example code
    pushl $gp_pythonApplication
    call *(gpf_PyRun_SimpleString)
    addl $4, %esp

    ## get reference to testHook
    leal gp_testHook, %eax
    pushl %eax
    call getGlobal  # XXX: might need to Py_IncRef what this returns

    ## set it to our hook dictionary
    pushl %eax
    pushl $@@returnaddress
    call setItemByInt

#    ## perform test
    movl $0xa, %eax
    movl $0xb, %ebx
    movl $0xc, %ecx
    movl $0xd, %edx
    movl $0xe, %esi
    movl $0xf, %edi
    mov $0xfeeddead, %ebp
    call hookstub
@@returnaddress:

    call *(gpf_Py_Finalize)

    popl %ebp
    ret

