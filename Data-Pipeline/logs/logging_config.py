# # scripts/logging_config.py
#
# import os
# import logging
#
# def setup_logging(log_filename="data_pipeline.log"):
#     """
#     Create a logger that writes to both a file and the console.
#     """
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.INFO)
#
#     # Ensure /logs folder exists relative to this script
#     current_dir = os.path.dirname(__file__)
#     logs_dir = os.path.join(current_dir, "..", "logs")
#     os.makedirs(logs_dir, exist_ok=True)
#
#     log_path = os.path.join(logs_dir, log_filename)
#     formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s")
#
#     # File handler
#     file_handler = logging.FileHandler(log_path, mode="a")
#     file_handler.setFormatter(formatter)
#     logger.addHandler(file_handler)
#
#     # Console handler
#     console_handler = logging.StreamHandler()
#     console_handler.setFormatter(formatter)
#     logger.addHandler(console_handler)
#
#     return logger

# logging_config.py

import logging

def get_logger(name=__name__):
    """
    Return a logger that writes to Airflow's logging system and console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        # Add console handler if not present
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s"
        ))
        logger.addHandler(console_handler)
    return logger
