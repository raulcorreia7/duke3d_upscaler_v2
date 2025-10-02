"""
Premultiply Phase - Premultiply alpha to prevent ESRGAN pink halos
"""
import os
import logging
from typing import Dict, Any
from PIL import Image
import numpy as np

from .base import AbstractPhase


class PremultiplyPhase(AbstractPhase):
    """Premultiply alpha to prevent ESRGAN pink halos"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the premultiply phase
        """
        self.logger.info("Starting premultiply phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/20_convert/textures")
            raise FileNotFoundError("Missing required files in files/temp/20_convert/textures")
        
        # Create output directory
        output_dir = os.path.join("files/temp", "21_premultiply", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Premultiply textures
        self._premultiply_textures()
        
        # Update the state
        self._update_state("premultiply", "completed")
        self.logger.info("Premultiply phase completed")

    def _check_required_files(self):
        """
        Check for required files in the pipeline/20_convert/textures directory
        """
        convert_dir = os.path.join("files/temp", "20_convert", "textures")
        if not os.path.exists(convert_dir):
            return False
        
        # Check for files in the directory
        if not os.listdir(convert_dir):
            return False
        
        # If we have files, we should be good
        return True

    def _premultiply_textures(self):
        """
        Premultiply all textures to prevent pink halos
        """
        # Get input and output directories
        input_dir = os.path.join("files/temp", "20_convert", "textures")
        output_dir = os.path.join("files/temp", "21_premultiply", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PNG files
        processed_count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                self.logger.info("Premultiplying alpha for %s", filename)
                self._premultiply_image(input_path, output_path)
                processed_count += 1
        
        self.logger.info("Processed %d images", processed_count)
        
        # Check if we processed any files
        if processed_count == 0:
            self.logger.warning("No PNG files found in %s", input_dir)

    def _premultiply_image(self, input_path, output_path):
        """
        Premultiply a single image's alpha channel
        For pixels where alpha = 0, set RGB to (0,0,0)
        For pixels where alpha > 0, premultiply RGB by alpha
        """
        # Load the image
        img = Image.open(input_path)
        
        # Check if the image has an alpha channel
        if img.mode == "RGBA":
            # Convert to numpy array for processing
            img_array = np.array(img)
            
            # Separate RGB and alpha channels
            rgb = img_array[:, :, :3].astype(np.float32)
            alpha = img_array[:, :, 3].astype(np.float32) / 255.0  # Normalize to 0-1
            
            # For pixels where alpha = 0, set RGB to (0,0,0)
            # For pixels where alpha > 0, premultiply RGB by alpha
            mask = alpha > 0
            rgb[mask] = rgb[mask] * alpha[mask, np.newaxis]
            rgb[~mask] = 0  # Set RGB to (0,0,0) where alpha = 0
            
            # Convert back to uint8
            rgb = np.clip(rgb, 0, 255).astype(np.uint8)
            
            # Create the new image with premultiplied alpha
            premultiplied_img = np.dstack([rgb, img_array[:, :, 3]])
            result_img = Image.fromarray(premultiplied_img, mode="RGBA")
        else:
            # If no alpha channel, just copy the image
            self.logger.info("Image %s has no alpha channel, copying as-is", os.path.basename(input_path))
            result_img = img.copy()
        
        # Save the premultiplied image
        result_img.save(output_path)
        self.logger.info("Saved premultiplied image to %s", output_path)