"""
Upscale Phase - Apply AI upscaling using Real-ESRGAN
"""
import os
import logging
from typing import Dict, Any
import numpy as np
from PIL import Image
import cv2
import torch
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
from tqdm import tqdm

from .base import AbstractPhase
from ..utils.gpu import get_device_info
from ..utils.model import download_model
from ..utils.compatibility import ensure_torchvision_compatibility
from ..utils.error_handling import (
    retry_on_exception, RetryStrategy, ProgressBar,
    log_exceptions, RetryableError, NonRetryableError,
    ConfigValidator
)


class UpscalePhase(AbstractPhase):
    """Apply AI upscaling using Real-ESRGAN"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.upscale_config = config.get("upscale", {})
        self.model_name = self.upscale_config.get("model", "realesrgan-x4plus")
        self.scale = ConfigValidator.ensure_positive(self.upscale_config.get("scale", 4), "scale")
        self.tile_size = ConfigValidator.ensure_positive(self.upscale_config.get("tile_size", 512), "tile_size")

        # Ensure torchvision compatibility before importing Realesrgan
        ensure_torchvision_compatibility()

    @log_exceptions("upscale")
    @retry_on_exception(max_attempts=3, delay=2.0, strategy=RetryStrategy.EXPONENTIAL,
                      exceptions=(OSError, IOError, RuntimeError))
    def run(self):
        """Execute the upscale phase"""
        self.logger.info("Starting upscale phase")

        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/20_convert")
            raise NonRetryableError("Missing required files in files/temp/20_convert", phase="upscale")

        # Download the model if needed
        self._download_model()

        # Load the model with retry logic
        upsampler = self._load_model()

        # Create output directory
        output_dir = os.path.join("files/temp", "30_upscale")
        ConfigValidator.ensure_directory_exists(output_dir, "output directory", create=True)

        # Upscale textures with progress tracking
        self._upscale_textures(upsampler)

        # Update the state
        self._update_state("upscale", "completed")
        self.logger.info("Upscale phase completed")

    @log_exceptions("upscale")
    @retry_on_exception(max_attempts=3, delay=5.0, strategy=RetryStrategy.EXPONENTIAL,
                      exceptions=(IOError, RuntimeError, torch.cuda.OutOfMemoryError))
    def _download_model(self):
        """Download the Real-ESRGAN model if needed"""
        model_dir = os.path.join("models")
        ConfigValidator.ensure_directory_exists(model_dir, "model directory", create=True)
        model_path = os.path.join(model_dir, f"{self.model_name}.pth")

        # Download the model with retry
        download_model(self.model_name, model_path, self.config)

        # Check if the model was downloaded
        if not os.path.exists(model_path):
            raise NonRetryableError(f"Model file not found at {model_path}", phase="upscale")

    @log_exceptions("upscale")
    @retry_on_exception(max_attempts=3, delay=3.0, strategy=RetryStrategy.EXPONENTIAL,
                      exceptions=(OSError, IOError, RuntimeError))
    def _load_model(self):
        """Load the Real-ESRGAN model"""
        # Get device information
        device_info = get_device_info()
        device = device_info["device"] if device_info else "cpu"
        self.logger.info("Using device: %s", device)

        # Get model path and validate
        model_path = os.path.join("models", f"{self.model_name}.pth")
        if not os.path.exists(model_path):
            raise NonRetryableError(f"Model file not found at {model_path}", phase="upscale")

        # Load the model based on the model name
        if self.model_name == "realesrgan-x4plus":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        elif self.model_name == "realesrgan-x4plus-anime":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        else:
            raise NonRetryableError(f"Unsupported model: {self.model_name}", phase="upscale")

        # Create the upsampler with error handling
        try:
            upsampler = RealESRGANer(
                scale=self.scale,
                model_path=model_path,
                dni_weight=None,
                model=model,
                tile=self.tile_size,
                tile_pad=10,
                pre_pad=0,
                half=False,
                device=device,
            )
            return upsampler
        except Exception as e:
            raise RetryableError(f"Failed to create upsampler: {str(e)}", phase="upscale", cause=e)

    def _check_required_files(self):
        """
        Check for required files in the pipeline/20_convert directory
        """
        convert_dir = os.path.join("files/temp", "20_convert")
        if not os.path.exists(convert_dir):
            return False
        
        # Check for textures directory
        textures_dir = os.path.join(convert_dir, "textures")
        if not os.path.exists(textures_dir):
            return False
        
        # Check for files in the directory
        if not os.listdir(textures_dir):
            return False
        
        # If we have files, we should be good
        return True

    def _download_model(self):
        """
        Download the Real-ESRGAN model if needed
        """
        model_dir = os.path.join("models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"{self.model_name}.pth")
        
        # Download the model
        download_model(self.model_name, model_path, self.config)
        
        # Check if the model was downloaded
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

    def _load_model(self):
        """
        Load the Real-ESRGAN model
        """
        # Get device information
        device_info = get_device_info()
        device = device_info["device"] if device_info else "cpu"
        self.logger.info("Using device: %s", device)
        
        # Get model path
        model_path = os.path.join("models", f"{self.model_name}.pth")
        
        # Load the model based on the model name
        if self.model_name == "realesrgan-x4plus":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        elif self.model_name == "realesrgan-x4plus-anime":
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
        
        # Create the upsampler
        upsampler = RealESRGANer(
            scale=self.scale,
            model_path=model_path,
            dni_weight=None,
            model=model,
            tile=self.tile_size,
            tile_pad=10,
            pre_pad=0,
            half=False,
            device=device,
        )
        
        return upsampler

    @log_exceptions("upscale")
    def _upscale_textures(self, upsampler):
        """Upscale all textures using Real-ESRGAN with retry logic"""
        # Get input and output directories with validation
        input_dir = os.path.join("files/temp", "20_convert", "textures")
        ConfigValidator.ensure_directory_exists(input_dir, "input texture directory")

        output_dir = os.path.join("files/temp", "30_upscale")
        ConfigValidator.ensure_directory_exists(output_dir, "output directory", create=True)

        # Get list of PNG files to process
        try:
            png_files = [f for f in os.listdir(input_dir) if f.endswith(".png")]
        except OSError as e:
            raise NonRetryableError(f"Failed to read input directory {input_dir}: {str(e)}", phase="upscale", cause=e)

        if not png_files:
            self.logger.warning("No PNG files found in %s", input_dir)
            return

        # Process all PNG files with progress tracking and retry logic
        progress_bar = ProgressBar(len(png_files), "Upscaling textures", self.logger)
        failed_files = []
        successful_files = []

        for filename in png_files:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            try:
                # Use retry logic for the image upscaling
                self._upscale_image_with_retry(input_path, output_path, upsampler, filename)
                successful_files.append(filename)
                progress_bar.update(1, file_description=filename)
            except Exception as e:
                failed_files.append((filename, str(e)))
                self.logger.error("Failed to upscale %s: %s", filename, str(e))
                progress_bar.update(1, file_description=f"Failed: {filename}")
                continue

        progress_bar.finish(success=len(failed_files) == 0)

        # Report summary
        if failed_files:
            self.logger.warning(f"Completed with {len(failed_files)} failed files:")
            for filename, error in failed_files[:5]:  # Show first 5 errors
                self.logger.warning(f"  - {filename}: {error}")
            if len(failed_files) > 5:
                self.logger.warning(f"  ... and {len(failed_files) - 5} more")
        else:
            self.logger.info(f"Successfully upscaled all {len(successful_files)} textures")

    @log_exceptions("upscale")
    @retry_on_exception(max_attempts=2, delay=1.0, strategy=RetryStrategy.FIXED,
                      exceptions=(OSError, IOError, RuntimeError, cv2.error))
    def _upscale_image_with_retry(self, input_path, output_path, upsampler, filename):
        """Upscale a single image with retry logic"""
        # Validate input file
        if not os.path.exists(input_path):
            raise NonRetryableError(f"Input file not found: {input_path}", phase="upscale")

        # Check if output already exists (skip if so)
        if os.path.exists(output_path):
            self.logger.debug(f"Skipping {filename}, output already exists")
            return

        self._upscale_image(input_path, output_path, upsampler)

    def _upscale_image(self, input_path, output_path, upsampler):
        """
        Upscale a single image using Real-ESRGAN with optimized alpha channel handling
        """
        # Load image with OpenCV for better alpha channel handling
        bgr_img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)

        if bgr_img is None:
            raise ValueError(f"Failed to load image: {input_path}")

        # Check if the image has an alpha channel
        has_alpha = bgr_img.shape[2] == 4 if len(bgr_img.shape) == 3 else False

        if has_alpha:
            # Split into BGR and alpha channels
            bgr_channels = bgr_img[:, :, :3]
            alpha_channel = bgr_img[:, :, 3]

            # Convert BGR to RGB for Real-ESRGAN
            rgb_channels = cv2.cvtColor(bgr_channels, cv2.COLOR_BGR2RGB)

            # Upscale RGB channels using Real-ESRGAN
            rgb_upscaled, _ = upsampler.enhance(rgb_channels, outscale=self.scale)

            # Upscale alpha channel using Lanczos interpolation for better quality
            # This is more efficient than converting to 3-channel and using Real-ESRGAN
            target_size = tuple(int(dim * self.scale) for dim in alpha_channel.shape[::-1])
            alpha_upscaled = cv2.resize(
                alpha_channel,
                target_size,
                interpolation=cv2.INTER_LANCZOS4
            )

            # Convert RGB back to BGR for OpenCV
            bgr_upscaled = cv2.cvtColor(rgb_upscaled, cv2.COLOR_RGB2BGR)

            # Merge BGR and alpha channels
            upscaled_img = cv2.merge([bgr_upscaled[:, :, 0],
                                    bgr_upscaled[:, :, 1],
                                    bgr_upscaled[:, :, 2],
                                    alpha_upscaled])
        else:
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)

            # Upscale the image
            upscaled_rgb, _ = upsampler.enhance(rgb_img, outscale=self.scale)

            # Convert back to BGR
            upscaled_img = cv2.cvtColor(upscaled_rgb, cv2.COLOR_RGB2BGR)

        # Save the upscaled image
        if has_alpha:
            # Use PNG to preserve alpha channel
            cv2.imwrite(output_path, upscaled_img, [cv2.IMWRITE_PNG_COMPRESSION, 6])
        else:
            cv2.imwrite(output_path, upscaled_img)

        self.logger.info("Saved upscaled image to %s", output_path)