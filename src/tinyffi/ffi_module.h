#ifndef __ffi_module_h
#define __ffi_module_h

/* each platform module callback */
struct ffi_platform_module {
    initialize,

    getwriteable,
    freewriteable,
    getexecutable,
    freeexecutable,

    call_syscall,
};

/* each arch module callback */
struct ffi_arch_module {
    context_init,

    alloc_closure,
    call_closure,
    free_closure,

    call_function,
    call_syscall,
};

#endif
