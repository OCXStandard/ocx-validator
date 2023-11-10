# ocx-validator
A docker XML and schematron validator for OCX models.


## Building the validator docker image
We use an XML validator provided by Interoperability Europe under the EUROPEAN UNION PUBLIC LICENCE v. 1.2, see the [LICENSE](License.txt]).
The ocx-validator docker image is based on the [official isaitb dockerhub image](https://hub.docker.com/r/isaitb/xml-validator): using the [Dockerfile](Dockerfile):

```
  docker build . --tag validator
  docker tag validator 3docx/validator
```
 
## Running the ocx-validator
Running the ``validator`` in a container:


```
  docker run -d --name validator -p 8080:8080  3docx/validator
```
   
The [Spring Boot configuration options](https://docs.spring.io/spring-boot/docs/current/reference/html/application-properties.html)

### Documentation
For full details on how to setup, configure and manage a validator built using the isaitb image please refer to the Interoperability Europe Test Bed's 
[XML validation guide](https://www.itb.ec.europa.eu/docs/guides/latest/validatingXML/index.html)


### Setting up XML validation

[Interoperability Test Bed Guideline: Setting up XML validation](https://www.itb.ec.europa.eu/docs/guides/latest/validatingXML/index.html)

[GitHub](https://github.com/ISAITB/xml-validator)

### Migrating the development test bed to production

[Interoperability Test Bed Guideline: Export and import your data](https://www.itb.ec.europa.eu/docs/itb-ta/latest/exportimport/index.html)
