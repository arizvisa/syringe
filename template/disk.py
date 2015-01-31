from ptypes import *

class sector(dyn.block(512)): pass

class partition_table_entry(pstruct.type):
    class chs(pbinary.struct):
        _fields_ = [(8,'head'),(6,'sector'),(10,'cylinder')]

    _fields_ = [
        (pint.uint8_t, 'boot_indicator'),
        (chs, 'chs_start'),
        (pint.uint8_t, 'type'),
        (chs, 'chs_end'),
        (pint.uint32_t, 'relative_sector'),
        (pint.uint32_t, 'total_sectors'),
    ]

class common_boot_record(pstruct.type):
    _fields_ = [
        (dyn.block(446), 'bootstrap'),
        (dyn.array(partition_table_entry, 4), 'partition'),
        (pint.uint16_t, 'mbr_signature'),
    ]

if __name__ == '__main__':
    import disk,ptypes
    ptypes.setsource(ptypes.provider.WindowsFile(r'\\.\PhysicalDrive%d'% (0), 'r'))

    a = disk.sector()
    print a.l.cast(disk.common_boot_record)['partitions'][0]['chs_start'].hexdump()
    b = a.l.cast(disk.common_boot_record)
    print b
