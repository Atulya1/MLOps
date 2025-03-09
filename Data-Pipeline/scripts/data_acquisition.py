"""
data_acquisition.py

Downloads multiple sets of files from the Kaggle dataset:
'bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows'
into local data folders.

Usage:
    1) pip install kaggle
    2) Place kaggle.json in ~/.kaggle/ or set KAGGLE_USERNAME / KAGGLE_KEY env vars.
    3) python data_acquisition.py
"""

import os
import sys
from kaggle.api.kaggle_api_extended import KaggleApi
from logging_config import get_logger

logger = get_logger("data_acquisition.log", logger_name=__name__)

# Adding scripts folder to system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))

from data_versions import get_data_version

# Use the dataset slug only. The --page-size is not valid here.
DATASET_NAME = "bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows"


def download_selected_files(files_to_get, download_folder):
    """
    Authenticates with Kaggle, downloads each file in 'files_to_get'
    from the 'DATASET_NAME', and saves them into download_folder.

    - If the download_folder doesn't exist or is empty, it performs the download.
    - If the folder exists and is not empty, it logs and skips downloading.
    - If Kaggle appends a .zip, it unzips and removes it.
    """
    from kaggle.api.kaggle_api_extended import KaggleApi  # ensure import if not already at top
    api = KaggleApi()
    api.authenticate()

    # Check if folder exists and is non-empty
    if os.path.exists(download_folder) and os.listdir(download_folder):
        logger.info(f"Folder '{download_folder}' already exists and is not empty. Skipping download.")
        return

    os.makedirs(download_folder, exist_ok=True)

    for filename in files_to_get:
        try:
            logger.info(f"Attempting to download {filename} ...")
            api.dataset_download_file(
                dataset=DATASET_NAME,
                file_name=filename,
                path=download_folder,
                force=True,
                quiet=False
            )

            # Check if Kaggle appended ".zip"
            zipped_path = os.path.join(download_folder, filename + ".zip")
            if os.path.exists(zipped_path):
                logger.info(f"Extracting and removing ZIP: {zipped_path}")
                import zipfile
                with zipfile.ZipFile(zipped_path, 'r') as zf:
                    zf.extractall(download_folder)
                os.remove(zipped_path)

            logger.info(f"Successfully downloaded {filename}")

        except Exception as e:
            logger.error(f"Error downloading {filename}: {str(e)}")

def main():

    # download_selected_files(FILES_TO_GET_V1, "../data/version_1")
    # download_selected_files(FILES_TO_GET_V2, "../data/version_2")
    # download_selected_files(FILES_TO_GET_V3, "../data/version_3")
    download_selected_files(get_data_version(1), "../data/version_1")

if __name__ == "__main__":
    main()
