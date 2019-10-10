import argparse
import logging
import os
import queue
import sys
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener

from pythonjsonlogger import jsonlogger

# formatter
log_format = "%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(lineno)d - %(funcName)s - %(message)s"
log_formatter = jsonlogger.JsonFormatter(fmt=log_format, timestamp=True)

# stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(log_formatter)

# init log_queue and listener
log_queue = queue.Queue()
log_queue_handler = QueueHandler(log_queue)
log_listener = QueueListener(log_queue, respect_handler_level=True)
log_listener.start()


def configure_handlers(log_path="main.log", console=True):
    """
    Configure log queue listener to log into file and console.

    Args:
        log_path (str): path of log file
        console (bool): whether to log on console

    Returns:
        logger (logging.Logger): configured logger
    """
    global log_listener
    log_listener.stop()
    log_handlers = []

    # rotating file handler
    if log_path:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 2 ** 20,  # 10 MB
            backupCount=1,  # 1 backup
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        log_handlers.append(file_handler)

    # console handler
    if console:
        log_handlers.append(stdout_handler)

    log_listener = QueueListener(log_queue, *log_handlers, respect_handler_level=True)
    log_listener.start()
    return log_listener


def get_logger(name="root"):
    """
    Simple logging wrapper that returns logger
    configured to log into file and console.

    Args:
        name (str): name of logger

    Returns:
        logger (logging.Logger): configured logger
    """
    logger = logging.getLogger(name)
    for log_handler in logger.handlers[:]:
        logger.removeHandler(log_handler)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_queue_handler)

    return logger


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple script to run `get_logger()`.")
    parser.add_argument(
        "--logger-name",
        default=__name__,
        help="name of logger"
    )
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

    configure_handlers(args.log_path, True)
    logger = get_logger(args.logger_name)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    try:
        raise ValueError("This is an exception message.")
    except ValueError as e:
        logger.exception(e)

    logger = get_logger(args.logger_name)
    logger.info("This message should appear just once.")

    configure_handlers("", True)
    logger.info("This message should appear in the console only.")

    configure_handlers(args.log_path, False)
    logger.info("This message should appear in the log file only.")

    configure_handlers("", False)
    logger.info("This message should not appear.")
