"""Hardware info module for detecting system configuration."""

import platform

import psutil
import torch


def get_hardware_info() -> dict:
    """
    Get hardware and environment information.

    Returns:
        Dictionary with os, cpu_cores, ram_gb, and gpu.
    """
    if torch.cuda.is_available():
        gpu = "CUDA"
    elif torch.backends.mps.is_available():
        gpu = "MPS"
    else:
        gpu = "CPU"

    ram_bytes = psutil.virtual_memory().total
    ram_gb = round(ram_bytes / (1024**3), 2)

    return {
        "os": platform.system(),
        "cpu_cores": psutil.cpu_count() or 0,
        "ram_gb": ram_gb,
        "gpu": gpu,
    }


if __name__ == "__main__":
    info = get_hardware_info()
    print(info)
