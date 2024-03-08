<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" xmlns:xsd="http://www.w3.org/2001/XMLSchema" queryBinding="xslt2">
   <sch:title>Units shall have RootUnits</sch:title>
   <sch:pattern id="UnithasRootUnits">
        <sch:rule context="*:Unit">
            <sch:let name="currentID" value="@*:id"/>
            <sch:let name="currentNode" value="name()"/>
            <sch:let name="n_rootUnits" value="count(*:RootUnits)"/>
            <sch:let name="dimensionURL" value="@dimensionURL"/>
            <sch:let name="dimensionLess" value="test([//*:Dimension[@dimensionless]] and [*:Dimension[@xs:id] eq $dimensionURL)"/>
            <!--<sch:let name="dimensionLess" value="[//*:Dimension[@dimensionless]] eq true and [//*Dimension[@xml:id eq $dimensionURL]]"/> -->
            <sch:assert role="error" id="missing_root_units" test="count(*:RootUnits) eq 1 and $dimensionLess eq 0">
            Element <sch:value-of select="$currentNode"/> with id <sch:value-of select="$currentID"/> and <sch:value-of select="$dimensionURL"/>:
            The element has not a mandatory RootUnits element. Count:<sch:value-of select="$n_rootUnits"/> dimensionLess: <sch:value-of select="$dimensionLess"/>
            </sch:assert>
        </sch:rule>
   </sch:pattern>
</sch:schema>