class state(dict):
    # represents the processor's state
    process = None
    pc = property(fget=lambda self: None)
    sp = property(fget=lambda self: None)
#    fp = property(fget=lambda self: None)

class base(object):
    # this represents the actions that can be applied to a job that is scheduled to the processor
    host = None
    r = state
    id = int

    def start(self):
        pass

    def stop(self):
        pass

    def interrupt(self):
        ''' interrupt execution of this thread '''
        pass

