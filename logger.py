import logging
from logging.handlers import RotatingFileHandler
import os


def get_logger(name, log_path=os.path.join(os.path.dirname(__file__), "main.log"), console=False):
    """
    Simple logging wrapper that returns logger
    configured to log into file and console.

    Args:
        name (str): name of logger
        log_path (str): path of log file
        console (bool): whether to log on console

    Returns:
        logging.Logger: configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # ensure that logging handlers are not duplicated
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    # rotating file handler
    if log_path:
        fh = RotatingFileHandler(log_path,
                                 maxBytes=2 ** 20,  # 1 MB
                                 backupCount=1)  # 1 backup
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # console handler
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if len(logger.handlers) == 0:
        logger.addHandler(logging.NullHandler())

    return logger


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple script to run `get_logger()`.")
    parser.add_argument("--log-path", default="main.log",
                        help="path of log file")
    parser.add_argument("--reset", action="store_true",
                        help="whether to reset log file")
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
