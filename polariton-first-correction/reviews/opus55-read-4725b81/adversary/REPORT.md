Head checked: `git -C C:/tmp/qnn-fc-read-wt rev-parse HEAD` printed 4725b8124d1ef19d2e22844534e3abf39543fb30, the tree was clean, and it was clean and unchanged when I finished. All 16 entries in `polariton-first-correction/SHA256SUMS` are OK. The row's sha256 is 3b1e0477…, the same as in PLAN.hbp.

The filed verdicts stand: an independent evaluation reproduces them. One README claim is refuted: on V², the law alone sits inside 1/1000 at 3 points. The "1/N²" headline holds at leading order only. The frozen clauses resolve the first correction to about 3% on C₁ and 4 to 7% on A₁, which is less than the data itself resolves. None of the four crude alternatives passes.

## What I ran
Everything evaluates closed forms in exact rationals or reads filed rows. I built a standalone copy of the pinned engine source (sha256 ad121216…) with cargo +1.81.0 inside my folder and did not run it, so no model ran.
- **`adv_lib.py`**: my own interval arithmetic over Fractions, my own parser of the row-48 expressions, and exp/sqrt enclosures. It shares no code with `read_first_correction.py`.
- **s1–s9**: one script per step, each writing an `.hbp` file (json=0), with sha256 listed in FINDINGS.txt.
- **Alternatives first**: I wrote the crude alternatives into FINDINGS.txt section 0 at 2026-11-05T19:20:35Z, before evaluating them. Those bytes are kept as `FINDINGS-SECTION0-AS-WRITTEN-20261105T192035Z.txt` (sha256 21c12b14…, mtime 19:20:55Z). Before writing them I had seen the README table, and I say so in section 0.

## What survives (MEASURED, no shared code)
- **The evaluation:** my enclosures of law and law plus first match all 60 printed integers in READ-GRID (first and law for C₁, A₁ and V², and predicted f). I also re-derived the law from displaced Bogoliubov theory; it matches the row to below 1e-60. (s1_verify_forms.hbp)
- **The verdicts:** blind 8 of 8 and touched 2 of 2 MET. C₁, A₁ and V² are at most 493.8, 125.4 and 242.9 ppm off law plus first. The law alone is 8,332 to 20,596 ppm off on C₁.
- **The remainder:** the lower bounds of the ratio are 77.65 to 78.31, equal to the filed `ratio_times_1000_lo` values.
- **README numbers:** all 50 table numbers match READ-GRID. Also true at this head:
  - largest C₁ half width 1.388e-8;
  - V² half width 6,382 ppm of margin at (1/2, 1/4);
  - expanding L offsets ≤3 and ≤29 ×10⁻¹⁸;
  - epsilon at K=1600 above K=1200 at 8 of 10 points;
  - K=1200 inside at 10 of 10;
  - predicted f 0.0033 to 0.0110;
  - costs as stated.
- **Crude alternatives (task 3):** none sits within 1/1000 on all three observables at any point (0 of 40). C₁ rejects each alternative at 9 or 10 of 10 points.

| Alternative | C₁ inside | A₁ inside | V² inside |
|---|---:|---:|---:|
| ALT1: law with N → N−1 | 0 | 0 | 3 |
| ALT2: law × (1 − f) | 0 | 7 | 0 |
| ALT3: Bogoliubov state with n₀ = N − n read-out | 1 (at (0, 1/2), −623 ppm) | 0 | 0 |
| ALT4: condensate depleted by f | 0 | 2 | 1 |

## Task 1: how far the first-order coefficient could be off (K=1600)
κ = (read − law)/(first − law) − 1, with the certified intervals carried.
- **C₁:** κ runs from [−1.070%, −1.038%] at (1/2, 1/4) to [−2.296%, −2.290%] at (−1/4, 1).
- **A₁:** from [−0.808%, −0.696%] at (1/2, 1/4) to [−1.459%, −1.448%] at (−1/4, 1).
- **V²:** from [+8.29%, +14.05%] at (1/2, 1/4) to [−10.88%, −8.93%] at (1/2, 1/2).
- **Worst:** C₁ 2.296%, A₁ 1.459%, V² 14.05%.
- **What the 1/1000 clause admits** (with zero remainder): C₁ errors of 4.64% to 11.77%, A₁ 11.59% to 23.00%, V² 24.3% to 462%.

## Task 2: two N at the four remainder points (s3, s3b, s6)
| Point | R(729), ppm | R(6561), ppm | Ratio |
|---|---:|---:|---|
| (0, 1/4) | 11199.09 | [142.875, 144.224] | [77.65, 78.38] |
| (0, 1/2) | 15651.92 | [199.083, 200.520] | [78.06, 78.62] |
| (1/2, 1/4) | 7071.46 | [88.150, 90.906] | [77.79, 80.22] |
| (1/2, 1/2) | 9606.21 | [119.642, 122.660] | [78.32, 80.29] |

The R(729) half widths are about 3e-5 ppm.

- **Benchmarks:** a first-coefficient error alone gives a ratio of 9.66 to 10.02. A pure 1/N² relative remainder gives 81. A pure 1/N³ term in C₁ itself gives 86.9 to 90.2.
- **e, exact under two-term models:**
  - With the remainder written in absolute terms, e is [−0.188, −0.174]%, [−0.238, −0.226]%, [−0.126, −0.090]% and [−0.152, −0.118]% at the four points.
  - In the task's relative form, e is [−0.065, −0.050]%, [−0.065, −0.053]%, [−0.048, −0.011]% and [−0.046, −0.012]%.
  - The two forms differ only at the next order, yet e moves by about 3×. So two N give |e| ≤ 0.24% and cannot separate e from the next order.
- **The 1/N² coefficient of R:** b = 5916–5924, 8274–8283, 3737–3753 and 5081–5099. In the absolute form, Z/C₀ = 5301–5308, 7235–7243, 3422–3437 and 4571–4587.
- **Third N from seen rows** (N=2187, δ=0): the two-term fit misses κ at N=2187 by −2,804 to −2,983 ppm, against about 8 ppm of numerical error and a +64 ppm s′ offset. So the remainder has a 1/N³ part (W′ ≈ 1.0e4). With it, e at (0, 1/2) is in [−0.030, −0.005]%. A₁ shows the same pattern. The 1/N³ part enters A₁ the same way.

## Task 4: the law-alone control
|first − law|/first spans 8.49 to 21.53 limits on C₁ and 4.35 to 8.63 on A₁, so no point could be nondiscriminating there. On V² it spans only 0.22 to 4.12 limits, because the A₁² and C₁ corrections nearly cancel. The law alone sits inside 1/1000 on V² at three blind points and straddles the limit at the touched one:

| Point | V² read over law − 1, ppm |
|---|---|
| (1/2, 1/4) | [−246.8, −234.3] |
| (1/2, 1/2) | [+390.0, +398.5] |
| (1/4, 1/4) | [+431.4, +440.0] |
| (0, 1/4), touched | [+998.0, +1004.5] |

## Task 5: what the clauses resolve, and what weakens the read
- **Rival first corrections that would also read MET on every clause** (s5 and the S3_RIVAL_BAND rows of s3):
  - whole C₁ correction scaled by 0.9711 to 1.0234 (the 30× clause sets the lower end);
  - whole A₁ correction by 0.9561 to 1.0718 (the V² clause binds);
  - C10 0.968 to 1.028, C11 0.900 to 1.041, C12 0.750 to 1.102, w10 0.916 to 1.117, w11 0.908 to 1.151.
- **C12 (the s⁴ term):** it carries 16 to 23% of the C₁ correction only at the two s = 1 points, and 0.15 to 4.1% elsewhere. The 30× clause admits any C12 scale from −0.35 to 2.22.
- **V²:** V² read over first − 1 equals (1+rA)²/(1+rC) − 1 to 1e-6 ppm at all ten points (rA and rC are the A₁ and C₁ offsets). So the three clauses carry two measurements per point.
- **The f and signs clauses** read MET for the law alone as well: f is read from the closed form only, and the law already has ⟨A⟩ < 0 and ⟨B⟩ > 0.
- **The tolerance:** it was set from the touched (0, 1/2), whose remainder is 199.8 ppm. The blind C₁ remainders are 0.45 to 2.47 times that. The 1/1000 limit is 2.0 to 11.2 times the measured C₁ remainder.
- **The N=729 side of the remainder clause:** three of its four rows are among the four contact C₁ misses that preceded the row (`polariton/READ.hbp`). The formula leaves R(729) at 0.71 to 1.12% on them, so it was not fitted there.
- **One time only:** the formula's time dependence is read at t = 2 alone (NAMED, scope).

## Refuted (MEASURED)
- `polariton-first-correction/README.md` line 29, "so every point discriminates", and the top-level `README.md` line 38, "The law alone sits outside 1/1000 at every point": both fail on V², which is inside at 3 points and straddles at 1.
- Line 30, "The remainder falls with N as 1/N²", is narrowed: it is a two-point ratio below both 1/N² benchmarks, and the third N shows a 1/N³ part.

## Holds (each OLD text occurs exactly once at this head; checked by s9)
- **H1, medium,** `polariton-first-correction/README.md` line 29: restrict the claim to C₁ and A₁, and add the V² law-alone values and that V² discriminates at 6 of 10 points.
- **H2, medium,** `README.md` (top level): "outside 1/1000 at every point on C₁ and A₁, and on V² at 6 of the 10".
- **H3, low,** `polariton-first-correction/README.md` line 30: headline the measured 77.65 to 78.31, the upper bounds 78.38 to 80.29, the benchmarks 81 and 9.7 to 10.0, e within 0.24% from two N, and the 1/N³ part with e within 0.03% at (0, 1/2).
- **H4, medium,** `polariton-first-correction/README.md` Scope line 36: add the rival bands, C12's dependence on the s = 1 points, the V² identity, the f and signs clauses also passing for the law, and that all four alternatives miss C₁.

## Could not check
- **The first correction's own derivation:** both evaluations parse the same row text, so a fault in that text would be shared. CANNOT_SEE.
- **A third N at δ = 1/2:** no row is on file. It would be settled by engine runs at N = 2187, δ = 1/2, y = 1/94 and 1/188; not run, E=0.
- **The s′ offset at N = 2187** in the three-N solve is my own secant estimate: 64 ppm, against a 2,800 ppm miss.
- **README line 33 route numbers** (122×10⁻¹⁸ and the rest): no filed artifact at this head carries them. CANNOT_SEE; by this lane's default, refuted=true (uncertain) until the hosted job's log at 4725b81 is read.
- **"after that head's hosted run passed":** at 4725b81 the workflow's checkout step is named "on a pull request its merge with the base". Whether the 7f72d2c run was a push run or a merge-ref run is CANNOT_SEE; GitHub was not queried.
- **Engine certification:** I took the engine's intervals as filed (reviewed at 2d77636) and did not re-certify them.
- **Fabric and recall** were not asked. These results are scoped evidence; the owning gate is the filed rows plus the repo's hosted job.

Files are in C:/tmp/opus55/fc-read-attack-adversary-20261105/:
- FINDINGS.txt
- HOLDS.txt
- FINDINGS-SECTION0-AS-WRITTEN-20261105T192035Z.txt
- s1_verify_forms.hbp … s9_check_holds.hbp, with adv_lib.py, adv_data.py and the s*.py scripts
- engine/ and target/ (the built copy, never run)
