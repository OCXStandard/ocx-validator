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
            <sch:assert test="not(@ocx:refType) and count(//*/@ocx:GUIDRef[. = $currentGuid]) = 1">
                Element <sch:value-of select="$currentNode"/> with GUIDRef <sch:value-of select="$currentGuid"/> must not have ocx:refType attribute and should have a unique value for ocx:GUIDRef.
            </sch:assert>
        </sch:rule>
   </sch:pattern>
</sch:schema>
