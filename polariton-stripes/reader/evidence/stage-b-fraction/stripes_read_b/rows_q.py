"""Rows Q01-Q07 of the frozen prediction, read from the QE rows (QR1-QR5) by rules READ3, EB and EXPOSED."""

from . import frozen as frozen_mod
from . import qe as qe_mod
from . import series
from .common import (
    MET,
    MISS,
    NOT_MEASURED,
    Band,
    Read,
    Scoring,
    StageBStop,
    Verdict,
    check_guard_file,
    exposed,
    exposed_s0,
    check_exposure_text,
    read3_exact,
    read3_interval,
    read3_pieces,
    report,
    scored,
    square_root,
)
from .exact import Ext, ExactError, dec, fmt, fr, ipow, parse_rat, quotient, rat_text

D = "-1/4"
TWO_E18 = fr(2, ipow(10, 18))


def _at(n, y=None, t=None, extra=""):
    s = "N%d" % n
    if y is not None:
        s += "_y" + y
    if t is not None:
        s += "_t" + t
    return s + extra


def _s(n, y):
    return parse_rat(y) * square_root(n)


def _nm(row, rid, at, kind, scoring, why="missing_QE_row"):
    return Read(row, rid, at, kind, scoring, NOT_MEASURED, detail=(("lost", why),))


def _ratio(num, den):
    """|B_num|/|B_den| as an Ext: bounded when |B_den| is certified above 0, else the half-line [lo, +inf)."""
    (piece,) = quotient(num.absB_iv(), den.absB_iv())
    return piece


def _sign_text(r):
    b, e = r.B(), r.e_B()
    cert = "certified" if abs(b) > e else "uncertified"
    return ("pos" if b > 0 else "neg" if b < 0 else "zero") + "_" + cert


# ---------------------------------------------------------------------------------------------------------------------
# Helpers, one per kind of read (tested on their own at the excluded N=9 points).


def q01_zero(r):
    """A_e18 = B_e18 = A1_e18 = D2_e18 = 0 and C2_e18 > 0."""
    v = r.v
    ok = v["A_e18"] == 0 and v["B_e18"] == 0 and v["A1_e18"] == 0 and v["D2_e18"] == 0 and v["C2_e18"] > 0
    det = (("A_e18", v["A_e18"]), ("B_e18", v["B_e18"]), ("A1_e18", v["A1_e18"]), ("D2_e18", v["D2_e18"]),
           ("C2_e18", v["C2_e18"]))
    return read3_exact(ok), det


def q01_same(sec, pnt):
    """Every printed field of the sector row equals the point row's, array_bytes apart."""
    a = [(k, v) for k, v in sec.d.items() if k != "array_bytes"]
    b = [(k, v) for k, v in pnt.d.items() if k != "array_bytes"]
    diff = [k for (k, v), (_, w) in zip(a, b, strict=False) if v != w]
    ok = len(a) == len(b) and not diff
    return read3_exact(ok), (("differ", ",".join(diff) or "none"), ("array_bytes", "%s/%s" % (
        sec.d["array_bytes"], pnt.d["array_bytes"])))


def q02_parity(rp, rm):
    """|B(y) - B(-y)| <= e_B(y) + e_B(-y) and |A(y) + A(-y)| <= (N/2)(A1_err(y) + A1_err(-y)) + 2 10^-18."""
    db = abs(rp.B() - rm.B())
    eb = rp.e_B() + rm.e_B()
    sa = abs(rp.A() + rm.A())
    ea = rp.A_err() + rm.A_err() + TWO_E18
    ok = db <= eb and sa <= ea
    det = (("dB", fmt(db, 6)), ("bound_B", fmt(eb, 6, "up")), ("sumA", fmt(sa, 6)), ("bound_A", fmt(ea, 6, "up")))
    return read3_exact(ok), det


def q03_ratio(r_half, r_full):
    """R = D2(y/2)/D2(y) = |B(y/2)|/|B(y)|, interval [(B2-e2)/(B1+e1), (B2+e2)/(B1-e1)], or [(B2-e2)/(B1+e1), +inf)
    when B1 - e1 <= 0."""
    return _ratio(r_half, r_full)


def q03_richardson(r216, r108, r54):
    """L = (4 R(1/108) - R(1/54))/3."""
    a = _ratio(r216, r108)
    b = _ratio(r108, r54)
    return (a.scale(4) - b).scale(fr(1, 3))


def q04_D(r, y, t):
    """D(t) = D2/(2 y^2 t^2) - 1 = |B|/(N y^2 t^2) - 1."""
    y, t = parse_rat(y), parse_rat(t)
    return r.absB_iv() * fr(1, r.N * y * y * t * t) - 1


def q06_c(r, y, t):
    """c = (D2_q/D2_law - 1 - y^2 b4/b2)/kappa_q, with D2_q = 2B/N from the signed B interval (the frozen method
    D2_q = 2B_e18/N): bounded at every B, since kappa_q is a nonzero constant."""
    yy, tt = parse_rat(y), parse_rat(t)
    law = series.d2_law(fr(-1, 4), yy, tt)
    b2, b4 = series.b2b4_iv(fr(-1, 4), tt)
    k = series.kappa_q(fr(-1, 4), tt, r.N)
    ratio = r.B_iv() * fr(2, r.N) * law.inv()
    num = ratio - 1 - b4 * b2.inv() * (yy * yy)
    return num * k.inv(), ratio - 1


def q07_qw_ratio(r, lawv):
    """Q_W/EB2_lin - 1."""
    return r.QW_iv() * lawv.EB2.inv() - 1


def q07_nstar(r):
    """n*_Q = Q_W/<B>^2 - 1 as an Ext: [Q_W.lo/(|B| + e_B)^2 - 1, +inf) when the |B| interval reaches 0."""
    (piece,) = quotient(r.QW_iv(), r.absB_iv().sq())
    return piece - 1


def q07_nstar_normal(r):
    """(Q_W - 1/4)/<B>^2 - 1 as an Ext."""
    (piece,) = quotient(r.QW_iv() - fr(1, 4), r.absB_iv().sq())
    return piece - 1


def q07_over_lin(ns, law):
    """n*_Q/n*_lin - 1 for an Ext n*_Q and the law's n*_lin (positive at y != 0)."""
    nl = law.nstar()
    if not nl.pos():
        raise StageBStop("rows_q", "n*_lin not positive")
    return ns.times_pos(nl.inv()) - 1


def _end_text(x, inf):
    return inf if x is None else x


def _pieces_text(pieces):
    return "_or_".join("%s..%s" % ("-inf" if p.lo is None else fmt(p.lo, 8, "down"),
                                   "+inf" if p.hi is None else fmt(p.hi, 8, "up")) for p in pieces)


def _interval_read(row, rid, at, kind, scoring, iv, band, frozen="none", detail=()):
    """READ3 of an interval, or of the union of half-lines a ratio is when its denominator reaches 0 (an Ext or a
    list of Ext pieces): MISS when every piece is disjoint from the band."""
    pieces = iv if isinstance(iv, list) else [Ext.of(iv)]
    out = read3_pieces(pieces, band)
    if len(pieces) == 1 and pieces[0].bounded():
        p = pieces[0]
        return Read(row, rid, at, kind, scoring, out, value=(p.lo + p.hi) * fr(1, 2), lo=p.lo, hi=p.hi, band=band,
                    frozen=frozen, detail=detail)
    lo = None if any(p.lo is None for p in pieces) else min(p.lo for p in pieces)
    hi = None if any(p.hi is None for p in pieces) else max(p.hi for p in pieces)
    return Read(row, rid, at, kind, scoring, out, value="unbounded", lo=_end_text(lo, "-inf"),
                hi=_end_text(hi, "+inf"), band=band, frozen=frozen,
                detail=tuple(detail) + (("interval", _pieces_text(pieces)),))


# ---------------------------------------------------------------------------------------------------------------------
# The rows.


def _g(reads, layout, n, y, t):
    return qe_mod.get(reads, layout, n, D, y, t)


def row_q01(reads, fz):
    rows = []
    k = 0
    for layout, ns in (("sector", (81, 729, 6561)), ("point", (81, 729))):
        for n in ns:
            for t in ("1/2", "1", "2", "4"):
                k += 1
                rid = "zero%02d" % k
                at = _at(n, "0", t, "_" + layout)
                r = _g(reads, layout, n, "0", t)
                if r is None:
                    rows.append(_nm("Q01", rid, at, "exact", scored("identity")))
                    continue
                out, det = q01_zero(r)
                rows.append(Read("Q01", rid, at, "exact", scored("identity"), out, band="A=B=A1=D2=0,C2>0",
                                 detail=det))
    k = 0
    for n in (81, 729):
        for t in ("1/2", "1", "2", "4"):
            k += 1
            rid = "same%d" % k
            at = _at(n, "0", t)
            a, b = _g(reads, "sector", n, "0", t), _g(reads, "point", n, "0", t)
            if a is None or b is None:
                rows.append(_nm("Q01", rid, at, "exact", scored("identity")))
                continue
            out, det = q01_same(a, b)
            rows.append(Read("Q01", rid, at, "exact", scored("identity"), out, band="sector=point_but_array_bytes",
                             detail=det))
    fz.require("STRIPES_PREDICT", "Q01", "point=QR1,_QR2:_20_READ_rows")
    if sum(1 for r in rows if r.rid.startswith("zero")) != 20:
        raise StageBStop("rows_q", "Q01 20 rows")
    return rows


def row_q02(reads, fz):
    rows = []
    rr = report(fz, "STRIPES_PREDICT", "Q02", "the_signs_of_B(+-y)_read_and_report_(RP17)", "RP17")
    pts = [(81, t) for t in ("1/2", "1", "2", "4")] + [(729, t) for t in ("1/2", "1", "2")]
    for i, (n, t) in enumerate(pts, 1):
        at = _at(n, "+-1/54", t)
        rp, rm = _g(reads, "point", n, "1/54", t), _g(reads, "point", n, "-1/54", t)
        if rp is None or rm is None:
            rows.append(_nm("Q02", "par%d" % i, at, "certificate", scored("symmetry")))
            rows.append(_nm("Q02", "sign%d" % i, at, "sign", rr))
            continue
        out, det = q02_parity(rp, rm)
        rows.append(Read("Q02", "par%d" % i, at, "certificate", scored("symmetry"), out,
                         band="diff_within_certificates", detail=det))
        rows.append(Read("Q02", "sign%d" % i, at, "sign", rr, MET, value="B(+y)=%s,B(-y)=%s" % (
            _sign_text(rp), _sign_text(rm))))
    fz.require("STRIPES_PREDICT", "Q02", "7_(N,t)")
    return rows


def row_q03(reads, fz):
    rows = []
    band = Band(fr(99, 400), fr(101, 400))
    ys = ("1/27", "1/54", "1/108", "1/216")
    k = 0
    for n, layout in ((81, "point"), (729, "point")):
        for t in ("1/2", "1"):
            for y, yh in zip(ys[:-1], ys[1:], strict=True):
                k += 1
                rid = "R%02d" % k
                at = _at(n, y + "->" + yh, t)
                tt = parse_rat(t)
                phrase = "(729,_1/27->1/54,_t=1/2)" if (n, y, t) == (729, "1/27", "1/2") else None
                sc = _value_scoring_pair(fz, "Q03", n, (y, yh), t, phrase)
                rh, rf = _g(reads, layout, n, yh, t), _g(reads, layout, n, y, t)
                det = (("series_R-1/4", fmt(series.r_two_term(fr(-1, 4), tt, parse_rat(y)), 5)),)
                if rh is None or rf is None:
                    rows.append(_nm("Q03", rid, at, "interval", sc))
                    continue
                rows.append(_interval_read("Q03", rid, at, "interval", sc, q03_ratio(rh, rf), band, detail=det))
    phrase = "R(1/108->1/216)_and_L_at_t=2"
    sc = _value_scoring_pair(fz, "Q03", 729, ("1/108", "1/216"), "2", phrase)
    r216, r108, r54 = (_g(reads, "point", 729, y, "2") for y in ("1/216", "1/108", "1/54"))
    det = (("series_R-1/4", fmt(series.r_two_term(fr(-1, 4), 2, fr(1, 108)), 5)),)
    if r216 is None or r108 is None:
        rows.append(_nm("Q03", "R13", _at(729, "1/108->1/216", "2"), "interval", sc))
    else:
        rows.append(_interval_read("Q03", "R13", _at(729, "1/108->1/216", "2"), "interval", sc,
                                   q03_ratio(r216, r108), band, detail=det))
    sc = _value_scoring_pair(fz, "Q03", 729, ("1/54", "1/108", "1/216"), "2", phrase)
    if r216 is None or r108 is None or r54 is None:
        rows.append(_nm("Q03", "L", _at(729, "L", "2"), "interval", sc))
    else:
        rows.append(_interval_read("Q03", "L", _at(729, "L", "2"), "interval", sc, q03_richardson(r216, r108, r54),
                                   band, frozen="L-1/4=-8.0e-6_two-term"))
    _count(fz, "Q03", rows, 14, 11, "so_11_of_14_reads_scored")
    return rows


def _value_scoring_pair(fz, rid, n, ys, ts, phrase):
    """A read built from several (y, t) at one N: exposed if any of its triples (-1/4, |s|, t) is (rule EXPOSED)."""
    ts = (ts,) if isinstance(ts, str) else ts
    ex = any(_exposed_triple(fr(-1, 4), abs(_s(n, y)), parse_rat(t)) for y in ys for t in ts)
    if ex != (phrase is not None):
        raise StageBStop("exposed", "%s N=%d %s t=%s: rule and row text disagree" % (rid, n, ys, ts))
    if phrase is None:
        return Scoring(True, "unexposed")
    fz.require("STRIPES_PREDICT", rid, phrase)
    return Scoring(False, "X08")


def _exposed_triple(delta, s, t):
    return exposed_s0(delta, t) if s == 0 else exposed(delta, s, t)


def _count(fz, rid, rows, total, n_scored, phrase):
    fz.require("STRIPES_PREDICT", rid, phrase)
    got = (len(rows), sum(1 for r in rows if r.scored))
    if got != (total, n_scored):
        raise StageBStop("rows_q", "%s reads/scored %s, frozen %d/%d" % (rid, got, total, n_scored))


def row_q04(reads, fz):
    rows = []
    band_r = Band(fr(1, 5), fr(3, 10))
    band_d = Band(0, fr(1, 20), lo_open=True, hi_open=True)
    y = "1/27"
    for n in (81, 729):
        r8, r4, r2 = (_g(reads, "point", n, y, t) for t in ("1/8", "1/4", "1/2"))
        for rid, (ra, ta), (rb, tb), frz in (("ratio_a", (r8, "1/8"), (r4, "1/4"), "classical_0.24837"),
                                             ("ratio_b", (r4, "1/4"), (r2, "1/2"), "classical_0.24357")):
            at = _at(n, y, "D(%s)/D(%s)" % (ta, tb))
            phrase = "D(1/4)/D(1/2)_at_N=729_read-and-report_(X08:_s=1,_t=1/2)" if (n, rid) == (729, "ratio_b") \
                else None
            sc = _value_scoring_pair(fz, "Q04", n, (y,), (ta, tb), phrase)
            rid2 = "%s_N%d" % (rid, n)
            if ra is None or rb is None:
                rows.append(_nm("Q04", rid2, at, "interval", sc))
                continue
            da, db = q04_D(ra, y, ta), q04_D(rb, y, tb)
            rows.append(_interval_read("Q04", rid2, at, "interval", sc, quotient(da, db), band_r, frozen=frz))
        at = _at(n, y, "1/8")
        sc = _value_scoring_pair(fz, "Q04", n, (y,), "1/8", None)
        if r8 is None:
            rows.append(_nm("Q04", "D8_N%d" % n, at, "interval", sc))
        else:
            rows.append(_interval_read("Q04", "D8_N%d" % n, at, "interval", sc, q04_D(r8, y, "1/8"), band_d,
                                       frozen="classical_0.010996"))
    _count(fz, "Q04", rows, 6, 5, "the_other_3_ratios_and_both_D(1/8)_bands_scored")
    return rows


Q05_PRED = (("1/2", "1/27", "+6.031e-5"), ("1", "1/27", "+4.912e-4"), ("1", "1/54", "+1.2255e-4"),
            ("2", "1/54", "+2.4604e-3"), ("2", "1/108", "+6.091e-4"))


def row_q05(reads, fz):
    rows = []
    fz.require("STRIPES_PREDICT", "Q05", "R-1/4=+6.031e-5,_+4.912e-4,_+1.2255e-4,_+2.4604e-3,_+6.091e-4")
    phrase = "read-and-report_(X08):_the_t=1/2_ratio_and_both_t=2_ratios,_so_the_two_t=1_ratios_are_scored"
    for i, (t, y, text) in enumerate(Q05_PRED, 1):
        yh = rat_text(parse_rat(y) * fr(1, 2))
        p = dec(text)
        band = Band(p * fr(4, 5), p * fr(6, 5)) if parse_rat(t) <= 1 else Band(p * fr(1, 2), p * fr(3, 2))
        sc = _value_scoring_pair(fz, "Q05", 729, (y, yh), t, None if t == "1" else phrase)
        at = _at(729, y + "->" + yh, t)
        rh, rf = _g(reads, "point", 729, yh, t), _g(reads, "point", 729, y, t)
        if rh is None or rf is None:
            rows.append(_nm("Q05", "dR%d" % i, at, "interval", sc))
            continue
        rows.append(_interval_read("Q05", "dR%d" % i, at, "interval", sc, q03_ratio(rh, rf) - fr(1, 4), band,
                                   frozen=text))
    _count(fz, "Q05", rows, 5, 2, phrase)
    return rows


Q06_FROZEN = {("1/2", "1/54"): ("2.02700e-4", "-0.000080"), ("1/2", "1/108"): ("5.06750e-5", "-0.000020"),
              ("1", "1/54"): ("1.241720e-3", "-0.000653"), ("1", "1/108"): ("3.104301e-4", "-0.000163"),
              ("2", "1/54"): ("1.629505e-2", "-0.012952"), ("2", "1/108"): ("4.073763e-3", "-0.003238")}
Q06_KAPPA = {"1/2": "-0.000648", "1": "-0.003599", "2": "-0.040379"}


def row_q06(reads, fz):
    rows = []
    band = Band(fr(1, 2), fr(3, 2))
    phrase = "read-and-report_(X08):_both_t=2_reads_with_their_sign,_so_4_reads_scored_(t=1/2,_1)"
    rr_dev = report(fz, "STRIPES_PREDICT", "Q06", "D2_q/D2_law-1_read_and_report", "row_text")
    dev = []
    for t in ("1/2", "1", "2"):
        for y in ("1/54", "1/108"):
            sc = _value_scoring_pair(fz, "Q06", 729, (y,), t, phrase if t == "2" else None)
            at = _at(729, y, t)
            d2, yb = Q06_FROZEN[(t, y)]
            frz = "D2_law=%s,kappa_q=%s,y2b4/b2=%s" % (d2, Q06_KAPPA[t], yb)
            r = _g(reads, "point", 729, y, t)
            rid = "c_y%s_t%s" % (y, t)
            if r is None:
                rows.append(_nm("Q06", rid, at, "interval", sc))
                dev.append(_nm("Q06", "dev_y%s_t%s" % (y, t), at, "interval", rr_dev))
                continue
            c, dv = q06_c(r, y, t)
            det = (("B_e18", r.v["B_e18"]), ("B_sign", _sign_text(r)))
            # the literal falsifier B_e18 <= 0, else READ3 on c (bounded at every B: no certificate on B is needed)
            out = MISS if r.v["B_e18"] <= 0 else read3_interval(c.lo, c.hi, band)
            rows.append(Read("Q06", rid, at, "interval", sc, out, value=c.mid(), lo=c.lo, hi=c.hi, band=band,
                             frozen=frz, detail=det))
            dev.append(Read("Q06", "dev_y%s_t%s" % (y, t), at, "interval", rr_dev, MET, value=dv.mid(), lo=dv.lo,
                            hi=dv.hi))
    _count(fz, "Q06", rows, 6, 4, phrase)
    return rows + dev


Q07_NSTAR = {("1/2", "1/27"): "17.760", ("1/2", "1/54"): "199.67", ("1", "1/27"): "5.566", ("1", "1/54"): "46.527",
             ("1", "1/108"): "574.30", ("2", "1/54"): "17.723", ("2", "1/108"): "182.18"}
Q07_EB2 = {("1/2", "1/27"): "1.6385", ("1/2", "1/54"): "1.0955", ("1", "1/27"): "21.522", ("1", "1/54"): "9.7361",
           ("1", "1/108"): "7.3657", ("2", "0"): "327.18", ("2", "1/54"): "660.50", ("2", "1/108"): "403.89"}


def row_q07(reads, fz):
    rows, extra = [], []
    phrase = "read-and-report_(X08):_t=1/2_at_y=1/27_and_every_t=2_band"
    fz.require("STRIPES_PREDICT", "Q07", phrase + ";_scored:_t=1/2_at_y=1/54_and_t=1_at_all_three_y")
    rr_norm = report(fz, "STRIPES_PREDICT", "Q07", "normal-order_(Q_W-1/4)/<B>^2-1_read_and_report", "row_text")
    rr_above = report(fz, "STRIPES_PREDICT", "Q07", "at_t=2_Q_W_at_or_above_the_law_read_and_report", "row_text")
    pts = (("1/2", "1/27"), ("1/2", "1/54"), ("1", "1/27"), ("1", "1/54"), ("1", "1/108"), ("2", "0"),
           ("2", "1/54"), ("2", "1/108"))
    for t, y in pts:
        tt = parse_rat(t)
        law = series.Law(fr(-1, 4), 729 * parse_rat(y) * parse_rat(y), tt)
        rr = phrase if (t, y) == ("1/2", "1/27") or t == "2" else None
        sc = _value_scoring_pair(fz, "Q07", 729, (y,), t, rr)
        bq = Band(fr(-1, 20), fr(1, 20)) if tt <= 1 else Band(fr(-3, 10), fr(-1, 20))
        bn = Band(fr(-1, 10), fr(1, 10)) if tt <= 1 else Band(fr(-1, 5), fr(1, 10))
        at = _at(729, y, t)
        r = _g(reads, "point", 729, y, t)
        if r is None:
            rows.append(_nm("Q07", "QW_y%s_t%s" % (y, t), at, "interval", sc))
            if y != "0":
                rows.append(_nm("Q07", "ns_y%s_t%s" % (y, t), at, "interval", sc))
                extra.append(_nm("Q07", "nsno_y%s_t%s" % (y, t), at, "interval", rr_norm))
            if t == "2":
                extra.append(_nm("Q07", "above_y%s" % y, at, "interval", rr_above))
            continue
        rows.append(_interval_read("Q07", "QW_y%s_t%s" % (y, t), at, "interval", sc, q07_qw_ratio(r, law), bq,
                                   frozen="EB2_lin=" + Q07_EB2[(t, y)]))
        if y != "0":
            rows.append(_interval_read("Q07", "ns_y%s_t%s" % (y, t), at, "interval", sc,
                                       q07_over_lin(q07_nstar(r), law), bn, frozen="n*_lin=" + Q07_NSTAR[(t, y)]))
            # the named quantity (Q_W - 1/4)/<B>^2 - 1, its ratio to n*_lin beside
            nn = q07_nstar_normal(r)
            extra.append(_interval_read("Q07", "nsno_y%s_t%s" % (y, t), at, "interval", rr_norm, nn, Band(None, None),
                                        detail=(("over_nstar_lin-1", _pieces_text([q07_over_lin(nn, law)])),)))
        if t == "2":
            q = r.QW_iv() - law.EB2
            extra.append(Read("Q07", "above_y%s" % y, at, "interval", rr_above, MET, value=q.mid(), lo=q.lo, hi=q.hi,
                              band="Q_W-EB2_lin"))
    # n*_Q infinite at y = 0 (t = 2), scored: B_e18 = 0 exactly and Q_W > 0.
    sc = scored("follows_from_Q01")
    fz.require("STRIPES_PREDICT", "Q07", "n*_Q_infinite_at_y=0_scored_(it_follows_from_Q01)")
    r = _g(reads, "point", 729, "0", "2")
    if r is None:
        rows.append(_nm("Q07", "ns_y0_t2", _at(729, "0", "2"), "exact", sc))
    else:
        ok = r.v["B_e18"] == 0 and r.QW_iv().lo > 0
        rows.append(Read("Q07", "ns_y0_t2", _at(729, "0", "2"), "exact", sc, read3_exact(ok), value="infinite"
                         if ok else "finite", band="B_e18=0,Q_W>0", frozen="infinite",
                         detail=(("B_e18", r.v["B_e18"]),)))
    n_sc = sum(1 for x in rows if x.scored)
    if n_sc != 9:
        raise StageBStop("rows_q", "Q07 scored reads %d, expected 9 (4 Q_W, 4 n*_Q, n*_Q at y=0)" % n_sc)
    return rows + extra


ROWS = (("Q01", row_q01), ("Q02", row_q02), ("Q03", row_q03), ("Q04", row_q04), ("Q05", row_q05), ("Q06", row_q06),
        ("Q07", row_q07))


def read_q(qe_path, cost_path=None, guard_path=None, fz=None, rc_path=None):
    """Verdicts of Q01-Q07 from the filed QE stdout (and, when given, its COST rows, the guard lines and the
    wrapper's QE-RC.hbp, whose nonzero rc leaves every read of that command NOT_MEASURED: rule STOP)."""
    fz = fz or frozen_mod.load()
    qe_mod.check_plan(fz)
    check_exposure_text(fz)
    if guard_path is not None:
        check_guard_file(guard_path, qe_mod.plan_guards())
    try:
        reads = qe_mod.parse_qe(qe_path, qe_mod.PLAN, cost_path, rc_path)
    except ExactError as e:
        raise StageBStop("qe_row", str(e)) from e
    out = []
    for rid, fn in ROWS:
        p = fz.predict(rid)
        rs = fn(reads, fz)
        fals = tuple(r.rid for r in rs if r.scored and r.outcome == MISS)
        out.append(Verdict(rid, p["name"], p["tag"], rs, falsifier_reads=fals, falsifier_text=p["falsifier"]))
    return out, reads

