"""
Ripped from https://www.smsoft.ru/en/pifdoc.htm
"""

import ptypes
from ptypes import *

class Heading(pstruct.type):
    def __Next_section_offset(self):
        return dyn.pointer(Section, pint.uint16_t)

    def __Section_data_offset(self):
        def _object_(_, self=self):
            length = self['Length'].li
            return SectionData.withdefault(length.int(), length=length.int())
        return dyn.pointer(_object_, pint.uint16_t)

    _fields_ = [
        (dyn.clone(pstr.string, length=0x10), 'Name'),
        (__Next_section_offset, 'NextOffset'),
        (__Section_data_offset, 'Offset'),
        (pint.uint16_t, 'Length'),
    ]

class SectionData(ptype.definition):
    cache = {}

    class default(pstr.string):
        pass

class Section(pstruct.type):
    def __data(self):
        res = self['heading'].li
        length = res['Length']
        return SectionData.withdefault(length.int(), length=length.int())

    def __padding_section(self):
        res = self['heading'].li
        if res['NextOffset'].int() < 0xffff:
            length, fields = res['NextOffset'].int() - self.getoffset(), ['heading', 'data']
            return dyn.block(max(0, length - sum(self[fld].li.size() for fld in fields)))
        return dyn.block(0)

    _fields_ = [
        (Heading, 'heading'),
        (__data, 'data'),
        (__padding_section, 'padding(data)'),
    ]

class MaximumRequired(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'maximum'),
        (pint.uint16_t, 'required'),
    ]

    def summary(self):
        return "required={:#x} maximum={:#x}".format(self['required'].int(), self['maximum'].int())

@SectionData.define
class BasicSection(pstruct.type):
    type = 0x171

    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (1, 'COM2'),
            (1, 'COM1'),
            (1, 'Reserved'),
            (1, 'Close on exit'),
            (1, 'No screen exchange'),
            (1, 'Prevent switch'),
            (1, 'Graphics mode'),
            (1, 'Direct memory'),
        ]
    @pbinary.littleendian
    class _Program_flags(pbinary.flags):
        _fields_ = [
            (1, 'Unused'),
            (1, 'Has parameters'),
            (1, 'Exchange interrupt vectors'),
            (5, 'Reserved'),
            (1, 'Direct screen'),
            (1, 'Stop in background mode'),
            (1, 'Use coprocessor'),
            (1, 'Direct keyboard'),
            (4, 'Unknown'),
        ]
    _fields_ = [
        (pint.uint8_t, 'Reserved'),
        (pint.uint8_t, 'Checksum'),
        (dyn.clone(pstr.string, length=30), 'Window title'),
        (MaximumRequired, 'Reserved memory'),
        (dyn.clone(pstr.string, length=63), 'Path'),
        (_Flags, 'Flags'),
        (pint.uint8_t, 'Drive index'),
        (dyn.clone(pstr.string, length=64), 'Directory'),
        (dyn.clone(pstr.string, length=64), 'Parameters'),
        (pint.uint8_t, 'Video mode'),
        (pint.uint8_t, 'Text video pages quantity'),
        (pint.uint8_t, 'First used interrupt'),
        (pint.uint8_t, 'Last used interrupt'),
        (pint.uint8_t, 'Rows'),
        (pint.uint8_t, 'Columns'),
        (pint.uint8_t, 'X position'),
        (pint.uint8_t, 'Y position'),
        (pint.uint16_t, 'Number of last video page'),
        (dyn.clone(pstr.string, length=64), 'Shared program path'),
        (dyn.clone(pstr.string, length=64), 'Shared program data'),
        (_Program_flags, 'Program flags'),
    ]

@SectionData.define
class Windows386Section(pstruct.type):
    type = 0x68

    @pbinary.littleendian
    class _Bit_mask1(pbinary.flags):
        _fields_ = [
            (3, 'Unused'),
            (1, 'No MS-DOS transition warning'),

            (1, 'Unused'),
            (1, 'No MS-DOS automatic transition'),
            (1, 'Unused'),
            (1, 'Prevent Windows detection'),

            (1, 'MS-DOS mode'),
            (1, 'Unused'),
            (1, 'Maximized window'),
            (1, 'Minimized window'),

            (1, 'Memory protection'),
            (1, 'Lock application memory'),
            (1, 'Fast paste'),
            (1, 'XMS memory locked'),

            (1, 'EMS memory locked'),
            (1, 'Use shortcut key'),
            (1, 'Do not use HMA'),
            (1, 'Detect idle time'),

            (1, 'No Ctrl+Esc'),
            (1, 'No PrtSc'),
            (1, 'No Alt+PrtSc'),
            (1, 'No Alt+Enter'),

            (1, 'No Alt+Space'),
            (1, 'No Alt+Esc'),
            (1, 'No Alt+Tab'),
            (1, 'Unused'),

            (1, 'Full-screen mode'),
            (1, 'Exclusive run mode'),
            (1, 'Background continuation'),
            (1, 'Permit exit'),
        ]
    @pbinary.littleendian
    class _Bit_mask2(pbinary.flags):
        _fields_ = [
            (8, 'Unused'),
            (1, 'Retain video memory'),
            (1, 'Memory: High graphics'),
            (1, 'Memory: Low graphics'),
            (1, 'Memory: Text graphics'),
            (1, 'Ports: High graphics'),
            (1, 'Ports: Low graphics'),
            (1, 'Ports: Text graphics'),
            (1, 'Video ROM emulation'),
        ]
    @pbinary.littleendian
    class _Shortcut_modifier(pbinary.flags):
        _fields_ = [
            (12, 'Unused'),
            (1, 'Alt'),
            (1, 'Ctrl'),
            (2, 'Shift'),
        ]
    _fields_ = [
        (MaximumRequired, 'Conventional memory'),
        (pint.uint16_t, 'Active priority'),
        (pint.uint16_t, 'Background priority'),
        (MaximumRequired, 'EMS memory'),
        (MaximumRequired, 'XMS memory'),
        (_Bit_mask1, 'Bit mask 1'),
        (_Bit_mask2, 'Bit mask 2'),
        (pint.uint16_t, 'Unknown_16'),
        (pint.uint16_t, 'Shortcut key scan code'),
        (_Shortcut_modifier, 'Shortcut key modifier'),
        (pint.uint16_t, 'Use shortcut key'),
        (pint.uint16_t, 'Extended shortcut key'),
        (pint.uint16_t, 'Unknown_20'),
        (pint.uint16_t, 'Unknown_22'),
        (pint.uint32_t, 'Unknown_24'),
        (dyn.clone(pstr.string, length=64), 'Parameters'),
    ]

@SectionData.define
class Windows286Section(pstruct.type):
    type = 0x6

    @pbinary.littleendian
    class _Flags(pbinary.flags):
        _fields_ = [
            (1, 'COM4'),
            (1, 'COM3'),
            (8, 'Unused'),

            (1, 'No screen retain'),
            (1, 'No Ctrl+Esc'),

            (1, 'No PrtSc'),
            (1, 'No Alt+PrtSc'),
            (1, 'No Alt+Esc'),
            (1, 'No Alt+Tab'),
        ]
    _fields_ = [
        (MaximumRequired, 'XMS memory'),
        (_Flags, 'Flags'),
    ]

@SectionData.define
class WindowsVMM40Section(pstruct.type):
    type = 0x1ac

    class _Dimensions(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'horizontal size'),
            (pint.uint16_t, 'vertical size'),
        ]
    @pbinary.littleendian
    class _Bit_mask1(pbinary.flags):
        _fields_ = [
            (10, 'Unknown'),
            (1, 'No screensaver'),
            (1, 'No exit warning'),
            (2, 'Unused'),
            (1, 'Continue in background'),
            (1, 'Reserved'),
        ]
    @pbinary.littleendian
    class _Bit_mask2(pbinary.flags):
        _fields_ = [
            (7, 'Unknown'),
            (1, 'Full-screen mode'),
            (1, 'No dynamic video memory'),
            (6, 'Unused'),
            (1, 'Video-ROM emulation'),
        ]
    @pbinary.littleendian
    class _Bit_mask3(pbinary.flags):
        _fields_ = [
            (4, 'Unknown'),
            (1, 'No Ctrl+Esc'),
            (1, 'No PrtSc'),
            (1, 'No Alt+PrtSc'),
            (1, 'No Alt+Enter'),

            (1, 'No Alt+Space'),
            (1, 'No Alt+Esc'),
            (1, 'No Alt+Tab'),
            (4, 'Unused'),
            (1, 'Fast paste'),
        ]
    @pbinary.littleendian
    class _Mouse_flags(pbinary.flags):
        _fields_ = [
            (14, 'Unused'),
            (1, 'Exclusive'),
            (1, 'No selection'),
        ]
    @pbinary.littleendian
    class _Font_flags(pbinary.flags):
        _fields_ = [
            (4, 'Unused'),
            (1, 'Current TrueType'),
            (1, 'Current Raster'),

            (5, 'Unknown'),
            (1, 'Automatic size'),

            (1, 'Use TrueType'),
            (1, 'Use Raster'),
            (2, 'Reserved'),
        ]
    @pbinary.littleendian
    class _Bit_mask4(pbinary.flags):
        _fields_ = [
            (14, 'Unused'),
            (1, 'Show toolbar'),
            (1, 'Unknown'),
        ]
    @pbinary.littleendian
    class _Last_maximized_flags(pbinary.flags):
        _fields_ = [
            (14, 'Unknown'),
            (1, 'Last maximized'),
            (1, 'Reserved'),
        ]
    class _Last_window_state(pint.enum, pint.uint16_t):
        _values_ = [
            ('Normal', 1),
            ('Minimized', 2),
            ('Maximized', 3),
        ]
    class _Border_position(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'left'),
            (pint.uint16_t, 'top'),
            (pint.uint16_t, 'right'),
            (pint.uint16_t, 'bottom'),
        ]
    _fields_ = [
        (dyn.block(88), 'Unknown_0'),
        (dyn.clone(pstr.string, length=80), 'Icon filename'),
        (pint.uint16_t, 'Icon number'),
        (_Bit_mask1, 'Bit mask 1'),
        (dyn.block(10), 'Unknown_ac'),
        (pint.uint16_t, 'Priority'),
        (_Bit_mask2, 'Bit mask 2'),
        (dyn.block(8), 'Unknown_ba'),
        (pint.uint16_t, 'Number of lines'),
        (_Bit_mask3, 'Bit mask 3'),
        (pint.uint16_t, 'Unknown_c6'),
        (pint.uint16_t, 'Unknown_c8'),
        (pint.uint16_t, 'Unknown_ca'),
        (pint.uint16_t, 'Unknown_cc'),
        (pint.uint16_t, 'Unknown_ce'),
        (pint.uint16_t, 'Unknown_d0'),
        (pint.uint16_t, 'Unknown_c2'),
        (pint.uint16_t, 'Unknown_c4'),
        (_Mouse_flags, 'Mouse flags'),
        (dyn.block(6), 'Unknown_d8'),
        (_Font_flags, 'Font flags'),
        (pint.uint16_t, 'Unknown_e0'),
        (_Dimensions, 'Raster font size'),
        (_Dimensions, 'Current font size'),
        (dyn.clone(pstr.string, length=32), 'Raster font name'),
        (dyn.clone(pstr.string, length=32), 'TrueType font name'),
        (pint.uint16_t, 'Unknown_12a'),
        (_Bit_mask4, 'Bit mask 4'),
        (pint.uint16_t, 'No restore settings'),
        (_Dimensions, 'Screen symbol size'),
        (_Dimensions, 'Client area size'),
        (_Dimensions, 'Window size'),
        (pint.uint16_t, 'Unknown_13c'),
        (_Last_maximized_flags, 'Last maximized'),
        (_Last_window_state, 'Last start'),
        (_Border_position, 'Maximized border position'),
        (_Border_position, 'Normal border position'),
        (pint.uint32_t, 'Unknown_152'),
        (dyn.clone(pstr.string, length=80), 'BAT file name'),
        (pint.uint16_t, 'Environment size'),
        (pint.uint16_t, 'DPMI memory volume'),
        (pint.uint16_t, 'Unknown_1aa'),
    ]

@SectionData.define
class WindowsNT31Section(pstruct.type):
    type = 0x8c
    _fields_ = [
        (pint.uint16_t, 'Hardware timer emulation'),
        (dyn.block(10), 'Unknown_2'),
        (dyn.clone(pstr.string, length=64), 'CONFIG.NT filename'),
        (dyn.clone(pstr.string, length=64), 'AUTOEXEC.NT filename'),
    ]

@SectionData.define
class WindowsNT40Section(pstruct.type):
    type = 0x68c

    _fields_ = [
        (pint.uint32_t, 'Unknown_0'),
        (dyn.clone(pstr.wstring, length=128), 'Unicode parameters'),
        (dyn.clone(pstr.string, length=128), 'Ascii parameters'),
        (dyn.block(240), 'Unknown_184'),
        (dyn.clone(pstr.wstring, length=80), 'Unicode PIF filename'),
        (dyn.clone(pstr.string, length=80), 'Ascii PIF filename'),
        (dyn.clone(pstr.wstring, length=30), 'Unicode window title'),
        (dyn.clone(pstr.string, length=30), 'Ascii window title'),
        (dyn.clone(pstr.wstring, length=80), 'Unicode icon filename'),
        (dyn.clone(pstr.string, length=80), 'Ascii icon filename'),
        (dyn.clone(pstr.wstring, length=64), 'Unicode working directory'),
        (dyn.clone(pstr.string, length=64), 'Ascii working directory'),
        (dyn.block(286), 'Unknown_56e'),
    ]

class Sections(parray.terminated):
    _object_ = Section

    def isTerminator(self, item):
        res = item['heading']
        return res['NextOffset'].int() == 0xffff

class File(pstruct.type):
    _fields_ = [
        (BasicSection, 'basicSection'),
        (Heading, 'basicHeading'),
        (Sections, 'sections'),
    ]

    def enumerate(self):
        item = self['basicHeading']
        yield item['Name'].str(), item['Offset'].d.li
        while item['NextOffset'].int() < 0xffff:
            res = item['NextOffset'].d.li
            item = res['heading']
            yield item['Name'].str(), item['Offset'].d.li
        return

    def iterate(self):
        for _, item in self.enumerate():
            yield item
        return

if __name__ == '__main__':
    import ptypes, local.pif as PIF
    ptypes.setsource(ptypes.prov.file('/home/user/work/syringe/template/samples/_default.pif','rb'))

    z = PIF.File()
    z=z.l

    for name, item in z.enumerate():
        print(name)
        print(item)

    for item in z.iterate():
        print(item)
