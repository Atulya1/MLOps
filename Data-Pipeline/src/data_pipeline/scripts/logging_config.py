# logging_config.py

import os
import logging

def get_logger(log_filename="data_acquisition.log", logger_name=__name__):
    """
    Returns a logger that writes to:
      1) Console (so Airflow can capture logs in UI, or you see them in terminal)
      2) A local file (./logs/<log_filename>) if running a script outside Airflow
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # If no handlers exist yet, attach them
    if not logger.handlers:
        # 1) Console Handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 2) File Handler (writes to ./logs/<log_filename>)
        current_dir = os.path.dirname(__file__)  # e.g., Data-Pipeline/scripts
        logs_dir = os.path.join(current_dir, "..", "logs")
        os.makedirs(logs_dir, exist_ok=True)

        file_path = os.path.join(logs_dir, log_filename)
        file_handler = logging.FileHandler(file_path, mode='a')
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger
