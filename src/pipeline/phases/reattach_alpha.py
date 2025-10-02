"""
Reattach Alpha Phase - Reattach alpha to upscaled images
"""
import os
import logging
from typing import Dict, Any
from PIL import Image

from .base import AbstractPhase


class ReattachAlphaPhase(AbstractPhase):
    """Reattach alpha to upscaled images"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the reattach alpha phase
        """
        self.logger.info("Starting reattach alpha phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/30_upscale/textures or files/temp/23_alpha_upscale")
            raise FileNotFoundError("Missing required files in files/temp/30_upscale/textures or files/temp/23_alpha_upscale")
        
        # Create output directory
        output_dir = os.path.join("files/temp", "31_reattach", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Reattach alpha channels
        self._reattach_alpha_channels()
        
        # Update the state
        self._update_state("reattach_alpha", "completed")
        self.logger.info("Reattach alpha phase completed")

    def _check_required_files(self):
        """
        Check for required files in the pipeline/30_upscale/textures and pipeline/23_alpha_upscale directories
        """
        # Check for upscaled RGB files
        rgb_dir = os.path.join("files/temp", "30_upscale", "textures")
        if not os.path.exists(rgb_dir) or not os.listdir(rgb_dir):
            return False
        
        # Check for upscaled alpha files
        alpha_dir = os.path.join("files/temp", "23_alpha_upscale")
        if not os.path.exists(alpha_dir) or not os.listdir(alpha_dir):
            return False
        
        # If we have both, we should be good
        return True

    def _reattach_alpha_channels(self):
        """
        Reattach alpha channels to all upscaled RGB images
        """
        # Get input and output directories
        rgb_dir = os.path.join("files/temp", "30_upscale", "textures")
        alpha_dir = os.path.join("files/temp", "23_alpha_upscale")
        output_dir = os.path.join("files/temp", "31_reattach", "textures")
        os.makedirs(output_dir, exist_ok=True)
        
        # Process all PNG files
        processed_count = 0
        for filename in os.listdir(rgb_dir):
            if filename.endswith(".png"):
                rgb_path = os.path.join(rgb_dir, filename)
                alpha_path = os.path.join(alpha_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                # Check if alpha file exists
                if not os.path.exists(alpha_path):
                    self.logger.warning("Alpha file not found for %s, skipping", filename)
                    continue
                
                self.logger.info("Reattaching alpha channel to %s", filename)
                self._combine_rgb_alpha(rgb_path, alpha_path, output_path)
                processed_count += 1
        
        self.logger.info("Processed %d images", processed_count)
        
        # Check if we processed any files
        if processed_count == 0:
            self.logger.warning("No PNG files found in %s", rgb_dir)

    def _combine_rgb_alpha(self, rgb_path, alpha_path, output_path):
        """
        Combine RGB and alpha channels into a single RGBA image
        """
        # Load the RGB image
        rgb_img = Image.open(rgb_path).convert("RGB")
        
        # Load the alpha channel
        alpha_img = Image.open(alpha_path).convert("L")
        
        # Check if the sizes match
        if rgb_img.size != alpha_img.size:
            self.logger.warning("Size mismatch between RGB and alpha for %s. RGB: %s, Alpha: %s", 
                              os.path.basename(rgb_path), rgb_img.size, alpha_img.size)
            # Resize alpha to match RGB size if needed
            alpha_img = alpha_img.resize(rgb_img.size, 1)  # LANCZOS = 1
        
        # Create RGBA image by combining RGB and alpha
        rgba_img = rgb_img.copy()
        rgba_img.putalpha(alpha_img)
        
        # Save the combined image
        rgba_img.save(output_path)
        self.logger.info("Saved combined RGBA image to %s", output_path)