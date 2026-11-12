#!/usr/bin/env python3
"""Gate source-native quantum, trajectory and jet schemas without blind read.

A production blind read MUST first authenticate a full exact artifact sha256
against the independently frozen output inventory. That permission is absent:
this module has only --selftest and does NOT load a single output path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpt6_read_core import StopRead, need, num, ratio, cmp, canon_int, fields
from gpt6_source_schema import validate_quantum, parse_rows

ZERO = ratio(0)
GATES = ("G_TRUNC", "G_FALL", "G_ODD", "G_CONS", "G_PAIR")


def certified_num(value, what):
    x = num(value)
    need(cmp(x, ZERO) >= 0, "negative_certification_" + what)
    return x


def quantum_route(row, point, route, *, authenticated=False):
    """No K=N substitution for a planned shell branch without authorization."""
    need(authenticated is True, "unverified_quantum_source_sha")
    need(route in ("FROZEN_PLANNED_FULL", "SHELL_VERIFIED",
                   "AUTHORIZED_FULL_FALLBACK"), "quantum_route_unknown")
    n = canon_int(point["N"], positive=True)
    delta = num(point["delta"])
    planned = point.get("quantum", "")
    if "full_exchange_even_space_K=N" in planned:
        need(route == "FROZEN_PLANNED_FULL", "unexpected_full_route_change")
        need(canon_int(row["K"], positive=True) == n, "planned_full_k_mismatch")
    else:
        need(n == 6561 and delta == ratio(-3, 5),
             "unrecognized_shell_point")
        # This program has no approved independent certificate for the
        # negative-delta K_shell+411 or K=N fallback. Even K=N must not
        # become accepted by merely editing its untrusted source metadata.
        raise StopRead("quantum_shell_route_HOLD_owner_and_bounds_not_authenticated")
    return validate_quantum(row, point)


def trajectory_bounds(items, point, *, authenticated=False):
    """Validate bound rows only; they do not themselves supply observations."""
    need(authenticated is True, "unverified_trajectory_artifact_sha")
    rows = parse_rows(items)
    need(len(rows) == 2 and {x["_tag"] for x in rows}
         == {"TRAJ_BOUND", "TRAJ_OBS_BOUND"}, "trajectory_missing_bound_pair")
    b = next(x for x in rows if x["_tag"] == "TRAJ_BOUND")
    ob = next(x for x in rows if x["_tag"] == "TRAJ_OBS_BOUND")
    for row in (b, ob):
        need(row.get("float_used") == "0"
             and row.get("order") == "28"
             and row.get("h") == "1/32"
             and row.get("fixed_point") == "2^-256"
             and row.get("reserved_open") == "1", "trajectory_model_or_guard_drift")
        need(all(k in row for k in ("delta", "y", "t", "steps", "half_step")),
             "trajectory_incomplete_identity")
        for name in ("delta", "y", "t"):
            need(num(row[name]) == num(point[name]), "trajectory_point_mismatch")
        need(row["steps"] == b["steps"] and
             row["half_step"] == b["half_step"], "trajectory_step_mismatch")
    need(ob.get("N") == point["N"], "trajectory_wrong_N")
    for name in ("state_err_2norm_le", "R_now_le", "f_err_le",
                 "A_over_N_err_le", "A1_err_le", "C1_err_le",
                 "X_err_le", "D2_err_le", "D2sq_err_le",
                 "V2_identity_err_le"):
        need(name in ob, "trajectory_missing_" + name)
        certified_num(ob[name], name)
    for name in ("state_err_2norm_le", "max_horner_part_le",
                 "mu_g_le", "mu_p_le", "R_p_le", "R_now_le"):
        need(name in b, "trajectory_missing_" + name)
        certified_num(b[name], name)
    need(cmp(num(ob["state_err_2norm_le"]),
             num(b["state_err_2norm_le"])) >= 0,
         "trajectory_state_bound_weakened")
    return ob


def jet_contract(items, frozen_plan, *, authenticated=False):
    """Validate every status/source identity; never substitute a failed jet."""
    need(authenticated is True, "unverified_jet_sha")
    raw = parse_rows(items)
    need(raw[0]["_tag"] == "JR_HEAD" and raw[-1]["_tag"] == "JR_END",
         "jet_wrong_row_order")
    heads = [r for r in raw if r["_tag"] == "JR_HEAD"]
    gates = [r for r in raw if r["_tag"] == "JR_GATES"]
    ends = [r for r in raw if r["_tag"] == "JR_END"]
    need(len(heads) == len(gates) == len(ends) == 1,
         "jet_duplicate_or_missing_key_record")
    h, gate, end = heads[0], gates[0], ends[0]
    need(all(k in h for k in (
        "row", "N", "delta", "y", "t", "step64", "step128",
        "plan_sha256", "reader_sha256", "jet_sha256",
        "eint_jet_sha256", "binary_sha256", "mode", "P", "q"
    )), "jet_missing_verified_head_fields")
    need(h["mode"] == "blind", "jet_wrong_run_role")
    need(frozen_plan.get("plan_sha256") == h["plan_sha256"],
         "jet_not_bound_to_frozen_plan")
    need(frozen_plan.get("row") == h["row"], "jet_wrong_plan_row")
    for k in ("N", "delta", "y", "t"):
        need(num(h[k]) == num(frozen_plan[k]), "jet_wrong_point_" + k)
    need(h["row"] == gate.get("row") == end.get("row"),
         "jet_row_sequence_mismatch")
    need(end.get("float_used") == "0" and
         canon_int(end["rows"], positive=True) == len(raw),
         "jet_bad_end")
    for name in GATES + (("G_ZERO",) if num(h["y"]) == ZERO else ()):
        need(name in gate, "jet_missing_" + name)
        need(gate[name] == "pass" or gate[name].startswith("fail:"),
             "jet_bad_gate_decision")
    should_be_ready = all(gate[k] == "pass" for k in
                          GATES + (("G_ZERO",) if num(h["y"]) == ZERO else ()))
    need(gate.get("status") == (
        "JET_READY" if should_be_ready else "JET_NOT_RESOLVED"
    ), "jet_status_inconsistent")
    observations = [r for r in raw if r["_tag"] == "JR_OBS"]
    needs = ("VNC", "V1")
    need(all(any(o.get("variant") == v for o in observations)
             for v in needs), "jet_missing_variant")
    for row in observations:
        need(row.get("row") == h["row"] and
             row.get("law") == "engine", "jet_observable_not_bound")
        need(row.get("variant") in needs and row.get("obs") in
             ("A1", "C1", "V2", "f", "D2", "ZR"),
             "jet_unexpected_observable")
        if row["obs"] == "V2" and num(h["y"]) == ZERO:
            need(row.get("value_P") == "UNDEFINED", "jet_zero_V2")
        else:
            for col in ("value_P", "T_P", "Trel_P", "e_int"):
                need(col in row and row[col] != "NA",
                     "jet_missing_numeric_" + col)
                certified_num(row[col], col) if col != "value_P" else num(row[col])
    return ("JET_READY" if should_be_ready else "JET_NOT_RESOLVED",
            len(observations))


def _as_bytes(lines):
    return ("\n".join(lines) + "\n").encode("ascii")


def selftest():
    point = {"N": "81", "delta": "3/5", "y": "1/27", "t": "1/2",
             "quantum": "full_exchange_even_space_K=N"}
    # Route authentication is a separate gate, not a source-field assertion.
    q = {
        "_tag": "POLARITON_FIRST_CORRECTION_READ", "N": "81", "K": "81",
        "delta": "3/5", "y": "1/27", "t": "1/2", "float_used": "0",
    }
    # Source schema requires the complete set even for a successful route.
    from gpt6_source_schema import QUANTUM_E18
    q.update({k: "0" for k in QUANTUM_E18})
    assert quantum_route(q, point, "FROZEN_PLANNED_FULL",
                         authenticated=True) is q
    good_t = [
        "TRAJ_BOUND|delta=3/5|y=1/27|t=1/2|order=28|h=1/32|fixed_point=2^-256|"
        "steps=16|half_step=0|state_err_2norm_le=1e-9|"
        "max_horner_part_le=0|mu_g_le=0|mu_p_le=0|R_p_le=1|R_now_le=1|"
        "reserved_open=1|float_used=0|json=0",
        "TRAJ_OBS_BOUND|delta=3/5|y=1/27|t=1/2|N=81|order=28|"
        "h=1/32|fixed_point=2^-256|steps=16|half_step=0|"
        "state_err_2norm_le=1e-9|R_now_le=1|f_err_le=1e-9|"
        "A_over_N_err_le=1e-9|A1_err_le=1e-9|C1_err_le=1e-9|"
        "X_err_le=1e-9|D2_err_le=1e-9|D2sq_err_le=1e-9|"
        "V2_identity_err_le=1e-9|reserved_open=1|float_used=0|json=0",
    ]
    assert trajectory_bounds(_as_bytes(good_t), point,
                             authenticated=True)["N"] == "81"
    point_shell = dict(point, N="6561", delta="-3/5",
                       quantum="energy_shell_block_or_authorized_full_fallback")
    blocked = 0
    for fn in (
        lambda: quantum_route(q, point, "FROZEN_PLANNED_FULL",
                              authenticated=False),
        lambda: quantum_route(dict(q, N="6561", K="6561", delta="-3/5"),
                              point_shell, "FROZEN_PLANNED_FULL",
                              authenticated=True),
        lambda: trajectory_bounds(_as_bytes(good_t), point,
                                  authenticated=False),
        lambda: trajectory_bounds(_as_bytes([
            good_t[0], good_t[1].replace("reserved_open=1", "reserved_open=0")
        ]), point, authenticated=True),
        lambda: trajectory_bounds(_as_bytes([
            good_t[0], good_t[1].replace("C1_err_le=1e-9",
                                      "C1_err_le=-1")
        ]), point, authenticated=True),
        lambda: jet_contract(b"", {}, authenticated=False),
    ):
        try:
            fn()
        except (StopRead, ValueError, KeyError, TypeError):
            blocked += 1
    need(blocked == 6, "source_route_sabotage")
    print("BRIDGE_SOURCE_CONTRACT|planned_full_K=N_verified=PASS|"
          "unapproved_shell_fallback_refused=PASS|"
          "trajectory_bound_pair=PASS|"
          "sabotages_rejected=%d|blind_outputs_opened=0|status=PASS|json=0"
          % blocked)


if __name__ == "__main__":
    try:
        need(sys.argv == [sys.argv[0], "--selftest"], "BLIND_READ_DISABLED")
        selftest()
    except (StopRead, ValueError, KeyError, TypeError, OSError) as exc:
        print("BRIDGE_SOURCE_REFUSED|reason=%s|json=0" % str(exc),
              file=sys.stderr)
        sys.exit(3)
