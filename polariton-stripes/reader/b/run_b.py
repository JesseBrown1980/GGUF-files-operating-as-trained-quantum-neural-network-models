"""stripes-read-b, part 1: python3 -I run_b.py <command> ...

  tables                       the point tables, X08 and the QE plan against the frozen file
  series                       every frozen decimal the closed forms and the y-series bracket
  q --qe P [--cost P] [--guard P] [--out P]
                               rows Q01-Q07 from the filed QE stdout (READ and VERDICT rows)
  point --dir D --id Pnn [--sums]
                               one dump point's call files under rules SEED and STOP (a summary row)
  run --dir D --id Rn          one run point's 64 batches (a summary row)

Exit 0 on success, 3 with one STOP row on stdout when stage B has nothing to decide (StageBStop).
The whole read (every row, the READ file, its audit) is stripes_read_b/__main__.py read; see reader/README.md."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)

from stripes_read_b import VERSION, common, frozen, qe, rows_q, runs, series  # noqa: E402
from stripes_read_b.exact import fmt  # noqa: E402
from stripes_read_b.hbp import emit  # noqa: E402


def _args(argv, keys, flags=()):
    out, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in flags:
            out[a] = True
            i += 1
        elif a in keys and i + 1 < len(argv) and a not in out:
            out[a] = argv[i + 1]
            i += 2
        else:
            raise common.StageBStop("usage", a)
    return out


def cmd_tables(argv):
    fz = frozen.load()
    common.check_tables(fz)
    common.check_exposure_text(fz)
    qe.check_plan(fz)
    print(emit("STRIPES_B_TABLES", [("frozen_sha256", fz.sha256), ("dump_points", str(len(common.DUMP_POINTS))),
                                     ("run_points", str(len(common.RUN_POINTS))), ("qe_commands", str(len(qe.PLAN))),
                                     ("result", "all_equal")]))


def cmd_series(argv):
    res = series.check_frozen()
    for label, _kind, rid, text, b, st in res:
        print(emit("STRIPES_B_SERIES", [("row", rid), ("what", label), ("frozen", text),
                                         ("lo", fmt(b.lo, 12, "down")), ("hi", fmt(b.hi, 12, "up")), ("status", st),
                                         ("note", series.KNOWN_SLIPS.get(label, "none"))]))
    bad = [r for r in res if r[5] != series.CONTAINS and r[0] not in series.KNOWN_SLIPS]
    print(emit("STRIPES_B_SERIES_END", [("checks", str(len(res))),
                                         ("contained", str(sum(1 for r in res if r[5] == series.CONTAINS))),
                                         ("known_slips", str(len(series.KNOWN_SLIPS))), ("unexpected", str(len(bad)))]))
    return 0 if not bad else 3


def cmd_q(argv):
    a = _args(argv, ("--qe", "--cost", "--guard", "--out"))
    if "--qe" not in a:
        raise common.StageBStop("usage", "--qe")
    vs, reads = rows_q.read_q(a["--qe"], a.get("--cost"), a.get("--guard"))
    rf = common.ReadFile()
    rf.add_input("QE", a["--qe"])
    for k in ("--cost", "--guard"):
        if k in a:
            rf.add_input(k[2:].upper(), a[k])
    miss = qe.missing(reads)
    rf.notes.append(("qe_rows", "%d_read,%d_missing_(NOT_MEASURED)" % (len(reads), len(miss))))
    for v in vs:
        rf.add(v)
    if "--out" in a:
        h = rf.write(a["--out"])
        print(emit("STRIPES_B_WROTE", [("path", a["--out"]), ("sha256", h)]))
    else:
        for ln in rf.lines():
            print(ln)
    return 0


def cmd_point(argv):
    a = _args(argv, ("--dir", "--id"), ("--sums",))
    spec = common.DUMP_POINTS[a["--id"]]
    pt = common.load_point(a["--dir"], spec, require_sums=bool(a.get("--sums")))
    print(emit("STRIPES_B_POINT", [("point", spec.id), ("calls", str(spec.calls)), ("read", str(len(pt.calls))),
                                    ("lost", ",".join(str(i) for i, _ in pt.lost) or "none"),
                                    ("attempt_files", str(len(pt.attempts))),
                                    ("steps", ",".join(map(str, pt.steps)) or "none"),
                                    ("not_measured", ",".join(map(str, pt.not_measured)) or "none"),
                                    ("M_vnc", str(pt.M())), ("M_ctrl", str(pt.M("ctrl", "V1")))]))
    return 0


def cmd_run(argv):
    a = _args(argv, ("--dir", "--id"))
    spec = common.RUN_POINTS[a["--id"]]
    r = runs.load_run(a["--dir"], spec)
    print(emit("STRIPES_B_RUN", [("point", spec.id), ("batches", str(spec.batches)), ("read", str(len(r.batches))),
                                  ("lost", ",".join(str(j) for j, _ in r.lost) or "none"),
                                  ("steps", ",".join(map(str, r.steps)) or "none"),
                                  ("not_measured", ",".join(map(str, r.not_measured)) or "none"), ("M", str(r.M()))]))
    return 0


COMMANDS = {"tables": cmd_tables, "series": cmd_series, "q": cmd_q, "point": cmd_point, "run": cmd_run}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        sys.stderr.write(__doc__)
        return 2
    try:
        rc = COMMANDS[argv[1]](argv[2:])
        return rc or 0
    except common.StageBStop as e:
        print(emit("STOP", [("reader", common.READER), ("reader_version", VERSION), ("reason", e.reason),
                            ("detail", e.detail or "none")]))
        return 3
    except KeyError as e:
        print(emit("STOP", [("reader", common.READER), ("reader_version", VERSION), ("reason", "usage"),
                            ("detail", str(e))]))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
