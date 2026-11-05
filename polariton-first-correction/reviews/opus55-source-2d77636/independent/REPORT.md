**Head checked:** `2d776369fbf7448c6adcf3ecce4bcaa2ae792c20`. The worktree is clean after all runs.

No engine ran any grid point or any off-limits delta. At grid parameters I used only `rows` and `bessel` modes, closed forms, and rows marked synthetic.

## Verdict
- **Engine: fit to read the grid.** I found no fault in its matrix, Bessel tables, certificate accounting or read-out bounds. Its only hold is one comment (H14).
- **Stage at this head: not fit.** Two faults in the reader and the route would corrupt the record only after the grid has run:
  - The reader would print `expanding_L` MISS on an estimated 9 of 10 points, from a clause the frozen row does not carry (H2).
  - The route's integrator mode would very likely turn the hosted job red, with no earlier warning (H1, H6).
- **Order before the grid:**
  1. Apply H1, H2 and H6. I recommend the others too.
  2. Regenerate the pins, and refile `READ-BASELINE` (plus the receipt and cost files with H15).
  3. Get a hosted pass, then run the grid.

The row stays untouched by all of this. H2 changes the reader before any grid read.

## What I ran
- **Second seat's `cheb`:** built on Rust 1.81 and driven through `chebdrv.py` with EXE and TABLES overridden. Compared on 13 seen rows, then read the engine's own state with exact roots at N=729, 2187 and 6561.
- **Hosted gate:** read run 42056499947 step by step, then reran the job's steps under WSL Ubuntu 24.04 with Rust 1.81 at parallel 2. Negative probes tested the pins, `cmp` and the process substitution.
- **Bessel:** E=1..3000 at W=6, W from 0 to 40, and the grid's 12 E values against my own exact series.
- **Hamiltonian:** all 20 grid runs in `rows` mode against my own formulas.
- **Certificate:** engine K=1600 and K=2000 at (0, y=1/81), state distance against the full space at N=729, and a port of the certificate floor.
- **Reader:** a dry run of grid mode on synthetic rows.
- **Mutations:** 16 engine mutations on seen rows.
- **Holds:** all 17 applied to a copy, then that workflow's own text run end to end under WSL at parallel 2. The only tested difference from `HOLDS.txt` is one comment.

## What survives (MEASURED unless tagged)
- **The two propagators agree on the state.** Second seat minus an exact-root read of the engine's state, in e-18:

| Row | C1 | A1 | f |
|---|---|---|---|
| N=6561, K=1200 | +1 | +5 | 0 |
| N=2187, K=1000 | +7 | +48 | +4 |
| N=729, K=512 | -2 | +2 | -1 |

- **Receipt fields:** f and C2 meet at 32e-18 or better. At N=6561 the second seat meets the printed C1 within 7e-18 (K=512 to 1600).
- **Bessel at the grid's E:** E runs 1008 to 1333 at W=6.
  - Tables sit within 0.498 units of 2^-62 of exact, and dropped entries stay under 0.484 units.
  - The route's exact series is off by at most 1 unit.
  - No assert or overflow at W=6 for E=1..3000. The checked overflow first appears at W=28.
- **Hamiltonian at all 20 grid runs:** 0 elements off, and E covers a separate Gershgorin bound.
  - The scaled row sum is at most 0.99919.
  - My norm(B) Schur test equals the engine's at K=1200, 1600 and 2000 on the seen point.
- **Certificate against truth at N=729:** eps >= `leak_sum` >= true distance on all 12 rows I read (2 deltas, 6 K). The smallest eps over true is 21. `x_up` and `s_up` are outward by 1.8 to 2.3.
- **Row forms:** the reader's `Forms` and my separate evaluator agree under 1e-30 at 14 points.
- **Hosted gate:**
  - `--locked --offline` work, the no-float grep has 0 hits, and clippy `--all-targets` passes here and in the hosted `ci` job.
  - Each pinned file turns the pins red on one changed byte.
  - `cmp` detects a one-byte change.
  - The process substitution works under `bash -e`, and hosted uses bash.
  - Receipts are the same bytes at parallel 4, 2 and 1, on Linux and Windows. K=1600 is also identical across both.
  - The `cheb` build line works with its manifest path and `CARGO_TARGET_DIR`.
- **Time limit:** about 25 minutes with the grid (DERIVED from hosted K=1200 at 88 s and local K=1600 at 296 s), against 340 minutes.
- **Path filters:** PR #11 triggers this job and `ci`, and no 98-minute polariton job, which is what the PR needs.
- **Errors at K=1600 (CONJECTURE, stated hand argument in F12):**
  - Relative C1 is at most 1.3e-6, A1 at most 2.4e-6, and V2 at most 6e-6, against margins near 9e-4.
  - The error over R6561 is at most 1.4e-2 on the four 30x points.
  - The gap to the 30x threshold is estimated at 4.5e-3 or more.

## What is refuted
1. **Route integrator mode and its 10^-14 limit (MEASURED).** It exits 1 on every seen row I tried.
   - A1_off_e18 is 53459 at N=6561 K=1200, 394272 at N=2187, and up to 1169874 at N=729. C1 reaches 10037 at N=729.
   - The offset is the engine's read-out (`root24`). The energy read shows the same effect: 4.3e-12 printed against 9e-18 exact.
   - The limit is not sharp. It is 2000 times the C1 offset at N=6561 and one fifth of the A1 offset.
   - The mode has never run hosted, because it sits behind the grid's guard.
2. **Reader `low.eps >= r.eps` (MEASURED cause, CONJECTURE count).** eps has a rounding floor that grows with K.
   - At (0, y=1/81) eps is 1.30e-7 at K=1600 and 2.00e-7 at K=2000, while C1 moves 2e-18.
   - At N=2187, delta=1/2, y=1/188, K=1000 gives 2.57e-8 and K=1200 gives 2.89e-8.
   - My port matches the printed `eps_tail` to 1e-18 at K=1600 and 2000, and puts the K=1600 floor above K=1200 on all 10 points.
   - On synthetic rows at the floor, all 10 `expanding_L` rows read MISS and blind reads 0 met, 8 with a miss.
3. **`route_bessel`'s tail check (MEASURED).**
   - Its slack of 1.1e-16 is the size of the printed `eps_poly`.
   - It reads only the printed degree, so it passes on `bessel_short` rows (exit 0).
   - The "table drops" comment has no code behind it.
   - Its reach is coarse but real: a majorant low by 8 turns it red.
4. **Peak memory on hosted (MEASURED).** `rstrip` eats trailing zeros, so `peak_rss_kB=179` is printed for what is evidently 17900.
5. **"Shares nothing, including conventions" (partly refuted, MEASURED).**
   - The route's Python shares nothing with the engine. `cheb` has verbatim `isqrt`, Q, ONE and helpers.
   - Different: basis, windows against one series, rounding, c and E, and the A and B scaling.
   - Shared, so no second route tests them: the operator text of H, K, and the C1 and A1 definitions.
6. **Sensitivity of the certificate checks (MEASURED).**
   - `every_certificate_holds` has about 4500 of room on A1 at K=128, so `tail_bound_over_8` stays green.
   - `b_norm_no_linear` passes every hosted check at this head.
7. **Text.** The README status says the baseline "comes next" although it is filed. The `bessel` comment "within 2^-54" is exceeded by 2659 of 3000 tables, with no fault in them.

## GPT-6's checklist (full mapping in F13)
Items 1 to 7 and the baseline each have a named file and check. These are the gaps:
- **Item 1 and the interval in item 2:** hosted reads N<=40 only. I covered N=6561 here, and hosted it remains an open item.
- **Item 2:** the tail check (H4, H5).
- **Item 6:** sensitivity (H10 to H12, H17).
- **Item 7:** never run on real rows.
- **Baseline:** RSS (H3).

## The frozen row (clause by clause in F14)
Every clause has a reader row, a check or an engine field. K=1200, 1600 and W=6 are consistent with the row. Two points remain:
- The extra eps clause in `expanding_L` (H2).
- K=1600 has no baseline row (H15).

## Holds
Tested together; each OLD occurs once at this head.
- **H1, high,** route: per-row limits from the engine's own read-out account, plus f and C2 at 1e-15. All 18 seen rows then pass, and three sabotages fail.
- **H2, high,** reader: drop `low.eps >= r.eps`, keep eps printed.
- **H3, medium,** `run_stage`: replace `rstrip` with a suffix cut.
- **H4, medium,** route: check `applies == (2 windows - 1) degree` and norm(B).
- **H5, medium,** route: check dropped entries exactly and tighten the tail slack to 2e-18.
- **H6, high,** workflow: run the second seat on seen rows at every head.
- **H7, medium,** workflow: run the route on all grid rows, since the verdict reads at K=1600.
- **H8, medium,** workflow: add the job's inputs to its path filters.
- **H9, low,** `SHA256SUMS`: pin `cheb`, `chebdrv.py`, `RECEIPT.hbp` and the Cargo files.
- **H10, medium,** reader: read `leak_sum` from the row.
- **H11, medium,** reader: add the check `tail_certificate_covers_the_logged_leak`.
- **H12, medium,** `CONTROLS.hbp`: update the expectation for `leak_understated`.
- **H13, low,** README: correct the status line.
- **H14, low,** engine: correct the sum-rule comment.
- **H15, medium,** `PLAN.hbp`: add K=1600 to the seen anchor.
- **H16, low,** README: name what the propagator shares with the engine.
- **H17, medium,** route: add `schur_norm_s20`, which turns `b_norm_no_linear` red.

Not a hold, for the owner to decide: roots at 2^40 on the A and B read-outs cut A1's offset from 53472 to 15 e-18 at N=6561, K=512 in a trial. It changes the receipts, so the baseline would refile.

## What could not be checked (CANNOT_SEE)
- Every grid point, which includes A1_off at y=1/324 and 1/162, the real K=1200 tail, and the residuals. These settle only with the grid run after the holds. If H1 is skipped, a row under 10^4 is possible at small y, but one row over it turns the job red.
- The grid step past its guard on a real receipt. The reader's grid mode has run on synthetic rows only.
- A hosted run of the holds. They ran only under WSL at parallel 2.
- Hosted K=1600 speed, estimated from the K=1200 ratio.
- A later row appended to `PREDICTION.hbp` for the ±3/5 experiment would turn the pins red through the whole-file line. That fails closed; I left it as an open item with no hold.
- I did not ask the Asolaria fabric or recall for this code review. The owning gate I read is the repo's hosted job.

## Files
Everything is in `C:/tmp/opus55/fc-review-independent-20261105/`:
- `FINDINGS.txt`
- `HOLDS.txt`
- `out/` (rows and logs)
- `scripts/`
