#  Copyright (c) 2022 3Docx.org, see the LICENSE

from lxml import etree as ET
import re
from .schema import OCXSchema, SchemaElement, SchemaEnumerator, DELIMITER, OCXEtree
from .utils import ns_prefix, strip_namespace_tag, strip_ns_prefix, MsgLine


# The OCX schema base class implementation
class Base:
    def __init__(self, object: ET.Element, etree:OCXEtree, schema:OCXSchema, validateEnums: bool, enumerations: dict = {}):
        self.object = object
        self.schema = schema
        self.etree = etree
        self.validateEnums = validateEnums
        self.enumerations = enumerations
        self.error_message = [] # List of error messages from validations
        self.tag = object.tag
        self.dimensionless = False
        self.logger = schema.logger
        # Check if this is a valid tag name defined by the schema
        if self.schema.is_schema_tag(self.tag) is True:
            schema_element = self.schema.get_element_from_tag(self.tag)
            self.schemaElement =  SchemaElement(schema_element, self.schema, self.tag)
        else:
            self.schemaElement = None
        # Special handling of unitsml:Unit
        if self.get_name() == 'Unit':
            if self.schemaElement is not None:
                attrib = self.object.attrib
                # If the Unit contains a pointer to a Dimension, we can check if the Unit is dimensionless
                if 'dimensionURL' in attrib:
                    dimURL = attrib['dimensionURL']
                    root = self.etree.get_root()
                    dimension = root.findall('.//{*}Dimension')
                    for dim in dimension:
                        values = list(dim.attrib.values())
                        keys = list(dim.attrib.keys())
                        if dimURL in values and 'dimensionless' in keys:
                           dimensionless = dim.attrib['dimensionless']
                           if dimensionless == 'true':
                               self.dimensionless = True

    def is_dimensionless(self)->bool:
        return self.dimensionless

    def validate(self)->list:
        if self.schemaElement is not None:
            # Check for presence of all mandatory elements
            self.validate_mandatory_element_presence()
            # Validate sub-element names
            self.validate_children_names()
            # Validate mandatory attributes
            self.validate_mandatory_attributes()
            # Validate any assertions
            self.validate_assertions()
        if len(self.error_message) > 0:
            bsource = ET.tostring(self.object, with_tail=False, pretty_print=True) # Write the elements xml code to a byte string
            source = bsource.decode().replace('\t',' ') # Replace tab characters with white space
            self.error_message.append({'Line': self.get_sourceline(),'Source':source})
        return self.error_message

    def get_error_messages(self)->list:
        return self.error_message

    def get_sourceline(self)->str:
        return self.object.sourceline

    def get_name(self)->str:
        qn = ET.QName(self.object)
        return qn.localname

    def get_namespace(self)->str:
        qn = ET.QName(self.object)
        return qn.namespace

    def get_tag(self)->str:
        return self.object.tag

    def get_ns_prefix(self)->str:
        ns_prefix = 'unknown'
        ns = self.get_namespace()
        nsmap = self.schema.get_name_space()
        for prefix in nsmap:
            if ns == nsmap[prefix]:
                ns_prefix = prefix
        return ns_prefix

    def get_ns_map(self):
        return self.schema.get_name_space()

    def get_schema_type(self)->str:
        typ = 'unknown'
        if self.schemaElement is not None:
            typ = self.schemaElement.get_type()
        return typ

    # Returns my own schema ET.Element
    def get_schema_element(self)->ET.Element:
        return self.schemaElement

    def get_super_type(self)->str:
        return self.schemaElement.my_parent()

    # Returns all mandatory schema sub elements of class SubElement
    def get_mandatory_children(self)->list:
        mandatory = []
        e = self.get_schema_element()
        children = e.get_schema_children()
        for name in children:
            child = children[name]
            if child.is_mandatory():
                type = child.get_type()
                if self.is_dimensionless() is False:
                    mandatory.append(child)
                # if type == 'unitsml:RootUnits' and self.is_dimensionless() is True: # ToDo: Check this test. Skip RottUnits only if dimensionless
                #     mandatory.append(child)
                # else:
                #     mandatory.append(child)
        return mandatory

    def get_children_names(self)->list:
        children = self.schemaElement.get_schema_children()
        names = []
        for child in children:
            names.append(child.get_type())
        return names

    # Returns all  the element type schema attributes types of class Attribute
    def get_attributes(self)->list:
        e = self.get_schema_element()
        return e.get_schema_attributes()

    # Returns all  the mandatory element type schema attributes types of class Attribute
    def get_mandatory_attributes(self)->list:
        mandatory = []
        e = self.get_schema_element()
        for att in e.get_schema_attributes():
            if att.is_mandatory():
                mandatory.append(att)
        return mandatory

    # Returns all  possible schema sub elements as dictionary keys
    def get_children(self)->list:
        e = self.get_schema_element()
        return  e.get_schema_children()

    def validate_name(self)->list:
        # Self validation
        if self.schema.is_schema_tag(self.tag):
            self.error_message.append({'Line': self.get_sourceline(),
                                           'Msg':'Unknown schema type: {}'.format(self.get_name())})
        return self.error_message

    def validate_assertions(self):
        schema_element = self.get_schema_element()
        if schema_element.has_assertions():
            assertions = schema_element.get_assertions()
            types = {}
            # Get attribute names from the assertions
            for test in assertions:
                search = re.findall(r'@\w+[\b:]\w+|@\w+\b',test)
                for t in search:
                    typ = t.replace('@','')
                    # add any namespace tags
                    name = strip_ns_prefix(t)
                    prefix = ns_prefix(typ)
                    namespace = self.schema.get_name_space()
                    if prefix is not None:
                        tag = namespace[prefix]
                        qn = ET.QName(tag,name)
                        types[qn.text] = t
                    types[typ] = t
            # With unique names, carry out the assertion of the attributes
            # At least one of the assertion types must be an attribute
            found = False
            object_attrib = self.object.attrib
            for attrib in object_attrib:
                if attrib in types:
                    found = True
            if found is not True:
                self.error_message.append({'Line': self.get_sourceline(),
                                           'Msg': 'Missing one required attribute. At least one of the valid types must be present: {}'.format(list(types.keys()))})
        return self.error_message

    def validate_mandatory_attributes(self)->list:
        # Check for presence of all mandatory attributes
        object_attrib = self.object.attrib
        attributes = self.get_attributes()
        for name in attributes:
            att = attributes[name]
            if att.is_mandatory() is True:
                typ = att.get_typed_name()
                found = False
                for attrib in object_attrib:
                    if strip_namespace_tag(attrib) == name:  # Strip off the namespace tag if an attribute carry this
                        found = True
                if found is not True:
                    self.error_message.append({'Line': self.get_sourceline(),
                                               'Msg':'Missing mandatory attribute: {}'.format(typ)})
        # Validate enumerations enumeration values
        for attrib in object_attrib:
            if self.validateEnums and self.get_super_type() != 'Quantity_T':
                self.validate_enum_values(attrib, object_attrib[attrib], self.get_ns_prefix())
        return self.error_message

    def validate_enum_values(self, tag: str, enum_value: str, prefix: str)->list:
        qn = ET.QName(tag)
        name = qn.localname
        if prefix is not None:
            name = prefix + ':' + name
        # Check for enumeration values
        for type in self.enumerations:
            enum = self.enumerations[type]
            if name == enum.get_type():
                enum_values = enum.get_values()
                if enum_value not in enum_values:
                    self.error_message.append({'Line': self.get_sourceline(),
                             'Msg': 'Illegal enumerator value: {} = "{}". Legal values: {}'.format(name,enum_value, list(enum_values.keys()))})
        return self.error_message

    def validate_mandatory_element_presence(self)->list:
        # Check for presence of all mandatory elements
        # For a sequence of elements, all must be present
        found = {}
        not_found = {}
        choice = False
        children = self.get_mandatory_children()
        for child in children:
            tag = child.get_tag()
            prefixed_name = child.get_type()
            type = child.get_typed_name()
            if child.is_choice():
                choice = True
                search = self.get_named_children(type)
                if len(search) > 0:
                    found[type] = type
                else:
                    not_found[type] = type
            else:
                presence = self.get_named_children(type)
                if len(presence) == 0:
                    self.error_message.append({'Line': self.get_sourceline(),
                                           'Msg':'Missing mandatory sub-element: {}'.format(type)})
        if len(found) == 0 and choice is True:
            self.error_message.append({'Line': self.get_sourceline(),
                                       'Msg': 'Missing a mandatory sub-element. Valid types are: {}'.format(list(not_found.values()))})
        return self.error_message

    def validate_children_names(self)->list:
        # Check sub-element tags
        for e in self.object.iterchildren(tag=ET.Element): # Only iterate children
            tag = e.tag
            qn = ET.QName(tag)
            name = qn.localname
            line = e.sourceline
            if self.schema.is_schema_tag(tag) is not True:
                if self.schema.is_schema_name(name) is True:
                    self.error_message.append({'Line':line,
                    'Msg':'Element {} is missing the mandatory namespace prefix: {}'.format(name,
                                               self.schema.get_schema_nsprefix(self.schema.names[name]))})

                else:
                    self.error_message.append({'Line':line,
                                               'Msg':'Element {} is not defined in the schema'.format(strip_namespace_tag(tag))})
        return self.error_message

    def get_named_children(self, name: str, namespace: str = '{*}')->list:
        children = []
        for child in self.object.iterchildren():
            qn = ET.QName(child)
            localname = qn.localname
            str_name = strip_ns_prefix(name)
            if localname == str_name:
                children.append(child)
        return children


class IDBase(Base):
    def __init__(self, object, etree:OCXEtree,schema: OCXSchema, validateEnums: bool, enumerations: dict):
        super().__init__(object, etree, schema, validateEnums, enumerations)
        self.id = object.get('id')

    def get_id(self):
        return self.id


class DescriptionBase(IDBase):
    def __init__(self, object, etree:OCXEtree, schema: OCXSchema, validateEnums: bool, enumerations: dict):
        super().__init__(object,  etree, schema,  validateEnums, enumerations)
        description = object.findall('.//{*}Description',schema.namespace)
        if description == None:
            self.hasDesc = False
        else:
            self.description = description
            self.hasDesc = True
        return

    def get_description(self):
        return self.description

    def has_description(self):
        return self.hasDesc



class EntityBase(DescriptionBase):
    def __init__(self, object,  etree:OCXEtree, schema: OCXSchema,  validateEnums: bool, enumerations: dict):
        super().__init__(object,  etree, schema,  validateEnums, enumerations)
        self.guid = self.get_object_guid(object)

    def get_guid(self):
        return self.guid

    def get_clean_guid(self):
        cleanguid = None
        if self.guid is not None:
            cleanguid = re.sub(r'[\{\}]*', '', self.guid)  # Remove the  brackets
            cleanguid = cleanguid.lower() # Return lower case GUID
        return cleanguid

    def get_object_guid(self, object: ET.Element) -> str:
        attributes = object.attrib
        qn = ET.QName(object)
        namespace = qn.namespace
        guid = None
        if namespace is not None:
            guidref = '{' + namespace + '}' + 'GUIDRef'
        else:
            guidref = 'GUIDRef'
        if guidref in attributes:
            guid = attributes[guidref]
        return guid


# 3Docx validator: validation of the 3Docx xml aginst the OCX schema
class OCXValidator:
    def __init__(self, ocxfile: str, schema: OCXSchema, validate_enums: bool, print_source:bool):
        self.ocxFile = ocxfile
        self.schema = schema
        self.errors = {}
        self.logger = schema.logger
        self.printSource = print_source
        self.validateEnums = validate_enums
        self.namespace = self.schema.get_name_space()
        self.countOfValidatedObjects = 0 # The number of objects validated
        self.etree = OCXEtree(ocxfile, schema, self.logger)
        # Create the enumeration objects
        self. enumerations = {}
        if validate_enums is True:
            schema_enums = self.schema.get_enumerations()
            for typ in schema_enums:
                element = SchemaEnumerator(typ, schema_enums[typ])
                self.enumerations[typ] = element
        # Create the schema elements
        elements = self.schema.get_elements()
        self.schemaElements = {}
        for typ in elements:
            tag = self.schema.get_tag_from_type(typ)
            element = SchemaElement(elements[typ], self.schema, tag)
            self.schemaElements[tag] = element

    # Import the OCX XML file
    def import_model(self)->bool:
        return self.etree.import_model(self.namespace)

    # Validate all model object instances against the schema
    def print_model_objects(self, objects: list):
        self.logger.info(DELIMITER)
        self.logger.info('Dump of OCX model objects')
        self.logger.info(DELIMITER)

        print_objects = {} # Collection of objects to validate
        # Get root element
        root = self.etree.get_root()
        for item in root.iter(tag= ET.Element):
            tag = item.tag
            if self.schema.is_schema_tag(tag): # Only validate valid schema types
                print_objects[tag] = item
        for e in print_objects:
            self.print_type_info(print_objects[e])
        return

    def validated(self)->int:
        return self.countOfValidatedObjects

    # Validate the enumeration values
    def validate_all_enums(self)->int:
        enums = self.schema.get_enumerations()
        # Get root element
        root = self.etree.get_root()
        n0 = 0
        for name in enums:
            enum = SchemaEnumerator(name, enums[name])
            enum_values = enum.get_values()
            print('Checking {}'.format(name))
            check = root.findall('.//{*}*[@'+name+']')
            for item in check:
                enum_val = item.get(name)
                qn = ET.QName(item)
                check_name = qn.localname
                line = item.sourceline
                print('Checking {}: {}, {}. Value: {}'.format(name,line, check_name,enum_val))
        return n0

    # Validate all model object instances against the schema
    def validate_model_objects(self, validate: bool, objects: list)->int:
        validate_unique = {} # Collection of the unique objects to validate
        validate_all = [] # Collection all objects to validate
        # Get root element
        root = self.etree.get_root()
        n0 = 0
        count = 0
        for item in root.iter(tag= ET.Element):
            qn = ET.QName(item)
            name = qn.localname
            tag = item.tag
            if self.schema.is_schema_tag(tag): # Only validate valid schema types
                if len(objects) > 0:
                    if name in objects:
                        validate_all.append(item)
                        validate_unique[tag] = item
                else:
                    validate_all.append(item)
                    validate_unique[tag] = item
        if validate:
            for e in validate_all:
                count = count + 1
                n = self.validate_object(e)
                qn = ET.QName(e)
                name = qn.localname
                if n > 0:
                    self.logger.error('{} contains {} schema errors'.format(name, n))
                    n0 = n0 + n
                else:
                    self.logger.info(MsgLine(name, 'OK').msg())
        else:
            for e in validate_unique:
                count = count + 1
                n = self.validate_object(validate_unique[e])
                qn = ET.QName(e)
                name = qn.localname
                if n > 0:
                    self.logger.error('{} contains {} schema errors'.format(name, n))
                    n0 = n0 + n
                else:
                    self.logger.info(MsgLine(name, 'OK').msg())
        self.countOfValidatedObjects = count
        return n0

    # Check if there are invalid names in the model
    def validate_names(self)->int:
        # Find root element
        self.logger.info('Validating all schema names...')
        root = self.etree.get_root()
        illegal_tag = {}
        missing_ns = {}
        for item in root.iter(tag= ET.Element):
            tag = item.tag
            qn = ET.QName(item)
            name = qn.localname
            ns = qn.namespace
            line = item.sourceline
            if self.schema.is_schema_tag(tag) is not True:
                if self.schema.is_schema_name(name) is True:
                    missing_ns[name] = self.schema.get_schema_nsprefix(self.schema.names[name])
                else:
                    illegal_tag[name] = name
        names = []
        for name in illegal_tag:
            names.append(name)
        n = len(names)
        if n > 0:
             self.logger.error('Found unknown schema types (probably mis-spelled): {}'.format(names))
        for name in missing_ns:
            self.logger.error('Element {} does not contain the mandatory namespace prefix: {}'.format(name, missing_ns[name]))
            n = n + 1
        return n


    # Carry out a full validation of  the named model object against the xsd schema
    def validate_object(self, element: ET.Element)->int:
        e = EntityBase(element, self.etree, self.schema, self.validateEnums, self.enumerations)
        type = e.get_schema_type()
        n = 0
        qn = ET.QName(element)
        name = qn.localname
        if len(e.validate()) > 0:
            self.logger.error('Line {}: {} of type {} is not valid.'.format(e.get_sourceline(), name,
                                                                            type))
            errors = e.get_error_messages()
            for err in errors:
                if 'Source' in err:
                    msg = err['Source']
                    line = err['Line']
                    if self.printSource:
                        lines = msg.splitlines()
                        for xml in lines:
                            self.logger.error('Line {}: {}'.format(line, xml))
                            line = line + 1
                else:
                    n = n + 1
                    line = err['Line']
                    msg = err['Msg']
                    self.logger.error(
                        '     Line {}: {}'.format(line, msg))
        return n

    def print_type_info(self, element: ET.Element):
        e = EntityBase(element, self.model, self.schema,self.validateEnums, self.enumerations)
        name = e.get_name()
        tag = e.get_tag()
        type = e.get_schema_type()
        prefix = e.get_ns_prefix()
        children = e.get_children()
        cnames = []
        ctags = []
        ctypes = []
        # Verify that the tags are the same
        if tag != element.tag:
            self.logger.error('The tags are not the same for Element: {} and schema {}'.format(element.tag, tag))
        for child in children:
            cnames.append(child.get_type())
            ctypes.append(child.get_type())
            ctags.append(child.get_tag())
        self.logger.info('Element {}:{} Type: {} Tag: {}'.format(prefix, name,type,tag))
        if len(children) > 0:
            self.logger.info('        Children names: {}'.format(cnames))
            self.logger.info('        Children types: {}'.format(ctypes))
            self.logger.info('        Children tags:  {}'.format(ctags))
        attributes = e.get_attributes()
        cnames = []
        ctags = []
        ctypes = []
        for a in attributes:
            cnames.append(a.get_type())
            ctypes.append(a.get_type())
            ctags.append(a.get_tag())
        if len(attributes) > 0:
            self.logger.info('        Attribute names:{}'.format(cnames))
            self.logger.info('        Attribute types:{}'.format(ctypes))
            self.logger.info('        Attribute tags: {}'.format(ctags))
        return

    def validateUnits(self):
        n = 0
        for unit in self.model.getUnitsML():
            t = UnitsML(unit, self.model, self.schema)
            err = t.validate()
            if len(err) > 0:
                self.logger.error('At line {}: {} with name {} is not valid.'.
                                  format(t.get_sourceline(), t.get_localname(), t.getName()))
                errors = t.get_error_messages()
                for err in errors:
                    n = n +1
                    line = err['Source']
                    msg = err['Msg']
                    self.logger.error('    At line {}: {}'.
                                      format(line,msg))
        # UnitSet
        for unit in self.model.getUnitSet():
            t = UnitsML(unit, self.model, self.schema)
            err = t.validate()
            if len(err) > 0:
                self.logger.error('At line {}: {} with name {} is not valid.'.
                                  format(t.get_sourceline(), t.get_localname(), t.getName()))
                errors = t.get_error_messages()
                for err in errors:
                    n = n +1
                    line = err['Source']
                    msg = err['Msg']
                    self.logger.error('    At line {}: {}'.
                                      format(line,msg))
        # DimensionSet
        for unit in self.model.getDimensionSet():
            t = UnitsML(unit, self.model, self.schema)
            err = t.validate()
            if len(err) > 0:
                self.logger.error('At line {}: {} with name {} is not valid.'.
                                  format(t.get_sourceline(), t.get_localname(), t.getName()))
                errors = t.get_error_messages()
                for err in errors:
                    n = n +1
                    line = err['Source']
                    msg = err['Msg']
                    self.logger.error('    At line {}: {}'.
                                      format(line,msg))
        return n

