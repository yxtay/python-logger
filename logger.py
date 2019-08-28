import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import jsonlogger

# formatter
log_format = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(lineno)d - %(funcName)s - %(message)s"
formatter = jsonlogger.JsonFormatter(fmt=log_format, timestamp=True)

# stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)


def get_logger(name, log_path="main.log", console=True):
    """
    Simple logging wrapper that returns logger
    configured to log into file and console.

    Args:
        name (str): name of logger
        log_path (str): path of log file
        console (bool): whether to log on console

    Returns:
        logger (logging.Logger): configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # ensure that logging handlers are not duplicated
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # rotating file handler
    if log_path:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 2 ** 20,  # 10 MB
            backupCount=1,  # 1 backup
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # console handler
    if console:
        logger.addHandler(stdout_handler)

    if not logger.hasHandlers():
        logger.addHandler(logging.NullHandler())

    return logger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple script to run `get_logger()`.")
    parser.add_argument(
        "--log-path",
        default="main.log",
        help="path of log file"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="whether to reset log file"
    )
    args = parser.parse_args()

    if args.reset and os.path.exists(args.log_path):
        os.remove(args.log_path)

    logger = get_logger(__name__, args.log_path, True)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    try:
        raise ValueError("This is an exception message.")
    except ValueError as e:
        logger.exception(e)

    logger = get_logger(__name__, args.log_path, True)
    logger.info("This message should appear just once.")

    logger = get_logger(__name__, "", True)
    logger.info("This message should appear in the console only.")

    logger = get_logger(__name__, args.log_path, False)
    logger.info("This message should appear in the log file only.")

    logger = get_logger(__name__, "", False)
    logger.info("This message should not appear.")
