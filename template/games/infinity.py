import functools, itertools, types, builtins, operator, weakref
import logging, re, fnmatch

import ptypes, image.bitmap
from ptypes import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)

## combinators
fcompose = lambda *f: functools.reduce(lambda f1, f2: lambda *a: f1(f2(*a)), builtins.reversed(f))

## primitive types
class s8(pint.sint_t): length = 1
class u8(pint.uint_t): length = 1
class s16(pint.sint_t): length = 2
class u16(pint.uint_t): length = 2
class s24(pint.sint_t): length = 3
class u24(pint.uint_t): length = 3
class s32(pint.sint_t): length = 4
class u32(pint.uint_t): length = 4

class f32(pfloat.single): pass
class f64(pfloat.double): pass

## core types
class String(pstr.string):
    def str(self):
        res = super(String, self).str()
        return res.rstrip('\0')
    def summary(self):
        return "({:d}) {:s}".format(self.blocksize(), self.str())

class Coord(pstruct.type):
    _fields_ = [(u16, 'x'), (u16, 'y')]
    def summary(self):
        return "x={:d} y={:d}".format(self['x'].int(), self['y'].int())

class resref(String):
    length = 8

class strref(u32):
    pass

class rect(pstruct.type):
    _fields_ = [(u16, 'x1'), (u16, 'y1'), (u16, 'x2'), (u16, 'y2')]
    def summary(self):
        return "x1={:d} y1={:d} x2={:d} y2={:d}".format(self['x1'].int(), self['y1'].int(), self['x2'].int(), self['y1'].int())

## encoded types
import zlib
class zdata(ptype.encoded_t):
    def decode(self, object, **attrs):
        encdata = object.serialize()
        decdata = zlib.decompress(encdata)
        return self.new(ptype.block).set(decdata)

    def encode(self, object, **attrs):
        decdata = object.serialize()
        encdata = zlib.compress(decdata)
        return self.new(ptype.block).set(encdata)

## record types
class IndexRecord(ptype.definition):
    '''
    Key is an integer as used by the BIFF format.
    '''
    cache = {}

class FileRecord(ptype.definition):
    '''
    Key is (signature, version=(major, minor))
    '''
    cache = {}

## special types
class ocStructure(pstruct.type):
    def __pointer_to_object__(self):
        def closure(ptr, parent=self):
            count = self['count'].li
            return dyn.array(parent._object_, count.int())
        return dyn.rpointer(closure, self.getparent(File), u32)

    _fields_ = [
        (lambda self: self.__pointer_to_object__(), 'offset'),
        (u32, 'count'),
    ]

    def summary(self):
        return "offset={:#x} count={:d}".format(self['offset'].int(), self['count'].int())

class coStructure(ocStructure):
    _fields_ = [
        (u32, 'count'),
        (lambda self: self.__pointer_to_object__(), 'offset'),
    ]

class ocStructure16(ocStructure):
    _fields_ = [
        (lambda self: self.__pointer_to_object__(), 'offset'),
        (u16, 'count'),
    ]

class coStructure16(ocStructure):
    _fields_ = [
        (u16, 'count'),
        (lambda self: self.__pointer_to_object__(), 'offset'),
    ]

class oc16Structure16(ocStructure):
    def __pointer_to_object__(self):
        def closure(ptr, parent=self):
            count = self['count'].li
            return dyn.array(parent._object_, count.int())
        return dyn.rpointer(closure, self.getparent(File), u16)

    _fields_ = [
        (u16, 'count'),
        (lambda self: self.__pointer_to_object__(), 'offset'),
    ]

class padStructure(pstruct.type):
    _fields_ = [
        (lambda self: self._object_, 'st'),
    ]

class osFile(pstruct.type):
    def __pointer_to_object__(self):
        def closure(self, parent=self):
            res = parent['size'].li
            return dyn.clone(File, blocksize=lambda _, cb=res.int(): cb)
        return dyn.pointer(closure, u32)

    _fields_ = [
        (lambda self: self.__pointer_to_object__(), 'offset'),
        (u32, 'size'),
    ]

    def summary(self):
        return "offset={:#x} size={!s}".format(self['offset'].int(), self['size'].summary())

class soFile(osFile):
    _fields_ = [
        (u32, 'size'),
        (lambda self: self.__pointer_to_object__(), 'offset'),
    ]

## unknown types
@IndexRecord.define(type=1)
class Unknown_0001(image.bitmap.File):
    '''This might be a bitmap file.'''

@IndexRecord.define(type=2050)
class Unknown_0802(pstr.string):
    pass

@IndexRecord.define(type=2051)
class Unknown_0803(parray.block):
    _object_ = u32

@IndexRecord.define(type=1003)
class Unknown_03eb(parray.block):
    _object_ = u32

@IndexRecord.define(type=1007)
class Unknown_03ef(pstr.string):
    pass

@IndexRecord.define(type=1008)
class Unknown_03f0(pstr.string):
    pass

@IndexRecord.define(type=1023)
class Unknown_03ff(ptype.block):
    pass

@IndexRecord.define(type=1028)
class Unknown_0404(ptype.block):
    pass

@IndexRecord.define(type=1029)
class Unknown_0405(pstr.string):
    '''shader'''

@IndexRecord.define(type=1032)
class Unknown_0408(pstr.string):
    '''looks like lua script for the ui'''

@IndexRecord.define(type=1033)
class Unknown_0409(pstr.string):
    '''looks like lua script'''

@IndexRecord.define(type=1034)
class Unknown_040a(ptype.block):
    pass

## complex types
class Statistics(pstruct.type):
    class Kills(pstruct.type):
        _fields_ = [
            (u32, 'XP'),
            (u32, 'Number'),
        ]
        def summary(self):
            return "xp={:d} number={:d}".format(self['xp'].int(), self['number'].int())

    _fields_ = [
        (strref, 'powerful(Name)'),
        (u32, 'powerful(XP)'),
        (u32, 'duration'),
        (u32, 'time'),
        (u8, 'memberQ'),
        (u16, 'unused'),
        (pstr.char_t, 'cname'),
        (Kills, 'kills(Chapter)'),
        (Kills, 'kills(Game)'),
        (dyn.array(resref, 4), 'favorite(spells)'),
        (dyn.array(u16, 4), 'favorite(count)'),
        (dyn.array(resref, 4), 'favorite(weapons)'),
        (dyn.array(u16, 4), 'favorite(time)'),
    ]

class NPC(pstruct.type):
    _fields_ = [
        (s16, 'selected'),
        (s16, 'order'),
        (osFile, 'CRE'),
        (dyn.clone(String, length=8), 'cname'),
        (u32, 'orientation'),
        (resref, 'area'),
        (Coord, 'coordinate'),
        (Coord, 'view'),
        (u16, 'action'),
        (u16, 'happiness'),
        (dyn.array(u32, 24), 'NumTimesInteracted'),
        (dyn.array(u16, 4), 'WeaponSlots'),
        (dyn.array(u16, 4), 'QuickAbility'),
        (dyn.array(resref, 3), 'QuickSpell'),
        (dyn.array(u16, 3), 'QuickItem'),
        (dyn.array(u16, 3), 'QuickItemSlot'),
        (dyn.clone(pstr.string, length=32), 'name'),
        (u32, 'Talkcount'),
        (Statistics, 'statistics'),
        (dyn.block(8), 'voice'),
    ]

class Inventory(ptype.undefined):
    pass

class Item(pstruct.type):
    _fields_ = [
        (resref, 'resname'),
        (u8, 'time(creation)'),
        (u8, 'time(expiration)'),
        (u16, 'quantity'),
#        (dyn.array(u16, 3), 'quantity'),
#        (u32, 'flags'),
    ]

class SpellKnown(pstruct.type):
    _fields_ = [
        (resref, 'resname'),
        (u16, 'level'),
        (u16, 'type'),
    ]

class SpellInfo(pstruct.type):
    _fields_ = [
        (u16, 'level'),
        (u16, 'number'),
        (u16, 'number(effects)'),
        (u16, 'type'),
        (u32, 'index'),
        (u32, 'count'),
    ]

class SpellMemo(pstruct.type):
    _fields_ = [
        (resref, 'resname'),
        (u32, 'memorizedQ'),
    ]

class Door(pstruct.type):
    _fields_ = [
        (dyn.clone(String, length=32), 'Name'),
        (dyn.clone(String, length=8), 'ID'),
        (u32, 'flags'),
        (u32, 'ivdoor(open)'),
        (u16, 'cvdoor(open)'),
        (u16, 'cvdoor(closed)'),
        (u32, 'ivdoor(closed)'),
        (rect, 'bounds(open)'),
        (rect, 'bounds(closed)'),
        (u32, 'ivcell(open)'),
        (u16, 'cvcell(open)'),
        (u16, 'cvcell(closed)'),
        (u32, 'ivcell(closed)'),
        (u16, 'HP'),
        (u16, 'AC'),
        (resref, 'sound(open)'),
        (resref, 'sound(closed)'),
        (u32, 'cursor'),
        (u16, 'trap(detection)'),
        (u16, 'trap(removal)'),
        (u16, 'trappedQ'),
        (u16, 'detectedQ'),
        (Coord, 'trap'),
        (resref, 'key'),
        (resref, 'script'),
        (u32, 'difficulty(detection)'),
        (u32, 'difficulty(lock)'),
        (rect, 'points'),
        (strref, 'string(pick)'),
        (dyn.clone(String, length=24), 'trigger'),
        (strref, 'speaker'),
        (resref, 'dialog'),
        (resref, 'unknown'),
    ]

class VAR(pstruct.type):
    _fields_ = [
        (dyn.clone(String, length=32), 'name'),
        (u16, 'type'),
        (u16, 'ref'),
        (u32, 'dword'),
        (s32, 'int'),
        (f64, 'double'),
        (dyn.clone(String, length=32), 'value'),
    ]

class Journal(pstruct.type):
    _fields_ = [
        (strref, 'text'),
        (u32, 'time'),
        (u8, 'chapter'),
        (u8, 'owner'),
        (u8, 'section'),
        (u8, 'location'),
    ]

class Actor(pstruct.type):
    _fields_ = [
        (dyn.clone(String, length=32), 'name'),
        (Coord, 'current'),
        (Coord, 'destination'),
        (u32, 'flags'),
        (u16, 'spawnedQ'),
        (pstr.char_t, 'cresref'),
        (u8, 'unused1'),
        (u32, 'animation'),
        (u16, 'orientation'),
        (u16, 'unused2'),
        (u32, 'timer(remove)'),
        (u16, 'move(distance)'),
        (u16, 'move(target)'),
        (u32, 'schedule'),
        (u32, 'NumTimesTalkedTo'),
        (resref, 'dialog'),
        (resref, 'script(override)'),
        (resref, 'script(general)'),
        (resref, 'script(class)'),
        (resref, 'script(race)'),
        (resref, 'script(default)'),
        (resref, 'script(specific)'),
        (resref, 'file(CRE)'),
        (osFile, 'CRE'),
        (dyn.block(128), 'unused3'),
    ]

## bitmap animation format
class RGBQUAD(pstruct.type):
    _fields_ = [
        (u8, 'b'),
        (u8, 'g'),
        (u8, 'r'),
        (u8, 'a'),
    ]

class BitmapFrame(pstruct.type):
    class _data(pbinary.flags):
        _fields_ = [
            (1, 'compressedQ'),
            (31, 'offset'),
        ]
    _fields_ = [
        (u16, 'width'),
        (u16, 'height'),
        (s16, 'x'),
        (s16, 'y'),
        (_data, 'data'),
    ]

class BitmapCycle(pstruct.type):
    _fields_ = [
        (u16, 'count(indices)'),
        (u16, 'index'),
    ]

@FileRecord.define
class BitmapAnimation(pstruct.type):
    type = 'BAM ', (1, None)

    def __offset_frame(self):
        count = self['count(frame)'].li
        t = dyn.array(BitmapFrame, count.int())
        # FIXME: this should be followed by count(cycle) BitmapCycle entries...
        return dyn.rpointer(t, self.getparent(File), u32)

    def __offset_palette(self):
        t = dyn.array(RGBQUAD, 0)
        # FIXME: figure out the correct count for this
        return dyn.rpointer(t, self.getparent(File), u32)

    def __offset_table(self):
        # FIXME: figure out the correct count for this
        t = dyn.array(u32, 0)
        return dyn.rpointer(t, self.getparent(File), u32)

    _fields_ = [
        (u16, 'count(frame)'),
        (u8, 'count(cycle)'),
        (u8, 'compressed'),
        (__offset_frame, 'offset(frame)'),
        (__offset_palette, 'offset(palette)'),
        (__offset_table, 'offset(table)'),
    ]

@FileRecord.define
class BitmapAnimationCompressed(pstruct.type):
    type = 'BAMC', (1, None)
    def __data(self):
        t = dyn.block(self['length'].li.int())
        return dyn.clone(zdata, _value_=t, _object_=ptype.block)
    _fields_ = [
        (u32, 'length'),
        (__data, 'data'),
    ]

## some table format (we define a bunch of keys for it because the devers can't seem to type it right)
@FileRecord.define(type=('2DA ', '    '))
@FileRecord.define(type=(' 2DA', ' V1.'))
@FileRecord.define
class TwoDimensionalArray(pstr.string):
    type = '2DA ', (1, 0)
    def iterate(self):
        string = self.str()
        items = string.replace('\r\n', '\n').split('\n')
        return (item.replace('\t', 7*' ') for item in items if item)

    def split(self):
        iterable = self.iterate()
        return [item for item in iterable]

    def Default(self):
        iterable = self.iterate()
        # figure out whatever the first single item is
        item = next(iterable).strip()
        return int(item) if item.isdigit() else item

    def Columns(self):
        iterable = self.iterate()
        # some heuristics to extract the column headers
        next(iterable)
        row = next(iterable)
        iterable = (item for item in row.split(' ') if item.strip())
        return [item.strip() for item in iterable]

    def Rows(self):
        iterable = self.iterate()
        next(iterable)
        next(iterable)
        # some heuristics to extract the first column
        iterable = (item.strip().split(' ')[0] for item in iterable if item.strip())
        return [item.strip() for item in iterable]

    def summary(self):
        default, rows, columns = self.Default(), self.Rows(), self.Columns()
        if rows and columns:
            return "default:{!s} rows:{:s} columns:{:s}".format(default, ','.join(rows), ','.join(columns))
        return "default:{!s} rows:{:s}".format(default, ','.join(rows)) if rows else "default:{!s} columns:{:s}".format(default, ','.join(columns))

    def details(self):
        return self.str().strip('\r\n')
    def repr(self):
        return self.details()

## creature format
@FileRecord.define
class Creature(pstruct.type):
    type = 'CRE ', (1, 0)
    class Portrait(pstruct.type):
        _fields_ = [
            (resref, 'small'),
            (resref, 'large'),
        ]
    class Color(pstruct.type):
        _fields_ = [
            (u8, 'metal'),
            (u8, 'minor'),
            (u8, 'major'),
            (u8, 'skin'),
            (u8, 'leather'),
            (u8, 'armor'),
            (u8, 'hair'),
        ]
    class AC(pstruct.type):
        _fields_ = [
            (s16, 'natural'),
            (s16, 'effective'),
            (s16, 'crushing'),
            (s16, 'missile'),
            (s16, 'piercing'),
            (s16, 'slashing'),
        ]
    class Saves(pstruct.type):
        _fields_ = [
            (u8, 'death'),
            (u8, 'wands'),
            (u8, 'poly'),
            (u8, 'breath'),
            (u8, 'spells'),
        ]
    class Resist(pstruct.type):
        _fields_ = [
            (u8, 'fire'),
            (u8, 'cold'),
            (u8, 'electricity'),
            (u8, 'acid'),
            (u8, 'magic'),
            (u8, 'magic-fire'),
            (u8, 'magic-cold'),
            (u8, 'slashing'),
            (u8, 'crushing'),
            (u8, 'piercing'),
            (u8, 'missile'),
        ]
    class Skills(pstruct.type):
        _fields_ = [
            (u8, 'Detect'),
            (u8, 'Traps(set)'),
            (u8, 'Lore'),
            (u8, 'Lockpicking'),
            (u8, 'Stealth'),
            (u8, 'Traps(disarm)'),
            (u8, 'Pickpocket'),
            (u8, 'Fatigue'),
            (u8, 'Intoxication'),
            (u8, 'Luck'),
        ]
    class Proficiencies(parray.type):
        length, _object_ = 20, u8

    class PSTEE(pstruct.type):
        _fields_ = [
            (u32, 'XP(thief)'),
            (u32, 'XP(mage)'),
            (u8, 'variable(GOOD)'),
            (u8, 'variable(LAW)'),
            (u8, 'variable(LADY)'),
            (u8, 'Faction'),
            (u8, 'Team'),
            (u8, 'Species'),
            (u8, 'range(Dialog)'),
            (u8, 'size(Circle)'),
            (u8, 'flags(shield)'),
            (u8, 'vision'),
            (u32, 'flags'),
            (dyn.block(10), 'unused'),
        ]
    def __Game(self):
        return self.PSTEE
    class Stats(pstruct.type):
        _fields_ = [
            (u8, 'STR'),
            (u8, 'STR%'),
            (u8, 'INT'),
            (u8, 'WIS'),
            (u8, 'DEX'),
            (u8, 'CON'),
            (u8, 'CHA'),
        ]

    class IDs(pstruct.type):
        '''these are all enumerations'''
        _fields_ = [
            (u8, 'enemy-ally'),
            (u8, 'general'),
            (u8, 'race'),
            (u8, 'class'),
            (u8, 'specific'),
            (u8, 'gender'),
            (dyn.array(u8, 5), 'object'),
            (u8, 'alignment'),
        ]
    class Enum(pstruct.type):
        _fields_ = [
            (u16, 'global'),
            (u16, 'local'),
        ]

    def __items(self):
        # XXX: i counted 25 items here, but i'm not sure where this comes
        #      from (other than loaded items, and inventory items)
        t = dyn.array(u16, 25)
        return dyn.rpointer(t, self.getparent(File), u32)

    _fields_ = [
        (strref, 'name'),
        (strref, 'tooltip'),
        (u32, 'flags'),
        (u32, 'xp'),
        (u32, 'power'),
        (u32, 'gold'),
        (u32, 'status'),
        (u16, 'hp'),
        (u16, 'maxhp'),
        (u32, 'animationid'),
        (Color, 'color'),
        (u8, 'EffVersion'),
        (Portrait, 'portrait'),
        (s8, 'reputation'),
        (u8, 'shadowsQ'),
        (AC, 'AC'),
        (u8, 'THAC0'),
        (u8, 'AttackCount'),
        (Saves, 'Saves'),
        (Resist, 'Resist'),
        (Skills, 'Skills'),
        (Proficiencies, 'Proficiencies'),
        (u8, 'TurnUndead'),
        (u8, 'Tracking'),
        (__Game, 'Game'),   # PSTEE-only
        (dyn.array(strref, 100), 'strtab'),
        (dyn.array(u8, 3), 'level(classes)'),
        (u8, 'gender'),
        (Stats, 'stats'),
        (u8, 'morale'),
        (u8, 'morale(break)'),
        (u8, 'enemy(race)'),
        (u16, 'morale(recovery)'),
        (u32, 'kit'),
        (resref, 'script(override)'),
        (resref, 'script(class)'),
        (resref, 'script(race)'),
        (resref, 'script(general)'),
        (resref, 'script(default)'),
        (IDs, 'id'),
        (Enum, 'actor'),
        (dyn.clone(String, length=32), 'variable(death)'),
        (dyn.clone(ocStructure, _object_=SpellKnown), 'spells(known)'),
        (dyn.clone(ocStructure, _object_=SpellInfo), 'spells(info)'),
        (dyn.clone(ocStructure, _object_=SpellMemo), 'spells(memorized)'),
        (dyn.clone(ocStructure, _object_=Item), 'items'),
        (__items, 'items(slots)'),
        (dyn.clone(ocStructure, _object_=ptype.block), 'effects'),
        (resref, 'dialog'),
    ]

## area format
@FileRecord.define
class Area(pstruct.type):
    type = 'AREA', (1, 0)

    class AreaFlags(pstruct.type):
        _fields_ = [
            (resref, 'area'),
            (u32, 'flags'),
        ]

    _fields_ = [
        (resref, 'wed'),
        (u32, 'last saved'),
        (u32, 'flags'),
        (AreaFlags, 'flags(North)'),
        (AreaFlags, 'flags(East)'),
        (AreaFlags, 'flags(South)'),
        (AreaFlags, 'flags(West)'),
        (u16, 'type'),
        (u16, 'probability(rain)'),
        (u16, 'probability(snow)'),
        (u16, 'probability(fog)'),
        (u16, 'probability(lightning)'),
        (u16, 'wind'),
        (dyn.clone(ocStructure16, _object_=Actor), 'actors'),
        (dyn.clone(coStructure16, _object_=ptype.block), 'regions'),
        (dyn.clone(ocStructure, _object_=ptype.block), 'spawns'),
        (dyn.clone(ocStructure, _object_=ptype.block), 'entrances'),
        (dyn.clone(ocStructure16, _object_=ptype.block), 'containers'),
        (dyn.clone(coStructure16, _object_=Item), 'items'),
        (dyn.clone(ocStructure16, _object_=ptype.block), 'vertices'),
        (dyn.clone(coStructure16, _object_=ptype.block), 'ambients'),
        (dyn.clone(ocStructure, _object_=VAR), 'variables'),
        (dyn.clone(oc16Structure16, _object_=ptype.block), 'tileflags'),
        (resref, 'script'),
        (soFile, 'explored'),
        (dyn.clone(coStructure, _object_=Door), 'doors'),
        (dyn.clone(coStructure, _object_=ptype.block), 'animations'),
        (dyn.clone(coStructure, _object_=ptype.block), 'tiles'),
        (lambda self: dyn.rpointer(ptype.undefined, self.getparent(File), u32), 'rest interruptions'),
        (dyn.clone(ocStructure, _object_=ptype.block), 'notes'),
        (dyn.clone(ocStructure, _object_=ptype.block), 'traps'),
        (resref, 'rest(day)'),
        (resref, 'rest(night)'),
        (dyn.block(56), 'unused'),
    ]

## archive (save) formats
class Contents(pstruct.type):
    def __data(self):
        length = self['length(data)'].li
        return dyn.clone(zdata, _value_=dyn.block(length.int()), _object_=File)

    _fields_ = [
        (u32, 'length(filename)'),
        (lambda self: dyn.clone(pstr.string, length=self['length(filename)'].li.int()), 'filename'),
        (u32, 'length'),
        (u32, 'length(data)'),
        (__data, 'data'),
    ]

@FileRecord.define
class Save(parray.block):
    type = 'SAV ', (1, 0)
    _object_ = Contents

## game format
@FileRecord.define
class Game(pstruct.type):
    type = 'GAME', (2, 0)
    _fields_ = [
        (u32, 'time'),
        (dyn.array(u16, 6), 'formation'),
        (u32, 'gold'),
        (u16, 'unknown'),
        (u16, 'flags(weather)'),
        (dyn.clone(ocStructure, _object_=NPC), 'PCs'),
        (dyn.clone(ocStructure, _object_=Inventory), 'inventory'),
        (dyn.clone(ocStructure, _object_=NPC), 'NPCs'),
        (dyn.clone(ocStructure, _object_=VAR), 'GVar'),
        (resref, 'area(Main)'),
        (dyn.pointer(ptype.undefined, u32), 'extra(familiar)'),
        (dyn.clone(coStructure, _object_=Journal), 'journal'),
        (u32, 'reputation'),
        (resref, 'area(Current)'),
        (u32, 'flags(gui)'),
        (u32, 'load progress'),
        (dyn.pointer(ptype.undefined, u32), 'info(familiar)'),
        (dyn.clone(ocStructure, _object_=ptype.undefined), 'locations'),
        (u32, 'game time'),
        (dyn.clone(ocStructure, _object_=ptype.undefined), 'planes'),
        (u32, 'zoom'),
        (resref, 'area(random encounter)'),
        (resref, 'worldmap'),
        (resref, 'campaign'),
        (u32, 'owner(familiar)'),
        (dyn.clone(String, length=20), 'random encounter'),
    ]

## biff format
class Index(parray.type):
    import collections
    Locator = collections.namedtuple('location', ['id', 'type', 'size', 'count'])

    def summary(self):
        if len(self):
            first, last = self[0], self[-1]
            return "{:s} {:s}[{:#x}:{:+x}]...{:s}[{:#x}:{:+x}]".format(self.__element__(), File.typename(), first['offset'].int(), first['size'].int(), File.typename(), last['offset'].int(), last['size'].int())
        return "{:s} ...".format(self.__element__())

class FileIndex(Index):
    class Locator(pstruct.type):
        _fields_ = [
            (u32, 'locator'),
            (u32, 'offset'),
            (u32, 'size'),
            (u16, 'type'),
            (u16, 'unknown'),
        ]
    _object_ = Locator

class TileIndex(Index):
    class Locator(pstruct.type):
        _fields_ = [
            (u32, 'locator'),
            (u32, 'offset'),
            (u32, 'count'),
            (u32, 'size'),
            (u16, 'type'),
            (u16, 'unknown'),
        ]
    _object_ = Locator

class BiffContents(parray.terminated):
    __index__ = None

    def __init__(self, **attrs):
        if self.__index__ is None:
            attrs.setdefault('__index__', [])
        self.__cache__ = {}
        return super(BiffContents, self).__init__(**attrs)

    def _object_(self):
        index = len(self.value)
        item = self.__index__[index]
        if item.id is not None:
            self.__cache__[item.id] = index
        t = IndexRecord.withdefault(item.type, ptype.block, type=item.type, length=item.size)
        return t if t is ptype.block else dyn.clone(t, blocksize=lambda _, cb=item.size: cb)

    def locate(self, locator):
        idx = self.__cache__[locator]
        return self[idx]

    def isTerminator(self, item):
        return len(self) >= len(self.__index__)

    def enumerate(self):
        for i, item in enumerate(self):
            if item.type is not None:
                yield i, item
            continue
        return

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

    def summary(self):
        items = [item for item in self.iterate()]
        if len(items):
            first, last = items[0], items[-1]
            types = {item.type for item in self.__index__ if item.type is not None}
            return "({:d}) {:s}...{:s} types:{:s}".format(len(items), first.instance(), last.instance(), ','.join(map("{:d}".format, sorted(types))))
        return "({:d}) ...".format(len(items))

@FileRecord.define
class BIFF(pstruct.type):
    type = 'BIFF', (1, None)

    def __items(self):
        def closure(self, parent=self):
            index = parent.__build_index__()
            return dyn.clone(BiffContents, __index__=index)

        offset, fields = self['offset'].li.int() - self.getoffset(), ['count(files)', 'count(tiles)', 'offset', 'unknown']
        t = dyn.block(offset - sum(self[fld].li.size() for fld in fields))
        return dyn.clone(ptype.encoded_t, _value_=t, _object_=closure)

    def __build_index__(self):
        files, tiles = (self[fld] for fld in ['index(file)', 'index(tile)'])

        # figure out the boundaries of our data so that we can determine
        # if a locator needs to be discarded.
        baseoffset, size = self['items'].getoffset(), self['items'].size()

        # combine both indices into a single list sorted by offset
        items = [item for item in sorted(itertools.chain(files, tiles), key=fcompose(operator.itemgetter('offset'), operator.methodcaller('int')))]

        # now we need to traverse our items so that we can build a flat
        # list (with no holes) for each item and its type. if we find a
        # hole that needs to be padded, then we use the none type.
        index, position = [], baseoffset
        for item in items:
            offset = item['offset'].int()

            # if our item offset is earlier than expected, then the
            # previous index is overlapping with this one. so in this
            # case, we'll warn the user and continue skipping records
            # until we're back at a reasonable position.
            if offset < position:
                logging.warning("Item {!s} with bounds {:#x}{:+x} is {:s}".format(item.instance(), offset, item['size'].int(), "overlapping with previous entry {!s}".format(index[-1]) if len(index) else "not within expected bounds {:#x}:{:+x}".format(baseoffset, size)))
                continue

            # if our item offset is farther along than expected, then we
            # need to pad this entry till we get to the right position.
            shift = offset - position
            if offset > position:
                res = Index.Locator(id=None, type=None, count=None, size=offset - position)
                index.append(res)
                position += shift

            # if our index item is a TileIndex, then figure out the count.
            if isinstance(item, TileIndex.Locator):
                count = item['count'].int()

            # otherwise, it's a FileIndex, and there isn't a count
            else:
                count = None

            # now we should be able to add the entry, and update position.
            res = Index.Locator(id=item['locator'].int(), type=item['type'].int(), size=item['size'].int(), count=count)
            index.append(res)
            position += res.size

        # check to see if we've filled up the entire block and pad it if necessary.
        if position < baseoffset + size:
            shift = position - baseoffset
            res = Index.Locator(id=None, type=None, count=None, size=size - shift)
            index.append(res)

        # our index should now be contiguous
        return index

    _fields_ = [
        (u32, 'count(files)'),
        (u32, 'count(tiles)'),
        (u32, 'offset'),
        (u32, 'unknown'),
        (__items, 'items'),
        (lambda self: dyn.clone(FileIndex, length=self['count(files)'].li.int()), 'index(file)'),
        (lambda self: dyn.clone(TileIndex, length=self['count(tiles)'].li.int()), 'index(tile)'),
    ]

    def summary(self):
        return "count(files)={:d} count(tiles)={:d} offset={:+#x} unknown={:#x}".format(*(self[fld].int() for fld in ['count(files)','count(tiles)','offset','unknown']))

## dialogue format
class DialogState(pstruct.type):
    _fields_ = [
        (strref, 'response'),
        (u32, 'index'),
        (u32, 'count'),
        (s32, 'trigger'),
    ]

    def summary(self):
        return "index={:d} count={:d} trigger={:d} response={!s}".format(self['index'].int(), self['count'].int(), self['trigger'].int(), self['response'].summary())

class DialogTransition(pstruct.type):
    @pbinary.littleendian
    class _flags(pbinary.flags):
        _fields_ = [
            (21, 'unused'),
            (1, 'clear'),
            (1, 'immediateQ'),
            (1, 'journal(solved)'),
            (1, 'journal(note)'),
            (1, 'journal(unsolved)'),
            (1, 'interrupt'),
            (1, 'journalQ'),
            (1, 'sentinelQ'),
            (1, 'actionQ'),
            (1, 'triggerQ'),
            (1, 'textQ'),
        ]
    class _nextState(pstruct.type):
        _fields_ = [
            (resref, 'state'),
            (u32, 'index'),
        ]
        def summary(self):
            return "index={!s} state={!s}".format(self['index'].summary(), self['state'].summary())

    _fields_ = [
        (_flags, 'flags'),
        (strref, 'text'),
        (strref, 'journal'),
        (u32, 'trigger'),
        (u32, 'action'),
        (_nextState, 'next'),
    ]

    #def summary(self):
    #    items = []
    #    if flags['textQ']:
    #        items.append(self['text'])
    #    if flags['journalQ']:
    #        items.append(self['journal'])
    #    if flags['triggerQ']:
    #        items.append(self['trigger'])
    #    if flags['actionQ']:
    #        items.append(self['action'])
    #    if not flags['sentinelQ']:
    #        items.append(self['node'])
    #    raise NotImplementedError

class DialogTrigger(ocStructure):
    def __pointer_to_object__(self):
        def closure(ptr, parent=self):
            count = self['count'].li
            return dyn.clone(pstr.string, length=count.int())
        return dyn.rpointer(closure, self.getparent(File), u32)

    def summary(self):
        item = self['offset'].d
        try:
            return "offset={:#x} : {!s}".format(self['offset'].int(), item.li.summary())
        except ptypes.error.LoadError:
            pass
        return super(DialogTrigger, self).summary()

    def str(self):
        item = self['offset'].d
        return item.li.str()

class DialogAction(DialogTrigger):
    pass

@FileRecord.define
class Dialog(pstruct.type):
    type = 'DLG ', (1, 0)

    class _trigger(ocStructure):
        _object_ = DialogTrigger
        def items(self):
            result = self['offset'].d.li
            return [item.str() for item in result]

        def summary(self):
            result = self['offset'].d.li
            iterable = (item.str() for item in result)
            return "({:d}) [{:s}]".format(len(result), ', '.join(map(repr, iterable)))

    class _action(_trigger):
        _object_ = DialogAction

    _fields_ = [
        (dyn.clone(coStructure, _object_=DialogState), 'state'),
        (dyn.clone(coStructure, _object_=DialogTransition), 'transition'),
        (_trigger, 'trigger(state)'),
        (_trigger, 'trigger(transition)'),
        (_action, 'action'),
        (u32, 'hostile'),
    ]

    def States(self):
        return [item for item in self['trigger(state)'].items()]

    def Transitions(self):
        return [item for item in self['trigger(transition)'].items()]

    def Actions(self):
        return [item for item in self['action'].items()]

## file format
class Header(pstruct.type):
    class _Version(String):
        length = 4
        def get(self):
            string = self.str()
            if not string.startswith('V'):
                return super(Header._Version, self).get()

            if string[1:].count('.') > 0:
                items = string[1:].split('.', 1)
                if not all(item.isnumeric() for item in items):
                    return super(Header._Version, self).get()
                major, minor = items
                return int(major), int(minor)
            major = string[1:].rstrip(' \0')
            return int(major), None

        def set(self, version):
            if not isinstance(version, builtins.tuple):
                return super(Header._Version, self).set(version)
            res = "V{:d}.{:d}".format(*version)
            if len(res) != self.blocksize():
                raise ValueError
            return self.set(res)

    _fields_ = [
        (dyn.clone(String, length=4), 'Signature'),
        (_Version, 'Version'),
    ]

    def Signature(self):
        return self['Signature'].str()

    def summary(self):
        sig, version = tuple(self[item].get() for item in ['Signature', 'Version'])
        try:
            t = FileRecord.lookup((sig, version))
            description = "{:s} ({:s})".format(sig.rstrip(' \0'), t.__name__)
        except KeyError:
            description = sig.rstrip( '\0')

        if isinstance(version, builtins.tuple):
            filtered = (item for item in version if item is not None)
            return "{:s} v{:s}".format(description, '.'.join(map("{:d}".format, filtered)))
        return ' '.join(map("{!s}".format, [description, repr(version)]))

@IndexRecord.define(type=4)
@IndexRecord.define(type=1000)
@IndexRecord.define(type=1001)
@IndexRecord.define(type=1002)
@IndexRecord.define(type=1004)
@IndexRecord.define(type=1005)
@IndexRecord.define(type=1006)
@IndexRecord.define(type=1009)
@IndexRecord.define(type=1010)
@IndexRecord.define(type=1011)
@IndexRecord.define(type=1012)
@IndexRecord.define(type=1013)
@IndexRecord.define(type=1014)
@IndexRecord.define(type=1015)
@IndexRecord.define(type=1016)
@IndexRecord.define(type=1019)
@IndexRecord.define(type=1021)
class File(pstruct.type):
    def __Contents(self):
        res, bs = self['Header'].li, self.blocksize()
        key = tuple(res[item].get() for item in ['Signature', 'Version'])
        t = FileRecord.lookup(key, ptype.block)
        if issubclass(t, (ptype.block, parray.block, pstr.string)):
            return dyn.clone(t, blocksize=lambda _, cb=bs - res.size(): cb)
        return t

    def __Extra(self):
        res, fields = self.blocksize(), ['Header', 'Contents']
        total = sum(self[fld].li.size() for fld in fields)
        return dyn.block(res - total)

    _fields_ = [
        (Header, 'Header'),
        (__Contents, 'Contents'),
        (__Extra, 'Extra'),
    ]

    def blocksize(self):
        return self.source.size()

    def Signature(self):
        return self['Header'].Signature()

if __name__ == '__main__':
    import os, sys, os.path
    import ptypes, games.infinity as infinity
    ptypes.setsource(ptypes.prov.file(sys.argv[1], 'rb'))

    z = infinity.File()
    z = z.l
    sig = z['header']['signature'].str()

    if sig == 'GAME':
        a = z['contents']
        Players = z['contents']['PCs']['offset'].d.l
        G = z['contents']['GVar']['offset'].d.l
        cre = { index : item['cre']['offset'].d.l for index, item in enumerate(Players) }
        iterable = ((index, item['contents']) for index, item in cre.items() )
        I = { index : (item['items(slots)'].d.l, item['items']['offset'].d.l) for index, item in iterable }

        def search(name, G=z['contents']['GVar']['offset'].d.li):
            regex = re.compile(fnmatch.translate("*{:s}*".format(name)))
            Fmatcher = fcompose(operator.itemgetter('name'), operator.methodcaller('str'), regex.match, bool)
            return [item for item in filter(Fmatcher, G)]

        bookvars = search('BOOK')
        #for item in z['contents']['gvar']['offset'].d.l:
        #    print('\t'.join([item['name'].str(), "{:d}".format(item['int'].int())]))
    elif sig == 'SAV ':
        members = z['contents']
        everything = [bytearray(item['data'].d.l.serialize()) for item in z['contents']]
        files = [infinity.File(source=ptypes.prov.bytes(item)).l for item in everything]
        L, = (item for i, item in enumerate(files) if item.Signature() == 'AREA' and item['contents']['wed'].str() == 'AR0109')
        #L, = (item for i, item in enumerate(files) if item.Signature() == 'AREA' and item['contents']['wed'].str() == 'AR0108')

        #for l in L['contents']:
        #    for item in l['variables']['offset'].d.l:
        #        print('\t'.join([item['name'].str(), "{:d}".format(item['int'].int())]))
        actors = [item for item in L['contents']['actors']['offset'].d.l]
        creatures = { item['name'].str() : item['CRE']['offset'].d.l for item in actors }
        doors = L['contents']['doors']['offset'].d.l

        def save():
            for item, data in zip(z['contents'], everything):
                zdata = zlib.compress(data)
                item['length(data)'].set(len(zdata))
                item['data'] = ptype.block().set(zdata)
            z.setoffset(z.getoffset(), recurse=True)

    elif sig == 'BIFF':
        a = z['contents']['items'].d
        a = a.l
