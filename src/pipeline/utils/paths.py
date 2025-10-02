"""
Path utilities using pathlib for modern path handling
"""
import os
from pathlib import Path
from typing import Union, List
import logging


class ProjectPaths:
    """Centralized path management for the Duke3D Upscale Pipeline"""

    def __init__(self, base_dir: Union[str, Path] = None):
        """
        Initialize project paths

        Args:
            base_dir: Base directory of the project (defaults to current working directory)
        """
        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir.resolve()
        self.logger = logging.getLogger(__name__)

        # Ensure we're in the project root
        self._ensure_project_root()

        # Define all paths using pathlib
        self.files = self.base_dir / "files"
        self.src = self.base_dir / "src"
        self.tools = self.base_dir / "tools"
        self.vendor = self.base_dir / "vendor"
        self.docs = self.base_dir / "docs"

        # Files subdirectories
        self.input_dir = self.files / "input"
        self.output_dir = self.files / "output"
        self.models_dir = self.files / "models"
        self.soundfonts_dir = self.files / "soundfonts"
        self.temp_dir = self.files / "temp"

        # Pipeline working directories
        self.game_files_dir = self.temp_dir / "00_game"
        self.extract_dir = self.temp_dir / "10_extract"
        self.convert_dir = self.temp_dir / "20_convert"
        self.upscale_dir = self.temp_dir / "30_upscale"
        self.premultiply_dir = self.temp_dir / "01_premultiply"
        self.extract_alpha_dir = self.temp_dir / "02_extract_alpha"
        self.upscale_alpha_dir = self.temp_dir / "21_upscale_alpha"
        self.reattach_alpha_dir = self.temp_dir / "31_reattach"

        # Tool paths
        self.tools_build = self.tools / "build"
        self.eduke32_build = self.tools_build / "eduke32"
        self.art2img_build = self.tools_build / "art2img"

        # Configuration
        self.config_dir = self.base_dir / ".pipeline"
        self.config_file = self.config_dir / "config.yaml"
        self.state_file = self.config_dir / "state.json"

    def _ensure_project_root(self):
        """Ensure we're at the project root by checking for key files/directories"""
        indicators = [
            self.base_dir / "src",
            self.base_dir / "Makefile",
            self.base_dir / "pyproject.toml"
        ]

        if not all(indicator.exists() for indicator in indicators):
            self.logger.warning("Some project root indicators are missing from %s", self.base_dir)

    # Directory creation utilities
    def ensure_dir(self, path: Union[str, Path], create: bool = True) -> Path:
        """
        Ensure a directory exists

        Args:
            path: Directory path as string or Path
            create: Whether to create the directory if it doesn't exist

        Returns:
            Path object for the directory
        """
        path_obj = Path(path)
        if create and not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
        elif not path_obj.exists():
            raise FileNotFoundError(f"Directory does not exist: {path_obj}")
        return path_obj

    def get_output_paths(self) -> dict:
        """Get a dictionary of common output paths for mod generation"""
        return {
            "mod_dir": self.output_dir / "duke3d",
            "textures_dir": self.output_dir / "duke3d" / "hightile" / "textures",
            "audio_dir": self.output_dir / "duke3d" / "hightile" / "audio",
            "models_dir": self.output_dir / "duke3d" / "hightile" / "models"
        }

    # File finding utilities
    def find_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """
        Find files matching a pattern in a directory

        Args:
            directory: Directory to search
            pattern: Glob pattern (default: "*")

        Returns:
            List of matching Path objects
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        return list(dir_path.glob(pattern))

    def find_art_files(self, directory: Union[str, Path] = None) -> List[Path]:
        """
        Find ART files in a directory

        Args:
            directory: Directory to search (defaults to extract_dir)

        Returns:
            List of ART file Path objects
        """
        if directory is None:
            directory = self.extract_dir
        return self.find_files(directory, "*.art")

    def find_png_files(self, directory: Union[str, Path] = None) -> List[Path]:
        """
        Find PNG files in a directory

        Args:
            directory: Directory to search (defaults to convert_dir)

        Returns:
            List of PNG file Path objects
        """
        if directory is None:
            directory = self.convert_dir / "textures"
        return self.find_files(directory, "*.png")

    # Path validation utilities
    def validate_file_exists(self, path: Union[str, Path], description: str = "File") -> Path:
        """
        Validate that a file exists and return Path object

        Args:
            path: File path as string or Path
            description: Description for error messages

        Returns:
            Path object for the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"{description} not found: {path_obj}")
        if not path_obj.is_file():
            raise ValueError(f"{description} is not a file: {path_obj}")
        return path_obj

    def validate_dir_exists(self, path: Union[str, Path], description: str = "Directory") -> Path:
        """
        Validate that a directory exists and return Path object

        Args:
            path: Directory path as string or Path
            description: Description for error messages

        Returns:
            Path object for the directory

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"{description} not found: {path_obj}")
        if not path_obj.is_dir():
            raise ValueError(f"{description} is not a directory: {path_obj}")
        return path_obj

    # Convenience methods for common operations
    def get_output_file_path(self, input_file: Union[str, Path], output_dir: Union[str, Path]) -> Path:
        """
        Get output file path for processing

        Args:
            input_file: Input file path
            output_dir: Output directory

        Returns:
            Path for output file with same name as input
        """
        input_path = Path(input_file)
        output_path = Path(output_dir)
        return output_path / input_path.name

    def get_relative_path(self, path: Union[str, Path], base: Union[str, Path] = None) -> Path:
        """
        Get relative path from a base directory

        Args:
            path: Path to make relative
            base: Base directory (defaults to project root)

        Returns:
            Relative path
        """
        path_obj = Path(path)
        base_dir = Path(base) if base else self.base_dir
        return path_obj.relative_to(base_dir)

    # String representation methods
    def __str__(self) -> str:
        return f"ProjectPaths(base_dir={self.base_dir})"

    def __repr__(self) -> str:
        return f"ProjectPaths(base_dir='{self.base_dir}')"


# Global instance for convenient access
_default_paths = None

def get_paths() -> ProjectPaths:
    """Get the default ProjectPaths instance"""
    global _default_paths
    if _default_paths is None:
        _default_paths = ProjectPaths()
    return _default_paths


def set_base_directory(base_dir: Union[str, Path]):
    """Set a custom base directory for the default paths instance"""
    global _default_paths
    _default_paths = ProjectPaths(base_dir)


# Backward compatibility functions for existing code
def to_path(path: Union[str, Path]) -> Path:
    """Convert string or Path to Path object"""
    return Path(path)


def ensure_dir(path: Union[str, Path], create: bool = True) -> Path:
    """
    Backward compatibility function for ensuring directory exists
    """
    paths = get_paths()
    return paths.ensure_dir(path, create)


def validate_file(path: Union[str, Path], description: str = "File") -> Path:
    """
    Backward compatibility function for file validation
    """
    paths = get_paths()
    return paths.validate_file_exists(path, description)


def safe_filename(filename: str) -> str:
    """
    Make a filename safe for all operating systems
    """
    import re
    # Remove invalid characters and replace with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length and avoid reserved names (Windows)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename or "unnamed_file"


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Get a hash of a file for comparison purposes
    """
    import hashlib
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hash_md5 = hashlib.md5()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_directory_size(path: Union[str, Path]) -> int:
    """
    Get total size of a directory in bytes
    """
    directory = Path(path)
    total_size = 0
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size