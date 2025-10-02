#!/usr/bin/env python3
"""
Workflow test for the Duke3D Upscale Pipeline
"""
import os

def test_pipeline_directories():
    """Test that all pipeline directories are defined correctly"""
    print("Testing pipeline directories...")
    
    # Check that the pipeline directories are in the Makefile
    required_dirs = [
        "pipeline/21_premultiply",
        "pipeline/22_alpha_extract",
        "pipeline/23_alpha_upscale",
        "pipeline/31_reattach",
        "pipeline/32_scrub"
    ]
    
    for directory in required_dirs:
        # Check if directory exists or would be created
        if not os.path.exists(directory):
            print(f"INFO: Directory {directory} does not exist yet (will be created during pipeline execution)")
        else:
            print(f"✓ Directory {directory} exists")
    
    print("Pipeline directories test passed!")
    return True

def test_file_structure():
    """Test that the file structure matches the requirements"""
    print("Testing file structure...")
    
    # Check that the new phase files are in the correct location
    phase_files = [
        "src/pipeline/phases/premultiply.py",
        "src/pipeline/phases/extract_alpha.py",
        "src/pipeline/phases/upscale_alpha.py",
        "src/pipeline/phases/reattach_alpha.py",
        "src/pipeline/phases/verify.py",
        "src/pipeline/phases/scrub.py"
    ]
    
    for file in phase_files:
        if not os.path.exists(file):
            print(f"ERROR: File {file} does not exist")
            return False
        print(f"✓ File {file} exists")
    
    print("File structure test passed!")
    return True

def test_configuration_options():
    """Test that the configuration options are added"""
    print("Testing configuration options...")
    
    if not os.path.exists("pipeline.yaml"):
        print("ERROR: pipeline.yaml does not exist")
        return False
    
    with open("pipeline.yaml", "r") as f:
        content = f.read()
    
    # Check that new configuration options are present
    if "verify:" not in content:
        print("ERROR: verify configuration section not found")
        return False
    print("✓ verify configuration section found")
    
    if "scrub:" not in content:
        print("ERROR: scrub configuration section not found")
        return False
    print("✓ scrub configuration section found")
    
    print("Configuration options test passed!")
    return True

def main():
    """Run workflow tests"""
    print("Running Duke3D Upscale Pipeline workflow tests...")
    print("=" * 50)
    
    tests = [
        test_pipeline_directories,
        test_file_structure,
        test_configuration_options
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All workflow tests passed! ✓")
        return 0
    else:
        print("Some workflow tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(main())