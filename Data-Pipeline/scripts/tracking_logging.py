"""
tracking_logging.py

Configure logging for your pipeline so that all logs
go to console + a file in /logs.
"""

import os
import logging

def setup_logging(log_filename="pipeline.log"):
    """
    Creates a logger that writes to console + a log file.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if already present
    if not logger.handlers:
        # create logs folder if not exists
        current_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(current_dir, "..", "logs")
        os.makedirs(logs_dir, exist_ok=True)

        formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s")

        # File handler
        file_path = os.path.join(logs_dir, log_filename)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
