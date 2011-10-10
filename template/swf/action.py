from primitives import *
from ptypes import *

class Action(object):
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

    @classmethod
    def Update(cls, record):
        a = set(cls.cache.keys())
        b = set(record.cache.keys())
        if a.intersection(b):
            logging.warning('%s : Unable to import module %s due to multiple definitions of the sam erecord')
            return False

        # merge record caches into a single one
        cls.cache.update(record.cache)
        record.cache = cls.cache
        return True

    class Command(pstruct.type): _fields_ = []

    class Unknown(Command):
        _fields_=[]
        def __repr__(self):
            if self.initialized:
                return self.name()
            return super(Unknown, self).__repr__()

        def shortname(self):
            s = super(Unknown, self).shortname()
            names = s.split('.')
            names[-1] = '%s<%x>[size:0x%x]'%(names[-1], self.type, self.blocksize())
            return '.'.join(names)

class ACTIONRECORDHEADER(pstruct.type):
    _fields_ = [
        (UI8, 'ActionCode'),
        (lambda s: (Zero, UI16)[s['ActionCode'].l.int() >= 0x80], 'Length'),
    ]

class ACTIONRECORD(pstruct.type):
    def __record(self):
        code = self['header'].l['ActionCode'].int()
        try:
            res = Action.Lookup(code)
        except KeyError:
            res = dyn.clone(Action.Unknown, type=code)
        return dyn.clone(res, blocksize=lambda s:s.parent['header']['Length'].int())

    _fields_ = [
        (ACTIONRECORDHEADER, 'header'),
        (__record, 'record'),
    ]

@Action.Define
class ActionEnd(Action.Command):
    type=0
    _fields_ = []

@Action.Define
class ActionGotoFrame(Action.Command):
    type=0x81
    _fields_ = [(UI16,'Frame')]

@Action.Define
class ActionGetURL(Action.Command):
    type=0x83
    _fields_ = [(STRING,'UrlString'),(STRING,'TargetString')]

@Action.Define
class ActionNextFrame(Action.Command):
    type=0x04
    _fields_ = [(STRING,'UrlString'),(STRING,'TargetString')]

@Action.Define
class ActionConstantPool(Action.Command):
    type=0x88
    _fields_ = [(UI16, 'Count'), (lambda s: dyn.array(STRING, s['Count'].l.int()), 'ConstantPool')]

@Action.Define
class ActionPush(Action.Command):
    type=0x96
    def __Value(self):
        n = self['Type'].l.int()
        lookup = {
            0:STRING, 1:FLOAT, 4:UI8, 5:UI8, 6:DOUBLE, 7:UI32, 8:UI8, 9:UI16
        }
        return lookup[n]

    _fields_ = [(UI8, 'Type'),(__Value, 'Value')]

@Action.Define
class ActionStoreRegister(Action.Command):
    type=0x87
    _fields_ = [(UI8, 'RegisterNumber')]

@Action.Define
class ActionPop(Action.Command):
    type=0x17

@Action.Define
class ActionGetVariable(Action.Command):
    type=0x1c

@Action.Define
class ActionToggleQuality(Action.Command):
    type=0x08

@Action.Define
class ActionNot(Action.Command):
    type=0x12

@Action.Define
class ActionIf(Action.Command):
    type=0x9d
    _fields_ = [(SI16, 'BranchOffset')]

@Action.Define
class ActionDefineFunction2(pstruct.type):
    type=0x8e

    # FIXME: I don't know how wrong this is...

    class __Flag(pbinary.struct):
        _fields_=[
            (1,'PreloadParent'),
            (1,'PreloadRoot'),
            (1,'SuppressSuper'),
            (1,'PreloadSuper'),
            (1,'SuppressArguments'),
            (1,'PreloadArguments'),
            (1,'SuppressThis'),
            (1,'PreloadThis'),
            (7,'Reserved'),
            (1,'PreloadGlobal'),
        ]

    class REGISTERPARAM(pstruct.type):
        _fields_ = [(UI8,'Register'),(STRING,'ParamName')]

    _fields_ = [
        (STRING, 'FunctionName'),
        (UI16, 'NumParams'),
        (UI8, 'RegisterCount'),
        (__Flag, 'Flag'),
        (lambda s: dyn.array(s.REGISTERPARAM, s['NumParams'].l.int()), 'Parameters'),
        (UI16, 'codeSize'),
#        (lambda s: dyn.block(s['codeSize'].l.int()), 'code'),   # FIXME
    ]
    
###
class Array(parray.terminated):
    _object_ = ACTIONRECORD
    def isTerminator(self, value):
        return value['header']['ActionCode'].l.int() == 0

