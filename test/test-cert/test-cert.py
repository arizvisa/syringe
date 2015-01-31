import ptypes,pecoff
from ptypes import *
ptypes.setsource(ptypes.prov.file('c:/windows/sysnative/ntdll.dll', 'r'))
z = pecoff.Executable.File()
z=z.l
a = z['next']['header']['datadirectory'][4]['Address'].d.l
a = z['next']['header']['certificate']
#print a['bCertificate'].hexdump()
c = a[0]['bCertificate']
file('./ntdll.cert.pkcs7','wb').write(c.serialize())
print c.hexdump(lines=1)

import ber; reload(ber)
d = c.cast(ber.Record, recurse={'byteorder':ptypes.config.byteorder.bigendian})

print d['value']
print d['value'][0]
print d['value'][1]['Value']

e = d['value'][1]['Value'].cast(ber.Record)
print e['Value'][0]
print e['Value'][1]['Value'][0]
print e['Value'][2]['Value'][0]

print e['Value'][2]['Value'][1]['Value']
f = e['Value'][2]['Value'][1]['Value'].cast(ber.Record)
print f['Value'][0]['Value'][0]
print f['Value'][0]['Value'][1]['Value'][0]
print f['Value'][0]['Value'][1]['Value'][1]['Value'].cast(ber.Record)['Value'].cast(ber.Record)['Value']
print f['Value'][1]['Value'][0]
print f['Value'][1]['Value'][0]['Value'][0]
print f['Value'][1]['Value'][0]['Value'][1]
print f['Value'][1]['Value'][1]['Value']

print e['Value'][3]['Value']
g = e['Value'][3]['Value'].cast(ber.Record)

print g['Value'][0]['Value'][0]
print g['Value'][0]['Value'][1]

print g['Value'][0]['Value'][2]['Value'][0]
print g['Value'][0]['Value'][2]['Value'][1]

print g['Value'][0]['Value'][3]['Value'][0]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][3]['Value'][0]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][3]['Value'][1]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][3]['Value'][1]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][3]['Value'][2]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][3]['Value'][2]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][3]['Value'][3]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][3]['Value'][3]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][3]['Value'][4]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][3]['Value'][4]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][4]['Value'][0]
print g['Value'][0]['Value'][4]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][0]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][0]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][1]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][1]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][2]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][2]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][3]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][3]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][4]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][4]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][5]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][5]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][5]['Value'][6]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][5]['Value'][6]['Value'][0]['Value'][1]

print g['Value'][0]['Value'][6]['Value'][0]['Value'][0]
print g['Value'][0]['Value'][6]['Value'][0]['Value'][1]
print g['Value'][0]['Value'][6]['Value'][1]['Value'].cast(ber.Record)['Value'].cast(ber.Record)

print g['Value'][0]['Value'][7]['Value']

print g['Value'][1]['Value'][0]
print g['Value'][1]['Value'][1]
print g['Value'][2]['Value'].cast(ber.Record)

print e['Value'][4]['Value'][0]['Value'][0]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][0]['Value'][0]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][0]['Value'][0]['Value'][1]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][1]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][2]['Value'][0]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][2]['Value'][0]['Value'][1]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][3]['Value'][0]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][3]['Value'][0]['Value'][1]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][4]['Value'][0]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][1]['Value'][0]['Value'][4]['Value'][0]['Value'][1]

print e['Value'][4]['Value'][0]['Value'][1]['Value'][1]
print e['Value'][4]['Value'][0]['Value'][2]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][2]['Value'][1]
print e['Value'][4]['Value'][0]['Value'][3]['Value'].cast(ber.Record)['Value'][0]
print e['Value'][4]['Value'][0]['Value'][3]['Value'].cast(ber.Record)['Value'][1]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][4]['Value'][0]
print e['Value'][4]['Value'][0]['Value'][4]['Value'][1]
print e['Value'][4]['Value'][0]['Value'][5]

print e['Value'][4]['Value'][0]['Value'][6]['Value']
h = e['Value'][4]['Value'][0]['Value'][6]['Value'].cast(ber.Record)
print h['Value'][0]
print h['Value'][1]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][0]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][0]['Value'][0]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][2]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][2]['Value'][0]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][3]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][3]['Value'][0]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][4]['Value'][0]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][1]['Value'][0]['Value'][4]['Value'][0]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][1]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][2]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][2]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][3]['Value'].cast(ber.Record)['Value'][0]
print h['Value'][1]['Value'][0]['Value'][3]['Value'].cast(ber.Record)['Value'][1]['Value'][0]

print h['Value'][1]['Value'][0]['Value'][4]['Value'][0]
print h['Value'][1]['Value'][0]['Value'][4]['Value'][1]

print h['Value'][1]['Value'][0]['Value'][5]
