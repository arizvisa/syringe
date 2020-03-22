import six, logging, time
#logging.root.setLevel(logging.INFO)

import pecoff, ptypes
from ptypes import pstruct, dyn
from pecoff.portable import clr

class CustomField(pstruct.type):
    _fields_ = [
        (clr.ELEMENT_TYPE, 'FieldOrProp'),
        (clr.ELEMENT_TYPE, 'FieldOrPropType'),
        (clr.SerString, 'FieldOrPropName'),
        (lambda s: clr.ElementType.lookup(s['FieldOrPropType'].li.int()), 'Value'),
    ]

class Fields(pstruct.type):
    _fields_ = [
        (clr.CInt, 'Count'),
        (lambda s: dyn.array(CustomField, s['Count'].li.Get()), 'Fields'),
    ]

def log(stdout):
    start = ts = time.time()
    while True:
        message = (yield)
        ts = time.time()
        six.print_("{:.3f} : {:s}".format(ts - start, message), file=stdout)
    return

if __name__ == '__main__':
    import sys, os
    import ptypes, pecoff

    if len(sys.argv) != 2:
        six.print_("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else 'test'), file=sys.stderr)
        sys.exit(1)
    filename = sys.argv[1]
    L = log(sys.stderr); next(L)

    ptypes.setsource(ptypes.prov.file(filename, mode='r'))

    L.send("Loading executable for {:s}".format(os.path.basename(filename)))
    z = pecoff.Executable.File()
    z = z.l
    dd = z['next']['header']['datadirectory'][14]
    if dd['address'].int() == 0:
        L.send("No IMAGE_COR20_HEADER found in executable!".format(os.path.basename(filename)))
        sys.exit(2)

    comdd = dd['address'].d.l
    meta = comdd['MetaData']['Address'].d.l

    strings = meta['StreamHeaders'].Get('#Strings')['Offset'].d
    #userstrings = meta['StreamHeaders'].Get('#US')['Offset'].d
    guids = meta['StreamHeaders'].Get('#GUID')['Offset'].d
    blobs = meta['StreamHeaders'].Get('#Blob')['Offset'].d
    htables = meta['StreamHeaders'].Get('#~')['Offset'].d

    ts = time.time()
    L.send("Loading heap \"{:s}\"".format('#~'))
    htables.l
    L.send("Loading heap \"{:s}\"".format('#Strings'))
    strings.l
    L.send("Loading heap \"{:s}\"".format('#GUID'))
    guids.l
    L.send("Loading heap \"{:s}\"".format('#Blob'))
    blobs.l
    L.send("Finished loading heaps in {:.3f}".format(time.time()-ts))

    tables = htables['tables']

    # output modules
    L.send("Enumerating {:d} modules.".format(len(tables['Module'])))
    modules = []
    for i, m in enumerate(tables['Module']):
        res = strings.field(m['Name'].int())
        if m['Mvid'].int():
            g = guids.Get(m['Mvid'].int())
            modules.append((res.str(), g.str()))
        else:
            modules.append((res.str(), None))

    # collect assemblies
    L.send("Enumerating {:d} assemblies.".format(len(tables['Assembly'])))
    assembly = {}
    for i, a in enumerate(tables['Assembly']):
        res = strings.field(a['Name'].int())
        assembly[i+1] = res.str()

    # for each permission that points to an Assembly
    perms = ((p['Parent'].Index(), p['Action'].str(), p['PermissionSet'].int()) for p in tables['DeclSecurity'] if p['Parent']['Tag'].Get() == 'Assembly')

    L.send("Listing properties from each permission.")
    properties = []
    for mi, ma, bi in perms:
        permset = blobs.field(bi)['data'].cast(clr.PermissionSet)
        attributes = []
        for attr in permset['attributes']:
            props = attr['Properties']['data'].cast(Fields)
            res = {}
            for f in props['Fields']:
                res[ f['FieldOrPropName'].str() ] = f['Value'].get()
            attributes.append(res)

        res = {}
        list(map(res.update, attributes))

        properties.append((assembly[mi], ma, res))
        mn, mid = next((mn, mid) for mn, mid in modules if mn.startswith(assembly[mi]))
        six.print_('{:s}\t{:s}{:s}\t{:s}\t{:s}:{:s}'.format(filename, mn, mid or '', assembly[mi], ma, ','.join('{:s}={:d}'.format(k, v) for k, v in res.viewitems())), file=sys.stdout)

    else:
        if not properties:
            for mn, mid in modules:
                six.print_('{:s}\t{:s}{:s}'.format(filename, mn, mid or ''), file=sys.stdout)
    sys.exit(0)
