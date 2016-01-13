from ptypes import ptype
class stackable:
    def nextlayer(self):
        '''returns a tuple of (type,remaining)'''
        raise NotImplementedError

class terminal(stackable):
    def nextlayer(self):
        return None,None
