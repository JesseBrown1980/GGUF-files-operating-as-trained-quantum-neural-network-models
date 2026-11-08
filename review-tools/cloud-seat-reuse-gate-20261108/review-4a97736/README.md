# The cloud seat's review of twens 0.4.0 (`memo=1`) at PR #15 head `4a97736`

This folder records the reuse review, run on the cloud seat on 2026-11-08 against twens 0.3.0 at allowed points only. Unlike the gate's baseline, these batches are large enough to put the reuse path in use: K4 from 2²² samples, K2 from 2¹⁰.

- `review_run.sh` is the script that was run. It expects a `bin/` beside it holding `twens03` (`75530df9…`), `twens04` (`33e62fbe…`) and the five `mut-*` binaries, and a copy of this gate under `gate/`. It writes `run/REVIEW.hbp`.
- `REVIEW.hbp` holds its 29 rows:
  - the binaries' hashes and the guard's verdict on each point;
  - the hosted workflow's four batches, rerun here;
  - the new batches E1–E3;
  - the five planted faults;
  - the correct engine's comparison.
- `REVIEW-NEWCMP.hbp` repeats the union comparisons with the fixed comparator (this folder's `../ens_merge_check.py`). The results are unchanged.
- `make_mutants.py` makes the five planted faults from `main.rs` `1d768fa9…`:
  - N1 and N2 add one to a reused weight;
  - N5 and N7 drop a count;
  - N6 flips the sign of c3 when a K4 key is rebuilt.

All five are refused by a named check. N1, N2 and N6 fail the comparator as `sum_differs`. N5 and N7 make the engine stop with `TWB_FAULT reason=memo_count_check` and exit 6.
