[![3DOCX.org logo](./static/logo.png)](https://3docx.org)
# ocx-validator

[![Build, Test and Lint Action](https://github.com/OCXStandard/ocx-validator/workflows/Build,%20Test,%20Lint/badge.svg)](https://github.com/OCXStandard/ocx-validator/workflows/Build,%20Test,%20Lint/badge.svg)
[![Push Action](https://github.com/https://github.com/OCXStandard/ocx-validator/workflows/Push/badge.svg)](https://github.com/https://github.com/OCXStandard/ocx-validator/workflows/Push/badge.svg)
[![Test Coverage](https://api.codeclimate.com/v1/badges/cd8ed3425a57a2c3dde5/test_coverage)](https://codeclimate.com/github/OCXStandard/ocx-validator/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/cd8ed3425a57a2c3dde5/maintainability)](https://codeclimate.com/github/OCXStandard/ocx-validator/maintainability)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=OCXStandard_ocx_validator&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=OCXStandard_ocx_validator)

## Usage
The `ocx-validator` package is a Python script to validate 3Docx models against a version of the [OCX standard](https://3docx.org).
The script can be executed from the command line:

```console
~ $ python -m ocx-validator [3docx model] [options]
```
## Package Maintenance

### Building using poetry

### Running

#### Using Python Interpreter
```shell
~ $ make run
```


### Testing

Test are ran every time you build _dev_ or _prod_. You can also run tests using:

```console
~ $ make test
```

### Cleaning

Clean _Pytest_ and coverage cache/files:

```console
~ $ make clean
```

### Setting Up Sonar Cloud for Quality gate
- Navigate to <https://sonarcloud.io/projects>
- Click _plus_ in top right corner -> analyze new project
- Setup with _other CI tool_ -> _other_ -> _Linux_
- Copy `-Dsonar.projectKey=` and `-Dsonar.organization=`
    - These 2 values go to `sonar-project.properties` file
- Click pencil at bottom of `sonar-scanner` command
- Generate token and save it
- Go to repo -> _Settings_ tab -> _Secrets_ -> _Add a new secret_
    - name: `SONAR_TOKEN`
    - value: _Previously copied token_
    
### Creating Secret Tokens
Token is needed for example for _GitHub Package Registry_. To create one:

- Go to _Settings_ tab
- Click _Secrets_
- Click _Add a new secret_
    - _Name_: _name that will be accessible in GitHub Actions as `secrets.NAME`_
    - _Value_: _value_

## Change log
| Date | Version | Reason
|------|---------| -----
|2020.11.30| 1.3.0   |Amended ".validation" to the log file name to distinguish the output from other log files.
|2020.11.30| 1.2.0   |Fixed an error when asserting "unitsml:Unit" types which are non-dimensional. Sub-element "RootUnits" are not required for non-dimensional unit types.
|2020.11.20| 1.1.0   |Fixed an error when asserting the presence of "localRef" and "GUIDRef" for types of "ocx:EntityRefBase". Presence of either one is mandatory, but not both
|2020.11.10| 1.0.0   |First version issued


## Resources
- Project blueprint based on  [Ultimate Setup for Your Next Python Project by Martin Heinz](https://towardsdatascience.com/ultimate-setup-for-your-next-python-project-179bda8a7c2c)
- The official [3Docx.org](https://3docx.org) site.
