#!/usr/bin/env bash
# no_float.sh: the reader uses integers and exact rationals only (rule DECIMAL); live stage B uses ints and checked
# integer pairs only (the owner's ruling of 2026-11-09). It
#   - checks every folder row of polariton-stripes/FLOAT-EVIDENCE.txt against its tree pin (float_evidence.py) and
#     leaves those folders out of every scan below (reader/evidence/stage-b-fraction, the Fraction stage B);
#   - greps the Rust of stage A (reader/a/src, reader/a/tests), comments and string literals removed, for f32/f64,
#     float literals (1.5, 1., 1e9) and float methods (sqrt, powf, exp, ln, sin, cos ...);
#   - scans every other .py under reader/ as tokens (strings and comments are not code) for float and complex
#     literals, float(), complex, round, pow, math other than isqrt and gcd, numpy, cmath, statistics, random,
#     builtins, __builtins__ and tomllib, and, after a '.', the float doors (pow, __pow__, float, __truediv__,
#     cast, literal_eval, float_info, timestamp, st_mtime, getmtime, modules and their kin);
#   - runs the AST check of reader/b/tests/test_nofloat.py: strict on stage B (reader/b: no fractions, decimal, math,
#     numpy, operator, array, time, datetime, tomllib or builtins, no float(), round(), complex() or format(), no
#     float literal, no true division anywhere, no '**', no float door attribute, getattr only with a constant name,
#     no float format, no struct float code), loose on the checker and the sabotage suite (math.isqrt, math.gcd and
#     fractions allowed there, no '/' or '**', and the attribute, getattr, format and struct rules).
# A self-test first plants one fault of each kind, and a moved pin, and requires every one to be found.
# Exit 0 when the tree is clean.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
READER=$(dirname "$HERE")
PY=${PYTHON:-python3}

RUST_PATTERNS=(
  '(^|[^0-9A-Za-z_])f(32|64)([^0-9A-Za-z_]|$)'
  '[0-9]f(32|64)([^0-9A-Za-z_]|$)'
  '(^|[^0-9A-Za-z_.])[0-9][0-9_]*\.[0-9]'
  '(^|[^0-9A-Za-z_.])[0-9][0-9_]*\.([^0-9.A-Za-z_]|$)'
  '(^|[^0-9A-Za-z_.])[0-9][0-9_]*[eE][+-]?[0-9]'
  '\.(sqrt|cbrt|powf|powi|exp|exp2|ln|log|log2|log10|sin|cos|tan|asin|acos|atan|atan2|sinh|cosh|tanh|hypot|floor|ceil|round|trunc|fract|to_degrees|to_radians)\('
  '(^|[^0-9A-Za-z_])(INFINITY|NEG_INFINITY|NAN|EPSILON)([^0-9A-Za-z_]|$)'
)

strip_rust() { sed -E -e 's://.*$::' -e 's/"([^"\\]|\\.)*"/""/g' -e "s/'([^'\\\\]|\\\\.)'/''/g" "$1"; }

grep_rust() {
  local f hits=0 p
  local out
  for f in "$@"; do
    for p in "${RUST_PATTERNS[@]}"; do
      out=$(strip_rust "$f" | grep -nE "$p")
      if [ -n "$out" ]; then sed "s|^|$f:|" <<<"$out"; hits=1; fi
    done
  done
  return $hits
}

# Python as tokens: file:line:token for every NUMBER and NAME token that is a float or a float function.
PY_TOKENS='
import io, sys, tokenize
BAD_NAMES = {"float", "complex", "round", "pow", "numpy", "cmath", "statistics", "random", "fsum", "truediv",
             "builtins", "__builtins__", "tomllib"}
# names that open a float even as an attribute (after a "."): operator.pow, (2).__pow__, builtins.float, sys.float_info
DOORS = {"pow", "__pow__", "__rpow__", "__ipow__", "float", "complex", "fsum", "truediv", "itruediv", "__truediv__",
         "__rtruediv__", "__itruediv__", "__float__", "__complex__", "__round__", "fromhex", "as_integer_ratio",
         "cast", "literal_eval", "float_info", "timestamp", "st_mtime", "st_atime", "st_ctime", "getmtime", "modules"}
MATH_OK = {"isqrt", "gcd"}
CODE = (tokenize.NAME, tokenize.OP, tokenize.NUMBER, tokenize.NEWLINE)
hits = 0
for path in sys.argv[1:]:
    if path.endswith("/tests/test_nofloat.py"):
        continue  # the AST checker itself names the float types it bans
    with open(path, "rb") as f:
        toks = [t for t in tokenize.tokenize(io.BytesIO(f.read()).readline) if t.type in CODE]
    from_math = False
    for i, t in enumerate(toks):
        s = t.string
        if t.type == tokenize.NEWLINE:
            from_math = False
            continue
        before = [x.string for x in toks[max(0, i - 3):i]]
        bad = False
        if t.type == tokenize.NUMBER:
            n = s.lower().replace("_", "")
            bad = not n.startswith(("0x", "0o", "0b")) and ("." in n or "e" in n or n.endswith("j"))
        elif t.type == tokenize.NAME:
            if before[-3:] == ["from", "math", "import"]:
                from_math = True
            if before[-2:] == ["math", "."] or (from_math and s != "import"):
                bad = s not in MATH_OK
            elif before[-1:] == ["."]:
                bad = s in DOORS
            elif s in BAD_NAMES:
                bad = True
        if bad:
            print("%s:%d: %s" % (path, t.start[0], s))
            hits += 1
sys.exit(1 if hits else 0)
'

grep_python() { "$PY" -I -c "$PY_TOKENS" "$@"; }

# ast_python STRICT_ROOT FILE...: the strict rules for files under STRICT_ROOT (stage B), the loose ones elsewhere.
ast_python() {
  "$PY" -I - "$READER/b" "$@" <<'EOF'
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from tests.test_nofloat import violations
strict_root = os.path.join(os.path.abspath(sys.argv[2]), "")
bad = []
for p in sys.argv[3:]:
    bad += violations(p, strict=os.path.abspath(p).startswith(strict_root))
for b in bad:
    print(b)
sys.exit(1 if bad else 0)
EOF
}

# Self-test: one planted fault of each kind must be found.
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
printf 'fn a() -> f64 { 0.5 }\n' > "$T/a.rs"
printf 'fn b() { let x = 1e9 as i64; }\n' > "$T/b.rs"
printf 'fn c(x: i64) -> i64 { (x as u64).isqrt() as i64 + 2.0_f32 as i64 }\n' > "$T/c.rs"
printf 'x = 0.5\n' > "$T/a.py"
printf 'x = float(3)\n' > "$T/b.py"
printf 'import math\nx = math.sqrt(2)\n' > "$T/c.py"
printf 'x = 3 / 4\n' > "$T/d.py"
mkdir -p "$T/strict"
printf 'from fractions import Fraction\n' > "$T/strict/e.py"
printf 'import math\nx = math.isqrt(4)\n' > "$T/strict/f.py"
printf 'def div(a, b):\n    return a / b\n' > "$T/strict/g.py"
printf 'import math\nx = math.isqrt(4)\n' > "$T/h.py"
# the float doors of review M6, as tokens (i-l) and in the strict AST (m-r); the loose AST finds i-l too
printf 'import operator\nx = operator.pow(2, -1)\n' > "$T/i.py"
printf 'x = (2).__pow__(-1)\n' > "$T/j.py"
printf 'import builtins\nx = builtins.float(1)\n' > "$T/k.py"
printf 'import sys\nx = sys.float_info\n' > "$T/l.py"
printf 'import time\nx = time.time()\n' > "$T/strict/m.py"
printf '%s\n' "x = format(1, '.3f')" > "$T/strict/n.py"
printf '%s\n' "x = getattr(1, '__true' + 'div__')(2)" > "$T/strict/o.py"
printf '%s\n' "from struct import unpack" "x = unpack('<d', b)" > "$T/strict/p.py"
printf '%s\n' "x = '{:.3f}'.format(1)" > "$T/strict/q.py"
printf '%s\n' "x = '%(a).3f' % {'a': 1}" > "$T/strict/r.py"
ok=0
for f in a b c; do grep_rust "$T/$f.rs" > /dev/null && { echo "SELF_TEST rust $f.rs not caught"; ok=1; }; done
for f in a b c i j k l; do grep_python "$T/$f.py" > /dev/null && { echo "SELF_TEST python $f.py not caught"; ok=1; }; done
for f in i j k l; do ast_python "$T/strict" "$T/$f.py" > /dev/null && { echo "SELF_TEST loose $f.py not caught"; ok=1; }; done
ast_python "$T/strict" "$T/d.py" > /dev/null && { echo "SELF_TEST python d.py ('/') not caught"; ok=1; }
for f in e f g m n o p q r; do ast_python "$T/strict" "$T/strict/$f.py" > /dev/null && { echo "SELF_TEST strict $f.py not caught"; ok=1; }; done
ast_python "$T/strict" "$T/h.py" > /dev/null || { echo "SELF_TEST loose h.py (math.isqrt) flagged"; ok=1; }
# a moved pin: a listed folder in a scratch repository, then one byte edited
R=$T/repo
mkdir -p "$R/polariton-stripes/ev"
git -C "$R" init -q
printf 'x = 1\n' > "$R/polariton-stripes/ev/a.py"
"$PY" -I "$HERE/float_evidence.py" --repo "$R" --pins polariton-stripes/ev/ > /dev/null && { echo "SELF_TEST untracked file pinned"; ok=1; }
git -C "$R" add polariton-stripes/ev/a.py
pin=$("$PY" -I "$HERE/float_evidence.py" --repo "$R" --pins polariton-stripes/ev/ | sed 's/^.*tree=\([0-9a-f]*\).*$/\1/')
printf '# test\npolariton-stripes/ev/ | tree=%s | a test row\n' "$pin" > "$R/polariton-stripes/FLOAT-EVIDENCE.txt"
"$PY" -I "$HERE/float_evidence.py" --repo "$R" > /dev/null || { echo "SELF_TEST pin of an unchanged folder refused"; ok=1; }
# the mode comes from git's index: with core.filemode=false (WSL /mnt/c) an executable bit on disk leaves the pin; with
# core.filemode=true an unstaged mode change is a fault, and so is an untracked file under the folder
chmod +x "$R/polariton-stripes/ev/a.py"
git -C "$R" config core.filemode false
"$PY" -I "$HERE/float_evidence.py" --repo "$R" > /dev/null || { echo "SELF_TEST pin moved by a mode git does not see"; ok=1; }
git -C "$R" config core.filemode true
"$PY" -I "$HERE/float_evidence.py" --repo "$R" > /dev/null && { echo "SELF_TEST unstaged mode change not caught"; ok=1; }
chmod -x "$R/polariton-stripes/ev/a.py"
printf 'y = 1\n' > "$R/polariton-stripes/ev/b.py"
"$PY" -I "$HERE/float_evidence.py" --repo "$R" > /dev/null && { echo "SELF_TEST untracked file not caught"; ok=1; }
rm "$R/polariton-stripes/ev/b.py"
printf 'x = 2\n' > "$R/polariton-stripes/ev/a.py"
"$PY" -I "$HERE/float_evidence.py" --repo "$R" > /dev/null && { echo "SELF_TEST moved pin not caught"; ok=1; }
printf 'fn ok(r: (u64, u64)) -> u64 { let s = "1.5e3"; r.0 + 2 + s.len() as u64 } // 0.5\n' > "$T/ok.rs"
printf 'x = "0.5"  # 1.5\ny = 7 // 2\nz = getattr(y, "real", 0)\nw = "{key: value} %%s %%d"\n' > "$T/ok.py"
grep_rust "$T/ok.rs" > /dev/null || { echo "SELF_TEST rust ok.rs flagged"; ok=1; }
grep_python "$T/ok.py" > /dev/null || { echo "SELF_TEST python ok.py flagged"; ok=1; }
ast_python "$T/strict" "$T/ok.py" > /dev/null || { echo "SELF_TEST loose ok.py flagged"; ok=1; }
[ "$ok" = 0 ] || { echo "NO_FLOAT|result=self_test_failed|json=0"; exit 2; }

r=0
REPO=$(dirname "$(dirname "$READER")")
"$PY" -I "$HERE/float_evidence.py" --repo "$REPO" || r=1
mapfile -t LISTED < <("$PY" -I "$HERE/float_evidence.py" --repo "$REPO" --folders)
prune=()
for f in "${LISTED[@]}"; do prune+=(-not -path "$REPO/${f}*"); done
mapfile -t RS < <(find "$READER/a/src" "$READER/a/tests" -name '*.rs' | sort)
mapfile -t PYS < <(find "$READER" -name '*.py' -not -path '*/.ruff_cache/*' -not -path '*/__pycache__/*' "${prune[@]}" | sort)
mapfile -t ALL_PYS < <(find "$READER" -name '*.py' -not -path '*/.ruff_cache/*' -not -path '*/__pycache__/*' | sort)
grep_rust "${RS[@]}" || r=1
grep_python "${PYS[@]}" || r=1
ast_python "$READER/b" "${PYS[@]}" || r=1
echo "NO_FLOAT|rust_files=${#RS[@]}|python_files=${#PYS[@]}|listed_folders=${#LISTED[@]}|python_files_in_listed_folders=$((${#ALL_PYS[@]} - ${#PYS[@]}))|self_test=pass|result=$([ $r = 0 ] && echo clean || echo float_found)|json=0"
exit $r
