import struct
def producer(address, mm):
    while True:
        yield mm.read(address, 1)
        address += 1
    raise NotImplementedError("WTF")

import ia32
class instruction(object):
    """
    This is only for hooking 32-bit x86. oh and it's not threadsafe...not
    like it matters tho
    """

    def __setitem__(self, key, value):
        self.loaded[key] = value
    def __getitem__(self, key):
        return self.loaded[key]

    def __init__(self, memorymanager):

        self.loaded = {}        # XXX: i don't know why i can only think of using this terminology for this...
        self.committed = {}     # (originalbytes, [addresses])

        self.__arena = None     # the address all of the hooks are located at
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
        self.__buildlifted(self.__codearena)
        self.__buildstub(self.__codearena + lifted)

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

### totals
    def __calculateliftedlength(self):
        '''Total the bytes required in order to lift each block of assembly'''
        br = self.__createfarbranch(0, '\xe9', 0)
        size = len(''.join(br))

        loaded = self.loaded
        result = 0
        for address in loaded:
            originalcode = self.__liftaddress(address, size)
            relocatedcode = self.__calculateblocksize(originalcode)    # promote branches
            result += relocatedcode
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
        br = self.__createfarbranch(0, '\xe9', 0)
        size = len(''.join(br))
        return size * len(self.loaded.keys())

    def __calculateblocksize(self, block):
        '''return the maximum size required for a block'''
        result = 0
        for n in ia32.disassemble(block):
            if ia32.isRelativeBranch(n) or ia32.isRelativeCall(n):
                n = self.__promotebranch(n)
            instructionlength = len(''.join(n))
            result += instructionlength
        return result

### writing
    def __buildlifted(self, baseaddress):
        """
        Reads lifted code, relocates it, tacks on a branch to return, and then writes
        it to baseaddress. updates self.committed
        """
        loaded = self.loaded
        mm = self.memorymanager

        for address in loaded:

            originalcode = self.__liftaddress(address, 5)
            relocatedcode = self.__relocateblock(originalcode, address, baseaddress)
            finalbranch = ''.join(self.__createfarbranch(baseaddress+len(relocatedcode), '\xe9', address + len(originalcode)))

            mm.write(baseaddress, relocatedcode+finalbranch)

            self.committed[address] = [originalcode, baseaddress]
            baseaddress += len(relocatedcode) + len(finalbranch)
        return

    def __buildstub(self, baseaddress):
        """
        Fetches hook-code, tacks on a branch, writes it to baseaddress. also updates
        self.committed
        """
        loaded = self.loaded
        mm = self.memorymanager

        for address in loaded:
            lastaddress = self.committed[address][-1]

            hookcode = loaded[address]
            finalbranch = ''.join(self.__createfarbranch(baseaddress+len(hookcode), '\xe9', lastaddress))

            mm.write(baseaddress, hookcode+finalbranch)

            self.committed[address].append(baseaddress)
            baseaddress += len(hookcode) + len(finalbranch)
        return

    def __writehooks(self):
        '''Write hooks into address space'''
        loaded = self.loaded
        for address in loaded:
            self.__patch(address, self.committed[address][2])
        return

### tools for lifting
    def __liftaddress(self, address, length):
        '''return the instructions required in order to lift to code at /address/'''
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
        offset = 0
        for n in ia32.disassemble(block):
            instructionlength = len(''.join(n))
            if ia32.isRelativeBranch(n) or ia32.isRelativeCall(n):
                currentaddress = destinationaddress + len(''.join(result))
                branchoffset = ia32.getBranchOffset(n)

                o = offset + instructionlength + branchoffset
                if (o<0) or (o>=len(block)):
                    operand = sourceaddress + o
    #                print hex(o), offset, repr(n), hex(operand)
                    n = self.__updatebranch(currentaddress, n, operand)
                
                pass

            result.append(''.join(n))
            offset += instructionlength
        return ''.join(result)

    def __promotebranch(self, instruction):
        '''will promote a banch to it's non-short equivalent'''
        n = instruction
        if ia32.isConditionalBranch8(n):
            column = ord(ia32.getOpcode(n)) & 0xf
            return ia32.setOpcode(n, '\x0f'+chr(column | 0x80))
        if ia32.isUnconditionalBranch8(n):
            prefix = [x for x in ia32.getPrefix(n) if x != '\x66']
            n = ia32.setPrefix(n, ''.join(prefix))
            return ia32.setOpcode(n, '\xe9')
        if ia32.isRelativeCall(n):
            prefix = [x for x in ia32.getPrefix(n) if x != '\x66']
            return ia32.setPrefix(n, ''.join(prefix))
        if ia32.isUnconditionalBranch(n) or ia32.isConditionalBranch(n):
            return n
        raise NotImplementedError(repr(n))
        return instruction

    def __updatebranch(self, sourceaddress, instruction, operand):
        '''Will promote a branch, and then update it's operand to point to the correct dest'''
        newinstruction = self.__promotebranch(instruction)
        newinstruction = ia32.setImmediate(newinstruction, '\x00\x00\x00\x00')
        res = operand - (sourceaddress+len(''.join(newinstruction)))
        res &= 0xffffffff
        return ia32.setImmediate(newinstruction, struct.pack('L', res))

### utility
    def __createfarbranch(self, address, opcode, target):
        '''Will create a branch with the specified opcode'''
        newinstruction = ia32.setOpcode( ia32.new(), opcode )
        newinstruction = ia32.setImmediate(newinstruction, '\x00\x00\x00\x00')
        res = target - (address+len(''.join(newinstruction)))
        res &= 0xffffffff
        return ia32.setImmediate(newinstruction, struct.pack('L', res))

    def __patch(self, sourceaddress, destinationaddress):
        instruction = ''.join( self.__createfarbranch(sourceaddress, '\xe9', destinationaddress) )

        mm = self.memorymanager
        mm.allocator.setMemoryPermission(sourceaddress, 1, int('110', 2))
        count = mm.write(sourceaddress, instruction)
        mm.allocator.setMemoryPermission(sourceaddress, 1, int('101', 2))

if __name__ == '__main__':
    import memorymanager
    mm = memorymanager.new(pid=1348)

    import instrument; reload(instrument)
    self = instrument.instruction(mm)

    address = 0x402f64
    self[address] = '\xcc\xcc\xcc\xcc\xcc'
    self.commit()

    print self
    print self.loaded
    print self.committed
