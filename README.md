# ocx-validator
A docker XML and schematron validator for OCX models.

## Changelog

[Changelog](CHANGELOG.md)

## Building the validator docker image
We use an XML validator provided by Interoperability Europe under the EUROPEAN UNION PUBLIC LICENCE v. 1.2, see the [LICENSE](License.txt]).
The ocx-validator docker image is based on the [official isaitb dockerhub image](https://hub.docker.com/r/isaitb/xml-validator): using the [Dockerfile](Dockerfile):

The docker image is built locally using the command:
```
  docker build . --tag 3docx/validator:latest
```
where `3docx/validator` is the image name and `latest`the image tag. The command will use the configuration in the local [Dockerfile](Dockerfile) when building the image.

### The Dockerfile

The  local `Dockerfile` is used to configure the image layers:
```
FROM isaitb/xml-validator:latest
COPY ./resources /validator/resources/
ENV validator.resourceRoot /validator/resources/
ENV validator.baseSoapEndpointUrl localhost:8080
ENV validator.identifier "3.0.0b6"
ENV validator.about "<a href="https://3docx.org">&copy;3Docx.org</a> The service is provided under the EUROPEAN UNION PUBLIC LICENCE v1.2"
# Servlet Spring Boot config: Setting unlimited file upload size and request size
ENV spring.servlet.multipart.max-file-size -1
ENV spring.servlet.multipart.max-request-size -1
# ENV spring.web.resources.static-locations="classpath:/webjars/,classpath:/css,classpath:/static , classpath:/public"
ENV logging.level.org.springframework=DEBUG
ENV debug=true
ENV validator.cleanupPollingRate=600000
```
1. The `FROM` command will pull the official isaitb image.
2. the `COPY` command copies the local `resources` folder content into the container.
3. The `ENV` commands provides values to the container environment variables `validator`, see [Validator configuration properties](https://www.itb.ec.europa.eu/docs/guides/latest/validatingXML/index.html#validator-configuration-properties)
4. The `ENV` commands for the `spring.servlet` variables are described in [Spring Boot configuration options](https://docs.spring.io/spring-boot/docs/current/reference/html/application-properties.html)

## The validator `resources`

The content of the `resources` folder is copied to the container image and provides the validator resources. The `resources` folder has the following structure:
```
.                       
├───resources             
    ├───ocx
    └───schematron
```
where the `ocx` sub-folder contains the OCX schema versions while the `schemtron` sub-folder can contain optional [Schematron](https://www.schematron.com/) rules.
The content of the `ocx` sub-folder can contain any number of schema versions as sub-folders:
```commandline
├───ocx
    ├───v2.8.6
    │   └───xsd
    ├───vb3.0.0b4
    │   └───xsd
    └───v3.0.0rc1
        └───xsd
```
Each schema version has an `xsd` sub-folder which contains the full OCX schema including any referenced schemas. This enables the validator to validate 3Docx models using only local resources without relying on an internet connection for url lookup.

## Validator configuration
The isaitbl image has a wide set of configuration options. The `ocx` folder must contain a file `ocx.properties` providing the validation specific properties:
```commandline
# The different types of validation to support. These values are reflected in other properties.
validator.report.name = OCX Validator
validator.report.validationServiceName = ocx-validator
validator.report.validationServiceVersion = 3.0.0b6
validator.type = ocx
validator.typeOptions.ocx = v2.8.6, v3.0.0b4, v3.0.0rc1
# Labels to describe the defined types.
validator.typeLabel.ocx = OCX XSD validation
# Validation artefacts (XML Schema and Schematron) for this domain.
# Version 2.8.6
validator.schemaFile.ocx.v2.8.6 =   v2.8.6/xsd/OCX_Schema.xsd
# Version 3.0.0b4
validator.schemaFile.ocx.v3.0.0b4 = v3.0.0b4/xsd/OCX_Schema.xsd
# Version 3.0.0rc2
validator.schemaFile.ocx.v3.0.0rc2 = v3.0.0rc2/xsd/OCX_Schema.xsd
## The title to display for the validator's user interface.
validator.uploadTitle = OCX Validator
validator.validator.remoteArtefactLoadErrors = fail
validator.javascriptExtension=$(document).ready(function() { $(".validatorReload").off().on("click", function() { window.location.href="upload"; });});
validator.bannerHtml=<div><div style="display: table;"><div style="display: table-row;"><div class="validatorReload" style="display: table-cell; cursor: pointer;"><h1>OCX validator</h1><p style="text-align:right"> <img src="https://3docx.org/fileadmin/user_upload/Images/OCX-IF_Logo.png"> </p></div></div><div style="display: table-row;"><div style="display: table-cell; padding-top: 20px;"><p> This service is provided by the OCX Interoperability Forum organised by the <a href="https://3docx.org"> OCX Consortium</a> . The service allows you to validate <strong>3Docx XML</strong>models against published and working draft versions of the <a href="https://3docx.org">Open Class 3D Exchange (OCX) standard</a> (to validate structure) and <a href="http://schematron.com/">Schematron</a> (to validate content). The service is based on the<a href="https://github.com/ISAITB/xml-validator"> open source XML validator</a> provided by the Interoperability Test Bed, a conformance testing service offered by the European Commission's DG DIGIT project.<p> Click <a href="https://ocxwiki.3docx.org">here</a> for a detailed reference of the OCX published standard.</p></div></div></div><hr></div>
validator.reportTitle=OCX Validation Report

```
The property file provides validation specific properties to the container explained in the [Validator configuration properties](https://www.itb.ec.europa.eu/docs/guides/latest/validatingXML/index.html#validator-configuration-properties).
* The property `vallidator.type` lists the available validation options (typically the schema versions). In the above case 3 schema versions are provided.
* The property `vallidator.SchemaFile` links the validation type with the provided schema in the `resource`folder.

## Running the ocx-validator
Running the ``validator`` in a container:

```
  docker run -d --name validator -p 8080:8080  3docx/validator:latest
```
where `validator`is the container name and `3docx/validator`is the image built in the previous command and the `tag`is the image version that will be pulled.


## Setting up XML validation, Interoperability Test Bed Guidelines
For full details on how to set up, configure and manage a validator built using the isaitb image please refer to the Interoperability Europe Test Bed's 
[Interoperability Test Bed Guideline: Setting up XML validation](https://www.itb.ec.europa.eu/docs/guides/latest/validatingXML/index.html).

The isaitb validator on GitHub: [GitHub](https://github.com/ISAITB/xml-validator)
