"""Rows E01-E08 (rows_e_sym) on synthetic pooled aggregates built by hand for the whole frozen layout (P01-P14, the
P08 and P13 side files, R1-R3), with a constructed MET and NOT_MET case per row, rule STOP, and the read helpers on the
real excluded-point blocks X0 (y=0) and X1 (y=1/40)."""

import hashlib
import os
import shutil
import struct
import tempfile
import unittest

from stripes_read_b import common as c
from stripes_read_b import frozen, qint, runs, series
from stripes_read_b import rows_e_sym as e
from stripes_read_b.exact import fr, parse_rat

from .util import AGG, X0, X1, TempDir, point_dir, read, rehash, with_trailer

FZ = frozen.load()
Q = e.lock_q(FZ)
ALL7 = c.VARIANTS
COUNT = c.COUNT


# ---------------------------------------------------------------------------------------------------------------------
# Hand-built pooled aggregates.


def split(m):
    return m // 2, m // 2, m - 2 * (m // 2)


def make_vr(sec, amb, atoms, xatoms=None, xbi=0, na_bi0=0):
    mp = sum(sec) + amb
    p, n, a = split(mp)
    ap, an, aa = split(atoms)
    return {"M": mp + atoms, "atoms": atoms, "xatoms": atoms if xatoms is None else xatoms, "xatom_bi_nz": xbi,
            "mp": mp, "na_bi0": na_bi0, "sec": list(sec), "amb": amb, "br_pos": p, "br_neg": n, "br_amb": a,
            "bi_pos": p, "bi_neg": n, "bi_amb": a, "at_br_pos": ap, "at_br_neg": an, "at_br_amb": aa,
            "at_bi_pos": 0, "at_bi_neg": 0, "at_bi_amb": atoms}


def uniform_vr(m, atoms):
    mp = m - atoms
    k = mp // 16
    return make_vr([k] * 16, mp - 16 * k, atoms)


def lattice_vr(m, atoms):
    mp = m - atoms
    sec = [qint.floor(mp * q) for q in Q]
    return make_vr(sec, mp - sum(sec), atoms)


def make_sums(m, s_br=0, s_bi=0):
    return {"m": m, "br": s_br, "bi": s_bi, "br2": m << 76, "bi2": m << 76, "brbi": 0, "bbr": 100 * m,
            "bbi": 100 * m, "bbr2": 10000 * m, "bbi2": 10000 * m}


def atom_sums(m):
    return dict.fromkeys(c.AGG_KEYS["AGG_SUM"][5:], 0) | {"m": m}


def make_cmp(vr):
    mp, amb = vr["mp"], vr["amb"]
    p, n, a = vr["br_pos"], vr["br_neg"], vr["br_amb"]
    return {"common": mp, "br": [p, 0, 0, 0, n, 0, 0, 0, a], "bi": [p, 0, 0, 0, n, 0, 0, 0, a], "cert2": mp - amb,
            "mis": 0, "cert2_big_both": mp - amb, "mis_big_both": 0, "cert2_big_any": mp - amb, "mis_big_any": 0}


def nl_text(spec, step, br, bi=0):
    vals = dict.fromkeys(c.TWB_NL_KEYS, "0")
    vals.update(N=str(spec.N), delta=spec.delta, u="1", y=spec.y, dtden="64", step=str(step),
                init="c0=sqrt(N),c+-=0", kappa="1", reads=c.TWB_NL_READS, at="2^40", float_used="0", br=str(br),
                bi=str(bi), rb_br="3", rb_bi="3")
    return "TWB_NL|" + "|".join("%s=%s" % (k, vals[k]) for k in c.TWB_NL_KEYS) + "|json=0"


ZERO_VR = make_vr([0] * 16, 0, 0)
ZERO_SUMS = atom_sums(0)
ZERO_CMP = {"common": 0, "br": [0] * 9, "bi": [0] * 9, "cert2": 0, "mis": 0, "cert2_big_both": 0,
            "mis_big_both": 0, "cert2_big_any": 0, "mis_big_any": 0}
ZERO_ATOMS = {"M": COUNT, "nl_klein": 0, "nl_exch": 0, "lk_klein": 0, "lk_exch": 0}


def atoms_of(m, lock):
    """Atom counts of m samples near the frozen masses: Klein 3.108e-4 and 0.042097, exchange 7.7708e-5 and
    0.0124662."""
    return {"M": COUNT, "nl_klein": m * 3108 // 10000000, "nl_exch": m * 77708 // 1000000000,
            "lk_klein": m * 42097 // 1000000 if lock else 0, "lk_exch": m * 124662 // 10000000 if lock else 0}


class Synth:
    """One dump point: the first read call below `all` carries the pooled controls and the first 2^18 VNC samples
    (part "ctrl"), the first read call at or above `all` the other VNC samples (part "rest"), every other call zeros."""

    def __init__(self, pid):
        spec = self.spec = c.DUMP_POINTS[pid]
        self.y0 = parse_rat(spec.y) == 0
        self.lost = set()
        self.call_steps = {}
        self.nl_override = {}
        self.sha_override = {}
        self.sides = {}
        ctrl_m = COUNT * spec.all
        sizes = {"ctrl": ctrl_m, "rest": spec.vnc - ctrl_m}
        self.vr, self.sums, self.cmp, self.lock, self.atoms = {}, {}, {}, {}, {}
        for part, m in sizes.items():
            if m == 0:
                continue
            variants = ALL7 if part == "ctrl" else ("VNC",)
            at = atoms_of(m, part == "ctrl")
            self.atoms[part] = at
            for step in spec.steps:
                for v in variants:
                    if v == "LOCK":
                        n_at = at["lk_klein"] if self.y0 else at["lk_exch"]
                        vr = lattice_vr(m, n_at)
                    else:
                        n_at = at["nl_klein"] if self.y0 else at["nl_exch"]
                        vr = uniform_vr(m, n_at)
                    self.vr[(part, step, v)] = vr
                    self.sums[(part, step, v, "all")] = make_sums(m)
                    self.sums[(part, step, v, "atom")] = atom_sums(n_at)
                    if v != "VNC":
                        self.cmp[(part, step, v)] = make_cmp(vr)
                    if v == "LOCK":
                        self.lock[(part, step)] = {"cert": vr["mp"] - vr["amb"], "mis": 0}
        self.nl = {s: nl_text(spec, s, 0 if self.y0 else 1000000) for s in spec.steps}

    def point(self):
        spec = self.spec
        pt = c.Point(spec)
        present = [i for i in range(spec.calls) if i not in self.lost]
        carrier = {}
        for i in present:
            part = "ctrl" if i < spec.all else "rest"
            if part not in carrier and part in self.atoms and i not in self.sides:
                carrier[part] = i
        by_call = {i: p for p, i in carrier.items()}
        for i in range(spec.calls):
            if i in self.lost:
                pt.lost.append((i, "engine_stop_rc4"))
                continue
            ctrl = i < spec.all
            part = by_call.get(i)
            b = c.CallBlock()
            b.call, b.point = i, spec.id
            b.variants = ALL7 if ctrl else ("VNC",)
            b.nl = ctrl
            b.steps = self.call_steps.get(i, spec.steps)
            for step in b.steps:
                for v in b.variants:
                    b.vr[(step, v)] = self.vr[(part, step, v)] if part else ZERO_VR
                    for which in ("all", "atom"):
                        b.sums[(step, v, which)] = self.sums[(part, step, v, which)] if part else ZERO_SUMS
                    if v != "VNC":
                        b.cmp[(step, v)] = self.cmp[(part, step, v)] if part else ZERO_CMP
                    if v == "LOCK":
                        b.lock[step] = self.lock[(part, step)] if part else {"cert": 0, "mis": 0}
                if ctrl:
                    b.nl_rows[step] = self.nl_override.get((i, step), self.nl[step])
            b.atoms = self.atoms[part] if part else ZERO_ATOMS
            if i in self.sides:
                # a side call (ensemble review M4): its AGG_SUM rows at the side records and its AGG_ATOMS are
                # those of its side file, and the side row carries the block, so open_side cross-checks them
                row = self.sides[i]
                for key, x in row["sums"].items():
                    b.sums[key] = x
                b.atoms = dict(ZERO_ATOMS)
                b.side = dict(row, block=b)
            nl = "".join(b.nl_rows[s] + "\n" for s in b.steps) if ctrl else None
            b.call_row = {"nl_sha256": self.sha_override.get(i, hashlib.sha256(nl.encode("ascii")).hexdigest()
                                                             if ctrl else "none"), "y_zero": "1" if self.y0 else "0"}
            pt.calls[i] = b
        k = min(len(b.steps) for b in pt.calls.values())
        pt.steps, pt.not_measured = spec.steps[:k], spec.steps[k:]
        return pt


def side_file(d, name, call, br_of, bb=20):
    """A side file of the call's 4096 samples at index 4096 call (AGG-FORMAT section 7), no atom flag, br_of(k, v, s)
    and b_br = bb; its AGG_SIDE row, with "sums": the AGG_SUM rows (set=all and set=atom, records 64 and 128) its
    block must carry, summed here from br_of and bb (not by the reader's side_sums)."""
    head = b"STRPSIDE" + struct.pack("<6I", 1, 7, 127, 2, 64, 128) + struct.pack("<2Q", COUNT * call, COUNT) \
        + bytes(16)
    body = b"".join(struct.pack("<Q", 0) + b"".join(struct.pack("<qQ", br_of(k, v, s), bb) for v in ALL7
                                                    for s in (64, 128)) for k in range(COUNT))
    path = os.path.join(d, name)
    with open(path, "wb") as f:
        f.write(head + body)
    sums = {}
    for v in ALL7:
        for st in (64, 128):
            brs = [br_of(k, v, st) for k in range(COUNT)]
            sums[(st, v, "all")] = {"m": COUNT, "br": sum(brs), "bi": 0, "br2": sum(x * x for x in brs), "bi2": 0,
                                    "brbi": 0, "bbr": bb * COUNT, "bbi": 0, "bbr2": bb * bb * COUNT, "bbi2": 0}
            sums[(st, v, "atom")] = atom_sums(0)
    return {"path": path, "sha256": hashlib.sha256(head + body).hexdigest(), "bytes": len(head + body),
            "indices": COUNT, "variants": ",".join(ALL7), "steps": "64,128", "dir": d, "sums": sums}


class StubBatch:
    def __init__(self, rec):
        self.rec = rec


def synth_run(rid, mu, eps=8):
    """A run point whose batch j has per-sample mean br of mu[step] + (-1)^j eps (units of 2^-40)."""
    spec = c.RUN_POINTS[rid]
    r = runs.Run(spec)
    n = spec.per_batch
    for j in range(spec.batches):
        d = eps if j % 2 else -eps
        rec = {}
        for s in spec.steps:
            rec[s] = {"n": n, "br": n * (mu[s] + d), "bi": 0, "br2": n << 76, "bi2": 0, "brbi": 0, "rb_br": 0,
                      "rb_bi": 0, "rb_br2": 0, "rb_bi2": 0, "rb_brbi": 0}
        r.batches.append(StubBatch(rec))
    r.steps = spec.steps
    return r


def run_set(r2_scale=1, r3_t2=256):
    return {"R1": synth_run("R1", dict.fromkeys((32, 64, 128), 4096)),
            "R2": synth_run("R2", dict.fromkeys((32, 64, 128), 1024 * r2_scale)),
            "R3": synth_run("R3", {32: 256, 64: 256, 128: r3_t2})}


def add_sides(synths, d, shift=0):
    """Side files for calls 0 and 1 of P08 and P13; P13 br = P08 br + (-1)^k 10^6 + shift (VNC, step 64)."""
    for i in (0, 1):
        synths["P08"].sides[i] = side_file(d, "P08.%d.side" % i, i, lambda k, v, s: 1000000007 * (k + 3))

        def b13(k, v, s):
            x = 1000000007 * (k + 3) + (1000000 if k % 2 else -1000000)
            return x + (shift if (v, s) == ("VNC", 64) else 0)

        synths["P13"].sides[i] = side_file(d, "P13.%d.side" % i, i, b13)


def points_of(synths):
    return {pid: s.point() for pid, s in synths.items()}


def by_rid(reads):
    return {r.rid: r for r in reads}


SHARED = {}


def setUpModule():
    SHARED["tmp"] = tempfile.mkdtemp(prefix="stripes-b-sym-")
    SHARED["synths"] = {pid: Synth(pid) for pid in e.SYM_POINTS}
    add_sides(SHARED["synths"], SHARED["tmp"])
    SHARED["pts"] = points_of(SHARED["synths"])


def tearDownModule():
    shutil.rmtree(SHARED["tmp"])


class Base(unittest.TestCase):
    """The whole layout built once per module (setUpModule); a test changes a fresh Synth of one point."""

    @classmethod
    def setUpClass(cls):
        cls.synths = SHARED["synths"]
        cls.pts = SHARED["pts"]

    def fresh(self, pid):
        """A Synth of one point that a test may change, and the points dict with it in place."""
        s = Synth(pid)
        s.sides = dict(self.synths[pid].sides)
        pts = dict(self.pts)
        return s, pts


# ---------------------------------------------------------------------------------------------------------------------
# The read helpers on hand-built counts.


class Helpers(unittest.TestCase):
    def test_h8_tests(self):
        vr = make_vr([100] * 16, 0, 0)
        t = e.h8_tests(vr, ("pi", "mir", "br", "bi"))
        self.assertEqual(len(t), 18)
        self.assertEqual(e.combine([x[4] for x in t]), c.MET)
        self.assertEqual(len(e.h8_tests(vr, ("mir", "bi"))), 9)
        sec = [100] * 16
        sec[3], sec[11] = 180, 20  # pi3: (160)^2 > 64 * 200
        t = e.h8_tests(make_vr(sec, 0, 0), ("pi",))
        self.assertEqual([x[0] for x in t if x[4] == c.FLAG], ["pi3"])
        self.assertEqual(e.combine([x[4] for x in t]), c.MISS)

    def test_h8_ambiguous_bracket(self):
        sec = [100] * 16
        sec[0], sec[8] = 145, 55  # (90 + 30)^2 = 14400 > 64 * 200, (90 - 30)^2 = 3600 <= 64 * 230
        t = e.h8_tests(make_vr(sec, 30, 0), ("pi",))
        self.assertEqual(t[0][4], c.UNRESOLVED)
        self.assertEqual(e.combine([x[4] for x in t]), c.NOT_RESOLVED)

    def test_signflip_rb_only_where_stated(self):
        s = make_sums(1 << 18, s_bi=1 << 50)
        s["bbi"] = 1 << 50
        self.assertEqual(e.signflip_test(s, "bi", False)[0], c.FLAG)  # 2^50 > 5 * 2^47
        self.assertEqual(e.signflip_test(s, "bi", True)[0], c.UNFLAGGED)  # |S| - RB = 0

    def test_lock_q(self):
        self.assertEqual(sum(Q), 1)
        for k in range(4):
            self.assertEqual({Q[k], Q[7 - k], Q[8 + k], Q[15 - k]}, {Q[k]})
        self.assertEqual(Q[0], fr(58030261, 1000000000))

    def test_lattice_tests(self):
        vr = lattice_vr(1 << 18, 11035)
        self.assertTrue(all(t[3] for t in e.lattice_tests(vr, Q)))
        sec = list(vr["sec"])
        sec[0], sec[2] = sec[2], sec[0]  # two sector counts swapped: |dev| = M'(q2 - q0) = 2149 > D + A
        bad = [t[0] for t in e.lattice_tests(make_vr(sec, vr["amb"], 11035), Q) if not t[3]]
        self.assertEqual(sorted(bad), [0, 2])

    def test_lattice_boundary_exact(self):
        # q = 1/16 at M' = 16 * 6400: D = (32 + sqrt(1024 + 1152 * 6000))/6 = (32 + sqrt(6913024))/6 = 443.53...
        q = [fr(1, 16)] * 16
        base = [6400] * 16
        for o, ok in ((6400 + 443, True), (6400 + 444, False)):
            sec = list(base)
            sec[0] = o
            sec[1] = 12800 - o
            got = {t[0]: t[3] for t in e.lattice_tests(make_vr(sec, 0, 0), q)}
            self.assertEqual((got[0], got[1]), (ok, ok))

    def test_e04_series_values(self):
        # 1/4 + the two-term series R(y) - 1/4, at the frozen E04 decimals
        for t, y, text in ((1, fr(1, 27), "0.25049"), (1, fr(1, 54), "0.25012"), (2, fr(1, 54), "0.25246")):
            b = fr(1, 4) + series.r_two_term(fr(-1, 4), t, y)
            self.assertEqual(series.check_decimal(b, text), series.CONTAINS)

    def test_x2(self):
        self.assertEqual(e.x2_of(make_vr([100] * 16, 0, 0)), 0)
        self.assertEqual(e.x2_of(make_vr([110, 90] + [100] * 14, 0, 0)), fr(2 * 160 * 160, 16 * 1600))

    def test_scoring_triples(self):
        m14 = fr(-1, 4)
        self.assertTrue(e.scoring_triples(FZ, "E04", [(m14, 1, 1), (m14, fr(1, 2), 1)], None).scored)
        s = e.scoring_triples(FZ, "E04", [(m14, fr(1, 2), 2), (m14, fr(1, 4), 2)], e.E04_T2)
        self.assertFalse(s.scored)
        with self.assertRaises(c.StageBStop):
            e.scoring_triples(FZ, "E04", [(m14, fr(1, 2), 2)], None)


# ---------------------------------------------------------------------------------------------------------------------
# The rows: constructed MET and NOT_MET cases.


class AllRows(Base):
    def test_all_met_and_read_file(self):
        vs = {v.row: v for v in e.read_e_sym(self.pts, run_set(), FZ)}
        self.assertEqual(sorted(vs), ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08"])
        for rid, v in vs.items():
            self.assertEqual(v.verdict, c.MET, rid)
            self.assertEqual(v.falsifier, "none", rid)
        cnt = {rid: v.counts() for rid, v in vs.items()}
        self.assertEqual(cnt["E01"]["scored"], 77)
        self.assertEqual(cnt["E02"]["scored"], 3 * 268 + 30)  # 9 points x (VNC, ctrl, LOCK) + P13 x 2 + P14
        self.assertEqual(cnt["E03"]["scored"], 154)
        self.assertEqual((cnt["E04"]["scored"], cnt["E04"]["report"]), (16, 1))
        self.assertEqual((cnt["E05"]["scored"], cnt["E05"]["report"]), (3 * 49, 38))
        self.assertEqual((cnt["E06"]["scored"], cnt["E06"]["report"]), (3 * 49, 25))
        self.assertEqual((cnt["E07"]["scored"], cnt["E07"]["report"]), (33, 11))
        self.assertEqual((cnt["E08"]["scored"], cnt["E08"]["report"]), (66, 66))
        rf = c.ReadFile(FZ)
        for v in vs.values():
            rf.add(v)
        lines = rf.lines()
        self.assertEqual(sum(1 for ln in lines if ln.startswith("STRIPES_VERDICT|")), 8)
        self.assertTrue(lines[-1].startswith("STRIPES_READ_END|"))

    def test_e07_designed_not_met_uniformity(self):
        r = by_rid(e.row_e07(self.pts, FZ))
        x = r["lk_b16_P01_t1_LOCK"]
        self.assertEqual((x.outcome, x.value), (c.MET, "not_uniform"))
        self.assertEqual(r["lk_lat_P07_t4_LOCK"].outcome, c.MET)


class RowE01(Base):
    def test_not_met_pi_pair(self):
        s, pts = self.fresh("P09")
        vr = s.vr[("ctrl", 192, "VNC")]
        vr["sec"][0] += 3000
        vr["sec"][8] -= 3000
        pts["P09"] = s.point()
        rs = e.row_e01(pts, FZ)
        bad = [r for r in rs if r.outcome == c.MISS]
        self.assertEqual([r.rid for r in bad], ["h8_P09_t3_VNC"])
        self.assertIn(("flagged", "pi0+mir0+mir7"), bad[0].detail)
        v = e._verdict(FZ, "E01", rs, e._misses(rs))
        self.assertEqual(v.verdict, c.NOT_MET)
        self.assertTrue(v.falsifier.startswith("h8_P09_t3_VNC:"))

    def test_sign_test(self):
        s, pts = self.fresh("P01")
        vr = s.vr[("ctrl", 64, "LOCK")]
        vr["bi_pos"] += 3000
        vr["bi_neg"] -= 3000
        pts["P01"] = s.point()
        r = by_rid(e.row_e01(pts, FZ))["h8_P01_t1_LOCK"]
        self.assertEqual(r.outcome, c.MISS)
        self.assertIn(("flagged", "sign_bi"), r.detail)


class RowE02(Base):
    def _row(self, pts):
        rs = e.row_e02(pts, FZ)
        return rs, e._verdict(FZ, "E02", rs, e._misses(rs)).verdict

    def test_met(self):
        rs, v = self._row(self.pts)
        self.assertEqual(v, c.MET)
        r = by_rid(rs)
        self.assertEqual(r["nx_P02_vnc"].value, 325)
        self.assertEqual(r["nx_P13_lock"].value, 3267)
        self.assertNotIn("nx_P13_ctrl", r)
        self.assertNotIn("nx_P14_lock", r)
        self.assertFalse(r["nabi0_P02_t1_VNC"].scored)

    def test_exchange_atom_with_bi_nonzero(self):
        s, pts = self.fresh("P05")
        s.vr[("ctrl", 128, "LOCK")]["xatom_bi_nz"] = 1
        pts["P05"] = s.point()
        rs, v = self._row(pts)
        self.assertEqual(v, c.NOT_MET)
        self.assertEqual(e._misses(rs), ["xbi_P05_t2_LOCK"])

    def test_atom_count_outside(self):
        s, pts = self.fresh("P03")
        s.atoms["rest"]["nl_exch"] += 200  # 525 > 433 at 2^22
        pts["P03"] = s.point()
        rs, v = self._row(pts)
        self.assertEqual((v, e._misses(rs)), (c.NOT_MET, ["nx_P03_vnc"]))

    def test_signflip_bi_and_mirror(self):
        s, pts = self.fresh("P08")
        s.sums[("ctrl", 64, "V1", "all")]["bi"] = 6 << 47
        vr = s.vr[("ctrl", 256, "RN")]
        vr["sec"][2] += 1500
        vr["sec"][13] -= 1500
        pts["P08"] = s.point()
        rs, v = self._row(pts)
        self.assertEqual(v, c.NOT_MET)
        self.assertEqual(sorted(e._misses(rs)), ["h8_P08_t4_RN", "sf_bi_P08_t1_V1"])

    def test_lock_rb(self):
        s, pts = self.fresh("P12")
        for v in ("LOCK", "FLIP"):
            x = s.sums[("ctrl", 64, v, "all")]
            x["bi"] = x["bbi"] = 1 << 50
        pts["P12"] = s.point()
        rs, _ = self._row(pts)
        r = by_rid(rs)
        self.assertEqual(r["sf_bi_P12_t1_LOCK"].outcome, c.MET)
        self.assertEqual(r["sf_bi_P12_t1_FLIP"].outcome, c.MISS)


class RowE03(Base):
    def test_met_and_not_met(self):
        rs = e.row_e03(self.pts, FZ)
        self.assertEqual(e._verdict(FZ, "E03", rs, []).verdict, c.MET)
        s, pts = self.fresh("P07")
        s.sums[("ctrl", 256, "FLIP", "all")]["br"] = -(6 << 47)
        pts["P07"] = s.point()
        rs = e.row_e03(pts, FZ)
        self.assertEqual(e._misses(rs), ["sf_br_P07_t4_FLIP"])
        self.assertEqual(e._verdict(FZ, "E03", rs, e._misses(rs)).verdict, c.NOT_MET)


class RowE04(Base):
    def test_met(self):
        rs = by_rid(e.row_e04(self.pts, run_set(), FZ))
        self.assertEqual(rs["pair_P08-P13_t1_VNC"].outcome, c.MET)
        self.assertIn(("pairs", 2 * COUNT), rs["pair_P08-P13_t1_VNC"].detail)
        self.assertEqual(rs["ratio_t1_1/27->1/54"].value, fr(1, 4))
        self.assertTrue(rs["ratio_t1_1/54->1/108"].scored)
        self.assertEqual((rs["ratio_t2_1/54->1/108"].scored, rs["ratio_t2_1/54->1/108"].scoring.why), (False, "X08"))

    def test_side_files_agree_with_their_blocks(self):
        # every side row of the fixtures carries its block: open_side cross-checks AGG_SUM and AGG_ATOMS (M4)
        for pid in ("P08", "P13"):
            sides = self.pts[pid].sides()
            self.assertEqual([i for i, _ in sides], [0, 1])
            for _, row in sides:
                self.assertIs(row["block"].side, row)
                self.assertEqual(c.open_side(row).count, COUNT)
        with TempDir() as d:
            syn = {"P08": Synth("P08"), "P13": Synth("P13")}
            add_sides(syn, d)
            p = syn["P13"].sides[1]["path"]
            with open(p, "r+b") as f:
                data = bytearray(f.read())
                data[64 + 8] ^= 1  # sample 0, VNC at step 64: br moved by one
                f.seek(0)
                f.write(bytes(data))
            syn["P13"].sides[1] = dict(syn["P13"].sides[1], sha256=hashlib.sha256(bytes(data)).hexdigest())
            pts = dict(self.pts, P08=syn["P08"].point(), P13=syn["P13"].point())
            with self.assertRaises(c.StageBStop) as ex:
                e.row_e04(pts, run_set(), FZ)
        self.assertEqual(ex.exception.reason, "side_sums")
        self.assertIn("P13 call 1 step 64 VNC set=all: side br=", ex.exception.detail)

    def test_paired_flag(self):
        with TempDir() as d:
            syn = {"P08": Synth("P08"), "P13": Synth("P13")}
            add_sides(syn, d, shift=-1000000)
            pts = dict(self.pts, P08=syn["P08"].point(), P13=syn["P13"].point())
            rs = e.row_e04(pts, run_set(), FZ)
        self.assertEqual(e._misses(rs), ["pair_P08-P13_t1_VNC"])
        self.assertEqual(e._verdict(FZ, "E04", rs, e._misses(rs)).verdict, c.NOT_MET)

    def test_ratio_power_one(self):
        rs = e.row_e04(self.pts, run_set(r2_scale=2), FZ)  # E[br](y/2)/E[br](y) = 1/2 and 1/8
        self.assertEqual(sorted(e._misses(rs)), ["ratio_t1_1/27->1/54", "ratio_t1_1/54->1/108"])
        self.assertEqual(e._verdict(FZ, "E04", rs, e._misses(rs)).verdict, c.NOT_MET)

    def test_t2_ratio_read_and_report(self):
        rs = e.row_e04(self.pts, run_set(r3_t2=512), FZ)  # t=2 ratio 1/2: no verdict
        r = by_rid(rs)["ratio_t2_1/54->1/108"]
        self.assertEqual((r.outcome, r.verdict), (c.MISS, c.REPORT))
        self.assertEqual(e._verdict(FZ, "E04", rs, e._misses(rs)).verdict, c.MET)

    def test_band_edge(self):
        # R2 mean 4096 * (1/4 + 1/100) + 4 SE away is MET at the edge: the band is [1/4 - 1/100 - 4SE, 1/4 + 1/100 +
        # 4SE] with e = 0 (the frozen falsifier band)
        rp = run_set()
        rp["R2"] = synth_run("R2", dict.fromkeys((32, 64, 128), 1065), eps=0)
        rp["R1"] = synth_run("R1", dict.fromkeys((32, 64, 128), 4096), eps=0)
        r = by_rid(e.row_e04(self.pts, rp, FZ))["ratio_t1_1/27->1/54"]
        self.assertEqual(r.value, fr(1065, 4096))  # 0.26001 > 0.26 with SE = 0
        self.assertEqual(r.outcome, c.MISS)
        rp["R2"] = synth_run("R2", dict.fromkeys((32, 64, 128), 1064), eps=0)
        self.assertEqual(by_rid(e.row_e04(self.pts, rp, FZ))["ratio_t1_1/27->1/54"].outcome, c.MET)


class RowE05(Base):
    def _v(self, pts):
        rs = e.row_e05(pts, FZ)
        return rs, e._verdict(FZ, "E05", rs, e._misses(rs)).verdict

    def test_met(self):
        rs, v = self._v(self.pts)
        self.assertEqual(v, c.MET)
        law = by_rid(rs)["nl_law_P08_t1_NL"]
        self.assertFalse(law.scored)

    def test_calls_differ(self):
        s, pts = self.fresh("P06")
        s.nl_override[(7, 192)] = nl_text(s.spec, 192, 1000001)
        pts["P06"] = s.point()
        rs, v = self._v(pts)
        self.assertEqual((v, e._misses(rs)), (c.NOT_MET, ["nl_same_P06_t3_NL"]))

    def test_bi_and_zero_field(self):
        s, pts = self.fresh("P02")
        s.nl[64] = nl_text(s.spec, 64, 1000000, bi=-1)
        t = Synth("P07")
        t.nl[256] = nl_text(t.spec, 256, 5)
        pts.update(P02=s.point(), P07=t.point())
        rs, v = self._v(pts)
        self.assertEqual(v, c.NOT_MET)
        self.assertEqual(sorted(e._misses(rs)), ["nl_bi_P02_t1_NL", "nl_br_P07_t4_NL"])

    def test_nl_sha256_edited(self):
        s, pts = self.fresh("P11")
        s.sha_override[3] = "0" * 64
        pts["P11"] = s.point()
        with self.assertRaises(c.StageBStop) as ex:
            e.row_e05(pts, FZ)
        self.assertEqual(ex.exception.reason, "nl_sha256")


class RowE06(Base):
    def _v(self, pts):
        rs = e.row_e06(pts, FZ)
        return rs, e._verdict(FZ, "E06", rs, e._misses(rs)).verdict

    def test_met_and_expectations(self):
        rs, v = self._v(self.pts)
        self.assertEqual(v, c.MET)
        r = by_rid(rs)
        x = r["m0_exp_P04_t1_MODE0-VNC"]
        self.assertEqual((x.scored, x.frozen, x.detail), (False, "expected_NOT_MET", (("as_read", c.MISS),)))
        self.assertEqual(r["m0_exp_P02_t2_MODE0-VNC"].detail, (("as_read", c.MET),))
        self.assertNotIn("m0_exp_P02_t3_MODE0-VNC", r)
        self.assertNotIn("m0_exp_P07_t1_MODE0-VNC", r)

    def test_not_met(self):
        s1, pts = self.fresh("P10")
        for k in ("mis_big_both", "mis_big_any", "mis"):
            s1.cmp[("ctrl", 128, "MODE0")][k] = 1
        s2 = Synth("P03")
        cm = s2.cmp[("ctrl", 256, "MODE0")]
        cm["br"][0] -= 1
        cm["br"][1] += 1
        s3 = Synth("P12")
        vr = s3.vr[("ctrl", 64, "MODE0")]
        for k, d in ((0, 900), (8, 900), (15, 900), (7, 900), (1, -900), (9, -900), (14, -900), (6, -900)):
            vr["sec"][k] += d
        pts.update(P10=s1.point(), P03=s2.point(), P12=s3.point())
        rs, v = self._v(pts)
        self.assertEqual(v, c.NOT_MET)
        self.assertEqual(sorted(e._misses(rs)), ["m0_b16_P12_t1_MODE0-VNC", "m0_sec_P10_t2_MODE0-VNC",
                                                 "m0_sign_P03_t4_MODE0-VNC"])
        self.assertEqual(by_rid(rs)["m0_b16_P12_t1_MODE0-VNC"].value, "VNC=uniform:MODE0=not_uniform")


class RowE06Readings(Base):
    def test_sector_claim_covers_both_readings(self):
        cm = {"mis_big_both": 0, "mis_big_any": 0}
        self.assertEqual(e.sector_claim(cm), c.MET)
        cm["mis_big_any"] = 2  # a mismatch where only one of the two B is big
        self.assertEqual(e.sector_claim(cm), c.NOT_RESOLVED)
        cm["mis_big_both"] = 1
        self.assertEqual(e.sector_claim(cm), c.MISS)


class RowE07(Base):
    def _v(self, pts):
        rs = e.row_e07(pts, FZ)
        return rs, e._verdict(FZ, "E07", rs, e._misses(rs)).verdict

    def test_met(self):
        self.assertEqual(self._v(self.pts)[1], c.MET)

    def test_mismatch(self):
        s, pts = self.fresh("P01")
        s.lock[("ctrl", 64)]["mis"] = 1
        pts["P01"] = s.point()
        rs, v = self._v(pts)
        self.assertEqual((v, e._misses(rs)), (c.NOT_MET, ["lk_mis_P01_t1_LOCK"]))

    def test_two_sector_counts_swapped(self):
        s, pts = self.fresh("P01")
        sec = s.vr[("ctrl", 128, "LOCK")]["sec"]
        sec[0], sec[2] = sec[2], sec[0]
        pts["P01"] = s.point()
        rs, v = self._v(pts)
        self.assertEqual((v, e._misses(rs)), (c.NOT_MET, ["lk_lat_P01_t2_LOCK"]))
        self.assertIn(("outside", "0:2"), by_rid(rs)["lk_lat_P01_t2_LOCK"].detail)
        self.assertIn("h8_P01_t2_LOCK", e._misses(e.row_e01(pts, FZ)))  # E01 sees the broken Klein orbit too

    def test_lock_uniform_breaks_design(self):
        s, pts = self.fresh("P07")
        m = 1 << 18
        at = s.atoms["ctrl"]["lk_klein"]
        s.vr[("ctrl", 192, "LOCK")] = uniform_vr(m, at)
        pts["P07"] = s.point()
        rs, v = self._v(pts)
        self.assertEqual(v, c.NOT_MET)
        self.assertEqual(sorted(e._misses(rs)), ["lk_b16_P07_t3_LOCK", "lk_lat_P07_t3_LOCK"])


class RowE08(Base):
    def _v(self, pts):
        rs, fals = e.row_e08(pts, FZ)
        return rs, fals, e._verdict(FZ, "E08", rs, fals).verdict

    def test_met(self):
        rs, fals, v = self._v(self.pts)
        self.assertEqual((v, fals), (c.MET, []))
        self.assertEqual(by_rid(rs)["x2_P09_t4_V0"].value, fr(225, 262063))  # 16 O_k = M' - 15, A = 15

    def test_klein_symmetric_anisotropy_is_the_falsifier(self):
        s, pts = self.fresh("P09")
        vr = s.vr[("ctrl", 256, "V0")]
        for k, d in ((0, 2000), (8, 2000), (15, 2000), (7, 2000), (1, -2000), (9, -2000), (14, -2000), (6, -2000)):
            vr["sec"][k] += d
        pts["P09"] = s.point()
        self.assertEqual(e._misses(e.row_e01(pts, FZ)), [])  # E01 holds
        rs, fals, v = self._v(pts)
        self.assertEqual((v, fals), (c.NOT_MET, ["b16_P09_t4_V0"]))

    def test_flag_while_e01_fails(self):
        s, pts = self.fresh("P01")
        vr = s.vr[("rest", 192, "VNC")]
        vr["sec"][5] += 6000
        vr["sec"][4] -= 6000
        pts["P01"] = s.point()
        self.assertEqual(e._misses(e.row_e01(pts, FZ)), ["h8_P01_t3_VNC"])
        rs, fals, v = self._v(pts)
        self.assertEqual((v, fals), (c.NOT_MET, []))
        self.assertEqual(e._misses(rs), ["b16_P01_t3_VNC"])


class Stop(Base):
    def test_lost_call_and_dropped_record(self):
        s, pts = self.fresh("P05")
        s.lost.add(3)
        s.call_steps[10] = (64, 128, 192)
        pts["P05"] = p = s.point()
        self.assertEqual((p.steps, p.not_measured), ((64, 128, 192), (256,)))
        rs = by_rid(e.row_e02(pts, FZ))
        r = rs["h8_P05_t4_V1"]
        self.assertEqual(r.outcome, c.NOT_MEASURED)
        self.assertIn(("lost", "record_not_reached"), r.detail)
        self.assertIn(("lost_calls", "3"), rs["h8_P05_t1_V1"].detail)
        self.assertEqual(rs["nx_P05_vnc"].outcome, c.NOT_MEASURED)
        self.assertEqual(rs["nx_P05_lock"].outcome, c.NOT_MEASURED)
        self.assertEqual(rs["h8_P05_t1_VNC"].outcome, c.MET)
        v = e._verdict(FZ, "E02", list(rs.values()), [])
        self.assertEqual(v.verdict, c.NOT_RESOLVED)
        self.assertEqual(len(rs), len(by_rid(e.row_e02(self.pts, FZ))))  # same reads, built NOT_MEASURED

    def test_every_call_lost(self):
        s, pts = self.fresh("P13")
        s.lost.update(range(64))
        p = c.Point(s.spec)
        p.lost = [(i, "engine_stop_rc4") for i in range(64)]
        p.steps, p.not_measured = (), s.spec.steps
        pts["P13"] = p
        rs = by_rid(e.row_e04(pts, run_set(), FZ))
        self.assertEqual(rs["pair_P08-P13_t2_LOCK"].outcome, c.NOT_MEASURED)
        rs6 = by_rid(e.row_e06(pts, FZ))
        self.assertEqual(rs6["m0_sec_P13_t1_MODE0-VNC"].outcome, c.NOT_MEASURED)
        self.assertEqual(rs6["m0_exp_P13_t1_MODE0-VNC"].verdict, c.NOT_MEASURED)

    def test_lost_run_batches(self):
        rp = run_set()
        r = rp["R3"]
        r.lost = [(5, "engine_stop_empty")]
        r.batches = r.batches[:63]
        r.steps = (32, 64)
        rs = by_rid(e.row_e04(self.pts, rp, FZ))
        # rule STOP for runs: a lost batch reached no record, so every ratio with R3 is NOT_MEASURED and states the
        # loss; the ratio of R1 and R2 is read
        for rid in ("ratio_t1_1/54->1/108", "ratio_t2_1/54->1/108"):
            self.assertEqual(rs[rid].outcome, c.NOT_MEASURED, rid)
            self.assertIn(("lost", "batch_lost_R3"), rs[rid].detail)
            self.assertIn(("lost_batches_R3", "5"), rs[rid].detail)
        self.assertEqual(rs["ratio_t1_1/27->1/54"].outcome, c.MET)


# ---------------------------------------------------------------------------------------------------------------------
# The read helpers on the real excluded-point blocks (N=27, delta=1/4, y=0 and y=1/40, 2 calls of 4096).


def load_x(spec, name, edit=None):
    files = {"0.hbp": read(os.path.join(AGG, name + ".0.agg")), "1.hbp": read(os.path.join(AGG, name + ".1.agg"))}
    if edit:
        files = edit(files)
    with TempDir() as d:
        point_dir(d, {k: with_trailer(v) for k, v in files.items()})
        return c.load_point(d, spec)


class RealExcluded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x0 = load_x(X0, "X0")
        cls.x1 = load_x(X1, "X1")

    def test_x0_klein_zero_mean_lattice(self):
        rr = c.Scoring(False, "test")
        for step in (64, 128):
            for v in ALL7:
                self.assertEqual(e.h8_read("T", self.x0, step, v, ("pi", "mir", "br", "bi")).outcome, c.MET)
                self.assertEqual(e.signflip_point_read("T", self.x0, step, v, "br", True, "T").outcome, c.MET)
                self.assertEqual(e.signflip_point_read("T", self.x0, step, v, "bi", v == "LOCK", "T").outcome,
                                 c.MET)
            lk = by_rid(e.lock_reads("T", self.x0, step, Q, rr))
            t = e.t_text(step)
            self.assertEqual(lk["lk_mis_X0_t%s_LOCK" % t].outcome, c.MET)  # arg B = arg(c^2) on real samples
            self.assertEqual(lk["lk_lat_X0_t%s_LOCK" % t].outcome, c.MET)  # the frozen q_k at N=27 too
            self.assertEqual(lk["lk_b16_X0_t%s_LOCK" % t].value, "uniform")  # 7824 samples: below B16 resolution
            for v in e.LATTICE6:
                self.assertEqual(e.uniform_reads("T", self.x0, step, v, rr)[0].outcome, c.MET)
            for r in e.nl_reads("T", self.x0, step, rr):
                self.assertEqual(r.outcome, c.MET)
            for r in e.mode0_reads("T", self.x0, step):
                self.assertEqual(r.outcome, c.MET)

    def test_x1_exchange_nl_mode0(self):
        rr = c.Scoring(False, "test")
        for step in (64, 128):
            for v in ALL7:
                self.assertEqual(e.h8_read("T", self.x1, step, v, ("mir", "bi")).outcome, c.MET)
                self.assertEqual(e.signflip_point_read("T", self.x1, step, v, "bi", v == "LOCK", "T").outcome,
                                 c.MET)
                self.assertEqual(e.xbi_read("T", self.x1, step, v).outcome, c.MET)
            nl = e.nl_reads("T", self.x1, step, rr)
            self.assertEqual([r.outcome for r in nl[:3]], [c.MET] * 3)
            law = nl[3]
            self.assertTrue(fr(9, 10) < law.lo and law.hi < fr(11, 10))  # br/2^40 against y^2 |g|^2 at s = 0.13
            for r in e.mode0_reads("T", self.x1, step):
                self.assertEqual(r.outcome, c.MET)
        e.check_nl_sha256(self.x0)
        e.check_nl_sha256(self.x1)

    def test_x1_forged_exchange_atom(self):
        def edit(files):
            t = files["0.hbp"].replace("|variant=VNC|M=4096|atoms=1|xatoms=1|xatom_bi_nz=0|",
                                       "|variant=VNC|M=4096|atoms=1|xatoms=1|xatom_bi_nz=1|", 1)
            self.assertNotEqual(t, files["0.hbp"])
            return dict(files, **{"0.hbp": rehash(t)})

        pt = load_x(X1, "X1", edit)
        self.assertEqual(e.xbi_read("E02", pt, 64, "VNC").outcome, c.MISS)

    def test_x1_forged_nl_row(self):
        def edit(files, forge_call_hash=False):
            t = files["1.hbp"]
            ln = [x for x in t.split("\n") if x.startswith("AGG_NL|") and "|step=64|" in x][0]
            br = [p for p in ln.split("|") if p.startswith("br=")][0]
            new = ln.replace("|" + br + "|", "|br=%d|" % (int(br[3:]) + 1))
            t = t.replace(ln, new)
            if forge_call_hash:
                body = [x for x in t.split("\n") if x.startswith("AGG_NL|")]
                h = hashlib.sha256("".join(x[len("AGG_NL|"):] + "\n" for x in body).encode("ascii")).hexdigest()
                call = [x for x in t.split("\n") if x.startswith("AGG_CALL|")][0]
                old = [p for p in call.split("|") if p.startswith("nl_sha256=")][0]
                t = t.replace(call, call.replace(old, "nl_sha256=" + h))
            return dict(files, **{"1.hbp": rehash(t)})

        with self.assertRaises(c.StageBStop) as ex:
            load_x(X1, "X1", edit)  # common.parse_block checks nl_sha256 against the call's AGG_NL rows
        self.assertEqual(ex.exception.reason, "nl_sha256")
        pt = load_x(X1, "X1", lambda f: edit(f, True))
        e.check_nl_sha256(pt)
        rr = c.Scoring(False, "test")
        self.assertEqual(e.nl_reads("E05", pt, 64, rr)[0].outcome, c.MISS)

    def test_real_side_pair(self):
        def row(name):
            t = read(os.path.join(AGG, name))
            ln = [x for x in t.split("\n") if x.startswith("AGG_SIDE|")][0]
            d = dict(p.split("=", 1) for p in ln.split("|")[1:-1])
            return {"path": d["path"], "sha256": d["sha256"], "bytes": int(d["bytes"]), "indices": int(d["indices"]),
                    "variants": d["variants"], "steps": d["steps"], "dir": AGG}

        a, b = row("Tside.0.agg"), row("Tside0.0.agg")
        acc, calls = e.paired_sums([(0, a)], [(0, b)])
        ref = c.paired_side_sums(c.open_side(a), c.open_side(b))
        self.assertEqual((acc, calls), (ref, [0]))
        with self.assertRaises(c.StageBStop) as ex:
            e.paired_sums([(1, a)], [(1, b)])  # a side file whose start is not 4096 * call
        self.assertEqual(ex.exception.reason, "side_pair")


class Layout(unittest.TestCase):
    def test_frozen_records_and_counts(self):
        self.assertEqual(sum(len(c.DUMP_POINTS[p].steps) for p in e.Y0_POINTS), 11)
        self.assertEqual(sum(len(c.DUMP_POINTS[p].steps) for p in e.NL_POINTS), 49)
        n = sum(len(c.DUMP_POINTS[p].steps) * (7 if c.DUMP_POINTS[p].all else 1) for p in e.E02_POINTS)
        self.assertEqual(n, 268)

    def test_table_point_required(self):
        pts = {pid: c.Point(c.DUMP_POINTS[pid]) for pid in e.SYM_POINTS}
        pts["P08"] = c.Point(c.DumpPoint("P08", 729, "-1/4", "1/54", 1048576, 64, (64, 128, 192, 256), True))
        with self.assertRaises(c.StageBStop):
            e.read_e_sym(pts, run_set(), FZ)


if __name__ == "__main__":
    unittest.main()
