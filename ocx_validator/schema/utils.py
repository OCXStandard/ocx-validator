#  Copyright (c) 2022 3Docx.org. See the LICENSE file.


import yaml
import logging
import colorlog
import re

DELIMITER = 52*'-'
SECTION = 52*'='
INDENT = 10*' '
INDENT_SMALL = 2*' '
RIGHT_PAD = ':<45'


def read_yaml(file_path):
    """ Safely load the yaml configuration
        :param file_path: The path to the yaml config file
        :return: A dict of config entries
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def init_logger(app_name, multiple: bool, loglevel='INFO') -> logging.Logger:
    if loglevel == 'DEBUG':
        log_format = (
            '%(asctime)s: '
            '%(name)s - '
            '%(funcName)30s - '
            '%(levelname)8s: '
            '%(message)s'
        )
    else:
        log_format = (
            '%(asctime)s: '
            # '%(name)s - '
            #'%(funcName)30s - '
            '%(levelname)8s: '
            '%(message)s'
        )

    fhlog_format = (
        # '%(asctime)s: '#
        # '%(name)s - '
        #'%(funcName)30s - '
        '%(levelname)8s: '
        '%(message)s'
    )

    bold_seq = '\033[1m'
    colorlog_format = (
        f'{bold_seq} '
        '%(log_color)s '
        f'{log_format}'
    )
    colorlog.basicConfig(format=colorlog_format)
    logger = logging.getLogger(app_name)

    # Set the logging level
    if loglevel == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif loglevel == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif loglevel == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Output full log
    fh = logging.FileHandler(app_name+'.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fhlog_format)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Output separate logs
    if multiple:

        # Output warning log
        fh = logging.FileHandler(app_name+'.warning.log')
        fh.setLevel(logging.WARNING)
        formatter = logging.Formatter(fhlog_format)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Output error log
        fh = logging.FileHandler(app_name+'.error.log')
        fh.setLevel(logging.ERROR)
        formatter = logging.Formatter(fhlog_format)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def parse_boolean(b):
    return b == 'True' or b == 'true'


def ns_prefix(element:str)->str:
    i = element.find(':')
    if not i == -1:
        element = element[0: i]
        return element
    else:
        return None


def strip_ns_prefix(element:str)->str:
    i = element.find(':')
    if not i == -1:
        element = element[i + 1:len(element)]
    return element


def strip_namespace_tag(element:str)->str:
    i = element.find('}')
    if not i == -1:
        element = element[i + 1:len(element)]
    return element

def find_replace_multi(string, dictionary):
    for item in dictionary.keys():
        # sub item for item's paired value in string
        string = re.sub(item, dictionary[item], string)
    return string


class MsgLine:
    def __init__(self, msg: str, parameter, format: str = ''):
        formatted = '{'+RIGHT_PAD+'}: ' + '{' + format + '}'
        self.message = formatted.format(msg,parameter)

    def msg(self):
        return self.message


class MsgSection:
    def __init__(self, msg: str, logger):
        self.message = msg
        self.logger = logger

    def log(self):
        self.logger.info(' ') # A blank line above each section
        self.logger.info(self.message)
        self.logger.info(DELIMITER)


class MsgHeader:
    def __init__(self, msg: str, logger):
        self.message = msg
        self.logger = logger

    def log(self):
        self.logger.info(SECTION)
        self.logger.info(self.message)
        self.logger.info(SECTION)

