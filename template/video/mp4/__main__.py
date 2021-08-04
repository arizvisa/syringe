import sys, ptypes, video.mp4
from ptypes import *
from video.mp4 import *

if __name__ == '__main__':
    filename = sys.argv[1]
    ptypes.setsource(ptypes.provider.file(filename, 'rb'))

    z = video.mp4.File()
    z = z.l

    print(z)
