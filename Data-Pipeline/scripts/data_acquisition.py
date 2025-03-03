# scripts/data_acquisition.py

import os
from kaggle.api.kaggle_api_extended import KaggleApi
from .logging_config import setup_logging  # relative import

logger = setup_logging(log_filename="data_acquisition.log")

DATASET_NAME = "bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows"
FILE_NAME = "0831_UkraineCombinedTweetsDeduped.csv.gzip"

def fetch_data_from_kaggle():
    """
    Downloads CSV from Kaggle into /data folder, logs progress,
    and returns the path to the final file.
    """
    current_dir = os.path.dirname(__file__)   # scripts/
    data_dir = os.path.join(current_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Initialize Kaggle
    api = KaggleApi()
    api.authenticate()

    logger.info(f"Downloading '{FILE_NAME}' from '{DATASET_NAME}'...")
    api.dataset_download_file(
        dataset=DATASET_NAME,
        file_name=FILE_NAME,
        path=data_dir,
        force=True,
        quiet=False
    )
    logger.info("Download complete.")

    downloaded_zip = os.path.join(data_dir, FILE_NAME + ".zip")
    if os.path.exists(downloaded_zip):
        import zipfile
        with zipfile.ZipFile(downloaded_zip, "r") as zf:
            zf.extractall(data_dir)
        os.remove(downloaded_zip)
        logger.info(f"Extracted ZIP -> {os.path.join(data_dir, FILE_NAME)}")
    else:
        logger.warning(f"No .zip found. Assuming file is directly at {os.path.join(data_dir, FILE_NAME)}")

    final_path = os.path.join(data_dir, FILE_NAME)
    logger.info(f"Data acquisition finished. File at: {final_path}")
    return final_path

if __name__ == "__main__":
    # Standalone test
    path = fetch_data_from_kaggle()
    logger.info(f"Local data now at: {path}")
