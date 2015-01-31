import pecoff,ptypes
from ptypes import *
ptypes.setsource( ptypes.prov.file('./kernel32.dll', mode='r') )

a = pecoff.Executable.File()
a=a.l
exp = a['Next']['Header']['DataDirectory'][0]['Address'].d.l
imp = a['Next']['Header']['DataDirectory'][1]['Address'].d.l
b = a['next']['header']['datadirectory']
print b[12]
print b[13]
print b[10]['address'].d.l

# exports
print exp.getNames()
print exp.getNameOrdinals()
print exp.getExportAddressTable()
print '\n'.join(map(repr,exp.iterateExports()))

# imports
b = imp[5]

print b['Name'].d.l.str()
print '\n'.join(map(repr,b.iterateImports()))

c = b['INT'].d.l[0]
print c['Name'].deref()
print c['Name'].getName()
print c['Name']
print c['Name'].details()
print c['Name'].summary()

print c['Ordinal'].getOrdinal()
print c['Ordinal']
print c['Ordinal'].details()
print c['Ordinal'].summary()

# delayload imports
