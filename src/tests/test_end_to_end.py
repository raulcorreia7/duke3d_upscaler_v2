#!/usr/bin/env python3
"""
End-to-end tests for the Duke3D Upscale Pipeline
Tests the actual pipeline execution with mock data
"""
import os
import sys
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
import logging

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, project_root)

from src.pipeline.main import main

class EndToEndTest:
    def __init__(self):
        self.test_dir = None
        self.original_dir = os.getcwd()
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Setup logging for tests"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def setup_test_environment(self):
        """Create a temporary test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="duke3d_test_")
        self.logger.info(f"Created test directory: {self.test_dir}")

        # Create project structure in test directory
        dirs_to_create = [
            "src/pipeline",
            "files/input",
            "files/output",
            "files/models",
            "files/soundfonts",
            "files/temp"
        ]

        for dir_path in dirs_to_create:
            full_path = os.path.join(self.test_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)

        # Copy essential files
        self._copy_pipeline_code()
        self._create_config_file()
        self._create_mock_game_files()

    def _copy_pipeline_code(self):
        """Copy pipeline source code to test directory"""
        src_dir = os.path.join(project_root, "src", "pipeline")
        dst_dir = os.path.join(self.test_dir, "src", "pipeline")

        # Create destination directory structure
        os.makedirs(dst_dir, exist_ok=True)
        os.makedirs(os.path.join(dst_dir, "phases"), exist_ok=True)
        os.makedirs(os.path.join(dst_dir, "utils"), exist_ok=True)

        # Copy all Python files
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py'):
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, src_dir)
                    dst_file = os.path.join(dst_dir, rel_path)

                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)

    def _create_config_file(self):
        """Create a test configuration file"""
        config = {
            "version": "2.0",
            "game": {
                "name": "Duke Nukem 3D",
                "supported_formats": ["GRP"],
                "default_palette": "standard"
            },
            "upscale": {
                "model": "realesrgan-x4plus",
                "scale": 2,  # Smaller scale for testing
                "tile_size": 256,
                "device": "cpu",  # Use CPU for testing
                "model_cache_dir": "files/models",
                "alpha_handling": "separate_upscale"
            },
            "audio": {
                "sample_rate": 22050,  # Lower for testing
                "bit_depth": 16,
                "soundfont": "files/soundfonts/test.sf2",
                "soundfont_url": None,  # Skip download for testing
                "preferred_format": "WAV"
            },
            "image": {
                "format": "PNG",
                "premultiply_alpha": True,
                "extract_alpha": True,
                "alpha_upscale_method": "lanczos",
                "compression_level": 9  # Higher compression for smaller test files
            },
            "verification": {
                "pink_threshold": 0.95,
                "magentat_tolerance": 5,
                "min_resolution": 512,  # Lower for testing
                "max_file_size": 1048576,  # 1MB for testing
                "require_alpha": False,
                "alpha_tolerance": 0.1
            },
            "scrub": {
                "remove_magenta": True,
                "magenta_threshold": 240,
                "magenta_fuzz": 10,
                "auto_contrast": False,  # Disable for testing
                "gamma_correction": 1.0
            },
            "output": {
                "mod_dir": "files/output/duke3d",
                "hightile_structure": True,
                "organize_by_type": True,
                "include_metadata": False  # Disable for testing
            },
            "performance": {
                "max_workers": 2,  # Fewer workers for testing
                "max_memory_mb": 1024,  # Less memory for testing
                "gpu_memory_fraction": 0.5,
                "enable_cache": True,
                "cache_dir": "files/temp/cache"
            }
        }

        config_dir = os.path.join(self.test_dir, ".pipeline")
        os.makedirs(config_dir, exist_ok=True)

        with open(os.path.join(config_dir, "config.yaml"), 'w') as f:
            import yaml
            yaml.dump(config, f, default_flow_style=False)

    def _create_mock_game_files(self):
        """Create mock game files for testing"""
        # Create a mock GRP file (just for file detection test)
        mock_grp_path = os.path.join(self.test_dir, "files/input", "DUKE3D.GRP")
        with open(mock_grp_path, 'wb') as f:
            f.write(b"KenSilverman")  # GRP magic number for testing

        # Create a simple test image file that can be processed
        # For now, just create the structure - actual processing tests will be added later

    def test_phase_imports(self):
        """Test that all phases can be imported"""
        self.logger.info("Testing phase imports...")

        phases_to_test = [
            "src.pipeline.phases.base",
            "src.pipeline.phases.game_files",
            "src.pipeline.phases.extract",
            "src.pipeline.phases.convert",
            "src.pipeline.phases.premultiply",
            "src.pipeline.phases.extract_alpha",
            "src.pipeline.phases.upscale_alpha",
            "src.pipeline.phases.upscale",  # This will test our compatibility fix
            "src.pipeline.phases.reattach_alpha",
            "src.pipeline.phases.verify",
            "src.pipeline.phases.scrub",
            "src.pipeline.phases.generate_mod"
        ]

        failed_imports = []

        # Change to test directory
        os.chdir(self.test_dir)

        try:
            for phase in phases_to_test:
                try:
                    __import__(phase)
                    self.logger.info(f"  ✓ {phase}")
                except ImportError as e:
                    failed_imports.append(f"{phase}: {e}")
                    self.logger.error(f"  ✗ {phase}: {e}")

            if failed_imports:
                self.logger.error(f"Failed imports: {failed_imports}")
                return False
            else:
                self.logger.info("All phase imports successful!")
                return True

        finally:
            os.chdir(self.original_dir)

    def test_configuration_loading(self):
        """Test that configuration can be loaded"""
        self.logger.info("Testing configuration loading...")

        config_path = os.path.join(self.test_dir, ".pipeline", "config.yaml")
        if not os.path.exists(config_path):
            self.logger.error("Configuration file not found")
            return False

        try:
            os.chdir(self.test_dir)
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            required_keys = ["version", "game", "upscale", "audio"]
            for key in required_keys:
                if key not in config:
                    self.logger.error(f"Missing required config key: {key}")
                    return False

            self.logger.info("Configuration loaded successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
        finally:
            os.chdir(self.original_dir)

    def cleanup_test_environment(self):
        """Clean up the test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            os.chdir(self.original_dir)
            shutil.rmtree(self.test_dir)
            self.logger.info("Test environment cleaned up")

    def run_all_tests(self):
        """Run all end-to-end tests"""
        self.logger.info("=" * 50)
        self.logger.info("Starting Duke3D Upscale Pipeline End-to-End Tests")

        test_results = []

        try:
            self.setup_test_environment()

            # Test 1: Phase imports
            result = self.test_phase_imports()
            test_results.append(("Phase Imports", result))

            # Test 2: Configuration loading
            result = self.test_configuration_loading()
            test_results.append(("Configuration Loading", result))

        finally:
            self.cleanup_test_environment()

        # Report results
        self.logger.info("=" * 50)
        self.logger.info("Test Results:")
        all_passed = True
        for test_name, result in test_results:
            status = "✓ PASSED" if result else "✗ FAILED"
            self.logger.info(f"  {test_name}: {status}")
            all_passed = all_passed and result

        overall_status = "✓ ALL TESTS PASSED" if all_passed else "✗ SOME TESTS FAILED"
        self.logger.info(f"\nOverall: {overall_status}")

        return all_passed

def main():
    """Main test runner"""
    test_runner = EndToEndTest()
    success = test_runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()