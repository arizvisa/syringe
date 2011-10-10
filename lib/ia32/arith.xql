<stack>
{ 
    for $entry in doc('x86reference.xml')/x86reference/(one-byte | two-byte)/pri_opcd/entry[not(@attr)]
    where (($entry/grp1 = "arith" and $entry/grp2 = "gen") or
          ($entry/grp1 = "gen" and $entry/grp2 = "arith")) and
          $entry[not(descendant::proc_end) and not(descendant::proc_start)]
    return 
        for $x in $entry
        return
            <opcode value="{$x/../@value}" repr="{$x/syntax[1]/mnem}" ext="{$x/opcd_ext/text()}">
                <store>{$x/syntax[1]/dst}</store>
                <load>{$x/syntax[1]/src}</load>
                <flags>
                    <modified>{$x/modif_f/text()}</modified>
                    <defined>{$x/def_f/text()}</defined>
                    <undefined>{$x/undef_f/text()}</undefined>
                </flags>
            </opcode>
}
</stack>
