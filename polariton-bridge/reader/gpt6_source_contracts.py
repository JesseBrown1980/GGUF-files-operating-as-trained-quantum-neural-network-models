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


def jet_rows(source):
    """Full jetread.py source grammar, including conservation and sign rows."""
    need(type(source) is bytes and source.endswith(b"\n")
         and b"\r" not in source, "jet_raw_output_lf")
    allowed = ("JR_HEAD", "JR_OBS", "JR_SIGN", "JR_PAIR",
               "JR_CONS", "JR_GATES", "JR_END")
    items = [fields(line) for line in source.decode("utf-8").splitlines()]
    need(items and all(x["_tag"] in allowed for x in items),
         "jet_raw_unknown_or_empty_row")
    return items


def jet_contract(items, frozen_plan, *, authenticated=False):
    """Validate every status/source identity; never substitute a failed jet."""
    need(authenticated is True, "unverified_jet_sha")
    raw = jet_rows(items)
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
    want = ("C1", "f", "V2") if num(h["y"]) == ZERO else (
        "C1", "A1", "V2", "f", "D2", "ZR"
    )
    need(len(observations) == len(want) * 2, "jet_observable_census")
    for variant in needs:
        need({r.get("obs") for r in observations
              if r.get("variant") == variant} == set(want),
             "jet_missing_or_duplicate_observable")
    signs = [r for r in raw if r["_tag"] == "JR_SIGN"]
    need(len(signs) == (0 if num(h["y"]) == ZERO else 2),
         "jet_sign_census")
    need(all(r.get("variant") in needs and
             r.get("E_Re_Z_sign") in ("+", "-", "0") and
             r.get("row") == h["row"] for r in signs),
         "jet_sign_bad")
    need({r["variant"] for r in signs} ==
         (set() if num(h["y"]) == ZERO else set(needs)),
         "jet_sign_variant_missing")
    pairs = [r for r in raw if r["_tag"] == "JR_PAIR"]
    cons = [r for r in raw if r["_tag"] == "JR_CONS"]
    need(len(pairs) == len(cons) == 1, "jet_pair_cons_census")
    need(pairs[0].get("row") == h["row"]
         and pairs[0].get("what") == "N^2*(C1_V1-C1_VNC)"
         and cons[0].get("row") == h["row"],
         "jet_pair_cons_identity")
    for name in ("value_P", "T_P", "T_P_over_absP"):
        need(name in pairs[0], "jet_pair_missing_" + name)
        certified_num(pairs[0][name], name) if name != "value_P" else num(pairs[0][name])
    need(cons[0].get("t0_exact") in ("0", "1"), "jet_conservation_flag")
    for row in observations:
        need(row.get("row") == h["row"] and
             row.get("law") == "engine", "jet_observable_not_bound")
        need(row.get("variant") in needs and row.get("obs") in
             ("A1", "C1", "V2", "f", "D2", "ZR"),
             "jet_unexpected_observable")
        if row["obs"] == "V2" and num(h["y"]) == ZERO:
            need(row.get("value_P") == "UNDEFINED", "jet_zero_V2")
        else:
            for col in ("value_P", "T_P", "e_int"):
                need(col in row and row[col] != "NA",
                     "jet_missing_numeric_" + col)
                certified_num(row[col], col) if col != "value_P" else num(row[col])
            # A zero observable can legitimately print an undefined relative
            # error. The absolute errors must still be present and nonnegative.
            need("Trel_P" in row, "jet_missing_relative_diagnostic")
            if row["Trel_P"] != "NA":
                certified_num(row["Trel_P"], "Trel_P")
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
    # A synthetic complete positive-y jetread record, including JR_SIGN,
    # JR_PAIR and JR_CONS, never a reserved-point measurement.
    plan_digest = "a" * 64
    frozen_plan = {"row": "L0481", "plan_sha256": plan_digest,
                   "N": "81", "delta": "3/5", "y": "1/27", "t": "1/2"}
    jr = [
        ("JR_HEAD|mode=blind|row=L0481|N=81|delta=3/5|y=1/27|t=1/2|"
         "step64=32|step128=64|plan_sha256=%s|reader_sha256=%s|"
         "jet_sha256=%s|eint_jet_sha256=%s|binary_sha256=%s|"
         "P=10|q=64|json=0") % ((plan_digest,) * 5),
    ]
    for var in ("VNC", "V1"):
        for obs in ("C1", "A1", "V2", "f", "D2", "ZR"):
            jr.append("JR_OBS|row=L0481|variant=%s|obs=%s|law=engine|"
                      "value_P=1/2|T_P=1e-8|Trel_P=2e-8|"
                      "e_int=1e-8|json=0" % (var, obs))
        jr.append("JR_SIGN|row=L0481|variant=%s|E_Re_Z_sign=+|json=0" % var)
    jr.extend((
        "JR_PAIR|row=L0481|what=N^2*(C1_V1-C1_VNC)|"
        "value_P=1|T_P=1e-8|T_P_over_absP=1e-8|json=0",
        "JR_CONS|row=L0481|t0_exact=1|json=0",
        "JR_GATES|row=L0481|G_TRUNC=pass|G_FALL=pass|G_ODD=pass|"
        "G_CONS=pass|G_PAIR=pass|status=JET_READY|json=0",
    ))
    jr.append("JR_END|row=L0481|rows=%d|float_used=0|json=0" % (len(jr) + 1))
    assert jet_contract(_as_bytes(jr), frozen_plan,
                        authenticated=True) == ("JET_READY", 12)
    not_ready = [
        x.replace("G_PAIR=pass", "G_PAIR=fail:pair_T_P").replace(
            "status=JET_READY", "status=JET_NOT_RESOLVED")
        if x.startswith("JR_GATES|") else x for x in jr
    ]
    assert jet_contract(_as_bytes(not_ready), frozen_plan,
                        authenticated=True) == ("JET_NOT_RESOLVED", 12)
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
        lambda: jet_contract(_as_bytes(jr), dict(frozen_plan, plan_sha256="b" * 64),
                             authenticated=True),
        lambda: jet_contract(_as_bytes(jr[0:2] + jr[3:]), frozen_plan,
                             authenticated=True),
        lambda: jet_contract(_as_bytes([
            x.replace("status=JET_READY", "status=JET_NOT_RESOLVED")
            if x.startswith("JR_GATES|") else x for x in jr
        ]), frozen_plan, authenticated=True),
        lambda: jet_contract(_as_bytes([
            x.replace("JR_SIGN|", "JR_WEIRD|")
            if x.startswith("JR_SIGN|") else x for x in jr
        ]), frozen_plan, authenticated=True),
    ):
        try:
            fn()
        except (StopRead, ValueError, KeyError, TypeError):
            blocked += 1
    need(blocked == 10, "source_route_sabotage")
    print("BRIDGE_SOURCE_CONTRACT|planned_full_K=N_verified=PASS|"
          "unapproved_shell_fallback_refused=PASS|"
          "trajectory_bound_pair=PASS|jet_all_12_observables=PASS|"
          "jet_failed_gate_stays_not_resolved=PASS|"
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
