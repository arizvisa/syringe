from __future__ import print_function
import logging, time
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
        print("{:.3f} : {:s}".format(ts - start, message), file=stdout)
    return

def strify(value):
    if isinstance(value, ptypes.integer_types):
        return "{:d}".format(value)
    elif isinstance(value, ptypes.string_types):
        return "{:s}".format(value)
    return "{!r}".format(value)

if __name__ == '__main__':
    import sys, os
    import ptypes, pecoff

    if len(sys.argv) != 2:
        print("Usage: {:s} file".format(sys.argv[0] if len(sys.argv) else 'test'), file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]
    L = log(sys.stderr); next(L)

    if not os.path.exists(filename):
        raise OSError("The specified file ({:s}) does not exist.".format(filename))

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
        res = strings.at(strings.getoffset() + m['Name'].int(), recurse=False)
        if m['Mvid'].int():
            g = guids.Get(m['Mvid'].int())
            print('{:s} {:s}'.format(res.str(), g.str()), file=sys.stdout)
            modules.append((res.str(), g))
        else:
            print('{:s}'.format(res.str()), file=sys.stdout)

    # collect assemblies
    L.send("Enumerating {:d} assemblies.".format(len(tables['Assembly'])))
    assembly = {}
    for i, a in enumerate(tables['Assembly']):
        res = strings.at(strings.getoffset() + a['Name'].int(), recurse=False)
        assembly[i+1] = res.str()

    # for each permission that points to an Assembly
    perms = ((p['Parent'].Index(), p['Action'].str(), p['PermissionSet'].int()) for p in tables['DeclSecurity'] if p['Parent']['Tag'].Get() == 'Assembly')

    L.send("Listing properties from each permission.")
    for mi, ma, bi in perms:
        permset = blobs.at(blobs.getoffset() + bi, recurse=False)['data'].cast(clr.PermissionSet)
        attributes = []
        for attr in permset['attributes']:
            props = attr['Properties']['data'].cast(Fields)
            res = {}
            for f in props['Fields']:
                res[ f['FieldOrPropName'].str() ] = f['Value'].get()
            attributes.append(res)
        res = {}
        map(res.update, attributes)
        print('\t{:s} : {:s} : {:s}'.format(assembly[mi], ma, ', '.join('{:s}={:s}'.format(k, strify(v)) for k, v in res.items())), file=sys.stdout)
