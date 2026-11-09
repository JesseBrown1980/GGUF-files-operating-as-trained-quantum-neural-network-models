#!/usr/bin/env python3
"""compare.py: the independent check of stage A. Each stream is read by stripes-read-a and by check_a.py; the two
outputs must be equal. A block must be equal byte for byte, its side file too. A STOP must agree in every field but
`detail` (the detail text is free), and its reason must be the one the case name expects.

    python3 -I compare.py --ra PATH [--streams DIR] [--excl DIR] [--work DIR]

--streams DIR holds synthetic cases NAME.args (one argument per line, @SIDE@ for a side-file path) and NAME.txt (the
stream), as written by `cargo test --test synthetic emit_streams_for_the_independent_check -- --ignored`.
--excl DIR holds real twens dumps at the excluded points only: X1.<i>.txt (N=27, delta=1/4, y=1/40) and X0.<i>.txt
(y=0), read as --point X1 or X0 --call i --side. This script runs no engine.

Exit 0 when every case is equal, 1 otherwise; usage errors exit 2."""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "check_a.py")
STOP_KEYS = ("reader", "reader_version", "point", "call", "reason", "line", "stdin_bytes", "stdin_lines",
             "stdin_sha256")
EXCL_NAME = re.compile(r"(X[01])\.(0|[1-9][0-9]*)\.txt\Z")
CASE_REASON = re.compile(r"(?:stop|args)[0-9]+_([A-Za-z0-9_]+)\Z")


def row_fields(line):
    out = {}
    for part in line.split("|")[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            out.setdefault(k, v)
    return out


def run(cmd, stdin_path):
    with open(stdin_path, "rb") as f:
        p = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout, p.stderr


def read_bytes(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def compare_case(ra, name, args, stream, work):
    side = os.path.join(work, "side.bin")
    args = [side if a == "@SIDE@" else a for a in args]
    uses_side = side in args
    for p in (side,):
        if os.path.exists(p):
            os.remove(p)
    rc_a, out_a, err_a = run([ra] + args, stream)
    side_a = read_bytes(side) if uses_side else None
    if os.path.exists(side):
        os.remove(side)
    rc_b, out_b, err_b = run([sys.executable, "-I", CHECKER] + args, stream)
    side_b = read_bytes(side) if uses_side else None
    if os.path.exists(side):
        os.remove(side)
    why = []
    if rc_a != rc_b:
        why.append("rc_%d_%d" % (rc_a, rc_b))
    kind = "block" if rc_a == 0 else "stop"
    if rc_a == 0 and rc_b == 0:
        if out_a != out_b:
            la, lb = out_a.split(b"\n"), out_b.split(b"\n")
            k = next((i for i, (x, y) in enumerate(zip(la, lb, strict=False)) if x != y), min(len(la), len(lb)))
            why.append("block_line_%d" % (k + 1))
        if err_a or err_b:
            why.append("stderr_on_success")
        if side_a != side_b:
            why.append("side_file")
    elif rc_a == 3 and rc_b == 3:
        ta, tb = out_a.decode("ascii", "replace"), out_b.decode("ascii", "replace")
        if ta.count("\n") != 1 or tb.count("\n") != 1 or not ta.startswith("STOP|") or not tb.startswith("STOP|"):
            why.append("stop_not_one_row")
        else:
            fa, fb = row_fields(ta.rstrip("\n")), row_fields(tb.rstrip("\n"))
            for k in STOP_KEYS:
                if fa.get(k) != fb.get(k):
                    why.append("stop_%s_%s_%s" % (k, fa.get(k), fb.get(k)))
            if err_a != out_a or err_b != out_b:
                why.append("stop_not_on_stderr")
            m = CASE_REASON.match(name)
            if m and fa.get("reason") != m.group(1):
                why.append("reason_%s_expected_%s" % (fa.get("reason"), m.group(1)))
        kind = "stop:" + row_fields(out_a.decode("ascii", "replace").rstrip("\n")).get("reason", "?")
    elif rc_a == rc_b:
        why.append("rc_%d" % rc_a)
    return why, kind


def cases_from(streams):
    out = []
    for nm in sorted(os.listdir(streams)):
        if nm.endswith(".args"):
            base = nm[: -len(".args")]
            with open(os.path.join(streams, nm), "rb") as f:
                args = [a for a in f.read().decode("ascii").split("\n") if a]
            out.append((base, args, os.path.join(streams, base + ".txt")))
    return out


def cases_excl(excl):
    out = []
    for nm in sorted(os.listdir(excl)):
        m = EXCL_NAME.match(nm)
        if m:
            out.append(("excl_" + nm[: -len(".txt")], ["--point", m.group(1), "--call", m.group(2), "--side", "@SIDE@"],
                        os.path.join(excl, nm)))
    return out


def main(argv):
    opts, i = {}, 1
    while i < len(argv):
        if argv[i] in ("--ra", "--streams", "--excl", "--work") and i + 1 < len(argv) and argv[i] not in opts:
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            sys.stderr.write(__doc__)
            return 2
    if "--ra" not in opts or not ("--streams" in opts or "--excl" in opts):
        sys.stderr.write(__doc__)
        return 2
    work = opts.get("--work") or os.path.join(os.path.dirname(os.path.abspath(opts["--ra"])), "compare-work")
    os.makedirs(work, exist_ok=True)
    cases = []
    if "--streams" in opts:
        cases += cases_from(opts["--streams"])
    if "--excl" in opts:
        cases += cases_excl(opts["--excl"])
    if not cases:
        sys.stderr.write("no cases\n")
        return 2
    equal = 0
    blocks = 0
    for name, args, stream in cases:
        why, kind = compare_case(opts["--ra"], name, args, stream, work)
        if kind == "block":
            blocks += 1
        if not why:
            equal += 1
        print("COMPARE_CASE|name=%s|kind=%s|result=%s|why=%s|json=0" % (name, kind, "equal" if not why else "differ",
                                                                        ",".join(why) or "none"))
    ok = equal == len(cases)
    print("COMPARE|cases=%d|blocks=%d|stops=%d|equal=%d|differ=%d|equal_all=%s|json=0" % (
        len(cases), blocks, len(cases) - blocks, equal, len(cases) - equal, "true" if ok else "false"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
