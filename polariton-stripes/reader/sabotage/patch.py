"""patch.py: stage B's read with one planted fault in its own code (the sabotage suite, run.sh). No engine runs.

    python3 -I patch.py CASE <arguments of `stripes_read_b read`>

  promote         rows_e_mom scores E15's cross-read at P08 t=1, which the frozen row (RP13) makes read-and-report
  falsify_report  rows_e_mom evaluates a falsifier on E17's read pi_t1, a read-and-report read (rule EXPOSED, X08)

Stage B must refuse to write a READ file: exit 3 with a STOP row (scoring_table, or falsifier)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "b"))

import stripes_read_b.__main__ as stage_b  # noqa: E402
from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import rows_e_mom as m  # noqa: E402


def plant_promote():
    report = c.report

    def promoted(fz, kind, rid, phrase, why):
        s = report(fz, kind, rid, phrase, why)
        if rid == "E15" and why == "RP13":
            return c.Scoring(True, "unexposed")
        return s

    c.report = promoted


def plant_falsify_report():
    row_e17 = m.row_e17

    def falsified(inp, fz):
        reads, _ = row_e17(inp, fz)
        return reads, [r.rid for r in reads if r.rid == "pi_t1"]

    m.ROWS = tuple((rid, falsified if rid == "E17" else fn) for rid, fn in m.ROWS)


PLANTS = {"promote": plant_promote, "falsify_report": plant_falsify_report}


def main(argv):
    if len(argv) < 2 or argv[1] not in PLANTS:
        sys.stderr.write(__doc__)
        return 2
    PLANTS[argv[1]]()
    return stage_b.main(["stripes_read_b", "read"] + argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
