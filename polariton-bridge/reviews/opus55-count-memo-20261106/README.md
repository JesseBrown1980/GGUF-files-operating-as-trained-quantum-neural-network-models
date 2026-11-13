# The second seat's build of count-weighted reuse in the ensemble engine, November 8, 2026

The operator's decision (2) of November 6: the ensemble engine reuses repeated starts by count, its saving measured at
plan scale first, built with a byte-for-byte gate against the plain engine, a second-seat review and an amendment row,
before the ensemble phase.

**Build, [`build/`](build/).** twens 0.4.0, `src/main.rs` sha256 `1d768fa9aba719d0439625f08ea2711cc0d28a5e751b25a81667b4b3d5fcacbb`, binaries `33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f`
(x86_64-unknown-linux-gnu, rustc 1.81.0) and `483ffa29ca55352fbe27b28bb02ddf9d9aeb0c63c637b090a2f21ee247721981` (x86_64-pc-windows-msvc, /Brepro). Predictions first
(`PREDICTIONS.hbp` before the code, `PREDICTIONS-2026-11-08.hbp` before the rerun, `PREDICTIONS-2026-11-08b.hbp`
before the halves of order 285), evaluated in `PRED-EVAL.hbp` and `RESULTS-NOTES.hbp` (the failed ones kept); the
gate's rows in `GATE.hbp` (0 failures), MEASURED at allowed points only:
- the 31 raw receipts of the design lane reproduced byte for byte by 0.3.0, 0.4.0 and 0.4.0 with `memo=1`
  (93 of 93), `TEST-RUNS.hbp` and `TEST-RUNS-T1B.hbp` by both engines (4 of 4);
- 10 of 10 plan-scale analogs with every row after the head equal to 0.3.0's; wall ratio memo/0.3.0
  o96:0.882,o97:0.930,o99:0.813,o210:0.902,o254:0.568,o266:1.001,o285:0.875,o296:0.709,o355:0.109,o404:0.849;
- the saving over the 347 ensemble launches [1019102161.2,1019102162.3] variant-sample time units,
  [17.28,17.29] percent of 5897110802.9 (DERIVED, `REALIZE.hbp`, `DERIVE.hbp`);
- 11 mutants, 11 caught by the tests, 9 by the batch gate (`MUTANTS.hbp`, `GATE.hbp`).

**Review:** open; the second-seat review runs before the ensemble phase.

The lane folder `C:/tmp/opus55/count-memo-20261106/` stays on the seat's machine with its scripts, logs, binaries and
build trees; its whole index is here (`build/INDEX.hbi`, `build/LANE-SHA256SUMS`, `build/SEAL.hbp`).
