"""Static check of the package source: ints and Fractions only (no float literal, float() or complex, no math other
than isqrt and gcd, no '/' outside exact.div, no '**' or pow(), no float format specs)."""

import ast
import os
import re
import unittest

PKG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stripes_read_b")
TESTS = os.path.dirname(os.path.abspath(__file__))
BANNED_NAMES = {"float", "complex", "round", "pow"}
BANNED_MODULES = {"numpy", "decimal", "statistics", "cmath", "random"}
MATH_OK = {"isqrt", "gcd"}
FMT = re.compile(r"%[-+ #0]*[0-9]*(\.[0-9]+)?[eEfFgG%]")


def violations(path, allow_div_in=("div",)):
    with open(path, "rb") as f:
        tree = ast.parse(f.read().decode("ascii"), path)
    out = []
    parents = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parents[ch] = node

    def func_of(node):
        while node in parents:
            node = parents[node]
            if isinstance(node, ast.FunctionDef):
                return node.name
        return None

    for node in ast.walk(tree):
        where = "%s:%d" % (os.path.basename(path), getattr(node, "lineno", 0))
        if isinstance(node, ast.Constant) and isinstance(node.value, (float, complex)):
            out.append(where + " float or complex literal")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and FMT.search(node.value):
            out.append(where + " float format in a string")
        if isinstance(node, ast.FormattedValue) and node.format_spec is not None:
            out.append(where + " f-string format spec")
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            out.append(where + " name " + node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "math" \
                and node.attr not in MATH_OK:
            out.append(where + " math." + node.attr)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for n in names:
                if n.split(".")[0] in BANNED_MODULES:
                    out.append(where + " import " + n)
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Div):
            if func_of(node) not in allow_div_in:
                out.append(where + " '/' outside div")
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Pow):
            out.append(where + " '**'")
    return out


class NoFloat(unittest.TestCase):
    def test_package_source(self):
        bad = []
        for nm in sorted(os.listdir(PKG)):
            if nm.endswith(".py"):
                bad += violations(os.path.join(PKG, nm))
        self.assertEqual(bad, [])

    def test_test_source(self):
        bad = []
        for nm in sorted(os.listdir(TESTS)):
            if nm.endswith(".py") and nm != "test_nofloat.py":
                bad += violations(os.path.join(TESTS, nm), allow_div_in=())
        self.assertEqual(bad, [])

    def test_checker_catches(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("import math\nx = 1.5\ny = 3 / 4\nz = float(2)\nw = math.sqrt(2)\nv = 2 ** 3\n")
            p = f.name
        try:
            v = violations(p)
        finally:
            os.unlink(p)
        self.assertEqual(len(v), 5, v)


if __name__ == "__main__":
    unittest.main()
