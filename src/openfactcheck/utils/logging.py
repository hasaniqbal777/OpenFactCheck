import os
import sys
import threading
import logging
from logging import (
    CRITICAL,  # noqa
    DEBUG,  # noqa
    ERROR,  # noqa
    FATAL,  # noqa
    INFO,  # noqa
    NOTSET,  # noqa
    WARN,  # noqa
    WARNING,  # noqa
)
from logging import captureWarnings as _captureWarnings
from typing import Optional

import datasets
import transformers

_lock = threading.Lock()
_default_handler: Optional[logging.Handler] = None

log_levels = {
    "debug": DEBUG,
    "info": INFO,
    "warning": WARNING,
    "error": ERROR,
    "critical": CRITICAL,
}

_default_log_level = logging.WARNING


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
    log_format = "%(levelname)s - %(module)s.%(funcName)s"

    # Define the log message formats for different log levels
    FORMATS = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: green + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.log_format)
        formatter = logging.Formatter(log_fmt + ": %(message)s")
        return formatter.format(record)


class CustomFileLoggingFormatter(logging.Formatter):
    """
    Custom log formatter class for file logging.
    """

    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    def format(self, record):
        formatter = logging.Formatter(self.log_format)
        return formatter.format(record)


def _get_default_logging_level():
    """
    If OPENFACTCHECK_VERBOSITY env var is set to one of the valid choices return that as the new default level.
    If it is not - fall back to `_default_log_level`
    """
    env_level_str = os.getenv("OPENFACTCHECK_VERBOSITY", None)
    if env_level_str:
        if env_level_str in log_levels:
            return log_levels[env_level_str]
        else:
            logging.getLogger().warning(
                f"Unknown option OPENFACTCHECK_VERBOSITY={env_level_str}, "
                f"has to be one of: { ', '.join(log_levels.keys()) }"
            )
    return _default_log_level


def _get_library_name() -> str:
    """
    Return the name of the library.
    """
    return __name__.split(".")[0]


def _get_library_root_logger() -> logging.Logger:
    """
    Return the root logger of the library.
    """
    return logging.getLogger(_get_library_name())


def _configure_library_root_logger() -> None:
    """
    Configure the library root logger with the default handler and formatter.
    """
    global _default_handler

    with _lock:
        if _default_handler:
            # This library has already configured the library root logger.
            return

        # Set sys.stderr as stream.
        _default_handler = logging.StreamHandler()
        _default_handler.setFormatter(CustomStreamLoggingFormatter())

        # set defaults based on https://github.com/pyinstaller/pyinstaller/issues/7334#issuecomment-1357447176
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

        # Flush the stderr stream to ensure that any logs are immediately written to the stream.
        _default_handler.flush = sys.stderr.flush

        # Apply our default configuration to the library root logger.
        library_root_logger = _get_library_root_logger()
        library_root_logger.addHandler(_default_handler)
        library_root_logger.setLevel(_get_default_logging_level())

        library_root_logger.propagate = False


def _configure_library_file_logger(file_name: str) -> None:
    global _default_handler

    with _lock:
        if _default_handler:
            # This library has already configured the library root logger.
            return

        # Set file_name as stream.
        _default_handler = logging.FileHandler(file_name)
        _default_handler.setFormatter(CustomFileLoggingFormatter())

        # set defaults based on
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

        # Flush the stderr stream to ensure that any logs are immediately written to the stream.
        _default_handler.flush = sys.stderr.flush

        # Apply our default configuration to the library root logger.
        library_root_logger = _get_library_root_logger()
        library_root_logger.addHandler(_default_handler)
        library_root_logger.setLevel(_get_default_logging_level())

        library_root_logger.propagate = False


def get_log_levels_dict():
    """
    Returns the dictionary of log levels used by OpenFactCheck.
    """
    return log_levels


def captureWarnings(capture):
    """
    Calls the `captureWarnings` method from the logging library to enable management of the warnings emitted by the
    `warnings` library.

    Read more about this method here:
    https://docs.python.org/3/library/logging.html#integration-with-the-warnings-module

    All warnings will be logged through the `py.warnings` logger.

    Careful: this method also adds a handler to this logger if it does not already have one, and updates the logging
    level of that logger to the library's root logger.
    """
    logger = get_logger("py.warnings")

    if not logger.handlers and _default_handler:
        logger.addHandler(_default_handler)

    logger.setLevel(_get_library_root_logger().level)

    _captureWarnings(capture)


def get_logger(
    name: Optional[str] = None,
    enable_file_logging: bool = False,
    file_name: str = "app.log",
) -> logging.Logger:
    """
    Return a logger with the specified name.

    This function is not supposed to be directly accessed unless you are writing a custom module.
    """

    # If the name is not provided, use the library name.
    if name is None:
        name = _get_library_name()

    # Configure the library root logger if it has not been configured yet.
    _configure_library_root_logger()

    if enable_file_logging:
        _configure_library_file_logger(file_name)

    # Return the logger with the specified name.
    return logging.getLogger(name)


def get_verbosity() -> int:
    """
    Return the current level for the OpenFactCheck's root logger as an int.

    Returns
    -------
    `int`
        The logging level of the OpenFactCheck's root logger.

    <Tip>

    OpenFactCheck has following logging levels:

    - 50: `openfactcheck.logging.CRITICAL` or `openfactcheck.logging.FATAL`
    - 40: `openfactcheck.logging.ERROR`
    - 30: `openfactcheck.logging.WARNING` or `openfactcheck.logging.WARN`
    - 20: `openfactcheck.logging.INFO`
    - 10: `openfactcheck.logging.DEBUG`

    </Tip>"""

    _configure_library_root_logger()
    return _get_library_root_logger().getEffectiveLevel()


def set_verbosity(verbosity: int | str) -> None:
    """
    Set the verbosity level for the OpenFactCheck's root logger.

    Args:
        verbosity (`int`):
            Logging level, e.g., one of:

            - `openfactcheck.logging.CRITICAL` or `openfactcheck.logging.FATAL`
            - `openfactcheck.logging.ERROR`
            - `openfactcheck.logging.WARNING` or `openfactcheck.logging.WARN`
            - `openfactcheck.logging.INFO`
            - `openfactcheck.logging.DEBUG`
    """

    _configure_library_root_logger()
    _get_library_root_logger().setLevel(verbosity)


def set_verbosity_info():
    """Set the verbosity to the `INFO` level."""
    return set_verbosity(INFO)


def set_verbosity_warning():
    """Set the verbosity to the `WARNING` level."""
    return set_verbosity(WARNING)


def set_verbosity_debug():
    """Set the verbosity to the `DEBUG` level."""
    return set_verbosity(DEBUG)


def set_verbosity_error():
    """Set the verbosity to the `ERROR` level."""
    return set_verbosity(ERROR)


def disable_default_handler() -> None:
    """Disable the default handler of the OpenFactCheck's root logger."""

    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().removeHandler(_default_handler)


def enable_default_handler() -> None:
    """Enable the default handler of the OpenFactCheck's root logger."""

    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().addHandler(_default_handler)


def add_handler(handler: logging.Handler) -> None:
    """Adds a handler to the OpenFactCheck's root logger."""

    _configure_library_root_logger()

    assert handler is not None
    _get_library_root_logger().addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    """Removes given handler from the OpenFactCheck's root logger."""

    _configure_library_root_logger()

    assert handler is not None and handler not in _get_library_root_logger().handlers
    _get_library_root_logger().removeHandler(handler)


def disable_propagation() -> None:
    """
    Disable propagation of the library log outputs. Note that log propagation is disabled by default.
    """

    _configure_library_root_logger()
    _get_library_root_logger().propagate = False


def enable_propagation() -> None:
    """
    Enable propagation of the library log outputs. Please disable the OpenFactCheck's default handler to
    prevent double logging if the root logger has been configured.
    """

    _configure_library_root_logger()
    _get_library_root_logger().propagate = True


# Disable Transformers and Datasets logging
transformers.logging.set_verbosity_error()
datasets.logging.set_verbosity_error()
logging.basicConfig(level=logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
