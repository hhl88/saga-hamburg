import logging


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
            logging.DEBUG: ColorCodes.WHITE + self.fmt + ColorCodes.RESET,
            logging.INFO: ColorCodes.GREEN + self.fmt + ColorCodes.RESET,
            logging.WARNING: ColorCodes.YELLOW + self.fmt + ColorCodes.RESET,
            logging.ERROR: ColorCodes.RED + self.fmt + ColorCodes.RESET,
            logging.CRITICAL: ColorCodes.RED + ColorCodes.BOLD + self.fmt + ColorCodes.RESET
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
