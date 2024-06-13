import ptypes
from ptypes import *

from . import layer, stackable, terminal, datalink
from . import inet4, inet6

pint.setbyteorder(ptypes.config.byteorder.bigendian)

class u_char(pint.uint8_t): pass
class u_short(pint.uint16_t): pass

class ar_hrd(datalink.layer.enum, u_short):
    pass

class hwtypes(ptype.definition):
    cache = { ar_hrd.byname(id, id) : header for id, header in [
        ('Ethernet', datalink.ethernet.lladdr),
    ]}

class ar_pro(layer.enum, u_short):
    pass

class ethertypes(ptype.definition):
    cache = { ar_pro.byname(id, id) : header for id, header in [
        ('IP', inet4.in_addr),
        ('IP6', inet6.in6_addr),
    ]}

class ar_op(pint.enum, u_short):
    _values_ = [
        ('REQUEST', 1),
        ('REPLY', 2),
        ('request-Reverse', 3),
        ('reply-Reverse', 4),
        ('DRARP-Request', 5),
        ('DRARP-Reply', 6),
        ('DRARP-Error', 7),
        ('InARP-Request', 8),
        ('InARP-Reply', 9),
        ('ARP-NAK', 10),
        ('MARS-Request', 11),
        ('MARS-Multi', 12),
        ('MARS-MServ', 13),
        ('MARS-Join', 14),
        ('MARS-Leave', 15),
        ('MARS-NAK', 16),
        ('MARS-Unserv', 17),
        ('MARS-SJoin', 18),
        ('MARS-SLeave', 19),
        ('MARS-Grouplist-Request', 20),
        ('MARS-Grouplist-Reply', 21),
        ('MARS-Redirect-Map', 22),
        ('MAPOS-UNARP', 23),
        ('OP_EXP1', 24),
        ('OP_EXP2', 25),
    ]

@datalink.layer.define
class arphdr(pstruct.type, terminal):
    type = 0x0806
    def __hardware_address(self):
        res, length = (self[fld].li for fld in ['ar_hrd', 'ar_hln'])
        hrd_t = hwaddr.lookup(res.int())
        if hasattr(hrd_t, 'length') and hrd_t.length != length.int():
            return dyn.clone(hrd_t, length=length.int())
        return hrd_t

    def __protocol_address(self):
        res, length = (self[fld].li for fld in ['ar_pro', 'ar_pln'])
        pro_t = ethertypes.lookup(res.int())
        if hasattr(pro_t, 'length') and pro_t.length != length.int():
            return dyn.clone(pro_t, length=length.int())
        return pro_t

    _fields_ = [
        (ar_hrd, 'ar_hrd'),
        (ar_pro, 'ar_pro'),
        (u_char, 'ar_hln'),
        (u_char, 'ar_pln'),
        (ar_op, 'ar_op'),

        (__hardware_address, 'ar_sha'),
        (__protocol_address, 'ar_spa'),

        (__hardware_address, 'ar_tha'),
        (__protocol_address, 'ar_tpa'),
    ]

    def alloc(self, **fields):
        res = super(arphdr, self).alloc(**fields)
        if 'ar_hln' not in fields:
            res['ar_hln'].set(max(res[fld].size() for fld in ['ar_sha', 'ar_tha']))
        if 'ar_pln' not in fields:
            res['ar_pln'].set(max(res[fld].size() for fld in ['ar_spa', 'ar_tpa']))
        if 'ar_hrd' not in fields:
            iterable = (res[fld].type for fld in ['ar_sha', 'ar_tha'] if hasattr(res[fld], 'type'))
            ar_hrd = next(iterable, None)
            res['ar_hrd'].set(ar_hrd) if ar_hrd is not None else res['ar_hrd']
        if 'ar_pro' not in fields:
            iterable = (res[fld].type for fld in ['ar_spa', 'ar_tpa'] if hasattr(res[fld], 'type'))
            ar_pro = next(iterable, None)
            res['ar_pro'].set(ar_pro) if ar_pro is not None else res['ar_pro']
        return res

header = arphdr
