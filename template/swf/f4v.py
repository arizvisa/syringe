from primitives import *
from ptypes import *

### generic types
class Language(pbinary.struct):
    class code(pbinary.array): _object_ = 5
    _fields_ = [
        (1, 'Pad'),
        (code, 'Language'),
    ]

class SAMPLEFLAGS(pbinary.struct):
    _fields_ = [
        (6, 'Reserved'),
        (2, 'SampleDependsOn'),
        (2, 'SampleIsDependedOn'),
        (2, 'SampleHasRedundancy'),
        (3, 'SamplePaddingValue'),
        (1, 'SampleIsDifferenceSample'),
        (16, 'SampleDegradationPriority'),
    ]

## root types
class BOXHEADER(pstruct.type):
    def __ExtendedSize(self):
        return UI64 if s['TotalSize'].li.int() == 1 else pint.uint_t

    _fields_ = [
        (UI32, 'TotalSize'),
        (UI32, 'BoxType'),
        (__ExtendedSize, 'ExtendedSize'),
    ]

    def BoxSize(self):
        return s['ExtendedSize'].li.int() if s['TotalSize'].li.int() == 1 else s['TotalSize'].li.int()

class BOX(pstruct.type):
    def __Payload(self):
        bh = self['Header'].li
        if bh['TotalSize'].int() == 0:
            return BOXLIST

        t, sz = bh['BoxType'].li.serialize(), bh.BoxSize()
        result = Boxes.withdefault(t, __name__=t, length=sz)
        return dyn.clone(result, blocksize=lambda s: sz)

    _fields_ = [
        (BOXHEADER, 'Header'),
        (__Payload, 'Payload'),
    ]

class BOXLIST(parray.infinite):
    _object_ = BOX

class Boxes(ptype.definition):
    attribute,cache = '__name__',{}

## tag types
@Boxes.define
class ftyp(pstruct.type):
    _fields_ = [
        (UI32, 'MajorBrand'),
        (UI32, 'MinorVersion'),
        (dyn.clone(parray.infinite, _object_=UI32), 'CompatibleBrands'),
    ]

@Boxes.define
class pdin(pstruct.type):
    class RATEDELAY(pstruct.type):
        _fields_ = [(UI32, 'Rate'), (UI32, 'InitialDelay')]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (dyn.clone(parray.infinite, _object_=RATEDELAY), 'RateDelay'),
    ]

@Boxes.define
class afra(pstruct.type):
    class GlobalAfraEntryFlags(pbinary.struct):
        _fields_ = [(1,'LongIDs'),(1,'LongOffsets'),(1,'GlobalEntries'),(5,'Reserved')]
    class AFRAENTRY(pstruct.type):
        _fields_ = [(UI64, 'Time'),(lambda s: UI32 if s.getparent(afra)['GlobalAfraEntryFlags'].li['LongOffsets'] == 0 else UI64, 'Offset')]
    class GLOBALAFRAENTRY(pstruct.type):
        _fields_ = [
            (UI64, 'Time'),
            (lambda s: UI16 if s.getparent(afra)['GlobalAfraEntryFlags'].li['LongIDs'] == 0 else UI32, 'Segment'),
            (lambda s: UI16 if s.getparent(afra)['GlobalAfraEntryFlags'].li['LongIDs'] == 0 else UI32, 'Fragment'),
            (lambda s: UI32 if s.getparent(afra)['GlobalAfraEntryFlags'].li['LongOffsets'] == 0 else UI64, 'AfraOffset'),
            (lambda s: UI32 if s.getparent(afra)['GlobalAfraEntryFlags'].li['LongOffsets'] == 0 else UI64, 'OffsetFromAfra'),
        ]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (GlobalAfraEntryFlags, 'GlobalAfraEntryFlags'),
        (UI32, 'TimeScale'),
        (UI32, 'EntryCount'),
        (lambda s: dyn.array(AFRAENTRY, s['EntryCount'].li.int()), 'LocalAccessEntries'),
        (lambda s: UI32 if s['GlobalAfraEntrySize'].li['GlobalEntries'] == 1 else pint.uint_t, 'GlobalEntryCount'),
        (lambda s: dyn.array(GLOBALAFRAENTRY,s['GlobalEntryCount'].li.int()), 'GlobalAccessEntries'),
    ]

@Boxes.define
class abst(pstruct.type):
    class BootstrapType(pbinary.struct):
        _fields_ = [
            (2, 'Profile'),
            (1, 'Live'),
            (1, 'Update'),
            (4, 'Reserved'),
        ]
    class SERVERENTRY(STRING): pass
    class QUALITYENTRY(STRING): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'BootstrapinfoVersion'),
        (BootstrapType, 'BootstrapinfoType'),
        (UI32, 'TimeScale'),
        (UI64, 'CurrentMediaTime'),
        (UI64, 'SmpteTimeCodeOffset'),
        (STRING, 'MovieIdentifier'),
        (UI8, 'ServerEntryCount'),
        (lambda s: dyn.array(SERVERENTRY,s['ServerEntryCount'].li.int()), 'ServerEntryTable'),
        (UI8, 'QualityEntryCount'),
        (lambda s: dyn.array(QUALITYENTRY,s['QualityEntryCount'].li.int()), 'QualityEntryTable'),
        (STRING, 'DrmData'),
        (STRING, 'MetaData'),
        (UI8, 'SegmentRunTableCount'),
        (lambda s: dyn.array(SegmentRunTable,s['SegmentRunTableCount'].li.int()), 'SegmentRunTableEntries'),
        (UI8, 'FragmentRunTableCount'),
        (lambda s: dyn.array(FragmentRunTable,s['FragmentRunTableCount'].li.int()), 'FragmentRunTableEntries'),
    ]

@Boxes.define
class asrt(pstruct.type):
    class SEGMENTRUNENTRY(pstruct.type):
        _fields_ = [(UI32,'FirstSegment'),(UI32,'FragmentsPerSegment')]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI8, 'QualityEntryCount'),
        (lambda s: dyn.array(STRING, s['QualityEntryCount'].li.int()), 'QualitySegmentUrlModifiers'),
        (UI32, 'SegmentRunEntryCount'),
        (lambda s: dyn.array(SEGMENTRUNENTRY, s['SegmentRunEntryCount'].li.int()), 'SegmentRunEntryTable'),
    ]

@Boxes.define
class afrt(pstruct.type):
    class FRAGMENTRUNENTRY(pstruct.type):
        _fields_ = [
            (UI32, 'FirstEntry'),
            (UI64, 'FirstFragmentTimestamp'),
            (UI32, 'FragmentDuration'),
            (lambda s: UI8 if s['FragmentDuration'].li.int() == 0 else pint.uint_t, 'DiscontinuityIndicator'),
        ]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'TimeScale'),
        (UI8, 'QualityEntryCount'),
        (lambda s: dyn.array(STRING, s['QualityEntryCount'].li.int()), 'QualitySegmentUrlModifiers'),
        (UI32, 'FragmentRunEntryCount'),
        (lambda s: dyn.array(FRAGMENTRUNENTRY, s['FragmentRunEntryCount'].li.int()), 'FragmentRunEntryTable'),
    ]

@Boxes.define
class moov(BOXLIST): pass

@Boxes.define
class mvhd(pstruct.type):
    __versioned = lambda s: UI32 if s['Version'].li.int() == 0 else UI64
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (__versioned, 'CreationTime'),
        (__versioned, 'ModificationTime'),
        (UI32, 'TimeScale'),
        (__versioned, 'Duration'),
        (SI16_16, 'Rate'),
        (SI8_8, 'Volume'),
        (UI16, 'Reserved(0)'),
        (dyn.array(UI32,2), 'Reserved(1)'),
        (dyn.array(SI32,9), 'Matrix'),
        (dyn.array(UI32,6), 'Reserved(2)'),
        (UI32, 'NextTrackID'),
    ]

@Boxes.define
class trak(BOXLIST): pass

@Boxes.define
class tkhd(pstruct.type):
    __versioned = lambda s: UI32 if s['Version'].li.int() == 0 else UI64
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (__versioned, 'CreationTime'),
        (__versioned, 'ModificationTime'),
        (UI32, 'TrackID'),
        (UI32, 'Reserved(0)'),
        (__versioned, 'Duration'),
        (dyn.array(UI32,2), 'Reserved(1)'),
        (SI16, 'Layer'),
        (SI16, 'AlternateGroup'),
        (SI8_8, 'Volume'),
        (UI16, 'Reserved(2)'),
        (dyn.array(SI32,9), 'TransformMatrix'),
        (UI16_16, 'Width'),
        (UI16_16, 'Height'),
    ]

@Boxes.define
class edts(BOX): pass

@Boxes.define
class elst(pstruct.type):
    class ELSTRECORD(pstruct.type):
        __versioned = lambda s: UI32 if s.getparent(elst)['Version'].li.int() == 0 else UI64
        __sversioned = lambda s: SI32 if s.getparent(elst)['Version'].li.int() == 0 else SI64
        _fields_ = [
            (__versioned, 'SegmentDuration'),
            (__sversioned, 'MediaTime'),
            (SI16, 'MediaRateInteger'),
            (SI16, 'MediaRateFraction'),
        ]

    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'EntryCount'),
        (lambda s: dyn.array(ELSTRECORD, s['EntryCount'].li.int()), 'EditListEntryTable'),
    ]

@Boxes.define
class mdia(BOXLIST): pass

@Boxes.define
class mdhd(pstruct.type):
    __versioned = lambda s: UI32 if s.getparent(elst)['Version'].li.int() == 0 else UI64
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (__versioned, 'CreationTime'),
        (__versioned, 'ModificationTime'),
        (UI32, 'TimeScale'),
        (__versioned, 'Duration'),
        (Language, 'Language'),
        (UI16, 'Reserved'),
    ]

@Boxes.define
class hdlr(pstruct.type):
    class HandlerType(pint.enum, UI32):
        _ = [('vide','Video Track'),('soun','Sound Track'),('data','Data Track'),('hint','Hint Track')]
        _values_ = [(reduce(lambda t,c: t*256|ord(c), t, 0),n) for t,n in _]

    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Predefined'),
        (UI32, 'HandlerType'),
        (dyn.array(UI32,3), 'Reserved'),
        (STRING, 'Name'),
    ]

@Boxes.define
class minf(BOXLIST): pass

@Boxes.define
class vmhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI16, 'GraphicsMode'),
        (dyn.array(UI16,3), 'OpColor'),
    ]

@Boxes.define
class smhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (SI8_8, 'Balance'),
        (UI16, 'Reserved'),
    ]

@Boxes.define
class hmhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI16, 'MaXPDUSize'),
        (UI16, 'AvgPDUSize'),
        (UI32, 'MaxBitRate'),
        (UI32, 'AvgBitRate'),
        (UI32, 'Reserved'),
    ]

@Boxes.define
class nmhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
    ]

@Boxes.define
class dinf(BOXLIST): pass

@Boxes.define
class dref(pstruct.type):
    class DataEntryBox(BOX): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'EntryCount'),
        (lambda s: dyn.array(s.DataEntryBox, s['EntryCount'].li.int()), 'DataEntry'),
    ]

@Boxes.define
class url(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
    ]

@Boxes.define
class stbl(BOXLIST): pass

@Boxes.define
class stsd(pstruct.type):
    class DESCRIPTIONRECORD(BOX): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Count'),
        (lambda s: dyn.array(DESCRIPTIONRECORD, s['Count'].li.int()), 'Descriptions'),
    ]

@Boxes.define
class stts(pstruct.type):
    class STTSRECORD(pstruct.type):
        _fields_ = [(UI32,'SampleCount'),(UI32,'SampleDelta')]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Count'),
        (lambda s: dyn.array(STTSRECORD, s['Count'].li.int()), 'Entries'),
    ]

@Boxes.define
class ctts(pstruct.type):
    class CTTSRECORD(pstruct.type):
        _fields_ = [(UI32,'SampleCount'),(UI32,'SampleOffset')]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Count'),
        (lambda s: dyn.array(CTTSRECORD, s['Count'].li.int()), 'Entries'),
    ]

@Boxes.define
class stsc(pstruct.type):
    class STSCRECORD(pstruct.type):
        _fields_ = [(UI32,'FirstChunk'),(UI32,'SamplesPerChunk'),(UI32,'SampleDescIndex'),]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Count'),
        (lambda s: dyn.array(STSCRECORD, s['Count'].li.int()), 'Entries'),
    ]

@Boxes.define
class stsz(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'ConstantSize'),
        (UI32, 'SizeCount'),
        (lambda s: dyn.array(UI32, s['SizeCount'].li.int()) if s['ConstantSize'].li.int() == 0 else dyn.array(UI32,0), 'SizeTable'),
    ]

@Boxes.define
class stco(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'OffsetCount'),
        (lambda s: dyn.array(UI32, s['OffsetCount'].li.int()), 'Offsets'),
    ]

@Boxes.define
class co64(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'OffsetCount'),
        (lambda s: dyn.array(UI64, s['OffsetCount'].li.int()), 'Offsets'),
    ]

@Boxes.define
class ctco(pstruct.type):
    _fields_ = []

@Boxes.define
class stss(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'SyncCount'),
        (lambda s: dyn.array(UI32, s['SyncCount'].li.int()), 'SyncTable'),
    ]

@Boxes.define
class sdtp(pstruct.type):
    class SAMPLEDEPENDENCY(pbinary.struct):
        _fields_ = [(2,name) for name in ('Reserved','SampleDependsOn','SampleIsDependedOn','SampleHasRedundancy')]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (dyn.clone(parray.infinite, _object_=SAMPLEDEPENDENCY), 'SampleDependency'),
    ]

@Boxes.define
class mvex(BOXLIST): pass

@Boxes.define
class mehd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (lambda s: UI32 if s['Version'] == 0 else UI64, 'FragmentDuration'),
    ]

@Boxes.define
class trex(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'TrackID'),
        (UI32, 'DefaultSampleDescriptionIndex'),
        (UI32, 'DefaultSampleDuration'),
        (UI32, 'DefaultSampleSize'),
        (SAMPLEFLAGS, 'DefaultSampleFlags'),
    ]

@Boxes.define
class udta(BOXLIST): pass

@Boxes.define
class moof(BOXLIST): pass

@Boxes.define
class mfhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'SequenceNumber'),
    ]

@Boxes.define
class traf(BOXLIST): pass

@Boxes.define
class tfhd(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'TrackID'),
        (lambda s: UI64 if s['Flags'].li.int() & 0x01 else pint.uint_t, 'BaseDataOffset'),
        (lambda s: UI32 if s['Flags'].li.int() & 0x02 else pint.uint_t, 'SampleDescriptionIndex'),
        (lambda s: UI32 if s['Flags'].li.int() & 0x08 else pint.uint_t, 'DefaultSampleDuration'),
        (lambda s: UI32 if s['Flags'].li.int() & 0x10 else pint.uint_t, 'DefaultSampleSize'),
        (lambda s: SAMPLEFLAGS if s['Flags'].li.int() & 0x20 else pint.uint_t, 'DefaultSampleFlags'),
    ]

@Boxes.define
class trun(pstruct.type):
    class SampleInformationStructure(pstruct.type):
        _fields_ = [
            (lambda s: UI32 if s.getparent(trun)['Flags'].li.int() & 0x100 else pint.uint_t, 'SampleDuration'),
            (lambda s: UI32 if s.getparent(trun)['Flags'].li.int() & 0x200 else pint.uint_t, 'SampleSize'),
            (lambda s: SAMPLEFLAGS if s.getparent(trun)['Flags'].li.int() & 0x400 else pint.uint_t, 'SampleFlags'),
            (lambda s: UI32 if s.getparent(trun)['Flags'].li.int() & 0x800 else pint.uint_t, 'SampleCompositionTimeOffset'),
        ]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'SampleCount'),
        (lambda s: SI32 if s['Flags'].li.int() & 0x01 else pint.uint_t, 'DataOffset'),
        (lambda s: SAMPLEFLAGS if s['Flags'].li.int() & 0x04 else pint.uint_t, 'FirstSampleFlags'),
        (lambda s: dyn.array(SampleInformationStructure,s['SampleCount'].li.int()), 'SampleInformation'),
    ]

#@Boxes.define
#class mdat(ptype.block): pass

@Boxes.define
class meta(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (BOXLIST, 'Boxes'),
    ]

@Boxes.define
class free(ptype.block): pass

@Boxes.define
class skip(ptype.block): pass

@Boxes.define
class mfra(BOXLIST): pass

@Boxes.define
class tfra(pstruct.type):
    class LengthSize(pbinary.struct):
        _fields_ = [(26,'Reserved'),(2,'TrafNumMinus1'),(2,'TrunNumMinus1'),(2,'SampleNumMinus1')]
    class RandomAccessStructure(pstruct.type):
        _fields_ = [
            (lambda s: UI64 if s.getparent(tfra)['Version'].li.int() == 1 else UI32, 'Time'),
            (lambda s: UI64 if s.getparent(tfra)['Version'].li.int() == 1 else UI32, 'MoofOffset'),
            (lambda s: (UI8,UI16,UI24,UI32)[s.getparent(tfra)['LengthSize'].li['TrafNumMinus1']], 'TrafNumber'),
            (lambda s: (UI8,UI16,UI24,UI32)[s.getparent(tfra)['LengthSize'].li['TrunNumMinus1']], 'TrunNumber'),
            (lambda s: (UI8,UI16,UI24,UI32)[s.getparent(tfra)['LengthSize'].li['SampleNumMinus1']], 'SampleNumber'),
        ]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'TrackID'),
        (LengthSize, 'LengthSize'),
        (UI32, 'NumberEntry'),
        (lambda s: dyn.array(RandomAccessStructure,s['NumberEntry'].li.int()), 'RandomAccessSample'),
    ]

@Boxes.define
class mfro(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'Size'),
    ]

@Boxes.define
class sinf(pstruct.type):
    class OriginalFormatBox(BOX): pass
    class SchemeTypeBox(BOX): pass
    class SchemeInformationBox(BOX): pass
    _fields_ = [
        (OriginalFormatBox, 'OriginalFormatBox'),
        (SchemeTypeBox, 'SchemeTypeBox'),
        (SchemeInformationBox, 'SchemeInformationBox'),
    ]

@Boxes.define
class frma(pstruct.type):
    _fields_ = [(UI32,'UnencryptedDataFormat')]

@Boxes.define
class schm(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (UI32, 'SchemeType'),
        (UI32, 'SchemeVersion'),
        (lambda s: STRING if s['Flags'] == 1 else ptype.undefined, 'SchemeUri'),
    ]

@Boxes.define
class schi(BOXLIST): pass

@Boxes.define
class adkm(pstruct.type):
    class AdobeDRMHeaderBox(BOX): pass
    class AdobeDRMAUFormatBox(BOX): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (AdobeDRMHeaderBox, 'Header'),
        (AdobeDRMAUFormatBox, 'AUFormat'),
    ]

@Boxes.define
class ahdr(pstruct.type):
    class StandardEncryptionParamsBox(BOX): pass
    class AdobeSignatureBox(BOX): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (StandardEncryptionParamsBox, 'StdEncryptionBox'),
        (lambda s: AdobeSignatureBox if s['Version'].li.int() == 1 else ptype.undefined, 'Signature'),
    ]

@Boxes.define
class aprm(pstruct.type):
    class EncryptionInfoBox(BOX): pass
    class KeyInfoBox(BOX): pass
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (EncryptionInfoBox, 'EncInfoBox'),
        (KeyInfoBox, 'KeyInfoBox'),
    ]

@Boxes.define
class aeib(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (STRING, 'EncryptionAlgorithm'),
        (UI8, 'KeyLength'),
    ]

@Boxes.define
class akey(pstruct.type):
    class APSParamsBox(BOX): pass
    class FMRMSv2ParamsBox(BOX): pass

    def __Params(self):
        res = self.getparent(aprm)
        return APSParamsBox if res['Version'].li.int() == 1 else FMRMSv2PAramsBox

    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (__Params, 'Params'),
    ]

@Boxes.define
class flxs(pstruct.type):
    _fields_ = [
        (STRING, 'FmrmsV2Metadata'),
    ]

@Boxes.define
class adaf(pstruct.type):
    class KeyInfo(pbinary.struct):
        _fields_ = [
            (1, 'SelectiveEncryption'),
            (7, 'Reserved(0)'),
            (8, 'Reserved(1)'),
            (8, 'IVLength'),
        ]
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (KeyInfo, 'KeyInfo'),
    ]

### Sample entries
@Boxes.define
class vide(pstruct.type):
    # VisualSampleEntry
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (UI16, 'Predefined(0)'),
        (UI16, 'Reserved(1)'),
        (dyn.array(UI32,3), 'Predefined(1)'),
        (UI16, 'Width'),
        (UI16, 'Height'),
        (UI16_16, 'HorizResolution'),
        (UI16_16, 'VertResolution'),
        (UI32, 'Reserved(2)'),
        (UI16, 'FrameCount'),
        (dyn.array(UI8,32), 'CompressorName'),
        (UI16, 'Depth'),
        (SI16, 'Predefined(2)'),
        (BOXLIST, 'Boxes'),
    ]

@Boxes.define
class soun(pstruct.type):
    # AudioSampleEntry
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (dyn.array(UI32,2), 'Reserved(1)'),
        (UI16, 'ChannelCount'),
        (UI16, 'Predefined'),
        (UI16, 'Reserved(2)'),
        (UI16_16, 'SampleRate'),
        (BOXLIST, 'Boxes'),
    ]

@Boxes.define
class meta(pstruct.type):
    # MetaDataSampleEntry
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (dyn.clone(parray.infinite, _object_=UI8), 'Data'),
    ]

@Boxes.define
class data(pstruct.type):
    # SampleEntry
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (BOXLIST, 'Boxes'),
    ]

@Boxes.define
class hint(pstruct.type):
    # HintSampleEntry
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (dyn.clone(parray.infinite, _object_=UI8), 'Data'),
    ]

### Sample descriptions
@Boxes.define
class rtmp(pstruct.type):
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (UI16, 'HintTrackVersion'),
        (UI16, 'HighestCompatibleVersion'),
        (UI16, 'MaxPacketSize'),
        (dyn.clone(parray.infinite, _object_=BOX), 'AdditionalData'),
    ]

@Boxes.define
class amhp(pstruct.type):
    class MuxHintProcessEntry(pbinary.struct):
        _fields_ = [
            (8,'HintTrackMode'),
            (1,'TrailerLengthField'),
            (1,'LengthField'),
            (1,'ModeField'),
            (1,'ConstructorCountField'),
            (1,'PacketCountField'),
            (3,'Reserved'),
            (8,'TrailerDefaultSize'),
        ]
    _fields_ = [
        (dyn.array(UI8,6), 'Reserved(0)'),
        (UI16, 'DataReferenceIndex'),
        (UI8, 'ModeCount'),
        (lambda s: dyn.clone(pbinary.array, _object_=MuxHintProcessEntry, length=s['ModeCount'].li.int()), 'ENTRIES'),
    ]

@Boxes.define
class amto(pstruct.type):
    _fields_ = [(UI32, 'TimeOffset'),]

### F4V Metadata
class TagBox(pstruct.type):
    _fields_ = [
        (UI8, 'Version'),
        (UI24, 'Flags'),
        (Language, 'Language'),
        (dyn.clone(parray.infinite, _object_=UI8), 'TagString'),
    ]
@Boxes.define
class auth(TagBox): pass

@Boxes.define
class titl(TagBox): pass

@Boxes.define
class dscp(TagBox): pass

@Boxes.define
class cprt(TagBox): pass

@Boxes.define
class uuid(pstruct.type):
    _fields_ = [
        (dyn.array(UI8,16), 'UUID'),
        (dyn.clone(parray.infinite,_object_=UI8), 'XMPMetadata'),
    ]

@Boxes.define
class ilst(pstruct.type):
    class TAGRECORD(pstruct.type):
        _fields_ = [
            (UI32, 'TagLength'),
            (dyn.array(UI8,4), 'TagName'),
            (UI32, 'DataLength'),
            (dyn.array(UI8,4), 'DataTag'),
            (UI32, 'DataType'),
            (UI32, 'Reserved'),
            (lambda s: dyn.array(UI8,s['DataLength'].li.int()), 'Payload'),
        ]
    _fields_ = [
        (UI32, 'TagCount'),
        (lambda s: dyn.array(TAGRECORD,s['TagCount'].li.int()), 'Tags'),
    ]

@Boxes.define
class styl(pstruct.type):
    class STYLERECORD(pstruct.type):
        _fields_ = [
            (UI16, 'StartChar'),
            (UI16, 'EndChar'),
            (UI16, 'FontID'),
            (UI8, 'FaceStyleFlags'),
            (UI8, 'FontSize'),
            (UI32, 'TextColor'),
        ]
    _fields_ = [
        (UI16, 'Count'),
        (lambda s: dyn.array(STYLERECORD,s['Count'].li.int()), 'Styles'),
    ]

@Boxes.define
class hlit(pstruct.type):
    _fields_ = [
        (UI16, 'StartChar'),
        (UI16, 'EndChar'),
    ]

@Boxes.define
class hclr(pstruct.type):
    _fields_ = [
        (dyn.array(UI16,3), 'HighlightColor'),
    ]

@Boxes.define
class krok(pstruct.type):
    class KARAOKEREC(pstruct.type):
        _fields_ = [(UI32,'EndTime'),(UI16,'StartChar'),(UI16,'EndChar')]
    _fields_ = [
        (UI32, 'StartTime'),
        (UI16, 'Count'),
        (lambda s: dyn.array(KARAOKEREC, s['Count'].li.int()), 'KaraokeRecords'),
    ]

@Boxes.define
class dlay(pstruct.type):
    _fields_ = [
        (UI32, 'ScrollDelay'),
    ]

@Boxes.define
class drpo(pstruct.type):
    _fields_ = [
        (UI16, 'DropShadowOffsetX'),
        (UI16, 'DropShadowOffsetY'),
    ]

@Boxes.define
class drpt(pstruct.type):
    _fields_ = [
        (UI16, 'DropShadowAlpha'),
    ]

@Boxes.define
class href(pstruct.type):
    _fields_ = [
        (UI16, 'StartChar'),
        (UI16, 'EndChar'),
        (UI8, 'URLSize'),
        (lambda s: dyn.clone(STRING,length=s['URLSize'].li.int()), 'URL'),
        (UI8, 'ALTSize'),
        (lambda s: dyn.clone(STRING,length=s['ALTSize'].li.int()), 'ALT'),
    ]

@Boxes.define
class tbox(pstruct.type):
    _fields_ = [
        (UI16, 'Top'),
        (UI16, 'Left'),
        (UI16, 'Bottom'),
        (UI16, 'Right'),
    ]

@Boxes.define
class blnk(pstruct.type):
    _fields_ = [
        (UI16, 'StartChar'),
        (UI16, 'EndChar'),
    ]

@Boxes.define
class twrp(pstruct.type):
    _fields_ = [
        (UI8, 'WrapFlag'),
    ]

### file types
class File(BOX): pass

if __name__ == '__main__':
    import ptypes,swf.f4v as f4v
    ptypes.setsource('c:/users/user/Documents/blah.flv',mode='rb')
