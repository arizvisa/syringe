import sys, logging

### Include/sdkddkver.h

## Service Packs
SP0 = 0x00000000
SP1 = 0x00000100
SP2 = 0x00000200
SP3 = 0x00000300
SP4 = 0x00000400
SP5 = 0x00000500

## Windows NT (3.10, 3.50, 3.51)
NTDDI_WINNT310 = 0x030a0000
NTDDI_WINNT350 = 0x03320000
NTDDI_WINNT351 = 0x03330000

## Windows NT (4.0)
NTDDI_WINNT4 = 0x04000000

## Windows 2000 (5.0)
NTDDI_WIN2K = 0x05000000
NTDDI_WIN2KSP1 = NTDDI_WIN2K | SP1
NTDDI_WIN2KSP2 = NTDDI_WIN2K | SP2
NTDDI_WIN2KSP3 = NTDDI_WIN2K | SP3
NTDDI_WIN2KSP4 = NTDDI_WIN2K | SP4

## Windows XP (5.1)
NTDDI_WINXP = 0x05010000
NTDDI_WINXPSP1 = NTDDI_WINXP | SP1
NTDDI_WINXPSP2 = NTDDI_WINXP | SP2
NTDDI_WINXPSP3 = NTDDI_WINXP | SP3
NTDDI_WINXPSP4 = NTDDI_WINXP | SP4

## Windows Server 2003 (5.2)
NTDDI_WS03 = 0x05020000
NTDDI_WS03SP1 = NTDDI_WS03 | SP1
NTDDI_WS03SP2 = NTDDI_WS03 | SP2
NTDDI_WS03SP3 = NTDDI_WS03 | SP3
NTDDI_WS03SP4 = NTDDI_WS03 | SP4

## Windows Vista (6.0)
NTDDI_WIN6 = 0x06000000
NTDDI_WIN6SP1 = NTDDI_WIN6 | SP1
NTDDI_WIN6SP2 = NTDDI_WIN6 | SP2
NTDDI_WIN6SP3 = NTDDI_WIN6 | SP3
NTDDI_WIN6SP4 = NTDDI_WIN6 | SP4

NTDDI_VISTA = NTDDI_WIN6
NTDDI_VISTASP1 = NTDDI_WIN6SP1
NTDDI_VISTASP2 = NTDDI_WIN6SP2
NTDDI_VISTASP3 = NTDDI_WIN6SP3
NTDDI_VISTASP4 = NTDDI_WIN6SP4

NTDDI_LONGHORN = NTDDI_VISTA

## Windows Server 2008 (6.0)
NTDDI_WS08 = NTDDI_WIN6SP1
NTDDI_WS08SP2 = NTDDI_WIN6SP2
NTDDI_WS08SP3 = NTDDI_WIN6SP3
NTDDI_WS08SP4 = NTDDI_WIN6SP4

## Windows 7 (6.1)
NTDDI_WIN7 = 0x06010000
NTDDI_WIN7SP1 = NTDDI_WIN7 | SP1
NTDDI_WIN7SP2 = NTDDI_WIN7 | SP2
NTDDI_WIN7SP3 = NTDDI_WIN7 | SP3
NTDDI_WIN7SP4 = NTDDI_WIN7 | SP4

## Windows 8 (6.2)
NTDDI_WIN8 = 0x06020000

## Windows 8.1 (6.3)
NTDDI_WINBLUE = 0x06030000

## Windows 10 (10.0)
NTDDI_WIN10 = 0x0a000000                 # 1507
NTDDI_WIN10_TH2  = NTDDI_WIN10 | 0x01    # 1511
NTDDI_WIN10_RS1  = NTDDI_WIN10 | 0x02    # 1607
NTDDI_WIN10_RS2  = NTDDI_WIN10 | 0x03    # 1703
NTDDI_WIN10_RS3  = NTDDI_WIN10 | 0x04    # 1709
NTDDI_WIN10_RS4  = NTDDI_WIN10 | 0x05    # 1803
NTDDI_WIN10_RS5  = NTDDI_WIN10 | 0x06    # 1809
NTDDI_WIN10_19H1 = NTDDI_WIN10 | 0x07    # 1903
NTDDI_WIN10_21H2 = NTDDI_WIN10 | 0x08

### Utilities
def NTDDI_MAJOR(dword):
    return dword & 0xffff0000

def NTDDI_MINOR(dword):
    return dword & 0x0000ffff

### Target platform architecture

# Calculate size of uintptr_t using a trick to calculate the size of a lock which
# always has 4 slots for it.
import sys
__allocate__ = __import__('thread').allocate if sys.version_info.major < 3 else __import__('threading')._allocate_lock
SIZEOF_UINTPTR_T = sys.getsizeof(__allocate__()) // 4

# Try and determine what to set WIN64 to based on the platform. Unfortunately
# this is supposed to detect the architecture of the platform, but the best we
# can do is to get the processor on windows and hope it corresponds.
import platform
WIN64 = 1 if platform.architecture()[0] in {"64bit"} else 0

### Target platform auto-detection
NTDDI_VERSION = 0
__SOURCE__ = None

# If we're on Windows, Python exposes sys.getwindowsversion() which we can use
# to determine some things. Unfortunately the Service Pack (CSVersion) is already
# stringified, so we have to conver it back to an integer
if hasattr(sys, 'getwindowsversion'):
    version = sys.getwindowsversion()
    NTDDI_VERSION = ((version.major & 0xff) << 24) | ((version.minor & 0xff) << 16) | ((version.service_pack_major & 0xff) << 8) | ((version.service_pack_minor & 0xff) << 0)
    del(version)
    __SOURCE__ = 'sys-module'

# If the pykd module was imported at some point, then we should be able to use
# it to figure out what version we're debugging.
if 'pykd' in sys.modules and sys.modules['pykd'].isWindbgExt():
    pykd, attributes = sys.modules['pykd'], ['isKernelDebugging', 'is64bitSystem', 'getSystemVersion']

    # if we have all of the newer pykd attributes, then this shit is fucking easy.
    if all(hasattr(pykd, attribute) for attribute in attributes):
        system, VER_PLATFORM_ = pykd.getSystemVersion(), {'WIN32s': 0, 'WIN32_WINDOWS': 1, 'WIN32_NT': 2}
        version = system.win32Major, system.win32Minor, system.buildNumber, system.servicePack, VER_PLATFORM_['WIN32_NT']

        WIN64, NTDDI_VERSION = 1 if pykd.is64bitSystem() else 0, ((version[0] & 0xff) << 24) | ((version[1] & 0xff) << 16) | ((version[3] & 0xff) << 8) | (version[4] & 0xff)

        del(version)
        del(VER_PLATFORM_)
        del(system)

        __SOURCE__ = 'pykd'

    # otherwise, check if we're in the kernel debugger because we'll have to disassemble
    # a symbol in order to extract the version information.
    elif all(hasattr(pykd, 'is64bitSystem'), hasattr(pykd, 'isKernelDebugging')) and pykd.isKernelDebugging():
        import ia32
        WIN64 = 1 if pykd.is64bitSystem() else 0

        # resolve the address for the exact ntddi_version symbol, and create a disassembler
        # at its entrypoint that terminates when we get to a return instruction.
        ea = pykd.expr('nt!RtlIsNtDdiVersionAvailable')
        iterable = (bytes(bytearray(pykd.loadBytes(ea + index, 1))) for index in __import__('itertools').count())
        disassembler = (ia32.decode(item) for item in __import__('itertools').repeat(iterable))
        items = __import__('itertools').takewhile(lambda ins: not ia32.isReturn(ins), disassembler)

        # keep disassembling things until we find the version information in the operand.
        for ins in items:
            if len(ia32.getImmediate(ins)) < 4:
                continue

            # okay. this immediate should already be the NTDDI_VERSION, so we just need to use it.
            NTDDI_VERSION = ia32.decodeInteger(ia32.getImmediate(ins))
            break

        # nothing happened, so we issue a warning and just accept our failure.
        else:
            logging.warning("Unable to determine the version from the disassembly of the {:s} symbol.".format('nt!RtlIsNtDdiVersionAvailable'))

        del(ins)
        del(items)
        del(disassembler)
        del(iterable)
        del(ea)
        del(ia32)

        __SOURCE__ = 'pykd-kernel'

    # otherwise, we need to find the PEB. we then use this to seek to some offsets
    # in order to extract the version components.
    elif hasattr(pykd, 'is64bitSystem'):
        pebaddr = pykd.expr('@$peb')
        if pykd.is64bitSystem():
            WIN64 = 1
            version = pykd.ptrDWord(pebaddr + 0x118), pykd.ptrDWord(pebaddr + 0x11c), pykd.ptrWord(pebaddr + 0x120), pykd.ptrWord(pebaddr + 0x122), pykd.ptrDWord(pebaddr + 0x124)
        else:
            WIN64 = 0
            version = pykd.ptrDWord(pebaddr + 0xa4), pykd.ptrDWord(pebaddr + 0xa8), pykd.ptrWord(pebaddr + 0xac), pykd.ptrWord(pebaddr + 0xae), pykd.ptrDWord(pebaddr + 0xb0)
        del(pebaddr)
        del(pykd)

        # Assign the NTDDI_VERSION from the version components we found (Major, Minor, ServicePack, PlatformId)
        NTDDI_VERSION = ((version[0] & 0xff) << 24) | ((version[1] & 0xff) << 16) | ((version[3] & 0xff) << 8) | (version[4] & 0xff)
        del(version)

        __SOURCE__ = 'pykd-peb'
    del(attributes)

### Inform the user what was determined

# Let the user know what we auto-detected so that way the user knows that they
# need to explicitly assign a default, or assign it as an attribute during
# instantiation.
if NTDDI_VERSION:
    logging.warning("Importing ndk for a {:s}-based platform {:04x} SP{:d} (auto-detected from {:s}): NTDDI_VERSION={:#0{:d}x}".format(sys.platform, (NTDDI_VERSION&0xffff0000) >> 16, (NTDDI_VERSION&0x0000ffff)>>8, __SOURCE__, NTDDI_VERSION, 2 + 8))

# Fall-back to some default since NTDDI_VERSION was not able to be detected..
else:
    NTDDI_VERSION = NTDDI_WIN7SP1
    logging.fatal("Importing ndk from an alternative non-windows based platform ({:s}). Defaulting to Windows 7 SP1 (NTDDI_VERSION={:#0{:d}x})".format(sys.platform, NTDDI_VERSION, 2+8))
