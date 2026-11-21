# The second seat's round 2 on the ensemble and trajectory engines, November 6, 2026

Four opus55 lanes worked on the two classical engines after the freeze at `38ce248`, every run at an allowed point, and a
fifth checked the result on this stage.

**Ensemble integrator, [`ensemble-build/`](ensemble-build/) and [`ensemble-review/`](ensemble-review/).** twens 0.3.0
(source e5682f1d) adds the per-sample rounding bound, the noiseless path NL and binary provenance. The review's verdict is
PASS_WITH_HOLDS: MODE0 stopped the batch at late times (exit 4), and its engine holds H1 to H7 give the source 723b3674.

**Trajectory integrator, [`trajectory-build/`](trajectory-build/) and [`trajectory-review/`](trajectory-review/).**
traj_int.py c08a0c75 with the two-layer guard, the half-step read and the observable bounds. The review's verdict is
PASS_WITH_HOLDS; its holds H1 and H2 add the audit and test checks that catch its 12 planted faults.

**Stage check, [`stage-check/`](stage-check/).** H1 to H7 applied and checked independently (Rust 1.81 on Windows and
Linux, reproduction, the late-time run, planted faults); the merged workflow run on this stage.

**Dispositions:** [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp), one row per hold of the four lanes (43).

Each lane's scripts, logs and receipts are in its folder `C:/tmp/opus55/bridge-engine-{ensemble2,review2-ensemble,trajectory2,review2-trajectory,final-stage}-20261106/`,
kept on the seat's machine.
