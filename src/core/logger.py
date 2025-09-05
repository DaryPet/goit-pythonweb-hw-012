import logging
from logging.config import dictConfig

LOG_LEVEL = "INFO"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "default",
        }
    },
    "root": {"level": LOG_LEVEL, "handlers": ["console"]},
}


def setup_logging() -> None:
    """
    Applies the logging configuration from the LOGGING_CONFIG dictionary.

    This function should be called once at the start of the application.
    """
    dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance for a specific module.
    """
    return logging.getLogger(name)
