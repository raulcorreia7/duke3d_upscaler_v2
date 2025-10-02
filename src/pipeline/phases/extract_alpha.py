"""
Extract Alpha Phase - Extract alpha channels for separate processing
"""
import os
import logging
from typing import Dict, Any
from PIL import Image

from .base import AbstractPhase


class ExtractAlphaPhase(AbstractPhase):
    """Extract alpha channels for separate processing"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the extract alpha phase
        """
        self.logger.info("Starting extract alpha phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/21_premultiply/textures")
            raise FileNotFoundError("Missing required files in files/temp/21_premultiply/textures")
        
        # Create output directory
        output_dir = os.path.join("files/temp", "22_alpha_extract")
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract alpha channels
        self._extract_alpha_channels()
        
        # Update the state
        self._update_state("extract_alpha", "completed")
        self.logger.info("Extract alpha phase completed")

    def _check_required_files(self):
        """
        Check for required files in the pipeline/21_premultiply/textures directory
        """
        premultiply_dir = os.path.join("files/temp", "21_premultiply", "textures")
        if not os.path.exists(premultiply_dir):
            return False
        
        # Check for files in the directory
        if not os.listdir(premultiply_dir):
            return False
        
        # If we have files, we should be good
        return True

    def _extract_alpha_channels(self):
        """
        Extract alpha channels from all premultiplied textures
        """
        # Get input and output directories
        input_dir = os.path.join("files/temp", "21_premultiply", "textures")
        output_dir = os.path.join("files/temp", "22_alpha_extract")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PNG files
        processed_count = 0
        for filename in os.listdir(input_dir):
            if filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                self.logger.info("Extracting alpha channel from %s", filename)
                self._extract_alpha_from_image(input_path, output_path)
                processed_count += 1
        
        self.logger.info("Processed %d images", processed_count)
        
        # Check if we processed any files
        if processed_count == 0:
            self.logger.warning("No PNG files found in %s", input_dir)

    def _extract_alpha_from_image(self, input_path, output_path):
        """
        Extract alpha channel from a single image
        """
        # Load the image
        img = Image.open(input_path)
        
        # Check if the image has an alpha channel
        if img.mode == "RGBA":
            # Extract the alpha channel
            alpha_channel = img.getchannel("A")
            
            # Save the alpha channel as a grayscale image
            alpha_channel.save(output_path)
            self.logger.info("Saved alpha channel to %s", output_path)
        else:
            # If no alpha channel, create a solid white alpha channel
            self.logger.info("Image %s has no alpha channel, creating solid white alpha", os.path.basename(input_path))
            # Create a solid white image with the same size
            alpha_channel = Image.new("L", img.size, 255)
            alpha_channel.save(output_path)
            self.logger.info("Saved solid white alpha channel to %s", output_path)