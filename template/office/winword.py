import logging, datetime

import ptypes
from ptypes import *

from . import storage

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

def rl(*l): return list(reversed(l))

## Atomic Types
class LID(pint.enum, pint.uint16_t):
    _values_ = [
        ('ar-SA', 1025), ('bg-BG', 1026), ('ca-ES', 1027), ('zh-TW', 1028),
        ('cs-CZ', 1029), ('da-DK', 1030), ('de-DE', 1031), ('el-GR', 1032),
        ('en-US', 1033), ('es-ES', 1034), ('fi-FI', 1035), ('fr-FR', 1036),
        ('he-IL', 1037), ('hu-HU', 1038), ('is-IS', 1039), ('it-IT', 1040),
        ('ja-JP', 1041), ('ko-KR', 1042), ('nl-NL', 1043), ('nb-NO', 1044),
        ('pl-PL', 1045), ('pt-BR', 1046), ('rm-CH', 1047), ('ro-RO', 1048),
        ('ru-RU', 1049), ('hr-HR', 1050), ('sk-SK', 1051), ('sq-AL', 1052),
        ('sv-SE', 1053), ('th-TH', 1054), ('tr-TR', 1055), ('ur-PK', 1056),
        ('id-ID', 1057), ('uk-UA', 1058), ('be-BY', 1059), ('sl-SI', 1060),
        ('et-EE', 1061), ('lv-LV', 1062), ('lt-LT', 1063), ('tg-Cyrl-TJ', 1064),
        ('fa-IR', 1065), ('vi-VN', 1066), ('hy-AM', 1067), ('az-Latn-AZ', 1068),
        ('eu-ES', 1069), ('wen-DE', 1070), ('mk-MK', 1071), ('st-ZA', 1072),
        ('ts-ZA', 1073), ('tn-ZA', 1074), ('ven-ZA', 1075), ('xh-ZA', 1076),
        ('zu-ZA', 1077), ('af-ZA', 1078), ('ka-GE', 1079), ('fo-FO', 1080),
        ('hi-IN', 1081), ('mt-MT', 1082), ('se-NO', 1083), ('gd-GB', 1084),
        ('yi', 1085), ('ms-MY', 1086), ('kk-KZ', 1087), ('ky-KG', 1088),
        ('sw-KE', 1089), ('tk-TM', 1090), ('uz-Latn-UZ', 1091), ('tt-RU', 1092),
        ('bn-IN', 1093), ('pa-IN', 1094), ('gu-IN', 1095), ('or-IN', 1096),
        ('ta-IN', 1097), ('te-IN', 1098), ('kn-IN', 1099), ('ml-IN', 1100),
        ('as-IN', 1101), ('mr-IN', 1102), ('sa-IN', 1103), ('mn-MN', 1104),
        ('bo-CN', 1105), ('cy-GB', 1106), ('km-KH', 1107), ('lo-LA', 1108),
        ('my-MM', 1109), ('gl-ES', 1110), ('kok-IN', 1111), ('mni', 1112),
        ('sd-IN', 1113), ('syr-SY', 1114), ('si-LK', 1115), ('chr-US', 1116),
        ('iu-Cans-CA', 1117), ('am-ET', 1118), ('tmz', 1119), ('ks-Arab-IN', 1120),
        ('ne-NP', 1121), ('fy-NL', 1122), ('ps-AF', 1123), ('fil-PH', 1124),
        ('dv-MV', 1125), ('bin-NG', 1126), ('fuv-NG', 1127), ('ha-Latn-NG', 1128),
        ('ibb-NG', 1129), ('yo-NG', 1130), ('quz-BO', 1131), ('nso-ZA', 1132),
        ('ig-NG', 1136), ('kr-NG', 1137), ('gaz-ET', 1138), ('ti-ER', 1139),
        ('gn-PY', 1140), ('haw-US', 1141), ('la', 1142), ('so-SO', 1143),
        ('ii-CN', 1144), ('pap-AN', 1145), ('ug-Arab-CN', 1152), ('mi-NZ', 1153),
        ('ar-IQ', 2049), ('zh-CN', 2052), ('de-CH', 2055), ('en-GB', 2057),
        ('es-MX', 2058), ('fr-BE', 2060), ('it-CH', 2064), ('nl-BE', 2067),
        ('nn-NO', 2068), ('pt-PT', 2070), ('ro-MD', 2072), ('ru-MD', 2073),
        ('sr-Latn-CS', 2074), ('sv-FI', 2077), ('ur-IN', 2080), ('az-Cyrl-AZ', 2092),
        ('ga-IE', 2108), ('ms-BN', 2110), ('uz-Cyrl-UZ', 2115), ('bn-BD', 2117),
        ('pa-PK', 2118), ('mn-Mong-CN', 2128), ('bo-BT', 2129), ('sd-PK', 2137),
        ('tzm-Latn-DZ', 2143), ('ks-Deva-IN', 2144), ('ne-IN', 2145), ('quz-EC', 2155),
        ('ti-ET', 2163), ('ar-EG', 3073), ('zh-HK', 3076), ('de-AT', 3079),
        ('en-AU', 3081), ('es-ES', 3082), ('fr-CA', 3084), ('sr-Cyrl-CS', 3098),
        ('quz-PE', 3179), ('ar-LY', 4097), ('zh-SG', 4100), ('de-LU', 4103),
        ('en-CA', 4105), ('es-GT', 4106), ('fr-CH', 4108), ('hr-BA', 4122),
        ('ar-DZ', 5121), ('zh-MO', 5124), ('de-LI', 5127), ('en-NZ', 5129),
        ('es-CR', 5130), ('fr-LU', 5132), ('bs-Latn-BA', 5146), ('ar-MO', 6145),
        ('en-IE', 6153), ('es-PA', 6154), ('fr-MC', 6156), ('ar-TN', 7169),
        ('en-ZA', 7177), ('es-DO', 7178), ('fr-029', 7180), ('ar-OM', 8193),
        ('en-JM', 8201), ('es-VE', 8202), ('fr-RE', 8204), ('ar-YE', 9217),
        ('en-029', 9225), ('es-CO', 9226), ('fr-CG', 9228), ('ar-SY', 10241),
        ('en-BZ', 10249), ('es-PE', 10250), ('fr-SN', 10252), ('ar-JO', 11265),
        ('en-TT', 11273), ('es-AR', 11274), ('fr-CM', 11276), ('ar-LB', 12289),
        ('en-ZW', 12297), ('es-EC', 12298), ('fr-CI', 12300), ('ar-KW', 13313),
        ('en-PH', 13321), ('es-CL', 13322), ('fr-ML', 13324), ('ar-AE', 14337),
        ('en-ID', 14345), ('es-UY', 14346), ('fr-MA', 14348), ('ar-BH', 15361),
        ('en-HK', 15369), ('es-PY', 15370), ('fr-HT', 15372), ('ar-QA', 16385),
        ('en-IN', 16393), ('es-BO', 16394), ('en-MY', 17417), ('es-SV', 17418),
        ('en-SG', 18441), ('es-HN', 18442), ('es-NI', 19466), ('es-PR', 20490),
        ('es-US', 21514), ('es-419', 58378), ('fr-015', 58380),
]

class Fts(pint.enum, pint.uint8_t):
    _values_ = [
        ('ftsNil', 0x00),
        ('ftsAuto', 0x01),
        ('ftsPercent', 0x02),
        ('ftsDxa', 0x03),
        ('ftsDxaSys', 0x13),
    ]

class _Fts(pbinary.enum):
    _width_, _values_ = 3, Fts._values_[:]

class Bool8(pint.enum, pint.uint8_t):
    _values_ = [
        ('false', 0x00),
        ('true', 0x00),
    ]


class character_position(pint.uint32_t):
    def properties(self):
        res = super(character_position, self).properties()
        if isinstance(self.parent, parray.type):
            container = self.parent

            try: idx = int(self.name())
            except ValueError: idx = container.index(self)

            if idx + 1 < len(container):
                res['deltaCP'] = container[idx + 1].int() - self.int()
            return res
        return res

class CP(character_position): pass
class FC(character_position): pass

class BYTE(pint.uint8_t): pass

class LONG(pint.uint32_t): pass

class USHORT(pint.uint16_t): pass

class XAS(pint.sint16_t):
    def summary(self):
        return "{:d} twip{:s}".format(self.int(), '' if self.int() == 0 else 's')
class YAS(XAS): pass

class XAS_nonNeg(pint.uint16_t):
    def summary(self):
        return "{:d} twip{:s}".format(self.int(), '' if self.int() == 0 else 's')
class YAS_nonNeg(XAS_nonNeg): pass

class XAS_plusOne(pint.sint16_t):
    def summary(self):
        res = self.int() - 1
        return "{:d} twip{:s}".format(res, '' if res == 0 else 's')
class YAS_plusOne(XAS_plusOne): pass

class COLORREF(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'red'),
        (pint.uint8_t, 'green'),
        (pint.uint8_t, 'blue'),
        (pint.uint8_t, 'fAuto'),
    ]

class Ipat(pint.enum, pint.uint16_t):
    _values_ = [
        ('ipatAuto', 0x0000),
        ('ipatSolid', 0x0001),
        ('ipatPct5', 0x0002),
        ('ipatPct10', 0x0003),
        ('ipatPct20', 0x0004),
        ('ipatPct25', 0x0005),
        ('ipatPct30', 0x0006),
        ('ipatPct40', 0x0007),
        ('ipatPct50', 0x0008),
        ('ipatPct60', 0x0009),
        ('ipatPct70', 0x000A),
        ('ipatPct75', 0x000B),
        ('ipatPct80', 0x000C),
        ('ipatPct90', 0x000D),
        ('ipatDkHorizontal', 0x000E),
        ('ipatDkVertical', 0x000F),
        ('ipatDkForeDiag', 0x0010),
        ('ipatDkBackDiag', 0x0011),
        ('ipatDkCross', 0x0012),
        ('ipatDkDiagCross', 0x0013),
        ('ipatHorizontal', 0x0014),
        ('ipatVertical', 0x0015),
        ('ipatForeDiag', 0x0016),
        ('ipatBackDiag', 0x0017),
        ('ipatCross', 0x0018),
        ('ipatDiagCross', 0x0019),
        ('ipatPctNew2', 0x0023),
        ('ipatPctNew7', 0x0024),
        ('ipatPctNew12', 0x0025),
        ('ipatPctNew15', 0x0026),
        ('ipatPctNew17', 0x0027),
        ('ipatPctNew22', 0x0028),
        ('ipatPctNew27', 0x0029),
        ('ipatPctNew32', 0x002A),
        ('ipatPctNew35', 0x002B),
        ('ipatPctNew37', 0x002C),
        ('ipatPctNew42', 0x002D),
        ('ipatPctNew45', 0x002E),
        ('ipatPctNew47', 0x002F),
        ('ipatPctNew52', 0x0030),
        ('ipatPctNew55', 0x0031),
        ('ipatPctNew57', 0x0032),
        ('ipatPctNew62', 0x0033),
        ('ipatPctNew65', 0x0034),
        ('ipatPctNew67', 0x0035),
        ('ipatPctNew72', 0x0036),
        ('ipatPctNew77', 0x0037),
        ('ipatPctNew82', 0x0038),
        ('ipatPctNew85', 0x0039),
        ('ipatPctNew87', 0x003A),
        ('ipatPctNew92', 0x003B),
        ('ipatPctNew95', 0x003C),
        ('ipatPctNew97', 0x003D),
        ('ipatNil', 0xFFFF),
    ]

class _Ipat(pbinary.enum):
    _width_, _values_ = 6, Ipat._values_[:-1] + [('iPatNil', 0x3f)]

class BrcType(pint.enum, pint.uint8_t):
    _values_ = [
        ('none', 0x00),
        ('single', 0x01),
        ('double', 0x03),
        ('thin', 0x05),
        ('dotted', 0x06),
        ('dashed', 0x07),
        ('dotDash', 0x08),
        ('dotDotDash', 0x09),
        ('triple', 0x0A),
        ('thinThickSmallGap', 0x0B),
        ('thickThinSmallGap', 0x0C),
        ('thinThickThinSmallGap', 0x0D),
        ('thinThickMediumGap', 0x0E),
        ('thickThinMediumGap', 0x0F),
        ('thinThickThinMediumGap', 0x10),
        ('thinThickLargeGap', 0x11),
        ('thickThinLargeGap', 0x12),
        ('thinThickThinLargeGap', 0x13),
        ('wave', 0x14),
        ('doubleWave', 0x15),
        ('dashSmallGap', 0x16),
        ('dashDotStroked', 0x17),
        ('threeDEmboss', 0x18),
        ('threeDEngrave', 0x19),
        ('outset', 0x1A),
        ('inset', 0x1B),
        ('apples', 0x40),
        ('archedScallops', 0x41),
        ('babyPacifier', 0x42),
        ('babyRattle', 0x43),
        ('balloons3Colors', 0x44),
        ('balloonsHotAir', 0x45),
        ('basicBlackDashes', 0x46),
        ('basicBlackDots', 0x47),
        ('basicBlackSquares', 0x48),
        ('basicThinLines', 0x49),
        ('basicWhiteDashes', 0x4A),
        ('basicWhiteDots', 0x4B),
        ('basicWhiteSquares', 0x4C),
        ('basicWideInline', 0x4D),
        ('basicWideMidline', 0x4E),
        ('basicWideOutline', 0x4F),
        ('bats', 0x50),
        ('birds', 0x51),
        ('birdsFlight', 0x52),
        ('cabins', 0x53),
        ('cakeSlice', 0x54),
        ('candyCorn', 0x55),
        ('celticKnotwork', 0x56),
        ('certificateBanner', 0x57),
        ('chainLink', 0x58),
        ('champagneBottle', 0x59),
        ('checkedBarBlack', 0x5A),
        ('checkedBarColor', 0x5B),
        ('checkered', 0x5C),
        ('christmasTree', 0x5D),
        ('circlesLines', 0x5E),
        ('circlesRectangles', 0x5F),
        ('classicalWave', 0x60),
        ('clocks', 0x61),
        ('compass', 0x62),
        ('confetti', 0x63),
        ('confettiGrays', 0x64),
        ('confettiOutline', 0x65),
        ('confettiStreamers', 0x66),
        ('confettiWhite', 0x67),
        ('cornerTriangles', 0x68),
        ('couponCutoutDashes', 0x69),
        ('couponCutoutDots', 0x6A),
        ('crazyMaze', 0x6B),
        ('creaturesButterfly', 0x6C),
        ('creaturesFish', 0x6D),
        ('creaturesInsects', 0x6E),
        ('creaturesLadyBug', 0x6F),
        ('crossStitch', 0x70),
        ('cup', 0x71),
        ('decoArch', 0x72),
        ('decoArchColor', 0x73),
        ('decoBlocks', 0x74),
        ('diamondsGray', 0x75),
        ('doubleD', 0x76),
        ('doubleDiamonds', 0x77),
        ('earth1', 0x78),
        ('earth2', 0x79),
        ('eclipsingSquares1', 0x7A),
        ('eclipsingSquares2', 0x7B),
        ('eggsBlack', 0x7C),
        ('fans', 0x7D),
        ('film', 0x7E),
        ('firecrackers', 0x7F),
        ('flowersBlockPrint', 0x80),
        ('flowersDaisies', 0x81),
        ('flowersModern1', 0x82),
        ('flowersModern2', 0x83),
        ('flowersPansy', 0x84),
        ('flowersRedRose', 0x85),
        ('flowersRoses', 0x86),
        ('flowersTeacup', 0x87),
        ('flowersTiny', 0x88),
        ('gems', 0x89),
        ('gingerbreadMan', 0x8A),
        ('gradient', 0x8B),
        ('handmade1', 0x8C),
        ('handmade2', 0x8D),
        ('heartBalloon', 0x8E),
        ('heartGray', 0x8F),
        ('hearts', 0x90),
        ('heebieJeebies', 0x91),
        ('holly', 0x92),
        ('houseFunky', 0x93),
        ('hypnotic', 0x94),
        ('iceCreamCones', 0x95),
        ('lightBulb', 0x96),
        ('lightning1', 0x97),
        ('lightning2', 0x98),
        ('mapPins', 0x99),
        ('mapleLeaf', 0x9A),
        ('mapleMuffins', 0x9B),
        ('marquee', 0x9C),
        ('marqueeToothed', 0x9D),
        ('moons', 0x9E),
        ('mosaic', 0x9F),
        ('musicNotes', 0xA0),
        ('northwest', 0xA1),
        ('ovals', 0xA2),
        ('packages', 0xA3),
        ('palmsBlack', 0xA4),
        ('palmsColor', 0xA5),
        ('paperClips', 0xA6),
        ('papyrus', 0xA7),
        ('partyFavor', 0xA8),
        ('partyGlass', 0xA9),
        ('pencils', 0xAA),
        ('people', 0xAB),
        ('peopleWaving', 0xAC),
        ('peopleHats', 0xAD),
        ('poinsettias', 0xAE),
        ('postageStamp', 0xAF),
        ('pumpkin1', 0xB0),
        ('pushPinNote2', 0xB1),
        ('pushPinNote1', 0xB2),
        ('pyramids', 0xB3),
        ('pyramidsAbove', 0xB4),
        ('quadrants', 0xB5),
        ('rings', 0xB6),
        ('safari', 0xB7),
        ('sawtooth', 0xB8),
        ('sawtoothGray', 0xB9),
        ('scaredCat', 0xBA),
        ('seattle', 0xBB),
        ('shadowedSquares', 0xBC),
        ('sharksTeeth', 0xBD),
        ('shorebirdTracks', 0xBE),
        ('skyrocket', 0xBF),
        ('snowflakeFancy', 0xC0),
        ('snowflakes', 0xC1),
        ('sombrero', 0xC2),
        ('southwest', 0xC3),
        ('stars', 0xC4),
        ('starsTop', 0xC5),
        ('stars3d', 0xC6),
        ('starsBlack', 0xC7),
        ('starsShadowed', 0xC8),
        ('sun', 0xC9),
        ('swirligig', 0xCA),
        ('tornPaper', 0xCB),
        ('tornPaperBlack', 0xCC),
        ('trees', 0xCD),
        ('triangleParty', 0xCE),
        ('triangles', 0xCF),
        ('tribal1', 0xD0),
        ('tribal2', 0xD1),
        ('tribal3', 0xD2),
        ('tribal4', 0xD3),
        ('tribal5', 0xD4),
        ('tribal6', 0xD5),
        ('twistedLines1', 0xD6),
        ('twistedLines2', 0xD7),
        ('vine', 0xD8),
        ('waveline', 0xD9),
        ('weavingAngles', 0xDA),
        ('weavingBraid', 0xDB),
        ('weavingRibbon', 0xDC),
        ('weavingStrips', 0xDD),
        ('whiteFlowers', 0xDE),
        ('woodwork', 0xDF),
        ('xIllusions', 0xE0),
        ('zanyTriangles', 0xE1),
        ('zigZag', 0xE2),
        ('zigZagStitch', 0xE3),
        ('ignored', 0xFF),
    ]

class _BrcType(pbinary.enum):
    _width_, _values_ = 8, BrcType._values_[:]

class TabJC(pbinary.enum):
    _width_, _values_ = 3, [
        ('jcLeft', 0),
        ('jcCenter', 1),
        ('jcRight', 2),
        ('jcDecimal', 3),
        ('jcBar', 4),
        ('jcList', 6),
    ]

class TabLC(pbinary.enum):
    _width_, _values_ = 3, [
        ('tlcNone', 0),
        ('tlcDot', 1),
        ('tlcHyphen', 2),
        ('tlcUnderscore', 3),
        ('tlcHeavy', 4),
        ('tlcMiddleDot', 5),
        ('tlcDefault', 7),
    ]

class TBD(pbinary.struct):
    _fields_ = [
        (TabJC, 'jc'),
        (TabLC, 'tlc'),
        (2, 'unused'),
    ]

class MSONFC(pint.enum, pint.uint8_t):
    _values_ = [
        ('msonfcArabic', 0x00),
        ('msonfcUCRoman', 0x01),
        ('msonfcLCRoman', 0x02),
        ('msonfcUCLetter', 0x03),
        ('msonfcLCLetter', 0x04),
        ('msonfcOrdinal', 0x05),
        ('msonfcCardtext', 0x06),
        ('msonfcOrdtext', 0x07),
        ('msonfcHex', 0x08),
        ('msonfcChiManSty', 0x09),
        ('msonfcDbNum1', 0x0A),
        ('msonfcDbNum2', 0x0B),
        ('msonfcAiueo', 0x0C),
        ('msonfcIroha', 0x0D),
        ('msonfcDbChar', 0x0E),
        ('msonfcSbChar', 0x0F),
        ('msonfcDbNum3', 0x10),
        ('msonfcDbNum4', 0x11),
        ('msonfcCirclenum', 0x12),
        ('msonfcDArabic', 0x13),
        ('msonfcDAiueo', 0x14),
        ('msonfcDIroha', 0x15),
        ('msonfcArabicLZ', 0x16),
        ('msonfcBullet', 0x17),
        ('msonfcGanada', 0x18),
        ('msonfcChosung', 0x19),
        ('msonfcGB1', 0x1A),
        ('msonfcGB2', 0x1B),
        ('msonfcGB3', 0x1C),
        ('msonfcGB4', 0x1D),
        ('msonfcZodiac1', 0x1E),
        ('msonfcZodiac2', 0x1F),
        ('msonfcZodiac3', 0x20),
        ('msonfcTpeDbNum1', 0x21),
        ('msonfcTpeDbNum2', 0x22),
        ('msonfcTpeDbNum3', 0x23),
        ('msonfcTpeDbNum4', 0x24),
        ('msonfcChnDbNum1', 0x25),
        ('msonfcChnDbNum2', 0x26),
        ('msonfcChnDbNum3', 0x27),
        ('msonfcChnDbNum4', 0x28),
        ('msonfcKorDbNum1', 0x29),
        ('msonfcKorDbNum2', 0x2A),
        ('msonfcKorDbNum3', 0x2B),
        ('msonfcKorDbNum4', 0x2C),
        ('msonfcHebrew1', 0x2D),
        ('msonfcArabic1', 0x2E),
        ('msonfcHebrew2', 0x2F),
        ('msonfcArabic2', 0x30),
        ('msonfcHindi1', 0x31),
        ('msonfcHindi2', 0x32),
        ('msonfcHindi3', 0x33),
        ('msonfcHindi4', 0x34),
        ('msonfcThai1', 0x35),
        ('msonfcThai2', 0x36),
        ('msonfcThai3', 0x37),
        ('msonfcViet1', 0x38),
        ('msonfcNumInDash', 0x39),
        ('msonfcLCRus', 0x3A),
        ('msonfcUCRus', 0x3B),
        ('msonfcNone', 0xFF),
    ]

class Ico(pint.enum, pint.uint8_t):
    # FIXME: Copy table
    _values_ = []
    def COLORREF(self):
        # FIXME: cons a COLORREF using the table and the index.
        raise NotImplementedError

class _Ico(pbinary.enum):
    _width_, _values_ = 5, Ico._values_
    def COLORREF(self):
        # FIXME: Copy the table and cons a COLORREF using it and the index.
        raise NotImplementedError

class _VerticalAlign(pbinary.enum):
    _width_, _values_ = 2, [
        ('vaTop', 0x00),
        ('vaCenter', 0x01),
        ('vaBottom', 0x02),
    ]

class _VerticalMergeFlag(pbinary.enum):
    _width_, _values_ = 2, [
        ('fvmClear', 0x00),
        ('fvmMerge', 0x01),
        ('fvmRestart', 0x02),
    ]

class _TextFlow(pbinary.enum):
    _width_, _values_ = 3, [
        ('grpfTFlrtb', 0x0000),
        ('grpfTFtbrl', 0x0001),
        ('grpfTFbtlr', 0x0003),
        ('grpfTFlrtbv', 0x0004),
        ('grpfTFtbrlv', 0x0005),
    ]

class flt(pint.enum, pint.uint8_t):
    _values_ = [
        ('Unparseable', 0x01),
        ('Unnamed', 0x02),
        ('REF', 0x03),
        ('FTNREF', 0x05),
        ('SET', 0x06),
        ('IF', 0x07),
        ('INDEX', 0x08),
        ('STYLEREF', 0x0A),
        ('SEQ', 0x0C),
        ('TOC', 0x0D),
        ('INFO', 0x0E),
        ('TITLE', 0x0F),
        ('SUBJECT', 0x10),
        ('AUTHOR', 0x11),
        ('KEYWORDS', 0x12),
        ('COMMENTS', 0x13),
        ('LASTSAVEDBY', 0x14),
        ('CREATEDATE', 0x15),
        ('SAVEDATE', 0x16),
        ('PRINTDATE', 0x17),
        ('REVNUM', 0x18),
        ('EDITTIME', 0x19),
        ('NUMPAGES', 0x1A),
        ('NUMWORDS', 0x1B),
        ('NUMCHARS', 0x1C),
        ('FILENAME', 0x1D),
        ('TEMPLATE', 0x1E),
        ('DATE', 0x1F),
        ('TIME', 0x20),
        ('PAGE', 0x21),
        ('EQUAL', 0x22),
        ('QUOTE', 0x23),
        ('INCLUDE', 0x24),
        ('PAGEREF', 0x25),
        ('ASK', 0x26),
        ('FILLIN', 0x27),
        ('DATA', 0x28),
        ('NEXT', 0x29),
        ('NEXTIF', 0x2A),
        ('SKIPIF', 0x2B),
        ('MERGEREC', 0x2C),
        ('DDE', 0x2D),
        ('DDEAUTO', 0x2E),
        ('GLOSSARY', 0x2F),
        ('PRINT', 0x30),
        ('EQ', 0x31),
        ('GOTOBUTTON', 0x32),
        ('MACROBUTTON', 0x33),
        ('AUTONUMOUT', 0x34),
        ('AUTONUMLGL', 0x35),
        ('AUTONUM', 0x36),
        ('IMPORT', 0x37),
        ('LINK', 0x38),
        ('SYMBOL', 0x39),
        ('EMBED', 0x3A),
        ('MERGEFIELD', 0x3B),
        ('USERNAME', 0x3C),
        ('USERINITIALS', 0x3D),
        ('USERADDRESS', 0x3E),
        ('BARCODE', 0x3F),
        ('DOCVARIABLE', 0x40),
        ('SECTION', 0x41),
        ('SECTIONPAGES', 0x42),
        ('INCLUDEPICTURE', 0x43),
        ('INCLUDETEXT', 0x44),
        ('FILESIZE', 0x45),
        ('FORMTEXT', 0x46),
        ('FORMCHECKBOX', 0x47),
        ('NOTEREF', 0x48),
        ('TOA', 0x49),
        ('MERGESEQ', 0x4B),
        ('AUTOTEXT', 0x4F),
        ('COMPARE', 0x50),
        ('ADDIN', 0x51),
        ('FORMDROPDOWN', 0x53),
        ('ADVANCE', 0x54),
        ('DOCPROPERTY', 0x55),
        ('CONTROL', 0x57),
        ('HYPERLINK', 0x58),
        ('AUTOTEXTLIST', 0x59),
        ('LISTNUM', 0x5A),
        ('HTMLCONTROL', 0x5B),
        ('BIDIOUTLINE', 0x5C),
        ('ADDRESSBLOCK', 0x5D),
        ('GREETINGLINE', 0x5E),
        ('SHAPE', 0x5F),
    ]

# XXX: Atomic types

## Primitive Types
class FcLcb(pstruct.type):
    def __fc(self):
        if not isinstance(getattr(self, '_object_', None), tuple):
            return FC

        # FIXME: this should be a pointer type that correctly handles all this stuff

        # extract the stream name and the structure
        stream, type = self._object_

        # figure out the name of the Table stream
        fib = self.getparent(Fib)
        table = "{:d}Table".format(fib['base']['b']['fWhichTblStm'])

        # grab the stream entry
        D = self.getparent(storage.Directory)
        entry = D.byname(table if stream == 'Table' else stream)

        # now we can somehow transition to the type within the specified stream
        def newtype(self, type=type, entry=entry):
            res, source = self.getparent(FcLcb).li, ptypes.provider.proxy(entry.Data())
            return dyn.block(res['lcb'].int(), source=source) if type is None else dyn.clone(type, blocksize=(lambda _, cb=res['lcb'].int(): cb), source=source)
        return dyn.pointer(newtype)

    _fields_ = [
        (__fc, 'fc'),      # offset
        (pint.uint32_t, 'lcb'),     # size
    ]
    def summary(self):
        return "fc={:#x} lcb={:+#x}".format(self['fc'].int(), self['lcb'].int())

class FILETIME(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'dwLowDateTime'),
        (pint.uint32_t, 'dwHighDateTime')
    ]
    def timestamp(self):
        low, high = self['dwLowDateTime'].int(), self['dwHighDateTime'].int()
        return high * 0x100000000 | + low
    def datetime(self):
        epoch = datetime.datetime(1601, 1, 1)
        return epoch + datetime.timedelta(microseconds=self.timestamp() / 10.0)
    def summary(self):
        epoch, ts = datetime.datetime(1601, 1, 1), self.timestamp()
        ts_s, ts_hns = ts // 1e7, ts % 1e7
        ts_ns = ts_hns * 1e-7

        res = epoch + datetime.timedelta(seconds=ts_s)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:s} ({:#x})".format(res.year, res.month, res.day, res.hour, res.minute, "{:02.9f}".format(res.second + ts_ns).zfill(12), ts)

class DTTM(pbinary.struct):
    _fields_ = rl(
        (3, 'wdy'),
        (9, 'yr'),
        (4, 'mon'),
        (5, 'dom'),
        (5, 'hr'),
        (6, 'mint'),
    )

class _Copts60(pbinary.flags):
    _fields_ = rl(
        (1, 'fNoTabForInd'),
        (1, 'fNoSpaceRaiseLower'),
        (1, 'fSuppressSpBfAfterPgBrk'),
        (1, 'fWrapTrailSpaces'),
        (1, 'fMapPrintTextColor'),
        (1, 'fNoColumnBalance'),
        (1, 'fConvMailMergeEsc'),
        (1, 'fSuppressTopSpacing'),
        (1, 'fOrigWordTableRules'),
        (1, 'unused14'),
        (1, 'fShowBreaksInFrames'),
        (1, 'fSwapBordersFacingPgs'),
        (1, 'fLeaveBackslashAlone'),
        (1, 'fExpShRtn'),
        (1, 'fDntULTrlSpc'),
        (1, 'fDntBlnSbDbWid'),
    )
class Copts60(_Copts60): pass

class _Copts80(pbinary.flags):
    _fields_ = rl(
        (1, 'fSuppressTopSpacingMac5'),
        (1, 'fTruncDxaExpand'),
        (1, 'fPrintBodyBeforeHdr'),
        (1, 'fNoExtLeading'),
        (1, 'fDontMakeSpaceForUL'),
        (1, 'fMWSmallCaps'),
        (1, 'f2ptExtLeadingOnly'),
        (1, 'fTruncFontHeight'),
        (1, 'fSubOnSize'),
        (1, 'fLineWrapLikeWord6'),
        (1, 'fWW6BorderRules'),
        (1, 'fExactOnTop'),
        (1, 'fExtraAfter'),
        (1, 'fWPSpace'),
        (1, 'fWPJust'),
        (1, 'fPrintMet'),
    )

class Copts80(pstruct.type):
    _fields_ = [
        (Copts60, 'copts60'),
        (_Copts80, 'copts80'),
    ]

class _Copts(pbinary.flags):
    _fields_ = rl(
        (1, 'fSpLayoutLikeWW8'),
        (1, 'fFtnLayoutLikeWW8'),
        (1, 'fDontUseHTMLParagraphAutoSpacing'),
        (1, 'fDontAdjustLineHeightInTable'),
        (1, 'fForgetLastTabAlign'),
        (1, 'fUseAutospaceForFullWidthAlpha'),
        (1, 'fAlignTablesRowByRow'),
        (1, 'fLayoutRawTableWidth'),
        (1, 'fLayoutTableRowsApart'),
        (1, 'fUseWord97LineBreakingRules'),
        (1, 'fDontBreakWrappedTables'),
        (1, 'fDontSnapToGridInCell'),
        (1, 'fDontAllowFieldEndSelect'),
        (1, 'fApplyBreakingRules'),
        (1, 'fDontWrapTextWithPunct'),
        (1, 'fDontUseAsianBreakRules'),
        (1, 'fUseWord2002TableStyleRules'),
        (1, 'fGrowAutoFit'),
        (1, 'fUseNormalStyleForList'),
        (1, 'fDontUseIndentAsNumberingTabStop'),
        (1, 'fFELineBreak11'),
        (1, 'fAllowSpaceOfSameStyleInTable'),
        (1, 'fWW11IndentRules'),
        (1, 'fDontAutofitConstrainedTables'),
        (1, 'fAutofitLikeWW11'),
        (1, 'fUnderlineTabInNumList'),
        (1, 'fHangulWidthLikeWW11'),
        (1, 'fSplitPgBreakAndParaMark'),
        (1, 'fDontVertAlignCellWithSp'),
        (1, 'fDontBreakConstrainedForcedTables'),
        (1, 'fDontVertAlignInTxbx'),
        (1, 'fWord11KerningPairs'),
        (1, 'fCachedColBalance'),
        (31, 'empty1'),
    )

class Copts(pstruct.type):
    _fields_ = [
        (_Copts60, 'copts60'),
        (_Copts80, 'copts80'),
        (_Copts, 'copts'),
        (pint.uint32_t, 'empty2'),
        (pint.uint32_t, 'empty3'),
        (pint.uint32_t, 'empty4'),
        (pint.uint32_t, 'empty5'),
        (pint.uint32_t, 'empty6'),
    ]

class DopTypography(pstruct.type):
    class _b(pbinary.flags):
        class _iJustification(pbinary.enum):
            _width_, _values_ = 2, [
                ('doNotCompress', 0),
                ('compressPunctuation', 1),
                ('compressPunctuationAndJapaneseKana', 2),
            ]
        class _iLevelOfKinsoku(pbinary.enum):
            _width_, _values_ = 2, [
                # FIXME
                ('forbidSpecifiedPunctuation', 2),
            ]
        class _iCustomKsu(pbinary.enum):
            _width_, _values_ = 3, [
                ('No language', 0),
                ('Japanese', 1),
                ('Chinese (simplified)', 2),
                ('Korean', 3),
                ('Chinese (traditional)', 4),
            ]
        _fields_ = rl(
            (1, 'fKerningPunct'),
            (_iJustification, 'iJustification'),
            (_iLevelOfKinsoku, 'iLevelOfKinsoku'),
            (1, 'f2on1'),
            (1, 'unused'),
            (_iCustomKsu, 'iCustomKsu'),
            (1, 'fJapeneseUseLevel2'),
            (5, 'reserved'),
        )
    _fields_ = [
        (_b, 'b'),
        (pint.uint16_t, 'cchFollowingPunct'),
        (pint.uint16_t, 'cchLeadingPunct'),
        # FIXME: the previous 2 uint16_t should be used for the following
        #        2 arrays, but the specs set them to a static size.
        (dyn.clone(pstr.wstring, length=202 // 2), 'rgxchFPunct'),
        (dyn.clone(pstr.wstring, length=102 // 2), 'rgxchLPunct'),
    ]

class Dogrid(pstruct.type):
    class _b(pbinary.flags):
        _fields_ = rl(
            (7, 'dyGridDisplay'),
            (1, 'unused'),
            (7, 'dxGridDisplay'),
            (1, 'fFollowMargins'),
        )
    _fields_ = [
        (XAS_nonNeg, 'xaGrid'),
        (YAS_nonNeg, 'yaGrid'),
        (XAS_nonNeg, 'dxaGrid'),
        (YAS_nonNeg, 'dyaGrid'),
        (_b, 'b'),
    ]

class Asumyi(pstruct.type):
    class _b(pbinary.flags):
        class _iViewBy(pbinary.enum):
            _width_, _values_ = 2, [
                ('highlight-summary', 0),
                ('hide-non-summary', 0),
                ('insert-summary', 0),
                ('create-document', 0),
            ]
        _fields_ = rl(
            (1, 'fValid'),
            (1, 'fView'),
            (_iViewBy, 'iViewBy'),
            (1, 'fUpdateProps'),
            (11, 'reserved'),
        )
    class _wDlgLevel(pint.enum, pint.uint16_t):
        _values_ = [
            ('10 sentences.', 0xFFFE),
            ('20 sentences.', 0xFFFD),
            ('100 words.', 0xFFFC),
            ('500 words.', 0xFFFB),
            ('10 percent of the original document size.', 0xFFFA),
            ('25 percent of the original document size.', 0xFFF9),
            ('50 percent of the original document size.', 0xFFF8),
            ('75 percent of the original document size.', 0xFFF7),
        ]
    _fields_ = [
        (_b, 'b'),
        (_wDlgLevel, 'wDlgLevel'),
        (pint.uint32_t, 'IHighestLevel'),
        (pint.uint32_t, 'ICurrentLevel'),
    ]

class PropRMark(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'fPropRMark'),
        (pint.sint16_t, 'ibstshort'),
        (DTTM, 'dttm'),
    ]

class XST(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cch'),
        (lambda self: dyn.clone(pstr.wstring, length=self['cch'].li.int()), 'rgtchar'),
    ]

class Shd(pstruct.type):
    _fields_ = [
        (COLORREF, 'cvFore'),
        (COLORREF, 'cvBack'),
        (Ipat, 'ipat'),
    ]

class Brc(pstruct.type):
    class _b(pbinary.flags):
        _fields_ = rl(
            (5, 'dptSpace'),
            (1, 'fShadow'),
            (9, 'fReserved'),
        )
    _fields_ = [
        (COLORREF, 'cv'),
        (pint.uint8_t, 'dptLineWidth'),
        (BrcType, 'brcType'),
        (_b, 'b'),
    ]

class UFEL(pbinary.flags):
    class _iWarichuBracket(pbinary.enum):
        _width_, _values_ = 3, [
            (0, 'No brackets'),
            (1, 'Round brackets'),
            (2, 'Square brackets'),
            (3, 'Angle brackets'),
            (4, 'Curly brackets'),
        ]

    _fields_ = rl(
        (1, 'fTNY'),
        (1, 'fWarichu'),
        (1, 'fKumimoji'),
        (1, 'fRuby'),
        (1, 'FLSFitText'),
        (1, 'fVRuby'),
        (2, 'spare1'),
        (_iWarichuBracket, 'iWarichuBracket'),
        (1, 'fWarichuNoOpenBracket'),
        (1, 'fTNYCompress'),
        (1, 'fTNYFetchTxm'),
        (1, 'fCellFitText'),
        (1, 'spare2'),
    )

class PChgTabsDel(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'cTabs'),
        (lambda self: dyn.array(XAS, self['cTabs'].li.int()), 'rgdxaDel'),
    ]

class PChgTabsAdd(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'cTabs'),
        (lambda self: dyn.array(XAS, self['cTabs'].li.int()), 'rgdxaAdd'),
        (lambda self: dyn.clone(pbinary.array, _object_=TBD, length=self['cTabs'].li.int()), 'rgtbdAdd'),
    ]

class PChgTabsDelClose(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'cTabs'),
        (lambda self: dyn.array(pint.sint16_t, self['cTabs'].li.int()), 'rgdxaDel'),
        (lambda self: dyn.array(XAS_plusOne, self['cTabs'].li.int()), 'rgdxaClose'),
    ]

class NumRM(pstruct.type):
    _fields_ = [
        (Bool8, 'fNumRM'),
        (Bool8, 'fIgnored'),
        (pint.uint16_t, 'lbstNumRM'),
        (DTTM, 'dttmNumRM'),
        (dyn.array(BYTE, 9), 'rgbxchNums'),
        (dyn.array(MSONFC, 9), 'rgnfc'),
        (pint.uint16_t, 'ignored'),
        (dyn.array(LONG, 9), 'pnbr'),
        (dyn.array(USHORT, 32), 'xst'),
    ]

class Brc80(pbinary.struct):
    class _b(pbinary.flags):
        _fields_ = rl(
            (5, 'dptSpace'),
            (1, 'fShadow'),
            (1, 'fFrame'),
            (1, 'reserved'),
        )

    _fields_ = rl(
        (8, 'dptLineWidth'),
        (_BrcType, 'brcType'),
        (Ico, 'ico'),
        (_b, 'b'),
    )

class Brc80MayBeNil(dynamic.union):
    _value_ = pint.uint32_t
    class _nil(pint.enum, pint.uint32_t):
        _values_ = [('Nil', 0xffffffff)]

    _fields_ = [
        (Brc80, 'brc'),
        (_nil, 'nil'),
    ]

class TCGRF(pbinary.flags):
    class _horzMerge(pbinary.enum):
        _width_, _values_ = 2, [
            ('unmerged', 0),
            ('horizontal', 1),
            ('consecutive', 2),
            ('consecutive2', 3), # ???
        ]

    _fields_ = rl(
        (_horzMerge, 'horzMerge'),
        (_TextFlow, 'textFlow'),
        (_VerticalMergeFlag, 'vertMerge'),
        (_VerticalAlign, 'vertAlign'),
        (_Fts, 'ftsWidth'),
        (1, 'fFitText'),
        (1, 'fNoWrap'),
        (1, 'fHideMark'),
        (1, 'fUnused'),
    )

class TC80(pstruct.type):
    _fields_ = [
        (TCGRF, 'tcgrf'),
        (pint.uint16_t, 'wWidth'),
        (Brc80MayBeNil, 'brcTop'),
        (Brc80MayBeNil, 'brcLeft'),
        (Brc80MayBeNil, 'brcBottom'),
        (Brc80MayBeNil, 'brcRight'),
    ]

class Shd80(pbinary.struct):
    _fields_ = [
        (_Ico, 'icoFore'),
        (_Ico, 'icoBack'),
        (_Ipat, 'ipat'),
    ]

# XXX: Primitive types

## Property Operand Types
class SprmOperandType(ptype.definition): cache = {}
class SprmOperandType(SprmOperandType):
    @SprmOperandType.define(type=0)
    class Toggle(pint.enum, pint.uint8_t):
        _values_ = [('OFF', 0), ('ON', 1), ('MATCH', 128)]

    @SprmOperandType.define(type=1)
    class Byte(pint.uint8_t): pass

    @SprmOperandType.define(type=2)
    @SprmOperandType.define(type=4)
    @SprmOperandType.define(type=5)
    class Word(pint.uint16_t): pass

    @SprmOperandType.define(type=3)
    class Dword(pint.uint32_t): pass

    @SprmOperandType.define(type=6)
    class Variable(pstruct.type):
        def __extra(self):
            cb, res = self['cb'].li.int(), self['operand'].li.size()
            if cb - res >= 0:
                return dyn.block(cb - res)
            cls = self.__class__
            logging.warn("{:s}: Variable operand size ({:d}) is larger than specified size ({:d}): {:s}".format('.'.join((cls.__module__, cls.__name__)), res, cb, self.instance()))
            return dyn.block(0)

        _fields_ = [
            (pint.uint8_t, 'cb'),
            (lambda self: getattr(self, 'operand', ptype.undefined), 'operand'),
            (__extra, 'extra'),
        ]

    @SprmOperandType.define(type=7)
    class Triple(pint.uint_t): length=3

## Properties
class Sprm_Enumeration(pint.enum, pint.uint16_t): pass
class Sprm_Unpacked(pbinary.struct):
    class _sgc(pbinary.enum):
        _width_, _values_ = 3, [
            ('paragraph', 1),
            ('character', 2),
            ('picture', 3),
            ('section', 4),
            ('table', 5),
        ]

    class _spra(pbinary.enum):
        _width_, _values_ = 3, [(cls.__name__, ti) for ti, cls in SprmOperandType.cache.items()]

    _fields_ = [
        (_spra, 'spra'),
        (_sgc, 'sgc'),
        (1, 'fSpec'),
        (9, 'ispmd'),
    ]

    def summary(self):
        spra, sgc = (self.__field__(fld) for fld in ('spra', 'sgc'))
        return "spra={:s} sgc={:s} fSpec={:d} ispmd={:d}".format(spra.str(), sgc.str(), self['fSpec'], self['ispmd'])

class Sprm(dynamic.union):
    _value_ = pint.uint16_t
    _fields_ = [
        (Sprm_Enumeration, 'enumeration'),
        (Sprm_Unpacked, 'unpacked'),
    ]

    def summary(self):
        e = self['enumeration']
        return "{:s} : {:s}".format(e.summary(), self['unpacked'].summary())

class SprmOperandValue(ptype.definition): cache = {}
class SprmOperandValue(SprmOperandValue):
    # FIXME: these values can be consolidated into just one type
    @SprmOperandValue.define(type=0)
    class Toggle(ptype.definition): cache = {}
    @SprmOperandValue.define(type=1)
    class Byte(ptype.definition): cache = {}
    @SprmOperandValue.define(type=2)
    class Word(ptype.definition): cache = {}
    @SprmOperandValue.define(type=3)
    class Dword(ptype.definition): cache = {}
    @SprmOperandValue.define(type=4)
    class Word2(ptype.definition): cache = {}
    @SprmOperandValue.define(type=5)
    class Word3(ptype.definition): cache = {}
    @SprmOperandValue.define(type=6)
    class Variable(ptype.definition): cache = {}
    @SprmOperandValue.define(type=7)
    class Triple(ptype.definition): cache = {}

class Prl(pstruct.type):
    def __operand(self):
        res = self['sprm']['unpacked']['spra']
        # FIXME: lookup the correct operand type
        return SprmOperandType.lookup(res)

    _fields_ = [
        (Sprm, 'sprm'),
        (__operand, 'operand'),
    ]

## For calculating CP
class PLC(ptype.base):
    def blocksize(self):
        raise NotImplementedError

class FcCompressed(pbinary.struct):
    _fields_ = rl(
        (30, 'fc'),
        (1, 'fCompressed'),
        (1, 'r1'),
    )
    def fc(self):
        fc = self['fc']
        return fc // 2 if self.fCompressedQ() else fc
    def fCompressedQ(self):
        return True if self['fCompressed'] else False
    def summary(self):
        return "fCompressed={:d} r1={:d} fc={:#x} : offset -> {:#x}".format(self['fCompressed'], self['r1'], self['fc'], self.fc())

class Prm0(pbinary.struct):
    class _isprm(pbinary.enum):
        _width_, _values_ = 7, [
            ('sprmCLbcCRJ', 0x00),
            ('sprmPIncLvl', 0x04),
            ('sprmPJc', 0x05),
            ('sprmPFKeep', 0x07),
            ('sprmPFKeepFollow', 0x08),
            ('sprmPFPageBreakBefore', 0x09),
            ('sprmPIlvl', 0x0C),
            ('sprmPFMirrorIndents', 0x0D),
            ('sprmPFNoLineNumb', 0x0E),
            ('sprmPTtwo', 0x0F),
            ('sprmPFInTable', 0x18),
            ('sprmPFTtp', 0x19),
            ('sprmPPc', 0x1D),
            ('sprmPWr', 0x25),
            ('sprmPFNoAutoHyph', 0x2C),
            ('sprmPFLocked', 0x32),
            ('sprmPFWidowControl', 0x33),
            ('sprmPFKinsoku', 0x35),
            ('sprmPFWordWrap', 0x36),
            ('sprmPFOverflowPunct', 0x37),
            ('sprmPFTopLinePunct', 0x38),
            ('sprmPFAutoSpaceDE', 0x39),
            ('sprmPFAutoSpaceDN', 0x3A),
            ('sprmCFRMarkDel', 0x41),
            ('sprmCFRMarkIns', 0x42),
            ('sprmCFFldVanish', 0x43),
            ('sprmCFData', 0x47),
            ('sprmCFOle2', 0x4B),
            ('sprmCHighlight', 0x4D),
            ('sprmCFEmboss', 0x4E),
            ('sprmCSfxText', 0x4F),
            ('sprmCFWebHidden', 0x50),
            ('sprmCFSpecVanish', 0x51),
            ('sprmCPlain', 0x53),
            ('sprmCFBold', 0x55),
            ('sprmCFItalic', 0x56),
            ('sprmCFStrike', 0x57),
            ('sprmCFOutline', 0x58),
            ('sprmCFShadow', 0x59),
            ('sprmCFSmallCaps', 0x5A),
            ('sprmCFCaps', 0x5B),
            ('sprmCFVanish', 0x5C),
            ('sprmCKul', 0x5E),
            ('sprmCIco', 0x62),
            ('sprmCIss', 0x68),
            ('sprmCFDStrike', 0x73),
            ('sprmCFImprint', 0x74),
            ('sprmCFSpec', 0x75),
            ('sprmCFObj', 0x76),
            ('sprmPOutLvl', 0x78),
            ('sprmCFSdtVanish', 0x7B),
            ('sprmCNeedFontFixup', 0x7C),
            ('sprmPFNumRMIns', 0x7E),
        ]
    _fields_ = rl(
        (1, 'fComplex'),
        (_isprm, 'isprm'),
        (8, 'val'),
    )
    def summary(self):
        res, sprm = self['val'], self.__field__('isprm')
        return "fComplex={:d} : isprm={:s} val={:d} ({:#x})".format(self['fComplex'], sprm.str(), res, res)

class Prm1(pbinary.struct):
    _fields_ = rl(
        (1, 'fComplex'),
        (15, 'igrpprl'),
    )
    def summary(self):
        res = self['igrpprl']
        return "fComplex={:d} : igrpprl={:d} ({:#x})".format(self['fComplex'], res, res)

class Prm(dynamic.union):
    class _value_(pbinary.struct):
        _fields_ = rl(
            (1, 'fComplex'),
            (15, 'data'),
        )
    _fields_ = [
        (Prm0, 'prm0'),
        (Prm1, 'prm1'),
    ]

    def prm(self):
        return self['prm1' if self.o['fComplex'] else 'prm0']

    def summary(self):
        res = self.prm()
        return "{:s} {!r} : {:s}".format(res.instance(), res.name(), res.summary())

class Sepx(pstruct.type):
    _fields_ = [
        (pint.sint16_t, 'cb'),
        (lambda self: dyn.blockarray(Prl, self['cb'].li.int()), 'grpprl'),
    ]

class Pcd(pstruct.type):
    class _b(pbinary.flags):
        _fields_ = rl(
            (1, 'fNoParaLast'),
            (1, 'fR1'),
            (1, 'fDirty'),
            (13, 'fR2'),
        )
    _fields_ = [
        (_b, 'b'),
        (FcCompressed, 'fc'),
        (Prm, 'prm'),
    ]

    def fc(self):
        return self['fc'].fc()

    def fCompressedQ(self):
        return self['fc'].fCompressedQ()

    def prm(self):
        return self['prm'].prm()

    def properties(self):
        fc, res = self.fc(), super(Pcd, self).properties()
        res['FC'] = fc
        if isinstance(self.parent, parray.type):
            container = self.parent

            try: idx = int(self.name())
            except ValueError: idx = container.index(self)

            if idx + 1 < len(container):
                res['deltaFC'] = container[idx + 1].fc() - fc
            return res
        return res

class PrcData(pstruct.type):
    clxt = 0x01
    _fields_ = [
        (pint.sint16_t, 'cbGrpprl'),
        (lambda self: dyn.array(Prl, self['cbGrpprl'].li.int()), 'GrpPrl'),
    ]
class Prc(PrcData): pass

class PlcPcd(PLC, pstruct.type):
    #def __aCP(self):
    #    D = self.getparent(storage.Directory)
    #    entry = D.byname('WordDocument')
    #    document = entry.Data(File).li

    #    fib = document['fib']
    #    rglw95 = fib['fibRgLw']['95']
    #    ccpText, ccps = rglw95['ccpText'].li.int(), rglw95.SumCCP()

    #    class _aCP(parray.terminated):
    #        _object_ = CP
    #        def isTerminator(self, value):
    #            res = ccps if ccps > 0 else ccpText
    #            return value.int() >= res
    #    return _aCP

    def __aCP(self):
        cp, res = CP().blocksize(), Pcd().a.blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(Pcd, self.blocksize() - self['aCP'].li.size()), 'aPcd'),
    ]

class Pcdt(pstruct.type):
    clxt = 0x02
    _fields_ = [
        (pint.uint32_t, 'lcb'),
        (lambda self: dyn.clone(PlcPcd, blocksize=(lambda _, cb=self['lcb'].li.int(): cb)), 'PlcPcd'),
    ]

class Clx(PLC, pstruct.type):
    class _clxt(pint.enum, pint.uint8_t):
        _values_ = [
            ('RgPrc', 0x01),
            ('Pcdt', 0x02),
        ]
    _fields_ = [
        (pint.uint8_t, 'clxt'),
        (lambda self: PrcData if self['clxt'].li.int() == 0x01 else ptype.undefined, 'RgPrc'),
        (lambda self: Pcdt if self['clxt'].li.int() == 0x02 else ptype.undefined, 'Pcdt'),
    ]

class Plcfhdd(PLC, pstruct.type):
    def __aCP(self):
        items = self.blocksize() // CP().blocksize()
        return dyn.clone(parray.type, _object_=CP, length=items)

    _fields_ = [
        (__aCP, 'aCP'),
    ]

class grffldEnd(pbinary.flags):
    _fields_ = rl(
        (1, 'fDiffer'),
        (1, 'fZombieEmbed'),
        (1, 'fResultsDirty'),
        (1, 'fResultsEdited'),
        (1, 'fLocked'),
        (1, 'fPrivateResult'),
        (1, 'fNested'),
        (1, 'fHasSep'),
    )

class Fld(pstruct.type):
    class _fldch(pint.enum, pint.uint8_t):
        _values_ = [
            ('flt', 0x13),
            ('unused', 0x14),
            ('grffldEnd', 0x15),
        ]

    def __grffld(self):
        res = self['fldch'].li.int()
        if res == 0x13:
            return flt
        elif res == 0x15:
            return grffldEnd
        return pint.uint8_t

    _fields_ = [
        (_fldch, 'fldch'),
        (__grffld, 'grffld'),
    ]

class PlcFld(PLC, pstruct.type):

    def __aCP(self):
        cp, res = CP().blocksize(), Fld().a.blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(Fld, self.blocksize() - self['aCP'].li.size()), 'aFld'),
    ]

class PlcfFldMom(PlcFld): pass
class PlcfFldHdr(PlcFld): pass
class PlcfFldFtn(PlcFld): pass
class PlcfFldAtn(PlcFld): pass
class PlcfFldEdn(PlcFld): pass
class PlcfFldTxbx(PlcFld): pass
class PlcfFldHdrTxbx(PlcFld): pass

class Sed(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'fn'),
        (pint.sint32_t, 'fcSepx'),
        (pint.uint16_t, 'fnMpr'),
        (pint.uint32_t, 'fcMpr'),
    ]

class PlcfSed(PLC, pstruct.type):
    def __aCP(self):
        cp, res = CP().blocksize(), Sed().a.blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(Sed, self.blocksize() - self['aCP'].li.size()), 'aSed'),
    ]

class BKC(pbinary.flags):
    _fields_ = rl(
        (7, 'itcFirst'),
        (1, 'fPub'),
        (6, 'itcLim'),
        (1, 'fNative'),
        (1, 'fCol'),
    )

class FBKF(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'lbkl'),
        (BKC, 'bkc'),
    ]

class Plcfbkf(PLC, pstruct.type):
    def __aCP(self):
        cp, res = CP().blocksize(), FBKF().a.blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(FBKF, self.blocksize() - self['aCP'].li.size()), 'aSed'),
    ]

class PlcfendRef(PLC, pstruct.type):
    #def __aCP(self):
    #    D = self.getparent(storage.Directory)
    #    entry = D.byname('WordDocument')
    #    document = entry.Data(File).li

    #    fib = document['fib']
    #    rglw95 = fib['fibRgLw']['95']
    #    ccpText = rglw95['ccpText'].li.int()

    #    class _aCP(parray.terminated):
    #        _object_ = CP
    #        def isTerminator(self, value):
    #            return value.int() >= ccpText
    #    return _aCP

    def __aCP(self):
        cp, res = CP().blocksize(), pint.uint16_t().blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(pint.uint16_t, self.blocksize() - self['aCP'].li.size()), 'aEndIdx'),
    ]

class PlcffndRef(PLC, pstruct.type):
    #def __aCP(self):
    #    D = self.getparent(storage.Directory)
    #    entry = D.byname('WordDocument')
    #    document = entry.Data(File).li

    #    fib = document['fib']
    #    rglw95 = fib['fibRgLw']['95']
    #    ccpText = rglw95['ccpText'].li.int()

    #    class _aCP(parray.terminated):
    #        _object_ = CP
    #        def isTerminator(self, value):
    #            return value.int() >= ccpText
    #    return _aCP

    def __aCP(self):
        cp, res = CP().blocksize(), pint.uint16_t().blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=CP, length=items + 1)

    _fields_ = [
        (__aCP, 'aCP'),
        (lambda self: dyn.blockarray(pint.uint16_t, self.blocksize() - self['aCP'].li.size()), 'aFtnIdx'),
    ]

class PlcffndTxt(PLC, pstruct.type):
    #def __aCP(self):
    #    D = self.getparent(storage.Directory)
    #    entry = D.byname('WordDocument')
    #    document = entry.Data(File).li

    #    fib = document['fib']
    #    rglw95 = fib['fibRgLw']['95']
    #    ccpFtn = rglw95['ccpFtn'].li.int()

    #    class _aCP(parray.terminated):
    #        _object_ = CP
    #        def isTerminator(self, value):
    #            return value.int() >= ccpFtn
    #    return _aCP

    def __aCP(self):
        items = self.blocksize() // CP().blocksize()
        return dyn.clone(parray.type, _object_=CP, length=items)

    _fields_ = [
        (__aCP, 'aCP'),
    ]

class PlcfendTxt(PLC, pstruct.type):
    #def __aCP(self):
    #    D = self.getparent(storage.Directory)
    #    entry = D.byname('WordDocument')
    #    document = entry.Data(File).li

    #    fib = document['fib']
    #    rglw95 = fib['fibRgLw']['95']
    #    ccpEdn = rglw95['ccpEdn'].li.int()

    #    class _aCP(parray.terminated):
    #        _object_ = CP
    #        def isTerminator(self, value):
    #            return value.int() >= ccpEdn
    #    return _aCP

    def __aCP(self):
        items = self.blocksize() // CP().blocksize()
        return dyn.clone(parray.type, _object_=CP, length=items)

    _fields_ = [
        (__aCP, 'aCP'),
    ]

class SttbfBkmk(pstruct.type):
    class _Data(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'cchData'),
            (lambda self: dyn.clone(pstr.string, length=self['cchData'].li.int()), 'cchData'),
        ]
    _fields_ = [
        (pint.uint16_t, 'fExtend'),
        (pint.uint16_t, 'cData'),
        (pint.uint16_t, 'cbExtra'),
        (lambda self: dyn.array(_Data, self['cData'].li.int()), 'Data'),
        (lambda self: dyn.block(self['cbExtra'].li.int()), 'extraData'),
    ]

class _PnFkp(pbinary.struct):
    _fields_ = rl(
        (22, 'pn'),
        (10, 'unused'),
    )
class PnFkpPapx(_PnFkp): pass
class PnFkpChpx(_PnFkp): pass

class PlcfBtePapx(PLC, pstruct.type):
    '''Paragraph Properties'''
    _object_ = PnFkpPapx
    def __aFC(self):
        cp, res = FC().blocksize(), PnFkpPapx().blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=FC, length=items + 1)

    _fields_ = [
        (__aFC, 'aFC'),
        (lambda self: dyn.clone(pbinary.blockarray, _object_=PnFkpPapx, blockbits=(lambda _, cb=self.blocksize() - self['aFC'].li.size(): cb * 8)), 'aPnBtePapx'),
    ]

class PlcfBteChpx(PLC, pstruct.type):
    '''Character Properties'''
    _object_ = PnFkpChpx
    def __aFC(self):
        cp, res = FC().blocksize(), PnFkpChpx().blocksize()
        items = (self.blocksize() - cp) // (cp + res)
        return dyn.clone(parray.type, _object_=FC, length=items + 1)

    _fields_ = [
        (__aFC, 'aFC'),
        (lambda self: dyn.clone(pbinary.blockarray, _object_=PnFkpChpx, blockbits=(lambda _, cb=self.blocksize() - self['aFC'].li.size(): cb * 8)), 'aPnBteChpx'),
    ]

class GrpPrlAndIstd(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'istd'),
        (lambda self: dyn.blockarray(Prl, self.blocksize() - self['istd'].li.size()), 'grpprl'),
    ]
class PapxInFkp(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'cb'),
        (lambda self: dyn.clone(GrpPrlAndIstd, blocksize=(lambda _, cb=self['cb'].li.int(): cb * 2)), 'grpprlInPapx'),
    ]
class BxPap(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'bOffset'),  # points to PapxInFkp
        (dyn.block(12), 'reserved'),
    ]
    def bOffset(self):
        return self['bOffset'].int() * 2

## Property enumerations
# https://www.opennet.ru/docs/formats/wword8.html
# https://github.com/jonasfj/libreoffice-writer/blob/master/sw/source/filter/ww8/dump/ww8scan.cxx
Sprm_Enumeration._values_ = [
    ('sprmCFRMarkDel', 0x0800),
    ('sprmCFRMarkIns', 0x0801),
    ('sprmCFFldVanish', 0x0802),
    ('sprmCPicLocation', 0x6A03),
    ('sprmCIbstRMark', 0x4804),
    ('sprmCDttmRMark', 0x6805),
    ('sprmCFData', 0x0806),
    ('sprmCIdslRMark', 0x4807),
    ('sprmCSymbol', 0x6A09),
    ('sprmCFOle2', 0x080A),
    ('sprmCHighlight', 0x2A0C),
    ('sprmCFWebHidden', 0x0811),
    ('sprmCRsidProp', 0x6815),
    ('sprmCRsidText', 0x6816),
    ('sprmCRsidRMDel', 0x6817),
    ('sprmCFSpecVanish', 0x0818),
    ('sprmCFMathPr', 0xC81A),
    ('sprmCIstd', 0x4A30),
    ('sprmCIstdPermute', 0xCA31),
    ('sprmCPlain', 0x2A33),
    ('sprmCKcd', 0x2A34),
    ('sprmCFBold', 0x0835),
    ('sprmCFItalic', 0x0836),
    ('sprmCFStrike', 0x0837),
    ('sprmCFOutline', 0x0838),
    ('sprmCFShadow', 0x0839),
    ('sprmCFSmallCaps', 0x083A),
    ('sprmCFCaps', 0x083B),
    ('sprmCFVanish', 0x083C),
    ('sprmCKul', 0x2A3E),
    ('sprmCDxaSpace', 0x8840),
    ('sprmCIco', 0x2A42),
    ('sprmCHps', 0x4A43),
    ('sprmCHpsPos', 0x4845),
    ('sprmCMajority', 0xCA47),
    ('sprmCIss', 0x2A48),
    ('sprmCHpsKern', 0x484B),
    ('sprmCHresi', 0x484E),
    ('sprmCRgFtc0', 0x4A4F),
    ('sprmCRgFtc1', 0x4A50),
    ('sprmCRgFtc2', 0x4A51),
    ('sprmCCharScale', 0x4852),
    ('sprmCFDStrike', 0x2A53),
    ('sprmCFImprint', 0x0854),
    ('sprmCFSpec', 0x0855),
    ('sprmCFObj', 0x0856),
    ('sprmCPropRMark90', 0xCA57),
    ('sprmCFEmboss', 0x0858),
    ('sprmCSfxText', 0x2859),
    ('sprmCFBiDi', 0x085A),
    ('sprmCFBoldBi', 0x085C),
    ('sprmCFItalicBi', 0x085D),
    ('sprmCFtcBi', 0x4A5E),
    ('sprmCLidBi', 0x485F),
    ('sprmCIcoBi', 0x4A60),
    ('sprmCHpsBi', 0x4A61),
    ('sprmCDispFldRMark', 0xCA62),
    ('sprmCIbstRMarkDel', 0x4863),
    ('sprmCDttmRMarkDel', 0x6864),
    ('sprmCBrc80', 0x6865),
    ('sprmCShd80', 0x4866),
    ('sprmCIdslRMarkDel', 0x4867),
    ('sprmCFUsePgsuSettings', 0x0868),
    ('sprmCRgLid0_80', 0x486D),
    ('sprmCRgLid1_80', 0x486E),
    ('sprmCIdctHint', 0x286F),
    ('sprmCCv', 0x6870),
    ('sprmCShd', 0xCA71),
    ('sprmCBrc', 0xCA72),
    ('sprmCRgLid0', 0x4873),
    ('sprmCRgLid1', 0x4874),
    ('sprmCFNoProof', 0x0875),
    ('sprmCFitText', 0xCA76),
    ('sprmCCvUl', 0x6877),
    ('sprmCFELayout', 0xCA78),
    ('sprmCLbcCRJ', 0x2879),
    ('sprmCFComplexScripts', 0x0882),
    ('sprmCWall', 0x2A83),
    ('sprmCCnf', 0xCA85),
    ('sprmCNeedFontFixup', 0x2A86),
    ('sprmCPbiIBullet', 0x6887),
    ('sprmCPbiGrf', 0x4888),
    ('sprmCPropRMark', 0xCA89),
    ('sprmCFSdtVanish', 0x2A90),
    ('sprmPIstd', 0x4600),
    ('sprmPIstdPermute', 0xC601),
    ('sprmPIncLvl', 0x2602),
    ('sprmPJc80', 0x2403),
    ('sprmPFKeep', 0x2405),
    ('sprmPFKeepFollow', 0x2406),
    ('sprmPFPageBreakBefore', 0x2407),
    ('sprmPIlvl', 0x260A),
    ('sprmPIlfo', 0x460B),
    ('sprmPFNoLineNumb', 0x240C),
    ('sprmPChgTabsPapx', 0xC60D),
    ('sprmPDxaRight80', 0x840E),
    ('sprmPDxaLeft80', 0x840F),
    ('sprmPNest80', 0x4610),
    ('sprmPDxaLeft180', 0x8411),
    ('sprmPDyaLine', 0x6412),
    ('sprmPDyaBefore', 0xA413),
    ('sprmPDyaAfter', 0xA414),
    ('sprmPChgTabs', 0xC615),
    ('sprmPFInTable', 0x2416),
    ('sprmPFTtp', 0x2417),
    ('sprmPDxaAbs', 0x8418),
    ('sprmPDyaAbs', 0x8419),
    ('sprmPDxaWidth', 0x841A),
    ('sprmPPc', 0x261B),
    ('sprmPWr', 0x2423),
    ('sprmPBrcTop80', 0x6424),
    ('sprmPBrcLeft80', 0x6425),
    ('sprmPBrcBottom80', 0x6426),
    ('sprmPBrcRight80', 0x6427),
    ('sprmPBrcBetween80', 0x6428),
    ('sprmPBrcBar80', 0x6629),
    ('sprmPFNoAutoHyph', 0x242A),
    ('sprmPWHeightAbs', 0x442B),
    ('sprmPDcs', 0x442C),
    ('sprmPShd80', 0x442D),
    ('sprmPDyaFromText', 0x842E),
    ('sprmPDxaFromText', 0x842F),
    ('sprmPFLocked', 0x2430),
    ('sprmPFWidowControl', 0x2431),
    ('sprmPFKinsoku', 0x2433),
    ('sprmPFWordWrap', 0x2434),
    ('sprmPFOverflowPunct', 0x2435),
    ('sprmPFTopLinePunct', 0x2436),
    ('sprmPFAutoSpaceDE', 0x2437),
    ('sprmPFAutoSpaceDN', 0x2438),
    ('sprmPWAlignFont', 0x4439),
    ('sprmPFrameTextFlow', 0x443A),
    ('sprmPOutLvl', 0x2640),
    ('sprmPFBiDi', 0x2441),
    ('sprmPFNumRMIns', 0x2443),
    ('sprmPNumRM', 0xC645),
    ('sprmPHugePapx', 0x6646),
    ('sprmPFUsePgsuSettings', 0x2447),
    ('sprmPFAdjustRight', 0x2448),
    ('sprmPItap', 0x6649),
    ('sprmPDtap', 0x664A),
    ('sprmPFInnerTableCell', 0x244B),
    ('sprmPFInnerTtp', 0x244C),
    ('sprmPShd', 0xC64D),
    ('sprmPBrcTop', 0xC64E),
    ('sprmPBrcLeft', 0xC64F),
    ('sprmPBrcBottom', 0xC650),
    ('sprmPBrcRight', 0xC651),
    ('sprmPBrcBetween', 0xC652),
    ('sprmPBrcBar', 0xC653),
    ('sprmPDxcRight', 0x4455),
    ('sprmPDxcLeft', 0x4456),
    ('sprmPDxcLeft1', 0x4457),
    ('sprmPDylBefore', 0x4458),
    ('sprmPDylAfter', 0x4459),
    ('sprmPFOpenTch', 0x245A),
    ('sprmPFDyaBeforeAuto', 0x245B),
    ('sprmPFDyaAfterAuto', 0x245C),
    ('sprmPDxaRight', 0x845D),
    ('sprmPDxaLeft', 0x845E),
    ('sprmPNest', 0x465F),
    ('sprmPDxaLeft1', 0x8460),
    ('sprmPJc', 0x2461),
    ('sprmPFNoAllowOverlap', 0x2462),
    ('sprmPWall', 0x2664),
    ('sprmPIpgp', 0x6465),
    ('sprmPCnf', 0xC666),
    ('sprmPRsid', 0x6467),
    ('sprmPIstdListPermute', 0xC669),
    ('sprmPTableProps', 0x646B),
    ('sprmPTIstdInfo', 0xC66C),
    ('sprmPFContextualSpacing', 0x246D),
    ('sprmPPropRMark', 0xC66F),
    ('sprmPFMirrorIndents', 0x2470),
    ('sprmPTtwo', 0x2471),
    ('sprmTJc90', 0x5400),
    ('sprmTDxaLeft', 0x9601),
    ('sprmTDxaGapHalf', 0x9602),
    ('sprmTFCantSplit90', 0x3403),
    ('sprmTTableHeader', 0x3404),
    ('sprmTTableBorders80', 0xD605),
    ('sprmTDyaRowHeight', 0x9407),
    ('sprmTDefTable', 0xD608),
    ('sprmTDefTableShd80', 0xD609),
    ('sprmTTlp', 0x740A),
    ('sprmTFBiDi', 0x560B),
    ('sprmTDefTableShd3rd', 0xD60C),
    ('sprmTPc', 0x360D),
    ('sprmTDxaAbs', 0x940E),
    ('sprmTDyaAbs', 0x940F),
    ('sprmTDxaFromText', 0x9410),
    ('sprmTDyaFromText', 0x9411),
    ('sprmTDefTableShd', 0xD612),
    ('sprmTTableBorders', 0xD613),
    ('sprmTTableWidth', 0xF614),
    ('sprmTFAutofit', 0x3615),
    ('sprmTDefTableShd2nd', 0xD616),
    ('sprmTWidthBefore', 0xF617),
    ('sprmTWidthAfter', 0xF618),
    ('sprmTFKeepFollow', 0x3619),
    ('sprmTBrcTopCv', 0xD61A),
    ('sprmTBrcLeftCv', 0xD61B),
    ('sprmTBrcBottomCv', 0xD61C),
    ('sprmTBrcRightCv', 0xD61D),
    ('sprmTDxaFromTextRight', 0x941E),
    ('sprmTSetBrc80', 0xD620),
    ('sprmTInsert', 0x7621),
    ('sprmTDelete', 0x5622),
    ('sprmTDxaCol', 0x7623),
    ('sprmTMerge', 0x5624),
    ('sprmTSplit', 0x5625),
    ('sprmTTextFlow', 0x7629),
    ('sprmTVertMerge', 0xD62B),
    ('sprmTVertAlign', 0xD62C),
    ('sprmTSetShd', 0xD62D),
    ('sprmTSetShdOdd', 0xD62E),
    ('sprmTSetBrc', 0xD62F),
    ('sprmTCellPadding', 0xD632),
    ('sprmTCellSpacingDefault', 0xD633),
    ('sprmTCellPaddingDefault', 0xD634),
    ('sprmTCellWidth', 0xD635),
    ('sprmTFitText', 0xF636),
    ('sprmTFCellNoWrap', 0xD639),
    ('sprmTIstd', 0x563A),
    ('sprmTCellPaddingStyle', 0xD63E),
    ('sprmTCellFHideMark', 0xD642),
    ('sprmTSetShdTable', 0xD660),
    ('sprmTWidthIndent', 0xF661),
    ('sprmTCellBrcType', 0xD662),
    ('sprmTFBiDi90', 0x5664),
    ('sprmTFNoAllowOverlap', 0x3465),
    ('sprmTFCantSplit', 0x3466),
    ('sprmTPropRMark', 0xD667),
    ('sprmTWall', 0x3668),
    ('sprmTIpgp', 0x7469),
    ('sprmTCnf', 0xD66A),
    ('sprmTDefTableShdRaw', 0xD670),
    ('sprmTDefTableShdRaw2nd', 0xD671),
    ('sprmTDefTableShdRaw3rd', 0xD672),
    ('sprmTRsid', 0x7479),
    ('sprmTCellVertAlignStyle', 0x347C),
    ('sprmTCellNoWrapStyle', 0x347D),
    ('sprmTCellBrcTopStyle', 0xD47F),
    ('sprmTCellBrcBottomStyle', 0xD680),
    ('sprmTCellBrcLeftStyle', 0xD681),
    ('sprmTCellBrcRightStyle', 0xD682),
    ('sprmTCellBrcInsideHStyle', 0xD683),
    ('sprmTCellBrcInsideVStyle', 0xD684),
    ('sprmTCellBrcTL2BRStyle', 0xD685),
    ('sprmTCellBrcTR2BLStyle', 0xD686),
    ('sprmTCellShdStyle', 0xD687),
    ('sprmTCHorzBands', 0x3488),
    ('sprmTCVertBands', 0x3489),
    ('sprmTJc', 0x548A),
    ('sprmScnsPgn', 0x3000),
    ('sprmSiHeadingPgn', 0x3001),
    ('sprmSDxaColWidth', 0xF203),
    ('sprmSDxaColSpacing', 0xF204),
    ('sprmSFEvenlySpaced', 0x3005),
    ('sprmSFProtected', 0x3006),
    ('sprmSDmBinFirst', 0x5007),
    ('sprmSDmBinOther', 0x5008),
    ('sprmSBkc', 0x3009),
    ('sprmSFTitlePage', 0x300A),
    ('sprmSCcolumns', 0x500B),
    ('sprmSDxaColumns', 0x900C),
    ('sprmSNfcPgn', 0x300E),
    ('sprmSFPgnRestart', 0x3011),
    ('sprmSFEndnote', 0x3012),
    ('sprmSLnc', 0x3013),
    ('sprmSNLnnMod', 0x5015),
    ('sprmSDxaLnn', 0x9016),
    ('sprmSDyaHdrTop', 0xB017),
    ('sprmSDyaHdrBottom', 0xB018),
    ('sprmSLBetween', 0x3019),
    ('sprmSVjc', 0x301A),
    ('sprmSLnnMin', 0x501B),
    ('sprmSPgnStart97', 0x501C),
    ('sprmSBOrientation', 0x301D),
    ('sprmSXaPage', 0xB01F),
    ('sprmSYaPage', 0xB020),
    ('sprmSDxaLeft', 0xB021),
    ('sprmSDxaRight', 0xB022),
    ('sprmSDyaTop', 0x9023),
    ('sprmSDyaBottom', 0x9024),
    ('sprmSDzaGutter', 0xB025),
    ('sprmSDmPaperReq', 0x5026),
    ('sprmSFBiDi', 0x3228),
    ('sprmSFRTLGutter', 0x322A),
    ('sprmSBrcTop80', 0x702B),
    ('sprmSBrcLeft80', 0x702C),
    ('sprmSBrcBottom80', 0x702D),
    ('sprmSBrcRight80', 0x702e),
    ('sprmSPgbProp', 0x522F),
    ('sprmSDxtCharSpace', 0x7030),
    ('sprmSDyaLinePitch', 0x9031),
    ('sprmSClm', 0x5032),
    ('sprmSTextFlow', 0x5033),
    ('sprmSBrcTop', 0xD234),
    ('sprmSBrcLeft', 0xD235),
    ('sprmSBrcBottom', 0xD236),
    ('sprmSBrcRight', 0xD237),
    ('sprmSWall', 0x3239),
    ('sprmSRsid', 0x703A),
    ('sprmSFpc', 0x303B),
    ('sprmSRncFtn', 0x303C),
    ('sprmSRncEdn', 0x303E),
    ('sprmSNFtn', 0x503F),
    ('sprmSNfcFtnRef', 0x5040),
    ('sprmSNEdn', 0x5041),
    ('sprmSNfcEdnRef', 0x5042),
    ('sprmSPropRMark', 0xD243),
    ('sprmSPgnStart', 0x7044),
    ('sprmPicBrcTop80', 0x6C02),
    ('sprmPicBrcLeft80', 0x6C03),
    ('sprmPicBrcBottom80', 0x6C04),
    ('sprmPicBrcRight80', 0x6C05),
    ('sprmPicBrcTop', 0xCE08),
    ('sprmPicBrcLeft', 0xCE09),
    ('sprmPicBrcBottom', 0xCE0A),
    ('sprmPicBrcRight', 0xCE0B),
    ('sprmSOlstAnm', 0xD202),
]

## Property Operand Definitions
class FtsWWidth_Table(pstruct.type):
    _fields_ = [
        (Fts, 'ftsWidth'),
        (pint.sint16_t, 'wWidth'),
    ]

class FtsWWidth_TablePart(pstruct.type):
    _fields_ = [
        (Fts, 'ftsWidth'),
        (pint.sint16_t, 'wWidth'),
    ]

class ItcFirstLim(pstruct.type):
    _fields_ = [
        (pint.sint8_t, 'itcFirst'),
        (pint.sint8_t, 'itcLim'),
    ]

class CellRangeFitText(pstruct.type):
    _fields_ = [
        (ItcFirstLim, 'itc'),
        (Bool8, 'fFitText'),
    ]

class FtsWWidth_Indent(pstruct.type):
    _fields_ = [
        (Fts, 'ftsWidth'),
        (pint.sint16_t, 'wWidth'),
    ]

class SDxaColWidthOperand(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'iCol'),
        (XAS_nonNeg, 'dxaCol'),
    ]

class SDxaColSpacingOperand(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'iCol'),
        (XAS_nonNeg, 'dxaCol'),
    ]

class MathPrOperand(pbinary.flags):
    _fields_ = rl(
        (3, 'jcMath'),
        (13, 'unused'),
    )

class SPPOperand(pstruct.type):
    def __rgIstdPermute(self):
        first, last = self['istdFirst'].li.int(), self['istdLast'].li.int()
        if last >= first:
            return dyn.array(pint.uint16_t, last - first + 1)
        cls = self.__class__
        logging.warn("{:s}: SPPOperand's fields (istdFirst={first:d}, istdLast={first:d}) are not sorted in the correct order. Fixing them to istdFirst={last:d}, istdLast={first:d}.".format('.'.join((cls.__module__, cls.__name__)), first=first, last=last))
        return dyn.array(pint.uint16_t, first - last + 1)

    _fields_ = [
        (pint.uint32_t, 'fLong'),
        (pint.uint16_t, 'istdFirst'),
        (pint.uint16_t, 'istdLast'),
        (__rgIstdPermute, 'rgIstdPermute'),
    ]

class CMajorityOperand(pstruct.type):
    _fields_ = [
        (lambda self: dyn.blockarray(Prl, self.getparent(SprmOperandTable.Variable)['cb'].li.int()), 'grpprl'),
    ]

class PropRMarkOperand(pstruct.type):
    _fields_ = [
        (PropRMark, 'proprmark'),
    ]

class DispFldRmOperand(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'f'),
        (pint.uint16_t, 'ibstshort'),
        (DTTM, 'dttm'),
        (XST, 'xst'),
    ]

class SHDOperand(pbinary.struct):
    _fields_ = [
        (Shd, 'shd'),
    ]

class BrcOperand(pbinary.struct):
    _fields_ = [
        (Brc, 'brc'),
    ]

class FarEastLayoutOperand(pstruct.type):
    _fields_ = [
        (UFEL, 'ufel'),
        (pint.sint32_t, 'IFELayoutID'),
    ]

class CNFOperand(pstruct.type):
    class _cnfc(pint.enum, pint.uint16_t):
        _values_ = [
            ('Header row', 0x0001),
            ('Footer row', 0x0002),
            ('First column', 0x0004),
            ('Last column', 0x0008),
            ('Banded columns', 0x0010),
            ('Even column banding', 0x0020),
            ('Banded rows', 0x0040),
            ('Even row banding', 0x0080),
            ('Top right cell', 0x0100),
            ('Top left cell', 0x0200),
            ('Bottom right cell', 0x0400),
            ('Bottom left cell', 0x0800),
        ]

    _fields_ = [
        (_cnfc, 'cnfc'),
        (lambda self: dyn.blockarray(Prl, self.getparent(SprmOperandTable.Variable)['cb'].li.int() - self['cnfc'].li.size()), 'grpprl'),
    ]

class PChgTabsPapXOperand(pstruct.type):
    _fields_ = [
        (PChgTabsDel, 'PChgTabsDel'),
        (PChgTabsAdd, 'PChgTabsAdd'),
    ]

class PChgTabsOperand(pstruct.type):
    _fields_ = [
        (PChgTabsDelClose, 'PChgTabsDelClose'),
        (PChgTabsAdd, 'PChgTabsAdd'),
    ]

class NumRMOperand(pstruct.type):
    _fields_ = [
        (NumRM, 'numRM'),
    ]

class PTIstdInfoOperand(pstruct.type):
    _fields_ = [
        (dyn.block(16), 'reserved'),
    ]

class TableBordersOperand80(pstruct.type):
    _fields_ = [
        (Brc80MayBeNil, 'brcTop'),
        (Brc80MayBeNil, 'brcLeft'),
        (Brc80MayBeNil, 'brcBottom'),
        (Brc80MayBeNil, 'brcRight'),
        (Brc80MayBeNil, 'brcHorizontalInside'),
        (Brc80MayBeNil, 'brcVerticalInside'),
    ]

class TDefTableOperand(pstruct.type):
    _fields_ = [
        (pint.uint8_t, 'NumberOfColumns'),
        (lambda self: dyn.array(XAS, self['NumberOfColumns'].li.int()), 'rgdxaCenter'),
        (lambda self: dyn.array(TC80, self['NumberOfColumns'].li.int()), 'rgTc80'),
    ]

class DefTableShd80Operand(pstruct.type):
    _fields_ = [
        (lambda self: dyn.blockarray(Shd80, self.getparent(SprmOperandType.Variable)['cb'].li.int()), 'rgShd80'),
    ]

class DefTableShdOperand(pstruct.type):
    _fields_ = [
        (lambda self: dyn.blockarray(Shd, self.getparent(SprmOperandType.Variable)['cb'].li.int()), 'rgShd'),
    ]

class TableBordersOperand(pstruct.type):
    _fields_ = [
        (Brc, 'brcTop'),
        (Brc, 'brcLeft'),
        (Brc, 'brcBottom'),
        (Brc, 'brcRight'),
        (Brc, 'brcHorizontalInside'),
        (Brc, 'brcVerticalInside'),
    ]

class BrcCvOperand(pstruct.type):
    _fields_ = [
        (lambda self: dyn.blockarray(COLORREF, self.getparent(SprmOperandType.Variable)['cb'].li.int()), 'rgcv'),
    ]

class TableBrc80Operand(pstruct.type):
    class _bordersToApply(pint.enum, pint.uint8_t):
        _values_ = [
            ('top', 0x01),
            ('left', 0x02),
            ('bottom', 0x04),
            ('right', 0x08),
        ]
    _fields_ = [
        (ItcFirstLim, 'itc'),
        (_bordersToApply, 'bordersToApply'),
        (Brc80MayBeNil, 'brc'),
    ]

# XXX: Property operand definitions

## Property Operands
@SprmOperandValue.Triple.define(type=0xf614)
class sprmTTableWidth(FtsWWidth_Table): pass
@SprmOperandValue.Triple.define(type=0xf617)
class sprmTWidthBefore(FtsWWidth_TablePart): pass
@SprmOperandValue.Triple.define(type=0xf618)
class sprmTWidthAfter(FtsWWidth_TablePart): pass
@SprmOperandValue.Triple.define(type=0xf618)
class sprmTFitText(CellRangeFitText): pass
@SprmOperandValue.Triple.define(type=0xf661)
class sprmTWidthIndent(FtsWWidth_Indent): pass
@SprmOperandValue.Triple.define(type=0xf203)
class sprmSDxaColWidth(SDxaColWidthOperand): pass
@SprmOperandValue.Triple.define(type=0xf204)
class sprmSDxaColSpacing(SDxaColSpacingOperand): pass
@SprmOperandValue.Variable.define(type=0xc81a)
class sprmCFMathPr(MathPrOperand): pass
@SprmOperandValue.Variable.define(type=0xca31)
class sprmCIstdPermute(SPPOperand): pass
@SprmOperandValue.Variable.define(type=0xca47)
class sprmCMajority(CMajorityOperand): pass
@SprmOperandValue.Variable.define(type=0xca57)
class sprmCPropRMark90(PropRMarkOperand): pass
@SprmOperandValue.Variable.define(type=0xca62)
class sprmCDispFldRMark(DispFldRmOperand): pass
@SprmOperandValue.Variable.define(type=0xca71)
class sprmCShd(SHDOperand): pass
@SprmOperandValue.Variable.define(type=0xca72)
class sprmCBrc(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xca76)
class sprmCFitText(Prl): pass
@SprmOperandValue.Variable.define(type=0xca78)
class sprmCFELayout(FarEastLayoutOperand): pass
@SprmOperandValue.Variable.define(type=0xca85)
class sprmCCnf(CNFOperand): pass
@SprmOperandValue.Variable.define(type=0xca89)
class sprmCPropRMark(PropRMarkOperand): pass
@SprmOperandValue.Variable.define(type=0xc601)
class sprmPIstdPermute(SPPOperand): pass
@SprmOperandValue.Variable.define(type=0xc60d)
class sprmPChgTabsPapx(PChgTabsPapXOperand): pass
@SprmOperandValue.Variable.define(type=0xc615)
class sprmPChgTabs(PChgTabsOperand): pass
@SprmOperandValue.Variable.define(type=0xc645)
class sprmPNumRM(NumRMOperand): pass
@SprmOperandValue.Variable.define(type=0xc64d)
class sprmPShd(SHDOperand): pass
@SprmOperandValue.Variable.define(type=0xc64e)
class sprmPBrcTop(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc64f)
class sprmPBrcLeft(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc650)
class sprmPBrcBottom(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc651)
class sprmPBrcRight(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc652)
class sprmPBrcBetween(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc653)
class sprmPBrcBar(BrcOperand): pass
@SprmOperandValue.Variable.define(type=0xc666)
class sprmPCnf(CNFOperand): pass
@SprmOperandValue.Variable.define(type=0xc669)
class sprmPIstdListPermute(SPPOperand): pass
@SprmOperandValue.Variable.define(type=0xc66c)
class sprmPTIstdInfo(PTIstdInfoOperand): pass
@SprmOperandValue.Variable.define(type=0xc66f)
class sprmPPropRMark(PropRMarkOperand): pass
@SprmOperandValue.Variable.define(type=0xd605)
class sprmTTableBorders80(TableBordersOperand80): pass
@SprmOperandValue.Variable.define(type=0xd608)
class sprmTDefTable(TDefTableOperand): pass
@SprmOperandValue.Variable.define(type=0xd609)
class sprmTDefTableShd80(DefTableShd80Operand): pass
@SprmOperandValue.Variable.define(type=0xd60c)
class sprmTDefTableShd3rd(DefTableShdOperand): pass
@SprmOperandValue.Variable.define(type=0xd612)
class sprmTDefTableShd(DefTableShdOperand): pass
@SprmOperandValue.Variable.define(type=0xd613)
class sprmTTableBorders(TableBordersOperand): pass
@SprmOperandValue.Variable.define(type=0xd616)
class sprmTDefTableShd2nd(DefTableShdOperand): pass
@SprmOperandValue.Variable.define(type=0xd61a)
class sprmTBrcTopCv(BrcCvOperand): pass
@SprmOperandValue.Variable.define(type=0xd61b)
class sprmTBrcLeftCv(BrcCvOperand): pass
@SprmOperandValue.Variable.define(type=0xd61c)
class sprmTBrcBottomCv(BrcCvOperand): pass
@SprmOperandValue.Variable.define(type=0xd61d)
class sprmTBrcRightCv(BrcCvOperand): pass
@SprmOperandValue.Variable.define(type=0xd620)
class sprmTSetBrc80(TableBrc80Operand): pass

# XXX: Property operands (:40)

## Document structures
class DopBase(pstruct.type):
    class _b(pbinary.flags):
        class _fpc(pbinary.enum):
            _width_, _values_ = 2, [
                ('end-of-section', 0),
                ('bottom-margin', 1),
                ('last-line-of-page', 2),
            ]
        class _rncFtn(pbinary.enum):
            _width_, _values_ = 2, [
                ('previous-section', 0),
                ('unique-section', 1),
                ('unique-page', 2),
            ]
        _fields_ = rl(
            (1, 'fFacingPages'),
            (1, 'unused1'),
            (1, 'fPMHMainDoc'),
            (1, 'unused2'),
            (_fpc, 'fpc'),
            (1, 'unused3'),
            (8, 'unused4'),
            (_rncFtn, 'rncFtn'),
            (14, 'nFtn'),
            (1, 'unused5'),
            (1, 'unused6'),
            (1, 'unused7'),
            (1, 'unused8'),
            (1, 'unused9'),
            (1, 'unused10'),
            (1, 'fSplAllDone'),
            (1, 'fSplAllClean'),
            (1, 'fSplHideErrors'),
            (1, 'fGramHideErrors'),
            (1, 'fLabelDoc'),
            (1, 'fHyphCapitals'),
            (1, 'fAutoHyphen'),
            (1, 'fFormNoFields'),
            (1, 'fLinkStyles'),
            (1, 'fRevMarking'),
            (1, 'unused11'),
            (1, 'fExactCWords'),
            (1, 'fPagHidden'),
            (1, 'fPagResults'),
            (1, 'fLockAtn'),
            (1, 'fMirrorMargins'),
            (1, 'fWord97Compat'),
            (1, 'unused12'),
            (1, 'unused13'),
            (1, 'fProtEnabled'),
            (1, 'fDispFormFldSel'),
            (1, 'fRMView'),
            (1, 'fRMPrint'),
            (1, 'fLockVbaProj'),
            (1, 'fLockRev'),
            (1, 'fEmbedFonts'),
        )
    class _b2(pbinary.flags):
        class _rncEdn(pbinary.enum):
            _width_, _values_ = 2, [
                ('previous-section', 0),
                ('unique-section', 1),
                ('unique-page', 2),
            ]
        class _epc(pbinary.enum):
            _width_, _values_ = 2, [
                ('end-of-section', 0),
                ('end-of-document', 3),
            ]
        _fields_ = rl(
            (_rncEdn, 'rncEdn'),
            (14, 'nEdn'),
            (_epc, 'epc'),
            (4, 'unused14'),
            (4, 'unused15'),
            (1, 'fPrintFormData'),
            (1, 'fSaveFormData'),
            (1, 'fShadeFormData'),
            (1, 'fShadeMergeFields'),
            (1, 'reserved2'),
            (1, 'fIncludeSubdocsInStats'),
        )
    class _b3(pbinary.flags):
        class _wvkoSaved(pbinary.enum):
            _width_, _values_ = 3, [
                ('none', 0),
                ('print', 1),
                ('outline', 2),
                ('masterPages', 3),
                ('normal', 4),
                ('web', 5),
            ]
        class _zkSaved(pbinary.enum):
            _width_, _values_ = 2, [
                ('none', 0),
                ('fullPage', 1),
                ('bestFit', 2),
                ('textFit', 3),
            ]
        _fields_ = rl(
            (_wvkoSaved, 'wvkoSaved'),
            (9, 'pctWwdSaved'),
            (_zkSaved, 'zkSaved'),
            (1, 'unused16'),
            (1, 'iGutterPos'),
        )
    _fields_ = [
        (_b, 'b'),
        (Copts60, 'copts60'),
        (pint.uint16_t, 'dxaTab'),
        (pint.uint16_t, 'cpgWebOpt'),
        (pint.uint16_t, 'dxaHotZ'),
        (pint.uint16_t, 'cConsecHypLim'),
        (pint.uint16_t, 'wSpare2'),
        (DTTM, 'dttmCreated'),
        (DTTM, 'dttmRevised'),
        (DTTM, 'dttmLastPrint'),
        (pint.sint16_t, 'nRevision'),
        (pint.sint32_t, 'tmEdited'),
        (pint.sint32_t, 'cWords'),
        (pint.sint32_t, 'cCh'),
        (pint.sint16_t, 'cPg'),
        (pint.sint32_t, 'cParas'),
        (_b2, 'b2'),
        (pint.sint32_t, 'cLines'),
        (pint.sint32_t, 'cWordsWithSubdocs'),
        (pint.sint32_t, 'cChWithSubdocs'),
        (pint.sint16_t, 'cPgWithSubdocs'),
        (pint.sint32_t, 'cParasWithSubdocs'),
        (pint.sint32_t, 'cLinesWithSubdocs'),
        (pint.sint32_t, 'lKeyProtDoc'),
        (_b3, 'b3'),
    ]

class Dop95(pstruct.type):
    _fields_ = [
        (DopBase, 'dopBase'),
        (Copts80, 'copts80'),
    ]

class Dop97(pstruct.type):
    class _adt(pint.enum, pint.uint16_t):
        _values_ = [
            ('notSpecified', 0x0000),
            ('letter', 0x0001),
            ('eMail', 0x0002),
        ]
    class _b(pbinary.flags):
        class _lvlDop(pbinary.enum):
            _width_, _values_ = 4, [
                (                             'Heading 1', 0x0),
                (                      'Headings 1 and 2', 0x1),
                (                   'Headings 1, 2 and 3', 0x2),
                (                'Headings 1, 2, 3 and 4', 0x3),
                (             'Headings 1, 2, 3, 4 and 5', 0x4),
                (          'Headings 1, 2, 3, 4, 5 and 6', 0x5),
                (       'Headings 1, 2, 3, 4, 5, 6 and 7', 0x6),
                (    'Headings 1, 2, 3, 4, 5, 6, 7 and 8', 0x7),
                ('Headings 1, 2, 3, 4, 5 , 6, 7, 8 and 9', 0x8),
                ('All levels', 0x9),
                ('All levels', 0xF),
            ]
        _fields_ = rl(
            (1, 'unused1'),
            (_lvlDop, 'lvlDop'),
            (1, 'fGramAllDone'),
            (1, 'fGramAllClean'),
            (1, 'fSubsetFonts'),
            (1, 'unused2'),
            (1, 'fHtmlDoc'),
            (1, 'fDiskLvcInvalid'),
            (1, 'fSnapBorder'),
            (1, 'fIncludeHeader'),
            (1, 'fIncludeFooter'),
            (1, 'unused3'),
            (1, 'unused4'),
        )
    class _grfDocEvents(pint.enum, pint.uint32_t):
        # FIXME: This should be a pbinary.flags
        _values_ = [
            ('New', 0x00000001),
            ('Open', 0x00000002),
            ('Close', 0x00000004),
            ('Sync', 0x00000008),
            ('XMLAfterInsert', 0x00000010),
            ('XMLBeforeDelete', 0x00000020),
            ('BBAfterInsert', 0x00000100),
            ('BBBeforeDelete', 0x00000200),
            ('BBOnExit', 0x00000400),
            ('BBOnEnter', 0x00000800),
            ('StoreUpdate', 0x00001000),
            ('BBContentUpdate', 0x00002000),
            ('LegoAfterInsert', 0x00004000),
        ]
    class _b2(pbinary.flags):
        _fields_ = rl(
            (1, 'fVirusPrompted'),
            (1, 'fVirusLoadSafe'),
            (30, 'KeyVirusSession30'),
        )
    _fields_ = [
        (Dop95, 'dop95'),
        (_adt, 'adt'),
        (DopTypography, 'doptypography'),
        (Dogrid, 'dogrid'),
        (_b, 'b'),
        (pint.uint16_t, 'unused5'),
        (Asumyi, 'asumyi'),
        (pint.uint32_t, 'cChWS'),
        (pint.uint32_t, 'cChWSWithSubdocs'),
        (_grfDocEvents, 'grfDocEvents'),
        (_b2, 'b2'),
        (dyn.block(30), 'space'),
        (pint.uint32_t, 'cpMaxListcacheMainDoc'),
        (pint.uint16_t, 'ilfoLastBulletMain'),
        (pint.uint16_t, 'ilfoLastNumberMain'),
        (pint.uint32_t, 'cDBC'),
        (pint.uint32_t, 'cDBCWithSubdocs'),
        (pint.uint32_t, 'reserved3a'),
        (MSONFC, 'nfcFtnRef'),
        (MSONFC, 'nfcEdnRef'),
        (pint.uint16_t, 'hpsZoomFontPag'),
        (pint.uint16_t, 'dywDispPag'),
    ]

# FIXME: finish these
class Dop2000(pstruct.type):
    _fields_ = [
        (Dop97, 'dop97'),
    ]
class Dop2002(pstruct.type):
    _fields_ = [
        (Dop2000, 'dop2000'),
    ]
class Dop2003(pstruct.type):
    _fields_ = [
        (Dop2002, 'dop2002'),
    ]
class Dop2007(pstruct.type):
    _fields_ = [
        (Dop2003, 'dop2002'),
    ]
class Dop2010(pstruct.type):
    _fields_ = [
        (Dop2007, 'dop2002'),
    ]
class Dop2013(pstruct.type):
    _fields_ = [
        (Dop2010, 'dop2010'),
    ]

class Dop(dynamic.union):
    _fields_ = [
        (lambda self: dyn.clone(DopBase, blocksize=lambda _, cb=min(DopBase().a.blocksize(), self.o.li.blocksize()): cb), 'Base'),
        (lambda self: dyn.clone(Dop95, blocksize=lambda _, cb=min(Dop95().a.blocksize(), self.o.li.blocksize()): cb), '95'),
        (lambda self: dyn.clone(Dop97, blocksize=lambda _, cb=min(Dop97().a.blocksize(), self.o.li.blocksize()): cb), '97'),
        (lambda self: dyn.clone(Dop2000, blocksize=lambda _, cb=min(Dop2000().a.blocksize(), self.o.li.blocksize()): cb), '2000'),
        (lambda self: dyn.clone(Dop2002, blocksize=lambda _, cb=min(Dop2002().a.blocksize(), self.o.li.blocksize()): cb), '2002'),
        (lambda self: dyn.clone(Dop2003, blocksize=lambda _, cb=min(Dop2003().a.blocksize(), self.o.li.blocksize()): cb), '2003'),
        (lambda self: dyn.clone(Dop2007, blocksize=lambda _, cb=min(Dop2007().a.blocksize(), self.o.li.blocksize()): cb), '2007'),
        (lambda self: dyn.clone(Dop2010, blocksize=lambda _, cb=min(Dop2010().a.blocksize(), self.o.li.blocksize()): cb), '2010'),
        (lambda self: dyn.clone(Dop2013, blocksize=lambda _, cb=min(Dop2003().a.blocksize(), self.o.li.blocksize()): cb), '2003'),
    ]

    def latest(self):
        res, cb = self.object, self.size()
        for k in self.keys():
            if self[k].initializedQ() and not self[k].properties().get('abated', False):
                res = self[k]
            continue
        return res

## Character stuff
class CharacterType(pint.enum):
    _values_ = [
        ('Cell Mark', 0x0007),      # Also Table Terminating Paragraph Mark (TTP Mark)
        ('Line Break', 0x000b),
        ('Section Mark', 0x000c),
        ('Paragraph Mark', 0x000d),
    ]

class ChpxFkp(pstruct.type):
    # FIXME
    _fields_ = [
    ]

class PapxFkp(pstruct.type):
    # FIXME
    _fields_ = [
    ]

## File Information Block
class FibBase(pstruct.type):
    class _b(pbinary.flags):
        _fields_ = rl(
            (1, 'fDot'),
            (1, 'fGlsy'),
            (1, 'fComplex'),
            (1, 'fHasPic'),
            (4, 'cQuickSaves'),
            (1, 'fEncrypted'),
            (1, 'fWhichTblStm'),
            (1, 'fReadOnlyRecommended'),
            (1, 'fWriteReservation'),
            (1, 'fExtChar'),
            (1, 'fLoadOverride'),
            (1, 'fFarEast'),
            (1, 'fObfuscated'),
        )
    class _b2(pbinary.flags):
        _fields_ = rl(
            (1, 'fMac'),
            (1, 'fEmptySpecial'),
            (1, 'fLoadOverridePage'),
            (1, 'reserved1'),
            (1, 'reserved2'),
            (3, 'fSpare0'),
        )
    _fields_ = [
        (pint.uint16_t, 'wIdent'),
        (pint.uint16_t, 'nFib'),
        (pint.uint16_t, 'unused'),
        (LID, 'lid'),
        (pint.uint16_t, 'pnNext'),
        (_b, 'b'),
        (pint.uint16_t, 'nFibBack'),
        (pint.uint32_t, 'lKey'),
        (pint.uint8_t, 'envr'),
        (_b2, 'b2'),
        (pint.uint16_t, 'chs'),
        (pint.uint16_t, 'chsTables'),
        (pint.uint32_t, 'fcMin'),
        (pint.uint32_t, 'fcMac'),
    ]

class FibRgW97(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'wMagicCreated'),
        (pint.uint16_t, 'wMagicRevised'),
        (pint.uint16_t, 'wMagicCreatedPrivate'),
        (pint.uint16_t, 'wMagicRevisedPrivate'),
        (pint.uint16_t, 'pnFbpChpFirst_W6'),
        (pint.uint16_t, 'pnChpFirst_W6'),
        (pint.uint16_t, 'cpnBteChp_W6'),
        (pint.uint16_t, 'pnFbpPapFirst_W6'),
        (pint.uint16_t, 'pnPapFirst_W6'),
        (pint.uint16_t, 'cpnBtePap_W6'),
        (pint.uint16_t, 'pnFbpLvcFirst_W6'),
        (pint.uint16_t, 'pnLvcFirst_W6'),
        (pint.uint16_t, 'cpnBteLvc_W6'),
        (LID, 'lidFE'),
    ]

class FibRgW(dynamic.union):
    _fields_ = [
        (lambda self: dyn.clone(FibRgW97, blocksize=lambda _, cb=min(FibRgW97().a.blocksize(), self.o.li.blocksize()): cb), '97'),
    ]

    def latest(self):
        res, cb = self.object, self.size()
        for k in self.keys():
            if self[k].initializedQ() and not self[k].properties().get('abated', False):
                res = self[k]
            continue
        return res

class FibRgLw95(pstruct.type):
    _fields_ = [
        (pint.uint32_t, 'cbMac'),
        (pint.uint32_t, 'lProductCreated'),
        (pint.uint32_t, 'lProductRevised'),
        (pint.uint32_t, 'ccpText'),
        (pint.uint32_t, 'ccpFtn'),
        (pint.uint32_t, 'ccpHdr'),
        (pint.uint32_t, 'ccpMcr'),
        (pint.uint32_t, 'ccpAtn'),
        (pint.uint32_t, 'ccpEdn'),
        (pint.uint32_t, 'ccpTxbx'),
        (pint.uint32_t, 'ccpHdrTxbx'),
    ]

    def SumCCP(self):
        return sum(self[n].int() for n in ('ccpFtn', 'ccpHdr', 'ccpMcr', 'ccpAtn', 'ccpEdn', 'ccpTxbx', 'ccpHdrTxbx'))

class FibRgLw97(pstruct.type):
    _fields_ = [
        (FibRgLw95, 'rgLw95'),
        (pint.uint32_t, 'pnFbpChpFirst'),
        (pint.uint32_t, 'pnChpFirst'),
        (pint.uint32_t, 'cpnBteChp'),
        (pint.uint32_t, 'pnFbpPapFirst'),
        (pint.uint32_t, 'pnPapFirst'),
        (pint.uint32_t, 'cpnBtePap'),
        (pint.uint32_t, 'pnFbLvcFirst'),
        (pint.uint32_t, 'pnLvcFirst'),
        (pint.sint32_t, 'cpnBteLvc'),
    ]

class FibRgLw97x(pstruct.type):
    _fields_ = [
        (FibRgLw97, 'rgLw97'),
        (pint.sint32_t, 'fcIslandFirst'),
        (pint.sint32_t, 'fcIslandLim'),
    ]

class FibRgLw(dynamic.union):
    _fields_ = [
        (lambda self: dyn.clone(FibRgLw95, blocksize=lambda _, cb=min(FibRgLw95().a.blocksize(), self.o.li.blocksize()): cb), '95'),
        (lambda self: dyn.clone(FibRgLw97, blocksize=lambda _, cb=min(FibRgLw97().a.blocksize(), self.o.li.blocksize()): cb), '97'),
        (lambda self: dyn.clone(FibRgLw97x, blocksize=lambda _, cb=min(FibRgLw97x().a.blocksize(), self.o.li.blocksize()): cb), '97x'),
    ]

    def latest(self):
        res, cb = self.object, self.size()
        keys = iter(self.keys())
        k = next(keys)
        for k in self.keys():
            if self[k].initializedQ() and not self[k].properties().get('abated', False):
                res = self[k]
            continue
        return res

class FibRgFcLcb97(pstruct.type):
    _fields_ = [
        (FcLcb, 'StshfOrig'),
        (FcLcb, 'Stshf'),
        (FcLcb, 'PlcffndRef'),
        (FcLcb, 'PlcffndTxt'),
        (FcLcb, 'PlcfandRef'),
        (FcLcb, 'PlcfandTxt'),
        (FcLcb, 'PlcfSed'),
        (FcLcb, 'PlcPad'),
        (FcLcb, 'PlcfPhe'),
        (FcLcb, 'SttbfGlsy'),
        (FcLcb, 'PlcfGlsy'),
        (FcLcb, 'PlcfHdd'),
        (FcLcb, 'PlcfBteChpx'),
        (FcLcb, 'PlcfBtePapx'),
        (FcLcb, 'PlcfSea'),
        (FcLcb, 'SttbfFfn'),
        (FcLcb, 'PlcfFldMom'),
        (FcLcb, 'PlcfFldHdr'),
        (FcLcb, 'PlcfFldFtn'),
        (FcLcb, 'PlcfFldAtn'),
        (FcLcb, 'PlcfFldMcr'),
        (FcLcb, 'SttbfBkmk'),
        (FcLcb, 'PlcfBkf'),
        (FcLcb, 'PlcfBkl'),
        (FcLcb, 'Cmds'),
        (FcLcb, 'Unused1'),
        (FcLcb, 'SttbfMcr'),
        (FcLcb, 'PrDrvr'),
        (FcLcb, 'PrEnvPort'),
        (FcLcb, 'PrEnvLand'),
        (FcLcb, 'Wss'),
        (FcLcb, 'Dop'),
        (FcLcb, 'SttbfAssoc'),
        (FcLcb, 'Clx'),
        (FcLcb, 'PlcfPgdFtn'),
        (FcLcb, 'AutosaveSource'),
        (FcLcb, 'GrpXstAtnOwners'),
        (FcLcb, 'SttbfAtnBkmk'),
        (FcLcb, 'Unused2'),
        (FcLcb, 'Unused3'),
        (FcLcb, 'PlcSpaMom'),
        (FcLcb, 'PlcSpaHdr'),
        (FcLcb, 'PlcfAtnBkf'),
        (FcLcb, 'PlcfAtnBkl'),
        (FcLcb, 'Pms'),
        (FcLcb, 'FormFldSttbs'),
        (FcLcb, 'PlcfendRef'),
        (FcLcb, 'PlcfendTxt'),
        (FcLcb, 'PlcfFldEdn'),
        (FcLcb, 'Unused4'),
        (FcLcb, 'DggInfo'),
        (FcLcb, 'SttbfRMark'),
        (FcLcb, 'SttbfCaption'),
        (FcLcb, 'SttbfAutoCaption'),
        (FcLcb, 'PlcfWkb'),
        (FcLcb, 'PlcfSpl'),
        (FcLcb, 'PlcftxbxTxt'),
        (FcLcb, 'PlcfFldTxbx'),
        (FcLcb, 'PlcfHdrtxbxTxt'),
        (FcLcb, 'PlcfFldHdrTxbx'),
        (FcLcb, 'StwUser'),
        (FcLcb, 'SttbTtmbd'),
        (FcLcb, 'CookieData'),
        (FcLcb, 'PgdMotherOldOld'),
        (FcLcb, 'BkdMotherOldOld'),
        (FcLcb, 'PgdFtnOldOld'),
        (FcLcb, 'BkdFtnOldOld'),
        (FcLcb, 'PgdEdnOldOld'),
        (FcLcb, 'BkdEdnOldOld'),
        (FcLcb, 'SttbfIntlFld'),
        (FcLcb, 'RouteSlip'),
        (FcLcb, 'SttbSavedBy'),
        (FcLcb, 'SttbFnm'),
        (FcLcb, 'PlfLst'),
        (FcLcb, 'PlfLfo'),
        (FcLcb, 'PlcfTxbxBkd'),
        (FcLcb, 'PlcfTxbxHdrBkd'),
        (FcLcb, 'DocUndoWord9'),
        (FcLcb, 'RgbUse'),
        (FcLcb, 'Usp'),
        (FcLcb, 'Uskf'),
        (FcLcb, 'PlcupcRgbUse'),
        (FcLcb, 'PlcupcUsp'),
        (FcLcb, 'SttbGlsyStyle'),
        (FcLcb, 'Plgosl'),
        (FcLcb, 'Plcocx'),
        (FcLcb, 'PlcfBteLvc'),
        (FILETIME, 'DateTime'),
        (FcLcb, 'PlcfLvcPre10'),
        (FcLcb, 'PlcfAsumy'),
        (FcLcb, 'PlcfGram'),
        (FcLcb, 'SttbListNames'),
        (FcLcb, 'SttbfUssr'),
    ]

class FibRgFcLcb2000(pstruct.type):
    _fields_ = [
        (FibRgFcLcb97, 'rgFcLcb97'),
        (FcLcb, 'fcPlcfTch'),
        (FcLcb, 'fcRmdThreading'),
        (FcLcb, 'fcMid'),
        (FcLcb, 'fcSttbRgtplc'),
        (FcLcb, 'fcMsoEnvelope'),
        (FcLcb, 'fcPlcfLad'),
        (FcLcb, 'fcRgDofr'),
        (FcLcb, 'fcPlcosl'),
        (FcLcb, 'fcPlcfCookieOld'),
        (FcLcb, 'fcPgdMotherOld'),
        (FcLcb, 'fcBkdMotherOld'),
        (FcLcb, 'fcPgdFtnOld'),
        (FcLcb, 'fcBkdFtnOld'),
        (FcLcb, 'fcPgdEdnOld'),
        (FcLcb, 'fcBkdEdnOld'),
    ]

class FibRgFcLcb2002(pstruct.type):
    _fields_ = [
        (FibRgFcLcb2000, 'rgFcLcb2000'),
        (FcLcb, 'Unused1'),
        (FcLcb, 'PlcfPgp'),
        (FcLcb, 'Plcfuim'),
        (FcLcb, 'PlfguidUim'),
        (FcLcb, 'AtrdExtra'),
        (FcLcb, 'Plrsid'),
        (FcLcb, 'SttbfBkmkFactoid'),
        (FcLcb, 'PlcBkfFactoid'),
        (FcLcb, 'Plcfcookie'),
        (FcLcb, 'PlcfBklFactoid'),
        (FcLcb, 'FactoidData'),
        (FcLcb, 'DocUndo'),
        (FcLcb, 'SttbfBkmkFcc'),
        (FcLcb, 'PlcfBkfFcc'),
        (FcLcb, 'PlcfBklFcc'),
        (FcLcb, 'SttbfbkmkBPRepairs'),
        (FcLcb, 'PlcfbkfBPRepairs'),
        (FcLcb, 'PlcfbklBPRepairs'),
        (FcLcb, 'PmsNew'),
        (FcLcb, 'ODSO'),
        (FcLcb, 'PlcfpmiOldXP'),
        (FcLcb, 'PlcfpmiNewXP'),
        (FcLcb, 'PlcfpmiMixedXP'),
        (FcLcb, 'Unused2'),
        (FcLcb, 'Plcffactoid'),
        (FcLcb, 'PlcflvcOldXP'),
        (FcLcb, 'PlcflvcNewXP'),
        (FcLcb, 'PlcflvcMixedXP'),
    ]

class FibRgFcLcb2003(pstruct.type):
    _fields_ = [
        (FibRgFcLcb2002, 'rgFcLcb2002'),
        (FcLcb, 'Hplxsdr'),
        (FcLcb, 'SttbfBkmkSdt'),
        (FcLcb, 'PlcfBkfSdt'),
        (FcLcb, 'PlcfBklSdt'),
        (FcLcb, 'CustomXForm'),
        (FcLcb, 'SttbfBkmkProt'),
        (FcLcb, 'PlcfBkfProt'),
        (FcLcb, 'PlcfBklProt'),
        (FcLcb, 'SttbProtUser'),
        (FcLcb, 'Unused'),
        (FcLcb, 'PlcfpmiOld'),
        (FcLcb, 'PlcfpmiOldInline'),
        (FcLcb, 'PlcfpmiNew'),
        (FcLcb, 'PlcfpmiNewInline'),
        (FcLcb, 'PlcflvcOld'),
        (FcLcb, 'PlcflvcOldInline'),
        (FcLcb, 'PlcflvcNew'),
        (FcLcb, 'PlcflvcNewInline'),
        (FcLcb, 'PgdMother'),
        (FcLcb, 'BkdMother'),
        (FcLcb, 'AfdMother'),
        (FcLcb, 'PgdFtn'),
        (FcLcb, 'BkdFtn'),
        (FcLcb, 'AfdFtn'),
        (FcLcb, 'PgdEdn'),
        (FcLcb, 'BkdEdn'),
        (FcLcb, 'AfdEdn'),
        (FcLcb, 'Afd'),
    ]

class FibRgFcLcb2007(pstruct.type):
    _fields_ = [
        (FibRgFcLcb2003, 'rgFcLcb2003'),
        (FcLcb, 'Plcfmthd'),
        (FcLcb, 'SttbfBkmkMoveFrom'),
        (FcLcb, 'PlcfBkfMoveFrom'),
        (FcLcb, 'PlcfBklMoveFrom'),
        (FcLcb, 'SttbfBkmkMoveTo'),
        (FcLcb, 'PlcfBkfMoveTo'),
        (FcLcb, 'PlcfBklMoveTo'),
        (FcLcb, 'Unused1'),
        (FcLcb, 'Unused2'),
        (FcLcb, 'Unused3'),
        (FcLcb, 'SttbfBkmkArto'),
        (FcLcb, 'PlcfBkfArto'),
        (FcLcb, 'PlcfBklArto'),
        (FcLcb, 'ArtoData'),
        (FcLcb, 'Unused4'),
        (FcLcb, 'Unused5'),
        (FcLcb, 'Unused6'),
        (FcLcb, 'OssTheme'),
        (FcLcb, 'ColorSchemeMapping'),
    ]

class FibRgFcLcb(dynamic.union):
    _fields_ = [
        (lambda self: dyn.clone(FibRgFcLcb97, blocksize=lambda _, cb=min(FibRgFcLcb97().a.blocksize(), self.o.li.blocksize()): cb), '97'),
        (lambda self: dyn.clone(FibRgFcLcb2000, blocksize=lambda _, cb=min(FibRgFcLcb2000().a.blocksize(), self.o.li.blocksize()): cb), '2000'),
        (lambda self: dyn.clone(FibRgFcLcb2002, blocksize=lambda _, cb=min(FibRgFcLcb2002().a.blocksize(), self.o.li.blocksize()): cb), '2002'),
        (lambda self: dyn.clone(FibRgFcLcb2003, blocksize=lambda _, cb=min(FibRgFcLcb2003().a.blocksize(), self.o.li.blocksize()): cb), '2003'),
        (lambda self: dyn.clone(FibRgFcLcb2007, blocksize=lambda _, cb=min(FibRgFcLcb2007().a.blocksize(), self.o.li.blocksize()): cb), '2007'),
    ]

    def latest(self):
        res, cb = self.object, self.size()
        for k in self.keys():
            if self[k].initializedQ() and not self[k].properties().get('abated', False):
                res = self[k]
            continue
        return res

class FibRgCswNewData2000(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'cQuickSavesNew'),
    ]

class FibRgCswNewData2007(pstruct.type):
    _fields_ = [
        (FibRgCswNewData2000, 'rgCswNewData2000'),
        (pint.uint16_t, 'lidThemeOther'),
        (pint.uint16_t, 'lidThemeFE'),
        (pint.uint16_t, 'lidThemeCS'),
    ]

class FibRgCswNew(dynamic.union):
    _fields_ = [
        (lambda self: dyn.clone(FibRgCswNewData2000, blocksize=lambda _, cb=min(FibRgFcLcb2000().a.blocksize(), self.o.li.blocksize()): cb), '2000'),
        (lambda self: dyn.clone(FibRgCswNewData2007, blocksize=lambda _, cb=min(FibRgFcLcb2007().a.blocksize(), self.o.li.blocksize()): cb), '2007'),
    ]

    def latest(self):
        res, cb = self.object, self.size()
        for k in self.keys():
            if self[k].initializedQ() and not self[k].properties().get('abated', False):
                res = self[k]
            continue
        return res

class Fib(pstruct.type):
    class c(pint.uint16_t):
        def int(self):
            return super(Fib.c, self).int() + 1
    _fields_ = [
        (FibBase, 'base'),
        (pint.uint16_t, 'csw'),
        (lambda self: dyn.clone(FibRgW, _value_=dyn.array(pint.uint16_t, self['csw'].li.int())), 'fibRgW'),
        (pint.uint16_t, 'cslw'),
        (lambda self: dyn.clone(FibRgLw, _value_=dyn.array(pint.uint32_t, self['cslw'].li.int())), 'fibRgLw'),
        (pint.uint16_t, 'cbRgFcLcb'),
        (lambda self: dyn.clone(FibRgFcLcb, _value_=dyn.array(pint.uint64_t, self['cbRgFcLcb'].li.int())), 'fibRgFcLcbBlob'),
        (pint.uint16_t, 'cswNew'),
        (lambda self: pint.uint16_t if self['cswNew'].li.int() else pint.uint_t, 'nFibNew'),
        (lambda self: dyn.clone(FibRgCswNew, _value_=dyn.array(pint.uint16_t, max(0, self['cswNew'].li.int() - 1))), 'fibRgCswNew'),
    ]

    def nFib(self):
        res = self['cswNew'].li.int()
        return self['nFibNew'].int() if res > 0 else self['base']['nFib'].int()

class File(pstruct.type):
    def __init__(self, **attributes):
        cls, res = self.__class__, super(File, self).__init__(**attributes)
        if isinstance(self.parent, storage.DirectoryEntryData) and not isinstance(self.source, ptypes.provider.proxy):
            logging.warn("{:s}: Class {:s} was instantiated with a source that does not point to the parent {:s}. Fixing it!".format('.'.join((cls.__module__, cls.__name__)), self.classname(), self.parent.classname()))
            data = self.getparent(storage.DirectoryEntryData)
            self.source = ptypes.provider.proxy(data)
        elif not isinstance(self.parent, storage.DirectoryEntryData):
            logging.warn("{:s}: Class {:s} was not instantiated as a child of {:s}. Fields that depend on other streams might not decode properly!".format('.'.join((cls.__module__, cls.__name__)), self.classname(), storage.DirectoryEntryData.typename()))
        return res

    _fields_ = [
        (Fib, 'fib'),
        (lambda self: dyn.block(self['fib'].li['fibRgLw']['95']['cbMac'].int() - self['fib'].size()), 'content'),
    ]

if __name__ == '__main__':
    import sys, os
    import ptypes, office.storage, office.winword

    path, = sys.argv[1:]
    ptypes.setsource(ptypes.prov.file(path, mode='rb'))

    store = office.storage.File().l

    entry = next((e for e in store.Directory() if e['Name'].str() == 'WordDocument'))
    data = entry.Data(office.winword.File).l

    fib = data['fib']

    print("nFib: {:#x}".format(fib.nFib()))
    print(fib)
    print(fib['base'])
    print(fib['fibRgW'].latest())
    print(fib['fibRgLw'].latest())
    print(fib['fibRgFcLcbBlob'].latest())
    print(fib['fibRgCswNew'].latest())
