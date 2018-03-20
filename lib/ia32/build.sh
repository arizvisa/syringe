#!/bin/sh
LANGUAGE=python
Transform -s:x86reference.xml -xsl:generate-table.xslt -o:operand-table.xml
perl generate-table.pl --format=${LANGUAGE} -f operand-table.xml
