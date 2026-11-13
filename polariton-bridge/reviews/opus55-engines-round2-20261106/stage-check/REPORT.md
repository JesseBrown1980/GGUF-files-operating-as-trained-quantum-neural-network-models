# Stage check: the ensemble engine holds H1 to H7 and the merged stage (opus55, November 6, 2026)

Lane folder `C:/tmp/opus55/bridge-engine-final-stage-20261106/`. Base `a12f856`, archived with `core.autocrlf=false`: the
worktree's Windows git has `core.autocrlf=true`, which writes CRLF into 232 files of an archive, and the LF archive equals
the committed blobs. Every run was at an allowed point. Tags: MEASURED (a number from a named run in the lane folder),
DERIVED (from reading the code, or an exact argument), CANNOT_SEE.

## Verdict on H1 to H7: PASS

- MEASURED: H1 to H7 of the ensemble review's HOLDS-REVIEW2.txt, applied by this lane's script with each OLD once on
  e5682f1d, give `src/main.rs` 723b36745af6c926849ff7a6da74d8c82007dfc4071761795bb639fcd8d4a609, the review's measured source.
- MEASURED, Rust 1.81.0 on Windows (MSVC, /Brepro) and on WSL Ubuntu: `fmt -- --check` 0, `clippy --release -- -D warnings`
  0, the same with `--all-targets` 0, `test --release` 14 of 14, build 0. Windows binary
  ac7ff8f41279f55a57f5c47823950c225c8aa111573f52832d52bd6a0e5ca44f and Linux binary
  75530df9c7414b9a1b28f7408cbacd512f35d48836e2a6823beefb4941b9598d, each equal to the review's, built at a new path (the
  Linux one also in the workflow run's tree).
- MEASURED, reproduction with the Linux binary and this lane's own drivers: 12 of 12 raw files of the
  design lane's LANE-RECEIPT.hbp, the slowest by the build lane's wall times (the review's 11 and raw_y_N729_d0_s1o2), are
  byte-equal in their TWENS and TWPAIR rows, with 0 CR bytes in stdout and every target at its receipt sha256.
  TEST-RUNS.hbp (18 runs, 331dc0a6...) and TEST-RUNS-T1B.hbp (4 runs, 8aee3a7f...) are byte-equal. The control triple,
  recomputed in exact rationals, equals the printed one on 174 of 174 distinct records.
- MEASURED, the late-time stop at its allowed analog N = 6561, delta = 1/2, y = 1/243, every variant and NL to t = 493/64:
  source e5682f1d (binary 9ad6f7d6) exits 4 with TWB_FAULT rounding_bound_hL_above_1/2 on 3 of 3 runs (8 samples of seed
  6060601, 96 of seed 20261106, 96 of MODE0 alone of seed 3141); source 723b3674 exits 0 on 3 of 3 and prints step 493.
  At seed 6060601 the state bounds at t = 493/64 are VNC 43126728 and MODE0 99392086 ulps, the review's 4.31e7 and 9.94e7.
- MEASURED, the build lane's noiseless check (its e2_nl.py, copied, its log pointed at this lane): 168 of 168 on 723b3674;
  every d and e_int equal to e5682f1d's; only rb and the limits moved (31 of 56 rows).
- MEASURED, the review's independent tools on new seeds: R2_BND (formula-level recomputation of every printed bound) 0
  mismatches at 3 allowed points; R2_HOLD (a 2^-160 reference with MODE0 rotated by its integer vector) 0 violations at 1.
- DERIVED, every changed line read (the diff e5682f1d to 723b3674):
  - amag = max(a, b) + ceil(min(a, b)/2): (a + b/2)^2 >= a^2 + b^2 when a >= b; the ratio to the modulus is at most
    sqrt(5)/2 = 1.118; the sum stays below 1.5 x 2^63, inside u64.
  - MODE0's start bound cu(e, 2^40 + 2^11) + 3: unit30x keeps a^2 + b^2 in [2^58, 2^60], so r >= 2^29 and
    |(c, s)|/2^40 < (r + 1)/r <= 1 + 2^-29; rot() floors two products per component, under 2 ulps per component and
    sqrt(5) < 3 per mode. The frozen C_MODE0 clause reads "a unit vector exact to at least 2^-29", which the drawn vector is.
  - rk4m returns rk4's state operation for operation, so H1 to H7 change bound code only; the value rows are unchanged
    (MEASURED above on 12 raw files and 22 control runs).
- MEASURED, 8 faults planted in the changed lines, each run through fmt, clippy in both forms, the tests, T1B, the
  late-time run, R2_BND at 2 points and R2_HOLD at 1:

  | Fault | Change | Caught by |
  |---|---|---|
  | M01 | amag's ceil(min/2) as a floor | none: every printed row equal to the clean engine's in all 5 checked runs |
  | M02 | min/4 in place of min/2 (a radius below the modulus) | R2_BND only |
  | M03 | max + min (the old radius) | R2_BND only |
  | M04 | min + max/2 (max and min swapped) | R2_BND only |
  | M05 | MODE0's norm excess dropped | R2_BND only |
  | M06 | half the norm excess (2^10) | none: every printed row equal to the clean engine's in all 5 checked runs |
  | M07 | the floors' 3 ulps as 2 | R2_BND only |
  | M08 | H1 reverted, H5 kept | R2_BND only; the late-time run passes, so H5 alone removes the stop at that point |

  DERIVED: M06 is output-equivalent wherever MODE0's start error e satisfies 1 <= e <= 2^29, since
  ceil(e (2^40 + 2^k)/2^40) = e + 1 for k = 10 and 11. M01 moves a stage magnitude by at most 1 ulp, inside the region's
  2 eps + 32 margin and below the resolution at which mu and L are rounded.

## The stage

- `engines/ensemble/`: the build lane's 7 files with `src/main.rs` at 723b3674.
- `engines/trajectory/`: the build lane's 7 files and the review's check_audit.py, test_engine.py and SHA256SUMS (its H1
  to H3). MEASURED: the review's 12 planted engines (V01 to V12, each at its recorded sha256) against the staged tests
  and audit at (1/2, 1/27, 64 steps): 12 of 12 caught (the audit: V01, V02, V03, V04, V05, V09, V10, V12; the tests: V05, V06, V07, V08, V11). The clean engine passes both.
- `CORRECTIONS.hbp`: 28 rows (ensemble-1 to ensemble-27, trajectory-1), each frozen_text once on its frozen line
  (MEASURED). ensemble-26 carries the ensemble review's H9 option (a) and the operator's reading of C_MODE0; ensemble-27
  is the build lane's candidate on line 423 in the operator's reading, the measured difference beside each row for
  information only. ensemble-8 and ensemble-18 to 20 carry 723b3674's numbers. trajectory-1 carries the trajectory
  review's H5, whose counts this lane recounted: 287, 11 and 54 of 352 rows, 120 times off the 1/32 grid, none finer than
  1/64, all 20 points with one.
- MEASURED at one allowed analog (N = 6561, delta = 1/2, y = 1/243, 96 samples, 723b3674): the printed e_round of the
  MODE0 - VNC pairs over 10^-7 of VNC's field sum is 7.0 to 1.3e4 on Re Z, 11.7 to 2.1e4 on X_NC and 2.3 to 2.5e3 on f,
  above 1 at all 16 records from t = 1/2 to 493/64, in line with C_MODE0 reading NOT RESOLVED from t = 1/2 on.
- `ENGINE-CHANGES.hbp`: a12f856's 4 lines; the ensemble build lane's 5 rows at 723b3674's numbers (the ensemble review's
  H8 and H12 to H15); the round-2 ensemble review's row and this check's row; the trajectory review's 4 rows; this
  check's trajectory row.
- The workflow: a12f856's frozen job, the ensemble job with the ensemble review's H11 (steps=0), the trajectory job.
  MEASURED: the trajectory lanes' proposed workflow f38502f4 carries its frozen-job prefix with CRLF endings (33 CR bytes,
  one per line of that prefix); the merged file takes a12f856's LF prefix and the LF job texts, 0 CR bytes.

## The workflow on the stage

WSL Ubuntu 24.04, Python 3.12.3, rustc 1.81.0. Each job in a fresh copy of the stage (the checkout step replaced by that
copy), each run step as `bash --noprofile --norc -eo pipefail`, a fresh RUNNER_TEMP per job.

The run below is on this stage as built before this report and its sums took their final bytes; the engines and the workflow are byte-identical to the final stage.

| Job | Step | Result |
|---|---|---|
| frozen | Checkout, on a pull request its merge with the base | replaced by a copy of the stage |
| frozen | PREDICTION.hbp at its sha256 of the freeze, commit 38ce248 | exit 0 |
| frozen | The stage's SHA256SUMS and each review folder's | exit 0 |
| frozen | LF line endings in every file of the stage | exit 0 |
| ensemble | Checkout, on a pull request its merge with the base | replaced by a copy of the stage |
| ensemble | Rust 1.81 and lints | exit 0 |
| ensemble | Format, Clippy in both forms, unit tests, build | exit 0 |
| ensemble | Integer types only in the engine's source (float_used=0, the second seat's lexer-based scan, its self-test first) | exit 0 |
| ensemble | The binary names the source it was compiled from, and that source is this one | exit 0 |
| ensemble | The guard refuses its neighbourhood bands before any model code (zero samples, no exact reserved point started), and lifts only on lift_reserved_guard=1 | exit 0 |
| ensemble | TEST-RUNS-T1B.hbp of the controls lane (its four twctl runs, PREDICTION.hbp BRIDGE_ENGINE_CHANGE lines 447 to 450), byte for byte | exit 0 |
| trajectory | Checkout, on a pull request its merge with the base | replaced by a copy of the stage |
| trajectory | The engine folder at its sums, and the interpreter | exit 0 |
| trajectory | The tools' reserved-point check, predicate only | exit 0 |
| trajectory | The guard and step tests (the review's 172 and the round-2 tests), with and without python -O | exit 0 |
| trajectory | float_used=0 by the static scan and the two dynamic scans | exit 0 |
| trajectory | The audit of the printed bounds at delta = 1/2, y = 1/27, 320 steps and a half-step read | exit 0 |
| trajectory | The line-446 byte gate, three runs against the sha256 values line 446 names | exit 0 |

## Slips, kept on file

- The first stage was extracted with the worktree's autocrlf; it was re-extracted with `core.autocrlf=false` before any
  edit.
- The first copies of the four round-2 reports were written by Windows Python with CRLF; they were rewritten from r2.json
  with LF before any parse.
- The first trajectory-fault run had no output folder, so every engine, the clean one too, failed on the write; it was
  stopped, the folder fixed, and the run repeated.
- The mutant harness's 36 twctl runs (N = 6561, delta = +-1/2, y = 1/162) and the first ensemble-job run started without
  a pre-launch code check; their points are allowed (checked after, out/WF-POINTS.hbp). The other 102 launches went
  through this lane's launcher or the review's guard first, 0 at a reserved point or band.

## Holds for the seat

1. trajectory-2 (the trajectory build lane's H7, line 446): its frozen text occurs once at line 446, byte 87; both
   trajectory lanes leave it to the seat; it is not staged.
2. The gate text (ensemble-23 to 25, the ensemble review's H10) names a formula-level recomputation of every printed
   bound. The workflow runs none, and here R2_BND alone caught each of the 6 caught faults.
3. ensemble-27 reads the operator's "beside each row" as every row's ensemble read; if the seat meant C_MODE0's rows,
   the row's text narrows to them.
4. The round-1 reports and the lanes' receipt files, cited by sha256 in ENGINE-CHANGES.hbp, stay in the lane folders;
   the trajectory review's H9 named them for the stage.
5. The repo's binary files (53 .gguf and .png files) hold 105 0x0D bytes as data, byte-equal to a12f856.
