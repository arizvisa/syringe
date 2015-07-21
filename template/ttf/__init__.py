import logging,ptypes
from ptypes import *
ptypes.setbyteorder( pint.config.byteorder.bigendian )

### base types
class uint0(pint.uint_t): pass
class int0(pint.int_t): pass
class uint8(pint.uint8_t): pass
class int8(pint.int8_t): pass
class uint16(pint.uint16_t): pass
class int16(pint.int16_t): pass
class uint32(pint.uint32_t): pass
class int32(pint.int32_t): pass

# floating based
class shortFrac(pint.int16_t): pass
class Fixed(pint.int32_t): pass

class FWord(pint.int16_t): pass
class uFWord(pint.uint16_t): pass

class F2Dot14(pint.int16_t): pass
class longDateTime(pint.uint32_t): pass     # XXX

### tables
class Table(ptype.definition):
    cache = {}
    # XXX: perhaps implement way to calculate checksum from a table

@Table.define
class cmap(pstruct.type):
    type = 'cmap'
    class entry(pstruct.type):
        _fields_ = [
            (uint16, 'platform-id'),
            (uint16, 'encoding-id'),
            (lambda s: dyn.rpointer(cmap.subtable, s.getparent(cmap)), 'offset'),
        ]
    def __data(self):
        sz = sum(x.li.size() for x in (s['version'],s['number'],s['entry']))
        return dyn.block(self.blocksize() - sz)

    _fields_ = [
        (uint16, 'version'),
        (uint16, 'number'),
        (lambda s: dyn.array(cmap.entry, s['number'].li.int()), 'entry'),
        (__data, 'data'),
    ]
    class subtable(pstruct.type):
        _fields_ = [
            (uint16, 'format'),
            (uint16, 'length'),
            (uint16, 'version'),
            (lambda s: cmap.table.get(s['format'].li.int(), length=s['length'].li.int()-6), 'data'),
        ]
    class table(ptype.definition):
        cache = {}

@cmap.table.define
class cmap_format_0(pstruct.type):
    type = 0
    _fields_ = [(dyn.array(uint8,0x100),'glyphIdArray')]
@cmap.table.define
class cmap_format_2(pstruct.type):
    type = 2
    class subHeader(pstruct.type):
        _fields_ = [
            (uint16, 'firstCode'),
            (uint16, 'entryCount'),
            (int16, 'idDelta'),
            (uint16, 'idRangeOffset'),
        ]
    _fields_ = [
        (dyn.array(uint16,0x100),'subHeaderKeys'),
        # FIXME: not sure how the variable-length-arrays work here...
    ]
@cmap.table.define
class cmap_format_4(pstruct.type):
    type = 4
    _fields_ = [
        (uint16, 'segCountX2'),
        (uint16, 'searchRange'),
        (uint16, 'entrySelector'),
        (uint16, 'rangeShift'),
        (lambda s: dyn.array(uint16,s['segCountX2'].li.int()/2), 'endCount'),
        (uint16, 'reservedPad'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()/2), 'startCount'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()/2), 'idDelta'),
        (lambda s: dyn.array(uint16,s['segCountX2'].int()/2), 'idRangeOffset'),
        #(lambda s: dyn.block(s.blocksize()-s.size()), 'glyphIdArray'), # FIXME: this might not be correct
    ]
@cmap.table.define
class cmap_format_6(pstruct.type):
    type = 6
    _fields_ = [
        (uint16, 'firstCode'),
        (uint16, 'entryCount'),
        (lambda s: dyn.array(uint16, s['entryCount'].li.int()), 'glyphIdArray'),
    ]

@Table.define
class cvt(parray.block):
    type = 'cvt '
    _object_ = FWord

@Table.define
class fpgm(parray.block):
    type = 'fpgm'
    _object_ = uint8

@Table.define
class gasp(pstruct.type):
    type = 'gasp'
    _fields_ = [
        (uint16, 'version'),
        (uint16, 'numRanges'),
        (lambda s: dyn.array(gasp.range, s['numRanges'].li.int()), 'gaspRange'),
    ]
    class range(pstruct.type):
        _fields_ = [(uint16,'rangeMaxPPEM'),(uint16,'rangeGaspBehaviour')]

@Table.define
class glyf(parray.block):
    type = 'glyf'

    class singleglyph(pstruct.type):
        class _flags(pbinary.terminatedarray):
            class _element(pbinary.struct):
                _fields_ = [
                    (2,'Reserved'),
                    (1,'y-Dual'),
                    (1,'x-Dual'),
                    (1,'Repeat'),
                    (1,'y-Short'),
                    (1,'x-Short'),
                    (1,'On Curve'),
                ]
            class _object_(pbinary.struct):
                def __count(self):
                    if self['value']['Repeat']:
                        return 8
                    return 0

                _fields_ = [
                    (lambda s: s.parent._element, 'value'),
                    (__count, 'count'),
                ]
            def getActualLength(self):
                return sum(((x['count']+1) if x['value']['Repeat'] else 1) for x in self)
            def getActualElement(self, index):
                cur = index
                for x in self:
                    count = (x['count']+1) if x['value']['Repeat'] else 1
                    if cur >= 0 and cur < count:
                        return x['value']
                    cur -= count
                raise IndexError, index
            def isTerminator(self, value):
                p = self.getparent(glyf.singleglyph)
                count = p['endPtsOfContours'][-1].int() + 1
                return self.getActualLength() >= count

        class _xCoords(parray.type):
            def _object_(self):
                idx,flags = len(self.value),self.parent['flags']
                fl = flags.getActualElement(idx)
                if fl['x-Short']:
                    return uint8
                if fl['x-Dual']:
                    return uint0
                return int16
        class _yCoords(parray.type):
            def _object_(self):
                idx,flags = len(self.value),self.parent['flags']
                fl = flags.getActualElement(idx)
                if fl['y-Short']:
                    return uint8
                if fl['y-Dual']:
                    return uint0
                return int16

        _fields_ = [
            (lambda s: dyn.array(uint16, abs(s.getparent(glyf.glyph)['numberOfContours'].li.int())), 'endPtsOfContours'),
            (uint16, 'instructionLength'),
            (lambda s: dyn.block(s['instructionLength'].li.int()), 'instructions'),
            (_flags, 'flags'),
            (lambda s: dyn.clone(s._xCoords, length=s['flags'].getActualLength()), 'xCoordinates'),
            (lambda s: dyn.clone(s._yCoords, length=s['flags'].getActualLength()), 'yCoordinates'),
        ]

    class compositeglyph(parray.terminated):
        class _object_(pstruct.type):
            class _flags(pbinary.struct):
                _fields_ = [
                    (6, 'PADDING'),
                    (1, 'USE_MY_METRICS'),
                    (1, 'WE_HAVE_INSTRUCTIONS'),
                    (1, 'WE_HAVE_A_TWO_BY_TWO'),
                    (1, 'WE_HAVE_AN_X_AND_Y_SCALE'),
                    (1, 'MORE_COMPONENTS'),
                    (1, 'RESERVED'),
                    (1, 'WE_HAVE_A_SCALE'),
                    (1, 'ROUND_XY_TO_GRID'),
                    (1, 'ARGS_ARE_XY_VALUES'), 
                    (1, 'ARG_1_AND_2_ARE_WORDS'), 
                ]
            class arg1and2_short(pstruct.type):
                _fields_ = [(uint16,'argument1'),(uint16,'argument2')]
            class arg1and2_fword(pstruct.type):
                _fields_ = [(FWord,'argument1'),(FWord,'argument2')]
            def __arg1and2(self):
                res = self.arg1and2_fword if 1 else self.arg1and2_short
                if self['flags'].li['ARG_1_AND_2_ARE_WORDS']:
                    return res
                return uint16

            class scale_xy(pstruct.type):
                _fields_ = [(F2Dot14,'xscale'),(F2Dot14,'yscale')]
            class scale_2x2(pstruct.type):
                _fields_ = [(F2Dot14,'xscale'),(F2Dot14,'scale01'),(F2Dot14,'scale10'),(F2Dot14,'yscale')]

            def __scale(self):
                f = self['flags']
                if f['WE_HAVE_A_SCALE']:
                    return F2Dot14
                elif f['WE_HAVE_AN_X_AND_Y_SCALE']:
                    return self.scale_xy
                elif f['WE_HAVE_A_TWO_BY_TWO']:
                    return self.scale_2x2
                return ptype.undefined

            class _instr(pstruct.type):
                _fields_ = [
                    (uint16, 'numInstr'),
                    (lambda s: dyn.block(s['numInstr'].li.int()), 'instr'),
                ]

            def __instr(self):
                return self._instr if self['flags']['WE_HAVE_INSTRUCTIONS'] else ptype.undefined

            _fields_ = [
                (_flags, 'flags'),
                (uint16, 'glyphIndex'),
                (__arg1and2, 'arg1and2'),
                (__scale, 'scale'),
                (__instr, 'instr'),
            ]
        def isTerminator(self, value):
            return value['flags']['MORE_COMPONENTS'] == 0

    class glyph(pstruct.type):
        def __data(self):
            n = self['numberOfContours'].li.int()
            if n >= 0:
                return glyf.singleglyph
            if n == -1:
                return glyf.compositeglyph
            logging.warning('glyf.compositeglyph:numberOfContours is negative but not -1:%d',n)
            return dyn.clone(ptype.undefined, length=self.blocksize()-(uint16.length*5))

        _fields_ = [
            (int16, 'numberOfContours'),
            (FWord, 'xMin'),
            (FWord, 'yMin'),
            (FWord, 'xMax'),
            (FWord, 'yMax'),
            (__data, 'header'),
            (dyn.align(2), 'alignment'),    # XXX: ?? is this right
        ] 
    _object_ = glyph

### main file format
class File(pstruct.type):
    class Entry(pstruct.type):
        class _tag(uint32):
            def str(self):
                return self.serialize()
            def summary(self, **options):
                return '{:s} (0x{:x})'.format(self.str(), self.int())

        def __table(self):
            self = self.getparent(File.Entry)
            rec,l = self['tag'].li.str(),self['length'].li.int()
            res = Table.get(rec, length=l)
            return dyn.clone(res, blocksize=lambda s:l)

        _fields_ = [
            (_tag, 'tag'),
            (uint32, 'checkSum'),
            (dyn.pointer(__table), 'offset'),
            (uint32, 'length'),
        ]
    _fields_ = [
        (Fixed, 'version'),
        (uint16, 'numTables'),
        (uint16, 'searchRange'),
        (uint16, 'entrySelector'),
        (uint16, 'rangeShift'),
        (lambda s: dyn.array(s.Entry, s['numTables'].li.num()), 'tables'),
    ]

if __name__ == '__main__':
    import ttf,ptypes
    reload(ttf)
    ptypes.setsource( ptypes.file('./cour.ttf', 'rb') )

    #t = dyn.block(ptypes.ptype.type.source.size())
    #a = t()
    #a = a.l

    b = ttf.File()
    b = b.l
    print '\n'.join(map(repr,((i,x['tag'].summary()) for i,x in enumerate(b['tables']))))
    
    if 'tables' and False:
        print b['tables'][0]['offset'].d.l.hexdump()
        print b['tables'][1]['offset'].d.l.hexdump()
        print b['tables'][8]['offset'].d.l.hexdump()
        print b['tables'][9]['offset'].d.l.hexdump()
        print b['tables'][10]['offset'].d.l
        print b['tables'][14]
        print b['tables'][15]['offset'].d.l

    # 'cmap'
    if 'cmap' and False:
        print b['tables'][10]
        x = b['tables'][10]['offset'].d.l
        print x
        print x['entry'][0]['offset'].d.l
        print x['entry'][0]['offset'].d.l['data']
        print x['entry'][1]['offset'].d.l['data'].hexdump()
        print x['entry'][2]['offset'].d.l['data']
        print x.blocksize()

    # 'glyf'
    if 'glyf' and True:
        print b['tables'][14]
        c = b['tables'][14]['offset'].d
        c = c.l

        #print c[1]['header']
        #d = c[1]
        #fl = d['header']['flags']
        #for i in range(fl.getActualLength()):
        #    f = set((k.lower() for k,v in fl.getActualElement(i).items() if v))
        #    print i, ','.join(f)

        if 'simple' and False:
            c = c.l
            (X,Y) = (0,0)
            for i,(x,y) in enumerate(zip(d['header']['xCoordinates'],d['header']['yCoordinates'])):
                f = d['header']['flags'].getActualElement(i)
                fl = set((k.lower() for k,v in f.items() if v))

                dx = x.int()
                if 'x-short' in fl:
                    dx = dx if 'x-dual' in fl else -dx

                dy = y.int()
                if 'y-short' in fl:
                    dy = dy if 'y-dual' in fl else -dy
                (X,Y) = (X+dx,Y+dy)
                print i, (X,Y)

        if False:
            d = ttf.glyf.glyph(offset=c.getoffset()+0x9036)
            d = d.l
            e = d['header']
            print e[0]['flags']
            print e[1]['flags']
            print e[1]['scale'].hexdump()

