# Acceptance gate for count-weighted reuse in twens (cloud seat, 2026-11-08)

This gate is filed before the reuse change exists, so the bar is fixed ahead of the code. It checks one property, and it relies on another.

**Relied on:** twens draws every sample from its own index (derivation seed + index × `0x1000_0000_01B3`). So a sample's contribution to each record does not depend on which batch computed it.

**Checked:** the sums of disjoint index ranges, added together, equal one run over their union. That holds field for field, on every summed row type: `TWB`, `TWB_ROUND`, `TWB_PAIR`, `TWB_PAIR_ROUND`, `TWENS` and `TWPAIR`. Count-weighted reuse must keep this property exactly.

## Files

- `ens_merge_check.py` compares exact integers and fails by name. It has two modes:
  - **union**: `REFERENCE PART…`. Each PART is one disjoint index range, the parts together cover REFERENCE, and their sums add up to REFERENCE's. Each `eps_max` (the per-record rounding bound) must not exceed REFERENCE's.
  - **`--stair REUSE NOREUSE…`**: every summed row of a reuse run must equal the same row of the no-reuse run that has the row's own count `n`, from the same start. This is the expected shape of reuse on the E4R staircase.
- `run_baseline.sh TWENS OUT` runs, on twens 0.3.0 as it stands:
  - both modes;
  - a thread-count invariance check;
  - seven controls, each of which must fail by its named check.
- `BASELINE.out` is this machine's output with binary `75530df9…` (source `main.rs` `723b3674…`). Results:
  - union mode at two points: 1,722 and 2,648 integer fields equal;
  - stair mode: 2,928 fields equal;
  - thread counts 1 and 4: byte-identical;
  - 7 of 7 controls failed by name.

All points used are allowed points (δ = 1/2 and −1/4); no reserved point is run.

## What acceptance of the reuse change needs

These are the operator's five conditions of 2026-11-08:

1. **Toolchain:** Rust 1.81 builds it clean, with tests, `clippy -D warnings` and the no-float scan.
2. **Identity:** `ens_merge_check.py`, in the mode that fits the change, gives `result=EQUAL` on reuse output against the no-reuse engine at the same allowed points. That covers every per-record sum, variant total and sample count.
3. **Negative control:** the change's own planted corruption of a reused count or weight fails by a named check, and so do this gate's controls.
4. **Frozen inputs:** `PREDICTION.hbp` (`fadd8412`), the plan and amendment, and `blind/jets-20261108*` are byte-unchanged.
5. **Hosted CI:** green at the exact final commit.
