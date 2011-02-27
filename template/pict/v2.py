from base import *

class header(pstruct.type):
    _fields_ = [
        (Integer, 'filesize'),
        (Integer, 'x1'),
        (Integer, 'y1'),
        (Integer, 'x2'),
        (Integer, 'y2'),
    ]

class OpStash(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

class OpRecord(pstruct.type):
    def __data(self):
        t = int(self['code'].l)

        if t <= 0x1f:
            res = OpStash.Lookup(t)
        elif t <= 0xff:
            res = OpStash.Lookup(t)
        elif t in [0x8200, 0x8201, 0x8202]:
            res = OpStash.Lookup(t)
        elif t in [0xc00]:
            res = OpStash.Lookup(t)
        elif t in [0x200]:
            res = OpStash.Lookup(t)
        elif t in [0x7f00]:
            res = OpStash.Lookup(t)
        elif t < 0x8100:
#            res = OpStash.Lookup(t)
            size = t >> 7
            size &= -2
            res = dyn.block(size)
        else:
            res = OpStash.Lookup(t)
        return res

    _fields_ = [
        (Opcode_v2, 'code'),
        (__data, 'data'),
    ]

@OpStash.Define
class header(pstruct.type):
    type = 0x0c00
    _fields_ = [
        (Integer, 'ffee'),
        (Integer, 'reserved_8'),
        (Long, 'horizontal res'),
        (Long, 'vertical res'),
        (Integer, 'x1'),
        (Integer, 'y1'),
        (Integer, 'x2'),
        (Integer, 'y2'),
        (Long, 'reserved'),
    ]

@OpStash.Define
class directBitsRect(pstruct.type):
    type = 0x009a

    class Pack3(pstruct.type):
        def __lineCount(self):
            return [uint8, Integer][self.parent.rowbytes > 250]
            
        _fields_ = [
            (__lineCount, 'stride'),
            (lambda s: dyn.block(int(s['stride'].l)), 'data')
        ]

    def __pixData(self):
        self['pixMap'].l
        packtype = int(self['pixMap']['packType'])
        rowbytes = int(self['pixMap']['rowBytes'])
        height = int(self['pixMap']['bounds']['bottom']) - int(self['pixMap']['bounds']['top'])

        if packtype == 1 or rowbytes < 8:
            result = dyn.block( rowbytes*height )
        elif packtype == 2:
            result = dyn.block( rowbytes*height * 3 / 4 + 0.5 )
        elif packtype == 3:
            result = dyn.array(self.Pack3, height)
        else:
            raise NotImplementedError(packtype)
        return dyn.clone(result, rowbytes=rowbytes)

    _fields_ = [
        (Long, 'base'),
        (PixMap, 'pixMap'),
        (Rect, 'srcRect'),
        (Rect, 'dstRect'),
        (Integer, 'mode'),
        (__pixData, 'pixData'),
    ]

# http://cpansearch.perl.org/src/EXIFTOOL/Image-ExifTool-8.25/lib/Image/ExifTool/PICT.pm
# GetPixData

"""
class pack3(parray.type):
    _object_ = __pack3

 public int readPack3(QDInputStream theStream)
    throws IOException, QDException
  {
    int data_len = 0;
    short[][] data = new short[this.bounds.height][this.bounds.width];
    for (int line = 0; line < this.bounds.height; ++line)
    {
      int lineCount;
      if (this.rowBytes > 250) {
        lineCount = theStream.readUnsignedShort();
        data_len += 2 + lineCount;
      } else {
        lineCount = theStream.readUnsignedByte();
        data_len += 1 + lineCount;
      }
      byte[] packed = new byte[lineCount];
      theStream.readFully(packed);
      QDBitUtils.unpackLine(packed, data[line]);
    }
    int[] pixData = QDBitUtils.short2RGB(data, QDUtils.rect2Dim(this.bounds));
    this.image_prod = new MemoryImageSource(this.bounds.width, this.bounds.height, direct16Model, pixData, 0, this.bounds.width);

    return data_len;
  }

  public int readPack4(QDInputStream theStream)
    throws IOException, QDException
  {
    int data_len = 0;
    if (this.cmpCount != 3) throw new QDWrongComponentNumber(this.cmpCount);
    byte[][] data = new byte[this.bounds.height][this.bounds.width * this.cmpCount];
    for (int line = 0; line < this.bounds.height; ++line)
    {
      int lineCount;
      if (this.rowBytes > 250) {
        lineCount = theStream.readUnsignedShort();
        data_len += 2 + lineCount;
      } else {
        lineCount = theStream.readUnsignedByte();
        data_len += 1 + lineCount;
      }
      byte[] packed = new byte[lineCount];
      theStream.readFully(packed);
      QDBitUtils.unpackLine(packed, data[line]);
    }
    int[] pixData = QDBitUtils.byte2RGB(data, QDUtils.rect2Dim(this.bounds));
    this.image_prod = new MemoryImageSource(this.bounds.width, this.bounds.height, direct24Model, pixData, 0, this.bounds.width);
    return data_len;
  }

  public int readData(QDInputStream theStream)
    throws IOException, QDException
  {
    int data_len = 0;
    switch (this.packType)
    {
    case 3:
      data_len += readPack3(theStream); break;
    case 4:
      data_len += readPack4(theStream); break;
    default:
      throw new QDUnknownPackException(this.packType);
    }
    return data_len;
  }
"""

@OpStash.Define
class ShortComment(pstruct.type):
    type = 0x00a0
    _fields_ = [
        (Integer, 'kind'),
    ]

@OpStash.Define
class LongComment(pstruct.type):
    type = 0x00a1
    _fields_ = [
        (Integer, 'kind'),
        (Integer, 'size'),
        (lambda s: dyn.block(int(s['size'].l)), 'data')
    ]

@OpStash.Define
class Clip(Rgn):
    type = 0x0001

@OpStash.Define
class PnMode(Integer):
    type = 0x0008

@OpStash.Define
class PnPixPat(PixPat):
    type = 0x0013

@OpStash.Define
class frameRgn(Rgn):
    type = 0x0080

@OpStash.Define
class paintRgn(Rgn):
    type = 0x0081

@OpStash.Define
class eraseRgn(Rgn):
    type = 0x0082

@OpStash.Define
class invertRgn(Rgn):
    type = 0x0083

@OpStash.Define
class fillRgn(Rgn):
    type = 0x0084

@OpStash.Define
class frameSameRRect(Rect):
    type = 0x0048

@OpStash.Define
class TxRatio(pstruct.type):
    type = 0x0010
    _fields_ = [
        (Point, 'numerator'),
        (Point, 'denominator'),
    ]

@OpStash.Define
class Reserved_92(Int16Data):
    type = 0x0092

@OpStash.Define
class NOP(ptype.type):
    type = 0x0000

@OpStash.Define
class OpEndPic(ptype.type):
    type = 0x00ff

@OpStash.Define
class DefHilite(ptype.type):
    type = 0x001e

@OpStash.Define
class CompressedQuickTime(pstruct.type):
    type = 0x8200
    _fields_ = [
        raise NotImplementedError
        (Long, 'size'),
        (Integer, 'version'),
        (dyn.array(Long, 9), 'matrix'),
        (Long, 'matteSize'),
        (Rect, 'matteRect'),
        (Integer, 'mode'),
        (Rect, 'srcRect'),
        (Long, 'accuracy'),
        (Long, 'maskSize'),

        (lambda s: s, 'matteDescr'),
#        (lambda s: dyn.block(s['matteSize'].l.int()), 'matteData'),
#        (lambda s: dyn.block(s['maskSize'].l.int()), 'maskRgn'),
#        (lambda s: s, 'imageData'),
    ]

#@OpStash.Define
#class UncompressedQuickTime(pstruct.type):
#    type = 0x8201

class File(pstruct.type):
    class __opcodes(parray.terminated):
        _object_ = OpRecord
        def isTerminator(self, value):
            return int(value['code']) == 0x00ff
        
    _fields_ = [
        (Integer, 'version'),
        (__opcodes, 'opcodes'),
    ]

if __name__ == '__main__':
    input = ptypes.provider.file('y:/cases/pucik0044/pict_pixdata_heap/poc.pict')
    
    if False:
        import sys
        sys.path.append('f:/work/syringe.git/lib')

    x = header()
    x.source = input
    x.setoffset(512)
    print x.load()
    print x['filesize']

    x = x.newelement(header_v2, 'v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(header_ext_v2, 'ext_v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(picSize, 'picsize', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(picFrame_v2, 'picframe_v2', x.getoffset() + x.size())
    print x.load()

    x = x.newelement(directBitsRect, 'directBitsRect', 0x250+2)
    print x.load()
