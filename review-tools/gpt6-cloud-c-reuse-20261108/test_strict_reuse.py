#!/usr/bin/env python3
"""Negative controls for Cloud C's independent count-weighted reuse checker."""
from pathlib import Path
import subprocess
import sys
import tempfile

CHECK = Path(__file__).with_name("strict_reuse.py")


def run(args, success, reason):
    p = subprocess.run([sys.executable, "-I", str(CHECK)] + list(map(str, args)),
                       capture_output=True, text=True, check=False)
    if (p.returncode == 0) != success or reason not in p.stdout:
        raise AssertionError("unexpected_result: %s, %s" % (p.returncode, p.stdout))
    print("CLOUD_C_CONTROL|check=%s|expected=%s|result=PASS|json=0" %
          (reason.replace("|", "_"), "EQUAL" if success else "REFUSE"))


def main():
    with tempfile.TemporaryDirectory() as root:
        folder = Path(root)
        head = ("TWB_HEAD|start={}|count={}|N=81|delta=1/2|u=1|y=1/18|seed=7|"
                "seed_string=x|dtden=64|steps=0,32|mask=VNC|q=40|sums=exact|"
                "rounding=per_sample|cli=run|json=0\n")
        row = "TWB|step={}|variant=VNC|n={}|f={}|eps_max={}|json=0\n"
        nl = "TWB_NL|N=81|delta=1/2|status=pass|json=0\n"

        def write(name, content):
            path = folder / name
            path.write_text(content, encoding="utf-8")
            return path

        r96 = write("ref96.hbp", head.format(0, 96) + nl +
                    row.format(0, 96, 480, 7) + row.format(32, 96, 960, 8))
        r40 = write("ref40.hbp", head.format(0, 40) + nl +
                    row.format(0, 40, 200, 7) + row.format(32, 40, 400, 8))
        stair = write("stair.hbp", head.format(0, 96) + nl +
                      row.format(0, 96, 480, 7) + row.format(32, 40, 400, 8))
        missing = write("missing.hbp", head.format(0, 96) + nl +
                        row.format(0, 96, 480, 7))
        no_nl = write("no_nl.hbp", head.format(0, 96) +
                      row.format(0, 96, 480, 7) + row.format(32, 40, 400, 8))
        corrupt = write("corrupt.hbp", head.format(0, 96) + nl +
                        row.format(0, 96, 481, 7) + row.format(32, 40, 400, 8))
        wrong_mask = write("wrong_mask.hbp", head.format(0, 40).replace(
            "mask=VNC", "mask=V1") + nl + row.format(0, 40, 200, 7) +
            row.format(32, 40, 400, 8))
        run(["--stair", stair, r96, r40], True, "CLOUD_C_PASS|mode=stair")
        run(["--stair", missing, r96, r40], False, "row_set_differs:missing=1")
        run(["--stair", no_nl, r96, r40], False, "nl_rows_differ")
        run(["--stair", corrupt, r96, r40], False, "row_differs:f")
        run(["--stair", stair, r96, wrong_mask], False, "job_field_differs:mask")
        p1 = write("p1.hbp", head.format(0, 40) + nl +
                   row.format(0, 40, 200, 7) + row.format(32, 40, 400, 8))
        p2 = write("p2.hbp", head.format(40, 56) + nl +
                   row.format(0, 56, 280, 7) + row.format(32, 56, 560, 8))
        run(["--union", r96, p1, p2], True, "CLOUD_C_PASS|mode=union")
        overlap = write("overlap.hbp", head.format(39, 56) + nl +
                        row.format(0, 56, 280, 7) + row.format(32, 56, 560, 8))
        run(["--union", r96, p1, overlap], False, "index_ranges_not_disjoint_or_not_covering")
        p2_no_nl = write("p2_no_nl.hbp", head.format(40, 56) +
                         row.format(0, 56, 280, 7) + row.format(32, 56, 560, 8))
        run(["--union", r96, p1, p2_no_nl], False, "nl_rows_differ")
        p2_bad = write("p2_bad.hbp", head.format(40, 56) + nl +
                       row.format(0, 56, 281, 7) + row.format(32, 56, 560, 8))
        run(["--union", r96, p1, p2_bad], False, "sum_differs:f")
    print("CLOUD_C_SELFTEST|controls=9|failed=0|json=0")


if __name__ == "__main__":
    main()
