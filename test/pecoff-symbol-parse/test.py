if __name__ == '__main__':
    import ptypes,pecoff
    from ptypes import *
    ptypes.setsource(ptypes.file('./chewbacca.exe.infected'))
    a = pecoff.Executable.File()
    a=a.l
    b = a['next']['header']
    #print b['header']
    c = b['FileHeader']['pointertosymboltable'].d
    c = c.l
    print c['Symbols'][1]
    print c['Symbols'][1].details()
    print c['Symbols']

    print c.names()
    print c.walk().next()

    print c.getSymbol('_main')
    print c.getAuxiliary('_main')
    print c.fetch('_main')
