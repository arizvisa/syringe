class addressspace(object):
    offset = 0
    def __init__(self, process):
        self.process = process

    def seek(self, offset):
        self.offset = offset

    def consume(self, amount):
        pass

    def store(self, data):
        pass

class base(object):
    task = dict     # each thread of execution, heh
    breakpoint = breakpointmanager
    module = dict
    memory = AddressSpace

    def __getitem__(self, taskid):
        return self.task[taskid]

    def stop(self):
        '''attempt to stop execution of process'''
        pass

    def start(self):
        ''' resume all task '''
        pass

    def terminate(self, **kwds):
        pass

    def __repr__(self):
        return '%s task:%s'%(type(self), repr(self.task))

