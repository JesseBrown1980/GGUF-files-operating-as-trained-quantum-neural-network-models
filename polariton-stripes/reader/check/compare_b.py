#!/usr/bin/env python3
"""compare_b.py: the live stage B (integer pairs, reader/b) against the stage B kept as evidence (fractions.Fraction,
reader/evidence/stage-b-fraction), on control data only. The output must be byte-identical.

    python3 -I compare_b.py [--excl DIR] [--work DIR] [--keep]

1. Checks the evidence folder's tree pin in polariton-stripes/FLOAT-EVIDENCE.txt (float_evidence.py), so the version
   compared is the one listed.
2. Lays the evidence out at its old depth, <work>/polariton-stripes/reader/b/, beside a copy of the frozen file (its
   frozen.py finds the file three folders up and checks its sha256).
3. Runs, with each version, `run_b.py tables`, `run_b.py series` and probe_b.py: the closed forms and frozen decimals,
   the QE rows at N = 9, delta = 1/3, the stage A blocks and run sums at N = 27, delta = 1/4, and with --excl the
   real side files of X1 and X0. No row point, no engine.
4. The lens step: the live tests/campaign.py writes fabricated QE receipts and runs R1-R4 once (--only qe,runs:
   small integers in the receipts' formats, no engine value), and `probe_b.py --lens` runs the row builders of
   Q01-Q07, E09-E15 and E17-E19 on them and on the X1 and X0 blocks, with each version.
5. Compares each stdout and exit code byte for byte. Prints one COMPARE_B row each and a COMPARE_B_DONE row; exit 0
   when every pair is equal.

Outputs a fix after the conversion changed on purpose are not compared: E16 (the conservative SE_pair), and the text
of a READ row (the band of an infinite end, the reason of a read lost to a QE exit). The lens prints reads by their
fields, so its lines do not carry that text. check/compare_read_b.py compares the two versions' READ files on the e2e
campaigns and requires each of those differences to be a declared one."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.dirname(HERE)
STRIPES = os.path.dirname(READER)
LIVE = os.path.join(READER, "b")
EVIDENCE = os.path.join(READER, "evidence", "stage-b-fraction")
FROZEN = os.path.join(STRIPES, "PREDICTION-STRIPE-PHASE.hbp")


def run(argv):
    p = subprocess.run([sys.executable, "-I"] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                       cwd="/")
    return p.returncode, p.stdout, p.stderr


def main(argv):
    excl, work, keep = None, None, False
    i = 1
    while i < len(argv):
        if argv[i] in ("--excl", "--work") and i + 1 < len(argv):
            if argv[i] == "--excl":
                excl = argv[i + 1]
            else:
                work = argv[i + 1]
            i += 2
        elif argv[i] == "--keep":
            keep, i = True, i + 1
        else:
            sys.stderr.write(__doc__)
            return 2
    rc, so, se = run([os.path.join(HERE, "float_evidence.py")])
    if rc != 0:
        sys.stdout.write(so.decode("ascii", "replace"))
        print("COMPARE_B_DONE|result=evidence_pin_moved|json=0")
        return 1
    own = work is None
    work = work or tempfile.mkdtemp(prefix="stripes-compare-b-")
    fails = 0
    try:
        frac = os.path.join(work, "polariton-stripes", "reader", "b")
        if os.path.isdir(os.path.join(work, "polariton-stripes")):
            shutil.rmtree(os.path.join(work, "polariton-stripes"))
        shutil.copytree(EVIDENCE, frac, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(FROZEN, os.path.join(work, "polariton-stripes", os.path.basename(FROZEN)))
        lens = os.path.join(work, "lens")
        if os.path.isdir(lens):
            shutil.rmtree(lens)
        rc, so, se = run([os.path.join(LIVE, "tests", "campaign.py"), "--out", lens, "--only", "qe,runs"])
        if rc != 0:
            sys.stderr.write(se.decode("ascii", "replace")[-2000:])
            print("COMPARE_B_DONE|result=lens_inputs_not_written|json=0")
            return 1
        probe = [os.path.join(HERE, "probe_b.py")]
        cases = (("run_b_tables", ["run_b.py", "tables"]), ("run_b_series", ["run_b.py", "series"]),
                 ("probe", None), ("lens", "lens"))
        for name, cmd in cases:
            got = {}
            for label, b in (("fraction", frac), ("integer_pairs", LIVE)):
                if cmd is None:
                    args = probe + [b] + ([excl] if excl else [])
                elif cmd == "lens":
                    args = probe + [b, "--lens", lens]
                else:
                    args = [os.path.join(b, cmd[0])] + cmd[1:]
                got[label] = run(args)
            (ra, oa, ea), (rb, ob, eb) = got["fraction"], got["integer_pairs"]
            equal = ra == rb and oa == ob
            fails += not equal
            print("COMPARE_B|what=%s|rc=%d:%d|lines=%d:%d|sha256=%s:%s|stderr_bytes=%d:%d|equal=%d|json=0" % (
                name, ra, rb, oa.count(b"\n"), ob.count(b"\n"), hashlib.sha256(oa).hexdigest()[:16],
                hashlib.sha256(ob).hexdigest()[:16], len(ea), len(eb), 1 if equal else 0))
            if not equal or ra != 0:
                fails += ra != 0
                sys.stderr.write(ea.decode("ascii", "replace")[-2000:] + eb.decode("ascii", "replace")[-2000:])
    finally:
        if own and not keep:
            shutil.rmtree(work)
    print("COMPARE_B_DONE|excl=%s|engine_runs=0|row_points=0|result=%s|json=0" % (
        "real_side_files" if excl else "none", "equal" if not fails else "differ"))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
