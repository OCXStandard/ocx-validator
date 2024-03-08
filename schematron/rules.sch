   <sch:title>Units shall have RootUnits</sch:title>
   <sch:pattern id="UnithasRootUnits">
        <sch:rule context="*:Unit">
            <sch:let name="currentID" value="@*:id"/>
            <sch:let name="currentNode" value="name()"/>
            <sch:assert test="position(//*[name() eq $currentNode][@ocx:GUIDRef eq $currentGuid]) = 2">
                Element <sch:value-of select="$currentNode"/> with GUIDRef <sch:value-of select="$currentGuid"/> count= <sch:value-of select="mycount"/>.
            </sch:assert>
        </sch:rule>
   </sch:pattern>