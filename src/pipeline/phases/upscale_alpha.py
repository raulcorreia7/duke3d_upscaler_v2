"""
Upscale Alpha Phase - Upscale alpha channels with Lanczos interpolation
"""
import os
import logging
from typing import Dict, Any
from PIL import Image

from .base import AbstractPhase


class UpscaleAlphaPhase(AbstractPhase):
    """Upscale alpha channels with Lanczos interpolation"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.upscale_config = config.get("upscale", {})
        self.scale = self.upscale_config.get("scale", 4)

    def run(self):
        """
        Execute the upscale alpha phase
        """
        self.logger.info("Starting upscale alpha phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/22_alpha_extract")
            raise FileNotFoundError("Missing required files in files/temp/22_alpha_extract")
        
        # Create output directory
        output_dir = os.path.join("files/temp", "23_alpha_upscale")
        os.makedirs(output_dir, exist_ok=True)
        
        # Upscale alpha channels
        self._upscale_alpha_channels()
        
        # Update the state
        self._update_state("upscale_alpha", "completed")
        self.logger.info("Upscale alpha phase completed")

    def _check_required_files(self):
        """
        Check for required files in the pipeline/22_alpha_extract directory
        """
        alpha_dir = os.path.join("files/temp", "22_alpha_extract")
        if not os.path.exists(alpha_dir):
            return False
        
        # Check for files in the directory
        if not os.listdir(alpha_dir):
            return False
        
        # If we have files, we should be good
        return True

    def _upscale_alpha_channels(self):
        """
        Upscale all alpha channels using Lanczos interpolation
        """
        # Get input and output directories
        input_dir = os.path.join("files/temp", "22_alpha_extract")
        output_dir = os.path.join("files/temp", "23_alpha_upscale")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PNG files
        processed_count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                self.logger.info("Upscaling alpha channel for %s", filename)
                self._upscale_alpha_image(input_path, output_path)
                processed_count += 1
        
        self.logger.info("Processed %d images", processed_count)
        
        # Check if we processed any files
        if processed_count == 0:
            self.logger.warning("No PNG files found in %s", input_dir)

    def _upscale_alpha_image(self, input_path, output_path):
        """
        Upscale a single alpha channel image using Lanczos interpolation
        """
        # Load the image
        img = Image.open(input_path)
        
        # Get the original size
        original_width, original_height = img.size
        
        # Calculate the new size
        new_width = original_width * self.scale
        new_height = original_height * self.scale
        
        # Resize using Lanczos interpolation
        upscaled_img = img.resize((new_width, new_height), 1)  # LANCZOS = 1
        
        # Save the upscaled image
        upscaled_img.save(output_path)
        self.logger.info("Saved upscaled alpha channel to %s", output_path)