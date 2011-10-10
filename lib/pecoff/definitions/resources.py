import ptypes,headers
from ptypes import pstruct,parray,pbinary,dyn,pstr
from __base__ import *
from headers import virtualaddress

class IMAGE_RESOURCE_DIRECTORY(pstruct.type):
    _fields_ = [
        (dword, 'Characteristics'),
        (dword, 'TimeDateStamp'),
        (word, 'MajorVersion'),
        (word, 'MinorVersion'),
        (word, 'NumberOfNames'),
        (word, 'NumberOfIds'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_TABLE_NAME, length=int(s['NumberOfNames'].l)), 'Names'),
        (lambda s: dyn.clone(IMAGE_RESOURCE_DIRECTORY_TABLE_ID, length=int(s['NumberOfIds'].l)), 'Ids'),
    ]

class IMAGE_RESOURCE_DIRECTORY_STRING(pstruct.type):
    _fields_ = [
        (word, 'Length'),
        (lambda s: dyn.clone(pstr.wstring,length=int(s['Length'].l)), 'String')
    ]

class IMAGE_RESOURCE_DATA_ENTRY(pstruct.type):
    _fields_ = [
        (virtualaddress(lambda s: dyn.block(s.parent['Size'].l)), 'Data RVA'),
        (dword, 'Size'),
        (dword, 'Codepage'),
        (dword, 'Reserved'),       
    ]

class IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA(pbinary.littleendian(pbinary.struct)):
    _fields_ = [(1,'type'),(31,'address')]
    def deref(self):
        n = self['address']
        base = self.getparent(headers.datadirectory.Resource)['VirtualAddress'].d
        makepointer = lambda x: dyn.rpointer(x, object=lambda s: base)
        p = [makepointer(IMAGE_RESOURCE_DATA_ENTRY), makepointer(IMAGE_RESOURCE_DIRECTORY_TABLE)][self['type'] == 1]
        return self.parent.newelement(p, 'RVA', self.getoffset()).set(n).d

    d = property(fget=deref)

class IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME(pstruct.type):
    _fields_ = [
        (virtualaddress(IMAGE_RESOURCE_DIRECTORY_STRING), 'Name RVA'),
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA, 'RVA'),
    ]
class IMAGE_RESOURCE_DIRECTORY_ENTRY_ID(pstruct.type):
    _fields_ = [
        (dword, 'IntegerID'),
        (IMAGE_RESOURCE_DIRECTORY_ENTRY_RVA, 'RVA'),
    ]

class IMAGE_RESOURCE_DIRECTORY_TABLE(IMAGE_RESOURCE_DIRECTORY):
    pass
class IMAGE_RESOURCE_DIRECTORY_TABLE_NAME(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME
class IMAGE_RESOURCE_DIRECTORY_TABLE_ID(parray.type):
    _object_ = IMAGE_RESOURCE_DIRECTORY_ENTRY_NAME

if __name__ == '__main__':
    import pecoff
    z = pecoff.Executable.open('c:/Program Files (x86)/Debugging Tools for Windows (x86)/windbg.exe')

    a = z['Pe']['OptionalHeader']['DataDirectory'][2]['VirtualAddress'].d.l
    b = a['Ids'][0]
    print b['Name RVA']
    print b['RVA']

#    from pecoff.definitions.headers import RelativeAddress,RelativeOffset
#    from pecoff.definitions.resources import DataDirectory

#    print DataDirectory(b['RVA']['address'])
