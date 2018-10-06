class attributes:
    attributes = None
    def __init__(self, **attrs):
        if self.attributes:
            attrs.update(self.attributes)
        self.attributes = attrs
    def __getattr__(self, name):
        return self.attributes[name]
    def __repr__(self):
        attrs = []
        for k,v in self.attributes.items():
            if type(v) in (int,long):
                result = "%d"% v
            elif type(v) in (str,unicode):
                result = "'%s'"% v
            elif isinstance(v, attributes):
                result = repr(v)
            elif type(v) in (float,):
                result = '%.3f'% v
            elif type(v) == type(attributes):
                result = v.__name__
            else:
                raise TypeError(k,v)
            attrs.append('%s=%s'%(k,result))
        return '%s(%s)'% (self.__class__.__name__, ','.join(attrs))

#############################################################################
class platform:
    """Operating system information"""
    class linux(attributes): pass
    class windows(attributes): pass
    class darwin(attributes): pass
    class distribution(attributes): pass

    @classmethod
    def valid(cls, value):
        return value in (cls.linux,cls.windows)

    class bits:
        class x32: attributes = {'size':4}
        class x64: attributes = {'size':8}
        map = {'32bit':x32,'64bit':x64}

    class format:
        class pe: pass
        class elf: pass
        map = {'WindowsPE':pe,'ELF':elf}

    map = {'Linux':linux,'Windows':windows,'Darwin':darwin}

#############################################################################
class architecture:
    """Information about the architecture"""
    class x86(attributes): attributes={'bits':platform.bits.x32,'order':byteorder.littleendian}
    class x64(attributes): attributes={'bits':platform.bits.x64,'order':byteorder.littleendian}

    @classmethod
    def valid(cls, value):
        return value in (cls.x86,cls.x64)

    map = {
        'i386':x86,'i486':x86,'i586':x86,'i686':x86,
        'amd64':x64,
    }

#############################################################################
class language:
    """Information about the language"""
    class CPython(attributes): pass

    map = {'CPython':CPython}

#############################################################################
def identify_system():
    bits,form = __platform.architecture()
    os,name,ver,minver,machine,proc = __platform.uname()

    plat = platform.map[os]

    # platform
    attrs = {}
    distro = None
    if plat is platform.windows:
        _,major,minor,descr = __platform.win32_ver()
        distro = platform.distribution(name='microsoft',major=major,minor=minor)
    elif plat is platform.linux:
        name,major,minor = __platform.dist()
        distro = platform.distribution(name=name,major=major,minor=minor)
        attrs['libc'] = '-'.join(__platform.libc_ver())

        res = ''
        for _ in ver:
            if _ not in '0123456789.':
                break
            res += _
        ver,place = 0.0,1.0
        for _ in res.replace('.',''):
            ver += float(_)*place
            place /= 10.0

    elif plat is platform.darwin:
        ver,_,machine = __platform.mac_ver()
        distro = platform.distribution(name='darwin', major=ver, minor=ver)

        #uname, ('Darwin', 'haake', '10.8.0', 'Darwin Kernel Version 10.8.0: Tue Jun  7 16:33:36 PDT 2011; root:xnu-1504.15.3~1/RELEASE_I386', 'i386', 'i386')
        #architecture, ('64bit', '')
        #dist, ('', '', '')
        #mac_ver, ('10.6.8', ('', '', ''), 'i386')
        #processor, 'i386'
        #libc_ver, ('', '')
        #java_ver, ('', '', ('', '', ''), ('', '', ''))

        #uname, ('Darwin', 'abduls-MacBook-Pro.local', '12.4.0', 'Darwin Kernel Version 12.4.0: Wed May  1 17:57:12 PDT 2013; root:xnu-2050.24.15~1/RELEASE_X86_64', 'x86_64', 'i386')
        #architecture, ('64bit', '')
        #dist, ('', '', '')
        #mac_ver, ('10.8.4', ('', '', ''), 'x86_64')
        #processor, 'i386'
        #libc_ver, ('', '')
        #java_ver, ('', '', ('', '', ''), ('', '', ''))
        # $ sw_vers
        # ProductName: Mac OS X
        # ProductVersion: 10.8.4
        # BuildVersion: 12E55

        # $ uname -a
        # Darwin abduls-MacBook-Pro.local 12.4.0 Darwin Kernel Version 12.4.0: Wed May  1 17:57:12 PDT 2013; root:xnu-2050.24.15~1/RELEASE_X86_64 x86_64


    PLATFORM = plat(bits=platform.bits.map[bits], format=platform.format.map[form], version=float(ver), dist=distro, **attrs)   # XXX

    # architecture
    mach = machine.lower()
    arch = architecture.map[mach]
    order = arch.attributes['order']
    ARCHITECTURE = arch(order=order,machine=mach,processor=proc)    # XXX

    # language
    lang = language.map[__platform.python_implementation()]
    size = long(math.log((sys.maxsize+1)*2,2)/8)
    order = byteorder.littleendian if sys.byteorder == 'little' else byteorder.bigendian if sys.byteorder == 'big' else None

    ver = sys.version_info[0] + (sys.version_info[1]/10.0) + (sys.version_info[2]/100.0)
    comp = __platform.python_compiler()
    LANGUAGE = lang(version=ver,byteorder=order,size=size,compiler=comp,platform=PLATFORM,architecture=ARCHITECTURE)
    return LANGUAGE
