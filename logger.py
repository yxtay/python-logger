import logging
from logging.handlers import RotatingFileHandler


def get_logger(name, log_path="log"):
    logger = logging.getLogger(name)

    # ensure that logging handlers are added just once
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # rotating file handler
        fh = RotatingFileHandler(log_path,
                                 maxBytes=2 ** 20,  # 1 MB
                                 backupCount=1)  # 1 backup
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Simple script to run get_logger.")
    parser.add_argument("--path", help="log file", default="log")
    parser.add_argument("--reset", help="delete log files", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.path):
        os.remove(args.path)

    logger = get_logger(__name__, args.path)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    try:
        raise ValueError("Test error.")
    except ValueError as e:
        logger.exception(e)

    logger = get_logger(__name__, args.path)
    logger.info("This message should appear just once.")
