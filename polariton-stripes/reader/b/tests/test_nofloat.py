"""Source scan of the live stage B (the owner's ruling of 2026-11-09): ints and checked integer pairs (qint.py) only.

Strict rules, for every .py of reader/b (the package, the tests, e2e.py, run_b.py, run_tests.py, this file too):
  - no import of fractions, decimal, math, numpy, or of statistics, cmath, random, json, pickle, marshal, importlib,
    ctypes, scipy, mpmath, sympy;
  - no call or name float, complex, round, pow, eval, exec, compile, __import__;
  - no float or complex literal;
  - no true division, '/' or '/=', anywhere (qint.div divides);
  - no '**';
  - no attribute __truediv__, __rtruediv__, __itruediv__, __float__, __complex__, __round__, fromhex,
    as_integer_ratio, truediv, itruediv;
  - no f-string format spec and no float percent-format in a string;
  - a struct call takes a literal format with no float code (e, f, d).
The looser rules for reader/check and reader/sabotage (no_float.sh) allow math.isqrt, math.gcd and fractions there."""

import ast
import os
import re
import unittest

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(B, "stripes_read_b")
TESTS = os.path.join(B, "tests")
STRICT_MODULES = {"fractions", "decimal", "math", "numpy", "statistics", "cmath", "random", "json", "pickle",
                  "marshal", "importlib", "ctypes", "scipy", "mpmath", "sympy"}
LOOSE_MODULES = {"decimal", "numpy", "statistics", "cmath", "random"}
STRICT_NAMES = {"float", "complex", "round", "pow", "eval", "exec", "compile", "__import__"}
LOOSE_NAMES = {"float", "complex", "round", "pow"}
BAD_ATTRS = {"__truediv__", "__rtruediv__", "__itruediv__", "__float__", "__complex__", "__round__", "fromhex",
             "as_integer_ratio", "truediv", "itruediv"}
MATH_OK = {"isqrt", "gcd"}
STRUCT_CALLS = {"pack", "pack_into", "unpack", "unpack_from", "iter_unpack", "calcsize", "Struct"}
FMT = re.compile(r"%[-+ #0]*[0-9]*(\.[0-9]+)?[eEfFgG%]")
LITERAL_TYPES = ("float", "complex")


def violations(path, strict=True, allow_div_in=()):
    """The findings of one file: strict for stage B, loose (allow_div_in names functions where '/' may stand) for the
    checker and the sabotage suite."""
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

    modules = STRICT_MODULES if strict else LOOSE_MODULES
    names = STRICT_NAMES if strict else LOOSE_NAMES
    for node in ast.walk(tree):
        where = "%s:%d" % (os.path.basename(path), getattr(node, "lineno", 0))
        if isinstance(node, ast.Constant) and type(node.value).__name__ in LITERAL_TYPES:
            out.append(where + " float or complex literal")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and FMT.search(node.value):
            out.append(where + " float format in a string")
        if isinstance(node, ast.FormattedValue) and node.format_spec is not None:
            out.append(where + " f-string format spec")
        if isinstance(node, ast.Name) and node.id in names:
            out.append(where + " name " + node.id)
        if isinstance(node, ast.Attribute) and node.attr in BAD_ATTRS:
            out.append(where + " attribute " + node.attr)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "math" \
                and (strict or node.attr not in MATH_OK):
            out.append(where + " math." + node.attr)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for n in mods:
                if n.split(".")[0] in modules:
                    out.append(where + " import " + n)
            if isinstance(node, ast.ImportFrom) and node.module == "math" and not strict:
                out += [where + " from math import " + a.name for a in node.names if a.name not in MATH_OK]
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Div):
            if strict or func_of(node) not in allow_div_in:
                out.append(where + " true division '/'")
        if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Pow):
            out.append(where + " '**'")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in STRUCT_CALLS \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "struct":
            fmt = node.args[0] if node.args else None
            if not (isinstance(fmt, ast.Constant) and isinstance(fmt.value, str)):
                out.append(where + " struct format the source does not show")
            elif set(fmt.value) & set("efd"):
                out.append(where + " struct float code")
    return out


def stage_b_files():
    """Every .py of the live stage B: the package, the tests, e2e.py, run_b.py and run_tests.py."""
    out = []
    for d in (B, PKG, TESTS):
        out += [os.path.join(d, nm) for nm in sorted(os.listdir(d)) if nm.endswith(".py")]
    return out


# One plant of each kind the ruling names, and the extra kinds; each must be found (the self-test of the scan).
PLANTS = (
    ("from fractions import Fraction\n", "import fractions"),
    ("import fractions\n", "import fractions"),
    ("import decimal\n", "import decimal"),
    ("from decimal import Decimal\n", "import decimal"),
    ("import math\nx = math.isqrt(4)\n", "import math"),
    ("from math import gcd\n", "import math"),
    ("import numpy\n", "import numpy"),
    ("x = float(2)\n", "name float"),
    ("x = round(7)\n", "name round"),
    ("x = complex(1)\n", "name complex"),
    ("x = 1" + ".5\n", "float or complex literal"),
    ("x = 1e" + "9\n", "float or complex literal"),
    ("x = 2" + "j\n", "float or complex literal"),
    ("x = 3 " + "/ 4\n", "true division"),
    ("x = 3\nx " + "/= 4\n", "true division"),
    ("x = (1)." + "__truediv__(2)\n", "attribute __truediv__"),
    ("x = 2 *" + "* 3\n", "'**'"),
    ("x = pow(2, 3)\n", "name pow"),
    ("import struct\nx = struct.unpack('<" + "d', b)\n", "struct float code"),
    ("import json\n", "import json"),
    ("x = ev" + "al('1')\n", "name eval"),
    ("x = '%" + ".3f' % 1\n", "float format in a string"),
)


class NoFloat(unittest.TestCase):
    def test_live_stage_b(self):
        bad = []
        files = stage_b_files()
        self.assertGreaterEqual(len(files), 30)
        for p in files:
            bad += violations(p)
        self.assertEqual(bad, [])

    def test_scan_finds_every_plant(self):
        import tempfile

        d = tempfile.mkdtemp(prefix="stripes-b-nofloat-")
        try:
            for k, (text, want) in enumerate(PLANTS):
                p = os.path.join(d, "plant%d.py" % k)
                with open(p, "w") as f:
                    f.write(text)
                found = violations(p)
                self.assertTrue(any(want in v for v in found), (text, want, found))
            p = os.path.join(d, "clean.py")
            with open(p, "w") as f:
                f.write("import struct\nx = 7 // 2\ny = struct.unpack('<qQ', bytes(16))\ns = '1.5'  # 0.5\n")
            self.assertEqual(violations(p), [])
        finally:
            for nm in os.listdir(d):
                os.unlink(os.path.join(d, nm))
            os.rmdir(d)

    def test_loose_rules_of_the_checker(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("import math\nfrom fractions import Fraction\nx = math.isqrt(4)\ny = math.sqrt(2)\n")
            p = f.name
        try:
            v = violations(p, strict=False)
        finally:
            os.unlink(p)
        self.assertEqual([x.split(" ", 1)[1] for x in v], ["math.sqrt"], v)


if __name__ == "__main__":
    unittest.main()
