import sys
sys.path.append('c:/users/arizvisa')

import ptypes
from ptypes import pstruct,parray,ptype
from ptypes import dyn,pint,pstr
from ptypes.pint import uint8_t,uint16_t,uint32_t,int16_t
from ptypes import utils

## primitive types
class ULONG(uint32_t): pass
class USHORT(uint16_t): pass

class OFFSET(int16_t): pass
class SECT(pint.penum, ULONG):
    _fields_ = [
        ('DIFSECT', 0xfffffffc),
        ('FATSECT', 0xfffffffd),
        ('ENDOFCHAIN', 0xfffffffe),
        ('FREESECT', 0xffffffff)
    ]
class FSINDEX(ULONG): pass
class FSOFFSET(USHORT): pass
class DFSIGNATURE(ULONG): pass

class BYTE(uint8_t): pass
class WORD(uint16_t): pass
class DWORD(uint32_t): pass

class DFPROPTYPE(WORD): pass
class SID(ULONG): pass

class CLSID(dyn.block(16)): pass
class GUID(CLSID): pass

class TIME_T(pstruct.type):
    _fields_ = [(DWORD, 'dwLowDateTime'), (DWORD, 'dwHighDateTime')]
FILE_TIME = TIME_T

class WCHAR(pstr.wchar_t): pass

## file header
class StructuredStorageHeader(pstruct.type):
    _fields_ = [
        (dyn.array(BYTE, 8), '_abSig'),
        (CLSID, '_clid'),
        (USHORT, '_uMinorVersion'),
        (USHORT, '_uDllVersion'),
        (USHORT, '_uByteOrder'),

        (USHORT, '_uSectorShift'),
        (USHORT, '_uMiniSectorShift'),

        (USHORT, '_usReserved'),
        (ULONG, '_ulReserved1'),
        (ULONG, '_ulReserved2'),

        (FSINDEX, '_csectFat'),     # number of sectors for the fat
        (SECT, '_sectDirStart'),    # directory sid
        (DFSIGNATURE, '_signature'),

        (ULONG, '_ulMiniSectorCutoff'),
        (SECT, '_sectMiniFatStart'),
        (FSINDEX, '_csectMiniFat'),

        (SECT, '_sectDifStart'),    # contains rest of FAT
        (FSINDEX, '_csectDif'),
        (dyn.array(SECT, 109), '_sectFat') # FAT
    ]

    def getsector(self, n):
        if n in [v for k,v in SECT._fields_]:
            raise ValueError('Invalid sector number %d'% n)
            
        size = 1<<int(self['_uSectorShift'])
        ofs = self.size() + n * size
        return self.newelement(dyn.block(size), 'Sector[%d]'% n, ofs)

    def getallocationtable(self, n):
        # XXX: check that n is not End-of-Chain, or any of our other SectorEnum.consants
        sector = self.getsector(n)
        sector.load()
        
        count = sector.size() / SECT.length
        return self.newelement(dyn.array(SECT, count), 'AllocationTable', sector.getoffset())

    def getdirectoryentry(self, n):
        size = 1<<int(self['_uSectorShift'])
        ofs = self.size() + n * size
        res = dyn.array(StructuredStorageDirectoryEntry, size / StructuredStorageDirectoryEntry_size)
        return self.newelement(res, 'Directory[%d]'%n, ofs)

    def getdata(self, chain):
        '''Fetches specified chain out of the FAT'''
        # XXX: verify chain is composed of valid sectors
        return ''.join([ self.getsector(int(x)).load().serialize() for x in chain ])

    def getfat(self):
        next = int(self['_sectDifStart'])
        endofchain = int(self['_sectDifStart']['ENDOFCHAIN'])

        fat = [x for x in self['_sectFat']]

        while next != endofchain:
            raise NotImplementedError("DIF hasn't been tested really.")
            v = self.getallocationtable(next)
            fat.extend(v)
            next = int(v[-1] )
        return fat

    if False:
        def getmsat(self):
            next = int(self['_sectDifStart'])
            endofchain = int(self['_sectDifStart']['ENDOFCHAIN'])

            msat = [x for x in self['_sectFat']]

            while next != endofchain:
                v = self.getallocationtable(next)
                msat.extend(v)
                next = int(v[-1] )
            return msat

        def getsat(self, msat=None):
            if msat is None:
                return self.getsat( self.getmsat() )
            return [msat[n] for n in range(int(self['_csectFat']))]

        def getstreams(self, sat=None):
            raise NotImplementedError
            if sat is None:
                return self.getstreams( self.getsat() )
            # sat should be a list of indexes including streams

            streams = {}
            index = 0
            for n in sat:
                try:
                    streams[index].append(n)
                except KeyError:
                    streams[index] = []
                    streams[index].append(n)

                if n == n['ENDOFCHAIN']:
                    index += 1
                continue
            return streams

    def getdirectory(self):
        start = int(self['_sectDirStart'])
        res = self.getdirectoryentry(start)
        raise NotImplementedError

## directory
class STGTY(pint.penum, BYTE):
    _fields_ = [
        ('INVALID', 0),
        ('STORAGE', 1),
        ('STREAM', 2),
        ('LOCKBYTES', 3),
        ('PROPERTY', 4),
        ('ROOT', 5)
    ]

class DECOLOR(pint.penum, BYTE):
    _fields_ = [('RED', 0), ('BLACK', 1)]

class StructuredStorageDirectoryEntry(pstruct.type):
    _fields_ = [
        (pstr.new(32, pstr.wstring), '_ab'),
        (WORD, '_cb'),
        (STGTY, '_mse'),
        (DECOLOR, '_bflags'),
        (SID, '_sidLeftSib'),
        (SID, '_sidRightSib'),
        (SID, '_sidChild'),
        (GUID, '_clsId'),
        (DWORD, '_dwUserFlags'),
        (dyn.array(TIME_T,2), '_time'),
        (SECT, '_sectStart'),           # Fat start
        (ULONG, '_ulSize'),             # stream size
        (DFPROPTYPE, '_dptPropType'),
        (lambda self: dyn.block(128 - self.size()), '__padding__')
    ]
    
StructuredStorageDirectoryEntry_size = StructuredStorageDirectoryEntry().load().size()

if __name__ == '__main__':
    import cdoc; reload(cdoc)
    import ptypes
    from ptypes import utils

    self = cdoc.StructuredStorageHeader()
    self.source = ptypes.provider.file('../org.fpx')
    self.load()

    fat = self.getfat()

    start = int(self['_sectMiniFatStart'])
    minifat = self.getallocationtable(start).load()
    print repr([x.get() for x in minifat])
    print repr([x.get() for x in fat])

    sys.exit()
        
    def getchain(fat):
        if fat[0] == 'ENDOFCHAIN':
            return []
        # XXX: should probably do something here if the chain we fetch isn't valid
        if fat[0] in SECT.values():
            raise NotImplementedError( repr(fat[0]) )
        return [fat[0]] + getchain(fat[1:])


    ## every file
#    for n in self.getdirectoryentry(1).load():
#        print repr(n['_ab'].get())
#        print n['_mse']
#        print 'sector', n['_sectStart']
#        print 'size', n['_ulSize'], self['_ulMiniSectorCutoff']
#
#        start = int(n['_sectStart'])
#        size = int(n['_ulSize'])
#        chain = getchain(table[ start: ])
#
#        data = self.getdata(chain)
#        print utils.hexdump(data)

    directory = self.getdirectoryentry(1).load()[0]
    print directory

    start = int(directory['_sectStart'])
    chain = getchain(table[ start:]) 
    print repr(chain)

    minisector = int(directory['_sectStart'])
    print utils.hexdump(self.getdata(chain)[:int(directory['_ulSize'])])
#    print utils.hexdump(self.getdata(chain))

#    blah = self.getallocationtable(int(table[minisector]))
#    print repr(blah.load())
