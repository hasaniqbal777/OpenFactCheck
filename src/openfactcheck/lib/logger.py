import logging

class CustomStreamLoggingFormatter(logging.Formatter):
    """
    Custom log formatter class to colorize log messages based on their level.
    """

    # Define the color codes
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    log_format = "%(levelname)s"

    # Define the log message formats for different log levels
    FORMATS = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: green + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt + " -- %(message)s")
        return formatter.format(record)

class CustomFileLoggingFormatter(logging.Formatter):
    """
    Custom log formatter class for file logging.
    """

    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    def format(self, record):
        formatter = logging.Formatter(self.log_format)
        return formatter.format(record)
    
def get_logger(name=__name__, enable_file_logging=False, file_name="app.log"):
    """
    Returns a logger object configured with a console handler and optionally a file handler.

    Parameters
    ----------
    name : str
        The name of the logger.
    enable_file_logging : bool
        Whether to enable file logging.
    file_name : str
        The name of the log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set the logger level to DEBUG

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomStreamLoggingFormatter())  # Apply the custom formatter
    logger.addHandler(console_handler)

    # Optional File Handler
    if enable_file_logging:
        file_handler = logging.FileHandler(file_name)
        file_handler.setFormatter(CustomFileLoggingFormatter())  # Apply the custom formatter
        logger.addHandler(file_handler)

    logger.propagate = False  # Prevent the logger from propagating to the root logger

    return logger

def set_logger_level(logger, level):
    """
    Set the logger level based on the input string.
    
    Parameters
    ----------
    logger : logging.Logger
        The logger object.
    level : str
        The log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    level = level.upper()
    if level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif level == "INFO":
        logger.setLevel(logging.INFO)
    elif level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        logger.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        logger.setLevel(logging.CRITICAL)
    else:
        logger.warning("Invalid log level. Using default level INFO.")
        logger.setLevel(logging.INFO)

# Create a logger object
logger = get_logger(__name__, enable_file_logging=True, file_name="app.log")