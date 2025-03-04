import os
import pytest
from unittest.mock import patch, MagicMock
import logging
import shutil

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs')))

from data_acquisition import download_selected_files, DATASET_NAME, FILES_TO_GET_V1
from logging_config import get_logger
logger = get_logger("test_logs/data_acquisition_test.log", logger_name=__name__)

@patch("kaggle.KaggleApi") 
def test_download_selected_files(mock_kaggle_api):
    """Test the download_selected_files function with a mocked Kaggle API."""
    mock_instance = mock_kaggle_api.return_value  # Correctly mock instance

    download_selected_files(FILES_TO_GET_V1, "/tmp/test_folder")

    mock_instance.authenticate.assert_called_once()

    # dataset_download_file() was called for each file
    for file in FILES_TO_GET_V1:
        mock_instance.dataset_download_file.assert_any_call(
            dataset=DATASET_NAME,
            file_name=file,
            path="/tmp/test_folder",
            force=True,
            quiet=False
        )
        
@patch("logging.getLogger")
def test_logging(mock_get_logger):
    """Test that logging works as expected."""
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    test_message = "This is a test log for download_selected_files function."
    logger.info(test_message)

def test_directory_creation():
    """Test directory creation and cleanup."""
    download_folder = "/tmp/test_folder"

    if os.path.exists(download_folder):
        shutil.rmtree(download_folder)

    os.makedirs(download_folder)
    assert os.path.exists(download_folder)

    shutil.rmtree(download_folder)
    assert not os.path.exists(download_folder)



