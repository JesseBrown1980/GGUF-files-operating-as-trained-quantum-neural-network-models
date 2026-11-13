# The sampling amendment of November 6, 2026 and its independent check

**Amend lane, [`amend/`](amend/).** It wrote [`../../AMENDMENT-2026-11-06-F-SAMPLING.hbp`](../../AMENDMENT-2026-11-06-F-SAMPLING.hbp) from a copy of the generator, which first reproduced `PREDICTION.hbp` byte for byte.
- 33 rows' M_VNC rise, on 14 points' VNC staircases.
- The total goes from 5.0504e9 to 5.8971e9 vst, 1.168 times.

**Verify lane, [`verify/`](verify/).** It wrote new code that imports nothing from the generator or the earlier checks. Verdict PASS_WITH_HOLDS.
- Every changed row, staircase and cost field reproduces exactly.
- f's 3-SE bound fits on 70 of 70 rows at y != 0. D2's fits on 38 of 70, read at its original sampling level.

**The holds as applied:**
- a summary row mapping the six frozen lines whose figures read at the amended counts;
- positive wording;
- the 1.168 ratio in the README;
- the driver reading this file's counts on its 33 rows.
