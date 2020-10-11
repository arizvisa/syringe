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
class OfficeArtClientData(ptype.type):
    type = 0,0x000

@FT_OfficeArtClientTextBox.define
class OfficeArtClientTextBox(ptype.type):
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

    class __short(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'Flag'),
            (pint.uint16_t, 'Col1'),
            (pint.uint16_t, 'DX1'),
            (pint.uint16_t, 'Row1'),
        ]

    class __long(pstruct.type):
        _fields_ = [
            (pint.uint16_t, 'DY1'),
            (pint.uint16_t, 'Col2'),
            (pint.uint16_t, 'DX2'),
            (pint.uint16_t, 'Row2'),
            (pint.uint16_t, 'DY2'),
        ]

    _fields_ = [
        (lambda s: pint.uint64_t if s.blocksize() == 8 else s.__short, 'short'),
        (lambda s: s.__long if s.blocksize() >= 18 else ptype.type, 'long'),
        (lambda s: dyn.clone(ptype.block, length=s.blocksize()-(s['short'].li.size()+s['long'].li.size())), 'extra'),
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

