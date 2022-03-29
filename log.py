import logging
import logging.handlers as handlers
import os
from singleton import Singleton


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


class MyLogger(Singleton):
    def __init__(self):
        super().__init__()
        if self._initialized:
            log_format = "%(asctime)s [%(levelname)s] [%(name)s]: %(filename)s(%(funcName)s:%(lineno)s) >> %(message)s"
            log_filemode = "a"  # w: overwrite; a: append

            # setup stdout logger
            self.stdout_handler = logging.StreamHandler()
            self.stdout_handler.setLevel(logging.DEBUG)
            self.stdout_handler.setFormatter(CustomFormatter(log_format))

            path = os.path.dirname(os.path.abspath(__file__))
            # setup normal logger file
            self.file_handler = handlers.TimedRotatingFileHandler(os.path.join(path, 'normal.log'), when='midnight',
                                                                  encoding='utf8')
            self.file_handler.namer = lambda name: name.replace(".log", "") + ".log"
            self.file_handler.setLevel(logging.DEBUG)
            self.file_handler.setFormatter(CustomFormatter(log_format))

            # setup error logger file
            self.error_file_handler = handlers.RotatingFileHandler(os.path.join(path, 'error.log'),
                                                                   maxBytes=1024 * 1024 * 5,
                                                                   encoding='utf8',
                                                                   backupCount=3)
            self.error_file_handler.setLevel(logging.ERROR)
            self.error_file_handler.setFormatter(CustomFormatter(log_format))

            logging.basicConfig(format=log_format, filemode=log_filemode, level=logging.DEBUG, force=True)
            self.logger = self.setup_logger('root')

    def get_root_logger(self):
        return self.logger

    def setup_logger(self, name):
        logger = logging.getLogger(name)

        # print log messages to console
        logger.addHandler(self.stdout_handler)

        # write log messages to file

        logger.addHandler(self.file_handler)

        # write error log messages to file
        logger.addHandler(self.error_file_handler)

        logger.propagate = False
        return logger


log = MyLogger()
