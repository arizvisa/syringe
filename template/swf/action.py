from primitives import *
from ptypes import *

class action(ptype.definition):
    cache = {}

    class command(pstruct.type):
        _fields_ = []

    class unknown(ptype.block):
        _fields_=[]
        def details(self):
            if self.initialized:
                return self.classname()
            return super(action.unknown, self).details()

        def classname(self):
            s = self.typename()
            names = s.split('.')
            names[-1] = '%s<%x>[size:0x%x]'%(names[-1], self.type, self.blocksize())
            return '.'.join(names)

class ACTIONRECORDHEADER(pstruct.type):
    _fields_ = [
        (UI8, 'ActionCode'),
        (lambda s: (Zero, UI16)[s['ActionCode'].li.int() >= 0x80], 'Length'),
    ]

class ACTIONRECORD(pstruct.type):
    def __record(self):
        hdr = self['header'].l
        code = hdr['ActionCode'].int()
        sz = hdr['Length'].int()
        return action.get(code, length=sz)

    _fields_ = [
        (ACTIONRECORDHEADER, 'header'),
        (__record, 'record'),
    ]

@action.define
class ActionEnd(action.command):
    type=0
    _fields_ = []

@action.define
class ActionGotoFrame(action.command):
    type=0x81
    _fields_ = [(UI16,'Frame')]

@action.define
class ActionGetURL(action.command):
    type=0x83
    _fields_ = [(STRING,'UrlString'),(STRING,'TargetString')]

@action.define
class ActionNextFrame(action.command):
    type=0x04
    _fields_ = [(STRING,'UrlString'),(STRING,'TargetString')]

@action.define
class ActionConstantPool(action.command):
    type=0x88
    _fields_ = [(UI16, 'Count'), (lambda s: dyn.array(STRING, s['Count'].li.int()), 'ConstantPool')]

@action.define
class ActionPush(action.command):
    type=0x96
    def __Value(self):
        n = self['Type'].li.int()
        lookup = {
            0:STRING, 1:FLOAT, 4:UI8, 5:UI8, 6:DOUBLE, 7:UI32, 8:UI8, 9:UI16
        }
        return lookup.get(n, ptype.undefined)

    _fields_ = [(UI8, 'Type'),(__Value, 'Value')]

@action.define
class ActionStoreRegister(action.command):
    type=0x87
    _fields_ = [(UI8, 'RegisterNumber')]

@action.define
class ActionPop(action.command):
    type=0x17

@action.define
class ActionGetVariable(action.command):
    type=0x1c

@action.define
class ActionToggleQuality(action.command):
    type=0x08

@action.define
class ActionNot(action.command):
    type=0x12

@action.define
class ActionIf(action.command):
    type=0x9d
    _fields_ = [(SI16, 'BranchOffset')]

@action.define
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
        (lambda s: dyn.array(s.REGISTERPARAM, s['NumParams'].li.int()), 'Parameters'),
        (UI16, 'codeSize'),
#        (lambda s: dyn.block(s['codeSize'].li.int()), 'code'),   # FIXME
    ]

###
class Array(parray.terminated):
    _object_ = ACTIONRECORD
    def isTerminator(self, value):
        return value['header']['ActionCode'].li.int() == 0

