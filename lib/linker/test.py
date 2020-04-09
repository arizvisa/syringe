if False:
    import linker

    a = linker.coff.executable.open('~/../../windows/system32/python26.dll')
    b = linker.coff.executable.open('~/../../windows/system32/kernel32.dll')
    c = linker.coff.executable.open('~/../../windows/system32/user32.dll')
    d = linker.coff.executable.open('~/../../windows/system32/msvcr100.dll')
    print(a)
    u32,wsprintf = list(a.externals)[0]
    print(c[None,wsprintf])

    print(a,b,c,d)

# all of these are static classes
class Scope(object):
    pass

class GlobalScope(Scope): pass
class LocalScope(Scope): pass
class ExternalScope(Scope): pass
class AliasScope(Scope): pass

class customdict(dict):
    def __setitem__(self, key, target):
        raise KeyError, key

    def add(self, pack_modulename, scope):
        (module, name) = pack_modulename
        # dictionary where each entry has an identifier
        pass

class symbols(customdict):
    def add(self, pack_modulename, scope, target):
        (module, name) = pack_modulename
        pass

if __name__ == '__main__':
    a = symbols(None)
