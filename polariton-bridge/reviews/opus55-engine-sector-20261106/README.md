# The second seat's work on the Q = 0 sector mode, November 8, 2026

The operator's decision (3) of November 6: run the y = 0 full-space points on their Q = n₊ − n₋ = 0 sector. At y = 0 the Hamiltonian keeps Q, and the start |N,0,0⟩ has Q = 0, so the full-space state lives on the K/2 + 1 states (2j, j).

**Build, [`build/`](build/).** The mode `sector` in `src/bin/polariton_first_correction.rs` (sha256 `c3b9498b…`), binary `6bf8ebf2…` (x86_64-unknown-linux-gnu, rustc 1.81.0). Predictions first (`PREDICTION-Q0.hbp`), then 12 of 12 met (`RESULTS-Q0.hbp`), MEASURED at allowed points:
- 17 of 17 READ rows equal `point` in every field but array_bytes, at 10 points from N = 81 to 6561, including K = N = 6561.
- `point` and `stream` reproduce their filed receipts unchanged.
- y ≠ 0 is refused with exit 2 and no row.
- Each of the three sabotages fails the checks `CONTROLS-SECTOR.hbp` names.
- N = K = 6561 over the frozen y = 0 time list: 13.5 s at a 2.5 MB peak. `point` takes 41.2 s for one window at 1.26 GB.

**Review, [`review/`](review/).** Verdict PASS_WITH_HOLDS. The rebuilt binary is bit-identical, and the sector integers match `point`'s at every allowed point run. The holds fix the wording of one comparison (the frozen-list match is against a separately written sector implementation) and the pins.

**Dispositions:** [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp). H10, a fallback launch at K = N, is declined: that fallback is not authorized. The optional harness R3 is held for its own check. The plan pins H9 and R2 go in at the resume.

The lane folders `C:/tmp/opus55/q0-sector-20261106/` and `C:/tmp/opus55/review-sector-20261106/` stay on the seat's machine with their scripts, logs and build trees. The build lane's whole index is here (`build/INDEX.hbi`, `build/LANE-SHA256SUMS`); the review's seal value is `befc6a3c61f8a1fd49715f73b85143b2cdcf6240f92e0cd34bf9f55eb301ff1e`.
