import sys,time
import utils

import debugger,memorymanager,psapi
from ctypes import *

# TODO:
# X remotely allocate/deallocate memory
#    v abstract this to a memqueue interface
#    X implemented phk-like malloc in memorymanager.py

#we need a better way to load code
# X  can use loadlibrary perhaps
#   X wrote a linker for coff objects
#

#we need some code for a generic breakpoint so that we
#    can "signal" the management process.

def getProcessIdByName(ps, name):
    res = ps.enumerateProcesses()
    res = dict([(b,a) for a,b,c,d in res])
    return res[ unicode(name) ]

def enumerateThreadWindows(threadId):
    WNDENUMPROC = WINFUNCTYPE(c_int, c_int, c_long)

    windows = []
    def enumerator(hWnd, object):
        windows.append(hWnd)
        return 1

    res = u32.EnumThreadWindows(threadId, WNDENUMPROC(enumerator), c_void_p(0))
    assert bool(res)

    return windows

def getWindowText(hWnd):
    buffer = (c_byte*1024)()
    res = u32.GetWindowTextA( hWnd, pointer(buffer), len(buffer) )
    assert bool(res), repr(getLastErrorTuple())
    return ''.join([ chr(x) for x in buffer ][ : res ])

def sendUpdateMessage(hWnd):
    WM_PAINT = 0x000f   # WinUser.h
    res = u32.PostMessageA(hWnd, WM_PAINT, 0, 0)
    if bool(res):
        print 'WM_PAINT was processed by application'
    else:
        print 'WM_PAINT was not processed by application'
    return True

