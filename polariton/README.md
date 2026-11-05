# The three-mode polariton test, November 4–5, 2026

The operator's word: *"Start the new run as well."* GPT-6 registered the design: *"whether a three-mode quantum system can reproduce the transition from spatial order in correlations to spatial order visible in the mean density, as a controlled symmetry-breaking field is introduced."*

**Status: run in integers, Rust 1.81 and clippy `-D warnings`, with [the prediction](PREDICTION.hbp) pushed before the engine existed, at `fce08f9`, and its additions pushed before their stages existed, at `89a026a`. Read against the frozen tolerances, [1,422 rows are met and 35 missed](READ.hbp), and the misses stay.**

- **Yes to the central test at U = J/2, Δ = 0,** in the ground state at N = 243 and 729: with every predicted value frozen first and zero free parameters, the correlation order at zero field becomes a pinned density modulation at 2k, at the predicted size. U = J/2 is a model point chosen at derivation, where the pair state lies below the plane wave.
- **At the contact value U = J,** the same move reads on the quench branch at k, the harmonic the paper reads. The visible share of the g² order, V² = A₁²/2C₁, follows Y/(1 + Y) within 2.7% on all 29 rows read. Y is set by Ny², so this conversion scales as y ~ N^(−1/2). The law's A₁, D₂ and C₁ met 59 of 63, with C₁ missing 4 at t = 2.
- **The ground state at U = J,** at the Δ < 0 points read, is an even mix of the two plane waves, with A₁/y = 2/(u − x). D₂ reads 0.00009 there at N = 243, yN = 4, where the rotor form of the pair state gives 0.437.
- **The second seat's attack at `8dfa11a`** refuted no formula, found a third engine error, and left the corrections applied here. [Its report is filed](second-seat/REPORT.md). A narrow recheck of this head is OPEN.

**Scope:** a closed system of N identical polaritons in three plane waves, with particle number conserved and unitary evolution. The overlaps enter through u = U/J: contact interactions with equal overlaps give u = 1, as the model section states, and the central result runs at u = 1/2. The source is [Trypogeorgos et al., Nature 639, 337 (2025)](https://www.nature.com/articles/s41586-025-08616-9), read at [arXiv:2407.02373](https://arxiv.org/abs/2407.02373). The paper reads a time-integrated density, averaged over about 8 × 10⁶ pulses, with its modulation at k_r, and g¹ by interferometry. Here that harmonic is A₁, and the central result is D₂ at 2k. The paper names g²(x − x′) and the removal of the linear coupling as next steps, so the field-driven move read here is a model result awaiting that experiment. Its 2.6% modulation, its wavevector shift of 0.04 μm⁻¹ at about 2.3 μm⁻¹, or 1.7%, and its 250 and 430 μW thresholds belong to an extended model, and those targets are OPEN.

## The model

Modes m = 0, +1, −1, so each polariton is one qutrit in balanced-ternary labels, and N of them live in the exact symmetric space, of dimension (N + 1)(N + 2)/2.

**H = Δ(n₊ + n₋) + U[n₀(n₊ + n₋) + n₊n₋] + J(P + P†) − h[a₀†(a₊ + a₋) + h.c.], with P = a₊†a₋†a₀a₀**

In units JN = 1: x = Δ/(JN), u = U/J, y = h/(JN), and δ = x + u. ρ is the fraction in each of the ± modes, ρ₀ = 1 − 2ρ, and j̄ = ⟨n₊⟩ is the pair count. In Re⟨P⟩, P is the pair operator above. In e(P) and in the rotor, P is the charge n₊ − n₋. Contact interactions on three plane waves give u = 1, after a constant.

The density is N + 2Re(⟨A⟩e^(ikx)) + 2Re(⟨B⟩e^(2ikx)), which is N + 2⟨A⟩cos kx + 2⟨B⟩cos 2kx on the states read, where ⟨A⟩ and ⟨B⟩ are real from real amplitudes or from the parity n₊ ↔ n₋, with A = a₀†a₊ + a₋†a₀ and B = a₋†a₊. So A₁ = 2|⟨A⟩|/N and D₂ = 2|⟨B⟩|/N are its two harmonics. The averaged two-point function is g²(r) = 1 + C₁cos kr + C₂cos 2kr.

## The central result, at 2k

At u = 1/2 and x = 0, mean field gives ρ = 1/5 in each of the ± modes. At y = 0 the density is flat and the order is in g². A generic even start at N = 729 converges to ⟨A⟩ = −30 ppb and ⟨B⟩ = −1 ppb at the residual 8 × 10⁻¹⁰, with C₂ = 0.0801 against 2ρ² = 0.08. At the residual 1 × 10⁻¹¹ ⟨A⟩ reads −1 ppb, and the energy equals N·e of the P = 0 sector within 1 ppb on the 26 y = 0 rows that hold P = 0 and have a sector row. The other 7 such rows, at u = 1 and x < 0, lie below that sector, by 136.29 at N = 729, x = −1/4.

Then the pinning comes on. The pattern's position α is a rotor with energy (c₀/N)P² + V(α), where c₀ = (ρ₀/ρ − u)/4 and V = −Ny²(u/4c₀) sin²α. So D₂/2ρ is the Mathieu expectation f(q), with q = (2/25)(yN)², and A₁/y = 2[1 + (1 + f)/10]. All of this was written before any engine run, with zero free parameters. The exact route's hand and Mathieu modes ran first, and f(q) comes from them.

| yN | q | D₂ read, N = 729 | 2ρf(q) predicted | A₁/y read | Predicted |
|---:|---:|---:|---:|---:|---:|
| 1/2 | 0.02 | 0.003962 | 0.004000 | 2.2028 | 2.2020 |
| 1 | 0.08 | 0.015830 | 0.015978 | 2.2087 | 2.2080 |
| 2 | 0.32 | 0.062062 | 0.062615 | 2.2317 | 2.2313 |
| 4 | 1.28 | 0.195339 | 0.196343 | 2.2980 | 2.2982 |
| 8 | 5.12 | 0.310305 | 0.310532 | 2.3551 | 2.3553 |
| 16 | 20.48 | 0.355329 | 0.355765 | 2.3774 | 2.3779 |

- **The conversion:** at strong pinning D₂ = f(q)·√(2C₂(y = 0)), so the correlation at zero field sets the modulation. Read within 0.6% at N = 729 for yN = 4, 8, 16, and within 1.9% at N = 243. Here √(2C₂) reads 0.40022, against 2ρ = 2/5, so these rows and the D₂ rows above read one number. Where the two differ, D₂/(f·2ρ) lies closer to 1 than D₂/(f·√(2C₂)) on all nine rows at N = 81, 243, 729, so a finite-N effect of C₂ on D₂ is OPEN. C₂ itself reads 0.0801 at zero field and 0.0798 at yN = 16, so the order in g² holds as the density appears.
- **Where it pins:** ⟨B⟩ is negative, so the 2k pattern's peaks sit at the nodes of the pinning potential, and ⟨A⟩ follows the sign of y. Under y → −y, ⟨A⟩ flips and ⟨B⟩ and E stay.
- **The susceptibility:** D₂/y² at yN = 1/2 grows by 9.57 and 9.17 from N = 81 to 243 to 729, against the predicted 9. At δ = 2, past the transition, it stays near 2/(δ + 1)² = 2/9. Exact y → 0 chains to N = 6561 reach the rotor as 1/N, with N(D₂ ratio − 1) = −6.72 at u = 1/2, x = 0, about the 0.95% at yN = 1/2 in the table.
- **With u = 0:** the mean-field energy is −Ny² at every α, so the leading-order pinning energy is 0. D₂ at yN = 4 reads 0.0010 at N = 729, against 0.1953 at u = 1/2, and A₁/y reads 2.00. The paper has this same linear term, and writes that the linear coupling alone leaves the modulation's phase unfixed. Below leading order the pin is set by zero-point energy: D₂/y² grows as N, with q₀ = Ny²/(16c₀²ω) and ω = √(2(1 − x²)) the sector gap, so y scales as N^(−1/2). The coefficient reads 1/ω to within 4×10⁻⁵ at seven x, from exact chains at N ≤ 6561 and from a Bogoliubov zero-point sum with zero fitted numbers. The form 1/ω is read off those numbers (CONJECTURE). ⟨B⟩ is positive here, so the 2k pattern pins at the potential's extrema, the opposite position from u > 0.

## The same move at contact, on the quench branch at k

At u = 1 the balanced pair state is an excited one, as the next section reads, so the contact test runs from |N, 0, 0⟩, the vacuum start of an optical parametric oscillator, with the linear coupling y on, at x = δ − 1.

**The law (derived for this test, pushed at `89a026a`).** With c = (a₊ + a₋)/√2 and d = (a₊ − a₋)/√2, A = √N(X_c + iP_d), and the pair term is a squeezer that the field displaces. With γ² = 1 − δ²:

- A₁ = 4|y|(cosh γt − 1)/(1 + δ), with ⟨A⟩ opposite to y and ⟨B⟩ positive
- C₁ = 4 sinh²(γt)/((1 + δ)N) + A₁²/2
- **V² = A₁²/2C₁ = Y/(1 + Y), with Y = (2Ny²/(1 + δ)) tanh²(γt/2)**
- D₂ = 2y²[(cosh γt − 1)²/(1 + δ)² + sinh²(γt)/γ²]

So at y → 0 the order at k sits in g² alone, with C₁ ≈ 4(1 − δ)j̄/N, and it passes into the mean density with Y. Before writing the law I had seen four rows at y = 1/1024, N = 729: three at δ = 0 and one at δ = 1/2, t = 3. Every row in this table was unseen.

| δ | y√N | t = 1: V² read | Law | t = 2: V² read | Law | t = 3: V² read | Law |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1/4 | 0.02604 | 0.02600 | 0.06814 | 0.06760 | 0.09457 | 0.09290 |
| 0 | 1/2 | 0.09667 | 0.09647 | 0.22805 | 0.22481 | 0.30552 | 0.29060 |
| 0 | 1 | 0.30032 | 0.29928 | 0.55140 | 0.53705 | 0.68060 | 0.62101 |
| 0 | 2 | 0.63444 | 0.63078 | 0.85066 | 0.82270 | 0.93713 | 0.86763 |
| 0 | 4 | 0.87872 | 0.87235 | 0.97334 | 0.94888 | 0.99410 | 0.96326 |
| 1/2 | 1/4 | 0.01367 | 0.01367 | 0.03906 | 0.03916 | 0.05761 | 0.05824 |
| 1/2 | 1/2 | 0.05256 | 0.05253 | 0.14054 | 0.14018 | 0.20072 | 0.19832 |
| 1/2 | 1 | 0.18192 | 0.18152 | 0.40086 | 0.39472 | 0.52650 | 0.49737 |
| 1/2 | 2 | 0.47278 | 0.47008 | 0.74486 | 0.72287 | 0.86093 | 0.79831 |
| 1/2 | 4 | 0.78754 | 0.78014 | 0.94056 | 0.91254 | 0.98240 | 0.94059 |

- **Against the frozen tolerances at N ≥ 243:** V² met 29 of 29 within 5% where predicted f ≤ 1/10, and read 0.9905 to 1.0267 of the law. A₁ met 21 of 21 within 5%, D₂ 21 of 21 within 10%, and C₁ 17 of 21 within 5%, where predicted f ≤ 1/20. The signs met 58 of 58, and energy stayed within 810 × 10⁻⁹ on all 94 rows.
- **The approach:** at δ = 0, y√N = 1/2, t = 2, the read over the law at N = 81, 243, 729, 2187 is 1.0746, 1.0341, 1.0144, 1.0052 for V², 0.7512, 0.8869, 0.9560, 0.9845 for A₁, and 0.5251, 0.7607, 0.9009, 0.9641 for C₁. Each deviation falls as 1/N.
- **Past the depletion range:** on the 35 rows at N ≥ 243 with predicted f above 1/10, V² reads 0.96 to 1.15 of the law, while A₁ reads down to 0.06 of its form and C₁ down to 0.004 of its form. So V² holds well past each of its parts (MEASURED on these rows, with the reason OPEN). At N = 81 it spreads from 0.02 to 1.27 of the law: the lowest row, y√N = 4, t = 3, has returned to f = 0.047.
- **Above 1:** as an operator identity V² = ((N − 1)/N)|⟨A⟩|²/(⟨A†A⟩ − ⟨n₀ + n₊⟩), so the shot term lets it pass 1 at finite N. It reads 1.20 on one row at N = 81 and 1.015 on one at N = 243.
- **The scale:** this conversion runs on y ~ N^(−1/2), against y ~ 1/N for the rotor's pin at u = 1/2. The exact power-series route reads j̄, ⟨A⟩, ⟨B⟩, C₁ and C₂ on 4 rows at N = 9, 27, largest off 1 × 10⁻⁹.

## The window of the pair state, and the plane wave below it

At u = 1, x = −1/4, a state with all polaritons in one mode has E/N² = −1/4, below the pair state's −1/16. So the contact model's pair state is an excited one, and the pinned ground-state test runs at u = 1/2, where the plane wave reads 0 against −1/10. A plain count with the paper's Hopfield coefficients, equal spatial overlaps and contact interactions puts the n₊² and n₊n₋ coefficients at 0.8 to 1.2 J, and unequal, so in that count the paper's point lies near u = 1 and outside this one-parameter form (CONJECTURE).

At y = 0, ρ₀ > 0 needs δ > −1 + 3u/2. The balanced state has c₀ > 0 for δ > (4u − 2)/(2 + u). It lies below the plane wave for 1 − δ < [(4 − 3u) − √(u(4 − 3u))]/2. For u = 0, 1/4, 1/2, 3/4, 1 that last edge is x = −1, −0.4243, −0.1910, −0.0522, 0, and the second seat's lowest sector at N = 243 follows it at 18 points scanned over P. At u = 1 the edge sits at δ = 1, where the disordered branch begins, so in mean field the ordered pair state is excited at every x there.

**Inside the window,** the same rotor with its frozen f(q) reads at five more points. These were predicted at `89a026a`, with every N = 729 row unseen. The read met 126 of 126, against D₂ within 20% at N = 243 and 10% at N = 729, and A₁/y within 2% and 1%.

| (u, x) | N | 2ρ | D₂ read, yN = 1 | Rotor | D₂ read, yN = 4 | Rotor | D₂ read, yN = 16 | Rotor | A₁/y read, yN = 4 | Rotor |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (1/4, −1/4) | 729 | 0.6154 | 0.075577 | 0.075894 | 0.458205 | 0.457938 | 0.576437 | 0.576913 | 2.4360 | 2.4360 |
| (1/4, 0) | 243 | 0.4615 | 0.013054 | 0.013283 | 0.179567 | 0.181921 | 0.394605 | 0.401360 | 2.1698 | 2.1673 |
| (3/4, 0) | 729 | 0.2857 | 0.005789 | 0.005929 | 0.085197 | 0.086940 | 0.240916 | 0.241801 | 2.2288 | 2.2302 |
| (3/4, 1/8) | 243 | 0.1429 | 0.000345 | 0.000423 | 0.005504 | 0.006759 | 0.066277 | 0.077093 | 2.0718 | 2.0698 |
| (1/2, 1/4) | 243 | 0.2000 | 0.000816 | 0.000889 | 0.012991 | 0.014160 | 0.120401 | 0.128489 | 2.0755 | 2.0714 |

The D₂ ratio rises to 1 from N = 243 to 729: at (3/4, 0) and yN = 1 it reads 0.930 and 0.976, and at (1/4, −1/4) 0.987 and 0.996.

**Below the plane-wave edge,** the ground state is the even mix of the two plane waves, read through ⟨(n₊ − n₋)²⟩/N². First-order theory from one plane wave gives A₁/y = 2/(u − x), and second order, with the pair term mixing n₀ = 2 into n₋ = 1, gives D₂/y² and its sign. I wrote these forms after seeing the second seat's rows at N = 81 and 243, so N = 729 is the unseen read. The read met 120 of 120, against ⟨P²⟩/N² at least 98%, A₁/y within 1%, D₂/y² within 5% at yN ≥ 4 and E = xN at y = 0.

| (u, x) | N | ⟨P²⟩/N² at yN = 16 | A₁/y read at yN = 4 | 2/(u − x) | D₂/y² read at yN = 16 | 2\|u − x − 1\|/(u(u − x)²) | Sign of ⟨B⟩ |
|---|---:|---:|---:|---:|---:|---:|---|
| (1, −1/4) | 729 | 0.9994 | 1.6017 | 1.6000 | 0.3202 | 0.3200 | + |
| (1, −1/8) | 243 | 0.9931 | 1.7842 | 1.7778 | 0.1961 | 0.1975 | + |
| (1/2, −1/4) | 729 | 0.9983 | 2.6691 | 2.6667 | 1.7922 | 1.7778 | − |
| (3/4, −1/8) | 243 | 0.9886 | 2.2936 | 2.2857 | 0.4501 | 0.4354 | − |

At u = 1, x = −1/4, N = 243, yN = 4, D₂ reads 0.00009 against the rotor's 0.437, and A₁/y reads 1.605 against the rotor's 3.875, with ⟨P²⟩ at 0.99965 of N². At u = 1/2, x = −1/4 D₂ reads 0.0005 against 0.511. The y → 0 response on the P = 0 branch still reaches the rotor's value as 1/N there, by the second seat's chains.

## N = 2 and N = 3, by hand

J = 2, Δ = 1, U = 0 give H₂ = [[0, √2J], [√2J, 2Δ]], with levels −2 and 4, and c₀² = 2/3, c₁² = 1/3 with opposite signs. The density is flat, and **g²(r) = (2/3)(1 − cos kr)²**, so two polaritons are never found at one point and g² at half a period reads 8/3. Pinning gives d⟨A⟩/dh = 2/9. The exact route and the engine both read these.

At N = 3, u = 1/4, x = −1/4, y = 0, the P = ±1 sectors share the ground level −1/3 − √73/12, below P = 0 at −0.951009. B carries P = +1 into P = −1, so the parity-even member the engine holds has ⟨B⟩ = (3/4)(1 + 1/√73) = 0.837781, and the engine reads 0.837780860.

## The ladder, to 3¹⁶ and 23,887,872

These are the fixed-momentum sectors of the symmetric space, with charge P = n₊ − n₋, tridiagonal with ⌊N/2⌋ + 1 states at P = 0, so N here counts interacting bosons in that space: 11,943,937 states at N = 23,887,872 and 21,523,361 at N = 43,046,721. A general state of N qutrits has dimension 3^N, and these rungs hold the symmetric, fixed-momentum part. Levels come from counting pivots at scale 2⁶⁰, with the squared off-diagonal at 2⁻⁹⁰, on 220 rows, and f, pairs and C₂ come from finite differences of those levels, with the step in each row. The exact route reads levels up to N = 243 and, at 2³²⁰ on a low-k block of 6,000 states, pairs and gap on the 44 rows from N = 59,049 up. [`READ.hbp`](READ.hbp) reads energy, f, gap, C₂ and the takeover ratios up to these rungs.

| u = 1/2 | Read at N = 23,887,872 | Read at N = 43,046,721 | Predicted |
|---|---:|---:|---:|
| x = 0: E/N² | −0.100000011 | −0.100000006 | −1/10 |
| x = 0: ⟨n₊ + n₋⟩/N | 0.399999975 | 0.399999986 | 2/5 |
| x = 0: gap | 1.095445 | 1.095445 | √(6/5) = 1.095445 |
| x = 3/2: pairs | 0.07735 | 0.07735 | 0.07735 |
| x = 3/2: gap | 3.46410 | 3.46410 | 2√3 = 3.46410 |
| x = 1/2, at the takeover: pairs | 86.65 | 105.54 | Grows as N^(1/3) |
| x = 1/2: gap | 0.013431 | 0.011038 | Falls as N^(−1/3) |

- **Across the ordered points:** energy, pair fraction, gap, C₂ and the rotor N²(e(P) − e(0)) = c₀P² all met their tolerances at N ≥ 19683. At N = 531,441, u = 1/2, x = 0, the rotor reads 0.625005, 2.500023, 5.625053, against 5/8, 5/2, 45/8.
- **Takeover scaling:** from N = 19683 up, each step of 3 raises the pair count by 1.4666, 1.4590, 1.4538, 1.4503, 1.4478, 1.4461, 1.4449, against 3^(1/3) = 1.4422, and the gap falls by 0.6945, 0.6941, 0.6939, 0.6937, 0.6936, 0.6935, 0.6935, against 0.6934.
- **Takeover constants:** near δ = 1 the soft modes are a 2D problem, H = p² + gr⁴ with g = (4 − 3u)/(16N). Its m = 0 levels give gap → 7.18495 g^(1/3) and pairs → 0.162869 g^(−1/3), less 0.44 at u = 1/2, read off the rows (CONJECTURE). Against the exact route at N = 43,046,721: gap ratio 0.99962, pairs 105.537 against 105.977 − 0.44.

## The quench

At u = 1, from |N, 0, 0⟩, the vacuum start of an optical parametric oscillator, a reversible leapfrog of integer shears runs the full dynamics, with every byte returned on reversal. In the paper the ±1 modes already hold population from the exciton reservoir and Rayleigh scattering when the oscillator starts. Bogoliubov gives pairs sinh²(γt)/γ² with γ² = 1 − δ² inside the band |δ| < 1, t² at the edges, and sin²(ωt)/ω² outside.

| δ | −2 | −1 | −1/2 | 0 | 1/2 | 1 | 2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Largest ⟨n₊ + n₋⟩/N by t = 8, N = 6561 | 0.0001 | 0.0069 | 0.2117 | 0.3842 | 0.6500 | 0.0154 | 0.0001 |

- **The first correction in 1/N:** j̄ = J₀ + J₁/N, with γ⁶J₁ = −(4 − 3δu)sinh²(2γt)/4 + (3/2)γt[1 + 3δ² − δu(2 + δ²)]sinh(2γt) + δ[3u(1 + δ²) − δ(7 + δ²)]sinh²(γt). At δ = ±1, J₁ = −[t² + (3 ∓ u)t⁴ + (2/5)(4 ∓ 3u)t⁶]. The second seat matched it to exact series through t¹⁴ at four (δ, u) with zero mismatch, and at large t it is −(4 − 3δu)J₀²/γ².
- **The pattern's harmonic:** after a quench C₁ = 4(1 − δ)j̄/N, as energy conservation fixes, so the order is at k. In the ground state it is at 2k, with C₁ of order 1/N.
- **Pinning in the quench:** A₁ = 4|y|(cosh γt − 1)/(1 + δ) at small depletion. It reads 0.002113 at δ = 0, t = 1, N = 729, against 0.002121. ⟨A⟩ is negative at y > 0 inside the band, opposite to the ground state, so the pattern grows with its k peaks on the potential's maxima there.
- **The preferred wavevector:** on a grid of x, the largest pair count at t = 2 sits at x = −u for u = 0, 1/2, 1. So a mode's resonance moves with the interaction. The 1.7% target needs the dispersion slope: the arXiv supplement writes it as a group velocity u in δ_j(k) = δ ± u(k − jk_r), with its value left to the measured dispersion of Fig. 1b.

## What missed

All 35 are in [`READ.hbp`](READ.hbp), against tolerances that stay as frozen. The rows are read by [`read_prediction.py`](read_prediction.py), first committed at `099b0c6`, after the first run finished and before its first read; the predictions it reads were frozen at `fce08f9`. Its floor of 2% of 1/50 at δ = 0 is the reader's own choice, and it holds out 12 C₁ rows at δ = 1, where the predicted value is 0: they read at most 200 ppm in size. A constant A₁/y of 2.29 would meet all twelve pinned A₁ rows of the central table at their 5%, so the table's fourth digit is what separates them. After the second seat's holds, the reader computes its own closed forms and counts rows per tag, so a missing row is a miss.

| Rows | Prediction | Read | What it shows |
|---:|---|---|---|
| 12 | Pair count within 2% of the closed form where it is at most N/100 | Furthest at δ = −1, t = 8, N = 6561: 0.33 of it, with pairs at 0.32% of N. At δ = 1, t = 8, N = 6561: 0.79 | That criterion is too wide. At fixed t the deviation falls as 1/N: at δ = 1, t = 4 it reads 5.7%, 2.0%, 0.7% at N = 2187, 6561, 19683. At the band edge the deviation is [1 + (3 ∓ u)t² + (2/5)(4 ∓ 3u)t⁴]/N, from exact series, so t⁴/N is its leading power, with coefficient 2/5 at δ = 1 and 14/5 at δ = −1 for u = 1. All 12 rows read within 0.35 to 1.37 of (first order)² from the first correction above |
| 6 | Re⟨P⟩/(N j̄) = −δ within 2% | At δ = ±1/2, t = 3: off by 5% | Energy conservation gives −δ + (3u/2)⟨j²⟩/(N j̄), which is −δ + 3u(j̄ + 1/2)/N for a Gaussian state: 0.5259 against the read 0.5244, and 0.0151 against 0.0148. Four of the six are at δ = 0, where my reader sets the 2% against a floor of 1/50, so 0.0004, and they read at most 0.015 |
| 12 | Pinned A₁ within 5% at N = 243, 729 for t = 1, 2, 3 | At δ = 0, t = 3, N = 729: 0.0279 against 0.0354 | Pairs read 9.2% of N there, where the closed form gives 13.8%, so the condensate has depleted. The first correction at δ = 0, u = 1 is A₁ = 2\|y\|\|w₀ + w₁/N\|, with w₀ = −2(cosh t − 1) and w₁ = −t sinh t + (65/12)cosh t − (11/3)cosh 2t + (5/4)cosh 3t − 3. Read over it at N = 729: 0.9998, 1.0031, 1.175 for t = 1, 2, 3. t = 1 is met everywhere, and t = 2 at N = 729 |
| 4 | Contact C₁ within 5% where predicted f ≤ 1/20 | 0.0709 against 0.0774 at N = 729, δ = 0, y√N = 1/4, t = 2; 0.0489 against 0.0517 at N = 2187, y√N about 1, t = 2. All four at t = 2 | The same 1/N term: C₁ is the part of the law that depletes fastest, and it reads 0.916 of its form at N = 729 and 0.945 at N = 2187. Its first correction is OPEN |
| 1 | e(P) rises with P at the rows read | It rises to P = 2N/3 and comes back to 0 at P = N | Every row read stays above e(0), so P = 0 is lowest, and "rises" was wrong at the last row |

## How the engine got here

[The first run](first-run/) stays on record, with 845 met and 73 missed, and [the third](third-run/), with 887 and 31. The separate route caught two engine errors, the attack caught a third, and one commit also raised the precision of the read-out. The tolerances stand as frozen:

- **A zero pivot went uncounted,** so the ground energy read 0 on 85 rows at P = 0, disordered and critical, up to 0.06 from exact at small N. That made up 42 of the misses, 30 on gaps and 12 on pairs: the first engine rebuilt with this fix alone reads 887 and 31, row for row as the third run does.
- **Matrix elements held 32 fractional bits in their roots,** so with the pivot fixed alone levels sit up to 9.3 × 10⁻¹² from exact, median 1.5 × 10⁻¹², outside the frozen 4,096 units of 2⁻⁶⁰ on 137 of the 143 rows. The first run's 143 of 143 counts both errors.
- **The read-out of ⟨A⟩, ⟨B⟩ and ⟨P⟩ held 20 fractional bits in its roots,** so ⟨A⟩ at N = 9 sat about 5 × 10⁻⁸ from exact. It now holds 32, and no row moved between met and missed.
- **The squared off-diagonal was floored at 2⁻⁶⁰,** found by the second seat's attack. Its first element is 622 units at N = 3¹⁶, so the third run read the pairs at the takeover 4,755 ppm high and the gap 371 ppm high there, and the disordered pairs 356 ppm low. It now sits at 2⁻⁹⁰, by long division, with levels within 1 unit at N ≤ 243, and the top rungs within 24 ppm of exact on pairs and under 1 ppm on gaps.

A second run was stopped when the second error was found.

## Second routes and controls

[`second_route.py`](second_route.py) is a separate Python program with exact rationals, and its rows are in [`SECOND-ROUTE.hbp`](SECOND-ROUTE.hbp).

- **Sector levels:** all 143 rows at N ≤ 243, within 1 unit of 2⁻⁶⁰.
- **Top rungs:** pairs and gap on 44 rows at N ≥ 59,049, at 2³²⁰ on a low-k block of 6,000 states, with largest offsets of 24 ppm and under 1 ppm, against limits of 200 ppm and 10 ppm. At N = 43,046,721, x = 1/2, pairs read 105.535428 against exact 105.537258, and the gap 0.011037825 at both.
- **Full space:** E, ⟨A⟩ and ⟨B⟩ on 60 rows at N ≤ 9, from exact inertia counts of a rational form congruent to H − λ, with one pinned row per point at N = 9. The central rows at N = 243 and 729 rest on the engine's Lanczos, with residuals at most 9.18 × 10⁻¹⁰. The first read of this route marked 1 row of 60, at the N = 3 doublet above: a centred difference across its cusp reads ⟨B⟩ = 0. ⟨B⟩ is now read on the parity-even block, which holds the engine's state, and [that first read](SECOND-ROUTE-FIRST-READ.hbp) stays on file.
- **Dynamics:** exact power series at N = 9 and 27, with pairs and ⟨A⟩ agreeing to about 10⁻⁹ against the engine's leapfrog, and ⟨B⟩, C₁ and C₂ on the 4 conversion rows.
- **Sector against full space:** at y = 0 the full-space run keeps every amplitude with n₊ ≠ n₋ at exactly 0, and the rest byte-equal to the sector engine, at N = 243 and 729.
- **Parity:** the engine's even start stays byte-even, so it reads the even space. Exact inertia of each exchange parity at N = 2, 3, 9 and 19 of 28 rows at N = 27, and Lanczos on the odd basis at N = 81, 243 and 5 pinned rows at N = 729, u = 1/2, x = 0, put the odd level above the even one on every row of the second seat's tests at `8dfa11a`. At yN = 16 they form a doublet, with the odd level 141,061, 12,014 and 3,059 × 10⁻¹² above at N = 81, 243, 729.
- **Control:** the pair element with its Bose factor removed reads 0.62, 0.19, 0.04, 0.008 of the closed form at t = 1, 2, 3, 4.

Hosted, [the workflow](../.github/workflows/polariton.yml) reproduces the receipt byte for byte, reads it against the prediction and reruns the exact route. At `8dfa11a`, [run 41939586670](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/41939586670) did all three on Ubuntu in 21 minutes, from a receipt first written on Windows. The hosted run of this receipt is OPEN.

## The second seat

[Three lanes attacked `8dfa11a`](second-seat/REPORT.md), on the derivations, the engine and the text, with no lane failed and no formula refuted. Every hold's disposition is in [`HOLDS-APPLIED.hbp`](second-seat/HOLDS-APPLIED.hbp).

- **Mutation:** 47 of 59 engine mutants were killed on lite stages at that head: 43 by the reader, 2 by the route alone, 2 by a panic alone. Three of the 12 survivors showed the reader trusting the engine's closed forms, and it now computes them. Hand rows and the route's C₂ now reach four more. One sets the printed energy offset to 0, and a separate read of that offset is OPEN. The other four sit below the tolerances at lite size or are equivalent. A mutation rerun on this head is OPEN.
- **Order of events:** `fce08f9` was pushed at 22:16:20Z and the engine file was first written at 22:16:32Z. Only the route's hand and Mathieu modes ran before the prediction. The prediction stands, and only attempt rows and added rows follow its first 29.
- **The leapfrog:** the exact series at N = 81 lies at most 2.25 × 10⁻⁷ from it, and a step 4 times larger panics at its check.

## Open

- **The extended model:** the off-resonant 100 fs pump at 80 MHz, the exciton reservoir that feeds the ±1 modes, loss over a BEC lifetime of a few hundred ps, spatial extent over about 30 μm, and averaging over about 8 × 10⁶ pulses, for the 250 and 430 μW thresholds and the coherence length, with the paper's Hopfield coefficients 0.54 for |0⟩ and 0.4 for |±1⟩ in the overlaps, and its dispersion slope for the 1.7% shift. With contact through the exciton fraction and equal spatial overlaps (CONJECTURE), a = X₁²/X₀² splits u: n₊n₋ takes u₁ = a, the −n² term takes u₂ = 2 − (a + 1/a)/2, δ shifts by 2 − 1/a, 4 − 3u becomes 4 − 4u₂ + u₁, and c₀ and q take u₁. With 0.54 and 0.4 as fractions, u₁ = 0.741 and the mean-field u is 1.026.
- **Reading the paper's 2.6% (CONJECTURE):** a coherent state of fixed position has A₁² = 16ρ₀ρ cos²(θ/2), with θ the pair phase, and a quench gives cos²(θ/2) = (1 − δ)/2. At the paper's Bragg fraction of 0.5%, 2.6% then needs (1 − δ)V² ≈ 0.017. The paper writes that its K = (n₁ + n₋₁)/2n₀ scales as A²/4, an expected 0.02%, and a density 1 + A cos kx with flat phase has K = A²/16, by direct Fourier 4.226×10⁻⁵ at A = 2.6%, or 0.004%. With the paper's factor the same reading needs (1 − δ)V² ≈ 0.068. How its Fig. 1e defines A is unread. With the law above at δ = 0 and tanh → 1, these read as y√N ≈ 0.09 and 0.19, a linear coupling h√N at about 9% to 19% of JN, from a vacuum start. The paper's seeded ±1 modes enter there. The averaged density holds δ and V² together, and g²(r) separates them, since C₁ and C₂ are independent of the pattern's position.
- **Which harmonic:** the paper's modulation is at k_r. The pinned ground state here is mainly at 2k, with D₂ = 0.195 and A₁ = 0.0126 at N = 729, yN = 4, and the k harmonic leads on the quench branch, with A₁ = 0.0800 and D₂ = 0.0046 at N = 729, δ = 0, y√N = 1, t = 1.
- **The first correction to C₁ and A₁ at general (δ, y),** and why V² holds past both.
- **A finite-N effect of C₂ on D₂,** at strong pinning.
- **Larger N:** the rotor rows reach N = 531,441, the full space reaches N = 729, of 266,815 states, and the quench's added rows reach N = 2187.
- **The narrow recheck of this head.**
