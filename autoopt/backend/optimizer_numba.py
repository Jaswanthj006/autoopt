"""Numba optimizer module for JIT-compiling Python computation."""

import ast


def create_numba_version(input_file: str, output_file: str) -> None:
    """
    Create a Numba-optimized version by wrapping main computation in an @njit function.

    Args:
        input_file: Path to the original Python file.
        output_file: Path to save the modified file (must differ from input_file).
    """
    if input_file == output_file:
        raise ValueError("output_file must differ from input_file to avoid overwriting")

    try:
        with open(input_file, encoding="utf-8") as f:
            source = f.read()
    except OSError:
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    lines = source.splitlines(keepends=True)
    body = tree.body

    imports = []
    rest = []
    for stmt in body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            imports.append(stmt)
        else:
            rest.append(stmt)

    if not rest:
        _write_simple_numba(source, input_file, output_file)
        return

    last = rest[-1]
    return_val = None
    if (
        isinstance(last, ast.Expr)
        and isinstance(last.value, ast.Call)
        and isinstance(last.value.func, ast.Name)
        and last.value.func.id == "print"
        and len(last.value.args) == 1
    ):
        return_val = last.value.args[0]
        rest = rest[:-1]

    if not rest or return_val is None:
        _write_simple_numba(source, input_file, output_file)
        return

    first_lineno = rest[0].lineno
    last_lineno = rest[-1].end_lineno
    body_source = "".join(lines[first_lineno - 1 : last_lineno])
    indented = "".join("    " + line for line in body_source.splitlines(keepends=True))
    return_expr = ast.unparse(return_val)

    import_parts = []
    for stmt in imports:
        seg = ast.get_source_segment(source, stmt)
        if seg:
            import_parts.append(seg + "\n")
    import_src = "".join(import_parts)
    numba_import = "from numba import njit\n\n"
    func_def = f"@njit\ndef compute():\n{indented}    return {return_expr}\n\n"
    result_code = "result = compute()\nprint(result)\n"
    output = import_src + numba_import + func_def + result_code

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
    except OSError:
        return


def _write_simple_numba(source: str, input_file: str, output_file: str) -> None:
    """Add numba import only, no wrapping."""
    if "from numba" not in source and "import numba" not in source:
        src_lines = source.splitlines(keepends=True)
        insert_idx = 0
        if src_lines and src_lines[0].strip().startswith("#!"):
            insert_idx = 1
        src_lines.insert(insert_idx, "from numba import njit\n")
        source = "".join(src_lines)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(source)
    except OSError:
        pass
