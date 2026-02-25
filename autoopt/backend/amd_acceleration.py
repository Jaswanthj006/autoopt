"""AMD ROCm acceleration detection module."""

import torch


def detect_rocm() -> tuple[bool, str | None]:
    """
    Detect if AMD ROCm is available via CUDA (AMD GPUs using ROCm).

    Returns:
        (True, device_name) if AMD GPU detected, else (False, None).
    """
    try:
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            if "AMD" in device_name or "Radeon" in device_name:
                return True, device_name
        return False, None
    except Exception:
        return False, None
