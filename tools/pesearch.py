import os,sys
import pecoff
from ptypes import utils

def rightjustify(string, size, space=' '):
    # i don't know if python has support for right justification with character
    #  filling. their fmtstring doesn't seem to..

    diff = size - len(string)
    if diff > 0:
        string = space*diff + string
    return string

def processexecutable(filename, address):
    # globals for interpretive use
    global mz,pe,imagebase,sections,datadirectory

    print 'Query: %x\n'% address

    print 'Module: %s'% os.path.basename(filename)
    print 'ImageBase: %x'% imagebase

    # try exe header first
    try:
        mz.setoffset(imagebase,recurse=True)
        result = mz
        for x in reversed(mz.at(address)):
            print rightjustify(' ------- %s'%x, 70, '-')
            result = result[x]
            print result
        pass

    # try sections
    except ValueError:
        mz.setoffset(0,recurse=True)
        va = address-imagebase
        s = pe['Sections'].getsectionbyaddress(va)
        offset = va - int(s['VirtualAddress'])
        data = s.get().load().serialize()

        left = offset - 8
        left &= ~0xf
        right = left+0x30

        if left < 0: left = 0
        if right > len(data): right = len(data)

        sectionname = s['Name'].get()
        print rightjustify(' section %s'% sectionname, 76, '-')
        print utils.hexdump(data[left:right], offset=int(s['VirtualAddress'])+offset+imagebase)

    mz.setoffset(0, recurse=True)
    return

from ptypes import ptype
def dumpcontainer(pc, indent=''):
    if type(pc.value) is list:
        for p in pc.value:
            a = p.getoffset()
            range ='%x-%x'% (a, a+p.size())
            sym = '%s -> %s'%( p.__name__, p.__class__.__name__)
            r = repr(p.serialize())

            if type(p.value) is not list:
                print indent, range, sym, ' | ', r
                continue
            print indent, range, sym
            dumpcontainer(p, indent+' ')
        pass
    return

def dumpexecutable(filename):
    # globals for interpretive use
    global mz,pe,imagebase,sections,datadirectory,imports

    print 'Module: %s'% os.path.basename(filename)
    print 'ImageBase: %x'% imagebase
    print 'Imports: %s'% ', '.join([x['Name'].d.l.str() for x in imports.l[:-1]])

    mz.setoffset(imagebase,recurse=True)
    print pe
    for x in sections:
        name = x['Name'].str()
        address = int(x['VirtualAddress']) + imagebase
        print x['Name'].str(), hex(address), hex(address + x.getloadedsize())
    mz.setoffset(0,recurse=True)
    return

def dumpversion(filename):
    global mz,pe,imagebase,sections,datadirectory,imports
    opt = pe['OptionalHeader']
    print 'OperatingSystem', float('%d.%d'%(opt['MajorOperatingSystemVersion'].num(), opt['MinorOperatingSystemVersion'].num()))
    print 'ImageVersion', float('%d.%d'%(opt['MajorImageVersion'].num(), opt['MinorImageVersion'].num()))
    print 'SubsystemVersion', float('%d.%d'%(opt['MajorSubsystemVersion'].num(), opt['MinorSubsystemVersion'].num()))
    print opt['Win32VersionValue']

    global root
    rsrc = pe['OptionalHeader']['DataDirectory'][2]
    root = rsrc['VirtualAddress'].d.l
    global a,b
    a,b = root['Ids']

if __name__ == '__main__':
    import sys
    zerobase = False
    if '-z' in sys.argv:
        i = sys.argv.index('-z')
        sys.argv.pop(i)
        zerobase = True

    try:
        filename = sys.argv[1]

    except:
        print 'Usage: %s [-z] filename [hexaddress]'% sys.argv[0]
        sys.exit(0)

    mz = pecoff.Executable.open(filename)
    pe = mz['Pe']
    sections = pe['Sections']
    imagebase = int(pe['OptionalHeader']['ImageBase'])
    datadirectory = pe['OptionalHeader']['DataDirectory']

    if zerobase:
        imagebase = 0

    exports = datadirectory[0].get()
    imports = datadirectory[1].get()
    resources = datadirectory[2].get()

    if len(sys.argv) == 2:
        dumpexecutable(filename)

    elif len(sys.argv) == 3:
        address = int(sys.argv[2], 16)

        try:
            processexecutable(filename, address)
        except KeyError:
            print 'address %x not found in %s'% (address, filename)
        pass
