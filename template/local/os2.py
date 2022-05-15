import ptypes
from ptypes import *

class void(ptype.undefined): pass
class _far(pint.uint32_t): pass
class _near(pint.uint16_t): pass
class _star(ptype.pointer_t):
    _value_, _object_ = _far, void

def star(t, **attributes):
    attributes.setdefault('_object_', t)
    return dynamic.clone(_star, **attributes)

class VOID(void): pass
class FAR(_near): pass
class NEAR(_near): pass
class FAR32(_far): pass

class VOID_FAR_star(_star):
    _value_, _object_= FAR, VOID
class VOID_NEAR_star(_star):
    _value_, _object_= NEAR, VOID

class int(pint.int32_t): pass
class long(pint.int32_t): pass
class short(pint.int16_t): pass
class char(pint.int8_t): pass
class unsigned_int(pint.uint32_t): pass
class unsigned_long(pint.uint32_t): pass
class unsigned_short(pint.uint16_t): pass
class unsigned_char(pint.uint8_t): pass

class INT(int): pass                # i
class UINT(unsigned_int): pass      # u
class BOOL(INT): pass               # f

class BYTE(unsigned_char): pass     # b
class WORD(unsigned_short): pass    # w
class DWORD(unsigned_long): pass    # dw

class CHAR(char): pass              # ch
class UCHAR(unsigned_char): pass    # uch
class SHORT(short): pass            # s
class USHORT(unsigned_short): pass  # us
class LONG(long): pass              # l
class ULONG(unsigned_long): pass    # ul

class BBOOL(UCHAR): pass            # bf
class SBOOL(USHORT): pass           # sf
class LBOOL(ULONG): pass            # lf

class FLAGS(ULONG): pass            # fl
class PORT(ULONG): pass             # port

class PVOID(VOID_FAR_star): pass    # p
class NPVOID(VOID_NEAR_star): pass  # np

class HANDLE(PVOID): pass           # h

class ulong_t(unsigned_long): pass
class ushort_t(unsigned_short): pass
class uchar_t(unsigned_char): pass
class vaddr_t(unsigned_long): pass

class ldrdld_s(pstruct.type):
    def __dld_next(self):
        return ldrdld_s
    def __dld_mteptr(self):
        return ldrmte_t
    _fields_ = [
        (star(__dld_next), 'dld_next'),     # MUST be first element in structure!
        (star(__dld_mteptr), 'dld_mteptr'),
        (ULONG, 'Cookie'),                  # This field holds a unique value for each process. We chose the address of the process's OS2_PROCESS data structure.
        (ULONG, 'dld_usecnt'),
    ]

class ldrsmte_s(pstruct.type):
    _fields_ = [
        (ulong_t, 'smte_eip'),              # Starting address for module
        (ulong_t, 'smte_stackbase'),        # Stack base
        (ulong_t, 'smte_stackinit'),        # Init commited stack
        (ulong_t, 'smte_objtab'),           # Object table offset
        (ulong_t, 'smte_objcnt'),           # Number of objects in module
        (ulong_t, 'smte_fpagetab'),         # Offset fixup pg tab for 32-bit
        (ulong_t, 'smte_expdir'),           # Export directory offset
        (ulong_t, 'smte_impdir'),           # Import directory offset
        (ulong_t, 'smte_fixtab'),           # Fixup record table offset
        (ulong_t, 'smte_rsrctab'),          # Offset of Resource Table
        (ulong_t, 'smte_rsrccnt'),          # count of resources
        (ulong_t, 'smte_filealign'),        # Alignment factor
        (ulong_t, 'smte_vbase'),            # Virtual base address of module
        (ulong_t, 'smte_heapsize'),         # use for converted 16-bit modules
        (ulong_t, 'smte_autods'),           # Object # for automatic data obj
        (ulong_t, 'smte_iat'),              # pointer to import address table
        (ulong_t, 'smte_debuginfo'),        # Offset of the debugging info
        (ulong_t, 'smte_debuglen'),         # Len of the debug info in bytes
        (ulong_t, 'smte_delta'),            # difference in load address
        (ulong_t, 'smte_pfilecache'),       # Pointer to file cache for
        (ulong_t, 'smte_path'),             # full pathname
        (ushort_t, 'smte_pathlen'),         # length of full pathname
        (ushort_t, 'smte_dyntrchndl'),      # used by dyn trace
        (ushort_t, 'smte_semcount'),        # Count of threads waiting on MTE semaphore. 0=> semaphore is free
        (ushort_t, 'smte_semowner'),        # Slot number of the owner of MTE semaphore
        (ulong_t, 'smte_nrestab'),          # Offset of non-resident tb 16-bit
        (ulong_t, 'smte_cbnrestab'),        # size of non-resident tb 16-bit
        (ulong_t, 'smte_csegpack'),         # count of segments to pack
        (ulong_t, 'smte_ssegpack'),         # size of object for seg packing
        (ulong_t, 'smte_spaddr'),           # virtual address of packed obj
        (ushort_t, 'smte_NEflags'),         # Orginal flags from NE header
        (ushort_t, 'smte_NEexpver'),        # Expver from NE header
        (ushort_t, 'smte_NEexetype'),       # Exetype from NE header
        (ushort_t, 'smte_NEflagsothers'),   # Flagsothers from NE header
    ]

class ldrmte_s(pstruct.type):
    def __mte_link(self):
        return ldrmte_s
    _fields_ = [
        (dyn.array(uchar_t, 2), 'mte_magic'),   # Magic number E32_MAGIC
        (ushort_t, 'mte_usecnt'),               # count of moudules using us
        (ulong_t, 'mte_mflags'),                # Module flags
        (ulong_t, 'mte_mflags2'),               # extension flags word
        (ulong_t, 'mte_modname'),               # pointer to resident module name
        (ulong_t, 'mte_impmodcnt'),             # Num of entries Import Modules
        (ulong_t, 'mte_modptrs'),               # pointer to module pointers table
        (star(ldrdld_s), 'mte_dldchain'),       # pointer to chain of modules loaded by DosLoadModule()
        (ushort_t, 'mte_handle'),               # the handle for this mte
        (HANDLE, 'mte_sfn'),                    # file system number for open file
        (star(__mte_link), 'mte_link'),         # link to next mte
        (star(ldrsmte_s), 'mte_swapmte'),       # link to swappable mte
    ]

