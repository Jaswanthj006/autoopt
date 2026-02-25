"""AMD CPU performance mode detection module."""

import os
import platform


def detect_amd_cpu() -> tuple[bool, str]:
    """
    Detect if the CPU is an AMD processor.

    Returns:
        (True, cpu_name) if AMD detected, else (False, cpu_name).
    """
    cpu_name = platform.processor() or platform.machine()
    if not cpu_name:
        cpu_name = platform.platform()
    is_amd = "amd" in cpu_name.lower()
    return (is_amd, cpu_name)
