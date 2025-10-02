"""
Compatibility utilities for handling dependency version issues
"""

def fix_torchvision_compatibility():
    """
    Fix torchvision compatibility issues for Real-ESRGAN
    """
    import sys
    import warnings

    try:
        # Try to import the old style first to see if it fails
        from torchvision.transforms.functional_tensor import rgb_to_grayscale
    except ImportError:
        # If it fails, we need to fix the compatibility
        try:
            # Find the basicsr degradations module and fix the import
            import basicsr.data.degradations
            import os

            # Get the path to the degradations file
            degradations_path = basicsr.data.degradations.__file__

            # Read the file content
            with open(degradations_path, 'r') as f:
                content = f.read()

            # Check if our fix is already applied
            if "from torchvision.transforms.functional import rgb_to_grayscale" in content:
                # Fix is already applied
                return True

            # Replace the problematic import
            old_import = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
            new_import = """try:
    from torchvision.transforms.functional_tensor import rgb_to_grayscale
except ImportError:
    from torchvision.transforms.functional import rgb_to_grayscale"""

            content = content.replace(old_import, new_import)

            # Write back the fixed content
            with open(degradations_path, 'w') as f:
                f.write(content)

            warnings.warn("Fixed torchvision compatibility in basicsr. Consider using a compatible version.")
            return True

        except Exception as e:
            warnings.warn(f"Failed to fix torchvision compatibility: {e}")
            return False

    return True

def ensure_torchvision_compatibility():
    """
    Ensure torchvision compatibility before importing Real-ESRGAN
    """
    return fix_torchvision_compatibility()