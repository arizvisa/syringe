import _PyDbgEng
from .. import dispatch,breakpoint

# dispatch tables for different granularities
class event_all(dispatch.system):
    defaultfields = []

    # types of callback results
    ignore = _PyDbgEng.ExecutionStatus.IGNORE_EVENT
    go = _PyDbgEng.ExecutionStatus.GO
    handled = _PyDbgEng.ExecutionStatus.GO_HANDLED
    nothandled = _PyDbgEng.ExecutionStatus.GO_NOT_HANDLED

    # default breakpoints
    userbreak = _PyDbgEng.ExecutionStatus.BREAK
    userignore = go

    # FIXME: would be nice to enable keyword arguments here
    def update(self, interface):
        def make_dict(ev):
            return dict(( (k, getattr(ev,k)) for k in dir(ev) if not k.startswith('__')))

        target = interface.EventCallbacks
        target.Breakpoint = lambda ev: self.dispatch('Breakpoint', ev.Breakpoint, **make_dict(ev))
        target.ChangeDebuggeeState = lambda ev: self.dispatch('ChangeDebuggeeState', ev.Flags, ev.Argument, **make_dict(ev))
        target.ChangeEngineState = lambda ev: self.dispatch('ChangeEngineState', ev.Flags, ev.Argument, **make_dict(ev))
        target.ChangeSymbolState = lambda ev: self.dispatch('ChangeSymbolState', ev.Flags, ev.Argument, **make_dict(ev))
        target.CreateProcess = lambda ev: self.dispatch('CreateProcess', ev.ImageFileHandle, ev.Handle, ev.BaseOffset, ev.ModuleSize, ev.ModuleName, ev.ImageName, ev.CheckSum, ev.TimeDateStamp, ev.InitialThreadHandle, ev.ThreadDataOffset, ev.StartOffset, **make_dict(ev))
        target.CreateThread = lambda ev: self.dispatch('CreateThread', ev.Handle, ev.DataOffset, ev.StartOffset, **make_dict(ev))
        target.Exception = lambda ev: self.dispatch('Exception', ev.IsFirstChance, ev.Code, ev.Flags, ev.Address, ev.Parameters, **make_dict(ev))
        target.ExitProcess = lambda ev: self.dispatch('ExitProcess', ev.ExitCode, **make_dict(ev))
        target.ExitThread = lambda ev: self.dispatch('ExitThread', ev.ExitCode, **make_dict(ev))
        target.LoadModule = lambda ev: self.dispatch('LoadModule', ev.ImageFileHandle, ev.BaseOffset, ev.ModuleSize, ev.ModuleName, ev.ImageName, ev.CheckSum, ev.TimeDateStamp, **make_dict(ev))
        target.SessionStatus = lambda ev: self.dispatch('SessionStatus', ev.Status, **make_dict(ev))
        target.SystemError = lambda ev: self.dispatch('SystemError', ev.Error, ev.Level, **make_dict(ev))
        target.UnloadModule = lambda ev: self.dispatch('UnloadModule', ev.ImageBaseName, ev.BaseOffset, **make_dict(ev))
        return target

    def update(self, interface):
        target = interface.EventCallbacks
        target.Breakpoint = lambda ev: self.dispatch('Breakpoint', ev.Breakpoint)
        target.ChangeDebuggeeState = lambda ev: self.dispatch('ChangeDebuggeeState', ev.Flags, ev.Argument)
#        target.ChangeEngineState = lambda ev: self.dispatch('ChangeEngineState', ev.Flags, ev.Argument)
        target.ChangeSymbolState = lambda ev: self.dispatch('ChangeSymbolState', ev.Flags, ev.Argument)
        target.CreateProcess = lambda ev: self.dispatch('CreateProcess', ev.ImageFileHandle, ev.Handle, ev.BaseOffset, ev.ModuleSize, ev.ModuleName, ev.ImageName, ev.CheckSum, ev.TimeDateStamp, ev.InitialThreadHandle, ev.ThreadDataOffset, ev.StartOffset)
        target.CreateThread = lambda ev: self.dispatch('CreateThread', ev.Handle, ev.DataOffset, ev.StartOffset)
        target.Exception = lambda ev: self.dispatch('Exception', {'Code':ev.Code,'Flags':ev.Flags,'Address':ev.Address,'Parameters':ev.Parameters}, ev.IsFirstChance)
        target.ExitProcess = lambda ev: self.dispatch('ExitProcess', ev.ExitCode)
        target.ExitThread = lambda ev: self.dispatch('ExitThread', ev.ExitCode)
        target.LoadModule = lambda ev: self.dispatch('LoadModule', ev.ImageFileHandle, ev.BaseOffset, ev.ModuleSize, ev.ModuleName, ev.ImageName, ev.CheckSum, ev.TimeDateStamp)
        target.SessionStatus = lambda ev: self.dispatch('SessionStatus', ev.Status)
        target.SystemError = lambda ev: self.dispatch('SystemError', ev.Error, ev.Level)
        target.UnloadModule = lambda ev: self.dispatch('UnloadModule', ev.ImageBaseName, ev.BaseOffset)
        return target

class event_process(event_all):
    defaultfields = [lambda **k: k['process'].host.interface.SystemObjects.GetCurrentProcessSystemId()]
class event_thread(event_all):
    defaultfields = [lambda **k: k['task'].host.interface.SystemObjects.GetCurrentProcessSystemId(), lambda **k: k['task'].host.interface.SystemObjects.GetCurrentThreadSystemId()]

# switching context to a process id
class processid(object):
    def __init__(self, process):
        self.interface = process.host.interface.SystemObjects
        self.pid = process.id

        try:
            self.cpid = self.interface.GetCurrentProcessId()
        except RuntimeError:
            self.cpid = None
        return

    def __enter__(self):
        self.processid = self.interface.GetProcessIdBySystemId(self.pid)
        self.interface.SetCurrentProcessId(self.processid)

    def __exit__(self, type, value, traceback):
        if self.cpid is not None:
            self.interface.SetCurrentProcessId(self.cpid)
        return

    @staticmethod
    def fromhandle(interface, handle):
        SystemObjects = interface.SystemObjects
        sid = SystemObjects.GetProcessIdByHandle(handle)
        SystemObjects.SetCurrentProcessId(sid)
        return SystemObjects.GetCurrentProcessSystemId()

# switching context to a thread id
class threadid(processid):
    def __init__(self, task):
        self.interface = task.host.interface.SystemObjects
        super(threadid, self).__init__(task.process)

        self.tid = task.id
        try:
            self.ctid = self.interface.GetCurrentThreadId()
        except RuntimeError:
            self.ctid = None
        return

    def __enter__(self):
        super(threadid, self).__enter__()
        self.threadid = self.interface.GetThreadIdBySystemId(self.tid)
        self.interface.SetCurrentThreadId(self.threadid)

    def __exit__(self, type, value, traceback):
        super(threadid, self).__exit__(type, value, traceback)
        if self.ctid is not None:
            self.interface.SetCurrentThreadId(self.ctid)

    @staticmethod
    def fromhandle(interface, handle):
        SystemObjects = interface.SystemObjects
        sid = SystemObjects.GetThreadIdByHandle(handle)
        SystemObjects.SetCurrentThreadId(sid)
        return SystemObjects.GetCurrentThreadSystemId()

class manager(breakpoint.manager):
    def __init__(self, task):
        self.task = task
        self.host = task.host
        self.interface = self.host.interface.Control

    def add(self, function, interruption, *args, **kwds):
        assert issubclass(interruption, breakpoint.interrupt)
        brk = interruption(self.task, *args, **kwds)
        id = brk.id
        self[id] = brk,function

    def dispatch(self, breakpoint, **kwds):
        id = breakpoint.Id
        brk,fn = self[id]
        with brk:
            result = fn(breakpoint=brk, scope=self.task)
        return result

    def rm(self, id):
        brk,fn = self[id]
        brk.remove()
        del(self[id])
