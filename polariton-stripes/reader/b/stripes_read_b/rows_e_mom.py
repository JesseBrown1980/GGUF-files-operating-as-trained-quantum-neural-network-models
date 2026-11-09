"""Rows E09-E19 of the frozen prediction: the stripe-phase histogram (E09), the pinning moment Pi (E10, E11, E15,
E16), the block contrast Z_n (E12, E13), the crossover n* (E14, E19), the strong-pinning report (E17) and the Weyl
second moment (E18). They are read from the pooled stage A aggregates of P01-P14, the twens run sums of R1-R4 and the
QE rows of QR2, QR3, by rules READ3, B16, H8, SE, STOP and EXPOSED.

Pi_hat counts every sample of a read, the atoms by their own sign states: Pi is P(Re B>0)-1/2 of the whole law, and
the lattice values of rule PI count the atoms too. The H8 sign test and B16 leave the atoms out (rule ATOMS)."""

import os

from . import common as c
from . import frozen as frozen_mod
from . import qe as qe_mod
from . import runs as runs_mod
from . import series
from .exact import Iv, Rad, dec, div, fmt, fr, parse_rat, rat_text

VNC = "VNC"
CONTROLS = c.VARIANTS[1:]
POW4 = (4, 16, 64, 256, 1024, 4096)
MIN_BLOCKS = 1024
QUARTER = fr(1, 4)
UNIFORM = "uniform"
NOT_UNIFORM = "not_uniform"
UNRESOLVED = "unresolved"
M14 = fr(-1, 4)


class Lost(Exception):
    """A read without data (rule STOP): its record, its calls, its batches or its QE row were not measured."""

    def __init__(self, why):
        Exception.__init__(self, why)
        self.why = why


class Inputs:
    """The data of the ensemble rows: dump points {Pnn: Point}, run points {Rn: Run} and the QE reads of
    qe.parse_qe (None when no QE file is read: E18's quantum side is then NOT_MEASURED)."""

    def __init__(self, points=None, runs=None, qe=None):
        self.points = dict(points or {})
        self.runs = dict(runs or {})
        self.qe = qe

    def point(self, pid):
        if pid not in self.points:
            raise c.StageBStop("missing_point", pid)
        return self.points[pid]

    def run(self, rid):
        if rid not in self.runs:
            raise c.StageBStop("missing_point", rid)
        return self.runs[rid]


def load_inputs(agg_root, run_dir, qe_path=None, require_sums=True):
    """Every dump point from agg_root/<Pnn>/, the runs from run_dir and, when given, the QE stdout."""
    pts = {pid: c.load_point(os.path.join(agg_root, pid), spec, require_sums=require_sums)
           for pid, spec in c.DUMP_POINTS.items()}
    rs = runs_mod.load_runs(run_dir)
    q = qe_mod.parse_qe(qe_path) if qe_path else None
    return Inputs(pts, rs, q)


# ---------------------------------------------------------------------------------------------------------------------
# Data access: a record, variant or set of calls without data raises Lost, and the read is built NOT_MEASURED.


def _step_ok(pt, step):
    if not pt.measured(step):
        raise Lost("record_not_measured")


def vr_of(pt, step, v, scope):
    _step_ok(pt, step)
    d = pt.vr(step, v, scope)
    if d is None:
        raise Lost("no_calls")
    return d


def sums_of(pt, step, v, scope):
    _step_ok(pt, step)
    d = pt.sums(step, v, "all", scope)
    if d is None:
        raise Lost("no_calls")
    return d


def blk_of(pt, step, v, n, scope):
    _step_ok(pt, step)
    d = pt.blk(step, v, n, scope)
    if d is None:
        raise Lost("no_calls")
    return d


def cmp_of(pt, step, v):
    _step_ok(pt, step)
    d = pt.cmp(step, v)
    if d is None:
        raise Lost("no_calls")
    return d


def calls_of(pt, step, v, scope):
    _step_ok(pt, step)
    d = pt.per_call_sums(step, v, "all", scope)
    if not d:
        raise Lost("no_calls")
    return d


def run_step_ok(run, step):
    """Rule STOP for runs: only the records all 64 batches reached are read, so a lost batch leaves every record of
    its point NOT_MEASURED."""
    if run.lost:
        raise Lost("%s_batch_lost_%s" % (run.spec.id, "_".join(str(j) for j, _ in run.lost)))
    if step not in run.steps:
        raise Lost("record_not_measured")


def loss(pt, scope="all"):
    k = len(pt.lost_indices(scope))
    return (("lost_calls", k),) if k else ()


def run_loss(run):
    return (("lost_batches", len(run.lost)),) if run.lost else ()


def nm(row, rid, at, kind, scoring, why):
    return c.Read(row, rid, at, kind, scoring, c.NOT_MEASURED, detail=(("lost", why),))


def guarded(row, rid, at, kind, scoring, fn, *args):
    """fn(*args) builds the read; NOT_MEASURED when its data was not measured."""
    try:
        return fn(*args)
    except Lost as e:
        return nm(row, rid, at, kind, scoring, e.why)


def at_text(pid, t, *parts):
    return "_".join([pid, "t" + rat_text(fr(t))] + [str(p) for p in parts])


def triple(spec, t):
    """(delta, |s|, t) of a dump or run point (rule EXPOSED)."""
    s = parse_rat(spec.y) * c.square_root(spec.N)
    return fr(parse_rat(spec.delta)), abs(s), fr(t)


def scoring_at(fz, rid, triples, phrase):
    """A value read built at triples (delta, |s|, t), s != 0: read-and-report iff one is exposed (rule EXPOSED); the
    phrase (or None) is the frozen text that names it, and its presence must agree with the rule."""
    if any(tr[1] == 0 for tr in triples):
        raise c.StageBStop("exposed", "%s: s=0 takes value_scoring" % rid)
    ex = any(c.exposed(*tr) for tr in triples)
    if ex != (phrase is not None):
        raise c.StageBStop("exposed", "%s %s: rule and row text disagree" % (rid, triples))
    if phrase is None:
        return c.scored("unexposed")
    return c.report(fz, "STRIPES_PREDICT", rid, phrase, "X08")


def need(fz, rid, phrase, *texts):
    """The phrase stands verbatim in the frozen row and holds every frozen decimal taken from it."""
    fz.require("STRIPES_PREDICT", rid, phrase)
    for t in texts:
        if t not in phrase:
            raise c.StageBStop("frozen_text", "%s: %s not in its phrase" % (rid, t))
    return phrase


def combine(outs):
    """The outcome of a read made of several tests (one per block size): READ3 over the tests."""
    if c.MISS in outs:
        return c.MISS
    if outs and all(o == c.MET for o in outs):
        return c.MET
    if outs and all(o == c.NOT_MEASURED for o in outs):
        return c.NOT_MEASURED
    return c.NOT_RESOLVED


def sampled_bracket(x_lo, x_hi, p, tol_lo, tol_hi, e):
    """Rule READ3 for a sampled estimate known to lie in [x_lo, x_hi] (its ambiguous samples placed every way), with a
    tolerance in [tol_lo, tol_hi]: MET if max |x-p| + e <= tol_lo, MISS if min |x-p| - e > tol_hi, else NOT_RESOLVED."""
    a, b = Rad.of(x_lo) - p, Rad.of(x_hi) - p
    if a > b:
        raise c.StageBStop("read3", "empty bracket")
    dmax = max(a.abs(), b.abs())
    dmin = Rad(0) if a.sign() <= 0 <= b.sign() else min(a.abs(), b.abs())
    if dmax + e <= tol_lo:
        return c.MET
    if dmin - e > tol_hi:
        return c.MISS
    return c.NOT_RESOLVED


def up(x, sig=4):
    """Upper decimal text of a Rad or a Q (for the detail fields)."""
    if isinstance(x, Rad):
        x = x.iv().hi
    return fmt(x, sig, "up")


# ---------------------------------------------------------------------------------------------------------------------
# Estimates.


class PiHat:
    """Pi_hat = (O+ - O-)/(2M) over the M samples of a read, the atoms by their own sign states, A ambiguous; SE^2 =
    (1 - 4 Pi_hat^2)/(4M) (rule SE) and the error e = 3SE + A/M of row E10."""

    def __init__(self, vr):
        self.pos = vr["br_pos"] + vr["at_br_pos"]
        self.neg = vr["br_neg"] + vr["at_br_neg"]
        self.amb = vr["br_amb"] + vr["at_br_amb"]
        self.M = vr["M"]
        if self.M <= 0 or self.pos + self.neg + self.amb != self.M:
            raise c.StageBStop("aggregate_identity", "Pi counts")
        self.x = c.pi_hat(self.pos, self.neg, self.M)
        self.se2 = c.se2_pi(self.x, self.M)

    def e(self):
        return c.se(self.se2, 3) + fr(self.amb, self.M)

    def bracket(self):
        """The values Pi_hat takes over the placements of the ambiguous samples."""
        return fr(self.pos - self.neg - self.amb, 2 * self.M), fr(self.pos - self.neg + self.amb, 2 * self.M)


class Zn:
    """Z_n = Sum s2 / Sum w over the K blocks of n of a read; z_b = K |S_b|^2 / Sum w has mean Z_n, and SE^2 =
    (K s4 - s2^2) / (w^2 (K - 1)) is the SE^2 of that mean (rule SE, CLT)."""

    def __init__(self, blk):
        self.K, s2, s4, w = blk["K"], blk["s2"], blk["s4"], blk["w"]
        if self.K < 2 or w <= 0:
            raise c.StageBStop("block_moments", "K<2 or w<=0")
        num = self.K * s4 - s2 * s2
        if num < 0:
            raise c.StageBStop("block_moments", "K s4 < s2^2")
        self.Z = div(s2, w)
        self.se2 = div(num, w * w * (self.K - 1))

    def e3(self):
        return c.se(self.se2, 3)


def moments(s):
    """(M, |Sum B|^2, Sum |B|^2) of pooled AGG_SUM (or run batch) sums, at 2^80."""
    m = s["m"] if "m" in s else s["n"]
    return m, s["br"] * s["br"] + s["bi"] * s["bi"], s["br2"] + s["bi2"]


def rho_u(s):
    """rho_u = (|Sum B|^2 - Sum |B|^2) / ((M - 1) Sum |B|^2) (row E12)."""
    m, sb2, s2 = moments(s)
    return div(sb2 - s2, (m - 1) * s2)


def bbar2_u(s):
    """|Bbar|^2_u = (|Sum B|^2 - Sum |B|^2) / (M (M - 1)) (rows E14, E19), at 2^80."""
    m, sb2, s2 = moments(s)
    return div(sb2 - s2, m * (m - 1))


def nstar_of(rs):
    """n*_hat = (S2/M)/|Bbar|^2_u - 1 = V/|Bbar|^2_u over the summed sums rs; None when |Bbar|^2_u <= 0."""
    tot = {k: sum(r[k] for r in rs) for k in ("m", "br", "bi", "br2", "bi2")}
    b2 = bbar2_u(tot)
    if b2 <= 0:
        return None
    return div(div(tot["br2"] + tot["bi2"], tot["m"]), b2) - 1


def nstar_jackknife(rs):
    """(n*_hat, jackknife SE^2) over the calls rs (rule SE); (None, None) when it or a leave-one-out value is not
    estimable."""
    if len(rs) < 2 or nstar_of(rs) is None or any(nstar_of(rs[:j] + rs[j + 1 :]) is None for j in range(len(rs))):
        return None, None
    return c.jackknife(nstar_of, rs)


def n_list(nominal):
    """The block sizes with at least 1024 blocks in the frozen sample count (row E12)."""
    return tuple(n for n in c.BLOCK_SIZES if nominal // n >= MIN_BLOCKS)


def b16_of(vr):
    return c.b16(vr["sec"], vr["amb"], vr["mp"])


def flagged_text(per):
    return "+".join(str(k) for k, p in enumerate(per) if p == c.FLAG) or "none"


def uniform_outcome(verdict, predicted):
    """A B16 (or E11 uniformity) verdict against the predicted one."""
    return c.read3_outcome(verdict, predicted, NOT_UNIFORM if predicted == UNIFORM else UNIFORM)


def band_verdict_text(out):
    return {c.MET: "MET", c.MISS: "NOT_MET"}.get(out, out)


# ---------------------------------------------------------------------------------------------------------------------
# Read builders shared by several rows.


def b16_read(row, rid, at, sc, vr, predicted, frozen="none", extra=()):
    """Rule B16 on the M' non-atom samples; predicted UNIFORM, NOT_UNIFORM or None (read and report, no prediction)."""
    verdict, per = b16_of(vr)
    mp, a, o0 = vr["mp"], vr["amb"], vr["sec"][0]
    out = c.MET if predicted is None else uniform_outcome(verdict, predicted)
    det = (("verdict", verdict), ("flagged", flagged_text(per)), ("Mp", mp), ("A", a),
           ("sector0_dev", "%s..%s" % (fmt(fr(o0, mp) - fr(1, 16), 4, "down"),
                                       fmt(fr(o0 + a, mp) - fr(1, 16), 4, "up"))),
           ("threshold", fmt(fr(c.b16_threshold_D(mp), 16 * mp), 3)))
    band = "B16_" + (predicted or "no_prediction")
    return c.Read(row, rid, at, "B16", sc, out, value=verdict, band=band, frozen=frozen, detail=det + tuple(extra))


def pi_tol(p, m, frac):
    """tol = frac Pi + 3/sqrt(M)."""
    return Rad(frac * p) + Rad.sqrt(fr(1, m), 3)


def pi_read(row, rid, at, sc, pi, p_text, tol, kind="sampled", frozen=None, extra=()):
    """Pi_hat against a frozen value p at tol with e = 3SE + A/M (rule READ3, sampled)."""
    p = dec(p_text)
    e = pi.e()
    out = c.read3_sampled(pi.x, p, tol, e)
    return c.Read(row, rid, at, kind, sc, out, value=pi.x, lo=pi.x - e, hi=pi.x + e,
                  band="p=%s,tol=%s" % (p_text, up(tol, 6)), frozen=frozen or p_text,
                  detail=(("M", pi.M), ("A", pi.amb), ("e", up(pi.e()))) + tuple(extra))


def pi_report(row, rid, at, sc, pi, extra=()):
    e = pi.e()
    return c.Read(row, rid, at, "report", sc, c.MET, value=pi.x, lo=pi.x - e, hi=pi.x + e,
                  detail=(("M", pi.M), ("A", pi.amb)) + tuple(extra))


def z_read(row, rid, at, sc, pt, step, v, scope, ns, kind, rho=None):
    """Z_n tests over the block sizes ns, one read: kind "zero" |Z_n - 1| + 3SE <= 1/4 (E12 at y=0); "iid"
    |Z_n - 1 - (n-1) rho_u| + 3SE <= 1/4 + (n-1) rho_u/10 (E12); "tol" |Z_n - 1 - (n-1) rho| + 3SE <= 1/4 + (n-1) rho/5
    at the frozen rho (E13). A size left with fewer than 1024 blocks by a loss is NOT_MEASURED."""
    s = sums_of(pt, step, v, scope)
    ru = rho_u(s)
    outs, det, last = [], [], None
    for n in ns:
        k = blk_of(pt, step, v, n, scope)
        if k["K"] < MIN_BLOCKS:
            outs.append(c.NOT_MEASURED)
            det.append(("n%d" % n, "K%d_NOT_MEASURED" % k["K"]))
            continue
        z = Zn(k)
        if kind == "zero":
            p, tol = fr(1), QUARTER
        elif kind == "iid":
            p, tol = 1 + (n - 1) * ru, QUARTER + div((n - 1) * ru, 10)
        else:
            p, tol = 1 + (n - 1) * rho, QUARTER + div((n - 1) * rho, 5)
        o = c.read3_sampled(z.Z, p, tol, z.e3())
        outs.append(o)
        det.append(("n%d" % n, "%s+-%s_%s" % (fmt(z.Z, 6), up(z.e3(), 3), o)))
        last = z
    out = combine(outs)
    extra = [("rho_u", fmt(ru, 6))]
    ns_hat = nstar_of([s])
    extra.append(("nstar_hat", "none" if ns_hat is None else fmt(ns_hat, 6)))
    band = {"zero": "abs(Z_n-1)+3SE<=1/4", "iid": "abs(Z_n-1-(n-1)rho_u)+3SE<=1/4+(n-1)rho_u/10",
            "tol": "abs(Z_n-1-(n-1)rho)+3SE<=1/4+(n-1)rho/5"}[kind]
    if last is None:
        return c.Read(row, rid, at, "sampled", sc, out, band=band, detail=tuple(det + extra) + loss(pt, scope))
    e = last.e3()
    return c.Read(row, rid, at, "sampled", sc, out, value=last.Z, lo=last.Z - e, hi=last.Z + e, band=band,
                  detail=tuple(det + extra) + loss(pt, scope))


def zband_read(row, rid, at, sc, pt, step, n, predicted, frozen):
    """The band [3/4, 5/4] at n: band MET if |Z_n - 1| + 3SE <= 1/4, NOT_MET if |Z_n - 1| - 3SE > 1/4; the read
    compares that band verdict with the predicted one (MET or NOT_MET)."""
    k = blk_of(pt, step, VNC, n, "all")
    if k["K"] < MIN_BLOCKS:
        raise Lost("fewer_than_1024_blocks")
    z = Zn(k)
    e = z.e3()
    bv = c.read3_sampled(z.Z, 1, QUARTER, e)
    want = c.MET if predicted == c.MET else c.MISS
    out = c.read3_outcome(bv, want, c.MISS if want == c.MET else c.MET)
    return c.Read(row, rid, at, "band", sc, out, value=z.Z, lo=z.Z - e, hi=z.Z + e, band=c.Band(fr(3, 4), fr(5, 4)),
                  frozen=frozen, detail=(("band_verdict", band_verdict_text(bv)), ("predicted", predicted),
                                         ("K", z.K)) + loss(pt))


def paired(pt, step, v):
    """Pi_v - Pi_VNC on the first 2^18 indices (the same samples): the bracket of the difference of the two Pi_hat over
    the ambiguous samples, and a conservative SE^2 = D/M^2 from AGG_CMP, D counting the discordant cells, every
    ambiguous cell and every sample outside the common non-atom set (rule SE, binomial)."""
    a = PiHat(vr_of(pt, step, v, "ctrl"))
    r = PiHat(vr_of(pt, step, VNC, "ctrl"))
    if a.M != r.M:
        raise c.StageBStop("aggregate_identity", "paired counts differ")
    cm = cmp_of(pt, step, v)
    t = cm["br"]
    m = a.M
    diff = (a.pos - a.neg) - (r.pos - r.neg)
    lo = fr(diff - a.amb - r.amb, 2 * m)
    hi = fr(diff + a.amb + r.amb, 2 * m)
    return lo, hi, fr(possibly_discordant(cm, m), m * m), a, r, cm


def possibly_discordant(cm, m):
    """An upper bound of D+ + D- on the M samples of a paired read: the certified discordant cells t1 and t3 of
    AGG_CMP, every ambiguous cell (t2, t5, t6, t7, t8) and every sample outside the common non-atom set (the atoms,
    whose concordance AGG_CMP does not give), each counted as possibly discordant."""
    t = cm["br"]
    if m < cm["common"]:
        raise c.StageBStop("aggregate_identity", "AGG_CMP common above M")
    return t[1] + t[3] + t[2] + t[5] + t[6] + t[7] + t[8] + (m - cm["common"])


def mid(lo, hi):
    return (fr(lo) + fr(hi)) * fr(1, 2)


# ---------------------------------------------------------------------------------------------------------------------
# E09 PHASE_HISTOGRAM_FLATTENS


E09_POINTS = ("P01", "P02", "P03", "P04", "P05", "P06", "P08")
E09_UNIFORM = ("P01", "P02")
E09_PRED = ("B16_uniform_at_t=1,_2:_P01_MET;_P02_MET_(sector-0_2.6e-4,_3.0e-4_against_6.70e-4;_false_flag_<=0.5"
            "_percent);_P03_NOT_MET_(1.03e-3,_1.21e-3:_8.7,_10.2_SD_against_5.67);_P04,_P05,_P06,_P08_NOT_MET")
E09_SECTOR0 = {"P02": ("2.6e-4", "3.0e-4"), "P03": ("1.03e-3", "1.21e-3")}
E09_EXCESS_TEXT = ("aligned_excess_p0+p15-1/8_(t=1/t=2,_Gaussian_MC_+-1.2e-4)_read_and_report:_P02_0.00055/0.00056,"
                   "_P03_0.00204/0.00239,_P04_0.00815/0.00954,_P05_0.03139/0.03639,_P06_0.10761/0.12151,"
                   "_P08_0.03958/0.05732")
E09_EXCESS = {"P02": ("0.00055", "0.00056"), "P03": ("0.00204", "0.00239"), "P04": ("0.00815", "0.00954"),
              "P05": ("0.03139", "0.03639"), "P06": ("0.10761", "0.12151"), "P08": ("0.03958", "0.05732")}
E09_X08 = "read-and-report_(X08):_P03-P06_at_every_record_and_P08_at_t=2;_scored:_P01,_P02_at_t=1,_2_and_P08_at_t=1"
E09_T34 = "t=1,_2_scored,_t=3,_4_read_and_report"
E09_FALS = "a_flag_at_P01_or_P02_at_t=1_or_2,_or_none_at_P08_at_t=1"


def excess_read(row, rid, at, sc, vr, frozen):
    """p0 + p15 - 1/8 over the M' non-atom samples, ambiguous samples bracketed, 3 binomial SE beside."""
    mp, a = vr["mp"], vr["amb"]
    o = vr["sec"][0] + vr["sec"][15]
    x = fr(o, mp) - fr(1, 8)
    hi = fr(o + a, mp) - fr(1, 8)
    e = c.se(c.se2_binomial(o, mp), 3)
    return c.Read(row, rid, at, "report", sc, c.MET, value=x, lo=x - e, hi=hi + e, frozen=frozen,
                  detail=(("over", "Mp_non-atoms"), ("Mp", mp), ("A", a)))


def row_e09(inp, fz):
    need(fz, "E09", E09_PRED, *[x for v in E09_SECTOR0.values() for x in v])
    need(fz, "E09", E09_EXCESS_TEXT, *[x for v in E09_EXCESS.values() for x in v])
    need(fz, "E09", E09_X08)
    need(fz, "E09", E09_T34)
    need(fz, "E09", E09_FALS)
    reads, fals = [], []
    for pid in E09_POINTS:
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        tr0 = triple(spec, 1)
        for t in (1, 2, 3, 4):
            step = c.step_of_t(t)
            if t >= 3:
                sc = c.report(fz, "STRIPES_PREDICT", "E09", E09_T34, "t3-4_read_and_report")
                pred = None
            elif tr0[1] == 0:
                sc = c.scored("s0_symmetry")
                pred = UNIFORM
            else:
                rr = pid in ("P03", "P04", "P05", "P06") or (pid == "P08" and t == 2)
                sc = scoring_at(fz, "E09", [triple(spec, t)], E09_X08 if rr else None)
                pred = UNIFORM if pid in E09_UNIFORM else NOT_UNIFORM
            frz = "sector-0_" + E09_SECTOR0[pid][t - 1] if pid in E09_SECTOR0 and t <= 2 else "none"
            rid = "b16_%s_t%d" % (pid, t)
            r = guarded("E09", rid, at_text(pid, t, VNC), "B16", sc, _e09_b16, rid, pid, t, sc, pt, step, pred, frz)
            reads.append(r)
            if r.scored and r.outcome == c.MISS:
                fals.append(rid)
        if pid in E09_EXCESS:
            for t in (1, 2):
                rid = "excess_%s_t%d" % (pid, t)
                sc = c.report(fz, "STRIPES_PREDICT", "E09", E09_EXCESS_TEXT, "row_text")
                reads.append(guarded("E09", rid, at_text(pid, t, VNC), "report", sc, _e09_excess, rid, pid, t, sc,
                                     pt, c.step_of_t(t)))
    return reads, fals


def _e09_b16(rid, pid, t, sc, pt, step, pred, frz):
    return b16_read("E09", rid, at_text(pid, t, VNC), sc, vr_of(pt, step, VNC, "all"), pred, frz, loss(pt))


def _e09_excess(rid, pid, t, sc, pt, step):
    return excess_read("E09", rid, at_text(pid, t, VNC), sc, vr_of(pt, step, VNC, "all"), E09_EXCESS[pid][t - 1])


# ---------------------------------------------------------------------------------------------------------------------
# E10 PINNING_MOMENT_LAW


E10_POINTS = ("P02", "P03", "P04", "P05", "P06", "P08")
E10_PI_TEXT = ("Pi_t=1/t=2:_P02_0.001354/0.001593;_P03_0.005387/0.006319;_P04_0.021076/0.024506;_P05_0.077517/0.088773;"
               "_P06_0.233911/0.262970;_P08_0.096275/0.136403;_tol_Pi/10+3/sqrt(M),_MET_on_all_12")
E10_PI = {"P02": ("0.001354", "0.001593"), "P03": ("0.005387", "0.006319"), "P04": ("0.021076", "0.024506"),
          "P05": ("0.077517", "0.088773"), "P06": ("0.233911", "0.262970"), "P08": ("0.096275", "0.136403")}
E10_RATIO_TEXT = ("Pi(P04)/Pi(P03)=3.912/3.878_(tol_1.2;_linear_onset_gives_2)_and_Pi(P05)/Pi(P04)=3.678/3.623"
                  "_(tol_0.4)_MET")
E10_RATIOS = (("P04", "P03", ("3.912", "3.878"), "1.2"), ("P05", "P04", ("3.678", "3.623"), "0.4"))
E10_SEP = "separation_from_4_read_and_report"
E10_X08 = "read-and-report_(X08):_P03-P06,_both_ratios_and_P08_t=2;_scored:_P02_(t=1,_2)_and_P08_t=1"
E10_METHOD = "Pi_hat=(O+_-_O-)/(2M),_certified_signs,_e=3SE+A/M,_SE^2=(1-4Pi_hat^2)/(4M);_delta-method_ratios"
E10_FALS = "a_MISS_on_a_scored_read;_P02_not_resolved_above_0_at_3_SE"


def ratio_parts(a, b):
    """R = Pi_a/Pi_b with its delta-method SE^2 (independent points, rule SE) and the half-width of its ambiguous
    bracket; None when Pi_b can reach 0."""
    blo, bhi = b.bracket()
    if blo <= 0 or b.x <= 0:
        return None
    r, se2 = c.ratio_indep(a.x, a.se2, b.x, b.se2)
    alo, ahi = a.bracket()
    iv = Iv(alo, ahi) * Iv(blo, bhi).inv()
    return r, se2, max(r - iv.lo, iv.hi - r)


def e10_not_above_zero(pi):
    """E10's falsifier "P02 not resolved above 0 at 3 SE": the low end of the ambiguity bracket, (O+ - O- - A)/(2M),
    minus 3 SE, is at or below 0 (ensemble review 2, M4; note reading_E10_falsifier)."""
    return (Rad.of(pi.bracket()[0]) - c.se(pi.se2, 3)).sign() <= 0


def row_e10(inp, fz):
    need(fz, "E10", E10_PI_TEXT, *[x for v in E10_PI.values() for x in v])
    need(fz, "E10", E10_RATIO_TEXT, *[x for _, _, v, tol in E10_RATIOS for x in v + (tol,)])
    need(fz, "E10", E10_SEP)
    need(fz, "E10", E10_X08)
    fz.require("STRIPES_PREDICT", "E10", E10_METHOD)
    need(fz, "E10", E10_FALS)
    reads, fals = [], []
    pis = {}
    for pid in E10_POINTS:
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        for t in (1, 2):
            rr = pid in ("P03", "P04", "P05", "P06") or (pid == "P08" and t == 2)
            sc = scoring_at(fz, "E10", [triple(spec, t)], E10_X08 if rr else None)
            rid = "pi_%s_t%d" % (pid, t)
            at = at_text(pid, t, VNC)
            try:
                pi = PiHat(vr_of(pt, c.step_of_t(t), VNC, "all"))
            except Lost as e:
                reads.append(nm("E10", rid, at, "sampled", sc, e.why))
                continue
            pis[(pid, t)] = pi
            p_text = E10_PI[pid][t - 1]
            r = pi_read("E10", rid, at, sc, pi, p_text, pi_tol(dec(p_text), pi.M, fr(1, 10)), extra=loss(pt))
            reads.append(r)
            if r.scored and r.outcome == c.MISS:
                fals.append(rid)
            elif r.scored and pid == "P02" and e10_not_above_zero(pi):
                fals.append(rid)
    if sum(1 for r in reads if r.rid.startswith("pi_")) != 12:
        raise c.StageBStop("rows_e", "E10 12 Pi reads")
    for num, den, texts, tol_text in E10_RATIOS:
        sn, sd = c.DUMP_POINTS[num], c.DUMP_POINTS[den]
        for t in (1, 2):
            sc = scoring_at(fz, "E10", [triple(sn, t), triple(sd, t)], E10_X08)
            rid = "ratio_%s/%s_t%d" % (num, den, t)
            at = "%s/%s_t%d_VNC" % (num, den, t)
            sep_sc = c.report(fz, "STRIPES_PREDICT", "E10", E10_SEP, "row_text")
            if (num, t) not in pis or (den, t) not in pis:
                reads.append(nm("E10", rid, at, "sampled", sc, "record_not_measured"))
                reads.append(nm("E10", "sep4_" + rid[6:], at, "report", sep_sc, "record_not_measured"))
                continue
            parts = ratio_parts(pis[(num, t)], pis[(den, t)])
            if parts is None:
                reads.append(c.Read("E10", rid, at, "sampled", sc, c.NOT_RESOLVED, frozen=texts[t - 1],
                                    detail=(("denominator", "reaches_0"),)))
                reads.append(c.Read("E10", "sep4_" + rid[6:], at, "report", sep_sc, c.MET, value="unbounded"))
                continue
            r, se2, half = parts
            e = c.se(se2, 3) + half
            out = c.read3_sampled(r, dec(texts[t - 1]), dec(tol_text), e)
            reads.append(c.Read("E10", rid, at, "sampled", sc, out, value=r, lo=r - e, hi=r + e,
                                band="p=%s,tol=%s" % (texts[t - 1], tol_text), frozen=texts[t - 1],
                                detail=(("e", up(e)), ("linear_onset", "2"))))
            reads.append(c.Read("E10", "sep4_" + rid[6:], at, "report", sep_sc, c.MET, value=r - 4, lo=r - 4 - e,
                                hi=r - 4 + e, band="R-4", detail=(("e", up(e)),)))
    return reads, fals


# ---------------------------------------------------------------------------------------------------------------------
# E11 DENSITY_ANALOG


E11_PI_TEXT = "Pi_t=1/t=2:_P11_0.001070/0.001260,_P12_0.004263/0.005005,_tol_Pi/10+3/sqrt(M),_MET"
E11_PI = {"P11": ("0.001070", "0.001260"), "P12": ("0.004263", "0.005005")}
E11_UNI_TEXT = ("uniform_NOT_MET_if_the_H8_sign_test_or_B16_flags:_P11_MET_(false_flag_0.02_to_0.3_percent),"
                "_P12_NOT_MET")
E11_UNI = {"P11": UNIFORM, "P12": NOT_UNIFORM}
E11_FALS = "P11_flagged_or_P12_unflagged_at_t=1_or_2;_a_MISS"


def uniformity(vr):
    """E11: not uniform if the H8 sign test on br or B16 flags, uniform if both are unflagged, else unresolved (both on
    the non-atom samples, rule ATOMS)."""
    sign = c.h8(vr["br_pos"], vr["br_neg"], vr["br_amb"])
    b, per = b16_of(vr)
    if sign == c.FLAG or b == NOT_UNIFORM:
        return NOT_UNIFORM, sign, b, per
    if sign == c.UNFLAGGED and b == UNIFORM:
        return UNIFORM, sign, b, per
    return UNRESOLVED, sign, b, per


def row_e11(inp, fz):
    need(fz, "E11", E11_PI_TEXT, *[x for v in E11_PI.values() for x in v])
    need(fz, "E11", E11_UNI_TEXT)
    need(fz, "E11", E11_FALS)
    reads, fals = [], []
    for pid in ("P11", "P12"):
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        for t in (1, 2):
            sc = scoring_at(fz, "E11", [triple(spec, t)], None)
            step = c.step_of_t(t)
            at = at_text(pid, t, VNC)
            p_text = E11_PI[pid][t - 1]
            reads.append(guarded("E11", "pi_%s_t%d" % (pid, t), at, "sampled", sc, _e11_pi, pid, t, sc, pt, step,
                                 p_text))
            reads.append(guarded("E11", "uniform_%s_t%d" % (pid, t), at, "uniformity", sc, _e11_uni, pid, t, sc, pt,
                                 step))
    fals = [r.rid for r in reads if r.scored and r.outcome == c.MISS]
    return reads, fals


def _e11_pi(pid, t, sc, pt, step, p_text):
    pi = PiHat(vr_of(pt, step, VNC, "all"))
    return pi_read("E11", "pi_%s_t%d" % (pid, t), at_text(pid, t, VNC), sc, pi, p_text,
                   pi_tol(dec(p_text), pi.M, fr(1, 10)), extra=loss(pt))


def _e11_uni(pid, t, sc, pt, step):
    vr = vr_of(pt, step, VNC, "all")
    v, sign, b, per = uniformity(vr)
    pred = E11_UNI[pid]
    out = uniform_outcome(v, pred)
    return c.Read("E11", "uniform_%s_t%d" % (pid, t), at_text(pid, t, VNC), "uniformity", sc, out, value=v,
                  band="uniform_" + ("MET" if pred == UNIFORM else "NOT_MET"),
                  detail=(("h8_sign_br", sign), ("b16", b), ("flagged", flagged_text(per)),
                          ("br_pos", vr["br_pos"]), ("br_neg", vr["br_neg"]), ("br_amb", vr["br_amb"])) + loss(pt))


# ---------------------------------------------------------------------------------------------------------------------
# E12 CONTRAST_DECAY_IID


E12_RANGE = ("y=0:_abs(Z_n-1)+3SE<=1/4_for_n=4..4096_(VNC_2^22),_up_to_1024_(2^20),_up_to_256_(2^18_controls),"
             "_at_least_1024_blocks")
E12_IID = ("identity_abs(Z_n-1-(n-1)rho_u)+3SE<=1/4+(n-1)rho_u/10_everywhere,_rho_u=(abs(Sum_B)^2-Sum_abs(B)^2)/"
           "((M-1)Sum_abs(B)^2)")
E12_POINT = "y=0:_P01,_P07,_P09,_all_variants_and_records;_identity_at_all_14_dump_points"
E12_METHOD = "exact_block_sums_inside_each_4096-sample_call;_SE_from_block_z_b_(CLT)"


def row_e12(inp, fz):
    need(fz, "E12", E12_RANGE)
    need(fz, "E12", E12_IID)
    need(fz, "E12", E12_POINT)
    need(fz, "E12", E12_METHOD)
    if n_list(1 << 22)[-1] != 4096 or n_list(1 << 20)[-1] != 1024 or n_list(1 << 18)[-1] != 256:
        raise c.StageBStop("rows_e", "E12 block ranges")
    reads = []
    for pid in sorted(c.DUMP_POINTS):
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        y0 = parse_rat(spec.y) == 0
        variants = (VNC,) + (CONTROLS if spec.all else ())
        for step in spec.steps:
            t = c.t_of_step(step)
            for v in variants:
                scope = "all" if v == VNC else "ctrl"
                ns = n_list(spec.vnc if v == VNC else spec.all * c.COUNT)
                at = at_text(pid, t, v)
                kinds = ("zero", "iid") if y0 else ("iid",)
                for kind in kinds:
                    sc = c.scored("s0_symmetry" if kind == "zero" else "iid_identity")
                    rid = "%s_%s_%s_t%s" % (kind, pid, v, rat_text(t))
                    reads.append(guarded("E12", rid, at, "sampled", sc, z_read, "E12", rid, at, sc, pt, step, v,
                                         scope, ns, kind))
    fals = [r.rid for r in reads if r.scored and r.outcome == c.MISS]
    return reads, fals


# ---------------------------------------------------------------------------------------------------------------------
# E13 CONTRAST_PLATEAU_WHEN_PINNED


E13_POINTS = ("P02", "P03", "P04", "P05", "P06", "P08")
E13_RHO_TEXT = ("rho_t=2_(t=1):_P02_9.2917e-6_(4.5447e-6);_P03_1.4500e-4_(7.1578e-5);_P04_2.1085e-3_(1.0770e-3);"
                "_P05_2.4298e-2_(1.3781e-2);_P06_0.16250_(0.11271);_P08_5.3411e-2_(2.1041e-2)")
E13_RHO = {"P02": ("4.5447e-6", "9.2917e-6"), "P03": ("7.1578e-5", "1.4500e-4"), "P04": ("1.0770e-3", "2.1085e-3"),
           "P05": ("1.3781e-2", "2.4298e-2"), "P06": ("0.11271", "0.16250"), "P08": ("2.1041e-2", "5.3411e-2")}
E13_NSTAR_TEXT = "n*_t=2:_107622,_6895.6,_473.28,_40.156,_5.1537,_17.723"
E13_NSTAR = {"P02": "107622", "P03": "6895.6", "P04": "473.28", "P05": "40.156", "P06": "5.1537", "P08": "17.723"}
E13_TOL = "Z_n_tol_1/4+(n-1)rho/5_MET"
E13_BAND2_TEXT = ("band_[3/4,5/4]_at_t=2:_P02_MET_to_n=4096_(1.038);_P03_MET_to_1024_(1.148),_NOT_MET_at_4096_(1.594);"
                  "_P04_MET_to_64_(1.133),_NOT_MET_from_256_(1.538,_3.157,_9.634);_P05,_P08_MET_at_4,_NOT_MET_from_16"
                  "_(P05_1.365,_2.531,_7.196,_25.86);_P06_NOT_MET_from_4_(1.4875)")
E13_BAND1_TEXT = ("band_[3/4,5/4]_at_P08_t=1_(rho_2.1041e-2,_added_before_the_freeze,_RP16):_MET_at_n=4_(1.0631),"
                  "_NOT_MET_from_n=16_(1.3156,_2.3256,_6.3655,_22.525_to_n=1024)")
MET_, NOT_ = c.MET, c.NOT_MET
E13_BANDS = (
    ("P02", 2, ((4, MET_, None), (16, MET_, None), (64, MET_, None), (256, MET_, None), (1024, MET_, None),
                (4096, MET_, "1.038"))),
    ("P03", 2, ((4, MET_, None), (16, MET_, None), (64, MET_, None), (256, MET_, None), (1024, MET_, "1.148"),
                (4096, NOT_, "1.594"))),
    ("P04", 2, ((4, MET_, None), (16, MET_, None), (64, MET_, "1.133"), (256, NOT_, "1.538"), (1024, NOT_, "3.157"),
                (4096, NOT_, "9.634"))),
    ("P05", 2, ((4, MET_, None), (16, NOT_, "1.365"), (64, NOT_, "2.531"), (256, NOT_, "7.196"),
                (1024, NOT_, "25.86"))),
    ("P06", 2, ((4, NOT_, "1.4875"), (16, NOT_, None), (64, NOT_, None), (256, NOT_, None), (1024, NOT_, None))),
    ("P08", 2, ((4, MET_, None), (16, NOT_, None), (64, NOT_, None), (256, NOT_, None), (1024, NOT_, None))),
    ("P08", 1, ((4, MET_, "1.0631"), (16, NOT_, "1.3156"), (64, NOT_, "2.3256"), (256, NOT_, "6.3655"),
                (1024, NOT_, "22.525"))),
)
E13_X08 = ("read-and-report_(X08):_P03-P06_at_every_record_and_P08_at_t=2,_their_frozen_rho,_n*_and_bands_kept_beside;"
           "_scored:_P02_(t=1,_2)_and_P08_t=1")
E13_POINT = "band_scored_at_t=2_at_P02_and_at_t=1_at_P08"
E13_FALS = "a_MISS,_or_a_scored_band_verdict_(P02_t=2,_P08_t=1)_reversed"


def _e13_rr(pid, t):
    return pid in ("P03", "P04", "P05", "P06") or (pid == "P08" and t == 2)


def row_e13(inp, fz):
    need(fz, "E13", E13_RHO_TEXT, *[x for v in E13_RHO.values() for x in v])
    need(fz, "E13", E13_NSTAR_TEXT, *E13_NSTAR.values())
    need(fz, "E13", E13_TOL)
    need(fz, "E13", E13_BAND2_TEXT, *[z for pid, t, b in E13_BANDS if t == 2 for _, _, z in b if z])
    need(fz, "E13", E13_BAND1_TEXT, *[z for pid, t, b in E13_BANDS if t == 1 for _, _, z in b if z])
    need(fz, "E13", E13_X08)
    fz.require("STRIPES_PREDICT", "E13", E13_POINT)
    need(fz, "E13", E13_FALS)
    reads = []
    for pid in E13_POINTS:
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        for t in (1, 2):
            sc = scoring_at(fz, "E13", [triple(spec, t)], E13_X08 if _e13_rr(pid, t) else None)
            rho_text = E13_RHO[pid][t - 1]
            rid = "tol_%s_t%d" % (pid, t)
            at = at_text(pid, t, VNC)
            r = guarded("E13", rid, at, "sampled", sc, z_read, "E13", rid, at, sc, pt, c.step_of_t(t), VNC, "all",
                        n_list(spec.vnc), "tol", dec(rho_text))
            r.frozen = "rho=" + rho_text + (",n*=" + E13_NSTAR[pid] if t == 2 else "")
            reads.append(r)
    for pid, t, bands in E13_BANDS:
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        if tuple(n for n, _, _ in bands) != tuple(n for n in POW4 if spec.vnc // n >= MIN_BLOCKS):
            raise c.StageBStop("rows_e", "E13 band sizes at " + pid)
        sc = scoring_at(fz, "E13", [triple(spec, t)], E13_X08 if _e13_rr(pid, t) else None)
        for n, pred, ztext in bands:
            rid = "band_%s_t%d_n%d" % (pid, t, n)
            at = at_text(pid, t, VNC, "n%d" % n)
            frz = "rho=%s,1+(n-1)rho=%s" % (E13_RHO[pid][t - 1], ztext or "none")
            slip = series.KNOWN_SLIPS.get("E13 Z_%d at frozen rho %s" % (n, E13_RHO[pid][t - 1]))
            if slip:
                frz += ",last-digit_slip:" + slip
            reads.append(guarded("E13", rid, at, "band", sc, zband_read, "E13", rid, at, sc, pt, c.step_of_t(t), n,
                                 pred, frz))
    if sum(1 for r in reads if r.scored and r.rid.startswith("band_")) != 11:
        raise c.StageBStop("rows_e", "E13 scored band reads")
    fals = [r.rid for r in reads if r.scored and r.outcome == c.MISS]
    return reads, fals


# ---------------------------------------------------------------------------------------------------------------------
# E14 CROSSOVER_GROWS_AS_Y_TO_MINUS_4


E14_T1 = ("t=1:_n*_hat(P14)/n*_hat(P08)_in_(4(1-4SE_rel),16(1+4SE_rel)],_closed_form_574.30/46.527=12.343"
          "_(Q07_linear-law_values)")
E14_T2 = "t=2:_closed_form_10.280,_read_and_report"
E14_HAT = "n*_hat=V/abs(Bbar)^2_u,_abs(Bbar)^2_u=(abs(Sum_B)^2-Sum_abs(B)^2)/(M(M-1))"
E14_FIRST = ("first_2^k_(k=2..10)_with_K2(n)<=2abs(Bbar)^2_u_read_and_report_(law:_2^6,_2^10_at_t=1;_2^5,_2^8_at_t=2)")
E14_LAW_FIRST = {("P08", 1): "2^6", ("P14", 1): "2^10", ("P08", 2): "2^5", ("P14", 2): "2^8"}
E14_POINT = "t=1_scored_(moved_from_t=2,_X08);_t=2_read_and_report"
E14_METHOD = "exact_block_sums;_jackknife_over_256_calls"


def first_crossing(pt, step):
    """The first n = 2^k, k = 2..10, with K2(n) = Sum s2/(n M) <= 2 |Bbar|^2_u (row E14), or None."""
    s = sums_of(pt, step, VNC, "all")
    b2 = bbar2_u(s)
    for k in range(2, 11):
        n = 1 << k
        bk = blk_of(pt, step, VNC, n, "all")
        if div(bk["s2"], n * s["m"]) <= 2 * b2:
            return n, b2
    return None, b2


def row_e14(inp, fz):
    need(fz, "E14", E14_T1, "574.30", "46.527", "12.343")
    need(fz, "E14", E14_T2, "10.280")
    need(fz, "E14", E14_HAT)
    need(fz, "E14", E14_FIRST, *E14_LAW_FIRST.values())
    need(fz, "E14", E14_POINT)
    need(fz, "E14", E14_METHOD)
    p08, p14 = inp.point("P08"), inp.point("P14")
    s08, s14 = c.DUMP_POINTS["P08"], c.DUMP_POINTS["P14"]
    reads, fals = [], []
    for t in (1, 2):
        sc = scoring_at(fz, "E14", [triple(s14, t), triple(s08, t)], None if t == 1 else E14_POINT)
        rid = "ratio_t%d" % t
        at = "P14/P08_t%d_VNC" % t
        frozen = "closed_form_" + ("574.30/46.527=12.343" if t == 1 else "10.280")
        r = guarded("E14", rid, at, "interval", sc, _e14_ratio, rid, at, sc, p14, p08, c.step_of_t(t), frozen)
        reads.append(r)
        if r.scored and r.outcome == c.MISS:
            fals.append(rid)
    for t in (1, 2):
        for pid, pt in (("P08", p08), ("P14", p14)):
            rid = "first_%s_t%d" % (pid, t)
            sc = c.report(fz, "STRIPES_PREDICT", "E14", E14_FIRST, "row_text")
            reads.append(guarded("E14", rid, at_text(pid, t, VNC), "report", sc, _e14_first, rid, pid, t, sc, pt))
    return reads, fals


def _e14_ratio(rid, at, sc, p14, p08, step, frozen):
    a, se2a = nstar_jackknife(calls_of(p14, step, VNC, "all"))
    b, se2b = nstar_jackknife(calls_of(p08, step, VNC, "all"))
    det = (("nstar_P14", "none" if a is None else fmt(a, 6)), ("nstar_P08", "none" if b is None else fmt(b, 6)))
    if a is None or b is None or a <= 0 or b <= 0:
        return c.Read("E14", rid, at, "interval", sc, c.NOT_RESOLVED, frozen=frozen,
                      detail=det + (("nstar", "not_estimable"),))
    r = div(a, b)
    se2_rel = div(se2a, a * a) + div(se2b, b * b)
    band = c.Band(Rad(4) - Rad.sqrt(se2_rel, 16), Rad(16) + Rad.sqrt(se2_rel, 64), lo_open=True)
    out = c.read3_interval(r, r, band)
    return c.Read("E14", rid, at, "interval", sc, out, value=r, lo=r, hi=r, band=band, frozen=frozen,
                  detail=det + (("SE_rel", up(Rad.sqrt(se2_rel))), ("calls", "%d/%d" % (
                      len(calls_of(p14, step, VNC, "all")), len(calls_of(p08, step, VNC, "all"))))))


def _e14_first(rid, pid, t, sc, pt):
    n, b2 = first_crossing(pt, c.step_of_t(t))
    return c.Read("E14", rid, at_text(pid, t, VNC), "report", sc, c.MET,
                  value="none_to_2^10" if n is None else "2^%d" % (n.bit_length() - 1),
                  frozen="law_" + E14_LAW_FIRST[(pid, t)], detail=(("bbar2_u_e80", fmt(b2, 6)),) + loss(pt))


# ---------------------------------------------------------------------------------------------------------------------
# E15 CONTROLS_FOLLOW_ONE_PLUS_MINUS_DELTA


E15_PI_TEXT = ("Pi_t=1/t=2:_P05_FLIP_0.105334/0.166661_>_VNC_0.077517/0.088773_>_LOCK_0.072019/0.063151;_P08_LOCK"
               "_0.140157/0.173339_>_VNC_0.096275/0.136403_>_FLIP_0.082538/0.099675;_each_MET_at_tol_Pi/10"
               "+3/sqrt(2^18)")
E15_PI = {("P05", "FLIP"): ("0.105334", "0.166661"), ("P05", VNC): ("0.077517", "0.088773"),
          ("P05", "LOCK"): ("0.072019", "0.063151"), ("P08", "LOCK"): ("0.140157", "0.173339"),
          ("P08", VNC): ("0.096275", "0.136403"), ("P08", "FLIP"): ("0.082538", "0.099675")}
E15_GAUSS_TEXT = "LOCK_on_its_lattice_(Gaussian_0.071939/0.063726,_0.140134/0.173228)"
E15_GAUSS = {"P05": ("0.071939", "0.063726"), "P08": ("0.140134", "0.173228")}
E15_CROSS_TEXT = ("against_VNC_frozen_values:_FLIP_MISS_at_P05_t=1,2_and_P08_t=2_(P08_t=1_read_and_report,_expected"
                  "_NOT_RESOLVED),_LOCK_MISS_at_P08_t=1,2_and_P05_t=2,_MET_at_P05_t=1")
E15_CROSS_RR = "(P08_t=1_read_and_report,_expected_NOT_RESOLVED)"
E15_CROSS = {("P05", "FLIP", 1): c.MISS, ("P05", "FLIP", 2): c.MISS, ("P08", "FLIP", 1): c.NOT_RESOLVED,
             ("P08", "FLIP", 2): c.MISS, ("P05", "LOCK", 1): c.MET, ("P05", "LOCK", 2): c.MISS,
             ("P08", "LOCK", 1): c.MISS, ("P08", "LOCK", 2): c.MISS}
E15_ORDER = {"P05": ("FLIP", VNC, "LOCK"), "P08": ("LOCK", VNC, "FLIP")}
E15_P04_TEXT = "P04_t=2_read_and_report:_FLIP/VNC=2.038,_LOCK/VNC=0.639_lattice_(0.709_Gaussian;_limits_3,_2/3)"
E15_P04 = {"FLIP": "2.038", "LOCK": "0.639_lattice,0.709_Gaussian"}
E15_X08 = "read-and-report_(X08):_the_value_and_cross_reads_at_P05_(every_record)_and_P08_t=2"
E15_SCORED = ("scored:_the_order_claims_among_variants_on_common_samples_at_P05_and_P08_(t=1,_2),_except_VNC>LOCK"
              "_at_P05_t=1_(a_7.6_percent_margin_on_an_exposed_VNC_value),_read_and_report,_and_the_value_and_cross"
              "_reads_at_P08_t=1")
E15_ORDER_RR = "except_VNC>LOCK_at_P05_t=1_(a_7.6_percent_margin_on_an_exposed_VNC_value),_read_and_report"
E15_FALS = "a_MISS,_a_scored_order_claim_not_as_stated,_or_a_scored_cross-read_(P08_t=1)_other_than_predicted"
E15_TOL_SQRT = 1 << 18


def e15_tol(p):
    """tol = Pi/10 + 3/sqrt(2^18), as frozen."""
    return pi_tol(p, E15_TOL_SQRT, fr(1, 10))


def cross_outcome(cross, pred):
    """A cross-read's READ3 outcome against the predicted one."""
    if cross == pred:
        return c.MET
    if pred == c.NOT_RESOLVED or cross != c.NOT_RESOLVED:
        return c.MISS
    return c.NOT_RESOLVED


def row_e15(inp, fz):
    need(fz, "E15", E15_PI_TEXT, *[x for v in E15_PI.values() for x in v])
    need(fz, "E15", E15_GAUSS_TEXT, *[x for v in E15_GAUSS.values() for x in v])
    need(fz, "E15", E15_CROSS_TEXT)
    need(fz, "E15", E15_P04_TEXT, "2.038", "0.639", "0.709")
    need(fz, "E15", E15_X08)
    need(fz, "E15", E15_SCORED)
    need(fz, "E15", E15_FALS)
    fz.require("STRIPES_RULE", "EXPOSED", "comparisons_of_two_variants_on_the_same_samples_with_no_frozen_value_(E06,"
               "_E15_order,_E16)")
    reads, fals = [], []
    for pid in ("P05", "P08"):
        spec = c.DUMP_POINTS[pid]
        pt = inp.point(pid)
        for t in (1, 2):
            step = c.step_of_t(t)
            rr = pid == "P05" or t == 2
            sc = scoring_at(fz, "E15", [triple(spec, t)], E15_X08 if rr else None)
            for v in (VNC, "FLIP", "LOCK"):
                rid = "pi_%s_%s_t%d" % (pid, v, t)
                frz = E15_PI[(pid, v)][t - 1]
                if v == "LOCK":
                    frz += ",Gaussian_" + E15_GAUSS[pid][t - 1]
                reads.append(guarded("E15", rid, at_text(pid, t, v), "sampled", sc, _e15_value, rid, pid, t, v, sc,
                                     pt, step, frz))
            for v in ("FLIP", "LOCK"):
                rid = "cross_%s_%s_t%d" % (pid, v, t)
                csc = sc
                if (pid, v, t) == ("P08", "FLIP", 1):
                    csc = c.report(fz, "STRIPES_PREDICT", "E15", E15_CROSS_RR, "RP13")
                pred = E15_CROSS[(pid, v, t)]
                r = guarded("E15", rid, at_text(pid, t, v), "cross", csc, _e15_cross, rid, pid, t, v, csc, pt, step,
                            pred)
                reads.append(r)
                # "a scored cross-read other than predicted": certified other (outcome MISS), as READ3 limits a
                # falsifier; a cross-read left NOT_RESOLVED makes the row NOT_RESOLVED, not NOT_MET.
                if r.scored and r.outcome == c.MISS:
                    fals.append(rid)
            chain = E15_ORDER[pid]
            for hi_v, lo_v in ((chain[0], chain[1]), (chain[1], chain[2])):
                rid = "order_%s_%s>%s_t%d" % (pid, hi_v, lo_v, t)
                if (pid, hi_v, lo_v, t) == ("P05", VNC, "LOCK", 1):
                    osc = c.report(fz, "STRIPES_PREDICT", "E15", E15_ORDER_RR, "row_text")
                else:
                    osc = c.scored("comparison_on_common_samples")
                r = guarded("E15", rid, at_text(pid, t, hi_v + ">" + lo_v), "order", osc, _e15_order, rid, pid, t,
                            hi_v, lo_v, osc, pt, step)
                reads.append(r)
                if r.scored and r.outcome == c.MISS:
                    fals.append(rid)
    pt = inp.point("P04")
    for v in ("FLIP", "LOCK"):
        rid = "ratio_P04_%s/VNC_t2" % v
        sc = c.report(fz, "STRIPES_PREDICT", "E15", E15_P04_TEXT, "row_text")
        reads.append(guarded("E15", rid, at_text("P04", 2, v + "/VNC"), "report", sc, _e15_p04, rid, v, sc, pt))
    for r in reads:
        if r.scored and r.outcome == c.MISS and r.rid not in fals:
            fals.append(r.rid)
    return reads, fals


def _e15_value(rid, pid, t, v, sc, pt, step, frz):
    pi = PiHat(vr_of(pt, step, v, "ctrl"))
    p_text = E15_PI[(pid, v)][t - 1]
    return pi_read("E15", rid, at_text(pid, t, v), sc, pi, p_text, e15_tol(dec(p_text)), frozen=frz,
                   extra=loss(pt, "ctrl"))


def _e15_cross(rid, pid, t, v, sc, pt, step, pred):
    pi = PiHat(vr_of(pt, step, v, "ctrl"))
    p_text = E15_PI[(pid, VNC)][t - 1]
    cross = c.read3_sampled(pi.x, dec(p_text), e15_tol(dec(p_text)), pi.e())
    e = pi.e()
    return c.Read("E15", rid, at_text(pid, t, v), "cross", sc, cross_outcome(cross, pred), value=pi.x, lo=pi.x - e,
                  hi=pi.x + e, band="against_VNC_%s,predicted_%s" % (p_text, pred), frozen="VNC_" + p_text,
                  detail=(("cross", cross), ("predicted", pred)) + loss(pt, "ctrl"))


def _e15_order(rid, pid, t, hi_v, lo_v, sc, pt, step):
    v = lo_v if hi_v == VNC else hi_v
    sign = 1 if hi_v != VNC else -1
    lo, hi, se2, a, r, cm = paired(pt, step, v)
    e = c.se(se2, 3)
    ilo, ihi = Rad.of(lo) - e, Rad.of(hi) + e
    band = c.Band(0, None, lo_open=True) if sign > 0 else c.Band(None, 0, hi_open=True)
    out = c.read3_interval(ilo, ihi, band)
    return c.Read("E15", rid, at_text(pid, t, hi_v + ">" + lo_v), "order", sc, out, value=mid(lo, hi), lo=ilo,
                  hi=ihi, band=band, detail=(("diff", "Pi_%s-Pi_VNC" % v), ("Pi_%s" % v, fmt(a.x, 6)),
                                             ("Pi_VNC", fmt(r.x, 6)), ("common", cm["common"]),
                                             ("3SE_pair", up(e))) + loss(pt, "ctrl"))


def _e15_p04(rid, v, sc, pt):
    step = c.step_of_t(2)
    a = PiHat(vr_of(pt, step, v, "ctrl"))
    b = PiHat(vr_of(pt, step, VNC, "ctrl"))
    parts = ratio_parts(a, b)
    if parts is None:
        return c.Read("E15", rid, at_text("P04", 2, v + "/VNC"), "report", sc, c.MET, value="unbounded",
                      frozen=E15_P04[v])
    r, se2, half = parts
    e = c.se(se2, 3) + half
    return c.Read("E15", rid, at_text("P04", 2, v + "/VNC"), "report", sc, c.MET, value=r, lo=r - e, hi=r + e,
                  frozen=E15_P04[v] + (",limit_3" if v == "FLIP" else ",limit_2/3"),
                  detail=(("se", "delta_method_independent"),) + loss(pt, "ctrl"))


# ---------------------------------------------------------------------------------------------------------------------
# E16 V1_V0_RN_PIN_AS_VNC


E16_PRED = "abs(Pi_V-Pi_VNC)+3SE_pair<=Pi_VNC/20_on_all_24_reads"
E16_METHOD = "discordant_counts_D+,_D-:_difference_(D+_-_D-)/(2M),_SE_pair=sqrt(D+_+_D-)/(2M)"
E16_SCORED = "a_comparison_on_common_samples_with_no_frozen_value,_scored_at_every_point_(rule_EXPOSED)"


def row_e16(inp, fz):
    need(fz, "E16", E16_PRED)
    fz.require("STRIPES_PREDICT", "E16", E16_METHOD)
    need(fz, "E16", E16_SCORED)
    reads = []
    for pid in ("P04", "P05", "P06", "P08"):
        pt = inp.point(pid)
        for t in (1, 2):
            for v in ("V1", "V0", "RN"):
                rid = "pair_%s_%s_t%d" % (pid, v, t)
                sc = c.scored("comparison_on_common_samples")
                reads.append(guarded("E16", rid, at_text(pid, t, v), "sampled", sc, _e16, rid, pid, t, v, sc, pt))
    if len(reads) != 24:
        raise c.StageBStop("rows_e", "E16 24 reads")
    return reads, [r.rid for r in reads if r.outcome == c.MISS]


def e16_outcome(out_recipe, out_diff):
    """E16 under its two frozen texts, both with SE_pair = sqrt(D_max)/(2M) (e16_se_pair_e): the prediction names
    abs(Pi_V-Pi_VNC) = abs(D+ - D-)/M, the method's recipe (D+ - D-)/(2M) is half of it. MET exactly when the
    prediction passes (then the recipe passes too), MISS exactly when the recipe fails (then the prediction fails
    too), else NOT_RESOLVED."""
    if out_diff == c.MET:
        if out_recipe != c.MET:
            raise c.StageBStop("e16_rule", "the difference passes and its half does not")
        return c.MET
    if out_recipe == c.MISS:
        if out_diff != c.MISS:
            raise c.StageBStop("e16_rule", "the half of the difference fails and the difference does not")
        return c.MISS
    return c.NOT_RESOLVED


def e16_se_pair_e(cm, m):
    """3 SE_pair as an upper bound (the reader's conservative reading, note reading_E16): the frozen SE_pair =
    sqrt(D+ + D-)/(2M) with D+ + D- replaced by possibly_discordant, which counts every ambiguous cell and every atom
    as possibly discordant. At every placement of those samples the frozen SE_pair is at most this one."""
    return c.se(fr(possibly_discordant(cm, m), 4 * m * m), 3)


def _e16(rid, pid, t, v, sc, pt):
    lo, hi, _, a, r, cm = paired(pt, c.step_of_t(t), v)
    xlo, xhi = div(lo, 2), div(hi, 2)
    e = e16_se_pair_e(cm, a.M)
    plo, phi = r.bracket()
    out_recipe = sampled_bracket(xlo, xhi, 0, div(plo, 20), div(phi, 20), e)
    out_diff = sampled_bracket(lo, hi, 0, div(plo, 20), div(phi, 20), e)
    return c.Read("E16", rid, at_text(pid, t, v), "sampled", sc, e16_outcome(out_recipe, out_diff),
                  value=mid(xlo, xhi), lo=Rad.of(xlo) - e, hi=Rad.of(xhi) + e,
                  band="abs(x)+3SE_pair<=Pi_VNC/20,Pi_VNC=" + fmt(r.x, 6),
                  detail=(("x", "(D+-D-)/(2M)"), ("recipe", out_recipe), ("Pi_hat_diff", "%s..%s" % (
                      fmt(lo, 4, "down"), fmt(hi, 4, "up"))), ("diff", out_diff), ("D+", cm["br"][1]),
                          ("D-", cm["br"][3]), ("D_max", possibly_discordant(cm, a.M)), ("common", cm["common"]),
                          ("M", a.M), ("3SE_pair", up(e)))
                  + loss(pt, "ctrl"))


# ---------------------------------------------------------------------------------------------------------------------
# E17 STRONG_PINNING_OUTLASTS_SATURATION (wholly read-and-report)


E17_PI1 = "t=1_Pi=0.233911_within_15_percent+3/sqrt(M)_MET"
E17_EVERY = "every_record_and_variant:_H8_sign_test_flags_with_Pi_hat>0_and_B16_flags"
E17_Z64 = "VNC_Z_64_band_NOT_MET_at_all_records_(Z_64=8.10_at_t=1)"
E17_PI24 = "Pi_at_t=2-4_read_and_report"
E17_STOP = "stopped_records_NOT_MEASURED"
E17_ALL = ("every_read_read-and-report_(X08:_P10_is_(delta,s)=(1/2,1),_exposed_at_every_t),_so_the_row_carries_no"
           "_verdict")


def row_e17(inp, fz):
    for ph in (E17_PI1, E17_EVERY, E17_Z64, E17_PI24, E17_STOP, E17_ALL):
        need(fz, "E17", ph)
    spec = c.DUMP_POINTS["P10"]
    pt = inp.point("P10")
    for t in (1, 2, 3, 4):
        if not c.exposed(*triple(spec, t)):
            raise c.StageBStop("exposed", "E17: P10 not exposed at t=%d" % t)
    sc = c.report(fz, "STRIPES_PREDICT", "E17", E17_ALL, "X08")
    reads = [guarded("E17", "pi_t1", at_text("P10", 1, VNC), "sampled", sc, _e17_pi1, sc, pt)]
    for t in (1, 2, 3, 4):
        step = c.step_of_t(t)
        for v in c.VARIANTS:
            scope = "all" if v == VNC else "ctrl"
            reads.append(guarded("E17", "sign_%s_t%d" % (v, t), at_text("P10", t, v), "H8", sc, _e17_sign, v, t, sc,
                                 pt, step, scope))
            reads.append(guarded("E17", "b16_%s_t%d" % (v, t), at_text("P10", t, v), "B16", sc, _e17_b16, v, t, sc,
                                 pt, step, scope))
        frz = "Z_64=8.10" if t == 1 else "none"
        rid = "z64_t%d" % t
        reads.append(guarded("E17", rid, at_text("P10", t, VNC, "n64"), "band", sc, zband_read, "E17", rid,
                             at_text("P10", t, VNC, "n64"), sc, pt, step, 64, c.NOT_MET, frz))
    for t in (2, 3, 4):
        reads.append(guarded("E17", "pi_t%d" % t, at_text("P10", t, VNC), "report", sc, _e17_pi, t, sc, pt))
    return reads, []


def _e17_pi1(sc, pt):
    pi = PiHat(vr_of(pt, c.step_of_t(1), VNC, "all"))
    p = dec("0.233911")
    return pi_read("E17", "pi_t1", at_text("P10", 1, VNC), sc, pi, "0.233911", pi_tol(p, pi.M, fr(15, 100)),
                   extra=loss(pt))


def _e17_sign(v, t, sc, pt, step, scope):
    vr = vr_of(pt, step, v, scope)
    s = c.h8(vr["br_pos"], vr["br_neg"], vr["br_amb"])
    if s == c.FLAG:
        out = c.MET if vr["br_pos"] > vr["br_neg"] else c.MISS
    else:
        out = c.MISS if s == c.UNFLAGGED else c.NOT_RESOLVED
    return c.Read("E17", "sign_%s_t%d" % (v, t), at_text("P10", t, v), "H8", sc, out, value=s,
                  band="H8_sign_br_flag_with_Pi_hat>0",
                  detail=(("br_pos", vr["br_pos"]), ("br_neg", vr["br_neg"]), ("br_amb", vr["br_amb"])) +
                  loss(pt, scope))


def _e17_b16(v, t, sc, pt, step, scope):
    return b16_read("E17", "b16_%s_t%d" % (v, t), at_text("P10", t, v), sc, vr_of(pt, step, v, scope), NOT_UNIFORM,
                    extra=loss(pt, scope))


def _e17_pi(t, sc, pt):
    pi = PiHat(vr_of(pt, c.step_of_t(t), VNC, "all"))
    return pi_report("E17", "pi_t%d" % t, at_text("P10", t, VNC), sc, pi, extra=loss(pt))


# ---------------------------------------------------------------------------------------------------------------------
# E18 WEYL_SECOND_MOMENT_BRIDGE


E18_PRED = "E_VNC[abs(B_W)^2]/Q_W-1_within_+-1/20_at_all_five"
E18_LAW_TEXT = "law_values_327.18,_21.522,_9.7361,_660.50,_403.89_beside"
E18_X08 = "read-and-report_(X08):_(1/54,2),_(1/108,2)_and_(0,2)"
E18_SCORED = "scored:_(1/27,1),_(1/54,1)"
E18_METHOD = "N^2(S_br2+S_bi2)/(M_2^80)_from_P07_(y=0)_and_R1-R3;_Q_W_from_QR2,_QR3"
E18_FALS = "abs(ratio-1)-(4SE_rel+read_error)>1/20_at_a_scored_point"
E18_POINTS = (("0", "2", "P07", "327.18"), ("1/27", "1", "R1", "21.522"), ("1/54", "1", "R2", "9.7361"),
              ("1/54", "2", "R2", "660.50"), ("1/108", "2", "R3", "403.89"))


def e18_moment(inp, src, step):
    """E[|B_W|^2] / N^2 = E[|br + i bi|^2]/2^80 at a point: (mean, SE^2) by batch means over the 4096-sample calls of
    P07 or the 64 batches of a run (rule SE)."""
    if src.startswith("P"):
        pt = inp.point(src)
        rs = calls_of(pt, step, VNC, "all")
        m, se2 = c.batch_means([r["br2"] + r["bi2"] for r in rs], [r["m"] for r in rs])
        sc = fr(1, 1 << 80)
        return m * sc, se2 * sc * sc, loss(pt)
    run = inp.run(src)
    run_step_ok(run, step)
    if len(run.batches) < 2:
        raise Lost("no_batches")
    m, se2 = run.moment2(step)
    return m, se2, run_loss(run)


def row_e18(inp, fz):
    need(fz, "E18", E18_PRED)
    need(fz, "E18", E18_LAW_TEXT, *[x[3] for x in E18_POINTS])
    need(fz, "E18", E18_X08)
    need(fz, "E18", E18_SCORED)
    fz.require("STRIPES_PREDICT", "E18", E18_METHOD)
    need(fz, "E18", E18_FALS)
    reads = []
    for y, t, src, law_text in E18_POINTS:
        tt = parse_rat(t)
        s = parse_rat(y) * 27
        rr = (y, t) in (("1/54", "2"), ("1/108", "2"), ("0", "2"))
        sc = c.value_scoring(fz, "E18", (M14, abs(s), tt), E18_X08 if rr else None)
        rid = "QW_y%s_t%s" % (y, t)
        at = "N729_y%s_t%s_%s" % (y, t, src)
        reads.append(guarded("E18", rid, at, "sampled", sc, _e18, rid, at, sc, inp, y, t, src, law_text))
    if len(reads) != 5:
        raise c.StageBStop("rows_e", "E18 five reads")
    return reads, [r.rid for r in reads if r.scored and r.outcome == c.MISS]


def _e18(rid, at, sc, inp, y, t, src, law_text):
    tt = parse_rat(t)
    m, se2, lost = e18_moment(inp, src, c.step_of_t(tt))
    q = None if inp.qe is None else qe_mod.get(inp.qe, "point", 729, "-1/4", y, t)
    if q is None:
        raise Lost("missing_QE_row" if inp.qe is None else qe_mod.lost_why(inp.qe, [("point", 729, "-1/4", y, t)]))
    if m < 0:
        raise c.StageBStop("aggregate_identity", "E18: a negative sum of squares")
    if m == 0 and q.QW_iv().lo > 0:
        # every sample has B_W = 0: the ratio is 0, abs(0 - 1) = 1 > 1/20 with no error
        return c.Read("E18", rid, at, "sampled", sc, c.MISS, value=0, lo=0, hi=0,
                      band="abs(ratio-1)+4SE_rel+read_error<=1/20", frozen="EB2_lin=" + law_text,
                      detail=(("moment", "zero"),) + lost)
    if m == 0:
        return c.Read("E18", rid, at, "sampled", sc, c.NOT_RESOLVED,
                      detail=(("moment", "zero"), ("Q_W", "not_positive")) + lost)
    e = m * 729 * 729
    qw = q.QW_iv()
    x = qw.inv() * e
    e4 = Rad.sqrt(div(se2, m * m), 4)
    out = sampled_bracket(x.lo, x.hi, 1, fr(1, 20), fr(1, 20), e4)
    law = series.Law(M14, 729 * parse_rat(y) * parse_rat(y), tt).EB2
    return c.Read("E18", rid, at, "sampled", sc, out, value=x.mid(), lo=Rad.of(x.lo) - e4, hi=Rad.of(x.hi) + e4,
                  band="abs(ratio-1)+4SE_rel+read_error<=1/20", frozen="EB2_lin=" + law_text,
                  detail=(("E_VNC", fmt(e, 8)), ("Q_W", "%s..%s" % (fmt(qw.lo, 8, "down"), fmt(qw.hi, 8, "up"))),
                          ("read_error", up(x.width() * fr(1, 2))), ("4SE_rel", up(e4)),
                          ("EB2_lin", "%s..%s" % (fmt(law.lo, 6, "down"), fmt(law.hi, 6, "up")))) + lost)


# ---------------------------------------------------------------------------------------------------------------------
# E19 CROSSOVER_COLLAPSES_ON_S


E19_PRED = ("n*_VNC(81)/n*_VNC(729)-1_within_+-1/4_at_both_t;_n*_VNC/n*_lin-1_within_+-1/5_at_N=729,_+-1/4_at_N=81;"
            "_E[br]>0_everywhere")
E19_LAW_TEXT = "share_n*_lin=199.67_(t=1/2),_46.527_(t=1)"
E19_POINT = "R4_and_R2_at_t=1/2,_1;_R3_at_t=1_against_574.30"
E19_METHOD = "run_sums;_n*=(S2/M)/abs(Bbar)^2_u-1;_batch_jackknife;_4_SE_intervals"
E19_FALS = "an_interval_outside_its_band,_or_E[br]<=0"
E19_LIN = (("R2", "1/2", "199.67", fr(1, 5)), ("R2", "1", "46.527", fr(1, 5)), ("R3", "1", "574.30", fr(1, 5)),
           ("R4", "1/2", "199.67", fr(1, 4)), ("R4", "1", "46.527", fr(1, 4)))
E19_EBR = (("R4", "1/2"), ("R4", "1"), ("R2", "1/2"), ("R2", "1"), ("R3", "1"))


def run_nstar(run, t):
    step = c.step_of_t(parse_rat(t))
    run_step_ok(run, step)
    if len(run.batches) < 2:
        raise Lost("no_batches")
    return run.nstar(step)


def row_e19(inp, fz):
    need(fz, "E19", E19_PRED)
    need(fz, "E19", E19_LAW_TEXT, "199.67", "46.527")
    need(fz, "E19", E19_POINT, "574.30")
    need(fz, "E19", E19_METHOD)
    need(fz, "E19", E19_FALS)
    reads = []
    for t in ("1/2", "1"):
        tt = parse_rat(t)
        sc = scoring_at(fz, "E19", [triple(c.RUN_POINTS["R4"], tt), triple(c.RUN_POINTS["R2"], tt)], None)
        rid = "collapse_t%s" % t
        reads.append(guarded("E19", rid, "R4/R2_t" + t, "interval", sc, _e19_collapse, rid, sc, inp, t))
    for rid_pt, t, text, half in E19_LIN:
        spec = c.RUN_POINTS[rid_pt]
        sc = scoring_at(fz, "E19", [triple(spec, parse_rat(t))], None)
        rid = "lin_%s_t%s" % (rid_pt, t)
        reads.append(guarded("E19", rid, "%s_t%s" % (rid_pt, t), "interval", sc, _e19_lin, rid, sc, inp, rid_pt, t,
                             text, half))
    for rid_pt, t in E19_EBR:
        spec = c.RUN_POINTS[rid_pt]
        sc = scoring_at(fz, "E19", [triple(spec, parse_rat(t))], None)
        rid = "Ebr_%s_t%s" % (rid_pt, t)
        reads.append(guarded("E19", rid, "%s_t%s" % (rid_pt, t), "interval", sc, _e19_ebr, rid, sc, inp, rid_pt, t))
    return reads, [r.rid for r in reads if r.scored and r.outcome == c.MISS]


def _e19_collapse(rid, sc, inp, t):
    r4, r2 = inp.run("R4"), inp.run("R2")
    a, se2a = run_nstar(r4, t)
    b, se2b = run_nstar(r2, t)
    band = c.Band(fr(-1, 4), fr(1, 4))
    det = (("nstar_R4", "none" if a is None else fmt(a, 6)), ("nstar_R2", "none" if b is None else fmt(b, 6)))
    if a is None or b is None or b <= 0:
        return c.Read("E19", rid, "R4/R2_t" + t, "interval", sc, c.NOT_RESOLVED, band=band,
                      detail=det + (("nstar", "not_estimable"),))
    r, se2 = c.ratio_indep(a, se2a, b, se2b)
    e = c.se(se2, 4)
    lo, hi = Rad.of(r - 1) - e, Rad.of(r - 1) + e
    return c.Read("E19", rid, "R4/R2_t" + t, "interval", sc, c.read3_interval(lo, hi, band), value=r - 1, lo=lo,
                  hi=hi, band=band, detail=det + (("4SE", up(e)),) + run_loss(r4) + run_loss(r2))


def _e19_lin(rid, sc, inp, rid_pt, t, text, half):
    run = inp.run(rid_pt)
    spec = c.RUN_POINTS[rid_pt]
    a, se2a = run_nstar(run, t)
    band = c.Band(-half, half)
    if a is None:
        return c.Read("E19", rid, "%s_t%s" % (rid_pt, t), "interval", sc, c.NOT_RESOLVED, band=band,
                      frozen="n*_lin=" + text, detail=(("nstar", "not_estimable"),))
    y = parse_rat(spec.y)
    law = series.Law(fr(parse_rat(spec.delta)), spec.N * y * y, parse_rat(t)).nstar()
    if law is None or not law.pos():
        # the bracket below needs n*_lin > 0 at both ends (a lower end at or below 0 gives no bound or a wrong one)
        raise c.StageBStop("e19_law", "%s t=%s: n*_lin is %s, not above 0" % (rid_pt, t, "infinite" if law is None
                                                                                 else "%r" % law))
    e = c.se(se2a, 4)
    # (n* -+ 4SE)/n*_lin over n*_lin in [law.lo, law.hi], law.lo > 0: each end's extreme is at one end of the
    # bracket, which one by the sign of n* -+ 4SE (quantum review 2, M2)
    a_lo, a_hi = Rad.of(a) - e, Rad.of(a) + e
    lo = min(a_lo.scale(div(1, law.lo)), a_lo.scale(div(1, law.hi))) - 1
    hi = max(a_hi.scale(div(1, law.lo)), a_hi.scale(div(1, law.hi))) - 1
    return c.Read("E19", rid, "%s_t%s" % (rid_pt, t), "interval", sc, c.read3_interval(lo, hi, band),
                  value=div(a, law.mid()) - 1, lo=lo, hi=hi, band=band, frozen="n*_lin=" + text,
                  detail=(("nstar", fmt(a, 6)), ("4SE", up(e)),
                          ("nstar_lin", "%s..%s" % (fmt(law.lo, 7, "down"), fmt(law.hi, 7, "up")))) + run_loss(run))


def _e19_ebr(rid, sc, inp, rid_pt, t):
    run = inp.run(rid_pt)
    step = c.step_of_t(parse_rat(t))
    run_step_ok(run, step)
    if len(run.batches) < 2:
        raise Lost("no_batches")
    m, se2 = run.mean_br(step)
    pooled = run.pooled(step)
    rb = fr(pooled["rb_br"], pooled["n"] * (1 << 40))
    e = c.se(se2, 4) + rb
    lo, hi = Rad.of(m) - e, Rad.of(m) + e
    band = c.Band(0, None, lo_open=True)
    return c.Read("E19", rid, "%s_t%s" % (rid_pt, t), "interval", sc, c.read3_interval(lo, hi, band), value=m, lo=lo,
                  hi=hi, band=band, detail=(("units", "B_W/N"), ("rounding_bound", up(rb)), ("4SE", up(c.se(se2, 4))))
                  + run_loss(run))


# ---------------------------------------------------------------------------------------------------------------------
# The rows.


ROWS = (("E09", row_e09), ("E10", row_e10), ("E11", row_e11), ("E12", row_e12), ("E13", row_e13), ("E14", row_e14),
        ("E15", row_e15), ("E16", row_e16), ("E17", row_e17), ("E18", row_e18), ("E19", row_e19))


def read_e_mom(inp, fz=None, rows=None):
    """Verdicts of E09-E19 (or of the rows named) from the pooled aggregates, run sums and QE reads in inp."""
    fz = fz or frozen_mod.load()
    c.check_tables(fz)
    c.check_exposure_text(fz)
    out = []
    for rid, fn in ROWS:
        if rows is not None and rid not in rows:
            continue
        p = fz.predict(rid)
        reads, fals = fn(inp, fz)
        out.append(c.Verdict(rid, p["name"], p["tag"], reads, falsifier_reads=tuple(fals),
                             falsifier_text=p["falsifier"]))
    return out
