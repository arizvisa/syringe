import ptypes
from ptypes import *

from .WinNT import *

# constants
MAX_GDI_CELLS = 0x10000
UNUSED_GDI_CELLS = 10

# fjBitmap flags
BMF_TOPDOWN = 0x01
BMF_NOZEROINIT = 0x02
BMF_DONTCACHE = 0x04
BMF_USERMEM = 0x08
BMF_KMSECTION = 0x10
BMF_NOTSYSMEM = 0x20
BMF_WINDOW_BLT = 0x40

# iType
STYPE_BITMAP = 0    # DIBSECTION
STYPE_DEVICE = 1
STYPE_DEVBITMAP = 3

# Window Messages
WM_DBGREADENTRY = WM_APP+1
WM_DBGREADCOLORTRANSFORM = WM_APP+2
WM_DBGREADLFONT = WM_APP+3
WM_DBGREADCOLORSPACE = WM_APP+4
WM_DBGREADSURFACE = WM_APP+5
WM_DBGREADPALETTE = WM_APP+6
WM_DBGREADBASEOBJ = WM_APP+7
WM_DBGDPRINT = WM_APP+8
WM_GONE = WM_APP+9

# structures ripped from https://github.com/CoreSecurity/GDIObjDump/blob/master/src/GDIObjDump/common.h
class GDICELL32(pstruct.type):
    _fields_ = [
        (ULONG, 'pKernelAddress'),
        (USHORT, 'wProcessId'),
        (USHORT, 'wCount'),
        (USHORT, 'wUpper'),
        (USHORT, 'wType'),
        (ULONG, 'pUserAddress'),
    ]

class GDICELL64(pstruct.type):
    _fields_ = [
        (PVOID64, 'pKernelAddress'),
        (USHORT, 'wProcessId'),
        (USHORT, 'wCount'),
        (USHORT, 'wUpper'),
        (USHORT, 'wType'),
        (PVOID64, 'pUserAddress'),
    ]

class BASEOBJECT32(pstruct.type):
    _fields_ = [
        (ULONG32, 'hHmgr'),
        (ULONG32, 'ulShareCount'),
        (WORD, 'cExclusiveLock'),
        (WORD, 'cBaseFlags'),
        (ULONG32, 'Tid'),
    ]

class BASEOBJECT64(pstruct.type):
    _fields_ = [
        (ULONG64, 'hHmgr'),
        (ULONG32, 'ulShareCount'),
        (WORD, 'cExclusiveLock'),
        (WORD, 'cBaseFlags'),
        (ULONG64, 'Tid'),
    ]

class SURFOBJ32(pstruct.type):
    _fields_ = [
        (ULONG32, 'dhsurf'),
        (ULONG32, 'hsurf'),
        (ULONG32, 'dhpdev'),
        (ULONG32, 'hdev'),
        (SIZEL, 'sizlBitmap'),
        (ULONG, 'cjBits'),
        (ULONG32, 'pvBits'),
        (ULONG32, 'pvScan0'),
        (LONG, 'lDelta'),
        (ULONG, 'iUniq'),
        (ULONG, 'iBitmapFormat'),
        (USHORT, 'iType'),
        (USHORT, 'fjBitmap'),
    ]


class SURFOBJ64(pstruct.type):
    _fields_ = [
        (ULONG64, 'dhsurf'),
        (ULONG64, 'hsurf'),
        (ULONG64, 'dhpdev'),
        (ULONG64, 'hdev'),
        (SIZEL, 'sizlBitmap'),
        (ULONG64, 'cjBits'),
        (ULONG64, 'pvBits'),
        (ULONG64, 'pvScan0'),
        (LONG32, 'lDelta'),
        (ULONG32, 'iUniq'),
        (ULONG32, 'iBitmapFormat'),
        (USHORT, 'iType'),
        (USHORT, 'fjBitmap'),
    ]

# win32k!gpentHmgr
#0x00 GDIObjType_DEF_TYPE
#0x01 GDIObjType_DC_TYPE
#0x04 GDIObjType_RGN_TYPE
#0x05 GDIObjType_SURF_TYPE
#0x06 GDIObjType_CLIENTOBJ_TYPE
#0x07 GDIObjType_PATH_TYPE
#0x08 GDIObjType_PAL_TYPE
#0x09 GDIObjType_ICMLCS_TYPE
#0x0a GDIObjType_LFONT_TYPE
#0x0b GDIObjType_RFONT_TYPE
#0x0e GDIObjType_ICMCXF_TYPE
#0x0f GDIObjType_SPRITE_TYPE
#0x10 GDIObjType_BRUSH_TYPE
#0x11 GDIObjType_UMPD_TYPE
#0x12 GDIObjType_HLSURF_TYPE
#0x15 GDIObjType_META_TYPE
#0x1c GDIObjType_DRVOBJ_TYPE

class GDICLRXFORM32(pstruct.type):
    # COLORTRANSFORMOBJ32
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (ULONG32, 'hColorTransform'),
    ]

class GDICLRXFORM64(pstruct.type):
    # COLORTRANSFORMOBJ64
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (HANDLE, 'hColorTransform'),
    ]

class COLORSPACE32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (LOGCOLORSPACEW, 'lcsColorSpace'),
        (DWORD, 'dwFlags'),
    ]

class COLORSPACE64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (LOGCOLORSPACEW, 'lcsColorSpace'),
        (DWORD, 'dwFlags'),
    ]

# FIXME: turn this into a pbinary.flags
class PALFLAGS(pint.enum):
    _values_ = [
        ('PAL_INDEXED', 0x00000001), # Indexed palette
        ('PAL_BITFIELDS', 0x00000002), # Bit fields used for DIB, DIB section
        ('PAL_RGB', 0x00000004), # Red, green, blue
        ('PAL_BGR', 0x00000008), # Blue, green, red
        ('PAL_CMYK', 0x00000010), # Cyan, magenta, yellow, black
        ('PAL_DC', 0x00000100), #
        ('PAL_FIXED', 0x00000200), # Can't be changed
        ('PAL_FREE', 0x00000400), #
        ('PAL_MANAGED', 0x00000800), #
        ('PAL_NOSTATIC', 0x00001000), #
        ('PAL_MONOCHROME', 0x00002000), # Two colors only
        ('PAL_BRUSHHACK', 0x00004000), #
        ('PAL_DIBSECTION', 0x00008000), # Used for a DIB section
        ('PAL_NOSTATIC256', 0x00010000), #
        ('PAL_HT', 0x00100000), # Halftone palette
        ('PAL_RGB16_555', 0x00200000), # 16-bit RGB in 555 format
        ('PAL_RGB16_565', 0x00400000), # 16-bit RGB in 565 format
        ('PAL_GAMMACORRECTION', 0x00800000), # Correct colors
    ]

class PALETTE32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (FLONG, 'flPal'),
        (ULONG32, 'cEntries'),
        (ULONG, 'ulTime'),
        (ULONG32, 'hdcHead'),
        (ULONG32, 'hSelected'),
        (ULONG, 'cRefhpal'),
        (ULONG, 'cRefRegular'),
        (ULONG32, 'ptransFore'),
        (ULONG32, 'ptransCurrent'),
        (ULONG32, 'ptransOld'),
        (ULONG, 'unk_038'),
        (ULONG32, 'pfnGetNearest'),
        (ULONG32, 'pfnGetMatch'),
        (ULONG, 'ulRGBTime'),
        (ULONG32, 'pRGBXlate'),
        (ULONG32, 'pFirstColor'),
        (ULONG32, 'ppalThis'),
        (dyn.array(PALETTEENTRY,1), 'apalColors'),
    ]

class PALETTE64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (FLONG, 'flPal'),
        (ULONG32, 'cEntries'),
        (ULONG32, 'ulTime'),
        (HDC, 'hdcHead'),
        (ULONG64, 'hSelected'),
        (ULONG64, 'cRefhpal'),
        (ULONG64, 'cRefRegular'),
        (ULONG64, 'ptransFore'),
        (ULONG64, 'ptransCurrent'),
        (ULONG64, 'ptransOld'),
        (ULONG32, 'unk_038'),
        (ULONG64, 'pfnGetNearest'),
        (ULONG64, 'pfnGetMatch'),
        (ULONG64, 'ulRGBTime'),
        (ULONG64, 'pRGBXlate'),
        (P(PALETTEENTRY), 'pFirstColor'),
        (P(PALETTE), 'ppalThis'),
        (dyn.array(PALETTEENTRY,3), 'apalColors'),
    ]

class FONTOBJ(pstruct.type):
    _fields_ = [
        (ULONG, 'iUniq'),
        (ULONG, 'iFace'),
        (ULONG, 'cxMax'),
        (FLONG, 'flFontType'),
        (ULONG_PTR, 'iTTUniq'),
        (ULONG_PTR, 'iFile'),
        (SIZE, 'sizLogResPpi'),
        (ULONG, 'ulStyleSize'),
        (PVOID, 'pvConsumer'),
        (PVOID, 'pvProducer'),
    ]

class LFONT32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (ULONG32, 'lft'),
        (FLONG, 'fl'),
        (ULONG32, 'Font'),
        (dyn.array(WCHAR,LF_FULLFACESIZE), 'FullName'),
        (dyn.array(WCHAR,LF_FACESIZE), 'Style'),
        (dyn.array(WCHAR,LF_FACESIZE), 'FaceName'),
        (DWORD, 'dwOffsetEndArray'),
        (ENUMLOGFONTEXDVW, 'logfont'),
        (ULONG32, 'lock'),
    ]

class LFONT64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (ULONG32, 'lft'),
        (ULONG32, 'res1'),
        (ULONG32, 'res2'),
        (FLONG, 'fl'),
        (P(FONTOBJ), 'Font'),
        (dyn.array(WCHAR,LF_FULLFACESIZE), 'FullName'),
        (dyn.array(WCHAR,LF_FACESIZE), 'Style'),
        (dyn.array(WCHAR,LF_FACESIZE), 'FaceName'),
        (DWORD, 'dwOffsetEndArray'),
        (ENUMLOGFONTEXDVW, 'logfont'),
        (ULONG64, 'lock'),
    ]

class LFONT_ACTUAL32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (dyn.array(ULONG32,3), 'unk0'),
        (DWORD, 'flags'),
        (dyn.array(BYTE,0x30), 'unk1'),
        (ULONG32, 'pCleanup'),
        (dyn.array(BYTE,0x74), 'unk3'),
        (dyn.array(WCHAR,0x30), 'FONTFAMILY'),
        (dyn.array(WCHAR,0x30), 'FONTNAME'),
    ]


class LFONT_ACTUAL64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (dyn.array(ULONG32,3), 'unk0'),
        (DWORD, 'flags'),
        (dyn.array(BYTE,0x30), 'unk1'),
        (ULONG64, 'pCleanup'),
        (dyn.array(BYTE,0x70), 'unk3'),
        (dyn.array(WCHAR,0x30), 'FONTFAMILY'),
        (dyn.array(WCHAR,0x30), 'FONTNAME'),
    ]

class SURFACE32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (SURFOBJ32, 'SurfObj'),
    # XDCOBJ *   pdcoAA;
        (FLONG, 'flags'),
        (ULONG32, 'ppal'),
        (ULONG32, 'hDDSurface'),
        (SIZEL, 'sizlDim'),
        (ULONG32, 'hdc'), # Doc in "Undocumented Windows", page 546, seems to be supported with XP.
        (ULONG, 'cRef'),
        (ULONG32, 'hpalHint'),

    # For device-independent bitmaps:
        (ULONG32, 'hDIBSection'),
        (ULONG32, 'hSecure'),
        (DWORD, 'dwOffset'),
    ]

class SURFACE64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (SURFOBJ64, 'SurfObj'),
    # XDCOBJ *   pdcoAA;
        (FLONG, 'flags'),
        (ULONG64, 'ppal'),
        (HANDLE, 'hDDSurface'),
        (SIZEL, 'sizlDim'),
        (HDC, 'hdc'), # Doc in "Undocumented Windows", page 546, seems to be supported with XP.
        (ULONG, 'cRef'),
        (HPALETTE, 'hpalHint'),
    # For device-independent bitmaps:
        (HANDLE, 'hDIBSection'),
        (HANDLE, 'hSecure'),
        (DWORD, 'dwOffset'),
    ]

class UNKNOWNOBJ32(pstruct.type):
    _fields_ = [
        (BASEOBJECT32, 'BaseObject'),
        (dyn.array(BYTE,0x100), 'Buffer'),
    ]

class UNKNOWNOBJ64(pstruct.type):
    _fields_ = [
        (BASEOBJECT64, 'BaseObject'),
        (dyn.array(BYTE,0x100), 'Buffer'),
    ]

class GDI_HANDLE_TABLE(pstruct.type):
    class _Type(pint.enum, ULONG):
        _values_ = [
            ('DeviceContext', 1),
            ('Region', 4)
            ('Bitmap', 5)
            ('Palette', 8)
            ('Font', 10),
            ('Brush', 16),
            ('EnhancedMetaFile', 33),
            ('Pen', 48),
        ]

    _fields_ = [
        (ULONG, 'KernelInfo'),
        (DWORD, 'ProcessID'),
        (ULONG, 'Count'),
        (ULONG, 'MaxCount'),
        (_Type, 'Type'),
        (ULONG, 'UserInfo'),
    ]
