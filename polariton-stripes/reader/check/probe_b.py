#!/usr/bin/env python3
"""probe_b.py: one stage B, run on control data only, printing every value it computes as text.

    python3 -I probe_b.py B_DIR [EXCL_DIR]
    python3 -I probe_b.py B_DIR --lens LENS_DIR

B_DIR is a stage B folder (the live reader/b, or the Fraction evidence laid out by compare_b.py). The data are the
excluded points, never a row point: the stage A blocks and run sums at N = 27, delta = 1/4 (y = 1/40 and y = 0) and the
QE rows at N = 9, delta = 1/3 in reader/b/tests/data, the closed forms at those (delta, y, t), the frozen decimals, and
with EXCL_DIR the real side files of X1 and X0. No engine runs. compare_b.py runs this file on both stage B versions
and requires the same bytes. Only functions both versions share are called, through the same arguments; the call
files get the trailer each version's grammar reads (rc and rc_reader, and the steps where the version files them).

With --lens, it runs the row builders instead (the review lens, quantum review 2 M4 and ensemble review 2 M2): Q01-Q07
on LENS_DIR's fabricated QE receipts (campaign.py --only qe: small integers at the plan's keys, not engine values),
and E09-E15 and E17-E19 on the X1 and X0 blocks (X0 placed at the y = 0 dump points, X1 at the others) and on
LENS_DIR's fabricated runs R1-R4 (campaign.py --only runs). Each read is printed by its fields at 30 digits, not by
Read.row_text, and each row by its verdict, falsifier and counts. E16 is left out: its conservative SE_pair changed
its output on purpose after the conversion. E01-E08 need the table's own points, so they are not in the lens."""

import os
import shutil
import sys
import tempfile

B_DIR = os.path.abspath(sys.argv[1])
sys.dont_write_bytecode = True
sys.path.insert(0, B_DIR)

from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import frozen  # noqa: E402
from stripes_read_b import qe  # noqa: E402
from stripes_read_b import rows_e_mom as m  # noqa: E402
from stripes_read_b import rows_e_sym as e  # noqa: E402
from stripes_read_b import rows_q  # noqa: E402
from stripes_read_b import runs  # noqa: E402
from stripes_read_b import series  # noqa: E402
from stripes_read_b.exact import Ext, Iv, Rad, fmt, fr  # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "b", "tests", "data")
STEPS_IN_TRAILER = hasattr(c, "check_side_sums")
SIG = 30
X1 = c.DumpPoint("X1", 27, "1/4", "1/40", 2 * 4096, 2, (64, 128), False)
X0 = c.DumpPoint("X0", 27, "1/4", "0", 2 * 4096, 2, (64, 128), False)
XR1 = c.RunPoint("XR1", 27, "1/4", "1/40", 4096, (32, 64, 128), batches=8)
XR0 = c.RunPoint("XR0", 27, "1/4", "0", 4096, (32, 64), batches=8)
QE_PLAN = [qe.Command("sector", 9, "1/3", "0", ("1/4", "1/2"), "T"),
           qe.Command("point", 9, "1/3", "0", ("1/4", "1/2"), "T"),
           qe.Command("point", 9, "1/3", "1/9", ("1/4", "1/2"), "T"),
           qe.Command("point", 9, "1/3", "-1/9", ("1/4", "1/2"), "T"),
           qe.Command("point", 9, "1/3", "1/18", ("1/4", "1/2"), "T")]
SC = c.scored("probe")


def out(*parts):
    print("|".join(str(p) for p in parts))


def t(x):
    """The text of a value: an int, a rational (30 significant digits, nearest), an interval or a radical (its 320-bit
    enclosure, outward), an Ext (None for an infinite end), or a container of those."""
    if x is None:
        return "none"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, str)):
        return str(x)
    if isinstance(x, Iv):
        return "[%s,%s]" % (fmt(x.lo, SIG, "down"), fmt(x.hi, SIG, "up"))
    if isinstance(x, Ext):
        return "[%s,%s]" % ("-inf" if x.lo is None else fmt(x.lo, SIG, "down"),
                            "+inf" if x.hi is None else fmt(x.hi, SIG, "up"))
    if isinstance(x, Rad):
        return "rad" + t(x.iv())
    if isinstance(x, (tuple, list)):
        return "(" + ",".join(t(y) for y in x) + ")"
    if isinstance(x, dict):
        return "{" + ",".join("%s:%s" % (k, t(x[k])) for k in sorted(x)) + "}"
    return fmt(x, SIG)


def guarded(label, fn):
    try:
        return fn()
    except (c.StageBStop, m.Lost) as ex:
        return "raised_%s" % getattr(ex, "reason", getattr(ex, "why", ""))


def part_series():
    for label, kind, rid, text, b, st in series.check_frozen():
        out("SERIES", rid, label, text, t(b), st)
    for d, y, n in (("1/3", "1/9", 9), ("1/3", "1/18", 9), ("1/4", "1/40", 27), ("1/4", "0", 27)):
        dd, yy = fr(d), fr(y)
        for tt in ("1/4", "1/2", "1", "2"):
            law = series.Law(dd, n * yy * yy, fr(tt))
            out("LAW", d, y, n, tt, t(law.EB), t(law.EB2), t(law.var), t(law.rho()), t(law.nstar()), t(law.Z(64)),
                t(law.f_lin(n)), t(law.C), t(law.S))
            out("CLOSED", d, y, tt, t(series.b2b4_iv(dd, fr(tt))), t(series.b2b4(dd, fr(tt))),
                t(series.kappa_q(dd, fr(tt), n)), t(series.d2_law(dd, yy, fr(tt))),
                t(series.D_classical(dd, fr(tt), yy)), t(series.series_remainder(dd, fr(tt))),
                t(series.sinh_iv(dd, fr(tt))))
        out("CLOSED", d, t(series.d2_coefficient(dd)), t(series.lowest_terms(dd)),
            t(series.r_two_term(dd, fr(1, 2), yy) if yy != 0 else None))


def part_qe():
    reads = qe.parse_qe(os.path.join(DATA, "qe9", "QE.hbp"), QE_PLAN, os.path.join(DATA, "qe9", "QE-COST.hbp"))
    for k in sorted(reads):
        r = reads[k]
        out("QE", t(k), t(r.B()), t(r.e_B()), t(r.B_iv()), t(r.absB_iv()), t(r.A()), t(r.A_err()), t(r.eps()),
            t(r.C2_iv()), t(r.f_iv()), t(r.QW_iv()), t(r.D2_iv()), rows_q._sign_text(r))
        out("QE_NSTAR", t(k), t(guarded("ns", lambda r=r: rows_q.q07_nstar(r))),
            t(guarded("nn", lambda r=r: rows_q.q07_nstar_normal(r))))
        if r.v["B_e18"] == 0:
            res = rows_q.q01_zero(r)
            out("Q01_ZERO", t(k), res[0], t(res[1]))
    band = c.Band(fr(99, 400), fr(101, 400))
    for tt in ("1/4", "1/2"):
        sec, pnt = reads[("sector", 9, "1/3", "0", tt)], reads[("point", 9, "1/3", "0", tt)]
        res = rows_q.q01_same(sec, pnt)
        out("Q01_SAME", tt, res[0], t(res[1]))
        rp, rm = reads[("point", 9, "1/3", "1/9", tt)], reads[("point", 9, "1/3", "-1/9", tt)]
        res = rows_q.q02_parity(rp, rm)
        out("Q02", tt, res[0], t(res[1]))
        rh, rf = reads[("point", 9, "1/3", "1/18", tt)], rp
        ratio = rows_q.q03_ratio(rh, rf)
        out("Q03", tt, t(ratio), rows_q._interval_read("T", "R" + tt, "N9", "interval", SC, ratio, band).row_text())
        for y, r in (("1/9", rp), ("-1/9", rm), ("1/18", rh)):
            d = rows_q.q04_D(r, y, tt)
            out("Q04", y, tt, t(d), rows_q._interval_read("T", "D" + tt, "N9", "interval", SC, d,
                                                          c.Band(0, fr(1, 20), lo_open=True, hi_open=True)).row_text())
        qa = guarded("q", lambda: Ext.of(rows_q.q04_D(rh, "1/18", tt)))
        out("Q04_PIECES", tt, t(qa), t(guarded("q", lambda: rows_q.quotient(rows_q.q04_D(rh, "1/18", tt),
                                                                           rows_q.q04_D(rp, "1/9", tt)))))


def with_trailer(text, rc=0, rc_reader=0, steps=None):
    if steps is None:
        steps = text.split("|steps=", 1)[1].split("|", 1)[0]
    if STEPS_IN_TRAILER:
        return text + "rc=%d rc_reader=%d steps=%s\n" % (rc, rc_reader, steps)
    return text + "rc=%d rc_reader=%d\n" % (rc, rc_reader)


def read_text(p):
    with open(p, "rb") as f:
        return f.read().decode("ascii")


def write(p, text):
    with open(p, "wb") as f:
        f.write(text.encode("ascii"))


def load_point(tmp, spec, names):
    d = os.path.join(tmp, spec.id)
    os.makedirs(d)
    for i, nm in enumerate(names):
        write(os.path.join(d, "%d.hbp" % i), with_trailer(read_text(os.path.join(DATA, "agg", nm))))
        write(os.path.join(d, "%d.eng.err" % i), "")
    return c.load_point(d, spec)


def point_rows(pt, fz):
    pid = pt.spec.id
    out("POINT", pid, t(pt.steps), t(pt.not_measured), pt.M(), pt.M("ctrl", "V1"), t(pt.atoms()), t(pt.lat()))
    q = e.lock_q(fz)
    for step in pt.steps:
        for v in c.VARIANTS:
            scope = "all" if v == "VNC" else "ctrl"
            vr, s = pt.vr(step, v, scope), pt.sums(step, v, "all", scope)
            out("VR", pid, step, v, t(vr), t(s), t(pt.sums(step, v, "nonatom", scope)))
            pi = m.PiHat(vr)
            out("PI", pid, step, v, t(pi.x), t(pi.se2), t(pi.e()), t(pi.bracket()))
            out("MOM", pid, step, v, t(m.rho_u(s)), t(m.bbar2_u(s)), t(m.nstar_of([s])),
                t(m.nstar_jackknife(pt.per_call_sums(step, v, "all", scope))))
            for n in c.BLOCK_SIZES:
                z = m.Zn(pt.blk(step, v, n, scope))
                out("ZN", pid, step, v, n, t(z.Z), t(z.se2), t(z.e3()))
            out("H8", pid, step, v, t([(a, b, x, c.h8(b, x, vr["amb"])) for a, b, x in c.h8_pairs(vr["sec"])]))
            out("B16", pid, step, v, t(c.b16(vr["sec"], vr["amb"], vr["mp"])), c.b16_threshold_D(vr["mp"]))
            for r in (e.h8_read("T", pt, step, v, ("pi", "mir", "br", "bi")),
                      e.signflip_point_read("T", pt, step, v, "br", True, "probe"),
                      e.signflip_point_read("T", pt, step, v, "bi", False, "probe"),
                      m.b16_read("T", "b16", "at", SC, vr, m.UNIFORM),
                      m.pi_report("T", "pi", "at", SC, pi),
                      m.pi_read("T", "pi", "at", SC, pi, "0.01", m.pi_tol(fr(1, 100), pi.M, fr(1, 5))),
                      m.excess_read("T", "ex", "at", SC, vr, "none"),
                      m.z_read("T", "zi", "at", SC, pt, step, v, scope, c.BLOCK_SIZES, "iid"),
                      m.z_read("T", "zz", "at", SC, pt, step, v, scope, c.BLOCK_SIZES, "zero"),
                      m.z_read("T", "zt", "at", SC, pt, step, v, scope, c.BLOCK_SIZES, "tol", fr(1, 50)),
                      e.x2_report("T", "x2", "at", SC, vr, "none")) + tuple(e.uniform_reads("T", pt, step, v, SC)):
                out("READ", r.row_text())
            if v != "VNC":
                lo, hi, se2, a, rr, cm = m.paired(pt, step, v)
                out("PAIRED", pid, step, v, t(lo), t(hi), t(se2), t(cm))
                out("BRACKET", pid, step, v, m.sampled_bracket(lo, hi, 0, rr.bracket()[0] * fr(1, 20),
                                                               rr.bracket()[1] * fr(1, 20), c.se(se2, 3)))
        for r in (m.zband_read("T", "zb", "at", SC, pt, step, 4, c.MET, "none"),) + tuple(e.mode0_reads("T", pt, step)) \
                + tuple(e.lock_reads("T", pt, step, q, SC)) + tuple(e.nl_reads("T", pt, step, SC)):
            out("READ", r.row_text())
    out("LOCK_Q", t(q))


def run_dir(tmp, ids):
    d = os.path.join(tmp, "run")
    os.makedirs(d)
    for nm in sorted(os.listdir(os.path.join(DATA, "run"))):
        if not any(nm.startswith(i + ".") for i in ids):
            continue
        src = os.path.join(DATA, "run", nm)
        if nm.endswith(".rc"):
            rc_line = read_text(src).split("\n")[0]
            write(os.path.join(d, nm), (rc_line if STEPS_IN_TRAILER else rc_line.split(" ")[0]) + "\n")
        else:
            shutil.copy(src, os.path.join(d, nm))
    return d


def part_runs(tmp):
    d = run_dir(tmp, ("XR1", "XR0"))
    rs = {spec.id: runs.load_run(d, spec) for spec in (XR1, XR0)}
    for rid, r in sorted(rs.items()):
        out("RUN", rid, t(r.steps), t(r.not_measured), r.M(), len(r.batches))
        for step in r.steps:
            out("RUN_STEP", rid, step, t(r.pooled(step)), t(r.mean_br(step)), t(r.moment2(step)), t(r.nstar(step)))
    for step in (32, 64):
        r = e.ratio_read("T", "ratio", step, rs["XR0"], rs["XR1"], SC, "none")
        out("READ", r.row_text())
    xs = [b.rec[64]["br"] for b in rs["XR1"].batches]
    ys = [b.rec[64]["br2"] for b in rs["XR1"].batches]
    out("SE", t(c.mean_se2(xs)), t(c.ratio_paired(xs, ys)), t(c.batch_means(xs, [512] * 8)),
        t(c.ratio_indep(fr(3, 7), fr(1, 1000), fr(5, 9), fr(1, 2000))), t(c.se2_pi(fr(1, 7), 4096)),
        t(c.se2_binomial(17, 4096)), t(c.jackknife(lambda bs: fr(sum(bs), len(bs)), xs)))


def part_sides(excl):
    if not excl:
        return
    for a, b in (("X1.0", "X0.0"), ("X1.1", "X0.1")):
        sa, sb = (c.SideFile(os.path.join(excl, n + ".side")) for n in (a, b))
        acc = c.paired_side_sums(sa, sb)
        for k in sorted(acc):
            x = acc[k]
            out("SIDE_PAIR", a, b, t(k), t(x), c.signflip(x["S"], x["Q"], x["RB"], x["RQ"]))


LENS_ROWS_E = tuple(rid for rid, _ in m.ROWS if rid != "E16")


def lens_read(r):
    """One read by its fields: the band by its ends and open flags, every number at 30 digits."""
    b = r.band
    band = "band(%s,%s,%s,%s)" % (t(b.lo), t(b.hi), t(b.lo_open), t(b.hi_open)) if isinstance(b, c.Band) else t(b)
    out("LENS_READ", r.row, r.rid, r.at, r.kind, t(r.scored), r.scoring.why, r.outcome, t(r.value), t(r.lo), t(r.hi),
        band, t(r.frozen), t([tuple(d) for d in r.detail]))


def lens_verdict(v):
    for r in v.reads:
        lens_read(r)
    out("LENS_VERDICT", v.row, v.verdict, v.falsifier, t(v.counts()))


def lens_runs(tmp, lens):
    """LENS_DIR/run (R1-R4) in this version's grammar: the .rc files with or without their steps."""
    d = os.path.join(tmp, "lens-run")
    os.makedirs(d)
    for nm in sorted(os.listdir(os.path.join(lens, "run"))):
        src = os.path.join(lens, "run", nm)
        if nm.endswith(".rc"):
            rc_line = read_text(src).split("\n")[0]
            write(os.path.join(d, nm), (rc_line if STEPS_IN_TRAILER else rc_line.split(" ")[0]) + "\n")
        else:
            shutil.copy(src, os.path.join(d, nm))
    return runs.load_runs(d)


def part_lens(lens, fz):
    qv, reads = rows_q.read_q(os.path.join(lens, "QE.hbp"), os.path.join(lens, "QE-COST.hbp"),
                              os.path.join(lens, "GUARD.hbp"), fz, os.path.join(lens, "QE-RC.hbp"))
    for v in qv:
        lens_verdict(v)
    tmp = tempfile.mkdtemp(prefix="stripes-probe-lens-")
    try:
        x1 = load_point(tmp, X1, ("X1.0.agg", "X1.1.agg"))
        x0 = load_point(tmp, X0, ("X0.0.agg", "X0.1.agg"))
        rs = lens_runs(tmp, lens)
        for rid, r in sorted(rs.items()):
            out("LENS_RUN", rid, len(r.batches), t(r.steps), t(r.not_measured), r.attempts)
        pts = {pid: x0 if spec.y == "0" else x1 for pid, spec in c.DUMP_POINTS.items()}
        for v in m.read_e_mom(m.Inputs(pts, rs, reads), fz, rows=LENS_ROWS_E):
            lens_verdict(v)
    finally:
        shutil.rmtree(tmp)


def main():
    fz = frozen.load()
    c.check_tables(fz)
    c.check_exposure_text(fz)
    qe.check_plan(fz)
    out("TABLES", fz.sha256, len(c.DUMP_POINTS), len(c.RUN_POINTS), len(qe.PLAN))
    if len(sys.argv) == 4 and sys.argv[2] == "--lens":
        part_lens(os.path.abspath(sys.argv[3]), fz)
        return 0
    part_series()
    part_qe()
    tmp = tempfile.mkdtemp(prefix="stripes-probe-")
    try:
        for spec, names in ((X1, ("X1.0.agg", "X1.1.agg")), (X0, ("X0.0.agg", "X0.1.agg"))):
            point_rows(load_point(tmp, spec, names), fz)
        part_runs(tmp)
    finally:
        shutil.rmtree(tmp)
    part_sides(sys.argv[2] if len(sys.argv) > 2 else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
