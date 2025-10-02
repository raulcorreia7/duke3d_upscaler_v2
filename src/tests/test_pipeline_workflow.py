#!/usr/bin/env python3
"""
Pipeline workflow test for the Duke3D Upscale Pipeline
"""
import os

def test_pipeline_phases():
    """Test that all pipeline phases are implemented correctly"""
    print("Testing pipeline phases...")
    
    # Check that the new phase files exist
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
        print(f"✓ Phase file {file} exists")
    
    # Check that the new phase classes are correctly implemented
    phase_classes = [
        ("src/pipeline/phases/premultiply.py", "PremultiplyPhase"),
        ("src/pipeline/phases/extract_alpha.py", "ExtractAlphaPhase"),
        ("src/pipeline/phases/upscale_alpha.py", "UpscaleAlphaPhase"),
        ("src/pipeline/phases/reattach_alpha.py", "ReattachAlphaPhase"),
        ("src/pipeline/phases/verify.py", "VerifyPhase"),
        ("src/pipeline/phases/scrub.py", "ScrubPhase")
    ]
    
    for file, class_name in phase_classes:
        if os.path.exists(file):
            with open(file, "r") as f:
                content = f.read()
            
            if f"class {class_name}" not in content:
                print(f"ERROR: Class {class_name} not found in {file}")
                return False
            print(f"✓ Class {class_name} found in {file}")
    
    print("Pipeline phases test passed!")
    return True

def test_pipeline_integration():
    """Test that the pipeline is integrated correctly"""
    print("Testing pipeline integration...")
    
    # Check that the main.py file has the new imports
    if not os.path.exists("src/pipeline/main.py"):
        print("ERROR: src/pipeline/main.py does not exist")
        return False
    
    with open("src/pipeline/main.py", "r") as f:
        content = f.read()
    
    # Check that the new imports are present
    required_imports = [
        "from .phases.premultiply import PremultiplyPhase",
        "from .phases.extract_alpha import ExtractAlphaPhase",
        "from .phases.upscale_alpha import UpscaleAlphaPhase",
        "from .phases.reattach_alpha import ReattachAlphaPhase",
        "from .phases.verify import VerifyPhase",
        "from .phases.scrub import ScrubPhase"
    ]
    
    for import_line in required_imports:
        if import_line not in content:
            print(f"ERROR: Import line '{import_line}' not found in main.py")
            return False
        print(f"✓ Import line '{import_line}' found in main.py")
    
    # Check that the new phases are in the phases dictionary
    required_phases = [
        '"premultiply": PremultiplyPhase(config, state)',
        '"extract_alpha": ExtractAlphaPhase(config, state)',
        '"upscale_alpha": UpscaleAlphaPhase(config, state)',
        '"reattach_alpha": ReattachAlphaPhase(config, state)',
        '"verify": VerifyPhase(config, state)',
        '"scrub": ScrubPhase(config, state)'
    ]
    
    for phase_line in required_phases:
        if phase_line not in content:
            print(f"ERROR: Phase line '{phase_line}' not found in main.py")
            return False
        print(f"✓ Phase line '{phase_line}' found in main.py")
    
    print("Pipeline integration test passed!")
    return True

def test_makefile_targets():
    """Test that the Makefile targets are implemented correctly"""
    print("Testing Makefile targets...")
    
    if not os.path.exists("Makefile"):
        print("ERROR: Makefile does not exist")
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
    
    # Check that the new targets are present
    required_targets = [
        "premultiply:",
        "extract_alpha:",
        "upscale_alpha:",
        "reattach_alpha:",
        "verify:",
        "scrub:"
    ]
    
    for target in required_targets:
        if target not in content:
            print(f"ERROR: Target '{target}' not found in Makefile")
            return False
        print(f"✓ Target '{target}' found in Makefile")
    
    print("Makefile targets test passed!")
    return True

def main():
    """Run pipeline workflow tests"""
    print("Running Duke3D Upscale Pipeline workflow tests...")
    print("=" * 50)
    
    tests = [
        test_pipeline_phases,
        test_pipeline_integration,
        test_makefile_targets
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All pipeline workflow tests passed! ✓")
        return 0
    else:
        print("Some pipeline workflow tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(main())