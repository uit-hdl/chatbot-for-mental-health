import logging

LOGFILE_DUMP_PATH = "chat.log"
DISCARDED_RESPONSES_LOGFILE = "discarded_responses.log"
HARVESTED_SYNTAX = "discarded_responses.log"


def setup_logging(logfile_dump_path, rejected_responses_dump_path):
    """Creates logging objects. One for general logging, and one for chatbot responses
    that get rejected (fail quality check)."""
    # Create a common configuration for both loggers
    common_config = {
        "level": logging.INFO,
        "format": "%(asctime)s - %(levelname)s [%(module)s.%(funcName)s]: \n%(message)s\n",
        "filemode": "w",
    }

    # Configure the main logger for chat.log
    logging.basicConfig(filename=logfile_dump_path, **common_config)
    logger_general = logging.getLogger(__name__)

    # Create a separate logger for rejected responses
    logger_rejected_responses = logging.getLogger("discarded_responses")
    logger_rejected_responses.setLevel(logging.INFO)

    # Configure the rejected responses logger to write to rejected_responses.log
    rejected_responses_handler = logging.FileHandler(
        rejected_responses_dump_path, mode="w"
    )
    rejected_responses_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s [%(module)s.%(funcName)s]:\nREJECTED RESPONSE:\n%(message)s\n\n"
    )
    rejected_responses_handler.setFormatter(rejected_responses_formatter)
    logger_rejected_responses.addHandler(rejected_responses_handler)

    return logger_general, logger_rejected_responses
