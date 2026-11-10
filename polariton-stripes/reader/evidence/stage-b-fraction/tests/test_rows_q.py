"""Rows Q01-Q07 end to end on a synthetic QE file for the whole frozen plan (QR1-QR5).

The synthetic rows are built from the design-side closed forms: <B> = N y^2 (b2 (1 + kappa_q) + y^2 b4), so that
c = 1 in Q06; Q_W = EB2_lin (t <= 1) or 0.9 EB2_lin (t = 2); A odd in y. Every row then reads MET; the tests also
plant faults and drop rows."""

import os
import unittest

from stripes_read_b import common as c
from stripes_read_b import frozen, qe, rows_q, series
from stripes_read_b.exact import fr, ipow, parse_rat
from stripes_read_b.hbp import parse_row, sha256_hex

from .util import QE9, TempDir, read, write

E18 = ipow(10, 18)


def _floor(x):
    return x.numerator // x.denominator


def _template():
    ln = read(os.path.join(QE9, "QE.hbp")).split("\n")[4]
    return parse_row(ln, qe.READ_KIND, qe.READ_KEYS)[1]


def synth_row(mode, n, y, t, qw_scale=None, b_scale=1):
    yy, tt = parse_rat(y), parse_rat(t)
    states = sum(q // 2 + 1 for q in range(n + 1))
    ab = states * 120 if mode == "point" else (n // 2 + 1) * 104
    law = series.Law(fr(-1, 4), n * yy * yy, tt)
    if yy == 0:
        b = fr(0)
        a = 0
    else:
        b2, b4 = series.b2b4(fr(-1, 4), tt)
        k = series.kappa_q(fr(-1, 4), tt, n).mid()
        b = n * yy * yy * (b2 * (1 + k) + yy * yy * b4) * b_scale
        a = (1 if yy > 0 else -1) * 123456789012345
    qw = law.EB2.mid() * (qw_scale if qw_scale is not None else (1 if tt <= 1 else fr(9, 10)))
    f = law.f_lin(n).mid()
    c2 = (qw - n * f * fr(1, 2) - fr(1, 4)) * fr(2, n * (n - 1))
    vals = {"N": str(n), "K": str(n), "even_states": str(states), "array_bytes": str(ab), "u": "1", "x": "-5/4",
            "y": y, "delta": "-1/4", "t": t, "window": "2^-6", "B_e18": str(_floor(b * E18)),
            "D2_e18": str(_floor(2 * abs(b) * E18 * fr(1, n))), "A_e18": str(a), "A1_e18": str(2 * abs(a) // n),
            "C2_e18": str(_floor(c2 * E18)), "f_e18": str(_floor(f * E18)), "eps_e18": "1000",
            "A1_err_e18": "1000"}
    out = []
    for key, v in _template():
        out.append((key, vals.get(key, v)))
    return qe.READ_KIND + "|" + "|".join("%s=%s" % kv for kv in out[:-1]) + "|json=0"


def synth_file(skip=(), edit=None):
    lines = []
    for cmd in qe.PLAN:
        for t in cmd.times:
            key = (cmd.mode, cmd.N, cmd.y, t)
            if key in skip:
                continue
            kw = edit(key) if edit else {}
            lines.append(synth_row(cmd.mode, cmd.N, cmd.y, t, **kw))
    return "\n".join(lines) + "\n"


def run_rows(text):
    with TempDir() as d:
        p = os.path.join(d, "QE.hbp")
        write(p, text)
        vs, reads = rows_q.read_q(p)
    return {v.row: v for v in vs}


_BASE = {}


def base():
    if "v" not in _BASE:
        _BASE["v"] = run_rows(synth_file())
    return _BASE["v"]


class AllMet(unittest.TestCase):
    def test_every_row_met(self):
        vs = base()
        self.assertEqual({k: v.verdict for k, v in vs.items()}, {r: c.MET for r in vs})

    def test_counts(self):
        vs = base()
        cnt = {k: (v.counts()["reads"], v.counts()["scored"]) for k, v in vs.items()}
        self.assertEqual(cnt, {"Q01": (28, 28), "Q02": (14, 7), "Q03": (14, 11), "Q04": (6, 5), "Q05": (5, 2),
                               "Q06": (12, 4), "Q07": (26, 9)})

    def test_scored_reads(self):
        vs = base()
        rr = {(v.row, r.rid) for v in vs.values() for r in v.reads if not r.scored}
        self.assertIn(("Q03", "R07"), rr)  # (729, 1/27->1/54, t=1/2)
        self.assertIn(("Q03", "L"), rr)
        self.assertIn(("Q04", "ratio_b_N729"), rr)
        self.assertNotIn(("Q04", "ratio_b_N81"), rr)
        self.assertIn(("Q07", "QW_y0_t2"), rr)
        self.assertNotIn(("Q07", "ns_y0_t2"), rr)
        self.assertIn(("Q06", "c_y1/54_t2"), rr)
        self.assertNotIn(("Q06", "c_y1/108_t1/2"), rr)

    def test_q06_c_is_one(self):
        r = [x for x in base()["Q06"].reads if x.rid == "c_y1/54_t1"][0]
        self.assertTrue(r.lo < 1 < r.hi)
        self.assertTrue(r.hi - r.lo < fr(1, 50))


class Faults(unittest.TestCase):
    def test_missing_rows_not_measured(self):
        skip = {("point", 729, "1/54", "1"), ("sector", 6561, "0", "4")}
        vs = run_rows(synth_file(skip=skip))
        q05 = {r.rid: r.verdict for r in vs["Q05"].reads}
        self.assertEqual((q05["dR2"], q05["dR3"]), (c.NOT_MEASURED, c.NOT_MEASURED))
        self.assertEqual(vs["Q05"].verdict, c.NOT_MEASURED)  # both scored reads lost
        self.assertEqual(vs["Q03"].verdict, c.NOT_RESOLVED)  # some scored reads lost, the others MET
        self.assertEqual(vs["Q01"].verdict, c.NOT_RESOLVED)
        self.assertEqual(vs["Q01"].counts()[c.NOT_MEASURED], 1)

    def test_all_rows_missing(self):
        vs = run_rows("")
        self.assertEqual({v.verdict for v in vs.values()}, {c.NOT_MEASURED})

    def test_q06_wrong_size(self):
        # c = 0: the quantum correction absent
        def edit(key):
            mode, n, y, t = key
            if n == 729 and y in ("1/54", "1/108") and t == "1":
                return {"b_scale": 1 - series.kappa_q(fr(-1, 4), 1, 729).mid()}
            return {}
        vs = run_rows(synth_file(edit=edit))
        self.assertEqual(vs["Q06"].verdict, c.NOT_MET)

    def test_q05_and_q03_power_one(self):
        # B(1/108) at t=1 doubled: R(1/54) -> about 1/2 (one insertion)
        def edit(key):
            return {"b_scale": 2} if key == ("point", 729, "1/108", "1") else {}
        vs = run_rows(synth_file(edit=edit))
        self.assertEqual(vs["Q03"].verdict, c.NOT_MET)
        self.assertEqual(vs["Q05"].verdict, c.NOT_MET)
        self.assertEqual(vs["Q07"].verdict, c.NOT_MET)

    def test_exposed_read_cannot_fail_a_row(self):
        # the same fault at t=2 only touches read-and-report reads of Q03 (R13, L) and Q05 (dR4, dR5)
        def edit(key):
            return {"b_scale": 2} if key == ("point", 729, "1/216", "2") else {}
        vs = run_rows(synth_file(edit=edit))
        self.assertEqual(vs["Q03"].verdict, c.MET)
        self.assertEqual(vs["Q05"].verdict, c.MET)

    def test_q02_parity_broken(self):
        def edit(key):
            return {"b_scale": fr(1001, 1000)} if key == ("point", 81, "-1/54", "2") else {}
        vs = run_rows(synth_file(edit=edit))
        self.assertEqual(vs["Q02"].verdict, c.NOT_MET)

    def test_q07_qw_off(self):
        def edit(key):
            return {"qw_scale": fr(11, 10)} if key == ("point", 729, "1/108", "1") else {}
        vs = run_rows(synth_file(edit=edit))
        self.assertEqual(vs["Q07"].verdict, c.NOT_MET)


def set_fields(text, n, y, t, **fields):
    """The synthetic QE file with fields of the READ row at (point, N, y, t) replaced."""
    out = []
    for ln in text.split("\n"):
        if ln.startswith(qe.READ_KIND + "|N=%d|" % n) and "|y=%s|" % y in ln and "|t=%s|" % t in ln:
            parts = ln.split("|")
            for k, part in enumerate(parts):
                key = part.split("=", 1)[0]
                if k and key in fields:
                    parts[k] = "%s=%s" % (key, fields[key])
            ln = "|".join(parts)
        out.append(ln)
    return "\n".join(out)


def reads_of(v):
    return {r.rid: r for r in v.reads}


class Unbounded(unittest.TestCase):
    """Rule READ3 where an interval reaches 0 or infinity: the failure branches of the prediction (review B1, B2)."""

    def test_q04_certified_negative_denominator(self):
        # probe P1: B(729, 1/27, t=1/4) scaled by 0.95, so D(1/4) is about -0.008, certified
        vs = run_rows(synth_file(edit=lambda k: {"b_scale": fr(95, 100)} if k == ("point", 729, "1/27", "1/4")
                                 else {}))
        r = reads_of(vs["Q04"])["ratio_a_N729"]
        self.assertTrue(r.scored)
        self.assertEqual(r.outcome, c.MISS)
        self.assertTrue(r.hi < 0)  # a bounded negative ratio
        self.assertEqual(vs["Q04"].verdict, c.NOT_MET)
        self.assertEqual(vs["Q04"].falsifier, "ratio_a_N729:" + frozen.load().predict("Q04")["falsifier"])

    def test_q04_denominator_across_zero(self):
        # |B| = 1/16 at (729, 1/27, t=1/4): D(1/4) = 16|B| - 1 holds 0 inside +-16 e_B; D(1/8)/D(1/4) is then
        # (-inf, a] or [b, +inf) with a < 0 and b far above 3/10: MISS
        text = set_fields(synth_file(), 729, "1/27", "1/4", B_e18=str(E18 // 16), D2_e18=str(E18 // 8 // 729))
        vs = run_rows(text)
        r = reads_of(vs["Q04"])["ratio_a_N729"]
        self.assertEqual((r.outcome, r.lo, r.hi, r.value), (c.MISS, "-inf", "+inf", "unbounded"))
        self.assertIn("_or_", dict(r.detail)["interval"])
        self.assertEqual(vs["Q04"].verdict, c.NOT_MET)
        # the pieces themselves
        d4 = rows_q.q04_D(parse_text(text)[("point", 729, "-1/4", "1/27", "1/4")], "1/27", "1/4")
        self.assertTrue(d4.lo < 0 < d4.hi)

    def test_q07_and_q03_vanishing_B(self):
        # probe P2: B_e18 = 0 at the scored point (729, 1/108, t=1)
        vs = run_rows(set_fields(synth_file(), 729, "1/108", "1", B_e18="0", D2_e18="0"))
        ns = reads_of(vs["Q07"])["ns_y1/108_t1"]
        self.assertEqual((ns.scored, ns.outcome, ns.hi), (True, c.MISS, "+inf"))
        self.assertEqual(vs["Q07"].verdict, c.NOT_MET)
        self.assertIn("ns_y1/108_t1", vs["Q07"].falsifier)
        r12 = reads_of(vs["Q03"])["R12"]  # (729, 1/108 -> 1/216, t=1): [a, +inf), a far above the band
        self.assertEqual((r12.scored, r12.outcome, r12.hi), (True, c.MISS, "+inf"))
        self.assertEqual(vs["Q03"].verdict, c.NOT_MET)
        self.assertEqual(reads_of(vs["Q06"])["c_y1/108_t1"].outcome, c.MISS)  # the literal falsifier B_e18 <= 0

    def test_q05_vanishing_B(self):
        vs = run_rows(set_fields(synth_file(), 729, "1/54", "1", B_e18="0", D2_e18="0"))
        d3 = reads_of(vs["Q05"])["dR3"]  # (729, 1/54 -> 1/108, t=1): R - 1/4 in [a, +inf)
        self.assertEqual((d3.scored, d3.outcome, d3.hi), (True, c.MISS, "+inf"))
        self.assertEqual(vs["Q05"].verdict, c.NOT_MET)
        self.assertEqual(reads_of(vs["Q03"])["R11"].outcome, c.MISS)

    def test_richardson_unbounded(self):
        # B(1/108) = 0 at t=2: R(1/108) = [a, +inf), so L = (4 R(1/108) - R(1/54))/3 is a half-line too; L is
        # read-and-report (X08), so the row stays MET
        vs = run_rows(set_fields(synth_file(), 729, "1/108", "2", B_e18="0", D2_e18="0"))
        rs = reads_of(vs["Q03"])
        self.assertEqual((rs["L"].scored, rs["L"].outcome, rs["L"].hi), (False, c.MISS, "+inf"))
        self.assertEqual(vs["Q03"].verdict, c.MET)

    def test_q06_positive_B_inside_its_certificate(self):
        # probe probe_q06.py: B_e18 = 1 at the scored read (729, 1/108, t=1/2): c near -1/kappa_q, certified outside
        vs = run_rows(set_fields(synth_file(), 729, "1/108", "1/2", B_e18="1", D2_e18="0"))
        r = reads_of(vs["Q06"])["c_y1/108_t1/2"]
        self.assertEqual((r.scored, r.outcome), (True, c.MISS))
        self.assertTrue(fr(1543, 1) < r.lo < r.hi < fr(1544, 1))
        self.assertEqual(vs["Q06"].verdict, c.NOT_MET)
        self.assertEqual(vs["Q06"].falsifier, "c_y1/108_t1/2:" + frozen.load().predict("Q06")["falsifier"])

    def test_extended_arithmetic(self):
        from stripes_read_b.exact import Ext, Iv, quotient
        self.assertEqual(len(quotient(Iv(1, 2), Iv(1, 4))), 1)
        (p,) = quotient(Iv(1, 2), Iv(0, 4))
        self.assertEqual((p.lo, p.hi), (fr(1, 4), None))
        (p,) = quotient(Iv(-2, -1), Iv(-4, -1))
        self.assertEqual((p.lo, p.hi), (fr(1, 4), 2))
        a, b = quotient(Iv(1, 2), Iv(-1, 4))
        self.assertEqual((a.lo, a.hi, b.lo, b.hi), (None, -1, fr(1, 4), None))
        a, b = quotient(Iv(-2, -1), Iv(-1, 4))
        self.assertEqual((a.lo, a.hi, b.lo, b.hi), (1, None, None, fr(-1, 4)))
        (p,) = quotient(Iv(-1, 1), Iv(-1, 1))
        self.assertEqual((p.lo, p.hi), (None, None))
        band = c.Band(fr(1, 5), fr(3, 10))
        self.assertEqual(c.read3_pieces([Ext(fr(1, 2), None)], band), c.MISS)
        self.assertEqual(c.read3_pieces([Ext(fr(1, 4), None)], band), c.NOT_RESOLVED)
        self.assertEqual(c.read3_pieces([Ext(None, -1), Ext(fr(1, 2), None)], band), c.MISS)
        self.assertEqual(c.read3_pieces([Ext(None, fr(1, 4)), Ext(fr(1, 2), None)], band), c.NOT_RESOLVED)
        self.assertEqual(c.read3_pieces([Ext(fr(1, 4), fr(1, 4))], band), c.MET)
        self.assertEqual(c.read3_pieces([Ext(0, None)], c.Band(0, None)), c.MET)
        x = (Ext(1, None).scale(4) - Ext(0, 1)).scale(fr(1, 3))
        self.assertEqual((x.lo, x.hi), (1, None))
        self.assertEqual((Ext(1, None).scale(-2).lo, Ext(1, None).scale(-2).hi), (None, -2))
        y = Ext(-1, None).times_pos(Iv(2, 3))
        self.assertEqual((y.lo, y.hi), (-3, None))


def parse_text(text):
    """The QE reads of a synthetic QE file (parse_qe reads it whole, so the file goes with the folder)."""
    with TempDir() as d:
        p = os.path.join(d, "QE.hbp")
        write(p, text)
        return qe.parse_qe(p)


class NormalOrder(unittest.TestCase):
    def test_reports_the_named_quantity(self):
        # "normal-order (Q_W-1/4)/<B>^2-1 read and report": the value is that quantity, its ratio to n*_lin beside
        vs = base()
        r = reads_of(vs["Q07"])["nsno_y1/54_t1"]
        q = parse_text(synth_file())[("point", 729, "-1/4", "1/54", "1")]
        nn = rows_q.q07_nstar_normal(q)
        self.assertEqual((r.lo, r.hi, r.scored), (nn.lo, nn.hi, False))
        self.assertIn("over_nstar_lin-1", dict(r.detail))


class ReadFile(unittest.TestCase):
    def test_file(self):
        fz = frozen.load()
        rf = c.ReadFile(fz)
        with TempDir() as d:
            p = os.path.join(d, "QE.hbp")
            write(p, synth_file())
            vs, _ = rows_q.read_q(p)
            rf.add_input("QE", p)
            for v in vs:
                rf.add(v)
            out = os.path.join(d, "READ.hbp")
            rf.write(out)
            lines = read(out).split("\n")[:-1]
        kinds = [ln.split("|", 1)[0] for ln in lines]
        self.assertEqual(kinds[0], "STRIPES_READ_HEAD")
        self.assertEqual(kinds.count("STRIPES_VERDICT"), 7)
        self.assertEqual(kinds.count("STRIPES_READ"), 105)
        for ln in lines:
            parse_row(ln)
        end = dict(x.split("=", 1) for x in lines[-1].split("|")[1:])
        self.assertEqual(end["sha256"], sha256_hex("".join(x + "\n" for x in lines[:-1]).encode("ascii")))
        self.assertEqual(int(end["rows"]), len(lines) - 1)
        v = [ln for ln in lines if ln.startswith("STRIPES_VERDICT|row=Q03|")][0]
        self.assertIn("|reads=14|scored=11|report=3|met=11|", v)


if __name__ == "__main__":
    unittest.main()
