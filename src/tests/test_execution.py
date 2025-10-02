#!/usr/bin/env python3
"""
Execution test for the Duke3D Upscale Pipeline
"""
import os
import sys
import subprocess

def test_help_command():
    """Test that the help command works"""
    print("Testing help command...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "src.pipeline.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"ERROR: Help command failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return False
        
        if "Duke3D Upscale Pipeline" not in result.stdout:
            print("ERROR: Help output does not contain expected text")
            return False
        
        print("✓ Help command works")
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: Help command timed out")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run help command: {e}")
        return False

def test_phase_list():
    """Test that all phases are listed in the help"""
    print("Testing phase list...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "src.pipeline.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"ERROR: Help command failed with return code {result.returncode}")
            return False
        
        required_phases = [
            "setup", "game_files", "extract", "convert", "premultiply",
            "extract_alpha", "upscale_alpha", "upscale", "reattach_alpha",
            "verify", "scrub", "generate_mod", "all"
        ]
        
        for phase in required_phases:
            if phase not in result.stdout:
                print(f"ERROR: Phase {phase} not found in help output")
                return False
            print(f"✓ Phase {phase} listed in help")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to check phase list: {e}")
        return False

def main():
    """Run execution tests"""
    print("Running Duke3D Upscale Pipeline execution tests...")
    print("=" * 50)
    
    tests = [
        test_help_command,
        test_phase_list
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("All execution tests passed! ✓")
        return 0
    else:
        print("Some execution tests failed! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())