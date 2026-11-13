# Shared Graft 81 × 81: one model with compact addressable corrections

**Build date:** November 13, 2026. First-stage integer predictive model. This code addresses 6,561 potential specialist correction slots; it does not claim to have trained all 6,561 slots on the operator's local corpus.

## What is built

- A **single shared** 256×256 conditional byte-probability table, trained by accumulating source counts and normalizing each row to at most 2,048 total unsmoothed counts. Counts use integer arithmetic only, with Laplace +1 smoothing. The same base table serves every specialist.
- **81 parent addresses × 81 leaf addresses**. Every *populated* parent stores three signed integer weight shifts; every populated leaf stores three further signed shifts. Parent and leaf corrections are added only when constructing effective probabilities. Unpopulated addresses are **not** recorded or counted as trained specialists.
- A compact **GGUF v3** file with the shared sparse count tensor once and two sparse delta tensors. A complete 6,561-head patch index would need at most 6,561×5 bytes plus 81×4 bytes, not 6,561 copies of the full conditional table. GGUF headers and alignment add some bytes and are always included in reported storage totals.
- A **past-only hierarchical router**. Each 256-byte decision checks trained parent heads using the 256 already-reconstructed bytes immediately before the decision, then checks the trained leaves of its chosen parent. Whenever the parent changes, the leaf history epoch resets. It never scores or chooses using future bytes. Deterministic ties use the first trained address.
- **Actual arithmetic coding**, with a separate cold decoder that needs only the GGUF model and the encoded stream, checks SHA-256 of the GGUF, stream payload and final reconstructed bytes, and recomputes all router decisions. The decoder does not need the training, validation or test source files.

The output is a working small learned *conditional byte predictor* with compact learned corrections. It is **not** an LLM, an actual trained qutrit quantum network, or any claim of 6,561 simultaneously executed individual GGUF LLMs.

## CPU commands (Rust 1.81)

```sh
# Tracked-file demo: 9 distinct training files, 3 validation files,
# 27 genuinely fitted correction addresses spread across 9 parent addresses.
cargo +1.81.0 run --release --locked --bin shared_graft -- --demo build/grafts

# Inspect the GGUF and its actual populated counts.
cargo +1.81.0 run --release --locked --bin shared_graft -- --inspect build/grafts/shared_tree.gguf

# Encode and later decode in a SEPARATE process.
cargo +1.81.0 run --release --locked --bin shared_graft -- --encode build/grafts/shared_tree.gguf INPUT.bin OUTPUT.stream tree
cargo +1.81.0 run --release --locked --bin shared_graft -- --decode build/grafts/shared_tree.gguf OUTPUT.stream RESTORED.bin
cmp INPUT.bin RESTORED.bin

# Train from prepared local corpus partitions (see schema below).
cargo +1.81.0 run --release --locked --bin shared_graft -- --fit-manifest manifest.tsv model.gguf
```

### Training on the operator's actual 6,561 files

The model accepts an **explicit manifest** with one line per *real* training/validation pair, separated by literal TAB characters:

```text
0    /path/to/train-0000.bin    /path/to/valid-0000.bin
1    /path/to/train-0001.bin    /path/to/valid-0001.bin
81   /path/to/train-0081.bin    /path/to/valid-0081.bin
6560 /path/to/train-6560.bin    /path/to/valid-6560.bin
```

(The spaces above represent TAB characters.)

The manifest must contain unique valid slots `0..6560`; each training and validation path must be distinct and may not appear in both splits. Each source reads up to 128 KiB of training and up to 512 bytes of validation. Fit the shared counts on training only; fit each parent and child correction by a deterministic integer grid search **on validation only**. The held-out test files and their paths do not appear in this manifest. The command fails closed on duplicate slots, missing files, and reused train/validation paths.

**No access to the operator's D: drive is available on the hosted runner.** Until all 6,561 real file partitions and hashes have been supplied to the runner, a 6,561-trained-head result must be marked NOT RUN. The small hosted fixture demonstrates *mechanics* and actually fitted weights on a known-burned local source benchmark; it is not a new blind performance claim.

## Test matrix and evidence

The dedicated [Rust 1.81 CI workflow](../.github/workflows/shared-graft.yml) verifies source and model integrity, strict format and Clippy, boundary checks, exact probability-frequency invertibility, malformed-model rejection and five matched encoded streams:

1. Shared backbone with no active corrections.
2. 81-parent selector using only the nine trained parents (no leaf table).
3. Shared parent-plus-leaf tree using 27 fitted leaf corrections.
4. Same trained address mask, but corrections zeroed.
5. Same mask with leaf correction assignments scrambled.

For each, it independently reloads the GGUF and encoded stream in a second executable process, recomputes all routing choices, restores the original held-out bytes exactly and writes SHA-256 receipts. It also trains a separate three-file manifest with sparse slots `0,81,6560` to exercise the very last 81×81 address.

**Storage accounting:** judge each arm by `GGUF model bytes + compressed stream bytes` for cold transfer, not the stream alone. Switching time and peak RAM matter separately, and streaming an unchanged cached model must be reported as an amortized *warm* scenario, not free cold compression.

## Scientific interpretation

This is a candidate to replace thousands of full specialist tables with a shared backbone and small weight patches. The hypothesis is falsifiable: this small three-class-bias model may compress **worse** than both the generalist and the original nine/27-table panels. The initial QNN [27-expert model test](../specialists/MEASURED-20261113.hbp) failed to beat the single generalist on its already inspected data; no subsequent rerun of that data becomes a blind test merely because the architecture changed.

Related operator report: the 6,561-file 81×81 panel and the dense-table surgery are **separate local experiments**. Their measured outputs must not be invented or imported into this GGUF model without explicit reproduction and hashed source partitions.

**Next gate:** freeze fresh independent source manifests, attach actual 6,561-file partitions, execute each arm on the exact same unknown test bytes, and compare both full cold transfer size and predictable decoder routes. Validate hierarchy resets whenever the selected parent changes and preserve all negative controls.
