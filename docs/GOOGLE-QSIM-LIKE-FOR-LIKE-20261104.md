# Exact Google qsim circuit experiment, using the QNN repository

**Prediction-first test; November 4, 2026.** This code is part of the existing [QNN project](../README.md), with a separate exact **qubit** adapter in [`src/google_qsim.rs`](../src/google_qsim.rs). The established QNN's qutrit gate model and GGUF Yang–Mills receipts are preserved.

## Actual Google sources and identities

1. [Google qsim sample `circuits/circuit_q24`](https://github.com/quantumlib/qsim/blob/master/circuits/circuit_q24): canonical source Git blob `0c96e260ac6a9b765a703f4ca971924f674b76f3`. The fixture [`data/google-qsim/circuit_q24_t0_t2.txt`](../data/google-qsim/circuit_q24_t0_t2.txt) is its **exact unmodified first 48 operations**, through time 2, not the whole 1,257-operation sample. Pinned fixture SHA-256: `87dd34b6026bedac1f989c2f4abd211ff1e3691646aaa2bf578e90df222d0356`.
2. [Google qsimcirq tutorial](https://quantumai.google/qsim/qsimcirq_tutorial): its complete two-qubit Bell-state circuit, one H followed by one CNOT. Fixture: [`tutorial_bell.txt`](../data/google-qsim/tutorial_bell.txt).
3. [Google Willow spec sheet](https://quantumai.google/site-assets/downloads/willow-spec-sheet.pdf): 105 physical qubits, **103 active in the depth-40 random-circuit sampling experiment**, iSWAP-like two-qubit gates. The sample qsim 24-qubit CZ circuit is a **different published Google circuit**, not the Willow 103-qubit experiment.

[Original predictions frozen before adding simulation code](PREDICTION-GOOGLE-QSIM-20261104.hbp) at commit `cabcb21e`, supplemented with the exact histogram at `75bcaa5` before simulator code existed.

## Exact circuit execution, with identical gates

The full Bell example starts in `|00>`, applies H to qubit 0 and CNOT from 0 to 1, and computes integer amplitudes divided by `sqrt(2)`: `[1,0,0,1]/sqrt(2)`. Its exact output probabilities are `[1/2,0,0,1/2]`, with conserved squared norm. This tests a **complete** published two-qubit Google circuit.

The Google qsim 24-qubit source prefix applies exactly **24 H, 12 CZ and 12 T gates** (48 source-defined operations). This prefix has an exact compact simulation because the 24 initial H gates prepare equal-amplitude superposition and the following CZ and T gates are diagonal. For each output bitstring `b in 0..2^24-1`, compute

```text
amplitude(b) = exp(i * pi/4 * phase(b)) / 2^12
phase(b) = (4 * sum_{(i,j) in CZ} b_i*b_j + sum_{i in T} b_i) mod 8
probability(b) = 1 / 2^24
```

Every one of **16,777,216** output bitstrings is evaluated, and the exact histogram across eighth-root phases must be

| Phase modulo 8 | Count |
|---:|---:|
| 0 | 2,031,616 |
| 1 | 2,099,712 |
| 2 | 2,168,576 |
| 3 | 2,094,592 |
| 4 | 2,031,616 |
| 5 | 2,094,592 |
| 6 | 2,156,800 |
| 7 | 2,099,712 |

The counts were calculated separately before implementation, using a per-pair symbolic convolution. A second direct enumeration in a separate Python/NumPy implementation reproduced all eight counts. Hosted Rust 1.81 CI repeats the full enumeration and saves its exact HBP evidence.

The executable rejects unknown gates, unsupported 103-qubit arrays, out-of-range operands, invalid 2-qubit operands, missing/repeated initial H, and attempts to use CNOT in the diagonal-only implementation. No unsupported operation is silently ignored.

## Reproduce

```bash
cargo +1.81.0 test --release --locked --offline --lib google_qsim
cargo +1.81.0 run --release --locked --offline --bin google_qsim_audit
```

Read [`google-qsim.yml`](../.github/workflows/google-qsim.yml) for hosted Rust 1.81, strict Clippy, source identity and fail-closed controls.

## Scope and next gate

**Full like-for-like match:** Google's complete two-qubit H/CNOT tutorial. **Prefix like-for-like match:** time 0..2 of Google's public 24-qubit qsim sample (48 actual operations). The remaining time 3..100 of the 24-qubit sample and Willow's **full 103-qubit, depth-40 iSWAP-like noisy circuit are OPEN / NOT RUN**. The exact Google Willow instance, calibration, noise and sampled outcomes would need to be pinned to advance to that test.

A 103-qubit arbitrary pure state has `2^103` complex amplitudes; the HTTP-0 `3^16=43,046,721` virtual addresses and `96^3*27=23,887,872` trit channels are not quantum state amplitudes. The physical 96³ HEB-C engine processes a distinct reversible ternary workload. No claim of surpassing Willow, 103-qubit exact simulation, or equivalent output-distribution fidelity follows from addressability.

Result semantics: exact gate list + full amplitude/probability check ⇒ PASS within that circuit's scope; incomplete circuit or unsupported gate ⇒ explicit NOT_RUN/REJECTED. Keep existing QNN version FAIL and OPEN receipts intact.

**Update, same day:** times 3 to 100 of the 24-qubit sample ran in [the whole-circuit integer engine](FULL-Q24-INTEGER-20261104.md), so this audit's prefix now has its full circuit beside it. Its comparison with Google's simulator [passes](QSIM-OFFICIAL-REFERENCE-20261104.md), 128 of 128 parts within 10⁻⁶.
