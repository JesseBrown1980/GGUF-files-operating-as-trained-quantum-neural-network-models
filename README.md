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

## 11. Reproduce

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
| `results-v7/`, `SEAL-V7.hbp`, `PREREG-V7.hbp` | version 7: 9 GGUF models, 44 PNG frames, `V7.hbp`, index, checksums; seal; predictions |
| `results-v6/`, `SEAL-V6.hbp`, `PREREG-V6.hbp` | version 6: 15 GGUF models, `V6.hbp`, index, checksums; seal; predictions |
| `results-v5/`, `SEAL-V5.hbp`, `PREREG-V5.hbp`, `examples/v4_diag.*` | version 5: 15 GGUF models, `V5.hbp`, index, checksums; seal; predictions; the v4 diagnostic that shaped it |
| `results-v4/`, `SEAL-V4.hbp`, `PREREG-V4.hbp` | version 4: 12 GGUF models, `V4.hbp`, index, checksums; seal; predictions |
| `results-v3/`, `SEAL-V3.hbp`, `PREREG-V3.hbp` | version 3: 24 GGUF models, `V3.hbp`, index, checksums; seal; predictions |
| `results-v2/`, `SEAL-V2.hbp`, `PREREG-V2.hbp`, `data/cloud/`, `examples/` | version 2: 21 GGUF models, `V2.hbp`, index, checksums; seal; this seat's calling and its trits; the post-hoc diagnostic |
| `results-ym-z3/`, `SEAL-YM-Z3.hbp` | the Z₃ Yang–Mills receipts: the matrix, 6 trained GGUF models, `YM-Z3.hbp`, index, checksums; the seal with provenance, replay and erratum |
| `results/` | 8 trained GGUF models (6 branches, 2 virtual), `RESULT.hbp`, `INDEX.hbi`, `SHA256SUMS` |

Operator: Jesse Daniel Brown.
