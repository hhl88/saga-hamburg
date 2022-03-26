import logging


class ColorCodes:
    grey = "\x1b[38;21m"
    green = "\x1b[1;32m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    purple = "\x1b[1;35m"
    reset = "\x1b[0m"


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: ColorCodes.grey + self.fmt + ColorCodes.reset,
            logging.INFO: ColorCodes.blue + self.fmt + ColorCodes.reset,
            logging.WARNING: ColorCodes.yellow + self.fmt + ColorCodes.reset,
            logging.ERROR: ColorCodes.red + self.fmt + ColorCodes.reset,
            logging.CRITICAL: ColorCodes.bold_red + self.fmt + ColorCodes.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name, log_file_path: str = None):
    # logger settings
    log_file_max_size = 1024 * 1024 * 20  # megabytes
    log_num_backups = 3
    log_format = "%(asctime)s [%(levelname)s]: %(filename)s(%(funcName)s:%(lineno)s) >> %(message)s"
    log_filemode = "w"  # w: overwrite; a: append

    # setup logger

    if log_file_path is not None:
        logging.basicConfig(filename=log_file_path, format=log_format, filemode=log_filemode, level=logging.DEBUG)
        rotate_file = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=log_file_max_size, backupCount=log_num_backups
        )
    else:
        logging.basicConfig(format=log_format, filemode=log_filemode, level=logging.DEBUG)

    logger = logging.getLogger(name)

    if log_file_path is not None and rotate_file is not None:
        logger.addHandler(rotate_file)

    # print log messages to console
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(CustomFormatter(log_format))
    logger.addHandler(stdout_handler)
    logger.propagate = False
    return logger
