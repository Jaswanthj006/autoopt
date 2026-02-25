"""Agent module for automatically selecting the fastest code version."""

import cProfile
import hashlib
import io
import os
import pstats
import shutil
import subprocess
import sys

from amd_acceleration import detect_rocm
from amd_cpu_mode import detect_amd_cpu
from ast_optimizer import optimize_with_ast
from executor import run_file
from hardware import get_hardware_info
from optimizer_gpu import create_gpu_version
from optimizer_numba import create_numba_version
from optimizer_parallel import create_parallel_version
from optimizer_vector import create_vector_version

INPUT_FILE = "../test_codes/main_test.py"


def get_output(file_path: str) -> str | None:
    """
    Run a Python file and return its stdout output.
    """
    try:
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return None


def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def analyze_bottleneck(file_path: str) -> None:
    """
    Run cProfile and show bottlenecks without printing user program output.
    """
    try:
        print("\nTop Bottlenecks (cProfile):\n")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "cProfile",
                "-s",
                "cumtime",
                file_path
            ],
            stdout=subprocess.DEVNULL,   # hide user prints
            stderr=subprocess.STDOUT,    # keep profiler output
            check=True
        )

    except Exception as e:
        print(f"Bottleneck analysis failed: {e}")


def run_agent(input_file: str) -> None:
    """
    Generate optimized versions, benchmark them, and create final optimized output file.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.normpath(os.path.join(base_dir, input_file))
    input_path = os.path.abspath(input_path)
    print(f"Running file: {input_path}")

    rocm_available, device = detect_rocm()
    print("\n=== AMD Acceleration Check ===")
    if rocm_available:
        print(f"ROCm Available on: {device}")
        print("Using AMD GPU Acceleration Mode")
    else:
        print("ROCm not available – running on CPU")
    print("===============================\n")
    if rocm_available:
        print("Large workloads can be offloaded to AMD GPU (future support)")

    is_amd, cpu_name = detect_amd_cpu()
    cores = os.cpu_count()
    print("\n=== CPU Detection ===")
    print(f"CPU: {cpu_name}")
    print(f"Cores: {cores}")
    if is_amd:
        print("AMD Performance Mode: Enabled")
        print("Using aggressive parallel optimization")
    else:
        print("AMD Performance Mode: Standard")
    print("=====================\n")

    test_dir = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    optimized_path = os.path.abspath(os.path.join(test_dir, f"{base_name}_optimized.py"))

    os.makedirs(test_dir, exist_ok=True)

    # AST optimization
    ast_path = os.path.join(test_dir, f"{base_name}_ast.py")
    changed, numpy_used = optimize_with_ast(input_path, ast_path)
    if changed:
        print("AST optimization applied")
        input_path = ast_path
    else:
        print("No AST transformations applied")
    if numpy_used:
        print("NumPy detected – consider vectorization")

    best_path = input_path

    original_time = run_file(input_path)
    if original_time is not None:
        print(f"Original execution time: {original_time:.4f}s")
    if original_time is None or original_time < 0.3:
        print("Workload too small – optimization skipped")
        shutil.copy(input_path, optimized_path)
        print("Optimization complete")
        print(f"Output: {optimized_path}")
        try:
            subprocess.run(["code", optimized_path], capture_output=True)
        except Exception:
            pass
        return

    if original_time is not None and original_time >= 1.0:
        print("Heavy workload detected – running bottleneck analysis")
        analyze_bottleneck(input_path)

    light_workload = original_time < 1.0
    if light_workload:
        print("Light workload – running fast mode")

    hardware = get_hardware_info()
    cpu_cores = hardware.get("cpu_cores", 1)
    gpu_type = hardware.get("gpu", "CPU")
    use_parallel = cpu_cores > 2
    if is_amd:
        use_parallel = True
        if (cores or 0) >= 8:
            print("High-core AMD CPU detected – prioritizing multiprocessing")
    use_gpu = gpu_type != "CPU"
    print(f"Hardware: CPU cores={cpu_cores}, GPU={gpu_type}")

    vector_path = os.path.join(test_dir, f"{base_name}_vector.py")
    parallel_path = os.path.join(test_dir, f"{base_name}_parallel.py")
    gpu_path = os.path.join(test_dir, f"{base_name}_gpu.py")
    numba_path = os.path.join(test_dir, f"{base_name}_numba.py")

    try:
        create_vector_version(input_path, vector_path)
        if not light_workload:
            if use_parallel:
                create_parallel_version(input_path, parallel_path)
            if use_gpu:
                create_gpu_version(input_path, gpu_path)
            create_numba_version(input_path, numba_path)
    except Exception as e:
        print(f"Error creating optimized versions: {e}")
        shutil.copy(input_path, optimized_path)
        print("Optimization complete")
        print(f"Output: {optimized_path}")
        try:
            subprocess.run(["code", optimized_path], capture_output=True)
        except Exception:
            pass
        return

    benchmark_list = [("original", input_path), ("vector", vector_path)]
    if not light_workload:
        if use_parallel:
            benchmark_list.append(("parallel", parallel_path))
        if use_gpu:
            benchmark_list.append(("gpu", gpu_path))
        benchmark_list.append(("numba", numba_path))

    results = []
    for name, path in benchmark_list:
        try:
            t = run_file(path)
            if t is not None:
                results.append((t, name, path))
                print(f"{name}: {t:.4f}s")
            else:
                print(f"{name}: failed (ignored)")
        except Exception as e:
            print(f"{name}: error - {e}")

    if not results:
        print("No valid version to select.")
        shutil.copy(input_path, optimized_path)
        print("Optimization complete")
        print(f"Output: {optimized_path}")
        try:
            subprocess.run(["code", optimized_path], capture_output=True)
        except Exception:
            pass
        return

    fastest_time, fastest_name, fastest_path = min(results, key=lambda x: x[0])
    original_time = next((t for t, n, _ in results if n == "original"), None)

    if original_time is not None:
        speedup = original_time / fastest_time
        print(f"Speedup: {speedup:.2f}")
        if speedup < 1.2:
            print("Optimization skipped: improvement too small")
            best_path = input_path
        else:
            best_path = fastest_path
            best_name = fastest_name
            best_time = fastest_time
    else:
        best_path = fastest_path
        best_name = fastest_name
        best_time = fastest_time

    if best_path != input_path:
        print("\nVerifying output correctness...")
        original_output = get_output(input_path)
        optimized_output = get_output(best_path)

        if original_output != optimized_output:
            print("Output mismatch – optimization rejected")
            print("Using original version instead")
            best_path = input_path
        else:
            print("Output verified – optimization is correct")
            print(f"Selected: {best_name} ({best_time:.4f}s)")

    shutil.copy(best_path, optimized_path)
    print("Optimization complete")
    print(f"Output: {optimized_path}")
    try:
        subprocess.run(["code", optimized_path], capture_output=True)
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "../test_codes/main_test.py"

    run_agent(input_file)
