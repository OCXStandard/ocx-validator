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

