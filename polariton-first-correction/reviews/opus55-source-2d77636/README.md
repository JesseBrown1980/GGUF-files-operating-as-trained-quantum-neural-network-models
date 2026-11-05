# The second seat's source and certificate review, at `2d77636`

Three opus55 lanes read the engine, the reader and the route at `2d776369fbf7448c6adcf3ecce4bcaa2ae792c20`, before any point of the frozen grid ran. They ran only on seen rows, small N and closed forms.

**Verdict: the engine is fit to read the grid, on all three lanes. The reader and the route needed the holds below before the grid.**

**The engine, MEASURED.** 0 of 42,258 reads at N ≤ 40 fall outside a printed bound, against an exact reference in big integers that shares no code. The smallest state margin is 1.021, at N = 2, and it matches its hand value. At N = 729, epsilon is at least 21 times the true state distance on all 12 rows read. The second seat's propagator meets the engine's state within 7 × 10⁻¹⁸ on C₁ and 48 × 10⁻¹⁸ on A₁, with exact roots on the same state. At K = 1600 on the seen point, the half width of V² is 1.9 parts per million of V².

**The faults, all in the checks around the engine.**

1. The reader's expanding-L clause `low.eps >= r.eps` goes beyond the frozen row's text, and it is false. Epsilon has a rounding floor that grows with K: 3.393 × 10⁻⁸ at K = 1200 and 5.495 × 10⁻⁸ at K = 1600, on the seen point at t = 1, with C₁ the same to 18 digits. So this clause would have printed frozen MISS rows on an estimated 8 or 9 of the 10 points, CONJECTURE, since the grid stayed unrun. The clause is gone, and eps still prints.
2. The route's limit of 10⁻¹⁴ on A₁ fails on healthy rows: 53,459 × 10⁻¹⁸ at N = 6561, K = 1200. The offset is the engine's read-out at roots of 2⁻²⁴, inside `A1_err`. The step ran only after a grid was filed, so it would have gone red after the read. The limits now come from the engine's own read-out account.
3. 68 of 153 mutants passed every check before the grid, 47 of them with a bound cut and the reads unchanged. With the holds, 57 of the 68 die by name. The other 11 move reads by at most 3097 × 10⁻¹⁸ and epsilon by at most 1.3%, and they are named in [the dispositions](HOLDS-APPLIED.hbp).
4. Nothing read the reader's grid mode before the grid. The mutation lane's battery of 87 scenarios on synthetic receipts, built from the closed forms with no engine and no model run, is now [a step of the job](../../synthetic/). One scenario changes with fault 1: eps rising alone now reads MET.

**Added by these holds.** The reader checks that each planned row appears once, and recomputes what each row owes: the model's fields, epsilon as its parts, the conversions, V² and its interval, the series' degree and reach, and the leak log under the certificate. The route walks the certificate in big integers on small blocks of N = 100 and N = 40, reads norm(B) and the spectral interval on each receipt row's own block, reads the Bessel tables past their ends, and reads the tail row by row. The second seat's propagator now runs on every baseline row, and on new rows at δ = −1/2, −3/4 and 3/4, at every head. Baseline rows at K = 1600 and at y = 1/648 cover the grid's largest K and sit below its smallest y.

**The disposition of every hold:** [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp). **Each lane's own words:** `REPORT.md`, `FINDINGS.txt` and `HOLDS.txt`, in [`certificate/`](certificate/), [`mutation/`](mutation/) and [`independent/`](independent/). The lanes' scripts and tables are in the tools archive `D:/safety-backups/opus55-fc-review-20261105-tools.tar.gz`.

**Limits, from the lanes.** The grid's own rows stayed off limits to every lane, so the MISS count in fault 1 is an estimate and the mechanism is the measured part. The exact reference stops at N = 40. Above that, N = 729 rests on the engine against itself across K and W, and N = 6561 on K against K and on the second seat's propagator. Fabric and recall were left unasked for this code review, and the owning gate is the repo's hosted job.
