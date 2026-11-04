# Google's official qsim: 64 complex amplitudes, actual source reference

**November 4, 2026.** This is the direct external reference gate for [the full 24-qubit, 1,257-gate QNN execution](FULL-Q24-INTEGER-20261104.md). The original prediction already registers 64 selected bitstrings, 128 real and imaginary components each within 10^-6 of the official Google simulator, and a sign-flipped √Y control that should disagree.

## Hosted method

1. GitHub Actions fetches the public official [quantumlib/qsim](https://github.com/quantumlib/qsim) source, **pinned at `50cac4b3fa331450b70387735479a00e223b8d25`**, without persisting write credentials. Both the original Google source file and the QNN circuit must match pinned Git blob `0c96e260ac6a9b765a703f4ca971924f674b76f3`.
2. On Ubuntu 24.04, compile Google's original C++17 `apps/qsim_amplitudes.cc`, then execute **all 1,257 published gates**, measuring the same 64 source-pinned output bitstrings.
3. Rebuild the existing Rust 1.81 exact-modular/fixed-point QNN 24-qubit implementation, retaining a byte-equal receipt. Also calculate the sign-flipped √Y gate control.
4. Compare 128 complex-component values by reading the upstream decimal output into exact arbitrary-precision integer fractions, and comparing against QNN's integer amplitudes scaled by 2^60. The gate requires **0 of 128 parts above 10^-6** for the genuine model, and **at least one part above 10^-6** for the wrong-gate control.
5. Save original Google output, the two QNN HBP records, verdict and SHA-256 receipt as a hosted artifact.

The [predict-first HBP](PREDICTION-FULL-Q24-20261104.hbp) was frozen ahead of this cross-check and remains unchanged. The [official reference workflow](../.github/workflows/qsim-official-reference.yml) and [fail-closed rational comparator](../tools/qsim_reference_gate.py) are additional independent checks.

**What it establishes upon a green run:** identical chosen bitstrings, the same entire 24-qubit gate file, agreement on all 64 complex amplitudes against Google's official simulator within the registered 10^-6 tolerance, and rejection of a wrong √Y convention. The benchmark maintains the original 24-qubit CPU timing receipts and all prior pass/fail outcomes. The 103-active-qubit Willow chip and its own depth-40 iSWAP-like circuit are separate published benchmarks.

A failed run must remain FAILED with the error, reference output and exact source head available. Any tolerance or source-revision change requires a new prediction and separate receipt.
