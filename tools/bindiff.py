import array

import ptypes
from ptypes import utils

def blockreader(file, blocksize):
    while True:
        res = file.read(blocksize)
        for x in res:
            yield x

        if not res:
            raise StopIteration

def infiniterange(start, stop=None, step=1):
    assert step != 0

    if step > 0:
        test = lambda x: x < stop
    elif step < 0:
        test = lambda x: x > stop

    if stop is None:
        test = lambda x: True
    res = start
    while test(res):
        yield res
        res += step
    return

###############
class STATE(object): pass
class FSM(object):
    #rules = [((CurrentState, IfTrue), (NextState, Action)) ]
    rules = None
    state = None

    # [1] get (currentState, test)
    # [2] get (currentState, None)

    def getExactState(self, input):
        res = [(c,n) for c,n in self.rules if c[1]]
        for c,n in res:
            if c[0] is self.state and c[1](self,input):
                return n
        return None

    def getAnyState(self, input):
        res = [(c,n) for c,n in self.rules if not c[1]]
        for c,n in res:
            if c[0] is self.state and c[1] is None:
                return n
        return None

    def getErrorState(self, input):
        raise LookupError('Unknown state from %s with %s'% (self.state, repr(input)))

    def consume(self, input):
        action = None

        res = self.getExactState(input)
        if not res:
            res = self.getAnyState(input)
        if not res:
            res = (self.getErrorState(input), None)

        nextState, action = res

        self.state = nextState
        if action:
            return action(self, input)
        return None

### state machine shit
class Same(STATE): pass
class Different(STATE): pass

def issame(self, input):
    return input[0] == input[1]
def isdiff(self, input):
    return input[0] != input[1]

class diff_machine(FSM):
    rules = [
        ((Same, isdiff), (Different, lambda s,n: s.enter(n))),
        ((Same, issame), (Same, None)),
        ((Different, isdiff), (Different, lambda s,n: s.add(n))),
        ((Different, issame), (Same, lambda s,n: s.exit(n)))
    ]
    length = address = 0
    startaddress = 0

    def enter(self, input):
        self.length = 0
        self.startaddress = self.address
        self.add(input)

    def exit(self, input):
        return self.startaddress, self.length

    def add(self, input):
        l = len(input[0])
        self.length += l

    def getErrorState(self, input):
        a,b = input
        return [Different, Same][ int(a==b) ]

    def consume(self, input):
        res = super(diff_machine, self).consume(input)
        self.address += len(input[0])
        return res

############# we start here....
def getDifferences(inputa, inputb):
    blah = diff_machine()
    for x in zip(inputa, inputb):
        res = blah.consume(x)
        if res:
            yield res
    return

def help(*args):
    try:
        first, = args
    except ValueError:
        first = 'bindiff.run'
    print 'Usage: %s [-generate template.%%s.diff] file1 file2'% first
    print """
    Will do a byte-for-byte compare between file1 and file2, and then output
    the results. If -generate is specified, the application will generate
    a version of the original file for each independant modification
    """

def do_diff_friendly( (a,inputa), (b,inputb) ):
    for o,l in getDifferences(a, b):

        print '\nDifference located at %08x:%08x'% (o, o+l)
        o = (o) & ~0xf
        l = (l+0xf) & ~0xf

        # collect the actual file data
        ## it sucks that we're double-reading...oh well
        inputa.seek(o)
        inputb.seek(o)
        left = inputa.read(l)
        right = inputb.read(l)

        left, right = utils.hexdump(left, o), utils.hexdump(right, o)

        res = [ left, right ]
        res = [ s.split('\n') for s in res ]
        rows = [ ' | '.join(x) for x in zip(*res) ]
        print '\n'.join(rows)

def do_diff_generate((a,inputa),(b,inputb), template='%s.diff'):
    assert '%s' in template, "Filename template `%s' needs a %%s for modification range"% template

    inputa.seek(0); inputb.seek(0)
    original = inputa.read()
    newer = array.array('c', inputb.read())
    inputa.seek(0); inputb.seek(0)

    count = 0
    for o,l in getDifferences(a, b):
        left,right = o,o+l
        buffer = array.array('c', original)
        buffer[left:right] = newer[left:right]

        filepiece = '%x-%x'% (left,right)
        out = file( template% filepiece, 'wb' )
        out.write( buffer.tostring() )
        out.close()
        count += 1

    print 'Outputted %d files'% count

def run(*args):
    """Run the bindiff.py commandline"""
    generate_differences = None
    args = list(args)
    try:
        if '-generate' in args:
            v = args.index('-generate')
            generate_differences = args[v+1]
            del(args[v:v+2])

    except IndexError:
        help(*args)
        return

    try:
        inputa, inputb = args

    except ValueError:
        help(*args)
        return

    inputa, inputb = file(inputa, 'rb'), file(inputb, 'rb')
    a,b = (blockreader(inputa, 512), blockreader(inputb, 512))

    if generate_differences:
        do_diff_generate( (a,inputa), (b,inputb), generate_differences )
    do_diff_friendly( (a,inputa), (b,inputb) )
    return

if __name__ == '__main__':
    import sys
    run(*sys.argv[1:])
