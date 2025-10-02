"""
Asset verification utility for the pipeline
"""
import os
import logging
from PIL import Image
import numpy as np
from typing import Tuple, List

def verify_no_pink_halos(image_path: str, tolerance: float = 0.08) -> bool:
    """
    Verify that an image does not contain pink halos (alpha=0 but RGB!=0).
    
    :param image_path: Path to the image file
    :param tolerance: Tolerance for pink detection (0.0-1.0)
    :return: True if no pink halos found, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Open the image
    img = Image.open(image_path)
    
    # Convert to RGBA if not already
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Separate RGB and alpha channels
    rgb_array = img_array[:, :, :3]
    alpha_array = img_array[:, :, 3]
    
    # Find pixels where alpha is 0
    alpha_zero_mask = alpha_array == 0
    
    # Check if there are any pixels with alpha=0
    if not np.any(alpha_zero_mask):
        return True
    
    # For pixels with alpha=0, check if RGB values are non-zero
    rgb_at_alpha_zero = rgb_array[alpha_zero_mask]
    
    # Check if any RGB values are significantly non-zero
    # (accounting for some tolerance)
    max_rgb_values = np.max(rgb_at_alpha_zero, axis=1)
    pink_pixels = max_rgb_values > (255 * tolerance)
    
    # If we found any pink pixels, return False
    if np.any(pink_pixels):
        pink_count = np.sum(pink_pixels)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        pink_percentage = (pink_count / total_pixels) * 100
        logger.warning(f"Found {pink_count} pink pixels ({pink_percentage:.2f}%) in {image_path}")
        return False
    
    return True

def verify_no_magenta_pixels(image_path: str, tolerance: float = 0.08) -> bool:
    """
    Verify that an image does not contain magenta pixels.
    
    :param image_path: Path to the image file
    :param tolerance: Tolerance for magenta detection (0.0-1.0)
    :return: True if no magenta pixels found, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Open the image
    img = Image.open(image_path)
    
    # Convert to RGB if not already
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Extract RGB channels
    r = img_array[:, :, 0].astype(np.float32)
    g = img_array[:, :, 1].astype(np.float32)
    b = img_array[:, :, 2].astype(np.float32)
    
    # Check for magenta pixels (high red, low green, high blue)
    # Magenta = (255, 0, 255)
    magenta_mask = (r >= 255 * (1 - tolerance)) & (g <= 255 * tolerance) & (b >= 255 * (1 - tolerance))
    
    # If we found any magenta pixels, return False
    if np.any(magenta_mask):
        magenta_count = np.sum(magenta_mask)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        magenta_percentage = (magenta_count / total_pixels) * 100
        logger.warning(f"Found {magenta_count} magenta pixels ({magenta_percentage:.2f}%) in {image_path}")
        return False
    
    return True

def verify_image_sanitization(image_path: str) -> bool:
    """
    Verify that an image has been properly sanitized (no pink halos or magenta pixels).
    
    :param image_path: Path to the image file
    :return: True if image passes all verification checks, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check for pink halos
    if not verify_no_pink_halos(image_path):
        logger.error(f"Image {image_path} failed pink halo verification")
        return False
    
    # Check for magenta pixels
    if not verify_no_magenta_pixels(image_path):
        logger.error(f"Image {image_path} failed magenta pixel verification")
        return False
    
    logger.info(f"Image {image_path} passed all verification checks")
    return True

def verify_all_images_in_directory(directory: str) -> bool:
    """
    Verify all images in a directory.
    
    :param directory: Path to the directory containing images
    :return: True if all images pass verification, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check if directory exists
    if not os.path.exists(directory):
        logger.error(f"Directory {directory} does not exist")
        return False
    
    # Get all PNG files in the directory
    png_files = [f for f in os.listdir(directory) if f.endswith(".png")]
    
    # If no PNG files, return True
    if not png_files:
        logger.info(f"No PNG files found in {directory}")
        return True
    
    # Verify each image
    all_passed = True
    for filename in png_files:
        image_path = os.path.join(directory, filename)
        if not verify_image_sanitization(image_path):
            all_passed = False
            logger.error(f"Image {filename} failed verification")
    
    if all_passed:
        logger.info(f"All {len(png_files)} images in {directory} passed verification")
    else:
        logger.error(f"Some images in {directory} failed verification")
    
    return all_passed