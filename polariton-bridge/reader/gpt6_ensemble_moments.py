#!/usr/bin/env python3
"""Common-prefix ensemble moment assembler, synthetic selftests only.

No filesystem output loader; accepts ONLY in-memory, independently
authenticated source-schema rows after final review. It cannot be run
on reserved outputs. All arithmetic is exact integer rational.

CV needs externally proved E[linear control] for the same point; no
guessing that the control expectation is zero. Nonlinear ratios use
shared-sample means, not mean of individual per-sample ratios. 3SE
is a *statistical* error estimate; it is not deterministic confidence.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpt6_read_core import (
    StopRead, need, ratio, add, sub, mul, div, cmp, fmt,
    num, canon_int, three_se, ceiling_sqrt_pair, exact_prefix,
    pair_certificate, SCALE,
)
from gpt6_source_schema import validate_ensemble

Z = ratio(0)
ONE = ratio(1)
THREE = ratio(3)


def rsum(rows, field):
    need(bool(rows), "empty_moment_sum")
    return sum(canon_int(row[field]) for row in rows)


def se_variance(m, first, second):
    need(m > 1, "too_few_samples")
    numerator = m * second - first * first
    need(numerator >= 0, "negative_sample_variance")
    return ratio(numerator, m * m * (m - 1) * SCALE * SCALE)


def sample_cov(m, sa, sb, sab):
    return ratio(m * sab - sa * sb, m * m * (m - 1) * SCALE * SCALE)


def upper_abs(x):
    return x if cmp(x, Z) >= 0 else (-x[0], x[1])


def upper_rsqrt(x):
    return ceiling_sqrt_pair(x, 10**18)


def sq(x):
    return mul(x, x)


def nonnegative_square_interval(x, e):
    need(cmp(e, Z) >= 0, "negative_component_width")
    lo, hi = sub(x, e), add(x, e)
    a, b = sq(lo), sq(hi)
    highest = a if cmp(a, b) > 0 else b
    if cmp(lo, Z) <= 0 and cmp(hi, Z) >= 0:
        return Z, highest
    lowest = a if cmp(a, b) < 0 else b
    return lowest, highest


def component_interval_ratio(zr, zi, x, rz, ri, rx, n):
    """Conservative rectangular 3SE propagation for V2 ratio of means.

    Bounds are conditional on the component confidence intervals being
    valid; 3SE alone is not a deterministic probability guarantee.
    """
    xlo, xhi = sub(x, rx), add(x, rx)
    if cmp(xlo, Z) <= 0:
        return None
    re_lo, re_hi = nonnegative_square_interval(zr, rz)
    im_lo, im_hi = nonnegative_square_interval(zi, ri)
    numer_lo, numer_hi = add(re_lo, im_lo), add(re_hi, im_hi)
    f = ratio(n - 1, n)
    lo = mul(f, div(numer_lo, xhi))
    hi = mul(f, div(numer_hi, xlo))
    mean = mul(f, div(add(sq(zr), sq(zi)), x))
    need(cmp(lo, mean) <= 0 and cmp(mean, hi) <= 0, "ratio_interval_wrong")
    return mean, lo, hi


def validate_authenticated_batches(batch_rows, *, source_authenticated=False):
    """Refuse any data before an external all-file SHA provenance check."""
    need(source_authenticated is True, "SOURCE_NOT_INDEPENDENTLY_HASH_AUTHENTICATED")
    need(type(batch_rows) is list and bool(batch_rows), "missing_batches")
    heads = []
    for batch in batch_rows:
        head, _, _ = validate_ensemble(batch)
        heads.append(head)
    for head in heads:
        need(head.get("binary_sha256") and head.get("source_sha256"),
             "batch_missing_binary_or_source_hash")
        need(all(head[k] == heads[0][k] for k in (
            "N", "delta", "y", "seed", "dtden", "binary_sha256",
            "source_sha256")),
             "cross_batch_provenance_mismatch")
    return heads


def get_moments(batch_rows, variant, t, count, ordering,
                *, source_authenticated=False, control=None):
    """Compute strictly common-prefix exact ensemble moments.

    Exact public source units:
      zr/zi, xw/xnc, dzr/dzi, dxw/dxnc at 2^40
      *_2 and zr*x at 2^80
      f2 and brbi at 2^80.
    """
    heads = validate_authenticated_batches(
        batch_rows, source_authenticated=source_authenticated
    )
    need(ordering in ("xw", "xnc"), "ordering_not_frozen")
    need(variant in ("VNC", "V1", "V0", "FLIP", "LOCK", "MODE0", "RN"),
         "bad_variant")
    need(type(t) is int and t >= 0, "bad_step")
    raw = []
    rounding = []
    for batch in batch_rows:
        for row in batch[1:-1]:
            if row.get("variant") != variant or row.get("step") != str(t):
                continue
            if row["_tag"] == "TWB":
                raw.append(row)
            elif row["_tag"] == "TWB_ROUND":
                rounding.append(row)
    need(raw and len(raw) == len(rounding), "missing_batch_or_rounding")
    exact_prefix(raw, count)
    exact_prefix(rounding_for_prefix(rounding), count)
    matched = {(canon_int(x["start"]), canon_int(x["count"])): x
               for x in rounding}
    need(len(matched) == len(rounding), "duplicate_round_batch")
    for row in raw:
        k = (canon_int(row["start"]), canon_int(row["count"]))
        need(k in matched, "round_missing_batch")
        rr = matched[k]
        need(all(row[f] == rr[f] for f in (
            "N", "delta", "y", "seed", "dtden", "step",
            "start", "count", "n", "variant"
        )), "round_metadata_mismatch")
    need(all(int(h["dtden"]) * int(h["steps"].split(",")[0]) >= 0
             for h in heads), "invalid_head_steps")
    n = canon_int(raw[0]["N"], positive=True)
    need(n > 1 and count > 1, "bad_sample_count")
    need(n == int(heads[0]["N"]) and all(int(x["n"]) == int(x["count"]) for x in raw),
         "raw_count_inconsistent")
    if variant == "VNC":
        need(ordering == "xnc", "VNC_wrong_ordering")
    if variant in ("V1", "V0"):
        need(ordering == "xw", "V1_V0_wrong_ordering")
    use_cv = control is not None
    if use_cv:
        need(type(control) is dict and set(control) == (
            {"zr", "zi", "x", "provenance", "independently_verified"}
        ), "cv_requires_proven_control_constants")
        need(control["independently_verified"] is True
             and control["provenance"] == "FROZEN_LINEAR_EXPECTATION",
             "CV_CONTROL_EXPECTATION_NOT_PROVEN")
    zr = "dzr" if use_cv else "zr"
    zi = "dzi" if use_cv else "zi"
    xx = "dx" + ordering[1:] if use_cv else ordering
    fields = (zr, zi, xx)
    square_fields = (zr + "2", zi + "2", xx + "2")
    covfield = zr + xx if use_cv else "zr" + ordering
    need(covfield in ("dzrdxw", "dzrdxnc", "zrxw", "zrxnc"),
         "missing_common_sample_covariance_field")
    for row in raw:
        need(all(k in row for k in fields + square_fields + (covfield,)),
             "missing_second_moments_or_covariance")
    sums = tuple(rsum(raw, f) for f in fields)
    squares = tuple(rsum(raw, f) for f in square_fields)
    covariance_sum = rsum(raw, covfield)
    means = [ratio(s, count * SCALE) for s in sums]
    if use_cv:
        means = [add(mu, num(control[name])) for mu, name in
                 zip(means, ("zr", "zi", "x"))]
    variances = [se_variance(count, sums[i], squares[i]) for i in range(3)]
    covariance = sample_cov(count, sums[0], sums[2], covariance_sum)
    need(cmp(sq(covariance), mul(variances[0], variances[2])) <= 0,
         "impossible_covariance")
    se3 = [mul(THREE, upper_rsqrt(v)) for v in variances]
    # The printed round RB units are sums of absolute per-sample
    # field errors. They must stay out of the sampling SE.
    rounds = []
    for field in fields:
        amount = sum(canon_int(rr["rb_" + field]) for rr in rounding)
        need(amount >= 0, "negative_rounding_budget")
        rounds.append(ratio(amount, count * SCALE))
    return {
        "N": n, "count": count, "variant": variant,
        "ordering": ordering, "CV": use_cv,
        "means": means, "variance_mean": variances,
        "covariance_re_x": covariance, "3SE_components": se3,
        "rounding_components": rounds,
        "V2_interval": component_interval_ratio(
            *means, *se3, n
        ),
    }


def rounding_for_prefix(round_rows):
    # Prefix checker recognizes the TWB metadata representation only.
    return [dict(x, _tag="TWB") for x in round_rows]


def pair_common(batch_rows, t, count, *, source_authenticated=False):
    validate_authenticated_batches(batch_rows, source_authenticated=source_authenticated)
    pairs = []
    rounds = []
    for batch in batch_rows:
        for row in batch[1:-1]:
            if row.get("pair") != "V1xw-VNCxnc" or row.get("step") != str(t):
                continue
            if row["_tag"] == "TWB_PAIR":
                pairs.append(row)
            elif row["_tag"] == "TWB_PAIR_ROUND":
                rounds.append(row)
    need(pairs and rounds, "paired_prefix_missing")
    return pair_certificate(pairs, count, rounds)


def _stub_head(count=4):
    return {
        "_tag": "TWB_HEAD", "guard": "lifted", "float_used": "0",
        "N": "81", "delta": "3/5", "y": "1/27",
        "seed": "7", "start": "0", "count": str(count),
        "samples": str(count), "dtden": "64", "steps": "32",
        "mask": "VNC", "source_sha256": "example-synthetic-source",
        "binary_sha256": "example-synthetic-binary", "u": "1",
    }


def selftest():
    from gpt6_source_schema import TWB_NUMERIC, FIXED_ROUND
    count = 4
    n = 81
    zrs = (0, 1, 2, 3)
    xxs = (4, 4, 4, 4)
    data = {k: "0" for k in TWB_NUMERIC}
    data.update({
        "n": str(count),
        "zr": str(sum(zrs) * SCALE), "zi": "0",
        "xnc": str(sum(xxs) * SCALE),
        "zr2": str(sum(v * v for v in zrs) * SCALE * SCALE),
        "zi2": "0",
        "xnc2": str(sum(v * v for v in xxs) * SCALE * SCALE),
        "zrxnc": str(sum(v * w for v, w in zip(zrs, xxs)) * SCALE * SCALE),
    })
    row = {
        "_tag": "TWB", "variant": "VNC", "N": str(n),
        "delta": "3/5", "y": "1/27", "seed": "7",
        "dtden": "64", "step": "32",
        "start": "0", "count": str(count), "float_used": "0",
        **data,
    }
    rr = {
        "_tag": "TWB_ROUND", "variant": "VNC",
        "N": str(n), "delta": "3/5", "y": "1/27",
        "seed": "7", "start": "0", "count": str(count),
        "dtden": "64", "step": "32", "n": str(count),
        "eps_max": "0", "float_used": "0",
    }
    rr.update({k: "0" for k in FIXED_ROUND})
    # dxnc2 is an additional *required* field of the real engine schema.
    row["dxnc2"] = "0"
    done = {"_tag": "TWB_DONE", "n": str(count)}
    batch = [_stub_head(), row, rr, done]
    # Validating the complete source schema is required before aggregation.
    state = get_moments([batch], "VNC", 32, count, "xnc",
                        source_authenticated=True)
    need(state["means"] == [ratio(3, 2), ratio(0), ratio(4)],
         "plain_shared_moments")
    need(state["V2_interval"] is not None, "positive_ratio_case")
    value, lo, hi = state["V2_interval"]
    need(value == ratio((n - 1) * 9, n * 16), "ratio_of_means")
    need(cmp(lo, value) <= 0 and cmp(value, hi) <= 0, "ratio_enclosure")
    need(state["covariance_re_x"] == Z, "zero_covariance")
    bads = [
        lambda: get_moments([batch], "VNC", 32, count, "xnc",
                            source_authenticated=False),
        lambda: get_moments([batch, batch], "VNC", 32, 2*count, "xnc",
                            source_authenticated=True),
        lambda: get_moments([batch], "VNC", 32, count, "xw",
                            source_authenticated=True),
        lambda: get_moments([batch], "VNC", 32, count, "xnc",
                            source_authenticated=True,
                            control={"zr": "0", "zi": "0", "x": "0",
                                     "provenance": "UNVERIFIED",
                                     "independently_verified": True}),
        lambda: get_moments([[_stub_head(), dict(row, zr2="-1"), rr, done]],
                            "VNC", 32, count, "xnc", source_authenticated=True),
        lambda: get_moments([[_stub_head(), row, dict(rr, rb_zr="-1"), done]],
                            "VNC", 32, count, "xnc", source_authenticated=True),
        lambda: get_moments([[_stub_head(), row, done]],
                            "VNC", 32, count, "xnc", source_authenticated=True),
    ]
    caught = 0
    for fn in bads:
        try:
            fn()
        except (StopRead, KeyError, ValueError, TypeError, ZeroDivisionError):
            caught += 1
    need(caught == len(bads), "ensemble_fault_not_caught")
    print("BRIDGE_MOMENTS|sample_count=4|mean_ReZ=3/2|"
          "mean_XNC=4/1|V2_ratio_of_means=%s|"
          "covariance_re_x=0/1|synthetic_faults_rejected=%d|"
          "actual_outputs_opened=0|status=PASS|json=0"
          % (fmt(value), caught))


if __name__ == "__main__":
    try:
        need(sys.argv == [sys.argv[0], "--selftest"],
             "BLIND_OUTPUT_READ_DISABLED")
        selftest()
    except (StopRead, KeyError, ValueError, TypeError,
            ZeroDivisionError, OSError) as e:
        print("BRIDGE_MOMENTS_REFUSED|reason=%s|json=0" % str(e),
              file=sys.stderr)
        sys.exit(3)
