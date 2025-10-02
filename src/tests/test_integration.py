#!/usr/bin/env python3
"""
Integration test for the Duke3D Upscale Pipeline
"""
import os

def test_makefile_integration():
    """Test that the Makefile integrates all phases correctly"""
    print("Testing Makefile integration...")
    
    if not os.path.exists("Makefile"):
        print("ERROR: Makefile does not exist")
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
    
    # Check that all new targets are in the Makefile
    required_targets = [
        "premultiply",
        "extract_alpha",
        "upscale_alpha",
        "reattach_alpha",
        "verify",
        "scrub"
    ]
    
    for target in required_targets:
        if f"{target}:" not in content:
            print(f"ERROR: Target {target} not found in Makefile")
            return False
        print(f"✓ Target {target} found in Makefile")
    
    # Check that the all target includes all phases
    if "all: game_files extract convert premultiply extract_alpha upscale_alpha upscale reattach_alpha verify scrub generate_mod" not in content:
        print("ERROR: 'all' target does not include all phases")
        return False
    print("✓ 'all' target includes all phases")
    
    # Check that the clean target includes all new directories
    if "pipeline/21_premultiply/*" not in content:
        print("ERROR: Clean target does not include pipeline/21_premultiply")
        return False
    print("✓ Clean target includes pipeline/21_premultiply")
    
    if "pipeline/22_alpha_extract/*" not in content:
        print("ERROR: Clean target does not include pipeline/22_alpha_extract")
        return False
    print("✓ Clean target includes pipeline/22_alpha_extract")
    
    if "pipeline/23_alpha_upscale/*" not in content:
        print("ERROR: Clean target does not include pipeline/23_alpha_upscale")
        return False
    print("✓ Clean target includes pipeline/23_alpha_upscale")
    
    if "pipeline/31_reattach/*" not in content:
        print("ERROR: Clean target does not include pipeline/31_reattach")
        return False
    print("✓ Clean target includes pipeline/31_reattach")
    
    if "pipeline/32_scrub/*" not in content:
        print("ERROR: Clean target does not include pipeline/32_scrub")
        return False
    print("✓ Clean target includes pipeline/32_scrub")
    
    print("Makefile integration test passed!")
    return True

def test_pipeline_order():
    """Test that the pipeline order is correct"""
    print("Testing pipeline order...")
    
    if not os.path.exists("src/pipeline/main.py"):
        print("ERROR: src/pipeline/main.py does not exist")
        return False
    
    with open("src/pipeline/main.py", "r") as f:
        content = f.read()
    
    # Check that the phase order is correct
    if '"game_files", "extract", "convert", "premultiply", "extract_alpha", "upscale_alpha", "upscale", "reattach_alpha", "verify", "scrub", "generate_mod"' not in content:
        print("ERROR: Pipeline order is not correct in main.py")
        return False
    print("✓ Pipeline order is correct in main.py")
    
    print("Pipeline order test passed!")
    return True

def main():
    """Run integration tests"""
    print("Running Duke3D Upscale Pipeline integration tests...")
    print("=" * 50)
    
    tests = [
        test_makefile_integration,
        test_pipeline_order
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All integration tests passed! ✓")
        return 0
    else:
        print("Some integration tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(main())