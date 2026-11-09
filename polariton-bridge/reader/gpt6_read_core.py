#!/usr/bin/env python3
"""Blind bridge reader: PRE-READ contract/interval/prefix core (no output access).

This file is intentionally not yet the final 352-time, all-clause reader.
It must remain read-disabled until independently reviewed and completed.
No floats, Fractions, eval, or JSON; all arithmetic uses reduced integer pairs.
"""
import hashlib
import sys
from math import gcd, isqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "PREDICTION.hbp"
AMEND_F = ROOT / "AMENDMENT-2026-11-06-F-SAMPLING.hbp"
AMEND_G = ROOT / "AMENDMENT-2026-11-06-G-MEMO.hbp"
CORRECTIONS = ROOT / "CORRECTIONS.hbp"
FROZEN_SHA = "fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892"
SCALE = 1 << 40


class StopRead(Exception):
    pass


def need(ok, code):
    if not ok:
        raise StopRead(code)


def ratio(a, b=1):
    need(type(a) is int and type(b) is int and b != 0, "not_integer_pair")
    if b < 0:
        a, b = -a, -b
    g = gcd(a, b)
    return (a // g, b // g)


def add(a, b):
    return ratio(a[0] * b[1] + b[0] * a[1], a[1] * b[1])


def neg(a):
    return (-a[0], a[1])


def sub(a, b):
    return add(a, neg(b))


def mul(a, b):
    return ratio(a[0] * b[0], a[1] * b[1])


def div(a, b):
    need(b[0] != 0, "zero_divisor")
    return ratio(a[0] * b[1], a[1] * b[0])


def abq(a):
    return (abs(a[0]), a[1])


def cmp(a, b):
    x = a[0] * b[1] - b[0] * a[1]
    return (x > 0) - (x < 0)


def fmt(a):
    return str(a[0]) + "/" + str(a[1])


def num(s):
    """Parse a scientific decimal or a/b, exactly. No binary floating point."""
    need(isinstance(s, str) and s and len(s) < 100, "number_syntax")
    if "/" in s:
        p = s.split("/")
        need(len(p) == 2, "number_slashes")
        return ratio(int(p[0]), int(p[1]))
    q = s.lower().split("e")
    need(len(q) <= 2, "number_exponent")
    t = q[0]
    sign = -1 if t.startswith("-") else 1
    t = t.lstrip("+-")
    p = t.split(".")
    need(len(p) <= 2 and all(x.isdigit() for x in p) and any(p), "number_decimal")
    digs = "".join(p)
    places = len(p[1]) if len(p) == 2 else 0
    exponent = int(q[1]) if len(q) == 2 else 0
    need(-200 <= exponent <= 200, "number_exponent_range")
    shift = exponent - places
    return ratio(sign * int(digs) * (10 ** max(shift, 0)), 10 ** max(-shift, 0))


def ceiling_sqrt_pair(a, scale=10**18):
    """Integer upper enclosure, expressed as a rational with denominator scale."""
    need(cmp(a, ratio(0)) >= 0 and scale > 0, "negative_variance")
    n = a[0] * scale * scale
    den = a[1]
    z = (n + den - 1) // den
    r = isqrt(z)
    if r * r < z:
        r += 1
    return ratio(r, scale)


def three_se(count, sum_units, squares_units, unit_scale=SCALE):
    """Three standard errors of a common-sample mean (unbiased variance)."""
    need(type(count) is int and count > 1, "se_count")
    need(all(type(x) is int for x in (sum_units, squares_units, unit_scale)), "se_type")
    need(unit_scale > 0, "se_scale")
    var_numerator = count * squares_units - sum_units * sum_units
    need(var_numerator >= 0, "negative_sample_variance")
    var_mean = ratio(var_numerator, count * count * (count - 1) * unit_scale * unit_scale)
    return mul(ratio(3), ceiling_sqrt_pair(var_mean))


def verdict(d, terms, tol, undefined=False):
    """Frozen FC02 rule with nonnegative, individually named error terms."""
    if undefined:
        return "UNDEFINED"
    need(cmp(tol, ratio(0)) >= 0, "negative_tolerance")
    need(bool(terms) and len(terms) == len(set(terms)), "missing_error_decomposition")
    for key, value in terms.items():
        need(key and cmp(value, ratio(0)) >= 0, "negative_or_unnamed_error")
    e = ratio(0)
    for value in terms.values():
        e = add(e, value)
    x = abq(d)
    if cmp(add(x, e), tol) <= 0:
        return "MET"
    if cmp(sub(x, e), tol) > 0:
        return "MISS"
    return "NOT_RESOLVED"


def fields(line):
    parts = line.split("|")
    need(len(parts) >= 2 and parts[-1] == "json=0", "hbp_format")
    d = {"_tag": parts[0]}
    for part in parts[1:]:
        need("=" in part, "hbp_missing_equal")
        key, value = part.split("=", 1)
        need(key not in d and key and value, "hbp_duplicate_or_empty")
        d[key] = value
    return d


def rows(path):
    raw = path.read_bytes()
    need(raw and raw[-1:] == b"\n" and b"\r" not in raw, "hbp_lf")
    return raw, [fields(line) for line in raw.decode("utf-8").splitlines()]


def key(row):
    return (int(row["N"]), row["delta"], row["y"], row["t"])


def preflight():
    """Only touches frozen publications, *never* blind output directories."""
    raw, pred = rows(PRED)
    need(hashlib.sha256(raw).hexdigest() == FROZEN_SHA, "frozen_prediction_sha")
    need(len(pred) == 873, "frozen_row_count")
    ats = {key(r): r for r in pred if r["_tag"] == "BRIDGE_AT"}
    pts = {(r["N"], r["delta"], r["y"]) for r in pred if r["_tag"] == "BRIDGE_POINT"}
    need(len(ats) == 352 and len(pts) == 28, "frozen_inventory")
    read = [r for r in pred if r["_tag"] == "BRIDGE_READ_RULE"]
    need(len(read) == 1 and read[0]["MET_if"] == "abs(d)+e<=tol"
         and read[0]["MISS_if"] == "abs(d)-e>tol"
         and read[0]["else"] == "NOT_RESOLVED", "frozen_rule_modified")
    fraw, fr = rows(AMEND_F)
    need(fr[0]["prediction_sha256"] == FROZEN_SHA, "amendment_wrong_prediction")
    changed = {}
    for r in fr:
        if r["_tag"] != "BRIDGE_AMENDED_AT":
            continue
        line = int(r["frozen_line"])
        need(1 <= line <= len(pred), "amendment_line_range")
        old = pred[line - 1]
        need(old["_tag"] == "BRIDGE_AT" and key(old) == key(r), "amendment_key_drift")
        need(old["M_VNC"] == r["M_VNC_frozen"], "amendment_original_count")
        need(int(r["M_VNC_amended"]) >= int(r["M_VNC_frozen"]), "amendment_count_decrease")
        need(key(old) not in changed, "amendment_duplicate")
        changed[key(old)] = int(r["M_VNC_amended"])
    need(bool(changed), "missing_F_sampling_amendment")
    _, gr = rows(AMEND_G)
    need(any(r["_tag"] == "BRIDGE_AMENDED_IDENTITY" for r in gr), "missing_G_memo_identity")
    _, corr = rows(CORRECTIONS)
    need(corr[0]["PREDICTION.hbp_sha256"] == FROZEN_SHA, "corrections_wrong_prediction")
    return ats, pts, changed, hashlib.sha256(fraw).hexdigest()


def exact_prefix(parts, goal, *, allow_variant=False):
    """Exactly one [0,goal) sample prefix; no gap, overlap or count substitution.

    parts are source-schema metadata dictionaries, not measurements.
    Every part must come from same point, seed, dtden, time step and mask role.
    For E_PAIR, same-sample coupling requires a TWB_PAIR source row, not
    independently computed differences of separate V1/VNC estimates.
    """
    need(type(goal) is int and goal > 0 and bool(parts), "prefix_empty")
    base = parts[0]
    identity = ("N", "delta", "y", "seed", "dtden", "step")
    for r in parts:
        need(all(r.get(k) == base.get(k) for k in identity), "prefix_identity")
        need(allow_variant or r.get("variant") == base.get("variant"), "prefix_variant")
        need(r.get("_tag") in ("TWB", "TWB_PAIR"), "prefix_source_tag")
        need("start" in r and "count" in r, "prefix_no_batch_boundaries")
    cursor = 0
    for r in sorted(parts, key=lambda x: int(x["start"])):
        start, count = int(r["start"]), int(r["count"])
        need(start == cursor and count > 0, "prefix_gap_or_overlap")
        cursor += count
    need(cursor == goal, "prefix_count_mismatch")
    return True


def pair_certificate(pair_rows, expected):
    """No verdict without a same-prefix TWB_PAIR and its rounding certificate."""
    need(bool(pair_rows), "missing_E_PAIR")
    for r in pair_rows:
        need(r["_tag"] == "TWB_PAIR"
             and r.get("pair") == "V1xw-VNCxnc", "pair_not_common_sample")
        need(all(k in r for k in ("d", "d2", "n", "start", "count")), "pair_schema")
        need(int(r["n"]) == int(r["count"]), "pair_count_inconsistent")
    exact_prefix(pair_rows, expected)
    d = sum(int(r["d"]) for r in pair_rows)
    sq = sum(int(r["d2"]) for r in pair_rows)
    # The TWB_PAIR d2 field is the sample-wise squared difference at 2^80.
    e = three_se(expected, d, sq, SCALE)
    n = int(pair_rows[0]["N"])
    coefficient = ratio(2 * n * n * n, n - 1)
    mean_p = mul(coefficient, ratio(d, expected * SCALE))
    return mean_p, mul(coefficient, e)


def selftest():
    z = ratio(0)
    one = ratio(1)
    need(num("1.25e-3") == ratio(1, 800), "parse_scientific")
    need(verdict(ratio(1, 2), {"sampling": ratio(1, 10)}, one) == "MET", "met")
    need(verdict(ratio(2), {"sampling": ratio(1, 10)}, one) == "MISS", "miss")
    need(verdict(ratio(1), {"sampling": ratio(1, 10)}, one) == "NOT_RESOLVED", "ambiguity")
    need(verdict(z, {"sampling": z}, z) == "MET", "boundary_met")
    need(verdict(ratio(2), {"sampling": one}, one) == "NOT_RESOLVED", "boundary_miss_strict")
    need(verdict(z, {"sampling": z}, one, undefined=True) == "UNDEFINED", "undefined")
    need(three_se(2, 0, 0) == z, "zero_variance")
    need(cmp(three_se(2, 0, 2 * SCALE * SCALE), one) > 0, "large_variance")
    p = dict(_tag="TWB_PAIR", N="81", delta="3/5", y="1/27", seed="5",
             start="0", count="2", dtden="64", step="32", pair="V1xw-VNCxnc",
             n="2", d="0", d2="0")
    a, e = pair_certificate([p], 2)
    need(a == z and e == z, "paired_zero")
    fail = 0
    bads = [
        lambda: exact_prefix([dict(p, count="1")], 2),
        lambda: exact_prefix([p, dict(p, start="1", count="1")], 3),
        lambda: exact_prefix([p, dict(p, seed="6", start="2")], 4),
        lambda: pair_certificate([dict(p, pair="V1xw-VNCxw")], 2),
        lambda: pair_certificate([dict(p, d2="-1")], 2),
        lambda: pair_certificate([dict(p, n="3")], 2),
        lambda: verdict(z, {"sampling": ratio(-1)}, one),
        lambda: verdict(z, {}, one),
        lambda: num("NaN"),
        lambda: num("1e400"),
        lambda: fields("TWB|n=1|n=2|json=0"),
    ]
    for fn in bads:
        try:
            fn()
        except (StopRead, ValueError):
            fail += 1
    need(fail == len(bads), "fault_suite")
    return fail


def main():
    try:
        need(len(sys.argv) == 2 and sys.argv[1] in ("--preflight", "--selftest"),
             "READ_DISABLED_pending_independent_review")
        if sys.argv[1] == "--selftest":
            print("BRIDGE_READER_CORE|synthetic_faults_rejected=%d|actual_outputs_opened=0|json=0" % selftest())
        else:
            ats, pts, changed, amend_sha = preflight()
            print("BRIDGE_PRECHECK|frozen_sha256=%s|rows=873|points=%d|at=%d|F_sampling_changes=%d|F_sha256=%s|actual_outputs_opened=0|status=READER_NOT_READY|json=0"
                  % (FROZEN_SHA, len(pts), len(ats), len(changed), amend_sha))
    except (StopRead, ValueError, KeyError, UnicodeError, OSError) as exc:
        print("BRIDGE_READER_REFUSED|reason=%s|json=0" % str(exc), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
