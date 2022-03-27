import logging
import logging.handlers as handlers

import datetime
import os


class ColorCodes:
    GREY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    WHITE = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = "\033[0m"
    BOLD = '\033[1m'


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: ColorCodes.BOLD + self.fmt + ColorCodes.RESET,
            logging.INFO: ColorCodes.GREEN + self.fmt + ColorCodes.RESET,
            logging.WARNING: ColorCodes.YELLOW + self.fmt + ColorCodes.RESET,
            logging.ERROR: ColorCodes.RED + self.fmt + ColorCodes.RESET,
            logging.CRITICAL: ColorCodes.RED + ColorCodes.BOLD + self.fmt + ColorCodes.RESET
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name, log_file_path: str = None, log_all_to_file: bool = True):
    global file_handler
    global error_file_handler

    # logger settings
    log_format = "%(asctime)s [%(levelname)s]: %(filename)s(%(funcName)s:%(lineno)s) >> %(message)s"
    log_filemode = "a"  # w: overwrite; a: append
    # setup logger

    logging.basicConfig(format=log_format, filemode=log_filemode, level=logging.DEBUG)

    if log_file_path is not None:
        # file_handler = logging.FileHandler('{0}_{1}.log'.format(log_file_path, today.strftime('%Y_%m_%d')))
        file_handler = handlers.TimedRotatingFileHandler(log_file_path, when='W0')

    elif log_all_to_file:
        path = os.path.dirname(os.path.abspath(__file__))
        # file_handler = logging.FileHandler(os.path.join(path, 'normal.log'))
        file_handler = handlers.TimedRotatingFileHandler(os.path.join(path, 'normal.log'), when='W0')
        error_file_handler = handlers.RotatingFileHandler(os.path.join(path, 'error.log'), maxBytes=1024 * 1024 * 5,
                                                          backupCount=3)

    logger = logging.getLogger(name)

    # print log messages to console
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(CustomFormatter(log_format))
    logger.addHandler(stdout_handler)

    # write log messages to file
    if file_handler is not None:
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(CustomFormatter(log_format))
        logger.addHandler(file_handler)

    # write error log messages to file
    if error_file_handler is not None:
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(CustomFormatter(log_format))
        logger.addHandler(error_file_handler)

    logger.propagate = False
    return logger
