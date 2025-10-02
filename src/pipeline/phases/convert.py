"""
Convert Phase - Convert assets to PNG32, WAV, and frames
"""
import os
import shutil
import subprocess
import logging
from typing import Dict, Any
from tqdm import tqdm
from .base import AbstractPhase
from ..utils.error_handling import (
    safe_subprocess_run, RetryStrategy, ProgressBar,
    log_exceptions, NonRetryableError, ConfigValidator
)
from ..utils.paths import get_paths

class ConvertPhase(AbstractPhase):
    """Convert assets to PNG32, WAV, and frames"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the convert phase
        """
        self.logger.info("Starting convert phase")

        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/10_extract")
            raise FileNotFoundError("Missing required files in files/temp/10_extract")

        # Create the destination directory
        dest_dir = os.path.join("files/temp", "20_convert")
        os.makedirs(dest_dir, exist_ok=True)

        # Convert assets to PNG32
        self._convert_textures()
        self._convert_audio()
        self._convert_animations()

        # Update the state
        self._update_state("convert", "completed")
        self.logger.info("Convert phase completed")

    def _check_required_files(self):
        """
        Check for required files in the files/temp/10_extract directory
        """
        extract_dir = os.path.join("files/temp", "10_extract")
        if not os.path.exists(extract_dir):
            return False

        # Check for files in the directory
        if not os.listdir(extract_dir):
            return False

        # If we have files, we should be good
        return True

    def _convert_textures(self):
        """
        Convert ART to PNG32 with magenta sanitization
        """
        paths = get_paths()

        # Create the output directory
        output_dir = paths.ensure_dir(paths.convert_dir / "textures")
        extract_dir = paths.ensure_dir(paths.extract_dir)

        # Find all art files to process
        art_files = []
        try:
            for filename in os.listdir(extract_dir):
                if filename.endswith(".art") or filename.startswith("TILES"):
                    art_files.append(filename)
        except OSError as e:
            raise NonRetryableError(f"Failed to read extract directory: {str(e)}", phase="convert", cause=e)

        if not art_files:
            self.logger.warning("No ART files found in %s", extract_dir)
            return

        # Process art files with progress bar
        self.logger.info("Converting %d ART files to PNG32...", len(art_files))

        for filename in tqdm(art_files, desc="Converting textures", unit="file"):
            art_path = extract_dir / filename
            self.logger.info("Converting ART file to PNG32 with art2img: %s", filename)

            # Use art2img to convert the files
            art2img_path = paths.art2img_build / "art2img"
            paths.validate_file_exists(art2img_path, "art2img tool")

            # Run the art2img to convert the files with error handling
            try:
                result = safe_subprocess_run(
                    [str(art2img_path), "-i", str(art_path), "-o", str(output_dir)],
                    timeout=300,  # 5 minute timeout
                    logger=self.logger
                )
                self.logger.info("Successfully converted %s", filename)
            except Exception as e:
                self.logger.error("Error converting %s: %s", filename, str(e))
                raise  # Let the decorated method handle the retry logic

        if not self._check_files_exist(output_dir):
            raise RuntimeError("No files were generated in the output directory")

    def _check_files_exist(self, directory: str):
        """
        Check for files in the directory
        """
        return os.path.exists(directory) and len(os.listdir(directory)) > 0

    def _convert_audio(self):
        """
        Convert audio files to WAV
        """
        # Create output directories
        output_dir = os.path.join("files/temp", "20_convert")
        audio_dir = os.path.join(output_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Check for files in the files/temp/10_extract
        extract_dir = os.path.join("files/temp", "10_extract")
        if not os.path.exists(extract_dir):
            return

        # Process audio files
        for file in os.listdir(extract_dir):
            file_path = os.path.join(extract_dir, file)
            if file.endswith(".voc"):
                self._convert_voc(file_path)
            elif file.endswith(".mid"):
                self._convert_mid(file_path)

    def _convert_voc(self, file_path):
        """
        Convert VOC file to WAV
        """
        if not os.path.exists(file_path):
            return

        # Generate output path
        output_dir = os.path.join("files/temp", "20_convert", "audio")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(file_path).replace(".voc", ".wav"))

        # Convert the file to wav
        try:
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-y", output_file],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info("Successfully converted %s to WAV", os.path.basename(file_path))
        except subprocess.CalledProcessError as e:
            self.logger.error("Error converting %s to WAV: %s", file_path, e.stderr)
            raise RuntimeError(f"Failed to convert {file_path} to WAV: {e.stderr}")

    def _convert_mid(self, file_path):
        """
        Convert MID file to WAV
        """
        if not os.path.exists(file_path):
            return

        # Generate output path
        output_dir = os.path.join("files/temp", "20_convert", "audio")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(file_path).replace(".mid", ".wav"))

        # Get soundfont path from config
        soundfont = self.config.get("audio", {}).get("soundfont", "files/soundfonts/Trevor0402_SC-55.sf2")

        # Check if fluidsynth is available
        if not shutil.which("fluidsynth"):
            raise FileNotFoundError("fluidsynth is not installed or not in the PATH")

        # Convert the file to wav
        try:
            result = subprocess.run(
                ["fluidsynth", "-F", output_file, soundfont, file_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info("Successfully converted %s to WAV", os.path.basename(file_path))
        except subprocess.CalledProcessError as e:
            self.logger.error("Error converting %s to WAV: %s", file_path, e.stderr)
            raise RuntimeError(f"Failed to convert {file_path} to WAV: {e.stderr}")

    def _convert_animations(self):
        """
        Convert animation files to PNG frames
        """
        # Create output directory
        output_dir = os.path.join("files/temp", "20_convert", "frames")
        os.makedirs(output_dir, exist_ok=True)

        # Check for files in the files/temp/10_extract
        extract_dir = os.path.join("files/temp", "10_extract")
        if not os.path.exists(extract_dir):
            return

        # Process animation files
        for file in os.listdir(extract_dir):
            file_path = os.path.join(extract_dir, file)
            if file.endswith(".anm"):
                self._convert_anm(file_path)

    def _convert_anm(self, file_path):
        """
        Convert ANM file to PNG frames
        """
        if not os.path.exists(file_path):
            return

        # Generate output directory
        output_dir = os.path.join("files/temp", "20_convert", "frames")
        os.makedirs(output_dir, exist_ok=True)
        # Create a subdirectory for this animation
        anim_name = os.path.splitext(os.path.basename(file_path))[0]
        anim_output_dir = os.path.join(output_dir, anim_name)
        os.makedirs(anim_output_dir, exist_ok=True)

        # Check if ffmpeg is available
        if not shutil.which("ffmpeg"):
            raise FileNotFoundError("ffmpeg is not installed or not in the PATH")

        # Convert the file to PNG frames
        try:
            output_pattern = os.path.join(anim_output_dir, "frame_%04d.png")
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-y", output_pattern],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.logger.info("Successfully converted %s to PNG frames", os.path.basename(file_path))
        except subprocess.CalledProcessError as e:
            self.logger.error("Error converting %s to PNG frames: %s", file_path, e.stderr)
            raise RuntimeError(f"Failed to convert {file_path} to PNG frames: {e.stderr}")