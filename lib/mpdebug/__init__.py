import dbgeng,logging
logging.root=logging.RootLogger(logging.INFO)

if __name__ == '__main__':
    import dbgeng,match

    if False:
        a = dbgeng.local()
        args = "~/python26/python.exe", ['python.exe','test.py']
        b = a.create(*args)
        b.subscribe('LoadModule', lambda *args,**kwds: (b.event.userignore, b.event.userbreak)[ args[4] == match.regex('.*kernel32.*') ])
        b.wait()
        c = b[ b.keys()[0] ]

        modulename = [k for k in b.module.keys() if k == match.regex('.*kernel32.dll')][0]
        module = b.module[modulename]
        exports = module['Pe']['DataDirectory'][0].get().l

        o = exports.search( match.regex('getcurrentprocessid') )
        address = module.getoffset() + o

        def flair(brk, task):
            print 'brokedown at breakpoint %d'% brk.id
            print brk
            print task
            return b.event.userbreak

        c.manager.add(flair, dbgeng.breakpoint.execute, address)
        a.wait()

    if False:
        remote = 'tcp:port=57005,server=172.22.22.134'
        z = dbgeng.remoteserver(remote)
        print z.list()
        for x in z.enum():
            print x
#        b = a.create(r'C:\Program Files\QuickTime\QuickTimePlayer.exe')

    if False:
        b = z.create('notepad.exe')

    if False:
        remote = 'tcp:port=57005,server=127.0.0.1'
        z = dbgeng.connect(remote)

        print z.list()
        b = z.create("calc.exe")

        t = b.task[3300]
        print help(t)
        help(t.manager)

