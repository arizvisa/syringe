import ptypes
from ptypes import *
from . import *

ptypes.setbyteorder(ptypes.config.byteorder.littleendian)
pbinary.setbyteorder(ptypes.config.byteorder.littleendian)

recordType = [
    ('FT_OfficeArtClientAnchorChart', 0xf010),
    ('FT_OfficeArtClientData', 0xf011),
    ('FT_OfficeArtClientTextBox', 0xf00d),
]

# create a ptype.definition for each record type
locals().update(map(RecordType.define,recordType))

# record types from [MS-OGRAPH]
@FT_OfficeArtClientData.define
class OfficeArtClientData(undefined):
    type = 0,0x000

@FT_OfficeArtClientTextBox.define
class OfficeArtClientTextBox(undefined):
    type = 0,0x000

@FT_OfficeArtClientAnchorChart.define
class OfficeArtClientAnchorChart(pstruct.type):
    type = 0,0x000

    #copied from http://svn.apache.org/viewvc/poi/trunk/src/java/org/apache/poi/ddf/EscherClientAnchorRecord.java?view=annotate

    _fields_ = [
        (pint.uint16_t, 'Flag'),
        (pint.uint16_t, 'Col1'),
        (pint.uint16_t, 'DX1'),
        (pint.uint16_t, 'Row1'),

        (pint.uint16_t, 'DY1'),
        (pint.uint16_t, 'Col2'),
        (pint.uint16_t, 'DX2'),
        (pint.uint16_t, 'Row2'),
        (pint.uint16_t, 'DY2'),
    ]

    class _short(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Flag'),
            (pint.uint16_t, 'Col1'),
            (pint.uint16_t, 'DX1'),
            (pint.uint16_t, 'Row1'),
        ]

    class _long(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'DY1'),
            (pint.uint16_t, 'Col2'),
            (pint.uint16_t, 'DX2'),
            (pint.uint16_t, 'Row2'),
            (pint.uint16_t, 'DY2'),
        ]

    def __short(self):
        try:
            p = self.getparent(RecordGeneral)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return self._short
        return pint.uint64_t if cb == 8 else self._short

    def __long(self):
        try:
            p = self.getparent(RecordGeneral)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return self._short
        return self._long if cb >= 18 else ptype.type

    def __extra(self):
        try:
            p = self.getparent(RecordGeneral)
            cb = p['header'].li.Length()
        except (ptypes.error.ItemNotFoundError, ptypes.error.InitializationError):
            return self._short
        return dyn.clone(ptype.block, length=cb - (self['short'].li.size() + self['long'].li.size()))

    _fields_ = [
        (__short, 'short'),
        (__long, 'long'),
        (__extra, 'extra'),
    ]

# FIXME
class DataFormat(pstruct.type):
    _fields_ = [
        (pint.uint16_t, 'xi'),
        (pint.uint16_t, 'yi'),
        (pint.uint16_t, 'iss'),
        (pint.uint16_t, 'fXL4iss'),     # XXX: this should be a pbinary.struct
    ]

if __name__ == '__main__':
    from ptypes import *
    import office.graph as graph

