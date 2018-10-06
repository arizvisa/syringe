### requirements for stub
## need to save state:
# general registers, fpu
# win32 error code (or errno) - kernel32.dll!GetLastError / errno
# tls (?)

## need address of a code object or a function object to call
# PyEval_EvalCode(PyCodeObject* co, PyObject* globals, PyObject* locals)
# code object takes a dictionary containing state
# eip = hook address

### might need generic code for loading/storing/manipulating program state
    registerNamesCount = 8
g_registerNames:
    .string "edi", "esi", "ebp", "esp", "ebx", "edx", "ecx", "eax"

g_pc:
    .string "pc"
g_sp:
    .string "sp"

.global load_state
load_state:
    pushal
    movl %esp, %ebp
    subl $8, %esp

    # FIXME: store fpu state (28 bytes)
    #wait
    #movl %eax, %ebp
    #subl %eax, 28 + 8
    #fnstenv %eax

    # new dict
    call *(PyDict_New)
    movl %eax, -4(%ebp)

    # store general registers to dictionary
    movl $g_registerNames, %esi
    pushl $registerNamesCount - 1

1:
    movl (%esp), %ecx
    pushl (%ebp, %ecx, 4)
    call *(PyInt_FromLong)

    movl 4(%esp), %ecx
    pushl %eax
    leal (%esi, %ecx, 4), %eax
    pushl %eax
    pushl -4(%ebp)
    call *(PyDict_SetItemString)
    addl $0x10, %esp

    decl (%esp)
    jns 1b
    addl $4, %esp

    # store program counter
    pushl 0x20(%ebp)
    call *(PyInt_FromLong)
    pushl %eax
    pushl $g_pc
    pushl -4(%ebp)
    call *(PyDict_SetItemString)
    addl $0x10, %esp

    # store stack pointer alias
    pushl 0xc(%ebp)
    call *(PyInt_FromLong)
    pushl %eax
    pushl $g_sp
    pushl -4(%ebp)
    call *(PyDict_SetItemString)
    addl $0x10, %esp

    addl $8, %esp
    popal
    ret
