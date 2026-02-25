"""GPU optimizer module for adding PyTorch device support to Python files."""


def create_gpu_version(input_file: str, output_file: str) -> None:
    """
    Create a version of a Python file with PyTorch GPU/MPS device support.

    Adds torch import and device setup at the top for GPU acceleration.

    Args:
        input_file: Path to the original Python file.
        output_file: Path to save the modified file (must differ from input_file).
    """
    if input_file == output_file:
        raise ValueError("output_file must differ from input_file to avoid overwriting")

    with open(input_file, encoding="utf-8") as f:
        source = f.read()

    lines = source.splitlines(keepends=True)
    insert_idx = 0
    if lines and lines[0].strip().startswith("#!"):
        insert_idx = 1

    header_parts = []
    if "import torch" not in source and "from torch" not in source:
        header_parts.append("import torch\n")
    if "device = torch.device" not in source:
        header_parts.append(
            'device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")\n'
        )

    if header_parts:
        header = "".join(header_parts) + "\n"
        lines.insert(insert_idx, header)
        source = "".join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(source)


if __name__ == "__main__":
    create_gpu_version(
        "../test_codes/test1.py",
        "../test_codes/test1_gpu.py",
    )
