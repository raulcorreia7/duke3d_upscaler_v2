"""
Model download utility for the pipeline
"""
import os
import logging
import gdown
import requests
from typing import Dict, Any

# Model URLs for Real-ESRGAN
MODEL_URLS = {
    "realesrgan-x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "realesrgan-x4plus-anime": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
}

def download_model(model_name: str, output_path: str, config: Dict[str, Any] = {}):
    """
    Download the model from the given URL.
    """
    logger = logging.getLogger(__name__)
    if os.path.exists(output_path):
        logger.info("Model file already exists at %s", output_path)
        return

    # Create the directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Get the model URL
    if model_name in MODEL_URLS:
        url = MODEL_URLS[model_name]
    else:
        # If model not in the URL, raise the URL
        raise ValueError("Model URL not in URL: %s" % model_name)

    # Download the model
    logger.info("Downloading model from URL: %s", url)
    # Download the file
    try:
        # If the URL is a Google Drive URL, use gdown
        if "drive.google.com" in url:
            # Download the file
            gdown.download(url, output_path, quiet=False)
        else:
            # Download the file with requests
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        # Print the file
        logger.info("Downloaded: %s", output_path)
        return
    # If error, raise the error
    except Exception as e:
        # Log the error
        logger.error("Error downloading model: %s", e)
        # Return the error
        raise
    # Return the file
    return