#!/usr/bin/env python3
"""Exhaustive blind-bridge clause compiler, synthetic only; READ DISABLED.

This module does not open any quantum, ensemble, trajectory or jet measurement.
It imports only the already frozen PREDICTION.hbp via gpt6_read_core.preflight()
and enumerates each obligation from every one of the 352 BRIDGE_AT lines.
Every unmeasured comparison is explicit; values cannot be guessed from a
predicted law, a missing file, or unrelated unpaired batches.

For authorized future reading, a separate audited adapter must construct
evidence with authenticated source hashes and exact five-term errors.
"""
import hashlib
import sys
from collections import Counter
from pathlib import Path

from gpt6_read_core import (
    StopRead, need, fields, rows, num, ratio, cmp, add, sub, mul, div,
    abq, fmt, verdict, pair_verdict, preflight, REQUIRED_ERRORS,
    PRED, key,
)

STATUS = ("MET", "MISS", "NOT_RESOLVED", "UNDEFINED", "NOT_MEASURED")
MISSING_REASONS = (
    "STILL_RUNNING", "BUDGET", "PRECISION", "NOT_REACHABLE_FROM_HERE",
)
READ_ONLY = ("E_V1", "E_V0", "T_READ", "E_READ",
             "C_INSUFF", "C_LOCK", "C_JFLIP")
APPLICABLE = ("T_V2_ID", "T_ANCHOR", "T_SELF", "E_VNC", "E_PAIR",
              "C_INSUFF", "C_JFLIP", "C_LOCK", "C_MODE0", "C_NOISELESS",
              "Q_GATES", "T_ZERO", "Q_ZERO", "E_VNC_ZERO",
              "T_LAW_BAND", "T_CLOCK_BAND")
EXPECTED_APPLIES = {
    "T_V2_ID": 298, "T_ANCHOR": 22, "T_SELF": 22,
    "E_VNC": 70, "E_PAIR": 83, "C_INSUFF": 83,
    "C_JFLIP": 156, "C_LOCK": 57, "C_MODE0": 352,
    "C_NOISELESS": 352, "Q_GATES": 352, "T_ZERO": 54,
    "Q_ZERO": 54, "E_VNC_ZERO": 13, "T_LAW_BAND": 64,
    "T_CLOCK_BAND": 66,
}
EXPECTED_REPORTS = {
    "E_V1": 352, "E_V0": 352, "T_READ": 170,
    "E_READ": 269, "C_INSUFF": 269, "C_LOCK": 295,
    "C_JFLIP": 196,
}
EXTRA_COUNTS = {
    "BRIDGE_TRAJ_PRED": 24, "BRIDGE_TRAJ_SCALING": 16,
    "ENS_ROW_QUANTUM": 60, "ENS_ROW_PAIR": 60,
    "ENS_ROW_SCALING": 16, "ENS_ROW_EXTRA": 29,
    "BRIDGE_DIAGNOSTIC": 24, "BRIDGE_PAIR": 10,
}
MAPS = ("TRAJ", "VNC", "V1", "V0")
OBS = ("A1", "C1", "V2", "f", "D2")
ZERO = ratio(0)


def fail(code):
    raise StopRead(code)


def clean_token(x):
    need(type(x) is str and bool(x) and "|" not in x and "\n" not in x
         and "\r" not in x, "unsafe_hbp_token")
    return x


def identity(row):
    return (
        row["N"], row["delta"], row["y"], row["t"]
    )


def parse_semi(value, valid):
    need(type(value) is str and bool(value), "missing_clause_set")
    components = value.split(";")
    need(len(components) == len(set(components)), "repeated_clause")
    need(all(c in valid for c in components), "unregistered_clause")
    return tuple(components)


def catalogue():
    ats, pts, changed, hold_sha = preflight()
    raw, all_rows = rows(PRED)
    assert len(raw) > 0
    counts = Counter()
    report_counts = Counter()
    extras = Counter()
    ordered = []
    seen = set()
    for number, row in enumerate(all_rows, start=1):
        if row["_tag"] in EXTRA_COUNTS:
            extras[row["_tag"]] += 1
        if row["_tag"] != "BRIDGE_AT":
            continue
        k = key(row)
        need(k not in seen, "duplicate_frozen_BRIDGE_AT")
        seen.add(k)
        applies = parse_semi(row["applies"], APPLICABLE)
        reports = parse_semi(row["read_and_report"], READ_ONLY)
        # The clause may be read on a predicted subset and reported on the
        # complement, but must never be silently omitted.
        need(not (set(applies) & set(reports)), "applies_vs_report_overlap")
        need(row.get("blind") == "1", "lost_blind_flag")
        need(cmp(num(row["t"]), ZERO) > 0,
             "invalid_read_time")
        for c in applies:
            counts[c] += 1
        for c in reports:
            report_counts[c] += 1
        ordered.append((number, row, applies, reports))
    need(len(ordered) == 352 and len(pts) == 28
         and len(ats) == 352 and len(seen) == 352,
         "full_at_coverage")
    need(dict(counts) == EXPECTED_APPLIES, "apply_clause_census_changed")
    need(dict(report_counts) == EXPECTED_REPORTS, "report_clause_census_changed")
    need(dict(extras) == EXTRA_COUNTS, "supplemental_clause_census_changed")
    need(bool(changed) and len(hold_sha) == 64, "amendment_or_hold_missing")
    return ordered, all_rows


def errors(term_text):
    need(type(term_text) is dict and set(term_text) == set(REQUIRED_ERRORS),
         "error_term_names")
    parsed = {k: num(v) for k, v in term_text.items()}
    need(all(cmp(v, ZERO) >= 0 for v in parsed.values()),
         "negative_error_component")
    return parsed


def evaluate(what, evidence):
    """The only numerical gate. No fallback from missing evidence to MET."""
    need(type(evidence) is dict, "bad_evidence_type")
    state = evidence.get("kind", "NOT_MEASURED")
    if state == "NOT_MEASURED":
        reason = evidence.get("reason", "NOT_REACHABLE_FROM_HERE")
        need(reason in MISSING_REASONS, "unsupported_missing_reason")
        need(not any(k in evidence for k in (
            "measured", "predicted", "tol", "errors", "undefined")),
            "missing_record_masquerades_as_measurement")
        return "NOT_MEASURED", reason
    if state == "UNDEFINED":
        need(evidence.get("justification") in (
            "ZERO_FIELD", "NONPOSITIVE_CERTIFIED_C1", "ZERO_DENOMINATOR",
            "TRAJECTORY_AMPLITUDE_NOT_SEPARATED",
        ), "undefined_without_mathematical_reason")
        need(not any(k in evidence for k in (
            "measured", "predicted", "tol", "errors")),
            "undefined_with_numeric_measurement")
        return "UNDEFINED", evidence["justification"]
    need(state == "CERTIFIED_COMPARISON", "unrecognized_comparison_kind")
    need(evidence.get("source_authenticated") is True, "unverified_numeric_source")
    need(evidence.get("identity_frozen") is True, "unmatched_frozen_identity")
    need(evidence.get("source_role") in (
        "QUANTUM", "ENSEMBLE_CV", "ENSEMBLE_PLAIN", "PAIR_COMMON",
        "TRAJECTORY", "JET", "CONTROL", "DIAGNOSTIC",
    ), "unverified_source_role")
    need(set(evidence) == {
        "kind", "source_authenticated", "identity_frozen", "source_role",
        "measured", "predicted", "tol", "errors",
    }, "unexpected_numeric_field")
    measured, predicted, tol = (
        num(evidence["measured"]), num(evidence["predicted"]),
        num(evidence["tol"]),
    )
    es = errors(evidence["errors"])
    need(cmp(tol, ZERO) >= 0, "negative_tol")
    if what == "E_PAIR":
        need(evidence["source_role"] == "PAIR_COMMON", "E_PAIR_unpaired")
        status = pair_verdict(measured, predicted, tol, es)
    else:
        status = verdict(sub(measured, predicted), es, tol)
    return status, "CERTIFIED_NUMERIC"


def default_missing():
    return {"kind": "NOT_MEASURED", "reason": "NOT_REACHABLE_FROM_HERE"}


def predicted_evidence(measured, predicted, tol, *, role="ENSEMBLE_PLAIN",
                       sampling="0", e_int="0", e_round="0",
                       e_q="0", e_trunc="0"):
    """Synthetic constructor only; not an engine adapter."""
    return {
        "kind": "CERTIFIED_COMPARISON", "source_authenticated": True,
        "identity_frozen": True, "source_role": role,
        "measured": measured, "predicted": predicted, "tol": tol,
        "errors": {
            "3SE": sampling, "e_int": e_int, "e_round": e_round,
            "e_q": e_q, "e_trunc": e_trunc,
        },
    }


def summarize_contract():
    ordered, all_rows = catalogue()
    h = hashlib.sha256()
    clause_lines = 0
    obs_lines = 0
    extra_lines = 0
    for line_num, row, applies, reports in ordered:
        for kind, cs in (("APPLIES", applies), ("READ_REPORT", reports)):
            for clause in cs:
                k = identity(row)
                text = (
                    "CONTRACT_CLAUSE|frozen_line=%d|N=%s|delta=%s|y=%s|t=%s|"
                    "section=%s|clause=%s|status=NOT_MEASURED|"
                    "reason=NOT_REACHABLE_FROM_HERE|actual_outputs_opened=0|json=0\n"
                ) % (line_num, *k, kind, clause)
                h.update(text.encode("ascii"))
                clause_lines += 1
        # Requirement R5 explicitly demands every classical map, observable and
        # time, including V2 undefined controls, rather than fewer output rows.
        for name in MAPS:
            for obs in OBS:
                text = (
                    "CONTRACT_EPS|frozen_line=%d|N=%s|delta=%s|y=%s|t=%s|"
                    "classical_map=%s|observable=%s|status=NOT_MEASURED|"
                    "reason=NOT_REACHABLE_FROM_HERE|actual_outputs_opened=0|json=0\n"
                ) % (line_num, *identity(row), name, obs)
                h.update(text.encode("ascii"))
                obs_lines += 1
    for row in all_rows:
        if row["_tag"] not in EXTRA_COUNTS:
            continue
        clean_token(row["_tag"])
        # Use a canonical frozen row hash, not guessed derived measurements.
        fingerprint = hashlib.sha256(
            "|".join("%s=%s" % (k, v) for k, v in row.items()).encode("utf-8")
        ).hexdigest()
        text = (
            "CONTRACT_EXTRA|kind=%s|frozen_record_sha256=%s|"
            "status=NOT_MEASURED|reason=NOT_REACHABLE_FROM_HERE|"
            "actual_outputs_opened=0|json=0\n"
        ) % (row["_tag"], fingerprint)
        h.update(text.encode("ascii"))
        extra_lines += 1
    need(obs_lines == 7040 and extra_lines == sum(EXTRA_COUNTS.values()),
         "contract_coverage_mismatch")
    return (
        "BRIDGE_READER_CONTRACT|frozen_rows=352|"
        "classical_epsilon_slots=%d|clause_slots=%d|supplemental_slots=%d|"
        "contract_sha256=%s|"
        "actual_blind_outputs_opened=0|"
        "status=READ_DISABLED_PENDING_INDEPENDENT_REVIEW|json=0"
    ) % (obs_lines, clause_lines, extra_lines, h.hexdigest())


def selftest():
    ordered, all_rows = catalogue()
    _ = all_rows
    candidates = tuple(dict.fromkeys(c for _, _, ac, rr in ordered for c in ac + rr))
    need(set(candidates) == set(APPLICABLE) | set(READ_ONLY),
         "clause_family_not_tested")
    caught = 0
    exercised = 0
    one = "1"
    z = "0"
    for clause in candidates:
        role = "PAIR_COMMON" if clause == "E_PAIR" else "ENSEMBLE_CV"
        synthetic = (
            ("MET", predicted_evidence(z, z, one, role=role)),
            ("MISS", predicted_evidence("3", z, one, role=role)),
            ("NOT_RESOLVED",
             predicted_evidence(one, z, one, role=role, sampling="1/2")),
            ("UNDEFINED", {
                "kind": "UNDEFINED", "justification": "ZERO_FIELD",
            }),
            ("NOT_MEASURED", default_missing()),
        )
        for expected, e in synthetic:
            # Pair MET cannot be claimed with zero predicted signal; use nonzero
            # expectation and exercise precision gate independently.
            if clause == "E_PAIR" and expected in ("MET", "MISS", "NOT_RESOLVED"):
                e = dict(e, predicted="2", measured={
                    "MET": "2", "MISS": "5", "NOT_RESOLVED": "3"
                }[expected])
                if expected == "NOT_RESOLVED":
                    e["errors"] = dict(e["errors"], **{"3SE": "1/2"})
            result, _ = evaluate(clause, e)
            need(result == expected, "synthetic_verdict_" + clause)
            exercised += 1
        bad = [
            dict(predicted_evidence(z, z, one), source_authenticated=False),
            dict(predicted_evidence(z, z, one), identity_frozen=False),
            dict(predicted_evidence(z, z, one), errors={"3SE": "0"}),
            dict(predicted_evidence(z, z, one), errors={
                "3SE": "-1", "e_int": z, "e_round": z,
                "e_q": z, "e_trunc": z,
            }),
            dict(predicted_evidence(z, z, one), tol="-1"),
            dict(default_missing(), measured=z),
            {"kind": "UNDEFINED", "justification": "NO_REASON"},
        ]
        if clause == "E_PAIR":
            bad.append(predicted_evidence(z, z, one, role="ENSEMBLE_CV"))
        for altered in bad:
            try:
                evaluate(clause, altered)
            except StopRead:
                caught += 1
            else:
                fail("synthetic_sabotage_accepted")
    # Each numeric proof-class clause uses the same immutable rational rule;
    # synthetic tests do not access, generate, or copy any blind output.
    return len(candidates), exercised, caught


def main(argv):
    need(argv in (["--inventory"], ["--selftest"]),
         "READ_DISABLED_ONLY_SYNTHETIC_MODES")
    if argv == ["--inventory"]:
        print(summarize_contract())
    else:
        clauses, comparisons, caught = selftest()
        print("BRIDGE_352_SYNTHETIC|all_clauses=%d|comparisons=%d|"
              "faults_rejected=%d|actual_outputs_opened=0|status=PASS|json=0"
              % (clauses, comparisons, caught))
        print(summarize_contract())
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (StopRead, KeyError, ValueError, TypeError, UnicodeError, OSError) as err:
        print("BRIDGE_352_REFUSED|reason=%s|json=0" % str(err),
              file=sys.stderr)
        sys.exit(3)
