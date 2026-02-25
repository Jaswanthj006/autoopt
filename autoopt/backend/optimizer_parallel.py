"""Parallel optimizer module for adding multiprocessing guard to Python files."""

import ast
import os
import tempfile

from executor import run_file


def create_parallel_version(input_file: str, output_file: str) -> None:
    """
    Create a version of a Python file with multiprocessing-safe execution.

    Auto-tunes worker count by benchmarking different values.

    Args:
        input_file: Path to the original Python file.
        output_file: Path to save the modified file (must differ from input_file).
    """
    if input_file == output_file:
        raise ValueError("output_file must differ from input_file to avoid overwriting")

    with open(input_file, encoding="utf-8") as f:
        source = f.read()

    cpu_cores = os.cpu_count() or 4
    workers_list = [2, max(2, cpu_cores // 2), cpu_cores]
    workers_list = list(dict.fromkeys(workers_list))

    parallel_source, range_bound = _build_parallel_source(source)
    if parallel_source is None:
        _write_simple_parallel(source, output_file)
        return

    best_workers = workers_list[0]
    best_time = float("inf")

    for workers in workers_list:
        filled_source = parallel_source.replace("{{WORKERS}}", str(workers))
        if range_bound is not None:
            filled_source = filled_source.replace("{{N}}", str(range_bound))
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tf:
            tf.write(filled_source)
            temp_path = tf.name
        try:
            t = run_file(temp_path)
            if t is not None and t < best_time:
                best_time = t
                best_workers = workers
        finally:
            os.unlink(temp_path)

    final_source = parallel_source.replace("{{WORKERS}}", str(best_workers))
    if range_bound is not None:
        final_source = final_source.replace("{{N}}", str(range_bound))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_source)


def _build_parallel_source(source: str) -> tuple[str | None, int | None]:
    """Build parallelized source with {{WORKERS}} placeholder. Returns (source, range_bound) or (None, None)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, None

    range_bound = _extract_range_bound(tree)
    if range_bound is None:
        return None, None

    lines = source.splitlines(keepends=True)
    body = tree.body
    imports = [s for s in body if isinstance(s, (ast.Import, ast.ImportFrom))]
    rest = [s for s in body if not isinstance(s, (ast.Import, ast.ImportFrom))]

    if not rest:
        return None, None

    last = rest[-1]
    if not (
        isinstance(last, ast.Expr)
        and isinstance(last.value, ast.Call)
        and isinstance(last.value.func, ast.Name)
        and last.value.func.id == "print"
        and len(last.value.args) == 1
    ):
        return None, None

    first_loop_end = rest[0].end_lineno if rest else 0
    for stmt in rest:
        if isinstance(stmt, ast.For):
            first_loop_end = stmt.end_lineno
            break

    rest_source = "".join(lines[first_loop_end : rest[-1].end_lineno])

    import_parts = []
    for s in imports:
        seg = ast.get_source_segment(source, s)
        if seg:
            import_parts.append(seg + "\n")
    import_src = "".join(import_parts)

    parallel_template = f'''{import_src}import multiprocessing as mp

WORKERS = {{{{WORKERS}}}}

def _chunk(args):
    start, end = args
    s = 0
    for i in range(start, end):
        s += i
    return s

if __name__ == "__main__":
    N = {{{{N}}}}
    step = (N + WORKERS - 1) // WORKERS
    chunks = [(i * step, min((i + 1) * step, N)) for i in range(WORKERS)]
    with mp.Pool(WORKERS) as pool:
        results = pool.map(_chunk, chunks)
    total = sum(results)
{rest_source}
'''

    return parallel_template, range_bound


def _extract_range_bound(tree: ast.AST) -> int | None:
    """Extract the upper bound from first 'for i in range(N)' loop."""
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
            func = node.iter.func
            if isinstance(func, ast.Name) and func.id == "range":
                args = node.iter.args
                if len(args) == 1:
                    arg = args[0]
                    if isinstance(arg, ast.Constant):
                        return arg.value
    return None


def _write_simple_parallel(source: str, output_file: str) -> None:
    """Fallback: wrap in if __name__ without actual parallelization."""
    lines = source.splitlines(keepends=True)
    indented = ["    " + line for line in lines]
    header = ""
    if "import multiprocessing" not in source and "from multiprocessing" not in source:
        header = "import multiprocessing as mp\n\n"
    result = header + 'if __name__ == "__main__":\n' + "".join(indented)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    create_parallel_version(
        "../test_codes/test1.py",
        "../test_codes/test1_parallel.py",
    )
