import sys, ptypes, elf
from ptypes import *

if __name__ == '__main__':
    import logging
    source = ptypes.setsource(ptypes.prov.file(sys.argv[1], 'rb'))
    z = elf.File(source=source)
    z=z.l

    e = z['e_data']
    sh, ph = (e[fld].d for fld in ['e_shoff', 'e_phoff'])

    ph = ph.l if e['e_phoff'].int() else ph
    sh = sh.l if e['e_shoff'].int() else sh

    d = next(item['p_vaddr'].d for item in ph if item['p_type']['DYNAMIC'])
    d=d.l

    dt_strtab, dt_symtab = (d.bytag(item).getparent(elf.dynamic.ElfXX_Dyn) for item in ['DT_STRTAB', 'DT_SYMTAB'])
    strtab, symtab = (item['d_un'].d.l for item in [dt_strtab, dt_symtab])
