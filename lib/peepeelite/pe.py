from ptypes import *
from structs import *

class wordTable(pArray):
    object = '<H'

class dwordTable(pArray):
    object = '<L'
        
# XXX: this is written with the intention of trusting the
#      executable it's parsing
class PE(dict):
    file = None

    def open(self, filename):
        '''open filename'''
        self.file = file(filename, 'rb')

    def bind(self, f):
        '''bind object to an already existing file obj'''
        self.file = f

    def read(self):
        '''pre-read all of our shit pefile styleee'''
        self.readMZ()
        self.readPE()
        self.readExports()
        self.readImports()

    def readMZ(self):
        self.file.seek(0)
        mz = IMAGE_DOS_HEADER()
        mz.deserialize( self.file.read(mz.size()) )
        self['mz'] = mz

    def readPE(self):
        file = self.file
        file.seek( self['mz']['e_lfanew'] )

        pe_file = IMAGE_FILE_HEADER()
        pe_file.deserialize( file.read(pe_file.size()) )
        self['file'] = pe_file

        pe_opt = IMAGE_OPTIONAL_HEADER()
        pe_opt.deserialize( file.read(pe_opt.size()) )
        self['opt'] = pe_opt
    
        directory = []
        for i in range(16):
            res = IMAGE_DATA_DIRECTORY()
            res.deserialize( file.read(res.size()) )
            directory.append(res)
        self['directory'] = directory

        section = []
        for i in range(pe_file['NumberOfSections']):
            res = IMAGE_SECTION_HEADER()
            res.deserialize( file.read(res.size()) )
            section.append(res)
        self['section'] = section

    ## we're totally ignoring oo conventions, and interacting 
    ## with sections via these PE methods
    def getSectionByFunction(self, func):
        '''returns the section matching the constraints determined by func'''
        section = self['section']

        sect = [x for x in section if func(x)]
        assert len(sect) <= 1, "Found >1 section [%s]"% sect

        if sect:
            sect, = sect
            return sect

        raise ValueError, "Unable to find matching PE section"

    def getSectionByRVA(self, va):
        sections = self['section']
        isInside = lambda sect: va >= sect['VirtualAddress'] and va < sect['VirtualAddress']+sect['VirtualSize']
        return self.getSectionByFunction(isInside)

    def getSectionByVA(self, va, **kwds):
        imagebase = kwds.get("ImageBase", self["opt"]["ImageBase"])
        assert va - imagebase > 0
        return self.getSectionByRVA( va - imagebase )

    def getSectionByOffset(self, offset):
        isInside = lambda sect: offset >= sect['PointerToRawData'] and offset < sect['PointerToRawData']+sect['VirtualSize']
        return self.getSectionByFunction(isInside)

    def getOffsetByRVA(self, va):
        section = self.getSectionByRVA(va)
        delta = va - section['VirtualAddress']
        return section['PointerToRawData'] + delta

    def getOffsetByVA(self, va, **kwds):
        imagebase = kwds.get("ImageBase", self["opt"]["ImageBase"])
        assert va - imagebase > 0
        return self.getOffsetByRVA( va - imagebase )

    def getOffsetByOffset(self, ofs):
        self.getSectionByOffset(ofs)
        return ofs
    # i thought that would've been funny. it wasn't.

    def getRVAByOffset(self, offset):
        sect = self.getSectionByOffset(offset)
        delta = offset - sect['PointerToRawData']
        return sect['VirtualAddress'] + delta

    def getVAByOffset(self, offset, **kwds):
        imagebase = kwds.get("ImageBase", self["opt"]["ImageBase"])
        return imagebase + self.getRVAByOffset(offset)

    def getVAByRVA(self, va, **kwds):   #heh
        imagebase = kwds.get("ImageBase", self["opt"]["ImageBase"])
        return imagebase + va

    def getRVAByVA(self, va, **kwds):
        imagebase = kwds.get("ImageBase", self["opt"]["ImageBase"])
        return va - imagebase

    def getStringByOffset(self, offset, buflen=0x10):
        self.file.seek(offset)
        res = ''
        while '\x00' not in res:
            res += self.file.read(buflen)
        res = res[ : res.index('\x00') ]
        self.file.seek(offset + len(res))
        return res

    def getStringByRVA(self, va):
        return self.getStringByOffset( self.getOffsetByRVA(va) )

    def __readTable(self, offset, object="<L"):
        f = self.file
        f.seek(offset)

        res = []
        while True:
            size = struct.calcsize(object)
            val, = struct.unpack(object, f.read(size))
            if val == 0:
                break
            res.append(val)
        return res

    def readExports(self):
        '''read EXPORTs directory from executable'''
        EXPORT = 0

        d = self['directory'][EXPORT]
        if d['VirtualAddress'] == 0:
            return
            
        ofs = self.getOffsetByRVA(d['VirtualAddress'])
        self.file.seek(ofs)

        res = IMAGE_EXPORT_DIRECTORY()
        res.deserialize( self.file.read(res.size()) )
        self['exports'] = res

    def readImports(self):
        '''read IMPORTs directory from executable'''
        IMPORT = 1

        d = self['directory'][IMPORT]
        if d['VirtualAddress'] == 0:
            self['imports'] = []
            return

        ofs = self.getOffsetByRVA(d['VirtualAddress'])

        f = self.file
        f.seek(ofs)
        # data = f.read(d['Size'])  # we're not going to trust the size specifier
        imports = []
        while True:
            res = IMAGE_IMPORT_DIRECTORY_ENTRY()
            res.deserialize( f.read(res.size()) )
            if res.serialize().count('\x00') == res.size():
                break
            imports.append(res)

        self['imports'] = dict([(self.getStringByRVA(res['Name']), res) for res in imports])

    def getExports(self):
        '''get a list of (name, address) containing all exported symbols'''
        res = self['exports']
        f = self.file

        # function addrs
        offset = self.getOffsetByRVA(res['AddressOfFunctions'])
        f.seek(offset)
        
        funcTable = dwordTable()
        funcTable.length = res['NumberOfFunctions']
        funcTable.deserialize( f.read(funcTable.size()) )

        # function names
        offset = self.getOffsetByRVA(res['AddressOfNames'])
        f.seek(offset)
        
        nameTable = dwordTable()
        nameTable.length = res['NumberOfNames']
        nameTable.deserialize( f.read(nameTable.size()) )

        # function ordinals
        offset = self.getOffsetByRVA(res['AddressOfNameOrdinals'])
        f.seek(offset)

        ordTable = wordTable()
        ordTable.length = res['NumberOfNames']
        ordTable.deserialize( f.read(ordTable.size()) )

        return [(self.getStringByRVA(name),funcTable[ordTable[i] - res['Base'] + 1]) for i,name in zip(range(len(nameTable)), nameTable)]

    def getImports(self, module):
        '''
        given a modulename, return a list of tuple(name, address, hint)
        containing all exported symbols
        '''
        res = self['imports'][module]
        f = self.file

        def resolveImport(value):
            flag = value & 0x80000000
            value = value & 0x7fffffff
            if flag:
                return "#%d"% value

            offset = self.getOffsetByRVA(value)
            f.seek(offset)

            object = '<H'
            val = f.read( struct.calcsize(object) )
            hint, = struct.unpack(object, val)

            return (hint, self.getStringByOffset(offset + struct.calcsize(object)) )

        # names
        int = self.__readTable( self.getOffsetByRVA(res['INT']) )
        iat = res['IAT']

        names = [resolveImport(n) for n in int]
        return [(name, iat + index*4, hint) for index,(hint,name) in zip(range(len(names)), names)]
        
## how _not_ to name a method. yes, i actually caught myself typing this trying
## to come up w/ a name...
# def cvt_rva2ofs(self):
#     pass

if __name__ == '__main__':
    input = PE()
    input.open("../msvcrt.dll")
    input.readMZ()
    input.readPE()
    input.readExports()
    input.readImports()

    self = input
    f = self.file
    EXPORT = 0
    IMPORT = 1
    RESOURCE = 2

    ### imports
    print self['imports']
    for a,b,c in self.getImports('KERNEL32.dll'):
        print '%08x> %s [%x]'% (b, a, c)

    ### exports
    print self['exports']
    for a,b in self.getExports():
        print '%08x> %s'% (b + input['opt']['ImageBase'], a)

    ### resources
    # j/k
