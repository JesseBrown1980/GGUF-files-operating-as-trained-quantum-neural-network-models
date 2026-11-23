"""Rows E01-E08 of the frozen prediction: Klein and exchange symmetry (H8), zero means (SIGNFLIP), evenness in y and
the two-insertion ratios (E04), the NL control (E05), MODE0 against VNC (E06), the LOCK lattice law (E07) and orbit
uniformity (E08). They read the pooled stage A aggregates, the P08 and P13 side files and the R1-R3 run sums."""

import os

from . import common as c
from . import frozen as frozen_mod
from . import runs as runs_mod
from . import series
from .common import (
    FLAG,
    MET,
    MISS,
    NOT_MEASURED,
    NOT_RESOLVED,
    UNFLAGGED,
    Band,
    Read,
    Scoring,
    StageBStop,
    Verdict,
)
from .exact import Rad, canon_int, dec, div, fmt, fr, parse_rat, rat_text
from .hbp import fields_dict, parse_row, sha256_hex

ALL7 = c.VARIANTS
LATTICE6 = ("VNC", "V1", "V0", "RN", "FLIP", "MODE0")
Y0_POINTS = ("P01", "P07", "P09")
E02_POINTS = ("P02", "P03", "P04", "P05", "P06", "P08", "P10", "P11", "P12", "P13", "P14")
NL_POINTS = ("P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "P13")
SYM_POINTS = NL_POINTS + ("P14",)
SYM_RUNS = ("R1", "R2", "R3")
H8_KINDS = {"pi": 8, "mir": 8, "br": 1, "bi": 1}


# ---------------------------------------------------------------------------------------------------------------------
# Small helpers.


def t_text(step):
    return rat_text(c.t_of_step(step))


def _at(pid, step=None, variant=None, extra=None):
    s = pid
    if step is not None:
        s += "_t" + t_text(step)
    if variant is not None:
        s += "_" + variant
    if extra is not None:
        s += "_" + extra
    return s


def _calls_text(calls):
    calls = sorted(calls)
    if len(calls) <= 6:
        return ":".join(str(i) for i in calls)
    return "%d..%d(%d)" % (calls[0], calls[-1], len(calls))


def loss_detail(pt, scope="all"):
    """The calls lost to an engine stop (rule STOP) in the scope of a read; empty when none."""
    lost = [i for i, _ in pt.lost if scope == "all" or i < pt.spec.all]
    if not lost:
        return ()
    return (("lost_calls", _calls_text(lost)), ("lost_indices", c.COUNT * len(lost)))


def scope_of(variant):
    return "all" if variant == "VNC" else "ctrl"


def missing_reason(pt, step, variant="VNC", scope="all"):
    """None when the read has data, else why it is NOT_MEASURED."""
    if step is not None and not pt.measured(step):
        return "record_not_reached"
    if pt.M(scope, variant) == 0:
        return "no_call_read"
    return None


def nm_read(row, rid, at, kind, scoring, why, pt=None, scope="all", band="", frozen="none"):
    det = (("lost", why),) + (loss_detail(pt, scope) if pt is not None else ())
    return Read(row, rid, at, kind, scoring, NOT_MEASURED, band=band, frozen=frozen, detail=det)


def combine(outcomes):
    """Certified test outcomes of one read: MISS if one flags, MET if all are unflagged, else NOT_RESOLVED."""
    if FLAG in outcomes:
        return MISS
    if all(o == UNFLAGGED for o in outcomes):
        return MET
    return NOT_RESOLVED


def scoring_triples(fz, rid, triples, phrase):
    """A read built from several (delta, |s|, t): read-and-report iff one triple is exposed (rule EXPOSED); the frozen
    phrase naming it must be given exactly then."""
    ex = any(c.exposed_s0(d, t) if fr(s) == 0 else c.exposed(d, s, t) for d, s, t in triples)
    if ex != (phrase is not None):
        raise StageBStop("exposed", "%s %s: rule and row text disagree" % (rid, triples))
    if phrase is None:
        return c.scored("unexposed")
    fz.require("STRIPES_PREDICT", rid, phrase)
    return Scoring(False, "X08")


def check_records(pt_spec, ts, rid):
    """The frozen record list of a row at a point (t values) equals the point table's steps."""
    got = tuple(t_text(s) for s in pt_spec.steps)
    if got != tuple(ts):
        raise StageBStop("rows_e_sym", "%s %s: records %s, frozen %s" % (rid, pt_spec.id, got, ts))


def _require(fz, rid, phrases):
    for p in phrases:
        fz.require("STRIPES_PREDICT", rid, p)


def _count(rid, what, got, want):
    if got != want:
        raise StageBStop("rows_e_sym", "%s %s: %d, frozen %d" % (rid, what, got, want))


# ---------------------------------------------------------------------------------------------------------------------
# Rule H8 on a pooled AGG_VR.


def h8_tests(vr, kinds):
    """[(name, Oa, Ob, A, outcome)]: 'pi' the pairs (k, k+8), 'mir' the pairs (k, 15-k), both with A = amb; 'br' and
    'bi' the certified sign counts with A = br_amb or bi_amb."""
    out = []
    for name, a, b in c.h8_pairs(vr["sec"]):
        if (name.startswith("pi") and "pi" in kinds) or (name.startswith("mir") and "mir" in kinds):
            out.append((name, a, b, vr["amb"], c.h8(a, b, vr["amb"])))
    for comp in ("br", "bi"):
        if comp in kinds:
            p, n, a = vr[comp + "_pos"], vr[comp + "_neg"], vr[comp + "_amb"]
            out.append(("sign_" + comp, p, n, a, c.h8(p, n, a)))
    return out


def h8_read(row, pt, step, variant, kinds, scope=None):
    scope = scope or scope_of(variant)
    pid = pt.spec.id
    rid = "h8_" + _at(pid, step, variant)
    at = _at(pid, step, variant, "M%d" % pt.M(scope, variant))
    sc = c.scored("symmetry")
    band = "no_flag_in_%d_H8_tests" % sum(H8_KINDS[k] for k in kinds)
    why = missing_reason(pt, step, variant, scope)
    if why:
        return nm_read(row, rid, at, "H8", sc, why, pt, scope, band)
    tests = h8_tests(pt.vr(step, variant, scope), kinds)
    outs = [t[4] for t in tests]
    flagged = [t[0] for t in tests if t[4] == FLAG]
    unres = [t[0] for t in tests if t[4] == c.UNRESOLVED]
    det = (("tests", len(tests)), ("flag", len(flagged)), ("unresolved", len(unres)),
           ("flagged", "+".join(flagged) or "none"), ("unresolved_tests", "+".join(unres) or "none"))
    return Read(row, rid, at, "H8", sc, combine(outs), value=len(flagged), band=band,
                detail=det + loss_detail(pt, scope))


# ---------------------------------------------------------------------------------------------------------------------
# Rule SIGNFLIP on pooled AGG_SUM rows.


def signflip_test(sums, comp, with_rb):
    """(outcome, S, Q, RB, RQ) for b_i = br or bi over every sample of the set; RB = Sum b_br (or b_bi) when the
    symmetry is exact only in the exact-reference law, 0 where it is bit-exact."""
    s, q = sums[comp], sums[comp + "2"]
    rb, rq = (sums["b" + comp], sums["b" + comp + "2"]) if with_rb else (0, 0)
    return c.signflip(s, q, rb, rq), s, q, rb, rq


def signflip_read(row, rid, at, scoring, out, s, q, rb, rq, extra=()):
    thr = Rad.sqrt(q, 5) + Rad.sqrt(rq, 5)
    det = (("S", s), ("Q", q), ("RB", rb), ("RQ", rq), ("threshold", thr.text(8))) + tuple(extra)
    return Read(row, rid, at, "SIGNFLIP", scoring, MISS if out == FLAG else MET, value=abs(s) - rb,
                band="flag_if_abs(S)-RB>5(sqrt(Q)+sqrt(RQ))", detail=det)


def signflip_point_read(row, pt, step, variant, comp, with_rb, why_text):
    scope = scope_of(variant)
    pid = pt.spec.id
    rid = "sf_%s_%s" % (comp, _at(pid, step, variant))
    at = _at(pid, step, variant, comp)
    sc = c.scored(why_text)
    why = missing_reason(pt, step, variant, scope)
    if why:
        return nm_read(row, rid, at, "SIGNFLIP", sc, why, pt, scope)
    out, s, q, rb, rq = signflip_test(pt.sums(step, variant, "all", scope), comp, with_rb)
    extra = (("rb", "b_" + comp if with_rb else "0"), ("M", pt.M(scope, variant))) + loss_detail(pt, scope)
    return signflip_read(row, rid, at, sc, out, s, q, rb, rq, extra)


# ---------------------------------------------------------------------------------------------------------------------
# Rule B16 on a pooled AGG_VR.


def b16_test(vr):
    return c.b16(vr["sec"], vr["amb"], vr["mp"])


def b16_detail(vr, per):
    mp = vr["mp"]
    dmax = max(abs(16 * o - mp) for o in vr["sec"]) if mp else 0
    thr = c.b16_threshold_D(mp) if mp else 0
    det = [("Mprime", mp), ("A", vr["amb"]),
           ("flag_sectors", ":".join(str(k) for k, p in enumerate(per) if p == FLAG) or "none"),
           ("unresolved_sectors", ":".join(str(k) for k, p in enumerate(per) if p == c.UNRESOLVED) or "none"),
           ("Dmax", dmax), ("D_threshold", thr)]
    if thr:
        det.append(("Dmax/threshold", fmt(fr(dmax, thr), 4)))
    return tuple(det)


def x2_of(vr):
    """Pearson X2 of the certified sector counts against uniform: Sum (16 O_k - M')^2 / (16 M')."""
    mp = vr["mp"]
    return div(sum((16 * o - mp) * (16 * o - mp) for o in vr["sec"]), 16 * mp)


def x2_report(row, rid, at, scoring, vr, frozen):
    return Read(row, rid, at, "report", scoring, MET, value=x2_of(vr) if vr["mp"] else None, frozen=frozen,
                detail=(("Mprime", vr["mp"]), ("A", vr["amb"])))


# ---------------------------------------------------------------------------------------------------------------------
# E01: Klein symmetry at y = 0.

E01_RECORDS = {"P01": ("1", "2", "3", "4"), "P07": ("2", "3", "4"), "P09": ("1", "2", "3", "4")}
E01_PHRASES = (
    "point=P01_(t=1-4),_P07_(t=2-4),_P09_(t=1-4);_all_seven_variants;_77_reads",
    "none_of_1386_H8_tests_flags_(8_pi_pairs,_8_mirror_pairs,_sign_br,_sign_bi_per_read",
)
E01_ATOMS = "Klein_atoms_about_3.108e-4_M_per_non-LOCK_variant,_0.042097_M_for_LOCK"


def atom_report(row, rid, at, scoring, pt, flag, scope, frozen):
    m = c.COUNT * len(pt.call_list(scope))
    if m == 0:
        return nm_read(row, rid, at, "report", scoring, "no_call_read", pt, scope, frozen=frozen)
    n = pt.atoms(scope)[flag]
    return Read(row, rid, at, "report", scoring, MET, value=fr(n, m), frozen=frozen,
                detail=(("count", n), ("M", m)) + loss_detail(pt, scope))


def row_e01(points, fz):
    _require(fz, "E01", E01_PHRASES)
    rr = c.report(fz, "STRIPES_PREDICT", "E01", E01_ATOMS, "about_no_band")
    reads, extra = [], []
    for pid in Y0_POINTS:
        pt = points[pid]
        check_records(pt.spec, E01_RECORDS[pid], "E01")
        for step in pt.spec.steps:
            for v in ALL7:
                reads.append(h8_read("E01", pt, step, v, ("pi", "mir", "br", "bi")))
        extra.append(atom_report("E01", "atoms_%s_nonlock" % pid, _at(pid, extra="VNC_nl_klein"), rr, pt, "nl_klein",
                                 "all", "3.108e-4"))
        extra.append(atom_report("E01", "atoms_%s_nonlock_ctrl" % pid, _at(pid, extra="ctrl_nl_klein"), rr, pt,
                                 "nl_klein", "ctrl", "3.108e-4"))
        extra.append(atom_report("E01", "atoms_%s_lock" % pid, _at(pid, extra="LOCK_lk_klein"), rr, pt, "lk_klein",
                                 "ctrl", "0.042097"))
    _count("E01", "reads", len(reads), 77)
    _count("E01", "H8 tests", 18 * len(reads), 1386)
    return reads + extra


# ---------------------------------------------------------------------------------------------------------------------
# E02: exchange at every y.

E02_PHRASES = (
    "P02-P06,_P08,_P10,_P11,_P12_(t=1-4,_all_variants);_P13_(t=1,2);_P14_(t=1,2,_VNC);_268_reads",
    "no_H8_flag_in_2412_tests",
    "no_SIGNFLIP_flag_on_bi_(RB_for_LOCK_only)",
    "every_exchange_atom_bi=0",
)
E02_NA_BI0 = "non-atoms_with_bi=0_read_and_report"
E02_COUNTS_TEXT = ("atom_counts_in_[219,433]_at_2^22,_[25,138]_at_2^20,_[0,51]_at_2^18_(non-LOCK),"
                   "_[2939,3597]_for_LOCK_at_2^18")
E02_NONLOCK = {1 << 22: (219, 433), 1 << 20: (25, 138), 1 << 18: (0, 51)}
E02_LOCK = (1 << 18, (2939, 3597))


def xbi_read(row, pt, step, variant):
    scope = scope_of(variant)
    pid = pt.spec.id
    rid = "xbi_" + _at(pid, step, variant)
    at = _at(pid, step, variant)
    sc = c.scored("exchange_atoms")
    why = missing_reason(pt, step, variant, scope)
    if why:
        return nm_read(row, rid, at, "exact", sc, why, pt, scope, "xatom_bi_nz=0")
    vr = pt.vr(step, variant, scope)
    return Read(row, rid, at, "exact", sc, c.read3_exact(vr["xatom_bi_nz"] == 0), value=vr["xatom_bi_nz"],
                band="xatom_bi_nz=0", detail=(("xatoms", vr["xatoms"]),) + loss_detail(pt, scope))


def na_bi0_report(row, pt, step, variant, scoring):
    scope = scope_of(variant)
    pid = pt.spec.id
    rid = "nabi0_" + _at(pid, step, variant)
    at = _at(pid, step, variant)
    why = missing_reason(pt, step, variant, scope)
    if why:
        return nm_read(row, rid, at, "report", scoring, why, pt, scope)
    vr = pt.vr(step, variant, scope)
    return Read(row, rid, at, "report", scoring, MET, value=vr["na_bi0"],
                detail=(("Mprime", vr["mp"]),) + loss_detail(pt, scope))


def count_read(row, rid, at, pt, flag, scope, nominal, interval):
    """An exchange-atom count against its frozen integer interval, read only on the full nominal sample set."""
    lo, hi = interval
    band = "[%d,%d]_at_M=%d" % (lo, hi, nominal)
    sc = c.scored("start_lattice_count")
    m = c.COUNT * len(pt.call_list(scope))
    if m != nominal:
        return nm_read(row, rid, at, "count", sc, "M=%d_not_%d" % (m, nominal), pt, scope, band)
    n = pt.atoms(scope)[flag]
    return Read(row, rid, at, "count", sc, c.read3_exact(lo <= n <= hi), value=n, band=band,
                detail=(("M", m),))


def row_e02(points, fz):
    _require(fz, "E02", E02_PHRASES + (E02_COUNTS_TEXT,))
    rr = c.report(fz, "STRIPES_PREDICT", "E02", E02_NA_BI0, "row_text")
    h8s, sfs, xbis, counts, extra = [], [], [], [], []
    for pid in E02_POINTS:
        pt = points[pid]
        spec = pt.spec
        check_records(spec, ("1", "2", "3", "4") if pid not in ("P13", "P14") else ("1", "2"), "E02")
        variants = ALL7 if spec.all > 0 else ("VNC",)
        for step in spec.steps:
            for v in variants:
                h8s.append(h8_read("E02", pt, step, v, ("mir", "bi")))
                sfs.append(signflip_point_read("E02", pt, step, v, "bi", v == "LOCK", "exchange"))
                xbis.append(xbi_read("E02", pt, step, v))
                extra.append(na_bi0_report("E02", pt, step, v, rr))
        counts.append(count_read("E02", "nx_%s_vnc" % pid, _at(pid, extra="nl_exch_M%d" % spec.vnc), pt, "nl_exch",
                                 "all", spec.vnc, E02_NONLOCK[spec.vnc]))
        if spec.all > 0:
            ctrl = c.COUNT * spec.all
            if ctrl != spec.vnc:
                counts.append(count_read("E02", "nx_%s_ctrl" % pid, _at(pid, extra="nl_exch_M%d" % ctrl), pt,
                                         "nl_exch", "ctrl", ctrl, E02_NONLOCK[ctrl]))
            if ctrl != E02_LOCK[0]:
                raise StageBStop("rows_e_sym", "E02 %s LOCK sample count" % pid)
            counts.append(count_read("E02", "nx_%s_lock" % pid, _at(pid, extra="lk_exch_M%d" % ctrl), pt, "lk_exch",
                                     "ctrl", ctrl, E02_LOCK[1]))
    _count("E02", "H8 reads", len(h8s), 268)
    _count("E02", "H8 tests", 9 * len(h8s), 2412)
    _count("E02", "SIGNFLIP reads", len(sfs), 268)
    return h8s + sfs + xbis + counts + extra


# ---------------------------------------------------------------------------------------------------------------------
# E03: zero mean at y = 0.

E03_PHRASES = (
    "P01,_P07,_P09;_every_record;_all_variants;_br_and_bi:_154_tests",
    "no_SIGNFLIP_flag_(RB_for_br;_for_bi_RB=0_except_LOCK)",
)


def row_e03(points, fz):
    _require(fz, "E03", E03_PHRASES)
    reads = []
    for pid in Y0_POINTS:
        pt = points[pid]
        check_records(pt.spec, E01_RECORDS[pid], "E03")
        for step in pt.spec.steps:
            for v in ALL7:
                reads.append(signflip_point_read("E03", pt, step, v, "br", True, "symmetry_T"))
                reads.append(signflip_point_read("E03", pt, step, v, "bi", v == "LOCK", "exchange"))
    _count("E03", "SIGNFLIP tests", len(reads), 154)
    return reads


# ---------------------------------------------------------------------------------------------------------------------
# E04: evenness in y (paired P08 and P13 side files) and the two-insertion ratios (R1-R3).

E04_PHRASES = (
    "P08_against_P13_on_indices_below_2^18,_seven_variants,_t=1,_2_(14_checks)",
    "VNC_ratios_R1,_R2,_R3:_t=1_1/27->1/54,_1/54->1/108;_t=2_1/54->1/108",
    "paired_d_i=br_i(P08)-br_i(P13)_(independent_seeds,_symmetric)_give_no_SIGNFLIP_flag_with_RB=RB(P08)+RB(P13)",
    "ratios_equal_1/4_within_1/100+4SE_(series_0.25049,_0.25012,_0.25246)",
)
E04_FALSIFIER = "a_flag_or_a_scored_ratio_outside_[1/4-1/100-4SE,1/4+1/100+4SE]"
E04_T2 = "the_t=2_ratio_(1/54->1/108)_read-and-report_(X08)"
E04_RATIOS = (("ratio_t1_1/27->1/54", 64, "R2", "R1", "0.25049"),
              ("ratio_t1_1/54->1/108", 64, "R3", "R2", "0.25012"),
              ("ratio_t2_1/54->1/108", 128, "R3", "R2", "0.25246"))
SUM_KEYS = ("S", "Q", "RB", "RQ", "m")


def paired_sums(sides_a, sides_b, steps=(64, 128)):
    """E04: c.paired_side_sums summed over the calls both points read, each pair of side files at index range
    [4096 i, 4096 i + count): ({(variant, step): {S, Q, RB, RQ, m}}, [calls])."""
    sa, sb = dict(sides_a), dict(sides_b)
    calls = sorted(set(sa) & set(sb))
    acc = {}
    for i in calls:
        fa, fb = c.open_side(sa[i]), c.open_side(sb[i])
        for f, row in ((fa, sa[i]), (fb, sb[i])):
            if f.start != c.COUNT * i or f.count != row["indices"]:
                raise StageBStop("side_pair", "call %d: side file start or count" % i)
        part = c.paired_side_sums(fa, fb, steps)
        for k, x in part.items():
            a = acc.setdefault(k, dict.fromkeys(SUM_KEYS, 0))
            for f in SUM_KEYS:
                a[f] += x[f]
            if x["m"] != fa.count:
                raise StageBStop("side_pair", "call %d %s: %d pairs of %d" % (i, k, x["m"], fa.count))
    return acc, calls


def run_s(spec):
    return abs(parse_rat(spec.y)) * c.square_root(spec.N)


def ratio_read(row, rid, step, run_half, run_full, scoring, frozen):
    """E[br](y/2)/E[br](y) from two independent runs: batch means and the delta method; MET inside
    [1/4 - 1/100 - 4SE, 1/4 + 1/100 + 4SE], MISS outside."""
    at = "%s/%s_t%s" % (run_half.spec.id, run_full.spec.id, t_text(step))
    lost = ()
    for r in (run_half, run_full):
        if r.lost:
            lost += (("lost_batches_" + r.spec.id, ":".join(str(j) for j, _ in r.lost)),)
    for r in (run_half, run_full):
        # rule STOP: the records all 64 batches reached; a lost batch reached none
        if r.lost or step not in r.steps:
            why = ("batch_lost_" if r.lost else "record_not_reached_") + r.spec.id
            return Read(row, rid, at, "interval", scoring, NOT_MEASURED, frozen=frozen,
                        detail=(("lost", why),) + lost)
    mh, se2h = run_half.mean_br(step)
    mf, se2f = run_full.mean_br(step)
    if mf == 0:
        return Read(row, rid, at, "interval", scoring, NOT_RESOLVED, frozen=frozen,
                    detail=(("ratio", "E[br](y)=0"),) + lost)
    r, se2 = c.ratio_indep(mh, se2h, mf, se2f)
    tol = Rad(fr(1, 100)) + c.se(se2, 4)
    band = Band(Rad(fr(1, 4)) - tol, Rad(fr(1, 4)) + tol)
    det = (("mean_br_half", fmt(mh, 8)), ("mean_br_full", fmt(mf, 8)), ("SE", c.se(se2).text(6))) + lost
    return Read(row, rid, at, "interval", scoring, c.read3_interval(r, r, band), value=r, band=band, frozen=frozen,
                detail=det)


def row_e04(points, run_points, fz):
    _require(fz, "E04", E04_PHRASES + (E04_FALSIFIER,))
    pa, pb = points["P08"], points["P13"]
    reads = []
    steps = [s for s in (64, 128) if pa.measured(s) and pb.measured(s)]
    acc, calls = paired_sums(pa.sides(), pb.sides(), tuple(steps)) if steps else ({}, [])
    lost = (("calls_paired", len(calls)),) + tuple(("P08_" + k, v) for k, v in loss_detail(pa, "ctrl")) \
        + tuple(("P13_" + k, v) for k, v in loss_detail(pb, "ctrl"))
    sc = c.scored("exact_symmetry_paired")
    for step in (64, 128):
        for v in ALL7:
            rid = "pair_" + _at("P08-P13", step, v)
            at = _at("P08-P13", step, v)
            x = acc.get((v, step))
            if step not in steps or x is None or x["m"] == 0:
                why = "record_not_reached" if step not in steps else "no_pair_read"
                reads.append(Read("E04", rid, at, "SIGNFLIP", sc, NOT_MEASURED, detail=(("lost", why),) + lost))
                continue
            out = c.signflip(x["S"], x["Q"], x["RB"], x["RQ"])
            reads.append(signflip_read("E04", rid, at, sc, out, x["S"], x["Q"], x["RB"], x["RQ"],
                                       (("pairs", x["m"]),) + lost))
    _count("E04", "paired checks", len(reads), 14)
    for rid, step, half, full, frz in E04_RATIOS:
        rh, rf = run_points[half], run_points[full]
        t = c.t_of_step(step)
        triples = [(fr(-1, 4), run_s(r.spec), t) for r in (rh, rf)]
        sc = scoring_triples(fz, "E04", triples, E04_T2 if step == 128 else None)
        reads.append(ratio_read("E04", rid, step, rh, rf, sc, "series_" + frz))
    return reads


# ---------------------------------------------------------------------------------------------------------------------
# E05: the noiseless path control.

E05_PHRASES = (
    "TWB_NL_rows_of_P01-P13,_every_record",
    "bi=0_everywhere;_br>0_at_y!=0;_br=bi=0_at_P01,_P07,_P09;_identical_across_a_point_calls",
)
E05_LAW = "br/2^40_against_y^2_abs(g)^2_read_and_report"


def check_nl_sha256(pt):
    """Each NL call's AGG_CALL nl_sha256 equals the sha256 of its AGG_NL rows, each with its newline, in record order
    (AGG-FORMAT section 5); a difference is an edited block, not a read. common.parse_block makes the same check when
    it reads a block; this one guards points built in memory."""
    for b in pt.call_list("ctrl", "V1"):
        h = sha256_hex("".join(b.nl_rows[s] + "\n" for s in b.steps).encode("ascii"))
        if h != b.call_row["nl_sha256"]:
            raise StageBStop("nl_sha256", "%s call %d" % (pt.spec.id, b.call))


def nl_values(pt, step):
    """[(br, bi, rb_br, rb_bi, calls)] of the distinct TWB_NL rows of a record."""
    out = []
    for text, calls in sorted(pt.nl_rows(step).items()):
        d = fields_dict(parse_row(text, "TWB_NL", c.TWB_NL_KEYS)[1])
        out.append((canon_int(d["br"]), canon_int(d["bi"]), canon_int(d["rb_br"]), canon_int(d["rb_bi"]),
                    sorted(calls)))
    return out


def nl_reads(row, pt, step, law_scoring):
    pid = pt.spec.id
    at = _at(pid, step, "NL")
    y = parse_rat(pt.spec.y)
    sc = c.scored("identity")
    names = (("same", "one_TWB_NL_row_across_calls"), ("bi", "bi=0"), ("br", "br>0" if y != 0 else "br=0"))
    why = missing_reason(pt, step, "V1", "ctrl")
    if why:
        out = [nm_read(row, "nl_%s_%s" % (n, at), at, "exact", sc, why, pt, "ctrl", b) for n, b in names]
        if y != 0:
            out.append(nm_read(row, "nl_law_" + at, at, "report", law_scoring, why, pt, "ctrl"))
        return out
    vals = nl_values(pt, step)
    lost = loss_detail(pt, "ctrl")
    det = (("rows", len(vals)), ("calls", sum(len(v[4]) for v in vals)), ("br", ":".join(str(v[0]) for v in vals)),
           ("bi", ":".join(str(v[1]) for v in vals))) + lost
    out = [Read(row, "nl_same_" + at, at, "exact", sc, c.read3_exact(len(vals) == 1), value=len(vals),
                band=names[0][1], detail=det),
           Read(row, "nl_bi_" + at, at, "exact", sc, c.read3_exact(all(v[1] == 0 for v in vals)), band=names[1][1],
                value=":".join(str(v[1]) for v in vals), detail=det)]
    ok = all(v[0] > 0 for v in vals) if y != 0 else all(v[0] == 0 and v[1] == 0 for v in vals)
    out.append(Read(row, "nl_br_" + at, at, "exact", sc, c.read3_exact(ok), band=names[2][1],
                    value=":".join(str(v[0]) for v in vals), detail=det))
    if y != 0:
        law = series.g2_abs(parse_rat(pt.spec.delta), c.t_of_step(step)) * (y * y)
        ratio = law.inv() * fr(vals[0][0], 1 << 40)
        out.append(Read(row, "nl_law_" + at, at, "report", law_scoring, MET, value=ratio.mid(), lo=ratio.lo,
                        hi=ratio.hi, band="(br/2^40)/(y^2_abs(g)^2)", frozen="y^2_abs(g)^2=" + fmt(law.mid(), 8),
                        detail=(("br", vals[0][0]), ("rb_br", vals[0][2]))))
    return out


def row_e05(points, fz):
    _require(fz, "E05", E05_PHRASES)
    rr = c.report(fz, "STRIPES_PREDICT", "E05", E05_LAW, "row_text")
    reads = []
    records = 0
    for pid in NL_POINTS:
        pt = points[pid]
        check_nl_sha256(pt)
        for step in pt.spec.steps:
            records += 1
            reads += nl_reads("E05", pt, step, rr)
    _count("E05", "records", records, 49)
    return reads


# ---------------------------------------------------------------------------------------------------------------------
# E06: MODE0 against VNC on the first 2^18 samples.

E06_PHRASES = (
    "P01-P13,_every_record,_first_2^18;_49_reads",
    "0_mismatches_of_sigma_among_samples_certified_in_both_with_abs(B)>=2^-20,_0_certified_sign(br)_disagreements;"
    "_equal_B16_verdicts_at_every_read",
)
E06_EXPECT = "(expected_NOT_MET_at_P04,_P05,_P06,_P08,_P10,_P13_at_t=1,2;_MET_at_P01,_P07,_P09,_P02,_P03,_P11,_P12)"
E06_EXPECT_NOT_MET = ("P04", "P05", "P06", "P08", "P10", "P13")
B16_ROW = {"uniform": MET, "not_uniform": c.NOT_MET, "unresolved": NOT_RESOLVED}


def sector_claim(cm):
    """E06's sector claim, "0 mismatches among samples certified in both with abs(B)>=2^-20", does not say which B must
    be big. The read covers both readings: MET when there is no mismatch where either B is big (mis_big_any = 0), MISS
    when there is one where both are big (mis_big_both > 0), NOT_RESOLVED when only the wider reading has one."""
    if cm["mis_big_both"] > 0:
        return MISS
    if cm["mis_big_any"] == 0:
        return MET
    return NOT_RESOLVED


def mode0_reads(row, pt, step, expect_scoring=None):
    pid = pt.spec.id
    at = _at(pid, step, "MODE0-VNC")
    sc = c.scored("comparison_common_samples")
    why = missing_reason(pt, step, "MODE0", "ctrl")
    expect = None
    if expect_scoring is not None and t_text(step) in ("1", "2"):
        expect = "not_uniform" if pid in E06_EXPECT_NOT_MET else "uniform"
    if why:
        out = [nm_read(row, "m0_%s_%s" % (n, at), at, k, sc, why, pt, "ctrl")
               for n, k in (("sec", "exact"), ("sign", "exact"), ("b16", "B16"))]
        if expect:
            out.append(nm_read(row, "m0_exp_" + at, at, "report", expect_scoring, why, pt, "ctrl",
                               frozen="expected_" + B16_ROW[expect]))
        return out
    cm = pt.cmp(step, "MODE0")
    lost = loss_detail(pt, "ctrl")
    out = [Read(row, "m0_sec_" + at, at, "exact", sc, sector_claim(cm), value=cm["mis_big_both"],
                band="0_mismatches_with_abs(B)>=2^-20_in_both_and_in_either",
                detail=(("cert2_big_both", cm["cert2_big_both"]), ("mis_big_any", cm["mis_big_any"]),
                        ("cert2_big_any", cm["cert2_big_any"]), ("mis_all", cm["mis"]), ("cert2", cm["cert2"]),
                        ("common", cm["common"])) + lost)]
    dis = cm["br"][1] + cm["br"][3]
    out.append(Read(row, "m0_sign_" + at, at, "exact", sc, c.read3_exact(dis == 0), value=dis,
                    band="certified_sign(br)_disagreements=0",
                    detail=(("pos/neg", cm["br"][1]), ("neg/pos", cm["br"][3]),
                            ("amb_cells", sum(cm["br"][k] for k in (2, 5, 6, 7, 8))), ("common", cm["common"]))
                    + lost))
    vv, vp = b16_test(pt.vr(step, "VNC", "ctrl"))
    mv, mpr = b16_test(pt.vr(step, "MODE0", "ctrl"))
    if vv == mv and vv != "unresolved":
        o = MET
    elif {vv, mv} == {"uniform", "not_uniform"}:
        o = MISS
    else:
        o = NOT_RESOLVED
    out.append(Read(row, "m0_b16_" + at, at, "B16", sc, o, value="VNC=%s:MODE0=%s" % (vv, mv), band="equal_verdicts",
                    detail=(("VNC_flag_sectors", sum(1 for p in vp if p == FLAG)),
                            ("MODE0_flag_sectors", sum(1 for p in mpr if p == FLAG)),
                            ("Mprime", pt.vr(step, "MODE0", "ctrl")["mp"])) + lost))
    if expect:
        if vv == expect and mv == expect:
            as_read = MET
        elif {vv, mv} & ({"uniform", "not_uniform"} - {expect}):
            as_read = MISS
        else:
            as_read = NOT_RESOLVED
        out.append(Read(row, "m0_exp_" + at, at, "report", expect_scoring, as_read, value="VNC=%s:MODE0=%s" % (vv, mv),
                        frozen="expected_" + B16_ROW[expect], detail=(("as_read", as_read),)))
    return out


def row_e06(points, fz):
    _require(fz, "E06", E06_PHRASES)
    rr = c.report(fz, "STRIPES_PREDICT", "E06", E06_EXPECT, "expected_verdicts_beside")
    reads = []
    records = 0
    for pid in NL_POINTS:
        pt = points[pid]
        for step in pt.spec.steps:
            records += 1
            reads += mode0_reads("E06", pt, step, rr)
    _count("E06", "reads", records, 49)
    return reads


# ---------------------------------------------------------------------------------------------------------------------
# E07: the LOCK zero-field phase slaved to its start lattice.

E07_PHRASES = (
    "P01_(t=1-4),_P07_(t=2-4),_P09_(t=1-4);_LOCK,_first_2^18;_11_reads",
    "(i)_every_certified_non-atom_sample_has_sigma(br,bi)=sigma(c0^2-c1^2,2c0c1):_0_mismatches",
    "(ii)_abs(O_k-M-prime_q_k)<=D_k+A,_3D_k^2=96M-prime_q_k(1-q_k)+32D_k,_q_k_as_in_LOCK",
    "(iii)_B16_flags_at_all_11_reads:_uniform_NOT_MET_by_design",
)
E07_X2 = "X2_about_965_read_and_report"
LOCK_Q_PHRASE = "q_0..q_3=0.058030261,_0.066030562,_0.066589471,_0.059349706,_q_(7-k)=q_(8+k)=q_(15-k)=q_k"
LOCK_Q_TEXT = ("0.058030261", "0.066030562", "0.066589471", "0.059349706")
E07_DEV_TEXT = ("-4.470e-3", "+3.531e-3", "+4.089e-3", "-3.150e-3")
E07_DEV_PHRASE = "(deviations_-4.470e-3,_+3.531e-3,_+4.089e-3,_-3.150e-3)"


def lock_q(fz):
    """q_0..q_15 of STRIPES_DERIVATION LOCK, the exact rationals the decimals spell, checked against E07's
    deviations from 1/16 and summing to 1."""
    fz.require("STRIPES_DERIVATION", "LOCK", LOCK_Q_PHRASE)
    fz.require("STRIPES_PREDICT", "E07", E07_DEV_PHRASE)
    q4 = [dec(x) for x in LOCK_Q_TEXT]
    for q, d in zip(q4, E07_DEV_TEXT, strict=True):
        if series.check_decimal(q - fr(1, 16), d) != series.CONTAINS:
            raise StageBStop("e07_q", "q - 1/16 against " + d)
    q = (q4 + q4[::-1]) * 2
    if sum(q) != 1:
        raise StageBStop("e07_q", "sum of q_k")
    return q


def lattice_tests(vr, q):
    """[(k, O_k, |O_k - M' q_k|, ok)]: ok when |O_k - M' q_k| <= D_k + A, D_k = (32 + sqrt(1024 + 1152 M' q_k
    (1 - q_k)))/6 the positive root of 3 D^2 = 96 M' q_k (1 - q_k) + 32 D."""
    mp, amb = vr["mp"], vr["amb"]
    out = []
    for k in range(16):
        e = mp * q[k]
        dev = abs(vr["sec"][k] - e)
        ok = Rad(6 * (dev - amb) - 32) <= Rad.sqrt(1024 + 1152 * e * (1 - q[k]))
        out.append((k, vr["sec"][k], dev, ok))
    return out


def lock_d(mp, qk):
    return (Rad(32) + Rad.sqrt(1024 + 1152 * mp * qk * (1 - qk))).scale(fr(1, 6))


def lock_reads(row, pt, step, q, x2_scoring):
    pid = pt.spec.id
    at = _at(pid, step, "LOCK")
    sc = c.scored("lattice_law")
    why = missing_reason(pt, step, "LOCK", "ctrl")
    if why:
        return [nm_read(row, "lk_%s_%s" % (n, at), at, k, s, why, pt, "ctrl")
                for n, k, s in (("mis", "exact", sc), ("lat", "count", sc), ("b16", "B16", sc),
                                ("x2", "report", x2_scoring))]
    lost = loss_detail(pt, "ctrl")
    lk = pt.lock(step)
    out = [Read(row, "lk_mis_" + at, at, "exact", sc, c.read3_exact(lk["mis"] == 0), value=lk["mis"],
                band="mis=0", detail=(("cert", lk["cert"]),) + lost)]
    vr = pt.vr(step, "LOCK", "ctrl")
    tests = lattice_tests(vr, q)
    bad = [t for t in tests if not t[3]]
    worst = max(tests, key=lambda t: (t[2] - vr["amb"]) * lock_d(vr["mp"], q[t[0]]).iv().inv().mid())
    wd = lock_d(vr["mp"], q[worst[0]]).iv()
    out.append(Read(row, "lk_lat_" + at, at, "count", sc, c.read3_exact(not bad), value=len(bad),
                    band="abs(O_k-Mprime_q_k)<=D_k+A_all_k", frozen="q_0..q_3=" + ":".join(LOCK_Q_TEXT),
                    detail=(("Mprime", vr["mp"]), ("A", vr["amb"]),
                            ("outside", ":".join(str(t[0]) for t in bad) or "none"), ("worst_k", worst[0]),
                            ("worst_dev", fmt(worst[2], 8)), ("worst_D", fmt(wd.mid(), 8))) + lost))
    verdict, per = b16_test(vr)
    o = {"not_uniform": MET, "uniform": MISS, "unresolved": NOT_RESOLVED}[verdict]
    out.append(Read(row, "lk_b16_" + at, at, "B16", sc, o, value=verdict, band="B16_flags_(uniform_NOT_MET)",
                    detail=b16_detail(vr, per) + lost))
    out.append(x2_report(row, "lk_x2_" + at, at, x2_scoring, vr, "965"))
    return out


def row_e07(points, fz):
    _require(fz, "E07", E07_PHRASES)
    rr = c.report(fz, "STRIPES_PREDICT", "E07", E07_X2, "row_text")
    q = lock_q(fz)
    reads = []
    records = 0
    for pid in Y0_POINTS:
        pt = points[pid]
        check_records(pt.spec, E01_RECORDS[pid], "E07")
        for step in pt.spec.steps:
            records += 1
            reads += lock_reads("E07", pt, step, q, rr)
    _count("E07", "reads", records, 11)
    return reads


# ---------------------------------------------------------------------------------------------------------------------
# E08: uniform across orbits for the six 4-D-lattice variants at y = 0.

E08_PHRASES = (
    "P01,_P07,_P09,_all_records;_VNC,_V1,_V0,_RN,_FLIP,_MODE0;_66_reads",
    "B16_unflagged_at_all_66",
)
E08_X2 = "X2_about_15+-5.5_read_and_report"
E08_FALSIFIER = "a_certified_flag_while_E01_holds"


def uniform_reads(row, pt, step, variant, x2_scoring):
    scope = scope_of(variant)
    pid = pt.spec.id
    at = _at(pid, step, variant)
    sc = c.scored("uniformity")
    why = missing_reason(pt, step, variant, scope)
    if why:
        return [nm_read(row, "b16_" + at, at, "B16", sc, why, pt, scope),
                nm_read(row, "x2_" + at, at, "report", x2_scoring, why, pt, scope)]
    vr = pt.vr(step, variant, scope)
    verdict, per = b16_test(vr)
    o = {"uniform": MET, "not_uniform": MISS, "unresolved": NOT_RESOLVED}[verdict]
    return [Read(row, "b16_" + at, at, "B16", sc, o, value=verdict, band="B16_unflagged",
                 detail=b16_detail(vr, per) + loss_detail(pt, scope)),
            x2_report(row, "x2_" + at, at, x2_scoring, vr, "15+-5.5")]


def row_e08(points, fz, e01_reads=None):
    _require(fz, "E08", E08_PHRASES + (E08_FALSIFIER,))
    rr = c.report(fz, "STRIPES_PREDICT", "E08", E08_X2, "row_text")
    reads = []
    for pid in Y0_POINTS:
        pt = points[pid]
        check_records(pt.spec, E01_RECORDS[pid], "E08")
        for step in pt.spec.steps:
            for v in LATTICE6:
                reads += uniform_reads("E08", pt, step, v, rr)
    _count("E08", "reads", sum(1 for r in reads if r.scored), 66)
    if e01_reads is None:
        e01_reads = [h8_read("E01", points[pid], s, v, ("pi", "mir", "br", "bi")) for pid in Y0_POINTS
                     for s in points[pid].spec.steps for v in LATTICE6]
    e01_met = {r.rid[len("h8_"):] for r in e01_reads if r.rid.startswith("h8_") and r.outcome == MET}
    fals = [r.rid for r in reads if r.scored and r.outcome == MISS and r.rid[len("b16_"):] in e01_met]
    return reads, fals


# ---------------------------------------------------------------------------------------------------------------------
# The rows.


def _misses(reads):
    return [r.rid for r in reads if r.scored and r.outcome == MISS]


def _verdict(fz, rid, reads, fals):
    p = fz.predict(rid)
    return Verdict(rid, p["name"], p["tag"], reads, fals, p["falsifier"] if fals else "none")


def read_e_sym(points, run_points, fz=None):
    """Verdicts of E01-E08 from the pooled dump points P01-P14 ({id: common.Point}) and the runs R1-R3
    ({id: runs.Run})."""
    fz = fz or frozen_mod.load()
    c.check_tables(fz)
    c.check_exposure_text(fz)
    for pid in SYM_POINTS:
        if points[pid].spec is not c.DUMP_POINTS[pid]:
            raise StageBStop("rows_e_sym", "%s is not the table's point" % pid)
    for rid in SYM_RUNS:
        if run_points[rid].spec is not c.RUN_POINTS[rid]:
            raise StageBStop("rows_e_sym", "%s is not the table's run point" % rid)
    out = []
    e01 = row_e01(points, fz)
    out.append(_verdict(fz, "E01", e01, _misses(e01)))
    for rid, fn in (("E02", row_e02), ("E03", row_e03)):
        rs = fn(points, fz)
        out.append(_verdict(fz, rid, rs, _misses(rs)))
    rs = row_e04(points, run_points, fz)
    out.append(_verdict(fz, "E04", rs, _misses(rs)))
    for rid, fn in (("E05", row_e05), ("E06", row_e06), ("E07", row_e07)):
        rs = fn(points, fz)
        out.append(_verdict(fz, rid, rs, _misses(rs)))
    rs, fals = row_e08(points, fz, e01)
    out.append(_verdict(fz, "E08", rs, fals))
    return out


def load_inputs(agg_root, run_dir, require_sums=True):
    """The dump points P01-P14 from agg_root/<id>/ (rules SEED and STOP) and the runs R1-R3 from run_dir."""
    points = {pid: c.load_point(os.path.join(agg_root, pid), c.DUMP_POINTS[pid], require_sums=require_sums)
              for pid in SYM_POINTS}
    rs = {rid: runs_mod.load_run(run_dir, c.RUN_POINTS[rid]) for rid in SYM_RUNS}
    return points, rs
