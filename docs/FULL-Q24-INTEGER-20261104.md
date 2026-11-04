# Google's whole `circuit_q24` in integers, November 4, 2026

**Scope:** all 1,257 gates of Google's published 24-qubit qsim sample, times 0 to 100, as a noiseless state vector on one laptop CPU, with interference from its 490 √X and √Y gates. Willow's 103-qubit depth-40 experiment is a different circuit, and `willow_103_depth40=NOT_RUN` stands.

**Status: every predicted row was met, including the comparison with Google's own simulator: [128 of 128 parts within 10⁻⁶](QSIM-OFFICIAL-REFERENCE-20261104.md), with the largest difference 1.667 × 10⁻⁹.**

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

## The reference

**The prediction named 64 amplitudes within 10⁻⁶ of Google's `qsim_amplitudes` at commit `50cac4b`. They agree.** [GPT-6's hosted run 41926857572](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/41926857572) built Google's source and ran the whole circuit on [these bitstrings](../data/google-qsim/full24_bitstrings.txt).

| Compared with Google's output | Parts | Above 10⁻⁶ | Largest difference |
|---|---:|---:|---:|
| This engine | 128 | 0 | 1.667 × 10⁻⁹ |
| The control, √Y's off-diagonal sign flipped | 128 | 128 | 8.01 × 10⁻⁴ |

So the gate and bit-order conventions the engine reads from Google's `lib/gates_qsim.h` and `lib/bitstring.h` are confirmed. The norm and the statistic above could not show this: the flipped sign reads 1.999464 at time 100, against 2.000356.

**A second reading of the same output.** FABLE5 ran [its own comparison script](../tools/compare_full24_with_qsim.py) on the hosted artifact, reading qsim's decimals exactly, and got the same four numbers. The hosted QNN outputs are byte-identical to this machine's: SHA-256 `6d2204b1…` for the engine and `3f6218c6…` for the control.

**How it came to run there.** The binary first built here was lost with WSL's `/tmp` before it produced output, and the rebuild was stopped by this machine's permission check on code from outside. The operator chose a GitHub runner, which leaves that code off this machine.

[The method, the receipt and the workflow](QSIM-OFFICIAL-REFERENCE-20261104.md).
