<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            queryBinding="xslt2">
   <sch:ns uri="https://3docx.org/fileadmin//ocx_schema//V300b4//OCX_Schema.xsd" prefix="ocx"/>
   <sch:title>Unique GUIDref</sch:title>
   <sch:pattern>
        <sch:rule context="*[@ocx:GUIDRef]">
          <sch:let name="currentGuid" value="@ocx:GUIDRef"/>
            <sch:let name="currentID" value="@*:id"/>
            <sch:let name="currentNode" value="name()"/>
            <sch:let name="mycount" value="count(//*[name() eq $currentNode][@ocx:GUIDRef])"/>
            <sch:assert test="count(//*[name() eq $currentNode][@ocx:GUIDRef eq $currentGuid]) = 2">
                Element <sch:value-of select="$currentNode"/> with GUIDRef <sch:value-of select="$currentGuid"/> count= <sch:value-of select="mycount"/>.
            </sch:assert>
        </sch:rule>
   </sch:pattern>
</sch:schema>
