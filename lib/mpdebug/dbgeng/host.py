import logging,os
import _PyDbgEng
from . import internalstate,process
import pecoff,ndk

def required(state):
    def ensure_state(method):
        def result(self, *args, **kwds):
            s = self.interface.Control.ExecutionStatus
            if s == state:
                return method(*args, **kwds)
            logging.fatal("attempted to call method %s<%s> while dbgeng in %s", method.__name__, state.name, s.name)
            return self.event.userbreak
        result.func_name = method.func_name
        return result
    return ensure_state

def excluded(state):
    def ensure_state(method):
        def result(self, *args, **kwds):
            s = self.interface.Control.ExecutionStatus
            if s != state:
                return method(*args, **kwds)
            logging.fatal("attempted to call method %s<^%s> while dbgeng in %s", method.__name__, state.name, s.name)
        result.func_name = method.func_name
        return result
    return ensure_state

#class dbgeng(default.host.base):
class dbgeng(object):
    process = dict
    event = internalstate.event_all
    handle = int
    interface = None

    current = property(fget=lambda s: (s.interface.SystemObjects.GetCurrentProcessSystemId(),s.interface.SystemObjects.GetCurrentThreadSystemId()))

    def subscribe(self, eventname, fn):
        valid_events = 'Breakpoint ChangeDebuggeeState ChangeEngineState ChangeSymbolState CreateProcess CreateThread Exception ExitProcess ExitThread LoadModule SessionStatus SystemError UnloadModule'
        valid_events = set(valid_events.split(' '))
        assert eventname in valid_events, valid_events
        self.event.register(eventname, fn)

    def unsubscribe(self, eventname, fn):
        self.event.unregister(eventname, fn)

    def __init__(self, interface, handle=0):
        self.interface = interface
        self.handle = handle
        self.process = {}
        self.event = internalstate.event_all(host=self)
        self.event.update(interface)

    def list(self):
        return self.interface.GetRunningProcessSystemIds(self.handle)

    def enum(self):
        for id in self.list():
            pid,name,descr = self.interface.GetRunningProcessDescription(id, server=self.handle)
            yield pid,name
        return

    def attach(self, id, **kwds):
        # temporary event hooks
        result = {}
        def __Host_OnCreateProcess(imageFileHandle, handle, baseOffset, moduleSize, moduleName, imageName, checkSum, timeDateStamp, initialThreadHandle, threadDataOffset, startOffset, **kwds):
            pid = self.interface.SystemObjects.GetCurrentProcessSystemId()
            tid = internalstate.threadid.fromhandle(self.interface, initialThreadHandle)

            result['pid'] = pid
            result['tid'] = tid
            result['phandle'] = handle
            result['thandle'] = initialThreadHandle
            result['fhandle'] = imageFileHandle
            result['imagename'] = imageName.replace(os.sep, '/')
            result['baseoffset'] = baseOffset
            result['modulesize'] = moduleSize
            return self.event.userbreak

        self.event.register('CreateProcess', __Host_OnCreateProcess)

        # create
        hr = self.interface.AttachProcess(id, flags=kwds.get('flags',_PyDbgEng.AttachUserFlags.DEFAULT), server=self.handle)
        # assert hr == 0

        # be patient
        state = self.wait()
        if state > 0:
            self.event.unregister('CreateProcess', __Host_OnCreateProcess)
            raise OSError("Unable to create process %s %s (0x%x)"% (executable,args,state))

        # caught it
        self.event.unregister('CreateProcess', __Host_OnCreateProcess)

        # create new process object
        pid,tid = result['pid'],result['tid']
        assert pid not in self.process
        logging.info("attached to process pid:tid %d:%d from %s"% (pid, tid, result['imagename']))

        p = process.dbgeng(self, (pid, result['phandle']), (tid, result['thandle']))
        self.process[pid] = p

        def __Host_OnExitProcess(exitcode, **kwds):
            id,tid = result['pid'],result['tid']
            logging.info("terminated process pid %d due to exitcode %d"% (id, exitcode))
            del(self.process[id])
            p.event.unregister(('ExitProcess',id), __Host_OnExitProcess)
            return self.event.userbreak
        p.event.register(('ExitProcess',pid), __Host_OnExitProcess)
        p.addmodule(result['imagename'], result['baseoffset'],result['modulesize'])
        return p

    def create(self, executable, args=None, env=[], directory='', IFS=' ', **kwds):
        # default args if it's undefined
        executable = executable.replace('/', os.sep)    # fix the paths
        if args is None:
            args = executable.split(IFS, 1)
        assert isinstance(args, tuple), 'args must be a tuple'

        # build commandline (for windows)
        assert len(args) > 0

        if args[0] != executable:
            args = (executable,) + args[1:]

        cmd = IFS.join(args)
        env = dict([x.split('=',1) for x in env])

        # temporary event hooks
        result = {}
        def __Host_OnCreateProcess(imageFileHandle, handle, baseOffset, moduleSize, moduleName, imageName, checkSum, timeDateStamp, initialThreadHandle, threadDataOffset, startOffset, **kwds):
            pid = self.interface.SystemObjects.GetCurrentProcessSystemId()
            tid = internalstate.threadid.fromhandle(self.interface, initialThreadHandle)

            result['pid'] = pid
            result['tid'] = tid
            result['phandle'] = handle
            result['thandle'] = initialThreadHandle
            result['fhandle'] = imageFileHandle
            result['imagename'] = imageName.replace(os.sep, '/')
            result['baseoffset'] = baseOffset
            result['modulesize'] = moduleSize
            return self.event.userbreak

        # register hooks..could probably unregister these on destruction, but
        #   dbgeng callbacks exist only as long as this object.
        self.event.register('CreateProcess', __Host_OnCreateProcess)

        # create
        aflags = _PyDbgEng.AttachUserFlags.DEFAULT
        cflags = _PyDbgEng.CreateFlags.ATTACH_PROCESS
        hr = self.interface.CreateProcess(cmd, environmentVariables=env, initialDirectory=directory, server=self.handle, createFlags=cflags, attachFlags=aflags)
        # assert hr == 0

        # be patient
        state = self.wait()
        if state > 0:
            self.event.unregister('CreateProcess', __Host_OnCreateProcess)
            raise OSError("Unable to create process %s %s (0x%x)"% (executable,args,state))

        # caught it
        self.event.unregister('CreateProcess', __Host_OnCreateProcess)

        # instantiate new process
        pid,tid = result['pid'],result['tid']
        assert pid not in self.process
        logging.info("created process pid:tid %d:%d from %s with '%s'"% (pid, tid, result['imagename'], cmd))

        p = process.dbgeng(self, (pid, result['phandle']), (tid, result['thandle']))
        self.process[pid] = p

        def __Host_OnExitProcess(exitcode, **kwds):
            id,tid = result['pid'],result['tid']
            logging.info("terminated process pid %d due to exitcode %d"% (id, exitcode))
            del(self.process[id])
            p.event.unregister(('ExitProcess',id), __Host_OnExitProcess)
            return self.event.userbreak
        p.event.register(('ExitProcess',pid), __Host_OnExitProcess)
        p.addmodule(result['imagename'], result['baseoffset'],result['modulesize'])
        return p

    def wait(self, timeout=0xffffffff):
        result = self.interface.Control.WaitForEvent(timeout)
        if result > 0:
            logging.warning("Control.WaitForEvent returned error code 0x%x", result)
        return result

    def __getitem__(self, processid):
        return self.process[processid]

    def __repr__(self):
        result = repr(self.process.keys())
        return '%s process:%s'%(type(self), result)

if __name__ == '__main__':
    pass
