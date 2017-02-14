import sys,logging

# service packs
SP0 = 0x00000000
SP1 = 0x00000100
SP2 = 0x00000200
SP3 = 0x00000300
SP4 = 0x00000400
SP5 = 0x00000500

### Include/sdkddkver.h
NTDDI_WIN2K = 0x05000000
NTDDI_WIN2KSP1 = NTDDI_WIN2K | SP1
NTDDI_WIN2KSP2 = NTDDI_WIN2K | SP2
NTDDI_WIN2KSP3 = NTDDI_WIN2K | SP3
NTDDI_WIN2KSP4 = NTDDI_WIN2K | SP4

NTDDI_WINXP = 0x05010000
NTDDI_WINXPSP1 = NTDDI_WINXP | SP1
NTDDI_WINXPSP2 = NTDDI_WINXP | SP2
NTDDI_WINXPSP3 = NTDDI_WINXP | SP3
NTDDI_WINXPSP4 = NTDDI_WINXP | SP4

NTDDI_WS03 = 0x05020000
NTDDI_WS03SP1 = NTDDI_WS03 | SP1
NTDDI_WS03SP2 = NTDDI_WS03 | SP2
NTDDI_WS03SP3 = NTDDI_WS03 | SP3
NTDDI_WS03SP4 = NTDDI_WS03 | SP4

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

NTDDI_WS08 = NTDDI_WIN6SP1
NTDDI_WS08SP2 = NTDDI_WIN6SP2
NTDDI_WS08SP3 = NTDDI_WIN6SP3
NTDDI_WS08SP4 = NTDDI_WIN6SP4

NTDDI_WIN7 = 0x06010000
NTDDI_WIN7SP1 = NTDDI_WIN7 | SP1
NTDDI_WIN7SP2 = NTDDI_WIN7 | SP2
NTDDI_WIN7SP3 = NTDDI_WIN7 | SP3
NTDDI_WIN7SP4 = NTDDI_WIN7 | SP4

NTDDI_WIN8 = 0x06020000

NTDDI_WINBLUE = 0x06020000

# try to automatically identify which NTDDI_VERSION to use by default
if not hasattr(sys,'getwindowsversion'):
    NTDDI_VERSION = 0x06010100
    logging.fatal("Loading ndk without running on a windows-based platform. Defaulting to Windows 7 SP1 (%08x): %s", NTDDI_VERSION, sys.platform)

else:
    _ = sys.getwindowsversion()
    NTDDI_VERSION = ((_.major&0xff) << 24) | ((_.minor&0xff) << 16) | ((_.service_pack_major&0xff) << 8)
    del(_)
    logging.info("Loading ndk with auto-detected %s-based operating-system : %04x SP%x", sys.platform, (NTDDI_VERSION&0xffff0000) >> 16, (NTDDI_VERSION&0x0000ffff)>>8)

WIN64 = 0

def NTDDI_MAJOR(dword):
    return dword & 0xffff0000

def NTDDI_MINOR(dword):
    return dword & 0x0000ffff
