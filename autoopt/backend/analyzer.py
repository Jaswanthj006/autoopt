"""Code analyzer module for detecting loops in Python files."""

import ast


def analyze_code(file_path: str) -> dict:
    """
    Analyze a Python file for loop structure.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        Dictionary with loop_count (number of for loops) and nested_loops (bool).
    """
    with open(file_path, encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    class LoopVisitor(ast.NodeVisitor):
        def __init__(self):
            self.loop_count = 0
            self.loop_depth = 0
            self.nested_loops = False

        def visit_For(self, node):
            self.loop_count += 1
            if self.loop_depth > 0:
                self.nested_loops = True
            self.loop_depth += 1
            self.generic_visit(node)
            self.loop_depth -= 1

    visitor = LoopVisitor()
    visitor.visit(tree)

    return {
        "loop_count": visitor.loop_count,
        "nested_loops": visitor.nested_loops,
    }


if __name__ == "__main__":
    result = analyze_code("../test_codes/test1.py")
    print(result)
