instancemethod = type(Exception.__str__)
function = type(lambda:False)
code = type(eval('lambda:False').func_code)

## representing certain types
def fn_repr(fn):
    assert isinstance(fn, type(fn_repr))
    attributes = [ x for x in dir(fn) if x.startswith('func_') ]
    res = dict([(k, getattr(fn, k)) for k in attributes])
    return '\n'.join(["%s: %s"%( k, repr(v) ) for k,v in res.items()])

def code_repr(obj):
    assert isinstance(obj, type(code_repr.func_code))
    attributes = [ x for x in dir(obj) if x.startswith('co_') ]
    res = dict([(k, getattr(obj, k)) for k in attributes])
    return '\n'.join(["%s: %s"%( k, repr(v) ) for k,v in res.items()])

def code_clone(obj, **kwds):
    '''duplicates a code obj w/ a modified arg'''
    assert isinstance(obj, code)

    #res = 'argcount nlocals stacksize flags codestring constants names varnames
    #res+= 'filename name firstlineno lnotab freevars cellvars'
    #res = res.split(' ')
    #attributes = [ 'co_%s'%x for x in res ]
    attributes = [
        'co_argcount', 'co_nlocals', 'co_stacksize', 'co_flags', 'co_code',
        'co_consts', 'co_names', 'co_varnames', 'co_filename', 'co_name',
        'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
    ]

    res = dict( [(k, getattr(obj,k)) for k in attributes] )
    res.update(kwds)
    args = [ res[k] for k in attributes ]

    return code( *args )

if __name__ == '__main__':
    ## i didn't name this codefu, blame aaron. ;)
    print fn_repr(fn_repr)

    print code_repr(code_repr.func_code)

    print code_repr( code_clone(code_clone.func_code, co_code='hello there, heh.') )
