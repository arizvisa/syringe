'''
generic functions for use when searching through a list of objects for some specific type
'''

class base(object):
    def __init__(self, *args, **kwds):
        pass

    def compare(self, value):
        return False

    def __cmp__(self, value):
        return (0, -1)[ not bool(self.compare(value)) ]

import re
class regex(base):
    '''Given a regular expression, return an object that when compared to a matching string will return equivalency'''
    regex = None
    def __init__(self, regularexpression, flags=re.I):
        self.regex = re.compile(regularexpression, flags=flags)

    def compare(self, string, flags=re.I):
        if type(string) is not str:  # if compared to against something not a string
            return False
        return re.match(self.regex, string) is not None

class block(base):
    def __init__(self, (offset, size)):
        self.left,self.right = offset,offset+size

    def compare(self, integer):
        return (integer >= self.left) and (integer < self.right)

if __name__ == '__main__':
    import match

    print 'hiihello' == match.regex('.*hello$')

