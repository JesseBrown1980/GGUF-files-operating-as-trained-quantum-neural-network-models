# The second seat on the polariton test, at `8dfa11a`

Three lanes ran and none failed. Their reports follow verbatim, and each lane's findings, holds and row files are in the folders beside this one. Row files of 200000 bytes or more stay in the tools tar. Their scripts are held on this machine at `D:/safety-backups/opus55-polariton-attack-20261104-tools.tar.gz`, 745 files, SHA-256 `743c251d96f38ec78f24380bd9cfd5316af40cbff7fd53b6c07230b7c5c57ba3`, and their upload to the Hugging Face dataset is OPEN.

## The derivations, by separate routes

VERDICT: HOLD at 8dfa11a. No formula is refuted: every derivation in items 1–7 came out as the note writes it, inside its rows. The holds are about scope, read-out and what the README leaves unsaid. All 13 are on `polariton/README.md`.

**Holds**
- **H1 (high):** the status says yes with no u. At contact u=1, x=−1/4, N=243, yN=4, D₂ reads 0.00009 against the rotor's 0.437.
- **H2 (high):** the window is undefined; state its three edges and the failure below the plane-wave line.
- **H3 (medium):** the top-rung digits and the 1.4509 and 0.6937 ratios are 2⁻⁶⁰ rounding of o²; add 180-bit values and the takeover constants.
- **H4 (medium):** u=0 pins at q₀ = Ny²/(16c₀²ω), with ⟨B⟩ positive, the opposite position from u>0.
- **H5 (medium):** the t⁴/N conjecture now has exact coefficients.
- **H6 (low):** the phase misses follow from energy conservation.
- **H7 (low):** the pinned misses have a closed form at δ=0.
- **H8 (medium):** K=A²/16 against the paper's A²/4, and the paper's k against the pinned state's 2k.
- **H9 (low):** the cosine density form needs real ⟨A⟩ and ⟨B⟩.
- **H10 (low):** add the quench correction J₁.
- **H11 (low):** unequal Hopfield weights split u.
- **H12 (low):** what limits the top rungs.
- **H13 (low):** the rotor test at new points.

**New measurements** (MEASURED unless tagged)
- **Contact form:** 451 Fock states with 0 mismatches give u=1 and pair/direct=1.
- **Density and g²:** first-quantised grid at N=2,3 matches on all five states. The cosine form fails 6/8 on a complex parity-free state.
- **Window:** the plane wave equals the pair state at x = −1, −0.4243, −0.1910, −0.0522, 0 for u = 0, 1/4, 1/2, 3/4, 1. At u=1 the pair state is excited for every x<0.
- **Rotor:** at 9 (u,x) with u>0, including u=1/4 and 3/4, exact y→0 chains reach the rotor as 1/N. So no term appears at the rotor's order, Berry or ordering. Full space at N=81 and 243 agrees, and the six frozen f(q) values reproduce exactly.
- **u=0:** the mean-field energy is exactly flat in α (6 circle points, 1 value). N·u_eff → −1/ω, ω=√(2(1−x²)), within 4×10⁻⁵ at seven x, from chains and a no-fit zero-point sum. The form 1/ω is CONJECTURE.
- **Takeover:** gap → 7.18495 g^(1/3), pairs → 0.162869 g^(−1/3) − 0.44 at u=1/2, g=(4−3u)/(16N). The 0.44 is read off, not derived.
- **Top rung:** at N=43,046,721 pairs read 106.039 against 105.537 at 180 bits. The top step is 1.4449, not 1.4509. Rebuilding the engine's rounding returns its gaps to 8 digits, and no READ row changes.
- **Quench:** γ⁶J₁ = −(4−3δu)sinh²(2γt)/4 + (3/2)γt[1+3δ²−δu(2+δ²)]sinh 2γt + δ[3u(1+δ²)−δ(7+δ²)]sinh²γt, exact through t¹⁴ at four (δ,u).
- **Band edge:** J₁ = −[t²+(3∓u)t⁴+(2/5)(4∓3u)t⁶]. The pair count deviates as t⁶/N, so the relative deviation goes as t⁴/N and the note's conjecture holds.
- **The 31 misses:**
  - 12 pair rows sit at 0.35–1.37 × (first order)² from the first correction.
  - 6 phase rows follow energy conservation.
  - 12 pinned rows follow the same 1/N term. It reads 0.9998–1.027 at t=1,2; at t=3 it needs higher order (1.175 at N=729, cancelled at N=243).
  - 1 row is the wrong word "rises".
- **Source:** the paper writes no interacting three-mode H, only the P and linear terms, and both match. A₁²=16ρ₀ρcos²(θ/2) and (1−δ)V²≈0.017 hold, the second using ρ/ρ₀=K.

**Could not check** (CANNOT_SEE)
- Fabric and recall were not asked.
- PR #8 required checks and hosted reproduction were not read.
- My solver did not run the full space at N=729.
- The paper's figures, including how Fig. 1e defines A, the Nature final text and its cited references were not opened.
- Closed-form w₁ at general δ exists only at δ=0, ±1.
- The ordered gap digit at N=43,046,721 is limited by my window.

My own crate is scratch and has 2 clippy warnings, so it is scoped evidence only, not the 1.81 `-D warnings` gate. The checkout is unchanged, with `git status` clean.

**Files**
- C:/tmp/opus55/polariton-derivations-20261104/FINDINGS.txt
- C:/tmp/opus55/polariton-derivations-20261104/HOLDS.txt
- C:/tmp/opus55/polariton-derivations-20261104/out/
- C:/tmp/opus55/polariton-derivations-20261104/code/
- C:/tmp/opus55/polariton-derivations-20261104/fullspace/
- C:/tmp/opus55/polariton-derivations-20261104/paper/

## The engine and the reader, by mutation and separate code

VERDICT: HOLD at 8dfa11a

**Holds** (32 blocks; a letter suffix means a part of the same hold)
- **H1 (high), engine:** `sector_o2` floors o² at 2⁻⁶⁰, and o²[0] is only 622 units at N = 3¹⁶. Move it to 2⁻⁹⁰ by long division.
- **H2 (medium), engine:** coarser takeover step, 2^-(20+power/2).
- **H3 (medium), reader:** read the 28 values at the four N above 3¹³.
- **H4 (high), reader:** compute the closed forms itself. It currently takes `closed_ppb`, `predicted_A1`, `predicted_C1` and `ratio_ppm` from the engine.
- **H5 (medium), reader:** read the N = 2 hand rows, and count a missing row as a miss.
- **H6 (medium), route:** `hand()` checks arithmetic on typed literals; compute them.
- **H7 (medium), route:** add C2 at y ≠ 0.
- **H8 (high), route and workflow:** add `top_compare` for the top rungs, and add `mathieu` to the workflow.
- **H9 (high), README:** correct the top-rung table, the 1.4509 ratio, and record the third engine error.
- **H10 (medium), README:** the conversion rows read the D₂ rows again.
- **H11 (low), README:** the −30 ppb is solver residue.
- **H12 (low), README:** add the parity results.
- **H13 (low), README:** state the reader's commit order and the width of the A₁ tolerance.
- **H14 (low), PREDICTION:** add an attempt row after the frozen 29.

**New measurements** (all MEASURED)
- **o² floor, against exact rationals at 2³²⁰:**

| Row at N = 3¹⁶ | Exact | Engine | Off |
|---|---|---|---|
| Takeover pairs | 105.5373 | 106.0391 | +4755 ppm |
| Takeover gap | 0.0110378 | 0.0110419 | +371 ppm |
| x = 3/2 pairs | 0.0773503 | 0.0773228 | −356 ppm |
| x = 3/2 gap | 3.464102 | 3.464215 | +33 ppm |

- **Takeover ratio:** the exact top step is 1.4449, and the README's 1.4509 is the floor. Exact Sturm with the engine's floored o² reproduces the engine's gap.
- **MET/MISS:** no row flips, and the ordered rows are untouched.
- **With H1 and H2:**
  - levels sit within 1 unit at N ≤ 243, against 66 now
  - the gap at 3¹⁶ is exact to the printed digit, and pairs are −17 ppm
  - `top_compare` gives bad=0, against bad=4 on the receipt
  - clippy 1.81 and fmt exit 0, on a one-bin package only
- **Mutants:** 47 of 59 killed (F 11/11, T 5/5, S 17/19, L 3/4, R 11/20).
  - The reader killed 43; the route alone killed 2 and a panic alone killed 2.
  - All runs used lite stages, scoped in `FINDINGS.txt`.
- **Survivors:**
  - R16 and R17 turn 8 and 9 misses into mets; R18 and R19 pass with no change (the reader trusts the engine).
  - R07, R12, R13, R14 sit on unread rows.
  - R20, S14 and S20 are too small to show at the tolerances or lite stages; S20 is not tested at the top rungs.
  - L04 is equivalent.
- **Parity:** the ground state is even on every row tested.
  - Exact inertia confirms 79 rows at N ≤ 27.
  - An odd-basis Lanczos confirms N = 81 and 243, and 7 rows at N = 729.
  - At yN = 16 there is a doublet, 3,059 × 10⁻¹² apart at N = 729.
  - y = 0 energies equal N·e of the sector within 1.1 × 10⁻⁹ on 24 rows.
- **Convergence:** all 174 rows are at or under 925 × 10⁻¹², with at most 93 cycles. Rerunning at about 1 × 10⁻¹¹ leaves D₂ and A₁ unchanged at the printed digit.
- **Sturm count:** exact zero pivots still occur, 1 per row (2 at N = 3), and are counted correctly. There is no overflow at 3¹⁶; the largest pivot is about 2⁶⁴.
- **Leapfrog holds:**
  - Against the exact series at N = 81, jbar error is at most 2.3 × 10⁻⁷.
  - The step tests at N = 6561 and 19683 change it by at most 1.0 × 10⁻⁹.
  - A step 4× larger panics.
- **Reader gaps:**
  - A receipt with 8 tags removed reads 434 met, 1 miss, rc = 0.
  - No read of the engine exists for POLARITON_TIME, the C1, C2, f, sign and slope of POLARITON_HAND, or the critical susceptibility; the 8 OTHER_U rows have no read and no prediction row.
  - POLARITON_SYMMETRY is read.
  - A constant A₁/y of 2.29 meets all 12 pinned A₁ rows.
  - The reader was first committed at 099b0c6, after the first run.
- **Conversion:** D₂/(f·2ρ) is closer to 1 than D₂/(f·√(2C₂)) on all nine rows at N ≥ 81.
- **Route:** the arithmetic is separate and the congruent form is correct (rederived). It shares the model text with the engine, and its exact sector read covers only `e_at_2^60` at N ≤ 243. By hand, the contact integral gives u = 1 (DERIVED).
- **Mathieu:** the frozen f(q) table matches exactly.
- **Reproduction:**
  - READ and SECOND-ROUTE are byte-equal after removing CR.
  - Windows and 4 workers match the receipt.
  - Linux matches for taylor, control, wavevector, rotor, reversal and the whole sector stage.
  - `gh pr checks 8`: the receipt job passes at head.

**Could not check** (CANNOT_SEE)
- The held engine's pin at N = 729, quench_pin, and a whole-receipt compare; the receipt must be regenerated.
- 9 inertia rows at N = 27 and the low-s odd rows at N = 729 (timeouts).
- Whether the reader's floors predate the first read.
- Fabric and recall were not asked.
- The extended-model claims are outside this lane.

**Please remove** these, which I created by mistake and did not delete. My earlier fix readings came from stale binaries because of the same path error, and I re-measured them.
- `C:/c/tmp/opus55/polariton-engine-20261104/` (111 MB)
- `/wsl_.err`, `/wsl_.out`, `/wsl_.rows` in the WSL root

Files are in `C:/tmp/opus55/polariton-engine-20261104/`:
- `FINDINGS.txt`
- `HOLDS.txt`
- `holdcopy/`
- `tools/`
- `out/`

## Every claim in the text against the rows

VERDICT: HOLD at 8dfa11a. The prediction order, the tolerances, the 887/31 count and the attempt record all survive. The text has scope faults: 7 high, 15 medium, 13 low. All 35 OLD strings occur exactly once at the commit (script-checked).

**High**
- H1: the status line's "Yes" gives no coupling. Scope it to U = J/2, Δ = 0. MEASURED: no pinned row is at u = 1.
- H2: "equal overlaps" plus README line 15 forces u = 1, which contradicts the central u = 1/2.
- H3: the paper reads its modulation at k_r, which is A₁ here. The central result is D₂ at 2k. The paper names g² as a future measurement.
- H4: the root README gives no sector sizes, and just above it the same two figures are HTTP-0 channels and addresses.
- H5, H6, H7: the same three faults in the PR body.

**Medium**
- H8: state sector sizes; 23,887,872 is in 0 READ rows.
- H9–H11: optional reader extension, as an alternative to H8's last sentence.
- H12: give the whole takeover sequence; the quoted top step turns back.
- H13: the furthest miss is 0.33, and the rows push against t⁴/N.
- H14: "14%" is refuted; pairs read 9.2%, and 13.8% is the closed form.
- H15: the paper's A²/4 against A²/16 here moves 0.017 to 0.068.
- H16: Hopfield count (CONJECTURE).
- H17: the quench is at u = 1, and the paper's ±1 modes are already populated.
- H18: fuller list of what "closed" leaves out.
- H19: full-space size, 266,815.
- H20: workflow paths omit Cargo and `.gitattributes`.
- H21: pin the reader and route; an edited reader plus READ.hbp passes every step.
- H24: "all 143 rows" misattributes (below).

**Low**
- H22, H23, H25: engine-record wording; the attempt record omits the read-out root change.
- H26: "0.196" is the predicted value; the read is 0.1953.
- H27–H35: wording, definitions and scope notes, each in HOLDS.txt.

**New measurements**
- Pivot-only rebuild of f47d662, with rotor and sector rerun: 887/31, same MET/MISS as READ.hbp on all 918 rows. The 42-from-pivot claim is confirmed by a run (30 gap, 12 pairs, 0 newly missed).
- Same rebuild against the exact route: 137 of 143 outside 4,096 units, median 1.5e-12, max 9.3e-12. In the first run 33 rows were 1e-9 or further off, up to 0.06, from the pivot.
- Frozen tolerances applied to the 28 unread rows at 3¹⁴–3¹⁶ and 23,887,872: all MET, giving 915/31.
- Order of events, from GitHub activity and the session log:
  - Before fce08f9, only the exact route's hand and Mathieu modes ran.
  - fce08f9 was pushed at 22:16:20Z and the engine file created at 22:16:32. The engine source was composed in the same model turn, after the prediction text was fixed.
  - The reader was composed before any first-run rows came back.
  - Only ATTEMPT rows were added after fce08f9, and no tolerance moved.
- Hosted run 41939586670: all steps success in 21m28s, so "about an hour" is stale.
  - The Windows-written receipt matched byte for byte on Ubuntu.
  - `/usr/bin/time` exists, the 240-minute limit fits, and the runner's python ran the exact route in 4m21s.
- f(q): my own computation reproduces all six frozen values. My first print was doubled by my own factor error; that retraction is in FINDINGS.txt.
- Takeover ratios: 1.4666, 1.4590, 1.4538, 1.4503, 1.4479, 1.4469, 1.4509.

**"No fit"** holds strictly: nothing was fitted and the values were frozen first. u = 1/2 is a pre-run model choice, disclosed only at line 59, so H1 moves it up.

**Could not check (CANNOT_SEE)**
- Nature text and its supplement: I read arXiv v1 only, 12 pages.
- Cause of the top-rung turn and the x = 3/2 drift (622 units at 3¹⁶ is CONJECTURE; a higher-precision run would settle it).
- Pinned rows near u = 1: none exist.
- Second run's partial output: overwritten, so it rests on the log.
- Fabric and recall were not asked; this lane rests on git, gh, the rows and the paper.

The checkout is unmodified (`git status` empty).

**Files**
- C:/tmp/opus55/polariton-text-20261104/FINDINGS.txt
- C:/tmp/opus55/polariton-text-20261104/HOLDS.txt
- C:/tmp/opus55/polariton-text-20261104/check_numbers.out
- C:/tmp/opus55/polariton-text-20261104/session-dump.txt
- C:/tmp/opus55/polariton-text-20261104/fix1only/read1.hbp
- C:/tmp/opus55/polariton-text-20261104/fix1only/route1.out
- C:/tmp/opus55/polariton-text-20261104/reader-ext/READ-top.hbp
- C:/tmp/opus55/polariton-text-20261104/reader-ext/read_prediction_top.py
- C:/tmp/opus55/polariton-text-20261104/scripts/
