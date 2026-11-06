# The trajectory engine

The single classical trajectory of the three-mode polariton model, in integer fixed point (2^-256), Taylor order 28, step 1/32, with printed bounds. The engine reads the trajectory clauses of `../../PREDICTION.hbp` (T_V2_ID, T_ANCHOR, T_SELF, T_LAW_BAND, T_CLOCK_BAND, T_ZERO, T_READ) and C_NOISELESS. Its gate is PREDICTION.hbp line 446.

| File | What it is |
|---|---|
| `traj_int.py` | The engine: the guard, the Taylor integrator, the half-step read `read_at`, `obs(N)`, `bound_row()` and `obs_bound_row(N)`. Integers and rationals only. |
| `exact.py` | The design lane's exact series, a byte copy (sha256 cb4c6936…). The harness reads it. |
| `s2_validate.py` | The design lane's validation harness (sha256 69c19c27…) with its two path lines pointed at this folder. |
| `gate446.py` | The byte gate of line 446: `s2_validate.py` at delta = 1/2, −1/2 and 3/4, each output's sha256 against the value line 446 names. |
| `test_engine.py` | The round-1 review's 172 tests and the round-2 tests: each guard check on its own, u, the images against `fx`, every explicit check with and without `python -O`, the half-step labels, and the rounding parts of the observable bounds. |
| `check_audit.py` | The audit of the printed bounds, step by step, from each step's own coefficients: the review's hold H7, widened to the half-step read and to the observable bounds. |
| `float_scan.py` | float_used=0 by a static scan and two dynamic scans (rewritten divisions and powers; a trace of every value). |
| `reserved.py` | The tools' own reserved-point check. Every model run of the tools passes it first. |
| `SHA256SUMS` | The sha256 of every file in this folder. |

## Run

Python 3.12 or later, from this folder:

```
python3 -I -B -X utf8 test_engine.py traj_int.py OUTDIR engine
python3 -O -I -B -X utf8 test_engine.py traj_int.py OUTDIR engine_O
python3 -I -B -X utf8 float_scan.py traj_int.py OUTDIR engine
python3 -I -B -X utf8 check_audit.py traj_int.py 1/2 1/27 320 d1o2_y1o27 OUTDIR
python3 -I -B -X utf8 gate446.py OUTDIR/gate446
```

Each writes an HBP receipt and its sha256 into OUTDIR. The receipts carry the runs' values and hashes, and the wall times go to standard output, so a rerun reproduces them byte for byte.

## The guard

The reserved points are delta = ±3/5 (any N, y, t) and y = 2/27 at N = 81, 729, 6561. The trajectory serves every N, so the guard refuses |y| = 2/27 at every delta. It reads each argument as the exact rational and as the 2^-256 image the run uses (delta, x = delta − 1 and y), against the allowed lists, the reserved values, and the bands |delta ∓ 3/5| < 1/20 and ||y| − 2/27| < 1/81. `guard_checks` names every check that refuses. The keyword `allow_reserved=True` (the literal True) opens delta = ±3/5 exactly, at the listed y, for the blind-run driver after the operator's word. u takes the frozen map's value 1.

## The bounds

`bound_row()` prints TRAJ_BOUND: the state bound e ≥ |Z − z|₂ against the exact solution with the exact rational parameters, and the f and A/N bounds. `obs_bound_row(N)` prints TRAJ_OBS_BOUND: the A1, C1, f and D2 bounds and the V2 identity bound, each as an exact-solution part from e and R plus a rounding part of `obs()`. The derivations are in the comments of `_bound_step` and `_obs_terms`. A read between grid points prints `steps=j|half_step=1`: j steps of h = 1/32 and one half step of 1/64.
