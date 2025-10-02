#!/usr/bin/env python3
"""
Run all tests for the Duke3D Upscale Pipeline
"""
import os
import sys
import subprocess

def run_test_script(script_name):
    """Run a test script and return the result"""
    print(f"Running {script_name}...")

    try:
        result = subprocess.run(
            ["python", script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60  # Longer timeout for end-to-end tests
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: {script_name} timed out")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run {script_name}: {e}")
        return False

def main():
    """Run all test scripts"""
    print("Running all Duke3D Upscale Pipeline tests...")
    print("=" * 50)

    # Get project root directory
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(tests_dir))

    # List of test scripts - they're in the tests directory but run from project root
    test_scripts = [
        "test_pipeline.py",
        "test_end_to_end.py",
        "test_phases.py",
        "test_integration.py"
    ]

    # Store original directory
    original_dir = os.getcwd()

    all_passed = True
    for script in test_scripts:
        script_path = os.path.join(tests_dir, script)

        # Change to project root for tests that need it
        os.chdir(project_root)

        try:
            if not run_test_script(script_path):
                all_passed = False
        finally:
            # Restore working directory
            os.chdir(original_dir)
        print()

    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())