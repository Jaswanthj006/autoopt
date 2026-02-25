AutoOpt – Automatic Python Performance Optimizer

Overview

AutoOpt is a tool that automatically improves the performance of Python programs.
It analyzes a Python script, generates multiple optimized versions using different techniques, and selects the fastest one while ensuring the output remains correct.

The goal is to reduce the time and effort developers spend on manual performance tuning.


---

Problem

Improving Python performance is time-consuming and requires expertise.
Developers usually try only one optimization method and may not explore all available options.
Manual tuning becomes difficult, especially for large or compute-heavy programs.


---

Solution

AutoOpt automates the optimization process:

Measures original execution time

Detects hardware (CPU cores, GPU availability)

Runs bottleneck analysis for heavy workloads

Generates optimized versions using:

Vectorization

Multi-core parallel execution

Numba JIT compilation

GPU (when available)


Benchmarks all versions

Verifies output correctness

Saves the fastest version as
<filename>_optimized.py



---

Key Features

Fully automatic optimization

Hardware-aware decisions

Multi-core and JIT acceleration

Built-in profiling (cProfile)

Output validation for safety

Works from terminal or VS Code



---

How to Run

cd backend
python3 agent.py ../test_codes/example.py

Optimized file will be created:

example_optimized.py


---

Impact

Saves developer time

Improves execution speed automatically

Reduces resource usage

Helps developers focus on building features instead of tuning performance
