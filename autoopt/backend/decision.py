"""Decision module for selecting optimization strategies based on profile and hardware."""


def decide_strategy(profile_file: str, hardware_info: dict) -> dict:
    """
    Decide which optimization strategies to apply based on profile and hardware.

    Args:
        profile_file: Path to the profile report.
        hardware_info: Dictionary from get_hardware_info().

    Returns:
        Dictionary with vector, parallel, gpu, numba (each True or False).
    """
    default = {"vector": False, "parallel": False, "gpu": False, "numba": False}

    try:
        with open(profile_file, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return default

    main_module_time = _parse_main_module_time(content)
    if main_module_time is None:
        main_module_time = 0.0

    result = default.copy()

    if main_module_time > 0.2:
        result["vector"] = True
        result["numba"] = True

    cpu_cores = hardware_info.get("cpu_cores", 0) or 0
    if cpu_cores > 4:
        result["parallel"] = True

    gpu = hardware_info.get("gpu", "CPU")
    if gpu != "CPU" and main_module_time > 1.0:
        result["gpu"] = True
    else:
        result["gpu"] = False

    return result


def _parse_main_module_time(content: str) -> float | None:
    """Extract cumulative time for the main script's module from profile output."""
    for line in content.splitlines():
        if "(<module>)" not in line or "frozen" in line or "runpy" in line:
            continue
        parts = line.split()
        floats = []
        for p in parts:
            try:
                floats.append(float(p))
            except ValueError:
                break
        if len(floats) >= 4:
            return floats[3]
    return None
