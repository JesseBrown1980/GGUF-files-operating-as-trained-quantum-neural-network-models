#!/usr/bin/env python3
"""Pure schema adapters for SOURCE engine output, with no file-reading CLI.

Consume ONLY bytes supplied after the reader has been frozen/reviewed.
No model computations or access to actual blind outputs in this module.
"""
from gpt6_read_core import StopRead, need, fields, num, ratio, cmp

TWB_NUMERIC = ("n", "zr", "zi", "dzr", "dzi", "xw", "dxw", "xnc", "dxnc",
               "f", "qdzr", "qdxw", "qdxnc", "qzr", "qxw", "qxnc", "qdzi",
               "f2", "br", "bi", "br2", "bi2", "brbi", "zrxw", "zrxnc",
               "dzrdxw", "dzrdxnc", "zr2", "zi2", "dzr2", "dzi2",
               "xw2", "dxw2", "xnc2")
FIXED_ROUND = tuple("rb_" + key for key in TWB_NUMERIC if key != "n")
QUANTUM_E18 = ("jbar_e18", "f_e18", "A_e18", "B_e18", "C1_e18",
               "C2_e18", "A1_e18", "D2_e18", "V2_e18",
               "energy_e18", "norm_off_e18", "eps_tail_e18",
               "eps_poly_e18", "eps_round_e18", "eps_e18",
               "C1_err_e18", "A1_err_e18", "V2_lo_e18", "V2_hi_e18",
               "tail_max_e18", "leak_max_e18", "leak_sum_e18")
QSCALE = 10**18


def parse_rows(source):
    need(type(source) is bytes and source.endswith(b"\n") and b"\r" not in source,
         "raw_output_lf")
    out = []
    for line in source.decode("utf-8").splitlines():
        need(line and line.split("|")[0] in (
            "TWB_HEAD", "TWB", "TWB_ROUND", "TWB_PAIR", "TWB_PAIR_ROUND",
            "TWB_NL", "TWB_DONE", "TWENS", "TWPAIR",
            "POLARITON_FIRST_CORRECTION_READ", "TRAJ_BOUND", "TRAJ_OBS_BOUND",
            "JR_HEAD", "JR_OBS", "JR_PAIR", "JR_GATES", "JR_END",
        ), "unknown_raw_row_type")
        out.append(fields(line))
    need(bool(out), "raw_output_empty")
    return out


def _same(a, b, ks):
    need(all(a.get(k) == b.get(k) for k in ks), "raw_metadata_mismatch")


def validate_ensemble(batch, *, required_pair=False):
    """Validate source-internal coherence, not completeness of all 347 launches."""
    need(bool(batch) and batch[0]["_tag"] == "TWB_HEAD", "missing_TWB_HEAD")
    head = batch[0]
    need(batch[-1]["_tag"] == "TWB_DONE", "missing_TWB_DONE")
    need(head.get("guard") == "lifted" and head.get("float_used") == "0",
         "ensemble_guard_or_arithmetic")
    for k in ("N", "delta", "y", "seed", "start", "count", "dtden", "steps",
              "mask", "source_sha256", "binary_sha256"):
        need(k in head, "head_missing_" + k)
    count, start = int(head["count"]), int(head["start"])
    need(count > 0 and start >= 0, "batch_invalid_range")
    need(int(head["dtden"]) in (64, 128), "batch_time_step")
    need(int(head["N"]) in (81, 729, 6561), "batch_N")
    need(head.get("u") == "1", "batch_coupling")
    need(int(head["samples"]) == count, "batch_samples")
    steps = head["steps"].split(",")
    need(len(set(steps)) == len(steps) and all(int(t) >= 0 for t in steps),
         "batch_steps")
    bases = ("N", "delta", "y", "seed", "start", "count", "dtden")
    seen = set()
    normals = {}
    partners = {}
    for row in batch[1:-1]:
        tag = row["_tag"]
        if tag not in ("TWB", "TWB_ROUND", "TWB_PAIR",
                       "TWB_PAIR_ROUND", "TWB_NL", "TWENS", "TWPAIR"):
            raise StopRead("unknown_ensemble_row")
        if tag in ("TWENS", "TWPAIR", "TWB_NL"):
            continue   # Legacy/one-shot streams cannot substitute for TWB source.
        _same(head, row, bases)
        need(row.get("float_used") == "0", "ensemble_row_arithmetic")
        need(row["step"] in steps, "ensemble_row_time")
        need(int(row["n"]) == count, "ensemble_row_count")
        if tag in ("TWB", "TWB_ROUND"):
            need("variant" in row, "missing_variant")
            key = (tag, row["step"], row["variant"])
            need(key not in seen, "duplicate_variant_row")
            seen.add(key)
            if tag == "TWB":
                for nm in TWB_NUMERIC:
                    need(nm in row, "TWB_missing_" + nm)
                    int(row[nm])
                normals[(row["step"], row["variant"])] = row
            else:
                for nm in FIXED_ROUND:
                    need(nm in row and int(row[nm]) >= 0,
                         "TWB_ROUND_missing_" + nm)
                need(int(row["eps_max"]) >= 0, "TWB_ROUND_eps")
        if tag in ("TWB_PAIR", "TWB_PAIR_ROUND"):
            need("pair" in row, "missing_pair_id")
            key = (tag, row["step"], row["pair"])
            need(key not in seen, "duplicate_pair_row")
            seen.add(key)
            if tag == "TWB_PAIR":
                for nm in ("d", "qd", "d2"):
                    int(row[nm])
                partners[(row["step"], row["pair"])] = row
            else:
                for nm in ("rb_d", "rb_qd", "rb_d2"):
                    need(int(row[nm]) >= 0, "pair_negative_round")
    for step, var in normals:
        need(("TWB_ROUND", step, var) in seen, "missing_variant_round")
    for step, pair in partners:
        need(("TWB_PAIR_ROUND", step, pair) in seen, "missing_pair_round")
    need(normals or partners, "no_batch_measurement")
    if required_pair:
        need(any(pair == "V1xw-VNCxnc" for _, pair in partners), "no_E_PAIR_source")
    need(int(batch[-1]["n"]) == count, "done_count")
    return (head, normals, partners)


def validate_quantum(row, point):
    need(row["_tag"] == "POLARITON_FIRST_CORRECTION_READ",
         "quantum_wrong_source")
    need(row.get("float_used") == "0", "quantum_float")
    for k in ("N", "K", "delta", "y", "t"):
        need(k in row, "quantum_missing_" + k)
    need(int(row["N"]) == int(point["N"]), "quantum_N")
    need(num(row["delta"]) == num(point["delta"]) and
         num(row["y"]) == num(point["y"]) and
         num(row["t"]) == num(point["t"]), "quantum_wrong_point")
    k, n = int(row["K"]), int(row["N"])
    need(0 < k <= n, "quantum_bad_truncation")
    for field in QUANTUM_E18:
        need(field in row, "quantum_missing_" + field)
        int(row[field])
    for field in ("eps_tail_e18", "eps_poly_e18", "eps_round_e18",
                  "eps_e18", "C1_err_e18", "A1_err_e18"):
        need(int(row[field]) >= 0, "quantum_negative_error")
    need(int(row["eps_e18"]) >=
         int(row["eps_poly_e18"]) + int(row["eps_round_e18"]),
         "quantum_error_budget_incomplete")
    if k == n:
        need(int(row["eps_tail_e18"]) == 0, "full_space_nonzero_tail")
    # K<N cannot be read without an independently checked energy-shell
    # tail/paired-K comparison, handled by the eventual full read adapter.
    else:
        raise StopRead("quantum_shell_gate_not_independently_verified")
    if point["y"] == "0":
        need(int(row["A1_e18"]) == 0 and int(row["D2_e18"]) == 0,
             "quantum_zero_field_observables")
    return row


def source_selftest():
    head = ("TWB_HEAD|engine=twens|version=0.4.0|cli=run|binary_sha256=abc"
            "|source_sha256=def|N=81|delta=3/5|u=1|y=1/27|seed=7|"
            "start=0|count=2|samples=2|dtden=64|threads=1|steps=32|"
            "mask=VNC,V1|reserved=1|guard=lifted|float_used=0|json=0")
    base = ("N=81|delta=3/5|y=1/27|seed=7|start=0|count=2|"
            "dtden=64|step=32")
    dims = "|".join(x + "=0" for x in TWB_NUMERIC if x != "n")
    t = "TWB|" + base + "|variant=VNC|n=2|" + dims + "|float_used=0|json=0"
    rb = ("TWB_ROUND|" + base + "|variant=VNC|n=2|"
          + "|".join(k + "=0" for k in FIXED_ROUND)
          + "|eps_max=0|float_used=0|json=0")
    pair = ("TWB_PAIR|" + base + "|pair=V1xw-VNCxnc|n=2|d=0|qd=0"
            "|d2=0|float_used=0|json=0")
    pround = ("TWB_PAIR_ROUND|" + base + "|pair=V1xw-VNCxnc|n=2|"
              "rb_d=0|rb_qd=0|rb_d2=0|float_used=0|json=0")
    done = "TWB_DONE|n=2|records=1|mask=VNC,V1|float_used=0|json=0"
    entries = [head, t, rb, pair, pround, done]
    validate_ensemble([fields(s) for s in entries], required_pair=True)
    faults = [
        [head, t, pair, pround, done],       # missing round
        [head, t, rb, pair, done],           # missing paired round
        [head, t, rb, pair, pair, pround, done],  # duplicate
        [head.replace("guard=lifted", "guard=active"), t, rb, pair, pround, done],
        [head, t.replace("count=2", "count=3"), rb, pair, pround, done],
        [head, t.replace("n=2", "n=3"), rb, pair, pround, done],
        [head, t, rb, pair.replace("pair=V1xw-VNCxnc", "pair=V1xw-VNCxw"),
         pround.replace("pair=V1xw-VNCxnc", "pair=V1xw-VNCxw"), done],
        [head, t, rb.replace("rb_f=0", "rb_f=-1"), pair, pround, done],
    ]
    rejected = 0
    for v in faults:
        try:
            validate_ensemble([fields(s) for s in v], required_pair=True)
        except (StopRead, KeyError, ValueError):
            rejected += 1
    need(rejected == len(faults), "source_fault_suite")
    return rejected
