class base(object):
    proc = dict
    pagesize = 2**12
    arch = None
    # and other host-specific attributes

    def __init__(self, **kwds):
        pass

    def __getitem__(self, processid):
        return self.proc[processid]

    def list(self):
        pass

    def create(self, executable, args, env=[], directory='.', **kwds):
        pass

    def attach(self, id):
        pass

    def detach(self, id):
        pass

    def terminate(self, id):
        pass

#######
