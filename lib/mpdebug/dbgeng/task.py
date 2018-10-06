import logging
import _PyDbgEng
import internalstate
import ndk

class registers_INT32(object):
    pc = property(fget=lambda self: self['eip'])
    sp = property(fget=lambda self: self['esp'])

    def __init__(self, task):
        self.task = task
        self.interface = task.host.interface.Registers

    def __getitem__(self, name):
        with internalstate.threadid(self.task):
            result = self.interface.Registers[name]
            return int(result)
        assert False

    def __setitem__(self, register, value):
        with internalstate.threadid(self.task):
            result = self.interface.Registers[name]
            r = int(result)
            result.Value = value
        return r

    def keys(self):
        INT32 = _PyDbgEng.ValueType.INT32
        registers = self.interface.Registers
        with internalstate.threadid(self.task):
            result = [ x for x in registers.keys() if int(registers[x].Type) == INT32 ]
        return result

    def __repr__(self):
        return repr( dict(((k, self[k]) for k in self.keys())) )

#class dbgeng(default.task.base):
class dbgeng(object):
    event = internalstate.event_thread
    host = None
    process = None
    id,handle = int,int
    manager = internalstate.manager

    def subscribe(self, eventname, fn):
        valid_events = 'Breakpoint ChangeDebuggeeState ChangeEngineState ChangeSymbolState CreateProcess CreateThread Exception ExitProcess ExitThread LoadModule SessionStatus SystemError UnloadModule'
        valid_events = set(valid_events.split(' '))
        assert eventname in valid_events, valid_events
        self.event.register((eventname, self.process.id, self.id), fn)

    def unsubscribe(self, eventname, fn):
        self.event.unregister((eventname, self.process.id, self.id), fn)

    def __OnException(self, Exception, Firstchance, **kwds):
        pid,tid = self.host.current
        if tid != self.id:
            # not for us
            return self.event.userignore

        friendly = '<Code:%x Address:%x Parameters:%s>'%(Exception['Code'],Exception['Address'],repr(Exception['Parameters']))
        if Firstchance:
            logging.info("(%d,%d) exception(handled) raised: %s", self.process.id, self.id, friendly)
            return self.event.userignore

        logging.warning("(%d,%d) exception(unhandled) raised: %s", self.process.id, self.id, friendly)
        return self.event.userbreak

    def __OnSystemError(self, Error, Level):
        # XXX never called?
        logging.fatal("(%d,%d) System Error: Error=%x, Level=%x", self.process.id, self.id, Error, Level)
        return self.event.userbreak

    def __init__(self, process, (tid, handle)):
        self.event = internalstate.event_thread(task=self)

        self.process = process
        self.host = process.host
        self.id = tid
        self.handle = handle

        pid = self.process.id
        self.r = registers_INT32(self)

        # register ourselves with the process
        process.event.register(('CreateProcess',pid), self.event.new_dispatch(('CreateProcess',pid, tid)))
        process.event.register(('ExitProcess',pid), self.event.new_dispatch(('ExitProcess',pid, tid)))
        process.event.register(('CreateThread',pid), self.event.new_dispatch(('CreateThread',pid, tid)))
        process.event.register(('ExitThread',pid), self.event.new_dispatch(('ExitThread',pid, tid)))
        process.event.register(('LoadModule',pid), self.event.new_dispatch(('LoadModule',pid, tid)))
        process.event.register(('UnloadModule',pid), self.event.new_dispatch(('UnloadModule',pid, tid)))

        process.event.register(('Breakpoint',pid), self.event.new_dispatch(('Breakpoint',pid, tid)))
        process.event.register(('Exception',pid), self.event.new_dispatch(('Exception',pid, tid)))
        process.event.register(('SystemError',pid), self.event.new_dispatch(('SystemError',pid, tid)))

        self.manager = internalstate.manager(self)
        self.event.register(('Breakpoint', pid, tid), self.manager.dispatch)
        self.event.register(('Exception', pid, tid), self.__OnException)
        self.event.register(('SystemError', pid, tid), self.__OnSystemError)

    def __teb(self):
        with internalstate.threadid(self):
            address = self.host.interface.SystemObjects.GetCurrentThreadTeb()
        return ndk.TEB(offset=address, source=self.process.memory).l
    teb = property(fget=__teb)

    def __repr__(self):
        return '<dbgeng.Process(%d).Thread(%d, 0x%x)> (pc=%x,sp=%x)'% (self.process.id, self.id, self.handle, self.r.pc, self.r.sp)

    def stop(self):
        logging.warning("I don't think this works remotely")
        return k32.SuspendThread(self.handle)

    def start(self):
        logging.warning("I don't think this works remotely")
        return k32.ResumeThread(self.handle)

    def interrupt(self):
        interface = self.host.interface
        type = _PyDbgEng.InterruptType.ACTIVE
        with internalstate.threadid(self.task):
            interface.Control.SetInterrupt(type)
        return type

    def wait(self, timeout=0xffffffff):
        # XXX: would be nice to only break only on events within our thread
        self.host.wait(timeout)
