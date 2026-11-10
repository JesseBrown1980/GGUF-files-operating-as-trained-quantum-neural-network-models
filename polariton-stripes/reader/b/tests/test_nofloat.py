"""Source scan of the live stage B (the owner's ruling of 2026-11-09): ints and checked integer pairs (qint.py) only.

Strict rules, for every .py of reader/b (the package, the tests, e2e.py, run_b.py, run_tests.py, this file too):
  - no import of fractions, decimal, math, numpy, or of statistics, cmath, random, json, pickle, marshal, importlib,
    ctypes, scipy, mpmath, sympy, operator, array, time, datetime, tomllib, builtins;
  - no call or name float, complex, round, pow, eval, exec, compile, __import__, format, __builtins__;
  - no float or complex literal;
  - no true division, '/' or '/=', anywhere (qint.div divides);
  - no '**';
  - no attribute __truediv__, __rtruediv__, __itruediv__, __float__, __complex__, __round__, fromhex,
    as_integer_ratio, truediv, itruediv, pow, __pow__, __rpow__, __ipow__, float, cast, literal_eval,
    float_info, timestamp, st_mtime, st_atime, st_ctime, getmtime, modules;
  - getattr only called, with a str constant as its name, and that name none of the attributes or names above;
  - no f-string format spec, no float percent-format in a string (with a mapping key, '*' width or precision too),
    and no brace format spec of type e, E, f, F, g, G or % in a string (str.format, format());
  - a struct call takes a literal format with no float code (e, f, d), through the module, an alias of it, or a
    name imported from it; no `from struct import *`.
The looser rules for reader/check and reader/sabotage (no_float.sh) allow math.isqrt, math.gcd and fractions there,
and the other modules of the strict list; the attribute, getattr, format and struct rules hold there too."""

import ast
import os
import re
import unittest

B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(B, "stripes_read_b")
TESTS = os.path.join(B, "tests")
STRICT_MODULES = {"fractions", "decimal", "math", "numpy", "statistics", "cmath", "random", "json", "pickle",
                  "marshal", "importlib", "ctypes", "scipy", "mpmath", "sympy", "operator", "array", "time",
                  "datetime", "tomllib", "builtins"}
LOOSE_MODULES = {"decimal", "numpy", "statistics", "cmath", "random"}
STRICT_NAMES = {"float", "complex", "round", "pow", "eval", "exec", "compile", "__import__", "format", "__builtins__"}
LOOSE_NAMES = {"float", "complex", "round", "pow"}
BAD_ATTRS = {"__truediv__", "__rtruediv__", "__itruediv__", "__float__", "__complex__", "__round__", "fromhex",
             "as_integer_ratio", "truediv", "itruediv", "pow", "__pow__", "__rpow__", "__ipow__", "float",
             "cast", "literal_eval", "float_info", "timestamp", "st_mtime", "st_atime", "st_ctime", "getmtime",
             "modules"}
MATH_OK = {"isqrt", "gcd"}
STRUCT_CALLS = {"pack", "pack_into", "unpack", "unpack_from", "iter_unpack", "calcsize", "Struct"}
FMT = re.compile(r"%(\([^)]*\))?[-+ #0]*(\*|[0-9]*)(\.(\*|[0-9]+))?[eEfFgG%]")
# a replacement field {name!conv:spec} whose spec ends in a float type: [[fill]align][sign][z][#][0][width][,_][.prec]
BRACE_FMT = re.compile(r"\{[^{}:!]*(![rsa])?:([^{}]?[<>=^])?[-+ ]?z?#?0?[0-9]*[,_]?(\.[0-9]+)?[eEfFgG%]\}")
LITERAL_TYPES = ("float", "complex")


def _struct_names(tree):
    """The names that reach the struct module (import struct [as s]) and its functions (from struct import f [as g])."""
    mods, funcs, star = {"struct"}, set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.asname or a.name for a in node.names if a.name == "struct"}
        elif isinstance(node, ast.ImportFrom) and node.module == "struct":
            for a in node.names:
                if a.name == "*":
                    star.append(node)
                elif a.name in STRUCT_CALLS:
                    funcs.add(a.asname or a.name)
    return mods, funcs, star


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
    struct_mods, struct_funcs, struct_star = _struct_names(tree)
    for node in struct_star:
        out.append("%s:%d from struct import *" % (os.path.basename(path), node.lineno))
    for node in ast.walk(tree):
        where = "%s:%d" % (os.path.basename(path), getattr(node, "lineno", 0))
        if isinstance(node, ast.Constant) and type(node.value).__name__ in LITERAL_TYPES:
            out.append(where + " float or complex literal")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and FMT.search(node.value):
            out.append(where + " float format in a string")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and BRACE_FMT.search(node.value):
            out.append(where + " float brace format in a string")
        if isinstance(node, ast.FormattedValue) and node.format_spec is not None:
            out.append(where + " f-string format spec")
        if isinstance(node, ast.Name) and node.id in names:
            out.append(where + " name " + node.id)
        if isinstance(node, ast.Name) and node.id == "getattr":
            call = parents.get(node)
            if not (isinstance(call, ast.Call) and call.func is node):
                out.append(where + " getattr not called")
            else:
                key = call.args[1] if len(call.args) > 1 else None
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    out.append(where + " getattr with a name the source does not show")
                elif key.value in BAD_ATTRS or key.value in STRICT_NAMES:
                    out.append(where + " getattr " + key.value)
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
        if isinstance(node, ast.Call) and (
                (isinstance(node.func, ast.Attribute) and node.func.attr in STRUCT_CALLS
                 and isinstance(node.func.value, ast.Name) and node.func.value.id in struct_mods)
                or (isinstance(node.func, ast.Name) and node.func.id in struct_funcs)):
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


# One plant of each kind the ruling names, and the extra kinds; each must be found (the self-test of the scan). Every
# module, name and attribute of the strict lists has its own row (test_every_listed_kind_is_planted). The plant texts
# are split where the scan would otherwise find them in this file's own strings.
PLANTS = (
    ("from fractions import Fraction\n", "import fractions"),
    ("import fractions\n", "import fractions"),
    ("import decimal\n", "import decimal"),
    ("from decimal import Decimal\n", "import decimal"),
    ("import math\nx = math.isqrt(4)\n", "import math"),
    ("from math import gcd\n", "import math"),
    ("import numpy\n", "import numpy"),
    ("import statistics\n", "import statistics"),
    ("import cmath\n", "import cmath"),
    ("import random\n", "import random"),
    ("import json\n", "import json"),
    ("import pickle\n", "import pickle"),
    ("import marshal\n", "import marshal"),
    ("import importlib\n", "import importlib"),
    ("import ctypes\n", "import ctypes"),
    ("import scipy\n", "import scipy"),
    ("import mpmath\n", "import mpmath"),
    ("import sympy\n", "import sympy"),
    ("import operator\nx = operator.mul(2, 3)\n", "import operator"),
    ("from array import array\n", "import array"),
    ("import time\n", "import time"),
    ("from datetime import datetime\n", "import datetime"),
    ("import tomllib\n", "import tomllib"),
    ("import builtins\n", "import builtins"),
    ("x = float(2)\n", "name float"),
    ("x = round(7)\n", "name round"),
    ("x = complex(1)\n", "name complex"),
    ("x = pow(2, 3)\n", "name pow"),
    ("x = ev" + "al('1')\n", "name eval"),
    ("ex" + "ec('x = 1')\n", "name exec"),
    ("x = com" + "pile('1', 's', 'eval')\n", "name compile"),
    ("x = __imp" + "ort__('os')\n", "name __import__"),
    ("x = for" + "mat(1, '.3" + "f')\n", "name format"),
    ("x = __buil" + "tins__\n", "name __builtins__"),
    ("x = 1" + ".5\n", "float or complex literal"),
    ("x = 1e" + "9\n", "float or complex literal"),
    ("x = 2" + "j\n", "float or complex literal"),
    ("x = 3 " + "/ 4\n", "true division"),
    ("x = 3\nx " + "/= 4\n", "true division"),
    ("x = 2 *" + "* 3\n", "'**'"),
    ("x = (1)." + "__truediv__(2)\n", "attribute __truediv__"),
    ("x = int." + "__rtruediv__\n", "attribute __rtruediv__"),
    ("x = int." + "__itruediv__\n", "attribute __itruediv__"),
    ("x = (1)." + "__float__()\n", "attribute __float__"),
    ("x = (1)." + "__complex__()\n", "attribute __complex__"),
    ("x = (1)." + "__round__()\n", "attribute __round__"),
    ("x = int." + "fromhex\n", "attribute fromhex"),
    ("x = (1)." + "as_integer_ratio()\n", "attribute as_integer_ratio"),
    ("x = m." + "truediv(1, 2)\n", "attribute truediv"),
    ("x = m." + "itruediv(1, 2)\n", "attribute itruediv"),
    ("x = m." + "pow(2, -1)\n", "attribute pow"),
    ("x = (2)." + "__pow__(-1)\n", "attribute __pow__"),
    ("x = (2)." + "__rpow__(2)\n", "attribute __rpow__"),
    ("x = int." + "__ipow__\n", "attribute __ipow__"),
    ("x = b." + "float(1)\n", "attribute float"),
    ("x = memoryview(b'').cast('" + "d')\n", "attribute cast"),
    ("x = a." + "literal_eval('1')\n", "attribute literal_eval"),
    ("x = s." + "float_info\n", "attribute float_info"),
    ("x = d." + "timestamp()\n", "attribute timestamp"),
    ("x = o.stat('.')." + "st_mtime\n", "attribute st_mtime"),
    ("x = o.stat('.')." + "st_atime\n", "attribute st_atime"),
    ("x = o.stat('.')." + "st_ctime\n", "attribute st_ctime"),
    ("x = o.path." + "getmtime('.')\n", "attribute getmtime"),
    ("x = s." + "modules['ma' + 'th']\n", "attribute modules"),
    ("x = getattr(1, '__true' + 'div__')(2)\n", "getattr with a name the source does not show"),
    ("x = getattr(1)\n", "getattr with a name the source does not show"),
    ("x = getattr(b, 'fl" + "oat')(1)\n", "getattr float"),
    ("x = getattr(1, '__fl" + "oat__')()\n", "getattr __float__"),
    ("g = getattr\n", "getattr not called"),
    ("import struct\nx = struct.unpack('<" + "d', b)\n", "struct float code"),
    ("import struct\nx = struct.Struct(f)\n", "struct format the source does not show"),
    ("from struct import unpack\nx = unpack('<" + "d', b)\n", "struct float code"),
    ("from struct import unpack_from as u\nx = u('<" + "f', b, 0)\n", "struct float code"),
    ("import struct as s\nx = s.iter_unpack('<" + "e', b)\n", "struct float code"),
    ("from struct import *\n", "from struct import *"),
    ("x = '%" + ".3f' % 1\n", "float format in a string"),
    ("x = '%(a)" + ".3f' % {'a': 1}\n", "float format in a string"),
    ("x = '%" + ".*f' % (3, 1)\n", "float format in a string"),
    ("x = '%" + "*.3f' % (8, 1)\n", "float format in a string"),
    ("x = '{:" + ".3f}'.format(1)\n", "float brace format in a string"),
    ("x = '{0!r:>" + "10e}'\n", "float brace format in a string"),
    ("x = '{share:" + ".1%}'\n", "float brace format in a string"),
    ("x = f'{1:" + ".3f}'\n", "f-string format spec"),
)
# Allowed forms each scan must leave alone: integer struct codes through the module and a name imported from it,
# getattr with a plain constant name, %s and %d, and braces that are not a float spec (a docstring's {key: value}).
CLEAN = ("import struct\nfrom struct import unpack_from as u\nx = 7 // 2\ny = struct.unpack('<qQ', bytes(16))\n"
         "z = u('<Q', bytes(8), 0)\nt = getattr(x, 'n', 0)\ns = '1.5'  # 0.5\n"
         "d = '{path: mode} {key: value} {0} {x!r} {:>8} %s %d' % (1, 2)\n")


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
                f.write(CLEAN)
            self.assertEqual(violations(p), [])
            self.assertEqual(violations(p, strict=False), [])
        finally:
            for nm in os.listdir(d):
                os.unlink(os.path.join(d, nm))
            os.rmdir(d)

    def test_every_listed_kind_is_planted(self):
        wants = {w for _, w in PLANTS}
        missing = sorted(["import " + m for m in STRICT_MODULES] + ["name " + n for n in STRICT_NAMES]
                         + ["attribute " + a for a in BAD_ATTRS])
        self.assertEqual([w for w in missing if w not in wants], [])

    def test_loose_rules_of_the_checker(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write("import math\nfrom fractions import Fraction\nx = math.isqrt(4)\ny = math.sqrt(2)\n"
                    "import time\nz = time.time_ns()\nw = getattr(x, 'p' + 'ow')\n")
            p = f.name
        try:
            v = violations(p, strict=False)
        finally:
            os.unlink(p)
        self.assertEqual([x.split(" ", 1)[1] for x in v], ["math.sqrt", "getattr with a name the source does not show"],
                         v)


if __name__ == "__main__":
    unittest.main()
