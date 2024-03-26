import logging
import os

LOGFILE_DUMP_PATH = "chat.log"
DISCARDED_RESPONSES_LOGFILE = "discarded_responses.log"
HARVESTED_SYNTAX = "discarded_responses.log"

def setup_logger(log_file_path: str, level=logging.INFO):
    """Creates a logger object."""
    # Create a logger
    logger = logging.getLogger(log_file_path)
    logger.setLevel(level)

    # Create directory if it does not exist
    dirpath = os.path.dirname(log_file_path)
    if dirpath != "":
        os.makedirs(dirpath, exist_ok=True)
    # Create a file handler and set the formatter
    file_handler = logging.FileHandler(filename=log_file_path, mode="w")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s [%(module)s.%(funcName)s]: \n%(message)s\n"
    )
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
