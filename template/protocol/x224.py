import ptypes
from ptypes import *

import functools,operator,itertools,types
import logging

ptypes.setbyteorder(ptypes.config.byteorder.bigendian)

### X.224 Variable
class X224Variable(ptype.definition):
    cache = {}

@X224Variable.define
class CR_TPDU(pstruct.type):
    '''Conection Request'''
    type = 0xe

    class _class_option(pbinary.struct):
        _fields_ = [
            (4, 'class'),
            (4, 'option'),
        ]

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint16_t, 'SRC-REF'),
        (_class_option, 'CLASS-OPTION'),
    ]

@X224Variable.define
class CC_TPDU(pstruct.type):
    '''Connection Confirm'''
    type = 0xd
    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint16_t, 'SRC-REF'),
        (CR_TPDU._class_option, 'CLASS-OPTION'),
    ]

@X224Variable.define
class DR_TPDU(pstruct.type):
    '''Disconnect Request'''
    type = 0x8

    class _reason(pint.enum, pint.uint8_t):
        # XXX: this enumeration is incomplete (ITU-T Rec. X.224 page 63)
        _values_ = [
            ('Normal disconnect initiated by session entity', 128+0),
            ('Connection negotiation failed', 128+2),
            ('Protocol error', 128+5),
            ('Reference overflow', 128+7),
            ('Header or parameter length invalid', 128+10),
        ]

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint16_t, 'SRC-REF'),
        (CR_TPDU._class_option, 'class-option'),
        (_reason, 'REASON'),
    ]

@X224Variable.define
class DC_TPDU(pstruct.type):
    '''Disconnect Confirm'''
    type = 0xc

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint16_t, 'SRC-REF'),
    ]

class EOT_NR(pbinary.struct):
    class unused(pbinary.enum):
        width, _values_ = 7, []

    def __nr(self):
        res = self['EOT']
        return EOT_NR.unused if res else 7

    _fields_ = [
        (1, 'EOT'),
        (__nr, 'NR'),
    ]

@X224Variable.define
class DT_TPDU(EOT_NR):
    '''Data (Class 0 and 1)'''
    type = 0xf

@X224Variable.define
class ED_TPDU(pstruct.type):
    '''Expedited Data'''
    type = 0x1

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (EOT_NR, 'ED-TPDU-NR'),
    ]

@X224Variable.define
class AK_TPDU(pstruct.type):
    '''Data Acknowledgement'''
    type = 0x6

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint8_t, 'YR-TPDU-NR'),
    ]

@X224Variable.define
class EA_TPDU(pstruct.type):
    '''Expedited Data Acknowledgement'''
    type = 0x2

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint8_t, 'YR-EDTU-NR'),
    ]

@X224Variable.define
class RJ_TPDU(pstruct.type):
    '''Reject'''
    type = 0x5

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (pint.uint8_t, 'YR-TU-NR'),
    ]

@X224Variable.define
class ER_TPDU(pstruct.type):
    '''Error'''
    type = 0x7

    class _cause(pint.enum, pint.uint8_t):
        _values_ = [
            ('Reason not specified', 0),
            ('Invalid parameter code', 1),
            ('Invalid TPDU type', 2),
            ('Invalid parameter value', 3),
        ]

    _fields_ = [
        (pint.uint16_t, 'DST-REF'),
        (_cause, 'CAUSE'),
    ]

### X.224 Parameters
class X224Param(ptype.definition):
    cache = {}

class X224Parameter(pstruct.type):
    def __value(self):
        res, cb = self['code'].li, self['length'].li
        res = X224Param.lookup(res)
        return dyn.block(cb)

    _fields_ = [
        (pint.uint8_t, 'code'),
        (pint.uint8_t, 'flags'),
        (pint.uint16_t, 'length'),
        (__value, 'value'),
    ]

class X224ParameterArray(parray.block):
    _object_ = X224Parameter

### Unused X.224 parameters
# @X224Param.define
# class RDPNegotiationRequest(pint.uint32_t, pint.enum):
#     type = 0x01
#     _values_ = [
#         ('PROTOCOL_RDP', 0x00000000),
#         ('PROTOCOL_SSL', 0x00000001),
#         ('PROTOCOL_HYBRID', 0x00000002),
#     ]
# @X224Param.define
# class RDPNegotiationResponse(pint.uint32_t, pint.enum):
#     type = 0x02
#     _values_ = [
#         ('PROTOCOL_RDP', 0x00000000),
#         ('PROTOCOL_SSL', 0x00000001),
#         ('PROTOCOL_HYBRID', 0x00000002),
#     ]
# @X224Param.define
# class RDPNegotiationFailure(pint.uint32_t, pint.enum):
#     type = 0x02
#     _values_ = [
#         ('SSL_REQUIRED_BY_SERVER', 0x00000001),
#         ('SSL_NOT_ALLOWED_BY_SERVER', 0x00000002),
#         ('SSL_CERT_NOT_ON_SERVER', 0x00000003),
#         ('INCONSISTENT_FLAGS', 0x00000004),
#         ('HYBRID_REQUIRED_BY_SERVER', 0x00000005),
#         ('SSL_WITH_USER_AUTH_REQUIRED_BY_SERVER', 0x00000006),
#     ]

### X.224 TPDU
class TPDU(pstruct.type):
    class _type(pbinary.struct):
        class code(pbinary.enum):
            width, _values_ = 4, [
                ('Connection request', 0xe),
                ('Connection confirm', 0xd),
                ('Disconenct request', 0x8),
                ('Disconnect confirm', 0xc),
                ('Data', 0xf),
                ('Expedited data', 0x1),
                ('Data acknowledgement', 0x6),
                ('Expedited data acknowledgement', 0x2),
                ('Reject', 0x5),
                ('Error', 0x7),
            ]

        _fields_ = [
            (code, 'high'),
            (4, 'low'),
        ]

    def __variable(self):
        res, fixed = self['length'].li.int(), self['type'].li.size()
        if res < fixed:
            logging.info("{:s} : length is too short ({:d} < {:d})".format(self.shortname(), res, fixed))
            return dyn.block(0)
        variable = res - fixed

        res = self['type'].li
        hi, lo = res['high'], res['low']

        return X224Variable.withdefault(hi, ptype.block, length=variable)

    def __parameters(self):
        res = self['length'].li.int()
        parameters = sum(self[fld].li.size() for fld in ['type','variable'])
        if res >= parameters:
            return dyn.block(res - parameters)
        logging.info("{:s} : length is too short ({:d} < {:d})".format(self.shortname(), res, parameters))
        return dyn.block(0)

    _fields_ = [
        (pint.uint8_t, 'length'),
        (_type, 'type'),
        (__variable, 'variable'),
        (__parameters, 'parameters'),
    ]
    
    def summary(self):
        res = []
        res.append("length={:#x}".format(self['length'].int()))

        t = self['type']
        res.append("type={:s}({:#x}, {:#06b})".format(t.__field__('high').str(), t['high'], t['low']))

        res.append("variable={:s}".format(self['variable'].summary()))

        if self['parameters'].size() > 0:
            res.append("parameters=...{:d} bytes...".format(self['parameters'].size()))

        return ' '.join(res)

### X.224 TPKT
class TPKT(pstruct.type):
    def __reserved(self):
        res = self['version'].li
        return pint.uint8_t if res.int() == 3 else pint.uint16_t

    def __tpdu(self):
        res = sum(self[fld].li.size() for fld in ['version','reserved','length'])
        return dyn.clone(TPDU, blocksize=lambda self, cb=self['length'].int() - res: cb)

    def __userdata(self):
        res = sum(self[fld].li.size() for fld in ['version','reserved','length','tpdu'])
        return dyn.block(self['length'].li.int() - res)

    _fields_ = [
        (pint.uint8_t, 'version'),
        (__reserved, 'reserved'),
        (pint.uint16_t, 'length'),
        (TPDU, 'tpdu'),
        (__userdata, 'data'),
    ]

if __name__ == '__main__':
    import user, ptypes, x224
    from user import *

### connection request
    data = "030000221de00000000000" + "Cookie: mstshash=hash\r\n".encode('hex')
    ptypes.setsource(ptypes.prov.string(data.decode('hex')))

    reload(x224)
    a = x224.TPKT()
    a = a.l
    print a['data']

    ### client mcs erect domain request
    data = "0300000c02f0800401000100"
    data = "0300000802f08028"
    data = "0300000c02f08038000603eb"
    ptypes.setsource(ptypes.prov.string(data.decode('hex')))

    reload(x224)
    a = x224.TPKT()
    a = a.l
    print a['data']
