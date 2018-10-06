#include "ffi.h"

/* stub-related things (platform) */
void*
ffi_stub_alloc(ffi_platform plat, struct ffi_stub_t* result, size_t count)
{
}
int
ffi_stub_lock(struct ffi_stub_t* stub, ffi_pc* result)
{
}
int
ffi_stub_free(struct ffi_stub_t* stub)
{
}

/* closure/stack related things (arch) */
int
ffi_closure_alloc(ffi_architecture arch, struct ffi_closure_t* c, size_t size)
{
}
int
ffi_closure_free(struct ffi_closure_t* c)
{
}

/* register specific stuff */
int
ffi_regs_add(struct ffi_regs_t* result, ffi_architecture arch, enum ffi_rmap_type t)
{
}
int
ffi_regs_remove_index(struct ffi_regs_t* result, int idx)
{
}
int
ffi_regs_remove_rmap(struct ffi_regs_t* result, enum ffi_rmap_type t)
{
}

/* arch-specific stuff */
int
ffi_internal_call(ffi_architecture arch, ffi_pc pc, ffi_sp sp, struct ffi_regs_t* r)
{
    ffi_sp oldsp;
    u8* p = sp;
    /* XXX: determine which x86 function to call based on architecture */

    /* XXX: this should be in ffi_x86_call */
    // copy pointer to register state to new stack
    struct { ffi_pc pc; ffi_sp sp; struct ffi_regs_t* r; } initstack;
    initstack.pc = pc;
    initstack.sp = sp;
    initstack.r = r;
    memcpy(p, &initstack, sizeof(initstack));
    return ffi_x86_call(&oldsp, p-sizeof(initstack));
}
