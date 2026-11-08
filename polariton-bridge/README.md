# Polariton bridge: the frozen prediction (QNN issue #9)

This folder holds the frozen prediction for the quantum-to-classical bridge of the three-mode polariton model,
[issue #9](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/issues/9).
The rows are in [`PREDICTION.hbp`](PREDICTION.hbp): 873 rows, one per line, `TAG|key=value|...|json=0`, LF line endings,
kept LF on every checkout by [`.gitattributes`](.gitattributes), sha256 in [`SHA256SUMS`](SHA256SUMS). They were assembled on
November 5, 2026 by the second seat (opus55) for ACER-CLAUDE-FABLE5, from the four design lanes whose findings and proposed
rows sit unchanged in [`design/`](design/). The generator (`build_prediction.py`, sha256 `c0e271d4a760f44f905ff91941e76ce2f1fef20e21c892aed73d6a2b56a362e5`, in the seat's local
notes) evaluates closed forms and exact series only; the freeze comes before every bridge calculation of any model at
any of these points. The model, its earlier rows and the first-correction row stay in
[`../polariton/PREDICTION.hbp`](../polariton/PREDICTION.hbp), untouched, so its whole-file pin holds.

Two checks read the assembled rows before the freeze: a values check (10 holds) and a requirements check against issue #9
(20 holds). The operator chose the sample design E4R on November 6, 2026, from the designs the cost lane priced; the generator
recomputes its counts from the cost lane's closed forms, prints them on every `BRIDGE_AT` row and lists each point's steps
in `BRIDGE_SAMPLE_PLAN`, status **SET_BY_OPERATOR_E4R**. A third check then recomputed the plan with code of its own (10 holds). Each
hold went through the generator, and [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp) records what was done with it; the seat's
decisions on them are `BRIDGE_SEAT_DECISION` D11 to D18.

Where a row carried from a lane and a row written for the freeze differ, the freeze's rows govern
(`BRIDGE_PRECEDENCE`). Every carried row ends with `src=design/<lane>/PROPOSED-ROWS.hbp#L<line>`.

## What is compared

- **The quantum frame map.** U = exp(-iH dt) on the exchange-even space (states (q, m), q = n+ + n-, even under
  n+ <-> n-), from the number state with all N quanta in mode 0. The Hamiltonian and its units are line 3 of
  `polariton/PREDICTION.hbp` (u = 1, x = delta - 1, JN = 1); the observables and their normalisation are line 4.
- **The single classical trajectory.** The mean-field equations of the normal-ordered Hamiltonian, z = c/sqrt(N),
  start c0 = sqrt(N), c+ = c- = 0 (`BRIDGE_TRAJ_MAP`). The scaled equations are free of N, so one trajectory per (delta, y)
  serves every N.
- **The sampled ensemble.** The primary ensemble is **VNC**: c0 = sqrt(N + 3/2 - |c+|^2 - |c-|^2) e^(i phi), vacuum noise
  of variance 1/2 per side mode, read with the number-conserving symbol X_NC. **V1** (the plain ring c0 = sqrt(N + 1/2))
  is a named comparison read through the pair rows P = N^2 (C1_V1 - C1_VNC). **V0** (the coherent stand-in) is reported,
  with its open item at N = 2187. V1 and V0 run on the same side-mode noise as VNC in every sample.
- **The observables** (`BRIDGE_OBSERVABLES`): A1 = 2|E[A_W]|/N; C1 = 2E[X]/(N(N-1)) with each variant's ordering;
  V^2 = A1^2/(2 C1) from the ensemble means, a ratio of ensemble moments; V^2 is UNDEFINED where A = 0 or where the
  certified lower bound of C1 is 0 or below; f, D2, and the sign of E[Re A] on every row.
- **The framework.** Brown and Fedotov (December 11, 2024, Zenodo 14390025) write the universe as frames,
  F_(n+1) = T(F_n). Here T is U for the quantum side and the trajectory or the ensemble for the classical side, and the
  test is Phi(U^n(rho_0)) against C^n(Phi(rho_0)) at every frozen time, each classical map read on its own. Phi maps the
  quantum initial state to a classical phase-space law (VNC for the ensemble; the point c0 = sqrt(N), c+ = c- = 0 for the
  trajectory), and each frame's record (A1, C1, V^2, f, D2, the sign of Re A) is read apart from the map. The paper's
  epsilon correction is set aside in this freeze (`BRIDGE_FREEZE_CHOICE` FC01).

## Where and when

- **Points** (28 distinct): N = 81, 729, 6561; delta = +3/5 and -3/5 (gamma = 4/5); fixed s = 1/3, 2/3, 4/3 with
  y = s/sqrt(N); fixed y = 2/27 (s = 2/3, 2, 6); and y = 0 at each (N, delta). At N = 81 the fixed-y point is the
  s = 2/3 point, one run read in both families. Every point is blind; the clocks lane's exposure audit is carried as the
  `BRIDGE_EXPOSURE` rows. Each point has a `BRIDGE_POINT` row: its clocks, its times, its quantum route, its staircase in
  the sample plan and its seed.
- **Times** (352 `BRIDGE_AT` rows). The clocks lane's rule: t_q, t_tr and t* = ln N/(2 gamma), each shifted by
  k ternary steps D3 = (5/8) ln 3 (k = -2, -1, 0, 1 for t_q and t_tr; k = -1, 0, 1 for t*), rounded to 1/64 and merged;
  plus the trajectory lane's anchor time t_e (the last 1/8-grid time with the law's f at most 1/200); plus t = 1/2 at
  N = 81, t = 1/2, 1 at N = 729, t = 1/2, 1, 2 at N = 6561. Every time is a multiple of 1/64. The clock rule was
  recomputed here with an independent logarithm and reproduces the clocks lane's 278 times exactly (`BRIDGE_CHECK`).
- **Each `BRIDGE_AT` row names what applies at its time** (`applies=`) and what is read and reported
  (`read_and_report=`): closed-form predictions only inside the law's or the first correction's range, the CONJECTURE
  bands at the clocks and the J flip's CONJECTURE sign past its window, and read-and-report everywhere else.
- **t\*** is frozen as the hypothesis for the unstable regime (requirement 4): at star-1, star+0 and star+1 the single
  trajectory's A1 and D2 ratios to the quantum are printed beside the first-order form of `BRIDGE_TRAJ_FAIL_A1`, read and
  reported (CONJECTURE).

## The single trajectory: where it fails, frozen

- **T_V2_ID.** On one trajectory V^2 = (N-1)/N exactly wherever A is nonzero (80/81, 728/729, 6560/6561), whatever the
  Hamiltonian; 0/0 and UNDEFINED where A = 0. It fails if a run's V^2 leaves the identity by more than 10^-9, or reads 1
  (the N^2 normalisation). 11 rows lie at or past the trajectory's return lower bound; there the identity is
  read where the certified |A| exceeds its integration bound.
- **T_ANCHOR** at t_e (22 rows): eps_V2, R_C = C1_traj/C1_q - 1 and R_A = A1_traj/A1_q - 1 against law plus first
  correction, with the trajectory lane's tolerances; the pair fraction through R_F = f_traj/f_q - 1 against the printed
  f_traj/f_law - 1 (its missing vacuum term 2 J0/N), within (1 + R_F_pred)/10, nondiscriminating at the 2 fixed-y anchors at N = 6561 (R_F_pred = -2.84e-2, -2.48e-2);
  and D2_traj/D2_q - 1 within 11/100, D2_traj = f_traj = D2_law at leading order. The quantum side is assumed within 1/200
  of law plus first there, and f_q within 1/10 of the law (CONJECTURE until read). **T_SELF**: the run's A1 and f within
  10^-6 of the trajectory's own exact series at the anchors.
- **T_LAW_BAND** (64 rows): where the law's own frozen tolerance holds (N at least 243, law f at most 1/10, V^2 within
  5 percent, line 39), eps_V2 = (N-1)/N - V2_q lies in [(N-1)/N - (21/20) V2_law, (N-1)/N - (19/20) V2_law].
  2 of these bands hold 0 and are marked `law_band_excludes_0=0`. On 10 more rows inside line 39's range,
  line 48's own V^2 correction exceeds half the law's tolerance (up to 1.63e-1), so the band is withheld there
  (`law_band=withheld`) and those rows carry the clock band or read and report.
- **T_CLOCK_BAND** (66 rows, CONJECTURE): at N = 729 and 6561, inside the trajectory lane's window from
  t_q^- - 1 to t_q^+, V2_q/V2_law in [3/4, 5/4]. 13 of these bands hold 0 and are marked
  `clock_band_excludes_0=0`. At its own 1/8-grid times the lane's band gave 48 rows with 12 holding 0; those rows stay in
  `design/trajectory/PROPOSED-ROWS.hbp`, marked there `band_excludes_0=0` at the lines the clause lists, and were
  reproduced exactly here.
- **T_ZERO** (y = 0): the trajectory sits at its fixed point; C1 and f miss with relative error exactly 1; V^2 UNDEFINED.
- **T_SCALING** (`BRIDGE_TRAJ_SCALING`): at fixed s the failure stays as N grows (the band of eps(6561)/eps(729) sits about
  1); at fixed y it falls like 1/N (that band sits well below 1).
- Elsewhere (170 rows) the trajectory is read and reported with T_V2_ID as its frozen clause.

## The ensemble: where it succeeds, frozen

- **E_VNC** on the 83 rows with the law's f at most 1/50 (29 of them beyond t = 1/2, 1, 2, in `ENS_ROW_EXTRA`):
  VNC within tau of the quantum on C1, A1, V^2, f and D2, tau = 1/200 at N = 81 and 1/1000 at N = 729, 6561. The basis:
  VNC carries every term of the first correction (w10, w11, C10, C11, C12 of line 48), so its residual is of order N^-2,
  for every observable at most quadratic in the side modes. A MISS refutes that. **E_VNC_ZERO** at y = 0: C1 and f within
  tau, A1 and D2 consistent with 0; V^2 UNDEFINED as a comparison at A = 0, its estimator printed beside its positive bias
  bound.
- **E_PAIR**: on common samples, N^2 (C1_V1 - C1_VNC) = P = (2 delta (cosh 2gt - 1) + 2 gt sinh 2gt)/(1 + delta)^2, free of N
  and s, within 43 phi0 |P| + |P|/100, phi0 = 2 sinh^2(gamma t)/((1 - delta^2) N); a MET also needs 3 SE at most |P|/100.
  The plan's pair count on each first-order row is at least four times the count at which 3 SE equals |P|/100 (four times on
  65 rows, more on 18 from the staircase), so all 83 rows meet
  that need. The ensemble lane proposed the coefficient 20;
  at the holds stage's placeholder count (2^25) its own
  resolved next-order coefficients (up to 2.139e1) leave a thin margin at N = 81, where a correct run could miss 20, so the
  coefficient is twice that largest one (FC20, kept by the seat). The values check's evidence row (`BRIDGE_EVIDENCE`): the part of the next
  order that grows with s^2, which the lane's calibration left out, uses at most 4.47e-2 of P_tol.
- **D_9_81**, the 9-versus-81 diagnostic, at fixed s: between N = 81 and 729 at t = 1/2, read with the control-variate
  estimator, VNC's residual is predicted to fall by more than 27 (= sqrt(9 x 81)) wherever the read resolves it, and V1's
  closed-form decline is about 9; between N = 729 and 6561 the VNC residual is predicted NOT RESOLVED while the
  plain-equivalent sample count stays below 10^9; at the plan's counts and the control-variate floors that count is 2.45e9 to
  8.16e14 on all 16 such rows (80 checks), so they read and report (CONJECTURE on the realised cut). Its precision is set by the
  plan: at t = 1/2 the V1 counts at N = 81 and
  729 are at least those at which V1's bounds, plus a 3-SE excursion, fit inside the gap to 27 on C1 and V^2 at the
  control-variate floors (CONJECTURE); each `BRIDGE_DIAGNOSTIC` row prints its counts.
- **E_V1, E_V0**: read and reported; V1's frozen test is E_PAIR.

## The negative controls and the matched pairs

The J flip and the pair-locked seeds read against the quantum with tau = 1/20 (the controls lane's margins); the
insufficient-sampling control reads with each row's own tau(N) (1/200 at N = 81, 1/1000 at N = 729 and 6561); the fixed
mode-0 phase reads against the uniform-phase ensemble within 10^-7; the noiseless control reads against the trajectory
engine within the two integration bounds. The J flip and the pair-locked seeds run on each point's staircase: at every row
at least the count each of its frozen MISS components needs, and 2^20 on read-and-report rows; the uniform-phase partner of VNC's fixed mode-0 phase (MODE0) runs
on the first 2^16 samples and the insufficient-sampling control on the first 57182; each row prints its counts. Every
predicted control outcome lies inside the law's range
(96 rows, `BRIDGE_CHECK`); C_MODE0 and C_NOISELESS are exact identities and stand on every row.

- **C_JFLIP**, an incorrect coupling (J with its sign flipped): in the window where line 48's correction is at most 1/10, a
  MISS on A1 (ratio band [30/11, 50/9] at 3/5, [15/88, 25/72] at -3/5), on C1 and on the sign of E[Re A]
  (82 rows; 13 y = 0 rows on C1; 1 row with part of it NOT RESOLVED); outside the window a MISS on the
  sign through t_q while the flipped map's leading-order pair fraction stays below its turning value 4(1 + delta)/7, tagged
  CONJECTURE (60 rows, 46 of them past the law's range); read and report from the row where it reaches
  that value (28 rows, all at delta = 3/5, where the flipped map's zero-energy shell puts A = 0 at its turning
  point) and after t_q (196 rows in all).
- **C_LOCK**, a changed initial phase distribution (pair-locked seeds b-(0) = conj(b+(0)), each marginal the vacuum):
  a MISS on C1 wherever its allowance band lies outside 1 +- (tau + 2e) (57 rows); NONDISCRIMINATING where the band
  reaches within tau of 1 (39 rows); read and report outside the window (256 rows).
- **C_MODE0**, mode 0's phase fixed: an invariance check that must read MET on every row (each sample rotated as a whole by
  a unit vector exact to at least 2^-29, within 10^-7).
- **C_NOISELESS**, the vacuum noise set to zero: c0 = sqrt(N), c+ = c- = 0, which is the single trajectory exactly. It must equal the
  trajectory engine within the two integration bounds, read in the trajectory's frame, and it carries the trajectory's rows
  against the quantum. In the ensemble's frames the offsets are exact: f_W - f_traj = -1/N, and its X_NC reading obeys
  C1_NC = (N/(N-1)) A1^2/2 + (4n - 2N - 1)/(N(N-1)) (checked exactly on 400 of 400 random rational triples).
- **C_INSUFF**, insufficient sampling: the primary ensemble at M_ins = floor(M_c,min/9) = 57182 samples, plain estimator,
  M_c,min = 514642 (V2 at N = 6561, delta = -3/5, y = 4/243, t = 135/64); every first-order row predicted
  NOT RESOLVED or MISS, a MET refuting it. NOT RESOLVED is expected, with 3.74e-1 to 4.13e-1 MISSes expected by
  sampling chance alone over its 223 checks (the values check); on the other 269 rows it is read and reported.
- **P_PAIRS**, the matched pairs (3/5, s = 2/3) with (-3/5, s = 1/3), and (3/5, s = 4/3) with (-3/5, s = 2/3): at leading order
  A1 doubles, C1 quadruples and V^2 is equal at every t. At N = 729 and 6561 the quantum's ratios are predicted at their
  first-order values from line 48 (`BRIDGE_PAIR`, 10 of 10 rows equal to the controls lane's own evaluation); the
  trajectory's V^2 ratio is exactly 1.
- **Q_ZERO**, the quantum at y = 0: A1 = D2 = 0 exactly, checked against the certified bound; V^2 printed UNDEFINED.

## How a row reads, and its errors

- `BRIDGE_READ_RULE`: MET if |d| + e <= tol; MISS if |d| - e > tol; NOT RESOLVED otherwise. e = 3 SE + integration +
  rounding + the quantum's certified half width + truncation, each printed on the row (`BRIDGE_ERRORS`; the ensemble's
  integration term is a step-halving estimate on the first 2^16 samples). UNDEFINED rows are counted in neither; a row
  without a measurement prints NOT_MEASURED with its reason.
- eps_O = |<O>_q - O_cl| is printed on every `BRIDGE_AT` row for A1, C1, V^2, f and D2 and for each classical map (the
  trajectory, VNC, V1, V0), with its numerical and sampling bounds apart (requirement 5); the relative eps is taken on the
  law's value at the row, which stays positive at every frozen t with y nonzero; at y = 0, eps for A1, D2 and V^2 is
  printed absolute.
- A prediction is kept where the read gives its verdict (either one, where two are named), failed where it reads the other
  of MET and MISS, and NOT RESOLVED for its prediction otherwise; a control predicted to MISS counts as detected where it
  reads MISS; CONJECTURE rows are scored the same way and counted apart. Failed predictions stay.
- The single trajectory's, the ensemble's, each control's, the pairs' and the diagnostic's verdicts are kept separate
  (`BRIDGE_VERDICTS`).

## Sampling

The operator chose the sample design E4R on November 6, 2026, from the designs the cost lane priced (status
SET_BY_OPERATOR_E4R). Each point (N, delta, y) has one shared ensemble drawn from its one seed, and every clause reads a prefix of it.
The counts
follow a time staircase: the first M samples run to time t, M being the largest count that any row of the point at t or
later needs, so the samples that stop early are a prefix of those that run on, and a row reads all its observables on the
same samples. Every `BRIDGE_AT` row prints its counts (`M_VNC`, `M_V1`, `M_V0`, `M_FLIP`, `M_LOCK`, `M_MODE0`, `M_eint`,
`M_ins`), and `BRIDGE_SAMPLE_PLAN` lists each point's steps.

- Each variant has its own count. VNC carries E_VNC (A1, C1 and V^2 read with the control variate, f and D2 read plain), the
  pair and the diagnostic; V1 carries the pair and its part of the diagnostic; V0 is reported at 2^20 samples.
- On each check the plan sizes (E_VNC on A1, C1 and V^2, and at y = 0 on C1 and f; the pair; the diagnostic's V1 part; the
  controls' frozen MISS components), the count is at least four times the smallest count at which its 3-SE bound fits, so the
  bound sits at half the margin when the difference equals the prediction; the cost lane puts the chance that a correct run
  then reads NOT RESOLVED at about 0.27 percent or less per check. On the E_VNC rows the count is also at least
  min(2^25, four times the plain estimator's count).
- E_VNC's f and D2 at y != 0 read plain at the row's M_VNC: there the 3-SE bound fits tau on 64 and 35 of the 70
  rows, and with a 3-SE excursion on 37 and 15; where the bound lies outside tau (6 rows for f, 35
  for D2) the expected read is NOT RESOLVED.
- Rows past the first-order range read every variant at 2^20 samples.
- The integration error is estimated on the first 2^16 samples of each variant, rerun at half the step.
- The J flip and the pair-locked seeds run at each point's thresholds for its frozen MISS rows, through the last of them,
  and at 2^20 on later rows; the uniform-phase partner of VNC's fixed mode-0 phase (MODE0) on the first 2^16 samples; the insufficient-sampling control on the
  first 57182.
- The generator recomputes every count from the cost lane's closed forms and matches the cost lane's own rows; at each
  row's count it checks every 3-SE bound the plan sizes, and it reads the control verdicts by exact comparison, equal to
  the frozen ones on all 352 rows (`BRIDGE_CHECK`).
- Seeds: the first 8 bytes of sha256 of the point's seed string, printed in its `BRIDGE_POINT` row. Uncertainty: 3
  standard errors at the row's count; V^2 by the delta method with the covariance from the same samples. The
  control-variate estimator, the ensemble lane's exact linear trajectory as that lane froze it, is the one read for E_VNC,
  E_VNC_ZERO and the diagnostic; the plain estimator for E_PAIR and C_INSUFF; both are printed on every row.
- Before any run the ensemble integrator gains a variant mask, the per-record sums of f^2, B_W, Re Z times X and (Re Z - Re Z_lin)(X - X_lin), exact sums of squares
  for every variance, and a start index, so that each step of the staircase runs as its own batch (`BRIDGE_ENGINE_CHANGE`).
- Cost: 5.050 x 10^9 variant-sample time units, 84.2 to 105 thread-hours at the ensemble lane's measured rate, about
  13.7 hours at the machine's measured floor of 102631 per second, two 3-thread processes together (CONJECTURE, scaled from
  measured rates; a dedicated 8-thread rate OPEN). The sampling amendment of November 6, 2026 (below) sets 5.897 x 10^9.

## Sampling amendment of November 6, 2026 (f at y != 0)

The operator approved, on November 6, 2026, one increase of the E4R sampling: f at y != 0 is sized by the plan's own
4 x M3 rule (the E4R check's hold H2), at 1.168 times the E4R cost (94353772847/80806023906; the operator authorized 1.17). The amendment is
recorded in its own dated file, [`AMENDMENT-2026-11-06-F-SAMPLING.hbp`](AMENDMENT-2026-11-06-F-SAMPLING.hbp), before any
blind run. `PREDICTION.hbp` stays as frozen: sha256 `fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892`,
873 lines, every value, band, verdict and tolerance as it was.

- The rule: on each first-order `BRIDGE_AT` row with y != 0, the VNC requirement is the larger of its frozen requirement and
  4 x M3_f, where M3_f is the smallest count at which f's plain 3-SE bound, at 1.04 times its leading-order sd (exact
  Gaussian moments), fits tau(N). Each point's VNC staircase is then rebuilt by the plan's own rule.
- 33 rows' M_VNC rise, each to its own 4 x M3_f, on 14 points' VNC staircases (one `BRIDGE_AMENDED_AT` row per row, with
  its frozen line number, and one `BRIDGE_AMENDED_STAIRCASE` row per point, frozen and amended steps in M@t notation). The
  largest is N = 81, delta = -3/5, y = 2/27, t = 1/16: 5475421080 to 6330267356.
- Every other count equals the frozen rows: M_VNC on the other 319 rows, M_V1, M_V0, M_FLIP, M_LOCK, M_MODE0 and M_eint on
  all 352 rows, M_ins = 57182, and the V1, V0, FLIP, LOCK and MODE0 staircases on all 28 points. The generator's own row
  writers, rerun with the amended counts, match the frozen file on 11469 of the 11502 fields of the 352 rows; the 33 others
  are those M_VNC values. 16 `BRIDGE_DIAGNOSTIC` precision fields and the `BRIDGE_SAMPLE_PLAN` steps of the 14 points also
  print moved counts; for the run they read at the amendment's counts.
- Expected reads at the amended counts: f at y != 0 has its 3-SE bound inside tau on 70 of 70 rows, and with a 3-SE
  excursion also on 70 (frozen: 64 and 37). D2 keeps the original rule; it is read plain on the same VNC samples, so its
  bound fits tau on 38 of 70 rows and with an excursion on 15 (frozen: 35 and 15); the expected read is NOT RESOLVED on the
  32 rows where the bound lies outside tau, and each is reported as read. The f increase sizes f; D2's precision stays at
  the original sampling level.
- Every other sized check is as frozen: E_VNC with the control variate 223 of 223, the plain floor on 83 of 83, E_VNC_ZERO
  f 13 of 13, E_PAIR 83 of 83, the diagnostic's V1 part 14 of 14, C_JFLIP 156 of 156, C_LOCK 57 of 57, and the 352 control
  verdicts equal to the frozen ones. The plain bound of A1, C1 and V^2 now fits on 137 of 223 checks (52 with an
  excursion), against 123 (47) frozen.
- Cost: 94353772847/16 = 5.897 x 10^9 variant-sample time units (primary 5.469 x 10^9; e_int 1.139 x 10^8 and controls
  3.141 x 10^8 as frozen), up from 5.050 x 10^9 by 13547748941/16 = 8.467 x 10^8, a ratio of 1.168; 98.3 to 123
  thread-hours at the ensemble lane's measured rate, about 16.0 hours at the machine's measured floor of 102631 per
  second, 2.3 hours more (CONJECTURE, scaled from measured rates; the duration of the amended workload is measured only
  when it runs).
- Check: the 33 rows, the 70 values of 4 x M3_f and the VNC work agree exactly with the E4R check's own forms
  (`ix_extra.hbp`, option f: 33 rows, VNC 3.5995 x 10^9, increment 5.8401 x 10^9 - 4.9934 x 10^9 = 8.467 x 10^8). The
  check priced the increment on its base before the e_int of the controls (hold H4, 5.697 x 10^7), which gives its
  5.840 x 10^9 total; on the frozen plan the same increment gives 5.897 x 10^9.

## The quantum side

The full exchange-even space at N = 81 and 729 at every frozen time, and at N = 6561 for delta = +3/5 (the operator's word
"Run them", November 5, 2026, about 10 to 14 hours at 4 runs at a time). At N = 6561, delta = -3/5, the clocks lane's
energy-shell block, gated by its printed tail certificate (tail_max at most 10^-10 in every window) and by agreement of K
and K + N/16 within their certified widths, with the full space as its fallback. The `BRIDGE_AT` rows per (N, delta): N = 81: 47 at 3/5, 45 at -3/5; N = 729: 62 at 3/5, 63 at -3/5; N = 6561: 70 at 3/5, 65 at -3/5. Half widths at most 10^-6 of
each value; V^2 read only where the certified lower bound of C1 is positive; the quantum rows and their sha256 are filed
before any classical row at the same point is read (`BRIDGE_QUANTUM_PLAN` and the carried `BRIDGE_QUANTUM_GATE_*` rows).

The quantum engine's streaming layout (`stream`, line 451) reproduces both first-correction receipts in every field
but array_bytes. On the full space at N = 6561 (the allowed point delta = 1/2, y = 1/324) it ran 1.978 times as fast
as `point` one run at a time (3 interleaved repeats, spread 1.940 to 2.006) and 1.928 times as fast four at a time
(2 repeats, spread 1.862 to 1.993), MEASURED, at a peak of 1.04 GB against 1.29 GB per run. The hours above are at
`point`'s rate.

The quantum engine's Q = 0 sector layout (`sector`, line 451) runs the points at y = 0. There H keeps Q = n+ - n-,
and |N,0,0> has Q = 0, so the run holds its amplitude on one state per even shell, (q, m) = (2j, j): K/2 + 1 states,
3,281 of the 10,768,242 at N = K = 6561. What `point` takes from the whole block (c, E, the elements' rounding bound,
norm(B), the tail norm and the read's terms of the states at amplitude 0) the sector layout takes from the whole block
too, shell by shell, and it prints every field `point` prints but array_bytes, which it counts for its own layout:
17 of 17 READ rows at 10 allowed points from N = 81 to 6561, at K = N and at blocks K < N with odd and even K
(`polariton-first-correction/RECEIPT-SECTOR.hbp`), and, at the frozen y = 0 time list to t = 207/32 (N = 6561,
delta = 1/2), the output of a separately written sector implementation (the Use lane's), byte for byte, MEASURED;
`point` at that length is projected at about 4.3 h on this machine. The sector run took 13.5 s at a peak of 2.5 MB; `point` at N = K = 6561 took
41.2 s for the first of its 414 windows and 89.6 to 104.3 s for the first two at a peak of 1.26 GB, two runs at a time
on the same machine, MEASURED. Three sabotaged sector modes (the Q != 0 couplings dropped from the whole block's
account, the basis in the wrong order, a run at y != 0 with the refusal lifted) each fail the checks
`polariton-first-correction/CONTROLS-SECTOR.hbp` names, and the mode refuses y != 0 with exit 2 and no row.

## The engines and their corrections (November 6, 2026)

The engine changes of `BRIDGE_ENGINE_CHANGE` (lines 445 to 451) are filed beside the frozen file, which keeps its bytes
(sha256 `fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892`).

- [`engines/ensemble/`](engines/ensemble/) is the ensemble integrator twens 0.3.0 (Rust 1.81, integers only, float_used=0),
  source `src/main.rs` sha256 `723b36745af6c926849ff7a6da74d8c82007dfc4071761795bb639fcd8d4a609`. It carries the variant
  mask, the per-record sums with exact sums of squares, the start index, the per-sample rounding bound printed beside every
  row (`TWB_ROUND`, `TWB_PAIR_ROUND`), the noiseless path NL, and the sha256 of its source in its head row. On Windows it
  links with /Brepro, so a rebuild of that source gives the same binary: `ac7ff8f41279f55a57f5c47823950c225c8aa111573f52832d52bd6a0e5ca44f`
  (x86_64-pc-windows-msvc) at three paths and `75530df9c7414b9a1b28f7408cbacd512f35d48836e2a6823beefb4941b9598d`
  (x86_64-unknown-linux-gnu) at three (MEASURED). The second seat's round-2 holds H1 to H7 take MODE0's start bound against
  its drawn integer unit vector and set the stage region from max + min/2 of each mode's components; with them all seven
  variants run to t = 493/64 at N = 6561, delta = 1/2, y = 1/243, where the earlier source e5682f1d stopped with exit 4
  (MEASURED, three runs each).
- [`engines/trajectory/`](engines/trajectory/) is the trajectory integrator (`traj_int.py`, sha256
  `c08a0c75bf7d089875d2e6017b731bac767fb93fff849464f9af9d9849afb504`), with its line-446 gate, tests, audit and float scan,
  its README.md and its SHA256SUMS.
- [`engines/jet/`](engines/jet/) is the flow-map jet jetens 0.2.0 (Rust 1.81, integers only, float_used=0), source
  `src/main.rs` sha256 `ac5672374f95e9b9f44c1675ef1e2ea028ac702d2bbe27c0ee5880f077d53fb8`, binary
  `334dddec67fc557ee66a8b7259f91c25b178c86f2ed4bcb343babb63486cec1e` (x86_64-unknown-linux-gnu). It is the ensemble engine's
  own RK4 map at dt = 1/64 expanded in the start noise, so its exact average under the engine's own noise law (the
  popcount Binomial(4096, 1/2) moments, the ideal Gaussian's printed beside it) is the number the frozen Monte Carlo
  estimates up to the order-P truncation, with no sampling error. [`PLAN-JETS.hbp`](PLAN-JETS.hbp) runs it on the 83 first-order `BRIDGE_AT` rows (VNC and
  V1; C1, A1, V2, f, D2, the sign of E[Re Z] and the pair N^2(C1_V1 - C1_VNC)), keyed by each row's line and with the
  amendment's M_VNC on its 33 rows, beside the Monte Carlo as an independent second answer filed by hash before the Monte
  Carlo runs (the operator's decision of November 6, 2026). `tools/drive_jets.py` runs the plan: a dry run, the proof at
  allowed analogs, and the reserved points only with `--opt-in=RUN_THE_RESERVED_JETS_FOR_THE_SEAT`.
- [`CORRECTIONS.hbp`](CORRECTIONS.hbp) holds 28 readings of frozen lines from the engine rounds' holds (ensemble-1 to
  ensemble-27, trajectory-1). Each frozen_text is a byte-for-byte substring of its frozen line and occurs once on it; every
  row has values_moved=0.
- C_MODE0 (ensemble-26 and ensemble-27, kind READ_DETAIL): the read rule's e carries the engine's rigorous rounding bound,
  and on C_MODE0's paired difference that bound lies above the 10^-7 tolerance from t = 1/2 on (1.08 to 2.0 x 10^5 times on
  the worst of A1, C1, f and D2 at allowed analogs, MEASURED), so C_MODE0 is expected to read NOT RESOLVED from t = 1/2 on.
  Beside each row the read prints, for information only, the measured difference of the row's first 2^10 samples against a
  2^-120 run of them. The frozen prediction and its tolerances stay as frozen (the operator's decision of November 6, 2026).
- [`ENGINE-CHANGES.hbp`](ENGINE-CHANGES.hbp) holds one row per engine change's result and per second-seat check: 3 for the
  quantum engine, 7 for the ensemble integrator, 5 for the trajectory integrator, 1 for the flow-map jet.
- The workflow `.github/workflows/polariton-bridge.yml` runs four jobs: `frozen` (PREDICTION.hbp at its pin, every
  SHA256SUMS, LF line endings), `ensemble` (the Rust 1.81 gate, the float scan, binary provenance, the guard's refusals,
  TEST-RUNS-T1B.hbp byte for byte) and `trajectory` (the engine's sums, the reserved check, the tests with and without
  -O, the float scan, the audit, the line-446 gate) and `jet` (the Rust 1.81 gate, the float scan, binary provenance, the
  guard's refusals, the driver's dry run, one analog jet byte for byte).
- [`reviews/opus55-engines-round2-20261106/`](reviews/opus55-engines-round2-20261106/) holds the four round-2 reports, the
  stage check's report and the disposition of every hold (`HOLDS-APPLIED.hbp`).

## Order (`BRIDGE_ORDER`)

1. This prediction is pushed.
2. The engine changes the lanes name (`BRIDGE_ENGINE_CHANGE`): dyadic time reads in the quantum engine; the trajectory and
   ensemble integrators, the latter with the sample plan's variant mask, per-record sums and start index. Each reproduces
   its filed receipts byte for byte where they overlap. Any other change before the
   blind runs, such as a streaming or memory-layout change of the quantum engine, passes the same gate on every receipt
   field but array_bytes, which it prints for its own layout beside the filed value.
3. A baseline at allowed points.
4. A second-seat review of the engines.
5. The blind runs.
6. The read, with the blind status kept.
7. The attack on the read.

The issue's own order is met: PR #8 and the first-correction stage (PR #11) are merged and both are ancestors of this
lane's base (`BRIDGE_SOURCE`).

## Choices made in the freeze

Each is a `BRIDGE_FREEZE_CHOICE` row with what the lanes and the seat said, the difference, the choice and the reason:
FC01 the epsilon correction set aside; FC02 one three-valued reading rule; FC03 three standard errors; FC04 the ensemble
sizes, the operator's design E4R; FC05 the ensemble's first-order predictions at every time inside the range;
FC06 the clock band at the frozen times; FC07 the law band from line 39, screened by line 48's own V^2 correction; FC08 the
pair-locked control's allowance band; FC09 the noiseless control as the trajectory itself; FC10 the insufficient-sampling
control on the plain estimator; FC11 the quantum's V^2 at y = 0; FC12 the matched-pair tolerance; FC13 the diagnostic's
classification rule, its precision set by the sample plan; FC14 bars and spaces in carried rows; FC15 lane rows kept in
design only; FC16 the trajectory's own-series check at the anchors; FC17 further engine changes; FC18 rows past the return
lower bound; FC19 the J flip's sampling conditions and its sign past the window; FC20 the pair tolerance's coefficient,
K = 43, kept by the seat with the values check's evidence row.

## Open items (`BRIDGE_OPEN`)

The quantum engine's dyadic reads and their gate; the energy-shell margin at N = 6561, delta = -3/5 until the engine prints
its tail; the full space at N = 6561 (16.8 times the largest filed state); the ensemble's second-order residual; V0 at
N = 2187; the controls' own 1/N corrections; the ensemble and the controls at the clocks; the trajectory's own series at
delta = 3/5 clocks and the exact first return; the basis of the clock band; the quantum side of the anchor tolerance; the
control-variate reduction at the blind points; the Fock start's Wigner negativity beyond first order; the epsilon
correction; the engine changes the sample plan needs; the diagnostic's resolution between N = 81 and 729, resting on the
realised control-variate cut; the fabric's answer to the seat's council envelope, recall's index of this work (count 0 for
polariton) and the owning seats; the exposure audit's own blind spots; the text of the earlier relays; the engines' printed
bounds; the operator's word on sizing f at y != 0 by the plan's rule (1.17 times the cost).

## Scope

This model and these observables, on a finite closed system: three modes, N = 81, 729 and 6561, delta = +-3/5, at the
frozen times. What the bridge can give is a controlled quantum-to-classical approximation here. Whether nature is
discrete, and which mechanism supplies decoherence, stay separate questions, OPEN.

## Files

- [`PREDICTION.hbp`](PREDICTION.hbp), [`README.md`](README.md), [`SHA256SUMS`](SHA256SUMS) (sha256 of PREDICTION.hbp, README.md
  and .gitattributes), and [`.gitattributes`](.gitattributes) (`* text eol=lf`, as in `../polariton-first-correction/`),
  which keeps every file here LF on any checkout.
- [`AMENDMENT-2026-11-06-F-SAMPLING.hbp`](AMENDMENT-2026-11-06-F-SAMPLING.hbp): the operator's sampling amendment of
  November 6, 2026 (f at y != 0 by 4 x M3), 57 rows, recorded beside the frozen `PREDICTION.hbp`, which it leaves as frozen.
- [`HOLDS-APPLIED.hbp`](HOLDS-APPLIED.hbp): one row per hold of the three checks, with what the generator did with it.
- `design/trajectory/` FINDINGS.txt (sha256 `20d8101fe1bf5d38d4e1b0ce254be8e85575c78c7c28dccfb6eb2cb1148e1a70`, 178 lines) and PROPOSED-ROWS.hbp (sha256 `1479b6b8cbeaae79e96b40e4eb043688acbdbf43bb6ea4caf26544c990d2c0ec`, 172 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-trajectory-20261105/`.
- `design/ensemble/` FINDINGS.txt (sha256 `a604c711aa2b27eeffde6508b651ca25f3f80efacc67d84aabf5711b3e59aaea`, 254 lines) and PROPOSED-ROWS.hbp (sha256 `1f8e493fa7659e6a6b6b2d47483c95e160ef1961095438e5a346a6822e457630`, 155 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-ensemble-20261105/`.
- `design/clocks/` FINDINGS.txt (sha256 `02be8a4028d257e1c4308a3731c8c31252689ac059c6c7f8d0c8b0c420038560`, 312 lines) and PROPOSED-ROWS.hbp (sha256 `92bc50b0f6861a8ab86c33546c5a39f8e14c0048f50f66199f2d6b259b963ff4`, 91 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-clocks-20261105/`.
- `design/controls/` FINDINGS.txt (sha256 `9755bb3a46f35eba28500750ebf2163d6c9d5de6c4b4c608b9fbd0b05b133b66`, 287 lines) and PROPOSED-ROWS.hbp (sha256 `9091896d690d0ccd8ac779137c5eec522665bc79ee930a6f704bf78c3a9430b5`, 33 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-controls-20261105/`.
- [`ENGINE-CHANGES.hbp`](ENGINE-CHANGES.hbp) and [`CORRECTIONS.hbp`](CORRECTIONS.hbp): the engine changes' results and
  reviews, and the readings of frozen lines from the engine rounds' holds; PREDICTION.hbp keeps its bytes.
- [`engines/ensemble/`](engines/ensemble/) (twens 0.3.0, `src/main.rs` sha256 `723b36745af6c926849ff7a6da74d8c82007dfc4071761795bb639fcd8d4a609`)
  and [`engines/trajectory/`](engines/trajectory/) (`traj_int.py` sha256 `c08a0c75bf7d089875d2e6017b731bac767fb93fff849464f9af9d9849afb504`,
  with its README.md and SHA256SUMS); the workflow's `ensemble` and `trajectory` jobs run them.
- [`PLAN-JETS.hbp`](PLAN-JETS.hbp) and [`engines/jet/`](engines/jet/) (jetens 0.2.0, `src/main.rs` sha256
  `ac5672374f95e9b9f44c1675ef1e2ea028ac702d2bbe27c0ee5880f077d53fb8`, with its reader, driver and plan generator): the jets
  beside the ensemble's first-order rows; the workflow's `jet` job runs its gate, its guard and its driver's dry run.
- [`reviews/`](reviews/): the second seat's reports, one folder per piece of work, each with its SHA256SUMS.
