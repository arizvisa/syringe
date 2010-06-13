import sys
import swf

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

    myfile = swf.File()
    myfile.open(filename)

    for tag in myfile:
        print repr(tag)
