#include "ffi.h"
#include "ffi_module.h"

void*
getWriteable(void* desiredAddress, size_t sz)
{
    // MEM_COMMIT = 0x1000
    // MEM_RESERVE = 0x2000
    res = VirtualAllocEx(
        0, desiredAddress, page_aligned(sz), MEM_COMMIT|MEM_RESERVE, PAGE_READWRITE
    );
    return res;
}


void*
getExecutable(void* oldAddress, size_t sz)
{
    DWORD oldPermissions;
    res = VirtualProtectEx(
        0, oldAddress, page_aligned(sz), PAGE_EXECUTE, &oldPermissions
    );
    return oldAddress;
}

int
freeWriteable(void* address, size_t sz)
{
    // MEM_DECOMMIT = 0x4000
    res = VirtualFreeEX(
        0, address, page_aligned(sz), MEM_DECOMMIT
    );
    return res;
}

int
freeExecutable(void* address, size_t sz)
{
    DWORD oldPermissions;
    // MEM_DECOMMIT = 0x4000
    res = VirtualProtectEx(
        0, address, page_aligned(sz), PAGE_EXECUTE, &oldPermissions
    );
    return res;
}

struct {
    HANDLE k32;
    HANDLE process;
} ctxstate;

static HANDLE k32;

int
initialize()
{
    k32 = LoadLibrary("kernel32.dll")
}
