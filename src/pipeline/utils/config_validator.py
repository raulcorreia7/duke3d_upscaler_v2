"""
Comprehensive configuration validation for the Duke3D Upscale Pipeline
"""
import os
import yaml
import logging
from typing import Dict, Any, List, Union
from pathlib import Path

from .error_handling import ConfigurationError


class ConfigValidator:
    """
    Comprehensive configuration validator for the pipeline configuration
    """

    # Required sections at the top level
    REQUIRED_SECTIONS = [
        "version",
        "game",
        "upscale",
        "audio",
        "image"
    ]

    # Valid AI models
    VALID_UPSCALE_MODELS = [
        "realesrgan-x4plus",
        "realesrgan-x4plus-anime",
        "realesrgan-x2plus",
        "realesrgan-x2plus-anime"
    ]

    # Valid alpha upscaling methods
    VALID_ALPHA_UPSCALE_METHODS = [
        "lanczos",
        "bicubic",
        "nearest"
    ]

    # Valid image formats
    VALID_IMAGE_FORMATS = [
        "PNG",
        "JPG",
        "JPEG",
        "WEBP",
        "TIFF"
    ]

    def __init__(self, config_path: str = None):
        """
        Initialize validator

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_and_load(self, config_path: str) -> Dict[str, Any]:
        """
        Load and validate configuration from file

        Args:
            config_path: Path to the configuration file

        Returns:
            Validated configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")

        self.validate_config(config)
        return config

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate pipeline configuration and return list of errors

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of validation error messages

        Raises:
            ConfigurationError: If validation fails with critical errors
        """
        errors = []

        # Check required sections
        for section in self.REQUIRED_SECTIONS:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate each section if it exists
        if "version" in config:
            self._validate_version(config["version"], errors)

        if "game" in config:
            self._validate_game(config["game"], errors)

        if "upscale" in config:
            self._validate_upscale(config["upscale"], errors)

        if "audio" in config:
            self._validate_audio(config["audio"], errors)

        if "image" in config:
            self._validate_image(config["image"], errors)

        if "verification" in config:
            self._validate_verification(config["verification"], errors)

        if "scrub" in config:
            self._validate_scrub(config["scrub"], errors)

        if "output" in config:
            self._validate_output(config["output"], errors)

        if "performance" in config:
            self._validate_performance(config["performance"], errors)

        if "logging" in config:
            self._validate_logging(config["logging"], errors)

        if "development" in config:
            self._validate_development(config["development"], errors)

        if errors:
            raise ConfigurationError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))

        return errors

    def _validate_version(self, version: Any, errors: List[str]):
        """Validate version section"""
        if not isinstance(version, str):
            errors.append("version must be a string")

    def _validate_game(self, game: Any, errors: List[str]):
        """Validate game section"""
        if not isinstance(game, dict):
            errors.append("game section must be a dictionary")
            return

        if "name" in game and not isinstance(game["name"], str):
            errors.append("game.name must be a string")

        if "supported_formats" in game:
            if not isinstance(game["supported_formats"], list):
                errors.append("game.supported_formats must be a list")
            else:
                valid_formats = {"GRP", "exe", "data"}
                for fmt in game["supported_formats"]:
                    if fmt not in valid_formats:
                        errors.append(f"Invalid game format: {fmt}")

    def _validate_upscale(self, upscale: Any, errors: List[str]):
        """Validate upscale section"""
        if not isinstance(upscale, dict):
            errors.append("upscale section must be a dictionary")
            return

        # Validate model
        if "model" not in upscale:
            errors.append("Missing upscale.model")
        elif upscale["model"] not in self.VALID_UPSCALE_MODELS:
            errors.append(f"Invalid upscale.model: {upscale['model']}. Valid options: {', '.join(self.VALID_UPSCALE_MODELS)}")

        # Validate scale
        if "scale" not in upscale:
            errors.append("Missing upscale.scale")
        elif not isinstance(upscale["scale"], (int, float)) or upscale["scale"] <= 0:
            errors.append("upscale.scale must be a positive number")
        elif upscale["scale"] not in [2, 4, 8]:
            self.logger.warning(f"Unusual scale factor: {upscale['scale']}. Expected: 2, 4, or 8")

        # Validate tile_size
        if "tile_size" in upscale:
            if not isinstance(upscale["tile_size"], int) or upscale["tile_size"] <= 0:
                errors.append("upscale.tile_size must be a positive integer")
            elif upscale["tile_size"] < 64:
                self.logger.warning(f"Small tile size: {upscale['tile_size']}. This may cause performance issues.")
            elif upscale["tile_size"] > 1024:
                self.logger.warning(f"Large tile size: {upscale['tile_size']}. This may cause memory issues.")

        # Validate device
        if "device" in upscale and upscale["device"] not in ["auto", "cpu", "cuda", "mps"]:
            errors.append(f"Invalid upscale.device: {upscale['device']}. Valid options: auto, cpu, cuda, mps")

        # Validate model_cache_dir
        if "model_cache_dir" in upscale:
            self._validate_directory_path(upscale["model_cache_dir"], "upscale.model_cache_dir", errors, create=True)

        # Validate alpha_handling
        if "alpha_handling" in upscale and upscale["alpha_handling"] not in ["separate_upscale", "premultiplied"]:
            errors.append(f"Invalid upscale.alpha_handling: {upscale['alpha_handling']}. Valid options: separate_upscale, premultiplied")

    def _validate_audio(self, audio: Any, errors: List[str]):
        """Validate audio section"""
        if not isinstance(audio, dict):
            errors.append("audio section must be a dictionary")
            return

        # Validate sample_rate
        if "sample_rate" in audio:
            if not isinstance(audio["sample_rate"], int) or audio["sample_rate"] <= 0:
                errors.append("audio.sample_rate must be a positive integer")
            elif audio["sample_rate"] not in [22050, 44100, 48000]:
                self.logger.warning(f"Unusual sample rate: {audio['sample_rate']}. Expected: 22050, 44100, or 48000")

        # Validate bit_depth
        if "bit_depth" in audio:
            if not isinstance(audio["bit_depth"], int) or audio["bit_depth"] not in [16, 24, 32]:
                errors.append("audio.bit_depth must be 16, 24, or 32")

        # Validate soundfont
        if "soundfont" in audio:
            self._validate_file_path(audio["soundfont"], "audio.soundfont", errors, optional=True)

        # Validate preferred_format
        if "preferred_format" in audio and audio["preferred_format"] not in ["WAV", "FLAC", "MP3", "OGG"]:
            errors.append(f"Invalid audio.preferred_format: {audio['preferred_format']}. Valid options: WAV, FLAC, MP3, OGG")

    def _validate_image(self, image: Any, errors: List[str]):
        """Validate image section"""
        if not isinstance(image, dict):
            errors.append("image section must be a dictionary")
            return

        # Validate format
        if "format" in image and image["format"] not in self.VALID_IMAGE_FORMATS:
            errors.append(f"Invalid image.format: {image['format']}. Valid options: {', '.join(self.VALID_IMAGE_FORMATS)}")

        # Validate boolean settings
        for bool_setting in ["premultiply_alpha", "extract_alpha"]:
            if bool_setting in image and not isinstance(image[bool_setting], bool):
                errors.append(f"image.{bool_setting} must be a boolean")

        # Validate alpha_upscale_method
        if "alpha_upscale_method" in image and image["alpha_upscale_method"] not in self.VALID_ALPHA_UPSCALE_METHODS:
            errors.append(f"Invalid image.alpha_upscale_method: {image['alpha_upscale_method']}. Valid options: {', '.join(self.VALID_ALPHA_UPSCALE_METHODS)}")

        # Validate compression_level
        if "compression_level" in image:
            if not isinstance(image["compression_level"], int) or image["compression_level"] < 0 or image["compression_level"] > 9:
                errors.append("image.compression_level must be an integer between 0 and 9")

    def _validate_verification(self, verification: Any, errors: List[str]):
        """Validate verification section"""
        if not isinstance(verification, dict):
            errors.append("verification section must be a dictionary")
            return

        # Validate numeric settings
        for numeric_setting in ["pink_threshold", "min_resolution", "max_file_size", "alpha_tolerance"]:
            if numeric_setting in verification:
                if not isinstance(verification[numeric_setting], (int, float)) or verification[numeric_setting] <= 0:
                    errors.append(f"verification.{numeric_setting} must be a positive number")

        # Validate boolean settings
        for bool_setting in ["require_alpha"]:
            if bool_setting in verification and not isinstance(verification[bool_setting], bool):
                errors.append(f"verification.{bool_setting} must be a boolean")

    def _validate_scrub(self, scrub: Any, errors: List[str]):
        """Validate scrub section"""
        if not isinstance(scrub, dict):
            errors.append("scrub section must be a dictionary")
            return

        # Validate numeric settings
        for numeric_setting in ["magenta_threshold", "magenta_fuzz", "gamma_correction"]:
            if numeric_setting in scrub:
                if not isinstance(scrub[numeric_setting], (int, float)) or scrub[numeric_setting] < 0:
                    errors.append(f"scrub.{numeric_setting} must be a non-negative number")

        # Validate boolean settings
        for bool_setting in ["remove_magenta", "auto_contrast"]:
            if bool_setting in scrub and not isinstance(scrub[bool_setting], bool):
                errors.append(f"scrub.{bool_setting} must be a boolean")

    def _validate_output(self, output: Any, errors: List[str]):
        """Validate output section"""
        if not isinstance(output, dict):
            errors.append("output section must be a dictionary")
            return

        # Validate mod_dir
        if "mod_dir" in output:
            self._validate_directory_path(output["mod_dir"], "output.mod_dir", errors, create=True)

        # Validate boolean settings
        for bool_setting in ["hightile_structure", "organize_by_type", "include_metadata"]:
            if bool_setting in output and not isinstance(output[bool_setting], bool):
                errors.append(f"output.{bool_setting} must be a boolean")

    def _validate_performance(self, performance: Any, errors: List[str]):
        """Validate performance section"""
        if not isinstance(performance, dict):
            errors.append("performance section must be a dictionary")
            return

        # Validate numeric settings
        for numeric_setting in ["max_workers", "max_memory_mb", "gpu_memory_fraction"]:
            if numeric_setting in performance:
                if not isinstance(performance[numeric_setting], (int, float)) or performance[numeric_setting] <= 0:
                    errors.append(f"performance.{numeric_setting} must be a positive number")
                elif numeric_setting == "max_workers" and performance[numeric_setting] > 32:
                    errors.append("performance.max_workers should not exceed 32")
                elif numeric_setting == "gpu_memory_fraction" and performance[numeric_setting] > 1.0:
                    errors.append("performance.gpu_memory_fraction should not exceed 1.0")

        # Validate boolean settings
        for bool_setting in ["enable_cache"]:
            if bool_setting in performance and not isinstance(performance[bool_setting], bool):
                errors.append(f"performance.{bool_setting} must be a boolean")

        # Validate cache_dir
        if "cache_dir" in performance:
            self._validate_directory_path(performance["cache_dir"], "performance.cache_dir", errors, create=True)

    def _validate_logging(self, logging_config: Any, errors: List[str]):
        """Validate logging section"""
        if not isinstance(logging_config, dict):
            errors.append("logging section must be a dictionary")
            return

        # Validate level
        if "level" in logging_config and logging_config["level"] not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append(f"Invalid logging.level: {logging_config['level']}. Valid options: DEBUG, INFO, WARNING, ERROR")

        # Validate Boolean settings
        for bool_setting in ["log_to_file", "console_output", "verbose"]:
            if bool_setting in logging_config and not isinstance(logging_config[bool_setting], bool):
                errors.append(f"logging.{bool_setting} must be a boolean")

        # Validate log_file
        if "log_file" in logging_config:
            if not isinstance(logging_config["log_file"], str):
                errors.append("logging.log_file must be a string")

    def _validate_development(self, development: Any, errors: List[str]):
        """Validate development section"""
        if not isinstance(development, dict):
            errors.append("development section must be a dictionary")
            return

        # Validate Boolean settings
        for bool_setting in ["debug", "dry_run", "test_mode", "force"]:
            if bool_setting in development and not isinstance(development[bool_setting], bool):
                errors.append(f"development.{bool_setting} must be a boolean")

    def _validate_file_path(self, path: str, setting_name: str, errors: List[str], optional: bool = False):
        """Validate file path"""
        if not isinstance(path, str):
            errors.append(f"{setting_name} must be a string")
            return

        if optional and not path:
            return

        # For development mode, allow missing files
        if not os.path.exists(path):
            self.logger.warning(f"{setting_name} file does not exist: {path}")

    def _validate_directory_path(self, path: str, setting_name: str, errors: List[str], create: bool = False):
        """Validate directory path"""
        if not isinstance(path, str):
            errors.append(f"{setting_name} must be a string")
            return

        if os.path.exists(path) and not os.path.isdir(path):
            errors.append(f"{setting_name} exists but is not a directory: {path}")
        elif not os.path.exists(path) and create:
            try:
                os.makedirs(path, exist_ok=True)
                self.logger.info(f"Created directory: {path}")
            except OSError as e:
                errors.append(f"Failed to create {setting_name} directory '{path}': {e}")


def validate_config_file(config_path: str) -> Dict[str, Any]:
    """
    Convenience function to validate a configuration file

    Args:
        config_path: Path to configuration file

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigurationError: If validation fails
    """
    validator = ConfigValidator()
    return validator.validate_and_load(config_path)