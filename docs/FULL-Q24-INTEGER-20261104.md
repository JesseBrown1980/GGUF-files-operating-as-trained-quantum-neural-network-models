# Google's whole `circuit_q24` in integers, November 4, 2026

**Scope:** all 1,257 gates of Google's published 24-qubit qsim sample, times 0 to 100, as a noiseless state vector on one laptop CPU, with interference from its 490 √X and √Y gates. Willow's 103-qubit depth-40 experiment is a different circuit, and `willow_103_depth40=NOT_RUN` stands.

**Status: the integer run met every row it could read. The comparison with Google's own simulator is OPEN.**

[The engine](../src/bin/google_qsim_full24.rs) is Rust 1.81, integers only, clippy `-D warnings`, with the [prediction](PREDICTION-FULL-Q24-20261104.hbp) pushed before it was written. It keeps two separate records of the same gates:

- **Exact:** each amplitude in Z[ω], ω⁸ = 1, over a power of √2, with coordinates mod 2⁶¹ − 1. Every gate of this circuit is additions and coordinate rotations here. About 537 MB.
- **Fixed point:** real and imaginary parts at scale 2⁶⁰. About 268 MB.

## What was read

[The receipt](FULL-Q24-RECEIPT-20261104.hbp), SHA-256 `6d2204b137128e8919a853e029a7a7ef2a3dfc9da2309af8c0f50ffe3fed665c`.

| Row | Predicted | Read |
|---|---|---|
| Gates | 1,257: 24 H, 474 CZ, 269 T, 243 √X, 247 √Y, max time 100 | The same, counted from the file |
| Google's file | Git blob `0c96e260…` | The same |
| Power of √2 at the end | 1004 | 1004 |
| Σ\|a\|², exact record | Rational part ≡ 2¹⁰⁰⁴, √2 part ≡ 0, mod p | Both hold |
| Phase counts at time 2, gate by gate from the state | The eight counts of [the 48-gate audit](GOOGLE-QSIM-LIKE-FOR-LIKE-20261104.md) | Equal |
| Norm, fixed-point record | Within 10⁻⁹ at each reading | Within 10⁻⁹ at each reading |
| 2²⁴ Σp² at time 2 | 1 | 1.000000 |
| 2²⁴ Σp² at time 100 | Between 1.9 and 2.1 | 2.000356 |

The statistic rises and settles at 2, the value for a deep random circuit:

| Time | 2 | 10 | 20 | 40 | 60 | 80 | 100 |
|---|---|---|---|---|---|---|---|
| 2²⁴ Σp² | 1.000000 | 3.039534 | 2.032014 | 2.000702 | 2.000024 | 2.000011 | 2.000356 |

Run time on an i5-8300H, one thread, with other work on the machine: 138 s for the exact record and 49 s for the fixed-point record.

## What is open

**The reference.** The prediction names 64 amplitudes, within 10⁻⁶ of Google's `qsim_amplitudes` at commit `50cac4b`. Those are [the bitstrings](../data/google-qsim/full24_bitstrings.txt) and the receipt's `FULL_Q24_AMPLITUDE` rows, and [the comparison script](../tools/compare_full24_with_qsim.py) reads qsim's output as exact decimals. It has not run: the binary built here was lost with WSL's `/tmp` before it produced output, and the rebuild was stopped by this machine's permission check on code from outside. This comparison is what tests the gate and bit-order conventions, which the engine reads from Google's `lib/gates_qsim.h` and `lib/bitstring.h`. The norm and the statistic above hold for a wrong convention too.

**The control.** Flipping the sign of √Y's off-diagonal gives 1.999464 at time 100, so the statistic alone cannot see it. The prediction has this mutant disagreeing with the reference, and that row waits with the comparison.
