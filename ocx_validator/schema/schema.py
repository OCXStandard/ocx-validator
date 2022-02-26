#  Copyright (c) 2022. 3Docx.org, see the LICENSE.

from lxml import etree as ET # The lxml libraryis used to pars xsd and xml structures

import re
from collections import defaultdict
from .utils import strip_ns_prefix, ns_prefix, DELIMITER, MsgLine
import os

WW3_NAMESPACE = 'http://www.w3.org/2001/XMLSchema'
OCX_NAMESPACE = 'http://data.dnvgl.com/Schemas/ocxXMLSchema'
UNITSML_NAMESPACE = 'urn:oasis:names:tc:unitsml:schema:xsd:UnitsMLSchema_lite-0.9.18'
XML_NAMESPACE = 'http://www.w3.org/2001/XMLSchema'

def element_annotation(element: ET.Element):
    text = ''
    description = ''
    for text in ET.ElementTextIterator(element, with_tail=False):
        description = description + text
    text = re.sub('[\n\t\r]', '', description)  # Strip off special characters
    return text

# Helper class for schema qualified names
class SchemaQName:
    def __init__(self, type: str):
        qn = ET.QName(type)

# Class parsing the ocx Header information
class Header:
    def __init__(self, header: ET.Element):
        # Mandatory attriburtes
        self.ts = header.get('time_stamp')
        self.name = header.get('name')
        self.author = header.get('author')
        self.org = header.get('organization')
        self.system = header.get('originating_system')
        # Optional attributes
        version = header.get('application_version')
        if version is None:
            self.applicationVersion = ''
        else:
            self.applicationVersion = version
        doc = header.get('documentation')
        if doc is None:
            self.documentation = ''
        else:
            self.documentation = doc

        self.header = True

    def timestamp(self):
        return self.ts

    def author(self):
        return self.author

    def name(self):
        return self.name

    def organization(self):
        return self.org

    def originatingSystem(self):
        return self.system

    def hasHeader(self):
        return self.header

# xsd schema parser functionality
class OCXSchema:
    def __init__(self, namespace_prefix, logger):
        self.namespacePrefix = namespace_prefix  #The namespace used in the input schema
        self.schema_changes = [] # Schema changes in this OCX version
        self.model = None # Pointer to the 3Docx model of type ET.lxml tree
        # Lookup tables with parsed schema element.
        # Separate lookup tables are created for each schema
        # One dictionary is created for each imported schema on the form lookup_table[schema_namespace] = schema_type[name] = Element_Class
        self.lookup_table = {} # Global look-up tables
        self.attribute_group = {}  # Dictionary of the  schema global attribute groups (name:ET.Element)
        self.enums = {} # Dictionary of global enums  (name:ET.Element)
        self.substitution_groups = {}  # dict of groups with a collection of elements which are defined as a substitution to a group
        self.schema_types = []  # List of all known schema types
        self.schema_tags = {}  # Dict of all known schema types with tag as key: tag = '{namespace}name'
        self.names = {} # A map between global names and the required namespace prefix
        self.namespace = {}  # The namespaces defined in xsd schema. Used in object searches
        self.schemaBase = {} # A mapping between schema base and schema prefix
        self.version = 'No version'  # The schema version of the xsd
        self.logger = logger # The python logger
        self.schema_objects = {}  # The lookup table of all global schema elements
        self.parsed = False
        self.input_schema = ''
        self.referenced_schemas = [] # The list of all referenced schema used by xs:import
        self.mandatoryElements = ['unitsml:RootUnits','unitsml:EnumeratedRootUnit'] # Used to override schema optional elements to force mandatory elements


    def get_logger(self):
        return self.logger

    #Load the schema App_validate3DOcx (this is the most timeconsuming operation)
    def load_schema(self, lxmltree):
        self.xmlschema = ET.XMLSchema(lxmltree)
        return

    #Read the schema global elements and create the lookup tables
    def read_schema(self, xsd_file: str, all_changes: bool = False) -> bool:
        self.input_schema = xsd_file
        referenced_namespace = False  # For the input schema there is no referenced name space
        is_reference = False  # Ant the input schema is not a reference
        # Read the input schema and all referenced schemas
        self.parsed = self.read_referenced_schemas(xsd_file, referenced_namespace, self.namespacePrefix,
                                                   is_reference, all_changes)
        if self.parsed is True:
            # Add the missing xml namespace
            self.namespace['xml'] = XML_NAMESPACE
            self.logger.debug('Number of parsed schema types: {}'.format(len(self.schema_types)))
            n = 0
            for ns in self.lookup_table:
                objects = self.lookup_table[ns]
                for e in objects:
                    n += 1
                    self.logger.debug('{}: {}:{}'.format(n,ns,e))
        # Create the tag dicts
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                tag = self.get_tag(ns,name)
                self.schema_tags[tag] = objects[name]
                self.names[name] = tag
        return self.parsed

    def read_referenced_schemas(self, schema_ref: str, referenced_namespace: str, ns_prefix: str,
                                is_reference: bool, all_changes) -> bool:
        if schema_ref is None and is_reference is True:
            return True
        if is_reference is True:
            self.referenced_schemas.append(schema_ref)
        self.logger.info('Importing schema from location {}.....'.format(schema_ref))
        try:
            etree = ET.parse(schema_ref)  # Create the DOM tree
            self.logger.info('{} is OK'.format(schema_ref))
        # Catch syntax errors from the parsing
        except ET.XMLSyntaxError as error:
            self.logger.error('{} has syntax errors: {}'.format(schema_ref, error))
            self.parsed = False
            return False
        # Get new name space declarations and add to the nsmap
        # Default namespace prefixes are of type None. If more than one schema is using default namespaces,
        # the namespace will be lost
        namespace = etree.getroot().nsmap
        for ns in namespace:
            tag = namespace[ns]
            self.namespace[ns] = tag
        # Find referenced namespace prefix
        if is_reference is True:
            prefix = None
            for ns in self.namespace:
                if referenced_namespace == self.namespace[ns]:
                    if ns is not None:
                        prefix = ns
                    break
        else:
            prefix = ns_prefix
        # Get the lxml root
        root = etree.getroot()
        # Get the schema version if present
        self.find_schema_version(root)
        # Read the schema changes
        if is_reference is not True:
            self.schema_changes = self.parse_schema_changes(root, all_changes)
       # All global ocx elements
        complex_dict = {}
        element_dict = {}
        attribute_dict = {}
        simple_dict = {}
        enum_dict = {}
        schema_dict = {}
        elements = root.findall('.//{*}element[@name]', self.namespace)
        # All complex types
        complex = root.findall('.//{*}complexType[@name]', self.namespace)
        # All attributes
        attributes = root.findall('.//{*}attribute[@name]', self.namespace)
        # Attribute groups
        attribute_group = root.findall('.//{*}attributeGroup[@name]', self.namespace)
        # All simple types
        simpletypes = root.findall('.//{*}simpleType[@name]', self.namespace)
        # Find all elements which have a substitution group
        groups = root.findall('.//{*}element[@substitutionGroup]')
        # Don't include substitution groups, these are already in elements
        all_types = attributes + elements + attribute_group + simpletypes + complex
        # Get all enumerations
        enums = self.parse_attribute_enumerations(all_types)
        # Create the lookup tables
#        self.create_dict_from_name(elements, element_dict, prefix)
#        self.create_dict_from_name(complex, complex_dict, prefix)
#        self.create_dict_from_name(attributes, attribute_dict, prefix)
        self.create_dict_from_name(attribute_group, attribute_dict, prefix)
#        self.create_dict_from_name(simpletypes, simple_dict, prefix)
        self.create_dict_of_substitutiongroups(groups, self.substitution_groups, prefix)
        self.create_dict_from_name(enums, enum_dict, prefix)
        self.enums[prefix] = enum_dict
        self.create_dict_from_name(all_types, schema_dict, prefix)
        # Add parsed elements to the list of schema types
        self.create_list_of_types(schema_dict, self.schema_types, prefix)
        self.create_base_map(all_types, self.schemaBase, prefix)
        self.lookup_table[prefix] = schema_dict
        self.logger.debug(MsgLine('Number of elements added', len(all_types)).msg())
        # Log number of parsed types
        self.logger.debug(MsgLine('Number of global elements', len(elements)).msg())
        self.logger.debug(MsgLine('Number of complexType', len(complex)).msg())
        self.logger.debug(MsgLine('Number of simpleType', len(simpletypes)).msg())
        self.logger.debug(MsgLine('Number of attribute', len(attributes)).msg())
        self.logger.debug(MsgLine('Number of attributeGroup', len(attribute_group)).msg())
        self.logger.debug(MsgLine('Number of substitutionGroup', len(groups)).msg())
        self.logger.debug(MsgLine('Number of enums', len(enums)).msg())
        # Recursively traverse referenced schemas and read them
        references = root.findall('.//{*}import')
        for ref in references:
            loc = ref.get('schemaLocation')
            # Use the global path to the referenced schema
            schema = os.path.abspath(loc)
            namespace = ref.get('namespace')
            # Verify that the referenced namespace is in the nsmap
            present = False
            for ns in self.namespace:
                if namespace == self.namespace[ns]:
                    present = True
            if present is not True:
                self.logger.error('The referenced namespace {} is not among the defined namespaces; {}'
                                  .format(namespace, list(self.namespace.values())))
            self.parsed = self.read_referenced_schemas(schema, namespace, prefix, True, all_changes)
        return True

    def schema_info(self):
        self.logger.info(DELIMITER)
        self.logger.info('Schema summary')
        self.logger.info(DELIMITER)
        self.logger.info(MsgLine('Input schema', self.input_schema).msg())
        self.logger.info(MsgLine('Schema version', self.get_version()).msg())
        for ref in self.referenced_schemas:
            self.logger.info(MsgLine('Referenced schema', ref).msg())
        self.logger.info(MsgLine('Global elements', len(self.get_elements())).msg())
        self.logger.info(MsgLine('Complex types', len(self.get_complex())).msg())
        self.logger.info(MsgLine('Global attributes', len(self.get_attributes())).msg())
        self.logger.info(MsgLine('Attribute groups', len(self.get_attribute_groups())).msg())
        self.logger.info(MsgLine('Enumerators', len(self.get_enumerations())).msg())
        self.logger.info(MsgLine('Object dictionary', len(self.get_dictionary())).msg())
        self.logger.info('-----------------------------')
        self.logger.debug(MsgLine('Dictionary objects:', '').msg())

        all_types = self.get_dictionary()
        for e in all_types:
            self.logger.debug(e)
        return

    def is_schema_type(self, type: str)->bool:
        if type in self.schema_types:
            return True
        else:
            self.logger.debug('{} is not a known schema type'.format(type))
            return False

    def get_tag_from_type(self, type:str)->str:
        prefix = ns_prefix(type)
        name = strip_ns_prefix(type)
        tag = '{}'+ name
        if prefix in self.namespace:
            ns = self.namespace[prefix]
            qn = ET.QName(ns,name)
        else:
            qn = ET.QName(None,name)
        return qn.text


    def get_tag(self, prefix:str, name:str)->str:
        tag = '{*}' + name
        if prefix in self.namespace:
            ns = self.namespace[prefix]
            tag = '{' + ns + '}' + name
        return tag

    def get_schema_nsprefix(self, tag:str):
        qn = ET.QName(tag)
        prefix = 'unknown'
        for ns in self.namespace:
            if qn.namespace == self.namespace[ns]:
                prefix = ns
        return prefix

    def get_element_from_tag(self, tag: str)->ET.Element:
        if tag in self.schema_tags:
            return self.schema_tags[tag]
        else:
            return None

    def is_schema_tag(self, tag: str)->bool:
        if tag in self.schema_tags:
            return True
        else:
            self.logger.debug('{} is not a known schema tag'.format(tag))
            return False

    def is_schema_name(self, name: str)->bool:
        if name in self.names:
            return True
        else:
            self.logger.debug('{} is not a known schema name'.format(name))
            return False

    # A unique key is defined by the schema namespace prefix and the element name: key ="ns_prefix:name"
    def get_element_name(self, element: ET.Element, prefix: str) -> str:
        if 'name' in element.attrib:
            name = element.get('name')
        elif 'ref' in element.attrib:
            name = strip_ns_prefix(element.get('ref'))
        return name

    # Create a lookup table from a list of objects using key="name". The lookup table is amended to the input dict
    def create_dict_from_name(self,  items:list, types:dict, prefix):
        table = {}
        for element in items:
            name = self.get_element_name(element, prefix)
            table[name] = element
        # Sorted dict on names
        for key in sorted(table.keys()):
            types[key] = table[key]
        return

    # Create a lookup elelement_table from a list of ET.Element objects
    def create_list_of_types(self,  look_up_table:dict, types:list, prefix):
        for name in look_up_table:
            type = prefix + ':' + name
            types.append(type)
        return

    def create_base_map(self, items: list, basemap: dict, prefix):
        for element in items:
            base = element.base
            basemap[base] = prefix

    # Collect all elements belonging to a substitution group
    def create_dict_of_substitutiongroups(self,  items:list, types:dict, prefix):
        groups = defaultdict(list)
        for element in items:
            group = element.get('substitutionGroup')
            type = self.get_element_type(element, prefix)
            groups[group].append(type) # Add elements belonging to a group
        for key in groups:
            types[key] = groups[key]
        return

    # Collect all elements belonging to aa attribute group
    def create_dict_of_attributegroups(self,  items:list, types:dict, prefix):
        groups = defaultdict(list)
        for element in items:
            group = element.get('attributeGroup')
            type = self.get_element_type(element, prefix)
            groups[group].append(type) # Add elements belonging to a group
        for key in groups:
            types[key] = groups[key]
        return

    # A unique key is defined by the schema namespace prefix and the element name: key ="ns_prefix:name"
    def get_element_type(self, element: ET.Element, prefix: str) -> str:
        typ = prefix
        if 'name' in element.attrib:
            name = element.get('name')
        elif 'ref' in element.attrib:
            name = strip_ns_prefix(element.get('ref'))
        if 'type' in element.attrib:
            if name == 'Description':  # Override prefix for Description as it does not follow the normal schema pattern
                typ = 'ocx'
            else:
                typ = ns_prefix(element.get('type'))
        else:
            base = element.findall('.//{*}*[@base]')
            if len(base) > 0:
                typ = ns_prefix(base[0].get('base'))
            else:
                itemtype = element.findall('.//{*}*[@itemType]')
                if len(itemtype) > 0:
                    typ = ns_prefix(itemtype[0].get('itemType'))
        if typ is None:
            typ = prefix
        # Search through global types and replace the prefix if it is referenced
#        for ref in self.referenced_attr:
#            glob_name = strip_ns_prefix(ref)
#            if glob_name == name:
#                typ = ns_prefix(ref)
#                break
        return typ + ':' + name

    def get_element_tag(self, element: ET.Element, prefix: str) -> str:
        typ = self.get_element_type(element,prefix)
        return self.get_tag_from_type(typ)

    def xsd_tags(self, tags:dict, schema_root,  prefix:str):
        alltags = schema_root.findall('.//{' + self.namespace[prefix] + '}*')
        for element in alltags:
            i = element.tag.find('}')
            if not i == -1:
               typ = element.tag[i+1:len(element.tag)]
               tags[typ] = element.tag
        return

    def get_name_space(self):
        return self.namespace

    def get_version(self)->str:
        return self.version

    def get_schema_changes(self):
        return self.schema_changes

    def parse_schema_changes(self, root, all: bool):
        schema_changes = []
        changes = root.findall('.//{*}SchemaChange', self.namespace)
        for change in changes:
            version = change.get('version')
            if version == self.get_version() or all is True: #Only include changes for this schema version
                schemachange = {}
                schemachange['version'] = change.get('version')
                schemachange['author'] = change.get('author')
                schemachange['date'] = change.get('date')
                description = element_annotation(change) # Strip off special characters
                text =  re.sub('[\n\t\r]','', description)
                schemachange['description'] = text
                schema_changes.append(schemachange)
        return schema_changes

    def get_element_from_type(self, base: str, type:str)->ET.Element:
        prefix = ns_prefix(type)
        name = strip_ns_prefix(type)
        # Add the prefix
        if prefix is None:
            prefix = self.schemaBase[base]
        element = None
        tag = self.get_tag_from_type(prefix + ':' + name)
        if self.is_schema_tag(tag):
            element = self.get_element_from_tag(tag)
        return element

    def get_elements(self):
        elements = {}
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                element = objects[name]
                qn = ET.QName(element)
                if qn.localname == 'element':
                    elements[ns + ':' + name] = element
        return elements

    def get_dictionary(self):
        return self.schema_types

    def get_attributes(self):
        elements = {}
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                element = objects[name]
                qn = ET.QName(element)
                if qn.localname == 'attribute':
                    elements[ns + ':' + name] = element
        return elements

    def get_attribute_groups(self):
        elements = {}
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                element = objects[name]
                qn = ET.QName(element)
                if qn.localname == 'attributeGroup':
                    elements[ns + ':' + name] = element
        return elements

    def get_complex(self):
        elements = {}
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                element = objects[name]
                qn = ET.QName(element)
                if qn.localname == 'complexType':
                    elements[ns + ':' + name] = element
        return elements

    def get_enumerations(self):
        enums = {}
        for prefix in self.enums:
            objects = self.enums[prefix]
            for name in objects:
                enum = objects[name]
                enums[prefix + ':' + name] = enum
        return enums

    def get_substitution_groups(self):
        return self.substitution_groups


    def get_simpletypes(self):
        elements = {}
        for ns in self.lookup_table:
            objects = self.lookup_table[ns]
            for name in objects:
                element = objects[name]
                qn = ET.QName(element)
                if qn.localname == 'simpleType':
                    elements[ns + ':' + name] = element
        return elements

    # Attributes enumerators
    def parse_attribute_enumerations(self, attributes:list):
        enums = {}
        for typ in attributes:
            enumerations = typ.findall('.//{*}enumeration', self.namespace)
            if len(enumerations) > 0:
                qn = ET.QName(typ)
                name = typ.get('name')
                if name is not None:
                    enums[typ] = typ
        return enums

    def find_schema_version(self, root):
        # Retrieve the schemaVersion if present
        version = root.findall('.//{*}attribute[@name="schemaVersion"]', self.namespace)
        if len(version) > 0:
            self.version = version[0].get('fixed')  # The version number
        return



# Class establishing the cardinality of an element
class Cardinality:
    def __init__(self, element: ET.Element, reference:ET.Element):
        self.element = element # Always the local element
        self.use = ''
        self.lower = ''
        self.upper = ''
        self.default = ''
        self.fixed = ''
        self.choice = False
        if reference is not None:
            self.cardinality(reference) # The reference has default cardinality
        self.cardinality(element) # The local element overrides any defaults

    def cardinality(self, element):
        qn = ET.QName(element)
        attributes = element.attrib
        if qn.localname == 'element':
            if 'minOccurs' in attributes:
                self.lower = attributes['minOccurs']
                if self.lower == '0':
                    self.use = 'opt.'
                else:
                    self.use = 'req.'
                    if 'minOccurs' in attributes:
                        self.lower = attributes['minOccurs']
                    else:
                        self.lower = '1'
            else:
                self.use = 'req.'
                self.lower = '1'
            if 'maxOccurs' in attributes:
                self.upper = attributes['maxOccurs']
            else:
                self.upper ='1'
            # Find closest sequence or choice ancestor which overrules mandatory use
            for item in self.element.iterancestors('{*}sequence', '{*}choice'):
                attributes = item.attrib
                qn = ET.QName(item)
                if qn.localname == 'choice':
                    self.choice = True
                if 'minOccurs' in attributes:
                    if attributes['minOccurs'] == '0':
                        self.use = 'opt.'
                        self.lower = '0'
                if 'maxOccurs' in attributes:
                    self.upper = attributes['maxOccurs']
                break
        if qn.localname == 'attribute':
            self.upper = '1'
            attributes = self.element.attrib
            if 'use' in attributes:
                if attributes['use'] == 'required':
                    self.use = 'req.'
                    self.lower = '1'
            else:
                self.use = 'opt.'
                self.lower = '0'
            if 'default' in attributes:
                self.default = attributes['default']
            if 'fixed' in attributes:
                self.fixed = attributes['fixed']
        return

    def get_cardinality(self):
        if self.upper == 'unbounded':
            self.upper = u'\u221E' # UTF-8 Infinity symbol
        return '[' + self.lower + ',' + self.upper +']'

    def is_mandatory(self)->bool:
        if self.use == 'req.':
            return True
        else:
            return False

    def is_choice(self):
        return self.choice

    def put_choice(self, choice: bool):
        self.choice = choice

class SchemaBase:
    def __init__(self, element: ET.Element, schema: OCXSchema, logger, tag: str):
        self.schema = schema
        self.logger = logger
        self.element = element
        self.tag = tag
        self.namespace = element.nsmap
        object = SchemaType(element, schema)
        self.type = object.get_type()
        self.name = object.get_name()
        self.referencedElement = object.get_referenced_element()
        # The element cardinality
        self.cardinalityObject = Cardinality(element, self.referencedElement)
        # The element documentation
        annotation_object = Annotation(self.get_name(),self.element, self.referencedElement, logger)
        self.annotation = annotation_object.find_annotation(self.referencedElement)

    # Used to override the element documentation using any locally declared annotation
    def put_annotation(self, element: ET.Element):
        annotation = Annotation(element, self.logger)
        self.annotation = annotation.find_annotation()

    def get_cardinality_object(self)->Cardinality:
        return self.cardinalityObject

    # Used to override the cardinality
    def put_cardinality(self, cardinality:Cardinality):
        self.cardinalityObject = cardinality

    def get_annotation(self) -> str:
        return self.annotation

    def get_type(self)->str:
        return self.type

    def get_name(self) -> str:
        return self.name

    def is_mandatory(self)->bool:
        if self.get_typed_name() in self.schema.mandatoryElements: # Force mandatory elements
            return True
        else:
            return self.cardinalityObject.is_mandatory()

    def is_choice(self)->bool:
        return self.cardinalityObject.is_choice()

    def put_choice(self, choice: bool):
        self.cardinalityObject.put_choice(choice)

    def get_cardinality(self)->str:
        return self.cardinalityObject.get_cardinality()

    def get_use(self)->str:
        return self.cardinalityObject.use

    def get_prefix(self)->str:
        return ns_prefix(self.get_type())

    def get_nsmap(self)->dict:
        return self.namespace

    def get_typed_name(self)->str:
        prefix = self.get_prefix()
        name = self.get_name()
        if prefix is not None:
            return prefix + ':' + name
        else:
            return name

    def get_tag(self)->str:
        if self.tag == 'None':
            prefix = self.get_prefix()
            nsmap = self.get_nsmap()
            if prefix in nsmap:
                tag = nsmap[prefix]
            else:
                tag = '*'
            return '{' + tag + '}' + self.get_name()
        else:
            return self.tag

    def is_abstract(self)->bool:
        if 'abstract' in self.element.attrib:
            return True
        else:
            return False

class SchemaElement(SchemaBase):
    def __init__(self, element: ET.Element, schema: OCXSchema, tag: str = 'None'):
        super().__init__(element, schema, schema.logger, tag)
        self.parents = [] # list of super types on the form prefix:name (str)
        self.children = {} # All children of type SchemaChild including also parent children
        self.attributes = {} # All my Attributes including also parent attributes
        self.recursive_find_parents(self.get_type())  # Recursively find all xsd supertypes
        self.schemaBase = element.base
        self.assertions = self.find_all_assertions()


    # Return my  parent if any
    def my_parent(self)->str:
        if len(self.parents)>0:
            return self.parents[0]
        else:
            return None

    def get_assertions(self):
        return self.assertions

    def has_assertions(self):
        if len(self.assertions) > 0:
            return True
        else:
            return False

    # Return all element children as a list. Empty if no children
    def get_schema_children(self)->list: # Return list of sub elements of class SchemaChild
        # Direct descendants
        self.find_sub_elements(self.get_type())
        # Parent descendants
        for parent in reversed(self.parents):
            if parent is not None: self.find_sub_elements(parent)
        return self.children


    # Recursive function retrieving all complex types (parent, grand parent ....)
    def recursive_find_parents(self, cmplx_type: str):
        if cmplx_type is not None:
            complex = self.schema.get_complex()
            if cmplx_type in complex: # Check that the type is a 'complex' schema type
                cmplx_obj = complex[cmplx_type] # Retrieve the ET.Element
                cmplxCont = cmplx_obj.find('{*}complexContent',
                                       self.schema.namespace)  # xs:complexContent defines the super type
                if cmplxCont is not None:
                    for parent in cmplxCont.iterchildren('{*}extension',
                                                     '{*}restriction'):  # supertype is either extension or restriction
                        type = SchemaType(parent, self.schema)
                        parent_type = type.get_type()
                        if parent_type is not None:
                            self.parents.append(parent_type)
                            self.recursive_find_parents(parent_type)
                else:
                    return
            else:
                return
        return

    # Finds all children of a named type
    def find_sub_elements(self, type: str):
        element = self.schema.get_element_from_type(self.schemaBase, type)
        if element is not None:
            for child in element.iter('{*}element'):
                subelement  = SchemaChild(child, self.schema, self.logger)
                # Add any substitutions
                name = subelement.get_typed_name()
                groups = self.schema.get_substitution_groups()
                if name in groups:
                    for sub_type in groups[name]:
                        element = self.schema.get_element_from_type(self.schemaBase,sub_type)
                        tag = self.schema.get_tag_from_type(sub_type)
                        substitute = SchemaChild(element, self.schema, self.logger, tag)
                        # The substitute inherits the cardinality from the substitution
                        substitute.put_cardinality(subelement.get_cardinality_object())
                        self.children[sub_type] = substitute
                else:
                    self.children[name] = subelement
            else:
                return
        return

    def get_schema_elements(self):
        return self.children

    def get_referenced_type(self, element: ET.ElementTree, ref: str)->str:
        namespace = element.nsmap
        prefix = ns_prefix(ref)
        name = strip_ns_prefix(ref)
        if prefix is None:
            tag = namespace[None]
            for ns in self.schema.namespace:
                if tag == self.schema.namespace[ns]:
                    prefix = ns
            typ = prefix + ':' + name
        else:
            typ = ref
        return typ

    def find_attribute_group(self, type: str): # Find attribute groups of an element
        tag = self.schema.get_tag_from_type(type)
        element = self.schema.get_element_from_tag(tag)
        groups = self.schema.get_attribute_groups()
        if element is not None:
            group = element.findall('.//{*}attributeGroup')
            for ref in group:
                name = ref.get('ref')
                if name is None:
                    name = ref.get('name')
                typ = self.get_referenced_type(ref, name)
                if typ in groups:
                    self.find_attribute(typ)
                else:
                    self.logger.error('{} has no type'.format(name))
        else:
            return

    def find_attribute(self, type: str):
        tag = self.schema.get_tag_from_type(type)
        element = self.schema.get_element_from_tag(tag)
        types = {}
        if self.has_assertions():
            assertions = self.get_assertions()
             # Get attribute names from the assertions
            for test in assertions:
                search = re.findall(r'@\w+[\b:]\w+|@\w+\b', test)
                for t in search:
                    types[t.replace('@', '')] = t
        if element is not None:
            for attrib in element.iter('{*}attribute'):
                attribute = SchemaAttribute(attrib, self.schema, self.logger)
                name = attribute.get_name()
                typedname = attribute.get_typed_name()
                if typedname in types or name in types:
                    attribute.put_choice(True)
                self.attributes[name] = attribute

    def find_all_assertions(self):
        assertions = []
        # Search my-self
        proc = self.find_assertion(self.element)
        if proc is not None:
            assertions.append(proc)
        # Search my type
        type = self.get_type()
        element = self.schema.get_element_from_type(self.schemaBase, type)
        if element is not None:
            proc = self.find_assertion(element)
            if proc is not None:
                assertions.append(proc)
        # Search parents
        for type in self.parents:
            parent = self.schema.get_element_from_type(self.schemaBase, type)
            if parent is not None:
                proc = self.find_assertion(parent)
                if proc is not None:
                    assertions.append(proc)
        return assertions

    def find_assertion(self, element: ET.Element)->str:
        test = None
        # Assertions
        asserts = element.findall('.//{*}assert', self.namespace)
        if len(asserts) > 0:
            attrib = asserts[0].attrib
            if 'test' in attrib:
                test = attrib['test']
        return test

    def get_schema_attributes(self)->list: # Returns the list of ocxSchema:Attribute schema attributes
        # Parent attributes
        for parent in reversed(self.parents):
            if parent is not None:
                self.find_attribute_group(parent)
                self.find_attribute(parent)
        # My attribute groups
        self.find_attribute_group(self.get_type())
        # My attributes
        self.find_attribute(self.get_type())
        return self.attributes


class SchemaChild(SchemaBase):
    def __init__(self, subelement: ET.Element, schema: OCXSchema, logger, tag: str = 'None'):
        super().__init__(subelement, schema, logger, tag)
        # The element has a substitution group
        if 'substitutionGroup' in subelement.attrib:
            self.substitutionGroup = subelement.attrib['substitutionGroup']
        else:
            if self.referencedElement is not None:
                attrib = self.referencedElement.attrib
                if 'substitutionGroup' in attrib:
                    self.substitutionGroup = attrib['substitutionGroup']
                else:
                    self.substitutionGroup = None
            else:
                self.substitutionGroup = None

    def is_substitutiongroup(self) -> bool:
        return self.substitutionGroup != None

    def substitutiongroup(self) -> str:
        return self.substitutionGroup


class SchemaAttribute(SchemaBase):
    def __init__(self, attribute: ET.Element, schema: OCXSchema, logger, tag: str='None'):
        super().__init__(attribute, schema, logger, tag)


    def get_default(self):
        return self.cardinalityObject.default

    def get_fixed(self):
        return self.cardinalityObject.fixed


class SchemaEnumerator:
    def __init__(self, type, attr):
        self.type = type
        self.name = strip_ns_prefix(type)
        self.enum = attr
        self.annotation = ''
        self.values = {} # Dict of enums (name: value)
        enumerations = attr.findall('.//{*}enumeration')
        for enum in enumerations:
            value = enum.get('value')
            annotation = enum.findall('.//{*}annotation')
            if len(annotation)> 0:
                text =  element_annotation(annotation[0])  # Enum annotation
            else:
                text = ''
            self.values[value] = text

    def get_annotation(self)->str:
        return self.annotation

    def get_values(self):
        return self.values

    def get_name(self)->str:
        return self.name

    def get_type(self)->str:
        return self.type


class SchemaType:
    def __init__(self, element: ET.Element, schema: OCXSchema):
        self.schema = schema
        self.element = element
        self.name = ''
        self.isReference = False
        self.referencedElement = None
        self.schemaBase = element.base
        self.namespace = element.nsmap
        self.schemaType = self.find_type(element)

    # Parses the schema and returns the element type
    def find_type(self, element: ET.Element)->str:
        attributes = element.attrib
        schemaType = None
        if 'ref' in attributes:
            ref = attributes['ref']
            # Use local namespace for references
            self.referencedElement = self.schema.get_element_from_type(self.schemaBase, ref)
            if self.referencedElement is not None:
                attributes = self.referencedElement.attrib
                element = self.referencedElement
                self.isReference = True
            else:
                schemaType = ref
        if 'name' in attributes:
            self.name = attributes['name']
        if 'type' in attributes:
              schemaType = attributes['type']
        if 'base' in attributes:
            schemaType = attributes['base']
        # The element may have complexContent
        base = element.findall('.//{*}*[@base]')
        if len(base) > 0:
            schemaType = base[0].get('base')
        # the element may be a simpleType
        itemtype = element.findall('.//{*}*[@itemType]')
        if len(itemtype) > 0:
            schemaType = itemtype[0].get('itemType')
        if schemaType is not None:
            # Add any missing prefix
            if ns_prefix(schemaType) is None:
                base = element.base
                if base in self.schema.schemaBase:
                    prefix = self.schema.schemaBase[base]
                    schemaType = prefix + ':' + schemaType
        else:
            schemaType = 'untyped'
        return schemaType

    def get_type(self):
        return self.schemaType

    def get_name(self):
        return self.name

    def is_reference(self):
        return self.isReference

    def get_referenced_element(self):
        return self.referencedElement

    def get_tag_from_type(self, type:str)->str:
        return self.schema.get_tag_from_type(type)


# Parser class for extracting element documentation from the schema
class Annotation:
    def __init__(self, type: str, element: ET.Element, reference:ET.Element, logger):
        self.element = element
        self.type = type
        self.logger = logger
        self.annotation = self.find_annotation(reference)


    def find_annotation(self, reference: ET.Element)->str:
        text = ''
        annotation = []
        # Search first for the local annotation
        annotation = self.element.findall('.//{*}annotation')
        if len(annotation) > 0:
            description = ''
            for text in ET.ElementTextIterator(annotation[0], with_tail=False):
                description = description + text
            text = re.sub('[\n\t\r]', '', description)
        else:
            # Search the reference
            if reference is not None:
                annotation = reference.findall('.//{*}annotation')
                if len(annotation) > 0:
                    description = ''
                    for text in ET.ElementTextIterator(annotation[0], with_tail=False):
                        description = description + text
                    text = re.sub('[\n\t\r]', '', description)
            else:
                self.logger.debug('{} has no documentation'.format(self.type))
        return text

# Implementation of the OCX xsd classes (not to be confused with the ET.Element etree class)
# The base class
class ElementBase:
    def __init__(self, element: ET.Element, schema: OCXSchema):
        self.element = element  # The ET.Element node
        self.schema = schema # The xsd schema
        type = SchemaType(element, schema)
        self.type = type.get_type()
        self.name = type.get_name()
        self.prefix = ns_prefix(self.type)
        self.logger = self.schema.logger
        self.substitutionGroup = None
        self.schemaBase = element.base
        # The element is a choice among one or more types
        self.choice = False
      # The element is abstract
        if 'abstract' in element.attrib:
            self.abstract = True
        else:
            self.abstract = False
        # The element has a substitution group
        if 'substitutionGroup' in element.attrib:
            self.substitutionGroup = element.attrib['substitutionGroup']
        else:
            self.substitutionGroup = None
        # Element documentation
        self.annotation = self.find_annotation()

    def get_type(self):
        return self.type

    def get_xsd_tag(self)->str:
        return self.xsdType

    def get_xsd_prefix(self)->str:
        return self.element.prefix

    def get_element_attrib(self)->dict:
        return self.element.attrib # The ET.Element attributes

    def is_reference(self)->bool:
        return self.reference

    def get_name(self) -> str:
        return self.name

    def is_abstract(self)->bool:
        return self.abstract

    def is_substitutiongroup(self)->bool:
        return self.substitutionGroup != None

    def substitutiongroup(self)->str:
        return self.substitutionGroup


    # Used to override the element documentation using any locally declared annotation
    def put_annotation(self, element: ET.Element):
        text = ''
        description = ''
        for text in ET.ElementTextIterator(element, with_tail=False):
            description = description + text
        text = re.sub('[\n\t\r]', '', description) # Strip off special characters
        self.annotation = text

    def get_annotation(self)->str:
        return self.annotation

    # The type is choice type  (The schema requires zero or one to many of this type)
    def is_choice(self):
        return self.choice

    def find_annotation(self)->str:
        text = ''
        annotation = []
        annotation = self.element.findall('.//{*}annotation')
        if len(annotation) > 0:
            description = ''
            for text in ET.ElementTextIterator(annotation[0], with_tail=False):
                description = description + text
            text = re.sub('[\n\t\r]', '', description)
        else:
            self.logger.warning('{} has no documentation'.format(self.element.tag))
        return text


class OCXEtree:
    def __init__(self, ocx, schema: OCXSchema, logger):
        self.ocxFile = ocx  # The 3Docx xml file
        self.schema = schema # The OCX schema version
        self.namespace = schema.get_name_space()
        self.parsed = False  # True if parsed without any syntax errors
        self.version = 'None'
        self.logger = logger
        self.root = None
        self.tree = None
        self.header = None

    def parse_xml(self)->bool:
        self.logger.info(MsgLine('Parsing xml file', self.ocxFile).msg())
        try:
            self.tree = ET.parse(self.ocxFile)  # Create the DOM tree
            self.parsed = True
            self.logger.info('{} syntax is OK'.format(self.ocxFile))
        # Catch syntax errors from the pxml parsing
        except ET.XMLSyntaxError as error:
            self.logger.error('{} has syntax errors: {}'.format(self.ocxFile,error))
            self.parsed = False
        return self.parsed

    def get_root(self):
        if self.is_parsed():
            self.root = self.tree.getroot()
        return self.root

    def get_schema_version(self):
        if self.is_parsed():
            root = self.get_root()
            attributes = root.attrib
            #.iter('.//{*}ocxXML', self.ocxXsd.namespace):
            self.version = attributes['schemaVersion']
        return self.version

    def get_named_children(self, object: ET.Element, name: str, namespace: dict, prefix='{*}')->list:
        objects = []
        if self.is_parsed():
            # Default namespace is to use wildcard {*}
            objects = object.findall('.//' + prefix + name, namespace)
        return objects

    def get_named_objetcs(self, name: str, namespace: dict, prefix='{*}')->list:
        objects = []
        if self.is_parsed():
            # Default namespace is to use wildcard {*}
            objects = self.root.findall('.//' + prefix + name, namespace)
        return objects

    def get_all_objetcs_with_attribute(self, attrib: str, namespace: dict, prefix='{*}')->list:
        objects = []
        if self.is_parsed():
            # Default namespace is to use wildcard {*}
            find = './/' + prefix + '*[@'+attrib+']'
            objects = self.root.findall(find, namespace)
        return objects

    def get_all_children_with_attribute(self, object: ET.Element, attrib: str, namespace: dict, prefix='{*}')->list:
        objects = []
        if self.is_parsed():
            # Default namespace is to use wildcard {*}
            find = './/' + prefix + '*[@'+attrib+']'
            objects = object.findall(find, namespace)
        return objects

    def get_children_with_attribute(self, object: ET.Element, attrib: str, namespace: dict, prefix='{*}')->list:
        objects = []
        if self.is_parsed():
            # Iterate only over the children
            for child in object.iterchildren(tag=ET.Element):
                if attrib in child.attrib:
                    objects.append(child)
        return objects


    def get_attribute_value(self, object: ET.Element, attrib: str):
        value = object.get(attrib)
        return value

    def get_file_name(self):
        return self.ocxFile

    def is_parsed(self):
        return self.parsed

    # Import the OCX XML file
    def import_model(self, namespace: dict)->bool:
        ok = True
        # Parse the model
        if self.parse_xml():
            # retrieve the namespace
            ocxnamespace = self.get_root().nsmap # The namespaces defined in the 3Docx
            # Add new namespace entries
            for key in ocxnamespace:
                namespace[key] = ocxnamespace[key]
            version = self.get_schema_version()
            self.logger.info('')
            self.logger.info('{}'.format(DELIMITER))
            self.logger.info('{}'.format('3Docx summary'))
            self.logger.info('{}'.format(DELIMITER))
            # print ocx version and get the root
            self.logger.info(MsgLine('3Docx file name', self.ocxFile).msg())
            self.logger.info(MsgLine('Referenced OCX Schema version', version).msg())
            # get the ocxXML header info
            search = self.root.findall('.//ocx:Header', self.namespace)
            if len(search)>0:
                self.header = Header(search[0])
                self.logger.info(MsgLine('Model name', self.header.name).msg())
                if self.header.hasHeader():
                    self.logger.info(MsgLine('Model timestamp', self.header.ts).msg())
                    self.logger.info(MsgLine('Author', self.header.author).msg())
                    self.logger.info(MsgLine('Originating system', self.header.system).msg())
                    self.logger.info(MsgLine('Application version', self.header.applicationVersion).msg())
                    self.logger.info(MsgLine('Documentation', self.header.documentation).msg())
            if version != self.schema.get_version():
                msg = ('The supported version {} of the 3Docx export is different from the referenced schema version: {}' \
                      .format(version, self.schema.get_version()))
                self.logger.warning(msg)
            return ok
        else:
            return False