import sys
import ptypes,vector.swf

def hr(s):
    print('-'*7,)
    print(s)

def help():
    print('Usage:')
    print('%s file.swf'% sys.argv[0])
    sys.exit(0)

import time
class clock(object):
    times = []

    @classmethod
    def start(cls, name=None, now=None):
        name = (name, '#%d'%len(cls.times))[name is None]
        now = (now, time.time())[now is None]
        cls.times.append((name,now))

    @classmethod
    def stop(cls, message='clocked "%s" at %f seconds'):
        stop = time.time()
        n,start = cls.times.pop()
        t = stop - start
        print(message% (n,t))
        return t

if __name__ == '__main__':
    try:
        filename = sys.argv[1]

    except ValueError:
        help()

    print('loading',filename)
    clock.start()
    myfile = vector.swf.File(source=ptypes.file(filename))
    myfile = myfile.l
    clock.stop()

    header = myfile['header']
    data = myfile['data'].d.l
    frameinfo = data['frameinfo']
    tags = data['tags']

    z = myfile

    print('loaded 0x%x tags'%( len(tags) ))

#    for tag in myfile['data']['tags']:
#        print(repr(tag))
