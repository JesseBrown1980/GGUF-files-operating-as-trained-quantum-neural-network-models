# GGUF files operating as trained neural models

> **Connected research index (2026-11-04):** [17-repository evidence map](https://github.com/JesseBrown1980/Hard-drive-and-USB-as-GPU/blob/main/ECOSYSTEM-RESEARCH-MAP-20261104.md) · [same-gate Google qsim test in QNN](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/blob/main/docs/GOOGLE-QSIM-LIKE-FOR-LIKE-20261104.md) · [physical 96³ HTTP-0 results](https://github.com/JesseBrown1980/qoled-internet-HEB-C-revisted-HTTP---free-0-hbi-hbp-sha-sh-hash/blob/main/engine96/MEASURED-20261104.hbp). These are navigation links; the verdicts and limits of this project remain as recorded here.

Qutrit virtual quantum neural networks, simulated exactly and stored as GGUF files.
The construction follows [Virtual quantum neural networks](https://arxiv.org/pdf/2609.11327)
(Zhao, Zhao, Li, Li & Chiribella). Several branch circuits are combined with
coefficients, here balanced trits c ∈ {−1, 0, +1}. A trained model, its branches
and its coefficients are one GGUF v3 file. Inference loads the file and runs the
circuit exactly.

Rust 1.81 with clippy (`-D warnings`), integer only, no `f32`/`f64`, no JSON, no
Node. Receipts are HBP/HBI with SHA-256, and every receipt line ends in `json=0`.

Predictions were sealed in [`PREREG.hbp`](PREREG.hbp) (sha256 `5485a600…`) and
pushed in commit `03ff607` before any code existed.

## Google qsim exact circuit compatibility — November 4, 2026

The [prediction-first Google-circuit audit](docs/GOOGLE-QSIM-LIKE-FOR-LIKE-20261104.md) uses this repository's integer-only Rust environment to run **exact Google-defined qubit operations** without replacing them with the existing QNN's qutrit operations. Its sources are [Google qsim's actual 24-qubit sample circuit](https://github.com/quantumlib/qsim/blob/master/circuits/circuit_q24) and [Google's complete Bell-state tutorial](https://quantumai.google/qsim/qsimcirq_tutorial).

- Complete **2-qubit H/CNOT tutorial**: expected `P(00)=P(11)=1/2`, `P(01)=P(10)=0`.
- Exact **24-qubit 48-gate published prefix**: 24 H, 12 CZ, 12 T; enumerate all **16,777,216** output bitstrings, their eighth-root amplitude phases and exact `1/2^24` probabilities.
- [Frozen prediction](docs/PREDICTION-GOOGLE-QSIM-20261104.hbp) committed before the implementation; [Rust 1.81 CI](.github/workflows/google-qsim.yml) tests gate/source identity, exact counts and unsupported-gate rejection.

- [The whole 1,257-gate circuit](docs/FULL-Q24-INTEGER-20261104.md), times 0 to 100, with interference, in integers: exact-record Σ|a|² ≡ 2¹⁰⁰⁴ mod 2⁶¹−1, and 2²⁴Σp² settling at 2.000356 at time 100. **[Official Google qsim 64-amplitude comparison PASS](docs/QSIM-OFFICIAL-REFERENCE-20261104.md): 128/128 complex components within 10⁻⁶ (largest discrepancy 1.667 × 10⁻⁹), with 128/128 wrong-√Y control components rejected.** [Source-pinned HBP receipt](docs/GOOGLE-QSIM-OFFICIAL-REFERENCE-20261104.hbp).

**Measured scope:** Google's 103-active-qubit depth-40 Willow experiment is an entirely different iSWAP-like, noisy quantum circuit. No full Willow circuit or quantum speed advantage is claimed. HTTP-0 has [23,887,872 actual ternary channels](https://github.com/JesseBrown1980/qoled-internet-HEB-C-revisted-HTTP---free-0-hbi-hbp-sha-sh-hash/blob/main/engine96/MEASURED-20261104.hbp) and 43,046,721 virtual evidence addresses, but those counts are not `2^103` complex qubit amplitudes.

## Three-mode polariton test — November 4, 2026

[The test](polariton/README.md) takes the pair scattering behind [the 2025 Nature polariton supersolid](https://www.nature.com/articles/s41586-025-08616-9) as N identical qutrits, with labels −1, 0, +1, in their exact symmetric space, in integers and with the prediction pushed first. It answers GPT-6's central question at U = J/2, a model point chosen at derivation, where contact interactions alone give U = J: with every predicted value frozen first and zero fitted numbers, the order that sits in the two-point correlation at zero field becomes a pinned density modulation at 2k, at the predicted size, reading 0.3553 against 0.3558 at N = 729, in the full symmetric space of 266,815 states. At U = J the ground state at the Δ < 0 points read is an even mix of the two plane waves, and the order moves into the density on the quench branch, at k, the harmonic the paper reads: the visible share of the g² order follows a closed law at leading order in 1/N, V² = Y/(1 + Y), within 2.7% on the 29 rows of its frozen range and at 0.96 to 1.15 of it on the 35 rows past that range. N counts bosons here, so the rungs at N = 23,887,872 and 43,046,721 are tridiagonal sectors of 11,943,937 and 21,523,361 states, and the section above counts HTTP-0 channels and addresses at those two sizes. On those rungs, at U = J/2, the energy, pair fraction and gap read the predicted values at Δ = 0, the pairs and gap at Δ = 3JN/2, and at the takeover, Δ = JN/2, the pairs and gap scale as N^(1/3) and N^(−1/3). **1,675 rows met and 36 missed**, with the misses kept, a separate exact-rational route on 143 levels at N ≤ 243 and on pairs and gaps at the top rungs from the takeover up, and [the second seat's attack](polariton/second-seat/REPORT.md) filed with its corrections applied.

**Scope:** a closed system of three plane waves, with particle number conserved and unitary evolution. The paper's modulation is at k_r, which is A₁ here. Its 2.6% modulation, 1.7% wavevector shift and 250 and 430 μW thresholds need pump, loss and its dispersion, and are OPEN.

**Status:** merged November 5, 2026, as [`4693097`](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/commit/4693097b82b27c15c4c9d7ae3d84f2500aee0575), at the head GPT-6 approved, `5792654`, with [hosted run 42029612465](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/42029612465) passing in 98 minutes. The read stands at 1,675 met and 36 missed, with every miss kept.

**Now, the frozen read of the first correction in 1/N, [PR #11](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/pull/11):** the baseline on seen rows is filed. [The second seat's source and certificate review](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/tree/fable5-polariton-first-correction-20261105/polariton-first-correction/reviews/opus55-source-2d77636) found the engine fit to read the grid on all three lanes, and its 53 holds on the reader, the route and the checks are applied at `7f72d2c`. No grid point has run. The grid runs next, once that head passes hosted, then [the quantum-to-classical bridge](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/issues/9).

## Versions at a glance

Every version was pre-registered before its code, run twice (the second time from a fresh clone, byte
for byte), and sealed with its failures kept. Every energy is exact. The certified ground energies E₀
come from HEB-C's sturmfast in exact integer arithmetic.

| Version | Lattice | What changed | Best r = 9 energy | Certified E₀ at r = 9 | Primary target |
|---|---|---|---|---|---|
| v1 | 2×2 Z₃ | Clifford qutrit network | 48 | [15.378, 15.379) | see §3–4 |
| v2 | 2×2 | non-Clifford, Z[ζ₉] | 33.578 | same | FAIL |
| v3 | 2×2 | identity-reachable layer | 16.000 | same | FAIL |
| v4 | 2×2 | real rational rotations | 15.696 | same | PASS |
| v5 | 2×2 | holonomy-sector coherence | 15.384 | same | PASS |
| v6 | 2×2 | 9× finer angle grid | 15.382 | same | PASS |
| v7 | 2×2 | correlated layer, pixel backend | 15.381 | same | PASS |
| v8 | 3×2 Z₃ | the largest torus held exactly; sector certificate | 23.380 | [23.298, 23.299) | FAIL |
| v9 | 3×2 | correlations in each plaquette's flux frame | 23.301 | same | PASS |
| v10 | 3×3 Z₃ | gauge-fixed basis; zero-winding certificate block | 35.622 | [35.288, 35.289) | FAIL |
| v11 | 3×3 | tree links dressed in their own frames | 35.321 | same | FAIL (r = 27, 81 within 0.002) |

## 1. The exact simulator

| | |
|---|---|
| Amplitudes | Eisenstein integers a + bω, ω = e^{2πi/3}, ω² = −1 − ω ([`src/eisenstein.rs`](src/eisenstein.rs)) |
| State | the true state is v / √3ᵏ; v holds 3ⁿ Eisenstein integers and k is counted ([`src/qutrit.rs`](src/qutrit.rs)) |
| Probabilities | exact fractions (Σ (a² − ab + b²)) / 3ᵏ |
| Gates | X shift; diag(1, ω^a, ω^b); Fourier F, which adds 1 to k; SUM \|c, t⟩ → \|c, t + c⟩; all with exact inverses |
| Network | L layers of [F on every qutrit, diag(1, ω^a, ω^b) on every qutrit, SUM ring q → q + 1] ([`src/qnn.rs`](src/qnn.rs)) |
| Parameters | trits: a and b ∈ {0, 1, 2} per qutrit per layer, 36 for 6 qutrits and 3 layers |

## 2. The task, the training and the models

- **Data:** the circle task sealed in the PREREG ([`src/task.rs`](src/task.rs)).
  Points (x, y) in 0…26 have label 1 iff (x − 13)² + (y − 13)² ≤ 81. The train set
  is the 486 points with (7x + 11y) mod 3 ≠ 0; the test set is the other 243
  (89 labelled 1, 154 labelled 0).
- **Encoding:** x and y each go in as three base-3 digits on qutrits 0–2 and 3–5.
  The readout is qutrit 0, with class 1 iff P(0) > P(1).
- **Training** ([`src/train.rs`](src/train.rs)): coordinate descent over the
  trits. Each trit tries its three values, and a change is kept only on a strict
  gain in the training count.
- **Branches:** three are seeded from the trits of `ACER-OPUS-RED`,
  `ACER-FABLE-GREEN` and `ACER-MYTHOS-BLUE` (parameter i = star trit (4099·i) mod
  12,288). Three controls are seeded from SHA-256 streams.
- **Virtual model** ([`src/virtual_qnn.rs`](src/virtual_qnn.rs)): score(x) =
  Σ_b c_b (P_b(0) − P_b(1)), exact. c is chosen on the train set from all 26
  non-zero balanced-trit vectors.
- **Models** ([`src/gguf_model.rs`](src/gguf_model.rs)): each trained branch and
  each virtual model is a GGUF v3 file (`general.architecture =
  asolaria-qutrit-vqnn`).
  - Header: task, encoding, layers, class rule, and train/test correct counts.
  - Tensors: int8 `branch_b.params` and `virtual.coefficients`.

## 3. Results (layers = 3, up to 4 sweeps)

| ID | Prediction | Measured | Verdict |
|---|---|---|---|
| Q1 | every circuit keeps the exact norm Σ\|v\|² = 3ᵏ | every trained branch, every test point | **PASS** |
| Q2 | F⁴ = I and every trained circuit's inverse restores its input | every test point | **PASS** |
| Q3 | each trained branch beats the majority class on test | every branch 154 / 243, the majority count | **FAIL** |
| Q4 | virtual train accuracy ≥ best single branch | 322 ≥ 322 | **PASS** |
| Q5 | virtual test accuracy ≥ best single branch | 154 ≥ 154 | **PASS** |
| Q6 | star-seeded and SHA-seeded best test accuracy within 50‰ | gap 0 | **PASS** |
| Q7 | every GGUF model, reloaded, reproduces its header | 8 of 8 | **PASS** |

**Why Q3 fails: the sealed circuit is a stabilizer circuit.** For qutrits, every
diagonal gate diag(1, ω^a, ω^b) is a Clifford gate, and so are F and SUM. A basis
input pushed through a Clifford circuit stays a stabilizer state. The consequence:

- **The readout:** each single-qutrit probability is exactly 0, 1/3 or 1; the
  test `trit_phase_circuits_are_stabilizer_circuits` checks this.
- **The landscape is flat:** on nearly every input P(0) = P(1) = 1/3, so every
  branch answers class 0. That gives 322 of 486 on train and 154 of 243 on test.
- **No training move:** no single trit change improves the count. Training stops
  after one sweep, and no parameter changes.

A trit-phase network of this kind cannot draw a circle, whatever its trits. This
is the Gottesman–Knill boundary.

**The next layer** needs one non-Clifford gate. The qutrit T gate,
diag(1, ζ, ζ⁸) with ζ = e^{2πi/9}, keeps the arithmetic exact and integer.
- **Amplitudes:** they move from Eisenstein integers into Z[ζ₉], six integer
  coefficients each.
- **Probabilities:** these lie in the real cubic field Q(2cos(2π/9)). They are
  compared exactly by isolating that root with integer bisection.

**Inference example:**
`gguf-qnn infer results/star-virtual.gguf 13 13` prints each branch's exact
P(0), P(1), P(2) = 129,140,163 / 3¹⁸ = 1/3, then score 0 and class 0.

## 4. Yang–Mills: the qutrit model on the Z₃ sector of S₃ gauge theory

Z₃ is the rotation subgroup of S₃. Its 3-cycle plaquettes are the excitations behind
the leading 3·J_B gap of the HEB-C S₃ certificates.

- **Lattice:** a 2 × 2 periodic torus with 8 links. Each link is a qutrit g ∈ Z₃.
- **Plaquettes:** h_p = g_x(s) + g_y(s + x̂) − g_x(s + ŷ) − g_y(s) mod 3.
- **Hamiltonian:** H = J_E·E + J_B·M, where E = Σ_links (2 − X − X†), M = Σ_p 3·[h_p ≠ 0] and r = J_B/J_E.
- **Physical states:** the Gauss-law sector, spanned by uniform superpositions over gauge orbits ([`src/ym_z3.rs`](src/ym_z3.rs)).

The physical Hamiltonian is written in the matrix format of HEB-C's `sturmfast`
certifier. Its levels are bracketed by exact interval Sturm counts: 185 calls,
none ambiguous. The qutrit model is trained on the exact gauge-projected energy
and stored as GGUF files.

Predictions: [`PREREG-YM-Z3.hbp`](PREREG-YM-Z3.hbp) (commit `71ba280`, unchanged).
Code: commit `a6d71e0`. Receipts: [`results-ym-z3/`](results-ym-z3/). Seal, provenance
and replay: [`SEAL-YM-Z3.hbp`](SEAL-YM-Z3.hbp).

### Certified levels (J_E = 1)

| r | E₀ | E₈ | E₉ | E₉ − E₈ | E₉ − E₈ − 6r |
|---|---|---|---|---|---|
| 9 | [15.378, 15.379) | [15.854, 15.855) | [61.833, 61.834) | (45.978, 45.980) | (−8.022, −8.020) |
| 27 | [15.799, 15.800) | [15.950, 15.951) | [170.742, 170.743) | (154.791, 154.793) | (−7.209, −7.207) |
| 81 | [15.933, 15.934) | [15.983, 15.984) | [495.081, 495.082) | (479.097, 479.099) | (−6.903, −6.901) |

### Verdicts

| ID | Prediction | Result |
|---|---|---|
| Z1 | 243 physical states, every gauge orbit of size 27 | **PASS** |
| Z2 | exactly 9 levels below 16 + 3r | **PASS** at r = 9, 27, 81 |
| Z3 | exactly 9 levels below 16 + 6r − 12 | **PASS** |
| Z4 | at least 10 levels below 16 + 6r | **PASS** (68 at each r) |
| Z5 | none below 15, exactly 9 below 16 | **PASS** |
| Z6 | the trained qutrit model reaches energy exactly 16, above the certified E₀ | **FAIL**: 48 and 64 at r = 9, 120 and 228 at r = 27, 336 and 662 at r = 81 (all above E₀) |
| C1 | the Z₃ leading gap is 6r, against S₃'s 3r | **supported at three couplings, not proven**: (E₉ − E₈)/r ≥ 5.108, 5.733, 5.914 |

**Results.**
- **Ground cluster:** the nine flat Z₃ vacua (holonomy pairs in Z₃²) form the
  ground cluster at every coupling, all below 16.
- **The gap:** the first excitation sits near 16 + 6r, not 16 + 3r. On a torus the
  Z₃ fluxes sum to zero mod 3, so the lightest excitation carries flux on two
  plaquettes, not one.
- **The model:** the Clifford model's best energies are far above the certified
  ground energy. The reference state |0…0⟩, projected onto the trivial flat
  orbit, has energy exactly 16. So 16 is the stabilizer value the v1 ansatz did not
  reach. This is the baseline version 2 must improve on.

**Replay.**
- **Two runs:** run A (this working copy) and run B (a fresh clone at `a6d71e0`,
  built separately) used the identical binary (sha256 `21ad3ad2…`).
- **Identical output:** all 10 files are byte-identical, including the matrix, the
  six GGUF models, the HBP and HBI receipts, the checksum manifest and the console
  log.
- **Certifier:** `sturmfast` sha256 `bf2455f5…`, built from HEB-C commit `5243e82`.

**Erratum E1.** In `YM-Z3.hbp`, the `gap_minus_6r_in` field of the CERTIFIED rows
formats negative milli-values incorrectly: it prints −9.978 for −8.022. The
receipts are kept as produced. The correct values, recomputed from the certified
E₈ and E₉ brackets in the same rows, are in the table above and in `SEAL-YM-Z3.hbp`.
No certified bracket and no verdict is affected.

Reproduce: build HEB-C's `sturmfast` (`native/ym`, `cargo build --release --bin
sturmfast`), then:

```sh
cargo run --release -- ym-z3 PATH/TO/sturmfast data/stars out 2
cd out && sha256sum -c ../results-ym-z3/SHA256SUMS
```

## 5. Version 2: the non-Clifford qutrit network

Predictions: [`PREREG-V2.hbp`](PREREG-V2.hbp) (commit `d5834b8`, unchanged). Code: commit
`334a066`. Receipts: [`results-v2/`](results-v2/). Seal, replay and diagnostic:
[`SEAL-V2.hbp`](SEAL-V2.hbp).

**Exact arithmetic.**
- **Amplitudes:** they live in Z[ζ₉], ζ = e^{2πi/9}, with six integer coefficients
  modulo x⁶ + x³ + 1 ([`src/cyclo.rs`](src/cyclo.rs)).
- **Probabilities:** they lie in Z[θ], θ = 2cos(2π/9), the root of x³ − 3x + 1 in
  (1.5, 1.875) ([`src/real3.rs`](src/real3.rs)).
- **Comparisons:** every comparison is an exact sign. θ is isolated by integer
  bisection and the value is checked at both ends with big integers
  ([`src/bigint.rs`](src/bigint.rs)). An undecided sign is counted as undecided;
  none occurred.

**The network.** Each qutrit in each layer gets diag(1, ζ^{3a+c}, ζ^{3a′+c′}), set by
four trits. This includes every version 1 phase, and the qutrit T gate
([`src/qutrit9.rs`](src/qutrit9.rs)).

**Seed sets.**
- STAR: Opus, Fable and Mythos.
- CLOUD: this seat's own calling written as trits, `data/cloud/`, with sha256
  `73844b0c…`.
- SHA: SHA-256 control streams.

### Verdicts

| ID | Prediction | Result |
|---|---|---|
| W1 | exact norm Σ\|v\|² = 3ᵏ | **PASS** |
| W2 | exact inverse | **PASS** |
| W3 | some readout probability is irrational | **FAIL**: the readout qutrit of every trained circle branch stays rational |
| W4 | **primary**: best branch test accuracy > 154/243 | **FAIL**: 154 for every branch in every set |
| W5 | virtual ≥ best single branch | **PASS** (154 ≥ 154) |
| W6 | **primary**: best Z₃ energy at r = 9 below 16, above the certified 15.378 | **FAIL**: best 33.578 |
| W7 | STAR, CLOUD and SHA within 50‰ on test | **PASS** (633‰ each) |
| W8 | every model, reloaded, reproduces its header | **PASS** (21 of 21) |
| W9 | an independent replay is byte-identical | **PASS** (23 files) |

### Z₃ energies (J_E = 1), best trained model per seed set

| r | v1 best | STAR | CLOUD | SHA | certified E₀ |
|---|---|---|---|---|---|
| 9 | 48 | 53.634 | **33.578** | 40.975 | ≥ 15.378 |
| 27 | 120 | 136.864 | **105.954** | 205.833 | ≥ 15.799 |
| 81 | 336 | 386.554 | **177.608** | 565.809 | ≥ 15.933 |

**What version 2 reached.**
- **Z₃ energy:** it beats version 1's Clifford energies at every coupling, best with
  the CLOUD seed. Every energy stays above the certified ground energy, as the
  variational principle requires.
- **Still short:** it does not reach the window below 16. Each seed set has one seed
  per coupling, so the CLOUD advantage is a single measurement, not a finding about
  seed sources.

**Why it stops** (post-hoc diagnostic, [`examples/v2_readout_diag.rs`](examples/v2_readout_diag.rs),
not a verdict).
- **The circle:** at the sealed depth of 3 layers, the readout qutrit is exactly
  uniform on every training point, so coordinate descent has nothing to climb.
  At 2 layers the same seed gives 162 positive margins out of 486, and an irrational
  readout on every qutrit.
- **Z₃:** the circuit begins with F on every link, so it cannot return to the flat
  orbit, the one state of energy 16.

These are inputs for a version 3, which needs its own pre-registration.

Reproduce:
```sh
cargo run --release -- v2 data/stars data/cloud results-ym-z3 out 3 2 4
cd out && sha256sum -c ../results-v2/SHA256SUMS
```
About 8 minutes on one core.

## 6. Version 3: an identity-reachable network

Version 3 ([`PREREG-V3.hbp`](PREREG-V3.hbp), sealed at `5a5cab5` before any v3 code)
acts on both findings of the version 2 diagnostic:
- **Circle:** the version 2 network and training, at 2 layers instead of 3.
- **Z₃:** on every link the layer applies F, then diag(1, ζ^e1, ζ^e2), then F†, then the
  SUM ring. With every trit at zero the layer is the identity, so the flat orbit
  (energy 16) is reachable. A fourth seed, IDENTITY, starts there.

The arithmetic is version 2's: Z[ζ₉] amplitudes and exact signs in Q(θ).
Seal: [`SEAL-V3.hbp`](SEAL-V3.hbp). Receipts: [`results-v3/`](results-v3/), 24 GGUF
models, `V3.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `809095a` rebuilt the
same binary (sha256 `a96f13ea…`) and reproduced all 27 files byte for byte.

| Claim | Result |
|---|---|
| T1 (primary): best circle branch test > 154 of 243 | **FAIL**, 154 |
| T2 (primary): best Z₃ energy at r = 9 in [15.378, 16) | **FAIL**, 16.000 exactly |
| X1, X2: exact norm and exact inverse | PASS |
| X3: an irrational readout on qutrit 0 | PASS |
| X4: T1 holds | FAIL |
| X5: virtual test ≥ best single, every set | PASS, 154 ≥ 154 |
| X6: IDENTITY starts at exactly 16 at every r | PASS |
| X7: T2 fails with best r = 9 energy exactly 16 | PASS |
| X8: all 24 models reload to their headers | PASS |
| X9: independent replay byte-identical | PASS |

Best Z₃ energy by seed:

| r | STAR | CLOUD | SHA | IDENTITY | v2 best | certified E₀ |
|---|---|---|---|---|---|---|
| 9 | 21.614 | 50.203 | 68.931 | **16.000** | 33.578 | ≥ 15.378 |
| 27 | 32.844 | 118.611 | 174.795 | **16.000** | 105.954 | ≥ 15.799 |
| 81 | 66.534 | 323.833 | 492.387 | **16.000** | 177.608 | ≥ 15.933 |

**What version 3 reached.**
- **Z₃:** the STAR seed (ACER-MYTHOS-BLUE) beats every version 2 energy at every
  coupling, 21.614 against 33.578 at r = 9. IDENTITY sits at exactly 16, the
  stabilizer value, and training changed none of its 64 trits: no single-trit move from
  the identity lowers the energy. Each trit turns a phase by a multiple of 2π/9, a large
  step next to the small amplitudes that separate the ground state from the flat orbit.
- **Circle:** the readout now carries irrational probabilities, but training changed at
  most one parameter per branch, and every branch tests at 154 or 133.

Reproduce:
```sh
cargo run --release -- v3 data/stars data/cloud results-ym-z3 out 2 2 4
cd out && sha256sum -c ../results-v3/SHA256SUMS
```

## 7. Version 4: real rational rotations

Version 4 ([`PREREG-V4.hbp`](PREREG-V4.hbp), sealed at `4e70af4` before any v4 code)
works on Z₃ only.
- **Amplitudes:** real integers of arbitrary size. The Hamiltonian is real symmetric, so a
  real ground state exists, and every energy is an exact rational.
- **Gate:** the rational rotation R_ij(b) on levels i, j of one link, with entries
  a² − b², ∓2ab and a² + b² on the third level, a = 729. So tan(angle/2) = b/729, and the
  rotation is orthogonal up to the scale a² + b².
- **Trits:** b = 27p₀ + 9p₁ + 3p₂ + p₃ from four balanced trits, b ∈ [−40, 40]. The
  smallest step is about 0.16°, against 40° in version 3.
- **Layer:** a SUM ring, then R₀₁(b), R₀₂(b′) on every link. 2 layers, 128 trits; all
  trits zero leaves |0…0⟩ unchanged.

Seal: [`SEAL-V4.hbp`](SEAL-V4.hbp). Receipts: [`results-v4/`](results-v4/), 12 GGUF
models, `V4.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `9e2c285` rebuilt the same
binary (sha256 `986a7c83…`) and reproduced all 15 files byte for byte. One run takes
about 3 minutes.

| Claim | Result |
|---|---|
| T2 (primary): best Z₃ energy at r = 9 in [15.378, 16) | **PASS**, 15.696 |
| Y1, Y2: exact norm and exact inverse | PASS |
| Y3: IDENTITY starts at exactly 16 at every r | PASS |
| Y4: T2 holds | PASS |
| Y5: trained IDENTITY below 16 at every r | PASS |
| Y6: every energy ≥ the certified E₀ | PASS |
| Y7: best r = 9 energy ≤ 15.689, half the gap | **FAIL**, 15.696 |
| Y8: the best r = 9 energy comes from IDENTITY | PASS |
| Y9: all 12 models reload to their headers | PASS |
| Y10: independent replay byte-identical | PASS |

Best Z₃ energy by seed (milli floors):

| r | STAR | CLOUD | SHA | IDENTITY | v3 best | certified E₀ | gap closed |
|---|---|---|---|---|---|---|---|
| 9 | 15.975 | 15.854 | 15.865 | **15.696** | 16.000 | 15.378 | 48.8% |
| 27 | 18.155 | 16.089 | 16.099 | **15.901** | 16.000 | 15.799 | 49.2% |
| 81 | 20.573 | 16.697 | 17.352 | **15.970** | 16.000 | 15.933 | 44.7% |

**What version 4 reached.**
- **Below the stabilizer value.** For the first time the qutrit network goes below 16, at
  every coupling. Every energy stays above the certified ground energy.
- **The IDENTITY model:** it closes just under half the gap to E₀ at every coupling.
  Training left the first layer at zero and set every link of the second layer to one
  shared tilt: b = b′ = 7 at r = 9, 2 at r = 27 and 1 at r = 81. The tilt shrinks with
  the coupling, as the magnetic term grows.
- **Y7 missed by 7 thousandths.** The state is a gauge-projected product of identical link
  states, and the remaining half of the gap is left for correlations between links.

Reproduce:
```sh
cargo run --release -- v4 data/stars data/cloud results-ym-z3 out 2 4
cd out && sha256sum -c ../results-v4/SHA256SUMS
```

## 8. Version 5: coherence between holonomy sectors

Version 5 ([`PREREG-V5.hbp`](PREREG-V5.hbp), sealed at `86a8725` before any v5 code)
starts from a post-hoc diagnostic of the sealed v4 code,
[`examples/v4_diag.rs`](examples/v4_diag.rs), with its output in
[`examples/v4_diag.out`](examples/v4_diag.out):
- **v4's ceiling:** v4's 15.696 is the best uniform product state, and it equals the
  second-order estimate inside the one holonomy sector that |0…0⟩ reaches.
- **The missing half:** summing the nine flux-free holonomy configurations and dressing
  each one reaches 15.381 at r = 9, 15.800 at r = 27 and 15.933 at r = 81. So the rest
  of the gap is coherence between holonomy sectors.

The v5 network:
- **Angles:** the v4 rotations, with six trits per angle: b = 243p₀ + … + p₅, b ∈ [−364, 364].
- **Partner SUMs:** after the rotations come SUMs 0→4, 2→6, 1→3 and 5→7, pairing the two
  links of a column or row. Equal values on such a pair carry no flux and shift a holonomy,
  so a wide rotation on one link and its SUM spread the state across holonomy sectors.
- **Size:** one layer, 96 trits.

Seal: [`SEAL-V5.hbp`](SEAL-V5.hbp). Receipts: [`results-v5/`](results-v5/), 15 GGUF
models, `V5.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `2ee26d6` rebuilt the same
binary (sha256 `1a4be9fa…`) and reproduced all 18 files byte for byte. One run takes
about 100 seconds.

| Claim | Result |
|---|---|
| T3 (primary): best Z₃ energy at r = 9 in [15.378, 15.420] | **PASS**, 15.384 |
| Z1, Z2: exact norm and exact inverse | PASS |
| Z3: IDENTITY starts at exactly 16 | PASS |
| Z4: WARM starts at the v4 product values | **FAIL**, 15.824, 15.949, 15.984 |
| Z5: T3 holds | PASS |
| Z6: best r = 27 ≤ 15.820 and best r = 81 ≤ 15.945 | PASS, 15.802 and 15.941 |
| Z7: every energy ≥ the certified E₀ | PASS |
| Z8: trained IDENTITY at r = 9 below 15.696 | PASS, 15.384 |
| Z9: the best r = 9 energy comes from WARM | **FAIL**: IDENTITY, by an exact margin below the milli digit |
| Z10: all 15 models reload to their headers | PASS |
| Z11: independent replay byte-identical | PASS |

Best Z₃ energy by seed (milli floors):

| r | STAR | CLOUD | SHA | IDENTITY | WARM | v4 best | certified E₀ | gap closed |
|---|---|---|---|---|---|---|---|---|
| 9 | 81.308 | 20.176 | 15.385 | **15.384** | 15.384 | 15.696 | 15.378 | 99.0% |
| 27 | 211.297 | 33.249 | 15.803 | **15.802** | 15.802 | 15.901 | 15.799 | 98.5% |
| 81 | 601.263 | 21.641 | 16.540 | **15.941** | 15.941 | 15.970 | 15.933 | 88.0% |

**What version 5 reached.**
- **Within 6 thousandths of the ground energy.** At r = 9 the trained network is at 15.384
  against the certified E₀ in [15.378, 15.379), closing 99% of the gap from the stabilizer
  value 16, and 98.5% at r = 27. Every energy stays above the certified E₀.
- **Three seeds agree.** IDENTITY, WARM and SHA reach the same energies to within one
  thousandth from different starts.
- **Z4 failed** because the partner SUMs copy the control link's dressing onto its partner,
  so the WARM start is not the v4 product state.
- **The STAR seed stalls.** Its six-trit angles start far from the flat orbit, and single-trit
  moves change only 9 of its 96 trits.
- **r = 81 closes less, 88%.** There the best product dressing in v4 was already the
  smallest step, b = 1, so the angle grid is the likely limit; v5 does not test this.

Reproduce:
```sh
cargo run --release -- v5 data/stars data/cloud results-ym-z3 out 1 8
cd out && sha256sum -c ../results-v5/SHA256SUMS
```

## 9. Version 6: a finer angle grid

Version 6 ([`PREREG-V6.hbp`](PREREG-V6.hbp), sealed at `a477e39` before any v6 code)
tests whether the angle grid is what held r = 81 at 88% in version 5.
- **Network:** the v5 network unchanged.
- **Grid:** a = 6561 instead of 729, with eight trits per angle,
  b = 2187p₀ + … + p₇ ∈ [−3280, 3280]. The smallest step is 9× finer.
- **WARM seed:** starts from the sealed v5 IDENTITY models with every b multiplied by 9.
  That is the same rotation, and the run checks that the start energy equals the v5 energy
  exactly.

Seal: [`SEAL-V6.hbp`](SEAL-V6.hbp). Receipts: [`results-v6/`](results-v6/), 15 GGUF
models, `V6.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `65a4ba7` rebuilt the same
binary (sha256 `244fee81…`) and reproduced all 18 files byte for byte. One run takes
about 150 seconds. After the shared rotation code was generalised, the v5 run was
repeated and still matched `results-v5/SHA256SUMS`.

| Claim | Result |
|---|---|
| T4 (primary): best Z₃ energy at r = 81 in [15.933, 15.937] | **PASS**, 15.933 |
| V1, V2: exact norm and exact inverse | PASS |
| V3: IDENTITY starts at exactly 16 | PASS |
| V4: WARM starts at exactly the v5 energy | PASS |
| V5: T4 holds | PASS |
| V6: best r = 9 ≤ 15.384 and best r = 27 ≤ 15.802 | PASS, 15.382 and 15.800 |
| V7: every energy ≥ the certified E₀ | PASS |
| V8: the STAR seed stays above 16 | PASS |
| V9: all 15 models reload to their headers | PASS |
| V10: independent replay byte-identical | PASS |

Best Z₃ energy by seed (milli floors):

| r | STAR | CLOUD | SHA | IDENTITY | WARM | v5 best | certified E₀ | gap closed |
|---|---|---|---|---|---|---|---|---|
| 9 | 81.269 | 60.068 | 60.049 | **15.382** | 15.382 | 15.384 | [15.378, 15.379) | 99.3% |
| 27 | 211.189 | 151.022 | 150.419 | **15.800** | 15.800 | 15.802 | [15.799, 15.800) | 99.5% |
| 81 | 600.949 | 421.971 | 419.983 | **15.933** | 15.933 | 15.941 | [15.933, 15.934) | same milli as E₀ |

**What version 6 reached.**
- **The grid was the limit at r = 81.** On the finer grid, r = 81 lands in [15.933, 15.934),
  the same thousandth as the certified ground energy, against 15.941 in version 5.
- **The other couplings:** r = 27 is one thousandth above E₀ and r = 9 four thousandths.
- **Every energy** stays above the certified E₀.
- **IDENTITY and WARM** reach the same energies at every coupling.
- **The random and star seeds stall.** The SHA, CLOUD and STAR seeds start far out on the
  eight-trit grid and stay above 16.

Reproduce:
```sh
cargo run --release -- v6 data/stars data/cloud results-ym-z3 results-v5 out 1 8
cd out && sha256sum -c ../results-v6/SHA256SUMS
```

## 10. Version 7: a correlated second layer and the pixel backend

Version 7 ([`PREREG-V7.hbp`](PREREG-V7.hbp), sealed at `9527555` before any v7 code was
compiled or run) keeps the v6 layer and adds a second one.
- **Layer 2:** a SUM ring, R₀₁(b) and R₀₂(b′) on every link, then the inverse ring. A
  rotation in the ring frame acts on sums of neighbouring link values, so it correlates
  links. With its trits at zero it is exactly the identity. 256 trits in all.
- **Seeds:** IDENTITY; WARM, the sealed v6 IDENTITY models with layer 2 at zero (checked
  equal to the v6 energy as a fraction); and STAR.
- **The pixel backend.** The 6,561 link configurations are an 81 × 81 framebuffer
  (x = links 0–3, y = links 4–7) with 64 u32 channels, one per prime below 2³¹. Every gate
  is a per-pixel gather, a pixel reading its own taps and writing only itself, and the
  gauge projection is an 81-tap gather. The energy leaves the framebuffer as residues and
  Garner's method lifts it back to exact integers, which must equal the big-integer energy
  digit for digit. This workspace has no GPU, so the passes run on the CPU, written the way
  a fragment shader runs them.
- **Frames:** [`results-v7/frames/`](results-v7/frames/) holds a PNG of the exact state
  after every pass of the best r = 9 model (40 passes, red positive, blue negative,
  brightness by bit length), and the final and gauge-projected states at every coupling.

Seal: [`SEAL-V7.hbp`](SEAL-V7.hbp). Receipts: [`results-v7/`](results-v7/), 9 GGUF models,
44 PNG frames, `V7.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `43a71e6` rebuilt the
same binary (sha256 `cb886835…`) and reproduced all 56 files byte for byte, every frame
included. One run takes about 12 minutes. The first code commit, `0677593`, compiled a
generic circuit into the binary crate, which embedded the build path and made the two builds
differ. `43a71e6` compiles the circuit once in the library; nothing ran before it.

| Claim | Result |
|---|---|
| T5 (primary): best Z₃ energy at r = 9 in [15.378, 15.381] | **PASS**, 15.381 |
| U1, U2: exact norm and exact inverse | PASS |
| U3: IDENTITY starts at exactly 16 | PASS |
| U4: WARM starts at exactly the v6 energy | PASS |
| U5: T5 holds | PASS |
| U6: best r = 27 ≤ 15.800 and best r = 81 ≤ 15.933 | PASS, 15.799 and 15.933 |
| U7: every energy ≥ the certified E₀ | PASS |
| U8: the pixel backend equals the exact energy | PASS, 9 of 9 models |
| U9: STAR stays above 16 | PASS |
| U10: all 9 models reload to their headers | PASS |
| U11: independent replay byte-identical, frames included | PASS |

| r | v7 best | v6 best | Certified E₀ |
|---|---|---|---|
| 9 | **15.381** | 15.382 | [15.378, 15.379) |
| 27 | **15.799** | 15.800 | [15.799, 15.800), the same thousandth |
| 81 | **15.933** | 15.933 | [15.933, 15.934), the same thousandth |

**What version 7 reached.**
- **Correlations help.** At r = 9 the trained IDENTITY model uses one correlated rotation
  in layer 2, on link 1 with b = 12, 13, and reaches 15.381, three thousandths above E₀. At
  r = 27 it uses b = 1, 1 and lands in the same thousandth as E₀. At r = 81 layer 2 stays
  off.
- **Joint training, not a warm start.** WARM did not move: no single trit of layer 2,
  starting from zero, lowers the v6 optimum. The gain came only when both layers were
  trained together from IDENTITY.
- **The ground state is positive.** The gauge-projected r = 9 state is positive on all
  6,561 configurations, as the Perron–Frobenius theorem requires for this Hamiltonian.

Reproduce:
```sh
cargo run --release -- v7 data/stars results-ym-z3 results-v6 out 6
cd out && sha256sum -c ../results-v7/SHA256SUMS
```

## 11. Version 8: the 3×2 torus

Version 8 ([`PREREG-V8.hbp`](PREREG-V8.hbp), sealed at `d4f782b` before any v8 code) moves to the
largest Z₃ torus this machine holds as an exact big-integer state: 3×2. That is 12 links,
531,441 amplitudes and 2,187 gauge orbits of 243 configurations each. At about 15 qutrits the
8.4 GB of RAM runs out for exact states.

- **Certification.** E₀ is certified by HEB-C's sturmfast, the same pinned binary as the 2×2
  certificate. [`ADDENDUM-V8.hbp`](ADDENDUM-V8.hbp), written before any v8 energy, moves the
  certificate to the translation-invariant sector (390 classes). One count on the full orbit
  matrix had taken 10 minutes; a sector count takes 5 seconds.
  - Two checks back the sector move. Every off-diagonal entry of H is ≤ 0 and the orbit graph is
    connected (C2c), so the ground state is unique, positive and therefore translation-invariant.
  - The same construction on the 2×2 torus returns the sealed E₀ (C2b).
- **Network.** v7's two layers, with SUMs along the flux-free cuts of the 3×2 torus. Each x-cut
  is the two x-links of a column. Each y-cut is the three y-links of a row. 384 trits.
- **Training.** Candidates are ranked by integer fixed-point energies at scale 2³⁶. Every
  reported energy is exact. The fixed-point estimate matched the exact thousandth at every
  coupling (C8).

Seal: [`SEAL-V8.hbp`](SEAL-V8.hbp). Receipts: [`results-v8/`](results-v8/), 3 GGUF models, both
sector matrices, `V8.hbp`, `INDEX.hbi`, `SHA256SUMS`. A fresh clone at `ad0c8ea` rebuilt the same
binary (sha256 `22d180d5…`) and reproduced all 9 files byte for byte. One run takes about 28 minutes.

| Claim | Result |
|---|---|
| T6 (primary): r = 9 within 0.020 of the certified E₀ | **FAIL**, 0.081 above |
| C1: 2,187 orbits of size 243 | PASS |
| C2, C2b, C2c: certificate complete; 2×2 control; Perron–Frobenius conditions | PASS |
| C3: IDENTITY starts at exactly 24 | PASS |
| C4: T6 holds | FAIL |
| C5: r = 27 and r = 81 within 0.010 | **FAIL**, 0.024 and 0.007 |
| C6: every energy ≥ the certified E₀ | PASS |
| C7: exact norm and exact inverse | PASS |
| C8: fixed point within one thousandth of exact | PASS |
| C9: all 3 models reload to their headers | PASS |
| C10: independent replay byte-identical | PASS |

| r | Certified E₀ | v8 network | Above E₀ | Gap from 24 closed |
|---|---|---|---|---|
| 9 | [23.298, 23.299) | 23.380 | 0.081 | 88.3% |
| 27 | [23.774, 23.775) | 23.799 | 0.024 | 88.9% |
| 81 | [23.925, 23.926) | 23.933 | 0.007 | 89.3% |

**What version 8 reached.**
- **The gap fraction is steady.** The network closes 88–89% of the gap from the flat value at
  every coupling. On the 2×2 torus v7 closed over 99%.
- **Training may be short.** Every run used all four sweeps.
- **Layer 2 is mostly idle.** It switched on only at r = 9.
- **Holonomy is spread.** The trained layer 1 spreads every cut's control link (b = 2065, 2722
  and similar), so the holonomy superposition is present.

The post-hoc diagnostic [`examples/v8_diag.rs`](examples/v8_diag.rs) tests three explanations on
the sealed models before version 9 is pre-registered: training budget, holonomy, and the geometry
of the correlations.

Reproduce:
```sh
cargo run --release -- v8 PATH/TO/sturmfast out 4
cd out && sha256sum -c ../results-v8/SHA256SUMS
```

## 12. Version 9: correlations in the plaquette's flux frame

Version 9 ([`PREREG-V9.hbp`](PREREG-V9.hbp), sealed at `40851b0` before any v9 code) is built on
the post-hoc diagnostic of the sealed v8 models. The diagnostic is
[`examples/v8_diag.rs`](examples/v8_diag.rs); its output is
[`examples/v8_diag.out`](examples/v8_diag.out). For r = 9 it found:
- **Training budget:** not the limit. Resuming v8 to 16 sweeps moved nothing.
- **Holonomy:** nine coherent sectors with a shift-covariant dressing reach 23.300, so the
  target state is known.
- **Correlation geometry:** the missing piece. With v8's layer 1 kept, a ring layer 2 never moved.
  A plaquette-local layer 2 reached 23.302 and cut the residual ‖(H − E)φ‖/‖φ‖ from 2.07 to 0.49.

**The network.** v8's layer 1 is kept, and layer 2 works one plaquette at a time.
- **Frame.** For each plaquette (a, b, c, d), three SUMs (a→b, b→c inverted, c→d) make link d
  hold minus the plaquette's flux.
- **Rotation.** R₀₁ and R₀₂ act on c and d.
- **Undo.** The three SUMs are undone.

With its trits at zero the layer is the identity, and the inverse is exact. Seeds: IDENTITY, and
WARM (the sealed v8 models with layer 2 at zero). E₀ is read from the sealed `V8.hbp`.

Seal: [`SEAL-V9.hbp`](SEAL-V9.hbp). Receipts: [`results-v9/`](results-v9/): 6 GGUF models,
`V9.hbp`, `INDEX.hbi` and `SHA256SUMS`. A fresh clone at `f3a9a0f` rebuilt the same binary
(sha256 `aa7a1176…`) and reproduced all 9 files byte for byte. One run takes about 75 minutes.

| Claim | Result |
|---|---|
| T7 (primary): r = 9 below 23.305 | **PASS**, 23.301 |
| P1: exact norm and exact inverse | PASS |
| P2: WARM starts at exactly the v8 energy | **FAIL**: the sealed v8 r = 9 model had its ring layer 2 on, and WARM sets layer 2 to zero |
| P3: T7 holds | PASS |
| P4: r = 27 below 23.780 and r = 81 below 23.931 | PASS, 23.774 and 23.925 |
| P5: every energy ≥ the certified E₀ | PASS |
| P6: WARM at r = 9 reaches 23.302 | PASS |
| P7: the plaquette layer is on in every best model | PASS |
| P8: r = 9 residual below v8's 2.071 | PASS, 0.413 |
| P9: fixed point within one thousandth of exact | PASS |
| P10: all 6 models reload to their headers | PASS |
| P11: independent replay byte-identical | PASS |

| r | Certified E₀ (3×2 torus) | v9 | v8 | Residual ‖(H − E)φ‖/‖φ‖ |
|---|---|---|---|---|
| 9 | [23.298, 23.299) | **23.301** | 23.380 | 0.413 |
| 27 | [23.774, 23.775) | **23.774**, the same thousandth | 23.799 | 0.198 |
| 81 | [23.925, 23.926) | **23.925**, the same thousandth | 23.933 | 0.233 |

**What version 9 reached.** On the 3×2 torus, the largest lattice this machine holds exactly:
- **r = 27 and r = 81:** the network lands in the same thousandth as the certified ground energy.
- **r = 9:** it is two thousandths above.
- **Both seeds agree.** IDENTITY and WARM reach the same values.

The change that did it was the geometry of the correlations: rotations in each plaquette's flux
frame. More training did not help, and more parameters were not needed.

Reproduce:
```sh
cargo run --release -- v9 results-v8 out 4
cd out && sha256sum -c ../results-v9/SHA256SUMS
```

## 13. Version 10: the 3×3 torus in the gauge-fixed basis

Version 10 ([`PREREG-V10.hbp`](PREREG-V10.hbp), sealed at `77d0f79` before any v10 code) has two
addenda written before its run. [`ADDENDUM-V10.hbp`](ADDENDUM-V10.hbp) records the operator's five
requirements and the evidence rule: sturmfast is the only certificate, and floating-point spectra are
cross-checks. [`ADDENDUM-V10b.hbp`](ADDENDUM-V10b.hbp) adds the exact checks QA and QB, with a
fallback.

- **Basis.** The comb spanning tree is gauge-fixed to zero, leaving the 10 free links of the 3×3 torus.
  That is 3¹⁰ = 59,049 states, and every one is gauge invariant, so no amplitude is unphysical.
- **Certificate.** E₀ is certified on the zero-winding, zero-momentum block. Its classes are free
  configurations under the two cut shifts and the translations: 753 of them on 3×3. The block carries
  the ground state because of two checks, each run in exact integers on the 2×2, 3×2 and 3×3 tori:
  - QA: the symmetries commute with H, entry by entry.
  - QB: every off-diagonal entry is ≤ 0, and the move graph reaches all states.
- **Controls.** The same construction returns the sealed 2×2 E₀ and the sealed v8 3×2 intervals.
  Mapped into this basis, the sealed v9 model reproduces its 23.301 exactly.
- **Network.** Rotations on every free link, then a plaquette-flux layer built from the free links of
  each plaquette. 304 trits.

Seal: [`SEAL-V10.hbp`](SEAL-V10.hbp). Receipts: [`results-v10/`](results-v10/): 3 GGUF models, the three
block matrices, `V10.hbp`, `INDEX.hbi` and `SHA256SUMS`. A fresh clone at `af737e0` rebuilt the same
binary (sha256 `278d1cb3…`) and reproduced all 9 files byte for byte. sturmfast made 117 counts, every
one complete and unambiguous. One run takes about 38 minutes.

| Claim | Result |
|---|---|
| T8 (primary): r = 9 within 0.010 of the certified 3×3 E₀ | **FAIL**, 0.333 above |
| QA, QB: exact commutation; Perron–Frobenius conditions (2×2, 3×2, 3×3) | PASS |
| Q1: the 3×3 block has 753 classes | PASS |
| Q2, Q3: the 2×2 and 3×2 controls return the sealed intervals | PASS |
| Q4: sturmfast complete and unambiguous | PASS |
| Q5: the sealed v9 energy, reproduced in the gauge-fixed basis | PASS |
| Q6: IDENTITY starts at exactly 36 | PASS |
| Q7: T8 holds | FAIL |
| Q8: r = 27 and r = 81 within 0.005 | **FAIL**, 0.101 and 0.032 |
| Q9: every energy ≥ the certified E₀ | PASS |
| Q10: exact norm and exact inverse | PASS |
| Q11: all 3 models reload to their headers | PASS |
| Q12: independent replay byte-identical | PASS |

| r | Certified E₀ (3×3 torus) | v10 network | Gap from 36 closed |
|---|---|---|---|
| 9 | [35.288, 35.289) | 35.622 | 53% |
| 27 | [35.773, 35.774) | 35.875 | 55% |
| 81 | [35.925, 35.926) | 35.958 | 56% |

**What version 10 reached.**
- **The certificate.** The 3×3 ground energy is certified at three couplings, every symmetry is checked
  in exact integers, and the controls hold.
- **The network.** It closes only about half of the gap, and training stops after 2 sweeps at a local
  minimum.
- **The working hypothesis.** In the gauge-fixed basis, moving a tree link shifts several free links at
  once. A rotation of a single free link therefore cannot dress a tree link. The post-hoc test is
  [`examples/v10_diag.rs`](examples/v10_diag.rs): it dresses each tree link in its own frame on top of
  the sealed model.
- **The test confirms it.** In [`examples/v10_diag.out`](examples/v10_diag.out), a tree-frame layer
  trained for one sweep on top of the sealed r = 9 model lowers the energy from 35.622 to 35.321. That
  closes 90% of the remaining distance to E₀ ([35.288, 35.289)). This is the input for a version 11.

Reproduce:
```sh
cargo run --release -- v10 PATH/TO/sturmfast results-v9 out 4
cd out && sha256sum -c ../results-v10/SHA256SUMS
```

## 14. Version 11: tree links dressed in their own frames

Version 11 ([`PREREG-V11.hbp`](PREREG-V11.hbp), sealed at `514f4c3` before any v11 code) adds the layer
the v10 diagnostic pointed to. A tree link's electric move shifts a fixed vector of free links,
δₜ = fix(eₜ). For each of the 8 tree links the new layer does three things:
- SUMs map δₜ onto a single free qutrit;
- R₀₁ and R₀₂ rotate that qutrit;
- the SUMs are undone.

That gives 432 trits. The layer is the identity at zero, and its inverse is exact. E₀ is reused from the
sealed `V10.hbp`. The seeds are IDENTITY and WARM (the sealed v10 models).

Seal: [`SEAL-V11.hbp`](SEAL-V11.hbp). Receipts: [`results-v11/`](results-v11/), 6 GGUF models, `V11.hbp`,
`INDEX.hbi`, `SHA256SUMS`. A fresh clone at `9859c6b` rebuilt the same binary (sha256 `d0bc135f…`) and
reproduced all 9 files byte for byte. One run takes about 7 minutes.

| Claim | Result |
|---|---|
| T9 (primary): r = 9 below 35.309 | **FAIL**, 35.321 |
| R1: exact norm and exact inverse | PASS |
| R2: WARM starts at exactly the v10 energy | PASS |
| R3: T9 holds | FAIL |
| R4: r = 27 and r = 81 within 0.010 | PASS, 0.002 and the same thousandth |
| R5: every energy ≥ the certified E₀ | PASS |
| R6: WARM at r = 9 reaches 35.321 | PASS |
| R7: the tree layer is on in every best model | PASS |
| R8: fixed point within one thousandth of exact | PASS |
| R9: all 6 models reload to their headers | PASS |
| R10: independent replay byte-identical | PASS |

| r | Certified E₀ (3×3 torus) | v11 | v10 |
|---|---|---|---|
| 9 | [35.288, 35.289) | 35.321 | 35.622 |
| 27 | [35.773, 35.774) | **35.776** | 35.875 |
| 81 | [35.925, 35.926) | **35.925**, the same thousandth | 35.958 |

**What version 11 reached.**
- **The two larger couplings.** On the 3×3 torus the network lands in the same thousandth as the
  certified ground energy at r = 81, and two thousandths above it at r = 27.
- **r = 9.** It is 32 thousandths above, and both seeds stop at the same energy, so this is a limit of
  the ansatz rather than of training.
- **Candidate for what is missing.** The zero-winding ground state is a uniform superposition over the
  cut shifts. That is the 3×3 counterpart of the holonomy coherence that version 5 added on the 2×2 torus.

Reproduce:
```sh
cargo run --release -- v11 results-v10 out 4
cd out && sha256sum -c ../results-v11/SHA256SUMS
```

## 15. Reproduce

```sh
cargo clippy --release --all-targets -- -D warnings
cargo test --release
cargo run --release -- train data/stars out 3 4
cd out && sha256sum -c ../results/SHA256SUMS && cd ..
cargo run --release -- verify results
cargo run --release -- infer results/star-virtual.gguf 13 13
```

Training takes about a minute.

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) installs Rust 1.81.0
and then:
- enforces no float, JSON or Node;
- runs clippy and the tests;
- checks the star inputs;
- retrains and checks every model and receipt against `results/SHA256SUMS`;
- reloads every committed GGUF model.

| Path | Contents |
|---|---|
| `PREREG.hbp` | the sealed predictions |
| `data/stars/` | the three seed GGUFs and their sha256 |
| `src/` | simulator, network, task, training, virtual QNN, GGUF model writer and reader, SHA-256, HBP |
| `tests/exact.rs` | ω³ = 1, F⁴ = I, exact norm, exact inverse, the stabilizer property, the GGUF round trip |
| `results-v11/`, `SEAL-V11.hbp`, `PREREG-V11.hbp`, `examples/v10_diag.*` | version 11: 6 GGUF models, `V11.hbp`, index, checksums; seal; predictions; the v10 diagnostic that shaped it |
| `results-v10/`, `SEAL-V10.hbp`, `PREREG-V10.hbp`, `ADDENDUM-V10*.hbp` | version 10: the 3×3 torus, 3 GGUF models, block matrices, `V10.hbp`, index, checksums; seal; predictions; addenda |
| `results-v9/`, `SEAL-V9.hbp`, `PREREG-V9.hbp`, `examples/v8_diag.*` | version 9: 6 GGUF models, `V9.hbp`, index, checksums; seal; predictions; the v8 diagnostic that shaped it |
| `results-v8/`, `SEAL-V8.hbp`, `PREREG-V8.hbp`, `ADDENDUM-V8.hbp` | version 8: the 3×2 torus, 3 GGUF models, sector matrices, `V8.hbp`, index, checksums; seal; predictions; addendum |
| `results-v7/`, `SEAL-V7.hbp`, `PREREG-V7.hbp` | version 7: 9 GGUF models, 44 PNG frames, `V7.hbp`, index, checksums; seal; predictions |
| `results-v6/`, `SEAL-V6.hbp`, `PREREG-V6.hbp` | version 6: 15 GGUF models, `V6.hbp`, index, checksums; seal; predictions |
| `results-v5/`, `SEAL-V5.hbp`, `PREREG-V5.hbp`, `examples/v4_diag.*` | version 5: 15 GGUF models, `V5.hbp`, index, checksums; seal; predictions; the v4 diagnostic that shaped it |
| `results-v4/`, `SEAL-V4.hbp`, `PREREG-V4.hbp` | version 4: 12 GGUF models, `V4.hbp`, index, checksums; seal; predictions |
| `results-v3/`, `SEAL-V3.hbp`, `PREREG-V3.hbp` | version 3: 24 GGUF models, `V3.hbp`, index, checksums; seal; predictions |
| `results-v2/`, `SEAL-V2.hbp`, `PREREG-V2.hbp`, `data/cloud/`, `examples/` | version 2: 21 GGUF models, `V2.hbp`, index, checksums; seal; this seat's calling and its trits; the post-hoc diagnostic |
| `results-ym-z3/`, `SEAL-YM-Z3.hbp` | the Z₃ Yang–Mills receipts: the matrix, 6 trained GGUF models, `YM-Z3.hbp`, index, checksums; the seal with provenance, replay and erratum |
| `results/` | 8 trained GGUF models (6 branches, 2 virtual), `RESULT.hbp`, `INDEX.hbi`, `SHA256SUMS` |

Operator: Jesse Daniel Brown.
