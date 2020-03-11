'''
This module provides facility to hook different parts of a target program given only
an instance of a memorymanager.

This module is also pretty stupid and shouldn't really be used without the python stub.
'''

import struct,ia32
class instruction(object):
    """
    This is only for hooking 32-bit x86. oh and it's not threadsafe...not
    like it matters tho..
    """

    def __setitem__(self, key, value):
        self.loaded[key] = value
    def __getitem__(self, key):
        return self.loaded[key]

    def __init__(self, memorymanager):

        self.loaded = {}        # XXX: i don't know why i can only think of using this terminology for this...
        self.committed = {}     # (originalbytes, [addresses])

        self.__arena = None     # the addresses all of the hooks are located at
        self.memorymanager = memorymanager

    def commit(self):
        # allocate memory
        total_hooks = self.__calculatehooklength()
        total_lifted = self.__calculateliftedlength()
        total_glue = self.__calculategluelength()

        hooks = total_hooks + total_glue
        lifted = total_lifted + total_glue

        self.__codearena = self.memorymanager.load( hooks + lifted )

        # start populating memory
        a = self.__buildlifted(self.__codearena)
        b = self.__buildstub(self.__codearena + lifted)

        # yes, i'm still doing this stupidly
        assert a == lifted, 'calculated lifted code size is different than expected: %d != %d'% (a,lifted)
        assert b == hooks, 'calculated hook code size is different than expected: %d != %d'% (b,hooks)

        # commit before we actually patch the hooks in
        res =  self.memorymanager.commit( self.__codearena )

        self.__writehooks()
        return res

    def unload(self):
        mm = self.memorymanager

        # restore the hooks
        for address,(original,lifted,stub) in self.committed.items():
            mm.write(address, original)

        # free our memory
        mm.unload( self.__codearena )
        self.committed = {}
        self.__codearena = None

    def __repr__(self):
       return '%s (loaded=%x,committed=%x)'% (self.__class__, len(self.loaded.keys()), len(self.committed.keys()))

### calculating sizes
    def __calculateliftedlength(self):
        '''Total the bytes required in order to lift each block of assembly'''
        br = self.__createbranch(0, '\xe9', 0)
        size = len(''.join(br))

        loaded = self.loaded
        result = 0
        for address in loaded:
            originalcode = self.lift(address, size)
            relocatedsize = self.__calculateblocksize(originalcode)    # promote branches
            result += relocatedsize
        return result

    def __calculatehooklength(self):
        '''
        Total the number of bytes in order to allocate all the user-supplied
        code
        '''
        loaded = self.loaded
        return reduce(lambda x,y: len(y)+x, loaded.values(), 0)

    def __calculategluelength(self):
        '''
        Total the number of bytes required for all the glue instructions
        that are used for branching back
        '''
        br = self.__createbranch(0, '\xe9', 0)
        size = len(''.join(br))
        return size * len(self.loaded.keys())

    def __calculateblocksize(self, block):
        '''return the maximum size required for a block'''
        result = 0
        for n in ia32.disassemble(block):
            if ia32.isRelativeBranch(n) or ia32.isRelativeCall(n):
                n = ia32.promoteBranch(n, 4)
            instructionlength = len(''.join(n))
            result += instructionlength
        return result

### writing to address space
    def __buildlifted(self, baseaddress):
        """
        Reads lifted code, relocates it, tacks on a branch to return to original code, and then writes
        it to baseaddress. updates self.committed
        """
        loaded = self.loaded
        mm = self.memorymanager

        result = 0
        for address in loaded:
            originalcode = self.lift(address, 5)
            relocatedcode = self.__relocateblock(originalcode, address, baseaddress)
            finalbranch = ''.join(self.__createbranch(baseaddress+len(relocatedcode), '\xe9', address + len(originalcode)))

            mm.write(baseaddress, relocatedcode+finalbranch)

            self.committed[address] = [originalcode, baseaddress]
            sz = len(relocatedcode)+len(finalbranch)
            baseaddress += sz
            result += sz
        return result

    def __buildstub(self, baseaddress):
        """
        Fetches hook-code, tacks on a branch to the lifted code, writes it to baseaddress. also updates
        self.committed
        """
        loaded = self.loaded
        mm = self.memorymanager

        result = 0
        for address in loaded:
            lastaddress = self.committed[address][-1]
            hookcode = loaded[address]
            finalbranch = ''.join(self.__createbranch(baseaddress+len(hookcode), '\xe9', lastaddress))

            mm.write(baseaddress, hookcode+finalbranch)

            self.committed[address].append(baseaddress)
            sz = len(hookcode) + len(finalbranch)
            baseaddress += sz
            result += sz
        return result

    def __writehooks(self):
        '''Write hooks into address space'''
        loaded = self.loaded
        for address in loaded:
            self.__patch(address, self.committed[address][2])
        return

### tools for lifting
    def lift(self, address, length):
        '''return the bytes required in order to lift to code at /address/ along a valid instruction boundary'''
        def producer(address, mm):
            while True:
                yield mm.read(address, 1)
                address += 1
            raise NotImplementedError("WTF")

        consumeable = producer(address, self.memorymanager)
        lifted = ""
        while length > 0:
            instruction = ''.join(ia32.consume(consumeable))
            lifted += instruction
            length -= len(instruction)
        return lifted

    def __relocateblock(self, block, sourceaddress, destinationaddress):
        '''
        Will relocate all the instructions in a block. Will promote branch
        instructions that target an address outside the block
        '''
        result = []
        sourceoffset,destoffset = 0,0
        for n in ia32.disassemble(block):
            instructionlength = len(''.join(n))

            if ia32.isRelativeBranch(n) or ia32.isRelativeCall(n):
                currentaddress = destinationaddress + len(''.join(result))
                branchoffset = ia32.getRelativeAddress(currentaddress, n) - currentaddress

                o = sourceoffset + instructionlength + branchoffset
                if (o<0) or (o>=len(block)):
                    operand = sourceaddress + o
                    n = self.__updatebranch(currentaddress, n, operand)
                pass

            n = ''.join(n)
            result.append(n)
            sourceoffset += instructionlength
            destoffset += len(n)
        return ''.join(result)

    def __relocateblock(self, block, sourceaddress, destinationaddress):
        blocklength = len(block)
        result = []
        sourceoffset = destoffset = 0
        currentaddress = destinationaddress
        for sourceinstruction in ia32.disassemble(block):
            sourcelength = len(''.join(sourceinstruction))
            destinstruction = sourceinstruction

            if ia32.isRelativeBranch(sourceinstruction) or ia32.isRelativeCall(sourceinstruction):
                branchoffset = ia32.getRelativeAddress(currentaddress, sourceinstruction) - currentaddress
                targetoffset = sourceoffset + branchoffset
                if (targetoffset < 0) or (targetoffset >= blocklength):
                    operand = sourceaddress + targetoffset
                    destinstruction = ia32.setRelativeAddress(currentaddress, sourceinstruction, operand)
                    destinstruction = ia32.promoteBranch(destinstruction,4)
                pass

            destinstruction = ''.join(destinstruction)
            result.append(destinstruction)
            destoffset += len(destinstruction)

        return ''.join(result)

#### utility
    def __createbranch(self, address, opcode, target):
        res = ia32.setOpcode( ia32.new(), opcode )
        res = ia32.setRelativeAddress(address, res, target)
        res = ia32.promoteBranch(res, 4)
        return res

    def __updatebranch(self, address, instruction, target):
        newinstruction = ia32.promoteBranch(instruction, 4)
        return ia32.promoteBranch(ia32.setRelativeAddress(address, newinstruction, target), 4)

    def __patch(self, sourceaddress, destinationaddress):
        instruction = ''.join( self.__createbranch(sourceaddress, '\xe9', destinationaddress) )

        mm = self.memorymanager
        mm.allocator.setMemoryPermission(sourceaddress, 1, int('110', 2))
        count = mm.write(sourceaddress, instruction)
        mm.allocator.setMemoryPermission(sourceaddress, 1, int('101', 2))

if __name__ == '__main__':
    import sys,memorymanager,instrument

    if False:
        mm = memorymanager.new(pid=int(sys.argv[1],16))

        self = instrument.instruction(mm)

        #address = 0x00402f64
        #address = 0x00401f0d
        address = int(sys.argv[2],16)
        self[address] = '\xcc\xcc\xcc\xcc\xcc'
        self.commit()

        print(self)
        print(self.loaded)
        print(self.committed)

    if False:
        import ia32,struct
        instruction = ia32.setOpcode(ia32.setImmediate(ia32.new(), '\x00\x00\x00\x00'), '\xe9')
        sourceaddress,targetaddress = 0x7c36364f,0x261000d
        sourceaddress = 0x1000
        targetaddress = 0x0000

        x = setBranch(sourceaddress, instruction, targetaddress)
        print(repr(x))

    #.text:7C36364F 8B C3                                                        mov     eax, ebx        ; hook point 1

    ### things needed for rewrite. why doesn't this shit work for all cases (???)

    ## stuff to add to the ia32 module
    # a generic way for promoting a branch from 16-bit to 32-bit
    # a generic way for creating a type of branch

    ## relocating a block of assembly ->
    #   promote any branches from 16-to-32 whom jump outside the boundaries of the requested block

    ## relocation
    # ensure that all appended branches resolve correctly and aren't touched at all by any other code

    if True:
        import ctypes
        def openprocess (pid):
            k32 = ctypes.WinDLL('kernel32.dll')
            res = k32.OpenProcess(0x30 | 0x0400, False, pid)
            return res

        def getcurrentprocess ():
            k32 = ctypes.WinDLL('kernel32.dll')
            return k32.GetCurrentProcess()

        def getPBIObj (handle):
            nt = ctypes.WinDLL('ntdll.dll')
            class ProcessBasicInformation(ctypes.Structure):
                _fields_ = [('Reserved1', ctypes.c_uint32),
                            ('PebBaseAddress', ctypes.c_uint32),
                            ('Reserved2', ctypes.c_uint32 * 2),
                            ('UniqueProcessId', ctypes.c_uint32),
                            ('Reserved3', ctypes.c_uint32)]

            pbi = ProcessBasicInformation()
            res = nt.NtQueryInformationProcess(handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
            return pbi

        handle = getcurrentprocess()
        pebaddress = getPBIObj(handle).PebBaseAddress

    if True:
        """
        .text:7C90E48A 0A C0                                   or      al, al          ; hooking here
        .text:7C90E48C 74 0C                                   jz      short loc_7C90E49A ;
        .text:7C90E48C                                                                 ;
        .text:7C90E48E 5B                                      pop     ebx
        .text:7C90E48F 59                                      pop     ecx
        .text:7C90E490 6A 00                                   push    0
        .text:7C90E492 51                                      push    ecx
        .text:7C90E493 E8 C6 EB FF FF                          call    _ZwContinue@8   ; ZwContinue(x,x)
        """
        import ptypes,ndk
        peb = ndk.PEB(offset=pebaddress)
        peb=peb.l

        mm = memorymanager.new()
        data = '\x0a\xc0\x74\x0c\x5b\x59\x6a\x00\x51\xe8\xc6\xeb\xff\xff'
        print(repr(data))

        hook = instrument.instruction(mm)

        baseaddress = int( peb.getmodulebyname('ntdll.dll')['DllBase'] )
        offset = 0x1010f
        hook[baseaddress+offset] = '\x90'

#        print(hex(baseaddress))

        hook.commit()

        """
        original

        ntdll!KiUserExceptionDispatcher+0xf:
        7735010f 0ac0            or      al,al
        *77350111 740c            je      ntdll!KiUserExceptionDispatcher+0x1f (7735011f)
        77350113 5b              pop     ebx
        77350114 59              pop     ecx
        77350115 6a00            push    0
        77350117 51              push    ecx
        77350118 e873fd0000      call    ntdll!ZwContinue (7735fe90)
        """

        """
        relocated
        ntdll!KiUserExceptionDispatcher+0xf:
        7735010f e9fafe4e89      jmp     0084000e
        77350114 59              pop     ecx
        77350115 6a00            push    0
        77350117 51              push    ecx
        77350118 e873fd0000      call    ntdll!ZwContinue (7735fe90)
        """

        """
        hook
        00840000 0ac0            or      al,al
        *00840002 0f841b01b176    je      ntdll!KiUserExceptionDispatcher+0x23 (77350123)
        00840008 5b              pop     ebx
        00840009 e90601b176      jmp     ntdll!KiUserExceptionDispatcher+0x14 (77350114)
        0084000e 90              nop
        0084000f e9ecffffff      jmp     00840000
    """
    if True:
        currentaddress = 0x840002
        sourceinstruction = ia32.decode('\x74\x0c')
        operand = 0x7735011f
        n = ia32.setRelativeAddress(currentaddress, sourceinstruction, operand)
        promoted = ia32.promoteBranch(n, 4)
