import os,sys
sys.path.append('./lib')

import ia32

import peepeelite
PE = peepeelite.PE
def findFile(name, paths=["."]):
    # I am Yor, the hunter from the future
    for path in paths + os.environ['PATH'].split( os.pathsep ):
        
        try:
            path += os.sep + name
            x = file(path, 'r')
            x.close()

            return path

        except IOError:
            pass

    raise ValueError('unable to find %s!'% name)

def getAllSections(pe):
    return [(sect['PointerToRawData'], sect['SizeOfRawData']) for sect in pe['section']]

def getAllImports(pe):
    res = {}
    for k in pe['imports'].keys():
        path = findFile(k)
        x = PE()
        x.open(path)
        x.read()
        if path in res:
            continue
        res[path] = ( x, getAllSections(pe) )

    return res

match = [
    {'opcode':'\x8b'},
    {'opcode':'\xc3'}
]

match = [
    {'opcode':'\xe9'},
    {'opcode':'\x05'}
]

def matchDictionary(minor, major):
    for k in minor.keys():
        if minor[k] == major[k]:
            return True
    return False

s = '\x8b\xff\xc3'
s = '\xe9'*30

print matchDictionary( match[0], ia32.decode(s) )
#print matchDictionary( match[0], ia32.decode('\x8c\xff') )

def matchInstructions(s, matches):
    ''' returns a list of instructionsl. will raise ValueError if no match was made '''

    res = []
    for m in matches:
        if not s:
            raise ValueError
        instruction = ia32.decode(s)
        if not matchDictionary(m, instruction):
            raise ValueError

        res.append(instruction)

        s = s[ instruction['size']:]
    return res

#print matchInstructions(s, match)
#print matchInstructions('\x8c\xff\xc6', match)

def searchInstructions(s, matches):
    ''' returns [(offset_in_string, instruction), ...] '''
    offset = 0
    res = []
    for m in matches:
        s = s[offset:]
        if not s:
            break

        try:
            insns = matchInstructions(s,matches)
            res.append( (offset, insns) )
            #size = reduce( lambda x,y: x+y, [ insn['size'] for insn in insns ] )
            #offset += size
            offset += 1
            continue

        except ValueError:
            pass

        offset += 1

    return res

#print '\n'.join([ repr(x) for x in searchInstructions(s, match) ])
#print '\n'.join([ repr(x) for x in searchInstructions('\x8b\xff\xc2', match) ])
#print '\n'.join([ repr(x) for x in searchInstructions('\x8c\xff\xc2', match) ])

def readSection(input, section):
    offset,width = section
    input.file.seek(offset)
    return input.file.read(width)

def getVAs(input, sectiontable, match):
    res = []
    for section in sectiontable:
        baseoffset,width = section
        s = readSection(input, section)
        v = [blah for blah in searchInstructions(s, match) if blah]
        if not v:
            continue
            
        v = [(input.getVAByOffset(baseoffset+ofs),insns) for ofs,insns in v]
        res.append(v)
    return res
        
if __name__ == '__main__':
    x = PE()
    x.open('/Program Files/IDM Computer Solutions/UltraEdit-32/uedit32.exe')
    x.open('/Windows/notepad.exe')
    x.read()
    pe = x

#    positions = [v['PointerToRawData'], v['SizeOfRawData']) for v in x['section']]
#    searchThroughForInstructions(positions)
#
#    for x in x['imports'].keys()
#        res = findFile(x)
#        PE.parse(res)
        
#    need some infinite loop instructions
#    need some instructions for writing to an address we can control and a return

    res = getAllImports(pe)
    for k in res:
        input, sections = res[k]
        print getVAs(input, sections, match)
    
