class Error(Exception):
    """Base class for other exceptions"""

class ConfigError(Error):
    """Raised when there is an error with the configurations"""