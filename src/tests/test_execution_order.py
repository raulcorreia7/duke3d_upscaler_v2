#!/usr/bin/env python3
"""
Execution order test for the Duke3D Upscale Pipeline
"""
import os

def test_makefile_help():
    """Test that the Makefile help includes all new phases"""
    print("Testing Makefile help...")
    
    if not os.path.exists("Makefile"):
        print("ERROR: Makefile does not exist")
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
    
    # Check that the help message includes all new phases
    required_help_lines = [
        "premultiply   - Premultiply alpha to prevent pink halos",
        "extract_alpha - Extract alpha channels for separate processing",
        "upscale_alpha - Upscale alpha channels with Lanczos interpolation",
        "reattach_alpha - Reattach alpha to upscaled images",
        "verify        - Check for pink artifacts in upscaled images",
        "scrub         - Remove residual magenta pixels"
    ]
    
    for line in required_help_lines:
        if line not in content:
            print(f"ERROR: Help line '{line}' not found in Makefile")
            return False
        print(f"✓ Help line '{line}' found in Makefile")
    
    print("Makefile help test passed!")
    return True

def test_phase_dependencies():
    """Test that the phase dependencies are correct"""
    print("Testing phase dependencies...")
    
    # Check that the main.py file has the correct phase order
    if not os.path.exists("src/pipeline/main.py"):
        print("ERROR: src/pipeline/main.py does not exist")
        return False
    
    with open("src/pipeline/main.py", "r") as f:
        content = f.read()
    
    # Check that the phase order is correct
    if 'phase_order = ["game_files", "extract", "convert", "premultiply", "extract_alpha", "upscale_alpha", "upscale", "reattach_alpha", "verify", "scrub", "generate_mod"]' not in content:
        print("ERROR: Phase order is not correct in main.py")
        return False
    print("✓ Phase order is correct in main.py")
    
    print("Phase dependencies test passed!")
    return True

def test_clean_target():
    """Test that the clean target includes all new directories"""
    print("Testing clean target...")
    
    if not os.path.exists("Makefile"):
        print("ERROR: Makefile does not exist")
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
    
    # Check that the clean target includes all new directories
    required_clean_dirs = [
        "pipeline/21_premultiply/*",
        "pipeline/22_alpha_extract/*",
        "pipeline/23_alpha_upscale/*",
        "pipeline/31_reattach/*",
        "pipeline/32_scrub/*"
    ]
    
    for directory in required_clean_dirs:
        if directory not in content:
            print(f"ERROR: Directory {directory} not found in clean target")
            return False
        print(f"✓ Directory {directory} found in clean target")
    
    print("Clean target test passed!")
    return True

def main():
    """Run execution order tests"""
    print("Running Duke3D Upscale Pipeline execution order tests...")
    print("=" * 50)
    
    tests = [
        test_makefile_help,
        test_phase_dependencies,
        test_clean_target
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All execution order tests passed! ✓")
        return 0
    else:
        print("Some execution order tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(main())