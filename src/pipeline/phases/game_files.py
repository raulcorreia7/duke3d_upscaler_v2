"""
Game Files Phase - Detect and copy input game files
"""
import os
import shutil
import subprocess
import logging
from typing import Dict, Any
from pathlib import Path
from .base import AbstractPhase

class GameFilesPhase(AbstractPhase):
    """Detect and copy input game files to files/temp/00_game"""

    def __init__(self, config: Dict[str, Any], state):
        super().__init__(config, state)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        """
        Execute the game files phase
        """
        self.logger.info("Starting game files phase")

        # Check for game files in inputs directory
        game_files = self._detect_game_files()

        if not game_files:
            self.logger.error("No game files found in inputs directory")
            raise FileNotFoundError("No game files found in inputs directory")

# Copy detected files to files/temp/00_game
        self._copy_game_files(game_files)

        self._update_state("game_files", "completed")
        self.logger.info("Game files phase completed")

    def _detect_game_files(self):
        """
        Auto-detect game files in inputs directory
        Priority: duke3d_wt/ > duke3d/ > setup_duke3d*.exe
        """
        inputs_dir = "files/input"
        if not os.path.exists(inputs_dir):
            os.makedirs(inputs_dir)
            self.logger.info("Created inputs directory")

        # Check for World Tour files
        wt_dir = os.path.join(inputs_dir, "duke3d_wt")
        if os.path.exists(wt_dir) and self._check_valid_game_dir(wt_dir):
            self.logger.info("Found World Tour files in duke3d_wt")
            return {"type": "world_tour", "path": wt_dir}

        # Check for regular Duke3D files
        duke_dir = os.path.join(inputs_dir, "duke3d")
        if os.path.exists(duke_dir) and self._check_valid_game_dir(duke_dir):
            self.logger.info("Found regular Duke3D files in duke3d")
            return {"type": "regular", "path": duke_dir}

        # Check for GOG installer
        exe_files = list(Path(inputs_dir).glob("setup_duke3d*.exe"))
        if exe_files:
            self.logger.info("Found GOG installer")
            return {"type": "gog", "path": str(exe_files[0])}

        # If no files, we need to inform the user
        self.logger.info("No game files found in inputs directory")
        return None

    def _check_valid_game_dir(self, directory):
        """
        Check if a directory contains valid game files
        """
        # Check for the main GRP file
        grp_files = list(Path(directory).glob("*.GRP"))
        if grp_files:
            return True
        return False

    def _extract_gog_installer(self, exe_path):
        """
        Extract GOG installer using innoextract
        """
        # Check for innoextract tool
        if not shutil.which("innoextract"):
            raise FileNotFoundError("innoextract is not installed or not in PATH")

        # Extract the GOG installer to the inputs directory
        self.logger.info("Extracting GOG installer: {}".format(exe_path))

# Create a temporary directory
        temp_dir = os.path.join("files/input", "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Run innoextract
        result = subprocess.run(
            ["innoextract", "-q", "-s", "-d", temp_dir, exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError("Failed to extract GOG installer: {}".format(result.stderr))

        # Find the DUKE3D.GRP file in the extracted directory
        grp_files = list(Path(temp_dir).rglob("DUKE3D.GRP"))
        if not grp_files:
            raise FileNotFoundError("DUKE3D.GRP not found in extracted GOG installer")

# Create the game directory in files/input
        game_dir = os.path.join("files/input", "duke3d")
        os.makedirs(game_dir, exist_ok=True)

        # Copy the GRP file to the game directory
        shutil.copy(grp_files[0], os.path.join(game_dir, "DUKE3D.GRP"))
        self.logger.info("Extracted GOG installer to duke3d")
        return game_dir

    def _copy_game_files(self, game_files):
        """
        Copy game files to pipeline/00_game
        """
# Create the destination directory
        dest_dir = os.path.join("files/temp", "00_game")
        os.makedirs(dest_dir, exist_ok=True)

        # Check if the game files have already been copied
        if self._check_files_exist(dest_dir):
            self.logger.info("Game files already copied to pipeline/00_game")
            return

        source = game_files["path"]
        if game_files["type"] == "gog":
            # Extract GOG installer
            self.logger.info("Extracting GOG installer")
            source = self._extract_gog_installer(source)

        # Clean the destination directory
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

# Copy the files to the files/temp/00_game directory
        if os.path.isfile(source):
            # If source is a file, copy it to files/temp/00_game
            shutil.copy(source, os.path.join(dest_dir, os.path.basename(source)))
        else:
            # If source is a directory, copy its contents to files/temp/00_game
            for item in os.listdir(source):
                item_path = os.path.join(source, item)
                if os.path.isfile(item_path):
                    # Copy the file to the files/temp/00_game
                    shutil.copy(item_path, os.path.join(dest_dir, item))
                elif os.path.isdir(item_path):
                    # Copy the directory to the files/temp/00_game
                    shutil.copytree(item_path, os.path.join(dest_dir, item))

        # Verify that the files are copied
        if not self._check_files_exist(dest_dir):
            raise FileNotFoundError("Failed to copy game files to pipeline/00_game")
        self.logger.info("Game files copied to pipeline/00_game")

    def _check_files_exist(self, directory):
        """
        Check for the presence of the files
        """
        # Check for the files in the directory
        if os.path.exists(directory) and os.listdir(directory):
            return True
        return False