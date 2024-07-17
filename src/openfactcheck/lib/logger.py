import logging

def get_logger():
    """
    This function returns a logger object that can be used to log messages 
    to the console and a file.
    """

    # Console Logger
    console_formatter = logging.Formatter('%(levelname)s -- %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)

    # File Logger
    # file_formatter = logging.Formatter(
    # '%(asctime)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
    # file_handler = logging.FileHandler("lambda.log")
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(file_formatter)

    # Getting the root logger
    newlogger = logging.getLogger(__name__)

    # Adding the handlers
    # logger.addHandler(file_handler)
    newlogger.addHandler(console_handler)

    # Setting the level
    newlogger.setLevel(logging.DEBUG)

    # Preventing the loggers from propagating to the root logger
    newlogger.propagate = False

    return newlogger


logger = get_logger()
