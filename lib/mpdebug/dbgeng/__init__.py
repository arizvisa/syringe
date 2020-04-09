import _PyDbgEng
from . import host,breakpoint

def local(handle=0):
    intf = _PyDbgEng.Create()
    return host.dbgeng(intf, handle)

def remoteserver(remote):
    intf = _PyDbgEng.Create()
    handle = intf.ConnectProcessServer(remote)
    return host.dbgeng(intf, handle)

def remote(remote):
#    raise NotImplementedError("I haven't successfully tested this interface with an already running windbg instance")
    intf = _PyDbgEng.Connect(remote)
    return host.dbgeng(intf)   # probably not a dbgeng_host

if __name__ == '__main__':
#    a = remoteserver('tcp:port=57005,server=172.22.22.143')
    a = local()
    a.enum()
