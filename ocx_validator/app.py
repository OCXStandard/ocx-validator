#  Copyright (c) 2022. 3Docx.org, see the LICENSE.

import sys, time, datetime
from pathlib import PurePath
import click
from tabulate import tabulate
from ocx_validator.schema.utils import init_logger, MsgLine, DELIMITER
from ocx_validator.schema.validator import OCXValidator
from ocx_validator.schema.schema import OCXSchema

VALIDATION_APPVERSION = '1.3'  # ToDo: Rememeber to change version number for a new deployment
REASON_FOR_CHANGE = [
    {'Date': '2021.01.27',
     'Version': '1.3',
     'Reason': 'Amended ".validation" to the log file name to distinguish the output from other log files.'},
    {'Date': '2020.11.30',
     'Version': '1.2',
     'Reason': 'Fixed an error when asserting "unitsml:Unit" types which are non-dimensional. '
               'Sub-element "RootUnits" are not required for non-dimensional unit types.'},
    {'Date': '2020.11.20',
     'Version': '1.1',
     'Reason': 'Fixed an error when asserting the presence of "localRef" and "GUIDRef" for types of "ocx:EntityRefBase".'
               ' Presence of either one is mandatory, but not both.'},
    {'Date': '2020.11.10',
     'Version': '1.0', 'Reason': 'First version issued'}
]
APP_SIGNATURE = 'validation'

COPYRIGHT = '(c) DNV GL AS. All rights reserved'
NAMESPACE_PREFIX = 'ocx'
NAMESPACE = False
LOGLEVEL = 'INFO'
SCHEMA_SUMMARY = False


@click.command()
@click.argument('model', type=click.Path(exists=True))  # The 3Docx xml file to be validated

@click.option('-sv', '--skip_validation', is_flag=True,
              help='Use this flag to skip any model validation.')
@click.option('-v', '--validate', type=click.Choice(['Lazy', 'Strict', 'Specific'],
                                                    case_sensitive=False), default='Lazy',
              help='The element instances in the 3Docx file to be validated:'
                   'Lazy: Validate one instance of every element. '
                   'This is a quick validation and most schema errors are captured. '
                   'Strict: Every instance of an element is validated. (Time-consuming for large models) '
                   'Specific: Named objects. All instances of the named element will be validated.'
                   'The objects to validate are specified using the option --element. ')
@click.option('-o', '--element', multiple=True,
              help='The element to be validated on the form "name". Repeat the option for multiple objects')
@click.option('-ve', '--validate_enumerations', is_flag=True,
              help='Use this flag to validate whether enumerations are according to the schema values. ')
@click.option('-ps', '--print_source', is_flag=True,
              help='Use this flag to output the xml source of a non-valid element to the error log')
@click.option('-sl', '--separate_logfiles', is_flag=True,
              help='Use this flag to output separate logfiles for errors and warnings which '
                   'is convenient for larege models. '
                   'The default is to output one logfile containing all logs ')
@click.option('-s', '--schema', type=click.Path(exists=True), default='schema_versions/OCX_Schema_V286.xsd',
              # The referenced 3Docx schema version
              help='The location of the 3docx XSD schema. The default location is "schema_versions/"')
@click.option('-r', '--reason_for_change', is_flag=True,
              help='This flag will print the validate3Docx version history and reasons for change.')
@click.option('-sc', '--schema_changes', type=click.Choice(['None', 'Current', 'All'], case_sensitive=False),
              default='None',
              help='Print the schema changes:'
                   'None: (Default) no output of schema changes.'
                   'Current Outputs the change history for the current schema version.'
                   'All: Output the complete version history.')
def validate3Docx(model, schema, validate, element, validate_enumerations, print_source,
                  skip_validation, schema_changes, separate_logfiles, reason_for_change):
    #    click.echo('ocx_validation will do a validation of the 3Docx file against the input schemas')
    """Validate a 3Docx xml model"""
    start = time.time()
    if reason_for_change is True:
        print(DELIMITER)
        print('validate3Docx version history')
        print(f'Current version: {VALIDATION_APPVERSION}')
        print(DELIMITER)
        print(tabulate(REASON_FOR_CHANGE, headers='keys'))
        sys.exit()  # Stop execution
    # __main__ execution
    if model is not None:
        modelpath = PurePath(model)
        filename = modelpath.stem + '.' + APP_SIGNATURE
    else:
        sys.exit()
    # Set up the logger
    logger = init_logger(filename, separate_logfiles, LOGLEVEL)
    logger.debug('Starting validation of {} with options {}'.format(schema,
                                                                    [{'--loglevel': LOGLEVEL, '--validate': validate,
                                                                      '--validate_enumertaions': validate_enumerations,
                                                                      '--skip_validation': skip_validation,
                                                                      '--schema_changes': schema_changes,
                                                                      '--schema_summary': SCHEMA_SUMMARY}]))

    logger.info(DELIMITER)
    logger.info(' Open Class 3D Exchange (OCX) conformance validation')
    logger.info(' Version: {}'.format(VALIDATION_APPVERSION))
    logger.info(' {}'.format(COPYRIGHT))
    now = datetime.datetime.now()
    logger.info(now.strftime(" %Y.%m.%d %H:%M:%S"))
    logger.info(DELIMITER)

    # Application flow
    # Read schemas
    ocx_schema = OCXSchema(NAMESPACE_PREFIX, logger)
    all_elements = False
    if schema_changes != 'None':
        if schema_changes == 'Current':
            all_elements = False
        else:
            all_elements = True
    if ocx_schema.read_schema(schema, all_elements):  # The schemas was parsed successfully
        # Output the schema summary
        if SCHEMA_SUMMARY:
            ocx_schema.schema_info()
        # Print the schema version changes
        if schema_changes != 'None':
            changes = ocx_schema.get_schema_changes()
            print(DELIMITER)
            print('Schema change history')
            print(DELIMITER)
            print(tabulate(changes, headers='keys'))
        # Initiate the validator
        if model is not None and skip_validation is not True:
            validator = OCXValidator(model, ocx_schema, validate_enumerations, print_source)
            # Parse the model
            n = 0
            if skip_validation is not True:
                logger.info('')
                logger.info('Reading model ...')
                if validator.import_model():
                    # Set up the validator
                    logger.info(DELIMITER)
                    logger.info('MODEL VALIDATION')
                    logger.info(DELIMITER)
                    # Validate element name spelling
                    n = validator.validate_names()
                    if n == 0:
                        logger.info(MsgLine('Schema names', 'OK').msg())
                    # Validate model objects
                    if validate == 'Lazy' or validate == 'lazy':
                        validate_all = False
                        element = []  # Override option -element
                        logger.info('{}'.format('Validating only unique objects:'))
                    elif validate == 'Specific' or validate == 'specific':
                        validate_all = True
                        logger.info(MsgLine('Validating named objects', element).msg())
                    else:
                        validate_all = True
                        element = []
                        logger.info(MsgLine('Validating all element instances', '').msg())

                    n = validator.validate_model_objects(validate_all, element)
                else:
                    n = 1
                if n == 0:
                    logger.info(DELIMITER)
                    logger.info(MsgLine('Number of entities validated', validator.validated()).msg())
                    logger.info(MsgLine('Validation completed', 'OK').msg())
                    end = time.time()
                    elapsed = end - start
                    logger.info('Elapsed time:         {}'.format(datetime.timedelta(seconds=elapsed)))
                    logger.info(DELIMITER)
                else:
                    logger.error(DELIMITER)
                    logger.error(MsgLine('Number of entities validated', validator.validated()).msg())
                    logger.error(MsgLine('Validation completed with ', '{} error(s)'.format(n)).msg())
                    end = time.time()
                    elapsed = end - start
                    logger.error('Elapsed time:        {}'.format(datetime.timedelta(seconds=elapsed)))
                    logger.error(DELIMITER)


if __name__ == "__main__":
    validate3Docx()
