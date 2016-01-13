### Include/sdkddkver.h
NTDDI_WIN2K = 0x05000000
NTDDI_WIN2KSP1 = 0x05000100
NTDDI_WIN2KSP2 = 0x05000200
NTDDI_WIN2KSP3 = 0x05000300
NTDDI_WIN2KSP4 = 0x05000400

NTDDI_WINXP = 0x05010000
NTDDI_WINXPSP1 = 0x05010100
NTDDI_WINXPSP2 = 0x05010200
NTDDI_WINXPSP3 = 0x05010300
NTDDI_WINXPSP4 = 0x05010400

NTDDI_WS03 = 0x05020000
NTDDI_WS03SP1 = 0x05020100
NTDDI_WS03SP2 = 0x05020200
NTDDI_WS03SP3 = 0x05020300
NTDDI_WS03SP4 = 0x05020400

NTDDI_WIN6 = 0x06000000
NTDDI_WIN6SP1 = 0x06000100
NTDDI_WIN6SP2 = 0x06000200
NTDDI_WIN6SP3 = 0x06000300
NTDDI_WIN6SP4 = 0x06000400

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

# TODO: should probably automatically identify which NTDDI_VERSION to use by default
NTDDI_VERSION = 0x06010000

WIN64 = 0

def NTDDI_MAJOR(dword):
    return dword & 0xffff0000
def NTDDI_MINOR(dword):
    return dword & 0x0000ffff
