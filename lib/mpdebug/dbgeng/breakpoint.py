from .. import breakpoint
import logging

class cc(breakpoint.interrupt):
    id = property(fget=lambda s: s.value.Id)
    offset = property(fget=lambda s: s.value.Offset)
    def __init__(self, task, offset, **kwds):
        interface = task.host.interface
        self.task = task

        value = interface.Control.AddBreakpoint()
        value.Offset = offset

        for k,v in kwds:
            setattr(self.value, k, v)

        self.value = value
        self.interface = interface
        value.Enable()

    def enable(self):
        self.value.Enable()
    def disable(self):
        self.value.Disable()

    def remove(self):  # XXX: such a good name :(
        self.value.Remove()

    def __enter__(self):
        logging.debug('Entering breakpoint %d at %x', self.id, self.value.Offset)

    def __exit__(self, type, value, trace):
        logging.debug('Leaving breakpoint %d at %x', self.id, self.value.Offset)

    def __repr__(self):
        pid,tid = self.task.process.id, self.task.id
        return '<dbgeng.Process(%d).Thread(%d).Breakpoint<#%d>(address=0x%x)>'%(pid, tid, self.id, self.offset)

# with interruption(offset)
#     callback(*args, **kwds)

