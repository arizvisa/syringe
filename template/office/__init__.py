from ptypes import *
class RecordUnknown(dyn.block(0)):
    def __repr__(self):
        if self.initialized:
            return self.name()
        return super(RecordUnknown, self).__repr__()

    def shortname(self):
        s = super(RecordUnknown, self).shortname()
        names = s.split('.')
        names[-1] = '%s<%x>[size:%d]'%(names[-1], self.type, self.blocksize())
        return '.'.join(names)

class RecordHeader(pstruct.type):
    class __verinstance(pbinary.struct):
        _fields_=[(4,'ver'),(12,'instance')]

    _fields_ = [
        (__verinstance, 'ver/instance'),
        (pint.uint16_t, 'type'),
        (pint.uint32_t, 'length')
    ]

    def __repr__(self):
        if self.initialized:
            v = self['ver/instance'].getinteger()
            t = int(self['type'])
            l = int(self['length'])
            return '%s ver=%04x type=0x%04x length=0x%08x'% (self.name(), v,t,l)
        return super(RecordHeader, self).__repr__()

class Record(object):
    cache = {}
    @classmethod
    def Add(cls, object):
        t = object.type
        cls.cache[t] = object

    @classmethod
    def Lookup(cls, type):
        return cls.cache[type]

    @classmethod
    def Define(cls, pt):
        cls.Add(pt)
        return pt

class RecordGeneral(pstruct.type):
    def __data(self):
        t = int(self['header'].l['type'])
        l = int(self['header']['length'])
        try:
            cls = self.Record.Lookup(t)
            if len(self.backtrace()) > 20:
                raise KeyError
        except KeyError:
            return dyn.clone(RecordUnknown, type=t, length=l)
        return dyn.clone(cls, blocksize=lambda s:l)
        
    def __extra(self):
        t = int(self['header'].l['type'])
        name = '[%s]'% ','.join(self.backtrace()[1:])


        total = int(self['header']['length'])
        used = self['data'].size()

        if total >= used:
            l = total-used
#            print "record at %x (type %x) %s has %x bytes unused"% (self.getoffset(), t, name, l)
            return dyn.block(l)
        print "record at %x (type %x) %s's contents are larger than expected (%x>%x)"% (self.getoffset(), t, name, used, total)
        return dyn.block(0)

    _fields_ = [
        (RecordHeader, 'header'),
        (__data, 'data'),
        (__extra, 'extra'),
    ]

    def blocksize(self):
        return self['header'].size() + int(self['header']['length'])

class RecordContainer(parray.block):
    _object_ = None

    def __repr__(self):
        if self.initialized:
            records = []
            for v in self.walk():
                n = '%s[%x]'%(v.__class__.__name__,v.type)
                records.append(n)
            return '[%x] %s records=%d [%s]'%(self.getoffset(),self.name(), len(self), ','.join(records))
        return super(RecordContainer, self).__repr__()

    def search(self, type, recurse=False):
        '''Search through a list of records for a particular type'''
        if not recurse:
            for x in self:
                if int(x['header']['recType']) == type:
                    yield x
                continue
            return

        # ourselves first
        for d in self.search(type, False):
            yield d

        # now our chidren
        for x in self:
            try:
                x['data'].search
            except AttributeError:
                continue

            for d in x['data'].search(type, True):
                yield d
            continue
        return

    def lookup(self, type):
        '''Return the first instance of specified record type'''
        res = [x for x in self if int(x['header']['recType']) == type]
        if not res:
            raise KeyError(type)
        assert len(res) == 1, repr(res)
        return res[0]

    def walk(self):
        for x in self:
            yield x['data']
        return

# yea, a file really is usually just a gigantic list of records...
class File(RecordContainer):
    _object_ = None

    def isTerminator(self, value):
        return False

    def __repr__(self):
        if self.initialized:
            records = []
            for v in self.walk():
                n = '%s[%x]'%(v.__class__.__name__,v.type)
                records.append(n)
            return '%s records=%d [%s]'%(self.name(), len(self), ','.join(records))
        return super(File, self).__repr__()

if __name__ == '__main__':
    from ptypes import *

#    @Record.Define
    class r(pstruct.type):
        type = 0
        _fields_ = [
            (pint.uint32_t, 'a')
        ]

    s = '\x00\x00\x00\x00\x0c\x00\x00\x00' + 'A'*30
    z = RecordGeneral()
    z.source = provider.string(s)
    print z.l
