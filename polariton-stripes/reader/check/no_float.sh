#!/usr/bin/env bash
# no_float.sh: the reader uses integers and exact rationals only (rule DECIMAL). It greps
#   - the Rust of stage A (reader/a/src, reader/a/tests), comments and string literals removed, for f32/f64, float
#     literals (1.5, 1., 1e9) and float methods (sqrt, powf, exp, ln, sin, cos ...);
#   - the Python of stage B, the checker and the sabotage suite (every .py under reader/), as tokens (strings and
#     comments are not code), for float and complex literals, float(), complex, round, pow, math other than isqrt and
#     gcd, numpy, cmath, statistics and random;
# then runs the AST check of reader/b/tests/test_nofloat.py on every .py file, which also bans true division '/'
# outside exact.div and '**'. A self-test first plants one fault of each kind and requires every one to be found.
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
BAD_NAMES = {"float", "complex", "round", "pow", "numpy", "cmath", "statistics", "random", "fsum", "truediv"}
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
            elif s in BAD_NAMES and before[-1:] != ["."]:
                bad = True
        if bad:
            print("%s:%d: %s" % (path, t.start[0], s))
            hits += 1
sys.exit(1 if hits else 0)
'

grep_python() { "$PY" -I -c "$PY_TOKENS" "$@"; }

ast_python() {
  "$PY" -I - "$READER/b" "$@" <<'EOF'
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from tests.test_nofloat import violations
bad = []
for p in sys.argv[2:]:
    if p.endswith("test_nofloat.py"):
        continue
    bad += violations(p, allow_div_in=("div",) if "/stripes_read_b/" in p else ())
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
ok=0
for f in a b c; do grep_rust "$T/$f.rs" > /dev/null && { echo "SELF_TEST rust $f.rs not caught"; ok=1; }; done
for f in a b c; do grep_python "$T/$f.py" > /dev/null && { echo "SELF_TEST python $f.py not caught"; ok=1; }; done
ast_python "$T/d.py" > /dev/null && { echo "SELF_TEST python d.py ('/') not caught"; ok=1; }
printf 'fn ok(r: (u64, u64)) -> u64 { let s = "1.5e3"; r.0 + 2 + s.len() as u64 } // 0.5\n' > "$T/ok.rs"
printf 'x = "0.5"  # 1.5\ny = 7 // 2\n' > "$T/ok.py"
grep_rust "$T/ok.rs" > /dev/null || { echo "SELF_TEST rust ok.rs flagged"; ok=1; }
grep_python "$T/ok.py" > /dev/null || { echo "SELF_TEST python ok.py flagged"; ok=1; }
[ "$ok" = 0 ] || { echo "NO_FLOAT|result=self_test_failed|json=0"; exit 2; }

mapfile -t RS < <(find "$READER/a/src" "$READER/a/tests" -name '*.rs' | sort)
mapfile -t PYS < <(find "$READER" -name '*.py' -not -path '*/.ruff_cache/*' -not -path '*/__pycache__/*' | sort)
r=0
grep_rust "${RS[@]}" || r=1
grep_python "${PYS[@]}" || r=1
ast_python "${PYS[@]}" || r=1
echo "NO_FLOAT|rust_files=${#RS[@]}|python_files=${#PYS[@]}|self_test=pass|result=$([ $r = 0 ] && echo clean || echo float_found)|json=0"
exit $r
