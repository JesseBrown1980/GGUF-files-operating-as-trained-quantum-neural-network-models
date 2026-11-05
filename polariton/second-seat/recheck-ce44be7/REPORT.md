# The second seat's recheck of the polariton test, at `ce44be7`

Four lanes ran and none failed. Their reports follow verbatim. Each lane's findings, holds, rows and code are in the folders beside this one. The mutants' own row files, 20 MB, and files of 1000000 bytes or more are in the tools tar held on this machine at `D:/safety-backups/opus55-polariton-recheck-20261105-tools.tar.gz`, 982 files, SHA-256 `930b09b572ee2c1ce03f79c0b204ba4783591bc2b2c778d2553a5ae7509f83b6`, with its upload to the Hugging Face dataset OPEN.

## The contact law

**Head checked:** `git -C C:/tmp/qnn-polariton-wt rev-parse HEAD` printed `ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd` at the start and again at the end. The worktree is clean, and nothing of mine is still running.

**Verdict:**
- **The law survives as stated:** derived independently, and it holds wherever depletion is small.
- **Refuted:** the README's "V² holds well past each of its parts", as a general statement.
- **Refuted in part:** the author's position-spread conjecture.
- **In tension with the paper:** the 2.6% reading, against the paper's own continuous-pump phase data.

All three holds on these are filed. Everything is on N = 81, 243, 729, with N = 2187 and above only as noted.

## What I ran (no code shared with the author)
- **`cheb/`:** integer Chebyshev propagator, Rust 1.81, `clippy -D warnings` exit 0, `float_used=0`. Bessel coefficients come from Python big integers. Norm off is at most 8e-18, energy/N at most 4e-18, on the 152 receipt rows.
- **`t2_anchor.py`:** big-integer Taylor series at 2⁻⁶⁸². It agrees with `cheb` to about 17 digits on the three N = 81 anchor rows.
- **`tw/`:** truncated Wigner in integers, Q40 RK4, with Gaussians from exact binomials.
- **`t5_firstcorr.py`:** exact normal-ordered algebra with Wick and τ integrals over Q(γ)[i], no CAS.
- **Predictions frozen first:** `out/LAW-PREDICTIONS.hbp`, sha256 `c6310e4a…b236061`, 1,616 rows. My stated expectations are in FINDINGS under F2-pre.

## What survives

**1. The law. DERIVED, then MEASURED.**
- I derived it before reading the author's steps, by displaced Bogoliubov with a number-conserving expansion; each step that could fail is listed in F1.
- At leading order, A/√N = z = q_s + i p_a, a complex Gaussian, with V² = |⟨z⟩|²/⟨|z|² − 1⟩.
- The operator identity holds as integer matrices for N = 0..25, with 0 rows differing.
- It also holds exactly on 109 random rational states (3 more are 0/0), and to 1e-18 on the evolved states of the 152 receipt rows.

**2. README digits and counts. MEASURED.**
- My route matches all 152 shared receipt rows. The worst relative offset on conversion rows is 1.5e-6 (on C₂), and on ⟨A⟩ it is 4.2e-7.
- The offset is in the receipt: on the N = 81 anchor row the receipt sits 1e-6 from my two routes, which agree with each other.
- The README's table, 29/29, 21/21, 21/21, 17/21, 58/58, the 810 energy offset, and the 35-row ranges all reproduce.

**3. New rows in the band. MEASURED.** Read/law at N = 729, f ≤ 1/20, over δ = −1..3/4:
- V² 0.9859–1.1025
- A₁ 0.8844–0.9994
- C₁ 0.7094–0.9979
- D₂ 0.7516–0.9995

The worst row is δ = −1, t = 3, where predicted f is a poor scope. N × deviation converges to the first correction's limit: at δ = −1/2, s = y√N = 1/4, t = 1, V² reads 1.82, 1.88, 1.91 → 1.93.

**4. Outside the band, δ > 1: the continuation holds, reported as read. MEASURED.** The repo never froze this; only my own file did.
- The sign test passes on 97 of 99 rows with |Y| < 1 and 81 of 81 with |Y| > 1, at N ≥ 243.
- δ = 2, N = 729: 1.1887 against 1.1887. Near the pole: −33.06 against −36.81.
- The pole is real, and its shift is the first correction: C₁ = 0 at t = 2.982 read, 3.014 law, 2.981 law + first.
- V² > 1 at leading order, so "the shot term lets it pass 1 at finite N" belongs to inside the band.
- ⟨A⟩ flips sign exactly at δ = 1: opposite to y on 612 of 612 rows below, same sign on 252 of 252 at or above.

**5. Outside the band, δ < −1: holds at early times. MEASURED.**
- N = 729, t ≤ 1: V²/law 1.0010–1.0073. C₁ < 0 and V² < 0 on 0 of 270 rows.
- The period pulls, as a 1/N effect: at δ = −5/4, s = 1/4, the first A₁ minimum reads 7.17, 7.77, 8.13, 8.29, 8.37 against the law's 8.378.

**6. δ = +1 forms. New: DERIVED and MEASURED.**
- A₁ = 2|y|t⁴(1 + Ny²/2)/N
- C₁ = −2t²[1 + 2t²(1 + Ny²)]/N²
- V² = −y²t⁶(1 + Ny²/2)²/(1 + 2t²(1 + Ny²))

So V² → 0 from below, at rate 1/N, and it has a pole at finite N (−25.06 at N = 729, s = 4, t = 2). These forms also fill in the 12 C₁ rows the README's reader holds out. They track the receipt where t⁴/N is small, for example −24 ppm against −24.5 at N = 6561, t = 4, and drift by t = 8 there.

**7. First correction, general (δ, y). DERIVED, exact.**
- Closed forms are in F5: 60/60 coefficients held out, and 672 coefficients as typed with 0 mismatches.
- The machine reproduces the README's J₁ (33/33) and w₁ (4/4), with first-order energy conservation identically zero.
- At δ = 0, u = 1, with C₁ = C₀/N + (C₁₀ + Ny²C₁₁ + N²y⁴C₁₂)/N²:
  - C₁₀ = 6t sinh 2t − (5/2)cosh 4t + 3cosh 2t − 1/2
  - C₁₁ = −8t sinh t − 16t sinh 2t − 10cosh 4t + 42cosh 3t − 40cosh 2t + 22cosh t − 14
  - C₁₂ = 136t sinh t − 68t sinh 2t − 5cosh 4t + 42cosh 3t − 16cosh 2t − 234cosh t + 213
- The four C₁ misses read 1.0112, 1.0071, 1.0096, 1.0038 of law + first (0.917–0.945 of the law alone).
- The worst offsets on the 21 receipt rows at f ≤ 1/20 fall by 2–10×: A₁ 0.040→0.0035, C₁ 0.084→0.011, D₂ 0.072→0.009, V² 0.0099→0.0041.
- Truncated blocks to N = 531441 show the remainders falling as 1/N.
- The README's w₁ is the s → 0 part only. There is an s² term, and without it N = 729, s = 4, t = 1 reads 0.961; with it, 1.002.

**8. The arithmetic of the 2.6% reading.** Reproduced: 0.0172, 0.0690, y√N = 0.093, 0.19.

## What is refuted

**A. "V² holds well past each of its parts" (MEASURED).** The README's numbers are right, but they don't support the sentence.
- **21 of the 35 rows have Y > 1, and all 21 sit above the law.**
  - Under a ceiling near 1/law, Y_read/Y runs 1.12–6.42, with one row above 1.
  - Setting V² = 1 on those 21 would still put 9 of them inside the quoted range.
- **The 14 rows with Y ≤ 1 are real agreement:** V²/law 0.96–1.09, Y_read/Y 0.96–1.18, read f up to 0.49.
- **All 35 stop at t ≤ 3.** The extreme row (N = 243, s = 4, t = 3, A₁ 0.06 of form) reads 1.007, 0.883, 0.472, 0.070 at t = 3, 3.25, 3.5, 3.75.
- **At the first f peak, N = 729:** V²/law 0.87–1.14 at δ = 0, 1/2.
- **Small Y:** it leaves 5% with C₁ at 0.09–0.42 of form, not 0.004. It falls toward about π/4: exact V²/Y = 0.848 at the peak at N = 729, and 0.812 at N = 59049 (TW).
- **Past the return, N = 729:** V²/law runs from 0.001 to 22.5 up to t = 12.
- **V² has no true ceiling at 1:** V² < 0 and V² > 1 both occur at N = 3 and at large N.

**B. The reason, which the README leaves OPEN (DERIVED and MEASURED).**
- At large γt, with ε = (5 − 2δ)e^(2γt)/(8γ⁴N):
  - A₁/law = 1 − ε(1 + Y/2)
  - C₁/law = 1 − 2ε(1 + 2Y + Y²/2)/(1 + Y)
  - V²/law = 1 + εY/(1 + Y)

  The ratio of machine coefficient to this form reaches 1.000 at γt ≥ 10.
- At small Y, past first order, V²/Y = ⟨ρ|ζ|⟩²/(⟨|ζ|²⟩⟨ρ²⟩). This is a Cauchy–Schwarz cosine² between final amplitude and seed amplitude, stationary at first order.
- At N = 59049 (TW) this matches within 1.5% to t = 7. At N = 729 the exact read is 1.12 of it at the peak, so it reads as a large-N limit. The exact state at that N is CANNOT_SEE.

**C. The author's conjecture: half right.**
- **Holds:** the position follows the seed, with cos(θ − arg ζ) ≥ 0.998 from t = 2.5 to 8.75. Phase coherence follows the Rician of the law's Y within about 3% up to the peak.
- **Refuted:** V² is not that spread.
  - At N = 59049 it reads 1.27 of R₁² at t = 3, equal near the peak, and 0.54 of it at t = 8.
  - From t = 6.5 to 8.5, V²/law falls from 0.837 to 0.411 with the position unchanged.

**D. Recurrences (MEASURED, exact).** The row at N = 81, s = 4, t = 3 sits exactly at the first f minimum, f = 0.047. V² swings 0.995 → 0.0095 → 0.911 → 0.0053 → 0.624 with the period of f. At the return:
- ⟨A²⟩/⟨A†A⟩ = −0.749: the weight of A moves to its imaginary axis, with the k pattern at ±π/2.
- ⟨B⟩ is negative, the one row of 94 that is.

At small Y a return goes the other way: 0.21 against 0.029.

**E. The 2.6% reading against the paper's own data (arithmetic MEASURED; the mapping stays CONJECTURE).**
- Y of 0.0175–0.074 predicts a shot-to-shot spread of cos θ of 0.68–0.70.
- SI Fig. S23 (continuous pumping), read from the figure's raster against its ticks, gives 0.353, 0.178, 0.118, 0.130 at 15–25 mW. That corresponds to Y ≈ 1.4–4.2 and y√N ≈ 0.8–1.4, which is 4–16 times larger.
- My first read by eye was off by up to 0.05. The correction is filed beside it in FINDINGS.
- This is a tension to carry, not a verdict on the law: Fig. S23 is a pumped, lossy steady state and the law is a closed quench. φ's meaning is inferred from 0.7 at random phase.
- Refutable predictions the law adds:
  - C₁ = 4ρ(1 − δ) ≈ 0.02(1 − δ), independent of V²; this is the sharpest test.
  - D₂ = A₁²/(4(1 − δ)).
  - g¹ fast amplitude 2ρ = 0.99% against the paper's about 1.5%.

## Holds (`HOLDS.txt`: each OLD verified byte for byte, once, at this head)
- **H1, high:** replace "Past the depletion range" with scope, split rows, how far it reaches, the reason, and returns.
- **H2, medium:** Open bullet: "why V² holds past both" → "V² past the first maximum of f, where it leaves the law on both sides".
- **H3, low:** "Each deviation falls as 1/N" → N × deviation values and their limits (ratios 2.0–2.8, not yet 3, by N = 2187).
- **H4, low:** "reads 1.20 on one row at N = 81" → three rows (1.02, 1.06, 1.20) plus the δ > 1 reading.
- **H5, low:** pinned digits 0.9998, 1.0031 → 1.0000, 1.0032 (README's come from a rounded ppm integer).
- **H6, low:** 0.916 → 0.917 (the row is 0.91650).
- **H7, low:** w₁ scope: add the Ny² term.
- **H8, low:** ⟨A⟩ opposite to y at δ < 1 and same sign at δ ≥ 1; ⟨B⟩ positive up to the first return.
- **H9, medium:** add the Fig. S23 spread and the C₁ test to "Reading the paper's 2.6%".

F9 also offers text for closing the README's OPEN first-correction items. Closing them corrects no fault, so they carry no hold number.

## What I could not check (CANNOT_SEE)
- **N = 2187 full-space grids:** stopped. One chain took about 12 minutes with other lanes loading the machine, so 35 chains were out of budget. The grids are complete at N = 81, 243, 729. N = 2187 has the receipt's 4 rows plus 24 truncated rows with edge weight read; truncated rows reach N = 531441.
- **Exact state at N ≥ 2187 past the f peak:** those statements rest on TW, validated against exact rows at N = 81 and 729.
- **Leapfrog offset:** no rerun of the engine at a smaller step. It would only confirm the 1e-6 offset, and it changes no quoted digit.
- **Hosted run, fabric, recall, owning seats:** not asked, per this lane's scope. Nothing here says green.
- **Paper:** Nature final text and later arXiv versions unread; I used the earlier lane's arXiv v1 copy.

Paths, all in `C:/tmp/opus55/polariton-recheck-contact-20261105/`:
- `FINDINGS.txt`
- `HOLDS.txt`
- `LANE-RECEIPT.hbp` (sha256 `fa0519e6…7ee9b1b`)
- `out/`

## The window of the pair state and the plane wave

**VERDICT at ce44be7: the numbers stand, and five text holds are proposed: 2 medium, 3 low.** None changes a receipt row or a tolerance. Everything here is scoped evidence from this laptop. No owning-gate claim is made, and the hosted run was not touched.

**Head checked:** `ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd`, before and after.

**One slip on the read-only rule:** my `t5_evenblock.py` imported `second_route.py` by path. `python -I` ignores `PYTHONDONTWRITEBYTECODE`, so at 04:16:45 local it wrote `polariton/__pycache__/second_route.cpython-313.pyc` into the worktree. I found it at 04:18 through `git status` and removed the file and its empty folder. Later runs use `-B`. `git status` is empty now, no tracked file was touched, and none of my processes remain.

## What I ran
All in `C:/tmp/opus55/polariton-recheck-window-20261105/code`, with rows in `out/`. Python integers and Fractions only, no engine code, and no float in the model arithmetic.

- **Plane-wave series:** exact rational from one plane wave (`pw_lib.py`), N = 9 to 729.
- **Parity blocks:** even and odd at K bits (`ed_lib.py`), N = 3, 9, 27, 81, up to 1200 bits.
- **Level scans:** chain levels over all P on rational grids, every N ≤ 27 (2,175 of 94,250 points took P = 1) and every N ≤ 24 at step 1/64, plus targeted scans to N = 2187. The P = 0 / P = N crossing ran to N = 19683.
- **y → 0 response:** exact chains at 600 bits, N to 32768, with Richardson in 1/N.
- **Reduced chain basis:** at fixed s, to N = 6561.
- **Earlier lane's Q48 block solver:** used at N = 81 and 243.
- **`even_block` checks:** 3,180, plus doctored rows through the route's own `compare_full`.
- **Reader:** `read_prediction.py` rerun on the receipt.
- **Row reads:** all 196 window rows and all 45 table cells.

## What survives

**Item 1, the forms (DERIVED, then MEASURED).** Exact in N, with D₁ = u(N−1)/N − x, a = 2(u(N−2)/N − x), b = u(N−1)/N, κ² = 2(N−1)/N²:
- A₁/y = 2/D₁
- D₂/y² = 4|u−x−1+(1−2u)/N| / (D₁(ab−κ²))

These equal the rational series exactly on 20 of 20 and read the table's gaps:
- (1/2, −1/4), N = 729: exact-in-N 1.79168, read 1.7917, limit form 1.7778
- (3/4, −1/8), N = 243: exact-in-N 0.45197, read 0.4520, limit form 0.4354

Mean field gives the same limit by a separate route.

**Item 1, the even mix.**
- B's sign and size come from one plane wave. Exchange maps B to B†, so the two branches contribute equally, and the cross terms are of order y^(2N−2).
- The even level lies lower on every window point read: 72 of 72 at N = 3, 9, 27 and 12 of 12 at N = 81, where gaps run from 5e−48 to 9e−172 and the ⟨B⟩ offset is at most 2e−45. The sign of the splitting at small y is also derived.
- The account does not reach its number by an accidental cancellation. The direct route and the pair route are of the same order, and the form's numerator is their difference. They cancel only at u−x = 1, and the receipt's four points sit at |W| = 1/8 and 1/4, where W = u−x−1.

**Item 2.** Away from the failure cases below, the forms hold at large |x| and near the edge. For x = −1 to −100, u ≥ 1/4, D₂/y² stays within 3.6% at N = 243 and 1.1% at N = 729.

**Item 3.**
- All three edges are right, each with a 1/N shift. N(x_cross − x_edge) reads −0.37504 against −0.37504 at u = 1/2, and x_edge values match the README.
- New exact point: u − x ≥ 2/3 on the plane-wave side, with the minimum at (1/3, −1/3).
- Mean field has no interior minimum in charge. The reduced energy along that branch is concave in s, and a 275-point grid found 0 interior minima.
- In exact levels the only P strictly between 0 and N that ever wins is P = ±1, on odd N only. It is the balanced state's odd-N form, |P|/N → 0, and the only receipt row with it is N = 3. No 2 ≤ P ≤ N−1 wins, on the scans at N ≤ 27, plus crossings to N = 244.

**Item 4.** The ratio reaches 1 as 1/N at all five points. The 20% tolerance hides no wrong limit.

Closed form derived here from the chains' Weyl symbol, with r = ρ, a = 4−3u, ω² = 4ar(1−2r):
- t₁ = −1/(2a) − (1−4r)/(2ω)
- c₁ = (1/(8r²))[1/a − 1 + 3r + (3−8r)/ω − ω/4]
- K = (t₁ + ½)/r − 2c₁/c₀ + (1/r − u − 1/u)/ω

| (u, x) | K from chains | Offset from closed form |
|---|---:|---:|
| (1/4, −1/4) | −3.1265079933672 | 0 (20 digits) |
| (1/4, 0) | −3.8843058731326 | 0 |
| (3/4, 0) | −17.356054289075 | 7e−17 |
| (3/4, 1/8) | −44.4811931834 | 4e−12 |
| (1/2, 1/4) | −17.783086750623 | 3e−16 |
| (1/2, 0), control | −6.7158383625775 | 1e−20 |

- The 0.81 at (3/4, 1/8), N = 243 is this term: 1 − 44.48/243 = 0.817, read 0.8160.
- At finite s (1, 4, 16) the ratio goes to 1 at N = 6561, with N(R−1) settling at each s. (3/4, 1/8), s = 16 reads 0.8598, 0.9613, 0.9880, 0.9961.
- The README's "reaches the rotor as 1/N" below the edge also holds, with the same K.

**Item 5, N = 3 doublet.**
- E = −1/3 − √73/12 is exact (discriminant 73/144), and ⟨B⟩ = (3/4)(1 + 1/√73) = 0.837780860 even, minus that odd.
- Other doublets: P = ±1 at odd N only, region listed per N in FINDINGS.txt.
- Sector ties sit on exact rational curves: N = 2, ux = −1/2; N = 3, u(u−3x) = 1; plus one N = 5 point. None is a route row.

**Item 5, the even-block change.**
- It hides nothing on any class I built. The two reads differ on 2 of 60 rows: the doublet and a 1.6e−7 step-size effect.
- The new check also catches a fault the old one passed: a pure P = +1 state, which reads B = 0.
- `even_block` agrees on 3,180 of 3,180 with a direct monomial-basis count, a characteristic-polynomial count with no pivots, and whole = even + odd.
- Odd below even by more than 2⁻⁴⁰: 0 of 26,117 points. The 3,638 near-ties at N ≤ 12 all resolve even at 1000 bits.

**Item 6.**
- Tables: 45 of 45 cells.
- y = 0 rows: 28 of 28 against exact levels over all P.
- N = 2 and N = 3 paragraphs: right by hand.
- Frozen f(q): all within 0.94 ppm.
- Reader rerun: byte-equal to `READ.hbp`, 1422 met and 35 missed.
- All 196 rows read by separate tools: offsets about 1e−9 from the even block and series. The reduced basis reads up to 4.2e−5 at N = 243, s = 16 on my truncation side, and the block solver reads those rows within 1e−9.

## What is refuted, each narrowly
1. **"The ground state is the even mix" below the edge** fails for Nu(u−x) below about 1, and at u = 0 for all x below −1. The lowest sector stays balanced there. N = 81, u = 1/64, x = −1, yN = 4 reads ⟨P²⟩/N² = 0.005 and D₂ = 0.98, against the form's 0.005. The crossing reads Nu(u−x) = 1.0098 at N = 122, x = −5.
2. **"Excited at every x" at u = 1** is right on −1/2 < x < 0. For x > 0 no ordered pair state exists, and the ground state is the disordered P = 0, with ⟨n₊+n₋⟩ = 0.155 at x = 1.
3. **sign⟨B⟩ = sign(u−x−1), as the frozen clause reads:** the zero actually sits at u−x−1 = −(1−2u)/N − 2(1−u)y². The limit form leaves 5% in a band around it, of about ±0.03 to 0.18 at N = 243 and u = 1/4, shrinking as 1/N. The receipt's points are outside the band.
4. **Count wording:** 42 of the 126 are a ⟨B⟩-negative check that the frozen inside row does not state. The sentence on the 120 omits 18 sign rows. The reader also reads the frozen sign clause only at s ≥ 4. The 18 rows at lower s hold, by my read.

**Where the forms fail (item 2):**
- near W = 0, as in point 3
- at small u: D₂/y² runs about 1/(Nuw) high, with w = u−x (1.14 at Nuw = 16), and A₁/y reaches 1.07 of its form at N = 243, u = 1/64, x = −5, s = 16
- at u − x → 0: outside the plane-wave ground-state region, since the plane-wave branch is excited there (E ≈ 40 against −0.75 at N = 81) and the ground state reads the rotor or disordered forms
- at the edge itself, by level order

## Holds, all on `polariton/README.md`
- **H1, medium:** "Below the plane-wave edge" gains the Nu(u−x) condition, the balanced branch and the crossing values.
- **H2, medium:** the u = 1 sentence states the range −1/2 < x < 0, and the disordered ground state for x > 0, with crossing at x = −0.967/N.
- **H3, low:** adds the exact-in-N forms, the zero of ⟨B⟩ and the 5% band.
- **H4, low:** the 126 splits into 42 D₂, 42 A₁/y and 42 sign rows, the last added by the reader.
- **H5, low:** the 120 names the sign rows, and notes the yN < 4 rows hold it outside the reader's count.

Each OLD text was checked to occur exactly once in the file. I propose no hold for the closed-form K, since it corrects no fault. It is in FINDINGS.txt F4.2 if wanted for the README.

## What I could not check
- **Even below odd on the plane-wave side at N = 243, 729:** CANNOT_SEE directly. Direct runs reached N = 81, and beyond that it rests on the derivation and the trend.
- **326 near-ties at N = 15, 21, 27:** unresolved in direction.
- **Even lowest at all y:** CONJECTURE. There is no sign gauge, so Perron-Frobenius does not apply.
- **The excited plane-wave branch near D₁ = 0:** my top-sector block is unconverged there, so its A₁/y numbers are CANNOT_SEE. A two-level guess I tried failed and is withdrawn in the findings.
- **1/N coefficient at finite q:** MEASURED only, not derived.
- **u > 1:** read only on grids and at u = 2.
- **Below-edge forms, first sweep:** I stopped it for time at 155 rows. The series reproduced those rows, and the remaining groups ran separately at s = 4 and 16.

**Tool faults of my own, kept on record:** my Mathieu reader had an uncounted zero pivot, the engine's first-run fault again. It read f(1) 2.6 ppm low, so the frozen 417999 was right. My reduced basis had a bad start vector at N = 6561. Both are fixed, and the old rows are kept in `out/`.

Files are in `C:/tmp/opus55/polariton-recheck-window-20261105`:
- `FINDINGS.txt`
- `HOLDS.txt`

## The engine, the reader, the holds and a mutation rerun

**Head checked:** `git rev-parse HEAD` printed `ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd` at the start and end. `git status --short` is empty, so nothing in the worktree changed. Tracked `polariton/second-seat/*/out/` folders are the only ignored ones (see H7).

**Files**
- `C:/tmp/opus55/polariton-recheck-engine-20261105/FINDINGS.txt`
- `C:/tmp/opus55/polariton-recheck-engine-20261105/HOLDS.txt`: 29 blocks, each OLD found exactly once in the blob at this head (script-checked).
- Tools are in `tools/`, rows in `out/`, under the same folder.

## What I ran

- **Holds:** every engine hold against the head blob by `git show`, then a line-by-line read of the new code. I also ran a copy of the engine that counts bits lost at every left shift and narrowing cast.
- **Mutation:** 124 mutants at Rust 1.81.
  - Each one's lite rows replace their partners in the whole filed receipt.
  - The reader and route are the files at this head, unmodified.
  - 7 more ran on the whole sector stage to 3^16.
- **Separate exact code, in integers:**
  - Taylor series of the unitary on all 30 conversion rows at N = 81.
  - A Mathieu read from the ground vector on all 36 frozen f(q) values.
- **Other runs:**
  - Step test at N = 729, 2^-14 against the filed 2^-12.
  - 18 skipped N = 9 window rows, through a copy of the route.
  - The reader on about 40 damaged receipts.
  - The workflow's pin steps on copies with one edit each.
- **Owning gate, read only with `gh`:** run 41981845809 at this head, conclusion success, 06:39:12Z to 08:07:20Z, 88 minutes. Both rust-181 checks succeeded. PR state OPEN.

## What survives (MEASURED)

**The 24 code holds**
- All 24 took effect as meant.
- H5, H7c, H7d and H8b were extended by later code, with effect intact.
- 43 of 43 critical rows print the H2 step.
- Stages the holds should not touch are byte-same: quench 240/240, reversal, wavevector, control, Taylor points.

**Binary**
- The fourth-run exe differs from two fresh builds in 24 bytes only: the PE time stamp in 4 places and the PDB GUID.
- `.text`, `.data` and the rest of `.rdata` are byte-equal, so it is this head's source.

**Filing**
- All 5 pins equal the blobs, each with 0 CR.
- The first 29 rows hash to the pin.
- PREDICTION.hbp at each commit is a byte prefix of this head's, and only 3 attempt rows have been added since `89a026a`.
- The receipt rebuilds from `fourth/*.out` to sha `347480a5…`.
- `third-run` equals the `8dfa11a` blobs, and `first-run` is unchanged.
- My build's taylor, control, reversal, wavevector and rotor rows are contiguous slices of the receipt, in place.
- My rerun of the reader and the whole route is byte-equal after CR removal.

**Reader against the frozen rows**
- The typed f(q) tables are right, and my own read agrees on 36 of 36.
- Tolerances are as frozen at the frozen rows, apart from the two sign narrowings below.
- Third run to this head: 0 verdicts changed, 61 reads changed, 0 predicted values changed.
- The head reader on the third-run receipt reproduces all 918 old rows exactly, so the 61 moves are the engine's.
- Largest move: `critical_jbar_ratio` 1.45090 to 1.44488, 4,149 ppm. All 61 rows are listed in `FINDINGS.txt`.

**Reader exit**
- It exits 0 at 35 misses and at any number of misses, and 1 only on a crash.
- A miss cannot fail the job. A change from the filed read fails it through `cmp`. This is by design, and the step name says so.

**Overflow**
- 0 bits lost at 16 sites, on sector to 3^16, rotor, reversal, the heaviest N = 729 window and conversion chains, and the k + 2 chains.
- Rows run this way are byte-in-receipt.
- Every stage's `.err` ends with its `whole` row, so none panicked.
- Other N = 729 and N = 2187 chains: DERIVED from the same sizes.

**Step**
- N = 81 against the exact unitary: largest off 3,988e-9 on values of order 10, with V² and D₂ within 1 ppm.
- N = 729, 2^-12 against 2^-14: V² equal at the printed ppm, D₂ within 1 ppm. ⟨A⟩, ⟨B⟩ and pairs carry about 1e-4.

**Warm start**
- At N ≤ 243, both a chain run upward and a generic start at every row stay on the same branch.
- ⟨A⟩ moves at most 25 ppb and ⟨B⟩ at most 478 ppb.

**README claim on the step:** "a step 4 times larger panics at its check" holds: T03 exits 101 at quench.

## Mutation result (MEASURED, `out/tally.txt`)

How the read differs from a real run:
- Rows lite does not run keep their filed values: N = 729, N = 2187, N = 19683, and the rungs above 3^13.
- Route lanes are taylor, convert, sector to 243 and full to 3.
- A kill is a real kill. A survivor may still die at a size lite did not rerun.
- Three reads that mix lite and filed rows are counted apart.
- Group F stops at the first reader value miss, so its family lists are a lower bound.

| Set | Run | Reader on a value | Route alone | Panic or timeout alone | Missing row alone | Survived |
|---|---:|---:|---:|---:|---:|---:|
| Earlier 59 | 59 | 49 | 1 | 2 | 0 | 7 |
| New code paths | 65 | 22 | 5 | 3 | 6 | 29 |

The earlier 59 now show 52 killed against 47 at `8dfa11a`. R07, R12, R13, R14 and L04 are new kills.

**Earlier 7 survivors, sized**
- R16, R17, R18 move only printed columns. No verdict moves, so the closed-form hold took effect.
- R19: the offset is at most 24e-9 on quench rows and 89,965,045e-9 on control rows. H1 kills it.
- S14 and R20 are 1/N factors: 51 and 150 ppm at the smallest N they are read at.
- S20: one unit on o². Its full-size twin X05 dies on the top route, bad 6 of 44 at 9,693 ppm, so the earlier CONJECTURE is now MEASURED.

**Whole-sector mutants**
- X01 (H1 undone): reader blind, top route bad 4 of 44. H8 works.
- X02 (H2 undone): passes the reader and the route at 183 ppm.
- X03 (quantised at 256 units): reader 6 misses, sector route bad 9, top route bad 20.
- X04 and X06: equivalent at the printed digits.
- X07 (floor at 2^-70): passes at 102 ppm.

**R19, the survivor the README left open.** The smallest change is H1, one reader line. The no-Bose control rows evolve under a different H from the one the row reads, so their printed offset must leave 10⁻⁴.
- R19 on the whole receipt goes from 0 new misses to 4, on a value.
- `conversion_chain` has its own energy line, and H2 covers it.

**Left after all holds: 24 of 36**
- Printed columns and labels (7): R16, R17, R18, W04, C13, C19, S22.
- Self-reports the reader takes on the engine's word (4): V02, V03, L06, S21.
- 1/N factors (2): S14, R20.
- Equivalent at the rows' digits (9): W10, W11, C09, C10, O02, O07, P03, P05, Z03.
- Dying at the top, unread in lite (2): S20, P04.

## Refuted (MEASURED)

1. **The class of engine columns in verdicts is still open.** Q03 prints `jbar_over_N_ppm` times N.
   - On the whole receipt 147 reads vanish, including all 18 quench_jbar and quench_phase misses, with 0 new misses and exit 0.
   - H12 closes it.
2. **README line 144, "counts rows per tag, so a missing row is a miss."**
   - A plain deletion is a miss.
   - A row replaced by a copy of another keeps the count on 6 read paths, and the miss count falls with no row saying so.
   - In the workflow the hashes catch it. The reader alone does not.
3. **The route's 200 ppm does not guard H2.** X02 would change the table's 105.54 to 105.52.
4. **README line 82, "126 of 126":** 84 reads are the two named tolerances, and 42 are a sign read row 37 does not freeze.
5. **Reader narrower than row 39.**
   - The frozen signs have no gate, and the reader reads 58 of 188.
   - On all 94 rows: ⟨A⟩ negative 94, ⟨B⟩ positive 93. The exception is N = 81, δ = 0, y = 4/9, t = 3, ⟨B⟩ = −0.122, predicted f = 74.6.
   - If row 39's N ≥ 243 is taken to scope the signs, the read is 128 of 128 and H3 is a choice, not a fault.
6. **Filing.**
   - 87 of the 102 files in `second-seat/SHA256SUMS` are ignored by `out/` and absent from the commit.
   - The added prediction rows and `Cargo.toml` have no pin: an edit to row 39, or `overflow-checks = false`, passes every pin. Taylor, control and rotor then print byte-equal rows.
7. **My own errors, corrected beside the claims.**
   - L04 is no longer equivalent: at the N = 3 doublet a generic start reads ⟨B⟩ = 0 against 0.837781, and the route kills it.
   - My first P² step of 2^-14 was too coarse on one row. The engine stood.

## Holds, one line each

- **H1** medium `read_prediction.py`: control rows' energy must leave 10⁻⁴, kills R19.
- **H2** medium `read_prediction.py`: conversion energy rebuilt from the row's other fields, kills C12.
- **H3** medium `read_prediction.py`: read conversion signs on all 94 rows, adds 1 miss.
- **H4** low `read_prediction.py`: below-edge ⟨B⟩ sign at all s ≥ 1/2, 18 more rows met.
- **H5** medium `read_prediction.py`: count distinct rows, so a swap is a miss.
- **H5b** low `read_prediction.py`: add the Taylor tags to the count list, kills TC3.
- **H6** medium `polariton.yml`: pin rows 36–41, `Cargo.toml` and `.gitattributes`.
- **H7** medium `.gitignore`: un-ignore `polariton/second-seat/*/out/`, then add them.
- **H8, H8b, H8c, H8d, H8e** medium `second_route.py`: exact P² at N ≤ 3, kills W07, W08, W09 (bad 20, 20, 19 of 21).
- **H9** low `second_route.py`: read `f_ppb` in convert_compare, kills C05.
- **H10** low `polariton.yml`: rerun the 30 window f(q) values in the workflow, all equal to frozen, 17 s.
- **H11** medium `read_prediction.py`: read the Lanczos residual ≤ 931e-12, kills L08.
- **H12** high `read_prediction.py`: gate the quench reads from `jbar_ppb`, closes Q03.
- **H13** low `read_prediction.py`: read energy on the pinned quench rows, kills Q01.
- **H14** low `read_prediction.py`: frozen conversion grid, kills C15.
- **H15** low `second_route.py`: read all 21 N = 9 window rows; my run of the other 18 is bad 0.
- **H16** medium `second_route.py`: top limit 200 to 50 ppm; X02 reads bad 3, filed rows bad 0.
- **H16b** medium `polariton/README.md`: limit text to match H16.
- **H17** low `read_prediction.py`: band column against its own rows, kills Q04.
- **H18** medium `README.md`: "counts the distinct rows", goes with H5.
- **H19** low `README.md`: 84 of 84 plus 42 sign rows.
- **H20** low `README.md`: signs on all 94 rows, with the one exception named.
- **H21** low `README.md`: N = 9 row scope, goes with H15. The count of 60 in that sentence becomes 78; H21's OLD does not reach it, so that edit is still to make.
- **H22** low `README.md`: the mutation rerun's counts, replacing the OPEN line.
- **H23** low `README.md`: names the hosted run, replacing the OPEN line.

**Re-pin needed if applied**
- The reader holds move `READ.hbp` from 1,422/35 to 1,675/36 on the filed receipt, with all 1,457 old rows unchanged.
- H8, H9, H10, H15 and H16 move `SECOND-ROUTE.hbp`.
- So the pins, the README counts and a new attempt row move too.
- No hold touches the engine or the receipt.

## What I could not check (CANNOT_SEE)

- Mutants at N = 729, 2187, 19683 and the top rungs, beyond the seven whole-sector ones.
- Group F past its first reader miss.
- What P06, Z01 and Z02 would read: they timed out, and a timeout is not a measurement.
- Warm start against generic start at N = 729.
- The exact unitary above N = 81. N = 729 has the step test only.
- Mutant rows on Linux. The hosted job read only the unmutated head.
- One whole end-to-end run of the held route. Each lane ran alone, and the new pin hashes follow from that run.
- Fabric and recall were not asked. The physics of the laws belongs to the contact and window lanes.

## Every number in the text against the rows

**TEXT LANE RECHECK: PR #8 at `ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd`**

**Verdict: HOLD.** One filing fault is high: 87 of the 102 hashed files are not in the commit. Two numbers are refuted, and both came from my own earlier lanes. The remaining faults are scope and wording; no formula, count or table cell is refuted.

**Head checked:** `rev-parse` printed that hash before and after. `gh pr view 8` gives the same head. The worktree is unchanged, with `git status --short` empty.

**Files:**
- `C:/tmp/opus55/polariton-recheck-text-20261105/FINDINGS.txt`
- `C:/tmp/opus55/polariton-recheck-text-20261105/HOLDS.txt` (52 blocks: 1 high, 22 medium, 29 low; `verify_holds.py` finds every OLD exactly once at this head or in the live body and title)
- `C:/tmp/opus55/polariton-recheck-text-20261105/out/`

## What I ran
- **Inventory:** `inventory.py` lists 1,208 number tokens in 259 sentences. The ledger by line is in FINDINGS. `coverage.py` left 23 tokens for reading by hand, and all 23 matched rows.
- **Own row checks:** separate loader and closed law in integers, `check_a` to `check_g`, `check_signs`, `check_time`, `check_moved`.
- **Own exact reads, sharing no code with the author:**
  - 143 sector levels, and the top rungs including x = 0
  - A†A identity, J₁ and w₁ series, and the 4 conversion rows
  - 24 rows at N = 9 and 42 quench rows at N = 81
  - y → 0 chains, a P scan at N = 243, and the r⁴ constants
  - one tight residual row from the head engine
- **Rerun of the head's tools:**
  - The reader's output is byte-equal to READ.hbp.
  - Clippy and fmt at 1.81 exit 0. This is scoped evidence from my run, and the hosted job is the owning gate.

## What survives (MEASURED)
- **Counts:**
  - 1,422 and 35, with 42, 30 and 12 between the first and third runs, and 0 flips from third to fourth.
  - 126 of 126, 120 of 120, 29 of 29, 21 of 21, 17 of 21, 58 of 58.
  - 810 × 10⁻⁹ on 94 rows.
- **Tables:** every cell of the central, contact, window, below-edge, ladder and band tables, and both PR tables, with 0 mismatches.
- **Ratios and takeover:**
  - 0.9905 to 1.0267.
  - All 14 takeover ratios.
  - 0.96 to 1.15, 0.06 and 0.004 past the range.
- **Top rungs:**
  - Own read at N = 43,046,721, x = 0: e −0.100000005861, f 0.399999986466, gap 1.095445086.
  - x = 1/2 pairs off 17 ppm, x = 3/2 pairs off 24 ppm, gap under 1 ppm.
- **Algebra:**
  - The identity holds on 1,586 elements with 0 mismatches.
  - J₁ has 0 mismatches through t¹⁶ at 9 new (δ, u), including δ = 3/2.
  - w₁ has 0 mismatches through t¹².
- **Second-seat numbers recomputed:**
  - −6.72: own −6.741, −6.724, −6.719.
  - −1 ppb: head engine at residual 13 × 10⁻¹².
  - 18 of 18 points, 7.18495, 0.162869, and 2.25 × 10⁻⁷ (own 2.245 × 10⁻⁷).
- **Rows moved since the third run:** the third-run quench rows are byte-equal to this head's. Pin energies and ppm columns did not move.
- **Filing:**
  - `SHA256SUMS` matches 102 of 102 files on disk.
  - `REPORT.md` is byte-equal to the task result in all three sections, with no escapes.
  - Token-shaped strings: 0. Operator email: 0.
  - Tools tar hash matches, 745 files.
  - All 21 internal links resolve at this head.
- **Dispositions:** 80 blocks to 80 rows, one to one. All README and body holds are present by phrase search, and none was dropped without a row.

## What is refuted
- **Filing (high):** `.gitignore`'s `out/` keeps `second-seat/*/out/` out of the commit, 87 of 102 listed files.
  - GitHub returns 404 for `engine/out` at this head.
  - REPORT's "row files are in the folders beside this one" is false at this head.
- **L160, "⟨A⟩ at N = 9 about 5 × 10⁻⁸":** own read gives 1.67 × 10⁻⁸ to 7.0 × 10⁻⁷, median 2.4 × 10⁻⁷. The floored read-out alone reproduces this within 1 × 10⁻⁹, so the attribution stands and the size does not. This was my text lane's number; the retraction is beside it in FINDINGS.
- **L174, "N = 2, 3, 9 and 19 of 28 at N = 27":** the row file holds N = 3: 28, N = 9: 28, N = 27: 23, N = 2: 0. This was my engine lane's error. N = 2 is now read by me.
- **L144, reader order:** "committed … before its first read" is false. Commit `099b0c6` holds the reader together with that read. It is also stale about `89a026a`.
- **Stronger than rows:**
  - "all 29 rows read": the table beside it has 10 of 30 cells past 2.7%.
  - "Each deviation falls as 1/N": the last step is 2.75 to 2.84.
  - "sets the modulation": the rows read √(2C₂) and 2ρ as one number.
  - Exact route "at the top rungs": it covers δ ≥ 1 only, 44 of 76 rows.
  - "three points" for energy and pair fraction.
  - "the same move".
- **Small mismatches:**
  - 1 ppb is really 1.07.
  - 0.95% is really 0.925%, which equals 6.72/729.
  - 1 × 10⁻⁹ is really 1.55 × 10⁻⁹.
  - 4 × 10⁻⁵ is really 4.05 × 10⁻⁵.
  - 220 rows is really 438.
  - The clock sentence mixes two clocks.
- **Merges that lost a measured fact:** derivations H2 (P = 0 branch), H3 (x = 0 agreement) and H13 (9 points); text H13 (δ = −1 limit) and H15 (visibility clause). Engine H10's row says applied, but the causal clause stayed.

## Holds
| Hold | File | Change |
|---|---|---|
| H1 high | `.gitignore` | Re-include `second-seat/*/out/`, tested in a scratch repo |
| H2 | README | 29 rows named as the frozen range, plus 0.96 to 1.15 past it |
| H3 | README | Replace "the same move" in the status |
| H4 low | README | Section title |
| H5 | README | Table N, seen rows, y√N grid |
| H6 low | PREDICTION | Beside row for the fourth seen row |
| H7 | README | 126 split 36 and 90, lowest 0.8145 |
| H8 | README | 120 split 40 and 80 |
| H9 | Body | Both splits, plus the U = J ground-state number |
| H10 | README | 438 rows, route and READ scope, own x = 0 read |
| H11 | README | Top rungs δ ≥ 1 |
| H12 | Root | U = J ground state, frozen range, law's order |
| H13 | Root | Three points spelled out |
| H14 | Root | Route from the takeover up |
| H15 | Body | Three points spelled out |
| H16 | Body | 44 rows with δ ≥ 1 |
| H17 | Body | Contact heading and leading order |
| H18 | README | Parity counts refuted, 7 rows at N = 729 |
| H19 | README | Read-out size refuted |
| H20 | README | Reader order and `89a026a` |
| H21 | README | Causal clause |
| H22 | Body | Causal clause |
| H23 | README | 1/N stated with rows and y√N |
| H24 | README | Law's order and tag |
| H25 | README | V as the paper's two visibilities |
| H26 low | README | D₂²/2C₂ reads f² |
| H27 low | README | 1.1 ppb |
| H28 low | README | 0.92%, 9 points |
| H29 low | README | 4.1 × 10⁻⁵ |
| H30 low | README | Signs on all 94 rows, one ⟨B⟩ = −0.122 at N = 81 |
| H31 low | README | Three rows above 1 at N = 81 |
| H32 low | README | 1.6 × 10⁻⁹ |
| H33 low | README | u = 1 rows on the P = 0 branch |
| H34 low | README | N·dev 125, 132, 134 against 135.4; δ = −1 stops at 6561 |
| H35 low | README | Clocks and the same-turn nuance |
| H36 low | README | 2.25 × 10⁻⁷ is relative |
| H37 low | README | Status names the hosted run OPEN |
| H38 low | README | 1/k_r main-text line, 9.2% |
| H39 low | Body | Methods line |
| H40 low | README | "zero fitted numbers" |
| H41 low | README | "zero fitted numbers" |
| H42 low | Root | "zero fitted numbers" |
| H43 low | Body | "zero fitted numbers" |
| H44 low | README | Positive text for "outside this form" |
| H45 low | README | Positive text for "never found" |
| H46 low | Root | Positive text for "a separate quantity" |
| H47 low | README | "unread" to OPEN |
| H48 low | Body | First corrections scoped, C₁ OPEN |
| H49 low | Body | 0.96 to 1.15 past the range |
| H50 low | README | "engine file existed" |
| H51 low | Body | "engine file existed" |
| H52 low | PR title | "at U = J/2" |

Holds not marked are medium.

## Could not check (CANNOT_SEE)
- Parity at N ≥ 81 at this head. Those rows were read at `8dfa11a`, and the even levels match at ppb.
- A mutation rerun at this head. The text already marks it OPEN.
- The hosted receipt job at this head: `gh pr checks` shows it pending and `rust-181` pass twice. I did not touch it.
- Nature's final text and the paper's figures, including Fig. 1e and Fig. 1b. `nature.com` returned 303 from here.
- What a model actually read before writing a form. "Unseen" is measured only from the file record, and session times come through `text/FINDINGS.txt`.
- The original operator and GPT-6 messages.
- Recall returned `count=0` for polariton, which means the index lacks it, not that it is absent. Fabric health answered. Owning seats and HELM were not asked.
