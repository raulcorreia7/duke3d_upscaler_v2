#!/usr/bin/env python3
"""
Phase test for the Duke3D Upscale Pipeline
"""
import os

def test_phase_files():
    """Test that all phase files exist and have the correct structure"""
    print("Testing phase files...")
    
    # Check that all required phase files exist
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
            print(f"ERROR: Phase file {file} does not exist")
            return False
        print(f"✓ {file} exists")
    
    # Check that the new phases are in the main.py file
    if os.path.exists("src/pipeline/main.py"):
        with open("src/pipeline/main.py", "r") as f:
            main_content = f.read()
        
        required_imports = [
            "phases.premultiply",
            "phases.extract_alpha",
            "phases.upscale_alpha",
            "phases.reattach_alpha",
            "phases.verify",
            "phases.scrub"
        ]
        
        for import_name in required_imports:
            if import_name not in main_content:
                print(f"ERROR: Import {import_name} not found in main.py")
                return False
            print(f"✓ Import {import_name} found in main.py")
    
    print("Phase files test passed!")
    return True

def test_phase_classes():
    """Test that all phase classes exist"""
    print("Testing phase classes...")
    
    # Check that the new phases have the correct class names
    phase_info = [
        ("src/pipeline/phases/premultiply.py", "PremultiplyPhase"),
        ("src/pipeline/phases/extract_alpha.py", "ExtractAlphaPhase"),
        ("src/pipeline/phases/upscale_alpha.py", "UpscaleAlphaPhase"),
        ("src/pipeline/phases/reattach_alpha.py", "ReattachAlphaPhase"),
        ("src/pipeline/phases/verify.py", "VerifyPhase"),
        ("src/pipeline/phases/scrub.py", "ScrubPhase")
    ]
    
    for file, class_name in phase_info:
        if os.path.exists(file):
            with open(file, "r") as f:
                content = f.read()
            
            if class_name not in content:
                print(f"ERROR: Class {class_name} not found in {file}")
                return False
            print(f"✓ Class {class_name} found in {file}")
    
    print("Phase classes test passed!")
    return True

def main():
    """Run phase tests"""
    print("Running Duke3D Upscale Pipeline phase tests...")
    print("=" * 50)
    
    tests = [
        test_phase_files,
        test_phase_classes
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All phase tests passed! ✓")
        return 0
    else:
        print("Some phase tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(main())