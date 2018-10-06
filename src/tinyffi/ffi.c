#include "ffi.h"

/* creates a context that stores the architecture and platform */
int
ffi_new(struct ffi_ctx* c, enum ffi_arch arch, enum ffi_platform plat, size_t stacksize)
{
    ffi_ctx res;

    res = malloc( sizeof(*res) );
    if (res == NULL)
        return MEMORY;

    *c = res;
    return SUCCESS;
}

int
ffi_destroy(struct ffi_ctx* c)
{
    *c = NULL;
    return SUCCESS;
}

/* make a system call. */
int
ffi_syscall(struct ffi_ctx c, int syscall_number, struct ffi_regs_t* r)
{
    return SUCCESS;
}

/* call some function at pc */
int
ffi_call(struct ffi_ctx c, ffi_pc pc, struct ffi_regs_t* r)
{
    int res;
    res = ffi_internal_call(c.architecture, pc, c.st.sp, r);
    return SUCCESS;
}

/* init a coroutine at pc. writes a pointer to ypc which will yield if called */
int
ffi_cocall(struct ffi_ctx c, ffi_pc pc, ffi_pc* ypc)
{
    return SUCCESS;
}

int
ffi_coresume(struct ffi_ctx c, ffi_pc pc, ffi_pc* ypc)
{
    return SUCCESS;
}
