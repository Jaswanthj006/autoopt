"""Profiler module for analyzing Python file execution."""

import cProfile
import os
import pstats
import runpy


def profile_file(file_path: str) -> str | None:
    """
    Profile a Python file and save top 10 functions by cumulative time.

    Args:
        file_path: Path to the Python file to profile.

    Returns:
        Path of the profile output file, or None on error.
    """
    try:
        abs_path = os.path.abspath(file_path)
        profiler = cProfile.Profile()
        profiler.enable()
        runpy.run_path(abs_path, run_name="__main__")
        profiler.disable()

        dir_path = os.path.dirname(abs_path)
        base_name = os.path.splitext(os.path.basename(abs_path))[0]
        output_path = os.path.join(dir_path, f"{base_name}_profile.txt")

        with open(output_path, "w", encoding="utf-8") as f:
            ps = pstats.Stats(profiler, stream=f)
            ps.sort_stats("cumulative")
            ps.print_stats(10)

        return output_path
    except Exception:
        return None
