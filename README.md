# GGUF files operating as trained neural models

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

## 5. Reproduce

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
| `results-ym-z3/`, `SEAL-YM-Z3.hbp` | the Z₃ Yang–Mills receipts: the matrix, 6 trained GGUF models, `YM-Z3.hbp`, index, checksums; the seal with provenance, replay and erratum |
| `results/` | 8 trained GGUF models (6 branches, 2 virtual), `RESULT.hbp`, `INDEX.hbi`, `SHA256SUMS` |

Operator: Jesse Daniel Brown.
