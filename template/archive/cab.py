import ptypes
from ptypes import *
from ptypes.pint import uint8_t,uint16_t,uint32_t
from ptypes.pint import sint8_t,sint16_t,sint32_t

pint.setbyteorder(pint.littleendian)
pbinary.setbyteorder(pbinary.littleendian)

class CFDATA(pstruct.type):
    _fields_ = [
        (uint32_t, 'csum'),
        (uint16_t, 'cbData'),
        (uint16_t, 'cbUncomp'),
        (lambda s: s.getparent(CFHEADER).reserve_data(), 'abReserve'),
        (lambda s: dyn.block(s['cbData'].li.int()), 'ab'),
    ]

class CFFOLDER(pstruct.type):
    class __typeCompress(pint.enum, uint16_t):
        _values_ = [
            (0xf, 'MASK_TYPE'),
            (0x0, 'TYPE_NONE'),
            (0x1, 'TYPE_MSZIP'),
            (0x2, 'TYPE_QUANTUM'),
            (0x3, 'TYPE_LZX'),
        ]
    _fields_ = [
#        (uint32_t, 'coffCabStart'),
        (lambda s: dyn.pointer(lambda x:dyn.array(CFDATA, s['cCFData'].li.int())), 'coffCabStart'),
        (uint16_t, 'cCFData'),
        (__typeCompress, 'typeCompress'),
        (lambda s: s.getparent(File)['header'].reserve_folder(), 'abReserve'),
    ]

class CFFILE(pstruct.type):
    class __attribs(pbinary.struct):
        _fields_ = [
            (1, 'NAME_IS_UTF'),
            (1, 'EXEC'),
            (1, 'ARCH'),
            (2, 'reserved'),
            (1, 'SYSTEM'),
            (1, 'HIDDEN'),
            (1, 'RDONLY'),
            (8, 'unknown'),
        ]

    class __iFolder(pint.enum, uint16_t):
        _values_ = [
            (0xfffd, 'CONTINUED_FROM_PREV'),
            (0xfffe, 'CONTINUED_TO_NEXT'),
            (0xffff, 'CONTINUED_PREV_AND_NEXT'),
        ]

    _fields_ = [
        (uint32_t, 'cbFile'),
#        (uint32_t, 'uoffFolderStart'),
        (lambda s: dyn.pointer( dyn.block(s['cbFile'].li.int()) ), 'uoffFolderStart'),
#        (uint16_t, 'iFolder'),
        (__iFolder, 'iFolder'),
        (uint16_t, 'date'),
        (uint16_t, 'time'),
        (__attribs, 'attribs'),
        (pstr.szstring, 'szName'),
    ]

class CFHEADER(pstruct.type):
    class __flags(pbinary.struct):
        _fields_ = [
            (5, 'unknown'),
            (1, 'RESERVE_PRESENT'),
            (1, 'NEXT_CABINET'),
            (1, 'PREV_CABINET'),
            (8, 'reserved'),
        ]

    def reserve_header(self):
        if self['flags']['RESERVE_PRESENT']:
            s = self['cbCFHeader'].int()
            return dyn.block(s)
        return ptype.undefined
    def reserve_folder(self):
        if self['flags']['RESERVE_PRESENT']:
            s = self['cbCFFolder'].int()
            return dyn.block(s)
        return ptype.undefined
    def reserve_data(self):
        if self['flags']['RESERVE_PRESENT']:
            s = self['cbCFData'].int()
            return dyn.block(s)
        return ptype.undefined

    _fields_ = [
        (dyn.clone(pstr.string, length=4), 'signature'),
        (uint32_t, 'reserved1'),
        (uint32_t, 'cbCabinet'),
        (uint32_t, 'reserved2'),
#        (dyn.pointer(CFFILE), 'coffFiles'),
        (lambda s: dyn.pointer(lambda x: dyn.array(CFFILE,s['cFiles'].li.int())), 'coffFiles'),
        (uint32_t, 'reserved3'),
        (uint8_t, 'versionMinor'),
        (uint8_t, 'versionMajor'),
        (uint16_t, 'cFolders'),
        (uint16_t, 'cFiles'),
        (__flags, 'flags'),
        (uint16_t, 'setID'),
        (uint16_t, 'iCabinet'),

        (lambda s: uint16_t if s['flags'].li['RESERVE_PRESENT'] else pint.uint_t, 'cbCFHeader'),
        (lambda s: uint8_t if s['flags'].li['RESERVE_PRESENT'] else pint.uint_t, 'cbCFFolder'),
        (lambda s: uint8_t if s['flags'].li['RESERVE_PRESENT'] else pint.uint_t, 'cbCFData'),
        (lambda s: s.reserve_header(), 'abReserve'),


        (lambda s: pstr.szstring if s['flags'].li['PREV_CABINET'] else pstr.string, 'szCabinetPrev'),
        (lambda s: pstr.szstring if s['flags'].li['PREV_CABINET'] else pstr.string, 'szDiskPrev'),

        (lambda s: pstr.szstring if s['flags'].li['NEXT_CABINET'] else pstr.string, 'szCabinetNext'),
        (lambda s: pstr.szstring if s['flags'].li['NEXT_CABINET'] else pstr.string, 'szDiskNext'),
    ]

class File(pstruct.type):
    _fields_ = [
        (CFHEADER, 'header'),
        (lambda s: dyn.array(CFFOLDER, s['header'].li['cFolders'].int()), 'folders'),
#        (lambda s: dyn.array(CFFILE, s['header']['cFiles'].int()), 'files'),
#        (lambda s: dyn.block(s['header']['cbCabinet'].int() - s['header'].size()-s['folders'].size()-s['files'].size()), 'data'),
#        (dyn.block(s['header']['cbCabinet'].int() - s['header'].size()-s['folders'].size()-s['files'].size()), 'data'),
    ]

if __name__ == '__main__':
    import sys,ptypes,archive.cab as cab
    ptypes.setsource(ptypes.file('~/shit/test/Windows6.1-KB2705219-x86.cab'))

    a = cab.File()
    a = a.l
    print(a['header']['cbCabinet'].int())
    print(a['header']['cbCabinet'])

    print(a['folders'][0]['typeCompress'].summary())
    print(a['folders'][0]['coffCabStart'].d.l)
    b = a['header']['coffFiles'].d.l

    for x in b:
        print(x['uoffFolderStart'])

    print(b[1])
    print(b[1]['uoffFolderStart'].d.l.hexdump())


    print(a['folders'][0]['typeCompress'])

    print(a['header'])
    print(a['header']['flags'])
    b = a['header']['coffFiles'].d.l
    print(a['header'])
    print(b[-1]['attribs'])
    print(a['header'])
