# The second seat's work on the flow-map jet, November 8, 2026

The jet is the Taylor series of the ensemble engine's RK4 map in the start noise, averaged exactly under the engine's own noise law, an independent second answer for the first-order `BRIDGE_AT` rows beside the frozen Monte Carlo (the operator's decision of November 6). Engine jetens 0.2.0, binary `334dddec…` (x86_64-unknown-linux-gnu, rustc 1.81.0).

**Build, [`build/`](build/).** Predictions first, then `PLAN-JETS.hbp` (83 rows, 40 launches), the guarded driver and its dry run, and the proof at allowed analogs: 44/44 analog rows within 3 SE of the filed Monte Carlo, an independently written jet agreeing to 4.9e-13 (`INDEP.hbp`), 28/28 sabotage stops (`SABOTAGE.hbp`). Its verification passed (`VERIFY.hbp`).

**Review, [`review/`](review/).** Verdict PASS_WITH_HOLDS, predictions sealed before any run. MEASURED at allowed points:
- the build, the binary hash and the integer-only scan;
- C1 at first order derived on paper, equal to the jet on 480 rows to 8e-18;
- the truncation order confirmed by the residual's slope;
- the moment tables equal on 66,624 of 66,624 fields;
- 240/240 and 376/376 comparisons within 3 SE where the gates hold and f ≤ 1/50;
- the analog pair recomputed on 83/83 rows. 79 of 83 lie inside the frozen E_PAIR tolerance; L0637, L0673, L0686 and L0687 lie 1.09 to 2.40 tolerances outside, with truncation at most 2.5e-6 of P.
- 11 planted faults, each caught by at least one check (`FAULTS-*.hbp`).

**Dispositions:** [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp), the build lane's six decisions and every hold.

The lane folders `C:/tmp/opus55/jet-plan-20261106/` and `C:/tmp/opus55/review-jets-20261108/` stay on the seat's machine. Build seal `833dfe1e5174d7463685253fdc22eb04a29537a14e4e821c085c644f776dfd45`; review seal `617f9e50ee04bc1c65bb3edd14a14c153809cc2c32950c2ee620f549f618cab2`.
