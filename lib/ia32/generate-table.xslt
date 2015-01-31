<?xml version="1.0"?>
<xsl:transform version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:utils="needhex">

    <xsl:template match="text()"></xsl:template>
    <xsl:template mode="syntax" match="text()"></xsl:template>

    <!-- http://www.xsltfunctions.com/xsl/functx_index-of-string.html -->
    <xsl:function name="utils:index-of">
        <xsl:param name="needle" />
        <xsl:param name="haystack" />
        <xsl:value-of select="string-length(substring-before($haystack, $needle))"/>
    </xsl:function>

    <xsl:function name="utils:fromHex">
        <xsl:param name="string" />

        <xsl:variable name="hexdigits" select="'0123456789ABCDEF'" />
        <xsl:variable name="lastcharacter" select="substring($string, string-length($string), 1)" />
        <xsl:variable name="value" select="utils:index-of($lastcharacter, $hexdigits)" />

        <xsl:value-of select="
            if (string-length($string) > 1) then
                $value + utils:fromHex(
                    substring($string, 1, string-length($string)-1)
                ) * 16
            else
               $value 
        " />
    </xsl:function>

    <xsl:function name="utils:toHex">
        <xsl:param name="number" />
        <xsl:variable name="hexdigits" select="'0123456789ABCDEF'" />
        <xsl:value-of select="
            if ($number eq 0) then
                '0'
            else
                concat(
                    if ($number &gt; 16) then
                        utils:toHex($number idiv 16)
                    else
                        '',
                    substring($hexdigits, ($number mod 16) + 1, 1)
                )
        " />
    </xsl:function>

    <xsl:template name="translateTypeString">
        <xsl:param name="string" />
        <xsl:choose>
            <xsl:when test="$string eq 'a'">ops_2opword</xsl:when>
            <xsl:when test="$string eq 'b'">1</xsl:when>
            <xsl:when test="$string eq 'bcd'">4</xsl:when>
            <xsl:when test="$string eq 'bs'">1</xsl:when>
            <xsl:when test="$string eq 'bsq'">1</xsl:when>
            <xsl:when test="$string eq 'bss'">1</xsl:when>
            <xsl:when test="$string eq 'c'">ops_opbyte</xsl:when>
            <xsl:when test="$string eq 'd'">4</xsl:when>
            <xsl:when test="$string eq 'di'">4</xsl:when>
            <xsl:when test="$string eq 'dq'">16</xsl:when>
            <xsl:when test="$string eq 'dqp'">ops_opdword</xsl:when>
            <xsl:when test="$string eq 'dr'">4</xsl:when>
            <xsl:when test="$string eq 'ds'">4</xsl:when>
            <xsl:when test="$string eq 'e'">4</xsl:when>
            <xsl:when test="$string eq 'er'">4</xsl:when>
            <xsl:when test="$string eq 'p'">ops_opfarpointer</xsl:when>
            <xsl:when test="$string eq 'pi'">8</xsl:when>
            <xsl:when test="$string eq 'pd'">4</xsl:when>
            <xsl:when test="$string eq 'ps'">4</xsl:when>
            <xsl:when test="$string eq 'psq'">4</xsl:when>
            <xsl:when test="$string eq 'pt'">ops_opfarpointer</xsl:when>
            <xsl:when test="$string eq 'ptp'">ops_opfarpointer</xsl:when>
            <xsl:when test="$string eq 'q'">8</xsl:when>
            <xsl:when test="$string eq 'qi'">8</xsl:when>
            <xsl:when test="$string eq 'qp'">8</xsl:when>
            <xsl:when test="$string eq 's'">4</xsl:when>
            <xsl:when test="$string eq 'sd'">4</xsl:when>
            <xsl:when test="$string eq 'si'"></xsl:when><!-- unused? -->
            <xsl:when test="$string eq 'sr'">4</xsl:when>
            <xsl:when test="$string eq 'ss'">4</xsl:when>
            <xsl:when test="$string eq 'st'">4</xsl:when>
            <xsl:when test="$string eq 'stx'">4</xsl:when>
            <xsl:when test="$string eq 't'">ops_opfarpointer</xsl:when>
            <xsl:when test="$string eq 'v'">ops_opword</xsl:when>
            <xsl:when test="$string eq 'vds'">ops_opword</xsl:when>
            <xsl:when test="$string eq 'vq'">ops_opqword</xsl:when>
            <xsl:when test="$string eq 'vqp'">ops_opword</xsl:when>
            <xsl:when test="$string eq 'vs'">ops_opword</xsl:when>
            <xsl:when test="$string eq 'w'">2</xsl:when>
            <xsl:when test="$string eq 'wi'">2</xsl:when>
            <xsl:otherwise>0</xsl:otherwise>
            <!--unknown-type><xsl:value-of select="$string" /></unknown-type-->
        </xsl:choose>
    </xsl:template>

    <xsl:template name="translateAddressString">
        <xsl:param name="string" />
        <xsl:choose>
            <xsl:when test="$string eq 'A'">IMM</xsl:when>
            <xsl:when test="$string eq 'BA'"></xsl:when>
            <xsl:when test="$string eq 'BB'"></xsl:when>
            <xsl:when test="$string eq 'C'">MODRM</xsl:when>
            <xsl:when test="$string eq 'D'">MODRM</xsl:when>
            <xsl:when test="$string eq 'E'">MODRM</xsl:when>
            <xsl:when test="$string eq 'ES'">MODRM</xsl:when>
            <xsl:when test="$string eq 'EST'">MODRM</xsl:when>
            <xsl:when test="$string eq 'F'"></xsl:when>
            <xsl:when test="$string eq 'G'">MODRM</xsl:when>
            <xsl:when test="$string eq 'H'">MODRM</xsl:when>
            <xsl:when test="$string eq 'I'">IMM</xsl:when>
            <xsl:when test="$string eq 'J'">IMM</xsl:when>
            <xsl:when test="$string eq 'M'">MODRM</xsl:when>
            <xsl:when test="$string eq 'N'">MODRM</xsl:when>
            <xsl:when test="$string eq 'O'">IMM</xsl:when>
            <xsl:when test="$string eq 'P'">MODRM</xsl:when>
            <xsl:when test="$string eq 'Q'">MODRM</xsl:when>
            <xsl:when test="$string eq 'R'">MODRM</xsl:when>
            <xsl:when test="$string eq 'S'">MODRM</xsl:when>
            <xsl:when test="$string eq 'T'">MODRM</xsl:when>
            <xsl:when test="$string eq 'U'">MODRM</xsl:when>
            <xsl:when test="$string eq 'V'">MODRM</xsl:when>
            <xsl:when test="$string eq 'W'">MODRM</xsl:when>
            <xsl:when test="$string eq 'X'"></xsl:when>
            <xsl:when test="$string eq 'Y'"></xsl:when>
            <xsl:when test="$string eq 'YD'"></xsl:when>
            <xsl:when test="$string eq 'Z'"><!-- spread this across 3 bits of the lower opcode --></xsl:when>
            <xsl:otherwise></xsl:otherwise>
            <!--unknown-address><xsl:value-of select="$string" /></unknown-address-->
        </xsl:choose>
    </xsl:template>

    <xsl:template name="operandtype">
        <xsl:choose>
            <xsl:when test="descendant::a">
                <xsl:call-template name="translateAddressString">
                    <xsl:with-param name="string" select="descendant::a/text()" />
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="operandsize">
        <xsl:choose>
            <xsl:when test="descendant::t">
                <xsl:call-template name="translateTypeString">
                    <xsl:with-param name="string" select="descendant::t/text()" />
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template mode="syntax" match="syntax[1]">
        <mnemonic><xsl:value-of select="mnem" /></mnemonic>
        <xsl:for-each select="src|dst">
            <operand>
                <type><xsl:call-template name="operandtype" /></type>
                <size><xsl:call-template name="operandsize" /></size>
            </operand>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="new-entry">
        <xsl:param name="opcode" required="yes" />

        <instruction>
            <value><xsl:value-of select="$opcode" /></value>
            <xsl:apply-templates mode="syntax" />
        </instruction>
    </xsl:template>

    <xsl:template name="new-Zop-instruction">
        <xsl:param name="opcode" required="yes" />
        <xsl:param name="index" select="0" />

        <!-- output the result -->
        <xsl:call-template name="new-entry">
            <xsl:with-param name="opcode" select="number($opcode + $index)" />
        </xsl:call-template>

        <!-- increment counter and try again -->
        <xsl:choose>
            <xsl:when test="$index &lt; 7">
                <xsl:call-template name="new-Zop-instruction">
                    <xsl:with-param name="opcode" select="$opcode" />
                    <xsl:with-param name="index" select="$index + 1" />
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="primary_opcode">
        <xsl:param name="opc_value" required="yes" />

        <xsl:for-each select="entry[
            not(@attr='invd' or @attr='undef' or @mode='e' or grp1/text() = 'prefix') and not(descendant::sec_opcd)
            ]">

            <xsl:sort select="number(proc_start) or number(00)" data-type="number" order="descending"/>

            <xsl:choose>
                <xsl:when test="syntax/src/a/text()='Z' or syntax/dst/a/text()='Z'">
                    <xsl:call-template name="new-Zop-instruction">
                        <xsl:with-param name="opcode" select="$opc_value" />
                    </xsl:call-template>
                </xsl:when>

                <xsl:when test="position()=1">
                    <xsl:call-template name="new-entry">
                        <xsl:with-param name="opcode" select="$opc_value" />
                    </xsl:call-template>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="//one-byte/pri_opcd">
        <xsl:call-template name="primary_opcode">        
            <xsl:with-param name="opc_value" select="utils:fromHex(@value)" />
        </xsl:call-template>
    </xsl:template>

    <!-- FIXME: these need to be checked/verified -->
    <xsl:template match="//two-byte/pri_opcd">
        <xsl:call-template name="primary_opcode">        
            <xsl:with-param name="opc_value" select="utils:fromHex(@value) + 256" />
        </xsl:call-template>
    </xsl:template>

    <xsl:template match="/">
        <ia32>
            <xsl:apply-templates />
        </ia32>
    </xsl:template>

</xsl:transform>
