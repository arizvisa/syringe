<stack>
{ 
    for $entry in doc('x86reference.xml')/x86reference/(one-byte | two-byte)/pri_opcd/entry[not(@attr)]
    where $entry/grp1 = "datamov" or $entry/grp2 = "datamov" and 
          $entry[not(descendant::proc_end) and not(descendant::proc_start)] and
          $entry/grp1 != "x87fpu" and $entry/grp2 != "x87fpu"
    return 
        for $x in $entry
        return
            <opcode value="{$x/../@value}" repr="{$x/syntax[1]/mnem}" ext="{$x/opcd_ext/text()}">
                <store>{$x/syntax[1]/dst}</store>
                <load>{$x/syntax[1]/src}</load>
            </opcode>
}
</stack>
