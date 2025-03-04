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
from kaggle.api.kaggle_api_extended import KaggleApi
from logging_config import get_logger

logger = get_logger("data_acquisition.log", logger_name=__name__)

# Use the dataset slug only. The --page-size is not valid here.
DATASET_NAME = "bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows"

FILES_TO_GET_V1 = [
    "0819_UkraineCombinedTweetsDeduped.csv",
    "0820_UkraineCombinedTweetsDeduped.csv",
    "0821_UkraineCombinedTweetsDeduped.csv",
    "0822_UkraineCombinedTweetsDeduped.csv",
    "0823_UkraineCombinedTweetsDeduped.csv",
    "0824_UkraineCombinedTweetsDeduped.csv",
    "0825_UkraineCombinedTweetsDeduped.csv",
    "0826_UkraineCombinedTweetsDeduped.csv",
    "0827_UkraineCombinedTweetsDeduped.csv",
    "0828_UkraineCombinedTweetsDeduped.csv"
]

FILES_TO_GET_V2 = [
    "0829_UkraineCombinedTweetsDeduped.csv",
    "0830_UkraineCombinedTweetsDeduped.csv",
    "0901_UkraineCombinedTweetsDeduped.csv",
    "0902_UkraineCombinedTweetsDeduped.csv",
    "0903_UkraineCombinedTweetsDeduped.csv",
    "0904_UkraineCombinedTweetsDeduped.csv",
    "0905_UkraineCombinedTweetsDeduped.csv",
    "0906_UkraineCombinedTweetsDeduped.csv",
    "0907_UkraineCombinedTweetsDeduped.csv",
    "0908_UkraineCombinedTweetsDeduped.csv",
    "0910_UkraineCombinedTweetsDeduped.csv",
    "0911_UkraineCombinedTweetsDeduped.csv",
    "0912_UkraineCombinedTweetsDeduped.csv",
    "0913_UkraineCombinedTweetsDeduped.csv",
]

FILES_TO_GET_V3 = [
    "0914_UkraineCombinedTweetsDeduped.csv",
    "0915_UkraineCombinedTweetsDeduped.csv",
    "0916_UkraineCombinedTweetsDeduped.csv",
    "0917_UkraineCombinedTweetsDeduped.csv",
    "0918_UkraineCombinedTweetsDeduped.csv",
    "0919_UkraineCombinedTweetsDeduped.csv",
    "0920_UkraineCombinedTweetsDeduped.csv",
    "0921_UkraineCombinedTweetsDeduped.csv",
    "0922_UkraineCombinedTweetsDeduped.csv",
    "0923_UkraineCombinedTweetsDeduped.csv",
    "0924_UkraineCombinedTweetsDeduped.csv",
    "0925_UkraineCombinedTweetsDeduped.csv"
    "0926_UkraineCombinedTweetsDeduped.csv",
    "0927_UkraineCombinedTweetsDeduped.csv",
    "0928_UkraineCombinedTweetsDeduped.csv",
    "0929_UkraineCombinedTweetsDeduped.csv",
    "0930_UkraineCombinedTweetsDeduped.csv",
    "0930_UkraineCombinedTweetsDeduped.csv"
]

def download_selected_files(files_to_get, download_folder):
    """
    Authenticates with Kaggle, downloads each file in 'files_to_get'
    from the 'DATASET_NAME', and saves them into download_folder.

    If Kaggle appends a .zip, we unzip and remove it.
    """
    api = KaggleApi()
    api.authenticate()

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
    download_selected_files(FILES_TO_GET_V1, "../data/version_1")
    download_selected_files(FILES_TO_GET_V2, "../data/version_2")
    download_selected_files(FILES_TO_GET_V3, "../data/version_3")

if __name__ == "__main__":
    main()
