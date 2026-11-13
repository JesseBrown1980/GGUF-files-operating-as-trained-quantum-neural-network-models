# Compact specialist routing: exact causal switching and three-integer edits

**Status:** initial CPU experiment; source and negative controls frozen in [PREDICTION.hbp](PREDICTION.hbp) before implementation. This is the implementation of the next learning gate proposed after [Spatial12B](../spatial12b/README.md) and [panel issue #22](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/issues/22).

The operator-reported, locally executed nine-table experiment V31 is published in the [reductions repository](https://github.com/JesseBrown1980/what-is-asolaria---how-do-we-get-reductions-in-everything/tree/main/measurements/unpump-switches-20261113). Its nine-table compression improvement and subsequent byte-identical decoder switch replay are separate evidence. V31 also found a concrete 48-cell null-wall ambiguity witness for the dense Asolaria body, so exact transfer of dense tables by nine walls is not assumed here.

## Actual byte-stream experiment

This module and CLI use **a deliberately simple integer byte-bigram predictor**, not a trained large-language-model or a quantum circuit. Every model conditions on the immediately preceding byte. Each row of 256 byte counts has add-one smoothing.

- **Source-disjoint split:** nine QNN-tracked training files (three Rust code, three prose and three HBP), three distinct validation files, and six distinct test files (two per category). A file appears in exactly one split. Training reads at most 1400 bytes from each source. Filenames are fixed in `src/bin/specialist_router.rs`; source SHA-256 and lengths are printed by CI.
- **9-expert panel:** three independent training-file tables per category.
- **27-expert panel:** the same nine training files, each broken into three contiguous shards. These are *27 specialized predictors*, not 27 physical neurons or quantum states.
- **Direct corrections:** each expert has three `i8` weights, adjusting the probability of next-byte categories (whitespace, letter, other). Their admissible shifts are integers -2..2, mapped to weights `2^(shift+2)`. Two deterministic coordinate-descent passes fit them on **validation only**, never on test.
- **Router:** reads only the last 256 **already decoded** bytes at each 256-byte boundary. It selects the expert with smallest recent fixed-point log loss. The very first expert is selected on validation and its one-byte index is stored in the stream header. Subsequent decisions are not sent and are recomputed by the decoder using the same past bytes.
- **Stream:** actual 32-bit arithmetic encoding with integer frequencies. The decoder reads only a separately serialized sparse model file and entropy stream; it has no access to the source documents, validation material, training examples, future bytes or labels. All decoded bytes and all routing decisions are compared exactly.
- **Model storage:** count-table entries are serialized as `(previous_byte,next_byte,u16 count)`, with only nonzeros stored. All three correction bytes per expert are included. The measured `full_bytes = model_bytes + stream_bytes` includes necessary model storage and the stream's length/header metadata. This may be much larger than the compressed stream alone.
- **Six matching tests:** one generalist; 9 uncorrected; 9 validation-corrected; 27 uncorrected; 27 validation-corrected; 27 with the trained correction arrays deliberately reassigned to different experts. Every configuration gets precisely the same held-out interleaved target.

The training and evaluation sources are **the QNN repository's own tracked files**, not the large local Asolaria `D:` corpora. This gives a reproducible independent host test of the mechanics, but is not evidence that the original V31 corpora were trained or reproduced here.

## Reproduce

```sh
cargo +1.81.0 test --locked --lib specialists
cargo +1.81.0 clippy --locked --all-targets -- -D warnings
cargo +1.81.0 run --release --locked --bin specialist_router -- --run build/specialists
```

The dedicated [hosted CI](../.github/workflows/specialists.yml) emits HBP receipts and six actual `.stream`/`.model` pairs with SHA-256 manifests. Any byte-level or routing mismatch fails CI.

## Nonclaims and follow-up

Do not describe the test as a new large language model, actual learned HRM/QNN circuit weights, 12 billion active networks, or a quantum speed advantage. The three integer edits here are real saved predictive parameters but not changes to the large HRM tensor. The previous HRM training report's proposed one-row weight edit **failed**, moving exact held-out mazes from 489 to 484; failures matter.

The next stage must use multiple independent language corpora, balanced training bytes and a held-out unknown-source set. It should also compare the cost of sharing/caching common tables and tiny correction deltas against transmitting all complete specialist tables. Do not claim performance gains until the hosted run's actual `stream_bytes`, `model_bytes`, and controls support them.
