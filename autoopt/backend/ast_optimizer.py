"""AST-based optimizer for Python code."""

import ast


def optimize_with_ast(input_path: str, output_path: str) -> tuple[bool, bool]:
    """
    Optimize Python file using AST transformations.

    Returns:
        changed: True if optimizations were applied
        numpy_used: True if numpy is imported
    """
    with open(input_path, encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    transformer = OptimizerTransformer()
    transformer.visit(tree)
    ast.fix_missing_locations(tree)

    if transformer.changed:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ast.unparse(tree))

    return transformer.changed, transformer.numpy_used


class OptimizerTransformer(ast.NodeTransformer):
    def __init__(self):
        self.changed = False
        self.numpy_used = False

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "numpy" or alias.name.startswith("numpy"):
                self.numpy_used = True
                break
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and (
            node.module == "numpy" or node.module.startswith("numpy.")
        ):
            self.numpy_used = True
        return self.generic_visit(node)

    def visit_Module(self, node):
        new_body = []
        i = 0
        while i < len(node.body):
            if i + 1 < len(node.body):
                sum_replacement = self._try_sum_pattern(node.body[i], node.body[i + 1])
                if sum_replacement is not None:
                    new_body.append(sum_replacement)
                    self.changed = True
                    i += 2
                    continue
                append_replacement = self._try_append_pattern(
                    node.body[i], node.body[i + 1]
                )
                if append_replacement is not None:
                    new_body.append(append_replacement)
                    self.changed = True
                    i += 2
                    continue
            new_body.append(self.visit(node.body[i]))
            i += 1
        node.body = new_body
        return node

    def _try_sum_pattern(self, stmt1, stmt2):
        if not isinstance(stmt1, ast.Assign) or len(stmt1.targets) != 1:
            return None
        target = stmt1.targets[0]
        if not isinstance(target, ast.Name):
            return None
        total_name = target.id
        if not self._is_zero(stmt1.value):
            return None
        if not isinstance(stmt2, ast.For) or len(stmt2.body) != 1:
            return None
        aug = stmt2.body[0]
        if not isinstance(aug, ast.AugAssign):
            return None
        if not isinstance(aug.op, ast.Add):
            return None
        if not isinstance(aug.target, ast.Name) or aug.target.id != total_name:
            return None
        loop_var = stmt2.target
        if not isinstance(loop_var, ast.Name):
            return None
        if not isinstance(aug.value, ast.Name) or aug.value.id != loop_var.id:
            return None
        return ast.Assign(
            targets=[ast.Name(id=total_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="sum", ctx=ast.Load()),
                args=[stmt2.iter],
                keywords=[],
            ),
        )

    def _is_zero(self, node):
        if isinstance(node, ast.Constant):
            return node.value == 0
        return False

    def _try_append_pattern(self, stmt1, stmt2):
        if not isinstance(stmt1, ast.Assign) or len(stmt1.targets) != 1:
            return None
        target = stmt1.targets[0]
        if not isinstance(target, ast.Name):
            return None
        result_name = target.id
        if not isinstance(stmt1.value, ast.List) or stmt1.value.elts:
            return None
        if not isinstance(stmt2, ast.For) or len(stmt2.body) != 1:
            return None
        call = stmt2.body[0]
        if not isinstance(call, ast.Expr) or not isinstance(call.value, ast.Call):
            return None
        call = call.value
        if not isinstance(call.func, ast.Attribute):
            return None
        if call.func.attr != "append" or len(call.args) != 1:
            return None
        if not isinstance(call.func.value, ast.Name):
            return None
        if call.func.value.id != result_name:
            return None
        expr = call.args[0]
        comp = ast.ListComp(
            elt=expr,
            generators=[
                ast.comprehension(
                    target=stmt2.target,
                    iter=stmt2.iter,
                    ifs=[],
                    is_async=0,
                )
            ],
        )
        return ast.Assign(
            targets=[ast.Name(id=result_name, ctx=ast.Store())],
            value=comp,
        )
