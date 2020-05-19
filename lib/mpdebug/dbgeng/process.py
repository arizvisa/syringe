import logging,os
import _PyDbgEng
from . import internalstate,task
import pecoff,ndk,match

class addressspace(object):
    offset = 0
    def __init__(self, process):
        self.process = process

    def seek(self, offset):
        self.offset = offset

    def consume(self, amount):
        host = self.process.host
        client = host.interface

        with internalstate.processid(self.process):
            return str( client.DataSpaces.Virtual.Read(self.offset, amount) )
        assert False

    def store(self, data):
        host = self.process.host
        client = host.interface
        with internalstate.processid(self.process):
            return client.DataSpaces.Virtual.Write(self.offset, data)
        assert False

    def __getitem__(self, i):
        self.seek(i)
        return self.consume(1)

    def __getslice__(self, i, j):
        if i < j:
            self.seek(i)
            return self.consume( j - i )
        return ''.join(reversed(self.consume(i-j)))

#class dbgeng(default.process.base):
class dbgeng(object):
    event = internalstate.event_process
    task = dict

    def subscribe(self, eventname, fn):
        valid_events = 'Breakpoint ChangeDebuggeeState ChangeEngineState ChangeSymbolState CreateProcess CreateThread Exception ExitProcess ExitThread LoadModule SessionStatus SystemError UnloadModule'
        valid_events = valid_events.split(' ')
        assert eventname in valid_events, valid_events
        self.event.register((eventname, self.id), fn)

    def unsubscribe(self, eventname, fn):
        self.event.unregister((eventname, self.id), fn)

    def __peb(self):
        with internalstate.processid(self):
            address = self.host.interface.SystemObjects.GetCurrentProcessPeb()
        return ndk.PEB(offset=address, source=self.memory).l
    peb = property(fget=__peb)

    def __init__(self, host, pack_pidhandle, pack_tidhandle):
        (id, handle) = pack_pidhandle
        (tid, thandle) = pack_tidhandle

        self.event = internalstate.event_process(process=self)

        self.host = host
        self.id, self.handle = id, handle
        self.task = {}
        self.task[tid] = task.dbgeng(self, (tid, thandle))
        self.memory = addressspace(self)
        self.module = {}
        self.__modulecache = {}

        # FIXME: propagate all events without using this much stupid code
        # register ourselves with the host
        __Host_OnCreateThread =  self.event.new_dispatch('CreateThread')
        __Host_OnExitThread = self.event.new_dispatch('ExitThread')
        __Host_OnLoadModule = self.event.new_dispatch('LoadModule')
        __Host_OnUnloadModule = self.event.new_dispatch('UnloadModule')

        __Host_OnCreateProcess =  self.event.new_dispatch('CreateProcess')
        __Host_OnExitProcess = self.event.new_dispatch('ExitProcess')

        __Host_OnBreakpoint = self.event.new_dispatch('Breakpoint')
        __Host_OnException = self.event.new_dispatch('Exception')
        __Host_OnSystemError = self.event.new_dispatch('SystemError')

        host.event.register('CreateThread', __Host_OnCreateThread)
        host.event.register('ExitThread', __Host_OnExitThread)
        host.event.register('LoadModule', __Host_OnLoadModule)
        host.event.register('UnloadModule', __Host_OnUnloadModule)
        host.event.register('CreateProcess', __Host_OnCreateProcess)
        host.event.register('ExitProcess', __Host_OnExitProcess)

        host.event.register('Breakpoint', __Host_OnBreakpoint)
        host.event.register('Exception', __Host_OnException)
        host.event.register('SystemError', __Host_OnSystemError)

        # events based on scope
        def __Process_OnExitProcess(exitcode, **kwds):
            host.event.unregister('CreateThread', __Host_OnCreateThread)
            host.event.unregister('ExitThread', __Host_OnExitThread)
            host.event.unregister('LoadModule', __Host_OnLoadModule)
            host.event.unregister('UnloadModule', __Host_OnUnloadModule)
            host.event.unregister('CreateProcess', __Host_OnCreateProcess)
            host.event.unregister('ExitProcess', __Host_OnExitProcess)

            host.event.unregister('Breakpoint', __Host_OnBreakpoint)
            host.event.unregister('Exception', __Host_OnException)
            host.event.unregister('SystemError', __Host_OnSystemError)
            return self.event.userignore

        self.event.register(('ExitProcess', id), __Process_OnExitProcess)

        def __OnCreateThread(Handle, DataOffset, StartOffset, **kwds):
            tid = host.interface.SystemObjects.GetCurrentThreadSystemId()
            t = task.dbgeng(self, (tid,Handle))
            self.task[tid] = t
            def __OnExitThread(ExitCode, **kwds):
                t.event.unregister(('ExitThread', id, tid), __OnExitThread)
                del(self.task[tid])
                return self.event.userignore
            t.event.register(('ExitThread', id, tid), __OnExitThread)
            return self.event.userignore

        self.event.register(('CreateThread', id), __OnCreateThread)

        self.event.register(('LoadModule', id), self.__OnLoadModule)
        self.event.register(('UnloadModule', id), self.__OnUnloadModule)

    def __OnLoadModule(self, ImageFileHandle, BaseOffset, ModuleSize, ModuleName, ImageName, CheckSum, TimeDateStamp, **kwds):
        logging.info('(pid:%d) loaded module %x:+%x %s'%(self.id, BaseOffset, ModuleSize, ImageName))
        name = ImageName.replace(os.sep, '/')   # XXX: makes more sense
        self.addmodule(name, BaseOffset, ModuleSize)
        return self.event.userignore

    def __OnUnloadModule(self, ImageName, BaseOffset, **kwds):
        name = ImageName
        if name is not None:
            name = ImageName.replace(os.sep, '/')   # XXX
            logging.info('(pid:%d) unloaded module %x %s'%(self.id, BaseOffset, ImageName))
            del(self.module[name])
        else:
            logging.warning('(pid:%d) unloaded unknown module %x %s'%(self.id, BaseOffset, ImageName))
        return self.event.userignore

    def addmodule(self, name, address, size):
        self.__modulecache[name] = address,size
        self.module[name] = pecoff.Executable.File(source=self.memory, offset=address)

    def getmodulebyaddress(self, address):
        cache = self.__modulecache
        for name, pos in cache.items():
            if match.block(pos) == address:
                return name
            continue
        raise KeyError(address)

    def terminate(self):
        with internalstate.processid(self):
            return self.host.interface.TerminateCurrentProcess()

    def detach(self):
        with internalstate.processid(self):
            return self.host.interface.DetachCurrentProcess()

    def wait(self, timeout=0xffffffff):
        # XXX: would be nice to only break only on events within our process
        self.host.wait(timeout)

    def __repr__(self):
        return '<dbgeng.Process(%d, %x)> -> task:%s'%(self.id, self.handle, repr(self.task.keys()))

    def __getitem__(self, taskid):
        return self.task[taskid]

    def keys(self):
        return self.task.keys()

    def __iter__(self):
        return iter(self.task.values())
