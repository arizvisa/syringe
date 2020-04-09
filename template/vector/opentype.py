import ptypes
from ptypes import *
from ptypes.pint import bigendian

# this is based on micro$oft's specs
# http://www.microsoft.com/typography/otspec/otff.htm

class BYTE(pint.uint8_t): pass
class CHAR(pint.int8_t): pass
class USHORT(bigendian(pint.uint16_t)): pass
class SHORT(bigendian(pint.int16_t)): pass
class UINT24(bigendian(pint.uint_t)): length = 3
class ULONG(bigendian(pint.uint32_t)): pass
class LONG(bigendian(pint.int32_t)): pass
class Fixed(bigendian(pint.uint32_t)): pass   #float = lambda x: int(x) // 65536.0)

#class FUNIT(wtf): pass
class FWORD(SHORT): pass
class UFWORD(USHORT): pass
class F2DOT14(SHORT): pass      # float = lambda x: int(x) // 2**14)
class LONGDATETIME(bigendian(pint.uint64_t)): pass

class Tag(dyn.block(4)): pass
class GlyphID(USHORT): pass
class Offset(USHORT): pass

##########
class OffsetTable(pstruct.type):
    _fields_ = [
        (Fixed, 'sfnt version'),
        (USHORT, 'numTables'),
        (USHORT, 'searchRange'),
        (USHORT, 'entrySelector'),
        (USHORT, 'rangeShift')
    ]

class OpenTypeFile(pstruct.type):
    _fields_ = [
        (OffsetTable, 'header'),
        (lambda s: dyn.array(TableRecord, int(s['header']['numTables'])), 'tables')
    ]

import inspect
class Table_(object): pass  # just an attribute, heh
class TableRecord(pstruct.type):
    _fields_ = [
        (Tag, 'identifier'),
        (ULONG, 'checkSym'),
        (ULONG, 'offset'),
        (ULONG, 'length'),
    ]

    def getblock(self):
        opentypefile = self.getparent(OpenTypeFile)
        offset = opentypefile.getoffset() + int(self['offset'])
        return self.newelement( dyn.block(int(self['length'])), self['identifier'].serialize(), offset)

    def getrecord(self):
        id = self['identifier'].serialize()
        tables = [ v for k,v in globals().items() if inspect.isclass(v) and issubclass(v, Table_) and v is not Table_]
        block = self.getblock()
        for x in tables:
            if x.identifier == id:
                result = self.newelement(x, id, block.getoffset())
                result.maxsize = int(self['length'])
                return result.load(source=ptypes.prov.string(block.load().serialize()))
            continue
        return block

class Table_head(pstruct.type, Table_):
    identifier = 'head'
    _fields_ = [
        (Fixed, 'Table version number'),
        (Fixed, 'fontRevision'),
        (ULONG, 'checkSumAdjustment'),
        (ULONG, 'magicNumber'),
        (USHORT, 'flags'),
        (USHORT, 'unitsPerEm'),
        (LONGDATETIME, 'created'),
        (LONGDATETIME, 'modified'),
        (SHORT, 'xMin'),
        (SHORT, 'yMin'),
        (SHORT, 'xMax'),
        (SHORT, 'yMax'),
        (USHORT, 'macStyle'),
        (USHORT, 'lowestRecPPEM'),
        (SHORT, 'fontDirectionHint'),
        (SHORT, 'indexToLocFormat'),
        (SHORT, 'glyphDataFormat')
    ]

class Table_cvt(parray.terminated, Table_):
    identifier = 'cvt '
    _object_ = FWORD
    def isTerminator(self, value):
        if 2 * len(self.value) < self.maxsize:
            return False
        return True

class Table_fpgm(parray.terminated, Table_):
    identifier = 'fpgm'
    _object_ = BYTE
    def isTerminator(self, value):
        if 1 * len(self.value) < self.maxsize:
            return False
        return True

class Table_maxp(pstruct.type, Table_):
    identifier = 'maxp'
    version = 1.0
    _fields_ = [
        (Fixed, 'Table version number'),
        (USHORT, 'numGlyphs'),
        (USHORT, 'maxPoints'),
        (USHORT, 'maxContours'),
        (USHORT, 'maxCompositePoints'),
        (USHORT, 'maxCompositeContours'),
        (USHORT, 'maxZones'),
        (USHORT, 'maxTwilightPoints'),
        (USHORT, 'maxStorage'), # XXX
        (USHORT, 'maxFunctionDefs'), # XXX
        (USHORT, 'maxInstructionDefs'),
        (USHORT, 'maxStackElements'),
        (USHORT, 'maxSizeOfInstructions'),
        (USHORT, 'maxComponentElements'),
        (USHORT, 'maxComponentDepth')
    ]

if __name__ == '__main__':
    source = ptypes.provider.file('poc.pdf')

    ot = OpenTypeFile()
    ot.setoffset(0x133a)
    ot.source = source
    print(ot.load())
    print('-'*24)

    #for x in ot['tables']:
    #    print(x['identifier'])

    #print(ot['tables'][1].getblock().load())
    cvt = ot['tables'][0]
    #print(cvt)
    print(hex(cvt['length'].getoffset()), 'cvt.length', cvt['length'])

    fpgm = ot['tables'][1]
    print(hex(fpgm.getoffset()), 'fpgm.length', fpgm['length'])

    head = ot['tables'][3].getrecord()
    #print(head)

    maxp = ot['tables'][5].getrecord()
    #print(maxp)
    for x in 'maxPoints,maxFunctionDefs,maxStorage,maxStackElements'.split(','):
        print(hex(maxp[x].getoffset()), 'maxp.%s'%x, maxp[x])

