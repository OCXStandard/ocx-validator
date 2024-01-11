<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            queryBinding="xslt2">
   <sch:ns uri="http://data.dnvgl.com/Schemas/ocxXMLSchema" prefix="ocx"/>
   <sch:title>Plate Rules Schematron</sch:title>
   <sch:pattern id="T01_UniquePlateGUIDRef">
	 <sch:title>Plate GUIDRef should be unique.</sch:title>
      <sch:rule context="ocx:ocxXML/ocx:Vessel/ocx:Plate">
         <sch:let name="guid" value="@*:GUIDRef"/>
         <sch:assert test="count(//ocx:Plate[@*:GUIDRef=$guid]) = 1">Plate (GUIDRef = <sch:value-of select="$guid"/>) is not unique. (count: <sch:value-of select="count(//ocx:Plate[@*:GUIDRef=$guid])"/>)</sch:assert>
      </sch:rule>
   
      <sch:rule context="ocx:ocxXML/ocx:Vessel/ocx:Panel/ocx:ComposedOf/ocx:Plate">
         <sch:let name="guid" value="@*:GUIDRef"/>
         <sch:assert test="count(//ocx:Plate[@*:GUIDRef=$guid]) = 1">Plate (GUIDRef = <sch:value-of select="$guid"/>) is not unique. (count: <sch:value-of select="count(//ocx:Plate[@*:GUIDRef=$guid])"/>)</sch:assert>
      </sch:rule>
   </sch:pattern>
   
   <sch:pattern id="T02_PlateMaterial_refers_Material">
	  <sch:title>PlateMaterial should refer to an existing Material.</sch:title>
      <sch:rule context="/ocx:ocxXML/ocx:Vessel/ocx:Panel/ocx:ComposedOf/ocx:Plate/ocx:PlateMaterial">
         <sch:let name="guid" value="@*:GUIDRef"/>
         <sch:assert test="//ocx:Material[@*:GUIDRef=$guid]">PlateMaterial refers NOT to a Material with GUIDRef = <sch:value-of select="$guid"/>.</sch:assert>
      </sch:rule>
   </sch:pattern>

</sch:schema>
