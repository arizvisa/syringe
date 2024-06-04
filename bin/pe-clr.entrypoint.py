from __future__ import print_function
import ptypes, pecoff

if __name__ == '__main__':
    import sys, os.path

    if len(sys.argv) != 2:
        raise ValueError('Please provided the path to the PE file.')

    if not os.path.exists(sys.argv[1]):
        raise OSError("The specified file ({:s}) does not exist.".format(sys.argv[1]))

    ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='r'))
    z=pecoff.Executable.File()
    print('Filename: {:s}\n'.format(z.source.file.name), file=sys.stdout)

    z=z.l
    p = z['next']['header']

    #lc = p['datadirectory']['loadconfig']['address'].d.li
    dn = p['datadirectory']['clr']['address'].d.li
    #dnv = dn['vtablefixups']['address'].d.li
    dnm = dn['metadata']['address'].d.li

    root = dnm['StreamHeaders'].Get('#~')['Offset'].d
    root = root.l
    print('Loading strings...', file=sys.stderr)
    names = dnm['StreamHeaders'].Get('#Strings')['Offset'].d.l
    print('Loading blobs...', file=sys.stderr)
    blobs = dnm['StreamHeaders'].Get('#Blob')['Offset'].d.l

    class pieces(ptypes.pbinary.struct):
        _fields_ = [
            (8, 'table'),
            (24, 'index'),
        ]

    e = dn['EntryPoint'].cast(pieces)
    if e['table'] != pecoff.portable.clr.TMethodDef.type:
        print('No CLR entrypoint found!', file=sys.stderr)
        sys.exit(1)

    emethod = root['Tables'][e['table']][e['index']]
    print('Method:\n{!r}\n'.format(emethod), file=sys.stdout)

    print('MethodDef:', file=sys.stdout)
    res = names.Get(emethod['Name'].int())
    sig = blobs.Get(emethod['Signature'].int()).cast(ptypes.pint.uint32_t)
    print('{:#x} : {:s} : Signature={:#x}\n'.format(dn['EntryPoint'].int(), res.str(), sig.int()), file=sys.stdout)

    sys.exit(0)

    #6 MethodDef
    #24 MethodSemantics
    #25 MethodImpl
    #43 MethodSpec
    #8 Param
    #42 GenericParam
    #44 GenericParamConstraint

    #print(root['tables'][24][0])
    #for msa in root['tables'][24]:
    #    if msa['Method'].int() == 0xda:
    #        print(msa)
    #
    #print(root['tables'][43])
    #print(root['tables'][8][0xde])
    #print(root['tables'][8][0xdf])
    #print(root['tables'][8][0xe0])
    #print(root['tables'][8][0xe1])
