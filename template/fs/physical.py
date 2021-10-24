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
    class _mbr_signature(pint.uint16_t):
        def default(self):
            return self.set(0xaa55)
        def valid(self):
            return self.int() == self.copy().default().int()
        def properties(self):
            res = super(common_boot_record._mbr_signature, self).properties()
            if self.initializedQ() and self.valid():
                res['valid'] = self.valid()
            return res
        def alloc(self, **attrs):
            res = super(common_boot_record._mbr_signature, self).alloc(**attrs)
            return res.default()

    _fields_ = [
        (dyn.block(440), 'bootstrap'),
        (pint.uint32_t, 'uuid'),
        (pint.uint16_t, 'unknown'),
        (dyn.array(partition_table_entry, 4), 'partition'),
        (_mbr_signature, 'mbr_signature'),
    ]

if __name__ == '__main__':
    import ptypes, fs.physical as disk
    ptypes.setsource(ptypes.provider.WindowsFile(r'\\.\PhysicalDrive%d'% (0), 'r'))

    a = disk.sector()
    print(a.l.cast(disk.common_boot_record)['partitions'][0]['chs_start'].hexdump())
    b = a.l.cast(disk.common_boot_record)
    print(b)
