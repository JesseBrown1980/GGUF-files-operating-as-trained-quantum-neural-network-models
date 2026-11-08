# Count-weighted reuse on PR #15: the acceptance gate and the landing, November 8, 2026

This folder records how twens 0.4.0 (`memo=1`) was placed on PR #15 and the cloud seat's acceptance gate as run on it before the push.

- **The engine and its review.** The build lane's files are in [`../opus55-count-memo-20261106/`](../opus55-count-memo-20261106/) and the second-seat review, verdict PASS_WITH_HOLDS, in [`../opus55-review-memo-20261108/`](../opus55-review-memo-20261108/). Holds H1–H8 are applied as the review gives them.
- **The rebase.** Both lanes worked on `46b92e8`. PR #15's head `c02c927` holds the jets row as row 18 of `ENGINE-CHANGES.hbp`, so the reuse row lands as row 19 and the file reads `f4f3f794…`. Its review field records the review, as the jets row does. The README and the workflow are three-way merges onto the jets head; [`LANDING.hbp`](LANDING.hbp) gives every file's hashes.
- **The cloud seat's gate** ([`GATE-RUN.hbp`](GATE-RUN.hbp)), at the allowed points N = 81, δ = 1/2, y = 1/18 and N = 729, δ = −1/4, y = 1/27:
  - 0.3.0 reproduces the gate's filed `BASELINE.out` byte for byte, and 0.4.0 plain and with `memo=1` give the same output;
  - union mode `result=EQUAL` on 1,722, 1,722 and 2,648 integer fields across the two engines, staircase mode `EQUAL` on 2,928;
  - the gate's six control rows fail by name on every engine.
- **Planted reuse faults** ([`GATE-RUN-K4.hbp`](GATE-RUN-K4.hbp), [`GATE-RUN-K4BIG.hbp`](GATE-RUN-K4BIG.hbp)):
  - F1, a key that merges two starts, fails as `sum_differs:zr` on a LOCK batch of 20,000 samples;
  - F3, a dropped count in the 4-ball path, fails as `sum_differs:zr` on a V1 batch of 2²² samples, the size at which that path is in use (3,685,002 distinct starts);
  - the correct engine reads `EQUAL` on both batches.
- **The driver.** `PLAN-BLIND.hbp` reads `3eca4df9…`: the build lane's proposal with the head's `ENGINE-CHANGES` pin set to `f4f3f794…`. The change record is in [`driver/`](driver/). The dry run accepts 347 of 347 ensemble launches, each running `twens-33e62fbe0837aedd` with `memo=1`, and the plan's total work is unchanged at 94353772847/16.
- **Frozen inputs** read the same as before: PREDICTION `fadd8412…`, the F amendment `60c403d3…`, CORRECTIONS `9bfdd27d…`, and every file under `blind/`.

The scripts that produced these rows are in [`tools/`](tools/).
