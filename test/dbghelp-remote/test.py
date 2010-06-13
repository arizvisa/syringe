if False:
    import sys
    sys.path.append('f:/work/syringe.git/lib')

import ctypes,pydbgeng

## types
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_byte*8)
    ]
    def set(self, string):
        # extract guid
        if string[0] != "{" and string[-1] != "}":
            raise ValueError
        string = string[1:-1]
        
        # collect elements
        elements = string.split("-")
        if len(elements) != 5:
            raise ValueError((elements, 5))

        # check and fetch each element length
        data = []
        for n,length in zip(elements, [8,4,4,4,12]):
            if len(n) != length:
                raise ValueError((n,length))
            res = int(n,16)
            data.append(res)

        # convert last 2 fields into a string
        result = []
        value = data[4]
        for x in range(6):
            result.append( value & 0xff )
            value /= 0x100
        assert value == 0, value
        data4 =  [(data[3]&0xff00)/0x100,data[3]&0xff]
        data4 += list(reversed(result))

        # create a ctypes buffer
        Data4 = (c_byte*8)(*data4)

        # assign them
        self.Data1 = data[0]
        self.Data2 = data[1]
        self.Data3 = data[2]
        self.Data4 = Data4
        return data

REFIID = POINTER(IID)
HRESULT = c_uint32
PCSTR = c_char_p

## prototypes
#DebugConnectPrototype = ctypes.WINFUNCTYPE(HRESULT, PCSTR, REFIID, c_void_p)

## utilities
#def map_prototype(function, result, args):
#    function.argtypes = [ x for x in args ]
#    function.restype = result
#    return function

### type checking is good
#map_prototype(dbgeng.DebugConnect, HRESULT, [PCSTR,REFIID,c_void_p])

if __name__ == '__main__':
    creator = pydbgeng.IDebugClientCreator()
    IDebugClient = creator.create_idebug_client(dbgeng)
    server = ctypes.c_uint64()
    dc = IDebugClient.QueryInterface(interface=pydbgeng.DbgEng.IDebugClient)
    print dc
    s = 'tcp:port=57005,server=172.22.22.107'
    
    print dc.ConnectProcessServer
    print dc.ConnectProcessServer.restype
    print dc.ConnectProcessServer.argtypes
