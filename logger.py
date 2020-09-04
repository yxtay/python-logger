import atexit
import logging
import logging.config
import sys
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any, Dict, List

import yaml
from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore

# init root logger with null handler
logging.basicConfig(handlers=[logging.NullHandler()])

# init log queue for handler and listener
log_queue: Queue = Queue()
log_qlistener: QueueListener = QueueListener(log_queue, respect_handler_level=True)
log_qlistener.start()
atexit.register(log_qlistener.stop)


class StackdriverFormatter(JsonFormatter):
    def process_log_record(self, log_record: Dict[str, Any]) -> Dict[str, Any]:
        log_record["severity"] = log_record["levelname"]
        return super().process_log_record(log_record)


def _get_log_formatter() -> StackdriverFormatter:
    # formatter
    log_format = " - ".join(
        [
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
        ]
    )
    date_format = "%Y-%m-%dT%H:%M:%S"
    log_formatter = StackdriverFormatter(
        fmt=log_format, datefmt=date_format, timestamp=True
    )
    return log_formatter


def _get_file_handler(
    log_path: str = "main.log", log_level: int = logging.DEBUG
) -> RotatingFileHandler:
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2 ** 20,  # 1 MB
        backupCount=10,  # 10 backup
        encoding="utf8",
        delay=True,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(_get_log_formatter())
    return file_handler


def _get_stdout_handler(log_level: int = logging.INFO) -> logging.StreamHandler:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(_get_log_formatter())
    return stdout_handler


class QueueListenerHandler(QueueHandler):
    def __init__(self, handlers):
        super().__init__(Queue())
        self.start_listener(self.queue, handlers)

    def start_listener(self, queue, handlers) -> QueueListener:
        self.listener = QueueListener(queue, *handlers, respect_handler_level=True)
        self.listener.start()
        atexit.register(self.listener.stop)
        return self.listener


def configure_log_listener(
    console: bool = True, log_path: str = "main.log"
) -> QueueListener:
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
        atexit.unregister(log_qlistener.stop)
        log_qlistener.stop()
        atexit.unregister(log_qlistener.stop)
    except (AttributeError, NameError):
        pass

    handlers: List[logging.Handler] = []

    # rotating file handler
    if log_path:
        file_handler = _get_file_handler(log_path)
        handlers.append(file_handler)

    # console handler
    if console:
        stdout_handler = _get_stdout_handler()
        handlers.append(stdout_handler)

    log_qlistener = QueueListener(log_queue, *handlers, respect_handler_level=True)
    log_qlistener.start()
    atexit.register(log_qlistener.stop)
    return log_qlistener


def configure_loggers(conf_yaml: str = "logging.yml") -> None:
    """
    Configure loggers with configurations defined in yaml
    Args:
        conf_yaml: path of yaml config file
    """
    log_conf = yaml.safe_load(Path(conf_yaml).read_text())
    logging.config.dictConfig(log_conf)


def get_logger(name: str, log_level: int = logging.DEBUG) -> logging.Logger:
    """
    Simple logging wrapper that returns logger
    configured to log into file and console.
    Args:
        name: name of logger
        log_level: log level
    Returns:
        logger: configured logger
    """
    logger = logging.getLogger(name)
    for log_handler in logger.handlers[:]:
        logger.removeHandler(log_handler)

    logger.setLevel(log_level)
    logger.addHandler(QueueHandler(log_queue))

    return logger


if __name__ == "__main__":
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Simple script to run `get_logger()`.")
    parser.add_argument("--logger-name", default=__name__, help="name of logger")
    parser.add_argument("--log-path", default="main.log", help="path of log file")
    parser.add_argument(
        "--reset", action="store_true", help="whether to reset log file"
    )
    args = parser.parse_args()

    if args.reset and os.path.exists(args.log_path):
        os.remove(args.log_path)

    configure_log_listener(True, args.log_path)
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

    configure_log_listener(True, "")
    logger.info("This message should appear in the console only.")

    configure_log_listener(False, args.log_path)
    logger.info("This message should appear in the log file only.")

    configure_log_listener(False, "")
    logger.info("This message should not appear.")
