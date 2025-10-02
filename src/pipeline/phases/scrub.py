"""
Scrub Phase - Remove residual magenta pixels from the images
"""
import os
import logging
from typing import Dict, Any
import numpy as np
from PIL import Image

from .base import AbstractPhase


class ScrubPhase(AbstractPhase):
    """Remove residual magenta pixels from the images"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tolerance = config.get("scrub", {}).get("magenta_tolerance", 0.08)

    def run(self):
        """
        Execute the scrub phase
        """
        self.logger.info("Starting scrub phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/output/31_reattach/textures")
            raise FileNotFoundError("Missing required files in files/output/31_reattach/textures")
        
        # Create output directory
        output_dir = os.path.join("files", "output", "32_scrub", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Scrub images
        self._scrub_images()
        
        # Update the state
        self._update_state("scrub", "completed")
        self.logger.info("Scrub phase completed")

    def _check_required_files(self):
        """
        Check for required files in the pipeline/31_reattach/textures directory
        """
        textures_dir = os.path.join("files", "output", "31_reattach", "textures")
        if not os.path.exists(textures_dir):
            return False
        
        # Check for files in the directory
        if not os.listdir(textures_dir):
            return False
        
        # If we have files, we should be good
        return True

    def _scrub_images(self):
        """
        Scrub all images to remove magenta pixels
        """
        # Get input and output directories
        input_dir = os.path.join("files", "output", "31_reattach", "textures")
        output_dir = os.path.join("files", "output", "32_scrub", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PNG files
        processed_count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                self.logger.info("Scrubbing magenta pixels from %s", filename)
                self._remove_magenta_pixels(input_path, output_path)
                processed_count += 1
        
        self.logger.info("Processed %d images", processed_count)
        
        # Check if we processed any files
        if processed_count == 0:
            self.logger.warning("No PNG files found in %s", input_dir)

    def _remove_magenta_pixels(self, input_path, output_path):
        """
        Remove magenta pixels from a single image
        """
        # Load the image
        img = Image.open(input_path)
        
        # Check if the image has an alpha channel
        if img.mode == "RGBA":
            # Convert to numpy array
            img_array = np.array(img)
            
            # Separate RGB and alpha channels
            rgb = img_array[:, :, :3]
            alpha = img_array[:, :, 3]
            
            # Check for magenta pixels (high red and blue, low green)
            red_channel = rgb[:, :, 0].astype(np.float32)
            green_channel = rgb[:, :, 1].astype(np.float32)
            blue_channel = rgb[:, :, 2].astype(np.float32)
            
            # Check for magenta pixels
            magenta_mask = (red_channel > (255 * (1 - self.tolerance))) & \
                          (blue_channel > (255 * (1 - self.tolerance))) & \
                          (green_channel < (255 * self.tolerance))
            
            # Sanitize magenta pixels
            if np.any(magenta_mask):
                magenta_count = np.sum(magenta_mask)
                self.logger.info("Found %d magenta pixels in %s", magenta_count, os.path.basename(input_path))
                
                # For pixels where alpha = 0, set RGB to (0,0,0)
                zero_alpha_mask = alpha == 0
                combined_mask = magenta_mask & zero_alpha_mask
                rgb[combined_mask] = [0, 0, 0]
                
                # For pixels where alpha > 0, we could set them to a more neutral color
                # but for now, we'll just leave them as is since they're not causing halos
                # This is just to remove the pure magenta pixels that cause artifacts
                
            # Create the new image
            if np.any(magenta_mask):
                scrubbed_img = np.dstack([rgb, alpha])
                result_img = Image.fromarray(scrubbed_img, mode="RGBA")
            else:
                result_img = img.copy()
        else:
            # No alpha channel, just copy the image
            self.logger.info("Image %s has no alpha channel, copying as-is", os.path.basename(input_path))
            result_img = img.copy()
        
        # Save the scrubbed image
        result_img.save(output_path)
        self.logger.info("Saved scrubbed image to %s", output_path)