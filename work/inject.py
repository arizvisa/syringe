import sys,time
sys.path.append('lib/')
sys.path.append('work/')
import utils

import debug,alloc,psapi
from ctypes import *

# TODO:
# X remotely allocate/deallocate memory
#    ? abstract this to a memqueue interface
# 
#we need a better way to load code
#    can use loadlibrary perhaps
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

if __name__ == '__main__':

    ps = psapi.getInterface()
    ps.attach()
    processId = getProcessIdByName(ps, 'calc.exe')
    x = ps.enumerateThreads(processId)
    
    threadId = x[0][0]
    dbg = debug.getDebugger()
    dbg.enablePrivileges()
    dbg.attach(threadId)

    allocator = alloc.getPageAllocator()
    allocator.attach(dbg.process.handle)

#    v = allocator.getWriteable(None, 64)
#    allocator.freeWriteable(v, 64)

    ctx = dbg.getcontext()
    #ctx['Esp'] = v + 60*0x1000
    #print '%x'%ctx['Esp']
    #l = dbg.setcontext(ctx)
# 0xaa0000

    v = allocator.getWriteable(None, 1)
    res = dbg.write(v, "hi there.")
    print 'wrote %d bytes to %x'% (res, v)

    #address = allocator.getExecutable(v, 4)
    #print '%x'% address
    #print utils.hexdump(v, offset=0x1012475)
    dbg.detach()

