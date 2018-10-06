#ifndef __ffi_arch_x86_h
#define __ffi_arch_x86_h

#include "ffi_types.h"

struct {
    u8 edi;
    u8 esi;
    u8 ebp;
    //u8 esp;
    u8 ebx;
    u8 edx;
    u8 ecx;
    u8 eax;
} x86_regs_gen;

struct {
    f80 st[8];
} x86_regs_fpu;

struct {
    typedef u8[16] u128;
    u128 xmm[16];
} x86_regs_xmm;

struct {
    typedef u8[32] u256;
    u256 ymm[16];
} x86_regs_ymm;

struct {
    typedef u8[64] u512;
    u512 zmm[32];
} x86_regs_zmm;

#endif
