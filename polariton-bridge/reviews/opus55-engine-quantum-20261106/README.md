# The second seat's work on the quantum engine, November 6, 2026

Three opus55 lanes worked on the quantum engine `src/bin/polariton_first_correction.rs` after the freeze at `38ce248`, every run at an allowed point.

**Dyadic reads, [`dyadic/`](dyadic/).** The engine reads at any multiple of 2^-W, and the frozen times need W = 6.
- MEASURED: `RECEIPT-GRID.hbp` reproduces byte for byte as a whole file, and `RECEIPT-BASELINE.hbp` on its 58 rows at allowed points (2,378 fields, 0 differing).
- The 6 rows of the two baseline runs at y = 2/27, N = 729 (delta = 0 and 1/2) reproduce in the blind phase, when the reserved set opens. Their whole-file check is OPEN, reason RESERVED.

**Streaming layout, [`stream/`](stream/).** The mode `stream` sweeps several Chebyshev levels across the shell wavefront, in tiles.
- It reproduces both receipts in every field but array_bytes.
- On the full space at N = 6561 (delta = 1/2, y = 1/324) it runs 1.98 times as fast as `point`, at a peak of 1.04 GB against 1.29 GB (MEASURED).

**Review, [`review/`](review/).** Verdict PASS_WITH_HOLDS.
- The rebuilt binaries are bit-identical to the lanes' binaries.
- All 10 planted faults are caught.
- Its holds add `RECEIPT-DYADIC.hbp`, the many-tile and dyadic steps in the stage workflow, and the pins.

**Dispositions:** [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp). Every hold is applied as held; two merge where the review measured the line.

**Binaries,** x86_64-unknown-linux-gnu, rustc 1.81.0: dyadic `cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776`, streaming `d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270`.

Each lane's own words are in its `REPORT.md`. Its scripts and logs are in the lane folders `C:/tmp/opus55/bridge-engine-{quantum,stream,review-quantum}-20261106/`, kept on the seat's machine.
