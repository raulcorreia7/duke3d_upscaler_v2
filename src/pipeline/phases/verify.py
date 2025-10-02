"""
Verification Phase - Check for pink artifacts in the upscaled images
"""
import os
import logging
from typing import Dict, Any
import numpy as np
from PIL import Image

from .base import AbstractPhase


class VerifyPhase(AbstractPhase):
    """Check for pink artifacts in the upscaled images"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tolerance = config.get("verify", {}).get("pink_tolerance", 0.08)

    def run(self):
        """
        Execute the verification phase
        """
        self.logger.info("Starting verification phase")
        
        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/output/31_reattach/textures")
            raise FileNotFoundError("Missing required files in files/output/31_reattach/textures")
        
        # Verify images
        issues = self._verify_images()
        
        # If we found issues, raise an error
        if issues:
            error_msg = f"Found {len(issues)} images with pink artifacts:\n"
            for issue in issues:
                error_msg += f"  - {issue}\n"
            self.logger.error(error_msg)
            raise RuntimeError("Pink artifacts detected in upscaled images")
        
        # Update the state
        self._update_state("verify", "completed")
        self.logger.info("Verification phase completed - no pink artifacts found")

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

    def _verify_images(self):
        """
        Verify all images for pink artifacts
        """
        # Get input directory
        input_dir = os.path.join("files", "output", "31_reattach", "textures")
        
        # Process all PNG files
        issues = []
        for filename in os.listdir(input_dir):
            if filename.endswith(".png"):
                input_path = os.path.join(input_dir, filename)
                
                self.logger.info("Verifying %s for pink artifacts", filename)
                if self._check_pink_halos(input_path):
                    issues.append(filename)
        
        # Check if we processed any files
        if not os.listdir(input_dir):
            self.logger.warning("No PNG files found in %s", input_dir)
        
        return issues

    def _check_pink_halos(self, image_path):
        """
        Check for pink halos in a single image
        """
        # Load the image
        img = Image.open(image_path)
        
        # Check if the image has an alpha channel
        if img.mode != "RGBA":
            # No alpha channel, no pink halos possible
            return False
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Separate RGB and alpha channels
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]
        
        # Find pixels where alpha = 0
        zero_alpha_mask = alpha == 0
        
        # For pixels where alpha = 0, check if RGB != (0,0,0)
        if np.any(zero_alpha_mask):
            # Get RGB values for pixels where alpha = 0
            zero_alpha_rgb = rgb[zero_alpha_mask]
            
            # Check if any of these pixels have non-zero RGB values
            # We use a tolerance to account for floating point errors
            non_zero_rgb = np.any(zero_alpha_rgb > (self.tolerance * 255))
            
            if non_zero_rgb:
                # Check if any pixels are pink/magenta
                # Pink/magenta has high red and blue values, low green values
                red_channel = zero_alpha_rgb[:, 0]
                green_channel = zero_alpha_rgb[:, 1]
                blue_channel = zero_alpha_rgb[:, 2]
                
                # Check for pink pixels (high red and blue, low green)
                pink_mask = (red_channel > (self.tolerance * 255)) & (blue_channel > (self.tolerance * 255)) & (green_channel < ((1 - self.tolerance) * 255))
                
                if np.any(pink_mask):
                    pink_count = np.sum(pink_mask)
                    self.logger.warning("Found %d pink pixels in %s", pink_count, os.path.basename(image_path))
                    return True
        
        return False