import sys, six
import ptypes,pecoff

ptypes.setsource(ptypes.prov.file(sys.argv[1], mode='r'))
z=pecoff.Executable.File()
six.print_('Filename: {:s}\n'.format(z.source.file.name), file=sys.stdout)

z=z.l
p = z['next']['header']

#lc = p['datadirectory']['loadconfig']['address'].d.li
dn = p['datadirectory']['clr']['address'].d.li
#dnv = dn['vtablefixups']['address'].d.li
dnm = dn['metadata']['address'].d.li

root = dnm['StreamHeaders'].Get('#~')['Offset'].d
root = root.l
six.print_('Loading strings...', file=sys.stderr)
names = dnm['StreamHeaders'].Get('#Strings')['Offset'].d.l
six.print_('Loading blobs...', file=sys.stderr)
blobs = dnm['StreamHeaders'].Get('#Blob')['Offset'].d.l

class pieces(ptypes.pbinary.struct):
    _fields_ = [
        (8, 'table'),
        (24, 'index'),
    ]

e = dn['EntryPoint'].cast(pieces)
if e['table'] != pecoff.portable.clr.TMethodDef.type:
    six.print_('No CLR entrypoint found!', file=sys.stderr)
    sys.exit(1)

emethod = root['Tables'][e['table']][e['index']]
six.print_('Method:\n{!r}\n'.format(emethod), file=sys.stdout)

six.print_('MethodDef:', file=sys.stdout)
res = names.Get(emethod['Name'].int())
sig = blobs.Get(emethod['Signature'].int()).cast(ptypes.pint.uint32_t)
six.print_('{:#x} : {:s} : Signature={:#x}\n'.format(dn['EntryPoint'].int(), res.str(), sig.int()), file=sys.stdout)

sys.exit(0)

#6 MethodDef
#24 MethodSemantics
#25 MethodImpl
#43 MethodSpec
#8 Param
#42 GenericParam
#44 GenericParamConstraint

#six.print_(root['tables'][24][0])
#for msa in root['tables'][24]:
#    if msa['Method'].int() == 0xda:
#        six.print_(msa)
#
#six.print_(root['tables'][43])
#six.print_(root['tables'][8][0xde])
#six.print_(root['tables'][8][0xdf])
#six.print_(root['tables'][8][0xe0])
#six.print_(root['tables'][8][0xe1])
