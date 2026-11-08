# Acceptance gate for count-weighted reuse in twens (cloud seat, 2026-11-08)

This gate is filed before the reuse change exists, so the bar is fixed ahead of the code. It checks one property, and it relies on another.

**Relied on:** twens draws every sample from its own index (derivation seed + index × `0x1000_0000_01B3`). So a sample's contribution to each record does not depend on which batch computed it.

**Checked:** the sums of disjoint index ranges, added together, equal one run over their union. That holds field for field, on every summed row type: `TWB`, `TWB_ROUND`, `TWB_PAIR`, `TWB_PAIR_ROUND`, `TWENS` and `TWPAIR`. Count-weighted reuse must keep this property exactly.

## Files

- `ens_merge_check.py` compares exact integers and fails by name. It has two modes:
  - **union**: `REFERENCE PART…`. Each PART is one disjoint index range, the parts together cover REFERENCE, and their sums add up to REFERENCE's. Each `eps_max` (the per-record rounding bound) must not exceed REFERENCE's.
  - **`--stair REUSE NOREUSE…`**: every summed row of a reuse run must equal the same row of the no-reuse run that has the row's own count `n`, from the same start. REUSE must carry exactly the references' row set, and every reference count must be used. This is the expected shape of reuse on the E4R staircase.
- `run_baseline.sh TWENS OUT` runs, on twens 0.3.0 as it stands:
  - both modes;
  - a thread-count invariance check;
  - ten controls, each of which must fail by its named check.
- `BASELINE.out` is this machine's output with binary `75530df9…` (source `main.rs` `723b3674…`). Results:
  - union mode at two points: 1,722 and 2,648 integer fields equal;
  - stair mode: 2,928 fields equal;
  - thread counts 1 and 4: byte-identical;
  - 10 of 10 controls failed by name.

## Correction of 2026-11-08

Cloud C (GPT-6) found on PR #15 that the first version of `--stair` (`81e5b962…`) read `result=EQUAL` on a reuse file with one real row deleted, because it never checked that the reuse file's rows were complete. Union mode had a smaller gap of the same kind: a part with no `TWB_NL` rows passed. Both are reproduced here on the first version: the deleted-row staircase read `rows=113` and EQUAL, and the part without NL rows read EQUAL.

This version refuses both. `--stair` now fails as `stair_row_set_differs` on a missing or extra row, `stair_reference_unused` on a reference count no row uses, `stair_reference_row_sets_differ` and `stair_reference_count_repeated` on inconsistent references, and `job_fields_differ` on different `steps` or `mask`. Union mode fails as `nl_rows_differ` when any part's NL rows differ from the reference's, including when they are missing.

`run_baseline.sh` gains three controls for these cases, so `BASELINE.out` gains three rows just before `BASE_DONE`; its other 11 rows are byte-identical to the first `BASELINE.out` (`4daf841d…`). twens 0.3.0 (`75530df9…`), 0.4.0 (`33e62fbe…`) and 0.4.0 with `memo=1` all give this file byte for byte. The engine was never at fault: the reuse change's own plain-against-memo byte comparison already protected against a missing row.

All points used are allowed points (δ = 1/2 and −1/4); no reserved point is run.

## What acceptance of the reuse change needs

These are the operator's five conditions of 2026-11-08:

1. **Toolchain:** Rust 1.81 builds it clean, with tests, `clippy -D warnings` and the no-float scan.
2. **Identity:** `ens_merge_check.py`, in the mode that fits the change, gives `result=EQUAL` on reuse output against the no-reuse engine at the same allowed points. That covers every per-record sum, variant total and sample count.
3. **Negative control:** the change's own planted corruption of a reused count or weight fails by a named check, and so do this gate's controls.
4. **Frozen inputs:** `PREDICTION.hbp` (`fadd8412`), the plan and amendment, and `blind/jets-20261108*` are byte-unchanged.
5. **Hosted CI:** green at the exact final commit.
