"""
GPU detection for the pipeline
"""
import logging
import subprocess
import sys
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

def get_device_info():
    """
    Get information about the available devices.
    """
    logger = logging.getLogger(__name__)
    if TORCH_AVAILABLE:
        # Get the GPU
        if torch.cuda.is_available():
            logger.info("Detected GPU")
            gpu = {
                "device": "cuda",
                "name": torch.cuda.get_device_name(),
                "count": torch.cuda.device_count(),
                "total": 0,
                "free": 0
            }
            # Add the memory to the GPU
            for i in range(gpu["count"]):
                try:
                    # Get the total memory
                    total = torch.cuda.get_device_properties(i).total_memory
                    # Add the memory to the
                    gpu["total"] = max(gpu["total"], total)
                except Exception as e:
                    logger.warning("Error getting GPU memory: %s", str(e))
        # Set the to the will
        if gpu is None:
            logger.info("No GPU detected, using CPU")
        else:
            logger.info("Using GPU: %s", gpu["device"])
        return gpu
    return None

def get_device_info():
    """
    Get information about the available devices.
    """
    logger = logging.getLogger(__name__)
    if TORCH_AVAILABLE:
        if torch.cuda.is_available():
            logger.info("Detected GPU")
            # Get the device
            device = torch.device("cuda")
            return {
                "device": "cuda",
                "name": torch.cuda.get_device_name(),
                "count": torch.cuda.device_count(),
                "total_memory": 0,
                "free_memory": 0
            }
        else:
            logger.info("No GPU detected, using CPU")
            return {
                "device": "cpu",
                "name": "CPU",
                "count": 1,
                "total_memory": 0,
                "free_memory": 0
            }
    else:
        logger.warning("PyTorch is not available, using CPU")
        return {
            "device": "cpu",
            "name": "CPU",
            "count": 1,
            "total_memory": 0,
            "free_memory": 0
        }