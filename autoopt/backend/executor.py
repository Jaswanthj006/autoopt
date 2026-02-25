"""Executor module for running Python files and measuring execution time."""

import subprocess
import sys
import time


def run_file(file_path: str) -> float | None:
    """
    Run Python file and return execution time (real wall time).
    """
    try:
        start = time.time()
        subprocess.run(
            [sys.executable, file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        end = time.time()
        return end - start
    except Exception:
        return None


if __name__ == "__main__":
    result = run_file("../test_codes/test1.py")
    print(result)
