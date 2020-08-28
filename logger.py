import logging
import logging.config
import queue
import sys
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pythonjsonlogger import jsonlogger  # type: ignore

# init root logger with null handler
logging.basicConfig(handlers=[logging.NullHandler()])

# init log queue for handler and listener
log_queue: queue.Queue = queue.Queue()
log_qlistener: QueueListener = QueueListener(log_queue)
log_qlistener.start()


class StackdriverFormatter(jsonlogger.JsonFormatter):
    def process_log_record(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        log_record["severity"] = log_record["levelname"]
        return super().process_log_record(log_record)


def __get_log_formatter() -> StackdriverFormatter:
    # formatter
    log_format = " - ".join([
        "%(asctime)s",
        "%(levelname)s",
        "%(name)s",
        "%(processName)s",
        "%(threadName)s",
        "%(filename)s",
        "%(module)s",
        "%(lineno)d",
        "%(funcName)s",
        "%(message)s",
    ])
    date_format = "%Y-%m-%dT%H:%M:%S"
    log_formatter = StackdriverFormatter(fmt=log_format, datefmt=date_format, timestamp=True)
    return log_formatter


def __get_file_handler(log_path: str = "main.log") -> RotatingFileHandler:
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 2 ** 20,  # 10 MB
        backupCount=1,  # 1 backup
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(__get_log_formatter())
    return file_handler


def __get_stdout_handler() -> logging.StreamHandler:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(__get_log_formatter())
    return stdout_handler


def configure_log_handlers(console: bool = True,
                           log_path: str = "main.log") -> QueueListener:
    """
    Configure log queue listener to log into file and console.
    Args:
        console (bool): whether to log on console
        log_path (str): path of log file
    Returns:
        log_qlistener (logging.handlers.QueueListener): configured log queue listener
    """
    global log_qlistener
    try:
        log_qlistener.stop()
    except (AttributeError, NameError):
        pass

    handlers: List[logging.Handler] = []

    # rotating file handler
    if log_path:
        file_handler = __get_file_handler(log_path)
        handlers.append(file_handler)

    # console handler
    if console:
        stdout_handler = __get_stdout_handler()
        handlers.append(stdout_handler)

    log_qlistener = QueueListener(log_queue, *handlers, respect_handler_level=True)
    log_qlistener.start()
    return log_qlistener


def configure_loggers(yaml_path: str = "logging.yml") -> None:
    log_conf = yaml.safe_load(Path(yaml_path).read_text())
    logging.config.fileConfig(log_conf)


def get_logger(name: str) -> logging.Logger:
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
    logger.addHandler(QueueHandler(log_queue))

    return logger


if __name__ == "__main__":
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Simple script to run `get_logger()`.")
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

    configure_log_handlers(True, args.log_path)
    # logger = get_logger(args.logger_name)
    configure_loggers()
    logger = logging.getLogger(args.logger_name)
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

    configure_log_handlers(True, "")
    logger.info("This message should appear in the console only.")

    configure_log_handlers(False, args.log_path)
    logger.info("This message should appear in the log file only.")

    configure_log_handlers(False, "")
    logger.info("This message should not appear.")
