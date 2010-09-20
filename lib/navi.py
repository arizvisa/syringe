import fu
from inspect import isclass
##################################################
# classes for navigating through types dynamically
class naviter(object):
    '''generic way of navigating through an object's properties if they are iterable'''
    attribute = 'co_consts'
    type = None
    object = None

    def __init__(self, obj, up=None, type=None):
        super(naviter, self).__init__()
        self.object = obj
        self.parent = up
        if type:
            self.type = type

    def __getattr__(self, attrib):
        obj = getattr( self.object, self.attribute )
        return getattr(obj, attrib)

    def __getitem__(self, k):
        obj = getattr( self, k )
        return obj

    def __repr__(self):
        return '%s -> %s'%( super(naviter, self).__repr__(), repr(self.object))

    def up(self):
        return self.parent

    def down(self):
        def ifelse( fn, istrue, isfalse ):
            if fn():
                return istrue
            return isfalse

#        return [ ifelse(lambda: type(dn) == self.type, naviter(dn, up=self, type=self.type), None) for dn in iter(getattr(self.object, self.attribute)) ]
        return [ naviter(dn, up=self, type=self.type) for dn in iter(getattr(self.object, self.attribute)) if type(dn) == self.type ]

########
class navt(naviter):
    '''all types need to be derived from this class in order for navi() to work'''
    def __str__(self):
        return repr(self)

def navi(object):
    '''automatically identifies object used to manipulate type, and provides a naviter interface to it'''
    all = [ x for x in globals().values() if isclass(x) and x != navt and issubclass(x, navt) ]
    for item in all:
        if item.type == type(object):
            return item( object )

    # dynamically create a class for this type
    class _navi(navt):
        type = type(object)
    _navi.__name__ = 'navi__%s'% _navi.type.__name__
    return _navi(object)

### how to represent each attribute by its type
class navcode(navt):
    type = fu.code.getclass()

    ## merged in from aaron's asm.py
    def findByName(navObj, nodeName):
        '''returns a code object, if it finds it'''
        
        ## top level object
        if navObj.object.co_name == "?":
            if navObj.object.co_filename == nodeName:
                return navObj.object
                
        ## found somethin
        elif navObj.object.co_name == nodeName:
            return navObj.object
        
        # get downgraph
        children = navObj.down()
        
        while children:
            child = children.pop()
            
            if child.object.co_name == nodeName:
                return child.object

            children = child.down()

        raise KeyError, '"%s" not found in %s'%( nodeName, repr(navObj) )

function = type(eval("lambda:True"))
class navfunc(navt):
    type = function

instancemethod = type(AssertionError.__str__)
class navinstancemethod(navt):
    type = instancemethod

class navlist(navt):
    type = list

if __name__ == '__main__':

    def dump_navi(nav):
        res = []
        res.append('self: %s'% repr(nav))
        res.append('object: %s'% repr(nav.object))
        res.append('up: %s'% repr(nav.up()))
        res.append('down: %s'% repr(nav.down()))
        print '\n'.join(res)

    ######################################
    # tests for closures and variable scope
    def example1():
        scope_1 = True
        def a():
            print scope_1
            scope_2 = True
        print scope_1
        a()
        return True

    print fu.function.repr(example1)
    cobj = example1.func_code

    ##
    print fu.code.repr(cobj)
    print fu.code.repr(cobj.co_consts[1])

    ##
    nav = navi(cobj)
    dump_navi(nav)
    nav = nav.down()[0]
    dump_navi(nav)

    def example2():
        scope_1 = True
        def a():
            scope_2a = True
            print scope_1

        scope_1 = False
        def b():
            scope_2b = True
            print scope_1

        a()
        b()
        return True

    ##
    print fu.function.repr(example2)
    cobj = example2.func_code

    ##
    print fu.code.repr(cobj)
    print fu.code.repr(cobj.co_consts[1])
    print fu.code.repr(cobj.co_consts[2])

    ##
    nav = navi(cobj)
    dump_navi(nav)
    nav = nav.down()[0]
    dump_navi(nav)
    nav = nav.up()
    nav = nav.down()[1]
    dump_navi(nav)

    def example3():
        scope_1 = True
        def a():
            scope_2 = True
            def aa():
                scope_3= True
            pass
        pass

    ##
    print fu.function.repr(example3)
    cobj = example3.func_code

    ##
    print fu.code.repr(cobj)
    print fu.code.repr(cobj.co_consts[1])
    print fu.code.repr(cobj.co_consts[1].co_consts[1])

    ##
    nav = navi(cobj)
    dump_navi(nav)
    nav = nav.down()[0]
    dump_navi(nav)
    nav = nav.down()[0]
    dump_navi(nav)
