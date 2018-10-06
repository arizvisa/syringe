#ifndef __ffi_h
#define __ffi_h

enum ffi_error_t {
    SUCCESS = 0,
    FAILURE,
    MEMORY,
};

/* these come from architecture-specific code */
typedef enum {
    FFI_ARCH_X86, FFI_ARCH_X64, FFI_ARCH_MIPS64
} ffi_arch;

typedef enum {
    FFI_PLAT_WINDOWS7,
    FFI_PLAT_FREEBSD,
    FFI_PLAT_LINUX,
    FFI_PLAT_WINDOWS9X,
    FFI_PLAT_WINDOWSNT,
} ffi_platform;

/* types used for specifying the program-counter and stack-pointer */
typedef int ffi_pc;
typedef int ffi_sp;

/* contains platform and architecture */
struct ffi_ctx_t {
    ffi_arch architecture;
    ffi_platform platform;

    ffi_pc exception_handler;       // platform-specific default exception handler

    /* register mask to pay attention to */
    int register_mask;

    /* the current stack to use */
    struct ffi_closure_t st;
} *ffi_ctx;

/* the stack for some code */
struct ffi_closure_t {
    size_t size;
    void* base; // allocation pointer

    ffi_sp sp;  // stack pointer that resides within base:+size
};

/* some code to get executed */
struct ffi_stub_t {
    ffi_platform platform;
    size_t size;

    enum { WRITE,EXEC } state;
    union {
        void* write;
        void* exec;
    } p;
};

struct ffi_coro_t {
    struct ffi_closure_t state;
    struct ffi_stub_t yield;

    struct ffi_regs_t r;

    ffi_pc pc;
    ffi_sp sp;
};

enum ffi_rmap_type;  // unique identity of register set
struct ffi_rmap_t {
    enum ffi_rmap_type t;  // unique identity of register set
    union {
        // XXX: each union member is defined by the arch-specific part
    } r;
};

struct ffi_regs_t {
    size_t count;
    struct ffi_rmap_t* map;
};

#endif
