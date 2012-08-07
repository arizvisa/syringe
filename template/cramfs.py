from ptypes import *

class u32(pint.uint32_t): pass
class u16(pint.uint16_t): pass
class u8(pint.uint8_t): pass

class inode(pbinary.struct):
    _fields_ = [
        (16, 'mode'),
        (16, 'uid'),
        (24, 'size'),
        (8, 'gid'),
        (6, 'namelen'),
        (26, 'offset'),
    ]
    
class info(pstruct.type):
    _fields_ = [
        (u32, 'crc'),
        (u32, 'edition'),
        (u32, 'blocks'),
        (u32, 'files'),
    ]

class super(pstruct.type):
    _fields_ = [
        (u32, 'magic'),     # defaults to 0x28cd3d45      
        (u32, 'size'),
        (u32, 'flags'),
        (u32, 'future'),
        (dyn.array(u8,16), 'signature'),
        (info, 'fsid'),
        (dyn.array(u8,16), 'name'),
        (inode, 'root'),
    ]

if __name__ == '__main__':
    import ptypes,cramfs
    ptypes.setsource('re1000.fw')

    a = cramfs.super()
    a.setoffset(0):
    a=a.l
