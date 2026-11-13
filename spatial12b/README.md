# QNN spatial12b: shared integer weights over twelve billion virtual addresses

**Date:** November 12, 2026. **Status:** first-stage computational architecture experiment, not a trained neural model at billion-node scale.

This is the owned QNN implementation of a proposed HEB-C/HTTP-0-adjacent *network of networks*. The source of the real ternary reference is [HEB-C and HTTP-0](https://github.com/JesseBrown1980/qoled-internet-HEB-C-revisted-HTTP---free-0-hbi-hbp-sha-sh-hash), whose existing 96³ × 27 = 23,887,872-channel physical integer engine is **not modified** by this experiment.

## Exact construction

- **12,000,000,000** stable virtual identifiers, 0..11,999,999,999; these are not separately allocated, connected or trained networks.
- **27 channels per virtual room**. Decomposition: `room = floor(id/27)`, `channel = id%27`; `x = room%1024`, `y = floor(room/1024)%1024`, `z = floor(room/1048576)`. The final room contains 12 valid channels rather than 27. Its absent 15 channel slots must be rejected.
- **22 base-three address digits** suffice because 3²¹ = 10,460,353,203 is smaller than 12 billion and 3²² = 31,381,059,609 is larger. Encodings and decodings must be exact.
- **27-state node:** one occupied node stores a symbol 1..26 representing a triple of trits; 0 denotes an implicit inactive node. These are **not** entangled qutrits or physical quantum particles.
- **27 shared signed integer weight coefficients**, arranged as a 3×3 base matrix (9), 3+3 rank-one context vectors (6), 3×3 output matrix (9), and three output biases (3).
- **On-demand matrix:** `W(address)=B+g(address)uvᵀ`, where `g` is derived from the ternary residues of its position and channel. A three-hidden-unit integer network consumes the node trits and two neighboring nodes' trits, then produces a new 27-state symbol. These coefficients are design parameters, **not** pretrained QNN or GPT-6 optimized weights.
- **Sparse synchronous updates:** at most 4096 initialized nodes, three actual passes per virtual capacity. The remaining addresses are never evaluated. The executable records the actual evaluation count, final active count, runtime in microseconds, and a SHA-256 digest of the resulting active states.

The address space is bounded, with absent final-room nodes explicitly rejected. At every stage, an address is a coordinate; the experiment does not instantiate 12 billion neural networks.

## Prediction and tests

The prediction and negative gates were sealed first in [PREDICTION.hbp](PREDICTION.hbp).

The four rungs: 23,887,872, 100,000,000, 1,000,000,000 and 12,000,000,000 virtual nodes. Each tests at most 4096 active nodes per step, not the full namespace. Tests include exact address path round-trips, out-of-range rejection, directional and terminal boundary checks, context-dependent generated matrices, deterministic repeat replay, corrupt-state rejection, source-independent hash sensitivity, and bounded active storage.

The existing HEB-C nonlinear collision laws and Yang–Mills Hamiltonian are **not** used as a claimed neural reduction. In particular, the integer matrix-jump law is held for these nonlinear neural steps until a correct reduction theorem is established. **No training, language learning, GGUF rewriting, transfer accuracy, network communication, physical quantum entanglement, or GPU speedup is claimed.**

## Reproduction

```sh
cargo +1.81.0 test --locked --lib spatial12b
cargo +1.81.0 clippy --all-targets --locked -- -D warnings
cargo +1.81.0 run --release --locked --bin spatial12b -- --lookup 11999999999
cargo +1.81.0 run --release --locked --bin spatial12b -- --bench
```

The [dedicated GitHub Actions workflow](../.github/workflows/spatial12b.yml) pins Rust 1.81, forbids floats/JSON/Node in this project, runs the exact tests, records an HBP benchmark and hashes the evidence files.

## Next gates

1. Attach the generator to actual model weights, preferably a trained compact HRM or QNN model, with a pinned source hash and **held-out predictions**.
2. Compare static shared matrices, generated local matrices, and true GPT-authored weight edits with parameter, time, memory and accuracy matched.
3. Verify local-neighbor exchange by injecting controlled localized activity and observing precisely which next-state logits change.
4. Compare on multiple independent corpora or GGUFs, rather than extending claims from one Asolaria sample.
5. Only consider larger active sets and nonlinear jump acceleration after timing, storage and correctness gates pass.

A full 12-billion-state dense evaluation is a separate, expensive workload; the current address test must never be reported as that experiment.
