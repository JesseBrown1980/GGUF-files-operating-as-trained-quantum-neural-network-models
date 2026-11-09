"""Rows E09-E19 on synthetic pooled aggregates built by hand: no engine output and no value from a receipt.

A synthetic dump point is a few CallBlocks of 2^18 samples each (block 0 holds every variant, as the calls below
`all` do; the others hold VNC only). Its counts and sums are chosen from the frozen values so that every row reads MET
(E17: no verdict). Each NotMet test plants one fault and checks that the row turns NOT_MET; the other tests check the
reads, the scoring, rule STOP and the helpers on cases worked by hand."""

import os
import unittest

from stripes_read_b import common as c
from stripes_read_b import frozen, qint, runs, series
from stripes_read_b import rows_e_mom as m
from stripes_read_b.exact import Iv, Rad, dec, div, fr, parse_rat
from stripes_read_b.hbp import parse_row, sha256_hex

from .util import AGG, RUN, X1, XR1, TempDir, point_dir, read, with_trailer

CHUNK = 1 << 18
Q = 1 << 60
VNC = "VNC"


def _floor(x):
    return qint.floor(fr(x))


def _ceil(x):
    return qint.ceil(fr(x))


# ---------------------------------------------------------------------------------------------------------------------
# Builders.


def vr_block(M, pi, dev=0, atoms=0, amb=0, br_amb=0):
    """AGG_VR of M samples: `atoms` atoms with br > 0, Pi_hat about pi over all M, sector 0 raised by dev M' and
    sector 8 lowered by as much."""
    mp = M - atoms
    d = _floor(2 * pi * M) - atoms
    pos = (mp - br_amb + d) // 2
    neg = mp - br_amb - pos
    base = (mp - amb) // 16
    sec = [base] * 16
    sec[0] += (mp - amb) - 16 * base
    k = _floor(dev * mp)
    sec[0] += k
    sec[8] -= k
    return {"M": M, "atoms": atoms, "xatoms": atoms, "xatom_bi_nz": 0, "mp": mp, "na_bi0": 0, "sec": sec, "amb": amb,
            "br_pos": pos, "br_neg": neg, "br_amb": br_amb, "bi_pos": mp // 2, "bi_neg": mp - mp // 2, "bi_amb": 0,
            "at_br_pos": atoms, "at_br_neg": 0, "at_br_amb": 0, "at_bi_pos": 0, "at_bi_neg": 0, "at_bi_amb": atoms}


def sum_block(M, rho, scale=1, s2ps=Q, sign=1):
    """AGG_SUM set=all with Sum |B|^2 = M s2ps and rho_u about rho (Sum B real)."""
    S2 = M * s2ps
    br = 0 if rho == 0 else sign * _floor(qint.isqrt(S2 + _floor(rho * (M - 1) * S2)) * fr(scale))
    return {"m": M, "br": br, "bi": 0, "br2": S2, "bi2": 0, "brbi": 0, "bbr": 0, "bbi": 0, "bbr2": 0, "bbi2": 0}


def zero_sums():
    return {k: 0 for k in ("m", "br", "bi", "br2", "bi2", "brbi", "bbr", "bbi", "bbr2", "bbi2")}


def blk_block(M, S2, rho, n, zscale=1):
    """AGG_BLK with Z_n = (1 + (n-1) rho) zscale and z_b variance (1-rho)^2 + 2 n rho (1-rho)."""
    K = M // n
    z = (1 + (n - 1) * rho) * fr(zscale)
    s2 = _floor(z * S2)
    var = (1 - rho) * (1 - rho) + 2 * n * rho * (1 - rho)
    s4 = _ceil((s2 * s2 + var * S2 * S2 * (K - 1) * fr(1, K)) * fr(1, K))
    return {"K": K, "s2": s2, "s4": s4, "w": S2, "w2": 0, "sw": 0}


def cmp_block(vv, ref, disc):
    """AGG_CMP of a variant against VNC on the same samples (no atoms, no ambiguous sign), with about disc M
    discordant samples."""
    M = vv["mp"]
    delta = vv["br_pos"] - ref["br_pos"]
    D = max(_floor(disc * M), abs(delta))
    if (D - delta) % 2:
        D += 1
    t1, t3 = (D + delta) // 2, (D - delta) // 2
    t0, t4 = vv["br_pos"] - t1, vv["br_neg"] - t3
    if min(t0, t4) < 0:
        raise AssertionError("cmp_block: negative cell")
    return {"common": M, "br": [t0, t1, 0, t3, t4, 0, 0, 0, 0], "bi": [M] + [0] * 8, "cert2": 0, "mis": 0,
            "cert2_big_both": 0, "mis_big_both": 0, "cert2_big_any": 0, "mis_big_any": 0}


_LAW = {}


def law_rho(pid, step):
    key = (pid, step)
    if key not in _LAW:
        spec = c.DUMP_POINTS[pid]
        y = parse_rat(spec.y)
        r = series.Law(parse_rat(spec.delta), spec.N * y * y, c.t_of_step(step)).rho().mid()
        _LAW[key] = fr(_floor(r * 1000000000), 1000000000)
    return _LAW[key]


def law_nstar(spec, step):
    key = (spec.id, step)
    if key not in _LAW:
        y = parse_rat(spec.y)
        _LAW[key] = series.Law(parse_rat(spec.delta), spec.N * y * y, c.t_of_step(step)).nstar().mid()
    return _LAW[key]


def base_model(pid, step, v, j):
    """The aggregates of every row's MET case: the frozen Pi, rho and B16 verdicts, the linear-law rho elsewhere."""
    spec = c.DUMP_POINTS[pid]
    t = step // 64
    t12 = min(t, 2)
    alt = 1 if j % 2 == 0 else -1
    p = {"pi": fr(0), "rho": fr(0), "dev": fr(0), "disc": fr(3, 10) if v in ("FLIP", "LOCK") else fr(1, 100),
         "scale": 1 + fr(alt, 1000), "s2ps": Q + alt * (Q >> 10)}
    if parse_rat(spec.y) != 0:
        p["rho"] = law_rho(pid, step)
        p["pi"] = fr(1, 100)
    if pid in m.E10_PI:
        p["pi"] = dec(m.E10_PI[pid][t12 - 1])
    if pid in m.E11_PI:
        p["pi"] = dec(m.E11_PI[pid][t12 - 1])
    if pid == "P10":
        p["pi"] = dec("0.233911") if t == 1 else fr(26, 100)
        p["dev"] = fr(1, 100)
    if (pid, v) in m.E15_PI:
        p["pi"] = dec(m.E15_PI[(pid, v)][t12 - 1])
    if v == VNC and pid in m.E13_RHO and t <= 2:
        p["rho"] = dec(m.E13_RHO[pid][t - 1])
    if v == VNC and pid in ("P03", "P04", "P05", "P06", "P08"):
        p["dev"] = fr(3, 1000)
    return p


def model_for(edits):
    def f(pid, step, v, j):
        p = base_model(pid, step, v, j)
        for key in ((pid, "*", "*"), (pid, "*", v), (pid, step, "*"), (pid, step, v)):
            if key in edits:
                p.update(edits[key])
        return p
    return f


def make_point(pid, model, steps=None, lose=()):
    spec = c.DUMP_POINTS[pid]
    steps = tuple(spec.steps if steps is None else steps)
    nch = spec.vnc // CHUNK
    idx = list(range(nch)) if spec.all == 0 else [0] + [spec.all + j for j in range(nch - 1)]
    pt = c.Point(spec)
    for j, i in enumerate(idx):
        if i in lose:
            pt.lost.append((i, "engine_stop_rc4"))
            continue
        variants = c.VARIANTS if (spec.all and i < spec.all) else (VNC,)
        b = c.CallBlock()
        b.call = i
        b.steps = steps
        b.variants = variants
        for step in steps:
            ref = None
            for v in variants:
                p = model(pid, step, v, j)
                vr = vr_block(CHUNK, p["pi"], p["dev"])
                b.vr[(step, v)] = vr
                s = sum_block(CHUNK, p["rho"], p["scale"], p["s2ps"], p.get("sign", 1))
                b.sums[(step, v, "all")] = s
                b.sums[(step, v, "atom")] = zero_sums()
                for n in c.BLOCK_SIZES:
                    b.blk[(step, v, n)] = blk_block(CHUNK, s["br2"], p["rho"], n, p.get("zscale", 1))
                if v == VNC:
                    ref = vr
                else:
                    b.cmp[(step, v)] = cmp_block(vr, ref, p["disc"])
        pt.calls[i] = b
    pt.steps = steps
    pt.not_measured = spec.steps[len(steps):]
    return pt


class FakeBatch:
    def __init__(self, j, rec):
        self.j = j
        self.rec = rec


def make_run(rid, nstar_scale=None, sign=None, steps=None, drop=()):
    """64 batches whose pooled n*_hat is near the linear-law n* (times nstar_scale[step]) and whose mean br has the
    sign sign[step] (default +)."""
    spec = c.RUN_POINTS[rid]
    steps = tuple(spec.steps if steps is None else steps)
    run = runs.Run(spec)
    n = spec.per_batch
    for j in range(spec.batches):
        if j in drop:
            run.lost.append((j, "engine_stop_empty"))
            continue
        alt = 1 if j % 2 == 0 else -1
        rec = {}
        for step in steps:
            ns = law_nstar(spec, step) * fr((nstar_scale or {}).get(step, 1))
            mu = qint.isqrt(_floor(fr(Q, 1 + ns)))
            br = (sign or {}).get(step, 1) * _floor(n * mu * (1 + fr(alt, 100)))
            rec[step] = {"n": n, "br": br, "bi": 0, "br2": n * (Q + alt * (Q >> 10)), "bi2": 0, "brbi": 0,
                         "rb_br": 4 * n, "rb_bi": 0, "rb_br2": 0, "rb_bi2": 0, "rb_brbi": 0}
        run.batches.append(FakeBatch(j, rec))
    run.steps = steps
    run.not_measured = spec.steps[len(steps):]
    return run


class FakeQe:
    def __init__(self, qw):
        self.qw = fr(qw)

    def QW_iv(self):
        e = self.qw * fr(1, 1000000)
        return Iv(self.qw - e, self.qw + e)


E18_KEYS = (("0", "2"), ("1/27", "1"), ("1/54", "1"), ("1/54", "2"), ("1/108", "2"))


def make_qe(scale=None):
    """Q_W equal to 729^2 E[|B_W/N|^2] of the synthetic points (Q at 2^80), times scale[(y, t)]."""
    q = fr(729 * 729 * Q, 1 << 80)
    return {("point", 729, "-1/4", y, t): FakeQe(q * fr((scale or {}).get((y, t), 1))) for y, t in E18_KEYS}


_BASE = {}


def base_points():
    if "p" not in _BASE:
        f = model_for({})
        _BASE["p"] = {pid: make_point(pid, f) for pid in c.DUMP_POINTS}
        _BASE["r"] = {rid: make_run(rid) for rid in c.RUN_POINTS}
    return _BASE["p"], _BASE["r"]


def inputs(edits=None, steps=None, lose=None, run_edits=None, qe_scale=None, with_qe=True):
    edits, steps, lose, run_edits = edits or {}, steps or {}, lose or {}, run_edits or {}
    bp, br = base_points()
    f = model_for(edits)
    pts = {}
    for pid in c.DUMP_POINTS:
        if any(k[0] == pid for k in edits) or pid in steps or pid in lose:
            pts[pid] = make_point(pid, f, steps.get(pid), lose.get(pid, ()))
        else:
            pts[pid] = bp[pid]
    rs = {rid: (make_run(rid, **run_edits[rid]) if rid in run_edits else br[rid]) for rid in c.RUN_POINTS}
    return m.Inputs(pts, rs, make_qe(qe_scale) if with_qe else None)


def verdicts(inp, rows=None):
    return {v.row: v for v in m.read_e_mom(inp, rows=rows)}


def reads_of(v):
    return {r.rid: r for r in v.reads}


def base_verdicts():
    if "v" not in _BASE:
        _BASE["v"] = verdicts(inputs())
    return _BASE["v"]


# ---------------------------------------------------------------------------------------------------------------------
# Helpers on cases worked by hand.


def tiny_point(vr_v, vr_r, cm, v="LOCK"):
    spec = c.DUMP_POINTS["P08"]
    b = c.CallBlock()
    b.call = 0
    b.steps = (64,)
    b.variants = c.VARIANTS
    b.vr[(64, VNC)] = vr_r
    b.vr[(64, v)] = vr_v
    b.cmp[(64, v)] = cm
    pt = c.Point(spec)
    pt.calls[0] = b
    pt.steps = (64,)
    return pt


class Helpers(unittest.TestCase):
    def test_zn(self):
        # |S_b|^2 = 1, 2, 3, 4 over K = 4 blocks with Sum |B|^2 = 5: z_b = 4/5 (1, 2, 3, 4), mean 2, sample variance
        # 16/15, SE^2 = 4/15
        z = m.Zn({"K": 4, "s2": 10, "s4": 30, "w": 5})
        self.assertEqual((z.Z, z.se2), (2, fr(4, 15)))
        with self.assertRaises(c.StageBStop):
            m.Zn({"K": 4, "s2": 10, "s4": 24, "w": 5})  # K s4 < s2^2

    def test_pi_hat_counts_atoms(self):
        v = vr_block(100, 0)
        v.update({"atoms": 5, "mp": 95, "br_pos": 60, "br_neg": 30, "br_amb": 5, "at_br_pos": 4, "at_br_neg": 0,
                  "at_br_amb": 1})
        p = m.PiHat(v)
        self.assertEqual((p.pos, p.neg, p.amb, p.M), (64, 30, 6, 100))
        self.assertEqual(p.x, fr(17, 100))
        self.assertEqual(p.bracket(), (fr(7, 50), fr(1, 5)))
        self.assertEqual(p.se2, fr(10000 - 1156, 4000000))

    def test_e10_falsifier_at_3_se(self):
        # x = 0.025, A/M = 0.015, 3SE = 0.01498: x - 3SE - A/M < 0, but the bracket's low end 0.0175 minus 3SE > 0
        v = vr_block(10000, 0)
        v.update({"br_pos": 5175, "br_neg": 4675, "br_amb": 150})
        p = m.PiHat(v)
        self.assertTrue((Rad.of(p.x) - p.e()).sign() < 0)
        self.assertFalse(m.e10_not_above_zero(p))
        v.update({"br_pos": 5100, "br_neg": 4750})  # x = 0.0175, low end 0.01, minus 3SE below 0
        self.assertTrue(m.e10_not_above_zero(m.PiHat(v)))

    def test_e19_lin_bounds_take_both_ends(self):
        # n* = 1 with 4SE = 3: n* - 4SE = -2 < 0, so the low end is -2/n*_lin.lo - 1 (quantum review 2, M2)
        spec = c.RUN_POINTS["R2"]

        class FakeRun:
            lost, steps, batches = [], spec.steps, [0, 1]

            def nstar(self, step):
                return fr(1), fr(9, 16)

        r = m._e19_lin("lin", c.scored(), m.Inputs(runs={"R2": FakeRun()}), "R2", "1/2", "199.67", fr(1, 5))
        y = parse_rat(spec.y)
        law = series.Law(parse_rat(spec.delta), spec.N * y * y, fr(1, 2)).nstar()
        self.assertEqual((r.lo - Rad.of(div(-2, law.lo) - 1)).sign(), 0)
        self.assertEqual((r.hi - Rad.of(div(4, law.lo) - 1)).sign(), 0)
        self.assertEqual(r.outcome, c.MISS)

    def test_e19_lin_law_not_above_zero_stops(self):
        # review N15: the bracket needs n*_lin.lo > 0; a law reaching 0 or below 0, or an infinite one, is a STOP
        spec = c.RUN_POINTS["R2"]

        class FakeRun:
            lost, steps, batches = [], spec.steps, [0, 1]

            def nstar(self, step):
                return fr(1), fr(9, 16)

        def law_of(value):
            class Law:
                def __init__(self, *args):
                    pass

                def nstar(self):
                    return value

            return Law

        law = series.Law
        try:
            for value in (Iv(-1, 2), Iv(0, 2), None):
                series.Law = law_of(value)
                with self.assertRaises(c.StageBStop) as cm:
                    m._e19_lin("lin", c.scored(), m.Inputs(runs={"R2": FakeRun()}), "R2", "1/2", "199.67",
                               fr(1, 5))
                self.assertEqual(cm.exception.reason, "e19_law")
            series.Law = law_of(Iv(fr(1, 2), 2))
            self.assertEqual(m._e19_lin("lin", c.scored(), m.Inputs(runs={"R2": FakeRun()}), "R2", "1/2", "199.67",
                                        fr(1, 5)).row, "E19")
        finally:
            series.Law = law

    def test_band_text_open_at_infinity(self):
        self.assertEqual(c.Band(0, None, lo_open=True).text(), "(0,inf)")
        self.assertEqual(c.Band(None, None).text(), "(-inf,inf)")
        t = c.Band(fr(-1, 4), fr(1, 4)).text()
        self.assertEqual((t[0], t[-1]), ("[", "]"))

    def test_sampled_bracket(self):
        sb = m.sampled_bracket
        self.assertEqual(sb(fr(1, 10), fr(2, 10), fr(15, 100), fr(1, 10), fr(1, 10), fr(2, 100)), c.MET)
        self.assertEqual(sb(fr(3, 10), fr(4, 10), 0, fr(1, 10), fr(1, 10), fr(1, 10)), c.MISS)
        self.assertEqual(sb(fr(3, 10), fr(4, 10), 0, fr(1, 10), fr(1, 10), fr(2, 10)), c.NOT_RESOLVED)
        # a bracket across p has min |x - p| = 0
        self.assertEqual(sb(fr(-1, 10), fr(1, 10), 0, fr(1, 10), fr(2, 10), 0), c.MET)
        self.assertEqual(sb(fr(-1, 10), fr(3, 10), 0, fr(1, 10), fr(2, 10), 0), c.NOT_RESOLVED)

    def test_paired_with_lock_atoms(self):
        # LOCK: 20 atoms (br > 0), non-atoms 520 pos, 450 neg, 10 amb; VNC: 2 atoms, 480 pos, 515 neg, 3 amb
        vv = vr_block(1000, 0)
        vv.update({"atoms": 20, "mp": 980, "br_pos": 520, "br_neg": 450, "br_amb": 10, "at_br_pos": 20})
        vr = vr_block(1000, 0)
        vr.update({"atoms": 2, "mp": 998, "br_pos": 480, "br_neg": 515, "br_amb": 3, "at_br_pos": 2})
        cm = {"common": 975, "br": [400, 60, 5, 50, 440, 2, 5, 3, 10]}
        pt = tiny_point(vv, vr, cm)
        lo, hi, se2, a, r, got = m.paired(pt, 64, "LOCK")
        # Sum s_LOCK - Sum s_VNC = (540 - 450) - (482 - 515) = 123, ambiguous 10 + 3
        self.assertEqual((lo, hi), (fr(110, 2000), fr(136, 2000)))
        # discordant 60 + 50, ambiguous cells 5 + 2 + 5 + 3 + 10, outside the common set 25
        self.assertEqual(se2, fr(160, 1000000))
        e16 = m._e16("x", "P08", 1, "LOCK", c.scored(), pt)
        self.assertEqual(e16.value, (fr(110, 2000) + fr(136, 2000)) * fr(1, 4))  # (D+ - D-)/(2M): half of it

    def test_nstar_and_rho(self):
        # samples br = 1, 3 | 0, 2: mean 3/2, |Bbar|^2_u = (36 - 14)/12 = 11/6, V = 5/3, n* = V/|Bbar|^2_u = 10/11
        rs = [{"m": 2, "br": 4, "bi": 0, "br2": 10, "bi2": 0}, {"m": 2, "br": 2, "bi": 0, "br2": 4, "bi2": 0}]
        self.assertEqual(m.nstar_of(rs), fr(10, 11))
        tot = {"m": 4, "br": 6, "bi": 0, "br2": 14, "bi2": 0}
        self.assertEqual(m.rho_u(tot), fr(11, 21))
        self.assertEqual(m.bbar2_u(tot), fr(11, 6))
        self.assertIsNone(m.nstar_of([{"m": 2, "br": 1, "bi": 0, "br2": 5, "bi2": 0}]))
        full, se2 = m.nstar_jackknife(rs + rs)
        self.assertEqual(full, m.nstar_of(rs + rs))
        self.assertTrue(se2 > 0)

    def test_n_list(self):
        self.assertEqual(m.n_list(1 << 22), c.BLOCK_SIZES)
        self.assertEqual(m.n_list(1 << 20)[-1], 1024)
        self.assertEqual(m.n_list(1 << 18), (4, 8, 16, 32, 64, 128, 256))

    def test_e16_two_readings(self):
        # (recipe, prediction), both with the frozen SE_pair: MET iff the prediction passes, MISS iff the recipe fails
        o = m.e16_outcome
        self.assertEqual(o(c.MET, c.MET), c.MET)
        self.assertEqual(o(c.MET, c.NOT_RESOLVED), c.NOT_RESOLVED)  # passes only at the recipe's half difference
        self.assertEqual(o(c.MET, c.MISS), c.NOT_RESOLVED)
        self.assertEqual(o(c.NOT_RESOLVED, c.MISS), c.NOT_RESOLVED)
        self.assertEqual(o(c.MISS, c.MISS), c.MISS)
        for bad in ((c.NOT_RESOLVED, c.MET), (c.MISS, c.NOT_RESOLVED)):  # cannot happen with one SE_pair
            with self.assertRaises(c.StageBStop):
                o(*bad)

    def _e16_point(self, pos_v, pos_r, dp, dm, amb=0):
        mm = 1 << 18
        vv, vr = vr_block(mm, 0), vr_block(mm, 0)
        vv.update({"br_pos": pos_v, "br_neg": mm - pos_v - amb, "br_amb": amb})
        vr.update({"br_pos": pos_r, "br_neg": mm - pos_r})
        t = [pos_v - dp, dp, 0, dm, mm - pos_v - amb - dm, 0, 0, amb, 0]
        return tiny_point(vv, vr, {"common": mm, "br": t, "bi": [mm] + [0] * 8}, "V1")

    def test_e16_probe_both_texts_met(self):
        # review probe e16_probe.py: Pi_V = Pi_VNC = 5243/2^18 (about 0.02), D+ = D- = 5000, no ambiguity; both
        # frozen texts give 0 + 3 sqrt(10^4)/2^19 = 5.72e-4 <= Pi_VNC/20 = 1.0e-3, so the read is MET
        mm = 1 << 18
        pt = self._e16_point(mm // 2 + 5243, mm // 2 + 5243, 5000, 5000)
        r = m._e16("pair_P04_V1_t1", "P04", 1, "V1", c.scored(), pt)
        d = dict(r.detail)
        self.assertEqual((r.outcome, d["recipe"], d["diff"]), (c.MET, c.MET, c.MET))
        self.assertEqual(d["3SE_pair"], "5.723e-4")
        self.assertEqual((m.e16_se_pair_e(pt.cmp(64, "V1"), mm) - c.se(fr(10000, 4 * mm * mm), 3)).sign(), 0)

    def test_e16_recipe_and_prediction_apart(self):
        # D+ - D- = 400 of 2^18 with D+ + D- = 1200: the recipe's half difference 400/2^19 = 7.6e-4 passes with
        # 3SE_pair = 1.98e-4 against 1.0e-3, the prediction's 400/2^18 = 1.53e-3 fails: NOT_RESOLVED
        mm = 1 << 18
        pt = self._e16_point(mm // 2 + 5243 + 400, mm // 2 + 5243, 800, 400)
        r = m._e16("x", "P04", 1, "V1", c.scored(), pt)
        d = dict(r.detail)
        self.assertEqual((r.outcome, d["recipe"], d["diff"]), (c.NOT_RESOLVED, c.MET, c.MISS))
        # twice that difference: the recipe fails too, MISS
        pt = self._e16_point(mm // 2 + 5243 + 1200, mm // 2 + 5243, 1600, 400)
        self.assertEqual(m._e16("x", "P04", 1, "V1", c.scored(), pt).outcome, c.MISS)

    def test_e16_ambiguity_widens_se_pair(self):
        # the conservative reading (note reading_E16): 40 ambiguous V1 samples widen the bracket of
        # the difference and count as possibly discordant, D_max = 10000 + 40, so 3SE_pair = 3 sqrt(10040)/2^19
        mm = 1 << 18
        pt = self._e16_point(mm // 2 + 5243, mm // 2 + 5243, 5000, 5000, amb=40)
        r = m._e16("x", "P04", 1, "V1", c.scored(), pt)
        d = dict(r.detail)
        self.assertEqual((d["D_max"], d["3SE_pair"]), (10040, "5.734e-4"))
        self.assertEqual(m.possibly_discordant(pt.cmp(64, "V1"), mm), 10040)
        self.assertEqual((m.e16_se_pair_e(pt.cmp(64, "V1"), mm) - c.se(fr(10040, 4 * mm * mm), 3)).sign(), 0)
        self.assertEqual(r.outcome, c.MET)

    def test_e16_atoms_count_as_possibly_discordant(self):
        # no certified discordance, no ambiguous sign, 40000 samples outside the common non-atom set: with the
        # certified cells alone SE_pair = 0 and the read would be MET; counting the atoms as possibly discordant,
        # 3SE_pair = 3 sqrt(40000)/2^19 = 1.14e-3 > Pi_VNC/20 = 1.0e-3, so it is NOT_RESOLVED
        mm = 1 << 18
        pt = self._e16_point(mm // 2 + 5243, mm // 2 + 5243, 0, 0)
        cm = pt.calls[0].cmp[(64, "V1")]
        cm["common"] = mm - 40000
        cm["br"] = [cm["br"][0] - 20000, 0, 0, 0, cm["br"][4] - 20000, 0, 0, 0, 0]
        r = m._e16("x", "P04", 1, "V1", c.scored(), pt)
        d = dict(r.detail)
        self.assertEqual((d["D+"], d["D-"], d["D_max"]), (0, 0, 40000))
        self.assertEqual((r.outcome, d["recipe"], d["diff"]), (c.NOT_RESOLVED, c.NOT_RESOLVED, c.NOT_RESOLVED))

    def test_cross_outcome(self):
        co = m.cross_outcome
        self.assertEqual(co(c.MISS, c.MISS), c.MET)
        self.assertEqual(co(c.MET, c.MISS), c.MISS)
        self.assertEqual(co(c.NOT_RESOLVED, c.MISS), c.NOT_RESOLVED)
        self.assertEqual(co(c.MET, c.NOT_RESOLVED), c.MISS)
        self.assertEqual(co(c.NOT_RESOLVED, c.NOT_RESOLVED), c.MET)

    def test_b16_read_against_prediction(self):
        flat = vr_block(1 << 20, 0)
        bent = vr_block(1 << 20, 0, fr(3, 1000))
        sc = c.scored()
        self.assertEqual(m.b16_read("T", "a", "x", sc, flat, m.UNIFORM).outcome, c.MET)
        self.assertEqual(m.b16_read("T", "a", "x", sc, flat, m.NOT_UNIFORM).outcome, c.MISS)
        self.assertEqual(m.b16_read("T", "a", "x", sc, bent, m.NOT_UNIFORM).outcome, c.MET)
        self.assertEqual(m.b16_read("T", "a", "x", sc, bent, m.UNIFORM).outcome, c.MISS)

    def test_uniformity(self):
        # E11 at 2^22: |O+ - O-| = 8976 is under the sign threshold sqrt(64 M) = 16384, 35760 is over it
        self.assertEqual(m.uniformity(vr_block(1 << 22, fr(107, 100000)))[0], m.UNIFORM)
        self.assertEqual(m.uniformity(vr_block(1 << 22, fr(4263, 1000000)))[0], m.NOT_UNIFORM)
        self.assertEqual(m.uniformity(vr_block(1 << 22, 0, fr(3, 1000)))[0], m.NOT_UNIFORM)

    def test_scoring_rule_and_text_agree(self):
        fz = frozen.load()
        p03 = m.triple(c.DUMP_POINTS["P03"], 1)
        with self.assertRaises(c.StageBStop):
            m.scoring_at(fz, "E09", [p03], None)
        self.assertFalse(m.scoring_at(fz, "E09", [p03], m.E09_X08).scored)
        p08 = m.triple(c.DUMP_POINTS["P08"], 1)
        with self.assertRaises(c.StageBStop):
            m.scoring_at(fz, "E09", [p08], m.E09_X08)


# ---------------------------------------------------------------------------------------------------------------------
# Every row on the synthetic world.


class AllMet(unittest.TestCase):
    def test_verdicts(self):
        got = {k: v.verdict for k, v in base_verdicts().items()}
        want = {r: c.MET for r, _ in m.ROWS}
        want["E17"] = c.NONE
        self.assertEqual(got, want)

    def test_counts(self):
        got = {k: (v.counts()["reads"], v.counts()["scored"]) for k, v in base_verdicts().items()}
        self.assertEqual(got, {"E09": (40, 5), "E10": (20, 3), "E11": (8, 8), "E12": (422, 422), "E13": (50, 14),
                               "E14": (6, 1), "E15": (30, 11), "E16": (24, 24), "E17": (64, 0), "E18": (5, 2),
                               "E19": (12, 12)})

    def test_scored_sets(self):
        vs = base_verdicts()
        sc = {k: sorted(r.rid for r in v.reads if r.scored) for k, v in vs.items()}
        self.assertEqual(sc["E09"], ["b16_P01_t1", "b16_P01_t2", "b16_P02_t1", "b16_P02_t2", "b16_P08_t1"])
        self.assertEqual(sc["E10"], ["pi_P02_t1", "pi_P02_t2", "pi_P08_t1"])
        self.assertEqual(sc["E14"], ["ratio_t1"])
        self.assertEqual(sc["E18"], ["QW_y1/27_t1", "QW_y1/54_t1"])
        e15 = set(sc["E15"])
        self.assertEqual(e15, {"pi_P08_VNC_t1", "pi_P08_FLIP_t1", "pi_P08_LOCK_t1", "cross_P08_LOCK_t1",
                               "order_P05_FLIP>VNC_t1", "order_P05_FLIP>VNC_t2", "order_P05_VNC>LOCK_t2",
                               "order_P08_LOCK>VNC_t1", "order_P08_LOCK>VNC_t2", "order_P08_VNC>FLIP_t1",
                               "order_P08_VNC>FLIP_t2"})
        e13 = [x for x in sc["E13"] if x.startswith("band_")]
        self.assertEqual(len(e13), 11)
        self.assertTrue(all(x.startswith(("band_P02_t2", "band_P08_t1")) for x in e13))

    def test_report_reads_carry_frozen_values(self):
        vs = base_verdicts()
        r = reads_of(vs["E09"])
        self.assertEqual(r["excess_P05_t2"].frozen, "0.03639")
        self.assertEqual(r["b16_P02_t1"].frozen, "sector-0_2.6e-4")
        self.assertEqual(r["b16_P03_t1"].verdict, c.REPORT)
        self.assertEqual(r["b16_P03_t1"].outcome, c.MET)  # not uniform, as frozen
        e13 = reads_of(vs["E13"])
        self.assertEqual(e13["band_P04_t2_n256"].frozen, "rho=2.1085e-3,1+(n-1)rho=1.538")
        self.assertEqual(dict(e13["band_P04_t2_n256"].detail)["band_verdict"], "NOT_MET")
        self.assertEqual(e13["tol_P02_t2"].frozen, "rho=9.2917e-6,n*=107622")
        self.assertIn("last-digit_slip", e13["band_P05_t2_n16"].frozen)  # 1.365 for 1 + 15 rho = 1.36447
        e14 = reads_of(vs["E14"])
        self.assertEqual([e14["first_%s" % k].value for k in ("P08_t1", "P14_t1", "P08_t2", "P14_t2")],
                         ["2^6", "2^10", "2^5", "2^8"])

    def test_e15_cross_reads_as_frozen(self):
        r = reads_of(base_verdicts()["E15"])
        got = {k: dict(x.detail)["cross"] for k, x in r.items() if k.startswith("cross_")}
        want = {"cross_%s_%s_t%d" % k: v for k, v in m.E15_CROSS.items()}
        self.assertEqual(got, want)
        self.assertEqual(r["cross_P08_FLIP_t1"].verdict, c.REPORT)  # RP13: expected NOT_RESOLVED, read and report

    def test_e17_reads_report_only(self):
        v = base_verdicts()["E17"]
        self.assertEqual({r.verdict for r in v.reads}, {c.REPORT})
        self.assertEqual({r.outcome for r in v.reads}, {c.MET})
        self.assertEqual(v.falsifier, "none")

    def test_read_file(self):
        fz = frozen.load()
        rf = c.ReadFile(fz)
        vs = m.read_e_mom(inputs())
        for v in vs:
            rf.add(v)
        with TempDir() as d:
            out = os.path.join(d, "READ.hbp")
            rf.write(out)
            lines = read(out).split("\n")[:-1]
        for ln in lines:
            parse_row(ln)
        kinds = [ln.split("|", 1)[0] for ln in lines]
        self.assertEqual(kinds.count("STRIPES_VERDICT"), 11)
        self.assertEqual(kinds.count("STRIPES_READ"), sum(len(v.reads) for v in vs))
        end = dict(x.split("=", 1) for x in lines[-1].split("|")[1:])
        self.assertEqual(end["sha256"], sha256_hex("".join(x + "\n" for x in lines[:-1]).encode("ascii")))


# ---------------------------------------------------------------------------------------------------------------------
# One planted fault per row.


def row(rid, **kw):
    return verdicts(inputs(**kw), rows=(rid,))[rid]


class NotMet(unittest.TestCase):
    def test_e09_flag_at_p02(self):
        v = row("E09", edits={("P02", 64, VNC): {"dev": fr(3, 1000)}})
        self.assertEqual(v.verdict, c.NOT_MET)
        self.assertIn("b16_P02_t1:", v.falsifier)

    def test_e09_no_flag_at_p08_t1(self):
        v = row("E09", edits={("P08", 64, VNC): {"dev": fr(0)}})
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e09_exposed_fault_keeps_met(self):
        v = row("E09", edits={("P04", 64, VNC): {"dev": fr(0)}, ("P02", 192, VNC): {"dev": fr(3, 1000)}})
        self.assertEqual(v.verdict, c.MET)
        self.assertEqual(reads_of(v)["b16_P04_t1"].outcome, c.MISS)

    def test_e10_pi_miss(self):
        v = row("E10", edits={("P02", 64, "*"): {"pi": fr(6, 1000)}})
        self.assertEqual(v.verdict, c.NOT_MET)
        self.assertEqual(reads_of(v)["pi_P02_t1"].outcome, c.MISS)

    def test_e10_p02_not_above_zero(self):
        # Pi_hat = 0.0004 at t=2: NOT_RESOLVED against 0.001593, and not above 0 at 3 SE: the falsifier
        v = row("E10", edits={("P02", 128, "*"): {"pi": fr(4, 10000)}})
        self.assertEqual(reads_of(v)["pi_P02_t2"].outcome, c.NOT_RESOLVED)
        self.assertEqual(v.verdict, c.NOT_MET)
        self.assertIn("pi_P02_t2:", v.falsifier)

    def test_e11_p11_flagged(self):
        v = row("E11", edits={("P11", 64, "*"): {"pi": fr(3, 1000)}})
        self.assertEqual(reads_of(v)["uniform_P11_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e11_p12_unflagged(self):
        v = row("E11", edits={("P12", 128, "*"): {"pi": fr(1, 1000)}})
        self.assertEqual(reads_of(v)["uniform_P12_t2"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e12_y0_contrast(self):
        v = row("E12", edits={("P09", 64, VNC): {"zscale": fr(3, 2)}})
        self.assertEqual(reads_of(v)["zero_P09_VNC_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e12_identity_broken(self):
        v = row("E12", edits={("P04", 128, "V1"): {"zscale": fr(3, 2)}})
        self.assertEqual(reads_of(v)["iid_P04_V1_t2"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e13_band_reversed(self):
        # Z_4096 at P02 t=2 raised 1.5x: the band verdict turns NOT_MET where MET is frozen
        v = row("E13", edits={("P02", 128, VNC): {"zscale": fr(3, 2)}})
        r = reads_of(v)
        self.assertEqual(r["band_P02_t2_n4096"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e13_exposed_band_keeps_met(self):
        v = row("E13", edits={("P05", 128, VNC): {"zscale": fr(100000, 136447)}})  # Z_16 about 1
        self.assertEqual(reads_of(v)["band_P05_t2_n16"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.MET)

    def test_e14_ratio_out(self):
        # n*(P14) set to 2 n*(P08) at t=1
        v = row("E14", edits={("P14", 64, VNC): {"rho": fr(1, 1 + 2 * 46526 * fr(1, 1000))}})
        self.assertEqual(reads_of(v)["ratio_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e15_order_reversed(self):
        v = row("E15", edits={("P08", 64, "FLIP"): {"pi": fr(11, 100)}})
        r = reads_of(v)
        self.assertEqual(r["order_P08_VNC>FLIP_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e15_cross_other_than_predicted(self):
        v = row("E15", edits={("P08", 64, "LOCK"): {"pi": fr(10, 100)}})
        self.assertEqual(dict(reads_of(v)["cross_P08_LOCK_t1"].detail)["cross"], c.MET)
        self.assertIn("cross_P08_LOCK_t1", v.falsifier)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e15_unresolved_cross_read_is_not_a_falsifier(self):
        r = c.Read("E15", "cross_P08_LOCK_t1", "x", "cross", c.scored(), m.cross_outcome(c.NOT_RESOLVED, c.MISS),
                   detail=(("cross", c.NOT_RESOLVED), ("predicted", c.MISS)))
        self.assertEqual(r.outcome, c.NOT_RESOLVED)
        v = c.Verdict("E15", "n", "t", [r], [x.rid for x in [r] if x.scored and x.outcome == c.MISS])
        self.assertEqual((v.falsifier, v.verdict), ("none", c.NOT_RESOLVED))

    def test_e15_exposed_value_keeps_met(self):
        v = row("E15", edits={("P05", 64, "FLIP"): {"pi": fr(13, 100)}})
        self.assertEqual(reads_of(v)["pi_P05_FLIP_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.MET)

    def test_e16_discordant(self):
        v = row("E16", edits={("P06", 128, "V0"): {"pi": dec("0.262970") + fr(4, 100)}})
        self.assertEqual(reads_of(v)["pair_P06_V0_t2"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e17_never_a_verdict(self):
        v = row("E17", edits={("P10", "*", "*"): {"pi": fr(-1, 10), "dev": fr(0)}})
        self.assertEqual(v.verdict, c.NONE)
        self.assertEqual(reads_of(v)["sign_VNC_t1"].outcome, c.MISS)

    def test_e18_qw_off(self):
        v = row("E18", qe_scale={("1/27", "1"): fr(11, 10)})
        self.assertEqual(reads_of(v)["QW_y1/27_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e18_zero_moment_is_a_miss(self):
        # E_VNC[|B_W|^2] = 0 is a ratio of 0: abs(0 - 1) = 1 > 1/20 (review M7)
        inp = inputs(run_edits={"R1": {}})
        for b in inp.run("R1").batches:
            b.rec[64]["br2"] = b.rec[64]["bi2"] = 0
        v = verdicts(inp, rows=("E18",))["E18"]
        self.assertEqual(reads_of(v)["QW_y1/27_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e18_exposed_qw_off_keeps_met(self):
        v = row("E18", qe_scale={("1/54", "2"): fr(11, 10), ("0", "2"): fr(9, 10)})
        self.assertEqual(reads_of(v)["QW_y1/54_t2"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.MET)

    def test_e19_mean_not_positive(self):
        v = row("E19", run_edits={"R4": {"sign": {64: -1}}})
        self.assertEqual(reads_of(v)["Ebr_R4_t1"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)

    def test_e19_collapse_broken(self):
        v = row("E19", run_edits={"R4": {"nstar_scale": {32: 2}}})
        r = reads_of(v)
        self.assertEqual(r["collapse_t1/2"].outcome, c.MISS)
        self.assertEqual(r["lin_R4_t1/2"].outcome, c.MISS)
        self.assertEqual(v.verdict, c.NOT_MET)


# ---------------------------------------------------------------------------------------------------------------------
# Rule STOP.


class Stop(unittest.TestCase):
    def test_dropped_record(self):
        # every P02 call rerun without its last record: t=4 is NOT_MEASURED (read and report in E09)
        vs = verdicts(inputs(steps={"P02": (64, 128, 192)}), rows=("E09", "E12"))
        self.assertEqual(reads_of(vs["E09"])["b16_P02_t4"].verdict, c.NOT_MEASURED)
        self.assertEqual(vs["E09"].verdict, c.MET)
        e12 = reads_of(vs["E12"])
        self.assertEqual(e12["iid_P02_V1_t4"].outcome, c.NOT_MEASURED)
        self.assertEqual(vs["E12"].verdict, c.NOT_RESOLVED)

    def test_scored_record_lost(self):
        v = row("E15", steps={"P08": (64,)})
        r = reads_of(v)
        self.assertEqual(r["order_P08_LOCK>VNC_t2"].outcome, c.NOT_MEASURED)
        self.assertEqual(v.verdict, c.NOT_RESOLVED)

    def test_lost_calls_stated(self):
        # the last VNC-only block of P02 lost: fewer than 1024 blocks of 4096 remain, and the reads state the loss
        v = row("E12", lose={"P02": (78,)})
        r = reads_of(v)["iid_P02_VNC_t1"]
        d = dict(r.detail)
        self.assertEqual(d["lost_calls"], 1)
        self.assertIn("NOT_MEASURED", d["n4096"])
        self.assertEqual(r.outcome, c.NOT_RESOLVED)

    def test_no_qe(self):
        v = row("E18", with_qe=False)
        self.assertEqual({r.outcome for r in v.reads}, {c.NOT_MEASURED})
        self.assertEqual(v.verdict, c.NOT_MEASURED)

    def test_lost_batch(self):
        # rule STOP for runs: the point keeps only the records all 64 batches reached; a lost batch reached none, so
        # every read of R2 is NOT_MEASURED and states the loss; the reads of R3 and R4 alone are read
        v = row("E19", run_edits={"R2": {"drop": (5,)}})
        r = reads_of(v)
        with_r2 = ("collapse_t1/2", "collapse_t1", "lin_R2_t1/2", "lin_R2_t1", "Ebr_R2_t1/2", "Ebr_R2_t1")
        for rid in with_r2:
            self.assertEqual(r[rid].outcome, c.NOT_MEASURED, rid)
            self.assertEqual(dict(r[rid].detail)["lost"], "R2_batch_lost_5", rid)
        for rid in set(r) - set(with_r2):
            self.assertEqual(r[rid].outcome, c.MET, rid)
        self.assertEqual(v.verdict, c.NOT_RESOLVED)

    def test_lost_batch_e18(self):
        v = row("E18", run_edits={"R2": {"drop": (5,)}})
        r = reads_of(v)
        for rid in ("QW_y1/54_t1", "QW_y1/54_t2"):
            self.assertEqual(r[rid].outcome, c.NOT_MEASURED, rid)
            self.assertEqual(dict(r[rid].detail)["lost"], "R2_batch_lost_5", rid)
        self.assertEqual(r["QW_y1/27_t1"].outcome, c.MET)

    def test_missing_point_stops(self):
        inp = inputs()
        del inp.points["P07"]
        with self.assertRaises(c.StageBStop) as e:
            m.read_e_mom(inp, rows=("E18",))
        self.assertEqual(e.exception.reason, "missing_point")


class RealExcluded(unittest.TestCase):
    """The helpers on the real stage A blocks and run sums of the excluded points X1 and XR1 (N=27, delta=1/4,
    y=1/40; tests/data), no engine run."""

    @classmethod
    def setUpClass(cls):
        with TempDir() as d:
            point_dir(d, {"0.hbp": with_trailer(read(os.path.join(AGG, "X1.0.agg"))),
                          "1.hbp": with_trailer(read(os.path.join(AGG, "X1.1.agg")))})
            cls.pt = c.load_point(d, X1)
        cls.xr1 = runs.load_run(RUN, XR1)

    def test_cmp_cells_match_marginals(self):
        # Sum (s_v - s_VNC) over the common samples, s = +1, -1, 0 (amb): row = the variant's state, column = VNC's
        for step in (64, 128):
            for v in c.VARIANTS[1:]:
                a, r, cm = self.pt.vr(step, v), self.pt.vr(step, VNC), self.pt.cmp(step, v)
                t = cm["br"]
                lhs = (a["br_pos"] - a["br_neg"]) - (r["br_pos"] - r["br_neg"])
                rhs = 2 * t[1] - 2 * t[3] + t[2] - t[5] - t[6] + t[7]
                if v == "LOCK":
                    self.assertTrue(abs(lhs - rhs) <= a["M"] - cm["common"])
                else:
                    self.assertEqual((lhs, cm["common"]), (rhs, a["mp"]))

    def test_block_sums_units(self):
        # n = 4096: one block per call, s2 = |Sum B|^2 of the call and w = Sum |B|^2, both at 2^80
        for step in (64, 128):
            k = self.pt.blk(step, VNC, 4096)
            ps = self.pt.per_call_sums(step, VNC)
            self.assertEqual(k["s2"], sum(x["br"] * x["br"] + x["bi"] * x["bi"] for x in ps))
            self.assertEqual(k["w"], sum(x["br2"] + x["bi2"] for x in ps))

    def test_bbar_same_on_dump_and_run(self):
        # indices 0..4095: call 0 of the X1 dump and the 8 batches of XR1
        for step in (64, 128):
            s = self.pt.calls[0].sums[(step, VNC, "all")]
            p = self.xr1.pooled(step)
            self.assertEqual(m.bbar2_u(s), m.bbar2_u(p))
            self.assertIsNone(m.nstar_of([s]))
            self.assertIsNone(runs.nstar_of(self.xr1.per_batch(step)))

    def test_reads_build(self):
        sc = c.scored()
        r = m.z_read("T", "z", "X1", sc, self.pt, 64, VNC, "all", (4, 8), "iid")
        self.assertIn(r.outcome, (c.MET, c.MISS, c.NOT_RESOLVED))
        self.assertTrue(r.lo < r.value < r.hi)
        p = m.PiHat(self.pt.vr(64, VNC))
        self.assertEqual(p.M, 8192)
        lo, hi, se2, a, ref, cm = m.paired(self.pt, 64, "LOCK")
        self.assertTrue(lo <= hi and se2 > 0)
        parse_row(m.b16_read("T", "b", "X1", sc, self.pt.vr(128, "V1", "ctrl"), m.UNIFORM).row_text())


if __name__ == "__main__":
    unittest.main()
