<stack>
{ 
    for $entry in doc('x86reference.xml')/x86reference/(one-byte | two-byte)/pri_opcd/entry[not(@attr)]
    where ($entry/grp1 = "stack" or $entry/grp2 = "stack") and
          $entry[not(descendant::proc_end) and not(descendant::proc_start)]
    return 
        for $x in $entry
        return
            <opcode value="{$x/../@value}" repr="{$x/syntax/mnem}" ext="{$x/opcd_ext/text()}" />
}
</stack>
