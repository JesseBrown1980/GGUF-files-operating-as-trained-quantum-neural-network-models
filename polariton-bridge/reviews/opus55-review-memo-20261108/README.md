# The second seat's review of count-weighted reuse (twens 0.4.0), November 8, 2026

The operator's decision (2) of November 6 asks for a second-seat review of twens 0.4.0 and its amendment before the
ensemble phase runs. This folder is that review. It attacked the build lane's work (`C:/tmp/opus55/count-memo-20261106/`,
head `e47ac9f`, filed in [`../opus55-count-memo-20261106/`](../opus55-count-memo-20261106/)) from its own folder,
`C:/tmp/opus55/review-memo-20261108/`, at allowed points only. The 113 launches of the lane's own batches went through
a reserved-point check in code first (delta = +-3/5 at any N; y = 2/27 at N in {81, 729, 6561}; a band around both):
113 started, 0 refused. The CI step and `TEST-RUNS-T1B` run fixed points, N=81, delta=1/2, y=1/27 and N=6561,
delta=+-1/2, y=1/162, read from their text and checked by the same rule ([`review/POINTS-SCAN.hbp`](review/POINTS-SCAN.hbp)).
Integers and exact rationals only, Rust 1.81, LF files, at most 2 heavy processes, each run stopped at 30 minutes.

Predictions came first: [`review/PREDICTIONS-REVIEW.hbp`](review/PREDICTIONS-REVIEW.hbp) before any build or run,
[`review/PREDICTIONS-REVIEW-b.hbp`](review/PREDICTIONS-REVIEW-b.hbp) before the thread-count batches, the Windows build
and the CI-job replay. [`review/PRED-EVAL-REVIEW.hbp`](review/PRED-EVAL-REVIEW.hbp) evaluates them and keeps this lane's
own errors and its two failed predictions (V3, and the P1 gate column).

**Verdict: PASS_WITH_HOLDS.** The holds are the placement of the build lane's files (its H1 to H7, with this review's
README line) and of this folder. Every tag below is MEASURED unless it says DERIVED.

## Rebuild ([`review/BUILD.hbp`](review/BUILD.hbp), [`review/WIN-BUILD.hbp`](review/WIN-BUILD.hbp))

- The proposed `main.rs` `1d768fa9...`, `Cargo.toml` `9dcc6a6e...`, `Cargo.lock` `44f9051f...` with the rest of the
  46b92e8 crate, in this lane's own target folder: fmt `--check` 0, clippy `--release -D warnings` 0 in both forms,
  21 of 21 tests, build 0, float scan 0 uses. Linux binary `33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f`,
  the build lane's.
- The 46b92e8 crate: 14 of 14 tests, binary `75530df9c7414b9a1b28f7408cbacd512f35d48836e2a6823beefb4941b9598d`, the filed one.
- Windows, rustc 1.81.0 x86_64-pc-windows-msvc with /Brepro, at a third source path: `483ffa29ca55352fbe27b28bb02ddf9d9aeb0c63c637b090a2f21ee247721981`,
  the build lane's.
- The proposed workflow's `ensemble` job replayed on 46b92e8 with the proposed files laid over
  ([`review/CI-JOB.hbp`](review/CI-JOB.hbp)): toolchain gate, float scan, the binary naming its source,
  `TEST-RUNS-T1B.hbp` (`8aee3a7f...`) and the count-weighted step, 5 of 5 steps exit 0. The guard step's band points
  were left out of the replay; that step's text is unchanged by the proposal.

## The build lane's gate, replayed ([`review/GATE-REPLAY.hbp`](review/GATE-REPLAY.hbp))

Its checker `rr_check.py`, run with only its two output paths changed, rewrote `GATE.hbp` (`acc9f866...`, 100 rows,
0 failures) and `PRED-EVAL.hbp` (`e964ad3a...`) byte for byte. Its three prediction files were each committed once,
before their code and runs, and are unchanged since (`428035ff...`, `24b3e947...`, `d319c0c9...`).

## Own batches ([`review/R-CHECK.hbp`](review/R-CHECK.hbp), [`review/T-CHECK.hbp`](review/T-CHECK.hbp))

Points, counts, seeds, starts and thread counts chosen here. In every batch the `memo=1` stdout equals the plain stdout
of 0.4.0 byte for byte, every row after the head equals 0.3.0's, the head differs in version and hashes only, plain
stderr is empty and the memo stderr is one `TWB_MEMO` row whose counts add up.

| Batch | Point and mask | Count | What runs memoised | Work ratio | Wall memo/plain |
|---|---|---|---|---|---|
| R1 | N=243, delta=1/3, y=1/9; VNC, V1, RN, FLIP, NL; 3 threads | 4194305 | K4: VNC, V1, RN, FLIP with their pair rows | 0.987 | 0.979 |
| R2 | N=2187, delta=-1/4, u=1/2, y=1/27; all seven | 4194304 | K4: RN, FLIP; K2: LOCK; per sample: VNC, V1, V0, MODE0 | 0.855 | 0.897 |
| R3 | N=729, delta=1/4, y=1/81; LOCK; 3 threads | 2097157 | K2: 40921 distinct starts | 0.019 | 0.118 |
| R4 | N=243, delta=0, y=1/16; VNC | 4194303 (2^22 - 1) | every sample one by one | 1.000 | 1.035 |
| R5 | the `twens` CLI, N=243, 100003 samples, 3 threads | 100002 | K2: LOCK | 0.887 | 0.556 |
| R6 | N=6561, delta=1/2, y=1/243; V1 | 4194310 | K4: V1 | 0.987 | 1.127 |

`memo=0` at R6 gives the no-key stdout byte for byte. G1, G2, G3 and G5 (the fault gate's batches, fewer steps) pass the
same checks, and G1 with `memo=1` at 1 and at 7 threads gives 0.3.0's rows at 3 threads and the same `TWB_MEMO` row.
The K4 saving at 2^22 samples is about 1.3 percent of the work; it grows with the count, as the build lane's
plan-scale analogs show (0.495 at 427423138 samples).

## Planted faults ([`review/MUTANTS-SRC.hbp`](review/MUTANTS-SRC.hbp), [`review/MUTANTS-REVIEW.hbp`](review/MUTANTS-REVIEW.hbp))

Twelve faults of this lane's own, one exact replacement each in a copy of `1d768fa9`, each through the crate's tests,
the gate batches G1 to G5 against the unmutated binary, and the proposed CI step run as written.

| Fault | Tests | Gate batches | CI step |
|---|---|---|---|
| F1 key merges two starts (low bit of c cleared) | 2 fail | rows differ, 4 of 4 | stops at `cmp` (batch A) |
| F2 phase-2 K4 start rebuilt with -c3 | 2 fail | rows differ (G1, G2) | stops at `cmp` |
| F3 dropped count (w - 1 copies for w > 1) | 1 fails | rows differ (G1, G2) | stops at `cmp` |
| F4 K2 weight taken mod 256 in the sums | 21 pass | rows differ (G2, G3) | stops at `cmp` |
| F5 phase-1 sample range shifted by one | 3 fail | rows differ, 4 of 4 | stops at `cmp` |
| F6 shared chunker boundary (t <= rem) | abort, exit 6 | plain rows differ; memo exit 6 (count check) | exit 6 |
| F7 wrap carried as 255 | 1 fails (`counter8_carries_its_wraps`) | equal | passes |
| F8 wraps of the first phase-1 thread only | 21 pass | equal | passes |
| F9 pair closure in one pass | abort, exit 6 | equal | passes |
| F10 phase-2 integrations left out of `TWB_MEMO` | 21 pass | `TWB_MEMO` differs, 4 of 4 | stops at the memo-row test |
| F11 eps_max taken as max(eps * w) | 3 fail | rows differ, 4 of 4 | stops at `cmp` |
| F12 K4 key reads g4 for c3 | 2 fail | rows differ (G1, G2) | stops at `cmp` |

Tests catch 9, the gate batches 9, the CI step 9, and 11 of 12 fall to at least one. F8 is caught by the engine itself:
a probe build whose counter wraps at every second hit (P1, [`review/PROBE-P1.hbp`](review/PROBE-P1.hbp)) gives the
plain rows byte for byte under 51296 to 51675 wraps per batch, and the same probe with F8 (P1F8) stops with `TWB_FAULT|reason=memo_count_check`, exit 6, at G1, G2,
the CI step's batch A and in the tests. A control change that no memoised variant reads (C1, g4 = 2^35 in the rebuild)
passes everything, as it should.

The wrap path matters only above 255 samples on one K4 cell. At the plan's largest launch (427423138 samples) the
centre cell holds 10.322 on average, and the chance that any of the 295937937 cells reaches 256 is at most 2^-793
(DERIVED, [`review/WRAP-BOUND.hbp`](review/WRAP-BOUND.hbp)). The ball's cell count and the K2 box's 261121 were counted
here independently ([`review/BALL-COUNT.hbp`](review/BALL-COUNT.hbp)).

## Texts ([`review/TEXT-CHECK.hbp`](review/TEXT-CHECK.hbp), [`review/PLAN-CHECK.hbp`](review/PLAN-CHECK.hbp))

- `PREDICTION.hbp` `fadd8412...` (873 lines, the amendment's `prediction_lines`), the F amendment `60c403d3...` and
  `CORRECTIONS.hbp` `9bfdd27d...` stay outside the proposal.
- The proposed `ENGINE-CHANGES.hbp` (`3ecb0e6f...`) is the 46b92e8 file (`cf66a72c...`, 17 rows) byte for byte and
  one 1972-byte row 18.
- The proposed `SHA256SUMS` replaces 5 lines, inserts 1 after the F amendment's, keeps the order, and checks 24 of 24
  on the laid-over tree; every review folder's own `SHA256SUMS` checks there; 0 CR bytes in the 33 proposed files.
- The README diff is one inserted section and 4 edits; the workflow diff is the job name, the timeout and one step.
- Every 64-hex value in the amendment, in row 18 and in the README section equals a value measured or read here.
- The `PLAN-BLIND.hbp` change: the 347 ensemble rows change only their `binary_sha256` (75530df9 to 33e62fbe) and
  end their argv with `~memo=1`; the head changes its `ensemble` and `ENGINE-CHANGES_sha256` fields and adds one,
  `ensemble_memo=1(AMENDMENT-2026-11-06-G-MEMO.hbp_sha256=9ca167ef...)`; the other 74 lines are byte-equal; the
  sidecar names the new plan; the driver's line 140 is the text the change replaces; all 347 rows keep
  `lift_reserved_guard=1`, so the operator's lift still governs them.

## The build lane's chain ([`review/CHAIN-BUILD-LANE.hbp`](review/CHAIN-BUILD-LANE.hbp))

The seal's arithmetic recomputes: `sha256(SHA256SUMS_sha256|INDEX.hbi_sha256)` = `af49bf60...`, over 896 files.
895 of 896 files verify today; the 896th is the lane's `.gitignore`, which gained the line `rr/apply-check/` in
commit `224b281`, after the seal (78 to 94 bytes). Written after the seal and outside the index: the laid-over tree
`rr/apply-check/` (1038 files), `rr/logs/APPLY-CHECK.hbp`, `rr/logs/PROPOSE.stdout` and `tools/rr_apply_check.sh`.
The proposed repository files lie outside this set: the 23 files of `build/` in the build lane's review folder equal
their lane files byte for byte and its `SHA256SUMS` checks 24 of 24.

## Findings carried forward

- The wrap merge across phase-1 threads has no test and no batch that reaches it (F8); the engine's count check stops
  the run on any dropped wrap, and at plan scale a wrap has probability at most 2^-793. Decided here: no code change
  before the ensemble phase, since any change re-pins the binary the plan names.
- K2 cells above 255 appear in the CI step's batches A and B (about 652 at the centre, DERIVED), and the unit tests'
  2^18 samples reach about 41 (DERIVED); the CI step is their gate (F4).
- The build lane's `GATE_MUTANT` row for M5 reads `caught_by_tests=1|failed_tests=none`: the test binary stopped with
  exit 6, as F6 and F9 do here.
- The driver's `bridge_plan.py` pins `EC_SHA = b5fc5d6a...` for `gen_plan.py` and `--check-needs`; the run path reads
  the plan and its sidecar. Both cf66a72c and 3ecb0e6f differ from that pin, so a `--check-needs` call stops at
  `PLAN_REFUSED` until the driver's pin moves with ENGINE-CHANGES (DERIVED from the code, no call made).

## This lane's chain

[`review/INDEX.hbi`](review/INDEX.hbi), [`review/LANE-SHA256SUMS`](review/LANE-SHA256SUMS) and
[`review/SEAL.hbp`](review/SEAL.hbp) are the lane folder's index, sums and seal, `seal = sha256(SHA256SUMS_sha256 + "|" +
INDEX.hbi_sha256)`, over every file but `.git/`, the 46b92e8 archive, the build and laid-over copies and `proposed/`.
[`review/RUNS.hbp`](review/RUNS.hbp) is every launch of the lane's own batches with its argv, exit, wall time and
peak memory.
