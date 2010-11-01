import sys
import ptypes,swf

def hr(s):
    print '-'*7,
    print s

def help():
    print 'Usage:'
    print '%s file.swf'% sys.argv[0]
    sys.exit(0)

if __name__ == '__main__':
    try:
        filename = sys.argv[1]

    except ValueError:
        help()

    print 'loading',filename
    myfile = swf.File(source=ptypes.file(filename))
    myfile = myfile.l

    for tag in myfile:
        print tag
        print repr(tag)
