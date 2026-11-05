# The three-mode polariton test, November 4, 2026

The operator's word: *"Start the new run as well."* GPT-6 registered the design: *"whether a three-mode quantum system can reproduce the transition from spatial order in correlations to spatial order visible in the mean density, as a controlled symmetry-breaking field is introduced."*

**Status: run in integers, Rust 1.81 and clippy `-D warnings`, with [the prediction](PREDICTION.hbp) pushed before the engine existed, at `fce08f9`. Read against its frozen tolerances, [887 rows are met and 31 missed](READ.hbp), and the misses stay. Yes to the central test: with no fit, the correlation order at zero field becomes a pinned density modulation at the predicted size. The second seat's attack is OPEN.**

**Scope:** a closed system of N identical polaritons in three plane waves, with equal overlaps, no pump and no loss. The source is [Trypogeorgos et al., Nature 639, 337 (2025)](https://www.nature.com/articles/s41586-025-08616-9), read at [arXiv:2407.02373](https://arxiv.org/abs/2407.02373). Its 2.6% modulation, 2% wavevector shift and 250 and 430 μW thresholds belong to an extended model, and those targets are OPEN.

## The model

Modes m = 0, +1, −1, so each polariton is one qutrit in balanced-ternary labels, and N of them live in the exact symmetric space, of dimension (N + 1)(N + 2)/2.

**H = Δ(n₊ + n₋) + U[n₀(n₊ + n₋) + n₊n₋] + J(P + P†) − h[a₀†(a₊ + a₋) + h.c.], with P = a₊†a₋†a₀a₀**

In units JN = 1: x = Δ/(JN), u = U/J, y = h/(JN), and δ = x + u. Contact interactions on three plane waves give u = 1, after a constant.

The density is N + 2⟨A⟩cos kx + 2⟨B⟩cos 2kx, with A = a₀†a₊ + a₋†a₀ and B = a₋†a₊. So A₁ = 2|⟨A⟩|/N and D₂ = 2|⟨B⟩|/N are its two harmonics. The averaged two-point function is g²(r) = 1 + C₁cos kr + C₂cos 2kr.

## The central result

At u = 1/2 and x = 0, mean field gives ρ = 1/5 in each of the ± modes. At y = 0 the density is flat and the order is in g². A generic even start at N = 729 converges to ⟨A⟩ = −30 ppb and ⟨B⟩ = −1 ppb, with C₂ = 0.0801 against 2ρ² = 0.08.

Then the pinning comes on. The pattern's position α is a rotor with energy (c₀/N)P² + V(α), where c₀ = (ρ₀/ρ − u)/4 and V = −Ny²(u/4c₀) sin²α. So D₂/2ρ is the Mathieu expectation f(q), with q = (2/25)(yN)², and A₁/y = 2[1 + (1 + f)/10]. All of this was written before any run, with no fitted number.

| yN | q | D₂ read, N = 729 | 2ρf(q) predicted | A₁/y read | Predicted |
|---:|---:|---:|---:|---:|---:|
| 1/2 | 0.02 | 0.003962 | 0.004000 | 2.2028 | 2.2020 |
| 1 | 0.08 | 0.015830 | 0.015978 | 2.2087 | 2.2080 |
| 2 | 0.32 | 0.062062 | 0.062615 | 2.2317 | 2.2313 |
| 4 | 1.28 | 0.195339 | 0.196343 | 2.2980 | 2.2982 |
| 8 | 5.12 | 0.310305 | 0.310532 | 2.3551 | 2.3553 |
| 16 | 20.48 | 0.355329 | 0.355765 | 2.3774 | 2.3779 |

- **The conversion:** at strong pinning D₂ = f(q)·√(2C₂(y = 0)), so the correlation at zero field sets the modulation. Read within 0.6% at N = 729 for yN = 4, 8, 16.
- **Where it pins:** ⟨B⟩ is negative, so the 2k pattern's peaks sit at the nodes of the pinning potential, and ⟨A⟩ follows the sign of y. Under y → −y, ⟨A⟩ flips and ⟨B⟩ and E stay.
- **The susceptibility:** D₂/y² at yN = 1/2 grows by 9.57 and 9.17 from N = 81 to 243 to 729, against the predicted 9. At δ = 2, past the transition, it stays near 2/(δ + 1)² = 2/9.
- **With u = 0:** the mean-field energy −Ny² has no dependence on α, so this pinning is absent at leading order. D₂ at yN = 4 reads 0.0010 at N = 729, against 0.196 at u = 1/2, and A₁/y reads 2.00.

## N = 2, by hand

J = 2, Δ = 1, U = 0 give H₂ = [[0, √2J], [√2J, 2Δ]], with levels −2 and 4, and c₀² = 2/3, c₁² = 1/3 with opposite signs. The density is flat, and **g²(r) = (2/3)(1 − cos kr)²**, so two polaritons are never found at one point and g² at half a period reads 8/3. Pinning gives d⟨A⟩/dh = 2/9. The exact route and the engine both read these.

## The ladder, to 3¹⁶ and 23,887,872

These are the fixed-momentum sectors of the symmetric space, tridiagonal with N/2 + 1 states at P = 0, so N here counts interacting bosons in that space. Levels come from counting pivots at scale 2⁶⁰, on 220 rows.

| u = 1/2 | Read at N = 23,887,872 | Read at N = 43,046,721 | Predicted |
|---|---:|---:|---:|
| x = 0: E/N² | −0.100000011 | −0.100000006 | −1/10 |
| x = 0: ⟨n₊ + n₋⟩/N | 0.399999975 | 0.399999986 | 2/5 |
| x = 0: gap | 1.095445 | 1.095445 | √(6/5) = 1.095445 |
| x = 3/2: pairs | 0.07734 | 0.07732 | 0.07735 |
| x = 3/2: gap | 3.46408 | 3.46422 | 2√3 = 3.46410 |
| x = 1/2, at the takeover: pairs | 86.80 | 106.04 | Grows as N^(1/3) |
| x = 1/2: gap | 0.013433 | 0.011042 | Falls as N^(−1/3) |

- **Across the ordered points:** energy, pair fraction, gap, C₂ and the rotor N²(e(P) − e(0)) = c₀P² all met their tolerances at N ≥ 19683. At N = 531,441, u = 1/2, x = 0, the rotor reads 0.625005, 2.500023, 5.625053, against 5/8, 5/2, 45/8.
- **Takeover scaling:** the pair count rises by 1.4509 at the top step, against 3^(1/3) = 1.4422, and the gap falls by 0.6937, against 0.6934.
- **The plane wave:** at u = 1, x = −1/4, a state with all polaritons in one mode has E/N² = −1/4, below the pair state's −1/16. So the contact model's pair state is an excited one, and the pinned ground-state test runs at u = 1/2, where the plane wave reads 0 against −1/10.

## The quench

From |N, 0, 0⟩, as an optical parametric oscillator starts, a reversible leapfrog of integer shears runs the full dynamics, with every byte returned on reversal. Bogoliubov gives pairs sinh²(γt)/γ² with γ² = 1 − δ² inside the band |δ| < 1, t² at the edges, and sin²(ωt)/ω² outside.

| δ | −2 | −1 | −1/2 | 0 | 1/2 | 1 | 2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Largest ⟨n₊ + n₋⟩/N by t = 8, N = 6561 | 0.0001 | 0.0069 | 0.2117 | 0.3842 | 0.6500 | 0.0154 | 0.0001 |

- **The pattern's harmonic:** after a quench C₁ = 4(1 − δ)j̄/N, as energy conservation fixes, so the order is at k. In the ground state it is at 2k, with C₁ of order 1/N.
- **Pinning in the quench:** A₁ = 4|y|(cosh γt − 1)/(1 + δ) at small depletion. It reads 0.002113 at δ = 0, t = 1, N = 729, against 0.002121. ⟨A⟩ is negative at y > 0 inside the band, opposite to the ground state, so the pattern grows with its k peaks on the potential's maxima there.
- **The preferred wavevector:** on a grid of x, the largest pair count at t = 2 sits at x = −u for u = 0, 1/2, 1. So a mode's resonance moves with the interaction. The 2% target needs the dispersion slope from the paper's supplement.

## What missed

All 31 are in [`READ.hbp`](READ.hbp), against tolerances that stay as frozen.

| Rows | Prediction | Read | What it shows |
|---:|---|---|---|
| 12 | Pair count within 2% of the closed form where it is at most N/100 | At δ = 1, t = 8, N = 6561: 0.79 of it | That criterion is too wide. At fixed t the deviation falls as 1/N: at δ = 1, t = 4 it reads 5.7%, 2.0%, 0.7% at N = 2187, 6561, 19683. At the band edge it grows quickly with t, about as t⁴/N (CONJECTURE) |
| 6 | Re⟨P⟩/(N j̄) = −δ within 2% | At δ = ±1/2, t = 3: off by 5% | The same depletion. Four of the six are at δ = 0, where a percentage of 0 is my reader's floor, reading at most 0.015 |
| 12 | Pinned A₁ within 5% at N = 243, 729 for t = 1, 2, 3 | At δ = 0, t = 3, N = 729: 0.0279 against 0.0354 | Pairs reach about 14% of N there, so the condensate has depleted. t = 1 is met everywhere, and t = 2 at N = 729 |
| 1 | e(P) rises with P at the rows read | It rises to P = 2N/3 and comes back to 0 at P = N | Every row read stays above e(0), so P = 0 is lowest, and "rises" was wrong at the last row |

## How the engine got here

[The first run](first-run/) stays on record, with 845 met and 73 missed. The separate route caught two engine errors, and neither touched a tolerance:

- **A zero pivot went uncounted,** so the ground energy read 0 on the disordered rows. That made up 42 of the misses.
- **Matrix elements held 32 fractional bits in their roots,** so levels sat about 10⁻¹¹ from exact, outside the frozen 4,096 units of 2⁻⁶⁰ on all 143 rows. They now read within 66 units.

A second run was stopped when the second error was found.

## Second routes and controls

[`second_route.py`](second_route.py) is a separate Python program with exact rationals, and its rows are in [`SECOND-ROUTE.hbp`](SECOND-ROUTE.hbp).

- **Sector levels:** all 143 rows at N ≤ 243 within 66 units of 2⁻⁶⁰.
- **Full space:** E, ⟨A⟩ and ⟨B⟩ on 36 rows at N ≤ 9, from exact inertia counts of a rational form congruent to H − λ.
- **Dynamics:** exact power series at N = 9 and 27, with pairs and ⟨A⟩ agreeing to about 10⁻⁹ against the engine's leapfrog.
- **Sector against full space:** at y = 0 the full-space run keeps every amplitude with n₊ ≠ n₋ at exactly 0, and the rest byte-equal to the sector engine, at N = 243 and 729.
- **Control:** the pair element without its Bose factor reads 0.62, 0.19, 0.04, 0.008 of the closed form at t = 1, 2, 3, 4.

Hosted, [the workflow](../.github/workflows/polariton.yml) reproduces the receipt byte for byte, reads it against the prediction and reruns the exact route.

## Open

- **The extended model:** pump, loss and spatial extent, for the 250 and 430 μW thresholds and the coherence length, with the paper's Hopfield coefficients 0.54 and 0.4 for the overlaps, and its dispersion slope for the 2% shift.
- **Reading the paper's 2.6% (CONJECTURE):** a coherent state of fixed position has A₁² = 16ρ₀ρ cos²(θ/2), with θ the pair phase, and a quench gives cos²(θ/2) = (1 − δ)/2. At the paper's Bragg fraction of 0.5%, 2.6% then needs (1 − δ)V² ≈ 0.017, with V the visibility after averaging over pulses. The averaged density cannot separate δ from V, and g²(r) can, since C₁ and C₂ do not depend on the pattern's position.
- **Larger N:** the rotor rows reach N = 531,441, and the full space reaches N = 729.
- **The second seat's attack on this folder.**
