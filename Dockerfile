FROM isaitb/xml-validator:latest
COPY ./resources /validator/resources/
ENV validator.resourceRoot /validator/resources/
# Servlet Spring Boot config: Setting unlimited file upload size and request size
ENV spring.servlet.multipart.max-file-size -1
ENV spring.servlet.multipart.max-request-size -1