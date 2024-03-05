<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            queryBinding="xslt2">
   <sch:ns uri="https://3docx.org/fileadmin//ocx_schema//V300rc1//OCX_Schema.xsd" prefix="ocx"/>
   <sch:title>Unique GUIDref</sch:title>
   <sch:pattern>
        <sch:rule context="*[@*:GUIDRef]">
          <sch:let name="currentGuid" value="@*:GUIDRef"/>
          <sch:assert test="count(//*[@*:GUIDRef = $currentGuid]) = 1">
            Element with guid "<sch:value-of select="$currentGuid"/>" must be unique.
          </sch:assert>
        </sch:rule>
   </sch:pattern>
</sch:schema>
