"""Vector optimizer module for creating NumPy-optimized versions of Python files."""


def create_vector_version(input_file: str, output_file: str) -> None:
    """
    Create an optimized version of a Python file with vectorization support.

    Adds 'import numpy as np' at the top if not already present.

    Args:
        input_file: Path to the original Python file.
        output_file: Path to save the modified file (must differ from input_file).
    """
    if input_file == output_file:
        raise ValueError("output_file must differ from input_file to avoid overwriting")

    with open(input_file, encoding="utf-8") as f:
        source = f.read()

    numpy_import = "import numpy as np"
    if "import numpy" not in source and "from numpy" not in source:
        lines = source.splitlines(keepends=True)
        insert_idx = 0
        if lines and lines[0].strip().startswith("#!"):
            insert_idx = 1
        lines.insert(insert_idx, numpy_import + "\n")
        source = "".join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(source)


if __name__ == "__main__":
    create_vector_version("../test_codes/test1.py", "../test_codes/test1_vector.py")
