# ripped mostly from
# https://raw.githubusercontent.com/Thiefyface/-_-/master/7z_parser.py
import functools, operator, itertools, types, math

import ptypes
from ptypes import *

pbinary.setbyteorder(ptypes.config.byteorder.bigendian)
pint.setbyteorder(ptypes.config.byteorder.littleendian)

class u8(pint.uint8_t): pass
class u16(pint.uint16_t): pass
class u32(pint.uint32_t): pass
class u64(pint.uint64_t): pass

class kInteger(pstruct.type):
    class kIntegerEncoded(pbinary.struct):
        class kIntegerLength(pbinary.terminatedarray):
            _object_ = 1
            def isTerminator(self, value):
                return self.bits() >= 8 or value.int() == 0

        _fields_ = [
            (kIntegerLength, 'length'),
            (lambda self: 8 - self['length'].li.bits(), 'value'),
        ]

        def Length(self):
            return self['length'].bits() - 1

        def int(self):
            return self['value']

    _fields_ = [
        (kIntegerEncoded, 'encoded'),
        (lambda self: dyn.clone(pint.uint_t, length=self['encoded'].li.o.Length()), 'value'),
    ]

    def int(self):
        return self['value'].int() | self['encoded'].int()

    def summary(self):
        length, res, value, encvalue = self['value'].size(), self.int(), self['value'].int(), self['encoded']['value']
        return "encoded={encoded:#04x} value={value:#0{length:d}x}|{encvalue:#04x} : result={result:#0{length:d}x} ({result:d})".format(encoded=ord(self['encoded'].serialize()), encvalue=encvalue, value=self['value'].int(), result=self.int(), length=2 * length + 2)

class kSignature(pstruct.type):
    @classmethod
    def default(cls):
        res = {}
        res['7z'] = cls.sig1.default().int()
        res['bcaf271c'] = cls.sig2.default().int()
        return cls().set(**res)

    class sigbase(ptype.base):
        def valid(self):
            return self.serialize() == self.default().serialize()
        def properties(self):
            res = super(kSignature.sigbase, self).properties()
            try: res['valid'] = self.valid()
            except Exception: res['valid'] = False
            return res

    class sig1(u16, sigbase):
        byteorder = ptypes.config.byteorder.bigendian
        @classmethod
        def default(cls):
            return cls().set(0x377a)

    class sig2(u32, sigbase):
        byteorder = ptypes.config.byteorder.bigendian
        @classmethod
        def default(cls):
            return cls().set(0xbcaf271c)

    _fields_ = [
        (sig1, '7z'),
        (sig2, 'bcaf271c'),
    ]

class ArchiveVersion(pstruct.type):
    _fields_ = [
        (u8, 'major'),
        (u8, 'minor'),
    ]

    def float(self):
        major, minor = self['major'].int(), self['minor'].int()
        precision = math.floor(math.log(minor, 10)) + 1.0
        return self['major'].int() + minor // 10 ** precision

    def summary(self):
        major, minor = self['major'].int(), self['minor'].int()
        precision = math.floor(math.log(minor, 10)) + 1.0
        return "{:.{:d}f}".format(self.float(), math.trunc(precision))

class NextHeader(pstruct.type):
    _fields_ = [
        (lambda self: dyn.opointer(ptype.undefined, lambda s, o: self.getoffset() + o + 20, u64), 'offset'),
        (u64, 'length'),
        (u32, 'crc'),
    ]


class File(pstruct.type):
    class EndHeader(pstruct.type):
        _fields_ = [
            (lambda self: dyn.opointer(ptype.undefined, lambda s, o: self.getparent(File).getoffset() + o + 0x20, u64), 'offset'),
            (u64, 'length'),
            (u32, 'crc'),
        ]

    _fields_ = [
        (kSignature, 'signature'),
        (ArchiveVersion, 'version'),
        (u32, 'crc'),
        (NextHeader, 'tail'),
    ]

class HeaderType(pint.enum, u8):
    _values_ = [
        ("kEnd", 0x0),
        ("kHeader", 0x1),
        ("kArchiveProperties", 0x2),
        ("kAdditionalStreamsInfo", 0x3),
        ("kMainStreamsInfo", 0x4),
        ("kFilesInfo", 0x5),
        ("kPackInfo", 0x6),
        ("kUnpackInfo", 0x7),
        ("kSubStreamsInfo", 0x8),
        ("kSize", 0x9),
        ("kCRC", 0xa),
        ("kFolder", 0xb),
        ("kCodersUnpackSize", 0xc),
        ("kNumUnpackStream", 0xd),
        ("kEmptyStream", 0xe),
        ("kEmptyFile", 0xf),
        ("kAnti", 0x10),
        ("kName", 0x11),
        ("kCTime", 0x12),
        ("kATime", 0x13),
        ("kMTime", 0x14),
        ("kWinAttrib", 0x15),
        ("kComment", 0x16),
        ("kEncodedHeader", 0x17),
        ("kStartPos", 0x18),
        ("kDummy", 0x19),
    ]

class Header(pstruct.type):
    _fields_ = [
        (HeaderType, 'type'),
        (HeaderType, 'attribute'),

    ]

class CompressionType(pint.enum):
    _values_ = [
        ("k_Copy", 0),
        ("k_Delta", 3),
        ("k_LZMA2 = ", 0x21),
        ("k_SWAP2", 0x20302),
        ("k_SWAP4", 0x20304),
        ("k_LZMA", 0x30101),
        ("k_PPMD", 0x30401),
        ("k_Deflate", 0x40108),
        ("k_BZip2", 0x40202),
        ("k_BCJ", 0x3030103),
        ("k_BCJ2", 0x303011B),
        ("k_PPC", 0x3030205),
        ("k_IA64", 0x3030401),
        ("k_ARM", 0x3030501),
        ("k_ARMT", 0x3030701),
        ("k_SPARC", 0x3030805),
        ("k_AES", 0x6F10701),
    ]


#     End header
#     002457e0  17 06 e0 20 4f 24 01 09   88 a0 00 07 0b 01 00 02
#     002457f0  24 06 f1 07 01 0a 53 07   1f 03 65 f5 9f 71 0b f1
#     00245800  23 03 01 01 05 5d 00 40   00 00 01 00 0c 88 98 b3
#     00245810  82 0a 01 5d 29 c8 39 00   00
#
#     +0x0 : '\x17' => "kEncodedHeader"
#     +0x1 : '\x06' => "kPackInfo"
#     +0x2 : '\xe0' => ReadNumber bit mask for amt of bytes to read in the next field.
#                     (e.g. 0x80=>1 byte.  0xc0=>2 bytes, 0xe0=>3 bytes, 0xf0 =>4 bytes.... 8 bytes)
#                                                        (0x88 => 1 byte mask, 0x8f => lower 1 byte)
#     +0x3 : Offset next header   '0x244f40'
#     +0x6 : '\x01' => # of pack streams
#     +0x7 : '\x09' => "kSize"
#     +0x8 : '\x88' => ReadNumber Mask. (0x80 | next field)
#     +0x9 : '\xa0' => kSize | 0x80 => 0xa0.  0x80 => minimum.
#     +0xa : '\x00' => "kEnd"
#     +0xb : '\x07' => "kUnpackInfo"
#     +0xC : '\x0b' => "kFolder"
#     +0xD : '\x01' => Readmask.
#     '''
#     # first it reads an ID. !=kHeader && !=kEncodedHeader => error.
#     hbyte = ord(tail[0])
#     if hbyte != 0x01 and hbyte != 0x17:
#         print "Error: tail[0] != kHeader(0x01)/kEncodedHeader(0x17). Val:0x%02x" %hbyte
#         sys.exit(-1)
#     print "============Begin Tail header parsing (0x%lx->0x%lx)=================" %(tail_addr,tail_addr+tail_size)
#     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#
#     hptr = 0x0
#     tptr = 0x1 # keep track of where we are in the tail header
#
#     if hbyte == 0x17: # yayyy, do Read/Decode.
#
#         '''
#         RESULT result = ReadAndDecodePackedStreams(
#             EXTERNAL_CODECS_LOC_VARS
#             db.ArcInfo.StartPositionAfterHeader, => 0x20 after first headers
#             db.ArcInfo.DataStartPosition2,       => Guessing this starts at 0x0
#             dataVector //   =>???                  |and is soon read in.
#             _7Z_DECODER_CRYPRO_VARS
#             );
#         => ReadStreamsInfo(NULL,dataOffset,folders,unpackSizes,digests)
#         '''
#         hbyte,bread = read_number(tail[tptr:tptr+9])
#         print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#         tptr+=bread
#
#         if hbyte == 0x6: #kPackInfo
#             dataOffset,bread = read_number(tail[tptr:tptr+9])
#             print "dataOffset     : 0x%lx" % dataOffset
#             tptr+=bread
#
#             numPackStreams,bread = read_number(tail[tptr:tptr+9])
#             print "numPackStreams : 0x%02x" % numPackStreams
#             tptr+=bread
#
#             #packinfo = ReadPackInfo()
#             while True:
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 if hbyte == 0x9: #(kSize)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     break
#
#             for i in range(0,numPackStreams):
#                 packSize,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 print "packSize[%d]    : 0x%02x" % (i,packSize)
#
#             while True:
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 if hbyte == 0x0: #(kEnd)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     break
#                 elif hbyte == 0xa: #(kCRC)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     print "implimient crc read, lol"
#                 else:
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     print "impliment skip data"
#
#
#
#             hbyte,bread = read_number(tail[tptr:tptr+9])
#             tptr+=bread
#             print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#
#
#         #unpackinfo = ReadUnpackInfo()
#         if hbyte == 0x7: #kUnpackInfo
#             dataOffset+=0x20
#             data = _7zbuff[dataOffset:]
#             dptr = 0x0
#
#
#             #print "\\x" + "\\x".join("%02x"%ord(s) for s in data[0:10])
#
#             numCodersOutStreams = 0x0
#
#             while True:
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 if hbyte == 0xb: #(kFolder)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     break
#             numFolders,bread = read_number(tail[tptr:tptr+9])
#             tptr+=bread
#             print "numFolders     : 0x%02x" % numFolders
#
#             useless,bread = read_number(tail[tptr:tptr+9])
#             tptr+=bread
#             print "Useless read   : 0x%02x" % useless
#
#             for x in range(0,numFolders):
#                 numCoders,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 print "numCoders      : 0x%02x" % numCoders
#                 if numCoders > 64 or numCoders == 0x0:
#                     print "Invalid numCoder:0x%x (> 64)" % numCoders
#                     sys.exit()
#
#                 coderID = []
#                 for i in range(0,numCoders):
#                     mainByte = ord(tail[tptr])
#                     tptr+=1
#                     print "mainByte       : 0x%02x" % mainByte
#                     if mainByte &0xC0 != 0x0:
#                         print "Invalid mainByte:0x%x " % mainByte
#                         sys.exit()
#
#                     idSize = mainByte&0xF
#                     if idSize > 8:
#                         print "Invalid idsize:0x%x (>0x8)" % idSize
#                         sys.exit()
#
#
#                     if idSize == 1:
#                         _id = struct.unpack("B",tail[tptr:tptr+idSize])[0]
#                     elif idSize == 2:
#                         _id = struct.unpack(">H",tail[tptr:tptr+idSize])[0]
#                     elif idSize == 3:
#                         _id = struct.unpack(">I","\x00" + tail[tptr:tptr+idSize])[0]
#                     elif idSize == 4:
#                         _id = struct.unpack(">I",tail[tptr:tptr+idSize])[0]
#                     elif idSize == 8:
#                         _id = struct.unpack(">Q",tail[tptr:tptr+idSize])[0]
#
#                     coderID.append(_id)
#
#                     # skip over idSize
#                     tptr+=idSize
#
#                     print "CoderID[%d]     : 0x%lx : (%s)" % (i,_id,cDict[_id])
#
#                     if (mainByte & 0x10) != 0:
#                         coderInStreams,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         if coderInStreams > 64:
#                             print "Invalid coderInStreams:%d"%coderInStreams
#                             sys.exit()
#                         _,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         if _ != 1:
#                             print "Invalid post coderInStream read:%d"%_
#                             sys.exit()
#
#                     if (mainByte & 0x20) != 0:
#                         propsSize,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         print "propsSize      : 0x%02x" % (propsSize)
#
#                         #if _id == 0x21 & propsSize == 1: #"k_LZMA2"
#                         if _id == 0x30101 and propsSize == 5: #"k_LZMA"
#                             dicSize = struct.unpack("<I",tail[tptr+1:tptr+5])[0]
#                             print "dicSize        : 0x%02x" % (dicSize)
#
#                     #skipzies
#                     #tptr+=propsSize
#
#                         if _id == 0x6f10701: # k_AES
#                             # parse out the props
#                             # NumCyclesPower,saltSize,ivSize,IV
#                             b0 = ord(tail[tptr])
#                             tptr+=1
#                             b1 = ord(tail[tptr])
#                             tptr+=1
#
#                             NumCyclesPower = b0 & 0x3F
#                             print "NumCyclesPower : 0x%02x" % (NumCyclesPower)
#                             saltSize = ((b0 >> 7) & 1) + (b1 >> 4)
#                             print "saltSize       : 0x%02x" % (saltSize)
#                             ivSize = ((b0 >> 6) & 1 ) + (b1 & 0xF)
#                             print "ivSize         : 0x%02x" % (ivSize)
#
#                             if saltSize > 0:
#                                 Salt = struct.unpack("B"*saltSize,tail[tptr:tptr+saltSize])
#                                 tptr+=saltSize
#                                 print "Salt          %08x" % Salt
#
#                             #print "\\x" + "\\x".join("%02x"%ord(x) for x in tail[tptr:tptr+ivSize])
#                             #IV,bread = struct.unpack("<Q",)
#                             IV = tail[tptr:tptr+ivSize] +"\x00\x00\x00\x00\x00\x00\x00\x00"
#                             tptr+=ivSize
#                             print "IV             : 0x%08x" % struct.unpack(">Q",IV[0:8])
#
#
#                 # end numCodersLoop
#                 numInStreams = numCoders
#                 if numCoders == 1 and numInStreams == 1:
#                     indexOfMainStream = 0
#                     numPackStreams = 1
#                     numBonds = 0
#                 else:
#                     numBonds = numCoders -1
#
#                     for i in range(0,numBonds):
#                         bIndex,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         print "bIndex         : 0x%02x" % (bIndex)
#
#                         cIndex,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         print "cIndex         : 0x%02x" % (cIndex)
#
#
#                 StreamUsed = []
#                 numPackStreams = numInStreams-numBonds
#                 if (numPackStreams != 1):
#                     for i in range(0,numPackStreams):
#                         sIndex,bread =read_number(tail[tptr:tptr+9])
#                         tptr+=bread
#                         print "sIndex      : 0x%02x" % (cIndex)
#                         StreamUsed.append(sIndex)
#
#
#                 numCodersOutStreams+=numCoders
#
#                 # end numFolders loop
#
#             while True:
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 if hbyte == 0xC: #(kCodersUnpackSize)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     break
#
#
#             CoderUnpackSizes = []
#             for i in range(0,numCodersOutStreams):
#                 size,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 CoderUnpackSizes.append(size)
#             print "CoderUnpackSize: %s" % str(CoderUnpackSizes)
#
#             while True:
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 tptr+=bread
#                 CRCs = []
#                 if hbyte == 0x0: #(kEnd)
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     break
#                 elif hbyte == 0xa: #kCRC
#                     boolVec = []
#                     print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                     # start ReadHashDigests(numFolders, folderCRCs)
#                     allAreDefined,bread = read_number(tail[tptr:tptr+9])
#                     print "allAreDefined  : 0x%02x" % (allAreDefined)
#                     tptr+=bread
#                     if allAreDefined == 0:
#                         #ReadBoolVector(1,v)
#                         # just being lazy and only reading 1 item XD
#                         for i in range(0,numFolders%8):
#                             boolVec.append(ord(tail[tptr]))
#                             tptr+=1
#                     else:
#                         #sets entire CBoolVector as true...
#                         for i in range(0,numFolders%8):
#                             boolVec.append(0xff)
#
#                     print "CRCBoolVec     : %s" % str(boolVec)
#
#                     for i in range(0,numFolders):
#                         crc = struct.unpack(">I",tail[tptr:tptr+4])[0]
#                         tptr+=4
#                         CRCs.append(crc)
#                         print "CRC[%i]         : 0x%08x"%(i,crc)
#
#
#
#                 else:
#                     skip,bread = read_number(tail[tptr:tptr+9])
#                     tptr+=(bread+skip)
#                     print "Skipping %d bytes" % skip
#
#
#             # at this point we shift over to the data header
#             print "============Begin packed header parsing (0x%lx,0x%x)=================" %(dataOffset,packSize)
#             from Crypto.Cipher import AES
#             import hashlib
#             s =hashlib.sha256()
#
#             eptr = dataOffset
#             cryptBuffer = _7zbuff[eptr:packSize]
#             tmpkey = "QggGPGqdMtzMmO2RROSCpaSRo1iKEAp8"
#             realkey = b""
#             for c in tmpkey:
#                 realkey+=b"\x00"
#                 realkey+=c
#
#             for i in range(0,1<<NumCyclesPower):
#                 s.update(realkey)
#
#             realkey = s.digest()
#             print "AES Key hashed alot: %s" % "\\x"+"\\x".join("%02x"%ord(c) for c in realkey)
#
#             d = AES.new(realkey,AES.MODE_CBC,IV) #third param == IV. Do we need one?
#             decryptedBuffer = d.decrypt(cryptBuffer)
#
#             buf = ""
#             if not len(decryptedBuffer):
#                 print "[;_;] Could not get the decrypted buffer..."
#                 sys.exit()
#
#             for i in range(0,len(decryptedBuffer)):
#                 buf += "\\x%02x"%ord(decryptedBuffer[i])
#             print buf
#
#             # Now we start reading all the headers and stuff....
#
#
#
#
#
#
#     # lol, okay, so what if it's unencoded...?
#     elif hbyte == 0x1: #kHeader
#         hbyte,bread = read_number(tail[tptr:tptr+9])
#         print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#         tptr+=bread
#
#         if hbyte != 0x4:   #0x4:"kMainStreamsInfo",
#             print "[x.x] invalid next header, expecting 0x4."
#             sys.exit()
#
#         if hbyte == 0x4:  # kMainStreamsInfo
#             # ReadStreamsInfo()
#             hbyte,bread = read_number(tail[tptr:tptr+9])
#             print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#             tptr+=bread
#
#             if hbyte == 0x6: # kPackInfo
#                 dataOffset,bread = read_number(tail[tptr:tptr+9])
#                 print "dataOffset     : 0x%02x" % (dataOffset)
#                 tptr+=bread
#
#             hbyte,bread = read_number(tail[tptr:tptr+9])
#             print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#             tptr+=bread
#
#             if hbyte == 0x2:    # kArchiveProperties
#                 #ReadArchiveProperties()
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                 tptr+=bread
#
#
#             if hbyte == 0x3:  # kAdditionalStreamsInfo
#                 #ReadAndDecodePackedstreams (same as other?idk.)
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                 tptr+=bread
#
#
#
#             if hbyte == 0x5:  # kFilesInfo
#                 # do a bunch of shit.
#                 hbyte,bread = read_number(tail[tptr:tptr+9])
#                 print "Hbyte          : 0x%02x (%s)" % (hbyte,hdict[hbyte])
#                 tptr+=bread

if __name__ == '__main__':
    # 0000000000: 37 7A BC AF 27 1C 00 04   5B 38 BE F9 59 0E 00 00
    # 0000000010: 00 00 00 00 23 00 00 00   00 00 00 00 7A 63 68 FD
    # 0000000020: 00 21 16 89 6C 71 3D AB   7D 89 E6 3C 2E BE 60 24

    res = '''
    37 7A BC AF 27 1C 00 04   5B 38 BE F9 59 0E 00 00
    00 00 00 00 23 00 00 00   00 00 00 00 7A 63 68 FD
    00 21 16 89 6C 71 3D AB   7D 89 E6 3C 2E BE 60 24
    '''.strip().translate(None, ' \n')

    ptypes.setsource(ptypes.prov.string(res.decode('hex')))

    # 002457e0  17 06 e0 20 4f 24 01 09   88 a0 00 07 0b 01 00 02
    # 002457f0  24 06 f1 07 01 0a 53 07   1f 03 65 f5 9f 71 0b f1
    # 00245800  23 03 01 01 05 5d 00 40   00 00 01 00 0c 88 98 b3
    # 00245810  82 0a 01 5d 29 c8 39 00   00

    res = '''
    17 06 e0 20 4f 24 01 09   88 a0 00 07 0b 01 00 02
    24 06 f1 07 01 0a 53 07   1f 03 65 f5 9f 71 0b f1
    23 03 01 01 05 5d 00 40   00 00 01 00 0c 88 98 b3
    82 0a 01 5d 29 c8 39 00   00
    '''.strip().translate(None, ' \n')

    ptypes.setsource(ptypes.prov.string(res.decode('hex')))
