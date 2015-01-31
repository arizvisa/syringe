Transform -s:test.xml -xsl:generate-table.xslt -o:operand-table.xml
perl generate-table.pl < operand-table.xml >| _optable.py
