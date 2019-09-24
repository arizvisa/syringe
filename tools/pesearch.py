import os,sys
import pecoff
from ptypes import utils

def traverse_address(address):
    def edges(self, address=address, **kwargs):
        if not isinstance(self, ptypes.ptype.container):
            return
        for item in self.value:
            if item.contains(address):
                yield item
            continue
        return
    return edges

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
    mz.setoffset(imagebase, recurse=True)
    if mz.contains(address):
        result = mz
        for item in mz.traverse(traverse_address(address)):
            x = item.__name__
            print rightjustify('------- %s'%x, 70, '-')
            result = result[int(x) if isinstance(result, ptypes.parray.type) else x]
            print result

    # try sections
    else:
        mz.setoffset(0,recurse=True)
        va = address - imagebase
        s = pe['Sections'].getsectionbyaddress(va)
        offset = va - s['VirtualAddress'].int()
        data = s['PointerToRawData'].d.load().serialize()

        left = offset - 8
        left &= ~0xf
        right = left+0x30

        if left < 0: left = 0
        if right > len(data): right = len(data)

        sectionname = s['Name'].get()
        print rightjustify(' section %s'% sectionname, 76, '-')
        print utils.hexdump(data[left:right], offset=s['VirtualAddress'].int()+offset+imagebase)

    mz.setoffset(0, recurse=True)
    return

from ptypes import ptype
def dumpcontainer(pc, indent=''):
    if isinstance(pc.value, list):
        for p in pc.value:
            a = p.getoffset()
            range ='%x-%x'% (a, a+p.size())
            sym = '%s -> %s'%( p.__name__, p.__class__.__name__)
            r = repr(p.serialize())

            if not isinstance(p.value, list):
                print indent, range, sym, ' | ', r
                continue
            print indent, range, sy
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
        address = x['VirtualAddress'].int() + imagebase
        print x['Name'].str(), hex(address), hex(address + x.getloadedsize())
    mz.setoffset(0,recurse=True)
    return

def dumpversion(filename):
    global mz,pe,imagebase,sections,datadirectory,imports
    opt = pe['OptionalHeader']
    print 'OperatingSystem', float('%d.%d'%(opt['MajorOperatingSystemVersion'].int(), opt['MinorOperatingSystemVersion'].int()))
    print 'ImageVersion', float('%d.%d'%(opt['MajorImageVersion'].int(), opt['MinorImageVersion'].int()))
    print 'SubsystemVersion', float('%d.%d'%(opt['MajorSubsystemVersion'].int(), opt['MinorSubsystemVersion'].int()))
    print opt['Win32VersionValue']

    global root
    rsrc = datadirectory[2]
    root = rsrc['VirtualAddress'].d.l
    global a,b
    a,b = root['Ids']

if __name__ == '__main__':
    import sys, ptypes
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

    source = ptypes.provider.file(filename)
    mz = pecoff.Executable.File(source=source).l
    pe = mz['Next']['Header']
    sections = pe['Sections']
    imagebase = pe['OptionalHeader']['ImageBase'].int()
    datadirectory = pe['DataDirectory']

    if zerobase:
        imagebase = 0

    imports = datadirectory[1]['Address'].d.l

    if len(sys.argv) == 2:
        dumpexecutable(filename)

    elif len(sys.argv) == 3:
        address = int(sys.argv[2], 16)

        try:
            processexecutable(filename, address)
        except KeyError:
            print 'address %x not found in %s'% (address, filename)
        pass
