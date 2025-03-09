import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
import logging
import shutil
import zipfile

# Set environment variables for testing
os.environ['KAGGLE_USERNAME'] = 'test_user'
os.environ['KAGGLE_KEY'] = 'test_key'

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs')))

from data_acquisition import download_selected_files, DATASET_NAME, main
from data_versions import FILES_TO_GET_V1
from logging_config import get_logger

logger = get_logger("test_logs/data_acquisition_test.log", logger_name=__name__)

@pytest.fixture
def mock_kaggle():
    with patch("kaggle.api.kaggle_api_extended.KaggleApi") as mock:
        yield mock.return_value

@pytest.fixture
def test_folder():
    folder = "/tmp/test_folder"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    yield folder
    if os.path.exists(folder):
        shutil.rmtree(folder)

def test_download_selected_files_success(mock_kaggle, test_folder):
    """Test successful file downloads"""
    download_selected_files(FILES_TO_GET_V1, test_folder)
    
    mock_kaggle.authenticate.assert_called_once()
    assert mock_kaggle.dataset_download_file.call_count == len(FILES_TO_GET_V1)

def test_download_selected_files_zip_handling(mock_kaggle, test_folder):
    """Test ZIP file handling"""
    with patch("zipfile.ZipFile") as mock_zip:
        def side_effect(**kwargs):
            zip_path = os.path.join(test_folder, kwargs['file_name'] + '.zip')
            with open(zip_path, 'w') as f:
                f.write('dummy zip content')
            return True

        mock_kaggle.dataset_download_file.side_effect = side_effect
        download_selected_files([FILES_TO_GET_V1[0]], test_folder)
        
        mock_zip.return_value.__enter__.return_value.extractall.assert_called_once()

def test_download_selected_files_error(mock_kaggle, test_folder):
    """Test error handling during download"""
    mock_kaggle.dataset_download_file.side_effect = Exception("Download failed")
    
    download_selected_files(FILES_TO_GET_V1, test_folder)
    mock_kaggle.authenticate.assert_called_once()

@patch('os.path.exists')
@patch('os.makedirs')
def test_folder_creation(mock_makedirs, mock_exists, mock_kaggle):
    """Test folder creation logic"""
    mock_exists.return_value = False
    download_selected_files(FILES_TO_GET_V1, "/tmp/new_folder")
    mock_makedirs.assert_called_once_with("/tmp/new_folder", exist_ok=True)

@patch('data_acquisition.download_selected_files')
@patch('data_versions.get_data_version')
def test_main_function(mock_get_data_version, mock_download):
    """Test main function"""
    mock_get_data_version.return_value = FILES_TO_GET_V1
    main()
    mock_download.assert_called_once_with(FILES_TO_GET_V1, "../data/version_1")

def test_logging_configuration():
    """Test logging setup and messages"""
    with patch('data_acquisition.logger') as mock_logger:
        download_selected_files(FILES_TO_GET_V1, "/tmp/test_folder")
        assert mock_logger.info.called

def test_kaggle_authentication_error(mock_kaggle):
    """Test Kaggle authentication failure"""
    mock_kaggle.authenticate.side_effect = Exception("Authentication failed")
    
    with pytest.raises(Exception):
        download_selected_files(FILES_TO_GET_V1, "/tmp/test_folder")

def test_multiple_file_downloads(mock_kaggle, test_folder):
    """Test downloading multiple files in sequence"""
    files = FILES_TO_GET_V1[:2]  # Test with first two files
    download_selected_files(files, test_folder)
    
    assert mock_kaggle.dataset_download_file.call_count == len(files)
    for file in files:
        mock_kaggle.dataset_download_file.assert_any_call(
            dataset=DATASET_NAME,
            file_name=file,
            path=test_folder,
            force=True,
            quiet=False
        )



