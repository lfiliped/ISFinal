<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">
        <orders>
            <xsl:for-each select="//order[State='Texas']">
                <order>
                    <xsl:copy-of select="*"/>
                </order>
            </xsl:for-each>
        </orders>
    </xsl:template>
</xsl:stylesheet>
