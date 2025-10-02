"""
Soundfont download utility for the pipeline
"""
import os
import logging
import requests
import zipfile
from typing import Dict, Any
import gdown

def download_soundfont(url: str, output_path: str, config: Dict[str, Any] = {}):
    """
    Download the soundfont from the given URL.
    """
    logger = logging.getLogger(__name__)
    if os.path.exists(output_path):
        logger.info("Soundfont file already exists at %s", output_path)
        return
    # Create the directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # If the URL is a Google Drive URL, download it with gdown
    if "drive.google.com" in url:
        logger.info("Downloading soundfont from Google Drive: %s", output_path)
        try:
            gdown.download(url, output_path, quiet=False)
        except Exception as e:
            logger.error("Error downloading soundfont from Google Drive: %s", e)
            raise
    elif "archive.org" in url:
        # Download from archive.org
        if url.endswith(".zip"):
            # Download the ZIP
            zip_file = output_path + ".zip"
            logger.info("Downloading soundfont from Archive.org: %s", zip_file)
            # Download the file
            response = requests.get(url)
            with open(zip_file, "wb") as f:
                f.write(response.content)
            # Extract the file
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                zip_ref.extractall(os.path.dirname(output_path))
            # Remove the file
            os.remove(zip_file)
            print("File downloaded and extracted: %s" % output_path)
        else:
            response = requests.get(url)
            with open(output_path, "w") as f:
                f.write(response.text)
            print("Downloaded: ", output_path)
    else:
        # Standard download
        logger.info("Downloading soundfont from URL: %s", output_path)
        try:
            response = requests.get(url)
            with open(output_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.error("Error downloading soundfont: %s", e)
            raise
    print("Soundfont downloaded: %s" % output_path)