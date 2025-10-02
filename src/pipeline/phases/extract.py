"""
Extract Phase - Extract game files to files/temp/10_extract
"""
import os
import shutil
import subprocess
import logging
import tempfile
from typing import Dict, Any
from .base import AbstractPhase

class ExtractPhase(AbstractPhase):
    """Extract game files to files/temp/10_extract using kextract"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the extract phase
        """
        self.logger.info("Starting extract phase")

        # Check for required files
        if not self._check_required_files():
            self.logger.error("Missing required files in files/temp/00_game")
            raise FileNotFoundError("Missing required files in files/temp/00_game")

        # Extract game files using kextract
        self._extract_files()

        self._update_state("extract", "completed")
        self.logger.info("Extract phase completed")

    def _check_required_files(self):
        """
        Check for required files in the files/temp/00_game directory
        """
        # Check for the main GRP file
        game_dir = os.path.join("files/temp", "00_game")
        if not os.path.exists(game_dir):
            return False

        # Look for a .GRP file
        for file in os.listdir(game_dir):
            if file.endswith(".GRP"):
                return True

        # If no .GRP file, check for files in the directory
        if os.listdir(game_dir):
            return True

        # If no files, return False
        return False

    def _extract_files(self):
        """
        Extract game files using kextract
        """
        # Check for kextract tool
        kextract_path = os.path.join("tools", "build", "eduke32", "kextract")
        if not os.path.exists(kextract_path):
            # Try alternative path
            kextract_path = os.path.join("tools", "eduke32", "kextract")
            if not os.path.exists(kextract_path):
                raise FileNotFoundError("kextract tool not found. Please run 'make setup' first.")

        # Find the GRP file in the 00_game directory
        game_dir = os.path.join("files/temp", "00_game")
        grp_files = [f for f in os.listdir(game_dir) if f.endswith(".GRP")]
        if not grp_files:
            raise FileNotFoundError("No .GRP file found in files/temp/00_game")

        grp_file = grp_files[0]
        grp_path = os.path.join(game_dir, grp_file)

        # Create the output directory
        output_dir = os.path.join("files/temp", "10_extract")
        os.makedirs(output_dir, exist_ok=True)

        # Run kextract to extract the files
        self.logger.info("Extracting %s to %s", grp_file, output_dir)
        result = subprocess.run(
            [kextract_path, grp_path, output_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError("Failed to extract files: {}".format(result.stderr))

        # Verify that files were extracted
        if not self._check_files_exist(output_dir):
            raise FileNotFoundError("Failed to extract files to files/temp/10_extract")

        self.logger.info("Files extracted successfully to files/temp/10_extract")

    def _check_files_exist(self, directory):
        """
        Check for the presence of the files
        """
        # Check for the files in the directory
        if os.path.exists(directory) and os.listdir(directory):
            return True
        return False